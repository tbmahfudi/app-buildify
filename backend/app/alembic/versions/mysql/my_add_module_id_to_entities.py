"""Add module_id to entity_definitions

Revision ID: add_module_id_to_entities
Revises: remove_menu_icon_secondary
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_module_id_to_entities'
down_revision = 'remove_menu_icon_secondary'
branch_labels = None
depends_on = None


def upgrade():
    """Add module_id column to entity_definitions table"""

    # Add module_id column (CHAR(36) for UUID in MySQL)
    op.add_column('entity_definitions', sa.Column('module_id', sa.CHAR(36), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_entity_definitions_module_id',
        'entity_definitions',
        'nocode_modules',
        ['module_id'],
        ['id']
    )

    # Add index for better performance
    op.create_index(
        'ix_entity_definitions_module_id',
        'entity_definitions',
        ['module_id'],
        unique=False
    )


def downgrade():
    """Remove module_id column from entity_definitions table"""

    # Drop index
    op.drop_index('ix_entity_definitions_module_id', table_name='entity_definitions')

    # Drop foreign key constraint
    op.drop_constraint('fk_entity_definitions_module_id', 'entity_definitions', type_='foreignkey')

    # Drop module_id column
    op.drop_column('entity_definitions', 'module_id')
