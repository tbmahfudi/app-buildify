---
artifact_id: arch-23
type: arch
producer: B1 Software Architect
consumers: [B2 Data Engineer, C1 Tech Lead, C2 Backend Developer, C3 Frontend Developer, D3 Security Engineer]
upstream: [epic-23-module-lifecycle-and-activation, vision-03-module-lifecycle-and-activation, research-03-module-lifecycle-and-activation]
downstream: []
status: approved
created: 2026-06-18
updated: 2026-06-18
---

# Architecture — Epic 23: Module Lifecycle & Activation (arch-23)

---

## 1. Context

App-Buildify is a SaaS platform where the operator (platform developer) builds and deploys modules; tenant and company administrators activate them. This epic delivers:

1. A developer-side **packaging and install pipeline** (`manage.sh module pack` / `manage.sh module install`) that deploys a sealed tarball to production atomically.
2. A tenant-side **activation layer** that lets admins enable/disable installed modules through a UI with a pre-activation permissions summary.

**Existing code this epic builds on** (all in `backend/app/`):
- `models/nocode_module.py` — `Module` and `ModuleActivation` models (already unified; rich schema)
- `routers/modules.py` — activation endpoints exist at `/install`, `/enable`, `/disable` (not `/activate`)
- `core/module_system/base_module.py` — `BaseModule` with `post_install()` / `post_enable()` hooks (not wired)
- `core/module_system/loader.py` — manifest loading and registration
- `alembic/versions/postgresql/pg_unify_module_system.py` — current head revision

---

## 2. Lifecycle State Machine

```
                     manage.sh install
                           │
                    ┌──────▼──────┐
                    │  in_progress│  (Module.install_status)
                    └──────┬──────┘
               success     │     failure
          ┌────────────────┤     ├─────────────┐
          ▼                │     │             ▼
     ┌─────────┐           │     │       ┌──────────┐
     │  ready  │◄──────────┘     └──────►│  failed  │ (rollback applied)
     └────┬────┘                         └──────────┘
          │  tenant/company admin
          │  POST /modules/{id}/enable
          ▼
    ┌──────────┐    POST /modules/{id}/disable    ┌──────────┐
    │  active  │◄────────────────────────────────►│ inactive │
    └──────────┘                                  └──────────┘
          │  operator: POST /admin/modules/{id}/deactivate-all
          ▼
  ┌───────────────────┐
  │ deactivation_pend │  (all tenants deactivated)
  └────────┬──────────┘
           │  operator: DELETE /admin/modules/{id}
           ▼
      ┌──────────┐
      │uninstalled│  (row deleted)
      └──────────┘
```

State is stored in `Module.install_status` (new column, see schema-23). Activation state is `ModuleActivation.is_enabled`.

---

## 3. Components

### 3.1 Developer Pipeline (CLI)

```
manage.sh module pack <dir> [--out <dir>]
    └── validates manifest (POST /api/v1/modules/validate)
    └── bundles: backend/ + frontend/ + manifest.json + migrations/ + install.sh
    └── produces: <name>_<version>.tar.gz + SHA256SUMS

manage.sh module install <tarball>
    └── verifies SHA256
    └── validates manifest
    └── sets Module.install_status = in_progress
    └── runs Alembic migrations (module's own alembic env)
    └── copies backend service → modules/<name>/backend/
    └── copies frontend assets → frontend/assets/modules/<name>/
    └── calls POST /api/v1/modules/register (idempotent)
    └── calls BaseModule.post_install(db_session)
    └── sets Module.install_status = ready
    └── on any failure → rollback steps in reverse + install_status = failed

manage.sh module uninstall <name>
    └── Phase 1: POST /api/v1/admin/modules/{id}/deactivate-all (with confirmation prompt)
    └── Phase 2: DELETE /api/v1/admin/modules/{id} (X-Confirm-Uninstall: true)
```

The `manage.sh` commands are bash scripts that call the platform API and run local filesystem operations. They do not embed business logic — the API is the source of truth.

### 3.2 API Layer (`backend/app/routers/modules.py`)

| Endpoint | Actor | Purpose |
|---|---|---|
| `POST /api/v1/modules/validate` | Developer CLI | Dry-run manifest validation; no DB write |
| `POST /api/v1/modules/register` | Developer CLI (via install) | Register or update module in `modules` table |
| `GET /api/v1/modules` | Tenant admin | List installed modules with tenant's `activation_status` |
| `GET /api/v1/modules/{id}/activation-preview` | Frontend | Returns permissions + menu items + dependency status |
| `POST /api/v1/modules/{id}/enable` | Tenant admin | Activate module for requesting tenant |
| `POST /api/v1/modules/{id}/disable` | Tenant admin | Deactivate module for requesting tenant |
| `POST /api/v1/admin/modules/{id}/deactivate-all` | Superadmin | Deactivate across all tenants (phase 1 of uninstall) |
| `DELETE /api/v1/admin/modules/{id}` | Superadmin | Hard removal (phase 2 of uninstall) |

### 3.3 Manifest Schema Validation (`backend/app/core/module_system/manifest.schema.json`)

New JSON Schema file. `POST /api/v1/modules/validate` and the install pipeline both call `jsonschema.validate(manifest, schema)`. Returns `{valid: true}` or `{valid: false, errors: [{field, message}]}`.

### 3.4 BaseModule Hook Wiring (`backend/app/core/module_system/loader.py`)

`post_install()` is called synchronously by `manage.sh module install` after registration succeeds (within the same DB session passed by the install script). `post_enable()` is called by `POST /api/v1/modules/{id}/enable` after the `ModuleActivation` row is created. Both are wrapped in try/except — a hook failure logs an error and writes `audit_logs` but does NOT roll back the install/enable (hooks are best-effort init helpers, not required preconditions).

**Spike decision**: the existing `base_module.py` hooks are plain Python method calls — they do not use the event bus. The loader calls them directly. No event bus needed for this scope. The spike in story 23.3.2 confirms this; the event bus is a future concern for distributed mode.

### 3.5 Menu + RBAC Integration on Enable/Disable

`POST /modules/{id}/enable`:
1. Read `Module.manifest.menu_items` — merge into the tenant's menu tree (existing menu service)
2. Read `Module.manifest.permissions` — seed `Permission` rows scoped to the tenant (existing RBAC service)
3. Create `ModuleActivation` row with `is_enabled=True`

`POST /modules/{id}/disable`:
1. Remove module menu items from tenant's menu tree
2. Set `Permission.is_active=False` for the module's seeded permissions in this tenant
3. Update `ModuleActivation.is_enabled=False`

Data written by the module (entity records, etc.) is NOT touched on disable.

---

## 4. Data Flow — Install Pipeline

```
Developer                    manage.sh               Platform API              Database
────────────────────────────────────────────────────────────────────────────────────────
git tag v1.2.0
                     module pack ./financial_module
                             │
                             ├─ POST /modules/validate ──────────────► validates manifest schema
                             │                        ◄──────────────  {valid: true}
                             └─ produces financial_1.2.0.tar.gz + SHA256SUMS

                     module install financial_1.2.0.tar.gz
                             │
                             ├─ verify SHA256 (local)
                             ├─ POST /modules/validate ──────────────►
                             ├─ SET install_status=in_progress ──────► modules table
                             ├─ alembic upgrade head (module env) ───► module DB tables
                             ├─ copy backend/ → modules/financial/
                             ├─ copy frontend/ → assets/modules/
                             ├─ POST /modules/register ──────────────► modules row upsert
                             ├─ BaseModule.post_install(db) ─────────► (seed data etc.)
                             └─ SET install_status=ready ────────────► modules table
```

---

## 5. Data Flow — Tenant Activation

```
Tenant Admin                 Frontend                 API                       Database
────────────────────────────────────────────────────────────────────────────────────────
                  GET /modules ──────────────────────────────────────────► modules + activations
                               ◄─────────────────────────────────────────  [{...activation_status}]
Modules page renders

click "Activate"
                  GET /modules/{id}/activation-preview ──────────────────►
                               ◄─────────────────────────────────────────  {permissions, menu_items, deps}
ActivationModal renders

click "Confirm"
                  POST /modules/{id}/enable ─────────────────────────────► check deps (409 if unmet)
                                                                          ► merge menu items
                                                                          ► seed RBAC permissions
                                                                          ► INSERT module_activations (is_enabled=True)
                                                                          ► audit_logs (module.enabled)
                               ◄─────────────────────────────────────────  {status: "active", ...}
Nav updates live
```

---

## 6. Integration Points

| Integration | Epic 23 behaviour | Existing code |
|---|---|---|
| **RBAC permission seeding** | `enable` seeds `Module.manifest.permissions` as Permission rows | `backend/app/routers/rbac.py`, `backend/app/services/rbac_service.py` |
| **Menu service** | `enable`/`disable` adds/removes menu items | `backend/app/services/menu_service.py` |
| **Alembic (module)** | `install` runs module's own Alembic env | `modules/<name>/backend/alembic/` per `modules/MODULE_ALEMBIC_SETUP.md` |
| **Epic 22 cleanup service** | `uninstall` phase 2 calls `cleanup_tenant_module_dbs(module_id=..., scope="module")` | epic-22 story 22.4.5 (must coordinate with B1-22) |
| **Audit log** | Every state transition writes `audit_logs` | `backend/app/services/audit_service.py create_audit_log()` |

---

## 7. NFRs

| Category | Requirement | How met |
|---|---|---|
| **Performance** | `POST /enable` completes in < 2 s (menu merge + RBAC seed) | Seed is a bulk insert; menu merge is in-memory tree op |
| **Atomicity** | `manage.sh module install` rolls back on failure | Steps tracked in `install_status`; rollback reverses in order |
| **Security** | Only superadmin can `register`, `deactivate-all`, or `DELETE` module | Existing `require_permission("modules:*:platform")` guard |
| **Observability** | Every lifecycle event in `audit_logs` | `create_audit_log()` called at every state transition |
| **Multi-tenancy** | `enable`/`disable` is scoped to `current_user.tenant_id` from JWT | Never trusts request body for tenant_id |
| **Idempotency** | Re-running `install` on same version is a no-op | Checked by `name + version` uniqueness before any write |

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Epic 22 cleanup service not ready when uninstall is implemented | Make cleanup a feature flag in `manage.sh uninstall`; fall back to manual DB cleanup steps if epic-22 story 22.4.5 is not merged yet |
| `post_install` hook raises an unhandled exception | Wrap in try/except; log + audit; do not roll back the install |
| Menu merge produces duplicates if enable is called twice | `ModuleActivation` unique constraint `(module_id, tenant_id, company_id=null, ...)` prevents double-enable at DB level |
| Large manifest (100+ permissions) makes `/activation-preview` slow | Pre-compute preview and cache on `Module` registration; invalidate on re-register |

---

## 9. Reference Map

| Concern | File(s) |
|---|---|
| Module model | `backend/app/models/nocode_module.py` — `Module`, `ModuleActivation` |
| Activation endpoints | `backend/app/routers/modules.py` |
| Manifest loading | `backend/app/core/module_system/loader.py` |
| BaseModule hooks | `backend/app/core/module_system/base_module.py` |
| Existing Alembic head | `backend/app/alembic/versions/postgresql/pg_unify_module_system.py` |
| Module Alembic convention | `modules/MODULE_ALEMBIC_SETUP.md` |
| Menu service | `backend/app/services/menu_service.py` |
| RBAC service | `backend/app/services/rbac_service.py` |
| Audit service | `backend/app/services/audit_service.py` |
| manage.sh | `manage.sh` (root) |
| Epic 22 cleanup | epic-22 story 22.4.5 (not yet implemented) |
