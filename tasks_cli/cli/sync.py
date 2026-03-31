"""Comandos de sincronización: setup, push, pull, status, auto."""

from __future__ import annotations

import typer

from tasks_cli.cli.utils import console, error, info, success
from tasks_cli.config import get_config, save_config
from tasks_cli.i18n import t


def _require_sync_deps() -> None:
    try:
        import cryptography  # noqa: F401
        import sqlalchemy  # noqa: F401
    except ImportError:
        error(t("msg.sync_deps_missing"))
        raise typer.Exit(1)


app = typer.Typer(help=t("help.sync_app"))


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


@app.command(help=t("help.sync_setup"))
def setup(
    dsn: str = typer.Option(
        ...,
        "--dsn",
        help="DSN de SQLAlchemy: postgresql://user:pass@host/db  |  mysql+pymysql://...",
    ),
) -> None:
    _require_sync_deps()
    try:
        from tasks_cli.db.sqlalchemy_repo import SQLAlchemyRepository

        repo = SQLAlchemyRepository(dsn)
        repo.close()
    except Exception as exc:
        error(t("msg.sync_connect_failed", exc=exc))
        raise typer.Exit(1)

    cfg = get_config()
    cfg.remote_dsn = _encrypt_dsn(dsn)
    save_config(cfg)
    success(t("msg.sync_connected"))


@app.command(help=t("help.sync_push"))
def push() -> None:
    _require_sync_deps()
    cfg = get_config()
    if not cfg.remote_dsn:
        error(t("msg.sync_not_configured"))
        raise typer.Exit(1)

    engine, local, remote = _build_engine(cfg)
    with console.status(t("msg.pushing")):
        result = engine.push()
    local.close()
    remote.close()

    if result.errors:
        for e in result.errors:
            error(e)
    success(t("msg.push_done", pushed=result.pushed, conflicts=result.conflicts))


@app.command(help=t("help.sync_pull"))
def pull() -> None:
    _require_sync_deps()
    cfg = get_config()
    if not cfg.remote_dsn:
        error(t("msg.sync_not_configured"))
        raise typer.Exit(1)

    engine, local, remote = _build_engine(cfg)
    with console.status(t("msg.pulling")):
        result = engine.pull()
    local.close()
    remote.close()

    if result.errors:
        for e in result.errors:
            error(e)
    success(t("msg.pull_done", pulled=result.pulled, conflicts=result.conflicts))


@app.command(name="status", help=t("help.sync_status"))
def sync_status() -> None:
    _require_sync_deps()
    cfg = get_config()
    if not cfg.remote_dsn:
        info(t("msg.sync_not_configured_short"))
        return

    engine, local, remote = _build_engine(cfg)
    st = engine.status()
    local.close()
    remote.close()

    console.print(t("msg.sync_pending", count=f"[bold]{st['pending_count']}[/bold]"))
    console.print(t("msg.sync_checked_at", time=f"[dim]{st['checked_at']}[/dim]"))


@app.command(help=t("help.sync_auto"))
def auto(
    interval: int = typer.Option(5, "--interval", "-i", help="Minutos entre sync"),
) -> None:
    _require_sync_deps()
    import time

    cfg = get_config()
    if not cfg.remote_dsn:
        error(t("msg.sync_not_configured"))
        raise typer.Exit(1)

    success(t("msg.sync_auto_start", interval=interval))
    try:
        while True:
            engine, local, remote = _build_engine(cfg)
            try:
                engine.push()
                engine.pull()
            except Exception as exc:
                error(t("msg.sync_auto_error", exc=exc))
            finally:
                local.close()
                remote.close()
            time.sleep(interval * 60)
    except KeyboardInterrupt:
        info(t("msg.sync_auto_stopped"))
