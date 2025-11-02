"""Add missing fields to departments table

Revision ID: pg_add_department_fields
Revises: pg_add_branch_fields
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'pg_add_department_fields'
down_revision = 'pg_add_branch_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add description field
    op.add_column('departments', sa.Column('description', sa.Text(), nullable=True))

    # Add hierarchy field
    op.add_column('departments', sa.Column('parent_department_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add head of department field
    op.add_column('departments', sa.Column('head_user_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add indexes for the new foreign key columns
    op.create_index('ix_departments_parent_department_id', 'departments', ['parent_department_id'])

    # Add foreign key constraint for parent_department_id
    op.create_foreign_key(
        'fk_departments_parent_department_id',
        'departments', 'departments',
        ['parent_department_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_departments_parent_department_id', 'departments', type_='foreignkey')
    op.drop_index('ix_departments_parent_department_id', table_name='departments')
    op.drop_column('departments', 'head_user_id')
    op.drop_column('departments', 'parent_department_id')
    op.drop_column('departments', 'description')
