"""Fix module registry foreign key cascades (PostgreSQL)

Revision ID: pg_fix_module_fk
Revises: pg_m1n2o3p4q5r6
Create Date: 2025-11-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "pg_fix_module_fk"
down_revision = "pg_m1n2o3p4q5r6"
branch_labels = None
depends_on = None


def upgrade():
    """
    Update foreign key constraints in module_registry and tenant_modules
    to use SET NULL on delete, preventing foreign key violations when
    users are deleted.
    """

    # Fix module_registry.installed_by_user_id
    op.drop_constraint(
        'fk_module_registry_installed_by_user',
        'module_registry',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_module_registry_installed_by_user',
        'module_registry', 'users',
        ['installed_by_user_id'], ['id'],
        ondelete='SET NULL'
    )

    # Fix tenant_modules.enabled_by_user_id
    op.drop_constraint(
        'fk_tenant_modules_enabled_by_user',
        'tenant_modules',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_tenant_modules_enabled_by_user',
        'tenant_modules', 'users',
        ['enabled_by_user_id'], ['id'],
        ondelete='SET NULL'
    )

    # Fix tenant_modules.disabled_by_user_id
    op.drop_constraint(
        'fk_tenant_modules_disabled_by_user',
        'tenant_modules',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_tenant_modules_disabled_by_user',
        'tenant_modules', 'users',
        ['disabled_by_user_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    """
    Revert foreign key constraints to not use SET NULL on delete.
    """

    # Revert module_registry.installed_by_user_id
    op.drop_constraint(
        'fk_module_registry_installed_by_user',
        'module_registry',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_module_registry_installed_by_user',
        'module_registry', 'users',
        ['installed_by_user_id'], ['id']
    )

    # Revert tenant_modules.enabled_by_user_id
    op.drop_constraint(
        'fk_tenant_modules_enabled_by_user',
        'tenant_modules',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_tenant_modules_enabled_by_user',
        'tenant_modules', 'users',
        ['enabled_by_user_id'], ['id']
    )

    # Revert tenant_modules.disabled_by_user_id
    op.drop_constraint(
        'fk_tenant_modules_disabled_by_user',
        'tenant_modules',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_tenant_modules_disabled_by_user',
        'tenant_modules', 'users',
        ['disabled_by_user_id'], ['id']
    )
