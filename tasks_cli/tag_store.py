"""Almacén persistente de etiquetas conocidas."""

from __future__ import annotations

import json
from pathlib import Path


def _path() -> Path:
    from tasks_cli.config import get_config
    return Path(get_config().db_path).parent / "tags.json"


def load() -> list[str]:
    p = _path()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def save(tag: str) -> None:
    tags = load()
    if tag not in tags:
        tags.append(tag)
        tags.sort()
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(tags, ensure_ascii=False), encoding="utf-8")
