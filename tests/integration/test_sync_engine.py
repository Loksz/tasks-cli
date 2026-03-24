"""Tests de integración: SyncEngine con dos repositorios SQLite en memoria."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from tasks_cli.db.sqlite import SQLiteRepository
from tasks_cli.models.task import SyncStatus, Task
from tasks_cli.sync.engine import SyncEngine
from tasks_cli.sync.resolver import ConflictResolver


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def local_repo(tmp_path: Path) -> SQLiteRepository:
    repo = SQLiteRepository(tmp_path / "local.db")
    yield repo
    repo.close()


@pytest.fixture
def remote_repo(tmp_path: Path) -> SQLiteRepository:
    repo = SQLiteRepository(tmp_path / "remote.db")
    yield repo
    repo.close()


@pytest.fixture
def engine(local_repo: SQLiteRepository, remote_repo: SQLiteRepository) -> SyncEngine:
    return SyncEngine(local_repo, remote_repo)


# ---------------------------------------------------------------------------
# Push
# ---------------------------------------------------------------------------


class TestSyncEnginePush:
    def test_push_empty_local_does_nothing(self, engine: SyncEngine) -> None:
        result = engine.push()
        assert result.pushed == 0
        assert result.errors == []

    def test_push_sends_pending_tasks(
        self, engine: SyncEngine, local_repo: SQLiteRepository, remote_repo: SQLiteRepository
    ) -> None:
        task = Task(title="Nueva tarea", device_id="dev-1")
        task.sync_status = SyncStatus.pending
        local_repo.save(task)

        result = engine.push()

        assert result.pushed == 1
        assert result.errors == []
        assert remote_repo.get(task.id) is not None

    def test_push_marks_local_as_synced(
        self, engine: SyncEngine, local_repo: SQLiteRepository
    ) -> None:
        task = Task(title="Pendiente", device_id="dev-1")
        task.sync_status = SyncStatus.pending
        local_repo.save(task)

        engine.push()

        updated = local_repo.get(task.id)
        assert updated is not None
        assert updated.sync_status == SyncStatus.synced

    def test_push_skips_already_synced_tasks(
        self, engine: SyncEngine, local_repo: SQLiteRepository, remote_repo: SQLiteRepository
    ) -> None:
        task = Task(title="Ya sincronizada", device_id="dev-1")
        task.sync_status = SyncStatus.synced
        local_repo.save(task)

        result = engine.push()

        assert result.pushed == 0
        assert remote_repo.get(task.id) is None

    def test_push_multiple_tasks(
        self, engine: SyncEngine, local_repo: SQLiteRepository, remote_repo: SQLiteRepository
    ) -> None:
        tasks = [Task(title=f"T{i}", device_id="d") for i in range(3)]
        for t in tasks:
            t.sync_status = SyncStatus.pending
            local_repo.save(t)

        result = engine.push()

        assert result.pushed == 3
        for t in tasks:
            assert remote_repo.get(t.id) is not None


# ---------------------------------------------------------------------------
# Pull
# ---------------------------------------------------------------------------


class TestSyncEnginePull:
    def test_pull_empty_remote_does_nothing(self, engine: SyncEngine) -> None:
        result = engine.pull()
        assert result.pulled == 0
        assert result.errors == []

    def test_pull_applies_remote_tasks_locally(
        self, engine: SyncEngine, local_repo: SQLiteRepository, remote_repo: SQLiteRepository
    ) -> None:
        task = Task(title="Tarea remota", device_id="dev-2")
        task.sync_status = SyncStatus.synced
        remote_repo.save(task)

        result = engine.pull()

        assert result.pulled == 1
        assert local_repo.get(task.id) is not None

    def test_pull_updates_existing_local_task(
        self, engine: SyncEngine, local_repo: SQLiteRepository, remote_repo: SQLiteRepository
    ) -> None:
        task = Task(title="Original", device_id="dev-1")
        task.sync_status = SyncStatus.synced
        local_repo.save(task)

        # Simular modificación remota más reciente
        remote_version = task.model_copy()
        remote_version.title = "Modificada remotamente"
        remote_version.sync_status = SyncStatus.synced
        remote_repo.save(remote_version)

        engine.pull()

        local_after = local_repo.get(task.id)
        assert local_after is not None
        assert local_after.title == "Modificada remotamente"


# ---------------------------------------------------------------------------
# Conflictos
# ---------------------------------------------------------------------------


class TestConflictResolution:
    def test_last_write_wins_remote_newer(self) -> None:
        resolver = ConflictResolver()
        local = Task(title="Local", device_id="d")
        remote = local.model_copy()
        remote.title = "Remote"
        remote.updated_at = local.updated_at + timedelta(seconds=1)

        winner = resolver.resolve(local, remote)
        assert winner.title == "Remote"

    def test_last_write_wins_local_newer(self) -> None:
        resolver = ConflictResolver()
        local = Task(title="Local", device_id="d")
        remote = local.model_copy()
        remote.title = "Remote"
        remote.updated_at = local.updated_at - timedelta(seconds=1)

        winner = resolver.resolve(local, remote)
        assert winner.title == "Local"

    def test_is_conflict_different_versions_and_times(self) -> None:
        resolver = ConflictResolver()
        local = Task(title="T", device_id="d")
        local.sync_version = 1
        remote = local.model_copy()
        remote.sync_version = 2
        remote.updated_at = local.updated_at + timedelta(seconds=5)

        assert resolver.is_conflict(local, remote) is True

    def test_is_conflict_same_version(self) -> None:
        resolver = ConflictResolver()
        local = Task(title="T", device_id="d")
        remote = local.model_copy()
        # mismo sync_version → no hay conflicto

        assert resolver.is_conflict(local, remote) is False

    def test_push_resolves_conflict_keeps_winner(
        self, engine: SyncEngine, local_repo: SQLiteRepository, remote_repo: SQLiteRepository
    ) -> None:
        task = Task(title="Base", device_id="dev-1")
        task.sync_status = SyncStatus.pending
        task.sync_version = 1
        local_repo.save(task)

        # Versión remota más reciente con distinto sync_version → conflicto
        remote_version = task.model_copy()
        remote_version.title = "Remota gana"
        remote_version.sync_version = 2
        remote_version.updated_at = task.updated_at + timedelta(seconds=10)
        remote_version.sync_status = SyncStatus.synced
        remote_repo.save(remote_version)

        result = engine.push()

        assert result.conflicts == 1
        saved = remote_repo.get(task.id)
        assert saved is not None
        assert saved.title == "Remota gana"


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


class TestSyncEngineStatus:
    def test_status_no_pending(self, engine: SyncEngine, local_repo: SQLiteRepository) -> None:
        task = Task(title="Synced", device_id="d")
        task.sync_status = SyncStatus.synced
        local_repo.save(task)

        st = engine.status()
        assert st["pending_count"] == 0

    def test_status_with_pending(self, engine: SyncEngine, local_repo: SQLiteRepository) -> None:
        for i in range(3):
            t = Task(title=f"P{i}", device_id="d")
            t.sync_status = SyncStatus.pending
            local_repo.save(t)

        st = engine.status()
        assert st["pending_count"] == 3
        assert "checked_at" in st
