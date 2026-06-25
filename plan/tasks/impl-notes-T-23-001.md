# Implementation Notes — T-23.001

**Task**: Audit `backend/app/routers/modules.py` — document canonical lifecycle paths, write decision note in `docs/backend/MODULE_API.md`
**Author**: C2 Backend Developer
**Date**: 2026-06-25
**Status**: DONE

---

## Files Audited

- `backend/app/routers/modules.py` — primary router file; contains two routers
- `backend/app/models/module_registry.py` — backward-compat shim re-exporting from `nocode_module.py`
- `backend/app/models/nocode_module.py` — unified `Module` and `ModuleActivation` models
- `plan/epics/epic-23-module-lifecycle-and-activation.md` — full spec
- `plan/tasks/tasks-23.md` — sprint backlog

---

## Key Findings

### Two Routers in One File

`modules.py` contains two routers:

1. `router` — prefix `/api/v1/module-registry`, 14 endpoints, the legacy surface
2. `_modules_v1_router` — prefix `/api/v1/modules`, currently only one stub endpoint (`GET /{module_id}/provisioning-status` from Epic 22.4.2)

The Epic 23 spec targets `/api/v1/modules/{id}/...`. The stub router is the correct extension point — no new file needed.

### Identifier Mismatch

Current endpoints use `module_name` (slug string) everywhere. Epic 23 spec requires `{id}` (UUID) in path parameters. The `Module` table has both `id` (UUID PK) and `name` (unique slug), so backend lookup by UUID is straightforward. The frontend needs to carry UUID in state.

### Missing Gaps (summary)

1. No `activation_status` in the available-modules list response
2. No `activation-preview` endpoint
3. No dependency/dependents checks on enable/disable
4. No RBAC or menu tree integration on enable/disable
5. No structured `{code, message, detail}` error bodies
6. No two-phase uninstall (deactivate-all + DELETE with header guard)
7. `deactivate_all` audit event is completely absent; existing audit event names use `verb_noun` instead of spec's `noun.verb`

### Model Is Ready

`Module.install_status` (T-23.017) and `Module.visibility` columns are already present in `nocode_module.py` — the Alembic migration task (T-23.016) will add them to the DB, but the ORM model is already updated.

`ModuleActivation` already has `company_id` nullable, supporting future company-level activation scope.

---

## Decision Taken

**Additive approach**: New Epic 23 endpoints are added to `_modules_v1_router` at `/api/v1/modules`. The legacy `/api/v1/module-registry` router is left intact for backward compatibility. No rename, no removal.

Full rationale in `docs/backend/MODULE_API.md` section 5.

---

## Unblocks

This task (T-23.001) gates the entire sprint. The following tasks are now unblocked:

- **T-23.002** — Add `GET /api/v1/modules/{id}/activation-preview`
- **T-23.003** — Standardise structured error bodies
- **T-23.004** — Fix `module-manager.js` frontend paths
- **T-23.006** — Create manifest JSON schema file
- **T-23.016** — Run Alembic migration for install_status/visibility columns
- **T-23.018** — Update `GET /api/v1/modules` with activation_status