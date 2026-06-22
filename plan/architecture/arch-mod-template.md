# Architecture: Module Template Scaffold (B1)

**Level:** L2 Container / L3 Component
**C4 Context:** App-Buildify Platform — Module System
**Date:** 2026-06-20
**Status:** Accepted

---

## 1. Context

App-Buildify ships a zero-to-module scaffold (`modules/template/`) so that
module authors start with working, idiomatic code rather than a blank slate.
The scaffold enforces the platform's core constraint: **modules must never
import directly from `backend.app`**. Instead they consume a versioned,
stable SDK surface (`modules/sdk/`).

This document covers the B1 milestone additions:
- Two new SDK re-export modules (`sdk/db.py`, `sdk/dependencies.py`)
- A complete, runnable TEMPLATE module (models, schemas, routes, frontend)
- The ADR that governs the SDK surface expansion

---

## 2. Components

### 2.1 SDK Layer (`modules/sdk/`)

| File | Responsibility |
|---|---|
| `db.py` | Re-exports `Base`, `GUID`, `generate_uuid` from `backend.app.models.base` |
| `dependencies.py` | Re-exports `tenant_scoped_session`, `get_current_user`, `has_permission` from `backend.app.core.dependencies` |
| `__init__.py` | Aggregates all public SDK names into a single import namespace |

The SDK layer acts as an **Anti-Corruption Layer (ACL)**. Platform internals
can be refactored without touching module code, as long as SDK re-exports are
kept in sync.

### 2.2 Backend Pattern (`modules/template/`)

```
models.py    — SQLAlchemy model; inherits Base from sdk.db
schemas.py   — Pydantic v2 request/response models
routes.py    — FastAPI APIRouter with full CRUD; uses sdk.dependencies
```

All routes are tenant-scoped by construction: `tenant_scoped_session` injects
a DB session pre-filtered to the current tenant; `has_permission` enforces
RBAC before any DB access.

### 2.3 Frontend Pattern (`modules/template/frontend/module.js`)

- ES Module exporting a single `init(container)` entry point
- All API calls via `window.apiFetch` (platform-injected, handles
  `Authorization` and `X-Tenant-ID` headers automatically)
- UI built from `<flex-datagrid>` and `<flex-button>` web components
- Zero hardcoded colours — all CSS from platform variables

---

## 3. Data Flow

```
Browser                     Platform Router          Module Backend
──────                      ───────────────          ──────────────
init(container)
  │
  └─► window.apiFetch ──► GET /api/v1/modules/TEMPLATE/items
                                │
                          has_permission("TEMPLATE:read")
                                │
                          tenant_scoped_session ──► DB (tenant-filtered)
                                │
                          TEMPLATEItem.query()
                                │
                          ItemListResponse ◄──────────────────────┘
  ◄── JSON ──────────────────────┘
  │
renderGrid(items)
  └─► <flex-datagrid rows="...">
```

---

## 4. Integration Points

| Point | Detail |
|---|---|
| Module loader | Platform discovers modules via `modules/<name>/manifest.json`; mounts `routes.router` into the main FastAPI app |
| Auth | `get_current_user` validates JWT; `has_permission` checks tenant RBAC table |
| Multi-tenancy | `tenant_scoped_session` wraps SQLAlchemy session with a `TenantScopeListener` that appends `WHERE tenant_id = :tid` to all queries |
| Frontend mount | Platform SPA imports `modules/template/frontend/module.js` and calls `init(container)` on route activation |
| Component library | `flex-datagrid`, `flex-button` loaded globally by the platform shell |

---

## 5. Non-Functional Requirements

| NFR | Approach |
|---|---|
| Isolation | Modules cannot reach `backend.app` internals; enforced by linting rule and SDK ACL |
| Tenant safety | `__tenant_scoped__ = True` on every model triggers automatic row filtering |
| Pagination | All list endpoints accept `page` / `page_size`; default 25, max 100 |
| Observability | Standard FastAPI request logging; module prefix in route tags for easy filtering |

---

## 6. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| SDK drift (platform refactors `backend.app`, SDK re-exports not updated) | Medium | SDK has its own test suite; CI checks import paths |
| Module author bypasses SDK | Low | Linting rule `no-direct-backend-import`; CI gate |
| `TEMPLATEItem` table name collision | Low | Authors must rename `__tablename__` before shipping |

---

## 7. Reference Map

| Artifact | Path |
|---|---|
| SDK database re-exports | `modules/sdk/db.py` |
| SDK dependency re-exports | `modules/sdk/dependencies.py` |
| SDK public API | `modules/sdk/__init__.py` |
| Template model | `modules/template/models.py` |
| Template schemas | `modules/template/schemas.py` |
| Template routes | `modules/template/routes.py` |
| Template frontend | `modules/template/frontend/module.js` |
| This document | `plan/architecture/arch-mod-template.md` |
| Governing ADR | `plan/architecture/adr-006-sdk-surface-db-and-dependencies.md` |
| Platform base model | `backend/app/models/base.py` |
| Platform dependencies | `backend/app/core/dependencies.py` |
