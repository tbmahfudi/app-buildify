"""
Healthcare SDK — PostgreSQL Row Level Security (RLS) policy framework.

T-HC-007

These SQL templates are applied via Alembic migrations, not automatically.
Call apply_tenant_rls() or apply_branch_rls() from migration upgrade() functions.

Example Alembic migration usage::

    from modules.healthcare.sdk.rls_policies import apply_tenant_rls, apply_branch_rls

    def upgrade():
        # PHI tables — tenant-only isolation (patients belong to tenant, not a branch)
        apply_tenant_rls(op, "hc_patients")

        # Branch-scoped PHI tables
        apply_branch_rls(op, "hc_encounters")
        apply_branch_rls(op, "hc_appointments")
        apply_branch_rls(op, "hc_prescriptions")
        apply_branch_rls(op, "hc_lab_orders")
        apply_branch_rls(op, "hc_invoices")

Clinic owner bypass:
    The branch isolation policy allows ``current_setting('app.branch_id') = 'ALL'``.
    The healthcare_branch_session dependency sets this sentinel for clinic_owner users.
    This must be matched by the RLS policy (see HC_BRANCH_RLS_POLICY_SQL below).

Prerequisites:
    - The database role used by the application must have RLS bypass disabled
      (i.e. it must NOT be a PostgreSQL superuser, otherwise RLS is bypassed).
    - SET LOCAL app.tenant_id and app.branch_id must be called at the start of
      every transaction that touches PHI tables (done by healthcare_branch_session).
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# SQL template strings
# ---------------------------------------------------------------------------

HC_TENANT_RLS_POLICY_SQL = """ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
CREATE POLICY {table}_tenant_isolation ON {table}
  USING (tenant_id = current_setting('app.tenant_id', true));
"""
"""
Tenant-only RLS policy template.

Applied to ``hc_patients`` — patients belong to a tenant, not a specific branch.
Use format(table="hc_patients") or pass to apply_tenant_rls().

The 'true' flag in current_setting makes it return NULL (not an error) if the
session variable is not set — the policy then matches nothing (fail-closed).
"""

HC_BRANCH_RLS_POLICY_SQL = """ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
CREATE POLICY {table}_branch_isolation ON {table}
  USING (
    tenant_id = current_setting('app.tenant_id', true)
    AND (
      branch_id = current_setting('app.branch_id', true)
      OR current_setting('app.branch_id', true) = 'ALL'
    )
  );
"""
"""
Branch-scoped RLS policy template.

Applied to all PHI tables that carry a branch_id column:
  hc_encounters, hc_appointments, hc_prescriptions, hc_lab_orders, hc_invoices

Clinic owner bypass: ``current_setting('app.branch_id') = 'ALL'`` allows
cross-branch access without a per-row filter. This is intentional — the
healthcare_branch_session dependency only sets 'ALL' for verified clinic_owner users.
"""


# ---------------------------------------------------------------------------
# Alembic helper functions
# ---------------------------------------------------------------------------

def apply_tenant_rls(op, table: str) -> None:
    """
    Execute tenant-only RLS policy SQL for the given table.

    Intended for use inside Alembic ``upgrade()`` functions::

        def upgrade():
            apply_tenant_rls(op, "hc_patients")

    Args:
        op:    Alembic ``Operations`` context (``from alembic import op``).
        table: Name of the PostgreSQL table to apply the policy to.
    """
    sql = HC_TENANT_RLS_POLICY_SQL.format(table=table)
    op.execute(sql)


def apply_branch_rls(op, table: str) -> None:
    """
    Execute branch-scoped RLS policy SQL for the given table.

    Intended for use inside Alembic ``upgrade()`` functions::

        def upgrade():
            apply_branch_rls(op, "hc_encounters")

    Args:
        op:    Alembic ``Operations`` context (``from alembic import op``).
        table: Name of the PostgreSQL table to apply the policy to.
    """
    sql = HC_BRANCH_RLS_POLICY_SQL.format(table=table)
    op.execute(sql)


__all__ = [
    "HC_TENANT_RLS_POLICY_SQL",
    "HC_BRANCH_RLS_POLICY_SQL",
    "apply_tenant_rls",
    "apply_branch_rls",
]
