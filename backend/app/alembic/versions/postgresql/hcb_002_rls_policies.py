"""Tenant-isolation RLS policies for hcb_002_rls_policies.py

Revision ID: hcb002
Revises: hcb001
"""
from __future__ import annotations
from alembic import op

revision = "hcb002"
down_revision = "hcb001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE hcb_invoices ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcb_invoices FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcb_invoices_tenant_isolation ON hcb_invoices USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcb_insurance_profiles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcb_insurance_profiles FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcb_insurance_profiles_tenant_isolation ON hcb_insurance_profiles USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcb_service_items ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcb_service_items FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcb_service_items_tenant_isolation ON hcb_service_items USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcb_invoice_lines ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcb_invoice_lines FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcb_invoice_lines_tenant_isolation ON hcb_invoice_lines USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcb_payments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcb_payments FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcb_payments_tenant_isolation ON hcb_payments USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcb_bpjs_exports ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcb_bpjs_exports FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcb_bpjs_exports_tenant_isolation ON hcb_bpjs_exports USING (tenant_id = current_setting('app.current_tenant_id', true))")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS hcb_invoices_tenant_isolation ON hcb_invoices;")
    op.execute("ALTER TABLE hcb_invoices DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcb_insurance_profiles_tenant_isolation ON hcb_insurance_profiles;")
    op.execute("ALTER TABLE hcb_insurance_profiles DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcb_service_items_tenant_isolation ON hcb_service_items;")
    op.execute("ALTER TABLE hcb_service_items DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcb_invoice_lines_tenant_isolation ON hcb_invoice_lines;")
    op.execute("ALTER TABLE hcb_invoice_lines DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcb_payments_tenant_isolation ON hcb_payments;")
    op.execute("ALTER TABLE hcb_payments DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcb_bpjs_exports_tenant_isolation ON hcb_bpjs_exports;")
    op.execute("ALTER TABLE hcb_bpjs_exports DISABLE ROW LEVEL SECURITY;")
