"""Sistema de internacionalización - soporta 'es' (español) y 'en' (inglés)."""

from __future__ import annotations

_LANGS = {
    "es": {
        # ── CLI: App principal ──────────────────────────────────────────────
        "help.app": "TASKS - CLI de Gestión de Tareas con Sincronización",
        "help.ui": "Abrir la interfaz interactiva navegable con flechas del teclado",
        "help.config_app": "Ver y modificar la configuración del usuario",
        "help.config_get": "Ver valor(es) de configuración",
        "help.config_set": "Establecer un valor de configuración persistente",
        # ── CLI: Tareas ─────────────────────────────────────────────────────
        "help.tasks_app": "Gestión de tareas",
        "help.add": "Crear una nueva tarea",
        "help.list": "Listar tareas con filtros opcionales",
        "help.done": "Marcar una o varias tareas como completadas",
        "help.edit": "Modificar campos de una tarea existente",
        "help.delete": "Eliminar una tarea de forma permanente",
        "help.show": "Ver detalle completo de una tarea",
        "help.search": "Búsqueda de texto en títulos y notas",
        "help.today": "Tareas con vencimiento hoy o vencidas sin completar",
        "help.overdue": "Listar todas las tareas vencidas",
        "help.upcoming": "Tareas con vencimiento en los próximos N días",
        "help.projects": "Listar proyectos activos con conteo de tareas",
        "help.tags": "Listar etiquetas con conteo de tareas",
        "help.stats": "Resumen estadístico de tareas",
        "help.export": "Exportar tareas a JSON, CSV o Markdown",
        "help.import": "Importar tareas desde archivo JSON o CSV",
        # ── CLI: Sync ───────────────────────────────────────────────────────
        "help.sync_app": "Sincronización entre dispositivos",
        "help.sync_setup": "Configurar conexión a una base de datos remota y guardar credenciales cifradas",
        "help.sync_push": "Enviar cambios locales pendientes al servidor remoto",
        "help.sync_pull": "Descargar cambios del servidor y aplicarlos localmente",
        "help.sync_status": "Mostrar cambios pendientes y estado del último sync",
        "help.sync_auto": "Activar sync automático en background cada N minutos",
        # ── Mensajes CLI ────────────────────────────────────────────────────
        "msg.task_created": "Tarea creada \\[{id}] - {title}",
        "msg.no_tasks": "No hay tareas.",
        "msg.task_not_found": "Tarea no encontrada: {id}",
        "msg.task_done": "\\[{id}] {title} - completada",
        "msg.task_updated": "Tarea \\[{id}] actualizada",
        "msg.delete_confirm": "¿Eliminar '{title}'?",
        "msg.task_deleted": "Tarea \\[{id}] eliminada",
        "msg.no_results": "Sin resultados.",
        "msg.no_today": "Sin tareas para hoy.",
        "msg.no_overdue": "Sin tareas vencidas.",
        "msg.no_upcoming": "Sin tareas en los próximos {days} días.",
        "msg.exported": "Exportado a {file} ({count} tareas)",
        "msg.imported": "Importadas: {imported}  Duplicados omitidos: {skipped}",
        "msg.file_read_error": "No se pudo leer el archivo: {exc}",
        "msg.json_not_list": "El archivo JSON debe contener una lista de tareas.",
        "msg.config_unknown_key": "Campo desconocido: {key}",
        "msg.install_ui": "Instala las dependencias con: pip install -e '.[ui]'",
        "msg.sync_deps_missing": (
            "Las dependencias de sincronización no están instaladas.\n"
            "Instálalas con:  pip install 'tasks-cli[sync]'"
        ),
        "msg.sync_not_configured": "Sync no configurado. Ejecuta: task sync setup --dsn <DSN>",
        "msg.sync_not_configured_short": "Sync no configurado.",
        "msg.sync_connect_failed": "No se pudo conectar: {exc}",
        "msg.sync_connected": "Conexión configurada y credenciales cifradas.",
        "msg.pushing": "Enviando cambios...",
        "msg.push_done": "Push completado - enviadas: {pushed}  conflictos: {conflicts}",
        "msg.pulling": "Descargando cambios...",
        "msg.pull_done": "Pull completado - aplicadas: {pulled}  conflictos: {conflicts}",
        "msg.sync_pending": "Cambios pendientes: {count}",
        "msg.sync_checked_at": "Comprobado: {time}",
        "msg.sync_auto_start": "Sync automático activo cada {interval} minuto(s). Ctrl+C para detener.",
        "msg.sync_auto_error": "Error durante sync: {exc}",
        "msg.sync_auto_stopped": "Sync automático detenido.",
        # ── CLI utils: show ─────────────────────────────────────────────────
        "show.status": "Estado",
        "show.priority": "Prioridad",
        "show.project": "Proyecto",
        "show.tags": "Etiquetas",
        "show.due": "Vence",
        "show.created": "Creada",
        "show.modified": "Modificada",
        "show.notes": "Notas",
        "show.panel_title": "Detalle de tarea",
        # ── CLI utils: tabla ────────────────────────────────────────────────
        "col.title": "Título",
        "col.project": "Proyecto",
        "col.due": "Vence",
        "col.status": "Estado",
        # ── CLI utils: fechas ────────────────────────────────────────────────
        "fmt.today": "hoy",
        "fmt.tomorrow": "mañana",
        # ── CLI: proyectos / tags / stats ────────────────────────────────────
        "lbl.no_project": "(sin proyecto)",
        "lbl.pending": "pendientes",
        "lbl.done": "completadas",
        "lbl.total": "Total",
        "lbl.completed": "Completadas",
        "lbl.overdue": "Vencidas",
        "lbl.rate": "Tasa",
        "lbl.task_count": "tarea(s)",
        # ── TUI: bindings ───────────────────────────────────────────────────
        "tui.add": "Agregar",
        "tui.edit": "Editar",
        "tui.done": "Completar",
        "tui.delete": "Eliminar",
        "tui.quit": "Salir",
        "tui.cancel": "Cancelar",
        # ── TUI: estados vacíos ─────────────────────────────────────────────
        "tui.select_task": "Selecciona una tarea",
        # ── TUI: formulario ─────────────────────────────────────────────────
        "tui.form.new_task": "Nueva tarea",
        "tui.form.edit_task": "Editar tarea",
        "tui.form.title": "Titulo *",
        "tui.form.title_ph": "Titulo de la tarea",
        "tui.form.notes": "Notas",
        "tui.form.notes_ph": "Detalles adicionales (opcional)",
        "tui.form.project": "Proyecto",
        "tui.form.project_ph": "opcional",
        "tui.form.due": "Vence",
        "tui.form.priority": "Prioridad",
        "tui.form.status": "Estado",
        "tui.form.save": "Guardar",
        "tui.form.cancel": "Cancelar  [Esc]",
        "tui.form.tags": "Etiquetas",
        "tui.form.tag_ph": "Crear nueva etiqueta y Enter",
        "tui.form.tags_available": "Disponibles:",
        "tui.form.no_tags": "ninguna aún",
        "tui.form.err_title_empty": "El titulo no puede estar vacio",
        "tui.form.err_date_invalid": "Fecha invalida - usa YYYY-MM-DD",
        "tui.form.err_date_incomplete": "Fecha incompleta",
        "tui.form.err_date_format": "Formato invalido - usa YYYY-MM-DD",
        # ── TUI: prioridades ────────────────────────────────────────────────
        "tui.priority.low": "Baja",
        "tui.priority.medium": "Media",
        "tui.priority.high": "Alta",
        # ── TUI: estados ────────────────────────────────────────────────────
        "tui.status.pending": "Pendiente",
        "tui.status.in_progress": "En curso",
        "tui.status.done": "Listo",
        "tui.status.cancelled": "Cancelado",
        # ── TUI: sync ───────────────────────────────────────────────────────
        "tui.sync.local": "local",
        "tui.sync.pending": "pendiente de subir",
        "tui.sync.synced": "sincronizado",
        "tui.sync.conflict": "conflicto",
        # ── TUI: fechas ─────────────────────────────────────────────────────
        "tui.due.overdue": "vencio hace {days}d",
        "tui.due.today": "hoy",
        "tui.due.tomorrow": "manana",
        "tui.urgency.overdue": "[bold red]VENCIDA HACE {days} DIA(S)[/bold red]",
        "tui.urgency.today": "[bold yellow]VENCE HOY[/bold yellow]",
        "tui.urgency.soon": "[yellow]vence en {days} dia(s)[/yellow]",
        # ── TUI: detalle ────────────────────────────────────────────────────
        "tui.detail.status": "Estado",
        "tui.detail.project": "Proyecto",
        "tui.detail.priority": "Prioridad",
        "tui.detail.due": "Vence",
        "tui.detail.tags": "Tags",
        "tui.detail.notes": "Notas",
        "tui.detail.created": "Creada",
        "tui.detail.modified": "Modificada",
        "tui.detail.completed": "Completada",
        "tui.detail.sync": "Sync",
        "tui.detail.no_tags": "sin etiquetas",
        # ── TUI: tabla ──────────────────────────────────────────────────────
        "tui.col.id": "ID",
        "tui.col.title": "Titulo",
        "tui.col.priority": "P",
        "tui.col.due": "Vence",
    },
    "en": {
        # ── CLI: App principal ──────────────────────────────────────────────
        "help.app": "TASKS - Task Management CLI with Sync",
        "help.ui": "Open the interactive UI, keyboard-navigable with arrow keys",
        "help.config_app": "View and modify user configuration",
        "help.config_get": "View configuration value(s)",
        "help.config_set": "Set a persistent configuration value",
        # ── CLI: Tareas ─────────────────────────────────────────────────────
        "help.tasks_app": "Task management",
        "help.add": "Create a new task",
        "help.list": "List tasks with optional filters",
        "help.done": "Mark one or more tasks as done",
        "help.edit": "Modify fields of an existing task",
        "help.delete": "Permanently delete a task",
        "help.show": "Show full task detail",
        "help.search": "Search tasks by text in title and notes",
        "help.today": "Tasks due today or overdue",
        "help.overdue": "List all overdue tasks",
        "help.upcoming": "Tasks due in the next N days",
        "help.projects": "List active projects with task counts",
        "help.tags": "List tags with task counts",
        "help.stats": "Task statistics summary",
        "help.export": "Export tasks to JSON, CSV or Markdown",
        "help.import": "Import tasks from a JSON or CSV file",
        # ── CLI: Sync ───────────────────────────────────────────────────────
        "help.sync_app": "Device-to-device synchronization",
        "help.sync_setup": "Configure remote database connection and save encrypted credentials",
        "help.sync_push": "Send pending local changes to the remote server",
        "help.sync_pull": "Download changes from the server and apply them locally",
        "help.sync_status": "Show pending changes and last sync status",
        "help.sync_auto": "Run automatic sync in the background every N minutes",
        # ── Mensajes CLI ────────────────────────────────────────────────────
        "msg.task_created": "Task created \\[{id}] - {title}",
        "msg.no_tasks": "No tasks.",
        "msg.task_not_found": "Task not found: {id}",
        "msg.task_done": "\\[{id}] {title} - done",
        "msg.task_updated": "Task \\[{id}] updated",
        "msg.delete_confirm": "Delete '{title}'?",
        "msg.task_deleted": "Task \\[{id}] deleted",
        "msg.no_results": "No results.",
        "msg.no_today": "No tasks for today.",
        "msg.no_overdue": "No overdue tasks.",
        "msg.no_upcoming": "No tasks in the next {days} days.",
        "msg.exported": "Exported to {file} ({count} tasks)",
        "msg.imported": "Imported: {imported}  Duplicates skipped: {skipped}",
        "msg.file_read_error": "Could not read file: {exc}",
        "msg.json_not_list": "The JSON file must contain a list of tasks.",
        "msg.config_unknown_key": "Unknown field: {key}",
        "msg.install_ui": "Install dependencies with: pip install -e '.[ui]'",
        "msg.sync_deps_missing": (
            "Sync dependencies are not installed.\n"
            "Install with:  pip install 'tasks-cli[sync]'"
        ),
        "msg.sync_not_configured": "Sync not configured. Run: task sync setup --dsn <DSN>",
        "msg.sync_not_configured_short": "Sync not configured.",
        "msg.sync_connect_failed": "Could not connect: {exc}",
        "msg.sync_connected": "Connection configured and credentials encrypted.",
        "msg.pushing": "Pushing changes...",
        "msg.push_done": "Push completed - sent: {pushed}  conflicts: {conflicts}",
        "msg.pulling": "Pulling changes...",
        "msg.pull_done": "Pull completed - applied: {pulled}  conflicts: {conflicts}",
        "msg.sync_pending": "Pending changes: {count}",
        "msg.sync_checked_at": "Last checked: {time}",
        "msg.sync_auto_start": "Auto-sync active every {interval} minute(s). Ctrl+C to stop.",
        "msg.sync_auto_error": "Sync error: {exc}",
        "msg.sync_auto_stopped": "Auto-sync stopped.",
        # ── CLI utils: show ─────────────────────────────────────────────────
        "show.status": "Status",
        "show.priority": "Priority",
        "show.project": "Project",
        "show.tags": "Tags",
        "show.due": "Due",
        "show.created": "Created",
        "show.modified": "Modified",
        "show.notes": "Notes",
        "show.panel_title": "Task detail",
        # ── CLI utils: tabla ────────────────────────────────────────────────
        "col.title": "Title",
        "col.project": "Project",
        "col.due": "Due",
        "col.status": "Status",
        # ── CLI utils: fechas ────────────────────────────────────────────────
        "fmt.today": "today",
        "fmt.tomorrow": "tomorrow",
        # ── CLI: proyectos / tags / stats ────────────────────────────────────
        "lbl.no_project": "(no project)",
        "lbl.pending": "pending",
        "lbl.done": "done",
        "lbl.total": "Total",
        "lbl.completed": "Completed",
        "lbl.overdue": "Overdue",
        "lbl.rate": "Rate",
        "lbl.task_count": "task(s)",
        # ── TUI: bindings ───────────────────────────────────────────────────
        "tui.add": "Add",
        "tui.edit": "Edit",
        "tui.done": "Done",
        "tui.delete": "Delete",
        "tui.quit": "Quit",
        "tui.cancel": "Cancel",
        # ── TUI: estados vacíos ─────────────────────────────────────────────
        "tui.select_task": "Select a task",
        # ── TUI: formulario ─────────────────────────────────────────────────
        "tui.form.new_task": "New task",
        "tui.form.edit_task": "Edit task",
        "tui.form.title": "Title *",
        "tui.form.title_ph": "Task title",
        "tui.form.notes": "Notes",
        "tui.form.notes_ph": "Additional details (optional)",
        "tui.form.project": "Project",
        "tui.form.project_ph": "optional",
        "tui.form.due": "Due",
        "tui.form.priority": "Priority",
        "tui.form.status": "Status",
        "tui.form.save": "Save",
        "tui.form.cancel": "Cancel  [Esc]",
        "tui.form.tags": "Tags",
        "tui.form.tag_ph": "Create new tag and press Enter",
        "tui.form.tags_available": "Available:",
        "tui.form.no_tags": "none yet",
        "tui.form.err_title_empty": "Title cannot be empty",
        "tui.form.err_date_invalid": "Invalid date - use YYYY-MM-DD",
        "tui.form.err_date_incomplete": "Incomplete date",
        "tui.form.err_date_format": "Invalid format - use YYYY-MM-DD",
        # ── TUI: prioridades ────────────────────────────────────────────────
        "tui.priority.low": "Low",
        "tui.priority.medium": "Medium",
        "tui.priority.high": "High",
        # ── TUI: estados ────────────────────────────────────────────────────
        "tui.status.pending": "Pending",
        "tui.status.in_progress": "In progress",
        "tui.status.done": "Done",
        "tui.status.cancelled": "Cancelled",
        # ── TUI: sync ───────────────────────────────────────────────────────
        "tui.sync.local": "local",
        "tui.sync.pending": "pending upload",
        "tui.sync.synced": "synced",
        "tui.sync.conflict": "conflict",
        # ── TUI: fechas ─────────────────────────────────────────────────────
        "tui.due.overdue": "overdue {days}d",
        "tui.due.today": "today",
        "tui.due.tomorrow": "tomorrow",
        "tui.urgency.overdue": "[bold red]OVERDUE BY {days} DAY(S)[/bold red]",
        "tui.urgency.today": "[bold yellow]DUE TODAY[/bold yellow]",
        "tui.urgency.soon": "[yellow]due in {days} day(s)[/yellow]",
        # ── TUI: detalle ────────────────────────────────────────────────────
        "tui.detail.status": "Status",
        "tui.detail.project": "Project",
        "tui.detail.priority": "Priority",
        "tui.detail.due": "Due",
        "tui.detail.tags": "Tags",
        "tui.detail.notes": "Notes",
        "tui.detail.created": "Created",
        "tui.detail.modified": "Modified",
        "tui.detail.completed": "Completed",
        "tui.detail.sync": "Sync",
        "tui.detail.no_tags": "no tags",
        # ── TUI: tabla ──────────────────────────────────────────────────────
        "tui.col.id": "ID",
        "tui.col.title": "Title",
        "tui.col.priority": "P",
        "tui.col.due": "Due",
    },
}

_current: str = "es"


def set_language(lang: str) -> None:
    """Establece el idioma activo. Si no es soportado, usa 'es'."""
    global _current
    _current = lang if lang in _LANGS else "es"


def get_language() -> str:
    return _current


def supported_languages() -> list[str]:
    return list(_LANGS.keys())


def t(msg_id: str, **kwargs: object) -> str:
    """Retorna la cadena traducida. Acepta kwargs para formato: t('msg.task_created', id='abc', title='x')."""
    text = _LANGS.get(_current, _LANGS["es"]).get(msg_id)
    if text is None:
        # fallback a español si la clave no existe en el idioma activo
        text = _LANGS["es"].get(msg_id, msg_id)
    return text.format(**kwargs) if kwargs else text
