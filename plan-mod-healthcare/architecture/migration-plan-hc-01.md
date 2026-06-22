---
artifact_id: migration-plan-hc-01
type: migration-plan
module: healthcare (base) + healthcare_scheduling + healthcare_billing + healthcare_pharmacy + healthcare_lab
status: Draft
producer: B2 Data Engineer
upstream: [schema-hc-01, adr-hc-001, adr-hc-002, platform-alembic-conventions]
created: 2026-06-21
---

# Migration Plan — Healthcare Module Suite

> Epic-06 (Telemedicine) is **excluded** — pending legal review.

## Conventions

- All Alembic migration files follow the platform naming convention: `<revision_id>_<slug>.py`
- Each module has its own `alembic_version` table (platform pattern from `pg_unify_module_system`).
- RLS policy migrations are raw SQL files (not ORM-generated) invoked from within the Alembic
  migration `op.execute()` calls. The platform does not auto-generate RLS from ORM decorators.
- Rollback = `downgrade()` function in every migration file. Rollback strategy per wave is
  documented below.
- Migrations that drop or alter PHI columns require a change-management ticket and DBA sign-off
  before running in production (PP 71/2019 data governance requirement).

---

## Migration File Locations

```
modules/healthcare/backend/app/alembic/versions/postgresql/
    hc_001_base_tables.py
    hc_002_rls_policies.py
    hc_003_audit_log_permissions.py
    hc_004_i18n_overrides.py

modules/healthcare_scheduling/backend/app/alembic/versions/postgresql/
    hcs_001_scheduling_tables.py
    hcs_002_rls_policies.py

modules/healthcare_billing/backend/app/alembic/versions/postgresql/
    hcb_001_billing_tables.py
    hcb_002_rls_policies.py

modules/healthcare_pharmacy/backend/app/alembic/versions/postgresql/
    hcp_001_pharmacy_tables.py
    hcp_002_rls_policies.py

modules/healthcare_lab/backend/app/alembic/versions/postgresql/
    hcl_001_lab_tables.py
    hcl_002_rls_policies.py
```

---

## Migration Sequence

### Wave 0 — Prerequisites (no healthcare tables yet)

**Pre-condition:** Platform migrations `pg_security_policy_system`, `pg_unify_module_system`,
and `pg_tenant_module_databases` must be at `head` before any healthcare migration runs.
Verify with: `alembic -n postgresql current` in `backend/app/`.

---

### Wave 1 — Healthcare Base Module

**File: `hc_001_base_tables.py`**
**Revision ID:** `hc001`
**Down revision:** Platform `pg_unify_module_system` revision ID (to be confirmed by platform team)

Creates (in dependency order within one migration):
1. `hc_branches` — no dependencies beyond `tenants` (platform table)
2. `hc_providers` — depends on `hc_branches`
3. `hc_branch_staff` — depends on `hc_branches`, platform `users`
4. `hc_patients` — depends on `tenants` only (tenant-wide, no branch FK)
5. `hc_patient_consents` — depends on `hc_patients`
6. `hc_encounters` — depends on `hc_branches`, `hc_patients`, `hc_providers`
7. `hc_audit_log` — no FKs (append-only, standalone)
8. `hc_clinic_reviews` — depends on `hc_branches`, `hc_patients`, `hc_encounters`

**Rollback strategy (`downgrade`):**
Drop tables in reverse order: `hc_clinic_reviews`, `hc_audit_log`, `hc_encounters`,
`hc_patient_consents`, `hc_patients`, `hc_branch_staff`, `hc_providers`, `hc_branches`.
Rollback must also drop all associated indexes (created in `upgrade()`).

---

**File: `hc_002_rls_policies.py`**
**Revision ID:** `hc002`
**Down revision:** `hc001`

Applies RLS policies as raw SQL via `op.execute()` for PHI tables:

```sql
-- Enable RLS
ALTER TABLE hc_patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE hc_encounters ENABLE ROW LEVEL SECURITY;
ALTER TABLE hc_clinic_reviews ENABLE ROW LEVEL SECURITY;

-- Tenant-only RLS for hc_patients (no branch filter — tenant-wide entity)
CREATE POLICY hc_patients_tenant_isolation ON hc_patients
    USING (tenant_id = current_setting('app.tenant_id', true));

-- Branch-scoped RLS for hc_encounters
CREATE POLICY hc_encounters_branch_isolation ON hc_encounters
    USING (
        tenant_id = current_setting('app.tenant_id', true)
        AND (
            branch_id = current_setting('app.branch_id', true)
            OR current_setting('app.branch_id', true) = 'ALL'
        )
    );

-- Branch-scoped RLS for hc_clinic_reviews
CREATE POLICY hc_clinic_reviews_branch_isolation ON hc_clinic_reviews
    USING (
        tenant_id = current_setting('app.tenant_id', true)
        AND (
            branch_id = current_setting('app.branch_id', true)
            OR current_setting('app.branch_id', true) = 'ALL'
        )
    );

-- GRANT SELECT to app_readonly_role; GRANT INSERT, UPDATE to app_user (no DELETE on audit)
```

**Rollback strategy (`downgrade`):**
`DROP POLICY` each named policy; `ALTER TABLE ... DISABLE ROW LEVEL SECURITY` for each table.

---

**File: `hc_003_audit_log_permissions.py`**
**Revision ID:** `hc003`
**Down revision:** `hc002`

Sets DB-level INSERT-only grant on `hc_audit_log`:

```sql
REVOKE UPDATE, DELETE ON hc_audit_log FROM app_user;
REVOKE UPDATE, DELETE ON hc_audit_log FROM app_readonly_role;
GRANT INSERT ON hc_audit_log TO app_user;
GRANT SELECT ON hc_audit_log TO app_readonly_role;
```

Creates an optional DB trigger for additional enforcement:
```sql
CREATE RULE no_update_audit_log AS ON UPDATE TO hc_audit_log DO INSTEAD NOTHING;
CREATE RULE no_delete_audit_log AS ON DELETE TO hc_audit_log DO INSTEAD NOTHING;
```

**Rollback strategy (`downgrade`):**
Drop rules; restore original grants (GRANT UPDATE, DELETE as per platform default).

---

**File: `hc_004_i18n_overrides.py`**
**Revision ID:** `hc004`
**Down revision:** `hc003`

Creates `hc_i18n_overrides` (no PHI; no RLS needed beyond platform tenant isolation):
1. Table + indexes
2. No RLS (non-sensitive configuration data)

**Rollback strategy (`downgrade`):** `DROP TABLE hc_i18n_overrides CASCADE`.

---

### Wave 2 — Healthcare Scheduling

**Dependency:** Wave 1 complete (`hc004` at head).

**File: `hcs_001_scheduling_tables.py`**
**Revision ID:** `hcs001`
**Down revision:** `hc004`

Creates (in order):
1. `hcs_provider_schedules` — depends on `hc_branches`, `hc_providers`
2. `hcs_appointment_slots` — depends on `hcs_provider_schedules`
3. `hcs_appointments` — depends on `hc_branches`, `hc_patients`, `hc_providers`, `hcs_appointment_slots`
4. `hcs_waitlist` — depends on `hc_branches`, `hc_patients`, `hc_providers`, `hcs_appointment_slots`
5. `hcs_notification_log` — depends on `hcs_appointments`

Note: `hc_encounters.appointment_id` FK to `hcs_appointments` must be added as a deferred ALTER
in this migration (not in Wave 1, where `hcs_appointments` does not yet exist):
```sql
ALTER TABLE hc_encounters
    ADD CONSTRAINT fk_hc_encounters_appointment_id
    FOREIGN KEY (appointment_id) REFERENCES hcs_appointments(id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
```

**Rollback strategy (`downgrade`):**
First drop the FK on `hc_encounters.appointment_id`. Then drop tables in reverse:
`hcs_notification_log`, `hcs_waitlist`, `hcs_appointments`, `hcs_appointment_slots`,
`hcs_provider_schedules`.

---

**File: `hcs_002_rls_policies.py`**
**Revision ID:** `hcs002`
**Down revision:** `hcs001`

Applies RLS for `hcs_appointments` (branch-scoped PHI):

```sql
ALTER TABLE hcs_appointments ENABLE ROW LEVEL SECURITY;

CREATE POLICY hcs_appointments_branch_isolation ON hcs_appointments
    USING (
        tenant_id = current_setting('app.tenant_id', true)
        AND (
            branch_id = current_setting('app.branch_id', true)
            OR current_setting('app.branch_id', true) = 'ALL'
        )
    );
```

No RLS on `hcs_provider_schedules`, `hcs_appointment_slots`, `hcs_waitlist`,
`hcs_notification_log` — these are branch-scoped operationally but do not contain PHI
requiring DB-level policy.

**Rollback strategy (`downgrade`):** `DROP POLICY`; `DISABLE ROW LEVEL SECURITY`.

---

### Wave 3 — Healthcare Billing

**Dependency:** Wave 2 complete (`hcs002` at head).

**File: `hcb_001_billing_tables.py`**
**Revision ID:** `hcb001`
**Down revision:** `hcs002`

Creates (in order):
1. `hcb_service_items` — depends on `hc_branches`
2. `hcb_insurance_profiles` — depends on `hc_branches`, `hc_patients`
3. `hcb_invoices` — depends on `hc_branches`, `hc_patients`, `hc_encounters`
4. `hcb_invoice_lines` — depends on `hcb_invoices`, `hcb_service_items`
5. `hcb_payments` — depends on `hcb_invoices`
6. `hcb_bpjs_exports` — depends on `hc_branches`

**Rollback strategy (`downgrade`):**
Drop in reverse: `hcb_bpjs_exports`, `hcb_payments`, `hcb_invoice_lines`, `hcb_invoices`,
`hcb_insurance_profiles`, `hcb_service_items`.

---

**File: `hcb_002_rls_policies.py`**
**Revision ID:** `hcb002`
**Down revision:** `hcb001`

Applies RLS for PHI tables `hcb_invoices` and `hcb_insurance_profiles`:

```sql
ALTER TABLE hcb_invoices ENABLE ROW LEVEL SECURITY;
CREATE POLICY hcb_invoices_branch_isolation ON hcb_invoices
    USING (
        tenant_id = current_setting('app.tenant_id', true)
        AND (branch_id = current_setting('app.branch_id', true) OR current_setting('app.branch_id', true) = 'ALL')
    );

ALTER TABLE hcb_insurance_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY hcb_insurance_profiles_branch_isolation ON hcb_insurance_profiles
    USING (
        tenant_id = current_setting('app.tenant_id', true)
        AND (branch_id = current_setting('app.branch_id', true) OR current_setting('app.branch_id', true) = 'ALL')
    );
```

**Rollback strategy (`downgrade`):** `DROP POLICY`; `DISABLE ROW LEVEL SECURITY`.

---

### Wave 4 — Healthcare Pharmacy

**Dependency:** Wave 3 complete (`hcb002` at head). Note: pharmacy may be deployed before or
after billing in practice; the migration down-revision is set to `hcb002` for a linear chain
but can be parallelised with Wave 3 if billing is deferred. Confirm deployment order with ops.

**File: `hcp_001_pharmacy_tables.py`**
**Revision ID:** `hcp001`
**Down revision:** `hcb002`

Creates (in order):
1. `hcp_medication_catalog` — depends on `hc_branches`
2. `hcp_prescriptions` — depends on `hc_branches`, `hc_encounters`, `hc_patients`, `hc_providers`
3. `hcp_prescription_items` — depends on `hcp_prescriptions`, `hcp_medication_catalog`
4. `hcp_dispensing_log` — depends on `hcp_prescriptions`, `hc_providers`
5. `hcp_dispensing_items` — depends on `hcp_dispensing_log`, `hcp_medication_catalog`, `hcp_prescription_items`
6. `hcp_drug_interaction_log` — no FK dependencies (cache table)

**Rollback strategy (`downgrade`):**
Drop in reverse: `hcp_drug_interaction_log`, `hcp_dispensing_items`, `hcp_dispensing_log`,
`hcp_prescription_items`, `hcp_prescriptions`, `hcp_medication_catalog`.

---

**File: `hcp_002_rls_policies.py`**
**Revision ID:** `hcp002`
**Down revision:** `hcp001`

Applies RLS for `hcp_prescriptions` and `hcp_dispensing_log`:

```sql
ALTER TABLE hcp_prescriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY hcp_prescriptions_branch_isolation ON hcp_prescriptions
    USING (
        tenant_id = current_setting('app.tenant_id', true)
        AND (branch_id = current_setting('app.branch_id', true) OR current_setting('app.branch_id', true) = 'ALL')
    );

ALTER TABLE hcp_dispensing_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY hcp_dispensing_log_branch_isolation ON hcp_dispensing_log
    USING (
        tenant_id = current_setting('app.tenant_id', true)
        AND (branch_id = current_setting('app.branch_id', true) OR current_setting('app.branch_id', true) = 'ALL')
    );
```

**Rollback strategy (`downgrade`):** `DROP POLICY`; `DISABLE ROW LEVEL SECURITY`.

---

### Wave 5 — Healthcare Lab

**Dependency:** Wave 4 complete (`hcp002` at head).

**File: `hcl_001_lab_tables.py`**
**Revision ID:** `hcl001`
**Down revision:** `hcp002`

Creates (in order):
1. `hcl_test_catalog` — depends on `hc_branches`
2. `hcl_test_orders` — depends on `hc_branches`, `hc_patients`, `hc_encounters`, `hc_providers`
3. `hcl_test_order_items` — depends on `hcl_test_orders`, `hcl_test_catalog`
4. `hcl_specimens` — depends on `hcl_test_orders`, `hcl_test_order_items`
5. `hcl_results` — depends on `hcl_test_orders`, `hcl_test_order_items`, `hcl_specimens`
6. `hcl_critical_alerts` — depends on `hcl_results`, `hcl_test_orders`, `hc_providers`

**Rollback strategy (`downgrade`):**
Drop in reverse: `hcl_critical_alerts`, `hcl_results`, `hcl_specimens`, `hcl_test_order_items`,
`hcl_test_orders`, `hcl_test_catalog`.

---

**File: `hcl_002_rls_policies.py`**
**Revision ID:** `hcl002`
**Down revision:** `hcl001`

Applies RLS for `hcl_test_orders` and `hcl_results`:

```sql
ALTER TABLE hcl_test_orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY hcl_test_orders_branch_isolation ON hcl_test_orders
    USING (
        tenant_id = current_setting('app.tenant_id', true)
        AND (branch_id = current_setting('app.branch_id', true) OR current_setting('app.branch_id', true) = 'ALL')
    );

ALTER TABLE hcl_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY hcl_results_branch_isolation ON hcl_results
    USING (
        tenant_id = current_setting('app.tenant_id', true)
        AND (branch_id = current_setting('app.branch_id', true) OR current_setting('app.branch_id', true) = 'ALL')
    );
```

**Rollback strategy (`downgrade`):** `DROP POLICY`; `DISABLE ROW LEVEL SECURITY`.

---

## Dependency Graph (Condensed)

```
Platform head (pg_unify_module_system)
  └─ hc001 (base tables)
      └─ hc002 (base RLS)
          └─ hc003 (audit_log permissions)
              └─ hc004 (i18n_overrides)
                  └─ hcs001 (scheduling tables + deferred FK on hc_encounters)
                      └─ hcs002 (scheduling RLS)
                          └─ hcb001 (billing tables)
                              └─ hcb002 (billing RLS)
                                  └─ hcp001 (pharmacy tables)
                                      └─ hcp002 (pharmacy RLS)
                                          └─ hcl001 (lab tables)
                                              └─ hcl002 (lab RLS)  ← final head
```

---

## RLS Migration Notes (ADR-HC-001 §D4)

1. **Raw SQL only** — RLS `CREATE POLICY` statements cannot be generated by SQLAlchemy's
   `autogenerate`. All RLS migrations use `op.execute(raw_sql)` inside the Alembic migration.

2. **Session variable setup** — `healthcare_branch_session` (ADR-HC-001 §D1) sets the
   following DB session variables before any query:
   ```sql
   SET LOCAL app.tenant_id = '<tid>';
   SET LOCAL app.branch_id = '<bid>';   -- or 'ALL' for clinic_owner
   ```
   RLS policies reference `current_setting('app.tenant_id', true)` (second arg = true returns
   NULL if unset, rather than raising an error). The application must always set both variables.

3. **Superuser / migration user exemption** — Alembic runs as the `alembic_admin` role, which
   has `BYPASSRLS`. RLS policies do NOT affect migration execution.

4. **Testing requirement** — ADR-HC-001 §Consequences mandates integration tests covering all
   three enforcement layers (ORM listener, RLS, header validation) for every model with
   `branch_id`. The D1 developer must confirm test fixtures cover:
   - A staff user querying their own branch (expect: data returned).
   - A staff user with a different `app.branch_id` (expect: empty result set from RLS).
   - A `clinic_owner` with `app.branch_id = 'ALL'` (expect: all branch data returned).

5. **Policy naming** — All RLS policies follow the pattern: `<table_name>_branch_isolation` or
   `<table_name>_tenant_isolation`. Names are enforced to ease `DROP POLICY` in rollback.

---

## Cross-Module FK Notes

| FK | Added in | Deferred? | Reason |
|---|---|---|---|
| `hc_encounters.appointment_id` → `hcs_appointments.id` | `hcs001` (ALTER TABLE) | YES — DEFERRABLE INITIALLY DEFERRED | `hcs_appointments` does not exist at Wave 1; FK added in Wave 2 |
| All other cross-module FKs | Same wave as parent table | NO | Tables in same migration batch |

---

## Rollback Strategy Summary

| Wave | Rollback complexity | Key risk |
|---|---|---|
| Wave 1 (base) | HIGH — deletes all PHI tables | Irreversible for live data; requires full DB backup before upgrade |
| Wave 2 (scheduling) | MEDIUM — drops scheduling tables + removes FK from encounters | Safe; no PHI data loss beyond appointments |
| Wave 3 (billing) | MEDIUM | Safe; drops billing tables |
| Wave 4 (pharmacy) | MEDIUM | Safe; drops pharmacy tables |
| Wave 5 (lab) | MEDIUM | Safe; drops lab tables |

**Production rollback protocol:**
1. Take a point-in-time snapshot before running any Wave upgrade.
2. For Wave 1, obtain explicit sign-off from the Data Protection Officer (DPO) before rollback,
   as it deletes PHI table structures (even if empty).
3. For Waves 2–5, rollback can be executed by the release engineer without DPO sign-off if
   no patient data has been written since the upgrade.

---

## Hand-off to C1 (Backend Developer)

The C1 developer team should action the following before implementing any service layer:

1. **Confirm `alembic_admin` role** has `BYPASSRLS` in the target DB environment.
2. **Confirm `app_user` role** (application DB user) does NOT have `BYPASSRLS`.
3. **Review the deferred FK** on `hc_encounters.appointment_id` — the ORM model for
   `hc_encounters` must reflect `Optional[UUID]` with a deferred FK constraint.
4. **Register `BranchScopeListener`** (ADR-HC-001 §D1) against all models tagged `branch_id NOT NULL`.
5. **Implement `write_phi_read_audit()`** (ADR-HC-002 §D2) inside `modules/healthcare/sdk/phi_audit.py`
   before any SDK PHI reader function is wired up.
6. **Encryption at rest** — PHI column encryption (AES-256) must be implemented at the model
   layer (e.g. via `sqlalchemy-utils EncryptedType` or equivalent) before any PHI migration
   goes to production. This is a HARD blocker for Wave 1 production deployment.
7. **`hcp_drug_interaction_log` TTL cleanup** — a scheduled job (or DB `pg_cron`) must delete
   rows where `expires_at < NOW()` to prevent unbounded cache growth.
8. **`hc_audit_log` partitioning** — recommend `PARTITION BY RANGE (created_at)` (monthly or
   quarterly) be added to `hc_001_base_tables.py` before the first production run, as this
   table will be the highest-volume append target.

*Schema design: B2 Data Engineer. Reviewed against: ADR-HC-001, ADR-HC-002, ADR-HC-003,
ADR-HC-004, epics 01-05, 07. Epic-06 excluded — pending legal review.*
