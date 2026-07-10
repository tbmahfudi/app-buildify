---
artifact_id: schema-hc-04
type: schema-design
module: healthcare (module deltas) + platform (Company reference)
status: proposed
producer: B1 Backend Architect
upstream: [schema-hc-01, schema-hc-02, schema-hc-03, adr-hc-010-saas-tenancy-and-patient-scoping, adr-hc-005 (Amendment v2), adr-hc-009 (Amendment v3), adr-hc-001, adr-hc-002, adr-hc-008]
created: 2026-07-06
---

# Schema Design v4 — Shared-Tenant SaaS: Company-Scoped Patients & Branch-Primary Isolation

> Companion to **ADR-HC-010**. Covers **only** the objects/columns ADR-HC-010 introduces or changes:
> the `hc_patients.company_id` isolation column (D1), the `hc_branch_staff.company_id` owner anchor
> (D4a), the **Company RLS re-key + `app.company_id` GUC** for the patient registry (D2), the
> `hc_patient_relationships` Company derivation (ADR-HC-009 AM3-1), and the portal clinic-resolution
> keying change (D6). Conventions, PHI encryption (`EncryptedPHIType`, AES-256), and the RLS style are
> inherited **verbatim** from schema-hc-01 §Conventions. DDL is Postgres; `gen_random_uuid()` stands in
> for the app's `GUID` default.
>
> **Isolation-invariant change (flagged).** This document **changes an ADR-HC-001 invariant**: the
> **patient registry's** isolation key moves from `tenant_id` to **`company_id`** (a new `app.company_id`
> GUC). Branch-scoped clinical tables are **unchanged** (still `tenant_id` + `branch_id`), because a
> Branch belongs to exactly one Company. See §R and the ADR-HC-001 conformance note in ADR-HC-010.

## Conventions (delta on schema-hc-01/02)

| Convention | Rule |
|---|---|
| `company_id` | `VARCHAR(36)` referencing platform `companies.id`; the **clinic-business isolation key** for the patient registry (ADR-HC-010 D1). FK real in shared-DB, app-enforced when split (R4 posture). |
| `tenant_id` | Retained on all `hc_*` rows (the shared `SAAS` tenant id, or a dedicated tenant id); **no longer the clinic-isolation key for patients** — kept as an AND-ed defence-in-depth guard + platform-session compatibility. |
| **RLS (Company-scoped patient registry)** | `company_id = current_setting('app.company_id')` (AND `tenant_id = current_setting('app.tenant_id')` as a defence-in-depth guard). **Fail-closed:** unset `app.company_id` → no rows. No `'ALL'` Company escape hatch. |
| **RLS (branch-scoped clinical)** | **Unchanged** — `tenant_id = current_setting('app.tenant_id') AND (branch_id = current_setting('app.branch_id') OR current_setting('app.branch_id') = 'ALL')` (schema-hc-02). Owner rollup additionally sets `app.company_id` (§R). |

---

## Part S — `hc_patients` & `hc_branch_staff` deltas (MODULE)

### S.1 `hc_patients` — new `company_id` column + Company RLS re-key (ADR-HC-010 D1/D2)

`hc_patients` today is `__tenant_scoped__`, no `branch_id` (`models.py` L371–376). It gains a
**`company_id`** column that becomes its isolation key. Not PHI (an id).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `company_id` | VARCHAR(36) | **NOT NULL** (after backfill) | — | FK → `companies.id` (shared-DB); app-enforced split. Isolation key. |

```sql
-- STEP 1 (migration): add nullable so existing rows migrate without a blocker.
ALTER TABLE hc_patients
    ADD COLUMN company_id VARCHAR(36) NULL;

-- STEP 2 (migration): backfill company_id for every patient from its clinic business
--   (per migration-plan-saas-tenancy-01: old-tenant → new Company mapping). Then:
CREATE INDEX idx_hc_patients_company_id ON hc_patients (company_id);

-- STEP 3 (migration, LAST — after no NULLs remain): constrain + FK (shared-DB).
ALTER TABLE hc_patients
    ALTER COLUMN company_id SET NOT NULL;
-- Shared-DB only — real FK to platform companies; app-enforced when split-DB.
ALTER TABLE hc_patients
    ADD CONSTRAINT fk_hc_patients_company
        FOREIGN KEY (company_id) REFERENCES companies(id);

-- RE-KEY RLS from tenant-only to Company (ADR-HC-010 D2). Replace the tenant-scoped policy:
DROP POLICY IF EXISTS rls_hc_patients ON hc_patients;
CREATE POLICY rls_hc_patients ON hc_patients
    USING (company_id = current_setting('app.company_id')
       AND tenant_id  = current_setting('app.tenant_id'));   -- tenant AND-ed as defence-in-depth
ALTER TABLE hc_patients ENABLE ROW LEVEL SECURITY;
```

**App-enforced invariant:** `companies.tenant_id == hc_patients.tenant_id` for the referenced Company
(validated at write; a cross-DB CHECK is not expressible — same posture as ADR-HC-005 D1's linkage
invariant). A patient at two unrelated Companies has **two rows with different `company_id`** (RULING 1;
no merge).

**ORM:** add `company_id = Column(String(36), nullable=False, index=True)` to `HCPatient` in
`modules/healthcare/backend/models.py` (after `tenant_id`, ~L379). The FK is DB-declared in shared-DB
(not on the ORM class, mirroring `HCBranch.platform_company_id` which keeps FKs DB-side).

### S.2 `hc_branch_staff` — new nullable `company_id` (owner-sentinel anchor, ADR-HC-010 D4a)

The `clinic_owner` sentinel row (`branch_id = NULL`) must carry **which Company** it owns, so the
"all branches" bypass is fenced to that Company (not the whole shared tenant). Non-owner rows leave it
NULL and stay isolated by `branch_id` as before. Not PHI.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `company_id` | VARCHAR(36) | NULL | — | FK → `companies.id` (shared-DB); set for `clinic_owner` (`branch_id=NULL`) rows; the owner's Company anchor. |

```sql
ALTER TABLE hc_branch_staff
    ADD COLUMN company_id VARCHAR(36) NULL;
-- Shared-DB only — real FK; app-enforced when split.
ALTER TABLE hc_branch_staff
    ADD CONSTRAINT fk_hc_branch_staff_company
        FOREIGN KEY (company_id) REFERENCES companies(id);
CREATE INDEX idx_hc_branch_staff_company ON hc_branch_staff (company_id)
    WHERE company_id IS NOT NULL;

-- App-enforced: a clinic_owner row (branch_id IS NULL) MUST have company_id NOT NULL
--   (the owner owns exactly one Company's branches). A non-owner row (branch_id NOT NULL)
--   leaves company_id NULL. Enforced at write + a partial CHECK where expressible:
ALTER TABLE hc_branch_staff
    ADD CONSTRAINT ck_hc_branch_staff_owner_company
        CHECK ( (branch_id IS NOT NULL) OR (company_id IS NOT NULL) );
```

**Owner bypass (ADR-HC-001 §D3 amended):** the `clinic_owner` session sets `app.branch_id = 'ALL'`
**AND** `app.company_id = <owner's company_id>`. The Company GUC is the outer fence; the owner sees all
branches **of their Company**, never other Companies. There is **no** Company-level `'ALL'`.

**ORM:** add `company_id = Column(String(36), nullable=True)` to `HCBranchStaff` (after `branch_id`,
~L88).

---

## Part R — RLS / GUC changes & reporting re-scope (ADR-HC-010 D2/D4/D7)

### R.1 New `app.company_id` GUC (set alongside `app.tenant_id`/`app.branch_id`)

Every healthcare session dependency sets `app.company_id` in addition to the existing GUCs:

```sql
-- staff branch session (healthcare_branch_session): the branch's Company
SET LOCAL app.tenant_id  = :tid;
SET LOCAL app.branch_id  = :bid;           -- or 'ALL' for owner
SET LOCAL app.company_id = :cid;           -- the caller's ONE Company (owner or branch's Company)

-- patient/portal session (get_patient_db): the active patient's Company (from the token company_id claim)
SET LOCAL app.tenant_id  = :active_tenant; -- the active patient's tenant
SET LOCAL app.company_id = :active_company;-- the active patient's company_id (ADR-HC-010 D5 claim)

-- reporting/owner session: the owner's Company (branch_id='ALL' for exec dashboards)
SET LOCAL app.company_id = :owner_company;
SET LOCAL app.branch_id  = 'ALL';
```

- **Fail-closed:** an unset `app.company_id` makes the Company-scoped RLS predicate false → **no rows**
  (matches ADR-HC-001 §D2 and ADR-HC-008 `current_setting(..., true)` NULL→no-rows).
- **No cross-Company super-read:** unlike `app.branch_id = 'ALL'`, there is **no** `app.company_id =
  'ALL'`. Cross-Company visibility exists only in the dedicated-tenant topology (a *separate tenant*,
  resolved the platform way).

### R.2 Tables that re-key to Company vs stay tenant/branch-scoped

| Table | Scope change |
|---|---|
| `hc_patients` | **RE-KEY to Company** (§S.1). Patient registry. |
| `hc_patient_relationships` | RLS **inherits the Company fence via `patient_id`** (co-located with `hc_patients`, RLS-scoped). Same-Company (Q2→Company) enforced by the patient's `company_id` + app check on the account holder's Company (ADR-HC-009 AM3-1). Optional denormalized `company_id` column only if the pending-queue index needs it — **not required**. |
| `hc_patient_consents` | Tenant-scoped module PHI today; follows the patient — reads are fenced by the patient's Company at the application layer (the consent's `patient_id` resolves to a Company-fenced patient). No RLS re-key required at MVP (consents are always accessed for a known, Company-fenced patient); flagged as an optional Company re-key for defence-in-depth. |
| `hc_branches`, `hc_branch_staff`, `hc_departments` (staff-facing reads) | Fenced by the session Company for **enumeration** (RBAC cross-Company gating, ADR-HC-010 D4b): a caller lists only their Company's branches/staff. `X-Branch-ID` selects the active branch within the Company. |
| Branch-scoped clinical (`hcr_visits`, `hc_encounters`, `hc_diagnoses`, `hc_procedures`, `hc_clinical_notes`, `hcr_queue_tickets`, `hcs_appointments`, `hcb_invoices`, dispensing, lab, …) | **UNCHANGED** — `tenant_id` + `branch_id` RLS (schema-hc-02). A Branch belongs to one Company, so branch-scoping already isolates by Company. |

### R.3 Reporting views (ADR-HC-008) — Company fence on owner rollup (ADR-HC-010 D7)

The eight ADR-HC-008 views (schema-hc-02 §D) are **branch-scoped clinical aggregates** and need **no
view-definition change** — branch-scoping already fences them to one Company. The change is at the
**session** layer: the owner exec-dashboard path (which sets `app.branch_id = 'ALL'`) must **also** set
`app.company_id = <owner's Company>` so an owner's "all branches" rollup is their **Company's** branches,
not the whole SaaS. Any future view that aggregates the **patient registry** directly must add the
`company_id = current_setting('app.company_id', true)` predicate (NULL→no rows). Documented as an
ADR-HC-008 conformance note; no DDL delta to the existing eight views.

---

## Part C — Portal clinic-resolution keying (ADR-HC-010 D6)

No new tables. The public clinic slug changes from **`tenants.code`** to **`companies.code`** (unique
per tenant; under the single shared tenant, unique across the SaaS), with an optional Branch segment.
Query changes (implementation handed to the portal epic; recorded here for schema/keying clarity):

- `routes_public.py` `_get_profile` (L264–272): `SELECT id,name FROM tenants WHERE UPPER(code)=UPPER(:slug)`
  → `SELECT id,name FROM companies WHERE UPPER(code)=UPPER(:slug) AND tenant_id = :saas_tenant`, then
  branches filtered by `hc_branches.platform_company_id = :company_id` (a Company's clinic sites).
- `clinic_search` groups by **Company** (`companies.id`/`code`) instead of tenant.
- `routes_household.py` `get_my_clinic` (`/me/clinic`, L108–114): `SELECT code,name FROM tenants WHERE
  id=:tid` → `SELECT code,name FROM companies WHERE id = :active_company` (the active patient's
  `company_id`, ADR-HC-010 D5).
- Logged-out landing → a PHI-free **Company directory/chooser** (the only cross-Company read surface),
  plus per-Company/Branch deep-link URLs.

`companies` already carries `id`, `tenant_id`, `code` (unique per tenant, indexed), `name`
(`backend/app/models/company.py`) — no new column needed for the slug; `code` **is** the slug.

---

## Object Summary

| Layer | Object | Kind | Key columns | PHI? |
|---|---|---|---|---|
| **MODULE** | `hc_patients` | ALTER +1 col + RLS re-key | `company_id`(→companies.id, **isolation key**, NOT NULL after backfill); RLS `company_id = app.company_id` | No (id) |
| **MODULE** | `hc_branch_staff` | ALTER +1 col | `company_id`(→companies.id, NULL; set on `clinic_owner` sentinel rows — owner Company anchor) | No |
| **MODULE** | `hc_patient_relationships` | (no schema change) | Company fence derived via `patient_id`→`hc_patients.company_id`; optional denorm `company_id` if queue index needs it | No |
| **PLATFORM** | `companies` | (no change) | `id`, `tenant_id`, `code` (public slug), `name` — FK target + portal resolution | No |
| **RLS/GUC** | `app.company_id` | New GUC | set alongside `app.tenant_id`/`app.branch_id`; fail-closed; no `'ALL'` | — |

| Kind | Count |
|---|---|
| Altered module tables | **2** (`hc_patients` +`company_id` + RLS re-key; `hc_branch_staff` +`company_id`) |
| New GUC | **1** (`app.company_id`) |
| RLS policies changed | **1** (`rls_hc_patients` re-keyed tenant→Company) |
| New PHI columns | **0** |
| Portal keying change | tenant code → Company (`companies.code`) slug (no DDL) |

---

*Cross-references: ADR-HC-010 (shared-tenant SaaS; Company scoping), ADR-HC-005 Amendment v2*
*(shared-tenant default), ADR-HC-009 Amendment v3 (household within one Company; token `company_id`),*
*ADR-HC-001 (branch isolation — patient-registry invariant amended to Company; branch RLS retained),*
*ADR-HC-002 (PHI — no new PHI), ADR-HC-008 (reporting — owner rollup Company fence), schema-hc-01/02/03*
*(base definitions + conventions), `backend/app/models/company.py` (`companies` shape).*
