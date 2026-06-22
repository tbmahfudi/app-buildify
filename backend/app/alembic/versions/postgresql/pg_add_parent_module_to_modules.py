"""Add parent_module_id to modules for sub-module hierarchy

Revision ID: aa11bb22cc33
Revises: pg_tenant_module_databases
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'aa11bb22cc33'
down_revision = 'pg_tenant_module_databases'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('modules',
        sa.Column('parent_module_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'modules_parent_module_id_fkey', 'modules', 'modules',
        ['parent_module_id'], ['id'], ondelete='RESTRICT')
    op.create_check_constraint('no_self_parent', 'modules', 'id != parent_module_id')
    op.create_index('ix_modules_parent_module_id', 'modules', ['parent_module_id'],
        postgresql_where=sa.text('parent_module_id IS NOT NULL'))


def downgrade():
    op.drop_index('ix_modules_parent_module_id', table_name='modules')
    op.drop_constraint('no_self_parent', 'modules', type_='check')
    op.drop_constraint('modules_parent_module_id_fkey', 'modules', type_='foreignkey')
    op.drop_column('modules', 'parent_module_id')
