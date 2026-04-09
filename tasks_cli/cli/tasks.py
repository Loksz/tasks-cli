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
from tasks_cli.i18n import t
from tasks_cli.models.task import ExportFormat, Priority, Task, TaskStatus

app = typer.Typer(help=t("help.tasks_app"))


def _repo() -> SQLiteRepository:
    cfg = get_config()
    return SQLiteRepository(cfg.db_path)


# ---------------------------------------------------------------------------
# CRUD Core
# ---------------------------------------------------------------------------


@app.command(help=t("help.add"))
def add(
    title: str = typer.Argument(..., help="Título de la nueva tarea"),
    priority: Priority = typer.Option(None, "--priority", "-p", help="Prioridad: low | medium | high"),
    due: str | None = typer.Option(None, "--due", "-d", help="Fecha de vencimiento (YYYY-MM-DD)"),
    tag: list[str] | None = typer.Option(None, "--tag", "-t", help="Etiqueta (repetible: --tag work --tag python)", autocompletion=complete_tag),
    project: str | None = typer.Option(None, "--project", "-P", help="Nombre del proyecto", autocompletion=complete_project),
    notes: str | None = typer.Option(None, "--notes", "-n", help="Notas adicionales"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Imprime solo el ID generado (útil en scripts)"),
) -> None:
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
        success(t("msg.task_created", id=task.short_id, title=task.title))


@app.command(name="list", help=t("help.list"))
def list_tasks(
    status: TaskStatus | None = typer.Option(None, "--status", "-s", help="Filtrar por estado: pending | in_progress | done | cancelled"),
    priority: Priority | None = typer.Option(None, "--priority", "-p", help="Filtrar por prioridad: low | medium | high"),
    tag: str | None = typer.Option(None, "--tag", "-t", help="Filtrar por etiqueta", autocompletion=complete_tag),
    project: str | None = typer.Option(None, "--project", "-P", help="Filtrar por proyecto", autocompletion=complete_project),
    due_before: str | None = typer.Option(None, "--due-before", help="Vence antes de (YYYY-MM-DD)"),
    due_after: str | None = typer.Option(None, "--due-after", help="Vence después de (YYYY-MM-DD)"),
    fmt: str | None = typer.Option(None, "--format", "-f", help="Formato de salida: table | json | ids"),
) -> None:
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
        typer.echo(json.dumps([t_.model_dump(mode="json") for t_ in tasks], indent=2, default=str))
        return
    if fmt == "ids":
        for t_ in tasks:
            typer.echo(t_.id)
        return

    if not tasks:
        typer.echo(t("msg.no_tasks"))
        return
    console.print(tasks_table(tasks))


@app.command(help=t("help.done"))
def done(
    ids: list[str] = typer.Argument(..., help="ID(s) de tareas a completar", autocompletion=complete_pending_id),
) -> None:
    repo = _repo()
    for task_id in ids:
        task = repo.get(task_id) or _find_by_short_id(repo, task_id)
        if not task:
            error(t("msg.task_not_found", id=task_id))
            continue
        task.mark_done()
        repo.save(task)
        success(t("msg.task_done", id=task.short_id, title=task.title))
    cache.update(repo)
    repo.close()


@app.command(help=t("help.edit"))
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
    repo = _repo()
    task = repo.get(task_id) or _find_by_short_id(repo, task_id)
    if not task:
        error(t("msg.task_not_found", id=task_id))
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
    success(t("msg.task_updated", id=task.short_id))


@app.command(help=t("help.delete"))
def delete(
    task_id: str = typer.Argument(..., help="ID de la tarea a eliminar", autocompletion=complete_task_id),
    force: bool = typer.Option(False, "--force", "-f", help="Omitir confirmación interactiva"),
) -> None:
    repo = _repo()
    task = repo.get(task_id) or _find_by_short_id(repo, task_id)
    if not task:
        error(t("msg.task_not_found", id=task_id))
        repo.close()
        raise typer.Exit(1)

    if not force:
        typer.confirm(t("msg.delete_confirm", title=task.title), abort=True)

    repo.delete(task.id)
    cache.update(repo)
    repo.close()
    success(t("msg.task_deleted", id=task.short_id))


@app.command(help=t("help.show"))
def show(
    task_id: str = typer.Argument(..., help="ID de la tarea", autocompletion=complete_task_id),
) -> None:
    repo = _repo()
    task = repo.get(task_id) or _find_by_short_id(repo, task_id)
    repo.close()

    if not task:
        error(t("msg.task_not_found", id=task_id))
        raise typer.Exit(1)

    lines = [
        f"[bold]{task.title}[/bold]",
        f"ID: [dim]{task.id}[/dim]",
        f"{t('show.status')}: {fmt_status(task.status)} {task.status.value}",
        f"{t('show.priority')}: {fmt_priority(task.priority)} {task.priority.value}",
        f"{t('show.project')}: {task.project or '-'}",
        f"{t('show.tags')}: {', '.join(task.tags) or '-'}",
        f"{t('show.due')}: {fmt_due(task.due_date)}",
        f"{t('show.created')}: {task.created_at.strftime('%d/%m/%Y %H:%M')} UTC",
        f"{t('show.modified')}: {task.updated_at.strftime('%d/%m/%Y %H:%M')} UTC",
    ]
    if task.notes:
        lines.append(f"\n[dim]{t('show.notes')}:[/dim] {task.notes}")

    console.print(Panel("\n".join(lines), title=t("show.panel_title")))


@app.command(help=t("help.search"))
def search(
    query: str = typer.Argument(..., help="Texto a buscar en título y notas"),
) -> None:
    repo = _repo()
    results = repo.search(query)
    repo.close()

    if not results:
        typer.echo(t("msg.no_results"))
        return
    console.print(tasks_table(results))


# ---------------------------------------------------------------------------
# Vistas rápidas
# ---------------------------------------------------------------------------


@app.command(help=t("help.today"))
def today() -> None:
    repo = _repo()
    all_tasks = repo.list(TaskFilters(status=TaskStatus.pending))
    repo.close()

    today_date = date.today()
    relevant = [t_ for t_ in all_tasks if t_.due_date and t_.due_date <= today_date]
    if not relevant:
        typer.echo(t("msg.no_today"))
        return
    console.print(tasks_table(relevant))


@app.command(help=t("help.overdue"))
def overdue() -> None:
    repo = _repo()
    all_tasks = repo.list(TaskFilters(status=TaskStatus.pending))
    repo.close()

    overdue_tasks = sorted(
        [t_ for t_ in all_tasks if t_.is_overdue],
        key=lambda t_: t_.due_date or date.today(),
    )
    if not overdue_tasks:
        typer.echo(t("msg.no_overdue"))
        return
    console.print(tasks_table(overdue_tasks))


@app.command(help=t("help.upcoming"))
def upcoming(
    days: int = typer.Option(7, "--days", "-d", help="Número de días hacia adelante (default: 7)"),
) -> None:
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
        typer.echo(t("msg.no_upcoming", days=days))
        return
    console.print(tasks_table(tasks))


@app.command(help=t("help.projects"))
def projects() -> None:
    repo = _repo()
    all_tasks = repo.list()
    repo.close()

    from collections import defaultdict

    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"pending": 0, "done": 0})
    for t_ in all_tasks:
        key = t_.project or t("lbl.no_project")
        if t_.status == TaskStatus.done:
            counts[key]["done"] += 1
        else:
            counts[key]["pending"] += 1

    for proj, c in sorted(counts.items()):
        console.print(f"[cyan]{proj}[/cyan]  {t('lbl.pending')}: {c['pending']}  {t('lbl.done')}: {c['done']}")


@app.command(help=t("help.tags"))
def tags() -> None:
    repo = _repo()
    all_tasks = repo.list()
    repo.close()

    from collections import Counter

    counter: Counter[str] = Counter()
    for t_ in all_tasks:
        for tag in t_.tags:
            counter[tag] += 1

    for tag, count in counter.most_common():
        console.print(f"[yellow]{tag}[/yellow]  {count} {t('lbl.task_count')}")


@app.command(help=t("help.stats"))
def stats() -> None:
    repo = _repo()
    all_tasks = repo.list()
    repo.close()

    total = len(all_tasks)
    done_count = sum(1 for t_ in all_tasks if t_.status == TaskStatus.done)
    pending_count = sum(1 for t_ in all_tasks if t_.status == TaskStatus.pending)
    overdue_count = sum(1 for t_ in all_tasks if t_.is_overdue)
    rate = (done_count / total * 100) if total else 0

    console.print(
        f"{t('lbl.total')}: [bold]{total}[/bold]  "
        f"{t('lbl.completed')}: [green]{done_count}[/green]  "
        f"{t('lbl.pending')}: [yellow]{pending_count}[/yellow]  "
        f"{t('lbl.overdue')}: [red]{overdue_count}[/red]  "
        f"{t('lbl.rate')}: [bold]{rate:.1f}%[/bold]"
    )


# ---------------------------------------------------------------------------
# Exportación / Importación
# ---------------------------------------------------------------------------


@app.command(name="export", help=t("help.export"))
def export_tasks(
    fmt: ExportFormat = typer.Option(ExportFormat.json, "--format", "-f", help="Formato de salida: json | csv | markdown"),
    output: str | None = typer.Option(None, "--output", "-o", help="Ruta del archivo de destino"),
    status_filter: TaskStatus | None = typer.Option(None, "--filter", help="Exportar solo tareas con este estado"),
) -> None:
    repo = _repo()
    tasks = repo.list(TaskFilters(status=status_filter) if status_filter else None)
    repo.close()

    if fmt == ExportFormat.json:
        content = json.dumps([t_.model_dump(mode="json") for t_ in tasks], indent=2, default=str)
        ext = "json"
    elif fmt == ExportFormat.csv:
        import csv
        import io

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "title", "status", "priority", "project", "due_date", "tags"])
        for t_ in tasks:
            writer.writerow([t_.id, t_.title, t_.status.value, t_.priority.value,
                             t_.project or "", t_.due_date or "", ",".join(t_.tags)])
        content = buf.getvalue()
        ext = "csv"
    else:
        lines = ["# Tasks export\n"]
        for t_ in tasks:
            status_char = "x" if t_.status == TaskStatus.done else " "
            lines.append(f"- [{status_char}] **{t_.title}** `{t_.short_id}`")
        content = "\n".join(lines)
        ext = "md"

    filename = output or f"tasks_export.{ext}"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    success(t("msg.exported", file=filename, count=len(tasks)))


@app.command(name="import", help=t("help.import"))
def import_tasks(
    file: str = typer.Option(..., "--file", "-f", help="Ruta al archivo JSON o CSV a importar"),
) -> None:
    repo = _repo()
    imported = 0
    skipped = 0

    try:
        with open(file, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        error(t("msg.file_read_error", exc=exc))
        repo.close()
        raise typer.Exit(1)

    if not isinstance(data, list):
        error(t("msg.json_not_list"))
        repo.close()
        raise typer.Exit(1)

    for item in data:
        if not isinstance(item, dict):
            skipped += 1
            continue
        if repo.get(item.get("id", "")):
            skipped += 1
            continue
        try:
            task = Task.model_validate(item)
        except Exception:
            skipped += 1
            continue
        repo.save(task)
        imported += 1

    if imported:
        cache.update(repo)
    repo.close()
    success(t("msg.imported", imported=imported, skipped=skipped))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_by_short_id(repo: SQLiteRepository, short_id: str) -> Task | None:
    """Busca una tarea por prefijo de ID usando la base de datos."""
    return repo.get_by_prefix(short_id)
