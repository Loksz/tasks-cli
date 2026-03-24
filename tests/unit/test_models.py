"""Tests unitarios de modelos, enums y validación."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from tasks_cli.models.task import Priority, SyncStatus, Task, TaskStatus


class TestTaskCreation:
    def test_task_with_required_fields(self):
        task = Task(title="Mi tarea", device_id="dev-1")
        assert task.title == "Mi tarea"
        assert task.status == TaskStatus.pending
        assert task.priority == Priority.medium
        assert task.tags == []
        assert task.notes is None
        assert task.due_date is None

    def test_task_generates_uuid(self):
        t1 = Task(title="A", device_id="d")
        t2 = Task(title="B", device_id="d")
        assert t1.id != t2.id
        assert len(t1.id) == 36

    def test_task_short_id(self):
        task = Task(title="Test", device_id="d")
        assert task.short_id == task.id[:8]

    def test_task_empty_title_raises(self):
        with pytest.raises(ValidationError):
            Task(title="   ", device_id="d")

    def test_task_invalid_priority_raises(self):
        with pytest.raises(ValidationError):
            Task(title="X", priority="urgente", device_id="d")  # type: ignore

    def test_task_nullable_due_date(self):
        task = Task(title="Sin fecha", device_id="d")
        assert task.due_date is None

    def test_task_with_due_date(self):
        due = date(2026, 12, 31)
        task = Task(title="Con fecha", due_date=due, device_id="d")
        assert task.due_date == due

    def test_task_tags_variants(self):
        t0 = Task(title="Sin tags", device_id="d")
        t1 = Task(title="Un tag", tags=["work"], device_id="d")
        t3 = Task(title="Tres tags", tags=["a", "b", "c"], device_id="d")
        assert t0.tags == []
        assert t1.tags == ["work"]
        assert len(t3.tags) == 3

    def test_task_round_trip(self):
        task = Task(title="Round trip", priority=Priority.high, tags=["x"], device_id="d")
        data = task.model_dump()
        restored = Task.model_validate(data)
        assert restored.id == task.id
        assert restored.title == task.title
        assert restored.priority == task.priority
        assert restored.tags == task.tags


class TestTaskBehavior:
    def test_mark_done(self):
        task = Task(title="Completar", device_id="d")
        task.mark_done()
        assert task.status == TaskStatus.done
        assert task.completed_at is not None
        assert task.sync_status == SyncStatus.pending

    def test_is_overdue_past_due(self):
        task = Task(title="Vencida", due_date=date(2020, 1, 1), device_id="d")
        assert task.is_overdue is True

    def test_is_overdue_future(self):
        task = Task(title="Futura", due_date=date(2099, 12, 31), device_id="d")
        assert task.is_overdue is False

    def test_is_overdue_no_date(self):
        task = Task(title="Sin fecha", device_id="d")
        assert task.is_overdue is False

    def test_is_overdue_done_task(self):
        task = Task(title="Hecha", due_date=date(2020, 1, 1), device_id="d")
        task.mark_done()
        assert task.is_overdue is False

    def test_touch_sets_pending_sync(self):
        task = Task(title="Touch", device_id="d")
        task.sync_status = SyncStatus.synced
        task.touch()
        assert task.sync_status == SyncStatus.pending
