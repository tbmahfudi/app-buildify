# Implementation Notes — T-23.020

**Task**: `POST /api/v1/modules/{module_id}/enable` — dep check, RBAC seed, menu merge, audit  
**Implemented by**: C2 Backend Developer  
**Date**: 2026-06-25

---

## Files changed

| File | Change |
|------|--------|
| `backend/app/schemas/module.py` | Added `ModuleEnableResponse` Pydantic schema (appended at end of file) |
| `backend/app/routers/modules.py` | Added `ModuleEnableResponse` to import list; appended `enable_module_v1` endpoint to `_modules_v1_router` |

---

## Endpoint summary

`POST /api/v1/modules/{module_id}/enable` — registered on `_modules_v1_router` (prefix `/api/v1/modules`).

### Step-by-step behaviour

1. **Lookup** — validates `module_id` is a valid UUID; returns 404 `{code:"not_found"}` if Module row absent.
2. **Auth** — superusers bypass; others need `is_tenant_admin=True` OR a role with `modules:enable:tenant` permission code.  Returns 403 `{code:"forbidden"}` otherwise.
3. **Dependency check** — queries `module_dependencies` for `dependency_type="required"` rows AND resolves any names listed in `manifest.dependencies` (both `list` and `{"required":[...]}` forms).  Fetches active `ModuleActivation` rows for the tenant.  If any required dep is absent/inactive, returns 409 `{code:"dependencies_unmet", detail:{missing:[{name,id}]}}`.
4. **ModuleActivation upsert** — creates new row or updates existing tenant-level (company/branch/department = NULL) row to `is_enabled=True`, sets `enabled_at`/`enabled_by_user_id`.  `db.flush()` before downstream steps.
5. **Menu merge** — iterates `manifest.menu_items` (fallback: `manifest.routes`).  For each dict entry with a code/id/route key, constructs a unique `tenant_code = "{module.name}_{code}_{tenant_id[:8]}"`.  Inserts new `MenuItem` row or sets `is_active=True` on existing.  Wrapped in try/except — failure is logged and skipped gracefully (non-fatal).
6. **RBAC seed** — iterates `manifest.permissions` (fallback: `module.permissions`).  Accepts string format `"resource:action:scope"` and dict format `{code, resource, action, scope, name, description, category}`.  Inserts new `Permission` row or sets `is_active=True` on existing.  Wrapped in try/except — failure is logged and skipped gracefully.
7. **`db.commit()`** — single commit after both menu and permission writes.
8. **Audit log** — `create_audit_log(action="module.enabled", entity_type="module", entity_id=str(module_id), ...)` with `permissions_added` and `menu_items_added` in `context_info`.
9. **post_enable hook** — loads module instance from `ModuleLoader("/opt/buildify/modules")`, calls `post_enable(db, tenant_id)`.  Any exception is logged + audit-logged as `module_hook_failure`; not re-raised (non-fatal per T-23.014).
10. **Response** — `ModuleEnableResponse(status="active", permissions_added=[...], menu_items_added=[...])`.

---

## Design decisions

- **Permission check fallback order**: `is_superuser` → `is_tenant_admin` flag → role permission code. This handles both the simple tenant-admin pattern already in use elsewhere and a fine-grained RBAC approach.
- **Menu item code uniqueness**: prefix with `{module.name}_{code}_{tenant_id[:8]}` ensures no cross-tenant collision and is idempotent (re-enable just sets `is_active=True`).
- **Single commit**: menu + permission writes share one `db.commit()` before audit log, so a partial failure in either doesn't leave orphan records without an activation row.
- **Hook loader path**: uses `/opt/buildify/modules` consistent with install pipeline (T-23.011). If loader errors (module not installed as code module), hook is skipped non-fatally.

---

## Known gaps / follow-up

- `modules:enable:tenant` permission must be seeded in the initial fixture/migration for it to be assignable — add to permission fixture in T-23.027 consolidation pass or a separate migration.
- `POST /api/v1/modules/{id}/disable` (T-23.022) should mirror this with inverse logic (is_active=False on perms, remove menu items).
- D3 Security Engineer review recommended before merge (noted in tasks-23.md sprint decisions).
