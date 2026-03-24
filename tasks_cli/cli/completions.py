"""Funciones de autocompletado — leen del caché JSON, sin imports pesados."""

from __future__ import annotations

import json
from pathlib import Path

_CACHE_FILE = Path.home() / ".tasks" / ".completions_cache.json"

_CONFIG_KEYS = [
    ("default_priority", "Prioridad por defecto (low/medium/high)"),
    ("sync_interval",    "Intervalo de sync en minutos"),
    ("date_format",      "Formato de fecha (DD/MM/YYYY)"),
    ("no_color",         "Desactivar colores (true/false)"),
]


def _load(key: str) -> list[list[str]]:
    try:
        data = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        return data.get(key, [])
    except Exception:
        return []


def complete_task_id(incomplete: str) -> list[tuple[str, str]]:
    return [
        (row[0], row[1])
        for row in _load("all_tasks")
        if row[0].startswith(incomplete) or not incomplete
    ]


def complete_pending_id(incomplete: str) -> list[tuple[str, str]]:
    return [
        (row[0], row[1])
        for row in _load("pending_tasks")
        if row[0].startswith(incomplete) or not incomplete
    ]


def complete_project(incomplete: str) -> list[tuple[str, str]]:
    return [
        (row[0], row[1])
        for row in _load("projects")
        if row[0].lower().startswith(incomplete.lower()) or not incomplete
    ]


def complete_tag(incomplete: str) -> list[tuple[str, str]]:
    return [
        (row[0], row[1])
        for row in _load("tags")
        if row[0].lower().startswith(incomplete.lower()) or not incomplete
    ]


def complete_config_key(incomplete: str) -> list[tuple[str, str]]:
    return [
        (k, desc)
        for k, desc in _CONFIG_KEYS
        if k.startswith(incomplete) or not incomplete
    ]
