"""E3 Access Control: external share links.

Adds dms_shares (tenant-scoped, RLS) — time-limited, optionally download-capped,
token-addressable links to a single document.

Revision ID: dms_005
Revises: dms_004
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "dms_005"
down_revision = "dms_004"
branch_labels = None
depends_on = None


def _tenant_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY {table}_tenant_isolation ON {table}
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )


def upgrade() -> None:
    op.create_table(
        "dms_shares",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "document_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dms_documents.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_downloads", sa.Integer(), nullable=True),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    # Token is the public credential — unique + indexed for O(1) resolution.
    op.create_index("uq_dms_shares_token", "dms_shares", ["token"], unique=True)
    op.create_index("ix_dms_shares_document", "dms_shares", ["tenant_id", "document_id"])
    _tenant_rls("dms_shares")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS dms_shares_tenant_isolation ON dms_shares")
    op.drop_table("dms_shares")
