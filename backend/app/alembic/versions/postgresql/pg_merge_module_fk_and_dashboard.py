"""Merge module FK fix and dashboard migrations

Revision ID: pg_merge_module_fk_dashboard
Revises: pg_fix_module_fk, pg_r2_add_dashboard_tables
Create Date: 2025-11-09

"""
from alembic import op
import sqlalchemy as sa

revision = 'pg_merge_module_fk_dashboard'
down_revision = ('pg_fix_module_fk', 'pg_r2_add_dashboard_tables')
branch_labels = None
depends_on = None


def upgrade():
    """Merge migration - no changes needed"""
    pass


def downgrade():
    """Merge migration - no changes needed"""
    pass
