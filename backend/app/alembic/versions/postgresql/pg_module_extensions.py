"""Create module extension framework tables (Phase 4 Priority 3)

Revision ID: pg_module_extensions
Revises: pg_module_services
Create Date: 2026-01-20 11:00:00.000000

Creates tables for Module Extension Framework:
- module_entity_extensions: Entity field extensions
- module_screen_extensions: Screen UI extensions (tabs, sections, widgets, actions)
- module_menu_extensions: Menu item extensions
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision = 'pg_module_extensions'
down_revision = 'pg_module_services'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create module extension framework tables.
    """

    # Create module_entity_extensions table
    op.create_table(
        'module_entity_extensions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),

        # Extension source
        sa.Column('extending_module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='CASCADE'), nullable=False),

        # Extension target
        sa.Column('target_module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_entity_id', UUID(as_uuid=True), sa.ForeignKey('entity_definitions.id', ondelete='CASCADE'), nullable=False),

        # Extension details
        sa.Column('extension_table', sa.String(100), nullable=False),
        sa.Column('extension_fields', JSON, nullable=False, server_default='[]'),

        # Status
        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),

        # Constraints
        sa.UniqueConstraint('extending_module_id', 'target_entity_id', name='unique_module_entity_extension'),
    )

    # Create indexes for module_entity_extensions
    op.create_index('idx_entity_extensions_extending', 'module_entity_extensions', ['extending_module_id'])
    op.create_index('idx_entity_extensions_target', 'module_entity_extensions', ['target_entity_id'])

    # Create module_screen_extensions table
    op.create_table(
        'module_screen_extensions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),

        # Extension source
        sa.Column('extending_module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='CASCADE'), nullable=False),

        # Extension target
        sa.Column('target_module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_screen', sa.String(100), nullable=False),

        # Extension details
        sa.Column('extension_type', sa.String(50), nullable=False),
        sa.Column('extension_config', JSON, nullable=False),
        sa.Column('position', sa.Integer, server_default='999'),

        # Status
        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Permissions
        sa.Column('required_permission', sa.String(200)),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),

        # Constraints
        sa.CheckConstraint(
            "extension_type IN ('tab', 'section', 'widget', 'action')",
            name='valid_screen_extension_type'
        ),
    )

    # Create indexes for module_screen_extensions
    op.create_index('idx_screen_extensions_target', 'module_screen_extensions', ['target_module_id', 'target_screen'])
    op.create_index('idx_screen_extensions_extending', 'module_screen_extensions', ['extending_module_id'])

    # Create module_menu_extensions table
    op.create_table(
        'module_menu_extensions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),

        # Extension source
        sa.Column('extending_module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='CASCADE'), nullable=False),

        # Extension target (NULL = add to root menu)
        sa.Column('target_module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='CASCADE')),
        sa.Column('target_menu_item', sa.String(100)),

        # Menu item details
        sa.Column('menu_config', JSON, nullable=False),
        sa.Column('position', sa.Integer, server_default='999'),

        # Status
        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Permissions
        sa.Column('required_permission', sa.String(200)),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )

    # Create indexes for module_menu_extensions
    op.create_index('idx_menu_extensions_target', 'module_menu_extensions', ['target_module_id'])
    op.create_index('idx_menu_extensions_extending', 'module_menu_extensions', ['extending_module_id'])


def downgrade() -> None:
    """
    Drop module extension framework tables.
    """

    # Drop module_menu_extensions table
    op.drop_index('idx_menu_extensions_extending', 'module_menu_extensions')
    op.drop_index('idx_menu_extensions_target', 'module_menu_extensions')
    op.drop_table('module_menu_extensions')

    # Drop module_screen_extensions table
    op.drop_index('idx_screen_extensions_extending', 'module_screen_extensions')
    op.drop_index('idx_screen_extensions_target', 'module_screen_extensions')
    op.drop_table('module_screen_extensions')

    # Drop module_entity_extensions table
    op.drop_index('idx_entity_extensions_target', 'module_entity_extensions')
    op.drop_index('idx_entity_extensions_extending', 'module_entity_extensions')
    op.drop_table('module_entity_extensions')
