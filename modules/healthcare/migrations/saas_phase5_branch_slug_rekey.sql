-- saas_phase5_branch_slug_rekey.sql
--
-- epic-20 Feature 20.2 — Company-scope the hc_branches slug uniqueness.
--
-- Under the shared SaaS tenant (ADR-HC-010) every clinic's branches share one
-- tenant_id, so the original UNIQUE(tenant_id, slug) would reject a second clinic
-- reusing a common branch slug (e.g. 'main', 'downtown') with an IntegrityError.
-- Re-key uniqueness to the owning Company (platform_company_id, slug), ignoring
-- soft-deleted rows so a slug can be reused after a branch is deleted.
--
-- Idempotent + safe on a live DB (existing slugs are already distinct).

BEGIN;

ALTER TABLE hc_branches DROP CONSTRAINT IF EXISTS uq_hc_branches_tenant_slug;

CREATE UNIQUE INDEX IF NOT EXISTS uq_hc_branches_company_slug
    ON hc_branches (platform_company_id, slug)
    WHERE deleted_at IS NULL;

COMMIT;
