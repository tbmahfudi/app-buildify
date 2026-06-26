# impl-notes-T-22.014 — Wire provisioner into module enable flow

**Task**: T-22.014
**Status**: DONE
**Files changed**: `backend/app/routers/modules.py`, `backend/app/schemas/module.py`

## What was done

After the RBAC seed and menu merge in `POST /api/v1/modules/{module_id}/enable` (`enable_module_v1`), added a provisioning block that fires when the module manifest declares `requires_tenant_db: true`:

1. Queries `tenant_module_databases` for an existing `(tenant_id, module_uuid)` row.
2. If no row exists, or the row has `status=failed` (retry path), calls `await ModuleDBProvisioner().provision(tenant_id, module.name)` and sets `_tenant_db_status = "provisioning"`.
3. If a row exists in any other state (provisioning, ready), returns the current status and `connection_secret_ref` from the row -- idempotent, no duplicate provision.
4. Any exception is caught non-fatally: a warning is logged and `_tenant_db_status = "failed"` is surfaced in the response.

`ModuleEnableResponse` schema extended with `tenant_db_status: Optional[str]` and `connection_secret_ref: Optional[str]`.

## Design notes

- Provisioner call is `await` (async delegate); the actual work runs synchronously inside `ModuleDBProvisioner._provision_sync()` via blocking I/O. Acceptable for sprint -- true async worker queue is L-1 follow-up.
- `GET /modules/{id}/provisioning-status` (already live at T-22.013 stub) returns real-time status from `tenant_module_databases`; the frontend should poll that after enable.
