"""Rename metadata column to extra_data in all models (PostgreSQL)"""
from alembic import op

revision = "pg_h2i3j4k5l6m7"
down_revision = "pg_g1h2i3j4k5l6"
branch_labels = None
depends_on = None

def upgrade():
    # Rename metadata to extra_data in tenants table
    op.alter_column('tenants', 'metadata', new_column_name='extra_data')

    # Rename metadata to extra_data in companies table
    op.alter_column('companies', 'metadata', new_column_name='extra_data')

    # Rename metadata to extra_data in branches table
    op.alter_column('branches', 'metadata', new_column_name='extra_data')

    # Rename metadata to extra_data in departments table
    op.alter_column('departments', 'metadata', new_column_name='extra_data')

    # Rename metadata to extra_data in users table
    op.alter_column('users', 'metadata', new_column_name='extra_data')

def downgrade():
    # Revert extra_data to metadata in users table
    op.alter_column('users', 'extra_data', new_column_name='metadata')

    # Revert extra_data to metadata in departments table
    op.alter_column('departments', 'extra_data', new_column_name='metadata')

    # Revert extra_data to metadata in branches table
    op.alter_column('branches', 'extra_data', new_column_name='metadata')

    # Revert extra_data to metadata in companies table
    op.alter_column('companies', 'extra_data', new_column_name='metadata')

    # Revert extra_data to metadata in tenants table
    op.alter_column('tenants', 'extra_data', new_column_name='metadata')
