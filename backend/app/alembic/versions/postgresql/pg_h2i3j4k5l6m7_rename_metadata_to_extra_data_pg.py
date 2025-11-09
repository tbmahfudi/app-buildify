"""Rename metadata column to extra_data in all models (PostgreSQL)"""
from alembic import op
from sqlalchemy import inspect

revision = "pg_h2i3j4k5l6m7"
down_revision = "pg_g1h2i3j4k5l6"
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def upgrade():
    """
    Rename metadata to extra_data in tables if the metadata column exists.

    Note: In the PostgreSQL migration chain, tables were created with 'extra_data'
    from the start, so this migration is a no-op for fresh databases. It only applies
    to databases that were created with the older schema that used 'metadata'.
    """

    tables = ['tenants', 'companies', 'branches', 'departments', 'users']

    for table in tables:
        if column_exists(table, 'metadata'):
            # Column exists as 'metadata', rename it to 'extra_data'
            print(f"Renaming '{table}.metadata' to '{table}.extra_data'")
            op.alter_column(table, 'metadata', new_column_name='extra_data')
        elif column_exists(table, 'extra_data'):
            # Column already exists as 'extra_data', no action needed
            print(f"Column '{table}.extra_data' already exists, skipping rename")
        else:
            # Neither column exists, skip
            print(f"Neither '{table}.metadata' nor '{table}.extra_data' exists, skipping")

def downgrade():
    """
    Revert extra_data to metadata in tables if needed.
    """

    tables = ['users', 'departments', 'branches', 'companies', 'tenants']

    for table in tables:
        if column_exists(table, 'extra_data'):
            print(f"Renaming '{table}.extra_data' back to '{table}.metadata'")
            op.alter_column(table, 'extra_data', new_column_name='metadata')
        else:
            print(f"Column '{table}.extra_data' does not exist, skipping")
