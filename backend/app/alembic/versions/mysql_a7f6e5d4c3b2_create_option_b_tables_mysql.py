"""Create Option B tables (MySQL) - Metadata, Audit, Settings"""
from alembic import op
import sqlalchemy as sa

revision = "mysql_a7f6e5d4c3b2"
down_revision = "mysql_f6e5d4c3b2a1"
branch_labels = None
depends_on = None

def upgrade():
    # Entity Metadata
    op.create_table(
        'entity_metadata',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('entity_name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('table_config', sa.Text(), nullable=True),
        sa.Column('form_config', sa.Text(), nullable=True),
        sa.Column('permissions', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        mysql_engine='InnoDB', mysql_charset='utf8mb4'
    )
    op.create_index('ix_entity_metadata_entity_name', 'entity_metadata', ['entity_name'])
    
    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('tenant_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.String(length=36), nullable=True),
        sa.Column('changes', sa.Text(), nullable=True),
        sa.Column('context_info', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('request_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        mysql_engine='InnoDB', mysql_charset='utf8mb4'
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'])
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('ix_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_tenant_created', 'audit_logs', ['tenant_id', 'created_at'])
    
    # User Settings
    op.create_table(
        'user_settings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('theme', sa.String(length=20), nullable=True, server_default='light'),
        sa.Column('language', sa.String(length=10), nullable=True, server_default='en'),
        sa.Column('timezone', sa.String(length=50), nullable=True, server_default='UTC'),
        sa.Column('density', sa.String(length=20), nullable=True, server_default='normal'),
        sa.Column('preferences', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        mysql_engine='InnoDB', mysql_charset='utf8mb4'
    )
    op.create_index('ix_user_settings_user_id', 'user_settings', ['user_id'])
    op.create_unique_constraint('uq_user_settings', 'user_settings', ['user_id'])
    
    # Tenant Settings
    op.create_table(
        'tenant_settings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), nullable=False, unique=True),
        sa.Column('tenant_name', sa.String(length=255), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=True),
        sa.Column('secondary_color', sa.String(length=7), nullable=True),
        sa.Column('theme_config', sa.Text(), nullable=True),
        sa.Column('enabled_features', sa.Text(), nullable=True),
        sa.Column('settings', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        mysql_engine='InnoDB', mysql_charset='utf8mb4'
    )
    op.create_index('ix_tenant_settings_tenant_id', 'tenant_settings', ['tenant_id'])

def downgrade():
    op.drop_table('tenant_settings')
    op.drop_table('user_settings')
    op.drop_table('audit_logs')
    op.drop_table('entity_metadata')