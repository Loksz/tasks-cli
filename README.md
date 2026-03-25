# tasks-cli

Herramienta de línea de comandos para gestión de tareas. Funciona completamente offline con SQLite — sin dependencias externas.

## Instalación

Clona o descarga el repositorio y luego instala en modo editable:

```bash
git clone https://github.com/tu-usuario/amadeus-task-cli.git
cd amadeus-task-cli
pip install -e .
```

O si prefieres pipx (recomendado para CLIs):

```bash
cd amadeus-task-cli
pipx install .
```

## Uso

```bash
tasks add "Revisar PR" --priority high --due 2026-03-25 --tag backend
tasks list
tasks done <id>
tasks --help
```

## Comandos

```
tasks add       Crear tarea
tasks list      Listar con filtros (--status, --priority, --tag, --project)
tasks done      Marcar como completada
tasks edit      Editar campos de una tarea
tasks delete    Eliminar tarea
tasks show      Ver detalle completo
tasks search    Buscar en títulos y notas
tasks today     Tareas para hoy y vencidas
tasks overdue   Todas las tareas vencidas
tasks upcoming  Tareas próximas (--days N, default 7)
tasks stats     Resumen estadístico
tasks export    Exportar a JSON, CSV o Markdown
tasks import    Importar desde JSON
tasks config    Ver y modificar configuración
```

## Sincronización multi-dispositivo (opcional)

Requiere PostgreSQL. Instala con las dependencias adicionales:

```bash
pip install -e '.[sync]'
tasks sync setup --dsn postgresql://user:pass@host:5432/db
tasks sync push
tasks sync pull
```

## Stack

Python 3.11 · Typer · Rich · Pydantic v2 · SQLite
