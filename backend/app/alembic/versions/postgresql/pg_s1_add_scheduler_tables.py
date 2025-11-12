"""Add scheduler tables

Revision ID: pg_s1_add_scheduler_tables
Revises: pg_merge_display_and_r3
Create Date: 2025-11-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'pg_s1_add_scheduler_tables'
down_revision = 'pg_merge_display_and_r3'
branch_labels = None
depends_on = None


def upgrade():
    # Create scheduler_configs table
    op.create_table(
        'scheduler_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_level', sa.Enum('SYSTEM', 'TENANT', 'COMPANY', 'BRANCH', name='configlevel'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_concurrent_jobs', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('default_timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('retry_delay_seconds', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('job_timeout_seconds', sa.Integer(), nullable=False, server_default='3600'),
        sa.Column('notify_on_failure', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_on_success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notification_recipients', sa.JSON(), nullable=True),
        sa.Column('extra_config', sa.JSON(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scheduler_configs_tenant_id', 'scheduler_configs', ['tenant_id'])
    op.create_index('ix_scheduler_configs_company_id', 'scheduler_configs', ['company_id'])
    op.create_index('ix_scheduler_configs_branch_id', 'scheduler_configs', ['branch_id'])

    # Create conditional unique indexes for different config levels
    op.execute("""
        CREATE UNIQUE INDEX idx_scheduler_config_system
        ON scheduler_configs(config_level)
        WHERE config_level = 'SYSTEM'
    """)

    op.execute("""
        CREATE UNIQUE INDEX idx_scheduler_config_tenant
        ON scheduler_configs(config_level, tenant_id)
        WHERE config_level = 'TENANT'
    """)

    op.execute("""
        CREATE UNIQUE INDEX idx_scheduler_config_company
        ON scheduler_configs(config_level, tenant_id, company_id)
        WHERE config_level = 'COMPANY'
    """)

    op.execute("""
        CREATE UNIQUE INDEX idx_scheduler_config_branch
        ON scheduler_configs(config_level, tenant_id, company_id, branch_id)
        WHERE config_level = 'BRANCH'
    """)

    # Create scheduler_jobs table
    op.create_table(
        'scheduler_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('job_type', sa.Enum('REPORT_GENERATION', 'DATA_SYNC', 'NOTIFICATION_BATCH', 'BACKUP', 'CLEANUP', 'CUSTOM', 'WEBHOOK', 'API_CALL', name='jobtype'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('cron_expression', sa.String(100), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('interval_seconds', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('handler_class', sa.String(255), nullable=True),
        sa.Column('handler_method', sa.String(100), nullable=True),
        sa.Column('job_parameters', sa.JSON(), nullable=True),
        sa.Column('max_runtime_seconds', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('retry_delay_seconds', sa.Integer(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'SKIPPED', name='jobstatus'), nullable=True),
        sa.Column('run_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['config_id'], ['scheduler_configs.id'], ondelete='CASCADE')
    )
    op.create_index('idx_scheduler_job_active', 'scheduler_jobs', ['is_active', 'next_run_at'])
    op.create_index('idx_scheduler_job_tenant', 'scheduler_jobs', ['tenant_id', 'is_active'])
    op.create_index('idx_scheduler_job_company', 'scheduler_jobs', ['company_id', 'is_active'])
    op.create_index('idx_scheduler_job_branch', 'scheduler_jobs', ['branch_id', 'is_active'])

    # Create scheduler_job_executions table
    op.create_table(
        'scheduler_job_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'SKIPPED', name='jobstatus'), nullable=False, server_default='PENDING'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('worker_id', sa.String(100), nullable=True),
        sa.Column('process_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['scheduler_jobs.id'], ondelete='CASCADE')
    )
    op.create_index('idx_scheduler_execution_status', 'scheduler_job_executions', ['status', 'scheduled_at'])
    op.create_index('idx_scheduler_execution_job', 'scheduler_job_executions', ['job_id', 'started_at'])
    op.create_index('ix_scheduler_job_executions_tenant_id', 'scheduler_job_executions', ['tenant_id'])
    op.create_index('ix_scheduler_job_executions_company_id', 'scheduler_job_executions', ['company_id'])
    op.create_index('ix_scheduler_job_executions_branch_id', 'scheduler_job_executions', ['branch_id'])

    # Create scheduler_job_logs table
    op.create_table(
        'scheduler_job_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('log_level', sa.String(20), nullable=False, server_default='INFO'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('log_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['execution_id'], ['scheduler_job_executions.id'], ondelete='CASCADE')
    )
    op.create_index('idx_scheduler_log_execution', 'scheduler_job_logs', ['execution_id', 'created_at'])


def downgrade():
    op.drop_table('scheduler_job_logs')
    op.drop_table('scheduler_job_executions')
    op.drop_table('scheduler_jobs')
    op.drop_table('scheduler_configs')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS jobstatus')
    op.execute('DROP TYPE IF EXISTS jobtype')
    op.execute('DROP TYPE IF EXISTS configlevel')
