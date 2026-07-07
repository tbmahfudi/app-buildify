"""
hc_saas_02_company_cutover

Revision ID: hcsaas02
Revises: hcsaas01
Create Date: 2026-07-07

SaaS shared-tenant migration — ENFORCEMENT half (ADR-HC-010 D2/D4a, schema-hc-04 §S.1 STEP 3 / §S.2,
migration-plan-saas-tenancy-01 Phase 4). Narrows hc_patients.company_id to uuid NOT NULL + FK, adds
the hc_branch_staff Company FK + owner-anchor CHECK, and re-keys the patient-registry RLS from
tenant-only (hc_patients_tenant_isolation, hc_002) to Company (rls_hc_patients).

PREREQUISITE: run AFTER company_id is backfilled and tenant_id re-pointed to the shared SAAS tenant
(saas_phase2_backfill.sql + saas_phase3_repoint.sql), else the NOT NULL / uuid cast will fail on
un-backfilled rows. On a fresh empty DB it applies directly after hcsaas01.

NOTE: appuser is superuser + BYPASSRLS, so rls_hc_patients is only *enforced* under a non-bypass
role — proven by saas_phase4_rls_proof.sql. The dev app additionally fences registry ENUMERATION by
the caller Company in application code (branch_scope.resolve_caller_company_id).
"""
from __future__ import annotations

from alembic import op

revision = "hcsaas02"
down_revision = "hcsaas01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. hc_patients.company_id -> uuid NOT NULL + FK to platform companies.id (shared-DB).
    op.execute("ALTER TABLE hc_patients ALTER COLUMN company_id TYPE uuid USING company_id::uuid;")
    op.execute("ALTER TABLE hc_patients ALTER COLUMN company_id SET NOT NULL;")
    op.execute(
        "ALTER TABLE hc_patients ADD CONSTRAINT fk_hc_patients_company "
        "FOREIGN KEY (company_id) REFERENCES companies(id);"
    )

    # 2. hc_branch_staff.company_id -> uuid + FK + owner-anchor CHECK (sentinel row must carry it).
    op.execute("ALTER TABLE hc_branch_staff ALTER COLUMN company_id TYPE uuid USING company_id::uuid;")
    op.execute(
        "ALTER TABLE hc_branch_staff ADD CONSTRAINT fk_hc_branch_staff_company "
        "FOREIGN KEY (company_id) REFERENCES companies(id);"
    )
    op.execute(
        "ALTER TABLE hc_branch_staff ADD CONSTRAINT ck_hc_branch_staff_owner_company "
        "CHECK ((branch_id IS NOT NULL) OR (company_id IS NOT NULL));"
    )

    # 3. Re-key the patient-registry RLS: tenant-only (hc_002) -> Company. Fail-closed; tenant AND-ed
    #    as defence-in-depth (the shared SAAS tenant on every hc row).
    op.execute("DROP POLICY IF EXISTS hc_patients_tenant_isolation ON hc_patients;")
    op.execute("DROP POLICY IF EXISTS rls_hc_patients ON hc_patients;")
    op.execute(
        "CREATE POLICY rls_hc_patients ON hc_patients USING ("
        "company_id::text = current_setting('app.company_id', true) "
        "AND tenant_id = current_setting('app.tenant_id', true));"
    )
    op.execute("ALTER TABLE hc_patients ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE hc_patients FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    # Restore the tenant-only registry RLS (hc_002 shape).
    op.execute("DROP POLICY IF EXISTS rls_hc_patients ON hc_patients;")
    op.execute(
        "CREATE POLICY hc_patients_tenant_isolation ON hc_patients USING ("
        "(tenant_id)::text = current_setting('app.current_tenant_id', true));"
    )

    op.execute("ALTER TABLE hc_branch_staff DROP CONSTRAINT IF EXISTS ck_hc_branch_staff_owner_company;")
    op.execute("ALTER TABLE hc_branch_staff DROP CONSTRAINT IF EXISTS fk_hc_branch_staff_company;")
    op.execute("ALTER TABLE hc_branch_staff ALTER COLUMN company_id TYPE varchar(36) USING company_id::text;")

    op.execute("ALTER TABLE hc_patients DROP CONSTRAINT IF EXISTS fk_hc_patients_company;")
    op.execute("ALTER TABLE hc_patients ALTER COLUMN company_id DROP NOT NULL;")
    op.execute("ALTER TABLE hc_patients ALTER COLUMN company_id TYPE varchar(36) USING company_id::text;")
