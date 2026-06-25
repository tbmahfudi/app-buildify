# T-23.022 Implementation Notes — POST /api/v1/modules/{id}/disable

## Files changed
- `backend/app/schemas/module.py` — added `ModuleDisableResponse` (status, permissions_deactivated, menu_items_deactivated)
- `backend/app/routers/modules.py` — added `ModuleDisableResponse` import; added `disable_module_v1` on `_modules_v1_router`

## Route
`POST /api/v1/modules/{module_id}/disable` maps to `disable_module_v1`

## Steps implemented

1. **404 lookup** — UUID parse + Module DB query, identical to enable pattern.
2. **Permission check** — superuser bypass, then is_tenant_admin, then modules:disable:tenant role permission.
3. **Dependents check** — queries all currently-active ModuleActivation rows for the tenant (excluding this module), loads each module manifest, checks dependencies list for this module's name. If any found, raises 409 dependents_active with list of dependents.
4. **Deactivate activation** — sets is_enabled=False, disabled_at=now, disabled_by_user_id, clears enabled_at/enabled_by_user_id.
5. **Menu items** — queries MenuItem by module_code == module.name AND tenant_id; falls back to code LIKE pattern. Sets is_active=False on all matched rows.
6. **RBAC permissions** — extracts perm codes from manifest.permissions[] (str or dict). Queries Permission.code IN codes, sets is_active=False.
7. **Commit**.
8. **Audit log** — action=module.disabled, entity_type=module, includes permissions_deactivated and menu_items_deactivated in context_info.

## Design decisions
- Menu item deactivation uses module_code column (primary) with code LIKE fallback — mirrors the reverse of what T-23.020 does on enable.
- Permission deactivation is global (not tenant-scoped) — permissions are shared rows; consistent with T-23.020 which sets is_active=True globally.
- Dependents check is O(active_modules) manifest scan — acceptable for typical module counts. An indexed ModuleDependency reverse-lookup could replace this at scale.
- post_disable hook not implemented (not in spec); can be added matching the post_enable pattern from T-23.020.

## AC coverage (epic-23 §23.4.3 backend)
- [x] 409 dependents_active with dependents list
- [x] Remove module menu items from tenant menu tree (is_active=False)
- [x] Permission.is_active=False for module's RBAC seeds
- [x] ModuleActivation.is_enabled=False
- [x] audit_logs(module.disabled)
