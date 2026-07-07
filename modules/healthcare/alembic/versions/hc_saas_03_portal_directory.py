"""
hc_saas_03_portal_directory

Revision ID: hcsaas03
Revises: hcsaas02
Create Date: 2026-07-08

SaaS onboarding (epic-20 Feature 20.4) — public clinic-directory opt-in flags. Adds
companies.public_listing (opt-in to the PHI-free directory, default OFF; user ruling 2026-07-06)
and hc_branches.public_visible (per-site visibility, gated by the Company flag, default ON).
Additive + defaulted → safe on a live DB. Mirrors saas_phase5_portal_directory.sql.
"""
from __future__ import annotations

from alembic import op

revision = "hcsaas03"
down_revision = "hcsaas02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE companies   ADD COLUMN IF NOT EXISTS public_listing BOOLEAN NOT NULL DEFAULT false;")
    op.execute("ALTER TABLE hc_branches ADD COLUMN IF NOT EXISTS public_visible BOOLEAN NOT NULL DEFAULT true;")
    op.execute("CREATE INDEX IF NOT EXISTS idx_companies_public_listing ON companies (public_listing) WHERE public_listing;")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_companies_public_listing;")
    op.execute("ALTER TABLE hc_branches DROP COLUMN IF EXISTS public_visible;")
    op.execute("ALTER TABLE companies   DROP COLUMN IF EXISTS public_listing;")
