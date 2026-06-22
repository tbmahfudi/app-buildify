"""Fix audit FK columns to use ON DELETE SET NULL so user deletion does not block

Revision ID: dd44ee55ff66
Revises: cc33dd44ee55
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa

revision = 'dd44ee55ff66'
down_revision = 'cc33dd44ee55'
branch_labels = None
depends_on = None


def upgrade():
    # Fix modules.created_by and updated_by
    op.drop_constraint('modules_created_by_fkey', 'modules', type_='foreignkey')
    op.drop_constraint('modules_updated_by_fkey', 'modules', type_='foreignkey')
    op.create_foreign_key('modules_created_by_fkey', 'modules', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('modules_updated_by_fkey', 'modules', 'users', ['updated_by'], ['id'], ondelete='SET NULL')

    # Fix module_versions.created_by
    op.drop_constraint('module_versions_created_by_fkey', 'module_versions', type_='foreignkey')
    op.create_foreign_key('module_versions_created_by_fkey', 'module_versions', 'users', ['created_by'], ['id'], ondelete='SET NULL')

    # Fix module_dependencies.created_by
    op.drop_constraint('module_dependencies_created_by_fkey', 'module_dependencies', type_='foreignkey')
    op.create_foreign_key('module_dependencies_created_by_fkey', 'module_dependencies', 'users', ['created_by'], ['id'], ondelete='SET NULL')


def downgrade():
    # Reverse module_dependencies.created_by
    op.drop_constraint('module_dependencies_created_by_fkey', 'module_dependencies', type_='foreignkey')
    op.create_foreign_key('module_dependencies_created_by_fkey', 'module_dependencies', 'users', ['created_by'], ['id'])

    # Reverse module_versions.created_by
    op.drop_constraint('module_versions_created_by_fkey', 'module_versions', type_='foreignkey')
    op.create_foreign_key('module_versions_created_by_fkey', 'module_versions', 'users', ['created_by'], ['id'])

    # Reverse modules.created_by and updated_by
    op.drop_constraint('modules_created_by_fkey', 'modules', type_='foreignkey')
    op.drop_constraint('modules_updated_by_fkey', 'modules', type_='foreignkey')
    op.create_foreign_key('modules_created_by_fkey', 'modules', 'users', ['created_by'], ['id'])
    op.create_foreign_key('modules_updated_by_fkey', 'modules', 'users', ['updated_by'], ['id'])
