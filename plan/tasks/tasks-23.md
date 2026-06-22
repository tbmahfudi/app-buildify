---
artifact_id: tasks-23
type: tasks
producer: C1 Tech Lead
consumers: [C2 Backend Developer, C3 Frontend Developer, D1 QA Engineer, E1 DevOps Engineer, D3 Security Engineer]
upstream: [epic-23-module-lifecycle-and-activation, arch-23, adr-005-module-packaging-format, schema-23]
downstream: []
status: approved
created: 2026-06-18
updated: 2026-06-18
sprint:
  goal: Deliver a working end-to-end module lifecycle — developer packages and installs with one command; tenant activates/deactivates via UI with pre-activation summary
  length_days: 10
  capacity_assumption: 1 BE + 1 FE + 0.5 DevOps + 0.25 QA ≈ 140 dev-hours
decisions:
  - Story 23.1.1 (API contract + frontend fix) is the gate — T-23.001 through T-23.005 must be DONE before any other item starts
  - Schema migration (T-23.016) runs early in item 23.4 so C2 backend work can reference new columns
  - T-23.013 (hook wiring spike) must complete before T-23.014 — if spike finds the event bus insufficient, T-23.014 is marked DEFERRED per story 23.3.2 AC
  - Uninstall phase 2 (T-23.025) calls the Epic 22 cleanup service stub — if epic-22 story 22.4.5 is not yet implemented, T-23.025 ships with a documented TODO and a no-op stub
  - All audit log writes are verified in T-23.027 as a consolidation pass after all enable/disable/uninstall tasks land
open_questions:
  - Epic 22 story 22.4.5 (cleanup service) — merged or not by the time T-23.025 is picked up? If not, stub it.
  - Should D3 Security Engineer review the enable/disable endpoints (permission enforcement) as part of this sprint, or defer to sec-review-23? Recommend: D3 reviews T-23.020 and T-23.022 before they merge.
---

# tasks-23 — Sprint Backlog for Module Lifecycle & Activation

> **Upstream**: [`epic-23-module-lifecycle-and-activation`](../epics/epic-23-module-lifecycle-and-activation.md), [`arch-23`](../architecture/arch-23.md), [`adr-005-module-packaging-format`](../architecture/adr-005-module-packaging-format.md), [`schema-23`](../architecture/schema-23.md).

---

## Sprint Goal

Ship a working end-to-end module lifecycle: the platform developer runs `manage.sh module pack` + `manage.sh module install` to deploy a module with zero manual steps; tenant administrators self-service activate and deactivate installed modules via a Modules page with a pre-activation permissions summary.

## Capacity Plan

| Role | Headcount | Hours over 10-day sprint |
|------|----------:|------------------------:|
| C2 Backend Developer | 1 | 80 |
| C3 Frontend Developer | 1 | 80 |
| E1 DevOps Engineer | 0.5 | 40 |
| D1 QA Engineer | 0.25 | 20 |
| **Total** | — | **220** |

Task estimates sum to ~85 hours, leaving ~135 hours buffer for code review, integration testing, and unknowns. Sprint is achievable by a small team; adjust headcount frontmatter as needed.

---

## Task Table

Status legend: `OPEN` = not started · `IN-PROGRESS` = picked up · `BLOCKED` = waiting · `REVIEW` = PR open · `DONE` = merged.

---

### Item 23.1 — API Contract Alignment (Story 23.1.1) ⛔ GATE

> **All other items are BLOCKED until T-23.001 through T-23.005 are DONE.**

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-23.001 | Audit `backend/app/routers/modules.py` — document canonical lifecycle paths, write decision note in `docs/backend/MODULE_API.md` | C2 | — | 4 | [epic-23 §23.1.1 backend — canonical paths](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.002 | Add `GET /api/v1/modules/{id}/activation-preview` → `{permissions, menu_items, dependencies}` | C2 | T-23.001 | 4 | [epic-23 §23.1.1 backend — activation-preview](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.003 | Standardise structured error bodies `{code, message, detail}` on all module endpoints; ensure 409 shapes for deps-unmet and dependents-active match spec | C2 | T-23.001 | 3 | [epic-23 §23.1.1 backend — structured errors](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.004 | Fix `frontend/assets/js/module-manager.js` — replace `/activate`/`/deactivate` paths with `/enable`/`/disable`; update response-shape handling; smoke-test in dev browser | C3 | T-23.001 | 4 | [epic-23 §23.1.1 frontend — contract fix](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.005 | Integration tests: install→enable→disable cycle; dep-unmet 409; system-module 403 on delete | D1 | T-23.002, T-23.003, T-23.004 | 4 | [epic-23 §23.1.1 backend — integration tests](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |

**Subtotal: 19 hrs**

---

### Item 23.2 — Module Packaging Pipeline (Stories 23.2.1 + 23.2.2)

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-23.006 | Create `backend/app/core/module_system/manifest.schema.json` — full JSON Schema for all manifest fields including semver `version` pattern | C2 | T-23.001 | 3 | [epic-23 §23.2.1 backend — schema file](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.007 | Add `jsonschema.validate()` call in `loader.py`; wire into `POST /modules/register` (422 on violation) and add `POST /modules/validate` dry-run endpoint (no DB write) | C2 | T-23.006 | 3 | [epic-23 §23.2.1 backend — validate endpoint](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.008 | Implement `manage.sh module pack <dir> [--out <dir>]` — produces `<name>_<version>.tar.gz` + `SHA256SUMS`; normalises file timestamps for determinism | E1 | T-23.007 | 4 | [epic-23 §23.2.2 backend — pack command](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.009 | Pack command calls `POST /modules/validate` before bundling; exits non-zero on validation failure | E1 | T-23.008 | 2 | [epic-23 §23.2.2 backend — pre-pack validation](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |

**Subtotal: 12 hrs**

---

### Item 23.3 — Production Install Pipeline (Stories 23.3.1 + 23.3.2)

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-23.010 | Implement `manage.sh module install <tarball>` steps 1-4: verify SHA256, call `/modules/validate`, set `install_status=in_progress`, run module Alembic migrations | E1 | T-23.007 | 4 | [epic-23 §23.3.1 backend — install steps 1-4](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.011 | Implement install steps 5-8: copy backend service + frontend assets, call `POST /modules/register`, call `BaseModule.post_install()`, set `install_status=ready`; implement rollback on any failure | E1 | T-23.010 | 4 | [epic-23 §23.3.1 backend — install steps 5-8 + rollback](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.012 | Idempotency: detect same `name+version` already installed → exit 0 with message; structured per-step log output | E1 | T-23.011 | 2 | [epic-23 §23.3.1 backend — idempotency + logging](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.013 | Spike: confirm `BaseModule.post_install()` / `post_enable()` can be called as direct Python method calls from loader without event bus; write one-paragraph findings note in task comments | C2 | — | 2 | [epic-23 §23.3.2 backend — spike](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.014 | Wire hooks: `post_install(db)` called in `loader.py` after registration; `post_enable(db, tenant_id)` called in `/enable` endpoint after `ModuleActivation` created; wrap both in try/except (log+audit on failure, do NOT roll back) | C2 | T-23.013 | 3 | [epic-23 §23.3.2 backend — hook wiring](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.015 | Integration test: install a test-module stub whose `post_install` writes a sentinel row; assert sentinel exists after `manage.sh module install` | D1 | T-23.014 | 2 | [epic-23 §23.3.2 backend — hook integration test](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |

**Subtotal: 17 hrs · Note**: if T-23.013 spike finds the direct-call approach insufficient, T-23.014 and T-23.015 are marked DEFERRED per story 23.3.2 AC; epic DoD checklist accepts DEFERRED status with note.

---

### Item 23.4 — Tenant Activation UI (Stories 23.4.1 + 23.4.2 + 23.4.3)

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-23.016 | Run Alembic migration `pg_module_lifecycle_columns` — add `install_status`, `install_error_message`, `visibility` to `modules` table; test forward + backward | C2 | — | 2 | [schema-23 §5 — migration](../architecture/schema-23.md) | OPEN |
| T-23.017 | Update `Module` SQLAlchemy model in `nocode_module.py` — add three new columns + two `CheckConstraint` entries per schema-23 §6 | C2 | T-23.016 | 1 | [schema-23 §6 — model update](../architecture/schema-23.md) | OPEN |
| T-23.018 | Update `GET /api/v1/modules` — filter `install_status=ready AND visibility=all_tenants`; join `module_activations` for requesting tenant; return `activation_status` field per tenant | C2 | T-23.017, T-23.001 | 3 | [epic-23 §23.4.1 backend](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.019 | Build `modules-page.js` + route `#/settings/modules` — FlexGrid of ModuleCards per B3 UILDC spec; loading/empty/error states; wire "Activate"/"Deactivate" buttons to open respective modals | C3 | T-23.018, T-23.005 | 4 | [epic-23 §23.4.1 frontend](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.020 | Update `POST /api/v1/modules/{id}/enable` — dependency check (409 deps-unmet), merge manifest menu_items into tenant menu tree, seed manifest permissions into tenant RBAC, create `ModuleActivation(is_enabled=True)`, write `audit_logs(module.enabled)` | C2 | T-23.003, T-23.014 | 4 | [epic-23 §23.4.2 backend](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.021 | Build ActivationModal in `modules-page.js` — fetch `activation-preview`, render permissions/menu-items/dependencies per B3 UILDC spec; skeleton loading state; confirm disabled when deps unmet; emit `module:activated` on success | C3 | T-23.020, T-23.002 | 4 | [epic-23 §23.4.2 frontend](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.022 | Update `POST /api/v1/modules/{id}/disable` — dependents check (409 dependents-active), remove module menu items from tenant menu tree, set `Permission.is_active=False` for module's RBAC seeds in tenant, update `ModuleActivation.is_enabled=False`, write `audit_logs(module.disabled)` | C2 | T-23.020 | 3 | [epic-23 §23.4.3 backend](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.023 | Build DeactivateModal in `modules-page.js` — safety message, dependents blocking list per B3 UILDC spec; confirm disabled when dependents active; emit `module:deactivated` on success | C3 | T-23.022 | 3 | [epic-23 §23.4.3 frontend](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |

**Subtotal: 24 hrs · Security note**: D3 should review T-23.020 and T-23.022 before merge — permission seeding/revocation on enable/disable is the security-critical path.

---

### Item 23.5 — Operator Uninstall & Audit Trail (Stories 23.5.1 + 23.5.2)

| id | title | owner | depends-on | hrs | AC link | status |
|----|-------|-------|-----------:|----:|---------|--------|
| T-23.024 | Implement `POST /api/v1/admin/modules/{id}/deactivate-all` (superadmin only) — deactivates module for every tenant, sets `Module.install_status=deactivation_pending`, writes per-tenant + summary `audit_logs` rows | C2 | T-23.022 | 3 | [epic-23 §23.5.1 backend — phase 1](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.025 | Implement `DELETE /api/v1/admin/modules/{id}` (superadmin only, `X-Confirm-Uninstall: true` header required) — callable only when `install_status=deactivation_pending`; calls Epic-22 cleanup service (or no-op stub if 22.4.5 not merged); removes `module_activations`, RBAC seeds, menu registrations, module files; deletes `modules` row; writes `audit_logs(module.uninstalled)` | C2 | T-23.024 | 4 | [epic-23 §23.5.1 backend — phase 2](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.026 | Implement `manage.sh module uninstall <name>` — calls phase 1 endpoint, prints summary, prompts for confirmation, calls phase 2 endpoint | E1 | T-23.025 | 3 | [epic-23 §23.5.1 backend — CLI](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.027 | Consolidation pass: verify all 5 lifecycle audit events (`module.installed`, `module.enabled`, `module.disabled`, `module.deactivate_all`, `module.uninstalled`) are written correctly; fix any missing writes found across tasks above | C2 | T-23.020, T-23.022, T-23.025 | 2 | [epic-23 §23.5.2 backend — audit consolidation](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |
| T-23.028 | QA: verify `GET /api/v1/audit-logs?entity_type=module` returns all 5 event types; add to D1 QA smoke checklist | D1 | T-23.027 | 1 | [epic-23 §23.5.2 frontend — audit log verification](../epics/epic-23-module-lifecycle-and-activation.md) | OPEN |

**Subtotal: 13 hrs**

---

## Dependency Graph (critical path)

```
T-23.001 (gate)
    ├── T-23.002 ──────────────────────────────────────── T-23.021
    ├── T-23.003
    ├── T-23.004
    └── T-23.005 (gate complete)
         │
         ├── T-23.006 → T-23.007 → T-23.008 → T-23.009   (packaging pipeline)
         │
         ├── T-23.010 → T-23.011 → T-23.012               (install pipeline)
         │
         ├── T-23.013 → T-23.014 → T-23.015               (hook wiring)
         │
         └── T-23.016 → T-23.017 → T-23.018 → T-23.019   (list page)
                                         │
                                    T-23.020 → T-23.021   (activate modal)
                                         └── T-23.022 → T-23.023   (deactivate modal)
                                                   └── T-23.024 → T-23.025 → T-23.026  (uninstall)
                                                                        └── T-23.027 → T-23.028  (audit)
```

**Critical path**: T-23.001 → T-23.016 → T-23.018 → T-23.020 → T-23.022 → T-23.024 → T-23.025 → T-23.027

---

## Sprint Summary

| Item | Stories | Tasks | Est. hrs | Owner(s) |
|---|---|---:|---:|---|
| 23.1 API Contract (GATE) | 23.1.1 | 5 | 19 | C2, C3, D1 |
| 23.2 Packaging Pipeline | 23.2.1, 23.2.2 | 4 | 12 | C2, E1 |
| 23.3 Install Pipeline | 23.3.1, 23.3.2 | 6 | 17 | C2, E1, D1 |
| 23.4 Tenant Activation UI | 23.4.1, 23.4.2, 23.4.3 | 8 | 24 | C2, C3 |
| 23.5 Uninstall & Audit | 23.5.1, 23.5.2 | 5 | 13 | C2, E1, D1 |
| **TOTAL** | **9 stories** | **28** | **85** | |

---

## Follow-up Backlog (out of sprint scope)

- Company-level activation UI (Persona C from research-03) — data model ready (`company_id` nullable); UI deferred to v2
- `module_tenant_whitelist` table + `visibility=whitelist` UI — `visibility` column is in place; whitelist table deferred
- Module version upgrade path (semver bump, migration fan-out) — deferred to a future vision
- D3 Security Engineer `sec-review-23.md` — to be commissioned after sprint completes
- E2 Technical Writer `release-notes-epic-23.md` — to be commissioned after D3 sign-off
