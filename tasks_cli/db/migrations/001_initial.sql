-- Migration: 001_initial
-- Description: Esquema inicial de la tabla tasks

CREATE TABLE IF NOT EXISTS tasks (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    notes        TEXT,
    status       TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','in_progress','done','cancelled')),
    priority     TEXT NOT NULL DEFAULT 'medium'
                     CHECK (priority IN ('low','medium','high')),
    project      TEXT,
    tags         TEXT NOT NULL DEFAULT '[]',
    due_date     TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    completed_at TEXT,
    sync_status  TEXT NOT NULL DEFAULT 'local'
                     CHECK (sync_status IN ('local','pending','synced','conflict')),
    sync_version INTEGER NOT NULL DEFAULT 0,
    device_id    TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_tasks_status   ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_project  ON tasks(project);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_sync     ON tasks(sync_status);
