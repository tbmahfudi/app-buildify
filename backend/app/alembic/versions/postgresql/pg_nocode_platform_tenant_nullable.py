"""Make tenant_id nullable for platform-level no-code configurations

Revision ID: pg_nocode_tenant_nullable
Revises: pg_phase1_nocode
Create Date: 2026-01-06 00:00:00.000000

Allows no-code configurations to be defined at platform level (tenant_id=NULL)
or tenant level (tenant_id=specific tenant). Platform-level configurations are
shared across all tenants, while tenant-level are tenant-specific.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'pg_nocode_tenant_nullable'
down_revision = 'pg_phase1_nocode'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Make tenant_id nullable in no-code platform tables to support
    platform-level (shared) configurations.
    """
    # Parent tables - Main no-code configuration tables
    op.alter_column('entity_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    op.alter_column('workflow_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    op.alter_column('automation_rules', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    op.alter_column('lookup_configurations', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    # Child tables - Data Model related
    op.alter_column('field_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    op.alter_column('relationship_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    op.alter_column('index_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    op.alter_column('entity_migrations', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    # Child tables - Workflow related
    op.alter_column('workflow_states', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    op.alter_column('workflow_transitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    op.alter_column('workflow_instances', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    op.alter_column('workflow_history', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    # Child tables - Automation related
    op.alter_column('automation_executions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    op.alter_column('webhook_configs', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    # Child tables - Lookup related
    op.alter_column('lookup_cache', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    op.alter_column('cascading_lookup_rules', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)


def downgrade() -> None:
    """
    Revert tenant_id to non-nullable.
    WARNING: This will fail if platform-level records (tenant_id=NULL) exist.
    """
    # Revert child tables - Lookup related
    op.alter_column('cascading_lookup_rules', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    op.alter_column('lookup_cache', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    # Revert child tables - Automation related
    op.alter_column('webhook_configs', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    op.alter_column('automation_executions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    # Revert child tables - Workflow related
    op.alter_column('workflow_history', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    op.alter_column('workflow_instances', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    op.alter_column('workflow_transitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    op.alter_column('workflow_states', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    # Revert child tables - Data Model related
    op.alter_column('entity_migrations', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    op.alter_column('index_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    op.alter_column('relationship_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    op.alter_column('field_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    # Revert parent tables
    op.alter_column('lookup_configurations', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    op.alter_column('automation_rules', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    op.alter_column('workflow_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    op.alter_column('entity_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)
