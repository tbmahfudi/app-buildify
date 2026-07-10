-- SaaS tenancy migration — PHASE 4 ISOLATION GATE (the make-or-break release gate)
-- migration-plan-saas-tenancy-01 §Phase 4 acceptance / ADR-HC-010.
--
-- PART A (backfill sanity) runs NOW and must be green before the cutover.
-- PART B (RLS isolation) is the HARD GATE: it only truly isolates AFTER Phase 4 applies the
--   Company RLS policy on hc_patients keyed on `current_setting('app.company_id')`, AND is run
--   under the RLS-enforced app role (NOT a BYPASSRLS superuser — appuser bypasses RLS, so the
--   cutover must FORCE ROW LEVEL SECURITY or use a non-bypass role). Until then PART B will show
--   all rows regardless of GUC (expected pre-cutover). Post-cutover it MUST show the asserted
--   isolation or the pivot does NOT ship.
--
-- Run: docker exec -i app_buildify_postgresql psql -U appuser -d appdb < this file

\echo '================ PART A — backfill sanity (must pass now) ================'
DO $$
DECLARE nulls int; xpart int;
BEGIN
  SELECT count(*) INTO nulls FROM hc_patients WHERE company_id IS NULL;
  IF nulls <> 0 THEN RAISE EXCEPTION 'GATE FAIL: % patients with NULL company_id', nulls; END IF;

  SELECT count(*) INTO xpart
    FROM hc_patients p JOIN saas_migration_map m ON p.tenant_id = m.old_tenant_id
    WHERE p.company_id <> m.new_company_id;
  IF xpart <> 0 THEN RAISE EXCEPTION 'GATE FAIL: % cross-partition patients', xpart; END IF;

  RAISE NOTICE 'PART A OK: 0 NULL company_id, 0 cross-partition (clean partition per RULING 1).';
END $$;

\echo '================ PART B — RLS isolation gate (run AFTER Phase 4 RLS cutover) ================'
-- Expected post-cutover (MedCare=3 patients, HealthPoint=4):
--   * app.company_id = MedCare      -> sees exactly the MedCare patients, ZERO HealthPoint.
--   * app.company_id = HealthPoint   -> sees exactly the HealthPoint patients, ZERO MedCare.
--   * app.company_id unset/empty     -> ZERO patients (FAIL-CLOSED, no 'ALL' escape).
DO $$
DECLARE
  medcare_co  text := 'c0000001-0000-4000-8000-000000000001';
  health_co   text := 'c0000002-0000-4000-8000-000000000001';
  seen_own int; seen_other int; seen_unset int;
  expect_medcare int; expect_health int;
BEGIN
  SELECT count(*) INTO expect_medcare FROM hc_patients WHERE company_id = medcare_co;
  SELECT count(*) INTO expect_health  FROM hc_patients WHERE company_id = health_co;

  -- Company A (MedCare) session
  PERFORM set_config('app.company_id', medcare_co, false);
  SELECT count(*) INTO seen_own   FROM hc_patients;
  SELECT count(*) INTO seen_other FROM hc_patients WHERE company_id = health_co;

  -- Fail-closed: unset company scope
  PERFORM set_config('app.company_id', '', false);
  SELECT count(*) INTO seen_unset FROM hc_patients;

  RAISE NOTICE 'MedCare session: sees % (expect %), of which % are HealthPoint (expect 0). Unset GUC sees % (expect 0).',
    seen_own, expect_medcare, seen_other, seen_unset;

  IF seen_other <> 0 THEN
    RAISE WARNING 'GATE NOT MET (or RLS not yet applied): MedCare session can see % HealthPoint patients.', seen_other;
  ELSIF seen_own <> expect_medcare THEN
    RAISE WARNING 'GATE NOT MET: MedCare session sees % patients, expected %.', seen_own, expect_medcare;
  ELSIF seen_unset <> 0 THEN
    RAISE WARNING 'GATE NOT MET: unset company scope is NOT fail-closed (sees % rows).', seen_unset;
  ELSE
    RAISE NOTICE 'PART B PASS: Company isolation enforced + fail-closed. Cutover may ship.';
  END IF;

  PERFORM set_config('app.company_id', '', false);
END $$;
