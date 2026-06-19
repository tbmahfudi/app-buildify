"""Merge module_lifecycle_columns into main head

Revision ID: pg_merge_lifecycle_main
Revises: ec859b2a490c, pg_module_lifecycle_columns
Create Date: 2026-06-20 00:00:00.000000
"""
from alembic import op

revision = "pg_merge_lifecycle_main"
down_revision = ("ec859b2a490c", "pg_module_lifecycle_columns")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
