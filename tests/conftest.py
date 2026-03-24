"""Fixtures compartidos para todos los tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from tasks_cli.db.sqlite import SQLiteRepository
from tasks_cli.models.task import Priority, Task, TaskStatus


@pytest.fixture
def tmp_db(tmp_path: Path) -> SQLiteRepository:
    """Repositorio SQLite en directorio temporal."""
    repo = SQLiteRepository(tmp_path / "test.db")
    yield repo
    repo.close()


@pytest.fixture
def sample_task() -> Task:
    return Task(
        title="Tarea de prueba",
        priority=Priority.high,
        project="test-project",
        tags=["pytest", "ci"],
        device_id="test-device",
    )


@pytest.fixture
def populated_db(tmp_db: SQLiteRepository) -> SQLiteRepository:
    """Repositorio con tareas de muestra."""
    tasks = [
        Task(title="Tarea alta", priority=Priority.high, device_id="d1"),
        Task(title="Tarea media", priority=Priority.medium, device_id="d1"),
        Task(title="Tarea baja", priority=Priority.low, device_id="d1"),
    ]
    for t in tasks:
        tmp_db.save(t)
    return tmp_db
