"""TUI interactiva para tasks-cli — navegable con flechas del teclado."""

from __future__ import annotations

from datetime import date

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.validation import ValidationResult, Validator
from textual.widget import Widget
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Rule,
    SelectionList,
    Static,
)
from textual.widgets.selection_list import Selection

from tasks_cli.config import get_config
from tasks_cli.db.sqlite import SQLiteRepository
from tasks_cli.i18n import t
from tasks_cli.models.task import Priority, Task, TaskStatus

# ---------------------------------------------------------------------------
# Helpers de display
# ---------------------------------------------------------------------------

def _priority_label() -> dict:
    return {
        Priority.high: t("tui.priority.high"),
        Priority.medium: t("tui.priority.medium"),
        Priority.low: t("tui.priority.low"),
    }


_PRIORITY_COLOR = {Priority.high: "red", Priority.medium: "yellow", Priority.low: "green"}


def _status_label() -> dict:
    return {
        TaskStatus.pending: t("tui.status.pending"),
        TaskStatus.in_progress: t("tui.status.in_progress"),
        TaskStatus.done: t("tui.status.done"),
        TaskStatus.cancelled: t("tui.status.cancelled"),
    }


_STATUS_COLOR = {
    TaskStatus.pending: "yellow",
    TaskStatus.in_progress: "cyan",
    TaskStatus.done: "green",
    TaskStatus.cancelled: "dim",
}


def _sync_label() -> dict:
    return {
        "local": (t("tui.sync.local"), "dim"),
        "pending": (t("tui.sync.pending"), "yellow"),
        "synced": (t("tui.sync.synced"), "green"),
        "conflict": (t("tui.sync.conflict"), "red"),
    }

_PRIORITIES = [Priority.low, Priority.medium, Priority.high]
_STATUSES = [TaskStatus.pending, TaskStatus.in_progress, TaskStatus.cancelled]


def _fmt_due(d: date | None) -> str:
    if d is None:
        return "-"
    delta = (d - date.today()).days
    if delta < 0:
        return t("tui.due.overdue", days=abs(delta))
    if delta == 0:
        return t("tui.due.today")
    if delta == 1:
        return t("tui.due.tomorrow")
    return d.strftime("%d/%m/%Y")


def _due_urgency(d: date | None, status: TaskStatus) -> str:
    if d is None or status in (TaskStatus.done, TaskStatus.cancelled):
        return ""
    delta = (d - date.today()).days
    if delta < 0:
        return t("tui.urgency.overdue", days=abs(delta))
    if delta == 0:
        return t("tui.urgency.today")
    if delta <= 2:
        return t("tui.urgency.soon", days=delta)
    return ""


def _detail_markup(task: Task, width: int = 50) -> str:
    """Genera el markup de detalle adaptado al ancho disponible del panel."""
    p_color = _PRIORITY_COLOR[task.priority]
    s_color = _STATUS_COLOR[task.status]
    s_label = _status_label()[task.status]
    p_label = _priority_label()[task.priority]
    urgency = _due_urgency(task.due_date, task.status)
    sync_text, sync_color = _sync_label().get(task.sync_status.value, (t("tui.sync.local"), "dim"))
    due_str = _fmt_due(task.due_date)
    sep = "[dim]" + "─" * min(width, 60) + "[/dim]"

    lines: list[str] = []

    # Título como headline principal
    lines += [f"[bold]{task.title}[/bold]", ""]

    # Estado como dot coloreado + urgencia opcional
    lines.append(f"[{s_color}]● {s_label.lower()}[/{s_color}]")
    if urgency:
        lines.append(urgency)

    lines += ["", sep, ""]

    # Meta: campos en lista alineada
    lbl_w = 11
    project_str = task.project if task.project else "[dim]-[/dim]"

    if width >= 36:
        lines += [
            f"[dim]{t('tui.detail.priority'):<{lbl_w}}[/dim][{p_color}]{p_label}[/{p_color}]",
            f"[dim]{t('tui.detail.due'):<{lbl_w}}[/dim]{due_str}",
            f"[dim]{t('tui.detail.project'):<{lbl_w}}[/dim]{project_str}",
        ]
    else:
        lines += [
            f"[dim]{t('tui.detail.priority')}[/dim]  [{p_color}]{p_label}[/{p_color}]",
            f"[dim]{t('tui.detail.due')}[/dim]  {due_str}",
            f"[dim]{t('tui.detail.project')}[/dim]  {project_str}",
        ]

    # Tags estilo terminal: #tag
    lines.append("")
    if task.tags:
        lines.append("  ".join(f"[dim]#[/dim][cyan]{tag}[/cyan]" for tag in task.tags))
    else:
        lines.append(f"[dim]{t('tui.detail.no_tags')}[/dim]")

    lines += ["", sep]

    # Notas (solo si existen)
    if task.notes:
        lines += [
            "",
            f"[dim italic]{t('tui.detail.notes')}[/dim italic]",
            "",
            task.notes,
            "",
            sep,
        ]

    # Footer dim: timestamps + sync + short_id
    lbl_created = t("tui.detail.created")
    lbl_modified = t("tui.detail.modified")
    lbl_completed = t("tui.detail.completed")

    lines += [
        "",
        f"[dim]{lbl_created:<11}{task.created_at.strftime('%d/%m/%Y  %H:%M')}[/dim]",
        f"[dim]{lbl_modified:<11}{task.updated_at.strftime('%d/%m/%Y  %H:%M')}[/dim]",
    ]
    if task.completed_at:
        lines.append(
            f"[dim]{lbl_completed:<11}{task.completed_at.strftime('%d/%m/%Y  %H:%M')}[/dim]"
        )

    lines += [
        "",
        f"[dim]sync  [{sync_color}]{sync_text}[/{sync_color}]    {task.short_id}[/dim]",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

APP_CSS = """
Screen { layout: vertical; }

#body {
    layout: horizontal;
    height: 1fr;
}

#left {
    width: 1fr;
    border-right: solid $accent;
}

#right {
    width: 1fr;
}

DataTable { height: 1fr; }

/* --- Panel de detalle --- */

TaskDetail {
    padding: 1 2;
    height: auto;
}

/* --- Formulario embebido --- */

TaskForm {
    display: none;
    height: 100%;
    layout: vertical;
}

TaskForm.visible {
    display: block;
}

#form-heading {
    text-style: bold;
    border-left: thick $accent;
    background: $boost;
    padding: 1 2;
    height: auto;
}

#form-scroll {
    height: 1fr;
    padding: 1 2 0 2;
}

/* Pie fijo */

#form-footer {
    height: auto;
    padding: 0 2 1 2;
    border-top: solid $panel;
}

#form-error {
    color: $error;
    height: 1;
    margin-top: 1;
}

#form-buttons {
    height: 3;
    margin-top: 1;
    align-horizontal: left;
}

Button { margin-right: 1; }

/* Labels */

.field-label {
    color: $text-muted;
    text-style: italic;
    margin-top: 1;
    margin-bottom: 0;
}

/* Separador entre grupos de campos */

Rule {
    color: $panel;
    margin: 1 0;
}

/* Filas de dos columnas */

.form-row {
    layout: horizontal;
    height: auto;
}

.row-col-left {
    width: 1fr;
    height: auto;
    padding-right: 1;
}

.row-col-right {
    width: 1fr;
    height: auto;
    padding-left: 1;
}

/* Tags + Priority */

.tags-col {
    width: 2fr;
    height: auto;
    padding-right: 1;
}

.priority-col {
    width: 1fr;
    height: auto;
    padding-left: 1;
}

/* Estado (solo edición) */

#status-section {
    height: auto;
}

/* DateInput con retroalimentación visual */

DateInput.-invalid {
    border: tall $error 60%;
}

DateInput.-valid {
    border: tall $success 40%;
}

/* Lista de tags */

#tags-list {
    height: 3;
    border: solid $panel;
    margin-bottom: 1;
}

RadioSet {
    background: transparent;
    border: none;
    height: auto;
    padding: 0;
}

/* Modo angosto: una sola columna */

TaskForm.narrow .form-row {
    layout: vertical;
}

TaskForm.narrow .row-col-left,
TaskForm.narrow .row-col-right,
TaskForm.narrow .tags-col,
TaskForm.narrow .priority-col {
    width: 1fr;
    padding-right: 0;
    padding-left: 0;
}
"""


# ---------------------------------------------------------------------------
# Validador y widget de fecha
# ---------------------------------------------------------------------------


class _DateValidator(Validator):
    def validate(self, value: str) -> ValidationResult:
        if not value:
            return self.success()
        if len(value) < 10:
            return self.failure(t("tui.form.err_date_incomplete"))
        try:
            date.fromisoformat(value)
            return self.success()
        except ValueError:
            return self.failure(t("tui.form.err_date_format"))


class DateInput(Input):
    """Input de fecha: solo acepta dígitos, auto-inserta guiones y valida en tiempo real."""

    _busy: bool = False

    def __init__(self, **kwargs) -> None:
        super().__init__(
            placeholder="YYYY-MM-DD",
            max_length=10,
            validators=[_DateValidator()],
            validate_on=["changed"],
            **kwargs,
        )

    @staticmethod
    def _fmt_digits(digits: str) -> str:
        d = digits[:8]
        if len(d) <= 4:
            return d
        if len(d) <= 6:
            return f"{d[:4]}-{d[4:]}"
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"

    def _on_key(self, event: events.Key) -> None:
        if not event.is_printable:
            return  # backspace, flechas, tab → Input los maneja normal

        if not event.character or not event.character.isdigit():
            event.prevent_default()  # bloquear letras y simbolos
            return

        # Dígito: prevenir inserción por defecto y hacer el formateo aquí
        event.prevent_default()
        digits = "".join(c for c in self.value if c.isdigit())
        if len(digits) >= 8:
            return
        formatted = self._fmt_digits(digits + event.character)
        self._busy = True
        self.value = formatted
        self.cursor_position = len(formatted)
        self._busy = False

    def watch_value(self, value: str) -> None:
        """Normaliza valores pegados (paste) que no pasan por _on_key."""
        if self._busy:
            return
        digits = "".join(c for c in value if c.isdigit())
        formatted = self._fmt_digits(digits)
        if formatted != value:
            self._busy = True
            self.value = formatted
            self.cursor_position = len(formatted)
            self._busy = False


# ---------------------------------------------------------------------------
# Helpers de UI
# ---------------------------------------------------------------------------


def _select_radio(radio_set: RadioSet, index: int) -> None:
    """Activa el RadioButton en la posición `index` dentro de un RadioSet."""
    buttons = list(radio_set.query(RadioButton))
    if 0 <= index < len(buttons):
        buttons[index].value = True


# ---------------------------------------------------------------------------
# Widget de detalle — adapta el renderizado al ancho del panel
# ---------------------------------------------------------------------------


class TaskDetail(Static):
    """Panel de detalle de una tarea. Se redibuja cuando cambia el tamaño del panel."""

    def __init__(self) -> None:
        super().__init__(f"[dim]{t('tui.select_task')}[/dim]")
        self._current_task: Task | None = None

    def show_task(self, task: Task | None) -> None:
        self._current_task = task
        self._redraw()

    def on_resize(self, event: events.Resize) -> None:
        self._redraw(event.size.width)

    def _redraw(self, width: int | None = None) -> None:
        w = width or (self.size.width if self.size.width > 0 else 50)
        content_w = max(10, w - 4)  # restar padding horizontal (1 2 → 4 cols)
        if self._current_task is None:
            self.update(f"[dim]{t('tui.select_task')}[/dim]")
        else:
            self.update(_detail_markup(self._current_task, content_w))


# ---------------------------------------------------------------------------
# Widget de etiquetas
# ---------------------------------------------------------------------------


class TagInput(Input):
    """Input especializado que notifica cuando se presiona Backspace en vacío."""

    class BackspaceOnEmpty(Message):
        pass

    def _on_key(self, event: events.Key) -> None:
        if event.key == "backspace" and not self.value:
            event.prevent_default()
            self.post_message(TagInput.BackspaceOnEmpty())


class TagsField(Widget):
    """Campo de etiquetas con lista seleccionable y campo para crear tags nuevos.

    - La lista muestra todos los tags conocidos; Space/Enter los activa/desactiva.
    - El input inferior permite crear tags nuevos (se guardan de forma persistente).
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._all_tags: list[str] = []

    def compose(self) -> ComposeResult:
        yield Label(t("tui.form.tags"), classes="field-label")
        yield SelectionList[str](id="tags-list")
        yield TagInput(placeholder=t("tui.form.tag_ph"), id="inp-tag")

    def load(self, tags: list[str], all_tags: list[str]) -> None:
        self._all_tags = list(all_tags)
        sel = self.query_one("#tags-list", SelectionList)
        sel.set_options(
            [Selection(tag, tag, tag in tags) for tag in self._all_tags]
        )

    @property
    def tags(self) -> list[str]:
        return list(self.query_one("#tags-list", SelectionList).selected)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()  # evitar que llegue al TaskForm._submit
        tag = event.value.strip()
        if tag:
            sel = self.query_one("#tags-list", SelectionList)
            if tag not in self._all_tags:
                # Tag nuevo: persistir y añadir a la lista
                from tasks_cli import tag_store
                tag_store.save(tag)
                self._all_tags.append(tag)
                self._all_tags.sort()
                sel.add_option(Selection(tag, tag, True))
            else:
                # Tag existente: activarlo
                sel.select(tag)
        self.query_one("#inp-tag", TagInput).value = ""

    def on_tag_input_backspace_on_empty(self, _: TagInput.BackspaceOnEmpty) -> None:
        sel = self.query_one("#tags-list", SelectionList)
        selected = list(sel.selected)
        if selected:
            sel.deselect(selected[-1])


# ---------------------------------------------------------------------------
# Widget de formulario embebido
# ---------------------------------------------------------------------------


class TaskForm(Widget):
    """Formulario embebido en el panel derecho — no es un modal."""

    BINDINGS = [Binding("escape", "cancel_form", t("tui.cancel"))]

    _NARROW_THRESHOLD = 52

    def __init__(self) -> None:
        super().__init__()
        self._original: Task | None = None
        self._is_edit = False

    def compose(self) -> ComposeResult:
        # Cabecera fija
        yield Label("", id="form-heading")

        # Área scrollable — contiene todos los campos
        with ScrollableContainer(id="form-scroll"):
            # Título y notas
            yield Label(t("tui.form.title"), classes="field-label")
            yield Input(placeholder=t("tui.form.title_ph"), id="inp-title")
            yield Label(t("tui.form.notes"), classes="field-label")
            yield Input(placeholder=t("tui.form.notes_ph"), id="inp-notes")

            yield Rule()

            # Proyecto | Vence
            yield Horizontal(
                Vertical(
                    Label(t("tui.form.project"), classes="field-label"),
                    Input(placeholder=t("tui.form.project_ph"), id="inp-project"),
                    classes="row-col-left",
                ),
                Vertical(
                    Label(t("tui.form.due"), classes="field-label"),
                    DateInput(id="inp-due"),
                    classes="row-col-right",
                ),
                classes="form-row",
            )

            yield Rule()

            # Tags (izquierda) + Prioridad (derecha)
            yield Horizontal(
                TagsField(classes="tags-col"),
                Vertical(
                    Label(t("tui.form.priority"), classes="field-label"),
                    RadioSet(
                        RadioButton(t("tui.priority.low")),
                        RadioButton(t("tui.priority.medium"), value=True),
                        RadioButton(t("tui.priority.high")),
                        id="inp-priority",
                    ),
                    classes="priority-col",
                ),
                classes="form-row",
            )

            # Estado — solo visible al editar
            with Vertical(id="status-section"):
                yield Rule()
                yield Label(t("tui.form.status"), classes="field-label")
                yield RadioSet(
                    RadioButton(t("tui.status.pending"), value=True),
                    RadioButton(t("tui.status.in_progress")),
                    RadioButton(t("tui.status.cancelled")),
                    id="inp-status",
                )

        # Pie fijo — error y botones siempre visibles
        with Vertical(id="form-footer"):
            yield Static("", id="form-error")
            yield Horizontal(
                Button(t("tui.form.save"), variant="primary", id="btn-save"),
                Button(t("tui.form.cancel"), id="btn-cancel"),
                id="form-buttons",
            )

    def on_resize(self, event: events.Resize) -> None:
        self.set_class(event.size.width < self._NARROW_THRESHOLD, "narrow")

    def load(self, task: Task | None, all_tags: list[str] | None = None) -> None:
        """Carga datos de una tarea existente o limpia para nueva."""
        self._original = task
        self._is_edit = task is not None

        self.query_one("#form-heading", Label).update(t("tui.form.edit_task") if self._is_edit else t("tui.form.new_task"))

        title_inp = self.query_one("#inp-title", Input)
        notes_inp = self.query_one("#inp-notes", Input)
        project_inp = self.query_one("#inp-project", Input)
        due_inp = self.query_one("#inp-due", DateInput)
        priority_set = self.query_one("#inp-priority", RadioSet)
        status_set = self.query_one("#inp-status", RadioSet)
        tags_field = self.query_one(TagsField)

        if task:
            title_inp.value = task.title
            notes_inp.value = task.notes or ""
            project_inp.value = task.project or ""
            due_inp.value = task.due_date.isoformat() if task.due_date else ""
            _select_radio(priority_set, _PRIORITIES.index(task.priority))
            status_idx = _STATUSES.index(task.status) if task.status in _STATUSES else 0
            _select_radio(status_set, status_idx)
            tags_field.load(task.tags, all_tags or [])
        else:
            title_inp.value = ""
            notes_inp.value = ""
            project_inp.value = ""
            due_inp.value = ""
            _select_radio(priority_set, 1)  # media por defecto
            _select_radio(status_set, 0)
            tags_field.load([], all_tags or [])

        self.query_one("#status-section").display = self._is_edit

        self.query_one("#form-error", Static).update("")
        title_inp.focus()

    def action_cancel_form(self) -> None:
        self.screen._cancel_form()  # type: ignore[attr-defined]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.screen._cancel_form()  # type: ignore[attr-defined]
        else:
            self._submit()

    def on_input_submitted(self, _: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        error_widget = self.query_one("#form-error", Static)
        title = self.query_one("#inp-title", Input).value.strip()
        if not title:
            error_widget.update(t("tui.form.err_title_empty"))
            self.query_one("#inp-title", Input).focus()
            return

        priority = _PRIORITIES[self.query_one("#inp-priority", RadioSet).pressed_index]
        project = self.query_one("#inp-project", Input).value.strip() or None
        notes = self.query_one("#inp-notes", Input).value.strip() or None
        due_raw = self.query_one("#inp-due", DateInput).value.strip()
        due_date: date | None = None

        if due_raw:
            try:
                due_date = date.fromisoformat(due_raw)
            except ValueError:
                error_widget.update(t("tui.form.err_date_invalid"))
                self.query_one("#inp-due", DateInput).focus()
                return

        tags = self.query_one(TagsField).tags

        if self._original is None:
            cfg = get_config()
            task = Task(
                title=title,
                priority=priority,
                project=project,
                notes=notes,
                due_date=due_date,
                tags=tags,
                device_id=cfg.device_id,
            )
        else:
            task = self._original.model_copy(deep=True)
            task.title = title
            task.priority = priority
            task.project = project
            task.notes = notes
            task.due_date = due_date
            task.tags = tags
            task.status = _STATUSES[self.query_one("#inp-status", RadioSet).pressed_index]
            task.touch()

        self.screen._save_form(task)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Pantalla principal
# ---------------------------------------------------------------------------


class MainScreen(Screen):
    BINDINGS = [
        Binding("a", "add_task", t("tui.add")),
        Binding("e", "edit_task", t("tui.edit")),
        Binding("d", "mark_done", t("tui.done")),
        Binding("x", "delete_task", t("tui.delete")),
        Binding("q", "quit_app", t("tui.quit")),
    ]

    CSS = APP_CSS

    def __init__(self) -> None:
        super().__init__()
        self._repo = SQLiteRepository(get_config().db_path)
        self._tasks: list[Task] = []
        self._form_mode = False
        self._title_w = 30

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Horizontal(
            Vertical(
                DataTable(id="table", cursor_type="row", zebra_stripes=True),
                id="left",
            ),
            ScrollableContainer(
                TaskDetail(),
                TaskForm(),
                id="right",
            ),
            id="body",
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.add_columns(t("tui.col.id"), t("tui.col.title"), t("tui.col.priority"), t("tui.col.due"))
        self._load_tasks()

    def on_resize(self, event: events.Resize) -> None:
        left_w = event.size.width // 2
        new_title_w = max(10, left_w - 8 - 2 - 12 - 6)
        if new_title_w != self._title_w:
            self._title_w = new_title_w
            self._load_tasks()

    # --- Carga de datos ---

    def _load_tasks(self) -> None:
        table = self.query_one("#table", DataTable)
        table.clear()
        self._tasks = self._repo.list()
        for task in self._tasks:
            p_label = {"high": "!!", "medium": "! ", "low": ". "}[task.priority.value]
            table.add_row(
                task.short_id,
                task.title[: self._title_w],
                p_label,
                _fmt_due(task.due_date)[:12],
                key=task.id,
            )

    def _refresh_detail(self, task: Task | None) -> None:
        self.query_one(TaskDetail).show_task(task)

    def _selected_task(self) -> Task | None:
        table = self.query_one("#table", DataTable)
        if table.row_count == 0:
            return None
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            return next((t for t in self._tasks if t.id == row_key.value), None)
        except Exception:
            return None

    # --- Modo formulario ---

    def _show_form(self, task: Task | None) -> None:
        self._form_mode = True
        self.query_one(TaskDetail).display = False
        form = self.query_one(TaskForm)
        form.add_class("visible")
        from tasks_cli import tag_store
        task_tags = {tag for t_ in self._tasks for tag in t_.tags}
        all_tags = sorted(set(tag_store.load()) | task_tags)
        form.load(task, all_tags)

    def _hide_form(self) -> None:
        self._form_mode = False
        self.query_one(TaskForm).remove_class("visible")
        self.query_one(TaskDetail).display = True
        self.query_one("#table", DataTable).focus()

    def _cancel_form(self) -> None:
        self._hide_form()
        self._refresh_detail(self._selected_task())

    def _save_form(self, task: Task) -> None:
        self._repo.save(task)
        self._load_tasks()
        self._hide_form()
        self._refresh_detail(task)

    # --- Eventos ---

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if self._form_mode:
            return
        task = next((t for t in self._tasks if t.id == event.row_key.value), None)
        self._refresh_detail(task)

    # --- Acciones ---

    def action_add_task(self) -> None:
        if self._form_mode:
            return
        self._show_form(None)

    def action_edit_task(self) -> None:
        if self._form_mode:
            return
        task = self._selected_task()
        if task:
            self._show_form(task)

    def action_mark_done(self) -> None:
        if self._form_mode:
            return
        task = self._selected_task()
        if task and task.status != TaskStatus.done:
            task.mark_done()
            self._repo.save(task)
            self._load_tasks()
            self._refresh_detail(task)

    def action_delete_task(self) -> None:
        if self._form_mode:
            return
        task = self._selected_task()
        if task:
            self._repo.delete(task.id)
            self._load_tasks()
            self._refresh_detail(None)

    def action_quit_app(self) -> None:
        self._repo.close()
        self.app.exit()


# ---------------------------------------------------------------------------
# App raiz
# ---------------------------------------------------------------------------


class TaskApp(App):
    TITLE = "task ui"
    SCREENS = {"main": MainScreen}

    def on_mount(self) -> None:
        self.push_screen("main")
