# Changelog

Todos los cambios notables de este proyecto se documentan aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/).

## [0.1.0] — 2026-03-23

### Añadido
- Comandos CRUD: `add`, `list`, `done`, `edit`, `delete`, `show`, `search`
- Vistas rápidas: `today`, `overdue`, `upcoming`, `projects`, `tags`, `stats`
- Exportación a JSON, CSV y Markdown (`export`)
- Importación desde JSON con detección de duplicados (`import`)
- Configuración persistente en `~/.tasks/config.toml` (`config get/set`)
- Sincronización entre dispositivos vía PostgreSQL (`sync setup/push/pull/status/auto`)
- Credenciales de PostgreSQL cifradas con Fernet
- Autocompletado de shell para IDs, proyectos, etiquetas y claves de config
- Migraciones de esquema con Alembic
- Tests unitarios y de integración con cobertura > 80%
