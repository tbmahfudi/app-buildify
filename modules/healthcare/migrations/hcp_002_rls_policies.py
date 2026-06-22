"""
hcp_002_rls_policies

Revision ID: hcp002
Revises: hcp001
Create Date: 2026-06-21

Apply RLS to pharmacy tables.
- hcp_prescriptions: branch-scoped (tenant + branch)
- hcp_dispensing_records: branch-scoped (tenant + branch)
- hcp_medications: tenant-scoped (catalog; branch filter at app layer)
- hcp_drug_interactions: tenant-scoped
- hcp_prescription_lines: tenant-scoped (accessed only via prescription join)
"""
from __future__ import annotations

from alembic import op
from modules.healthcare.sdk.rls_policies import apply_tenant_rls, apply_branch_rls

revision = "hcp002"
down_revision = "hcp001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Branch-scoped: prescriptions and dispensing are branch-level operations
    apply_branch_rls(op, "hcp_prescriptions")
    apply_branch_rls(op, "hcp_dispensing_records")

    # Tenant-scoped: medication catalog and interaction data are tenant-wide
    apply_tenant_rls(op, "hcp_medications")
    apply_tenant_rls(op, "hcp_drug_interactions")
    apply_tenant_rls(op, "hcp_prescription_lines")


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS hcp_prescription_lines_tenant_isolation "
        "ON hcp_prescription_lines;"
    )
    op.execute("ALTER TABLE hcp_prescription_lines DISABLE ROW LEVEL SECURITY;")

    op.execute(
        "DROP POLICY IF EXISTS hcp_drug_interactions_tenant_isolation "
        "ON hcp_drug_interactions;"
    )
    op.execute("ALTER TABLE hcp_drug_interactions DISABLE ROW LEVEL SECURITY;")

    op.execute(
        "DROP POLICY IF EXISTS hcp_medications_tenant_isolation ON hcp_medications;"
    )
    op.execute("ALTER TABLE hcp_medications DISABLE ROW LEVEL SECURITY;")

    op.execute(
        "DROP POLICY IF EXISTS hcp_dispensing_records_branch_isolation "
        "ON hcp_dispensing_records;"
    )
    op.execute("ALTER TABLE hcp_dispensing_records DISABLE ROW LEVEL SECURITY;")

    op.execute(
        "DROP POLICY IF EXISTS hcp_prescriptions_branch_isolation ON hcp_prescriptions;"
    )
    op.execute("ALTER TABLE hcp_prescriptions DISABLE ROW LEVEL SECURITY;")
