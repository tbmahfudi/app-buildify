"""E3 Access Control: row-level ACLs + privacy flags.

Adds `is_private` to folders and documents and a `dms_acls` table of per-resource
grants (view/edit/manage) to a user or group. A resource is ACL-restricted when
it — or any ancestor folder — is private; otherwise coarse RBAC governs.

Revision ID: dms_006
Revises: dms_005
Create Date: 2026-07-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "dms_006"
down_revision = "dms_005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("dms_folders", sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("dms_documents", sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "dms_acls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_type", sa.String(length=16), nullable=False),   # folder | document
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("principal_type", sa.String(length=16), nullable=False),  # user | group
        sa.Column("principal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("capability", sa.String(length=16), nullable=False),      # view | edit | manage
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_dms_acls_resource", "dms_acls", ["tenant_id", "resource_type", "resource_id"]
    )
    op.create_index(
        "ix_dms_acls_principal", "dms_acls", ["tenant_id", "principal_type", "principal_id"]
    )
    # One grant row per (resource, principal); capability is updated in place.
    op.create_index(
        "uq_dms_acls_resource_principal", "dms_acls",
        ["tenant_id", "resource_type", "resource_id", "principal_type", "principal_id"],
        unique=True,
    )
    op.execute("ALTER TABLE dms_acls ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dms_acls FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY dms_acls_tenant_isolation ON dms_acls
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS dms_acls_tenant_isolation ON dms_acls")
    op.drop_table("dms_acls")
    op.drop_column("dms_documents", "is_private")
    op.drop_column("dms_folders", "is_private")
