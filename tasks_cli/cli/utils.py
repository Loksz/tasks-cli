"""Funciones de formato para output: tablas, colores, mensajes."""

from __future__ import annotations

from datetime import date

from rich.console import Console
from rich.table import Table
from rich.text import Text

from tasks_cli.models.task import Priority, Task, TaskStatus

console = Console()
_err_console = Console(stderr=True)


# Formateo de campos individuales


def fmt_priority(priority: Priority) -> str:
    symbols = {Priority.high: "!!", Priority.medium: "!", Priority.low: "·"}
    return symbols[priority]


def fmt_status(status: TaskStatus) -> str:
    icons = {
        TaskStatus.pending: "○",
        TaskStatus.in_progress: "◑",
        TaskStatus.done: "✓",
        TaskStatus.cancelled: "✗",
    }
    return icons[status]


def fmt_due(due_date: date | None) -> Text:
    if due_date is None:
        return Text("—", style="dim")
    today = date.today()
    delta = (due_date - today).days
    if delta < 0:
        return Text(due_date.strftime("%d/%m"), style="red bold")
    if delta == 0:
        return Text("hoy", style="yellow bold")
    if delta == 1:
        return Text("mañana", style="yellow")
    return Text(due_date.strftime("%d/%m"), style="default")


def fmt_title(task: Task) -> Text:
    title = task.title if len(task.title) <= 40 else task.title[:37] + "..."
    style = "bold" if task.priority == Priority.high else "default"
    if task.is_overdue:
        style = "red"
    return Text(title, style=style)


# Tablas


def tasks_table(tasks: list[Task]) -> Table:
    table = Table(show_header=True, header_style="bold cyan", box=None, pad_edge=False)
    table.add_column("ID", style="dim", width=9, no_wrap=True)
    table.add_column("Título", min_width=20, max_width=42)
    table.add_column("Proyecto", style="cyan", min_width=8)
    table.add_column("P", width=3, justify="center")
    table.add_column("Vence", width=7, justify="right")
    table.add_column("Estado", width=7, justify="center")

    for task in tasks:
        table.add_row(
            task.short_id,
            fmt_title(task),
            task.project or "",
            fmt_priority(task.priority),
            fmt_due(task.due_date),
            fmt_status(task.status),
        )
    return table


# Mensajes


def success(msg: str) -> None:
    console.print(f"[green]✓[/green] {msg}")


def error(msg: str) -> None:
    _err_console.print(f"[red]✗[/red] {msg}")


def info(msg: str) -> None:
    console.print(f"[dim]{msg}[/dim]")
