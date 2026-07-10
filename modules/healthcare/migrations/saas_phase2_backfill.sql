-- SaaS tenancy migration — PHASE 2 (backfill company_id, ADDITIVE — no tenant_id change)
-- migration-plan-saas-tenancy-01 §Phase 2. Populates the new company_id column from the Phase-0 map.
-- Clean partition (RULING 1): no cross-Company merge. Reversible (SET company_id = NULL).
-- hc_branches.platform_* re-pointing is deferred to Phase 3 (consolidation), keeping Phase 2
-- non-destructive to the live tenants. Apply to appdb.

BEGIN;

-- 1. Patients — Company from the row's (still old) tenant via the map.
UPDATE hc_patients p
SET    company_id = m.new_company_id
FROM   saas_migration_map m
WHERE  p.tenant_id = m.old_tenant_id
  AND  p.company_id IS NULL;

-- 2. Staff — only the clinic_owner sentinel rows (branch_id IS NULL) get the Company anchor.
--    Non-owner rows stay NULL: a Branch already fences them to one Company.
UPDATE hc_branch_staff s
SET    company_id = m.new_company_id
FROM   saas_migration_map m
WHERE  s.tenant_id = m.old_tenant_id
  AND  s.branch_id IS NULL
  AND  s.company_id IS NULL;

-- 3. Consents — derive Company from the owning patient (keeps consent aligned with its patient).
UPDATE hc_patient_consents c
SET    company_id = p.company_id
FROM   hc_patients p
WHERE  c.patient_id = p.id
  AND  c.company_id IS NULL
  AND  p.company_id IS NOT NULL;

COMMIT;
