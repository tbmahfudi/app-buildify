-- hcs_004 — Household / Proxy Access (ADR-HC-009 v2, schema-hc-03 §M)
-- Idempotent. Apply directly to appdb (module Alembic head is not tracked in appdb).
--   docker exec -i app_buildify_postgresql psql -U appuser -d appdb -f - < this file
--
-- M.1 — hc_patients.user_id stays nullable + NOT UNIQUE (already the case); keep the
--        non-unique lookup index and add the shared-DB FK -> users.id.
-- M.2 — new MODULE table hc_patient_relationships (household/proxy authority).
-- M.3 — hc_patient_consents gains basis + consented_by_user_id (proxy-consent attribution).

BEGIN;

-- ---------------------------------------------------------------------------
-- M.1 — user_id lookup index (idempotent) + shared-DB FK -> users.id
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_hc_patients_user_id ON hc_patients (user_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_hc_patients_user'
    ) THEN
        -- shared-DB only; harmless if users lives in the same DB (current dev)
        ALTER TABLE hc_patients
            ADD CONSTRAINT fk_hc_patients_user
            FOREIGN KEY (user_id) REFERENCES users(id);
    END IF;
EXCEPTION WHEN others THEN
    -- split-DB or unresolved refs: integrity is app-enforced (ADR-HC-009 R4)
    RAISE NOTICE 'fk_hc_patients_user not added (%). App-enforced fallback.', SQLERRM;
END $$;

-- ---------------------------------------------------------------------------
-- M.2 — hc_patient_relationships
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hc_patient_relationships (
    id                   VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id            VARCHAR(36) NOT NULL,
    branch_id            VARCHAR(36) NULL REFERENCES hc_branches(id),
    account_user_id      VARCHAR(36) NOT NULL,
    patient_id           VARCHAR(36) NOT NULL REFERENCES hc_patients(id) ON DELETE CASCADE,
    relationship         VARCHAR(20) NOT NULL,
    role                 VARCHAR(10) NOT NULL,
    status               VARCHAR(10) NOT NULL DEFAULT 'active',
    basis                VARCHAR(20) NOT NULL,
    granted_by           VARCHAR(36) NOT NULL,
    granted_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    approved_by_staff_id VARCHAR(36) NULL,
    approved_at          TIMESTAMP NULL,
    revoked_at           TIMESTAMP NULL,
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_hcpr_relationship CHECK (relationship IN ('self','spouse','child','parent','other')),
    CONSTRAINT ck_hcpr_role         CHECK (role IN ('owner','proxy')),
    CONSTRAINT ck_hcpr_status       CHECK (status IN ('active','pending','revoked')),
    CONSTRAINT ck_hcpr_basis        CHECK (basis IN ('self','parental_guardian','delegated_adult','spousal')),
    CONSTRAINT ck_hcpr_self_coherent CHECK (
        relationship <> 'self' OR (role = 'owner' AND basis = 'self')
    ),
    CONSTRAINT uq_hcpr_account_patient UNIQUE (account_user_id, patient_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_hcpr_one_self_per_holder
    ON hc_patient_relationships (account_user_id) WHERE relationship = 'self';
CREATE INDEX IF NOT EXISTS idx_hcpr_account_active
    ON hc_patient_relationships (account_user_id, status);
CREATE INDEX IF NOT EXISTS idx_hcpr_patient
    ON hc_patient_relationships (patient_id, status);
CREATE INDEX IF NOT EXISTS idx_hcpr_branch_pending
    ON hc_patient_relationships (branch_id, status) WHERE status = 'pending';

-- ---------------------------------------------------------------------------
-- M.3 — hc_patient_consents: proxy-consent attribution
-- ---------------------------------------------------------------------------
ALTER TABLE hc_patient_consents
    ADD COLUMN IF NOT EXISTS basis                VARCHAR(20) NOT NULL DEFAULT 'self',
    ADD COLUMN IF NOT EXISTS consented_by_user_id VARCHAR(36) NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_hc_patient_consents_basis'
    ) THEN
        ALTER TABLE hc_patient_consents
            ADD CONSTRAINT ck_hc_patient_consents_basis
            CHECK (basis IN ('self','parental_guardian','delegated_adult','spousal'));
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- Backfill — every currently-linked patient becomes its account holder's SELF patient.
-- (D7: self-owned legacy patients get a self/owner relationship row.)
-- ---------------------------------------------------------------------------
INSERT INTO hc_patient_relationships
    (id, tenant_id, branch_id, account_user_id, patient_id, relationship, role, status, basis, granted_by, granted_at)
SELECT gen_random_uuid(), p.tenant_id, NULL, p.user_id, p.id, 'self', 'owner', 'active', 'self', p.user_id, NOW()
FROM hc_patients p
WHERE p.user_id IS NOT NULL
  AND p.deleted_at IS NULL
ON CONFLICT (account_user_id, patient_id) DO NOTHING;

COMMIT;
