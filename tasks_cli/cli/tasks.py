"""Comandos principales: add, list, done, edit, delete, show, search y vistas."""

from __future__ import annotations

import json
from datetime import date, timedelta

import typer
from rich.panel import Panel

from tasks_cli import cache
from tasks_cli.cli.completions import (
    complete_pending_id,
    complete_project,
    complete_tag,
    complete_task_id,
)
from tasks_cli.cli.utils import (
    console,
    error,
    fmt_due,
    fmt_priority,
    fmt_status,
    success,
    tasks_table,
)
from tasks_cli.config import get_config
from tasks_cli.db.base import TaskFilters
from tasks_cli.db.sqlite import SQLiteRepository
from tasks_cli.models.task import ExportFormat, Priority, Task, TaskStatus

app = typer.Typer(help="Gestión de tareas")


def _repo() -> SQLiteRepository:
    cfg = get_config()
    return SQLiteRepository(cfg.db_path)


# ---------------------------------------------------------------------------
# CRUD Core
# ---------------------------------------------------------------------------


@app.command()
def add(
    title: str = typer.Argument(..., help="Título de la nueva tarea"),
    priority: Priority = typer.Option(None, "--priority", "-p", help="Prioridad: low | medium | high"),
    due: str | None = typer.Option(None, "--due", "-d", help="Fecha de vencimiento (YYYY-MM-DD)"),
    tag: list[str] | None = typer.Option(None, "--tag", "-t", help="Etiqueta (repetible: --tag work --tag python)", autocompletion=complete_tag),
    project: str | None = typer.Option(None, "--project", "-P", help="Nombre del proyecto", autocompletion=complete_project),
    notes: str | None = typer.Option(None, "--notes", "-n", help="Notas adicionales"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Imprime solo el ID generado (útil en scripts)"),
) -> None:
    """Crear una nueva tarea."""
    cfg = get_config()
    due_date = date.fromisoformat(due) if due else None
    task = Task(
        title=title,
        notes=notes,
        priority=priority or cfg.default_priority,
        due_date=due_date,
        tags=list(tag) if tag else [],
        project=project,
        device_id=cfg.device_id,
    )

    repo = _repo()
    repo.save(task)
    cache.update(repo)
    repo.close()

    if quiet:
        typer.echo(task.id)
    else:
        success(f"Tarea creada [{task.short_id}] — {task.title}")


@app.command(name="list")
def list_tasks(
    status: TaskStatus | None = typer.Option(None, "--status", "-s", help="Filtrar por estado: pending | in_progress | done | cancelled"),
    priority: Priority | None = typer.Option(None, "--priority", "-p", help="Filtrar por prioridad: low | medium | high"),
    tag: str | None = typer.Option(None, "--tag", "-t", help="Filtrar por etiqueta", autocompletion=complete_tag),
    project: str | None = typer.Option(None, "--project", "-P", help="Filtrar por proyecto", autocompletion=complete_project),
    due_before: str | None = typer.Option(None, "--due-before", help="Vence antes de (YYYY-MM-DD)"),
    due_after: str | None = typer.Option(None, "--due-after", help="Vence después de (YYYY-MM-DD)"),
    fmt: str | None = typer.Option(None, "--format", "-f", help="Formato de salida: table | json | ids"),
) -> None:
    """Listar tareas con filtros opcionales."""
    filters = TaskFilters(
        status=status,
        priority=priority,
        tag=tag,
        project=project,
        due_before=date.fromisoformat(due_before) if due_before else None,
        due_after=date.fromisoformat(due_after) if due_after else None,
    )
    repo = _repo()
    tasks = repo.list(filters)
    repo.close()

    if fmt == "json":
        typer.echo(json.dumps([t.model_dump(mode="json") for t in tasks], indent=2, default=str))
        return
    if fmt == "ids":
        for t in tasks:
            typer.echo(t.id)
        return

    if not tasks:
        typer.echo("No hay tareas.")
        return
    console.print(tasks_table(tasks))


@app.command()
def done(
    ids: list[str] = typer.Argument(..., help="ID(s) de tareas a completar", autocompletion=complete_pending_id),
) -> None:
    """Marcar una o varias tareas como completadas."""
    repo = _repo()
    for task_id in ids:
        task = repo.get(task_id) or _find_by_short_id(repo, task_id)
        if not task:
            error(f"Tarea no encontrada: {task_id}")
            continue
        task.mark_done()
        repo.save(task)
        success(f"[{task.short_id}] {task.title} — completada")
    cache.update(repo)
    repo.close()


@app.command()
def edit(
    task_id: str = typer.Argument(..., help="ID de la tarea a editar", autocompletion=complete_task_id),
    title: str | None = typer.Option(None, "--title", help="Nuevo título"),
    priority: Priority | None = typer.Option(None, "--priority", "-p", help="Nueva prioridad: low | medium | high"),
    due: str | None = typer.Option(None, "--due", "-d", help="Nueva fecha de vencimiento (YYYY-MM-DD)"),
    tag: list[str] | None = typer.Option(None, "--tag", "-t", help="Nuevas etiquetas (reemplaza las actuales)", autocompletion=complete_tag),
    project: str | None = typer.Option(None, "--project", "-P", help="Nuevo proyecto", autocompletion=complete_project),
    notes: str | None = typer.Option(None, "--notes", "-n", help="Nuevas notas"),
    status: TaskStatus | None = typer.Option(None, "--status", "-s", help="Nuevo estado: pending | in_progress | done | cancelled"),
) -> None:
    """Modificar campos de una tarea existente."""
    repo = _repo()
    task = repo.get(task_id) or _find_by_short_id(repo, task_id)
    if not task:
        error(f"Tarea no encontrada: {task_id}")
        repo.close()
        raise typer.Exit(1)

    if title:
        task.title = title
    if priority:
        task.priority = priority
    if due:
        task.due_date = date.fromisoformat(due)
    if tag:
        task.tags = list(tag)
    if project:
        task.project = project
    if notes:
        task.notes = notes
    if status:
        task.status = status

    task.touch()
    repo.save(task)
    cache.update(repo)
    repo.close()
    success(f"Tarea [{task.short_id}] actualizada")


@app.command()
def delete(
    task_id: str = typer.Argument(..., help="ID de la tarea a eliminar", autocompletion=complete_task_id),
    force: bool = typer.Option(False, "--force", "-f", help="Omitir confirmación interactiva"),
) -> None:
    """Eliminar una tarea de forma permanente."""
    repo = _repo()
    task = repo.get(task_id) or _find_by_short_id(repo, task_id)
    if not task:
        error(f"Tarea no encontrada: {task_id}")
        repo.close()
        raise typer.Exit(1)

    if not force:
        typer.confirm(f"¿Eliminar '{task.title}'?", abort=True)

    repo.delete(task.id)
    cache.update(repo)
    repo.close()
    success(f"Tarea [{task.short_id}] eliminada")


@app.command()
def show(
    task_id: str = typer.Argument(..., help="ID de la tarea", autocompletion=complete_task_id),
) -> None:
    """Ver detalle completo de una tarea."""
    repo = _repo()
    task = repo.get(task_id) or _find_by_short_id(repo, task_id)
    repo.close()

    if not task:
        error(f"Tarea no encontrada: {task_id}")
        raise typer.Exit(1)

    lines = [
        f"[bold]{task.title}[/bold]",
        f"ID: [dim]{task.id}[/dim]",
        f"Estado: {fmt_status(task.status)} {task.status.value}",
        f"Prioridad: {fmt_priority(task.priority)} {task.priority.value}",
        f"Proyecto: {task.project or '—'}",
        f"Etiquetas: {', '.join(task.tags) or '—'}",
        f"Vence: {fmt_due(task.due_date)}",
        f"Creada: {task.created_at.strftime('%d/%m/%Y %H:%M')} UTC",
        f"Modificada: {task.updated_at.strftime('%d/%m/%Y %H:%M')} UTC",
    ]
    if task.notes:
        lines.append(f"\n[dim]Notas:[/dim] {task.notes}")

    console.print(Panel("\n".join(lines), title="Detalle de tarea"))


@app.command()
def search(
    query: str = typer.Argument(..., help="Texto a buscar en título y notas"),
) -> None:
    """Búsqueda de texto en títulos y notas."""
    repo = _repo()
    results = repo.search(query)
    repo.close()

    if not results:
        typer.echo("Sin resultados.")
        return
    console.print(tasks_table(results))


# ---------------------------------------------------------------------------
# Vistas rápidas
# ---------------------------------------------------------------------------


@app.command()
def today() -> None:
    """Tareas con vencimiento hoy o vencidas sin completar."""
    repo = _repo()
    all_tasks = repo.list(TaskFilters(status=TaskStatus.pending))
    repo.close()

    today_date = date.today()
    relevant = [t for t in all_tasks if t.due_date and t.due_date <= today_date]
    if not relevant:
        typer.echo("Sin tareas para hoy.")
        return
    console.print(tasks_table(relevant))


@app.command()
def overdue() -> None:
    """Listar todas las tareas vencidas."""
    repo = _repo()
    all_tasks = repo.list(TaskFilters(status=TaskStatus.pending))
    repo.close()

    overdue_tasks = sorted(
        [t for t in all_tasks if t.is_overdue],
        key=lambda t: t.due_date or date.today(),
    )
    if not overdue_tasks:
        typer.echo("Sin tareas vencidas.")
        return
    console.print(tasks_table(overdue_tasks))


@app.command()
def upcoming(
    days: int = typer.Option(7, "--days", "-d", help="Número de días hacia adelante (default: 7)"),
) -> None:
    """Tareas con vencimiento en los próximos N días."""
    today_date = date.today()
    limit = today_date + timedelta(days=days)

    repo = _repo()
    tasks = repo.list(
        TaskFilters(
            status=TaskStatus.pending,
            due_after=today_date,
            due_before=limit,
        )
    )
    repo.close()

    if not tasks:
        typer.echo(f"Sin tareas en los próximos {days} días.")
        return
    console.print(tasks_table(tasks))


@app.command()
def projects() -> None:
    """Listar proyectos activos con conteo de tareas."""
    repo = _repo()
    all_tasks = repo.list()
    repo.close()

    from collections import defaultdict
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"pending": 0, "done": 0})
    for t in all_tasks:
        key = t.project or "(sin proyecto)"
        if t.status == TaskStatus.done:
            counts[key]["done"] += 1
        else:
            counts[key]["pending"] += 1

    for proj, c in sorted(counts.items()):
        console.print(f"[cyan]{proj}[/cyan]  pendientes: {c['pending']}  completadas: {c['done']}")


@app.command()
def tags() -> None:
    """Listar etiquetas con conteo de tareas."""
    repo = _repo()
    all_tasks = repo.list()
    repo.close()

    from collections import Counter
    counter: Counter[str] = Counter()
    for t in all_tasks:
        for tag in t.tags:
            counter[tag] += 1

    for tag, count in counter.most_common():
        console.print(f"[yellow]{tag}[/yellow]  {count} tarea(s)")


@app.command()
def stats() -> None:
    """Resumen estadístico de tareas."""
    repo = _repo()
    all_tasks = repo.list()
    repo.close()

    total = len(all_tasks)
    done = sum(1 for t in all_tasks if t.status == TaskStatus.done)
    pending = sum(1 for t in all_tasks if t.status == TaskStatus.pending)
    overdue_count = sum(1 for t in all_tasks if t.is_overdue)
    rate = (done / total * 100) if total else 0

    console.print(f"Total: [bold]{total}[/bold]  Completadas: [green]{done}[/green]  "
                  f"Pendientes: [yellow]{pending}[/yellow]  Vencidas: [red]{overdue_count}[/red]  "
                  f"Tasa: [bold]{rate:.1f}%[/bold]")


# ---------------------------------------------------------------------------
# Exportación / Importación
# ---------------------------------------------------------------------------


@app.command(name="export")
def export_tasks(
    fmt: ExportFormat = typer.Option(ExportFormat.json, "--format", "-f", help="Formato de salida: json | csv | markdown"),
    output: str | None = typer.Option(None, "--output", "-o", help="Ruta del archivo de destino"),
    status_filter: TaskStatus | None = typer.Option(None, "--filter", help="Exportar solo tareas con este estado"),
) -> None:
    """Exportar tareas a JSON, CSV o Markdown."""
    repo = _repo()
    tasks = repo.list(TaskFilters(status=status_filter) if status_filter else None)
    repo.close()

    if fmt == ExportFormat.json:
        content = json.dumps([t.model_dump(mode="json") for t in tasks], indent=2, default=str)
        ext = "json"
    elif fmt == ExportFormat.csv:
        import csv
        import io
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "title", "status", "priority", "project", "due_date", "tags"])
        for t in tasks:
            writer.writerow([t.id, t.title, t.status.value, t.priority.value,
                             t.project or "", t.due_date or "", ",".join(t.tags)])
        content = buf.getvalue()
        ext = "csv"
    else:
        lines = ["# Tareas exportadas\n"]
        for t in tasks:
            status_char = "x" if t.status == TaskStatus.done else " "
            lines.append(f"- [{status_char}] **{t.title}** `{t.short_id}`")
        content = "\n".join(lines)
        ext = "md"

    filename = output or f"tasks_export.{ext}"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    success(f"Exportado a {filename} ({len(tasks)} tareas)")


@app.command(name="import")
def import_tasks(
    file: str = typer.Option(..., "--file", "-f", help="Ruta al archivo JSON o CSV a importar"),
) -> None:
    """Importar tareas desde archivo JSON o CSV."""
    repo = _repo()
    imported = 0
    skipped = 0

    with open(file, encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        if repo.get(item.get("id", "")):
            skipped += 1
            continue
        task = Task.model_validate(item)
        repo.save(task)
        imported += 1

    if imported:
        cache.update(repo)
    repo.close()
    success(f"Importadas: {imported}  Duplicados omitidos: {skipped}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_by_short_id(repo: SQLiteRepository, short_id: str) -> Task | None:
    """Busca una tarea por prefijo de ID usando la base de datos."""
    return repo.get_by_prefix(short_id)
