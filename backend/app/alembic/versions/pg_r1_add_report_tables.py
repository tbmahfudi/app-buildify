"""Add report tables

Revision ID: pg_r1_add_report_tables
Revises: pg_merge_all_heads
Create Date: 2025-11-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'pg_r1_add_report_tables'
down_revision = 'pg_merge_all_heads'
branch_labels = None
depends_on = None


def upgrade():
    # Create report_definitions table
    op.create_table(
        'report_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('report_type', sa.String(50), nullable=False, server_default='tabular'),
        sa.Column('base_entity', sa.String(100), nullable=False),
        sa.Column('query_config', sa.JSON(), nullable=True),
        sa.Column('columns_config', sa.JSON(), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('visualization_config', sa.JSON(), nullable=True),
        sa.Column('formatting_rules', sa.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('allowed_roles', sa.JSON(), nullable=True),
        sa.Column('allowed_users', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_report_definitions_tenant_id', 'report_definitions', ['tenant_id'])
    op.create_index('ix_report_definitions_category', 'report_definitions', ['category'])

    # Create report_executions table
    op.create_table(
        'report_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('report_definition_id', sa.Integer(), nullable=False),
        sa.Column('executed_by', sa.Integer(), nullable=False),
        sa.Column('executed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('parameters_used', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('export_format', sa.String(50), nullable=True),
        sa.Column('export_file_path', sa.String(500), nullable=True),
        sa.Column('export_file_size', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['report_definition_id'], ['report_definitions.id'], ondelete='CASCADE')
    )
    op.create_index('ix_report_executions_tenant_id', 'report_executions', ['tenant_id'])
    op.create_index('ix_report_executions_report_id', 'report_executions', ['report_definition_id'])

    # Create report_schedules table
    op.create_table(
        'report_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('report_definition_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('cron_expression', sa.String(100), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('default_parameters', sa.JSON(), nullable=True),
        sa.Column('export_format', sa.String(50), nullable=False, server_default='pdf'),
        sa.Column('email_recipients', sa.JSON(), nullable=True),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('storage_path', sa.String(500), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['report_definition_id'], ['report_definitions.id'], ondelete='CASCADE')
    )
    op.create_index('ix_report_schedules_tenant_id', 'report_schedules', ['tenant_id'])

    # Create report_templates table
    op.create_table(
        'report_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('template_config', sa.JSON(), nullable=False),
        sa.Column('preview_image_url', sa.String(500), nullable=True),
        sa.Column('is_builtin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_report_templates_category', 'report_templates', ['category'])

    # Create report_cache table
    op.create_table(
        'report_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('report_definition_id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(255), nullable=False),
        sa.Column('parameters_hash', sa.String(255), nullable=False),
        sa.Column('cached_data', sa.JSON(), nullable=True),
        sa.Column('cached_file_path', sa.String(500), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['report_definition_id'], ['report_definitions.id'], ondelete='CASCADE')
    )
    op.create_index('ix_report_cache_tenant_id', 'report_cache', ['tenant_id'])
    op.create_index('ix_report_cache_cache_key', 'report_cache', ['cache_key'], unique=True)


def downgrade():
    op.drop_table('report_cache')
    op.drop_table('report_templates')
    op.drop_table('report_schedules')
    op.drop_table('report_executions')
    op.drop_table('report_definitions')
