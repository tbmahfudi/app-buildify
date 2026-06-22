"""
hcl_002_rls_policies

Revision ID: hcl002
Revises: hcl001
Create Date: 2026-06-21

Apply RLS to laboratory tables.
- hcl_lab_orders: branch-scoped (tenant + branch)
- hcl_specimens: branch-scoped (tenant + branch)
- hcl_results: branch-scoped (tenant + branch — order_id join enforces branch)
- hcl_test_panels: tenant-scoped (catalog; branch filter at app layer)
- hcl_order_lines: tenant-scoped (accessed only via order join)
"""
from __future__ import annotations

from alembic import op
from modules.healthcare.sdk.rls_policies import apply_tenant_rls, apply_branch_rls

revision = "hcl002"
down_revision = "hcl001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Branch-scoped: orders, specimens, and results are branch-level operations
    apply_branch_rls(op, "hcl_lab_orders")
    apply_branch_rls(op, "hcl_specimens")
    apply_branch_rls(op, "hcl_results")

    # Tenant-scoped: test panel catalog is tenant-wide; order lines accessed via join
    apply_tenant_rls(op, "hcl_test_panels")
    apply_tenant_rls(op, "hcl_order_lines")


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS hcl_order_lines_tenant_isolation ON hcl_order_lines;"
    )
    op.execute("ALTER TABLE hcl_order_lines DISABLE ROW LEVEL SECURITY;")

    op.execute(
        "DROP POLICY IF EXISTS hcl_test_panels_tenant_isolation ON hcl_test_panels;"
    )
    op.execute("ALTER TABLE hcl_test_panels DISABLE ROW LEVEL SECURITY;")

    op.execute(
        "DROP POLICY IF EXISTS hcl_results_branch_isolation ON hcl_results;"
    )
    op.execute("ALTER TABLE hcl_results DISABLE ROW LEVEL SECURITY;")

    op.execute(
        "DROP POLICY IF EXISTS hcl_specimens_branch_isolation ON hcl_specimens;"
    )
    op.execute("ALTER TABLE hcl_specimens DISABLE ROW LEVEL SECURITY;")

    op.execute(
        "DROP POLICY IF EXISTS hcl_lab_orders_branch_isolation ON hcl_lab_orders;"
    )
    op.execute("ALTER TABLE hcl_lab_orders DISABLE ROW LEVEL SECURITY;")
