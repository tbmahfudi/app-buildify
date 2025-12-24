"""Initial migration - create builder tables

Revision ID: 001_initial_builder
Revises:
Create Date: 2025-12-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'pg_001_initial_builder'
down_revision = 'pg_create_menu_items'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create builder_pages table
    op.create_table(
        'builder_pages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text),

        # Module association
        sa.Column('module_id', sa.String(36), nullable=True, index=True),
        sa.Column('module_name', sa.String(100), nullable=True),

        # Route configuration
        sa.Column('route_path', sa.String(500), nullable=False),

        # GrapeJS data (stored as JSON)
        sa.Column('grapejs_data', JSONB, nullable=False),

        # Generated outputs
        sa.Column('html_output', sa.Text),
        sa.Column('css_output', sa.Text),
        sa.Column('js_output', sa.Text),

        # Menu configuration
        sa.Column('menu_id', sa.String(36), nullable=True),
        sa.Column('menu_label', sa.String(255)),
        sa.Column('menu_icon', sa.String(100)),
        sa.Column('menu_parent', sa.String(100)),
        sa.Column('menu_order', sa.Integer),
        sa.Column('show_in_menu', sa.Boolean, default=True, nullable=False),

        # Permission configuration
        sa.Column('permission_id', sa.String(36), nullable=True),
        sa.Column('permission_code', sa.String(255)),
        sa.Column('permission_scope', sa.String(50), default='company'),

        # Publishing
        sa.Column('published', sa.Boolean, default=False, nullable=False, index=True),
        sa.Column('published_at', sa.DateTime),
        sa.Column('published_by', sa.String(36)),

        # Metadata
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('updated_by', sa.String(36)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),

        sa.UniqueConstraint('tenant_id', 'slug', name='uq_builder_page_slug'),
        sa.UniqueConstraint('tenant_id', 'route_path', name='uq_builder_page_route'),
    )

    # Create builder_page_versions table for version control
    op.create_table(
        'builder_page_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('page_id', sa.String(36), sa.ForeignKey('builder_pages.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('grapejs_data', JSONB, nullable=False),
        sa.Column('html_output', sa.Text),
        sa.Column('css_output', sa.Text),
        sa.Column('js_output', sa.Text),
        sa.Column('commit_message', sa.String(500)),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),

        sa.UniqueConstraint('page_id', 'version_number', name='uq_page_version'),
    )

    # Create indices for better query performance
    op.create_index('idx_builder_pages_tenant_module', 'builder_pages', ['tenant_id', 'module_name'])
    op.create_index('idx_builder_pages_published', 'builder_pages', ['tenant_id', 'published'])
    op.create_index('idx_builder_versions_page', 'builder_page_versions', ['page_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_builder_versions_page')
    op.drop_index('idx_builder_pages_published')
    op.drop_index('idx_builder_pages_tenant_module')
    op.drop_table('builder_page_versions')
    op.drop_table('builder_pages')
