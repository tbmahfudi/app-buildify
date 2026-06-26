---
artifact_id: arch-22
type: arch
producer: B1 Software Architect
consumers: [B2 Data Engineer, C1 Tech Lead, C2 Backend Developer, D3 Security Engineer]
upstream: [epic-22-tenant-isolation-hardening, vision-02-tenant-isolation-hardening, research-02-tenant-isolation-hardening, sec-review-22]
downstream: [schema-22, tasks-22]
status: approved
created: 2026-06-26
updated: 2026-06-26
decisions:
  - Two-layer shared-core defense: centralized helper (scope.py) + ORM session listener (tenant_listener.py)
  - Per-tenant module databases keyed by (tenant_id, module_id) with secrets-manager reference, not raw DSN
  - DATABASE_STRATEGY=per_tenant added as third mode extending ADR-001
  - ModuleScopeMiddleware marker pattern for now; full connection-pool wiring deferred to story 22.4.3 follow-up
  - cleanup_tenant_module_dbs (story 22.4.5) called by manage.sh and stubbed in T-23.025 admin endpoint
  - BaseModule.tenant_scoped flag defaults true (backwards-compatible); explicit false needed to opt out
  - with_admin_cross_tenant_scope() is the ONLY legitimate cross-tenant read path
open_questions:
  - Should __tenant_scoped__ enforcement use TenantScopedBase inheritance rather than per-model opt-in? (M-1 from sec-review-22)
  - Full connection-pool wiring in ModuleScopeMiddleware needed before DATABASE_STRATEGY=per_tenant is production-safe (L-1)
  - Should audit_log_fn in with_admin_cross_tenant_scope be made required before next caller is added? (L-2)
---

# arch-22 -- System Design for Epic 22: Tenant Isolation Hardening

> **Upstream**: epic-22-tenant-isolation-hardening. Bound by arch-platform.md, adr-001-deployment-modes.md, and sec-review-22.md. One new ADR (adr-003-per-tenant-module-databases.md) is produced alongside this document.

---

## 1. Context

### 1.1 Gap statement

`arch-platform.md` section 5.1 documented the original multi-tenancy posture as:

> "Multi-tenancy is **soft**: rows carry a `tenant_id` UUID column, and services apply `tenant_id` filters explicitly on every query. There is no row-level security policy and no SQLAlchemy session-scoped mixin enforcing this."

`arch-platform.md` section 9 risk #1 flagged this directly:

> "Filtering relies on every service writing `query.filter(Model.tenant_id == self.tenant_id)`. A missed filter is a cross-tenant data leak."

`sec-review-21.md` confirmed this as the highest residual platform risk. Epic 22 closes it with two complementary layers:

1. **Shared-core DB hardening** (Features 22.2 + 22.3): centralized helper + ORM listener so a forgotten filter becomes a loud crash instead of a silent cross-tenant leak.
2. **Database-per-tenant for module data** (Feature 22.4): physical isolation for module rows. Even if the ORM layer were bypassed, module data for tenant A cannot be reached from a session authenticated as tenant B.

### 1.2 What sec-review-22 required

`sec-review-22.md` identified two HIGH findings that gated shipment:

- **H-1**: `TenantScopeListener` guarded SELECT only; ORM UPDATE and DELETE were unguarded. **Resolved**: `is_select` guard removed; listener now fires on all ORM DML (confirmed in current `tenant_listener.py`).
- **H-2**: `connection_url` stored as plaintext in `tenant_module_databases`. **Resolved**: column renamed to `connection_secret_ref`; stores a secrets-manager reference (Vault path, env var name, or AWS ARN), never a raw DSN (confirmed in `pg_tenant_module_databases.py` migration).

Remaining tracked items from sec-review-22:

- **M-1** (medium): opt-in `__tenant_scoped__ = True` with no automated detection of models that miss the flag. Address in sprint N+1.
- **M-2** (medium): router layer has 20+ raw `.tenant_id ==` literals not covered by `check-tenant-scope` gate. Gate extended to cover `routers/` as part of this epic; full migration sprint N+1.
- **L-1** (low): `ModuleScopeMiddleware` sets a marker only when `DATABASE_STRATEGY=per_tenant`. Default stays `shared`; document prominently.
- **L-2** (low): `audit_log_fn=None` is a valid call to `with_admin_cross_tenant_scope`. Tighten before next caller is added.

### 1.3 Why this epic does not use PostgreSQL RLS

PostgreSQL Row-Level Security was evaluated (vision-02, research-02). Decision: application-layer defense first. Rationale:

- JWT `tenant_id` is authoritative at the application tier; no need to duplicate identity management at the DB layer.
- RLS requires session-level `SET app.tenant_id` injection for every pooled connection, coupling the connection pool to the auth layer.
- RLS does not protect raw `text()` SQL any more than the ORM listener does; both have the same bypass surface.
- The two-layer ORM approach achieves defense-in-depth without changing the PostgreSQL deployment model.

See `adr-003-per-tenant-module-databases.md` for the module-DB layer decision.

---

## 2. Goals and Non-Goals

### Goals

1. Every ORM query against a `__tenant_scoped__` model raises loudly if no tenant context is set -- no silent cross-tenant reads or writes.
2. A single canonical API (`apply_tenant_scope`, `tenant_scoped_session`) replaces all ad-hoc inline `tenant_id` filters in services.
3. Cross-tenant admin operations are only possible through a named, audit-logged context manager.
4. Module data for each tenant lives in a physically separate database, provisioned automatically on first module enable.
5. Alembic fan-out delivers module migrations to all tenant instances in one command.
6. Tenant deactivation cleans up or archives all per-tenant module databases in one command.

### Non-Goals

1. PostgreSQL Row-Level Security.
2. Celery worker tenant-scope binding (follow-up story 22.3.3, noted in sec-review-22 out-of-scope).
3. Frontend changes beyond the provisioning status UI (story 22.4.2).
4. Core-platform schema-per-tenant.
5. Raw-SQL `text()` interception by the ORM listener (documented limitation; helper API is the only safe path for raw SQL).

---

## 3. Architecture Decisions

### 3.1 Data-layer isolation: application-level tenant filters via centralized helper

**Decision**: `backend/app/core/scope.py` is the single source of truth for tenant filtering. All services call `apply_tenant_scope(query, Model, user)` instead of writing inline `query.filter(Model.tenant_id == user.tenant_id)`. No PostgreSQL RLS.

Rationale: application-layer is authoritative (JWT carries `tenant_id`); RLS would couple pooled connections to session variables; the helper is independently testable and code-reviewable.

**Enforcement gate**: `manage.sh check-tenant-scope` greps `backend/app/services/` and `backend/app/routers/` for raw `.tenant_id ==` literals and exits non-zero if any remain outside approved annotations.

### 3.2 ORM-level listener as fail-loud safety net

**Decision**: `TenantScopeListener` (story 22.3.1) is installed at engine startup and intercepts all ORM SELECT, UPDATE, and DELETE on `__tenant_scoped__` models. Missing scope raises `TenantScopeMissingError`, which the existing `generic_exception_handler` returns as HTTP 500 (sanitized) and logs at ERROR level. This is defense-in-depth, not a replacement for the helper.

**Superuser bypass**: session carries `_tenant_scope = '__superuser__'`; listener skips filtering.

**Cross-tenant admin bypass**: `with_admin_cross_tenant_scope()` sets the superuser marker for the duration of the context manager block.

### 3.3 API-layer: per-request scope binding via FastAPI dependency

**Decision**: `tenant_scoped_session(user, db)` FastAPI dependency (story 22.3.2, implemented in `backend/app/core/dependencies.py`) binds `user.tenant_id` to the SQLAlchemy session at request start and clears it in a `finally` block on teardown. Routes that serve tenant data migrate from `Depends(get_db)` to `Depends(tenant_scoped_session)`. Public routes (login, health checks) keep `get_db` with no scope set.

### 3.4 Cross-tenant leak prevention: named API plus mandatory audit trail

**Decision**: `with_admin_cross_tenant_scope(user, admin_reason, audit_log_fn)` in `scope.py` is the ONLY sanctioned path for legitimate cross-tenant reads. Every call is audit-logged with `tenant.cross_scope.enter` and `tenant.cross_scope.exit` including the calling stack frame. Misuse without `is_superuser` raises `PermissionError`; missing `admin_reason` raises `ValueError`.

**Future hardening (L-2, tracked)**: make `audit_log_fn` a required parameter before the next caller is added.

### 3.5 Module-DB strategy: DATABASE_STRATEGY=per_tenant

**Decision**: extend ADR-001 `DATABASE_STRATEGY` with a third value `per_tenant`. When set, each `(tenant_id, module_id)` pair gets its own PostgreSQL database. Routing is handled by `ModuleScopeMiddleware`. Credentials are stored as a secrets-manager reference in `tenant_module_databases.connection_secret_ref`, never as a raw DSN (H-2 fix). See `adr-003-per-tenant-module-databases.md`.

**Backwards compatibility**: `DATABASE_STRATEGY=shared` (default) is unchanged. Existing tenants on the financial module retain `shared` until an explicit per-tenant migration is run (story 22.4.6). `DATABASE_STRATEGY=separate` (ADR-001) is deprecated with a one-release window.

### 3.6 Cleanup service (story 22.4.5) -- relationship to T-23.025

`scripts/cleanup_tenant_module_dbs.py` implements `cleanup_tenant_module_dbs(tenant_id)`, called by `manage.sh tenant deactivate <id>`. It archives or drops all `tenant_module_databases` rows for the tenant per `TENANT_DELETION_POLICY` and emits an audit-log entry per `(tenant, module)` pair.

The admin endpoint at `backend/app/routers/modules.py` line 1883 (`DELETE /api/v1/modules/admin/{module_id}`, tagged `T-23.025`) currently logs a no-op stub because story 22.4.5 had not merged when that endpoint was scaffolded. Once 22.4.5 merges, the endpoint calls `cleanup_tenant_module_dbs` after confirming the module is not `is_core`. This wiring is the primary backend deliverable of story 22.4.5.

### 3.7 BaseModule.tenant_scoped flag (story 22.5.2)

**Decision**: `BaseModule` ABC gains `tenant_scoped: bool = True` and `get_tenant_scoped_tables() -> List[str]`. Default is `True` (backwards-compatible; existing modules without the declaration are treated as tenant-scoped). Modules with `tenant_scoped=False` continue on the shared DB; the framework refuses to provision per-tenant databases for them.

Epic-22 open question answered: default is `True`. Existing modules must explicitly opt out.

---

## 4. Component Design

### 4.1 New components

| Component | Path | Story | Description |
|-----------|------|-------|-------------|
| Scope helper | `backend/app/core/scope.py` | 22.2.1 | `apply_tenant_scope`, `apply_tenant_scope_by_id`, `tenant_scope_dependency`, `with_admin_cross_tenant_scope`, `TenantScopeMissingError` |
| ORM listener | `backend/app/core/tenant_listener.py` | 22.3.1 | `TenantScopeListener.install(engine)`, `set_tenant_scope`, `clear_tenant_scope`; installed at FastAPI lifespan startup |
| Module scope middleware | `backend/app/core/module_scope_middleware.py` | 22.4.3 | `ModuleScopeMiddleware`; routes module requests to per-tenant DB when `DATABASE_STRATEGY=per_tenant` (marker phase; full wiring is follow-up) |
| Provisioning script | `scripts/provision-tenant-module-db.py` | 22.1.1 / 22.4.2 | Creates DB, runs module Alembic migrations, writes `tenant_module_databases` row |
| Migration fan-out | `scripts/migrate-module.py` | 22.4.4 | Reads registry, runs `alembic upgrade head` on all tenant DBs for a module (bounded concurrency = 4) |
| Cleanup service | `scripts/cleanup_tenant_module_dbs.py` | 22.4.5 | Archives or drops all module DBs for a deactivating tenant; called by `manage.sh tenant deactivate` and wired into T-23.025 stub |
| Tenant isolation doc | `docs/platform/TENANT_ISOLATION.md` | 22.5.1 | Canonical isolation guarantee document; D3 review required |

### 4.2 Modified components

| Component | Path | Change |
|-----------|------|--------|
| FastAPI dependencies | `backend/app/core/dependencies.py` | `tenant_scoped_session` dependency (story 22.3.2); `clear_tenant_scope` in `finally` block |
| BaseModule ABC | `backend/app/core/module_system/base_module.py` | Add `tenant_scoped: bool = True` and `get_tenant_scoped_tables()` (story 22.5.2) |
| Module manifest | `modules/*/manifest.json` | Add optional `tenant_scoped` boolean key (default true if absent) |
| Service layer | `backend/app/services/*.py` | Migrate `DynamicEntityService._get_org_context()` and all ad-hoc `tenant_id` filters to `apply_tenant_scope` (story 22.2.2 inventory pass) |
| Admin modules router | `backend/app/routers/modules.py` line 1883 | Wire `cleanup_tenant_module_dbs` into the `DELETE /api/v1/modules/admin/{module_id}` handler (story 22.4.5; resolves T-23.025 no-op stub) |
| manage.sh | `manage.sh` | Add `tenant deactivate <id>`, `check-tenant-scope`, `module migrate-tenant <tenant_id> <module_id>` subcommands |
| Modules page (FE) | `frontend/assets/js/` (modules page) | Provisioning status badge + retry button per story 22.4.2 |

### 4.3 Unchanged but referenced

- `backend/app/core/audit.py`: receives new audit action strings (`tenant.cross_scope.enter`, `tenant.cross_scope.exit`, `tenant.scope_missing`, `tenant.module_dbs.cleanup`). No schema change to `audit_log` table.
- `backend/app/core/db.py`: `SessionLocal` and engine unchanged; `TenantScopeListener.install(engine)` called at startup using the existing engine.
- `backend/app/core/exceptions.py`: `TenantScopeMissingError` caught by `generic_exception_handler`; returns HTTP 500 with sanitized body (sec-review-22 I-1 verified).

---

## 5. Data Flow

### 5.1 Tenant-scoped request (steady state)

```
Client -- Bearer JWT --> FastAPI router
                             |
                      Depends(tenant_scoped_session)
                             |
                      set_tenant_scope(db, user.tenant_id)
                             |
                      Service: apply_tenant_scope(query, Model, user)
                             |  <- helper adds WHERE tenant_id = ?
                             |
                      ORM compiles query
                             |  <- TenantScopeListener verifies scope set
                             |
                      PostgreSQL executes filtered query
                             |
                      Response --> Client
                             |
                      finally: clear_tenant_scope(db)
```

### 5.2 Missing-scope path (fail-loud)

```
Background task creates plain SessionLocal() with no scope set
    |
    ORM query on __tenant_scoped__ model
    |
    TenantScopeListener._on_orm_execute()
        scope = getattr(session, '_tenant_scope', None)  -> None
    |
    raise TenantScopeMissingError
    |
    generic_exception_handler -> HTTP 500 (sanitized)
                              -> audit_log: tenant.scope_missing
```

### 5.3 Module provisioning flow

```
Tenant admin: POST /modules/{id}/enable
    |
    ModuleService kicks provision-tenant-module-db.py (async)
    |
    Script:
        CREATE DATABASE {tenant_id}_{module_id}
        Run module Alembic migrations against new DB
        INSERT tenant_module_databases (status='provisioning')
        UPDATE tenant_module_databases SET status='ready',
               connection_secret_ref=<vault-ref>
    |
    Frontend polls GET /modules/{id}/provisioning-status every 2 s
        provisioning -> badge "Provisioning..."
        ready        -> badge "Ready"
        failed       -> FlexAlert + "Retry provisioning" button
```

### 5.4 Cross-tenant admin read

```
Admin tool:
    with with_admin_cross_tenant_scope(user, reason, audit_log_fn):
        audit_log_fn(action='tenant.cross_scope.enter', ...)
        set_tenant_scope(db, '__superuser__')
        query executes across all tenants
    finally:
        audit_log_fn(action='tenant.cross_scope.exit', ...)
        clear_tenant_scope(db)
```

### 5.5 Tenant offboarding cleanup

```
manage.sh tenant deactivate <tenant_id>
    |
    scripts/cleanup_tenant_module_dbs.py <tenant_id>
    |
    TENANT_DELETION_POLICY=archive (default):
        UPDATE tenant_module_databases SET status='archived'
    |
    TENANT_DELETION_POLICY=drop:
        DROP DATABASE for each (tenant, module) DB
        DELETE FROM tenant_module_databases WHERE tenant_id=?
    |
    audit_log: tenant.module_dbs.cleanup per (tenant, module)
    |
    [T-23.025 wired post-merge]:
        DELETE /api/v1/modules/admin/{module_id}
        calls cleanup_tenant_module_dbs after confirming not is_core
```

---

## 6. Integration Points

| Integration | Direction | Notes |
|-------------|-----------|-------|
| Secrets manager (Vault / AWS SM / env var) | Outbound from provisioning script | `connection_secret_ref` format: `vault:<path>`, `env:<VAR_NAME>`, `arn:aws:secretsmanager:...`; resolved at connection-pool init in `ModuleScopeMiddleware` |
| Per-tenant module PostgreSQL databases | Outbound from `ModuleScopeMiddleware` | Active only when `DATABASE_STRATEGY=per_tenant`; default `shared` adds no new external dependency |
| `manage.sh` CLI | Operator-facing | New subcommands: `tenant deactivate`, `check-tenant-scope`, `module migrate-tenant` |
| Admin REST endpoint `DELETE /api/v1/modules/admin/{module_id}` | Internal (T-23.025) | No-op stub today; wired to cleanup service on 22.4.5 merge |
| Frontend provisioning status | `GET /modules/{id}/provisioning-status` | New endpoint; response: `{status: provisioning|ready|failed, error?: str}` |

New environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_STRATEGY` | `shared` | Gains third value `per_tenant` (in addition to `shared`/`separate`) |
| `TENANT_DELETION_POLICY` | `archive` | `archive` marks rows archived; `drop` destroys physical databases |
| `MODULE_DB_POOL_MAX` | `50` | LRU bound for `(tenant_id, module_id)` connection pools in `ModuleScopeMiddleware` |

---

## 7. Security Considerations

Informed by `sec-review-22.md` (verdict: CLEAR TO SHIP -- both HIGH findings resolved before re-review 2026-06-20).

### 7.1 Defense layers

| Layer | Mechanism | Documented bypass surface |
|-------|-----------|--------------------------|
| Helper (`scope.py`) | `apply_tenant_scope` adds `WHERE tenant_id = ?` explicitly | Raw `text()` SQL; missed call site |
| ORM listener (`tenant_listener.py`) | Auto-injects scope; raises on missing scope for SELECT/UPDATE/DELETE | Raw `text()` SQL; `bulk_insert_mappings` |
| Per-request dependency (`dependencies.py`) | Binds scope at request start; clears in `finally` | Background tasks that bypass the dependency |
| Per-tenant module DB | Physical DB separation for module data | None (separate credentials per tenant per module) |

### 7.2 Credential handling

`tenant_module_databases.connection_secret_ref` stores a reference, not a credential. The middleware resolves the secret at connection-pool initialization time from the named provider. Operators must configure a secrets backend before enabling `DATABASE_STRATEGY=per_tenant`. This is the H-2 resolution from sec-review-22.

### 7.3 Residual risks (all tracked, none blocking ship)

| ID | Risk | Status | Mitigation |
|----|------|--------|-----------|
| M-1 | New model without `__tenant_scoped__ = True` gets no listener protection | Sprint N+1 | Automate model introspection in `check-tenant-scope` |
| M-2 | Router-layer raw `.tenant_id ==` literals not fully migrated | Sprint N+1 | Gate extended to `routers/`; full migration tracked |
| L-1 | `per_tenant` mode sets marker only in `ModuleScopeMiddleware` | Follow-up 22.4.3 | Default is `shared`; middleware should 501 if `per_tenant` set before wiring completes |
| L-2 | `audit_log_fn=None` valid in `with_admin_cross_tenant_scope` | Before next caller | Tighten signature; no current production caller omits it |

### 7.4 New audit event types

No schema change to `audit_log`. New action strings used in this epic:

- `tenant.cross_scope.enter` / `tenant.cross_scope.exit` -- every admin cross-tenant read
- `tenant.scope_missing` -- every `TenantScopeMissingError` raised by the listener
- `tenant.module_dbs.cleanup` -- per `(tenant, module)` during offboarding

---

## 8. Data Model Impacts

Detailed schema delegated to `schema-22.md` (B2 Data Engineer). Summary:

### 8.1 New table: tenant_module_databases

Already in codebase as migration `pg_tenant_module_databases.py`:

```sql
CREATE TABLE IF NOT EXISTS tenant_module_databases (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id             UUID NOT NULL,
    module_id             UUID NOT NULL,
    db_name               VARCHAR(255) NOT NULL,
    connection_secret_ref TEXT,
    status                VARCHAR(30) NOT NULL DEFAULT 'provisioning',
    error_message         TEXT,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, module_id)
);
```

Status lifecycle: `provisioning` -> `ready` | `failed` -> `archived`.

The `connection_secret_ref` column format: `vault:<path>`, `env:<VAR_NAME>`, or `arn:aws:secretsmanager:<region>:<account>:secret:<name>`. The raw DSN is never stored.

### 8.2 No changes to existing core tables

Shared-core hardening (Features 22.2 + 22.3) adds no new columns to existing models. `__tenant_scoped__ = True` is a Python class attribute, not a DB column. Existing `tenant_id` columns are unchanged.

### 8.3 BaseModule manifest contract change

`manifest.json` gains an optional `tenant_scoped` boolean key (default `true` if absent). No DB migration required.

---

## 9. NFRs

Inherited from `arch-platform.md` section 7 and refined:

| NFR | Target | Notes |
|-----|--------|-------|
| API p95 latency | < 500 ms (unchanged) | Helper adds one `filter()` call per query (no extra DB round-trip). Listener fires at ORM compile time, O(mappers) per query, expected < 1 ms overhead. |
| Tenant filter overhead | <= 1 ms per query p99 | C2 must benchmark on the hot CRUD path before merge. |
| Module DB provisioning | <= 60 s for (tenant, module) | Story 22.1.1 prototype gate; Feature 22.4 blocked until this passes. |
| Connection pool bound | <= 50 active (tenant, module) pools | LRU eviction in `ModuleScopeMiddleware`; `MODULE_DB_POOL_MAX` configurable. |
| Alembic fan-out concurrency | Default 4 parallel connections per run | Bounded to avoid DB connection exhaustion; configurable. |
| check-tenant-scope gate | Exits non-zero on any raw literal in `services/` or `routers/` | Pre-merge CI gate; covers both layers per M-2 remediation. |
| Unit test coverage | All new core modules (`scope.py`, `tenant_listener.py`, `tenant_scoped_session`, `module_scope_middleware.py`) must have unit tests | C2 deliverable. |
| Adversarial test plan | >= 30 core-DB + >= 10 module-DB scenarios (test-plan-22) | D1 QA owns story 22.5.3. |
| Observability | `TenantScopeMissingError` logged at ERROR with full traceback; scope transitions logged at INFO; provisioning changes logged at INFO. Structured log fields must include `tenant_id`, `module_id`. | No new Prometheus metrics required this sprint. |

---

## 10. Risks

| Signal | Risk | Mitigation |
|--------|------|-----------|
| Yellow | Story 22.1.1 prototype may exceed <= 60 s provisioning gate on cold DB + connection-pool init. | First task in sprint; gate blocks all Feature 22.4 stories. |
| Yellow | `ModuleScopeMiddleware` connection-pool wiring incomplete -- `per_tenant` mode silently uses shared DB (L-1). | Default is `shared`; release notes must warn operators; middleware should return HTTP 501 for `per_tenant` until wiring completes. |
| Yellow | Models added post-sprint without `__tenant_scoped__ = True` receive no listener protection (M-1). | Automated detection in sprint N+1; tracked. |
| Yellow | `DynamicEntityService._get_org_context()` migration (22.2.2) touches hot CRUD path -- regression risk. | Story 22.2.2 AC must include integration tests on existing entity CRUD flows. |
| Green | `UNIQUE(tenant_id, module_id)` prevents double-provisioning. | sec-review-22 I-3 verified; `IntegrityError` -> HTTP 409. |
| Green | `TenantScopeMissingError` -> HTTP 500, fail-closed. | sec-review-22 I-1 verified. |
| Green | Session teardown clears scope in `finally` -- no cross-request bleed in pool. | sec-review-22 I-2 verified. |

---

## 11. Reference Map

### Backend -- new files (this epic)
- `backend/app/core/scope.py` -- tenant scope helper: `apply_tenant_scope`, `with_admin_cross_tenant_scope`, `TenantScopeMissingError`
- `backend/app/core/tenant_listener.py` -- ORM listener: `TenantScopeListener`, `set_tenant_scope`, `clear_tenant_scope`
- `backend/app/core/module_scope_middleware.py` -- module DB routing middleware: `ModuleScopeMiddleware`
- `backend/app/alembic/versions/postgresql/pg_tenant_module_databases.py` -- `tenant_module_databases` DDL

### Backend -- modified (this epic)
- `backend/app/core/dependencies.py` -- `tenant_scoped_session` dependency (story 22.3.2); `clear_tenant_scope` in `finally`
- `backend/app/core/module_system/base_module.py` -- `tenant_scoped` flag and `get_tenant_scoped_tables()`
- `backend/app/services/dynamic_entity_service.py` -- `_get_org_context()` migrated to `apply_tenant_scope`
- `backend/app/services/*.py` -- ad-hoc `tenant_id ==` literals migrated (22.2.2 inventory)
- `backend/app/routers/modules.py` line 1883 -- T-23.025 stub wired to `cleanup_tenant_module_dbs`
- `manage.sh` -- new subcommands: `tenant deactivate`, `check-tenant-scope`, `module migrate-tenant`

### Scripts -- new
- `scripts/provision-tenant-module-db.py` -- per-tenant module DB provisioning (22.1.1 / 22.4.2)
- `scripts/migrate-module.py` -- Alembic fan-out for module migrations (22.4.4)
- `scripts/cleanup_tenant_module_dbs.py` -- tenant offboarding cleanup (22.4.5)

### Frontend -- new/modified
- `frontend/assets/js/` (modules page) -- provisioning status badge + retry button (22.4.2)

### Documentation -- new
- `docs/platform/TENANT_ISOLATION.md` -- canonical isolation guarantee document (22.5.1)
- `docs/modules/MODULE_DEVELOPMENT.md` -- updated with `tenant_scoped` flag contract (22.5.2)

### ADRs produced by this epic
- `plan/architecture/adr-003-per-tenant-module-databases.md` -- extends ADR-001 with `DATABASE_STRATEGY=per_tenant`

---

## 12. Decisions

- **No new microservice.** All new components are modules within the existing FastAPI application or operator-facing scripts.
- **Application-layer isolation preferred over PostgreSQL RLS.** JWT-embedded `tenant_id` is authoritative; RLS adds operational coupling to pooled connections without stronger guarantees on the `text()` bypass surface.
- **`per_tenant` is the correct module DB isolation strategy.** `DATABASE_STRATEGY=separate` (ADR-001) is deprecated with a one-release window.
- **`BaseModule.tenant_scoped = True` is the default.** Modules must explicitly opt out; the framework refuses per-tenant provisioning for `tenant_scoped=False` modules.
- **Provisioning gate (22.1.1) blocks Feature 22.4.** If <= 60 s is not achievable, Feature 22.4 scope is renegotiated with A3 before proceeding.
- **`with_admin_cross_tenant_scope()` is the ONLY legitimate cross-tenant read path.** Any other mechanism that bypasses the ORM listener is a bug, not a workaround.

---

## 13. Hand-off

`status: approved`. Downstream agents:

- **B2 Data Engineer**: `schema-22.md` -- confirm `tenant_module_databases` DDL from section 8.1; document `connection_secret_ref` format; confirm no other schema changes needed.
- **C1 Tech Lead**: gated on B2 approval; produce `tasks-22.md`; first task MUST be story 22.1.1 prototype gate; Feature 22.4 stories must not start until gate passes.
- **C2 Backend Developer**: implement section 11 backend list in story order; benchmark tenant filter overhead against <= 1 ms p99 NFR before merge; provide unit tests for all new core modules.
- **D3 Security Engineer**: confirm M-1 and M-2 remediation approaches before sprint N+1 planning; review `TENANT_ISOLATION.md` for compliance narrative quality (story 22.5.1 AC).