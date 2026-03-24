"""Tests de integración: SQLiteRepository con base de datos real."""

from __future__ import annotations

from tasks_cli.db.base import TaskFilters
from tasks_cli.db.sqlite import SQLiteRepository
from tasks_cli.models.task import Priority, SyncStatus, Task, TaskStatus


class TestSQLiteRepository:
    def test_save_and_get(self, tmp_db: SQLiteRepository, sample_task: Task):
        tmp_db.save(sample_task)
        retrieved = tmp_db.get(sample_task.id)
        assert retrieved is not None
        assert retrieved.id == sample_task.id
        assert retrieved.title == sample_task.title
        assert retrieved.priority == sample_task.priority

    def test_get_nonexistent_returns_none(self, tmp_db: SQLiteRepository):
        assert tmp_db.get("00000000-0000-0000-0000-000000000000") is None

    def test_list_no_filters(self, populated_db: SQLiteRepository):
        tasks = populated_db.list()
        assert len(tasks) == 3

    def test_list_filter_by_status(self, tmp_db: SQLiteRepository):
        pending = Task(title="Pendiente", device_id="d")
        done = Task(title="Hecha", device_id="d")
        done.mark_done()
        tmp_db.save(pending)
        tmp_db.save(done)

        results = tmp_db.list(TaskFilters(status=TaskStatus.done))
        assert all(t.status == TaskStatus.done for t in results)
        assert len(results) == 1

    def test_list_filter_by_priority(self, populated_db: SQLiteRepository):
        results = populated_db.list(TaskFilters(priority=Priority.high))
        assert all(t.priority == Priority.high for t in results)

    def test_delete_existing(self, tmp_db: SQLiteRepository, sample_task: Task):
        tmp_db.save(sample_task)
        assert tmp_db.delete(sample_task.id) is True
        assert tmp_db.get(sample_task.id) is None

    def test_delete_nonexistent_returns_false(self, tmp_db: SQLiteRepository):
        assert tmp_db.delete("00000000-0000-0000-0000-000000000000") is False

    def test_search_by_title(self, tmp_db: SQLiteRepository):
        tmp_db.save(Task(title="Revisar PR de backend", device_id="d"))
        tmp_db.save(Task(title="Escribir tests", device_id="d"))
        results = tmp_db.search("backend")
        assert len(results) == 1
        assert "backend" in results[0].title

    def test_search_by_notes(self, tmp_db: SQLiteRepository):
        t = Task(title="Tarea", notes="Revisar la documentación del API", device_id="d")
        tmp_db.save(t)
        results = tmp_db.search("documentación")
        assert len(results) == 1

    def test_upsert_updates_existing(self, tmp_db: SQLiteRepository, sample_task: Task):
        tmp_db.save(sample_task)
        sample_task.title = "Título modificado"
        sample_task.touch()
        tmp_db.save(sample_task)

        updated = tmp_db.get(sample_task.id)
        assert updated is not None
        assert updated.title == "Título modificado"

    def test_get_pending_sync(self, tmp_db: SQLiteRepository):
        t1 = Task(title="Pendiente sync", device_id="d")
        t2 = Task(title="Synced", device_id="d")
        t1.sync_status = SyncStatus.pending
        t2.sync_status = SyncStatus.synced
        tmp_db.save(t1)
        tmp_db.save(t2)

        pending = tmp_db.get_pending_sync()
        assert len(pending) == 1
        assert pending[0].id == t1.id

    def test_mark_synced(self, tmp_db: SQLiteRepository):
        tasks = [Task(title=f"T{i}", device_id="d") for i in range(3)]
        for t in tasks:
            t.sync_status = SyncStatus.pending
            tmp_db.save(t)

        ids = [t.id for t in tasks[:2]]
        count = tmp_db.mark_synced(ids)
        assert count == 2

        for t_id in ids:
            task = tmp_db.get(t_id)
            assert task is not None
            assert task.sync_status == SyncStatus.synced

    def test_tags_round_trip(self, tmp_db: SQLiteRepository):
        task = Task(title="Con tags", tags=["alpha", "beta", "gamma"], device_id="d")
        tmp_db.save(task)
        retrieved = tmp_db.get(task.id)
        assert retrieved is not None
        assert retrieved.tags == ["alpha", "beta", "gamma"]
