---
artifact_id: arch-22
type: arch
producer: B1 Software Architect
consumers: [B2 Data Engineer, C1 Tech Lead, C2 Backend Developer, C3 Frontend Developer, D3 Security Engineer, E1 DevOps Engineer]
upstream: [vision-02-tenant-isolation-hardening, research-02-tenant-isolation-hardening, epic-22-tenant-isolation-hardening]
downstream: [adr-003-per-tenant-module-databases]
status: review
created: 2026-05-08
updated: 2026-05-08
decisions:
  - Two architectural tracks: shared-core hardening (helper + listener) and module-DB-per-tenant; they share no code path
  - Module DB naming: `tm_{short_hash(tenant_id)}_{module_id}` to avoid Postgres identifier restrictions (no dashes, no leading digit)
  - Credentials model: single `platform_app` Postgres role with `CREATE` privilege at the cluster level + per-DB `CONNECT` GRANT — simpler than per-tenant role rotation, residual risk noted in §6
  - Module DB provisioning is lazy at first module-enable (A3 confirmed in epic-22 22.4.2)
  - Connection pool: bounded LRU cache of per-(tenant, module) pools, default `MODULE_DB_POOL_CACHE_SIZE=50`, idle-evict after 10 minutes
  - Cross-DB FKs: logical only; periodic reconciliation job; never DB-enforced
open_questions:
  - When `MODULE_DB_POOL_CACHE_SIZE` is reached and an evicted pool's tenant returns, latency spike on first request — acceptable or pool-warm proactively? Decide after benchmark.
  - SECURITY DEFINER functions in module DBs (if any module ships them) — do they implicitly bypass tenant scope? Out of scope for v1; require module-review.
corrections: []
---

# arch-22 — System Design for Tenant Isolation Hardening

> **Upstream**: [`epic-22-tenant-isolation-hardening`](../epics/epic-22-tenant-isolation-hardening.md). Designs the two-track architecture (shared-core hardening + per-tenant module DBs) called out in `vision-02` and `research-02`. Records the rationale for one significant ADR ([`adr-003-per-tenant-module-databases`](adr-003-per-tenant-module-databases.md)) extending [`adr-001-deployment-modes`](adr-001-deployment-modes.md) with a third `DATABASE_STRATEGY` value.

---

## 1. Context

Per `vision-02` revised 2026-05-08, epic-22 ships a hybrid tenant-isolation design:

- **Shared core DB**: 2-layer logical isolation (centralized scope helper + SQLAlchemy session-event listener). Direct-DB-access path (DBA / `psql` / raw SQL) remains structurally unprotected; covered by operational controls. Identity + login + system catalogs stay in the shared core.
- **Module DBs**: database-per-tenant (`DATABASE_STRATEGY=per_tenant` extends ADR-001). Each tenant gets a dedicated Postgres database per module they enable. Physical isolation, no shared rows possible.

The two tracks share no code path: hardening the core's ORM is independent of provisioning module DBs. They land in the same sprint because both are required to close the `sec-review-21` highest-residual-risk finding, but C2 can develop them in parallel.

The first sprint task (per `research-02` §5 caveat) is a provisioning prototype (story 22.1.1) that must hit the ≤ 60 s budget before broad rollout. If it doesn't, scope narrows to core-only.

## 2. Components

### 2.1 New (shared core track — Features 22.2 + 22.3)

- **`backend/app/core/scope.py`** (NEW). Exports `apply_tenant_scope(query, model, user)`, `tenant_scope_dependency(user)`, `with_admin_cross_tenant_scope(reason)`, and `TenantScopeMissingError`. Single source of truth for tenant-aware query construction.
- **`backend/app/core/scope_listener.py`** (NEW). SQLAlchemy `before_compile` event handler. For any `Query` against a model with `__tenant_scoped__ = True`, injects `WHERE tenant_id = <session_scope>` if scope is set, raises `TenantScopeMissingError` if not. Honors the `with_admin_cross_tenant_scope` context manager (skips injection inside the block).
- **Tenant-scoped model registry** — a class-level marker `__tenant_scoped__: bool = True` on `Base` subclasses; the listener consults this on first compile of each model and caches the result.

### 2.2 New (module-DB track — Feature 22.4)

- **`tenant_module_databases` table** (in core DB). Registry of `(tenant_id, module_id, db_name, status, created_at, last_migrated_at, error_message)`. Owns the lifecycle state for every per-tenant module DB.
- **`backend/app/core/module_db/provisioner.py`** (NEW). Service that creates a Postgres database, runs the module's Alembic migrations against it, and writes the registry row. Idempotent: re-running on a `status='failed'` row retries; re-running on `status='ready'` is a no-op.
- **`backend/app/core/module_db/registry.py`** (NEW). Read-side API: `get_connection_url(tenant_id, module_id)` → URL or raises if not provisioned. Caches lookups for the request lifetime.
- **`backend/app/core/module_db/pool_cache.py`** (NEW). Bounded LRU cache (default 50 entries) of per-(tenant, module) SQLAlchemy `Engine` instances. Idle entries (no requests for ≥ 10 min) are evicted and disposed. Cache size + idle TTL are configurable via env.
- **`backend/app/middleware/module_scope.py`** (NEW). FastAPI middleware. For requests matching `/api/v1/modules/{module_id}/...`, reads JWT `tenant_id`, asks `registry.get_connection_url(tenant_id, module_id)`, opens a session from the pool cache, attaches to `request.state.module_db`.
- **`scripts/migrate-module.py`** (NEW). Alembic fan-out runner. Reads `tenant_module_databases` for the given module, runs `alembic upgrade head` against each connection with `MODULE_MIGRATION_CONCURRENCY` parallel workers (default 4). Idempotent on partial failure.
- **`manage.sh tenant deactivate <id>`** extension (modified). Invokes new `cleanup_tenant_module_dbs(tenant_id)` service per `TENANT_DELETION_POLICY=drop|archive`.

### 2.3 Modified (cross-cutting)

- **`backend/app/core/module_system/base_module.py`** — `BaseModule` ABC gains `tenant_scoped: bool = True` class attribute and `get_tenant_scoped_tables() -> List[str]` method. Backwards-compatible: existing modules without the declaration default to `tenant_scoped=True`.
- **Every `*Service` class with `tenant_id == user.tenant_id` literals** (Story 22.2.2) — migrated to `apply_tenant_scope(query, Model, user)`. Inventory pass first; ~10-20 services expected based on epic-04 / epic-05 / epic-06 audit cites.
- **`backend/app/main.py`** — middleware chain extended with `ModuleScopeMiddleware`; lifespan optionally pre-warms the most-recently-active (tenant, module) pools.

### 2.4 Unchanged but referenced

- **`backend/app/core/db.py SessionLocal`** — the existing core-DB session factory. Unchanged. The new dependency `tenant_scoped_session(user, db)` wraps `Depends(get_db)`.
- **Existing module registry / `module_service_registry.py`** — unchanged; module loading still happens at platform startup. Per-tenant DB selection is a request-time concern handled by middleware, not at module-load time.

## 3. Data Flow

### 3.1 Tenant-scoped CRUD query against shared core DB (the happy path)

```
client request ──Bearer JWT (sub, tenant_id)──> FastAPI handler
handler ──Depends(tenant_scoped_session(user))──> Session w/ scope set to user.tenant_id
handler ──db.query(Role)──> SQLAlchemy compile
SQLAlchemy ──before_compile event──> scope_listener.before_compile()
scope_listener ──reads __tenant_scoped__ True──> injects WHERE roles.tenant_id = <scope>
SQLAlchemy ──compiled SQL──> Postgres
Postgres ──filtered rows──> handler
```

### 3.2 Forgotten scope (a real failure mode)

```
admin script (no FastAPI) ──opens raw SessionLocal()──> Session w/ NO scope set
script ──db.query(User).all()──> compile event fires
scope_listener ──scope is None on a tenant_scoped model──> raises TenantScopeMissingError
script ──crashes loudly with stack trace──> exits non-zero; audit-log row `tenant.scope_missing`
```

The same fail-loud behavior applies if a route handler forgets to use `tenant_scoped_session` and uses `Depends(get_db)` against a tenant-scoped query.

### 3.3 Module-DB-routed request (the happy path)

```
client request ──/api/v1/modules/financial/invoices──> ModuleScopeMiddleware
middleware ──reads JWT.tenant_id, parses URL──> registry.get_connection_url(tenant_id, 'financial')
registry ──cache miss──> SELECT FROM tenant_module_databases WHERE tenant_id=? AND module_id='financial'
registry ──row found, status='ready'──> returns URL `postgresql://platform_app@db/tm_<hash>_financial`
middleware ──asks pool_cache for engine──> cache hit (or new pool created)
middleware ──opens session, attaches to request.state.module_db──> handler runs
handler ──uses request.state.module_db──> queries against the right tenant's financial DB
```

### 3.4 First module-enable triggers provisioning

```
tenant admin ──POST /api/v1/modules/financial/enable──> module-enable handler
handler ──checks registry──> no row exists for (tenant_id, 'financial')
handler ──enqueues provisioning task (or runs synchronously if T-21.X.5 budget allows)──> provisioner.provision(tenant_id, 'financial')
provisioner ──CREATE DATABASE tm_<hash>_financial──> Postgres
provisioner ──connects to new DB──> runs alembic upgrade head from module's Alembic dir
provisioner ──registry INSERT (tenant_id, 'financial', db_name, status='ready', created_at)──> core DB
handler ──returns 200 to tenant admin──> UI flips badge to 'Ready' (poll)
```

On provisioning failure:

```
provisioner ──CREATE DATABASE fails OR migration fails──> caught exception
provisioner ──registry INSERT (..., status='failed', error_message=str(exc))──> core DB
handler ──returns 500 with error detail──> UI flips badge to 'Failed (retry)'
admin ──clicks Retry──> handler re-invokes provisioner; row updated to 'ready' or 'failed' again
```

### 3.5 Module migration fan-out

```
operator ──python scripts/migrate-module.py financial──> reads tenant_module_databases WHERE module='financial' AND status='ready'
script ──N rows──> distributes across 4 worker threads (configurable)
each worker ──for its tenant DB: alembic upgrade head──> success → UPDATE last_migrated_at; failure → UPDATE error_message + alert
script ──collects results──> exits 0 if all succeeded, 1 if any failed (with summary)
```

## 4. Integration Points

| Integration | Direction | Failure isolation |
|---|---|---|
| **Postgres core DB** | bi-directional | Existing pool; unchanged |
| **Postgres per-tenant module DB** | bi-directional (per-request) | Connection failure on one (tenant, module) DB does NOT affect requests to other DBs; pool cache evicts and recreates on next request |
| **Module Alembic dirs** | platform reads | Per-module Alembic config is per-module concern; platform invokes `alembic upgrade` via subprocess + env-var override of `sqlalchemy.url` |
| **`module-system` registry** | unchanged | Module discovery + routing-table population at startup unchanged; per-tenant DB selection is request-time |
| **No new external services** | — | — |

Required env vars (new):
- `DATABASE_STRATEGY=per_tenant` (extends ADR-001 — was `shared|separate`)
- `MODULE_DB_HOST` / `MODULE_DB_PORT` / `MODULE_DB_USER` / `MODULE_DB_PASSWORD` — credentials for the `platform_app` role used to provision + connect to all per-tenant module DBs (same Postgres cluster as core, simplest topology; remote cluster supported via these vars)
- `MODULE_DB_POOL_CACHE_SIZE=50` — bounded pool LRU
- `MODULE_DB_POOL_IDLE_TTL_SECONDS=600` — idle eviction
- `MODULE_MIGRATION_CONCURRENCY=4` — parallel fan-out workers
- `TENANT_DELETION_POLICY=drop|archive` (default `archive`)

## 5. NFRs

Inherited from `arch-platform.md` §7 + epic-22-specific:

| NFR | Target | Source |
|---|---|---|
| Core-DB query latency p95 | ≤ 500 ms (unchanged from arch-platform.md §7) | unchanged |
| Helper overhead per query | ≤ 50 µs added | NEW — measured during 22.2.1 dev |
| Listener overhead per query compile | ≤ 100 µs added | NEW |
| Per-tenant module DB provisioning time | ≤ 60 s end-to-end (story 22.1.1 gate) | vision-02 metric #5 |
| Module-routing middleware overhead | ≤ 5 ms per request (pool cache hit); ≤ 200 ms (pool cache miss; engine init) | NEW |
| Cross-DB query — explicitly impossible | n/a | a feature, not a bug |
| Module migration fan-out | 100 tenants × financial module < 5 minutes wall-clock | NEW; depends on `MODULE_MIGRATION_CONCURRENCY` |

## 6. Risks

| 🚦 | Risk | Mitigation |
|---|---|---|
| 🔴 | Single `platform_app` Postgres role + per-DB GRANT (vs per-tenant role) means a credential compromise = all tenants' module DBs exposed | Accepted trade-off vs per-tenant role rotation complexity. Document in `sec-review-22`. Long-term: per-tenant role is a backlog item. |
| 🔴 | Pool-cache eviction at high tenant churn could cause request latency spikes (new tenant returns after eviction → 200 ms engine init) | Tune `MODULE_DB_POOL_CACHE_SIZE` per deployment; warm-up on lifespan startup; metrics dashboard for evict rate |
| 🟡 | Module DB names use a hash of `tenant_id` → hash collisions possible (theoretical) | Use SHA-1 truncated to 12 hex chars (48 bits) — collision probability negligible at expected scale; on conflict, fall back to full UUID-as-hex with database-name length check |
| 🟡 | SECURITY DEFINER functions inside module DBs (if any module ships them) could implicitly bypass tenant scope at the SQL level | Out of scope for v1; require module-review-time check; document in module dev guide |
| 🟡 | Alembic migration fan-out partial failure leaves the deployment in a mixed-version state | Per-tenant migration status tracked in registry row; rerun is idempotent; alerting on stuck tenants |
| 🟡 | Cross-DB foreign keys are impossible → module data references core `user_id` / `tenant_id` as plain UUIDs; orphaned references possible after user-delete | Reconciliation job runs daily; logs orphans; deletes after grace period |
| 🟢 | Scope-context-unset on a public route (login, health) — listener fires and crashes the request | `tenant_scoped_session()` is opt-in; public routes use a different dependency that disables scope checking |
| 🟢 | Listener doesn't cover raw `text()` / `bulk_insert_mappings` calls | Documented in `TENANT_ISOLATION.md`; helper API is the only sanctioned path for those |

## 7. Reference Map

Files this design touches, grouped by component.

### Backend (new files)
- `backend/app/core/scope.py` — helper API (Story 22.2.1)
- `backend/app/core/scope_listener.py` — SQLAlchemy event handler (Story 22.3.1)
- `backend/app/core/module_db/__init__.py` — package marker
- `backend/app/core/module_db/provisioner.py` — DB creation + Alembic runner (Story 22.4.2)
- `backend/app/core/module_db/registry.py` — read-side connection-URL lookup (Story 22.4.1)
- `backend/app/core/module_db/pool_cache.py` — bounded LRU engine cache (Story 22.4.3)
- `backend/app/middleware/module_scope.py` — FastAPI request middleware (Story 22.4.3)
- `scripts/migrate-module.py` — Alembic fan-out runner (Story 22.4.4)
- `scripts/provision-tenant-module-db.py` — prototype throwaway (Story 22.1.1)

### Backend (modified)
- `backend/app/core/module_system/base_module.py` — `tenant_scoped` class attr + `get_tenant_scoped_tables()` method (Story 22.5.2)
- `backend/app/main.py` — register `ModuleScopeMiddleware`; optional pool warm-up in lifespan
- `backend/app/services/*.py` — every `*Service` with `tenant_id == ...` literals migrated to `apply_tenant_scope` (Story 22.2.2). Concrete inventory:
  - `backend/app/services/dynamic_entity_service.py` (`_get_org_context` becomes a thin wrapper or is removed)
  - Every other service touching tenant-scoped models — full list produced by `scripts/grep-tenant-literals.sh` (helper script written as part of 22.2.2)
- `backend/manage.sh` — extend `tenant deactivate` per `TENANT_DELETION_POLICY` (Story 22.4.5); add `check-tenant-scope` and `module migrate-tenant` subcommands

### Frontend
- `frontend/assets/templates/modules.html` — provisioning status badge per module card + retry button (Story 22.4.2)
- `frontend/assets/js/modules.js` (or equivalent) — poll `GET /api/v1/modules/{id}/provisioning-status` every 2 s while in-flight; FlexAlert on failure

### Configuration / Deployment
- `backend/.env.example` — add `MODULE_DB_*`, `MODULE_MIGRATION_CONCURRENCY`, `TENANT_DELETION_POLICY`, `DATABASE_STRATEGY=per_tenant` option
- `docker-compose.yml` (root, dev) — `core-platform` service gains the new env vars; no new container needed
- `infra/docker-compose.prod.yml` — same env-var additions

### Documentation
- `docs/platform/TENANT_ISOLATION.md` (NEW) — Story 22.5.1
- `docs/modules/MODULE_DEVELOPMENT.md` (modified) — document the `tenant_scoped` flag (Story 22.5.2)

### Database (handled by B2 in schema-22)
- `tenant_module_databases` table — DDL belongs in B2's `schema-22.md`; arch-22 references its shape only

## 8. Decisions

- **Two parallel tracks.** Shared-core hardening (Features 22.2 + 22.3) and module-DB-per-tenant (Feature 22.4) share no code path. C2 can develop them in parallel; only the test plan (Feature 22.5) integrates them.
- **Lazy module-DB provisioning** (at first module-enable, not at tenant create). Saves operational cost at scale; users see provisioning time on the first enable only.
- **Bounded LRU pool cache** rather than unbounded pool-per-(tenant, module). Cap at 50 active engines (configurable); idle-evict at 10 min. Trade-off: cold-start latency spike on cache-evicted tenant returns. Acceptable per benchmark expectations.
- **Single `platform_app` Postgres role** for all module DBs (rather than per-tenant roles). Simpler ops; residual risk documented (single credential compromise = all module DBs). Per-tenant role is a backlog item if a regulated tenant ever demands it.
- **Module DB naming**: `tm_{12hex hash of tenant_id}_{module_id}`. 12 hex chars = 48 bits; collision negligible at expected scale; PG identifier valid (no dashes, no leading digit).
- **Cross-DB FKs**: logical only, never DB-enforced. Reconciliation job runs daily. Module DB rows reference core `user_id` / `tenant_id` as plain UUID columns.
- **ADR-003** authored alongside this design extends ADR-001's `DATABASE_STRATEGY` with `per_tenant` as a third value; `separate` (wired but unused) gets a one-release deprecation window.

## 9. Open Questions

- **Pool cache eviction tuning**: when `MODULE_DB_POOL_CACHE_SIZE=50` is reached, the eviction policy is LRU. Should we additionally pre-warm based on last-N-active tenants on lifespan startup? Defer to post-benchmark.
- **Migration fan-out failure semantics**: if 95 of 100 tenants migrate but 5 fail, do we retry automatically next deploy or require manual operator action? Currently requires manual rerun. Revisit if failure rates are non-trivial.
- **SECURITY DEFINER inside module DBs**: requires module-review-time policy. Not solving in v1; document as a known caveat.

## 10. Hand-off

`status: review`. Once `approved`:
- **B2 Data Engineer** — produces `schema-22.md` covering the `tenant_module_databases` registry table + the per-module-DB schema template (Alembic-generated)
- **B3 UX Designer** — produces UILDC for Story 22.4.2 (provisioning status badges + retry button on existing `#/modules` page)
- **C1 Tech Lead** — produces `tasks-22.md` once B1/B2/B3 are approved; first task is the 22.1.1 prototype gate
- **C2 Backend Developer** — implements §7 backend list per item ordering in epic-22
- **C3 Frontend Developer** — implements §7 frontend list (small slice — only Story 22.4.2 has UI)
- **D3 Security Engineer** — review the single-`platform_app` role decision + cross-DB FK absence (M-1 + L-1 candidate findings)
- **E1 DevOps Engineer** — review env-var additions + the `docker-compose` changes; produce the migration runbook
