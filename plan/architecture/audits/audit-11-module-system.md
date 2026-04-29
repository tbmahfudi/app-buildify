---
artifact_id: audit-11-module-system
type: audit
producer: Code Auditor
consumers: [Tech Lead, Product Owner]
upstream:
  - epic-11-module-system
  - arch-platform
  - adr-001-deployment-modes
downstream: []
status: approved
created: 2026-04-29
updated: 2026-04-29
audit_target: epic-11-module-system
auditor: Claude (Opus 4.7)
commit_sha: cc47a54
coverage_pct: 100
decisions:
  - Three stories tagged `[DONE]` drift from the code (different endpoint paths or partial impl)
  - Distributed-mode readiness blocked on the LISTEN/NOTIFY stub (separate gap, see ADR-001)
open_questions:
  - Should the AC for 11.1.2 be updated to match the implemented `install/enable/disable` endpoints, or should `/activate` aliases be added?
---

# Audit — Epic 11: Module System (audit-11-module-system)

## 1. Summary

- Stories audited: **7**
- DONE: **2** • PARTIAL: **2** • DRIFT: **2** • MISSING: **1** (PLANNED + 1 PLANNED matches)
- Tag-drift count: **3** (`[DONE]` stories whose `verified_status` is PARTIAL or DRIFT)
- Recommended `BACKLOG.md` tag: **Mostly DONE; activation API drift, marketplace + export/import OPEN** (currently "Mostly DONE; Marketplace PLANNED" — understates the activation endpoint drift and missing nocode export/import)

## 2. Story-by-story

| Story | Title | Claimed | Verified | Backend evidence | Frontend evidence | Gaps | 🚦 |
|-------|-------|---------|----------|------------------|-------------------|------|----|
| 11.1.1 | Module Registration | DONE | PARTIAL | `app/routers/modules.py:628 POST /register`, `app/core/module_system/loader.py:279 validate_module()`, `app/core/module_system/loader.py:319` (required-field check), `app/models/module_registry.py ModuleRegistry`, `app/routers/modules.py:653-680` (idempotent upsert) | `frontend/assets/js/nocode-modules.js` (catalog page) | Manifest validation is a presence check on required fields (loader.py:319), not a full JSON-schema validation as the AC requires. No `manifest.schema.json` artifact in repo. | 🟡 |
| 11.1.2 | Per-Tenant Module Activation | DONE | **DRIFT** | `app/routers/modules.py:302 POST /install`, `app/routers/modules.py:414 POST /enable`, `app/routers/modules.py:503 POST /disable`, `app/core/module_system/base_module.py post_install/post_enable hooks` | `frontend/assets/js/module-manager.js` | AC specifies `POST /api/v1/modules/{id}/activate`; actual surface is `/install`, `/enable`, `/disable` (no `/activate` path). The `company.created` event-triggered initialization is not wired (see also adr-001). | 🔴 |
| 11.1.3 | Module Dependency Management | DONE | DONE | `app/models/nocode_module.py:266 ModuleDependency`, `app/routers/nocode_modules.py:194 GET /{id}/dependencies`, `app/routers/nocode_modules.py:212 POST /{id}/dependencies`, `app/routers/nocode_modules.py:261 GET /{id}/dependents`, `app/routers/nocode_modules.py:279 GET /{id}/dependencies/check` | `frontend/assets/js/module-manager.js` | The 409 with `{missing: [{name, required_version, installed_version?}]}` response shape was not verified by inspection; spot-check during PR review. | 🟢 |
| 11.2.1 | Module Catalog Browse | PLANNED | **MISSING** | `app/routers/modules.py:63 GET /available` (returns list but no `category`/`module_type`/`is_installed`/`search` query params) | — | Marketplace UI route `#/modules/marketplace` not present; query-param filters not implemented; module record fields `screenshots`, `permissions_required`, `dependencies` not in response schema | — |
| 11.2.2 | One-Click Module Activation from Marketplace | PLANNED | **MISSING** | — (depends on 11.1.2's `/activate` which itself is DRIFT) | — | Reuse target endpoint doesn't exist at the claimed path | — |
| 11.3.1 | User-Designed Module Creation | DONE | DONE | `app/routers/nocode_modules.py:38 POST /nocode-modules`, `app/models/nocode_module.py:26 Module` with `module_type`, `app/routers/nocode_modules.py:148 POST /{id}/publish`, `app/routers/nocode_modules.py:118 PUT /{id}` | `frontend/assets/js/` (nocode-modules-list-page, nocode-module-detail-page) | Association of `EntityDefinition.module_id = module.id` is implied by the data model but the explicit `POST /nocode-modules/{id}/entities` endpoint to attach existing entities was not found | 🟡 |
| 11.3.2 | Module Template Export and Import | DONE | **DRIFT** | `app/routers/templates.py:95 GET /export/entity/{entity_id}`, `app/routers/templates.py:161 POST /import/entity`, `app/routers/templates.py:174 POST /import/package`, `app/routers/templates.py:187 POST /import/zip` | `frontend/assets/js/` (no nocode-module export/import UI located) | AC says `POST /api/v1/nocode-modules/{id}/export` and `POST /api/v1/nocode-modules/import` — these endpoints do NOT exist on `nocode_modules.py`. Export/import lives on `templates.py` with different semantics (entity-scoped, not module-scoped); the ZIP shape `{entities.json, fields.json, workflows.json, dashboards.json}` was not verified. | 🔴 |

## 3. Gaps

### 🔴 High

- [ ] **11.1.2** Reconcile activation API. Either (a) add `POST /api/v1/modules/{id}/activate` and `/deactivate` aliases that call the install/enable/disable internals, or (b) update the AC + frontend to use `/install/enable/disable` directly. **Files**: `backend/app/routers/modules.py:302-565`, `plan/epics/epic-11-module-system.md`. **Effort**: S (alias) or M (rewrite AC + UI).
- [ ] **11.1.2** Wire the `company.created` event to module initialization hooks. Today `BaseModule.post_install/post_enable` exist (`backend/app/core/module_system/base_module.py`) but the event subscription is not registered. Required for distributed mode per ADR-001. **Effort**: M.
- [ ] **11.3.2** Add `POST /nocode-modules/{id}/export` and `POST /nocode-modules/import` (the AC's path) returning the ZIP shape `{entities.json, fields.json, workflows.json, dashboards.json}` with idempotent import + `{created, updated, skipped}` summary. Reuse the ZIP plumbing in `templates.py:174-187`. **Files**: `backend/app/routers/nocode_modules.py`, `backend/app/services/nocode_module_service.py`. **Effort**: M.
- [ ] **(cross-cutting, ties to ADR-001)** Finish the LISTEN/NOTIFY subscriber stub at `modules/financial/backend/app/core/event_handler.py:43-47`. Without this, `DEPLOYMENT_MODE=distributed` cannot be declared production-ready. **Effort**: M.

### 🟡 Medium

- [ ] **11.1.1** Replace the required-field presence check in `backend/app/core/module_system/loader.py:319` with full JSON-schema validation. Add `backend/app/core/module_system/manifest.schema.json`. Return structured per-field errors on `POST /modules/register` violations. **Effort**: S.
- [ ] **11.3.1** Add the explicit `POST /nocode-modules/{id}/entities` (and `/workflows`, `/dashboards`) attachment endpoints described in the frontend AC. Currently association is via setting `EntityDefinition.module_id` directly which the UI cannot do without an API. **Effort**: S.

### 🟢 Low

- [ ] **11.1.3** Verify the 409 response body shape `{missing: [{name, required_version, installed_version?}]}` matches the AC; correct the schema if not. **Effort**: XS.

## 4. Drift notes

- **11.1.2**: The backend has a richer surface than the AC describes (`/install`, `/enable`, `/disable`, `/uninstall`, `/configuration`, `/heartbeat`, `/sync`) but no `/activate`. The richer model is arguably better (separates installation from per-tenant enable) but the AC was written against `/activate`. Pick one and align the frontend.
- **11.3.2**: Export/import IS implemented but for different scopes — `templates.py:174-187` exports a single entity or a "package" template, not a nocode-module bundle. The user-visible feature ("export this module as a ZIP, import elsewhere") is not delivered end-to-end despite the `[DONE]` tag.
- **11.1.1**: "Validated against JSON schema" was implemented as "checked for required fields" — DONE in spirit, not in letter.

## 5. Verdict

`BACKLOG.md` row for Epic 11 currently reads "Mostly DONE; Marketplace PLANNED". The marketplace planning is honest, but two `[DONE]` stories (11.1.2 activation API drift, 11.3.2 nocode export/import missing) overstate completion. Single most impactful next action: **decide the activation API contract (11.1.2) and align the AC + endpoints + frontend before adding the marketplace UI** — the marketplace's only backend dependency is this endpoint.

This epic is also load-bearing for ADR-001's distributed mode: the `BaseModule` contract at `backend/app/core/module_system/base_module.py` is solid, but the event-bus subscriber finish (cross-cutting 🔴 above) gates the distributed deployment shape.

## Decisions

- Story 11.3.2 marked DRIFT (not MISSING) because export/import code exists but at a different endpoint with different semantics; the user-visible feature is not delivered.
- Story 11.1.2 marked DRIFT because the activation flow exists end-to-end, just not at the path the AC specifies.
- The cross-cutting LISTEN/NOTIFY gap is recorded here (since module-system epic owns the module contract) and cross-referenced from ADR-001.

## Open Questions

- Is the marketplace UI worth building before consolidating the activation API? Recommend no — fix 11.1.2 first.
- Should `templates.py` and `nocode_modules.py` export/import logic be merged behind a single service? Avoids two parallel ZIP formats.
