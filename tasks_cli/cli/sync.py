"""Comandos de sincronización: setup, push, pull, status, auto."""

from __future__ import annotations

import typer

from tasks_cli.cli.utils import console, error, info, success
from tasks_cli.config import get_config, save_config

_SYNC_DEPS_MSG = (
    "Las dependencias de sincronización no están instaladas.\n"
    r"Instálalas con:  pip install 'tasks-cli\[sync]'"
)


def _require_sync_deps() -> None:
    try:
        import cryptography  # noqa: F401
        import sqlalchemy  # noqa: F401
    except ImportError:
        error(_SYNC_DEPS_MSG)
        raise typer.Exit(1)

app = typer.Typer(help="Sincronización entre dispositivos")


def _encrypt_dsn(dsn: str) -> str:
    """Cifra el DSN con Fernet antes de guardarlo en disco."""

    from cryptography.fernet import Fernet

    key_path = _key_path()
    if not key_path.exists():
        key = Fernet.generate_key()
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(key)

    key = key_path.read_bytes()
    return Fernet(key).encrypt(dsn.encode()).decode()


def _decrypt_dsn(token: str) -> str:
    from cryptography.fernet import Fernet
    key = _key_path().read_bytes()
    return Fernet(key).decrypt(token.encode()).decode()


def _key_path():
    from pathlib import Path
    return Path.home() / ".tasks" / ".sync.key"


@app.command()
def setup(
    dsn: str = typer.Option(..., "--dsn", help="postgresql://user:pass@host:5432/db"),
) -> None:
    """Configurar conexión a PostgreSQL y guardar credenciales cifradas."""
    _require_sync_deps()
    try:
        from tasks_cli.db.postgres import PostgreSQLRepository
        repo = PostgreSQLRepository(dsn)
        repo.close()
    except Exception as exc:
        error(f"No se pudo conectar: {exc}")
        raise typer.Exit(1)

    cfg = get_config()
    cfg.pg_dsn = _encrypt_dsn(dsn)
    save_config(cfg)
    success("Conexión configurada y credenciales cifradas.")


@app.command()
def push() -> None:
    """Enviar cambios locales pendientes al servidor PostgreSQL."""
    _require_sync_deps()
    cfg = get_config()
    if not cfg.pg_dsn:
        error("Sync no configurado. Ejecuta: tasks sync setup --dsn <DSN>")
        raise typer.Exit(1)

    from tasks_cli.db.postgres import PostgreSQLRepository
    from tasks_cli.db.sqlite import SQLiteRepository
    from tasks_cli.sync.engine import SyncEngine

    local = SQLiteRepository(cfg.db_path)
    remote = PostgreSQLRepository(_decrypt_dsn(cfg.pg_dsn))
    engine = SyncEngine(local, remote)

    with console.status("Enviando cambios..."):
        result = engine.push()

    local.close()
    remote.close()

    if result.errors:
        for e in result.errors:
            error(e)
    success(f"Push completado — enviadas: {result.pushed}  conflictos: {result.conflicts}")


@app.command()
def pull() -> None:
    """Descargar cambios del servidor y aplicarlos localmente."""
    _require_sync_deps()
    cfg = get_config()
    if not cfg.pg_dsn:
        error("Sync no configurado. Ejecuta: tasks sync setup --dsn <DSN>")
        raise typer.Exit(1)

    from tasks_cli.db.postgres import PostgreSQLRepository
    from tasks_cli.db.sqlite import SQLiteRepository
    from tasks_cli.sync.engine import SyncEngine

    local = SQLiteRepository(cfg.db_path)
    remote = PostgreSQLRepository(_decrypt_dsn(cfg.pg_dsn))
    engine = SyncEngine(local, remote)

    with console.status("Descargando cambios..."):
        result = engine.pull()

    local.close()
    remote.close()

    if result.errors:
        for e in result.errors:
            error(e)
    success(f"Pull completado — aplicadas: {result.pulled}  conflictos: {result.conflicts}")


@app.command(name="status")
def sync_status() -> None:
    """Mostrar cambios pendientes y estado del último sync."""
    _require_sync_deps()
    cfg = get_config()
    if not cfg.pg_dsn:
        info("Sync no configurado.")
        return

    from tasks_cli.db.postgres import PostgreSQLRepository
    from tasks_cli.db.sqlite import SQLiteRepository
    from tasks_cli.sync.engine import SyncEngine

    local = SQLiteRepository(cfg.db_path)
    remote = PostgreSQLRepository(_decrypt_dsn(cfg.pg_dsn))
    engine = SyncEngine(local, remote)
    st = engine.status()
    local.close()
    remote.close()

    console.print(f"Cambios pendientes: [bold]{st['pending_count']}[/bold]")
    console.print(f"Comprobado: [dim]{st['checked_at']}[/dim]")


@app.command()
def auto(
    interval: int = typer.Option(5, "--interval", "-i", help="Minutos entre sync"),
) -> None:
    """Activar sync automático en background cada N minutos."""
    _require_sync_deps()
    import time
    success(f"Sync automático activo cada {interval} minuto(s). Ctrl+C para detener.")
    try:
        while True:
            push.callback()  # type: ignore[misc]
            pull.callback()  # type: ignore[misc]
            time.sleep(interval * 60)
    except KeyboardInterrupt:
        info("Sync automático detenido.")
