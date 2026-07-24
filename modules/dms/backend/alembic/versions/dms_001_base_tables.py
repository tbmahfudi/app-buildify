"""DMS base tables: dms_documents (+ tenant RLS).

Revision ID: dms_001
Revises:
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "dms_001"
down_revision = None
branch_labels = ("dms",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dms_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column(
            "content_type",
            sa.String(length=255),
            nullable=False,
            server_default="application/octet-stream",
        ),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_dms_documents_tenant_id", "dms_documents", ["tenant_id"]
    )
    op.create_index(
        "ix_dms_documents_tenant_active",
        "dms_documents",
        ["tenant_id", "is_active"],
    )

    # Row-Level Security: fence rows to the caller's tenant. The module sets
    # `app.tenant_id` per request (see app/core/database.py). This is layer 2 of
    # the platform's two-layer isolation model — the service also filters by
    # tenant in code, since the `appuser` role may carry BYPASSRLS.
    op.execute("ALTER TABLE dms_documents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dms_documents FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY dms_documents_tenant_isolation ON dms_documents
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS dms_documents_tenant_isolation ON dms_documents")
    op.drop_index("ix_dms_documents_tenant_active", table_name="dms_documents")
    op.drop_index("ix_dms_documents_tenant_id", table_name="dms_documents")
    op.drop_table("dms_documents")
