"""Create module service registry tables (Phase 4 Priority 2)

Revision ID: pg_module_services
Revises: pg_nocode_module_system
Create Date: 2026-01-20 10:00:00.000000

Creates tables for Cross-Module Service Access:
- module_services: Service registry for cross-module communication
- module_service_access_log: Audit log for service access
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision = 'pg_module_services'
down_revision = 'pg_nocode_module_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create module service registry tables.
    """

    # Create module_services table
    op.create_table(
        'module_services',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),

        # Module reference
        sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='CASCADE'), nullable=False),

        # Service definition
        sa.Column('service_name', sa.String(100), nullable=False),
        sa.Column('service_class', sa.String(200), nullable=False),
        sa.Column('service_version', sa.String(20), nullable=False, server_default='1.0.0'),

        # API contract
        sa.Column('methods', JSON, nullable=False, server_default='[]'),

        # Documentation
        sa.Column('description', sa.Text),

        # Status
        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),

        # Constraints
        sa.UniqueConstraint('module_id', 'service_name', 'service_version', name='unique_module_service'),
    )

    # Create indexes for module_services
    op.create_index('idx_module_services_module', 'module_services', ['module_id'])
    op.create_index('idx_module_services_name', 'module_services', ['service_name'])

    # Create module_service_access_log table
    op.create_table(
        'module_service_access_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),

        # Access details
        sa.Column('calling_module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='SET NULL')),
        sa.Column('service_id', UUID(as_uuid=True), sa.ForeignKey('module_services.id', ondelete='CASCADE'), nullable=False),
        sa.Column('method_name', sa.String(100), nullable=False),

        # Request context
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parameters', JSON),

        # Response
        sa.Column('success', sa.Boolean),
        sa.Column('error_message', sa.Text),
        sa.Column('execution_time_ms', sa.Integer),

        # Permissions
        sa.Column('permission_checked', sa.String(200)),

        # Audit
        sa.Column('accessed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes for module_service_access_log
    op.create_index('idx_service_access_calling_module', 'module_service_access_log', ['calling_module_id'])
    op.create_index('idx_service_access_service', 'module_service_access_log', ['service_id'])
    op.create_index('idx_service_access_time', 'module_service_access_log', ['accessed_at'])
    op.create_index('idx_service_access_tenant', 'module_service_access_log', ['tenant_id'])


def downgrade() -> None:
    """
    Drop module service registry tables.
    """

    # Drop module_service_access_log table
    op.drop_index('idx_service_access_tenant', 'module_service_access_log')
    op.drop_index('idx_service_access_time', 'module_service_access_log')
    op.drop_index('idx_service_access_service', 'module_service_access_log')
    op.drop_index('idx_service_access_calling_module', 'module_service_access_log')
    op.drop_table('module_service_access_log')

    # Drop module_services table
    op.drop_index('idx_module_services_name', 'module_services')
    op.drop_index('idx_module_services_module', 'module_services')
    op.drop_table('module_services')
