# Module API — Canonical Lifecycle Paths

> **T-23.001** — Audit document + decision note for Epic 23 (Module Lifecycle & Activation).
> Author: C2 Backend Developer · Date: 2026-06-25

---

## 1. Current Endpoint Surface

### 1.1 Router: `/api/v1/module-registry` (`backend/app/routers/modules.py`)

All module_name values are passed in the **request body**, not as path parameters.

| Method | Path | Auth | Request Body | Response Schema | Notes |
|--------|------|------|-------------|-----------------|-------|
| GET | `/api/v1/module-registry/available` | `get_current_user` | — | `AvailableModulesResponse` (`{modules: ModuleListItem[], total: int}`) | Lists all ModuleRegistry rows |
| GET | `/api/v1/module-registry/enabled` | `get_current_user` | — | `EnabledModulesResponse` (`{modules: TenantModuleInfo[], total: int}`) | Filtered to current tenant; joins TenantModule where is_enabled=True AND is_installed=True |
| GET | `/api/v1/module-registry/enabled/names` | `get_current_user` | — | `List[str]` | Thin helper: enabled module name strings for the current tenant |
| GET | `/api/v1/module-registry/enabled/all-tenants` | `require_superuser` | — | `AllTenantsModulesResponse` | Superuser only; cross-tenant view |
| GET | `/api/v1/module-registry/{module_name}` | `get_current_user` | — | `ModuleInfo` | Full detail by name; 404 if not found |
| GET | `/api/v1/module-registry/{module_name}/manifest` | `get_current_user` | — | Raw manifest JSON | Proxies to module backend service; falls back to DB |
| POST | `/api/v1/module-registry/install` | `require_superuser` | `{module_name: str}` | `ModuleOperationResponse` | Calls registry.install_module(); writes audit log |
| POST | `/api/v1/module-registry/uninstall` | `require_superuser` | `{module_name: str}` | `ModuleOperationResponse` | Calls registry.uninstall_module(); writes audit log |
| POST | `/api/v1/module-registry/enable` | `get_current_user` | `{module_name, tenant_id?, configuration?}` | `ModuleOperationResponse` | Enables for current or target tenant (superuser for other tenants); writes audit log |
| POST | `/api/v1/module-registry/disable` | `get_current_user` | `{module_name: str}` | `ModuleOperationResponse` | Disables for current tenant; writes audit log |
| PUT | `/api/v1/module-registry/{module_name}/configuration` | `get_current_user` | `{configuration: dict}` | `ModuleOperationResponse` | Updates tenant-level config; validates via module_instance.validate_configuration() |
| POST | `/api/v1/module-registry/register` | **No auth** | `{manifest: dict, backend_service_url: str}` | `ModuleRegistrationResponse` | Called by modules at startup; upserts ModuleRegistry row; calls post_install hook; validates manifest schema (T-23.007) |
| POST | `/api/v1/module-registry/{module_name}/heartbeat` | **No auth** | `{version?, status?}` | `ModuleHeartbeatResponse` | Updates updated_at; version change is logged |
| POST | `/api/v1/module-registry/sync` | `require_superuser` | — | `ModuleOperationResponse` | Filesystem to DB sync |

### 1.2 Router: `/api/v1/modules` (`_modules_v1_router` in same file)

Stub router added for Epic 22 story 22.4.2.

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/api/v1/modules/{module_id}/provisioning-status` | `get_current_user` | Polls `tenant_module_databases` table; returns `{status, db_name, error_message}` |

---

## 2. Data Model Summary

### `Module` (aliased as `ModuleRegistry` via shim in `module_registry.py`)

- **Table**: `modules`
- **Key fields**:
  - `id` (UUID PK), `name` (unique slug), `display_name`, `version`
  - `module_type`: `code | nocode | hybrid`
  - `status`: `available | stable | beta | deprecated` (code) or `draft | active | deprecated | archived` (nocode)
  - `is_installed` (bool), `is_core` (bool — core modules cannot be disabled)
  - `install_status` (T-23.017 column): `ready | in_progress | failed | deactivation_pending`
  - `visibility` (T-23.017 column): `all_tenants | whitelist`
  - `install_error_message`, `manifest` (JSON), `dependencies_json` (JSON), `permissions` (JSON)
  - `api_prefix`, `subscription_tier`

### `ModuleActivation` (aliased as `TenantModule`)

- **Table**: `module_activations`
- **Key fields**:
  - `id`, `module_id` (FK), `tenant_id` (FK), `company_id?`, `branch_id?`, `department_id?`
  - `is_enabled` (bool), `is_configured` (bool)
  - `configuration` (JSON), `enabled_features`, `disabled_features`
  - `enabled_at`, `enabled_by_user_id`, `disabled_at`, `disabled_by_user_id`
  - `last_used_at`

---

## 3. Canonical Lifecycle State Machine (Epic 23 Spec)

```
                        [registered]
                             |
              POST /api/v1/module-registry/register
                             |
                        [installed]
                    (install_status=ready)
                             |
              POST /api/v1/modules/{id}/enable
                             |
                          [active]
              (ModuleActivation.is_enabled=True)
                             |
              POST /api/v1/modules/{id}/disable
                             |
                         [inactive]
              (ModuleActivation.is_enabled=False)
                             |
               can re-enable (back to active)
                             |
      POST /api/v1/admin/modules/{id}/deactivate-all
                             |
                   [deactivation_pending]
                 (Module.install_status changed)
                             |
         DELETE /api/v1/admin/modules/{id}
         (header: X-Confirm-Uninstall: true)
                             |
                       [uninstalled]
                     (Module row deleted)
```

State transitions:

| From | To | Trigger | Who |
|------|----|---------|-----|
| — | registered | `POST /module-registry/register` | Module service (no auth) |
| registered | installed | `POST /module-registry/install` or auto on register | Superadmin / module startup |
| installed | active | `POST /modules/{id}/enable` | Tenant admin |
| active | inactive | `POST /modules/{id}/disable` | Tenant admin |
| inactive | active | `POST /modules/{id}/enable` | Tenant admin (re-enable) |
| installed/active/inactive | deactivation_pending | `POST /admin/modules/{id}/deactivate-all` | Superadmin |
| deactivation_pending | uninstalled | `DELETE /admin/modules/{id}` | Superadmin |

---

## 4. Gap Analysis: Current vs Epic 23 Spec

### 4.1 Path Structure

| Epic 23 Spec | Current Reality | Gap |
|-------------|----------------|-----|
| `GET /api/v1/modules` with `activation_status` per tenant | `GET /api/v1/module-registry/available` (no activation_status field) | Missing field — no per-tenant activation join |
| `GET /api/v1/modules/{id}/activation-preview` | Does not exist | Missing endpoint |
| `POST /api/v1/modules/{id}/enable` | `POST /api/v1/module-registry/enable` (body: module_name) | Path prefix mismatch; body vs path param; slug vs UUID |
| `POST /api/v1/modules/{id}/disable` | `POST /api/v1/module-registry/disable` (body: module_name) | Path prefix mismatch; body vs path param; slug vs UUID |
| `POST /api/v1/admin/modules/{id}/deactivate-all` | Does not exist | Missing endpoint |
| `DELETE /api/v1/admin/modules/{id}` | `POST /api/v1/module-registry/uninstall` (body, no header guard) | Wrong HTTP method; wrong prefix; no X-Confirm-Uninstall header; no phase-gate check |

### 4.2 Identifier: UUID `{id}` vs string `{module_name}`

- Epic 23 spec uses `{id}` (UUID) in all path parameters.
- Current router uses `{module_name}` (string slug) everywhere — path params and body.
- Impact: Frontend must carry UUID to call new endpoints. Old endpoints continue to accept slugs.

### 4.3 Dependency + Dependents Checking

- **Spec**: `POST /modules/{id}/enable` returns 409 `{code: "dependencies_unmet", missing: [...]}` when required deps not active.
- **Spec**: `POST /modules/{id}/disable` returns 409 `{code: "dependents_active", dependents: [...]}` when other active modules depend on this one.
- **Current**: Neither check exists. Enable/disable proceed without validating the dependency graph.

### 4.4 Menu Tree and RBAC Integration on Enable/Disable

- **Spec**: Enable merges `manifest.menu_items` into tenant menu tree; seeds `manifest.permissions` into tenant RBAC.
- **Spec**: Disable removes menu items and marks RBAC seeds inactive (does not delete rows).
- **Current**: No such logic in the enable/disable endpoints.

### 4.5 Structured Error Bodies

- **Spec**: All module endpoints return `{code, message, detail}`.
- **Current**: Endpoints raise `HTTPException(detail=string)` — bare string, no `code` field.

### 4.6 `activation-preview` Endpoint

- **Spec**: `GET /api/v1/modules/{id}/activation-preview` returns `{permissions, menu_items, dependencies}` with per-tenant dependency status.
- **Current**: Does not exist. The manifest endpoint proxies raw manifest but does not compute per-tenant dependency status.

### 4.7 Admin Deactivate-All + Two-Phase Uninstall

- **Spec Phase 1**: `POST /admin/modules/{id}/deactivate-all` sets `install_status=deactivation_pending`, deactivates all tenant activations, writes per-tenant audit rows.
- **Spec Phase 2**: `DELETE /admin/modules/{id}` guarded by `X-Confirm-Uninstall: true` header and `install_status=deactivation_pending` precondition.
- **Current**: `POST /module-registry/uninstall` is a single-phase, single-endpoint operation — no header guard, no phase gate, no per-tenant loop, no `deactivation_pending` status.

### 4.8 Audit Event Naming

- **Spec**: Five named events: `module.installed`, `module.enabled`, `module.disabled`, `module.deactivate_all`, `module.uninstalled`.
- **Current**: Audit writes exist for `module_install`, `module_uninstall`, `module_enable`, `module_disable` (verb_noun convention, not noun.verb). The `deactivate_all` event does not exist.

---

## 5. Decision Note: Migration Approach

### Decision

**Add new `/api/v1/modules/{id}/...` endpoints alongside the existing `/api/v1/module-registry/...` router. Do not rename or remove existing endpoints in this sprint.**

### Rationale

1. **Zero breakage**: The `/api/v1/module-registry` router is called by `module-manager.js`, by module services at registration/heartbeat time, and potentially by external integrations. Renaming requires a coordinated cutover of all callers simultaneously — too risky for a gate story.

2. **Incremental migration**: The `/api/v1/modules` stub router (`_modules_v1_router`) is already wired in the same file and registered at the right prefix. All new Epic 23 features (activation-preview, structured errors, dependency checks, RBAC/menu integration, two-phase uninstall) are added here exclusively.

3. **Frontend migration is isolated to T-23.004**: `module-manager.js` is updated in its own task to point to new paths; that change is self-contained and reviewable independently of backend router changes.

4. **Deprecation timeline**: Once all callers migrate to `/api/v1/modules`, the `/api/v1/module-registry` router is marked deprecated in its docstrings and removed in a later sprint. No action required during Epic 23.

### New Endpoint Implementation Plan

| New Endpoint | Implementation Notes |
|-------------|---------------------|
| `GET /api/v1/modules` | Filter `install_status=ready AND visibility=all_tenants`; left-join `module_activations` for requesting tenant; return `activation_status` field |
| `GET /api/v1/modules/{id}/activation-preview` | Read `manifest.permissions` and `manifest.menu_items`; query `module_activations` for each declared dependency to get per-tenant status |
| `POST /api/v1/modules/{id}/enable` | Dependency check (409); create/update `ModuleActivation`; merge menu items; seed RBAC permissions; call `post_enable` hook; write `module.enabled` audit row |
| `POST /api/v1/modules/{id}/disable` | Dependents check (409); set `ModuleActivation.is_enabled=False`; remove menu items; deactivate RBAC seeds; write `module.disabled` audit row |
| `POST /api/v1/admin/modules/{id}/deactivate-all` | Loop all active `ModuleActivation` rows for this module; set `Module.install_status=deactivation_pending`; write per-tenant + summary audit rows |
| `DELETE /api/v1/admin/modules/{id}` | Require `X-Confirm-Uninstall: true` header; gate on `install_status=deactivation_pending`; cascade-delete activations, RBAC seeds, menu registrations, files; write `module.uninstalled` |

### Identifier Strategy

New endpoints use **UUID `{id}`** (consistent with all other resource endpoints in this platform, aligned with the Epic 23 spec). The legacy router retains slug-based lookup. No dual-lookup shim needed — new endpoints resolve by UUID only.

---

## 6. References

- `backend/app/routers/modules.py` — current router (both prefixes)
- `backend/app/models/nocode_module.py` — `Module` and `ModuleActivation` models
- `backend/app/models/module_registry.py` — backward-compat shim
- `plan/epics/epic-23-module-lifecycle-and-activation.md` — full spec
- `plan/tasks/tasks-23.md` — sprint backlog
- `plan/architecture/schema-23.md` — DB schema additions (T-23.016/T-23.017)