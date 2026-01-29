"""Add commit_message column to entity_migrations

Revision ID: pg_add_commit_message_to_migrations
Revises: pg_add_display_field
Create Date: 2026-01-29 00:00:00.000000

Adds commit_message column to entity_migrations table to store
optional user-provided commit messages when generating migrations.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pg_add_commit_message_to_migrations'
down_revision = 'pg_add_display_field'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add commit_message column to entity_migrations table.
    This allows users to provide descriptive messages when generating migrations.
    """
    op.add_column('entity_migrations',
                  sa.Column('commit_message', sa.Text(), nullable=True))


def downgrade() -> None:
    """
    Remove commit_message column from entity_migrations table.
    """
    op.drop_column('entity_migrations', 'commit_message')
