# impl-notes-T-23-018

**Task**: Update `GET /api/v1/modules` — filter `install_status=ready AND visibility=all_tenants`; join `module_activations` for requesting tenant; return `activation_status` field per tenant.

**Status**: DONE
**Implemented by**: C2 Backend Developer
**Date**: 2026-06-25

---

## What was changed

### `backend/app/schemas/module.py`

- Expanded `ModuleListItemV2` (already existed as a stub) to include all required response fields:
  - `id`, `name`, `display_name`, `description`, `version`, `category`, `status`, `is_core`, `install_status`
  - `activation_status: str` — `"active"` | `"inactive"` per requesting tenant
  - `permissions_added: List[Any]` — from module manifest `permissions` key
  - `menu_items_added: List[Any]` — from manifest `menu_items` / `routes` key
  - `dependencies: List[Any]` — from manifest `dependencies` or `dependencies_json` column
- `ModulesListResponse` (already existed) — `{modules: List[ModuleListItemV2], total: int}` — unchanged.

### `backend/app/routers/modules.py`

- Added `ModuleListItemV2`, `ModulesListResponse` to the schema import block.
- Added `GET ""` endpoint on `_modules_v1_router` (resolves to `GET /api/v1/modules`):
  1. Queries `modules` table with `install_status='ready' AND visibility='all_tenants'`.
  2. Bulk-fetches matching `module_activations` rows for `current_user.tenant_id` in one SQL query (avoids N+1).
  3. Builds a set of `active_ids` and stamps each item with `"active"` or `"inactive"`.
  4. Returns `ModulesListResponse`.

---

## Design decisions

- **Bulk activation fetch**: a single `.in_()` query over the filtered module IDs rather than one query per module avoids N+1 on large catalogues.
- **No outerjoin**: keeping the two queries separate is simpler and easier to cache later.
- **Schema reuse**: `ModuleListItemV2` / `ModulesListResponse` were pre-scaffolded; this task only filled them in.
- The existing `GET /api/v1/module-registry/available` endpoint is untouched per task spec.

---

## AC coverage (epic-23 §23.4.1 backend)

| AC | Status |
|----|--------|
| Endpoint returns only `install_status=ready AND visibility=all_tenants` modules | Done |
| Each item includes `activation_status` derived from `module_activations` for requesting tenant | Done |
| Response includes `permissions_added`, `menu_items_added`, `dependencies` | Done |
| Auth via `get_current_user` (tenant-scoped) | Done |
| Existing `module-registry/available` endpoint untouched | Done |
