"""
hc_saas_01_company_scoping

Revision ID: hcsaas01
Revises: hc006, hcl002   (merge of the two healthcare heads)
Create Date: 2026-07-07

SaaS shared-tenant migration — ADDITIVE half (ADR-HC-010 / schema-hc-04 §S, migration-plan-
saas-tenancy-01 Phase 1 + Phase 3 catalog re-scope). Adds the Company isolation column to the
patient registry / owner-sentinel / consents, and Company-scopes the per-clinic catalog tables
whose natural key would otherwise collide when clinics consolidate onto one shared tenant.

Everything here is additive + nullable, so it is safe to apply on a live DB with data present.
The DATA consolidation (backfill company_id, re-point tenant_id) is a one-time operational step
run BETWEEN this migration and hcsaas02 — see modules/healthcare/migrations/saas_phase{2,3}*.sql.
Ordering for an existing deploy:  upgrade hcsaas01  ->  run saas_phase2/3 SQL  ->  upgrade hcsaas02.
On a fresh (empty) DB the data step is a no-op and hcsaas01+hcsaas02 apply back-to-back.
"""
from __future__ import annotations

from alembic import op

revision = "hcsaas01"
down_revision = ("hc006", "hcl002")  # merge the two healthcare heads into one
branch_labels = None
depends_on = None

# Per-clinic catalog tables whose unique key must move tenant -> company (schema-hc-04 §S,
# user ruling 2026-07-07). (table, added company_id column, old unique, new unique, new-unique cols)
_CATALOGS = [
    ("hcl_test_panels",       "uq_hcl_test_panels_tenant_code",   "uq_hcl_test_panels_company_code",   "company_id, code"),
    ("hcb_service_items",     "uq_hcb_service_items_tenant_code", "uq_hcb_service_items_company_code", "company_id, code"),
    ("hcp_drug_interactions", "uq_hcp_drug_interactions_pair",    "uq_hcp_drug_interactions_pair",     "company_id, medication_a_id, medication_b_id"),
    ("hc_icd10_codes",        "uq_hc_icd10_codes",                "uq_hc_icd10_codes",                 "company_id, code"),
    ("hc_icd9cm_codes",       "uq_hc_icd9cm_codes",               "uq_hc_icd9cm_codes",                "company_id, code"),
    ("hc_i18n_overrides",     "uq_hc_i18n_overrides",             "uq_hc_i18n_overrides",              "company_id, locale, translation_key"),
]

# Company isolation column on the patient registry + owner sentinel + consents (VARCHAR now;
# hcsaas02 narrows hc_patients / hc_branch_staff to uuid + FK once backfilled).
_COMPANY_COLS = ["hc_patients", "hc_branch_staff", "hc_patient_consents"]


def upgrade() -> None:
    for t in _COMPANY_COLS:
        op.execute(f"ALTER TABLE {t} ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL;")
        op.execute(f"CREATE INDEX IF NOT EXISTS idx_{t}_company_id ON {t} (company_id);")

    for tbl, old_uq, new_uq, new_cols in _CATALOGS:
        op.execute(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL;")
        op.execute(f"CREATE INDEX IF NOT EXISTS idx_{tbl}_company ON {tbl} (company_id);")
        # NOTE: on an existing deploy the saas_phase3 data step backfills company_id BEFORE this
        # unique is created; on a fresh DB the tables are empty so the re-key is trivially valid.
        op.execute(f"ALTER TABLE {tbl} DROP CONSTRAINT IF EXISTS {old_uq};")
        op.execute(f"ALTER TABLE {tbl} ADD  CONSTRAINT {new_uq} UNIQUE ({new_cols});")


def downgrade() -> None:
    for tbl, old_uq, new_uq, _new_cols in _CATALOGS:
        op.execute(f"ALTER TABLE {tbl} DROP CONSTRAINT IF EXISTS {new_uq};")
        # restore the original tenant-scoped unique (best-effort; column names per schema-hc-01/02)
        if tbl == "hcp_drug_interactions":
            op.execute(f"ALTER TABLE {tbl} ADD CONSTRAINT {old_uq} UNIQUE (tenant_id, medication_a_id, medication_b_id);")
        elif tbl == "hc_i18n_overrides":
            op.execute(f"ALTER TABLE {tbl} ADD CONSTRAINT {old_uq} UNIQUE (tenant_id, locale, translation_key);")
        else:
            op.execute(f"ALTER TABLE {tbl} ADD CONSTRAINT {old_uq} UNIQUE (tenant_id, code);")
        op.execute(f"DROP INDEX IF EXISTS idx_{tbl}_company;")
        op.execute(f"ALTER TABLE {tbl} DROP COLUMN IF EXISTS company_id;")

    for t in _COMPANY_COLS:
        op.execute(f"DROP INDEX IF EXISTS idx_{t}_company_id;")
        op.execute(f"ALTER TABLE {t} DROP COLUMN IF EXISTS company_id;")
