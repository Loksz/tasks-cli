"""Comandos de sincronización: setup, push, pull, status, auto."""

from __future__ import annotations

import typer

from tasks_cli.cli.utils import console, error, info, success
from tasks_cli.config import get_config, save_config

_SYNC_DEPS_MSG = (
    "Las dependencias de sincronización no están instaladas.\n"
    r"Instálalas con:  pip install 'tasks-cli[sync]'"
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

    return Fernet(_key_path().read_bytes()).decrypt(token.encode()).decode()


def _key_path():
    from pathlib import Path

    return Path.home() / ".tasks" / ".sync.key"


def _build_engine(cfg):
    from tasks_cli.db.sqlalchemy_repo import SQLAlchemyRepository
    from tasks_cli.db.sqlite import SQLiteRepository
    from tasks_cli.sync.engine import SyncEngine

    local = SQLiteRepository(cfg.db_path)
    remote = SQLAlchemyRepository(_decrypt_dsn(cfg.remote_dsn))
    return SyncEngine(local, remote), local, remote


@app.command()
def setup(
    dsn: str = typer.Option(
        ...,
        "--dsn",
        help="DSN de SQLAlchemy: postgresql://user:pass@host/db  |  mysql+pymysql://...",
    ),
) -> None:
    """Configurar conexión a una base de datos remota y guardar credenciales cifradas."""
    _require_sync_deps()
    try:
        from tasks_cli.db.sqlalchemy_repo import SQLAlchemyRepository

        repo = SQLAlchemyRepository(dsn)
        repo.close()
    except Exception as exc:
        error(f"No se pudo conectar: {exc}")
        raise typer.Exit(1)

    cfg = get_config()
    cfg.remote_dsn = _encrypt_dsn(dsn)
    save_config(cfg)
    success("Conexión configurada y credenciales cifradas.")


@app.command()
def push() -> None:
    """Enviar cambios locales pendientes al servidor remoto."""
    _require_sync_deps()
    cfg = get_config()
    if not cfg.remote_dsn:
        error("Sync no configurado. Ejecuta: tasks sync setup --dsn <DSN>")
        raise typer.Exit(1)

    engine, local, remote = _build_engine(cfg)
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
    if not cfg.remote_dsn:
        error("Sync no configurado. Ejecuta: tasks sync setup --dsn <DSN>")
        raise typer.Exit(1)

    engine, local, remote = _build_engine(cfg)
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
    if not cfg.remote_dsn:
        info("Sync no configurado.")
        return

    engine, local, remote = _build_engine(cfg)
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

    cfg = get_config()
    if not cfg.remote_dsn:
        error("Sync no configurado. Ejecuta: tasks sync setup --dsn <DSN>")
        raise typer.Exit(1)

    success(f"Sync automático activo cada {interval} minuto(s). Ctrl+C para detener.")
    try:
        while True:
            engine, local, remote = _build_engine(cfg)
            try:
                engine.push()
                engine.pull()
            except Exception as exc:
                error(f"Error durante sync: {exc}")
            finally:
                local.close()
                remote.close()
            time.sleep(interval * 60)
    except KeyboardInterrupt:
        info("Sync automático detenido.")
