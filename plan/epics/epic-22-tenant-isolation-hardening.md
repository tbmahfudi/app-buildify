---
artifact_id: epic-22-tenant-isolation-hardening
type: epic
producer: A3 Product Owner
consumers: [B1 Software Architect, B2 Data Engineer, B3 UX Designer, C1 Tech Lead]
upstream: [vision-02-tenant-isolation-hardening, research-02-tenant-isolation-hardening]
downstream: []
status: approved
created: 2026-05-08
updated: 2026-06-18
shape: feature
sprint_target: epic-22 sprint 1
decisions:
  - First story (22.1.1) is the provisioning-prototype gate per research-02's caveat — sprint cannot scale beyond this until the gate passes
  - Two-track structure: shared-core hardening (Features 22.2 + 22.3) runs in parallel with module-DB-per-tenant work (Feature 22.4); both are required for the headline guarantee
  - Documentation + adversarial test plan (Feature 22.5) closes the sprint; not deferrable like T-21.1.6 was
  - 14 stories total — under A3's soft cap of 15
open_questions:
  - Story 22.4.6 (financial module migration from shared → per_tenant) may need its own ADR if it touches module-system contract — defer to B1
  - Whether to ship the `BaseModule.tenant_scoped` flag as a backwards-compat default (true) or require explicit declaration — B1 architecture call
---

# Epic 22 — Tenant Isolation Hardening

> **Hybrid design** per [`vision-02-tenant-isolation-hardening`](../vision/vision-02-tenant-isolation-hardening.md): two-layer logical isolation for the shared core DB (helper + ORM listener) + database-per-tenant for module data. Closes the highest residual platform risk identified in [`sec-review-21`](../architecture/sec-review-21.md). Sprint must start with a per-tenant-module-DB provisioning prototype (story 22.1.1) per [`research-02`](../research/research-02-tenant-isolation-hardening.md) §5 caveat.

---

## Feature 22.1 — Provisioning prototype gate `[OPEN]`

### Story 22.1.1 — Per-tenant module DB provisioning prototype `[OPEN]`

#### Backend
*As the platform engineering team, I want a working end-to-end provisioning prototype against the existing financial module on a clean tenant before broad rollout, so that the operational story (Alembic fan-out, connection-pool init, secrets distribution) is validated against the ≤ 60s budget from `vision-02` metric #5 before the rest of the sprint scales the work.*
- A new `scripts/provision-tenant-module-db.py` (or equivalent CLI) creates a database `{tenant_id}_{module_id}`, runs the module's Alembic migrations against it, registers the connection in a temporary `tenant_module_databases` table (or staging equivalent), and returns timing
- End-to-end provisioning under representative load measures ≤ 60s for `(tenant=X, module=financial)`
- If > 60s, the provisioning workflow MUST be reworked before any other story in Feature 22.4 starts (gate)
- Prototype is throwaway-acceptable — does NOT need to be production-ready code; the gate is "we know the shape works"
- Output: a short timing/findings note appended to the epic-22 sprint retrospective

#### Frontend
*No frontend story — internal infrastructure prototype only.*

---

## Feature 22.2 — Centralized scope helper for shared core DB `[OPEN]`

### Story 22.2.1 — Helper API at `app/core/scope.py` `[OPEN]`

#### Backend
*As a backend developer, I want a single helper API for tenant-scoped queries — `apply_tenant_scope(query, model, user)` and a FastAPI dependency `tenant_scope_dependency(user)` — so that I never write `Model.tenant_id == user.tenant_id` by hand again.*
- New module `backend/app/core/scope.py` exports both functions plus a `TenantScopeMissingError` exception class
- `apply_tenant_scope(query, model, user)` returns the query with the appropriate `tenant_id` filter applied (and any deeper org-context fields if the model has them, per `_get_org_context()` semantics from `DynamicEntityService`)
- Calling on a non-tenant-scoped model is a no-op
- Superuser short-circuit (no filter applied) when `user.is_superuser` — consistent with existing RBAC bypass
- `tenant_scope_dependency` returns the user object after validating that scope context is set on the SQLAlchemy session

#### Frontend
*No frontend story — backend helper only.*

---

### Story 22.2.2 — Migrate `*Service` classes to the helper `[OPEN]`

#### Backend
*As the platform engineering team, I want every existing service that filters by `tenant_id` migrated onto the centralized helper, so that ad-hoc literal filters disappear and the convention is enforced by code review (any new `Model.tenant_id ==` literal becomes a review rejection).*
- Inventory pass: list every service file with `tenant_id ==` or `_get_org_context()` literals
- Migrate each to `apply_tenant_scope(query, Model, user)`
- `DynamicEntityService._get_org_context()` becomes a thin wrapper that delegates to the helper (or is removed entirely once callers migrate)
- A `manage.sh check-tenant-scope` script greps for ad-hoc literal patterns and exits non-zero if any remain — used as a manual pre-merge gate until CI exists
- Closes `audit-04` 4.2.2 medium gap

#### Frontend
*No frontend story.*

---

### Story 22.2.3 — Named API for legitimate cross-tenant operations `[OPEN]`

#### Backend
*As a platform engineer writing admin tooling that legitimately needs to read across tenants (e.g. a global notification scan or a platform-wide audit query), I want an explicit named API in the helper — `with_admin_cross_tenant_scope()` context manager — so that every cross-tenant operation is intentional, code-reviewable, and audit-logged at every call.*
- `with_admin_cross_tenant_scope()` context manager temporarily marks the SQLAlchemy session as cross-tenant; queries inside the block bypass the listener
- Entry and exit are audit-logged with action `tenant.cross_scope.enter` / `.exit`, including the calling stack frame so the audit trail captures *which* code legitimately needed it
- Misuse (entering the context without `is_superuser` or without an `admin_reason: str` argument) raises `PermissionError`
- All existing legitimate cross-tenant reads (if any are found in 22.2.2 inventory) migrate to this API

#### Frontend
*No frontend story.*

---

## Feature 22.3 — SQLAlchemy session-event listener `[OPEN]`

### Story 22.3.1 — Listener implementation + fail-loud on missing scope `[OPEN]`

#### Backend
*As the platform engineering team, I want a SQLAlchemy session-event listener that auto-injects the `tenant_id` filter on tenant-scoped queries, so that a forgotten filter in service code becomes a loud crash instead of a silent cross-tenant leak.*
- Listener attaches to the `before_compile` (or equivalent) SQLAlchemy event for `Query.compile`
- For each query against a model registered as tenant-scoped: if the session has a scope context, inject `WHERE tenant_id = <scope>`; if not, raise `TenantScopeMissingError` (caught at the FastAPI level and returned as 500 + audit-log entry `tenant.scope_missing`)
- Models opt in to tenant-scoped status via a class-level marker (e.g. `__tenant_scoped__ = True` or registration in a registry)
- Bulk operations (`bulk_insert_mappings`, raw `text()`) are documented as NOT covered — the helper API is the only safe path for those (story 22.2.1)
- Cross-tenant context (story 22.2.3) is honored — listener skips injection when the session is in admin-cross-tenant mode

#### Frontend
*No frontend story.*

---

### Story 22.3.2 — Per-request scope-context binding `[OPEN]`

#### Backend
*As a FastAPI route handler, I want the tenant scope context auto-bound to my SQLAlchemy session for the duration of the request based on the JWT's `tenant_id` claim, so that I never set the scope manually.*
- New FastAPI dependency `tenant_scoped_session(user, db)` returns a session with scope context already set to `user.tenant_id`
- Existing `Depends(get_db)` patterns migrated to the new dependency where the route is tenant-scoped
- Public routes (login, forgot-password, public health checks) opt out via a different dependency that explicitly disables scope checking
- Session teardown clears the scope context

#### Frontend
*No frontend story.*

---

## Feature 22.4 — Database-per-tenant for module DBs `[OPEN]`

### Story 22.4.1 — `DATABASE_STRATEGY=per_tenant` + registry table `[OPEN]`

#### Backend
*As a platform operator, I want a third `DATABASE_STRATEGY` value `per_tenant` (extending ADR-001's `shared` and `separate`) plus a `tenant_module_databases` registry table, so that the platform can route per-(tenant, module) connections.*
- Alembic migration creates `tenant_module_databases (tenant_id, module_id, connection_url, status, created_at)`
- `DATABASE_STRATEGY=per_tenant` env var honored by the module-system loader
- New ADR (likely `adr-003-per-tenant-module-databases`) authored by B1 to extend ADR-001
- Existing `DATABASE_STRATEGY=separate` deprecated but not removed (one-release deprecation window)

#### Frontend
*No frontend story.*

---

### Story 22.4.2 — Provisioning workflow `[OPEN]`

#### Backend
*As a tenant administrator enabling a new module, I want the platform to auto-provision a fresh module DB for my tenant within seconds, so that I don't wait or interact with operations.*
- Tenant-onboarding flow: on tenant creation, no module DBs are provisioned yet (lazy-at-first-enable per `vision-02` §9 question — A3 picks lazy)
- First module-enable for a (tenant, module) pair: kick the provisioning script (production-grade version of story 22.1.1), persist `tenant_module_databases` row with `status='ready'`
- Provisioning failure: row inserted with `status='failed'` + error message; module remains disabled; alert raised (logger.error + audit-log)
- Re-enable retries provisioning if the row is in `status='failed'`

#### Frontend
*As a tenant administrator on the Modules page, I want to see provisioning status when I enable a module, so that I know whether the action succeeded or needs attention.*
- Route: `#/modules` (existing page per `audit-11` 11.x DONE)
- New status badge on each module card: `Provisioning…` (in-flight), `Ready`, `Failed (retry)` — via a `GET /modules/{id}/provisioning-status` endpoint
- "Failed" state shows an FlexAlert with the error and a "Retry provisioning" FlexButton(secondary)
- States: loading (initial fetch), polling (every 2s while in-flight), error (request itself failed)

---

### Story 22.4.3 — Module-routing middleware `[OPEN]`

#### Backend
*As any authenticated request that hits a module endpoint, I want the platform to automatically route my DB session to the right per-tenant module DB based on my JWT's `tenant_id`, so that module services don't manually pick connections.*
- New middleware `ModuleScopeMiddleware` reads JWT `tenant_id` + URL prefix `/api/v1/modules/{module_id}/...`, looks up the connection from `tenant_module_databases`, opens a session against it, attaches to the request scope
- Cache pool keyed by `(tenant_id, module_id)` with bounded size (default 50 active pools, LRU-evict idle)
- Connection-pool initialization on first request to a (tenant, module) pair; subsequent requests reuse
- Falls back to the shared module DB if `DATABASE_STRATEGY=shared` (backwards compat)

#### Frontend
*No frontend story — middleware is transparent.*

---

### Story 22.4.4 — Alembic fan-out for module migrations `[OPEN]`

#### Backend
*As a module developer shipping a migration, I want `alembic upgrade head` to run across all tenant-deployed instances of my module's DB with one command, so that release coordination is automatic.*
- New `scripts/migrate-module.py {module_id}` reads `tenant_module_databases` for the module, runs Alembic upgrade against each connection in parallel-with-bounded-concurrency (default concurrency = 4)
- Per-(tenant, module) migration status tracked in the registry row
- Partial failure: failed tenants logged + alerted; succeeded tenants retain new revision; the script returns a non-zero exit code with a summary
- Idempotent: re-running on a partial failure picks up where it left off

#### Frontend
*No frontend story — operator-only tool.*

---

### Story 22.4.5 — Tenant offboarding cleanup `[OPEN]`

#### Backend
*As a platform operator deactivating or deleting a tenant, I want all that tenant's module DBs cleaned up (or archived per retention policy) in one command, so that no orphan databases accumulate.*
- `manage.sh tenant deactivate <id>` calls a new `cleanup_tenant_module_dbs(tenant_id)` service
- Per platform retention policy (read from a new `TENANT_DELETION_POLICY=drop|archive` env var, default `archive`): drops the DB or renames + read-only-flags it
- `tenant_module_databases` rows updated to `status='archived'` or deleted
- Audit-log entry `tenant.module_dbs.cleanup` per (tenant, module) pair

#### Frontend
*No frontend story — operator command-line action.*

---

### Story 22.4.6 — Migrate financial module from `shared` to `per_tenant` `[OPEN]`

#### Backend
*As the platform vendor, I want the existing financial module migrated from `DATABASE_STRATEGY=shared` to `per_tenant` for new tenants, with grandfather treatment for existing tenants, so that the new isolation guarantee applies without disrupting current deployments.*
- New tenants enabling the financial module after this story merges go through the per-tenant provisioning workflow
- Existing tenants whose financial module is already in `shared` mode retain the `shared` deployment until an explicit per-tenant migration is run
- New `manage.sh module migrate-tenant <tenant_id> <module_id>` command: provisions the per-tenant DB, copies the tenant's data from the shared DB, validates row counts match, flips the registry row, deletes the original rows from the shared DB after a confirmation prompt
- Dry-run mode prints what would happen without writing
- Coordinates with B1 ADR (story 22.4.1) — may require ADR amendment if module-system contract changes are needed

#### Frontend
*No frontend story — operational migration tool.*

---

## Feature 22.5 — Documentation + adversarial test plan `[OPEN]`

### Story 22.5.1 — `docs/platform/TENANT_ISOLATION.md` `[OPEN]`

#### Backend
*As any developer, operator, or compliance officer evaluating App-Buildify, I want a single canonical document describing how tenant isolation is enforced, so that the answer to "how do you prevent cross-tenant data exposure?" lives in one well-known place.*
- Single page covers: the two-layer core defense (helper + ORM listener), the per-tenant module-DB model, the named cross-tenant API + when to use it, the documented direct-DB-access caveat for the shared core, the test scenarios from story 22.5.3, and a "how to add a new tenant-scoped table" runbook
- Linked from `docs/SUMMARY.md` Table of Contents
- Reviewed by D3 Security Engineer for compliance-narrative quality

#### Frontend
*No frontend story.*

---

### Story 22.5.2 — `BaseModule` SDK update for `tenant_scoped` flag `[OPEN]`

#### Backend
*As a module developer, I want my module manifest to declare whether the module is tenant-scoped (default `true`) and which of its tables are tenant-scoped, so that the platform handles per-tenant DB provisioning + ORM listener registration without per-module boilerplate.*
- `BaseModule` ABC gains a class attribute `tenant_scoped: bool = True` and a method `get_tenant_scoped_tables() -> List[str]`
- Module manifest gains optional `tenant_scoped` key (defaults to true)
- Modules with `tenant_scoped=false` (rare; e.g. system-wide telemetry modules) get the existing shared DB; the framework refuses to provision per-tenant DBs for them
- Backwards-compatible default — existing modules without the declaration assume `tenant_scoped=true`
- Update `docs/modules/MODULE_DEVELOPMENT.md` (or equivalent) with the new contract

#### Frontend
*No frontend story.*

---

### Story 22.5.3 — `test-plan-22.md` adversarial scenarios `[OPEN]`

#### Backend
*As D1 QA Engineer, I want a manual smoke runbook covering ~40 adversarial scenarios across the shared-core helper + listener + per-tenant module DBs, so that a single sprint-end pass verifies the headline isolation guarantee.*
- ~30 core-DB scenarios: forgotten filter, ORM bypass attempt, scope-context-unset (loud crash verified), admin-cross-tenant API correctness, helper edge cases (no-tenant-scoped model, superuser bypass), `_check_entity_permission` interaction with the helper, regression tests against `test-plan-21` flows
- ~10 module-DB scenarios: provisioning success path, provisioning failure recovery, tenant-A-cannot-reach-tenant-B-module-DB (different physical DBs), Alembic fan-out partial failure recovery, connection-pool exhaustion, offboarding cleanup
- Each scenario has steps + expected outcome (matches `test-plan-21` format)
- Output: `tests/test-plans/test-plan-22.md` + `tests/test-reports/test-report-22.md`
- ✦ Code Auditor review after sprint to retag stories per A3 retag mode

#### Frontend
*No frontend story — verification-only artifact.*

---

## Sprint-Level Definition of Done

This epic is `[DONE]` when:

- [ ] Story 22.1.1 prototype passed the ≤ 60s gate (or scope was renarrowed if not)
- [ ] All 14 stories meet their backend AC
- [ ] Story 22.4.2 frontend (provisioning status UI) renders + functional
- [ ] `test-plan-22` (story 22.5.3) executes with all ~40 scenarios passing (code-walk PASS minimum; live-run PASS recommended)
- [ ] No regression in any `test-plan-21` scenario
- [ ] `docs/platform/TENANT_ISOLATION.md` published and reviewed
- [ ] D3 Security Engineer publishes `sec-review-22.md` with verdict CLEAR TO SHIP (or worse with documented mitigations)
- [ ] E2 Technical Writer publishes `release-notes-epic-22.md`

---

## Hand-off

This epic is `status: review`. Once approved (human stakeholder per A3 spec):
- **B1 Software Architect** — author `arch-22.md` + `adr-003-per-tenant-module-databases.md` (extending ADR-001)
- **B2 Data Engineer** — `schema-22.md` covering the `tenant_module_databases` table + module-DB provisioning template
- **B3 UX Designer** — UILDC for story 22.4.2 (provisioning status badges + retry button on Modules page)
- **C1 Tech Lead** — `tasks-22.md` once B1/B2/B3 approved; first task MUST be 22.1.1 prototype gate
