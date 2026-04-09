<div align="center">
  <img src="./docs/assets/banner.svg" alt="tasks-cli - Offline-first task manager for the terminal" width="100%"/>
</div>

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Typer](https://img.shields.io/badge/Typer-CLI-009688)](https://typer.tiangolo.com)
[![Textual](https://img.shields.io/badge/Textual-TUI-7C3AED)](https://textual.textualize.io)
[![CI](https://github.com/Loksz/tasks-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/Loksz/tasks-cli/actions/workflows/ci.yml)

</div>

<br/>

**tasks-cli** is an offline-first task manager that runs entirely in the terminal. Tasks are stored locally in SQLite — no account, no server, no internet required. An optional sync layer lets you push and pull tasks across multiple devices using your own PostgreSQL or MySQL database.

---

## Features

| | |
|---|---|
| **Full CRUD** | Add, edit, complete, and delete tasks with a single command |
| **Filtering & views** | Filter by status, priority, project, tag, or date range |
| **Quick views** | `today`, `overdue`, `upcoming` — get context instantly |
| **Full-text search** | Search across titles and notes |
| **Interactive TUI** | Keyboard-navigable interface powered by Textual |
| **Export / Import** | JSON, CSV, and Markdown with duplicate detection |
| **Multi-device sync** | Optional push/pull via PostgreSQL, MySQL, or MariaDB |
| **Encrypted credentials** | Sync DSN stored with Fernet encryption at rest |
| **i18n** | English and Spanish, configurable per user |
| **Shell completions** | Tab completion for all commands and flags |

---

## Installation

**Requires Python 3.11+**

```bash
git clone https://github.com/Loksz/tasks-cli.git
cd tasks-cli
pip install -e .
```

**Optional extras:**

```bash
pip install -e '.[ui]'              # Interactive TUI (Textual)
pip install -e '.[sync-postgres]'   # PostgreSQL sync
pip install -e '.[sync-mysql]'      # MySQL / MariaDB sync
pip install -e '.[dev]'             # Tests and linting
```

---

## Usage

```bash
# Add a task
task add "Review pull request" --priority high --due 2026-04-15 --tag backend

# List tasks
task list
task list --status pending --priority high --project work

# Quick views
task today       # due today + overdue
task overdue     # only overdue
task upcoming    # next 7 days (--days N to customize)

# Complete, edit, delete
task done <id> [<id2> ...]
task edit <id> --title "New title" --priority medium
task delete <id>          # prompts for confirmation
task delete <id> --force  # skip confirmation

# Search and inspect
task search "pull request"
task show <id>
task stats
```

### Interactive TUI

```bash
task ui
```

| Key | Action |
|---|---|
| `a` | Add task |
| `e` | Edit selected |
| `d` | Mark as done |
| `x` | Delete |
| `q` | Quit |

### Export / Import

```bash
task export --format json --output backup.json
task export --format csv  --output tasks.csv
task export --format markdown

task import --file backup.json   # skips duplicates automatically
```

---

## Multi-device Sync

Sync is entirely optional. When configured, tasks are pushed to and pulled from your own database - no third-party service involved.

**Supported databases:** PostgreSQL, MySQL, MariaDB

```bash
# One-time setup
task sync setup --dsn postgresql://user:pass@host:5432/db

# Manual sync
task sync push    # upload local changes
task sync pull    # download remote changes

# Automatic sync (runs every 5 minutes, Ctrl+C to stop)
task sync auto

# Check sync state
task sync status
```

Conflict resolution uses a **latest-write-wins** strategy based on `updated_at` timestamps with device-level version tracking. Credentials are stored encrypted at `~/.tasks/.sync.key` using Fernet (AES-128-CBC).

---

## Configuration

```bash
task config get                         # show all settings
task config set default_priority high   # set a value
task config set language en             # switch to English
task config set no_color true           # disable colors
```

| Key | Default | Description |
|---|---|---|
| `default_priority` | `medium` | Priority assigned to new tasks |
| `date_format` | `%Y-%m-%d` | Date display format |
| `language` | `es` | Interface language (`es` / `en`) |
| `no_color` | `false` | Disable colored output |
| `sync_interval` | `300` | Auto-sync interval in seconds |

Config is stored at `~/.tasks/config.toml`. Tasks database at `~/.tasks/tasks.db`.

---

## Architecture

```
tasks_cli/
├── cli/              # Typer commands (tasks, sync, config, completions)
├── db/
│   ├── base.py       # Abstract TaskRepository interface + TaskFilters
│   ├── sqlite.py     # Local SQLite implementation
│   ├── sqlalchemy_repo.py  # Remote PostgreSQL/MySQL implementation
│   └── migrations/   # Alembic schema versioning
├── sync/
│   ├── engine.py     # SyncEngine - push/pull coordination
│   └── resolver.py   # Conflict resolution logic
├── tui/
│   └── app.py        # Textual TUI application
├── models/task.py    # Task and Config domain models (Pydantic v2)
├── i18n.py           # Internationalization (es / en)
├── config.py         # User config persistence
└── cache.py          # In-memory task cache
```

The storage layer uses a **Repository Pattern** — `TaskRepository` is an abstract interface implemented independently by SQLite (local) and SQLAlchemy (remote). Swapping backends requires no changes to CLI logic.

---

## Development

```bash
pip install -e '.[dev]'

# Run tests
pytest

# Lint and format
ruff check .
ruff format .

# Type check
mypy tasks_cli/
```

CI runs on Python 3.11 and 3.12 via GitHub Actions on every push and pull request.

---

## Tech Stack

| | |
|---|---|
| Language | Python 3.11+ |
| CLI framework | Typer |
| Terminal UI | Textual |
| Output formatting | Rich |
| Data validation | Pydantic v2 |
| Local storage | SQLite |
| Remote sync | SQLAlchemy (PostgreSQL / MySQL / MariaDB) |
| Migrations | Alembic |
| Encryption | cryptography (Fernet) |
| Testing | pytest + pytest-cov |
| Linting | Ruff |

---

<div align="center">

**Sebastian Hernandez** - [LinkedIn](https://www.linkedin.com/in/shdez-dev/) - [Portfolio](https://www.shernandez.dev)

</div>
