---
artifact_id: adr-002
type: adr
producer: Software Architect (B1)
consumers: [Backend Engineer, Tech Lead, C1, C2, C3, D3]
upstream: [arch-platform, adr-001-deployment-modes, epic-11-module-system, epic-19-infrastructure-deployment]
downstream: [arch-01-deployment-topology]
status: Proposed
created: 2026-05-03
updated: 2026-05-03
---

# ADR-002 — Monolith: Service Boundary Definitions

## Status

Proposed.

## Context

ADR-001 established that `DEPLOYMENT_MODE=monolith` runs every module's router in-process inside the core-platform FastAPI application. That decision left unanswered a finer-grained question: **within the monolith, where do domain boundaries live, and what rules govern what may cross them?**

Without explicit boundaries, the monolith degrades into a big ball of mud: services import each other arbitrarily, cross-domain queries bypass the service layer, and the codebase becomes impossible to decompose later when `DEPLOYMENT_MODE=distributed` is needed.

The current codebase already exhibits boundary pressure:

- `backend/app/routers/` contains 20+ router modules that import from `backend/app/services/` — a clean horizontal boundary.
- `backend/app/services/` occasionally imports sibling services directly (e.g. `DashboardService` imports `ReportService`) rather than going through an event or a shared repository.
- The financial module at `modules/financial/backend/` is a separate process in production (`docker-compose.yml`) but is also imported in-process via `ModuleLoader` during monolith boots — creating an implicit double-boundary.
- `backend/app/core/module_system/base_module.py` defines the `BaseModule` ABC as the official inter-domain contract, but core services do not systematically honour it: they may call module services directly during tests.

The C4 Component-level boundaries for the monolith need to be stated explicitly so engineers know:
1. Which domains exist.
2. What may cross a domain boundary and how.
3. What is forbidden.

## Decision

Define **six vertical domain slices** inside the monolith, each owning its own routers, services, models, and schemas. Cross-domain calls are permitted only through two sanctioned channels: **shared service interfaces** (Python function calls on a published facade) and the **event bus** (PostgreSQL LISTEN/NOTIFY, `backend/app/core/event_bus/`). Direct model imports across domain boundaries are forbidden.

### Domain slices

| # | Domain | Owns | Entry point(s) |
|---|--------|------|----------------|
| D1 | **Identity & Access** | Auth, RBAC, Users, Groups, Roles, Permissions, Session, Password, Lockout | `app/routers/auth.py`, `app/routers/rbac.py`, `app/routers/org.py` |
| D2 | **Organisation** | Tenant, Company, Branch, Department, Menu | `app/routers/org.py`, `app/routers/menu.py` |
| D3 | **NoCode Platform** | Entity Designer, Data Model, Dynamic CRUD, Dynamic Query, Lookups, Builder Pages | `app/routers/data_model.py`, `app/routers/data.py`, `app/routers/dynamic_data.py`, `app/routers/builder_pages.py`, `app/routers/lookups.py` |
| D4 | **Process** | Workflow Engine, Automation Rules, Scheduler | `app/routers/workflows.py`, `app/routers/automations.py`, `app/routers/scheduler.py` |
| D5 | **Insights** | Dashboards, Reports, Analytics | `app/routers/dashboards.py`, `app/routers/reports.py` |
| D6 | **Platform Services** | Module System, Notifications, Audit, Settings, i18n, Developer SDK | `app/routers/modules.py`, `app/routers/audit.py`, `app/routers/settings.py`, `app/core/notification_service.py` |

Modules (e.g. Financial) are **not** a domain slice inside core — they are boundary-isolated guests registered via D6 (Module System). Their code lives in `modules/<name>/` and is mounted by `ModuleLoader`; they may **call** D1 for auth and D3 for entity resolution, but core domain slices may **not** import module code.

### Boundary rules

```
ALLOWED:
  Router (Dx) → Service (Dx)           # same domain, always ok
  Service (Dx) → Repository / ORM (Dx) # same domain, always ok
  Service (Dx) → SharedFacade (Dy)     # cross-domain, published interface only
  Service (Dx) → EventBus.publish()    # cross-domain async notification
  Module → SharedFacade (D1, D3)       # module may call identity + nocode facades

FORBIDDEN:
  Service (Dx) → Model (Dy)            # no cross-domain ORM import
  Module code → any app/models/*.py    # modules resolve via API or facade, not ORM
  Router (Dx) → Service (Dy) directly  # router never bypasses its own domain service
```

### Published shared facades

Minimal set; expand only with an ADR:

| Facade | Provided by | Consumed by |
|--------|-------------|-------------|
| `get_current_user(token)` | D1 | All domains (via FastAPI Depends) |
| `has_permission(user, perm)` | D1 | All domains (via FastAPI Depends) |
| `get_entity_definition(name, tenant_id)` | D3 | D4 (Workflow), D5 (Reports/Dashboards), modules |
| `create_audit_log(...)` | D6 | All domains |
| `publish_event(type, payload)` | D6/EventBus | D4 (triggers), modules |

These facades already exist in `app/core/dependencies.py` (D1), `app/services/data_model_service.py` (D3), and `app/core/audit.py` (D6). The ADR formalises them as the **only** cross-domain call sites.

### Enforcement

- Module boundaries are enforced at import time: `ModuleLoader` (`backend/app/core/module_system/loader.py`) must not expose core ORM models to modules.
- A linting rule (e.g. `import-linter` or custom `flake8` plugin) should enforce that `modules/*/` never imports from `backend/app/models/` or `backend/app/services/`. Add to CI when Epic 19 lands.
- Cross-domain service-to-service calls that are not via a published facade should fail code review (checked by D2 agent in each PR).

## Consequences

### Positive

- **Composability**: any domain slice can be extracted to a standalone service when `DEPLOYMENT_MODE=distributed` without touching the other slices.
- **Testability**: each domain slice can be unit-tested with mocks at the facade boundary.
- **Onboarding clarity**: a new engineer can read one domain slice without needing to understand the whole codebase.

### Negative

- **Facade maintenance**: published facades are a contract; changes require review (mitigated by the ADR process).
- **Some refactoring required now**: `DashboardService` imports `ReportService` directly — this must be converted to a facade call or event. Not a large change but not zero cost.
- **Event latency**: async cross-domain notifications (EventBus) are not synchronous; workflows that need an immediate cross-domain result must use a facade, not an event.

## Alternatives considered

- **No explicit boundaries (status quo)**: any service imports any other. Rejected — the codebase is already large enough that this causes merge conflicts and cross-domain bugs.
- **Package-level isolation (separate Python packages per domain)**: enforced by pip — strongest isolation but very high refactoring cost for the current layout. Deferred until the codebase has matured.
- **Hexagonal / ports-and-adapters per domain**: introduces abstract interfaces for every interaction. Overkill for a team of this size; the facade approach achieves 80% of the benefit.

## Related artifacts

- `plan/architecture/arch-platform.md` — platform topology this ADR refines.
- `plan/architecture/adr-001-deployment-modes.md` — deployment mode switch that makes these boundaries load-bearing.
- `plan/architecture/arch-01-deployment-topology.md` — system-level view referencing both modes.
- `backend/app/core/module_system/base_module.py` — BaseModule ABC (the module ↔ core boundary).
- `backend/app/core/dependencies.py` — D1 published facades (`get_current_user`, `has_permission`).
- `backend/app/core/audit.py` — D6 published facade (`create_audit_log`).
- `backend/app/core/event_bus/publisher.py` — EventBus publish facade.
