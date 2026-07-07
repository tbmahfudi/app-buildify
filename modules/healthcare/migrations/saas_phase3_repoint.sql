-- SaaS tenancy migration — PHASE 3 (re-point tenant_id to the shared SAAS tenant)
-- migration-plan-saas-tenancy-01 §Phase 3. Collapses every hc_* row from its old per-clinic
-- tenant onto the single shared SAAS tenant, PER CLINIC, inside one transaction. Also reconciles
-- hc_branches.platform_company_id / platform_branch_id to the map's Company/Branch ids (ADR-HC-005
-- linkage backfill: MedCare from scratch, HealthPoint re-pointed off its old per-clinic linkage).
--
-- SAFE ONLY AFTER Phase 1/2 verify green (0 NULL company_id). company_id is already set (Phase 2),
-- so even as tenant_id collapses to one value patients stay isolated by company_id — that is why
-- Phase 1/2 gate this phase. Reversible via the inverse map (company_id still identifies each clinic's
-- rows). Snapshot the DB before running (see _migration_snapshots/pre_phase3.sql).
--
-- Run: docker exec -i app_buildify_postgresql psql -U appuser -d appdb < this file

\set ON_ERROR_STOP on

-- Whole phase is ONE transaction: any RAISE below aborts and rolls back the entire
-- re-point (nothing is left half-migrated). ON_ERROR_STOP makes psql stop so COMMIT never runs.
BEGIN;

-- ---------------------------------------------------------------------------
-- Pre-flight GATE: refuse to run unless Phase 1/2 are green.
-- ---------------------------------------------------------------------------
DO $$
DECLARE nulls int; unmapped int;
BEGIN
  SELECT count(*) INTO nulls FROM hc_patients WHERE company_id IS NULL;
  IF nulls <> 0 THEN
    RAISE EXCEPTION 'PHASE 3 BLOCKED: % patients still have NULL company_id (Phase 2 not green).', nulls;
  END IF;
  -- Every old clinic tenant present on hc_patients must exist in the map.
  SELECT count(DISTINCT p.tenant_id) INTO unmapped
    FROM hc_patients p LEFT JOIN saas_migration_map m ON p.tenant_id = m.old_tenant_id
    WHERE m.old_tenant_id IS NULL;
  IF unmapped <> 0 THEN
    RAISE EXCEPTION 'PHASE 3 BLOCKED: % patient tenant(s) missing from saas_migration_map.', unmapped;
  END IF;
  RAISE NOTICE 'Pre-flight OK: 0 NULL company_id, all patient tenants mapped.';
END $$;

-- ---------------------------------------------------------------------------
-- Catalog Company re-scope (user ruling 2026-07-07): per-clinic reference/catalog
-- tables are keyed on (tenant_id, <natural key>). Collapsing two clinics onto the
-- shared SAAS tenant would collide/merge them (e.g. both clinics seed a 'CBC' lab
-- panel). Per ADR-HC-010 (Company = clinic-business isolation key), these catalogs
-- become Company-scoped: add company_id, backfill from the map, and re-key the
-- unique constraint tenant_id -> company_id. Done BEFORE the tenant_id re-point so
-- the collapse no longer collides. Not PHI. hcl_test_panels / hcb_service_items /
-- hcp_drug_interactions are raw-SQL tables (no ORM); the ICD/i18n ORM models carry
-- the matching company_id column.
-- ---------------------------------------------------------------------------

-- 1. Add company_id (nullable) to each catalog table.
ALTER TABLE hcl_test_panels       ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL;
ALTER TABLE hcb_service_items     ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL;
ALTER TABLE hcp_drug_interactions ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL;
ALTER TABLE hc_icd10_codes        ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL;
ALTER TABLE hc_icd9cm_codes       ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL;
ALTER TABLE hc_i18n_overrides     ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL;

-- 2. Backfill company_id from the (still old) tenant_id via the map.
DO $$
DECLARE tbl text;
BEGIN
  FOREACH tbl IN ARRAY ARRAY['hcl_test_panels','hcb_service_items','hcp_drug_interactions',
                             'hc_icd10_codes','hc_icd9cm_codes','hc_i18n_overrides']
  LOOP
    EXECUTE format(
      'UPDATE %I t SET company_id = m.new_company_id '
      'FROM saas_migration_map m WHERE t.tenant_id = m.old_tenant_id AND t.company_id IS NULL', tbl);
  END LOOP;
END $$;

-- 3. Re-key the unique constraints tenant_id -> company_id (same natural key), + indexes.
ALTER TABLE hcl_test_panels       DROP CONSTRAINT IF EXISTS uq_hcl_test_panels_tenant_code;
ALTER TABLE hcl_test_panels       ADD  CONSTRAINT uq_hcl_test_panels_company_code UNIQUE (company_id, code);
ALTER TABLE hcb_service_items     DROP CONSTRAINT IF EXISTS uq_hcb_service_items_tenant_code;
ALTER TABLE hcb_service_items     ADD  CONSTRAINT uq_hcb_service_items_company_code UNIQUE (company_id, code);
ALTER TABLE hcp_drug_interactions DROP CONSTRAINT IF EXISTS uq_hcp_drug_interactions_pair;
ALTER TABLE hcp_drug_interactions ADD  CONSTRAINT uq_hcp_drug_interactions_pair UNIQUE (company_id, medication_a_id, medication_b_id);
ALTER TABLE hc_icd10_codes        DROP CONSTRAINT IF EXISTS uq_hc_icd10_codes;
ALTER TABLE hc_icd10_codes        ADD  CONSTRAINT uq_hc_icd10_codes UNIQUE (company_id, code);
ALTER TABLE hc_icd9cm_codes       DROP CONSTRAINT IF EXISTS uq_hc_icd9cm_codes;
ALTER TABLE hc_icd9cm_codes       ADD  CONSTRAINT uq_hc_icd9cm_codes UNIQUE (company_id, code);
ALTER TABLE hc_i18n_overrides     DROP CONSTRAINT IF EXISTS uq_hc_i18n_overrides;
ALTER TABLE hc_i18n_overrides     ADD  CONSTRAINT uq_hc_i18n_overrides UNIQUE (company_id, locale, translation_key);

CREATE INDEX IF NOT EXISTS idx_hcl_test_panels_company       ON hcl_test_panels (company_id);
CREATE INDEX IF NOT EXISTS idx_hcb_service_items_company     ON hcb_service_items (company_id);
CREATE INDEX IF NOT EXISTS idx_hcp_drug_interactions_company ON hcp_drug_interactions (company_id);
CREATE INDEX IF NOT EXISTS idx_hc_icd10_codes_company        ON hc_icd10_codes (company_id);
CREATE INDEX IF NOT EXISTS idx_hc_icd9cm_codes_company       ON hc_icd9cm_codes (company_id);
CREATE INDEX IF NOT EXISTS idx_hc_i18n_overrides_company     ON hc_i18n_overrides (company_id);

-- ---------------------------------------------------------------------------
-- Re-point one clinic at a time. Each clinic is one atomic transaction so a
-- partial re-point never leaves a clinic's rows split across two tenants.
--
-- The UPDATE is driven off a plpgsql loop over EVERY hc_* table that carries a
-- tenant_id column, so no table is missed as the schema grows. Rows on other
-- tenants (e.g. shared reference data) are untouched — only rows whose tenant_id
-- equals THIS clinic's old tenant are moved.
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  cm         RECORD;
  tbl        text;
  moved      bigint;
  clinic_tot bigint;
BEGIN
  FOR cm IN
    SELECT old_tenant_id, clinic AS name, new_company_id, new_branch_id, saas_tenant_id
    FROM saas_migration_map ORDER BY clinic
  LOOP
    clinic_tot := 0;
    RAISE NOTICE '--- Re-pointing clinic % (old tenant % -> SAAS %) ---',
      cm.name, cm.old_tenant_id, cm.saas_tenant_id;

    -- Registry/branches first: reconcile the ADR-HC-005 platform linkage to the
    -- map's Company/Branch, then re-point tenant_id below in the generic sweep.
    UPDATE hc_branches
       SET platform_company_id = cm.new_company_id::uuid,
           platform_branch_id  = cm.new_branch_id::uuid,
           updated_at          = NOW()
     WHERE tenant_id = cm.old_tenant_id;

    -- Generic sweep: every hc_* table with a tenant_id column, this clinic's rows.
    FOR tbl IN
      SELECT table_name FROM information_schema.columns
      WHERE column_name = 'tenant_id' AND table_name LIKE 'hc%'
        AND table_schema = 'public'
      ORDER BY table_name
    LOOP
      EXECUTE format(
        'UPDATE %I SET tenant_id = $1 WHERE tenant_id = $2', tbl
      ) USING cm.saas_tenant_id, cm.old_tenant_id;
      GET DIAGNOSTICS moved = ROW_COUNT;
      clinic_tot := clinic_tot + moved;
      IF moved > 0 THEN
        RAISE NOTICE '    % : % row(s) re-pointed', tbl, moved;
      END IF;
    END LOOP;

    RAISE NOTICE '--- Clinic % done: % row(s) moved to SAAS tenant ---', cm.name, clinic_tot;
  END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- Post-conditions (fail hard if any invariant is violated).
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  saas       text := (SELECT DISTINCT saas_tenant_id FROM saas_migration_map);
  stray      int;
  bad_link   int;
  med_before int := 3;  -- pre-migration MedCare patient count (verified 2026-07-07)
  hp_before  int := 4;  -- pre-migration HealthPoint patient count
  med_after  int;
  hp_after   int;
  cat_null   int;
  cat        text;
BEGIN
  -- 0. Every catalog row that carried a mapped tenant now has a company_id.
  FOREACH cat IN ARRAY ARRAY['hcl_test_panels','hcb_service_items','hcp_drug_interactions',
                             'hc_icd10_codes','hc_icd9cm_codes','hc_i18n_overrides']
  LOOP
    EXECUTE format('SELECT count(*) FROM %I WHERE company_id IS NULL', cat) INTO cat_null;
    IF cat_null <> 0 THEN
      RAISE EXCEPTION 'POST FAIL: % catalog rows in % have NULL company_id.', cat_null, cat;
    END IF;
  END LOOP;

  -- 1. No hc_* row still sits on any OLD clinic tenant.
  SELECT count(*) INTO stray FROM hc_patients p
    JOIN saas_migration_map m ON p.tenant_id = m.old_tenant_id;
  IF stray <> 0 THEN RAISE EXCEPTION 'POST FAIL: % patients still on an old tenant.', stray; END IF;

  -- 2. Linkage invariant: companies.tenant_id == hc_patients.tenant_id == SAAS for every patient.
  SELECT count(*) INTO bad_link
    FROM hc_patients p JOIN companies c ON p.company_id = c.id::text
    WHERE p.tenant_id <> saas OR c.tenant_id::text <> saas;
  IF bad_link <> 0 THEN
    RAISE EXCEPTION 'POST FAIL: % patients violate companies.tenant_id==patient.tenant_id==SAAS.', bad_link;
  END IF;

  -- 3. Per-clinic patient counts preserved and partitioned by company_id (no merge — RULING 1).
  SELECT count(*) INTO med_after FROM hc_patients WHERE company_id = 'c0000001-0000-4000-8000-000000000001';
  SELECT count(*) INTO hp_after  FROM hc_patients WHERE company_id = 'c0000002-0000-4000-8000-000000000001';
  IF med_after <> med_before OR hp_after <> hp_before THEN
    RAISE EXCEPTION 'POST FAIL: patient counts changed (MedCare %/% , HealthPoint %/%).',
      med_after, med_before, hp_after, hp_before;
  END IF;

  RAISE NOTICE 'PHASE 3 OK: all hc_* rows on SAAS tenant; linkage invariant holds; counts preserved (MedCare %, HealthPoint %).',
    med_after, hp_after;
END $$;

COMMIT;
