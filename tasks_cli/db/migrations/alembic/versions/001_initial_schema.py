"""initial_schema

Revision ID: 001
Revises: 
Create Date: 2026-03-23 19:48:38.560257

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("priority", sa.Text, nullable=False, server_default="medium"),
        sa.Column("project", sa.Text, nullable=True),
        sa.Column("tags", sa.Text, nullable=False, server_default="[]"),
        sa.Column("due_date", sa.Text, nullable=True),
        sa.Column("created_at", sa.Text, nullable=False),
        sa.Column("updated_at", sa.Text, nullable=False),
        sa.Column("completed_at", sa.Text, nullable=True),
        sa.Column("sync_status", sa.Text, nullable=False, server_default="local"),
        sa.Column("sync_version", sa.Integer, nullable=False, server_default="0"),
        sa.Column("device_id", sa.Text, nullable=False, server_default=""),
    )
    op.create_index("idx_tasks_status",   "tasks", ["status"])
    op.create_index("idx_tasks_priority", "tasks", ["priority"])
    op.create_index("idx_tasks_project",  "tasks", ["project"])
    op.create_index("idx_tasks_due_date", "tasks", ["due_date"])
    op.create_index("idx_tasks_sync",     "tasks", ["sync_status"])


def downgrade() -> None:
    op.drop_index("idx_tasks_sync")
    op.drop_index("idx_tasks_due_date")
    op.drop_index("idx_tasks_project")
    op.drop_index("idx_tasks_priority")
    op.drop_index("idx_tasks_status")
    op.drop_table("tasks")
