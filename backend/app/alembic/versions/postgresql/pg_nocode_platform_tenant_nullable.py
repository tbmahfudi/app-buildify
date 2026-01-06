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
    # Alter entity_definitions table
    op.alter_column('entity_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    # Alter workflow_definitions table
    op.alter_column('workflow_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    # Alter automation_rules table
    op.alter_column('automation_rules', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    # Alter lookup_configurations table
    op.alter_column('lookup_configurations', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=True)

    # Note: Child tables (workflow_states, workflow_transitions, field_definitions, etc.)
    # remain tenant-specific as they inherit tenant context from their parent


def downgrade() -> None:
    """
    Revert tenant_id to non-nullable.
    WARNING: This will fail if platform-level records (tenant_id=NULL) exist.
    """
    # Revert lookup_configurations
    op.alter_column('lookup_configurations', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    # Revert automation_rules
    op.alter_column('automation_rules', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    # Revert workflow_definitions
    op.alter_column('workflow_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)

    # Revert entity_definitions
    op.alter_column('entity_definitions', 'tenant_id',
                    existing_type=UUID(as_uuid=True),
                    nullable=False)
