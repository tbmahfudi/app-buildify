"""add data_scope column to entity_definitions

Revision ID: pg_add_data_scope
Revises: pg_merge_all_heads
Create Date: 2026-02-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pg_add_data_scope'
down_revision = 'pg_merge_all_heads'
branch_labels = None
depends_on = None


def upgrade():
    # Add data_scope column with default 'tenant' (matches current behavior)
    op.add_column('entity_definitions',
        sa.Column('data_scope', sa.String(20), nullable=False, server_default='tenant')
    )

    # Add check constraint for valid values
    op.create_check_constraint(
        'ck_entity_definitions_data_scope',
        'entity_definitions',
        "data_scope IN ('platform', 'tenant', 'company', 'branch', 'department')"
    )

    # Add index for filtering by data_scope
    op.create_index('idx_entity_definitions_data_scope', 'entity_definitions', ['data_scope'])


def downgrade():
    op.drop_index('idx_entity_definitions_data_scope', table_name='entity_definitions')
    op.drop_constraint('ck_entity_definitions_data_scope', 'entity_definitions', type_='check')
    op.drop_column('entity_definitions', 'data_scope')
