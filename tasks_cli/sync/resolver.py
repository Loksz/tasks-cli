"""ConflictResolver — estrategia last-write-wins basada en updated_at."""

from __future__ import annotations

from tasks_cli.models.task import Task


class ConflictResolver:
    """Resuelve conflictos entre la versión local y la versión del servidor.

    Estrategia: last-write-wins comparando updated_at.
    Extensible: sobreescribir `resolve` para otras estrategias.
    """

    def resolve(self, local: Task, remote: Task) -> Task:
        """Retorna la versión ganadora entre local y remota."""
        if remote.updated_at >= local.updated_at:
            return remote
        return local

    def is_conflict(self, local: Task, remote: Task) -> bool:
        """True si ambas versiones fueron modificadas desde el último sync."""
        return (
            local.sync_version != remote.sync_version
            and local.updated_at != remote.updated_at
        )
