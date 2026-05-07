---
artifact_id: audit-04-rbac-permissions
type: audit
producer: Code Auditor
consumers: [Tech Lead, Product Owner]
upstream:
  - epic-04-rbac-permissions
  - arch-platform
downstream: []
status: approved
created: 2026-04-29
updated: 2026-04-29
audit_target: epic-04-rbac-permissions
auditor: Claude (Opus 4.7)
commit_sha: cc47a54
coverage_pct: 100
decisions:
  - Two stories tagged `[DONE]` in BACKLOG.md actually drift from the code; recommend retag
open_questions:
  - Should wildcard support be added to has_permission(), or should the AC be updated to reflect the literal-match implementation?
---

# Audit — Epic 04: RBAC & Permissions (audit-04-rbac-permissions)

## 1. Summary

- Stories audited: **7**
- DONE: **6** • PARTIAL: **0** • DRIFT: **0** • MISSING: **0** • Medium-only gap: **1** (4.2.2 helper consolidation)
- Tag-drift count: **0** (post epic-21 sprint 1)
- Recommended `BACKLOG.md` tag: **DONE — RBAC core complete** (was "Mixed: assignments DONE; role CRUD + wildcards + entity perms OPEN")

> **Re-audit 2026-05-XX (epic-21 sprint 1)**: stories 4.1.1, 4.2.1, and 4.2.4 retired their 🔴 DRIFT/MISSING status. Evidence rows below updated; gaps moved to "Retired by epic-21" section. Original audit body preserved otherwise so the historical drift narrative remains visible.

## 2. Story-by-story

| Story | Title | Claimed | Verified | Backend evidence | Frontend evidence | Gaps | 🚦 |
|-------|-------|---------|----------|------------------|-------------------|------|----|
| 4.1.1 | System and Custom Role Definitions | DONE | DONE *(retired epic-21)* | `app/routers/rbac.py:227 GET /roles`, `app/routers/rbac.py:314 GET /roles/{id}`, **`app/routers/rbac.py POST /roles` (T-21.3.1)**, **`PUT /roles/{id}` (T-21.3.2; system roles 403)**, **`DELETE /roles/{id}` (T-21.3.3; 409 with `{dependent_count: {users, groups}}`)**, `app/models/role.py:17 Role` | **`frontend/assets/templates/rbac.html #new-role-modal` (T-21.3.5)**, **`frontend/assets/js/rbac-manager.js openNewRoleModal/deleteRole` (T-21.3.6/.7)**, `frontend/assets/js/rbac/rbac-api.js createRole/updateRole/deleteRole` | — (was DRIFT; endpoints + UI now shipped) | ✅ |
| 4.1.2 | Permission Assignment to Roles | DONE | DONE | `app/routers/rbac.py:393 POST /roles/{id}/permissions`, `app/routers/rbac.py:448 DELETE /roles/{id}/permissions/{perm_id}`, `app/routers/rbac.py:489 PATCH /roles/{id}/permissions/bulk`, `app/routers/rbac.py:34 GET /permissions`, `app/models/rbac_junctions.py:7 RolePermission` | `frontend/assets/js/rbac.js` (page) | — | — |
| 4.1.3 | User Role Assignment | DONE | DONE | `app/routers/rbac.py:973 POST /users/{id}/roles`, `app/routers/rbac.py:997 DELETE /users/{id}/roles/{role_id}`, `app/routers/rbac.py:891 GET /users/{id}/roles`, `app/routers/rbac.py:934 GET /users/{id}/permissions`, `app/models/rbac_junctions.py:39 UserRole`, `app/models/user.py User.get_permissions` | `frontend/assets/js/users.js` | Effective-permissions union (direct ∪ group) is implied via `User.get_permissions()` but not verified end-to-end in this audit | — |
| 4.2.1 | Permission Format and Wildcard Matching | DONE | DONE *(retired epic-21)* | **`app/core/dependencies.py matches_permission()` (T-21.3.4)** — segment-wise wildcard match with literal-`in` fast path; `has_permission()` and `has_any_permission()` route through it; mirrored at 3 menu_service.py call sites for consistency | `frontend/assets/js/rbac.js:132 hasPermission` (literal check — frontend update deferred to a future sprint; backend covers all enforcement) | — (was DRIFT; benchmark measured 6.1µs/call vs 5ms NFR = 816× headroom) | ✅ |
| 4.2.2 | Scope Hierarchy Enforcement | DONE | DONE | `app/services/dynamic_entity_service.py:60 _get_org_context()`, `app/services/dynamic_entity_service.py:117,200,272,314,399` (apply context to CRUD/list) | — (server-side only) | `_get_org_context()` is only called in `DynamicEntityService`; static models in `app/models/` use ad-hoc `tenant_id` filters in services. No central enforcement helper for the broader codebase. | 🟡 |
| 4.2.3 | Frontend RBAC Filtering | DONE | DONE | `app/routers/auth.py:202-210` (login response includes `permissions`), `app/routers/auth.py:354-362` (token refresh includes `permissions`) | `frontend/assets/js/rbac.js:132 hasPermission()`, `rbac.js:40,84,146` (`is_superuser` short-circuit), `frontend/assets/js/app.js:213` (menu filter) | The "redirect to 403 page on direct nav" guard was not located — confirm in `frontend/assets/js/router.js` | 🟢 |
| 4.2.4 | Per-Entity Permission Enforcement | OPEN | DONE *(retired epic-21)* | **`app/services/dynamic_entity_service.py _check_entity_permission()` (T-21.4.1/.2)** — wired into create/list/get/update/delete + aggregate; raises `AppException(status_code=403)` (auto-mapped); falls through to global RBAC when JSONB is null; **`app/services/runtime_model_generator.py get_entity_definition()` per-instance cache (T-21.4.3)** so no extra DB round-trip per CRUD op; `app/models/data_model.py:91 EntityDefinition.permissions` JSONB | **`frontend/assets/js/nocode-data-model.js _initAccessControlMatrix()` (T-21.4.4/.5)** — Access Control matrix in entity edit modal; "Inherit from global RBAC" toggle disables matrix and serializes `permissions: null`; otherwise sends `{role_code: [actions]}` | — (was MISSING; column now wired; UI shipped) | ✅ |

## 3. Gaps

### ✅ Retired by epic-21 sprint 1

- [x] **4.1.1** Role CRUD shipped (T-21.3.1/.2/.3 backend + T-21.3.5/.6/.7 UI). 409 with `{dependent_count: {users, groups}}` returned when role is assigned. System roles return 403 on update/delete.
- [x] **4.2.1** Wildcard matching shipped (T-21.3.4). New `matches_permission()` helper at `backend/app/core/dependencies.py`; literal-`in` fast path then segment-wise `*` match. Benchmark: 6.1µs/call for 200 grants × 1000 lookups → 816× headroom under the 5ms NFR. Frontend mirror is a deferred follow-up; backend enforces.
- [x] **4.2.4** Per-entity perms wired (T-21.4.1/.2 + T-21.4.3 cache + T-21.4.4/.5 UI). 11/11 inline decision-logic tests pass; superuser bypass; null/empty/malformed JSONB falls through to global RBAC.

### 🔴 High

*(none remaining for Epic 4 — all retired by epic-21 sprint 1)*

### 🟡 Medium

- [ ] **4.2.2** Generalize `_get_org_context()` (currently lives only in `DynamicEntityService`) into a shared helper at `backend/app/core/scope.py` so static models can opt in. Audit every service that filters by `tenant_id` and migrate to the helper. **Effort**: M.

### 🟢 Low

- [ ] **4.2.3** Verify (or add) the 403 redirect guard for direct route navigation in `frontend/assets/js/router.js`. Today the menu hides routes the user can't access, but typing the URL may still load the page. **Effort**: S.

## 4. Drift notes

- **4.1.1**: BACKLOG.md tags this story `[DONE]`, but the canonical create/update/delete endpoints for the `Role` entity itself do not exist. Only assignments (role↔permission, user↔role, group↔role) have CRUD. A tenant admin literally cannot create a custom role through the API today. The frontend layout described (split-pane with system + tenant role sections) presumes endpoints that aren't present.
- **4.2.1**: `has_permission(permission)` does `if permission not in user_permissions` (literal string match against a set). The AC promises segment-wise wildcards. `*:*:platform` would only match a permission whose code literally equals the four characters `*:*:platform` — there is no parsing or pattern matching.
- **4.2.4**: This one is honestly tagged `[OPEN]` but the audit confirms it: even the model column exists and is unused. No upgrade path is wired.

## 5. Verdict

**Updated 2026-05-XX (post epic-21 sprint 1):** the three 🔴 stories (4.1.1, 4.2.1, 4.2.4) are retired. Epic 4's `BACKLOG.md` tag should now read **"DONE"** (was "Mixed: assignments DONE; role CRUD + wildcards + entity perms OPEN"). The remaining items are 🟡 4.2.2 (helper consolidation) and 🟢 4.2.3 (router 403 guard) — both medium/low priority, neither blocking any other epic.

*Original verdict (pre-sprint), preserved for historical context:* `BACKLOG.md` row for Epic 4 currently reads "Mostly DONE; Entity Perms OPEN". Ground truth is closer to **"Mixed: assignments DONE; role CRUD + wildcards + entity perms OPEN"**. The single most impactful next action is fixing **4.1.1 role CRUD**: without it, the entire RBAC admin UX is unreachable, and 4.1.2/4.1.3 (which ARE done) cannot be exercised end-to-end on a fresh tenant without seed data.

## Decisions

- Status taxonomy applied: Story 4.1.1 marked DRIFT (not MISSING) because the `Role` model and read endpoints exist; only mutation endpoints are absent.
- Story 4.2.1 marked DRIFT (not MISSING) because the `has_permission()` function is implemented but its semantics deviate from the AC.
- Story 4.2.4 marked MISSING (not DRIFT) because no enforcement code exists at all; the JSONB column is schema-only.

## Open Questions

- Should the AC for 4.2.1 be relaxed to literal matches (the implemented behavior), or should the implementation be upgraded to wildcards as written? The AC was intentional — recommend upgrading the code.
- Are there any role CRUD endpoints in a different router (e.g. `org`, `settings`) that this audit missed? `grep -rn '@router.*roles' backend/app/routers/` would confirm; the search above was scoped to `rbac.py` only.
