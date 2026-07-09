"""
hc_saas_04_branch_slug_rekey

Revision ID: hcsaas04
Revises: hcsaas03
Create Date: 2026-07-09

SaaS onboarding (epic-20 Feature 20.2) — Company-scope hc_branches slug uniqueness.
Under the shared SaaS tenant every clinic's branches share one tenant_id, so the
original UNIQUE(tenant_id, slug) would reject a second clinic reusing a common slug
(e.g. 'main'). Re-key to (platform_company_id, slug), partial on deleted_at IS NULL
so a slug frees up after soft-delete. Mirrors migrations/saas_phase5_branch_slug_rekey.sql.
Existing slugs are already distinct → safe on a live DB.
"""
from __future__ import annotations

from alembic import op

revision = "hcsaas04"
down_revision = "hcsaas03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE hc_branches DROP CONSTRAINT IF EXISTS uq_hc_branches_tenant_slug;")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_hc_branches_company_slug "
        "ON hc_branches (platform_company_id, slug) WHERE deleted_at IS NULL;"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_hc_branches_company_slug;")
    op.execute(
        "ALTER TABLE hc_branches ADD CONSTRAINT uq_hc_branches_tenant_slug "
        "UNIQUE (tenant_id, slug);"
    )
