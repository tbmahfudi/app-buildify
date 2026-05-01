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
- DONE: **3** • PARTIAL: **0** • DRIFT: **3** • MISSING: **1**
- Tag-drift count: **4** (stories whose `verified_status` ≠ `claimed_status`)
- Recommended `BACKLOG.md` tag: **Mostly Mixed; Role CRUD + Wildcards + Entity Perms OPEN** (currently "Mostly DONE; Entity Perms OPEN" — understates the gap)

## 2. Story-by-story

| Story | Title | Claimed | Verified | Backend evidence | Frontend evidence | Gaps | 🚦 |
|-------|-------|---------|----------|------------------|-------------------|------|----|
| 4.1.1 | System and Custom Role Definitions | DONE | **DRIFT** | `app/routers/rbac.py:227 GET /roles`, `app/routers/rbac.py:314 GET /roles/{id}`, `app/models/role.py:17 Role`, `app/models/role.py is_system` | — (no role-CRUD UI to verify against) | `POST /api/v1/rbac/roles` MISSING; `PUT/PATCH /api/v1/rbac/roles/{id}` MISSING; `DELETE /api/v1/rbac/roles/{id}` MISSING (only `DELETE /roles/{id}/permissions/{perm_id}` at line 448 exists); 409-on-dependent-count guard not implementable without delete endpoint | 🔴 |
| 4.1.2 | Permission Assignment to Roles | DONE | DONE | `app/routers/rbac.py:393 POST /roles/{id}/permissions`, `app/routers/rbac.py:448 DELETE /roles/{id}/permissions/{perm_id}`, `app/routers/rbac.py:489 PATCH /roles/{id}/permissions/bulk`, `app/routers/rbac.py:34 GET /permissions`, `app/models/rbac_junctions.py:7 RolePermission` | `frontend/assets/js/rbac.js` (page) | — | — |
| 4.1.3 | User Role Assignment | DONE | DONE | `app/routers/rbac.py:973 POST /users/{id}/roles`, `app/routers/rbac.py:997 DELETE /users/{id}/roles/{role_id}`, `app/routers/rbac.py:891 GET /users/{id}/roles`, `app/routers/rbac.py:934 GET /users/{id}/permissions`, `app/models/rbac_junctions.py:39 UserRole`, `app/models/user.py User.get_permissions` | `frontend/assets/js/users.js` | Effective-permissions union (direct ∪ group) is implied via `User.get_permissions()` but not verified end-to-end in this audit | — |
| 4.2.1 | Permission Format and Wildcard Matching | DONE | **DRIFT** | `app/core/dependencies.py:108 has_permission()` (literal `in user_permissions` check) | `frontend/assets/js/rbac.js:132 hasPermission` (literal check) | Wildcard matching (`*:*:platform` etc.) not implemented; `has_permission()` does literal string `in` check on the user's set; `*` is not a wildcard, only a literal segment. The 5 ms perf claim is untested. | 🔴 |
| 4.2.2 | Scope Hierarchy Enforcement | DONE | DONE | `app/services/dynamic_entity_service.py:60 _get_org_context()`, `app/services/dynamic_entity_service.py:117,200,272,314,399` (apply context to CRUD/list) | — (server-side only) | `_get_org_context()` is only called in `DynamicEntityService`; static models in `app/models/` use ad-hoc `tenant_id` filters in services. No central enforcement helper for the broader codebase. | 🟡 |
| 4.2.3 | Frontend RBAC Filtering | DONE | DONE | `app/routers/auth.py:202-210` (login response includes `permissions`), `app/routers/auth.py:354-362` (token refresh includes `permissions`) | `frontend/assets/js/rbac.js:132 hasPermission()`, `rbac.js:40,84,146` (`is_superuser` short-circuit), `frontend/assets/js/app.js:213` (menu filter) | The "redirect to 403 page on direct nav" guard was not located — confirm in `frontend/assets/js/router.js` | 🟢 |
| 4.2.4 | Per-Entity Permission Enforcement | OPEN | **MISSING** | `app/models/data_model.py:91 EntityDefinition.permissions` (JSONB column exists, schema-only) | — | `DynamicEntityService` does NOT read `entity.permissions` before any CRUD op (grep against `app/services/dynamic_entity_service.py` returns no matches for `permissions` or per-role check); column is dead weight today | 🔴 |

## 3. Gaps

### 🔴 High

- [ ] **4.1.1** Add role CRUD: `POST/PUT/DELETE /api/v1/rbac/roles` and the dependent-count 409 guard. **Files**: `backend/app/routers/rbac.py` (new handlers), `backend/app/schemas/role.py` (request bodies). **Effort**: M.
- [ ] **4.2.1** Replace literal `in` check in `has_permission()` (`backend/app/core/dependencies.py:108-135`) with segment-wise wildcard match. Mirror the same change in `frontend/assets/js/rbac.js:132`. Add a unit test for `*:*:platform` and `invoices:*:company`. **Effort**: S.
- [ ] **4.2.4** Wire `EntityDefinition.permissions` into `DynamicEntityService` create/read/update/delete paths (`backend/app/services/dynamic_entity_service.py`). When the JSONB is `null`, fall back to global RBAC; when populated, evaluate the user's role set against the action map. **Effort**: M.

### 🟡 Medium

- [ ] **4.2.2** Generalize `_get_org_context()` (currently lives only in `DynamicEntityService`) into a shared helper at `backend/app/core/scope.py` so static models can opt in. Audit every service that filters by `tenant_id` and migrate to the helper. **Effort**: M.

### 🟢 Low

- [ ] **4.2.3** Verify (or add) the 403 redirect guard for direct route navigation in `frontend/assets/js/router.js`. Today the menu hides routes the user can't access, but typing the URL may still load the page. **Effort**: S.

## 4. Drift notes

- **4.1.1**: BACKLOG.md tags this story `[DONE]`, but the canonical create/update/delete endpoints for the `Role` entity itself do not exist. Only assignments (role↔permission, user↔role, group↔role) have CRUD. A tenant admin literally cannot create a custom role through the API today. The frontend layout described (split-pane with system + tenant role sections) presumes endpoints that aren't present.
- **4.2.1**: `has_permission(permission)` does `if permission not in user_permissions` (literal string match against a set). The AC promises segment-wise wildcards. `*:*:platform` would only match a permission whose code literally equals the four characters `*:*:platform` — there is no parsing or pattern matching.
- **4.2.4**: This one is honestly tagged `[OPEN]` but the audit confirms it: even the model column exists and is unused. No upgrade path is wired.

## 5. Verdict

`BACKLOG.md` row for Epic 4 currently reads "Mostly DONE; Entity Perms OPEN". Ground truth is closer to **"Mixed: assignments DONE; role CRUD + wildcards + entity perms OPEN"**. The single most impactful next action is fixing **4.1.1 role CRUD**: without it, the entire RBAC admin UX is unreachable, and 4.1.2/4.1.3 (which ARE done) cannot be exercised end-to-end on a fresh tenant without seed data.

## Decisions

- Status taxonomy applied: Story 4.1.1 marked DRIFT (not MISSING) because the `Role` model and read endpoints exist; only mutation endpoints are absent.
- Story 4.2.1 marked DRIFT (not MISSING) because the `has_permission()` function is implemented but its semantics deviate from the AC.
- Story 4.2.4 marked MISSING (not DRIFT) because no enforcement code exists at all; the JSONB column is schema-only.

## Open Questions

- Should the AC for 4.2.1 be relaxed to literal matches (the implemented behavior), or should the implementation be upgraded to wildcards as written? The AC was intentional — recommend upgrading the code.
- Are there any role CRUD endpoints in a different router (e.g. `org`, `settings`) that this audit missed? `grep -rn '@router.*roles' backend/app/routers/` would confirm; the search above was scoped to `rbac.py` only.
