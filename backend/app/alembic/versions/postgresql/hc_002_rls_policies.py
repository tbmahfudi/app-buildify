"""
hc_002_rls_policies

Revision ID: hc002
Revises: hc001
"""
from __future__ import annotations
from alembic import op

revision = "hc002"
down_revision = "hc001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE hc_patients ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hc_patients FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY hc_patients_tenant_isolation ON hc_patients "
        "USING (tenant_id = current_setting('app.current_tenant_id', true))"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS hc_patients_tenant_isolation ON hc_patients;")
    op.execute("ALTER TABLE hc_patients DISABLE ROW LEVEL SECURITY;")
