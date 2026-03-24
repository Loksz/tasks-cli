"""App Typer raíz — registra todos los grupos de comandos."""

from __future__ import annotations

import typer

import tasks_cli.cli.sync as sync_commands
import tasks_cli.cli.tasks as tasks_commands
from tasks_cli.cli.completions import complete_config_key
from tasks_cli.cli.utils import console
from tasks_cli.config import get_config, set_value

app = typer.Typer(
    name="tasks",
    help="TASKS — CLI de Gestión de Tareas con Sincronización",
    no_args_is_help=True,
)

# Registrar subgrupos
app.add_typer(tasks_commands.app, name=None)   # comandos al nivel raíz
app.add_typer(sync_commands.app, name="sync")  # tasks sync <subcomando>


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

config_app = typer.Typer(help="Ver y modificar la configuración del usuario")
app.add_typer(config_app, name="config")


@config_app.command(name="get")
def config_get(
    key: str = typer.Argument(None, help="Nombre del campo a consultar (omitir para ver todos)", autocompletion=complete_config_key),
) -> None:
    """Ver valor(es) de configuración."""
    cfg = get_config()
    data = cfg.model_dump()
    if key:
        if key not in data:
            typer.echo(f"Campo desconocido: {key}", err=True)
            raise typer.Exit(1)
        console.print(f"{key} = {data[key]}")
    else:
        for k, v in data.items():
            console.print(f"{k} = [dim]{v}[/dim]")


@config_app.command(name="set")
def config_set(
    key: str = typer.Argument(..., help="Nombre del campo a modificar", autocompletion=complete_config_key),
    value: str = typer.Argument(..., help="Nuevo valor"),
) -> None:
    """Establecer un valor de configuración persistente."""
    try:
        set_value(key, value)
        console.print(f"[green]✓[/green] {key} = {value}")
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
