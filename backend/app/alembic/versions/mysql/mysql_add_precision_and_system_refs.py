"""Add precision and reference_table_name to field_definitions (MySQL)

Revision ID: mysql_add_precision_refs
Revises: mysql_m1n2o3p4q5r6
Create Date: 2026-01-25 00:00:00.000000

Adds precision and reference_table_name columns to field_definitions table:
- precision: For DECIMAL/NUMERIC types to specify total number of digits
- reference_table_name: For referencing system tables (users, tenants, etc.)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'mysql_add_precision_refs'
down_revision = 'mysql_m1n2o3p4q5r6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add precision and reference_table_name columns to field_definitions table.

    - precision: INTEGER - Total number of digits for DECIMAL(p,s) types
    - reference_table_name: VARCHAR(100) - Direct table name for system entity references
    """
    # Add precision column for DECIMAL/NUMERIC type configuration
    op.add_column('field_definitions',
                  sa.Column('precision', sa.Integer(), nullable=True))

    # Add reference_table_name for direct system table references
    op.add_column('field_definitions',
                  sa.Column('reference_table_name', sa.String(100), nullable=True))


def downgrade() -> None:
    """
    Remove precision and reference_table_name columns from field_definitions table.
    """
    # Remove reference_table_name column
    op.drop_column('field_definitions', 'reference_table_name')

    # Remove precision column
    op.drop_column('field_definitions', 'precision')
