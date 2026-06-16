"""enforce org tenant_id not null (companies, branches, departments)

Revision ID: ec859b2a490c
Revises: 009300f92b21
Create Date: 2026-06-15 18:45:01.879857

Background
----------
`Company`, `Branch`, and `Department` all declare
``tenant_id = Column(..., nullable=False)`` in the ORM, but on long-lived
databases the column had drifted to nullable, which let tenant-less org rows
exist (see DEF-001 — an orphan company with tenant_id=NULL caused
GET /api/v1/org/companies to 500 on response serialization).

This migration captures, in version control, the column-level guarantee that
matches the models so that fresh databases built via ``alembic upgrade head``
get it too. It was previously applied to the dev DB only as the one-off
``backend/scripts/fix_company_tenant_not_null.sql``.

The cleanup below removes only *childless* tenant-less rows (leaf-first), so a
tenant-less row that still has linked children is NOT silently deleted —
instead ``SET NOT NULL`` will fail loudly so an operator can investigate.
On a clean database these statements are harmless no-ops (no NULL rows exist).
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'ec859b2a490c'
down_revision = '009300f92b21'
branch_labels = None
depends_on = None

_TABLES = ("companies", "branches", "departments")


def upgrade() -> None:
    # 1) Repair drifted data, leaf-first so parents become childless in turn.
    op.execute("DELETE FROM departments WHERE tenant_id IS NULL")
    op.execute(
        "DELETE FROM branches b WHERE b.tenant_id IS NULL "
        "AND NOT EXISTS (SELECT 1 FROM departments d WHERE d.branch_id = b.id)"
    )
    op.execute(
        "DELETE FROM companies c WHERE c.tenant_id IS NULL "
        "AND NOT EXISTS (SELECT 1 FROM branches b WHERE b.company_id = c.id) "
        "AND NOT EXISTS (SELECT 1 FROM departments d WHERE d.company_id = c.id)"
    )

    # 2) Enforce the model invariant. Idempotent: SET NOT NULL on an already
    #    NOT NULL column is a no-op in PostgreSQL.
    for table in _TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET NOT NULL")


def downgrade() -> None:
    for table in _TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id DROP NOT NULL")
