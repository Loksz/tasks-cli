# task-cli

CLI para gestionar tareas desde la terminal. Guarda todo localmente en SQLite, sin necesidad de cuenta ni conexión.

## Instalación

```bash
git clone https://github.com/Loksz/task-cli.git
cd task-cli
pip install -e .
```

## Uso básico

```bash
task add "Revisar PR" --priority high --due 2026-03-28 --tag backend
task list
task list --status pending --project trabajo
task done <id>
task today          # qué tengo para hoy
task upcoming       # próximos 7 días
task search "PR"
```

## Comandos disponibles

```
task add       Nueva tarea (--priority, --due, --tag, --project, --notes)
task list      Listar con filtros opcionales
task done      Marcar como completada (acepta varios IDs a la vez)
task edit      Modificar cualquier campo
task delete    Eliminar (pide confirmación, o --force para saltar)
task show      Ver detalle completo de una tarea
task search    Buscar texto en títulos y notas
task today     Tareas para hoy y las que ya vencieron
task overdue   Solo las vencidas
task upcoming  Las que vencen en los próximos N días (--days)
task stats     Resumen rápido: total, completadas, pendientes, vencidas
task export    Exportar a JSON, CSV o Markdown (--format, --output)
task import    Importar desde un JSON exportado previamente
task config    Ver y cambiar configuración (prioridad por defecto, colores, etc.)
```

## Sincronización entre dispositivos (opcional)

Si trabajas desde varias máquinas, puedes sincronizar las tareas usando una base de datos externa. Funciona con PostgreSQL, MySQL y MariaDB.

Instala el driver que necesites:

```bash
pip install -e '.[sync-postgres]'   # PostgreSQL
pip install -e '.[sync-mysql]'      # MySQL o MariaDB
```

Conecta una vez:

```bash
task sync setup --dsn postgresql://user:pass@host:5432/db
task sync setup --dsn mysql+pymysql://user:pass@host/db
```

Y ya puedes sincronizar:

```bash
task sync push     # sube tus cambios
task sync pull     # baja los cambios de otros dispositivos
task sync auto     # sync automático cada 5 minutos (Ctrl+C para parar)
```

Los conflictos se resuelven automáticamente: gana siempre la versión más reciente. Las credenciales se guardan cifradas en `~/.task/.sync.key`.

## Stack

Python 3.11 · Typer · Rich · Pydantic v2 · SQLite · SQLAlchemy
