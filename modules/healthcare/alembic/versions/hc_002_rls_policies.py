"""
hc_002_rls_policies

Revision ID: hc002
Revises: hc001
Create Date: 2026-06-21

Applies PostgreSQL Row Level Security policies to PHI tables using the
apply_tenant_rls / apply_branch_rls helpers from modules.healthcare.sdk.rls_policies.
"""
from __future__ import annotations

from alembic import op
from modules.healthcare.sdk.rls_policies import apply_tenant_rls, apply_branch_rls

revision = "hc002"
down_revision = "hc001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # hc_patients — tenant-only RLS (patient belongs to clinic, not branch)
    apply_tenant_rls(op, "hc_patients")

    # hc_encounters — branch-scoped RLS
    apply_branch_rls(op, "hc_encounters")

    # hc_clinic_reviews — branch-scoped RLS
    apply_branch_rls(op, "hc_clinic_reviews")

    # Grant SELECT to app_readonly_role on all PHI tables
    op.execute("GRANT SELECT ON hc_patients TO app_readonly_role;")
    op.execute("GRANT SELECT ON hc_encounters TO app_readonly_role;")
    op.execute("GRANT SELECT ON hc_clinic_reviews TO app_readonly_role;")

    # Grant INSERT, UPDATE to app_user on PHI tables (not DELETE — handled by table design)
    op.execute("GRANT INSERT, UPDATE ON hc_patients TO app_user;")
    op.execute("GRANT INSERT, UPDATE ON hc_encounters TO app_user;")
    op.execute("GRANT INSERT, UPDATE ON hc_clinic_reviews TO app_user;")


def downgrade() -> None:
    # Drop policies and disable RLS in reverse order
    op.execute("DROP POLICY IF EXISTS hc_clinic_reviews_branch_isolation ON hc_clinic_reviews;")
    op.execute("ALTER TABLE hc_clinic_reviews DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS hc_encounters_branch_isolation ON hc_encounters;")
    op.execute("ALTER TABLE hc_encounters DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS hc_patients_tenant_isolation ON hc_patients;")
    op.execute("ALTER TABLE hc_patients DISABLE ROW LEVEL SECURITY;")
