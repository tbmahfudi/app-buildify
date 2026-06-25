# T-23.024 — Implementation Notes

## Endpoint

`POST /api/v1/modules/admin/{module_id}/deactivate-all`

Resolves via `_modules_v1_router` (prefix `/api/v1/modules`) + path `/admin/{module_id}/deactivate-all`.

## Auth

Enforced by `require_superuser` FastAPI dependency — same pattern as other superadmin endpoints in modules.py.

## Logic

1. UUID parse — `Module` lookup — 404 on miss.
2. `require_superuser` dep rejects non-superadmins before function body runs.
3. Query `ModuleActivation` where `module_id=uuid` AND `is_enabled=True` (all tenants, no tenant filter).
4. For each activation: set `is_enabled=False`, `disabled_at=now()`, `disabled_by_user_id=current_user.id`; write per-tenant `audit_log(action="module.disabled", context_info={"reason":"deactivate_all", "tenant_id":...})`.
5. Set `Module.install_status="deactivation_pending"`.
6. `db.commit()`.
7. Write summary `audit_log(action="module.deactivate_all", context_info={"tenants_deactivated": N})`.
8. Return `ModuleDeactivateAllResponse(status="deactivation_pending", tenants_deactivated=N)`.

## Schema

`ModuleDeactivateAllResponse` was already present at the bottom of `backend/app/schemas/module.py`. Only the import into `backend/app/routers/modules.py` was added.

## Files changed

- `backend/app/routers/modules.py` — added `ModuleDeactivateAllResponse` to imports; appended endpoint (~120 lines)
- `backend/app/schemas/module.py` — no change needed (schema pre-existed)
