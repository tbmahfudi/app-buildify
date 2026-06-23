"""Tenant-isolation RLS policies for hcp_002_rls_policies.py

Revision ID: hcp002
Revises: hcp001
"""
from __future__ import annotations
from alembic import op

revision = "hcp002"
down_revision = "hcp001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE hcp_prescriptions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcp_prescriptions FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcp_prescriptions_tenant_isolation ON hcp_prescriptions USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcp_dispensing_records ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcp_dispensing_records FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcp_dispensing_records_tenant_isolation ON hcp_dispensing_records USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcp_medications ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcp_medications FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcp_medications_tenant_isolation ON hcp_medications USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcp_drug_interactions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcp_drug_interactions FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcp_drug_interactions_tenant_isolation ON hcp_drug_interactions USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcp_prescription_lines ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcp_prescription_lines FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcp_prescription_lines_tenant_isolation ON hcp_prescription_lines USING (tenant_id = current_setting('app.current_tenant_id', true))")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS hcp_prescriptions_tenant_isolation ON hcp_prescriptions;")
    op.execute("ALTER TABLE hcp_prescriptions DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcp_dispensing_records_tenant_isolation ON hcp_dispensing_records;")
    op.execute("ALTER TABLE hcp_dispensing_records DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcp_medications_tenant_isolation ON hcp_medications;")
    op.execute("ALTER TABLE hcp_medications DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcp_drug_interactions_tenant_isolation ON hcp_drug_interactions;")
    op.execute("ALTER TABLE hcp_drug_interactions DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcp_prescription_lines_tenant_isolation ON hcp_prescription_lines;")
    op.execute("ALTER TABLE hcp_prescription_lines DISABLE ROW LEVEL SECURITY;")
