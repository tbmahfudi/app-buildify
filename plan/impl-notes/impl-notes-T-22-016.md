# impl-notes-T-22.016 — Add tenant_db_status to activation-preview endpoint

**Task**: T-22.016
**Status**: DONE
**Files changed**: `backend/app/routers/modules.py`, `backend/app/schemas/module.py`

## What was done

In `GET /api/v1/modules/{module_id}/activation-preview` (`get_activation_preview`), added a query against `tenant_module_databases` immediately before the return:

1. Queries `TenantModuleDatabase` filtered by `(current_user.tenant_id, module_id)`.
2. Returns `row.status` if a row exists; otherwise returns `"not_provisioned"`.
3. Exception is caught non-fatally -- `tenant_db_status` remains `None` on DB error.

`ActivationPreviewResponse` schema extended with `tenant_db_status: Optional[str] = None`.
