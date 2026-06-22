"""Replace broken multi-column unique constraint on module_activations with NULL-safe partial indexes

Revision ID: cc33dd44ee55
Revises: bb22cc33dd44
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa

revision = 'cc33dd44ee55'
down_revision = 'bb22cc33dd44'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the broken multi-column unique constraint (NULLs are never equal, so it does not enforce uniqueness)
    op.drop_constraint('unique_module_activation_scope', 'module_activations', type_='unique')

    # Drop duplicate idx_-prefixed indexes (ix_-prefixed equivalents already exist)
    op.drop_index('idx_module_activations_tenant', table_name='module_activations')
    op.drop_index('idx_module_activations_module', table_name='module_activations')
    op.drop_index('idx_module_activations_company', table_name='module_activations')

    # Add missing scope indexes (branch and department)
    op.create_index('ix_module_activations_branch_id', 'module_activations', ['branch_id'],
        postgresql_where=sa.text('branch_id IS NOT NULL'))
    op.create_index('ix_module_activations_department_id', 'module_activations', ['department_id'],
        postgresql_where=sa.text('department_id IS NOT NULL'))

    # Partial unique indexes that correctly handle NULLs across each scope level
    op.execute("""
        CREATE UNIQUE INDEX uq_module_activation_tenant
        ON module_activations (module_id, tenant_id)
        WHERE company_id IS NULL AND branch_id IS NULL AND department_id IS NULL
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_module_activation_company
        ON module_activations (module_id, tenant_id, company_id)
        WHERE company_id IS NOT NULL AND branch_id IS NULL AND department_id IS NULL
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_module_activation_branch
        ON module_activations (module_id, tenant_id, company_id, branch_id)
        WHERE branch_id IS NOT NULL AND department_id IS NULL
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_module_activation_department
        ON module_activations (module_id, tenant_id, company_id, branch_id, department_id)
        WHERE department_id IS NOT NULL
    """)


def downgrade():
    op.execute('DROP INDEX IF EXISTS uq_module_activation_tenant')
    op.execute('DROP INDEX IF EXISTS uq_module_activation_company')
    op.execute('DROP INDEX IF EXISTS uq_module_activation_branch')
    op.execute('DROP INDEX IF EXISTS uq_module_activation_department')
    op.drop_index('ix_module_activations_branch_id', table_name='module_activations')
    op.drop_index('ix_module_activations_department_id', table_name='module_activations')
    op.create_index('idx_module_activations_tenant', 'module_activations', ['tenant_id'])
    op.create_index('idx_module_activations_module', 'module_activations', ['module_id'])
    op.create_index('idx_module_activations_company', 'module_activations', ['company_id'])
    op.create_unique_constraint('unique_module_activation_scope', 'module_activations',
        ['module_id', 'tenant_id', 'company_id', 'branch_id', 'department_id'])
