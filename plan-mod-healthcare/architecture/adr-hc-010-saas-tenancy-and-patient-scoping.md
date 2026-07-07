---
artifact_id: adr-hc-010
type: adr
module: healthcare
status: proposed
producer: B1 Backend Architect
upstream: [review-saas-tenancy-01, adr-hc-005-org-linkage-departments (accepted), adr-hc-001-branch-isolation-strategy, adr-hc-002-phi-handling, adr-hc-004-i18n, adr-hc-008-reporting-views, adr-hc-009-patient-identity-and-auth (v2), schema-hc-02, schema-hc-03, models.py, routes_public.py, routes_household.py, routes_clinic_signup.py, routes_patient_auth.py]
created: 2026-07-06
---

# ADR-HC-010 — Shared-Tenant SaaS: Company-Scoped Patients, Branch-Primary Isolation

## Status

proposed — implements A3's `review-saas-tenancy-01` Hand-off items **(a)** patient scoping,
**(c)** branch-as-primary isolation + RBAC + reporting re-scope, and **(f)** the tenancy-model
disposition (amend ADR-HC-005, do **not** supersede). Hand-off **(b)** household re-scope amends
ADR-HC-009 (separate amendment). Hand-off **(d)** portal resolution is a decision here + a hand to
the implementation epic. Hand-off **(e)** migration is `migration-plan-saas-tenancy-01.md`. This is a
**design/docs** artifact — no application code.

## Why a new ADR rather than folding into ADR-HC-005 (Hand-off (f))

**Decision: NEW ADR (this one) + a marked amendment on ADR-HC-005, NOT a supersede.** ADR-HC-005 is
about *platform-org linkage* (a clinic **is** a platform Branch; linkage columns; `hc_departments`).
That decision is correct and unchanged. What is genuinely new and material is a **patient-store
isolation-boundary change** (tenant → Company) and a **privilege-escalation fix** — big enough to
deserve its own titled, testable ADR rather than being buried in a linkage ADR's addendum. ADR-HC-005
gets a short **Amendment v2** stating the default flip (shared tenant) and pointing here for the
patient-scoping consequence; the four A4 decisions in ADR-HC-005 (dedicated-tenant = provisioning
choice, no HC schema differs) **stand verbatim**.

## Context (verified against code — the isolation boundary is moving)

| Aspect | Today | Under shared-tenant SaaS |
|---|---|---|
| `tenant_id` meaning | **== one clinic business** (MedCare, HealthPoint are separate tenants). | A single shared `SAAS` tenant for ALL clinics; `tenant_id` no longer isolates a clinic. |
| `hc_patients` scope | `__tenant_scoped__`, **no `branch_id`** (`models.py` L371–376, "patients belong to tenant, not branch"). | Must become **Company-scoped** — else all patients of every clinic on the SaaS pool into one set (data-isolation breach). |
| Patient RLS | ADR-HC-001 §D4: `tenant_id = app.tenant_id` (patient registry is tenant-scoped, not branch-scoped). | Patient registry re-keys to **`company_id = app.company_id`**; branch-scoped clinical tables keep `branch_id` isolation. |
| `clinic_owner` staff row | `hc_branch_staff` with `branch_id = NULL` = "owner of this tenant's clinic" (`routes_clinic_signup.py` L120–128). | `branch_id = NULL` now means "owner of the whole shared tenant" = **SaaS-wide super-owner** unless re-scoped to Company. Privilege-escalation risk. |
| Reporting views (ADR-HC-008) | tenant + branch scoped; a tenant-wide aggregate == one clinic. | tenant-wide aggregate == the whole SaaS; must re-scope to **Company** (+ Branch). |

The pivot's core tension: **every isolation invariant is keyed on `tenant_id`, and today `tenant_id`
== one clinic.** Collapsing all clinics into one tenant removes `tenant_id` as the clinic boundary.
This ADR re-homes the patient-store boundary onto **Company** and confirms **Branch** as the primary
isolation axis for clinical data, under a single shared tenant.

Ratified user rulings this ADR enforces:

- **RULING 1 — Patient scope = COMPANY.** A patient record is scoped to a Company, **shared across
  that Company's Branches**, **isolated between Companies**. A person who is a patient at two unrelated
  Companies has **two records**; no cross-Company shared PHI. Company is the "clinic-business"
  isolation unit that `tenant_id` is today.
- **RULING 2 — Household/proxy scope = WITHIN ONE COMPANY.** (Enforced in the ADR-HC-009 Amendment v3;
  referenced here for the token-claims decision.)

---

## Decision

### D1 — Patient-store scoping mechanism: add `company_id` to `hc_patients` (explicit column, not derived)

**Decision: `hc_patients` gains a `company_id VARCHAR(36) NOT NULL` column (the platform
`companies.id`), and it becomes the patient registry's primary isolation key** — **NOT** derived at
query time from a Branch/site link.

**Column, not derive — why.**

| Option | Verdict |
|---|---|
| **(chosen) Explicit `hc_patients.company_id`** | Indexable (fast Company-scoped search/list), RLS-friendly (a single `company_id = current_setting('app.company_id')` predicate — the same shape ADR-HC-001 already uses for `tenant_id`/`branch_id`), and unambiguous: the patient's owning clinic business is a stored fact, not a join result. A patient is deliberately **not** branch-scoped (ADR-HC-001 §D3 — a patient belongs to the whole clinic business, cross-site); Company is exactly "the whole clinic business," so a direct column matches the semantics. |
| Derive Company via `hc_patients → (some branch link) → hc_branches.platform_company_id` | `hc_patients` has **no `branch_id`** by design (L376), so there is no branch to derive from; adding one would fragment a patient across a Company's own sites (rejected by RULING 1 / ADR-HC-001 §D3). Deriving through a visit/clinical table is per-query, un-RLS-able (RLS can't run a join in a `USING` clause cheaply), and would make "which Company owns this patient" a computed, race-prone answer. Rejected. |

`company_id` references the platform `companies.id`. Cross-DB posture is **identical to ADR-HC-005
addendum A1 and ADR-HC-009 R4**: a **real FK `hc_patients.company_id → companies.id` in shared-DB**;
**app-enforced** when healthcare and platform are split-DB. One integrity story across all three ADRs.

**Relationship to `tenant_id`.** `hc_patients.tenant_id` is **retained** (all clinics now carry the
shared `SAAS` tenant id) for platform-session/GUC compatibility and defence-in-depth, but it **no
longer isolates clinics** — `company_id` does. The invariant is `hc_patients.company_id`'s
`companies.tenant_id == hc_patients.tenant_id` (app-validated at write, same as the ADR-HC-005 linkage
invariant). In the **dedicated-tenant** topology (rare, A4) `tenant_id` additionally hard-isolates that
owner's world and Company scoping applies within it — the column and RLS below hold one level down.

### D2 — Patient RLS re-keys from `tenant_id` to a new `app.company_id` GUC (invariant change — flagged)

**This changes an ADR-HC-001 isolation invariant for the patient registry and is called out
explicitly.** ADR-HC-001 §D4 scopes every healthcare object by `app.tenant_id` (+ `app.branch_id` for
branch-scoped). For the **patient registry and Company-scoped patient-adjacent tables**, the isolation
predicate becomes **Company-keyed**:

```sql
-- NEW patient-registry RLS (Company-scoped), replaces the tenant-only policy on hc_patients:
company_id = current_setting('app.company_id')
-- (tenant_id = current_setting('app.tenant_id') is retained as an AND-ed defence-in-depth guard,
--  but company_id is the clinic-isolation key.)
```

- A **new GUC `app.company_id`** is introduced **alongside** `app.tenant_id` (not instead of — branch-
  scoped clinical tables still use `app.tenant_id` + `app.branch_id` unchanged). The healthcare session
  dependencies (`healthcare_branch_session`, the patient/public sessions, and the reporting session)
  set `SET LOCAL app.company_id = :cid` in addition to the existing `app.tenant_id`/`app.branch_id`.
- **Where `company_id` comes from per caller:**
  - **Staff sessions:** resolved from the staff member's Company (the `hc_branches.platform_company_id`
    of the branch(es) they are assigned to, or the `clinic_owner`'s Company sentinel — D3). A staff
    caller's `app.company_id` is their one Company; cross-Company staff access is denied by RLS.
  - **Patient/portal sessions:** the active patient's `company_id` (the patient token gains a `company_id`
    claim — see D5 and the ADR-HC-009 amendment). `get_current_patient` / `get_patient_db` set
    `app.company_id` from the token so patient reads are Company-fenced.
  - **Owner aggregate / reporting:** `app.company_id` = the owner's Company; an `'ALL'`-Company escape
    hatch is **NOT** introduced (unlike `app.branch_id = 'ALL'`) — there is no cross-Company super-read,
    consistent with RULING 1's deny-cross-Company. The dedicated-tenant consolidated-view case (A4) gets
    cross-Company visibility only because it is a *separate tenant*, resolved the platform way.
- **Fail-closed:** an unset `app.company_id` yields **no rows** for Company-scoped tables (the RLS
  predicate is false), matching ADR-HC-001 §D2's fail-closed stance and ADR-HC-008's
  `current_setting(..., true)` NULL→no-rows rule for views.

**Branch-scoped clinical tables (`hcr_visits`, `hc_diagnoses`, `hc_encounters`, `hc_clinical_notes`,
etc.) are UNCHANGED** — they keep ADR-HC-001 §D4's `tenant_id` + `branch_id` RLS. Because a Branch
belongs to exactly one Company (a clinic site is one Company's branch), branch-scoping **already**
isolates by Company for clinical data; only the **non-branch-scoped patient registry** needed the new
Company key. This keeps the blast radius of the change tight.

### D3 — Re-scope every tenant-scoped patient path to Company (bridge, search, `me/*`)

Every path that today relies on `tenant_id` to fence patients re-scopes to **Company** (deny-cross-
Company by default, RULING 1 Rule P3):

- **`from-platform` bridge / `_resolve_active_patient`** (`routes_patient_auth.py` L366+): already
  authorizes via `hc_patient_relationships` (an `active` row for the account holder), which is
  Company-fenced by RULING 2 (the household is single-Company). No cross-Company set can form. The
  minted token carries the active patient's `company_id` (D5).
- **Patient search / list (staff)** — any staff patient search re-scopes from `WHERE tenant_id = :tid`
  to `WHERE company_id = :cid` (enforced by the D2 RLS; app queries filter on the session Company). A
  staff member at Company A can never search Company B's patients.
- **`GET /me/household`, `GET /me/clinic`, `switch`** — the household set is Company-fenced (RULING 2);
  `me/clinic` re-resolves to the patient's Company/Branch slug (D6).
- **Registration** (`register_dependent`, clinic-created patients) stamps the new patient's `company_id`
  from the creating caller's Company (staff branch → Company, or the account holder's Company).

### D4 — Branch is the primary isolation axis; re-scope the `clinic_owner` `branch_id = NULL` sentinel to Company (privilege-escalation fix)

**With one shared tenant, Branch is the primary isolation boundary and Company is the mid grouping**
(A3 §5). Two concrete decisions:

**(a) The `clinic_owner` `branch_id = NULL` sentinel is re-scoped to the owner's Company.** Today
(`routes_clinic_signup.py` L120–128) an owner row is `hc_branch_staff(branch_id = NULL, role =
clinic_owner)` and ADR-HC-001 §D3 grants it a `branch_id = 'ALL'` bypass "all branches within their
`tenant_id`." Under one shared tenant that bypass would span **every clinic on the SaaS** — a SaaS-wide
super-owner. **Fix:** the owner's "all branches" bypass is fenced to **their Company**:

- The `clinic_owner` `hc_branch_staff` row gains an explicit **Company anchor**. Because
  `hc_branch_staff` has no `company_id` column today, the owner row's Company is resolved via the
  Company the owner registered (the `companies` row created at onboarding). **Schema delta (D-schema):**
  add a nullable **`company_id`** to `hc_branch_staff` so the `branch_id = NULL` owner sentinel carries
  *which Company* it owns (a non-owner staff row leaves it NULL and is isolated by `branch_id` as
  before). See schema-hc-04 §S.2.
- The owner bypass becomes: `app.branch_id = 'ALL'` **AND** `app.company_id = <owner's Company>` — i.e.
  the owner sees all branches **of their Company**, never other Companies. The `'ALL'` branch escape
  hatch stays branch-level; the **Company GUC (D2) is the outer fence** the owner can never widen. There
  is **no** Company-level `'ALL'`.
- **Conformance note (amends ADR-HC-001 §D3/§D4):** the `clinic_owner` bypass row in ADR-HC-001 §D3 is
  amended from "all branches within their `tenant_id`" to "all branches **within their Company**." The
  §D4 owner RLS `branch_id = 'ALL'` bypass is retained but now **AND-ed with** the Company GUC for every
  Company-scoped table.

**(b) RBAC cross-Company gating.** Platform RBAC resolves User→Group→Role→Permission and is tenant-
aware; with one tenant, role grants must not leak across Companies. Staff/role visibility (branch and
staff enumeration, `hc_branch_staff` reads) is fenced by the session Company: a Company-A branch
manager cannot enumerate Company-B branches/staff. This is enforced by the same `app.company_id` GUC on
the staff-facing tables (`hc_branches`, `hc_branch_staff`, `hc_departments` reads gated by the branch's
Company). `X-Branch-ID` continues to select the active branch **within** the caller's Company; a branch
outside the caller's Company fails the existing `healthcare_branch_session` assignment check (the staff
member has no `hc_branch_staff` row there) **and** the Company GUC.

### D5 — Patient token gains a `company_id` claim (token-claims decision for Hand-off (b)/(d))

The patient JWT (ADR-HC-003 §D1 shape, retained by ADR-HC-009) today carries `patient_id`, `tenant_id`
(the active patient's tenant), `roles:["patient"]`, `sid`, and (v2) `acct`/`obo`. **Decision: add a
`company_id` claim = the active patient's Company.** Rationale:

- The portal must scope Company-facing reads without a DB round-trip; the SDK reader
  (`get_current_patient`) surfaces `company_id` on `PatientTokenData` and the patient DB session sets
  `app.company_id` from it (D2). Without the claim, every patient request would re-derive the Company.
- The household is single-Company (RULING 2), so the `company_id` claim is stable across a switch within
  the household; `switch`/`from-platform` re-mint carry the (same) Company. `tenant_id` remains the
  shared `SAAS` tenant (or the dedicated tenant); `company_id` is the clinic-isolation value.
- Claim shape otherwise **unchanged** — this is additive, backward-compatible (legacy tokens without
  `company_id` fall back to a DB lookup on the active patient's `company_id`, mirroring the `acct`
  fallback already in `routes_household.py`).

### D6 — Portal clinic resolution re-keys from tenant-code to Company/Branch slug (decision; implementation handed to the epic)

**Decision (Hand-off (d)):** the public clinic slug becomes a **Company slug** (`companies.code`, which
is unique per tenant and, under one shared tenant, unique across the SaaS), with an optional **Branch**
segment for a specific site. `tenants.code` **stops** being the clinic identifier.

- `routes_public.py` `_get_profile` (L252+, `WHERE UPPER(code) = UPPER(:slug)` on `tenants`),
  `clinic_search` (tenant-grouping → **Company-grouping**), `clinic_public_profile`,
  `clinic_branch_public`, and the public-slots endpoint re-key from tenant code to **Company/Branch
  slug**. `routes_household.py` `get_my_clinic` (`/me/clinic`, L99–114, `SELECT code,name FROM tenants`)
  re-resolves to the active patient's **Company** (`companies.code`, `companies.name`) and, where a site
  is implied, its **Branch**.
- The **logged-out landing** (the "only shows MedCare" complaint) becomes a **clinic directory /
  chooser** across Companies on the SaaS, plus per-Company (and per-Branch) deep-link public URLs — no
  single clinic hard-coded as "the" landing.
- **Anti-enumeration / RLS caveat:** the public directory is a deliberate, non-PHI listing of Companies
  that have opted into public visibility; it lists Company display data only (name, city, branches), no
  patient data. It is the **only** cross-Company read surface, and it is PHI-free by construction.

**This ADR does not build the endpoints** — the re-keying is handed to the portal implementation epic
(A3 flags a new `epic-20-saas-onboarding` + portal-resolution stories). This ADR fixes the decision
(Company/Branch slug, directory landing) so the epic implements against it.

### D7 — Reporting views (ADR-HC-008) re-scope tenant → Company/Branch (conformance)

The eight ADR-HC-008 views (schema-hc-02 §D) filter on `app.tenant_id` + `app.branch_id`. Under one
tenant a tenant-wide aggregate spans the whole SaaS. **Re-scope:**

- Views that aggregate the **patient registry** or cross a Company boundary must add the **`app.company_id`**
  filter (or join through the branch's Company). In practice most ADR-HC-008 views are **branch-scoped
  clinical aggregates** (`hcr_visits`, `hc_encounters`, `hcr_queue_tickets`, `hcs_appointments`,
  `hcb_invoices`, `hc_diagnoses`, dispensing, lab) — branch-scoping already fences them to one Company,
  so they need **no change** beyond the owner-session Company fence (D4). The owner exec-dashboard path
  (`app.branch_id = 'ALL'`) must now **also** set `app.company_id` = the owner's Company so an owner's
  "all branches" rollup is their **Company's** branches, not the SaaS. Documented in schema-hc-04 §R and
  as an ADR-HC-008 conformance note.

---

## Consequences

### Positive
- **RULING 1 enforced in one indexable, RLS-native column** (`company_id`) — the same mechanism class
  ADR-HC-001 already proves for `tenant_id`/`branch_id`; deny-cross-Company is a `WHERE`/`USING`
  predicate, not application logic that can be forgotten.
- **Privilege-escalation closed** — the owner sentinel is fenced to a Company; no SaaS-wide super-owner.
- **Tight blast radius** — only the non-branch-scoped patient registry (+ `hc_patient_relationships`,
  consents) re-keys; every branch-scoped clinical table is unchanged because Branch already implies
  Company.
- **Consistent cross-DB story** — `company_id` FK posture is identical to ADR-HC-005 A1 / ADR-HC-009 R4.

### Negative / Security & Ops
- **A new GUC (`app.company_id`) and RLS predicate to maintain** across every session dependency and
  Company-scoped table — three enforcement layers to keep in sync (ADR-HC-001's standing cost, now +1
  axis for the patient registry). Mitigation: integration tests that a cross-Company patient read
  returns 0 rows at the RLS layer, and that the owner sentinel cannot read another Company.
- **`app.company_id` must be set on every Company-scoped path** — a missed `SET LOCAL` fails **closed**
  (no rows), so the failure mode is a functional bug (empty result), not a leak. This is the intended
  safe direction.
- **Migration is gated on D1/D2 landing first** (backfill `company_id`, add RLS) before consolidation —
  see `migration-plan-saas-tenancy-01.md`. Running consolidation before scoping would pool all patients
  in one tenant with no Company isolation (the make-or-break risk).
- **Token grows one claim** (`company_id`) — negligible; additive and backward-compatible.

## Conformance notes (isolation-invariant changes stated explicitly)

- **ADR-HC-001** — the **patient registry isolation key changes from `tenant_id` to `company_id`**
  (D1/D2). §D3 `clinic_owner` bypass re-scoped from tenant to **Company** (D4a). §D4 branch-scoped RLS
  is **unchanged** for clinical tables; a **new `app.company_id` GUC** is added and the owner
  `branch_id='ALL'` bypass is AND-ed with the Company GUC. These are the amended invariants; ADR-HC-001
  should carry a pointer to this ADR.
- **ADR-HC-002** — no new PHI; `company_id` is not PHI. The Company re-scope tightens (never loosens)
  PHI isolation; SDK PHI readers + audit unchanged. `hc_patient_relationships` remains RLS-scoped.
- **ADR-HC-004** — new/changed error codes (`cross_company` 422, cross-Company deny) are structured,
  translatable codes (ID default / EN), consistent with ADR-HC-005 A1's fail-closed codes.
- **ADR-HC-005** — Amendment v2 (shared-tenant default; Branch/Company become primary isolation).
- **ADR-HC-008** — owner rollup sets `app.company_id`; view conformance in schema-hc-04 §R.
- **ADR-HC-009** — Amendment v3 (household within one Company; token `company_id` claim) — separate.

## Reference Map

| File | Relevance |
|---|---|
| `plan-mod-healthcare/architecture/review-saas-tenancy-01.md` | A3 review + Hand-off (a)–(f) this ADR resolves |
| `modules/healthcare/backend/models.py` | `HCPatient` (+`company_id`, D1); `HCBranchStaff` (+`company_id` owner anchor, D4a); `HCBranch.platform_company_id` (Company resolution) |
| `modules/healthcare/backend/routes_clinic_signup.py` | `clinic_owner` `branch_id=NULL` sentinel (L120–128) re-scoped to Company (D4a) |
| `modules/healthcare/backend/routes_public.py` | `_get_profile`/`clinic_search`/`clinic_branch_public` re-key to Company/Branch slug (D6) |
| `modules/healthcare/backend/routes_household.py` | `/me/clinic` re-resolves to Company (D6); household Company-fenced (D3) |
| `modules/healthcare/backend/routes_patient_auth.py` | `from-platform`/`_resolve_active_patient` Company-fenced; token `company_id` (D3/D5) |
| `backend/app/models/company.py` | `companies` (id, tenant_id, code, name) — FK target for `company_id`; `code` = public slug |
| `plan-mod-healthcare/architecture/adr-hc-001-branch-isolation-strategy.md` | Isolation invariant amended (patient registry → Company; owner bypass → Company) |
| `plan-mod-healthcare/architecture/schema-hc-04.md` | DDL deltas (this ADR): `hc_patients.company_id`, `hc_branch_staff.company_id`, Company RLS/GUC |
| `plan-mod-healthcare/architecture/migration-plan-saas-tenancy-01.md` | Ordered migration gated on D1/D2 |

---

## Amendment v1 (2026-07-07) — Execution deltas (Phases 3 + 4 applied)

Migration-plan-saas-tenancy-01 Phases 3 (tenant re-point) and 4 (Company cutover) were executed and
verified against the dev DB. Two decisions **extended the original D1/D2 scope** (both approved by the
product owner during execution) and are recorded here as accepted amendments.

### AM1-1 — Per-clinic catalog tables are Company-scoped (not just the patient registry)

**Problem.** D1/D2 scoped `company_id` to `hc_patients` (+ `hc_branch_staff` owner anchor) only. But
several **per-clinic reference/catalog tables** carry a `(tenant_id, <natural key>)` unique constraint.
Collapsing MedCare + HealthPoint onto the shared `SAAS` tenant makes those keys collide (both clinics
seed a `CBC` lab panel) and makes tenant-keyed *enumeration* of a catalog leak across clinics.

**Decision.** Company-scope the catalogs: add `company_id` and re-key the unique constraint
`tenant_id → company_id` on **`hcl_test_panels`, `hcb_service_items`, `hcp_drug_interactions`,
`hc_icd10_codes`, `hc_icd9cm_codes`, `hc_i18n_overrides`**. Child/transactional tables
(invoice_lines, results, order_lines) and per-patient tables (consents, insurance) are **not**
changed — they inherit the Company fence via their branch-scoped parent or their `patient_id`.
Catalog `company_id` is **VARCHAR(36), app-enforced (no FK)** — distinct from the patient/owner
`company_id` which is **uuid + FK** (R4 posture: real FK where cheap, app-enforced elsewhere).
DDL: `saas_phase3_repoint.sql` (catalog preamble) + Alembic `hcsaas01`.

### AM1-2 — hc data layer decoupled from the staff user's platform tenant

**Problem.** Phase 3 moves all `hc_*` rows to the `SAAS` tenant, but staff **platform users** stay on
their original per-clinic tenant (their RBAC groups are tenant-scoped; re-homing users is a
platform-org migration = epic-20). So `current_user.tenant_id` (≈90 hc call sites + the ORM
tenant-scope) no longer matches the tenant hc rows carry.

**Decision.** The healthcare module resolves its **own** single hc tenant — `SAAS` — independent of the
platform user, via `modules/healthcare/backend/sdk/hc_tenant.py::hc_shared_tenant_id()` (primed at
service startup). Every hc `current_user.tenant_id` use is replaced with it; `branch_scope` /
`hc_permissions` / `verify_branch_access` query `hc_branch_staff` against `SAAS` and set
`app.company_id`. **`routes_clinic_signup.py` is exempt** — it still mints a per-clinic tenant and is
handed to Phase 5 / epic-20 (stop-minting + attach-to-SAAS onboarding).

### AM1-3 — Dev enforcement caveat: appuser BYPASSRLS → explicit enumeration filter

`appuser` (the deployed dev DB role) is a superuser + **BYPASSRLS**, so `rls_hc_patients` does **not**
isolate app queries in dev. RLS correctness is proven under a non-bypass role
(`saas_phase4_rls_proof.sql`: MedCare 3/0-cross, HealthPoint 4/0-cross, unset 0). Registry
**enumeration** routes therefore carry an **explicit** Company filter as defence-in-depth (correct in
prod too): `routes_visits.list_patients` uses `branch_scope.resolve_caller_company_id()` +
`HCPatient.company_id == caller_company` (fail-closed). By-id/by-patient reads remain inherently scoped.

### Amendment-v1 decision log
- Catalog set = the six `(tenant_id,…)`-unique tables with cross-clinic collision/enumeration risk; the
  branch-qualified uniques (departments, rooms, providers, provider_departments, appointment_slots,
  branch_staff) do **not** collide (branches are Company-disjoint) and are unchanged.
- Full staff cutover chosen over user-migration to avoid cascading into SAAS-tenant RBAC/menu
  provisioning (epic-20). MedCare has no `hc_branch_staff`/owner yet — its staff side is untested.
- Migrations: SQL `saas_phase{0..4}*.sql`; Alembic `hcsaas01` (additive) + `hcsaas02` (cutover), merging
  heads `hc006`+`hcl002`. RLS proven via `saas_phase4_rls_proof.sql`.
