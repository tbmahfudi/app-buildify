"""Generalize workflow_instances to run against a module-owned record.

The workflow engine could only attach an instance to a no-code entity
(entity_id NOT NULL FK to entity_definitions). To let platform *modules*
(e.g. the standalone DMS) drive approvals on their own records, make entity_id
nullable and add `source_module`; the existing (already generic) `record_id`
holds the module record's id.

revision = "pg_workflow_module_records"
down_revision = "pg_user_trusted_devices"
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "pg_workflow_module_records"
down_revision = "pg_user_trusted_devices"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "workflow_instances", "entity_id",
        existing_type=UUID(as_uuid=True), nullable=True,
    )
    op.add_column(
        "workflow_instances",
        sa.Column("source_module", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_workflow_instances_source", "workflow_instances",
        ["source_module", "record_id"],
    )


def downgrade():
    op.drop_index("ix_workflow_instances_source", table_name="workflow_instances")
    op.drop_column("workflow_instances", "source_module")
    # entity_id is left nullable: module-owned instances may have NULL, so we
    # cannot safely re-impose NOT NULL here.
