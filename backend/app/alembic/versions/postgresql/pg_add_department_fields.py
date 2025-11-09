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
    # Check what columns exist before making changes
    from sqlalchemy import inspect
    from alembic import context
    conn = context.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('departments')]

    # Add description field if it doesn't exist
    if 'description' not in columns:
        op.add_column('departments', sa.Column('description', sa.Text(), nullable=True))

    # Handle parent_id -> parent_department_id rename or add
    if 'parent_id' in columns and 'parent_department_id' not in columns:
        # Rename existing parent_id column
        op.alter_column('departments', 'parent_id', new_column_name='parent_department_id')
    elif 'parent_department_id' not in columns:
        # Add new column if neither exists
        op.add_column('departments', sa.Column('parent_department_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_index('ix_departments_parent_department_id', 'departments', ['parent_department_id'])
        op.create_foreign_key(
            'fk_departments_parent_department_id',
            'departments', 'departments',
            ['parent_department_id'], ['id'],
            ondelete='SET NULL'
        )

    # Add head_user_id field if it doesn't exist
    if 'head_user_id' not in columns:
        op.add_column('departments', sa.Column('head_user_id', postgresql.UUID(as_uuid=True), nullable=True))


def downgrade():
    op.drop_constraint('fk_departments_parent_department_id', 'departments', type_='foreignkey')
    op.drop_index('ix_departments_parent_department_id', table_name='departments')
    op.drop_column('departments', 'head_user_id')
    op.drop_column('departments', 'parent_department_id')
    op.drop_column('departments', 'description')
