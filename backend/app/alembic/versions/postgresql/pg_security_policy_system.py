"""Add comprehensive security policy system

Revision ID: pg_security_policy_system
Revises: pg_merge_all_heads
Create Date: 2025-11-10 00:00:00.000000

This migration adds:
- User security columns (password_changed_at, password_expires_at, etc.)
- password_history table
- login_attempts table
- account_lockouts table
- user_sessions table
- security_policies table (tenant-level configuration)
- notification_queue table (for async notifications)
- notification_config table (system and tenant-level)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'pg_security_policy_system'
down_revision = 'pg_merge_all_heads'
branch_labels = None
depends_on = None


def upgrade():
    # ========== Update users table with security columns ==========
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('password_expires_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('last_password_check_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('require_password_change', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('grace_logins_remaining', sa.Integer(), nullable=True))

    # Add indexes for security columns
    op.create_index('ix_users_locked_until', 'users', ['locked_until'])
    op.create_index('ix_users_password_expires_at', 'users', ['password_expires_at'])

    # ========== password_history table ==========
    op.create_table(
        'password_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_password_history_user_created', 'password_history', ['user_id', 'created_at'])

    # ========== login_attempts table ==========
    op.create_table(
        'login_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),  # Nullable for failed attempts with non-existent email
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True),  # IPv6 max length
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, index=True),
        sa.Column('failure_reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_login_attempts_email_created', 'login_attempts', ['email', 'created_at'])
    op.create_index('ix_login_attempts_ip_created', 'login_attempts', ['ip_address', 'created_at'])

    # ========== account_lockouts table ==========
    op.create_table(
        'account_lockouts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('locked_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('locked_until', sa.DateTime(), nullable=False, index=True),
        sa.Column('lockout_reason', sa.String(255), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), nullable=True),
        sa.Column('unlocked_by', postgresql.UUID(as_uuid=True), nullable=True),  # Admin who unlocked
        sa.Column('unlock_reason', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unlocked_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_account_lockouts_user_locked', 'account_lockouts', ['user_id', 'locked_until'])

    # ========== user_sessions table ==========
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('jti', sa.String(255), nullable=False, unique=True, index=True),  # JWT ID
        sa.Column('device_id', sa.String(255), nullable=True),
        sa.Column('device_name', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('last_activity', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_user_sessions_user_active', 'user_sessions', ['user_id', 'revoked_at', 'expires_at'])

    # ========== security_policies table (tenant-level config) ==========
    op.create_table(
        'security_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True, unique=True, index=True),  # NULL = system default
        sa.Column('policy_name', sa.String(100), nullable=False),
        sa.Column('policy_type', sa.String(50), nullable=False),  # 'password', 'session', 'lockout', 'notification'

        # Password policy fields
        sa.Column('password_min_length', sa.Integer(), nullable=True),
        sa.Column('password_max_length', sa.Integer(), nullable=True),
        sa.Column('password_require_uppercase', sa.Boolean(), nullable=True),
        sa.Column('password_require_lowercase', sa.Boolean(), nullable=True),
        sa.Column('password_require_digit', sa.Boolean(), nullable=True),
        sa.Column('password_require_special_char', sa.Boolean(), nullable=True),
        sa.Column('password_min_unique_chars', sa.Integer(), nullable=True),
        sa.Column('password_max_repeating_chars', sa.Integer(), nullable=True),
        sa.Column('password_allow_common', sa.Boolean(), nullable=True),
        sa.Column('password_allow_username', sa.Boolean(), nullable=True),
        sa.Column('password_history_count', sa.Integer(), nullable=True),
        sa.Column('password_expiration_days', sa.Integer(), nullable=True),
        sa.Column('password_expiration_warning_days', sa.Integer(), nullable=True),
        sa.Column('password_grace_logins', sa.Integer(), nullable=True),

        # Account lockout policy fields
        sa.Column('login_max_attempts', sa.Integer(), nullable=True),
        sa.Column('login_lockout_duration_min', sa.Integer(), nullable=True),
        sa.Column('login_lockout_type', sa.String(20), nullable=True),  # 'fixed', 'progressive'
        sa.Column('login_reset_attempts_after_min', sa.Integer(), nullable=True),
        sa.Column('login_notify_user_on_lockout', sa.Boolean(), nullable=True),

        # Session policy fields
        sa.Column('session_timeout_minutes', sa.Integer(), nullable=True),
        sa.Column('session_absolute_timeout_hours', sa.Integer(), nullable=True),
        sa.Column('session_max_concurrent', sa.Integer(), nullable=True),
        sa.Column('session_terminate_on_password_change', sa.Boolean(), nullable=True),

        # Password reset policy fields
        sa.Column('password_reset_token_expire_hours', sa.Integer(), nullable=True),
        sa.Column('password_reset_max_attempts', sa.Integer(), nullable=True),
        sa.Column('password_reset_notify_user', sa.Boolean(), nullable=True),

        # Metadata
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_security_policies_tenant_type', 'security_policies', ['tenant_id', 'policy_type'])

    # ========== notification_queue table (buffer for async notifications) ==========
    op.create_table(
        'notification_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('notification_type', sa.String(50), nullable=False, index=True),  # 'account_locked', 'password_expiring', 'password_changed', 'password_reset'
        sa.Column('delivery_method', sa.String(20), nullable=False),  # 'email', 'sms', 'webhook', 'push'
        sa.Column('recipient', sa.String(255), nullable=False),  # Email address, phone number, webhook URL, etc.
        sa.Column('subject', sa.String(255), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('template_data', sa.JSON(), nullable=True),  # JSON data for templating
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),  # 1-10, lower = higher priority
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', index=True),  # 'pending', 'processing', 'sent', 'failed', 'cancelled'
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True, index=True),  # For delayed notifications
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_notification_queue_status_priority', 'notification_queue', ['status', 'priority', 'scheduled_for'])

    # ========== notification_config table (system and tenant-level) ==========
    op.create_table(
        'notification_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True, unique=True, index=True),  # NULL = system default
        sa.Column('config_name', sa.String(100), nullable=False),

        # Notification settings per type
        sa.Column('account_locked_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('account_locked_methods', sa.JSON(), nullable=True),  # ['email', 'sms']
        sa.Column('password_expiring_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('password_expiring_methods', sa.JSON(), nullable=True),
        sa.Column('password_changed_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('password_changed_methods', sa.JSON(), nullable=True),
        sa.Column('password_reset_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('password_reset_methods', sa.JSON(), nullable=True),
        sa.Column('login_from_new_device_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('login_from_new_device_methods', sa.JSON(), nullable=True),

        # Delivery method configurations
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_from', sa.String(255), nullable=True),
        sa.Column('email_smtp_host', sa.String(255), nullable=True),
        sa.Column('email_smtp_port', sa.Integer(), nullable=True),
        sa.Column('email_smtp_user', sa.String(255), nullable=True),
        sa.Column('email_smtp_password', sa.String(255), nullable=True),
        sa.Column('email_use_tls', sa.Boolean(), nullable=True),

        sa.Column('sms_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sms_provider', sa.String(50), nullable=True),  # 'twilio', 'aws_sns', etc.
        sa.Column('sms_api_key', sa.String(255), nullable=True),
        sa.Column('sms_from_number', sa.String(20), nullable=True),

        sa.Column('webhook_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('webhook_auth_header', sa.String(255), nullable=True),

        # Metadata
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
    )

    # ========== password_reset_tokens table ==========
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('token_hash', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_password_reset_tokens_user_expires', 'password_reset_tokens', ['user_id', 'expires_at'])


def downgrade():
    # Drop tables in reverse order
    op.drop_index('ix_password_reset_tokens_user_expires', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')

    op.drop_table('notification_config')

    op.drop_index('ix_notification_queue_status_priority', table_name='notification_queue')
    op.drop_table('notification_queue')

    op.drop_index('ix_security_policies_tenant_type', table_name='security_policies')
    op.drop_table('security_policies')

    op.drop_index('ix_user_sessions_user_active', table_name='user_sessions')
    op.drop_table('user_sessions')

    op.drop_index('ix_account_lockouts_user_locked', table_name='account_lockouts')
    op.drop_table('account_lockouts')

    op.drop_index('ix_login_attempts_ip_created', table_name='login_attempts')
    op.drop_index('ix_login_attempts_email_created', table_name='login_attempts')
    op.drop_table('login_attempts')

    op.drop_index('ix_password_history_user_created', table_name='password_history')
    op.drop_table('password_history')

    # Drop user table columns
    op.drop_index('ix_users_password_expires_at', table_name='users')
    op.drop_index('ix_users_locked_until', table_name='users')
    op.drop_column('users', 'grace_logins_remaining')
    op.drop_column('users', 'require_password_change')
    op.drop_column('users', 'last_password_check_at')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'password_expires_at')
    op.drop_column('users', 'password_changed_at')
