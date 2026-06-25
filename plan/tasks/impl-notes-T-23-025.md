# impl-notes-T-23-025 — DELETE /api/v1/modules/admin/{module_id}

**Task**: T-23.025  
**Implemented by**: C2 Backend Developer  
**File**: `backend/app/routers/modules.py` (appended to `_modules_v1_router`)

## Endpoint

`DELETE /api/v1/modules/admin/{module_id}`  
Registered on `_modules_v1_router` (prefix `/api/v1/modules`), tags `["modules-v1"]`.  
Returns **204 No Content** on success.

## Guards

- `require_superuser` dependency: 401/403 if caller is not superadmin
- `X-Confirm-Uninstall: true` header: 400 `confirm_header_required` if missing or not exactly `"true"`
- `Module.install_status == "deactivation_pending"`: 409 `uninstall_not_ready` if condition not met

## Cleanup Steps (in order)

1. **Epic-22 cleanup stub** — no-op with `logger.info` and `# TODO: Epic-22 cleanup service (story 22.4.5)` comment. Checked: no 22.4.5 endpoint exists anywhere in `backend/`.
2. **Delete ModuleActivation rows** — all rows for the module (enabled and disabled) deleted with `db.delete()` plus `db.flush()`.
3. **Deactivate RBAC permissions** — reads permission codes from `module.manifest.permissions` and `module.permissions`; sets `Permission.is_active = False` (consistent with T-23.022 approach). Non-fatal on DB error.
4. **Delete MenuItem rows** — deletes via `MenuItem.module_code == module_name`; fallback pattern `LIKE "{name}_%"` if no rows found by `module_code`. Non-fatal on DB error.
5. **Remove module files** — `subprocess.run(["docker", "exec", "app_buildify_backend", "bash", "-c", "rm -rf /app/modules/<name>"])`. Wrapped in try/except; logs warning on failure, does NOT abort.
6. **Delete modules row** — `db.delete(module)` plus `db.commit()`.
7. **Audit log** — `create_audit_log(action="module.uninstalled", ...)` with `context_info` containing `module_name`, `activations_removed`, `permissions_deactivated`, `menu_items_removed`.

## Schema changes

None. No new response schema needed (204 returns no body). `Header` was added to the `from fastapi import ...` import line.

## Decisions

- **Permissions deactivated not deleted**: matches T-23.022 pattern; `is_active=False` keeps audit trail of what permissions once existed.
- **MenuItems deleted not deactivated**: uninstall is permanent; rows are hard-deleted across all tenants.
- **Docker exec wrapping**: uses `subprocess.run` with `timeout=30`; failure is non-fatal to allow cleanup to complete even if the container is not reachable.
- **Epic-22 stub**: no-op with explicit TODO comment per spec guidance (story 22.4.5 not merged at time of implementation).
