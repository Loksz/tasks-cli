"""Implementación PostgreSQL de TaskRepository — backend de sincronización."""

from __future__ import annotations

import json

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from tasks_cli.db.base import TaskFilters, TaskRepository
from tasks_cli.models.task import Priority, SyncStatus, Task, TaskStatus


class PostgreSQLRepository(TaskRepository):
    def __init__(self, dsn: str) -> None:
        self._engine: Engine = create_engine(dsn, pool_pre_ping=True)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS tasks (
            id           UUID PRIMARY KEY,
            title        TEXT NOT NULL,
            notes        TEXT,
            status       TEXT NOT NULL DEFAULT 'pending',
            priority     TEXT NOT NULL DEFAULT 'medium',
            project      TEXT,
            tags         JSONB NOT NULL DEFAULT '[]',
            due_date     DATE,
            created_at   TIMESTAMPTZ NOT NULL,
            updated_at   TIMESTAMPTZ NOT NULL,
            completed_at TIMESTAMPTZ,
            sync_status  TEXT NOT NULL DEFAULT 'synced',
            sync_version INTEGER NOT NULL DEFAULT 0,
            device_id    TEXT NOT NULL DEFAULT ''
        );
        """
        with self._engine.begin() as conn:
            conn.execute(text(ddl))

    def get(self, task_id: str) -> Task | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM tasks WHERE id = :id"), {"id": task_id}
            ).mappings().fetchone()
        return self._map_to_task(dict(row)) if row else None

    def list(self, filters: TaskFilters | None = None) -> list[Task]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: dict = {}

        if filters:
            if filters.status:
                query += " AND status = :status"
                params["status"] = filters.status.value
            if filters.priority:
                query += " AND priority = :priority"
                params["priority"] = filters.priority.value
            if filters.project:
                query += " AND project = :project"
                params["project"] = filters.project

        with self._engine.connect() as conn:
            rows = conn.execute(text(query), params).mappings().fetchall()
        return [self._map_to_task(dict(r)) for r in rows]

    def save(self, task: Task) -> Task:
        upsert = text("""
            INSERT INTO tasks (
                id, title, notes, status, priority, project, tags,
                due_date, created_at, updated_at, completed_at,
                sync_status, sync_version, device_id
            ) VALUES (
                :id, :title, :notes, :status, :priority, :project, :tags::jsonb,
                :due_date, :created_at, :updated_at, :completed_at,
                :sync_status, :sync_version, :device_id
            )
            ON CONFLICT (id) DO UPDATE SET
                title        = EXCLUDED.title,
                notes        = EXCLUDED.notes,
                status       = EXCLUDED.status,
                priority     = EXCLUDED.priority,
                project      = EXCLUDED.project,
                tags         = EXCLUDED.tags,
                due_date     = EXCLUDED.due_date,
                updated_at   = EXCLUDED.updated_at,
                completed_at = EXCLUDED.completed_at,
                sync_status  = EXCLUDED.sync_status,
                sync_version = EXCLUDED.sync_version
        """)
        params = task.model_dump()
        params["tags"] = json.dumps(params["tags"])
        params["status"] = task.status.value
        params["priority"] = task.priority.value
        params["sync_status"] = task.sync_status.value

        with self._engine.begin() as conn:
            conn.execute(upsert, params)
        return task

    def delete(self, task_id: str) -> bool:
        with self._engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM tasks WHERE id = :id"), {"id": task_id}
            )
        return result.rowcount > 0

    def search(self, query: str) -> list[Task]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM tasks WHERE title ILIKE :q OR notes ILIKE :q"),
                {"q": f"%{query}%"},
            ).mappings().fetchall()
        return [self._map_to_task(dict(r)) for r in rows]

    def get_pending_sync(self) -> list[Task]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM tasks WHERE sync_status = 'pending'")
            ).mappings().fetchall()
        return [self._map_to_task(dict(r)) for r in rows]

    def mark_synced(self, ids: list[str]) -> int:
        if not ids:
            return 0
        with self._engine.begin() as conn:
            result = conn.execute(
                text("UPDATE tasks SET sync_status = 'synced' WHERE id = ANY(:ids)"),
                {"ids": ids},
            )
        return result.rowcount

    def close(self) -> None:
        self._engine.dispose()

    @staticmethod
    def _map_to_task(row: dict) -> Task:
        if isinstance(row.get("tags"), str):
            row["tags"] = json.loads(row["tags"])
        row["status"] = TaskStatus(row["status"])
        row["priority"] = Priority(row["priority"])
        row["sync_status"] = SyncStatus(row.get("sync_status", "synced"))
        return Task.model_validate(row)
