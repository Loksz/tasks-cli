"""Interface abstracta TaskRepository — patrón Repository."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

from tasks_cli.models.task import Priority, Task, TaskStatus


@dataclass
class TaskFilters:
    status: TaskStatus | None = None
    priority: Priority | None = None
    tag: str | None = None
    project: str | None = None
    due_before: date | None = None
    due_after: date | None = None
    limit: int | None = None
    extra: dict = field(default_factory=dict)


class TaskRepository(ABC):
    """Contrato de acceso a datos — independiente del backend."""

    @abstractmethod
    def get(self, task_id: str) -> Task | None:
        """Obtener una tarea por su ID."""
        ...

    @abstractmethod
    def list(self, filters: TaskFilters | None = None) -> list[Task]:
        """Listar tareas con filtros opcionales."""
        ...

    @abstractmethod
    def save(self, task: Task) -> Task:
        """Crear o actualizar una tarea (upsert)."""
        ...

    @abstractmethod
    def delete(self, task_id: str) -> bool:
        """Eliminar una tarea. Retorna True si existía."""
        ...

    @abstractmethod
    def search(self, query: str) -> list[Task]:
        """Búsqueda de texto completo en título y notas."""
        ...

    @abstractmethod
    def get_pending_sync(self) -> list[Task]:
        """Tareas con sync_status = pending — para push."""
        ...

    @abstractmethod
    def mark_synced(self, ids: list[str]) -> int:
        """Marcar tareas como synced. Retorna cantidad actualizada."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Cerrar la conexión / limpiar recursos."""
        ...
