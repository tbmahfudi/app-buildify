"""E2 Search & Discovery: saved searches (per user).

Revision ID: dms_008
Revises: dms_007
Create Date: 2026-07-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "dms_008"
down_revision = "dms_007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dms_saved_searches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("params", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_dms_saved_user", "dms_saved_searches", ["tenant_id", "user_id"])
    op.execute("ALTER TABLE dms_saved_searches ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dms_saved_searches FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY dms_saved_searches_tenant_isolation ON dms_saved_searches
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS dms_saved_searches_tenant_isolation ON dms_saved_searches")
    op.drop_table("dms_saved_searches")
