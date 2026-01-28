"""Add display_field column to field_definitions (MySQL)

Revision ID: mysql_add_display_field
Revises: mysql_security_policy_system
Create Date: 2026-01-28 00:00:00.000000

Adds display_field column to separate:
- reference_field: Column in referenced table for FK constraint (e.g., 'id', 'code')
- display_field: Column to display in UI dropdowns (e.g., 'name', 'full_name')
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'mysql_add_display_field'
down_revision = 'mysql_security_policy_system'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add display_field column to field_definitions table.
    This column specifies which field to show in UI dropdowns,
    separate from reference_field which is used for FK constraints.
    """
    op.add_column('field_definitions',
                  sa.Column('display_field', sa.String(100), nullable=True))


def downgrade():
    """
    Remove display_field column from field_definitions table.
    """
    op.drop_column('field_definitions', 'display_field')
