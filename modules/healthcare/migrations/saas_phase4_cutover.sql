-- SaaS tenancy migration — PHASE 4 CUTOVER (constrain + re-key RLS to Company)
-- migration-plan-saas-tenancy-01 §Phase 4 items 1-3 + schema-hc-04 §S.1 STEP 3 / §S.2.
--
-- SAFE ONLY AFTER Phase 3 verified green (all hc_* on the SAAS tenant, 0 NULL company_id).
-- This is the enforcement cutover: hc_patients.company_id becomes NOT NULL + FK, the tenant-only
-- RLS policy is dropped and replaced with the Company-keyed policy, and the owner-anchor CHECK lands.
-- Snapshot before running (see _migration_snapshots/pre_phase4.sql). Reversible by restoring the
-- tenant-only policy + dropping NOT NULL/FK.
--
-- Run: docker exec -i app_buildify_postgresql psql -U appuser -d appdb < this file

\set ON_ERROR_STOP on
BEGIN;

-- Pre-flight: refuse unless Phase 3 is green.
DO $$
DECLARE nulls int; stray int;
BEGIN
  SELECT count(*) INTO nulls FROM hc_patients WHERE company_id IS NULL;
  IF nulls <> 0 THEN RAISE EXCEPTION 'PHASE 4 BLOCKED: % patients with NULL company_id.', nulls; END IF;
  SELECT count(*) INTO stray FROM hc_patients p JOIN saas_migration_map m ON p.tenant_id = m.old_tenant_id;
  IF stray <> 0 THEN RAISE EXCEPTION 'PHASE 4 BLOCKED: % patients still on an old tenant (Phase 3 not green).', stray; END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 1. hc_patients.company_id -> uuid + NOT NULL + FK to platform companies.id.
--    company_id was created VARCHAR(36) (Phase 1); companies.id is native uuid, so a real
--    FK needs the column typed uuid (all backfilled values are uuid-format). Mirrors the
--    HCBranch.platform_company_id posture (uuid, DB-side FK).
-- ---------------------------------------------------------------------------
ALTER TABLE hc_patients ALTER COLUMN company_id TYPE uuid USING company_id::uuid;
ALTER TABLE hc_patients ALTER COLUMN company_id SET NOT NULL;
ALTER TABLE hc_patients
    ADD CONSTRAINT fk_hc_patients_company FOREIGN KEY (company_id) REFERENCES companies(id);

-- ---------------------------------------------------------------------------
-- 2. hc_branch_staff.company_id -> uuid + FK + owner-anchor CHECK (schema-hc-04 §S.2).
--    A clinic_owner sentinel row (branch_id IS NULL) MUST carry a company_id; a non-owner
--    row (branch_id NOT NULL) leaves it NULL (Branch fences the Company).
-- ---------------------------------------------------------------------------
ALTER TABLE hc_branch_staff ALTER COLUMN company_id TYPE uuid USING company_id::uuid;
ALTER TABLE hc_branch_staff
    ADD CONSTRAINT fk_hc_branch_staff_company FOREIGN KEY (company_id) REFERENCES companies(id);
ALTER TABLE hc_branch_staff
    ADD CONSTRAINT ck_hc_branch_staff_owner_company
        CHECK ( (branch_id IS NOT NULL) OR (company_id IS NOT NULL) );

-- ---------------------------------------------------------------------------
-- 3. Re-key the patient-registry RLS from tenant-only to Company (ADR-HC-010 D2).
--    The old policy was named hc_patients_tenant_isolation (deployed) — drop it and any
--    schema-hc-04 alias, then create the Company-keyed policy. Fail-closed: an unset
--    app.company_id -> current_setting(...,true) NULL -> predicate false -> zero rows.
--    tenant_id is AND-ed as defence-in-depth (the shared SAAS tenant on every hc row).
--    NOTE: appuser is superuser + BYPASSRLS, so this policy is enforced only under a
--    non-bypass role (see saas_phase4_isolation_gate.sql PART B) — that is the real gate.
-- ---------------------------------------------------------------------------
DROP POLICY IF EXISTS hc_patients_tenant_isolation ON hc_patients;
DROP POLICY IF EXISTS rls_hc_patients ON hc_patients;
CREATE POLICY rls_hc_patients ON hc_patients
    USING (
        company_id::text = current_setting('app.company_id', true)
        AND tenant_id     = current_setting('app.tenant_id', true)
    );
ALTER TABLE hc_patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE hc_patients FORCE ROW LEVEL SECURITY;

-- Post-conditions.
DO $$
DECLARE polcount int; col_nullable text;
BEGIN
  SELECT count(*) INTO polcount FROM pg_policies WHERE tablename='hc_patients' AND policyname='rls_hc_patients';
  IF polcount <> 1 THEN RAISE EXCEPTION 'POST FAIL: rls_hc_patients policy not present.'; END IF;

  SELECT is_nullable INTO col_nullable FROM information_schema.columns
    WHERE table_name='hc_patients' AND column_name='company_id';
  IF col_nullable <> 'NO' THEN RAISE EXCEPTION 'POST FAIL: hc_patients.company_id is still nullable.'; END IF;

  RAISE NOTICE 'PHASE 4 DDL OK: company_id uuid NOT NULL + FK; Company RLS policy in place.';
END $$;

COMMIT;
