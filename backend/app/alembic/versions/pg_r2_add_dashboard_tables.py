"""Add dashboard tables

Revision ID: pg_r2_add_dashboard_tables
Revises: pg_r1_add_report_tables
Create Date: 2025-11-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'pg_r2_add_dashboard_tables'
down_revision = 'pg_r1_add_report_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create dashboards table
    op.create_table(
        'dashboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('layout_type', sa.String(50), nullable=False, server_default='grid'),
        sa.Column('theme', sa.String(50), nullable=False, server_default='light'),
        sa.Column('global_parameters', sa.JSON(), nullable=True),
        sa.Column('global_filters', sa.JSON(), nullable=True),
        sa.Column('refresh_interval', sa.String(50), nullable=False, server_default='none'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('allowed_roles', sa.JSON(), nullable=True),
        sa.Column('allowed_users', sa.JSON(), nullable=True),
        sa.Column('show_header', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_filters', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('full_screen_mode', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dashboards_tenant_id', 'dashboards', ['tenant_id'])
    op.create_index('ix_dashboards_category', 'dashboards', ['category'])

    # Create dashboard_pages table
    op.create_table(
        'dashboard_pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dashboard_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('layout_config', sa.JSON(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboards.id'], ondelete='CASCADE')
    )
    op.create_index('ix_dashboard_pages_tenant_id', 'dashboard_pages', ['tenant_id'])
    op.create_index('ix_dashboard_pages_dashboard_id', 'dashboard_pages', ['dashboard_id'])

    # Create dashboard_widgets table
    op.create_table(
        'dashboard_widgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('page_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('widget_type', sa.String(50), nullable=False),
        sa.Column('report_definition_id', sa.Integer(), nullable=True),
        sa.Column('data_source_config', sa.JSON(), nullable=True),
        sa.Column('widget_config', sa.JSON(), nullable=True),
        sa.Column('chart_config', sa.JSON(), nullable=True),
        sa.Column('filter_mapping', sa.JSON(), nullable=True),
        sa.Column('position', sa.JSON(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('show_title', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_border', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('background_color', sa.String(20), nullable=True),
        sa.Column('auto_refresh', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('refresh_interval', sa.String(50), nullable=False, server_default='none'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['page_id'], ['dashboard_pages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['report_definition_id'], ['report_definitions.id'], ondelete='SET NULL')
    )
    op.create_index('ix_dashboard_widgets_tenant_id', 'dashboard_widgets', ['tenant_id'])
    op.create_index('ix_dashboard_widgets_page_id', 'dashboard_widgets', ['page_id'])

    # Create dashboard_shares table
    op.create_table(
        'dashboard_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dashboard_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('shared_with_user_id', sa.Integer(), nullable=True),
        sa.Column('shared_with_role_id', sa.Integer(), nullable=True),
        sa.Column('share_token', sa.String(255), nullable=True, unique=True),
        sa.Column('can_view', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_edit', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_share', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboards.id'], ondelete='CASCADE')
    )
    op.create_index('ix_dashboard_shares_tenant_id', 'dashboard_shares', ['tenant_id'])

    # Create dashboard_snapshots table
    op.create_table(
        'dashboard_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dashboard_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('snapshot_data', sa.JSON(), nullable=False),
        sa.Column('parameters_used', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboards.id'], ondelete='CASCADE')
    )
    op.create_index('ix_dashboard_snapshots_tenant_id', 'dashboard_snapshots', ['tenant_id'])

    # Create widget_data_cache table
    op.create_table(
        'widget_data_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('widget_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(255), nullable=False, unique=True),
        sa.Column('parameters_hash', sa.String(255), nullable=False),
        sa.Column('cached_data', sa.JSON(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['widget_id'], ['dashboard_widgets.id'], ondelete='CASCADE')
    )
    op.create_index('ix_widget_data_cache_tenant_id', 'widget_data_cache', ['tenant_id'])
    op.create_index('ix_widget_data_cache_cache_key', 'widget_data_cache', ['cache_key'])


def downgrade():
    op.drop_table('widget_data_cache')
    op.drop_table('dashboard_snapshots')
    op.drop_table('dashboard_shares')
    op.drop_table('dashboard_widgets')
    op.drop_table('dashboard_pages')
    op.drop_table('dashboards')
