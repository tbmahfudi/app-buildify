"""Make tenant_id nullable in no-code child tables

Revision ID: pg_nocode_child_nullable
Revises: pg_nocode_tenant_nullable
Create Date: 2026-01-07 00:00:00.000000

Extends platform-level support to child tables of no-code configurations.
This allows fields, states, transitions, and other child records to inherit
the platform-level scope from their parent records.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'pg_nocode_child_nullable'
down_revision = 'pg_nocode_tenant_nullable'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Make tenant_id nullable in child tables to support platform-level
    configurations that inherit from parent records.
    """

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
    Revert tenant_id to non-nullable in child tables.
    WARNING: This will fail if platform-level child records (tenant_id=NULL) exist.
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
