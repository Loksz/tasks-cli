"""App Typer raíz — registra todos los grupos de comandos."""

from __future__ import annotations

import typer

import tasks_cli.cli.sync as sync_commands
import tasks_cli.cli.tasks as tasks_commands
from tasks_cli.cli.completions import complete_config_key
from tasks_cli.cli.utils import console
from tasks_cli.config import get_config, set_value
from tasks_cli.i18n import t

app = typer.Typer(
    name="tasks",
    help=t("help.app"),
    no_args_is_help=True,
)

# Registrar subgrupos
app.add_typer(tasks_commands.app, name=None)   # comandos al nivel raíz
app.add_typer(sync_commands.app, name="sync")  # task sync <subcomando>


# ---------------------------------------------------------------------------
# TUI
# ---------------------------------------------------------------------------


@app.command(help=t("help.ui"))
def ui() -> None:
    try:
        from tasks_cli.tui.app import TaskApp
    except ImportError:
        typer.echo(t("msg.install_ui"), err=True)
        raise typer.Exit(1)
    TaskApp().run()


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

config_app = typer.Typer(help=t("help.config_app"))
app.add_typer(config_app, name="config")


@config_app.command(name="get", help=t("help.config_get"))
def config_get(
    key: str = typer.Argument(None, help="Campo a consultar (omitir para ver todos)", autocompletion=complete_config_key),
) -> None:
    cfg = get_config()
    data = cfg.model_dump()
    if key:
        if key not in data:
            typer.echo(t("msg.config_unknown_key", key=key), err=True)
            raise typer.Exit(1)
        console.print(f"{key} = {data[key]}")
    else:
        for k, v in data.items():
            console.print(f"{k} = [dim]{v}[/dim]")


@config_app.command(name="set", help=t("help.config_set"))
def config_set(
    key: str = typer.Argument(..., help="Campo a modificar", autocompletion=complete_config_key),
    value: str = typer.Argument(..., help="Nuevo valor"),
) -> None:
    cfg = get_config()
    if key not in cfg.model_fields:
        typer.echo(t("msg.config_unknown_key", key=key), err=True)
        raise typer.Exit(1)
    try:
        set_value(key, value)
        console.print(f"[green]✓[/green] {key} = {value}")
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
