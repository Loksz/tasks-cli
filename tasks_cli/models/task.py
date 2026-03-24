"""Entidades del dominio: Task, enums y Config."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Enumeraciones
# ---------------------------------------------------------------------------


class TaskStatus(StrEnum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class SyncStatus(StrEnum):
    local = "local"
    pending = "pending"
    synced = "synced"
    conflict = "conflict"


class ExportFormat(StrEnum):
    json = "json"
    csv = "csv"
    markdown = "markdown"


# ---------------------------------------------------------------------------
# Entidad principal
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    notes: str | None = None
    status: TaskStatus = TaskStatus.pending
    priority: Priority = Priority.medium
    project: str | None = None
    tags: list[str] = Field(default_factory=list)
    due_date: date | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    completed_at: datetime | None = None
    sync_status: SyncStatus = SyncStatus.local
    sync_version: int = 0
    device_id: str = ""

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El título no puede estar vacío")
        return v.strip()

    def mark_done(self) -> None:
        self.status = TaskStatus.done
        self.completed_at = _utcnow()
        self.updated_at = _utcnow()
        self.sync_status = SyncStatus.pending

    def touch(self) -> None:
        self.updated_at = _utcnow()
        self.sync_status = SyncStatus.pending

    @property
    def short_id(self) -> str:
        return self.id[:8]

    @property
    def is_overdue(self) -> bool:
        if self.due_date is None or self.status in (TaskStatus.done, TaskStatus.cancelled):
            return False
        return self.due_date < date.today()


# ---------------------------------------------------------------------------
# Configuración del usuario
# ---------------------------------------------------------------------------


class Config(BaseModel):
    device_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    db_path: Path = Path.home() / ".tasks" / "tasks.db"
    pg_dsn: str | None = None  # cifrado en disco
    sync_interval: int = 5
    default_priority: Priority = Priority.medium
    date_format: str = "DD/MM/YYYY"
    no_color: bool = False
