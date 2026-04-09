# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/).

## [0.1.0] - 2026-03-23

### Added
- Core CRUD commands: `add`, `list`, `done`, `edit`, `delete`, `show`, `search`
- Quick views: `today`, `overdue`, `upcoming`, `projects`, `tags`, `stats`
- Export to JSON, CSV, and Markdown (`export`)
- Import from JSON with duplicate detection (`import`)
- Persistent configuration at `~/.tasks/config.toml` (`config get/set`)
- Multi-device sync via PostgreSQL/MySQL (`sync setup/push/pull/status/auto`)
- Sync credentials encrypted at rest with Fernet (AES-128-CBC)
- Shell tab completion for IDs, projects, tags, and config keys
- Schema versioning with Alembic migrations
- Unit and integration test suite (76 tests passing)
