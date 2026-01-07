"""Create template management tables for categories, versions, and packages

Revision ID: pg_template_management
Revises: pg_nocode_child_nullable
Create Date: 2026-01-07 01:00:00.000000

Creates tables for advanced template management:
- template_categories: Hierarchical categorization of templates
- template_versions: Version control and history tracking
- template_packages: Bundling and distribution of templates
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'pg_template_management'
down_revision = 'pg_nocode_child_nullable'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create template management tables.
    """

    # Create template_categories table
    op.create_table(
        'template_categories',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('icon', sa.String(50)),
        sa.Column('color', sa.String(50)),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('template_categories.id'), nullable=True),
        sa.Column('level', sa.Integer, default=0),
        sa.Column('path', sa.String(500)),
        sa.Column('category_type', sa.String(50), nullable=False),
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_system', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for template_categories
    op.create_index('idx_template_categories_code', 'template_categories', ['code'])
    op.create_index('idx_template_categories_type', 'template_categories', ['category_type'])
    op.create_index('idx_template_categories_parent', 'template_categories', ['parent_id'])
    op.create_index('idx_template_categories_path', 'template_categories', ['path'])

    # Create template_versions table
    op.create_table(
        'template_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('template_type', sa.String(50), nullable=False),
        sa.Column('template_id', UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('version_name', sa.String(100)),
        sa.Column('change_summary', sa.Text, nullable=False),
        sa.Column('change_type', sa.String(50)),
        sa.Column('changelog', sa.Text),
        sa.Column('template_snapshot', sa.Text, nullable=False),
        sa.Column('is_published', sa.Boolean, default=False),
        sa.Column('is_current', sa.Boolean, default=True),
        sa.Column('published_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
    )

    # Create indexes for template_versions
    op.create_index('idx_template_versions_template', 'template_versions', ['template_type', 'template_id'])
    op.create_index('idx_template_versions_version', 'template_versions', ['template_type', 'template_id', 'version_number'])
    op.create_index('idx_template_versions_current', 'template_versions', ['is_current'])

    # Create template_packages table
    op.create_table(
        'template_packages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('version', sa.String(50), server_default='1.0.0'),
        sa.Column('author', sa.String(200)),
        sa.Column('author_email', sa.String(255)),
        sa.Column('license', sa.String(100)),
        sa.Column('homepage_url', sa.String(500)),
        sa.Column('category_id', UUID(as_uuid=True), sa.ForeignKey('template_categories.id')),
        sa.Column('package_data', sa.Text, nullable=False),
        sa.Column('dependencies', sa.Text),
        sa.Column('install_count', sa.Integer, default=0),
        sa.Column('last_installed_at', sa.DateTime),
        sa.Column('is_published', sa.Boolean, default=False),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )

    # Create indexes for template_packages
    op.create_index('idx_template_packages_code', 'template_packages', ['code'])
    op.create_index('idx_template_packages_category', 'template_packages', ['category_id'])
    op.create_index('idx_template_packages_published', 'template_packages', ['is_published', 'is_active'])


def downgrade() -> None:
    """
    Drop template management tables.
    """

    # Drop template_packages table
    op.drop_index('idx_template_packages_published', 'template_packages')
    op.drop_index('idx_template_packages_category', 'template_packages')
    op.drop_index('idx_template_packages_code', 'template_packages')
    op.drop_table('template_packages')

    # Drop template_versions table
    op.drop_index('idx_template_versions_current', 'template_versions')
    op.drop_index('idx_template_versions_version', 'template_versions')
    op.drop_index('idx_template_versions_template', 'template_versions')
    op.drop_table('template_versions')

    # Drop template_categories table
    op.drop_index('idx_template_categories_path', 'template_categories')
    op.drop_index('idx_template_categories_parent', 'template_categories')
    op.drop_index('idx_template_categories_type', 'template_categories')
    op.drop_index('idx_template_categories_code', 'template_categories')
    op.drop_table('template_categories')
