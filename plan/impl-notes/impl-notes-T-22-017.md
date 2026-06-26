# impl-notes-T-22.017 — GET /api/v1/modules/{id}/tenant-db-status endpoint

**Task**: T-22.017
**Status**: DONE
**Files changed**: `backend/app/routers/modules.py`, `backend/app/schemas/module.py`

## What was done

Added new endpoint `GET /api/v1/modules/{module_id}/tenant-db-status` on `_modules_v1_router`:

- Returns `TenantDBStatusResponse` with fields: `status`, `connection_secret_ref`, `error_message`, `created_at`.
- Returns HTTP 404 with `code: not_provisioned` if no `tenant_module_databases` row exists for `(current_user.tenant_id, module_id)`.
- Returns HTTP 404 with `code: not_found` if `module_id` is not a valid UUID.

`TenantDBStatusResponse` schema added to `backend/app/schemas/module.py`.
