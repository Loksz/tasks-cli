# tasks-cli

CLI para gestionar tareas desde la terminal. Guarda todo localmente en SQLite, sin necesidad de cuenta ni conexión.

## Instalación

```bash
git clone https://github.com/Loksz/tasks-cli.git
cd tasks-cli
pip install -e .
```

## Uso básico

```bash
tasks add "Revisar PR" --priority high --due 2026-03-28 --tag backend
tasks list
tasks list --status pending --project trabajo
tasks done <id>
tasks today          # qué tengo para hoy
tasks upcoming       # próximos 7 días
tasks search "PR"
```

## Comandos disponibles

```
tasks add       Nueva tarea (--priority, --due, --tag, --project, --notes)
tasks list      Listar con filtros opcionales
tasks done      Marcar como completada (acepta varios IDs a la vez)
tasks edit      Modificar cualquier campo
tasks delete    Eliminar (pide confirmación, o --force para saltar)
tasks show      Ver detalle completo de una tarea
tasks search    Buscar texto en títulos y notas
tasks today     Tareas para hoy y las que ya vencieron
tasks overdue   Solo las vencidas
tasks upcoming  Las que vencen en los próximos N días (--days)
tasks stats     Resumen rápido: total, completadas, pendientes, vencidas
tasks export    Exportar a JSON, CSV o Markdown (--format, --output)
tasks import    Importar desde un JSON exportado previamente
tasks config    Ver y cambiar configuración (prioridad por defecto, colores, etc.)
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
tasks sync setup --dsn postgresql://user:pass@host:5432/db
tasks sync setup --dsn mysql+pymysql://user:pass@host/db
```

Y ya puedes sincronizar:

```bash
tasks sync push     # sube tus cambios
tasks sync pull     # baja los cambios de otros dispositivos
tasks sync auto     # sync automático cada 5 minutos (Ctrl+C para parar)
```

Los conflictos se resuelven automáticamente: gana siempre la versión más reciente. Las credenciales se guardan cifradas en `~/.tasks/.sync.key`.

## Stack

Python 3.11 · Typer · Rich · Pydantic v2 · SQLite · SQLAlchemy
