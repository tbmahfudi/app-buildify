-- SaaS tenancy migration — PHASE 1 (land patient-scoping SCHEMA, nullable — the GATE step)
-- migration-plan-saas-tenancy-01 §Phase 1 + schema-hc-04 §S. Adds company_id (NULLABLE) to the
-- Company-scoped tables. NO backfill, NO NOT NULL, NO RLS cutover, NO tenant re-point (Phases 2-4).
-- Reversible: DROP COLUMN reverts. Apply to appdb.

BEGIN;

-- Company isolation key on the patient registry (ADR-HC-010 D1)
ALTER TABLE hc_patients         ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL;
-- Owner-sentinel Company anchor (ADR-HC-010 clinic_owner fix)
ALTER TABLE hc_branch_staff     ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL;
-- Consent Company re-key (user-confirmed defence-in-depth, 2026-07-06)
ALTER TABLE hc_patient_consents ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL;

CREATE INDEX IF NOT EXISTS idx_hc_patients_company_id         ON hc_patients (company_id);
CREATE INDEX IF NOT EXISTS idx_hc_branch_staff_company_id     ON hc_branch_staff (company_id);
CREATE INDEX IF NOT EXISTS idx_hc_patient_consents_company_id ON hc_patient_consents (company_id);

COMMIT;
