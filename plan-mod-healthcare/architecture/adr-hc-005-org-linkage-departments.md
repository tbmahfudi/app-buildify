---
artifact_id: adr-hc-005
type: adr
module: healthcare
status: proposed
producer: B1 Backend Architect
upstream: [BACKLOG.md (v3), adr-hc-001, adr-hc-002, adr-hc-004, schema-hc-01, epic-08-organization-departments (v2)]
created: 2026-07-02
updated: 2026-07-06
---

# ADR-HC-005 — Platform-Org Linkage & Healthcare Departments

## Status

accepted (2026-07-06) — was `proposed`. Promoted after epic-08 v2's linkage-lifecycle
clarification pass; the finalized decisions on the four A3 hand-off items are recorded in the
**2026-07-06 addendum** at the end of this document (D1 addendum, D2 addendum, and the accept
decision on Story 8.2.4's optional FK).

## Context

BACKLOG v3 redesign decision #3 restructures the healthcare organization model:

> keep `hc_branches`, **add `hc_departments`**, and **link `hc_branches` to the platform
> Company/Branch/Department** (a clinic **is** a platform branch; everything under a Tenant; a
> dedicated tenant only on explicit request). Healthcare-side change only.

Today (`schema-hc-01`, `modules/healthcare/backend/models.py`) the healthcare suite carries its own
branch registry, `hc_branches`, keyed by `tenant_id`, with no structural relationship to the platform
org hierarchy (`Tenant → Company → Branch → Department`, see `backend/app/models/{tenant,company,
branch,department}.py`). The platform already ships a full org module (`backend/app/routers/org.py`)
with a Department entity (`departments` table: `id`, `tenant_id`, `company_id`, `branch_id`,
`parent_department_id`, `head_user_id`).

Three questions must be settled before epic-08 stories are implemented:

1. **Linkage** — how does an `hc_branches` row relate to a platform `branches`/`companies`/
   `departments` row, and who owns the linkage columns?
2. **Departments** — do we reuse the platform `departments` table for clinical departments
   (medical, pharmacy, laboratory, radiology, administration, finance) or add a healthcare-owned
   `hc_departments` table?
3. **Assignment** — how are providers (`hc_providers`) and staff (`hc_branch_staff`) assigned to a
   department, and how is that scoped?

**Constraints from upstream documents:**
- BACKLOG v3 Reuse Register: platform Org hierarchy is a **reuse** capability; healthcare adds a
  *link*, not a rebuild — "Healthcare-side change only."
- ADR-HC-001: every branch-scoped table carries `tenant_id` + `branch_id` and is enforced by the
  `BranchScopeListener` + DB RLS (`§D4`). The healthcare `branch_id` is the **`hc_branches.id`**,
  not the platform `branches.id`.
- ADR-006 (platform) + ADR-HC-001/-002: healthcare code must not mutate platform tables; the
  platform SDK surface is platform-owned.

## Decision

### D1 — Read-only FK linkage columns on `hc_branches` (healthcare owns them)

`hc_branches` gains three **nullable** linkage columns pointing at the platform org hierarchy:

| Column | Type | Nullable | FK target | Meaning |
|---|---|---|---|---|
| `platform_company_id` | VARCHAR(36) | NULL | `companies.id` | Owning platform Company (a clinic legal entity) |
| `platform_branch_id` | VARCHAR(36) | NULL | `branches.id` | The platform Branch this clinic **is** (1:1) |
| `platform_department_id` | VARCHAR(36) | NULL | `departments.id` | Optional platform Department this clinic rolls up to |

**Rationale — "a clinic IS a platform branch":** the canonical model is one `hc_branches` row ⇄ one
platform `branches` row within the same `tenant_id`. The linkage is expressed as FK columns **on the
healthcare side only**. The platform `branches`/`companies`/`departments` tables are **not modified**
(no reverse FK, no new columns) — coupling is one-directional and read-only from healthcare's
perspective. Healthcare never writes platform org rows through these columns; provisioning of the
platform Branch is done via the existing platform org API (`backend/app/routers/org.py`), and the
healthcare onboarding flow records the resulting id.

**Nullable, not NOT NULL:** columns are nullable so that (a) existing `hc_branches` rows migrate
without a backfill blocker, and (b) a clinic can be created healthcare-first and linked later. Once
linked, the invariant `hc_branches.tenant_id = branches.tenant_id` holds (validated at the
application layer during linkage, since a cross-DB CHECK is not expressible).

**"Everything under a Tenant; a dedicated tenant only on explicit request":** the default topology is
a single platform Tenant containing one Company whose Branches are the clinics. A per-clinic
*dedicated tenant* is provisioned only when a customer explicitly requests hard tenant isolation;
that is a platform-org provisioning choice and requires no healthcare schema change (the linkage
columns already carry whichever `tenant_id`/`company_id`/`branch_id` the platform assigns).

### D2 — New healthcare-owned `hc_departments` table (not the platform `departments` table)

Clinical departments are a **healthcare-owned** concept and live in a new `hc_departments` table,
branch-scoped per ADR-HC-001:

```
hc_departments (
  id, tenant_id, branch_id,
  code, name,
  kind ∈ {medical, pharmacy, laboratory, radiology, administration, finance},
  is_active, created_at, updated_at
)
```

`hc_departments.branch_id` is a healthcare `branch_id` (FK → `hc_branches.id`), so the table is
`__branch_scoped__` and inherits the `BranchScopeListener` + RLS treatment. A department belongs to
exactly one healthcare branch.

**Why a dedicated table rather than reusing platform `departments`:**

| Consideration | Verdict |
|---|---|
| `kind` taxonomy | Healthcare needs a fixed clinical taxonomy (`medical`/`pharmacy`/`laboratory`/`radiology`/`administration`/`finance`) that drives queue routing (ADR-HC-006), coding scope (ADR-HC-007), and dept-scoped reports (ADR-HC-008). The platform `departments` table has no such column and is a generic org-chart node. |
| Branch scoping model | `hc_departments` must be filtered by the healthcare `branch_id` (`hc_branches.id`) via `BranchScopeListener`. Platform `departments` are scoped by the platform `branch_id` (`branches.id`) — a different scoping axis. Overloading one table across two scoping regimes would break the ADR-HC-001 invariant. |
| Ownership / migrations | Reusing `departments` would put clinical semantics into a platform table (mutating a platform table), violating BACKLOG v3 "Healthcare-side change only" and ADR-006. |
| Lifecycle | Clinical departments are seeded and managed by the healthcare module; a platform org-chart Department is an HR/finance construct. Keeping them separate avoids coupling the two lifecycles. |

The platform `departments` table is still available for the customer's *org-chart* needs and can be
optionally referenced from `hc_branches.platform_department_id` (D1) for reporting roll-up, but it is
**not** the clinical department store.

### D3 — Provider/staff → department assignment via a join table `hc_provider_departments`

Providers and staff are assigned to one or more departments through a branch-scoped join table
`hc_provider_departments`:

```
hc_provider_departments (
  id, tenant_id, branch_id,
  provider_id  → hc_providers.id,
  department_id → hc_departments.id,
  is_primary,  # a provider's home department
  created_at
)
UNIQUE (tenant_id, branch_id, provider_id, department_id)
```

- Assignment is at the **provider** grain (`hc_providers`), which already carries `user_id`,
  `branch_id`, and `provider_type`. Staff who are not clinical providers (e.g. pure `billing_staff`)
  are represented as providers of the corresponding `provider_type` (consistent with `hc_providers`'
  existing `provider_type` CHECK), so a single join table covers doctor/nurse/pharmacist/lab_tech/
  billing_staff department membership.
- `department_id` and `provider_id` must belong to the **same** `(tenant_id, branch_id)` — enforced
  by the `BranchScopeListener` filter plus an application-layer check at assignment time.
- `is_primary` marks the provider's home department; at most one primary per provider per branch is
  enforced by a partial unique index (`WHERE is_primary`).
- Department routing for a visit (ADR-HC-006 `hcr_visits.department_id`) references
  `hc_departments.id`; the set of providers eligible for a department is resolved through this join.

### D4 — Isolation & RLS conformance

`hc_departments` and `hc_provider_departments` are branch-scoped and follow ADR-HC-001 `§D4`
verbatim:

```
tenant_id = current_setting('app.tenant_id')
AND (branch_id = current_setting('app.branch_id') OR current_setting('app.branch_id') = 'ALL')
```

The three linkage columns on `hc_branches` are **not PHI** and carry no branch filter (`hc_branches`
is the tenant-wide branch registry, ADR-HC-001 §D3 / schema-hc-01). They are covered by the existing
`hc_branches` tenant-scoped policy. No new PHI is introduced by this ADR.

## Consequences

### Positive
- **Reuse over rebuild:** the platform org module remains the source of truth for
  Tenant/Company/Branch; healthcare only records a link. Satisfies BACKLOG v3 Reuse Register.
- **No platform mutation:** all new columns/tables are healthcare-owned; platform tables untouched
  (ADR-006 / BACKLOG "Healthcare-side change only").
- **Clean scoping:** clinical departments inherit the proven ADR-HC-001 branch-isolation machinery
  without overloading a platform table across two scoping axes.
- **Routing-ready:** `kind` on `hc_departments` gives queue (ADR-HC-006), coding (ADR-HC-007), and
  reporting (ADR-HC-008) a stable dimension to route/aggregate on.

### Negative
- **Two "branch" ids coexist:** healthcare `branch_id` (`hc_branches.id`) and platform
  `platform_branch_id` (`branches.id`). Mitigation: the 1:1 link is documented here; healthcare code
  always scopes on `hc_branches.id`; `platform_branch_id` is used only for platform org roll-up and
  reporting joins.
- **Linkage integrity is app-enforced:** `hc_branches.tenant_id = branches.tenant_id` cannot be a DB
  CHECK across the FK. Mitigation: validated at linkage time and covered by an integration test.
- **Duplicated department concept** if a customer also builds a platform org-chart Department tree.
  Mitigation: `platform_department_id` provides an explicit roll-up pointer; the two are intentionally
  decoupled by lifecycle.

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Reuse platform `departments` for clinical departments | No `kind` taxonomy; wrong scoping axis (platform `branch_id`); would mutate/overload a platform table (violates ADR-006 + BACKLOG "Healthcare-side change only"). |
| Add reverse FK columns on platform `branches` pointing to `hc_branches` | Mutates a platform table; couples platform release cycle to healthcare. Rejected by BACKLOG "Healthcare-side change only." |
| Make linkage columns NOT NULL | Blocks migration of existing `hc_branches` rows and healthcare-first onboarding. Nullable + app-validated invariant is safer. |
| Assign providers to departments by a `department_id` column directly on `hc_providers` | A provider can belong to multiple departments (e.g. a doctor covering medical + administration); a single column cannot model many-to-many. Join table chosen. |

## Reference Map

| File | Relevance |
|------|-----------|
| `backend/app/models/{company,branch,department}.py` | Platform org tables (`companies`, `branches`, `departments`) — FK targets for D1 |
| `backend/app/routers/org.py` | Platform org provisioning API — creates the platform Branch a clinic links to |
| `modules/healthcare/backend/models.py` | `HCBranch`, `HCProvider`, `HCBranchStaff` extended by this ADR |
| `plan-mod-healthcare/architecture/adr-hc-001-branch-isolation-strategy.md` | Branch isolation invariant + RLS `§D4` inherited by `hc_departments` |
| `plan-mod-healthcare/architecture/schema-hc-02.md` | DDL for the linkage columns, `hc_departments`, `hc_provider_departments` |
| `plan-mod-healthcare/BACKLOG.md` | v3 decision #3, Reuse Register, Canonical names |

---

## Addendum (2026-07-06) — epic-08 v2 linkage-lifecycle resolutions

epic-08 v2 (A3) added a "Hierarchy correspondence" section and four linkage-lifecycle stories
(8.1.3 unlink, 8.1.4 1:1 + tenant-invariant enforcement, 8.1.5 onboarding topology, 8.2.4 optional
clinical-dept ⇄ platform-dept link). This addendum resolves the four "Architecture note for B1"
hand-off items and promotes the ADR to **accepted**. It **amends, not rewrites,** D1 and D2 above.

### A1 — Enforcement of the 1:1 clinic-site⇄branch rule and `tenant_id` equality (Story 8.1.4)

Finalizes the app-enforced invariant asserted in D1 ("validated at the application layer during
linkage") and specifies the cross-DB posture.

**Authoritative enforcement point — application layer, fail-closed.** On the 8.1.1 `PUT`
org-linkage, the healthcare linkage service is the authoritative validator. It calls the
**platform-org SDK/API** (`backend/app/routers/org.py` — `/api/v1/org/companies`, `/api/v1/org/branches`)
to confirm the referenced `companies` / `branches` (and, when supplied, `departments`) rows **exist**
and share the **caller's `tenant_id`**, in this order:

1. `platform_branch_id` resolves to an existing `branches` row → else **422 `platform_branch_not_found`**.
2. `branches.tenant_id == hc_branches.tenant_id` → else **422 `tenant_mismatch`**.
3. `platform_company_id`, when supplied, resolves and shares the tenant → else **422**.
4. `platform_department_id`, when supplied, resolves and belongs to the same tenant/company → else **422**.
5. `platform_branch_id` not already held by another `hc_branches` row → else **409
   `platform_branch_already_linked`** (1:1 rule).

**Fail modes (fail-closed — never silently link):**
- Invalid reference / tenant mismatch / duplicate → **422** (or **409** for the 1:1 duplicate);
  no linkage write is emitted; errors are structured, translatable codes (ADR-HC-004), not raw DB errors.
- Platform-org lookup **unavailable** (SDK/API down or times out) → **503 `platform_org_unavailable`**;
  the link is **not** written. The service never assumes validity when it cannot verify.

**Uniqueness owner (single-DB backstop):** the partial unique index
`uq_hc_branches_platform_branch` (schema-hc-02 §A.1) is the DB-level backstop that makes the 1:1 rule
race-safe **when healthcare and platform share a database** — the concurrent second link fails closed
at the DB even if two requests pass app validation simultaneously.

**Cross-DB story (consistent with ADR-HC-009 D5 / schema-hc-03 §M for `hc_patients.user_id`):**
- **Shared DB (current dev — both in `appdb`):** the FK constraints
  (`fk_hc_branches_platform_company/branch/department`) and the partial unique index
  `uq_hc_branches_platform_branch` are **real** and enforced by the DB. The `tenant_id` cross-table
  equality remains app-validated (a cross-FK CHECK is not expressible even in one DB).
- **Split DB (platform-org and healthcare in separate databases):** the cross-service FKs are
  **not** declarable; integrity is **fully app-enforced** via the synchronous platform-org SDK check
  above, and the healthcare-side partial unique index still guarantees 1:1 **within** the healthcare DB
  (one `hc_branches` row per `platform_branch_id` value). The `tenant_id` equality is app-enforced in
  both topologies. This is the same posture as ADR-HC-009 D5's `hc_patients.user_id` (real FK when
  shared, app-enforced when split) — the two are intentionally kept consistent.

Covered by an integration test that attempts a cross-tenant link (expects 422) and a duplicate link
(expects 409).

### A2 — Unlink policy (Story 8.1.3): always-allowed at MVP

**Decision: unlink is always allowed at MVP; the 409 dependency guard is dropped.** No MVP artifact
hard-depends on a *live* linkage. The reporting views (schema-hc-02 §D, ADR-HC-008) and their
`EntityDefinition` bindings aggregate on the **healthcare** `branch_id` (`hc_branches.id`), never on the
platform linkage columns; platform-org roll-up joins resolve `platform_*` at read time and simply
return no platform context when the columns are NULL (surfaced as `linkage_health`/"not linked",
Story 8.1.2). There is no pinned platform-org report/export that must retain a frozen linkage for a
period. Therefore:

- `DELETE /org-linkage` clears `platform_company_id` / `platform_branch_id` / `platform_department_id`
  back to NULL, deletes **no** `hc_branches` or platform row, emits `hc_branch.org_unlinked`
  change-audit (old linkage JSON), and always succeeds.
- Clearing `platform_branch_id` frees that platform branch for reuse (the partial unique index no
  longer sees the old value), so unlink + re-link (8.1.1 `PUT`) is the supported "re-point" flow.
- If a future epic introduces a hard dependency on a live linkage (e.g. a period-pinned platform-org
  export), re-introduce the 409 guard then; it is **out of scope for MVP** and epic-08 Story 8.1.3's
  conditional 409 branch is **dropped**.

Optional `platform_department_id` on `hc_departments` (see A3 below), when set, is likewise cleared by
the site-level unlink only insofar as it is a separate per-department link — a site unlink does **not**
cascade-clear per-department org links; those are managed via 8.2.4's own `org-link` endpoint. (A
department link pointing under a now-unlinked site simply loses its resolvable company context and is
surfaced as stale, mirroring the site `linkage_health = stale` treatment.)

### A3 — Accept the optional `hc_departments.platform_department_id` FK (Story 8.2.4) — D2 addendum

**Decision: ACCEPT A3's recommendation.** `hc_departments` gains an **optional, nullable**
`platform_department_id VARCHAR(36) NULL, FK → departments.id`, **default NULL, no unique constraint**.
This is a **D2 addendum**: it does **not** revise D2's core ruling that clinical `hc_departments` and
the platform org-chart `departments` table are **structurally separate** concepts with independent
lifecycles. The new column is a **reporting-alignment pointer only** — it lets a customer who maintains
a platform org-chart line up an individual clinical department with an org-chart node (for
head-of-department roll-up / reporting), **without** coupling the two lifecycles or making the clinical
`kind` taxonomy or branch-scoping depend on the platform tree.

**Rationale for accept:** low cost (one nullable column, no new table), unblocks org-chart reporting
roll-up, and does not couple lifecycles (default NULL; the clinical taxonomy is unaffected whether set
or not). Rejecting it would leave org-chart customers unable to align clinical departments with
org-chart nodes for no schema-simplicity gain worth the loss.

**Semantics / constraints:**
- **Nullable, default NULL, no uniqueness.** Unlike the 1:1 site⇄branch rule, **many** clinical
  departments MAY map to **one** platform Department (N:1) — no unique index is imposed.
- **Distinct from `hc_branches.platform_department_id` (D1):** the D1 column rolls up the *whole clinic
  site*; this column rolls up an *individual clinical department*. Both are healthcare-owned, nullable,
  read-only toward platform; platform `departments` rows are never modified.
- **Validation (app-enforced, fail-closed, same posture as A1):** the 8.2.4 `org-link` endpoint
  validates the referenced `departments` row exists and shares the site's `tenant_id` (and, if the site
  is linked, its `platform_company_id`) → **422** otherwise; **503** if the platform-org lookup is
  unavailable. Emits `hc_department.org_linked` / `hc_department.org_unlinked` change-audit.
- **Not PHI** (ADR-HC-002 — org/dept rows carry no PHI; the change-audit event carries the id diff only).
- **Cross-DB:** real FK when healthcare + platform share `appdb`; app-enforced when split (same posture
  as A1 and ADR-HC-009 D5).

Schema delta is in **schema-hc-02 §A.2** (the single change from this addendum). **ORM model:** add the
column to `HCDepartment` in `modules/healthcare/backend/models.py` immediately after the `kind` column
(currently line 131) — `platform_department_id = Column(String(36), ForeignKey("departments.id"),
nullable=True)`. epic-08 Story 8.2.4 stays **`[OPEN]`** (not superseded).

### A4 — Dedicated-tenant vs clinic-as-Company topology (Story 8.1.5) — D1 clarification

**Decision (explicit line for D1):** the choice between **(A) clinic-as-Company/Branch** (default — the
clinic is a platform Branch under an existing Company in the current Tenant) and **(B) dedicated Tenant**
(hard isolation, on explicit request) is a **platform-org provisioning choice that requires no
healthcare schema change**. This restates and pins D1's "everything under a Tenant; a dedicated tenant
only on explicit request":

- Healthcare creates **no** platform org rows directly beyond calling the existing platform org API;
  the dedicated-tenant path (B) is **platform-org-owned, out-of-band provisioning** — healthcare only
  **records the request** (`hc_branch.onboarding_topology_selected` audit) and the **resulting
  `platform_company_id` / `platform_branch_id`**, which are handed to the 8.1.1 linkage step.
- **No `hc_*` schema differs** between the two topologies: the same three `hc_branches.platform_*`
  columns carry whichever `tenant_id` / `company_id` / `branch_id` the platform assigns, regardless of
  whether the clinic sits under a shared or a dedicated tenant.

### Addendum consequences / conformance

- **ADR-HC-001:** the healthcare RLS `branch_id` remains `hc_branches.id`; all `platform_*` columns
  (site-level and the new department-level one) are used **only** for platform-org roll-up/reporting
  joins, **never** for RLS scoping. The two `branch_id` notions stay de-conflated.
- **ADR-HC-002:** org/dept rows are **not PHI**; every linkage/unlink and department org-link/unlink
  write emits a standard change-audit event with a non-PHI id diff. No new PHI is introduced.
- **ADR-HC-004:** all validation/fail-closed error codes (`tenant_mismatch`,
  `platform_branch_already_linked`, `platform_org_unavailable`, department out-of-tenant/company) are
  structured, translatable codes (ID default / EN), surfaced inline per the epic-08 frontend AC.
- **Cross-DB consistency:** A1 and A3's shared-DB-FK / split-DB-app-enforced posture is deliberately
  identical to ADR-HC-009 D5 (`hc_patients.user_id`) — one integrity story across both ADRs.

### Addendum decision log (supersedes the "pending B1" markers in epic-08 v2)

| Item | Story | Decision |
|---|---|---|
| Optional `hc_departments.platform_department_id` FK | 8.2.4 | **ACCEPT** — nullable, no unique, FK → `departments.id`, reporting-alignment only; D2 addendum; story stays `[OPEN]` |
| 1:1 + `tenant_id` equality enforcement | 8.1.4 | App-layer platform-org SDK check is authoritative; **fail-closed** 422/409; **503** when lookup unavailable; partial unique index is single-DB backstop |
| Unlink / re-point policy | 8.1.3 | **Always-allowed at MVP**; 409 dependency guard **dropped** (no live-linkage hard dependency exists) |
| Dedicated-tenant vs clinic-as-Company | 8.1.5 | Platform-org provisioning choice; **no HC schema change**; healthcare records request + resulting ids only |
| Cross-DB integrity | 8.1.4 / 8.2.4 | Real FK when shared `appdb`; app-enforced when split — consistent with ADR-HC-009 D5 |

---

## Amendment v2 (2026-07-06) — Shared-tenant SaaS default & Company-scoped patients

This amendment records the tenancy-model pivot ratified after A3's `review-saas-tenancy-01`. It
**amends, does not rewrite,** D1 and the A4 addendum: the four A4 decisions (dedicated-tenant is a
platform-org provisioning choice, no `hc_*` schema differs between shared and dedicated topologies)
**stand verbatim**. What changes is the **default topology** and, consequentially, **which entity is
the patient-store isolation boundary**. The core patient-scoping enforcement lives in the new
**ADR-HC-010** (this amendment points there rather than duplicating it — see Hand-off (f):
*amend, not supersede*).

### AM2-1 — The default is now a single shared SaaS Tenant (default flip)

D1 (A4) said "everything under a Tenant; a dedicated tenant only on explicit request" but left the
*default* as tenant-per-clinic. **The default now flips:** ALL clinics on the SaaS live in **ONE
shared platform Tenant** (`SAAS`). An owner registers as a **Company**; each clinic **site is a
Branch** under that Company (Company 1:N Branch) — this is exactly D1's "a clinic IS a platform Branch"
linkage, now the mainline rather than the exception. A **dedicated Tenant** is reserved for the rare
multi-company-consolidated-view owner (**A4 stands** — provisioning choice, approval-gated, no `hc_*`
schema differs).

- The onboarding flow **stops minting a Tenant per clinic** (`routes_clinic_signup.py` `clinic_register`
  today `INSERT INTO tenants` per clinic); new signup attaches to the shared `SAAS` tenant and creates a
  **Company** (+ first Branch). (Onboarding redesign is A3's new `epic-20-saas-onboarding`; this ADR
  only records the topology decision.)
- The three `hc_branches.platform_*` linkage columns (D1) are **unchanged** — they already carry
  whichever `tenant_id`/`company_id`/`branch_id` the platform assigns, shared or dedicated (A4).

### AM2-2 — Isolation-boundary shift: Branch/Company become primary isolation, not Tenant

Because `tenant_id` is now a single shared value for all clinics, **it no longer isolates a clinic**.
The isolation boundaries shift:

- **Company** becomes the **clinic-business isolation unit** that `tenant_id` used to be — specifically
  for the **patient registry** (RULING 1: patient records are Company-scoped, Branch-shared within a
  Company, Company-isolated between Companies; two unrelated Companies keep two records). The mechanism
  (an explicit `hc_patients.company_id` + a Company-keyed RLS GUC) is decided in **ADR-HC-010 D1/D2**.
- **Branch** becomes the **primary isolation axis for branch-scoped clinical data** — which was always
  the finer axis (ADR-HC-001 §D4), so those tables are largely unchanged; a Branch belongs to exactly
  one Company, so branch-scoping already fences clinical data to one Company.
- The **`clinic_owner` `branch_id = NULL` sentinel** is re-scoped from "owner of this tenant" to "owner
  of this **Company**" to prevent a SaaS-wide super-owner (privilege-escalation fix, **ADR-HC-010 D4**).

**Conformance:** ADR-HC-001's patient-registry isolation invariant (`tenant_id`) is superseded by the
Company key for `hc_patients` (see ADR-HC-010's conformance note); the branch-scoped RLS (§D4) is
retained. No `hc_*` schema differs between shared and dedicated tenants (A4 preserved) — the
`company_id` patient-scoping column exists in both topologies and simply sits under whichever tenant the
platform assigned.

### Amendment-v2 pointer

The **enforcement design** (patient `company_id` column vs derive, the `app.company_id` GUC, the RLS
rewrite, the owner-sentinel fix, reporting re-scope) is authored in **ADR-HC-010 —
Shared-Tenant SaaS: Company-Scoped Patients, Branch-Primary Isolation**, with DDL in **schema-hc-04**
and the consolidation sequence in **migration-plan-saas-tenancy-01**. This ADR-HC-005 remains the
authority on **platform-org linkage**; ADR-HC-010 is the authority on **patient/isolation scoping under
the shared tenant**.
