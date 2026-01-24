"""Add field groups for organizing fields into collapsible sections

Revision ID: pg_field_groups
Revises: pg_week3_field_enhancements
Create Date: 2026-01-24 00:10:00.000000

Creates field_groups table for organizing fields into collapsible sections
and adds field_group_id column to field_definitions.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'pg_field_groups'
down_revision = 'pg_week3_field_enhancements'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create field_groups table and add field_group_id to field_definitions.
    """

    # Create field_groups table
    op.create_table(
        'field_groups',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('entity_definitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),

        # Display Configuration
        sa.Column('is_collapsible', sa.Boolean, server_default='true'),
        sa.Column('is_collapsed_default', sa.Boolean, server_default='false'),
        sa.Column('display_order', sa.Integer, server_default='0'),

        # Visibility Rules (same format as field visibility_rules)
        sa.Column('visibility_rules', JSONB, nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Metadata
        sa.Column('meta_data', JSONB, server_default='{}'),

        # Audit fields
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
    )

    # Create indexes
    op.create_index('idx_field_groups_entity', 'field_groups', ['entity_id'])
    op.create_index('idx_field_groups_display_order', 'field_groups', ['entity_id', 'display_order'])

    # Add field_group_id column to field_definitions
    op.add_column('field_definitions',
                  sa.Column('field_group_id', UUID(as_uuid=True),
                           sa.ForeignKey('field_groups.id', ondelete='SET NULL'),
                           nullable=True))

    # Create index on field_group_id
    op.create_index('idx_field_definitions_group', 'field_definitions', ['field_group_id'])


def downgrade() -> None:
    """
    Remove field_group_id from field_definitions and drop field_groups table.
    """
    # Drop index and column from field_definitions
    op.drop_index('idx_field_definitions_group', table_name='field_definitions')
    op.drop_column('field_definitions', 'field_group_id')

    # Drop indexes from field_groups
    op.drop_index('idx_field_groups_display_order', table_name='field_groups')
    op.drop_index('idx_field_groups_entity', table_name='field_groups')

    # Drop field_groups table
    op.drop_table('field_groups')
