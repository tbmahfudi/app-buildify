"""Tenant-isolation RLS policies for hcl_002_rls_policies.py

Revision ID: hcl002
Revises: hcl001
"""
from __future__ import annotations
from alembic import op

revision = "hcl002"
down_revision = "hcl001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE hcl_lab_orders ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcl_lab_orders FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcl_lab_orders_tenant_isolation ON hcl_lab_orders USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcl_specimens ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcl_specimens FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcl_specimens_tenant_isolation ON hcl_specimens USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcl_results ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcl_results FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcl_results_tenant_isolation ON hcl_results USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcl_test_panels ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcl_test_panels FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcl_test_panels_tenant_isolation ON hcl_test_panels USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcl_order_lines ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcl_order_lines FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcl_order_lines_tenant_isolation ON hcl_order_lines USING (tenant_id = current_setting('app.current_tenant_id', true))")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS hcl_lab_orders_tenant_isolation ON hcl_lab_orders;")
    op.execute("ALTER TABLE hcl_lab_orders DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcl_specimens_tenant_isolation ON hcl_specimens;")
    op.execute("ALTER TABLE hcl_specimens DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcl_results_tenant_isolation ON hcl_results;")
    op.execute("ALTER TABLE hcl_results DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcl_test_panels_tenant_isolation ON hcl_test_panels;")
    op.execute("ALTER TABLE hcl_test_panels DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcl_order_lines_tenant_isolation ON hcl_order_lines;")
    op.execute("ALTER TABLE hcl_order_lines DISABLE ROW LEVEL SECURITY;")
