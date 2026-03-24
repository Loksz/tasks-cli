"""Implementación SQLite de TaskRepository — backend local."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tasks_cli.db.base import TaskFilters, TaskRepository
from tasks_cli.models.task import Priority, SyncStatus, Task, TaskStatus

_DDL = """
CREATE TABLE IF NOT EXISTS tasks (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    notes        TEXT,
    status       TEXT NOT NULL DEFAULT 'pending',
    priority     TEXT NOT NULL DEFAULT 'medium',
    project      TEXT,
    tags         TEXT NOT NULL DEFAULT '[]',
    due_date     TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    completed_at TEXT,
    sync_status  TEXT NOT NULL DEFAULT 'local',
    sync_version INTEGER NOT NULL DEFAULT 0,
    device_id    TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_tasks_status   ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_project  ON tasks(project);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_sync     ON tasks(sync_status);
"""


class SQLiteRepository(TaskRepository):
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Interface implementation
    # ------------------------------------------------------------------

    def get(self, task_id: str) -> Task | None:
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return self._row_to_task(row) if row else None

    def get_by_prefix(self, prefix: str) -> Task | None:
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE id LIKE ?", (f"{prefix}%",)
        ).fetchall()
        return self._row_to_task(rows[0]) if len(rows) == 1 else None

    def list(self, filters: TaskFilters | None = None) -> list[Task]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list = []

        if filters:
            if filters.status:
                query += " AND status = ?"
                params.append(filters.status.value)
            if filters.priority:
                query += " AND priority = ?"
                params.append(filters.priority.value)
            if filters.project:
                query += " AND project = ?"
                params.append(filters.project)
            if filters.due_before:
                query += " AND due_date <= ?"
                params.append(filters.due_before.isoformat())
            if filters.due_after:
                query += " AND due_date >= ?"
                params.append(filters.due_after.isoformat())
            if filters.tag:
                query += " AND tags LIKE ?"
                params.append(f'%"{filters.tag}"%')
            if filters.limit:
                query += f" LIMIT {filters.limit}"

        query += " ORDER BY priority DESC, due_date ASC, created_at ASC"
        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_task(r) for r in rows]

    def save(self, task: Task) -> Task:
        data = task.model_dump()
        data["tags"] = json.dumps(data["tags"])
        data["due_date"] = task.due_date.isoformat() if task.due_date else None
        data["created_at"] = task.created_at.isoformat()
        data["updated_at"] = task.updated_at.isoformat()
        data["completed_at"] = task.completed_at.isoformat() if task.completed_at else None
        data["status"] = task.status.value
        data["priority"] = task.priority.value
        data["sync_status"] = task.sync_status.value

        self._conn.execute(
            """
            INSERT INTO tasks VALUES (
                :id, :title, :notes, :status, :priority, :project,
                :tags, :due_date, :created_at, :updated_at, :completed_at,
                :sync_status, :sync_version, :device_id
            )
            ON CONFLICT(id) DO UPDATE SET
                title        = excluded.title,
                notes        = excluded.notes,
                status       = excluded.status,
                priority     = excluded.priority,
                project      = excluded.project,
                tags         = excluded.tags,
                due_date     = excluded.due_date,
                updated_at   = excluded.updated_at,
                completed_at = excluded.completed_at,
                sync_status  = excluded.sync_status,
                sync_version = excluded.sync_version
            """,
            data,
        )
        self._conn.commit()
        return task

    def delete(self, task_id: str) -> bool:
        cursor = self._conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def search(self, query: str) -> list[Task]:
        like = f"%{query}%"
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE title LIKE ? OR notes LIKE ?",
            (like, like),
        ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def get_pending_sync(self) -> list[Task]:
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE sync_status = 'pending'"
        ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def mark_synced(self, ids: list[str]) -> int:
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        cursor = self._conn.execute(
            f"UPDATE tasks SET sync_status = 'synced' WHERE id IN ({placeholders})",
            ids,
        )
        self._conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        d = dict(row)
        d["tags"] = json.loads(d["tags"] or "[]")
        d["status"] = TaskStatus(d["status"])
        d["priority"] = Priority(d["priority"])
        d["sync_status"] = SyncStatus(d["sync_status"])
        return Task.model_validate(d)
