"""SyncEngine — coordina push/pull entre el repositorio local y el remoto."""

from __future__ import annotations

from datetime import UTC, datetime

from tasks_cli.db.base import TaskRepository
from tasks_cli.models.task import SyncStatus
from tasks_cli.sync.resolver import ConflictResolver


class SyncResult:
    def __init__(self) -> None:
        self.pushed: int = 0
        self.pulled: int = 0
        self.conflicts: int = 0
        self.errors: list[str] = []

    def __repr__(self) -> str:
        return (
            f"SyncResult(pushed={self.pushed}, pulled={self.pulled}, "
            f"conflicts={self.conflicts}, errors={len(self.errors)})"
        )


class SyncEngine:
    def __init__(
        self,
        local: TaskRepository,
        remote: TaskRepository,
        resolver: ConflictResolver | None = None,
    ) -> None:
        self._local = local
        self._remote = remote
        self._resolver = resolver or ConflictResolver()

    def push(self) -> SyncResult:
        """Envía tareas pendientes desde el local hacia el remoto."""
        result = SyncResult()
        pending = self._local.get_pending_sync()

        if not pending:
            return result

        synced_ids: list[str] = []
        for task in pending:
            try:
                remote_task = self._remote.get(task.id)
                if remote_task and self._resolver.is_conflict(task, remote_task):
                    winner = self._resolver.resolve(task, remote_task)
                    winner.sync_status = SyncStatus.synced
                    winner.sync_version += 1
                    self._remote.save(winner)
                    self._local.save(winner)  # aplica el ganador también en local
                    result.conflicts += 1
                else:
                    task.sync_status = SyncStatus.synced
                    task.sync_version += 1
                    self._remote.save(task)

                synced_ids.append(task.id)
                result.pushed += 1
            except Exception as exc:
                result.errors.append(f"{task.id}: {exc}")

        self._local.mark_synced(synced_ids)
        return result

    def pull(self, since: datetime | None = None) -> SyncResult:
        """Descarga cambios del remoto y los aplica en el local."""
        result = SyncResult()
        remote_tasks = self._remote.list()
        pulled_ids: list[str] = []

        for remote_task in remote_tasks:
            if since and remote_task.updated_at < since:
                continue
            try:
                local_task = self._local.get(remote_task.id)
                if local_task and self._resolver.is_conflict(local_task, remote_task):
                    winner = self._resolver.resolve(local_task, remote_task)
                    winner.sync_status = SyncStatus.synced
                    winner.sync_version += 1
                    self._local.save(winner)
                    result.conflicts += 1
                else:
                    remote_task.sync_status = SyncStatus.synced
                    self._local.save(remote_task)
                    result.pulled += 1

                pulled_ids.append(remote_task.id)
            except Exception as exc:
                result.errors.append(f"{remote_task.id}: {exc}")

        self._local.mark_synced(pulled_ids)
        return result

    def status(self) -> dict:
        pending = self._local.get_pending_sync()
        return {
            "pending_count": len(pending),
            "checked_at": datetime.now(UTC).isoformat(),
        }
