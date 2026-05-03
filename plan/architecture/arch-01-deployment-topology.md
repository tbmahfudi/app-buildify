---
artifact_id: arch-01-deployment-topology
type: arch
producer: Software Architect (B1)
consumers: [Backend Engineer, Frontend Engineer, DevOps, Tech Lead, B2, C1, C2, C3, D3]
upstream: [vision-01-app-buildify, research-01-app-buildify, arch-platform, adr-001-deployment-modes, adr-002-monolith-service-boundaries, adr-003-microservices-decomposition, adr-004-inter-service-communication]
downstream: [B2, C1, C2, C3, D3]
status: review
created: 2026-05-03
updated: 2026-05-03
decisions:
  - Monolith (DEPLOYMENT_MODE=monolith) is the production-ready default; six domain slices run in one FastAPI process (ADR-002)
  - Distributed (DEPLOYMENT_MODE=distributed) is the growth topology; modules become independent FastAPI services (ADR-003)
  - Both modes share one codebase, one Nginx gateway, one PostgreSQL host; they differ only in process layout and database-per-module setting (ADR-001)
  - Three inter-service communication patterns govern all cross-domain interactions: gateway aggregation (sync), event bus (async), admin REST (lifecycle) (ADR-004)
open_questions:
  - Asymmetric JWT (RS256) needed before distributed mode is "rotate without restart"; when to prioritise?
  - Port auto-allocation for modules beyond 9004 — manifest registry or orchestrator-assigned?
  - When does Reporting Service warrant extraction from core? Trigger criteria in ADR-003 are qualitative; should we set a quantitative threshold (e.g. p95 report export > 3 s for 30 days)?
  - Kubernetes target timeline? Service mesh (mTLS) only makes sense at Kubernetes; Docker Compose operators should not pay the complexity cost.
---

# arch-01 — App-Buildify Deployment Topology: Monolith and Microservices

> Architectural system design for **how App-Buildify deploys as a modular monolith and as distributed microservices**, covering both topology shapes from a single codebase. Companion to `arch-00-platform` (which covers the platform's internal structure regardless of topology). Epic: "explain the monolithic and microservices that can be implemented."

---

## 1. Context

App-Buildify is a multi-tenant NoCode/LowCode platform built on FastAPI, SQLAlchemy, and Vanilla JS. Its vision (`vision-01-app-buildify`) requires it to run cost-effectively for small teams (single host, one process) and scale horizontally for large organisations (independent module deployments, per-module databases).

ADR-001 established a single environment-variable switch (`DEPLOYMENT_MODE`) that selects between two topology shapes without changing application code. This document presents both shapes at the C4 Container and Component levels, specifies the NFRs each shape must meet, and maps risks and mitigations.

**Audience**: engineers and operators who need to understand what runs where, why, and what to do when a topology changes.

---

## 2. System Context (C4 Level 1)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                            App-Buildify System                                  │
│                                                                                  │
│   ┌──────────────┐    ┌─────────────────────┐    ┌──────────────────────────┐  │
│   │  Browser /   │    │  Core Platform &     │    │  Module Services         │  │
│   │  API client  │◄──►│  API Gateway (Nginx) │◄──►│  (Financial, HR, CRM …)  │  │
│   └──────────────┘    └─────────────────────┘    └──────────────────────────┘  │
│                                  │                            │                  │
│                          ┌───────┴────────┐         ┌────────┴──────────┐       │
│                          │  PostgreSQL     │         │  Redis             │       │
│                          │  (shared host) │         │  (cache/blacklist) │       │
│                          └───────────────┘         └────────────────────┘       │
└────────────────────────────────────────────────────────────────────────────────┘

External systems:
  SMTP server          (Notifications — email delivery)
  SMS gateway          (Notifications — SMS delivery)
  Webhooks             (Outbound event delivery to tenant integrations)
  Sentry               (Optional: error tracking, SENTRY_DSN env)
  Prometheus           (Optional: metrics scraping, ENABLE_METRICS env)
```

---

## 3. Container View — Monolith Mode (C4 Level 2)

`DEPLOYMENT_MODE=monolith` (default). One FastAPI process hosts all domain slices and all enabled module routers. Suitable for: development environments, single-tenant deployments, small multi-tenant deployments (< ~20 tenants, < ~1k daily active users).

```
Browser
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  api-gateway (Nginx)  :80                             │
│  Rate-limit: 100 r/s burst 20                         │
│  Headers forwarded: Authorization, X-Tenant-ID,       │
│                     X-Company-ID, Content-Type        │
└─────────────────────┬────────────────────────────────┘
                      │ all traffic
                      ▼
┌──────────────────────────────────────────────────────┐
│  core-platform  :8000  (FastAPI)                      │
│                                                        │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐             │
│  │ D1       │ │ D2       │ │ D3        │             │
│  │ Identity │ │ Org      │ │ NoCode    │  … D4 D5 D6 │
│  │ & Access │ │          │ │ Platform  │             │
│  └──────────┘ └──────────┘ └───────────┘             │
│                                                        │
│  ┌────────────────────────────────────────────────┐  │
│  │  Module routers (in-process via ModuleLoader)   │  │
│  │  financial router  │  hr router  │  crm router  │  │
│  └────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────┘
                         │
          ┌──────────────┴─────────────┐
          ▼                            ▼
  ┌──────────────────┐      ┌────────────────────┐
  │  postgres :5432  │      │  redis :6379        │
  │  DB: buildify    │      │  JWT blacklist      │
  │  (shared schema) │      │  Widget cache       │
  └──────────────────┘      └────────────────────┘
```

### Nginx routing (monolith)

| Path pattern | Upstream | Notes |
|-------------|----------|-------|
| `/api/v1/financial/*` | `core-platform:8000` | Financial router mounted in-process |
| `/api/v1/*` | `core-platform:8000` | All core routes |
| `/modules/` | filesystem `/app/modules/` | Module frontend assets |
| `/health` | static `200 healthy` | Gateway liveness |
| everything else | frontend static | Served from Nginx or dev server |

### Key properties

- **Process count**: 1 (core-platform) + infra (postgres, redis, nginx)
- **Database**: 1 (`buildify`) — all domain tables, all module tables (name-prefixed)
- **Migration**: core Alembic + per-module Alembic version tables (`financial_alembic_version`) run at startup
- **Module activation**: `ModuleLoader` scans `modules/` directory at boot; enabled modules' routers are included in the FastAPI app
- **Event bus**: used for intra-process async notifications; LISTEN/NOTIFY may still be used for decoupled triggering within the same DB

---

## 4. Container View — Distributed Mode / Microservices (C4 Level 2)

`DEPLOYMENT_MODE=distributed`. Core platform runs domain slices D1–D6. Each module is its own FastAPI service with its own database. Suitable for: multi-team development, large tenants, independent module scaling, fault isolation.

```
Browser
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│  api-gateway (Nginx)  :80/443                                      │
│  Rate-limit: 100 r/s burst 20                                      │
│  Routing: path-based to service containers                         │
└──────┬──────────────────────┬────────────────────┬───────────────┘
       │ /api/v1/*             │ /api/v1/financial/* │ /api/v1/hr/*  …
       ▼                       ▼                     ▼
┌────────────────┐   ┌───────────────────┐   ┌────────────────────┐
│ core-platform  │   │ financial-module  │   │  hr-module         │
│   :8000        │   │   :9001           │   │   :9002            │
│                │   │                   │   │                    │
│ D1 Identity    │   │ Accounts          │   │ Employees          │
│ D2 Org         │   │ Invoices          │   │ Payroll            │
│ D3 NoCode      │   │ Payments          │   │ Leave              │
│ D4 Process     │   │ Journal entries   │   │                    │
│ D5 Insights    │   │ Financial reports │   │                    │
│ D6 Platform    │   │                   │   │                    │
│                │   │ DB: buildify_fin  │   │ DB: buildify_hr    │
└───────┬────────┘   └────────┬──────────┘   └────────┬───────────┘
        │                     │                        │
        └─────────────────────┴────────────────────────┘
                              │
              ┌───────────────┴──────────────┐
              │  postgres :5432               │
              │  DB: buildify (core)          │
              │  DB: buildify_financial       │
              │  DB: buildify_hr              │
              │  (shared host, separate DBs)  │
              └──────────────────────────────┘
              │
              ▼
       ┌────────────────────┐
       │  redis :6379        │
       │  (shared)           │
       │  JWT blacklist      │
       │  Widget cache       │
       └────────────────────┘

Cross-service communication (see ADR-004):
  ══════ Pattern 1 (sync aggregation): core-platform → module service (MODULE_API_KEY)
  ─ ─ ─ Pattern 2 (async events):     any service → postgres event bus → any service
  ······ Pattern 3 (admin/lifecycle):  module → core register endpoint at boot
```

### Nginx routing (distributed)

| Path pattern | Upstream | Notes |
|-------------|----------|-------|
| `/api/v1/financial/*` | `financial-module:9001` | Module's own FastAPI process |
| `/api/v1/hr/*` | `hr-module:9002` | (planned) |
| `/api/v1/crm/*` | `crm-module:9003` | (planned) |
| `/api/v1/*` | `core-platform:8000` | Core platform |
| `/modules/` | filesystem `/app/modules/` | Module frontend assets |
| `/health` | static `200 healthy` | Gateway liveness |
| everything else | frontend static | — |

### Key properties

- **Process count**: 1 core + 1 per enabled module + 3 infra = N+4 containers minimum
- **Database**: 1 host; `buildify` (core) + `buildify_{module}` per module (`DATABASE_STRATEGY=separate`)
- **Migrations**: each service runs its own Alembic at startup against its own DB
- **Auth**: every service validates JWT independently using shared `JWT_SECRET_KEY`
- **Module registration**: each module service calls `POST /api/v1/modules/register` on core at startup with exponential backoff

### Compose profiles

```bash
# Monolith (default)
COMPOSE_PROFILES=monolith docker compose up

# Distributed / microservices
COMPOSE_PROFILES=distributed docker compose up
```

---

## 5. Component View — Core Platform (C4 Level 3)

Applies to both modes. The core-platform FastAPI app is structured in three horizontal tiers and six vertical domain slices.

```
app/main.py  (lifespan: migrate → register modules → conditional in-process mount)
   │
   ├─ D1 Identity & Access
   │    app/routers/{auth, rbac, org}          ← HTTP: auth, RBAC, org mgmt
   │    app/services/{auth, rbac, org, user}   ← Business logic
   │    app/core/{auth, dependencies,          ← Shared facades: get_current_user,
   │              security_middleware,              has_permission, session_manager,
   │              lockout_manager, …}               password_validator
   │
   ├─ D2 Organisation
   │    app/routers/{org, menu}
   │    app/services/{org, menu}
   │
   ├─ D3 NoCode Platform
   │    app/routers/{data_model, data, dynamic_data, builder_pages, lookups, metadata}
   │    app/services/{data_model, dynamic_entity, migration_generator, runtime_model_generator}
   │    app/core/{dynamic_query_builder, model_cache}
   │
   ├─ D4 Process
   │    app/routers/{workflows, automations, scheduler}
   │    app/services/{workflow, automation, scheduler_engine}
   │
   ├─ D5 Insights
   │    app/routers/{dashboards, reports}
   │    app/services/{dashboard, report, report_export}
   │
   └─ D6 Platform Services
        app/routers/{modules, audit, settings, nocode_modules, module_extensions}
        app/core/{notification_service, module_system/*, event_bus/*}
        app/core/audit.py                       ← Shared facade: create_audit_log
        app/core/event_bus/publisher.py         ← Shared facade: publish_event

Cross-cutting (all domains):
   app/core/config.py          Settings(BaseSettings), lru_cache
   app/core/db.py              SQLAlchemy engine, SessionLocal
   app/core/rate_limiter.py    slowapi
   app/core/logging_config.py  structlog + optional Sentry
```

---

## 6. Component View — Module Service (Financial, reference) (C4 Level 3)

```
modules/financial/backend/app/main.py
   │  (lifespan: connect DB → run migrations → register with core → start event subscriber)
   │
   ├─ Routers: accounts, customers, invoices, payments, journal_entries, reports
   ├─ Services: account, invoice, payment, journal, report
   ├─ Models:   financial_accounts, financial_invoices, financial_payments, …
   ├─ Schemas:  Pydantic v2 DTOs
   ├─ Core:
   │    config.py            Settings (DATABASE_STRATEGY, CORE_PLATFORM_URL, MODULE_API_KEY)
   │    db.py                own engine + SessionLocal
   │    auth.py              JWT validation (validates same JWT_SECRET_KEY — no round-trip to core)
   │    event_handler.py     🔴 STUB (lines 43-47) — must become a real EventSubscriber loop
   └─ alembic/               own migrations → financial_alembic_version table
```

The same layout applies to every future module (`hr`, `crm`, `inventory`). The `scripts/create-module.sh` script scaffolds it.

---

## 7. Data Flow

### 7.1 Authentication (both modes)

```
POST /api/auth/login
  → auth.py verify_password (bcrypt)
  → lockout_manager check
  → JWT issue (access 30 min + refresh 7 d, HS256, jti in payload)
  → Redis: record session
  ← {access_token, refresh_token}

Subsequent requests:
  → Nginx forwards Authorization header
  → get_current_user(token) decodes JWT, checks Redis blacklist (jti), verifies tenant_id
  → verify_tenant_access() cross-checks X-Tenant-ID header == JWT tenant_id
  → has_permission(user, "resource:action:scope") checks UserGroup → GroupRole → RolePermission
```

### 7.2 NoCode entity CRUD (both modes)

```
POST /api/v1/data/{entity_name}
  → DynamicEntityService.create(entity_name, data, tenant_id)
  → RuntimeModelGenerator.get_model(entity_name, tenant_id)   [cached in ModelCache]
  → DynamicQueryBuilder.insert(model, data)
  → create_audit_log("data.create", entity_name, …)
  → EventBus.publish("core.entity.created", …)               [consumed by D4 automations]
```

### 7.3 Cross-module dashboard widget (distributed mode)

```
GET /api/v1/dashboards/{id}/render
  → DashboardService.render(dashboard_id, tenant_id)
  → for each widget:
       if widget.source == "financial":
           if WidgetDataCache.hit(widget_id, tenant_id):
               return cached value
           else:
               HTTP GET financial-module:9001/api/v1/financial/summary
               (headers: MODULE_API_KEY, X-Tenant-Id, X-Company-Id, timeout 2s)
               → WidgetDataCache.set(widget_id, tenant_id, result, ttl=300s)
       if widget.source == "nocode_entity":
           DynamicQueryBuilder.aggregate(…)  [local query]
  ← merged dashboard JSON
```

### 7.4 Domain event flow (distributed mode)

```
financial-module: POST /api/v1/financial/invoices/{id}/pay
  → InvoiceService.mark_paid(invoice_id, tenant_id)
  → EventPublisher.publish("financial.invoice.paid", {invoice_id, amount}, tenant_id)
      → INSERT INTO platform_events (type, payload, …)
      → NOTIFY platform_events, '<json>'

core-platform EventSubscriber (running as background task in lifespan):
  → LISTEN platform_events
  → receives notification: event_type="financial.invoice.paid"
  → AutomationService.trigger_by_event("financial.invoice.paid", tenant_id, payload)
  → WorkflowService.start(…) or NotificationService.queue(…)
```

---

## 8. Integration Points

| Integration | Direction | Protocol | Auth | File(s) |
|-------------|-----------|----------|------|---------|
| Module → Core: registration | Module → Core | HTTP POST (internal) | MODULE_API_KEY | `modules/financial/backend/app/main.py:24-79`, `backend/app/routers/modules.py` |
| Core → Module: aggregation query | Core → Module | HTTP GET (internal) | MODULE_API_KEY + user JWT | `backend/app/services/dashboard_service.py`, `infra/nginx/nginx.conf` |
| Core ↔ Module: domain events | Both directions | PostgreSQL LISTEN/NOTIFY | n/a (internal DB) | `backend/app/core/event_bus/`, `modules/financial/backend/app/core/event_handler.py` |
| Module frontend registration | Browser → Nginx → Core | HTTP GET | user JWT | `frontend/assets/js/core/module-system/module-loader.js` |
| Notifications: email | Core → SMTP | SMTP/TLS | SMTP credentials | `backend/app/core/notification_service.py` |
| Notifications: SMS | Core → SMS GW | HTTP | API key | `backend/app/core/notification_service.py` |
| Notifications: webhooks | Core → Tenant endpoint | HTTP POST | HMAC-SHA256 signature | `backend/app/core/notification_service.py` |
| Observability: Sentry | Core → Sentry | HTTPS | DSN | `backend/app/core/logging_config.py` (SENTRY_DSN env) |
| Observability: Prometheus | Scraper → Core | HTTP GET /metrics | none (internal) | `backend/app/main.py` (ENABLE_METRICS env) |

---

## 9. Non-Functional Requirements

### 9.1 Performance

| Metric | Monolith target | Distributed target | Notes |
|--------|----------------|-------------------|-------|
| API p95 latency | < 500 ms | < 500 ms (< 700 ms for aggregated widget) | Per vision-01 §3 metric #4 |
| Dashboard render | < 2 s | < 2 s (with WidgetDataCache) | Cache TTL 300 s |
| Cross-service aggregation timeout | n/a | 2 s hard timeout | Partial response if exceeded |
| Background event processing | n/a | < 5 s from publish to consumer action | LISTEN/NOTIFY is near-real-time; polling fallback adds max 10 s |
| Throughput | Nginx: 100 r/s burst 20 | Same at gateway; each service independently limited | `infra/nginx/nginx.conf` |

### 9.2 Security

| Control | Implementation | File |
|---------|---------------|------|
| Authentication | JWT HS256, access (30 min) + refresh (7 d), JTI revocation via Redis blacklist | `backend/app/core/auth.py` |
| Multi-tenant isolation | JWT-embedded `tenant_id` verified on every request; X-Tenant-ID header cross-checked | `backend/app/core/dependencies.py` |
| Module auth (distributed) | Each module validates JWT independently — no proxy auth through core | `modules/financial/backend/app/core/auth.py` |
| Module-to-core calls | MODULE_API_KEY (service account secret); never a user JWT | `modules/financial/backend/app/config.py` |
| Rate limiting | slowapi (app-level) + Nginx 100 r/s burst 20 (gateway) | `backend/app/core/rate_limiter.py`, `infra/nginx/nginx.conf` |
| CORS | `ALLOWED_ORIGINS` env — **must be restricted to tenant domains before production** (currently `*`) | `backend/app/main.py` |
| Input validation | Pydantic v2 on every router input | `backend/app/schemas/*` |
| Audit logging | `create_audit_log()` on every sensitive mutation | `backend/app/core/audit.py` |
| Secret management | JWT_SECRET_KEY, MODULE_API_KEY via env; no defaults in production | `backend/.env.template` |

### 9.3 Observability

| Capability | Implementation | Notes |
|------------|---------------|-------|
| Structured logging | structlog JSON (all services) | `backend/app/core/logging_config.py` |
| Error tracking | Sentry (optional; SENTRY_DSN env) | Same SDK for core and modules |
| Metrics | Prometheus (optional; ENABLE_METRICS=true) — `/metrics` endpoint | Add Grafana dashboard for multi-service view |
| Health checks | `/api/health` (component checks), `/api/healthz` (liveness) | `backend/app/main.py`; replicate in each module |
| Distributed tracing | **Not implemented** — add W3C TraceContext headers when distributed mode stabilises | Prerequisite for meaningful cross-service latency analysis |

### 9.4 Multi-tenancy

| Layer | Mechanism |
|-------|-----------|
| Data isolation | Shared schema; every query filters `WHERE tenant_id = :tid` (core services); separate DB per module in distributed mode |
| Auth scope | JWT-embedded `tenant_id` verified by `get_current_user()`; X-Tenant-ID cross-checked by `verify_tenant_access()` |
| Module activation | Per-tenant `TenantModule` row; module routes gated by `has_permission()` |
| RBAC scope | Permission strings include scope segment (`resource:action:scope`); scoped to company, branch, or department |

Defense-in-depth gap: no SQLAlchemy session-level `tenant_id` mixin. A missed `WHERE tenant_id` filter in any service = cross-tenant data exposure. Tracked as risk #1 in `arch-platform.md §9`.

### 9.5 Scalability

| Dimension | Monolith path | Distributed path |
|-----------|--------------|-----------------|
| Vertical (single host) | Increase container CPU/memory | Same per service |
| Horizontal (stateless) | Multiple core-platform replicas behind Nginx upstream | Multiple replicas per service; Redis and Postgres are shared infrastructure |
| Module isolation | All modules share the core process; one misbehaving module can degrade others | Each module is a separate process; faults are isolated |
| Database | Shared schema; optimise with indexes and read replicas | Per-module DB; each scales independently |
| Session state | Redis-backed (stateless HTTP) | Same Redis cluster, shared across all services |

---

## 10. Risks

| 🚦 | Risk | Mode | Mitigation | Source |
|----|------|------|-----------|--------|
| 🔴 | Event bus subscriber stub in financial module — distributed mode not production-ready | Distributed | Replace `modules/financial/backend/app/core/event_handler.py:43-47` with real `EventSubscriber` loop | `arch-platform.md §9 risk #14` |
| 🔴 | CORS `*` at both gateway and FastAPI in production — any origin can access the API | Both | Set `ALLOWED_ORIGINS` to tenant domain list before production rollout | `arch-platform.md §9 risk #4` |
| 🔴 | JWT_SECRET_KEY literal default in `docker-compose.yml` — must be rotated before any production deployment | Both | Remove default from compose file; require secret from vault or env injection | `arch-platform.md §9 risk #5` |
| 🔴 | No CI/CD pipeline — distributed mode adds N+4 containers with no automated integration test | Both | Epic 19; add GitHub Actions with `DEPLOYMENT_MODE=distributed` integration test matrix | `arch-platform.md §9 risk #7` |
| 🟡 | Tenant isolation relies on per-service `tenant_id` filters only — no SQLAlchemy session-level guard | Both | Add SQLAlchemy event listener or PostgreSQL RLS as defense-in-depth (ADR opportunity) | `arch-platform.md §9 risk #1` |
| 🟡 | Symmetric JWT (HS256) requires all module services to hold the same secret — rotation is disruptive | Distributed | Future ADR for RS256 (asymmetric): core holds private key; modules hold public key | ADR-003 consequences |
| 🟡 | Port allocation for modules is manual (financial=9001 hardcoded) — breaks at module N+1 | Distributed | Add `service.port` to `manifest.json`; validate in `backend/validate_module_manifest.py` | ADR-003 §implementation |
| 🟡 | Dashboard aggregation latency in distributed mode — live module calls add network hop | Distributed | WidgetDataCache (TTL 300 s) already exists; populate proactively via event bus subscription | ADR-004 Pattern 1 |
| 🟡 | No distributed tracing — cross-service latency invisible without TraceContext propagation | Distributed | Add W3C `traceparent` header forwarding in Nginx and `apiFetch`; integrate OpenTelemetry | §9.3 observability |

---

## 11. Reference Map

| Area | Path |
|------|------|
| Deployment switch | `backend/app/core/config.py` (`DEPLOYMENT_MODE` setting) |
| In-process mount guard | `backend/app/main.py:70-76` |
| Module loader | `backend/app/core/module_system/loader.py` |
| BaseModule ABC | `backend/app/core/module_system/base_module.py` |
| Module registry service | `backend/app/core/module_system/registry.py` |
| Financial module main | `modules/financial/backend/app/main.py` |
| Financial manifest | `modules/financial/manifest.json` |
| Event bus publisher | `backend/app/core/event_bus/publisher.py` |
| Event bus subscriber | `backend/app/core/event_bus/subscriber.py` |
| Event handler stub (🔴) | `modules/financial/backend/app/core/event_handler.py:43-47` |
| Cross-domain facades (D1) | `backend/app/core/dependencies.py` |
| Audit facade (D6) | `backend/app/core/audit.py` |
| Dashboard widget cache | `backend/app/services/dashboard_service.py` (WidgetDataCache) |
| Nginx gateway config | `infra/nginx/nginx.conf` |
| Compose (dev) | `docker-compose.yml` |
| Compose (prod) | `infra/docker-compose.prod.yml` |
| Module scaffold script | `scripts/create-module.sh` |
| Module manifest validator | `backend/validate_module_manifest.py` |
| ADR-001 (deployment modes) | `plan/architecture/adr-001-deployment-modes.md` |
| ADR-002 (monolith boundaries) | `plan/architecture/adr-002-monolith-service-boundaries.md` |
| ADR-003 (microservices decomposition) | `plan/architecture/adr-003-microservices-decomposition.md` |
| ADR-004 (inter-service comms) | `plan/architecture/adr-004-inter-service-communication.md` |

---

## Hand-off

Status: **review**. Downstream agents may proceed in parallel:

- **B2 (Data Modeler)**: design the `platform_events` table schema (event bus), `service_registry` table (distributed port/host allocation), and `TenantModule` extensions for distributed mode.
- **C1 (Task Decomposer)**: decompose into implementation tasks: (1) event bus stub fix, (2) manifest `service.port` field + validator update, (3) Compose profile `distributed`, (4) Nginx template for new module locations, (5) WidgetDataCache proactive population.
- **C2 / C3 (Implementers)**: implement tasks as decomposed by C1.
- **D3 (Security Reviewer)**: review this arch against the OWASP Top 10 and the multi-tenancy isolation risk (§10); flag any new concerns before implementation starts.
