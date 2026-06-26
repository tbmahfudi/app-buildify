---
artifact_id: tasks-22
type: tasks
producer: C1 Tech Lead
consumers: [C2 Backend Developer, D1 QA Engineer, E1 DevOps Engineer, D3 Security Engineer]
upstream: [epic-22-tenant-isolation-hardening, arch-22, schema-22]
downstream: []
status: approved
created: 2026-06-26
updated: 2026-06-26
sprint:
  goal: Deliver two-layer tenant isolation — centralized scope helper + ORM listener on the shared core DB, plus per-tenant module DB provisioning and cleanup service that unblocks T-23.025
  length_days: 10
  capacity_assumption: 1 BE (C2) + 0.5 DevOps (E1) + 0.25 QA (D1) + 0.25 Security (D3)
decisions:
  - Story 22.1 scope.py is the absolute gate; T-22.001 through T-22.003 must be DONE before any other stories start
  - Listener 22.2 goes live LAST among shared-core stories per schema-22 section 10.2 rollout order to avoid HTTP 500 storms
  - Story 22.4.1 TenantModuleDatabase ORM model unblocks all Feature 22.4 provisioning and cleanup tasks; schedule early
  - TD-1 and TD-2 follow-up migrations are code-only Alembic files; safe to run at any point after 22.4.1 lands
  - Story 22.4.5 cleanup service is a sprint DoD requirement; T-23.025 stub in modules.py line 1883 remains no-op until this merges
  - D3 Security review of cleanup service gates T-22.019 merge before it lands
open_questions:
  - M-1 automated detection of new models missing __tenant_scoped__ flag deferred to sprint N+1
  - Financial module migration from shared to per_tenant may need ADR amendment; B1 to decide before sprint N+1
  - audit_log_fn=None valid in with_admin_cross_tenant_scope is tracked as L-2 but not sprint-blocking
---

# tasks-22 — Sprint Backlog for Tenant Isolation Hardening

> **Upstream**: [`epic-22-tenant-isolation-hardening`](../epics/epic-22-tenant-isolation-hardening.md), [`arch-22`](../architecture/arch-22.md), [`schema-22`](../architecture/schema-22.md).

---

## Sprint Goal

Ship two-layer tenant isolation: (1) a centralized `scope.py` helper + ORM session listener that turns a forgotten filter from a silent data leak into a loud HTTP 500; (2) per-tenant module DB provisioning and the `cleanup_tenant_module_dbs` cleanup service that resolves the no-op stub left by T-23.025. Every subsequent service author calls `apply_tenant_scope` instead of writing inline `tenant_id ==` literals; the `check-tenant-scope` CI gate enforces the convention forever after.

## Capacity Plan

| Role | Headcount | Hours over 10-day sprint |
|------|----------:|------------------------:|
| C2 Backend Developer | 1 | 80 |
| E1 DevOps Engineer | 0.5 | 40 |
| D1 QA Engineer | 0.25 | 20 |
| D3 Security Engineer | 0.25 | 20 |
| **Total** | — | **160** |

Task estimates sum to ~102 hours, leaving buffer for code review, integration runs, and D3 async review cycles.

---

## Task Table

Status legend: `OPEN` = not started | `IN-PROGRESS` = picked up | `BLOCKED` = waiting | `REVIEW` = PR open | `DONE` = merged.

---

### Item 22.1 — Scope Helper `scope.py` (Story 22.1) ⛔ GATE

> **All Feature 22.2, 22.3, 22.4, 22.5 tasks are BLOCKED until T-22.001 through T-22.003 are DONE.**

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-22.001 | Create `backend/app/core/scope.py` — implement `apply_tenant_scope(query, model, user)`: adds `WHERE tenant_id = user.tenant_id`; no-op on non-tenant-scoped models; superuser short-circuit when `user.is_superuser` | C2 | — | 3 | [epic-22 §22.2.1](../epics/epic-22-tenant-isolation-hardening.md) | DONE |
| T-22.002 | Add `apply_tenant_scope_by_id(query, model, tenant_id)` variant and `TenantScopeMissingError` exception class to `scope.py`; wire `TenantScopeMissingError` into `backend/app/core/exceptions.py` generic_exception_handler returning HTTP 500 sanitized body | C2 | T-22.001 | 2 | [epic-22 §22.2.1](../epics/epic-22-tenant-isolation-hardening.md) | DONE |
| T-22.003 | Add `with_admin_cross_tenant_scope(user, admin_reason, audit_log_fn)` context manager to `scope.py`: sets session `_tenant_scope='__superuser__'`; writes `tenant.cross_scope.enter` and `tenant.cross_scope.exit` audit-log entries including calling stack frame; raises `PermissionError` if not superuser; raises `ValueError` if `admin_reason` missing | C2 | T-22.002 | 3 | [epic-22 §22.2.3](../epics/epic-22-tenant-isolation-hardening.md) | DONE |

**Subtotal: 8 hrs**

---

### Item 22.2 — ORM Session Listener (Story 22.2)

> Install listener LAST in the rollout — after service migration (T-22.007) and route dependency rollout (T-22.009) — to avoid HTTP 500 storms per schema-22 §10.2.

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-22.004 | Create `backend/app/core/tenant_listener.py` — implement `TenantScopeListener` class with `_on_orm_execute()` hook: intercepts SELECT, UPDATE, DELETE on `__tenant_scoped__ = True` models; reads `session._tenant_scope`; raises `TenantScopeMissingError` if not set; skips when `_tenant_scope == '__superuser__'` | C2 | T-22.003 | 4 | [epic-22 §22.3.1](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |
| T-22.005 | Add `set_tenant_scope(session, tenant_id)` and `clear_tenant_scope(session)` to `tenant_listener.py`; implement `TenantScopeListener.install(engine)` class method attaching to the SQLAlchemy engine; call `TenantScopeListener.install(engine)` in FastAPI lifespan startup in `backend/app/main.py` — this task depends on T-22.009 being merged first | C2 | T-22.004, T-22.009 | 2 | [epic-22 §22.3.1](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |
| T-22.006 | Add `__tenant_scoped__ = True` class attribute to all 18 models listed in schema-22 §5.1: User, Company, Branch, Department, Group, ReportDefinition, ReportExecution, ReportSchedule, ReportCache, Dashboard, DashboardPage, DashboardWidget, DashboardShare, DashboardSnapshot, WidgetDataCache, BuilderPage, ModuleServiceAccessLog, ModuleActivation; confirm excluded models in schema-22 §5.2 are NOT marked | C2 | T-22.004 | 3 | [schema-22 §5.1](../architecture/schema-22.md) | DONE |

**Subtotal: 9 hrs**

---

### Item 22.3 — FastAPI Dependency + Service Migration (Stories 22.2.2 + 22.3.2)

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-22.007 | Inventory `backend/app/services/` — list every raw `tenant_id ==` literal and `_get_org_context()` call; migrate each to `apply_tenant_scope(query, Model, user)`; make `DynamicEntityService._get_org_context()` a thin wrapper delegating to `apply_tenant_scope`; add integration tests on existing entity CRUD flows as regression guard | C2 | T-22.001 | 8 | [epic-22 §22.2.2](../epics/epic-22-tenant-isolation-hardening.md) | DONE |
| T-22.008 | Inventory `backend/app/routers/` for raw `.tenant_id ==` literals; document all occurrences in `docs/backend/TENANT_SCOPE_MIGRATION.md`; migrate router-layer literals where feasible this sprint; flag remaining as follow-up for sprint N+1 (M-2 partial remediation) | C2 | T-22.007 | 4 | [epic-22 §22.2.2](../epics/epic-22-tenant-isolation-hardening.md) | DONE |
| T-22.009 | Add `tenant_scoped_session(user, db)` FastAPI dependency to `backend/app/core/dependencies.py`: calls `set_tenant_scope(db, user.tenant_id)` at entry; calls `clear_tenant_scope(db)` in `finally` block on teardown; migrate all tenant-data routes from `Depends(get_db)` to `Depends(tenant_scoped_session)`; public routes (login, health checks) keep `get_db` with no scope set | C2 | T-22.007 | 5 | [epic-22 §22.3.2](../epics/epic-22-tenant-isolation-hardening.md) | DONE |

**Subtotal: 17 hrs**

---

### Item 22.4 — Per-Tenant Module DB: Model + Tech Debt Migrations (Story 22.4.1 / TD-3, TD-1, TD-2)

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-22.010 | Create `backend/app/models/tenant_module_database.py` — implement `TenantModuleDatabase` SQLAlchemy ORM class per schema-22 §5.3 (TD-3 resolution): columns id, tenant_id, module_id, db_name, connection_secret_ref, status, error_message, created_at, updated_at; UniqueConstraint on (tenant_id, module_id); two indexes on tenant_id and module_id; do NOT add `__tenant_scoped__` (admin scripts need cross-tenant visibility) | C2 | T-22.003 | 2 | [schema-22 §5.3](../architecture/schema-22.md) | DONE |
| T-22.011 | Extend env/config parsing to accept `DATABASE_STRATEGY=per_tenant` alongside existing `shared` and `separate`; add `MODULE_DB_POOL_MAX` (default 50) and `TENANT_DELETION_POLICY` (default `archive`) env var parsing; document all three new vars in `docs/backend/ENV_VARS.md` | C2 | T-22.010 | 2 | [epic-22 §22.4.1](../epics/epic-22-tenant-isolation-hardening.md) | DONE |
| T-22.012 | Write follow-up Alembic migration `pg_tenant_module_db_constraints.py` (down-revision: `pg_tenant_module_databases`): add FK constraint `tenant_id -> tenants.id` and FK constraint `module_id -> modules.id` (TD-1); add CHECK constraint `status IN ('provisioning','ready','failed','archived')` (TD-2); implement both `upgrade()` and `downgrade()` | C2 | T-22.010 | 2 | [schema-22 §7.1 TD-1 TD-2](../architecture/schema-22.md) | DONE |

**Subtotal: 6 hrs**

---

### Item 22.5 — Per-Tenant Module DB: Provisioning (Stories 22.4.2 + 22.4.3 + 22.4.4)

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-22.013 | Implement provisioning prototype: `scripts/provision-tenant-module-db.py` — creates DB `{tenant_id}_{module_id}`, runs module Alembic migrations against it, inserts `tenant_module_databases` row (status `provisioning` to `ready` on success, `failed` on error with error_message); measure end-to-end time against 60 s gate for (tenant=X, module=financial); append timing note to sprint retro | C2 | T-22.010 | 5 | [epic-22 §22.1.1](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |
| T-22.014 | Wire provisioning into module enable flow: on `POST /modules/{id}/enable` for a new (tenant, module) pair kick `provision-tenant-module-db.py` async; poll or callback updates status in `tenant_module_databases`; on `status=failed` row re-enable retries provisioning; add `GET /modules/{id}/provisioning-status` endpoint returning `{status, error?}` | C2 | T-22.013 | 4 | [epic-22 §22.4.2 backend](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |
| T-22.015 | Provisioning status UI: add status badge to modules page in `frontend/assets/js/` — `Provisioning...` (in-flight), `Ready`, `Failed (retry)` states; poll `GET /modules/{id}/provisioning-status` every 2 s while in-flight; `Failed` state shows FlexAlert with error message and Retry provisioning FlexButton(secondary) | C2 | T-22.014 | 4 | [epic-22 §22.4.2 frontend](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |
| T-22.016 | Create `backend/app/core/module_scope_middleware.py` — implement `ModuleScopeMiddleware`: reads JWT `tenant_id` and URL prefix `/api/v1/modules/{module_id}/...`, looks up `tenant_module_databases` row, sets marker on request scope; LRU connection pool keyed by (tenant_id, module_id) bounded to `MODULE_DB_POOL_MAX` (default 50); return HTTP 501 when `DATABASE_STRATEGY=per_tenant` but full pool wiring not yet complete (L-1 guard per arch-22 §7.3) | C2 | T-22.014 | 5 | [epic-22 §22.4.3](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |
| T-22.017 | Implement `scripts/migrate-module.py {module_id}` — reads `tenant_module_databases` for all `status=ready` rows for the module; runs `alembic upgrade head` against each connection in parallel with bounded concurrency default 4; per-(tenant, module) success/failure logged; non-zero exit on partial failure; idempotent on re-run | C2 | T-22.014 | 4 | [epic-22 §22.4.4](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |

**Subtotal: 22 hrs**

---

### Item 22.6 — Cleanup Service (Story 22.4.5) ⚑ REQUIRED for T-23.025

> **D3 Security Engineer must review T-22.018 and approve (T-22.020) before T-22.019 merges.** The cleanup service is called by T-23.025 (`DELETE /api/v1/admin/modules/{module_id}` in `modules.py` line ~1883); that endpoint stub remains a no-op until this story lands.

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-22.018 | Implement `scripts/cleanup_tenant_module_dbs.py` — expose `cleanup_tenant_module_dbs(tenant_id)` callable: reads all `tenant_module_databases` rows for the tenant; if `TENANT_DELETION_POLICY=archive` rename DB and update rows to `status=archived`; if `TENANT_DELETION_POLICY=drop` DROP DATABASE and delete rows; emit `audit_log` entry `tenant.module_dbs.cleanup` per (tenant, module) pair before any destructive operation; implement `--dry-run` flag | C2 | T-22.010, T-22.011 | 5 | [epic-22 §22.4.5](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |
| T-22.019 | Wire cleanup service into T-23.025 stub: in `backend/app/routers/modules.py` line ~1883 replace no-op comment with call to `cleanup_tenant_module_dbs(tenant_id)` after confirming `not module.is_core`; add `manage.sh tenant deactivate <id>` subcommand calling the script; add `module migrate-tenant <tenant_id> <module_id>` subcommand placeholder per arch-22 §4.2 | C2 | T-22.018, T-22.020 | 3 | [arch-22 §3.6](../architecture/arch-22.md) | OPEN |
| T-22.020 | D3 Security review of cleanup service: verify `TENANT_DELETION_POLICY=drop` path requires superuser auth; verify audit entries written before any destructive operation; verify `--dry-run` writes no DB; sign off or raise blocking findings before T-22.019 merges | D3 | T-22.018 | 4 | [epic-22 §22.4.5 AC](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |

**Subtotal: 12 hrs**

---

### Item 22.7 — CI Gate (Story 22.5)

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-22.021 | Add `manage.sh check-tenant-scope` subcommand: greps `backend/app/services/` and `backend/app/routers/` for raw `.tenant_id ==` patterns; exits non-zero if any hits found outside lines annotated `# tenant-scope-ok`; outputs file:line for each violation | E1 | T-22.003 | 3 | [epic-22 §22.2.2](../epics/epic-22-tenant-isolation-hardening.md) | DONE |
| T-22.022 | Wire `check-tenant-scope` into CI pipeline: run as pre-merge gate step after lint; fail build on non-zero exit; document the `# tenant-scope-ok` annotation convention in `docs/backend/TENANT_SCOPE_MIGRATION.md` | E1 | T-22.021 | 2 | [epic-22 §22.2.2](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |

**Subtotal: 5 hrs**

---

### Item 22.8 — Adversarial Test Suite (Story 22.6)

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-22.023 | Write `tests/test-plans/test-plan-22.md` — shared-core scenarios (30 minimum): forgotten filter raises `TenantScopeMissingError` and HTTP 500; ORM bypass attempt; scope-context-unset listener raises loudly; `with_admin_cross_tenant_scope` correctness and audit entries written; helper edge cases (non-scoped model no-op, superuser bypass); `apply_tenant_scope` regression against existing CRUD paths from test-plan-21; `_check_entity_permission` interaction | D1 | T-22.005, T-22.009 | 6 | [epic-22 §22.5.3](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |
| T-22.024 | Extend `tests/test-plans/test-plan-22.md` — module-DB scenarios (10 minimum): provisioning success path; provisioning failure recovery (retry on re-enable); tenant-A cannot reach tenant-B module DB (separate physical DBs); Alembic fan-out partial failure recovery; connection-pool exhaustion LRU eviction at MODULE_DB_POOL_MAX; cleanup service archive path; cleanup service drop path; `check-tenant-scope` gate catches raw literal | D1 | T-22.017, T-22.019 | 5 | [epic-22 §22.5.3](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |
| T-22.025 | Execute `test-plan-22.md` — run all 40+ scenarios against sprint build; document results in `tests/test-reports/test-report-22.md`; all scenarios must reach code-walk PASS minimum; flag FAIL to C2 for hotfix before sprint close | D1 | T-22.023, T-22.024 | 4 | [epic-22 §22.5.3](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |

**Subtotal: 15 hrs**

---

### Item 22.9 — Documentation (Stories 22.5.1 + 22.5.2)

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-22.026 | Write `docs/platform/TENANT_ISOLATION.md` — covers: two-layer shared-core defense (helper + listener); per-tenant module-DB model; `with_admin_cross_tenant_scope` API and when to use it; documented bypass surfaces (raw `text()` SQL, `bulk_insert_mappings`); test scenarios summary; how-to-add-a-new-tenant-scoped-table runbook; link from `docs/SUMMARY.md` ToC | C2 | T-22.005, T-22.009 | 3 | [epic-22 §22.5.1](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |
| T-22.027 | Update `docs/modules/MODULE_DEVELOPMENT.md` with `BaseModule.tenant_scoped: bool = True` and `get_tenant_scoped_tables() -> List[str]` contract; add `tenant_scoped` optional manifest key; explain `tenant_scoped=False` behavior (retained on shared DB, no per-tenant provisioning); update `backend/app/core/module_system/base_module.py` with new attributes | C2 | T-22.016 | 2 | [epic-22 §22.5.2](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |
| T-22.028 | D3 Security Engineer review of `docs/platform/TENANT_ISOLATION.md`: verify compliance narrative quality; confirm bypass surfaces accurately documented; confirm audit event types match implementation; sign off with comment or raise blocking findings | D3 | T-22.026, T-22.025 | 3 | [epic-22 §22.5.1 AC](../epics/epic-22-tenant-isolation-hardening.md) | OPEN |

**Subtotal: 8 hrs**

---

## Dependency Graph (critical path)

```
T-22.001 (scope.py gate -- starts all work)
    |
    +-- T-22.002 -- T-22.003
                        |
            +-----------+------------------------------------+
            |                                                |
       T-22.004 -- T-22.006                            T-22.010 (ORM model TD-3)
       (listener)  (__tenant_scoped__)                       |
            |                                          T-22.011 (env vars)
       T-22.007 (service migration)                          |
            |                                          T-22.012 (TD-1+TD-2 migrations)
       T-22.008 (router inventory)                           |
            |                                          T-22.013 (provisioning prototype -- gate)
       T-22.009 (tenant_scoped_session dep)                  |
            |                                          T-22.014 (enable flow wiring)
       T-22.005 (install listener -- LAST)                   |
            |                                  +------------+------------+
       T-22.021 -- T-22.022 (CI gate)     T-22.015 (FE badge)    T-22.016 (middleware)
                                                |                       |
                                          T-22.017 (fan-out)      T-22.018 (cleanup svc)
                                                |                       |
                                          T-22.023             T-22.020 (D3 review -- gate)
                                                |                       |
                                          T-22.024             T-22.019 (T-23.025 wire)
                                                |
                                          T-22.025 (test-report)
    |
    +-- T-22.026 -- T-22.027
              |
         T-22.028 (D3 doc review)
```

**Critical path to unblocking T-23.025**: T-22.001 -- T-22.002 -- T-22.003 -- T-22.010 -- T-22.013 -- T-22.014 -- T-22.018 -- T-22.020 (D3 sign-off) -- T-22.019 merged

**Listener activation rollout order** (must be respected; violating order causes HTTP 500 storms):
1. T-22.001 through T-22.003 — scope.py helper live
2. T-22.007 — all services migrated to apply_tenant_scope
3. T-22.009 — tenant_scoped_session dependency deployed to all tenant-scoped routes
4. T-22.006 — `__tenant_scoped__ = True` added to all 18 models
5. T-22.005 — listener installed at FastAPI lifespan startup (listener goes live last)

---

## Sprint Summary

| Item | Stories | Tasks | Est. hrs | Owner(s) |
|---|---|---:|---:|---|
| 22.1 Scope Helper (GATE) | 22.1 | 3 | 8 | C2 |
| 22.2 ORM Listener | 22.2 | 3 | 9 | C2 |
| 22.3 FastAPI Dep + Service Migration | 22.2.2 / 22.3.2 | 3 | 17 | C2 |
| 22.4 Module DB: Model + Tech Debt | 22.4.1 / TD-1 / TD-2 / TD-3 | 3 | 6 | C2 |
| 22.5 Module DB: Provisioning | 22.4.2 / 22.4.3 / 22.4.4 | 5 | 22 | C2 |
| 22.6 Cleanup Service | 22.4.5 | 3 | 12 | C2, D3 |
| 22.7 CI Gate | 22.5 | 2 | 5 | E1 |
| 22.8 Adversarial Test Suite | 22.6 | 3 | 15 | D1 |
| 22.9 Documentation | 22.5.1 / 22.5.2 | 3 | 8 | C2, D3 |
| **TOTAL** | **9 story groups** | **28** | **102** | |

---

## Sprint DoD Checklist

- [ ] T-22.001 through T-22.003 DONE (scope.py gate passed)
- [ ] T-22.005 merged (listener live at FastAPI startup) — must be last in shared-core rollout
- [ ] All 18 models carry `__tenant_scoped__ = True` (T-22.006 verified)
- [ ] T-22.009 merged (tenant_scoped_session on all tenant routes)
- [ ] T-22.013 prototype 60 s gate passed — Feature 22.4 confirmed viable
- [ ] T-22.019 merged (T-23.025 no-op stub wired to real cleanup service)
- [ ] T-22.020 D3 sign-off on cleanup service before T-22.019 merges
- [ ] T-22.022 CI gate (check-tenant-scope) green in pipeline
- [ ] T-22.025 test-report-22.md published with all 40+ scenarios PASS
- [ ] T-22.028 D3 sign-off on TENANT_ISOLATION.md
- [ ] No regression in test-plan-21 scenarios

---

## Follow-up Backlog (out of sprint scope)

- M-1 automated model introspection for `__tenant_scoped__` — sprint N+1
- M-2 full router-layer `tenant_id ==` literal migration — sprint N+1 (gate catches new occurrences)
- L-1 ModuleScopeMiddleware full connection-pool wiring for `DATABASE_STRATEGY=per_tenant` production-safe operation — sprint N+1
- L-2 make `audit_log_fn` required in `with_admin_cross_tenant_scope` — before next caller is added
- Story 22.4.6 financial module migration from shared to per_tenant for new tenants — may need ADR amendment; B1 call
- `DATABASE_STRATEGY=separate` deprecation notice in release notes — E2 Technical Writer
- D3 sec-review-22-followup.md confirming M-1 and M-2 sprint N+1 approach — post-sprint
- E2 Technical Writer release-notes-epic-22.md — after D3 final sign-off
