"""Update departments unique constraint to include branch_id

Revision ID: pg_fix_dept_constraint
Revises: pg_add_department_fields
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pg_fix_dept_constraint'
down_revision = 'pg_add_department_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old constraint that only used (company_id, code)
    # This was too restrictive - it prevented same department code across different branches
    op.drop_constraint('uq_dept_code_per_company', 'departments', type_='unique')

    # Add new constraint that includes branch_id
    # This allows same department code in different branches of the same company
    # e.g., "STORE-MGT" can exist in NYC-01 and BOS-01 branches
    op.create_unique_constraint(
        'uq_dept_branch_code',
        'departments',
        ['tenant_id', 'company_id', 'branch_id', 'code']
    )


def downgrade():
    op.drop_constraint('uq_dept_branch_code', 'departments', type_='unique')
    op.create_unique_constraint(
        'uq_dept_code_per_company',
        'departments',
        ['company_id', 'code']
    )
