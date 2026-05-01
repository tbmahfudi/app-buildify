---
artifact_id: arch-00-platform
type: arch
producer: Software Architect
consumers: [Backend Engineer, Frontend Engineer, Data Modeler, DevOps, Tech Lead]
upstream: [BACKLOG.md, all platform epics]
downstream: []
status: approved
created: 2026-04-28
updated: 2026-04-29
decisions:
  - Modular monolith for the core API; each business module is a separate FastAPI service mounted behind one Nginx gateway
  - Multi-tenancy via shared schema with explicit tenant_id filtering in services (no session-scoped mixin, no schema-per-tenant)
  - Per-module Alembic version tables in a shared PostgreSQL database (e.g. financial_alembic_version) so module migrations evolve independently
  - Vanilla JS ES modules with no bundler; Flex Component Library extends a single BaseComponent class
  - APScheduler for background jobs (not Celery)
  - Deployment topology decision deferred to ADR-001 (monolith vs distributed via DEPLOYMENT_MODE env var)
open_questions:
  - Should multi-tenancy enforcement migrate from explicit per-service filters to a session-scoped tenant filter (defense-in-depth)?
  - When a second module is added, do we keep one shared PostgreSQL or move to per-module databases (DATABASE_STRATEGY=separate is wired but unused)?
  - CI/CD is absent from the repo; what is the target pipeline (GitHub Actions assumed)?
  - When to ship the 9 missing Flex layout components (15.1.1) — they block every UILDC frontend story?
---

# App-Buildify — Platform Architecture (arch-00-platform)

> System architecture document for the **platform** itself, reverse-engineered from the codebase as of 2026-04-28. Module-specific architectures (e.g. Financial) live in `plan-mod-<name>/architecture/`.

## 1. Context

App-Buildify is a multi-tenant NoCode/LowCode enterprise platform. Users in a tenant authenticate, are scoped to one or more companies/branches/departments, and use the platform to design entities, build pages, run workflows, and view dashboards/reports. Pluggable modules (currently: Financial) extend the platform with domain features; each module ships as its own FastAPI service.

**Primary actors**: end-user, tenant admin, platform admin, module developer.
**Primary external systems**: SMTP (email), webhooks, optional Sentry, optional Prometheus.

## 2. Container View (deployment topology)

Source: `docker-compose.yml`, `infra/nginx/nginx.conf`.

```
                Browser
                   │
                   ▼
        ┌──────────────────────┐
        │  api-gateway (Nginx) │  :80   security headers, rate-limit 100 r/s burst 20
        └──────────┬───────────┘
                   │
   ┌───────────────┼────────────────────────┐
   │               │                        │
   ▼               ▼                        ▼
core-platform  financial-module        frontend
FastAPI :8000  FastAPI :9001           static :5173 (dev)
   │               │                       (Nginx serves /index.html in prod)
   │               │
   └───────┬───────┘
           │
   ┌───────┼────────┐
   ▼                ▼
postgres :5432   redis :6379
(buildify db,    (cache, JWT
 shared schema)   blacklist)
```

| Service | Image / Build | Port | Depends on | Key env |
|---------|---------------|------|------------|---------|
| `postgres` | `postgres:15-alpine` | 5432 | — | `POSTGRES_DB=buildify` |
| `redis` | `redis:7-alpine` | 6379 | — | — |
| `core-platform` | `./backend` | 8000 | postgres ✓, redis ✓ | `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY` |
| `financial-module` | `./modules/financial/backend` | 9001 | postgres ✓, core-platform | `DATABASE_STRATEGY`, `CORE_PLATFORM_URL`, `MODULE_API_KEY` |
| `api-gateway` | `nginx:alpine` | 80 | core-platform, financial-module | — |
| `frontend` | `./frontend` (dev) | 5173 | — | `VITE_API_URL` |

Volumes: `postgres_data → /var/lib/postgresql/data`. Network: `buildify-network` (bridge).

### 2.1 Gateway routing
File: `infra/nginx/nginx.conf`.

| Path | Upstream |
|------|----------|
| `/api/v1/financial/` | `financial-module:9001` |
| `/api/v1/` | `core_platform:8000` |
| `/modules/` | filesystem alias `/app/modules/` (serves module frontend manifests + JS) |
| `/health` | static `200 healthy` |
| everything else | frontend |

Headers passed through: `Authorization`, `Content-Type`, `X-Tenant-ID`, `X-Company-ID`. CORS is open (`*`) at gateway level.

## 3. Component View — Backend (`/backend/`)

Stack: FastAPI · SQLAlchemy 2.0 · Pydantic v2 · APScheduler · slowapi · structlog · PyJWT · bcrypt.

### 3.1 Layering
Three-tier inside a single FastAPI app:

```
app/main.py  (lifespan: migrate → register modules → mount routers)
   │
app/routers/*.py        ← HTTP layer (HTTPBearer, Depends(get_db), Depends(get_current_user))
   │
app/services/*.py       ← Business logic, query orchestration
   │
app/models/*.py + app/core/db.py  ← SQLAlchemy ORM, Session
```

Schemas (Pydantic DTOs) live in `app/schemas/`. Cross-cutting concerns live in `app/core/`.

### 3.2 Cross-cutting (`app/core/`)
| File | Purpose |
|------|---------|
| `config.py` | `Settings(BaseSettings)`, cached via `@lru_cache get_settings()`, loads `.env` |
| `db.py` | `engine`, `SessionLocal`, dialect-aware `GUID` type |
| `auth.py` | JWT (HS256) issue/verify, JTI for revocation, bcrypt hashing |
| `dependencies.py` | `get_db`, `get_current_user`, `verify_tenant_access`, `has_permission`, `require_superuser` |
| `security_middleware.py` | Per-request session-timeout + password-expiration enforcement |
| `session_manager.py` | `UserSession` lifecycle, idle timeout |
| `lockout_manager.py` | Failed-login tracking, account lock |
| `password_validator.py`, `password_history.py` | Policy checks, history (no reuse) |
| `rate_limiter.py` | `slowapi` setup, configured by `RATE_LIMIT_*` env |
| `audit.py` | `create_audit_log()` writes to `audit_log` model |
| `exceptions.py`, `exceptions_helpers.py` | Standardized error envelope handlers |
| `notification_service.py` | Queue-based dispatch (email/SMS/webhook/push) |
| `module_system/registry.py` | `ModuleRegistryService` — sync filesystem ↔ DB |
| `module_system/loader.py` | `ModuleLoader` — discover + import modules |
| `module_system/base_module.py` | `BaseModule` ABC: `get_routers()`, `get_permissions()`, lifecycle hooks |

### 3.3 Routers (mounted in `main.py` lifespan)
`auth`, `org`, `metadata`, `data`, `audit`, `settings`, `modules`, `rbac`, `reports`, `dashboards`, `scheduler`, `menu`, `builder_pages`, `data_model`, `workflows`, `automations`, `lookups`, `dynamic_data`, `nocode_modules`, `module_extensions`. Health endpoints: `/api/health`, `/api/healthz`, plus `/api/system/info`.

### 3.4 Services worth knowing
- `DataModelService` + `RuntimeModelGenerator` — generate SQLAlchemy classes at runtime from NoCode `EntityDefinition`s
- `DynamicEntityService` + `DynamicQueryBuilder` (`app/core/dynamic_query_builder.py`) — generic CRUD/search/sort/pagination over runtime models
- `WorkflowService` — declarative workflows: steps, conditions, actions
- `SchedulerEngine` (`AsyncIOScheduler`, `MemoryJobStore`) + `SchedulerService` + `SchedulerJob` model — cron/interval/date triggers
- `MigrationGenerator` — generates Alembic migrations for NoCode entity changes
- `ReportService` + `ReportExportService` — definition, execution, export
- `DashboardService` — pages, widgets, snapshots, `WidgetDataCache`

### 3.5 Background work
APScheduler only. No Celery, no FastAPI `BackgroundTasks` in startup, no thread pools spawned at boot.

## 4. Component View — Frontend (`/frontend/`)

Stack: Vanilla JS ES modules · Tailwind (CDN) · Phosphor Icons (CDN) · i18next (CDN) · no bundler.

### 4.1 Bootstrap
`index.html` → `<script type="module" src="assets/js/app-entry.js">`.

`app-entry.js` imports the resource loader, i18n, and every page module up front, then calls `i18n.init()` and `initApp()` from `app.js`. `app.js` checks `localStorage.tokens`, redirects to `/assets/templates/login.html` if absent, otherwise loads `main.html` into `#root`, calls `/auth/me`, and initialises module loader + RBAC + menu rendering.

### 4.2 Routing & state
- Router: hash-based, `assets/js/router.js`. Routes are a `Map<path, handler>`, with `beforeEach` guards and a `route:loaded` CustomEvent on success.
- Dynamic NoCode routes: `assets/js/dynamic-route-registry.js` auto-registers `#/dynamic/{entity}/list` etc. by fetching `/metadata/entities/{name}`.
- State: no global store. Service singletons (`auth-service.js`, `module-manager.js`) hold their own state; per-component state in `this.state`; tokens/tenantId/preferred language persisted in `localStorage`.

### 4.3 Component model — Flex Component Library
`assets/js/core/base-component.js` defines `BaseComponent`:
- `(container, options)` constructor, options merged with static `DEFAULTS`
- Event system: `emit(name, detail)` dispatches a `CustomEvent` on the container
- Lifecycle: `init()` → `render()` → `attachEventListeners()`

Components extend it: `flex-button.js`, `flex-input.js`, `flex-datagrid.js`, `flex-form.js`, layout components in `assets/js/layout/` (`flex-container.js`, `flex-grid.js`, etc.). Plain DOM (`createElement` / `innerHTML`), no Web Components, no framework. Centralized re-export: `assets/js/components/index.js`.

### 4.4 API client (`assets/js/api.js`)
`apiFetch(path, opts)` injects `Authorization: Bearer <access>` and `X-Tenant-Id`, handles 401 by calling `/auth/refresh` once and retrying. Token helpers: `loadTokens()`, `saveTokens()`, `clearTokens()`, `setTenant()`. No central error boundary — callers handle status codes.

### 4.5 i18n
`assets/js/i18n.js` (`I18nManager`) wraps i18next + http backend. Files served from `/assets/i18n/{lng}/{ns}.json`. Namespaces: `common`, `menu`, `pages`. Languages: `en`, `de`, `es`, `fr`, `id`. DOM elements use `data-i18n="key"`; JS uses `window.i18n.t()`.

### 4.6 Frontend module integration
`assets/js/core/module-system/module-loader.js`:
1. `GET /module-registry/enabled/names` → list of enabled modules for the tenant
2. `GET /modules/{name}/manifest` → manifest.json (served by Nginx from `/app/modules/`)
3. Dynamic `import()` of the module's `entry_point` (e.g. `module.js`)
4. Routes from manifest are registered into the hash router; menu items merged into the sidebar

## 5. Data Architecture

### 5.1 Schema strategy
Single PostgreSQL database (`buildify`), shared schema. Per-module tables are name-prefixed (e.g. `financial_accounts`, `financial_invoices`). Multi-tenancy is **soft**: rows carry a `tenant_id` UUID column, and **services apply `tenant_id` filters explicitly** on every query. There is no row-level security policy and no SQLAlchemy session-scoped mixin enforcing this — see open questions.

### 5.2 Identity model
```
Tenant
 └── Company
      └── Branch
           └── Department
User ── Tenant   (1 user → exactly 1 tenant; nullable=False)
User ── Companies (many-to-many access)
```
JWT payload: `sub`, `tenant_id`, `exp`, `iat`, `jti`. `tenant_id` is verified in `get_current_user()` and again by `verify_tenant_access()` for tenant-scoped routes; superusers bypass.

### 5.3 RBAC
Permission format: `resource:action:scope`. Example: `financial:invoices:read:company`. Junction tables (`app/models/rbac_junctions.py`): `UserGroup`, `GroupRole`, `RolePermission`. Resolution at request time via `has_permission()` dependency.

### 5.4 Migrations
- Core: `backend/alembic.ini` → `backend/app/alembic/`. `env.py` detects dialect; per-dialect version dirs `versions/postgresql/`, `versions/mysql/`. Run automatically in the FastAPI lifespan startup.
- Per-module: each module ships its own `alembic.ini` + `alembic/` and uses a **distinct version table**: `{module_name}_alembic_version` (e.g. `financial_alembic_version`). This lets modules upgrade independently against the shared database.

### 5.5 Seeds
Scripts live in `backend/app/seeds/` (e.g. `seed_all_permissions.py`, `seed_complete_org.py`, `seed_builder_rbac.py`). Driven by `manage.sh seed-*` subcommands.

## 6. Module System

A module is a self-contained FastAPI service plus frontend assets that follows a manifest contract.

### 6.1 Folder layout (`/modules/<name>/`)
```
modules/financial/
├── manifest.json
├── backend/
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/env.py            ← {MODULE_NAME}_alembic_version
│   ├── requirements.txt
│   └── app/{main.py, models/, routers/, schemas/, services/, core/}
└── frontend/
    ├── module.js                 ← entry point loaded dynamically
    ├── pages/                    ← route components
    ├── components/               ← module-local components
    └── styles/
```

### 6.2 Manifest contract (`manifest.json`)
Key fields: `name`, `display_name`, `version`, `backend_service_url`, `entry_point`, `routes[]` (path, component, permission, menu metadata), `navigation` (primary_menu, menu_items, dashboard_widgets), `dependencies` (required_modules, optional_modules), `database.has_migrations`, `subscription_tier`, `pricing`, `is_core`.

### 6.3 Lifecycle
1. **Discovery**: `ModuleLoader` scans the modules directory for `manifest.json` + `module.py`.
2. **Sync**: `ModuleRegistryService.sync_modules()` upserts records into the `ModuleRegistry` table and registers their permissions.
3. **Mount (backend)**: in the core-platform lifespan, each module's `get_routers()` is included on the FastAPI app — though in production the module also runs as its own service behind the gateway at `/api/v1/<name>/`.
4. **Enable (per tenant)**: `TenantModule` row created when a tenant admin enables the module via `/modules/{name}/enable`.
5. **Frontend load**: browser fetches the manifest, dynamic-imports `entry_point`, merges routes + menu.

## 7. Cross-cutting Concerns (NFRs)

| Concern | How it's met today | File(s) |
|---------|-------------------|---------|
| **Authentication** | JWT HS256, access (30 min) + refresh (7 d) tokens, JTI revocation in Redis blacklist | `app/core/auth.py`, `app/routers/auth.py` |
| **Authorization** | RBAC dependency `has_permission(...)`; permission strings checked per route | `app/core/dependencies.py`, `app/routers/rbac.py` |
| **Multi-tenancy isolation** | JWT-embedded `tenant_id` + explicit per-service filters | `app/services/*` |
| **Session security** | Idle + absolute timeout, max concurrent sessions, force-logout on password change | `app/core/security_middleware.py`, `app/core/session_manager.py` |
| **Password policy** | Length, classes, history, expiration | `app/core/password_validator.py`, `app/core/password_history.py` |
| **Rate limiting** | slowapi at app level + Nginx 100 r/s burst 20 at gateway | `app/core/rate_limiter.py`, `infra/nginx/nginx.conf` |
| **Audit logging** | `audit_log` model written from `create_audit_log()` calls in routers | `app/core/audit.py`, `app/routers/audit.py` |
| **Observability** | structlog structured logs; optional Sentry (`SENTRY_DSN`); optional Prometheus (`ENABLE_METRICS`) | `app/core/logging_config.py` |
| **Health** | `/api/health` (component checks), `/api/healthz` (liveness), gateway `/health` | `app/main.py`, `infra/nginx/nginx.conf` |
| **CORS** | `ALLOWED_ORIGINS` env (default `*`) at FastAPI; `*` at Nginx | `app/main.py`, `infra/nginx/nginx.conf` |
| **Input validation** | Pydantic v2 schemas on every router | `app/schemas/*` |

## 8. Operations

### 8.1 Entry points
- **`manage.sh`** is the canonical CLI: `start`, `stop`, `restart`, `migrate`, `seed`, `seed-{permissions,rbac,menu,menu-rbac,module-rbac,financial-rbac}`, `db-reset`, `backup`, `restore`, `db-shell`, `shell`, `logs`, `test`, `health-check`.
- **`Makefile`** mirrors a subset for local dev: `setup`, `migrate-pg`, `migrate-mysql`, `seed`, `run`, `docker-up`, `docker-down`.
- **`scripts/create-module.sh`** scaffolds a new module.

### 8.2 Tests
- Backend: pytest + pytest-bdd. `backend/tests/{unit,integration,features,steps}` with `pytest.ini` markers `unit | integration | pg | slow`. Test DB defaults to SQLite, switches to PostgreSQL when `TEST_DATABASE_URL` is set.
- Frontend: Vitest configured (`vitest.config.js`, jsdom, 80% line/statement coverage threshold). `frontend/tests/{components, core, helpers, layout, setup.js}` exists; coverage of actual `.test.js` files is currently sparse — flag for QA.

### 8.3 CI/CD
**Absent**. No `.github/workflows/`. All migrations/seeds/builds today are run via `manage.sh`. Adding GitHub Actions for PR validation, image build/push, and prod deploy is on the roadmap (see EPIC 19).

## 9. Risks & Open Questions

> Updated 2026-04-29 with findings from the first-round epic audits in [`audits/`](audits/). Risks 8–13 are net new from those audits.

1. **Tenant-isolation defense-in-depth**: Filtering relies on every service writing `query.filter(Model.tenant_id == self.tenant_id)`. A missed filter is a cross-tenant data leak. Options: PostgreSQL RLS, or a SQLAlchemy event listener that injects the filter automatically.
2. **Database strategy**: `DATABASE_STRATEGY=shared|separate` is plumbed for the financial module but only `shared` is used. ADR-001 ties this to `DEPLOYMENT_MODE`: `distributed` mode defaults to `separate`. Second module will force the operational choice.
3. **Module mount duplication**: Both in-process mounting (`backend/app/main.py:70-76`) and standalone-service mounting (`modules/financial/backend/app/main.py:110-118`) are alive. ADR-001 resolves this by making `DEPLOYMENT_MODE` the canonical switch — pending implementation of the one-line guard in `main.py`.
4. **CORS `*` everywhere**: Acceptable in dev, must be tightened before prod (gateway and FastAPI).
5. **JWT secret**: `JWT_SECRET_KEY=your-secret-key-change-in-production` is the literal compose default. Rotation/management procedure needs documenting.
6. **Frontend has no bundler / no SRI**: Tailwind, Phosphor, and i18next load from CDNs; CSP must be reviewed before prod.
7. **No CI/CD**: Production deployments are manual via `manage.sh`. EPIC 19 covers this; `audit-19-infrastructure-deployment.md` flags it 🔴.
8. **🔴 Wildcard permissions are not implemented**: `has_permission()` at `app/core/dependencies.py:108` does a literal `in` check; AC for story 4.2.1 promises segment-wise wildcards. `*:*:platform` matches nothing. See `audit-04-rbac-permissions.md`.
9. **🔴 Role CRUD missing**: No `POST/PUT/DELETE /api/v1/rbac/roles` endpoints (only assignment endpoints exist). Tenant admins cannot create custom roles via API. See `audit-04-rbac-permissions.md` story 4.1.1.
10. **🔴 Per-entity permissions are dead schema**: `EntityDefinition.permissions` JSONB exists at `app/models/data_model.py:91` but `DynamicEntityService` does not consume it. See `audit-04-rbac-permissions.md` story 4.2.4.
11. **🔴 Flex layout suite missing**: Stories tagged `[DONE]` claim 9 layout components (`flex-stack`, `flex-grid`, `flex-split-pane`, …) that don't exist. Every UILDC v1.0 story across all 19 epics depends on them. See `audit-15-flex-component-library.md`.
12. **🔴 Email/SMS/in-app notification delivery missing**: Queue architecture is real (Feature 14.1 DONE), but no message has ever been delivered. Password-reset flow currently dead-letters. See `audit-14-notification-system.md`.
13. **🔴 No backend or frontend tests**: `pytest` and `vitest` configured; `.test.py`/`.test.js` files not located. Audit fidelity gates further work. See `audit-13-security-compliance.md` stories 13.4.1/13.4.2.
14. **🟡 LISTEN/NOTIFY subscriber stub**: `modules/financial/backend/app/core/event_handler.py:43-47` is a placeholder. Distributed deployment mode (ADR-001) cannot be declared production-ready without it. See `audit-11-module-system.md`.

## 10. Reference Map (where to look in the codebase)

| Area | Path |
|------|------|
| Backend entry | `backend/app/main.py` |
| Cross-cutting | `backend/app/core/` |
| Routers | `backend/app/routers/` |
| Services | `backend/app/services/` |
| Models | `backend/app/models/` |
| Migrations | `backend/app/alembic/` |
| Module system | `backend/app/core/module_system/` |
| Frontend entry | `frontend/index.html`, `frontend/assets/js/app-entry.js`, `frontend/assets/js/app.js` |
| Components | `frontend/assets/js/components/`, `frontend/assets/js/layout/`, `frontend/assets/js/core/base-component.js` |
| API client | `frontend/assets/js/api.js` |
| Router | `frontend/assets/js/router.js`, `frontend/assets/js/dynamic-route-registry.js` |
| Module system (FE) | `frontend/assets/js/core/module-system/` |
| Modules | `modules/<name>/` (e.g. `modules/financial/`) |
| Gateway | `infra/nginx/nginx.conf` |
| Compose | `docker-compose.yml`, `infra/docker-compose.prod.yml` |
| Ops | `manage.sh`, `Makefile`, `scripts/` |
| Tests | `backend/tests/`, `frontend/tests/`, `vitest.config.js`, `backend/pytest.ini` |

## Decisions

- Modular monolith for the core API; modules run as sibling FastAPI services routed by Nginx — chosen for independent module deployability without the operational cost of full microservices.
- Shared PostgreSQL with name-prefixed module tables and per-module Alembic version tables — chosen to keep cross-module joins cheap while letting modules ship migrations independently.
- Vanilla JS + Flex Component Library, no build step — chosen to keep the frontend dependency footprint near zero and the deploy unit a static directory.
- APScheduler over Celery — single-process scheduling fits current scale; revisit if multi-worker / durable queues become required.
- Multi-tenancy via explicit `tenant_id` filters — pragmatic given existing services; flagged in §9 for hardening.

## Open Questions

- See §9. The most consequential is question 1 (tenant-isolation defense-in-depth) which should be resolved before EPIC 13 closes.
