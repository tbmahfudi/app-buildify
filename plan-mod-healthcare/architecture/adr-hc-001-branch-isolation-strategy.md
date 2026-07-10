---
artifact_id: adr-hc-001
type: adr
module: healthcare
status: Accepted
producer: B1 Software Architect
upstream: [vision-02, research-02, epic-01-base-healthcare, BACKLOG.md]
created: 2026-06-21
---

# ADR-HC-001 — Branch Isolation Strategy

## Status

Accepted — **amended for shared-tenant SaaS by ADR-HC-010 (2026-07-06).** Under the shared-tenant SaaS
model (ADR-HC-005 Amendment v2) the **patient-registry isolation key changes from `tenant_id` to
`company_id`** (a new `app.company_id` GUC; ADR-HC-010 D1/D2, schema-hc-04 §S/§R), and the
`clinic_owner` §D3 bypass is re-scoped from "all branches within their `tenant_id`" to **"all branches
within their Company"** (ADR-HC-010 D4). The branch-scoped clinical RLS (§D4) is **unchanged** — a
Branch belongs to exactly one Company, so branch-scoping already isolates by Company. See ADR-HC-010 for
the amended invariants.

## Context

The App-Buildify platform enforces multi-tenancy via explicit `tenant_id` filtering in every
service query (arch-00-platform §3.1). The `tenant_scoped_session` dependency
(`modules/sdk/dependencies.py`) injects a DB session that carries the caller's `tenant_id`.

The Healthcare Module Suite introduces a second mandatory scoping dimension: **`branch_id`**.
A clinic tenant can operate 1–20 branches (epic-01, Story 1.2.1). Every clinical record
(Patient, Encounter, Appointment, Prescription, Lab Order, Invoice) belongs to exactly one
branch. A user is assigned to one or more branches with a specific role at each
(`branch_staff` table: `user_id × branch_id × role`).

Three design questions must be settled before any data model or API story is implemented:

1. **Query-layer enforcement** — does the existing `TenantScopeListener` (or equivalent) handle
   `branch_id`, or is there a new `BranchScopeListener`, or is it manual per-query?
2. **Fail-safe** — should a query that omits `branch_id` return all branches for the tenant
   (wide-open) or return an error?
3. **Cross-branch access** — how do Clinic Owner, Branch Manager, and Doctor roles traverse
   branch boundaries?

**Constraints from upstream documents:**
- vision-02 Guardrail: "PHI never crosses tenant boundaries."
- vision-02 Risk: "Multi-location data isolation complexity underestimated." Mitigation: branch
  isolation ADR before any sprint.
- research-02 Pre-condition: "Branch Isolation ADR signed off by B1 before the first sprint."
- epic-01 Story 1.3.1: `GET patients/:id` returns 403 if caller's `branch_id` does not match
  (unless cross-branch role).
- The platform's `tenant_scoped_session` dependency is in `modules/sdk/dependencies.py` and
  re-exports `backend.app.core.dependencies.tenant_scoped_session`. It currently carries only
  `tenant_id`; it does NOT carry `branch_id`.

## Decision

### D1 — Dedicated `BranchScopeListener` at the ORM layer

A new SQLAlchemy `BranchScopeListener` is introduced inside `modules/healthcare/sdk/` (not in
`modules/sdk/`, which is platform-owned). It is analogous to the platform's
`TenantScopeListener` but operates at the branch level:

```
modules/healthcare/sdk/
  branch_scope.py          # BranchScopeListener + healthcare_branch_session dependency
  phi_audit.py             # PHI audit hook (see ADR-HC-002)
  __init__.py              # re-exports for sub-module authors
```

`BranchScopeListener` uses SQLAlchemy's `SessionEvents.do_orm_execute` hook. On every SELECT,
INSERT, UPDATE, it appends a `WHERE branch_id = :branch_id` filter to all models that carry a
`branch_id` column and are tagged with the `BranchScoped` mixin.

The healthcare `FastAPI` dependency for branch-aware routes is:

```python
# modules/healthcare/sdk/branch_scope.py
def healthcare_branch_session(
    branch_id: UUID = Header(..., alias="X-Branch-ID"),
    db: Session = Depends(tenant_scoped_session),   # from modules.sdk.dependencies
    current_user = Depends(get_current_user),
) -> Generator[Session, None, None]:
    # 1. Verify current_user has a branch_staff record for (branch_id, tenant_id)
    # 2. Attach branch_id to session info dict so BranchScopeListener can read it
    # 3. Yield; listener enforces filter on every ORM execute
    ...
```

All healthcare sub-module routes that access branch-scoped data MUST use
`healthcare_branch_session` instead of `tenant_scoped_session` directly.

The `BranchScopeListener` is registered once when the healthcare module mounts
(analogous to how the financial module registers its own listeners).

### D2 — Fail-safe: queries without `branch_id` raise 422

If the `X-Branch-ID` header is absent from a request to any branch-scoped endpoint, the
`healthcare_branch_session` dependency raises `HTTP 422 Unprocessable Entity` before the session
is yielded. The ORM listener is never reached.

**There is no "return all branches" fallback** for any endpoint that touches PHI. The only
exception is the Clinic Owner aggregate-reporting endpoint family (e.g. `GET
/api/v1/tenants/:tenant_id/reports/overview`), which explicitly does NOT go through
`healthcare_branch_session` — it uses a dedicated `clinic_owner_session` dependency that reads
the tenant scope only and returns aggregated, non-PHI metrics.

### D3 — Cross-branch access by role

| Role | Branch access | Mechanism |
|------|--------------|-----------|
| `clinic_owner` | All branches within their `tenant_id` | `branch_staff` row with `branch_id = NULL` (sentinel) OR `clinic_owner` flag on tenant membership. `BranchScopeListener` bypasses the branch filter for this flag. |
| `branch_manager` | Assigned branches only (1–N) | `branch_staff` rows with explicit `branch_id` per assignment. `healthcare_branch_session` validates the requested `X-Branch-ID` is in the user's assignment list. |
| `doctor` / `nurse` / `pharmacist` / `lab_tech` / `billing_staff` | Assigned branches only | Same as Branch Manager — `branch_staff` rows validate the header. |
| `patient` | Own records only, across any branch they have an appointment at | Patient portal uses a separate `patient_session` dependency (ADR-HC-003). PHI access is scoped to `patient_id = current_user.patient_id`; `branch_id` is not filtered out — patients can see records from all branches they visited. |

Cross-branch read for clinical continuity (a Doctor at Branch A seeing a patient's prior
encounter at Branch B) is **not permitted in v1**. Branch B encounter data is not exposed to
Branch A staff. This aligns with vision-02 Guardrail 1. Cross-branch continuity is deferred to
a future phase requiring explicit patient consent.

### D4 — Database-level enforcement (defence-in-depth)

Row-Level Security (RLS) policies on PHI tables in PostgreSQL enforce
`tenant_id = current_setting('app.tenant_id')` AND `branch_id = current_setting('app.branch_id')`
at the DB engine level. The `healthcare_branch_session` dependency sets both session variables
via `SET LOCAL app.tenant_id = :tid; SET LOCAL app.branch_id = :bid;` on session open.

This means even if a bug in application code bypasses the ORM listener, the DB will reject the
cross-branch read.

The `clinic_owner` bypass is implemented by setting `app.branch_id = 'ALL'` and a corresponding
RLS policy: `branch_id = current_setting('app.branch_id') OR current_setting('app.branch_id') = 'ALL'`.

## Consequences

### Positive
- **Defence-in-depth**: ORM listener + DB RLS + header validation gives three independent
  enforcement layers.
- **Fail-closed**: missing `branch_id` header is an immediate 422, not a silent data leak.
- **Healthcare SDK is self-contained**: the `modules/healthcare/sdk/` pattern mirrors
  `modules/sdk/` and keeps healthcare concerns out of the platform SDK surface.
- **Cross-branch continuity is explicitly deferred**, preventing a premature design that might
  compromise PHI isolation.

### Negative
- **Three enforcement layers to maintain**: ORM listener, DB RLS policies, and header
  validation must be kept in sync as schema evolves. Mitigation: integration tests covering
  all three layers are mandatory for every model that carries `branch_id`.
- **`clinic_owner` RLS sentinel** (`branch_id = 'ALL'`) is a special-case that must be
  documented and tested. Mitigation: a dedicated test suite for owner-level bypass scenarios.
- **No cross-branch continuity in v1** is a known UX gap for multi-branch chains. Mitigation:
  Clinic Owner aggregate reports provide non-PHI operational visibility; cross-branch PHI is
  deferred with a clear ADR note for the future phase.

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Extend `tenant_scoped_session` with optional `branch_id` | Platform SDK (`modules/sdk/`) is platform-owned; healthcare concerns must not pollute it (ADR-006). Optional branch_id creates a footgun — callers can forget it and get wide-open queries. |
| Manual `WHERE branch_id = ?` in every query | No fail-safe; developers will forget. A single missed filter leaks PHI across branches. |
| Schema-per-branch isolation | Excessive complexity; incompatible with platform's shared-schema Alembic strategy (arch-00-platform). |
| Return all-branches data when header absent | Violates vision-02 Guardrail 1 (PHI never crosses tenant boundaries by default). |

## Reference Map

| File | Relevance |
|------|-----------|
| `modules/sdk/dependencies.py` | Platform `tenant_scoped_session` — extended by `BranchScopeListener` |
| `modules/sdk/db.py` | `Base`, `GUID` — `BranchScoped` mixin will extend `Base` |
| `plan/architecture/adr-006-sdk-surface-db-and-dependencies.md` | SDK isolation contract |
| `plan/architecture/arch-platform.md` §3.1 | Platform layering and session model |
| `plan-mod-healthcare/epics/epic-01-base-healthcare.md` | Stories 1.2.1, 1.3.1, 1.5.1 — branch assignment and PHI isolation ACs |
| `plan-mod-healthcare/vision/vision-02.md` | Guardrail 1, Risk: Multi-location isolation |
