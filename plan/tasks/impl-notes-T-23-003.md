# impl-notes T-23.003 - Structured Error Bodies on Module Endpoints

**Task**: Standardise structured error bodies {code, message, detail} on all module endpoints.

**Status**: DONE  
**Date**: 2026-06-25  
**Author**: C2 Backend Developer

## What was changed

**File**: backend/app/routers/modules.py

All HTTPException raises (19 total) updated to structured detail dicts.
Every error body now follows: {"code": str, "message": str, "detail": any}

### Error code mapping

| Endpoint | HTTP status | New code |
|---|---|---|
| get_module_registry (dep) | 503 | service_unavailable |
| get_module_info | 404 | not_found |
| get_module_manifest | 404 | not_found |
| get_module_manifest | 503 | service_unavailable |
| install_module | 400 | module_install_error |
| uninstall_module | 400 | module_uninstall_error |
| enable_module | 403 | module_enable_error |
| enable_module | 404 (tenant) | not_found |
| enable_module | 400 | module_enable_error |
| disable_module | 400 | module_disable_error |
| update_module_configuration | 404 | not_found |
| update_module_configuration | 400 (not enabled) | module_configure_error |
| update_module_configuration | 400 (invalid config) | module_configure_error |
| register_module | 400 (no name) | module_register_error |
| register_module | 500 | module_register_error |
| module_heartbeat | 404 | not_found |
| module_heartbeat | 500 | module_heartbeat_error |
| sync_modules | 500 | module_sync_error |
| get_activation_preview | 404 | not_found |

### 409 shapes (for T-23.020 / T-23.022)

Dependency unmet shape (enable_module when deps check fails in T-23.020):
  {"code": "dependencies_unmet", "message": "...", "detail": {"missing": [{"name": "...", "id": "..."}]}}

Dependents active shape (disable_module when dependents check fails in T-23.022):
  {"code": "dependents_active", "message": "...", "detail": {"dependents": [{"name": "...", "id": "..."}]}}

System module delete shape (future DELETE endpoint):
  {"code": "system_module", "message": "Cannot delete a system module", "detail": null}

These 409 bodies are not yet raised (dep-check logic lives in T-23.020/T-23.022).

## Notes

- exceptions.py reviewed - no module-specific helpers exist; HTTPException + structured
  detail is consistent with FastAPI conventions and requires no new exception hierarchy.
- T-23.007 validate endpoint uses {"valid": False, "errors": [...]} which is intentionally
  different (validation response, not error) and was not modified.
