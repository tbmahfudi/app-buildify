# impl-notes-T-22.015 — Wire deprovision into module disable flow

**Task**: T-22.015
**Status**: DONE
**Files changed**: `backend/app/routers/modules.py`

## What was done

After `db.commit()` in `POST /api/v1/modules/{module_id}/disable` (`disable_module_v1`), added a deprovision block:

1. Queries `tenant_module_databases` for `(tenant_id, module_uuid)`.
2. If a row exists with `status == "ready"`, calls `await ModuleDBProvisioner().deprovision(tenant_id, module.name)`.
3. Skips silently if no row (module was never provisioned -- e.g. `requires_tenant_db` not declared).
4. Any exception is caught non-fatally with a warning log -- disable operation itself is not rolled back.

## Design notes

- Deprovision is non-fatal on the disable path to avoid leaving a module stuck enabled due to DB cleanup failure. Operators can re-run deprovision manually or via cleanup service (T-22.018).
- Only fires when `status == "ready"` -- avoids double-DROP on already-deprovisioned or still-provisioning rows.
