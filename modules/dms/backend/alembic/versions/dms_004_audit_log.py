"""E3 Access Control: append-only DMS audit trail.

Adds dms_audit_log (tenant-scoped, RLS) plus a trigger that blocks UPDATE/DELETE
so the trail is tamper-evident even against a BYPASSRLS role.

Revision ID: dms_004
Revises: dms_003
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "dms_004"
down_revision = "dms_003"
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
        "dms_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("detail", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_dms_audit_tenant_time", "dms_audit_log", ["tenant_id", "created_at"])
    op.create_index("ix_dms_audit_entity", "dms_audit_log", ["tenant_id", "entity_type", "entity_id"])
    _tenant_rls("dms_audit_log")

    # Append-only: block UPDATE/DELETE at the DB regardless of role/RLS bypass.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION dms_audit_no_mutate() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'dms_audit_log is append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER dms_audit_log_append_only
        BEFORE UPDATE OR DELETE ON dms_audit_log
        FOR EACH ROW EXECUTE FUNCTION dms_audit_no_mutate();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS dms_audit_log_append_only ON dms_audit_log")
    op.execute("DROP FUNCTION IF EXISTS dms_audit_no_mutate()")
    op.execute("DROP POLICY IF EXISTS dms_audit_log_tenant_isolation ON dms_audit_log")
    op.drop_table("dms_audit_log")
