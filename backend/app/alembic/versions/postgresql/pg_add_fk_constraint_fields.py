"""Add FK constraint behavior fields to field_definitions

Revision ID: pg_add_fk_constraint
Revises: pg_nocode_child_nullable
Create Date: 2026-01-23 00:00:00.000000

Adds on_delete and on_update columns to field_definitions table to support
proper foreign key constraint definition for reference/lookup fields.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pg_add_fk_constraint'
down_revision = 'pg_nocode_child_nullable'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add on_delete and on_update columns to field_definitions table
    to support FK constraint behavior configuration.
    """
    # Add on_delete column with default 'NO ACTION'
    op.add_column('field_definitions',
                  sa.Column('on_delete', sa.String(20), server_default='NO ACTION'))

    # Add on_update column with default 'NO ACTION'
    op.add_column('field_definitions',
                  sa.Column('on_update', sa.String(20), server_default='NO ACTION'))


def downgrade() -> None:
    """
    Remove on_delete and on_update columns from field_definitions table.
    """
    # Remove on_update column
    op.drop_column('field_definitions', 'on_update')

    # Remove on_delete column
    op.drop_column('field_definitions', 'on_delete')
