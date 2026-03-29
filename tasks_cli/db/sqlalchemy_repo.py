"""Implementación SQLAlchemy de TaskRepository — compatible con PostgreSQL, MySQL, MariaDB, etc."""

from __future__ import annotations

import json

from sqlalchemy import JSON, Column, Date, DateTime, Index, Integer, String, Text, create_engine, func, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session

from tasks_cli.db.base import TaskFilters, TaskRepository
from tasks_cli.models.task import Priority, SyncStatus, Task, TaskStatus


class _Base(DeclarativeBase):
    pass


class _TaskRow(_Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    title = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    priority = Column(String(10), nullable=False, default="medium")
    project = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=False, default=list)
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(String(20), nullable=False, default="synced")
    sync_version = Column(Integer, nullable=False, default=0)
    device_id = Column(String(36), nullable=False, default="")

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_project", "project"),
        Index("ix_tasks_due_date", "due_date"),
        Index("ix_tasks_sync_status", "sync_status"),
    )


class SQLAlchemyRepository(TaskRepository):
    """Repositorio basado en SQLAlchemy — funciona con cualquier BD compatible."""

    def __init__(self, dsn: str) -> None:
        self._engine: Engine = create_engine(dsn, pool_pre_ping=True)
        _Base.metadata.create_all(self._engine)

    def get(self, task_id: str) -> Task | None:
        with Session(self._engine) as s:
            row = s.get(_TaskRow, task_id)
            return _to_task(row) if row else None

    def list(self, filters: TaskFilters | None = None) -> list[Task]:
        with Session(self._engine) as s:
            q = s.query(_TaskRow)
            if filters:
                if filters.status:
                    q = q.filter(_TaskRow.status == filters.status.value)
                if filters.priority:
                    q = q.filter(_TaskRow.priority == filters.priority.value)
                if filters.project:
                    q = q.filter(_TaskRow.project == filters.project)
                if filters.due_before:
                    q = q.filter(_TaskRow.due_date <= filters.due_before)
                if filters.due_after:
                    q = q.filter(_TaskRow.due_date >= filters.due_after)
                if filters.tag:
                    q = q.filter(_TaskRow.tags.contains(filters.tag))
                if filters.limit:
                    q = q.limit(filters.limit)
            rows = q.all()
        return [_to_task(r) for r in rows]

    def save(self, task: Task) -> Task:
        with Session(self._engine) as s:
            row = s.get(_TaskRow, task.id)
            if row is None:
                row = _TaskRow(id=task.id)
                s.add(row)
            _fill_row(row, task)
            s.commit()
        return task

    def delete(self, task_id: str) -> bool:
        with Session(self._engine) as s:
            row = s.get(_TaskRow, task_id)
            if row is None:
                return False
            s.delete(row)
            s.commit()
        return True

    def search(self, query: str) -> list[Task]:
        pattern = f"%{query.lower()}%"
        with Session(self._engine) as s:
            rows = (
                s.query(_TaskRow)
                .filter(
                    func.lower(_TaskRow.title).like(pattern)
                    | func.lower(_TaskRow.notes).like(pattern)
                )
                .all()
            )
        return [_to_task(r) for r in rows]

    def get_pending_sync(self) -> list[Task]:
        with Session(self._engine) as s:
            rows = s.query(_TaskRow).filter(_TaskRow.sync_status == "pending").all()
        return [_to_task(r) for r in rows]

    def mark_synced(self, ids: list[str]) -> int:
        if not ids:
            return 0
        with Session(self._engine) as s:
            count = (
                s.query(_TaskRow)
                .filter(_TaskRow.id.in_(ids))
                .update({"sync_status": "synced"}, synchronize_session=False)
            )
            s.commit()
        return count

    def close(self) -> None:
        self._engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_task(row: _TaskRow) -> Task:
    tags = row.tags if isinstance(row.tags, list) else json.loads(row.tags or "[]")
    return Task.model_validate(
        {
            "id": row.id,
            "title": row.title,
            "notes": row.notes,
            "status": TaskStatus(row.status),
            "priority": Priority(row.priority),
            "project": row.project,
            "tags": tags,
            "due_date": row.due_date,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "completed_at": row.completed_at,
            "sync_status": SyncStatus(row.sync_status),
            "sync_version": row.sync_version,
            "device_id": row.device_id,
        }
    )


def _fill_row(row: _TaskRow, task: Task) -> None:
    row.title = task.title
    row.notes = task.notes
    row.status = task.status.value
    row.priority = task.priority.value
    row.project = task.project
    row.tags = task.tags
    row.due_date = task.due_date
    row.created_at = task.created_at
    row.updated_at = task.updated_at
    row.completed_at = task.completed_at
    row.sync_status = task.sync_status.value
    row.sync_version = task.sync_version
    row.device_id = task.device_id
