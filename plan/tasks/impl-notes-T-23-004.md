# impl-notes — T-23.004

**Task**: Fix `frontend/assets/js/module-manager.js` — replace old enable/disable paths, update response-shape handling.
**Author**: C3 Frontend Developer
**Date**: 2026-06-25

---

## What was changed

File: `frontend/assets/js/module-manager.js`

### 1. `loadEnabledModules` — wrong path

- **Before**: `apiFetch('/modules?activation_status=active')`
- **After**: `apiFetch('/module-registry/enabled')`
- **Reason**: `/api/v1/modules?activation_status=active` does not exist. The canonical endpoint for listing a tenant's enabled modules is `GET /api/v1/module-registry/enabled` (see `MODULE_API.md` §1.1).

### 2. `enableModule` — path-param style, no body

- **Before**: `apiFetch(\`/modules/${moduleName}/enable\`, { method: 'POST' })`
- **After**: `apiFetch('/module-registry/enable', { method: 'POST', body: JSON.stringify({ module_name: moduleName }) })`
- **Reason**: The Epic 23 spec path `/api/v1/modules/{id}/enable` does not exist yet. The current working endpoint is `POST /api/v1/module-registry/enable` with body `{module_name: str}`. The old call was hitting a 404.

### 3. `disableModule` — path-param style, no body

- **Before**: `apiFetch(\`/modules/${moduleName}/disable\`, { method: 'POST' })`
- **After**: `apiFetch('/module-registry/disable', { method: 'POST', body: JSON.stringify({ module_name: moduleName }) })`
- **Reason**: Same as above — the spec path doesn't exist; current working endpoint requires body.

---

## Response shape handling

Current `ModuleOperationResponse` returns `{success: bool, message: str, module_name: str}`.

- **Error path**: `extractErrorMessage(result, fallback)` already handles `result.message` (string) correctly — no change needed.
- **Success path**: Toast uses a static string; does not need to parse `result.message`. This is intentional — static messages are localisation-friendly and the response `message` is backend-facing.

No changes were required to `extractErrorMessage` or the success toast logic.

---

## Paths verified absent after fix

```
grep -n 'activate\|deactivate\|/modules/' frontend/assets/js/module-manager.js
# → exit 1 (no matches)
```

---

## Note on future migration

When `POST /api/v1/modules/{id}/enable` and `/disable` are implemented (T-23.020, T-23.022), `module-manager.js` will need a second update to switch to UUID-based paths. That is out of scope for T-23.004.
