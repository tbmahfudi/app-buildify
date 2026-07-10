-- SaaS onboarding (epic-20) — Phase 5 portal directory schema (Feature 20.4)
-- Adds the opt-in public-directory flags (ADR-HC-010 D6, user ruling 2026-07-06: directory is
-- opt-in per Company via companies.public_listing, default false) and a per-branch visibility flag
-- gated by the Company flag. Additive + defaulted → safe on a live DB. Apply to appdb.

BEGIN;

-- Company opt-in to the PHI-free public clinic directory (default OFF).
ALTER TABLE companies   ADD COLUMN IF NOT EXISTS public_listing BOOLEAN NOT NULL DEFAULT false;

-- Per-branch public visibility (only meaningful when the owning Company opts in). Default true so
-- an opted-in Company shows all its sites unless a site is explicitly hidden.
ALTER TABLE hc_branches ADD COLUMN IF NOT EXISTS public_visible BOOLEAN NOT NULL DEFAULT true;

CREATE INDEX IF NOT EXISTS idx_companies_public_listing ON companies (public_listing) WHERE public_listing;

-- Demo: opt the two migrated clinics into the directory so the chooser has content to show.
UPDATE companies SET public_listing = true
 WHERE code IN ('MEDCARE','HEALTHPOINT')
   AND tenant_id = '5aa50000-0000-4000-8000-000000000001';

COMMIT;
