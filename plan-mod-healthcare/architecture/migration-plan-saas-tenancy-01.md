---
artifact_id: migration-plan-saas-tenancy-01
type: migration-plan
module: healthcare
status: proposed
producer: B1 Backend Architect
upstream: [adr-hc-010-saas-tenancy-and-patient-scoping, adr-hc-005 (Amendment v2), adr-hc-009 (Amendment v3), schema-hc-04, review-saas-tenancy-01]
created: 2026-07-06
---

# Migration Plan — Consolidate Separate-Tenant Clinics into the Shared SaaS Tenant

> **Design/docs only.** Ordered plan to migrate **MedCare** (legacy, unlinked) and **HealthPoint**
> (already ADR-HC-005-linked) from separate platform Tenants into ONE shared `SAAS` Tenant as
> **Companies**, each clinic site a **Branch**, with **Company** as the new patient isolation key
> (ADR-HC-010). Per RULING 1 it is a **clean partition — no patient merge across Companies.**

## The make-or-break ordering constraint

**Patient-scoping enforcement (ADR-HC-010 D1/D2 — `hc_patients.company_id` + Company RLS) MUST land
BEFORE any data is consolidated into the shared tenant.** If clinics are re-pointed to the shared tenant
*before* `company_id` isolates patients, there is a window where **all patients of all clinics pool into
one tenant with no Company isolation** — the critical data-isolation breach A3 flagged. The sequence is
therefore: **(a) scoping schema → (b) backfill Company on all HC rows → (c) re-point tenant_id / provision
Companies+Branches → (d) consolidate + cut over RLS → verify.** Migration is the **last** thing; scoping
is the **first**.

## Ground truth (verified)

| Clinic | Today | ADR-HC-005 linkage | Notes |
|---|---|---|---|
| **MedCare** | Own platform Tenant (`MEDCARE`). | **None** — `hc_branches.platform_company_id/branch_id` NULL (legacy). | Needs a Company provisioned + linkage backfilled from scratch. |
| **HealthPoint** | Own platform Tenant (`HEALTHPOINT`). | **Partial** — `hc_branches` carry `platform_company_id`/`platform_branch_id`, but `tenant_id` still points at the old per-clinic tenant. | Closer; still must re-point `tenant_id` to shared + set patient `company_id`. |

Tables carrying `tenant_id` that must be handled: `hc_patients`, `hc_patient_relationships`,
`hc_patient_consents`, `hc_branches`, `hc_branch_staff`, `hc_departments`, `hc_provider_departments`,
all branch-scoped clinical tables (`hcr_visits`, `hc_encounters`, `hcs_appointments`, `hcb_invoices`,
`hc_diagnoses`, `hc_procedures`, `hc_clinical_notes`, `hcr_queue_tickets`, dispensing, lab), and
`hc_audit_log`.

---

## Phase 0 — Provision the shared tenant & the target Companies (platform-org, out-of-band)

Before touching HC data:

1. **Provision the shared `SAAS` Tenant** (once) via the platform org API — or reuse if it exists.
2. **Create a Company per legacy clinic** under `SAAS` via the platform org API: **Company MedCare**,
   **Company HealthPoint** (`companies.code` = the intended public slug — the future portal slug,
   ADR-HC-010 D6). Record the resulting `companies.id` values → `medcare_company_id`,
   `healthpoint_company_id`.
3. **Create a Branch per clinic site** under each Company via the platform org API; record the
   `branches.id` per site. (HealthPoint already has `platform_branch_id` values — reconcile/reuse them;
   MedCare gets fresh ones.)
4. Build the **mapping table** (a scratch/migration table): `old_tenant_id → new_company_id`, and per
   clinic site `old hc_branches.id → platform branches.id → company_id`. This mapping drives every
   backfill below. No `hc_*` data changes yet.

## Phase 1 — Land the patient-scoping SCHEMA (ADR-HC-010 D1/D2, schema-hc-04 §S) — GATE

**Nothing consolidates until this phase is complete and verified.**

1. `ALTER TABLE hc_patients ADD COLUMN company_id VARCHAR(36) NULL;` (nullable — schema-hc-04 §S.1 STEP 1).
2. `ALTER TABLE hc_branch_staff ADD COLUMN company_id VARCHAR(36) NULL;` (schema-hc-04 §S.2).
3. Add ORM columns (`HCPatient.company_id`, `HCBranchStaff.company_id`) so the app reads/writes them.
4. Do **NOT** yet re-key RLS or set NOT NULL — the column is nullable and unenforced during backfill.

**Verify:** columns exist, nullable, app boots with the new ORM.

## Phase 2 — Backfill `company_id` on ALL HC rows (per the Phase-0 mapping)

Using the mapping (each old clinic tenant → its new Company):

1. **`hc_patients`** — set `company_id` from the row's old `tenant_id` via the mapping. **Clean
   partition (RULING 1):** MedCare patients → `medcare_company_id`; HealthPoint patients →
   `healthpoint_company_id`. **No merge** — a person who is a patient at both keeps **two rows** with
   different `company_id`.
2. **`hc_branch_staff`** — for `clinic_owner` sentinel rows (`branch_id IS NULL`), set `company_id` =
   the owner's Company (from the mapping). Non-owner rows leave `company_id` NULL (isolated by
   `branch_id`).
3. **`hc_branches`** — backfill/reconcile `platform_company_id`/`platform_branch_id` from the mapping
   (MedCare from scratch; HealthPoint reconcile existing values). This is the ADR-HC-005 linkage backfill.
4. `hc_patient_relationships` — no `company_id` column (derives via `patient_id`, ADR-HC-009 AM3-1);
   verify each row's `patient_id` now resolves to a patient with a `company_id`. If the optional denorm
   `company_id` is adopted, backfill it from the patient here.

**Verify:** `SELECT count(*) FROM hc_patients WHERE company_id IS NULL` = 0 for every clinic; each
patient's `company_id`'s `companies.tenant_id` equals the (still old) row `tenant_id` for that clinic
(the app-enforced linkage invariant, pre-repoint).

## Phase 3 — Re-point `tenant_id` to the shared tenant (all HC tables)

For **every** HC table carrying `tenant_id`, update `tenant_id` from the old per-clinic tenant to the
shared `SAAS` tenant, per clinic, in dependency-safe order (registry/branches first, then patient +
clinical + relationships + consents + audit):

```
UPDATE <hc_table> SET tenant_id = :saas_tenant WHERE tenant_id = :old_medcare_tenant;
UPDATE <hc_table> SET tenant_id = :saas_tenant WHERE tenant_id = :old_healthpoint_tenant;
```

- Do this **inside a transaction per clinic** (or a controlled window) so a partial re-point never
  leaves rows split across tenants for one clinic.
- **`company_id` is already set (Phase 2)** — so even as `tenant_id` collapses to one value, patients
  remain isolated by `company_id`. This is why Phase 1/2 gate Phase 3.
- HealthPoint's `hc_branches.platform_*` columns are re-pointed/reconciled to the shared tenant's
  Company/Branch ids in this phase.

**Verify (after each clinic):** every re-pointed table has `tenant_id = :saas_tenant`; patient counts
per `company_id` are unchanged (no rows lost/merged); the linkage invariant now reads
`companies.tenant_id == :saas_tenant == hc_patients.tenant_id`.

## Phase 4 — Cut over RLS to Company + constrain (schema-hc-04 §S.1 STEP 3, §R)

Only after Phase 2/3 (no NULL `company_id`, all rows on the shared tenant):

1. `ALTER TABLE hc_patients ALTER COLUMN company_id SET NOT NULL;`
2. Shared-DB: `ADD CONSTRAINT fk_hc_patients_company FOREIGN KEY (company_id) REFERENCES companies(id);`
   and `fk_hc_branch_staff_company`. (Split-DB: app-enforced, skip the FK.)
3. **Re-key the patient-registry RLS** (schema-hc-04 §S.1): drop the tenant-only `rls_hc_patients`
   policy, create the Company-keyed one (`company_id = current_setting('app.company_id') AND tenant_id =
   current_setting('app.tenant_id')`).
4. Deploy the session-dependency change that **sets `app.company_id`** on every healthcare session
   (staff branch, patient/portal, reporting) — schema-hc-04 §R.1. The owner `branch_id='ALL'` bypass is
   now AND-ed with the owner's Company GUC (ADR-HC-010 D4a).
5. Deploy the `clinic_owner` sentinel re-scope, the household same-Company guards (ADR-HC-009 AM3-3), and
   the token `company_id` claim (ADR-HC-010 D5).

**Verify (isolation acceptance tests — the make-or-break checks):**
- A **staff/owner session for Company A returns ZERO Company-B patients** (RLS-level: with
  `app.company_id = A`, `SELECT * FROM hc_patients` yields no Company-B rows). Test both a branch
  manager and the `clinic_owner` sentinel (the ex-super-owner) — the owner must **not** see Company B.
- A **patient/portal session** with the active patient's `company_id` cannot read another Company's
  patient (household `switch`/`from-platform` to a foreign patient → 403; `request_link` to a foreign-
  Company patient → silent deny / `cross_company` 422).
- An unset `app.company_id` yields **no rows** (fail-closed).
- MedCare patient count under `company_id = medcare_company_id` == pre-migration MedCare patient count;
  same for HealthPoint. **No cross-Company leakage, no merged rows.**

## Phase 5 — Onboarding + portal cutover (hand to epic-20)

- Stop minting a Tenant per clinic in `clinic_register`; new signup attaches to `SAAS` + creates a
  Company + first Branch (ADR-HC-005 Amendment v2; A3's `epic-20-saas-onboarding`).
- Re-key portal clinic resolution to Company/Branch slug + directory landing (ADR-HC-010 D6,
  schema-hc-04 §C). These are **application** changes handed to the epic; the migration above makes the
  data ready for them.

---

## Rollback

- **Phases 1–2 (additive, nullable, no RLS change):** fully reversible — drop `company_id` columns; no
  data lost (the mapping is external; original `tenant_id` untouched until Phase 3).
- **Phase 3 (tenant_id re-point):** reversible by the **inverse mapping** (`shared → old per-clinic
  tenant`) **per clinic**, because `company_id` uniquely identifies each clinic's rows even after the
  re-point — so the old tenant assignment can be reconstructed from `company_id`. Take a DB snapshot
  before Phase 3 regardless.
- **Phase 4 (RLS re-key + NOT NULL + FK):** reversible by restoring the tenant-only `rls_hc_patients`
  policy and dropping NOT NULL/FK; the session-dependency deploy is a code rollback. Because Phase 4 is
  the enforcement cutover, gate it behind the Phase-4 verification suite and be prepared to roll the RLS
  policy back independently of the data.
- **Golden rule:** never run Phase 3 before Phase 1/2 verify green; never run Phase 4 before Phase 3
  verify green. Snapshot before Phase 3 and before Phase 4.

## Verification summary (the isolation guarantees to prove)

1. Zero NULL `company_id` on `hc_patients` before Phase 4 (Phase 2 gate).
2. Per-clinic patient counts preserved and partitioned by `company_id` (no merge — RULING 1).
3. Company-A session (branch manager **and** owner sentinel) reads zero Company-B patients (RLS).
4. Patient/household paths deny cross-Company (403 / `cross_company` 422).
5. Fail-closed on unset `app.company_id` (no rows).
6. Linkage invariant `companies.tenant_id == hc_patients.tenant_id == :saas_tenant` post-Phase-3.

---

*Cross-references: ADR-HC-010 (scoping decisions D1/D2/D4/D5), schema-hc-04 (DDL + RLS §S/§R),*
*ADR-HC-005 Amendment v2 (shared-tenant default), ADR-HC-009 Amendment v3 (household within one*
*Company), review-saas-tenancy-01 §6 + Hand-off (e).*
