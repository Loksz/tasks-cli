"""Caché de autocompletado — archivo JSON ligero actualizado tras cada mutación."""

from __future__ import annotations

import json
from pathlib import Path

_CACHE_FILE = Path.home() / ".tasks" / ".completions_cache.json"


def update(repo) -> None:  # type: ignore[no-untyped-def]
    """Regenera el caché leyendo el estado actual del repositorio."""
    from tasks_cli.models.task import TaskStatus

    all_tasks = repo.list()
    pending = [t for t in all_tasks if t.status == TaskStatus.pending]

    projects: dict[str, int] = {}
    tags: dict[str, int] = {}
    for t in all_tasks:
        if t.project:
            projects[t.project] = projects.get(t.project, 0) + 1
        for tag in t.tags:
            tags[tag] = tags.get(tag, 0) + 1

    cache = {
        "all_tasks": [[t.short_id, t.title] for t in all_tasks],
        "pending_tasks": [[t.short_id, t.title] for t in pending],
        "projects": [[name, f"{count} tarea(s)"] for name, count in sorted(projects.items())],
        "tags": [[tag, f"{count} tarea(s)"] for tag, count in sorted(tags.items())],
    }

    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
