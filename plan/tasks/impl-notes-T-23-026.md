# T-23.026 Implementation Notes — `manage.sh module uninstall`

## What was done

Replaced the pre-existing stub `module_uninstall()` in `manage.sh` (which used wrong endpoint paths, `SUPERADMIN_TOKEN`, and no confirmation prompt) with a spec-compliant implementation at lines ~1002–1100.

## Flow

1. **Flag parsing** — accepts `--api-url` and `--token`; falls back to `BUILDIFY_TOKEN` env var. Exits 1 with a clear message if token is absent.
2. **Module ID lookup** — `GET /api/v1/module-registry/` with Bearer auth; extracts UUID by matching `name == <module_name>` from the JSON list/items array. Exits 1 if not found.
3. **Phase 1 deactivate-all** — `POST /api/v1/modules/admin/{module_id}/deactivate-all`. Parses `tenants_deactivated` from the 200 response and prints: `Module '<name>' deactivated from N tenant(s). This will remove all module data.`
4. **Confirmation prompt** — `read -r -p "Type the module name to confirm uninstall: " CONFIRM`. If `$CONFIRM != $MODULE_NAME` prints "Aborted." and exits 0.
5. **Phase 2 DELETE** — `DELETE /api/v1/modules/admin/{module_id}` with `X-Confirm-Uninstall: true` header. Accepts 200 or 204 as success. On error, prints response body to stderr and exits 1.

## Endpoints used (corrected from stub)

| Step | Method | Path |
|------|--------|------|
| Lookup | GET | `/api/v1/module-registry/` |
| Phase 1 | POST | `/api/v1/modules/admin/{id}/deactivate-all` |
| Phase 2 | DELETE | `/api/v1/modules/admin/{id}` + `X-Confirm-Uninstall: true` |

## Auth token

Uses `BUILDIFY_TOKEN` (not `SUPERADMIN_TOKEN`) per spec — same token pattern as `module install`.

## Syntax check

`bash -n manage.sh` passes clean.

## Dispatcher

Already wired: `uninstall) shift; module_uninstall "$@" ;;` was present in the `module` case block.
