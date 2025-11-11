"""Merge display security and report/dashboard UUID migrations

Revision ID: pg_merge_display_r3
Revises: pg_merge_display_security, pg_r3
Create Date: 2025-11-11 15:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'pg_merge_display_r3'
down_revision = ('pg_merge_display_security', 'pg_r3')
branch_labels = None
depends_on = None


def upgrade():
    """Merge migration - no changes needed"""
    pass


def downgrade():
    """Merge migration - no changes needed"""
    pass
