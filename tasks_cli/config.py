"""Gestión de configuración — lectura y escritura de ~/.tasks/config.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from tasks_cli.models.task import Config, Priority

_CONFIG_DIR = Path.home() / ".tasks"
_CONFIG_FILE = _CONFIG_DIR / "config.toml"


def get_config() -> Config:
    """Carga la configuración del usuario. Crea defaults si no existe."""
    if not _CONFIG_FILE.exists():
        config = Config()
        _ensure_dir()
        save_config(config)
        return config

    with open(_CONFIG_FILE, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    return Config.model_validate(data)


def save_config(config: Config) -> None:
    """Persiste la configuración en ~/.tasks/config.toml."""
    _ensure_dir()
    db_path_str = str(config.db_path).replace("\\", "/")
    lines = [
        f'device_id = "{config.device_id}"\n',
        f'db_path = "{db_path_str}"\n',
        f'sync_interval = {config.sync_interval}\n',
        f'default_priority = "{config.default_priority.value}"\n',
        f'date_format = "{config.date_format}"\n',
        f'no_color = {str(config.no_color).lower()}\n',
    ]
    if config.pg_dsn:
        lines.append(f'pg_dsn = "{config.pg_dsn}"\n')

    _CONFIG_FILE.write_text("".join(lines), encoding="utf-8")


def set_value(key: str, value: str) -> Config:
    """Actualiza un campo de configuración por nombre."""
    config = get_config()
    field_map: dict[str, Any] = {
        "sync_interval": int,
        "no_color": lambda v: v.lower() in ("true", "1", "yes"),
        "default_priority": Priority,
    }
    cast = field_map.get(key, str)
    setattr(config, key, cast(value))
    save_config(config)
    return config


def _ensure_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
