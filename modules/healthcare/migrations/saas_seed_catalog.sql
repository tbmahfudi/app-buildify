-- ============================================================================
-- saas_seed_catalog.sql  —  Idempotent catalog seed for the shared SAAS clinics
-- ----------------------------------------------------------------------------
-- Fills the three clinical catalogs the clinical-journey flows read from, for
-- every registered hc_branch on the shared SAAS tenant, plus the tenant DPA
-- consent that gates billing. Safe to re-run: every INSERT is guarded.
--
--   hcp_medications    (branch-scoped)   — dispensable drugs
--   hcl_test_panels    (company-scoped, UNIQUE(company_id, code)) — lab panels
--   hcb_service_items  (company-scoped, UNIQUE(company_id, code)) — billable items
--   hc_patient_consents(clinic_dpa)      — opens require_dpa for billing writes
--
-- Context: the SAAS lineage (tenant 5aa50000…) is the one the running app
-- resolves against (ADR-HC-010). seed_demo.py seeds the *legacy* per-clinic
-- tenants; this file is its SAAS counterpart for the catalog + DPA that
-- seed_demo never populated on SAAS. company_id is the isolation boundary, so
-- company-scoped rows are seeded once per Company (attached to that Company's
-- first branch), not once per branch.
--
-- Apply:
--   docker exec -i app_buildify_postgresql psql -U appuser -d appdb \
--     < modules/healthcare/migrations/saas_seed_catalog.sql
-- ============================================================================

\set shared_tenant '5aa50000-0000-4000-8000-000000000001'

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Medications (branch-scoped) — ensure every branch has a small formulary.
--    Guard on (branch_id, name); no company_id/code column on this table.
-- ---------------------------------------------------------------------------
INSERT INTO hcp_medications
  (id, tenant_id, branch_id, name, generic_name, category, form, strength, unit,
   stock_quantity, minimum_stock, unit_price, currency, is_active, created_at, updated_at)
SELECT md5('med:' || b.id || ':' || m.name),
       :'shared_tenant', b.id, m.name, m.generic_name, m.category, m.form,
       m.strength, m.unit, m.stock, m.min_stock, m.price, 'IDR', true, now(), now()
FROM hc_branches b
CROSS JOIN (VALUES
    ('Paracetamol 500mg', 'Paracetamol',  'analgesic',   'tablet', '500mg', 'tablet', 500, 50, 2500),
    ('Amoxicillin 500mg', 'Amoxicillin',  'antibiotic',  'capsule','500mg', 'capsule',300, 40, 4000),
    ('Ibuprofen 400mg',   'Ibuprofen',    'nsaid',       'tablet', '400mg', 'tablet', 400, 40, 3000)
  ) AS m(name, generic_name, category, form, strength, unit, stock, min_stock, price)
WHERE b.tenant_id = :'shared_tenant'
  AND NOT EXISTS (
    SELECT 1 FROM hcp_medications x
    WHERE x.branch_id = b.id AND x.name = m.name
  );

-- ---------------------------------------------------------------------------
-- 2. Test panels (company-scoped, UNIQUE(company_id, code)) — seed once per
--    Company, attached to that Company's lowest branch id.
-- ---------------------------------------------------------------------------
WITH company_branch AS (
    SELECT platform_company_id::text AS company_id, MIN(id) AS branch_id
    FROM hc_branches
    WHERE tenant_id = :'shared_tenant' AND platform_company_id IS NOT NULL
    GROUP BY platform_company_id::text
)
INSERT INTO hcl_test_panels
  (id, tenant_id, branch_id, code, name, category, turnaround_hours, unit_price,
   currency, sample_type, requires_fasting, is_active, created_at, updated_at, company_id)
SELECT md5('panel:' || cb.company_id || ':' || p.code),
       :'shared_tenant', cb.branch_id, p.code, p.name, p.category, p.tat,
       p.price, 'IDR', p.sample, p.fasting, true, now(), now(), cb.company_id
FROM company_branch cb
CROSS JOIN (VALUES
    ('CBC',   'Complete Blood Count',       'hematology', 24, 150000, 'blood', false),
    ('LFT',   'Liver Function Test',        'chemistry',  24, 200000, 'blood', true),
    ('URIN',  'Urinalysis',                 'urine',      12,  80000, 'urine', false)
  ) AS p(code, name, category, tat, price, sample, fasting)
WHERE NOT EXISTS (
    SELECT 1 FROM hcl_test_panels x
    WHERE x.company_id = cb.company_id AND x.code = p.code
  );

-- ---------------------------------------------------------------------------
-- 3. Service items (company-scoped, UNIQUE(company_id, code)) — the billing
--    catalog, empty until now. Seed once per Company.
-- ---------------------------------------------------------------------------
WITH company_branch AS (
    SELECT platform_company_id::text AS company_id, MIN(id) AS branch_id
    FROM hc_branches
    WHERE tenant_id = :'shared_tenant' AND platform_company_id IS NOT NULL
    GROUP BY platform_company_id::text
)
INSERT INTO hcb_service_items
  (id, tenant_id, branch_id, name, code, unit_price, currency, category,
   is_active, created_at, updated_at, company_id)
SELECT md5('si:' || cb.company_id || ':' || s.code),
       :'shared_tenant', cb.branch_id, s.name, s.code, s.price, 'IDR', s.category,
       true, now(), now(), cb.company_id
FROM company_branch cb
CROSS JOIN (VALUES
    ('REG-FEE',      'Registration Fee',        25000,  'administrative'),
    ('CONSULT-GEN',  'General Consultation',    150000, 'consultation'),
    ('CONSULT-SPEC', 'Specialist Consultation', 300000, 'consultation'),
    ('LAB-CBC',      'Complete Blood Count',    150000, 'laboratory'),
    ('PROC-INJECT',  'Injection Administration', 50000, 'procedure')
  ) AS s(code, name, price, category)
WHERE NOT EXISTS (
    SELECT 1 FROM hcb_service_items x
    WHERE x.company_id = cb.company_id AND x.code = s.code
  );

-- ---------------------------------------------------------------------------
-- 4. DPA consent (clinic_dpa) — require_dpa gates billing writes on an active
--    clinic_dpa row for the tenant. Seed one per Company (require_dpa filters
--    by tenant only, but per-Company rows are correct under ADR-HC-010 and
--    forward-compatible if the gate is ever tightened to company scope).
--
--    First widen ck_hc_patient_consents_type to permit 'clinic_dpa'. Both
--    routes_clinic_signup (writes clinic_dpa) and sdk/dpa_gate (reads it) use
--    this type, but the original constraint (models.py / hc_001) never listed
--    it — so clinic-DPA inserts and the billing gate were both un-satisfiable.
--    Matches the widened CheckConstraint in models.py.
-- ---------------------------------------------------------------------------
ALTER TABLE hc_patient_consents DROP CONSTRAINT IF EXISTS ck_hc_patient_consents_type;
ALTER TABLE hc_patient_consents ADD  CONSTRAINT ck_hc_patient_consents_type
    CHECK (consent_type IN ('dpa_acceptance','clinic_dpa','data_processing','marketing'));

-- patient_id has a FK to hc_patients(id) and require_dpa filters only on
-- (tenant_id, consent_type, status) — so we anchor the clinic_dpa to a real
-- patient in each Company (the gate is patient_id-blind). One row per Company
-- that has patients; that already opens the tenant-scoped gate for every branch.
INSERT INTO hc_patient_consents
  (id, tenant_id, patient_id, consent_type, consent_version, status, accepted_at,
   ip, user_agent, basis, purpose_description, created_at, company_id)
SELECT md5('dpa:' || c.company_id), :'shared_tenant', c.patient_id,
       'clinic_dpa', '1.0', 'active', now(),
       '127.0.0.1', 'saas-seed-catalog', 'self',
       'Clinic Data Processing Agreement (seed)', now(), c.company_id
FROM (
    SELECT company_id::text AS company_id, MIN(id) AS patient_id
    FROM hc_patients
    WHERE tenant_id = :'shared_tenant' AND company_id IS NOT NULL
    GROUP BY company_id::text
  ) c
WHERE NOT EXISTS (
    SELECT 1 FROM hc_patient_consents x
    WHERE x.tenant_id = :'shared_tenant'
      AND x.consent_type = 'clinic_dpa'
      AND x.company_id = c.company_id
  );

COMMIT;

-- Report
SELECT 'medications'   AS catalog, count(*) FROM hcp_medications   WHERE tenant_id = :'shared_tenant'
UNION ALL SELECT 'test_panels',   count(*) FROM hcl_test_panels    WHERE tenant_id = :'shared_tenant'
UNION ALL SELECT 'service_items', count(*) FROM hcb_service_items  WHERE tenant_id = :'shared_tenant'
UNION ALL SELECT 'clinic_dpa',    count(*) FROM hc_patient_consents WHERE tenant_id = :'shared_tenant' AND consent_type='clinic_dpa';
