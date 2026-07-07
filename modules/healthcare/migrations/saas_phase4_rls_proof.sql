-- SaaS tenancy migration — PHASE 4 RLS ISOLATION PROOF (hard gate)
-- migration-plan-saas-tenancy-01 §Phase 4 acceptance. The deployed app role (appuser) is a
-- superuser + BYPASSRLS, so it CANNOT exercise the Company RLS policy. This script proves the
-- rls_hc_patients policy under a purpose-made NON-BYPASS role (SET ROLE), which is how a
-- production non-superuser role behaves. RAISES on any leak so it can gate a release.
--
-- Run: docker exec -i app_buildify_postgresql psql -U appuser -d appdb < this file

\set ON_ERROR_STOP on

DROP ROLE IF EXISTS hc_rls_probe;
CREATE ROLE hc_rls_probe NOLOGIN;
GRANT USAGE ON SCHEMA public TO hc_rls_probe;
GRANT SELECT ON hc_patients TO hc_rls_probe;

DO $$
DECLARE
  saas   text := '5aa50000-0000-4000-8000-000000000001';
  med    text := 'c0000001-0000-4000-8000-000000000001';
  hp     text := 'c0000002-0000-4000-8000-000000000001';
  expect_med int; expect_hp int;
  med_total int; med_other int;
  hp_total  int; hp_other  int;
  unset_total int;
BEGIN
  SELECT count(*) INTO expect_med FROM hc_patients WHERE company_id::text = med;
  SELECT count(*) INTO expect_hp  FROM hc_patients WHERE company_id::text = hp;

  SET LOCAL ROLE hc_rls_probe;

  -- MedCare session
  PERFORM set_config('app.tenant_id', saas, true);
  PERFORM set_config('app.company_id', med, true);
  SELECT count(*) INTO med_total FROM hc_patients;
  SELECT count(*) INTO med_other FROM hc_patients WHERE company_id::text = hp;

  -- HealthPoint session
  PERFORM set_config('app.company_id', hp, true);
  SELECT count(*) INTO hp_total FROM hc_patients;
  SELECT count(*) INTO hp_other FROM hc_patients WHERE company_id::text = med;

  -- Fail-closed: unset company
  PERFORM set_config('app.company_id', '', true);
  SELECT count(*) INTO unset_total FROM hc_patients;

  RESET ROLE;

  IF med_other <> 0 THEN RAISE EXCEPTION 'RLS LEAK: MedCare session sees % HealthPoint patients.', med_other; END IF;
  IF hp_other  <> 0 THEN RAISE EXCEPTION 'RLS LEAK: HealthPoint session sees % MedCare patients.', hp_other; END IF;
  IF med_total <> expect_med THEN RAISE EXCEPTION 'RLS WRONG: MedCare sees % (expected %).', med_total, expect_med; END IF;
  IF hp_total  <> expect_hp  THEN RAISE EXCEPTION 'RLS WRONG: HealthPoint sees % (expected %).', hp_total, expect_hp; END IF;
  IF unset_total <> 0 THEN RAISE EXCEPTION 'RLS NOT FAIL-CLOSED: unset company sees % rows.', unset_total; END IF;

  RAISE NOTICE 'RLS PROOF PASS: MedCare=% (0 cross), HealthPoint=% (0 cross), unset=0 (fail-closed).',
    med_total, hp_total;
END $$;

DROP OWNED BY hc_rls_probe;
DROP ROLE hc_rls_probe;
