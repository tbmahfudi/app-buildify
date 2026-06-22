"""
hcb_002_rls_policies

Revision ID: hcb002
Revises: hcb001
Create Date: 2026-06-21

Apply tenant + branch RLS to billing tables.
"""
from __future__ import annotations

from alembic import op
from modules.healthcare.sdk.rls_policies import apply_tenant_rls, apply_branch_rls

revision = "hcb002"
down_revision = "hcb001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # hcb_invoices -- branch-scoped RLS (tenant + branch)
    apply_branch_rls(op, "hcb_invoices")

    # hcb_insurance_profiles -- tenant-only RLS (patient not branch-scoped)
    apply_tenant_rls(op, "hcb_insurance_profiles")

    # hcb_service_items -- branch-level catalog
    apply_branch_rls(op, "hcb_service_items")

    # hcb_invoice_lines -- accessed via invoice, tenant-only RLS
    apply_tenant_rls(op, "hcb_invoice_lines")

    # hcb_payments -- branch-scoped RLS
    apply_branch_rls(op, "hcb_payments")

    # hcb_bpjs_exports -- branch-scoped RLS
    apply_branch_rls(op, "hcb_bpjs_exports")

    # Grants
    for table in ("hcb_service_items", "hcb_invoices", "hcb_invoice_lines",
                  "hcb_payments", "hcb_insurance_profiles", "hcb_bpjs_exports"):
        op.execute(f"GRANT SELECT ON {table} TO app_readonly_role;")
        op.execute(f"GRANT INSERT, UPDATE ON {table} TO app_user;")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS hcb_insurance_profiles_tenant_isolation ON hcb_insurance_profiles;")
    op.execute("ALTER TABLE hcb_insurance_profiles DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS hcb_invoices_branch_isolation ON hcb_invoices;")
    op.execute("ALTER TABLE hcb_invoices DISABLE ROW LEVEL SECURITY;")
