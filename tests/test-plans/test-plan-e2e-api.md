---
artifact_id: test-plan-e2e-api
type: test-plan
producer: D1 QA Engineer
consumers: [C1 Tech Lead, E1 DevOps Engineer, C2 Backend Developer]
upstream: [BACKLOG.md, api-inventory-e2e]
downstream: [test-report-e2e-api]
status: draft
created: 2026-06-16
updated: 2026-06-16
decisions:
  - Black-box live-container testing (pytest + httpx) rather than in-process TestClient — exercises the deployed artifact end to end.
  - Run inside app_buildify_backend (owns pytest + httpx); no host deps needed.
  - `--confcutdir=tests/e2e` isolates from the in-process tests/conftest.py.
open_questions:
  - Should this run in CI against an ephemeral compose stack per PR (recommended once epic-19 CI lands)?
---

# Test Plan — Backend API E2E (live container)

## 1. Objective

Exhaustively exercise the App-Buildify backend HTTP API **as a black box**
against the running `app_buildify_backend` container, covering every router
with positive, negative, edge, and authorization cases. Catches regressions
in routing, middleware, auth, RBAC, serialization, and persistence that
in-process unit tests cannot.

## 2. Target & environment

| Item | Value |
|------|-------|
| Base URL | `http://localhost:8000` |
| API prefix | `/api/v1` |
| Stack | `infra/docker-compose.dev.yml` via `./manage.sh start postgres` |
| DB | PostgreSQL `appuser/apppass@appdb` (seeded: `seed_complete_org`) |
| Superadmin | `superadmin@system.com` / `SuperAdmin123!` |
| Tenant user | `ceo@techstart.com` / `password123` (low-privilege) |
| Runner | `docker exec app_buildify_backend python -m pytest tests/e2e --confcutdir=tests/e2e` |

Full route catalogue: [`api-inventory-e2e.md`](api-inventory-e2e.md) — 23 routers, 277 operations.

## 3. Test design

- **Harness** (`backend/tests/e2e/conftest.py`): auto-reauthenticating clients
  (`su`, `user`), an `anon` client, an `ephemeral` login factory that releases
  its session slot, a `unique` name factory, and a live-API connectivity guard.
- **Session-limit awareness**: the platform enforces `max_concurrent_sessions=3`
  and evicts the *oldest* session. Shared clients re-auth on 401; one-off logins
  use `ephemeral`. (Discovered during harness bring-up — see DEF tracking.)
- **Known defects** are `xfail(strict=True)` with a `DEF-NNN` reason so the run
  stays green while still flagging the regression the moment it is fixed.

## 4. Coverage matrix (by router)

Legend: ✅ deep (positive+negative+edge+authz) · 🟡 smoke only (auto GET sweep) · ⬜ not started

| Router | Ops | Status | Notes |
|--------|----:|:------:|-------|
| auth | 9 | ✅ | login/refresh/me/logout/change-pw/reset/password-policy, all branches |
| health/openapi | 3 | ✅ | healthz, openapi served, 404 handling |
| _all routers (parameterless GET)_ | — | 🟡 | OpenAPI-driven sweep: not-5xx (authed) + requires-auth (anon) |
| rbac | 23 | ✅ | roles/permissions/groups CRUD, permission assign (single+bulk), user-roles, org-structure |
| org | 21 | ✅ | tenant CRUD + company→branch→department hierarchy lifecycle + tenant-user scoping |
| data-model | 26 | ✅ | entity + field design-time CRUD, clone, soft-delete/restore/permanent, migration preview, introspect |
| dynamic-data | 11 | ✅ | publish→record CRUD (create/get/update/delete), list/search/paginate, aggregate, bulk, tenant scoping |
| workflows | 20 | ✅ | definition CRUD, states, transitions, publish/unpublish/simulate, instance create→execute→history |
| automations | 16 | ✅ | rules CRUD + toggle/test/execute, executions, action-templates, webhooks CRUD |
| reports | 17 | ✅ | definitions CRUD + base_entity derivation, execute/export/history, preview (flat+designer), lookup, schedules CRUD, templates, join-suggestions; SQL injection regression (DEF-011) |
| dashboards | 16 | ✅ | dashboard CRUD + clone, page CUD, widget CUD + bulk-update + data 404, share creation, snapshot; auth-required on every group; DEF-019 (UUID/default missing on 6 models + int path params → fixed), DEF-020 (shared_with_role_id model/DB mismatch → fixed), DEF-021 (snapshot UUID serialization → fixed) |
| modules / module-registry / module-extensions | 44 | ✅ | module-registry reads/install/uninstall/enable/disable/configure/register/heartbeat/sync; nocode-modules CRUD/dependencies/versions/validation/components; entity/screen/menu extension CRUD |
| scheduler | 14 | ✅ | configs CRUD + effective-config resolution + system-level superuser-only, jobs CRUD + execute + schedule-required validation, executions list/get + status filter, execution logs; IDOR regression (DEF-016), creation-breaking type/default (DEF-015), status-param shadow 500→404 (DEF-017), no-schedule 500→422 (DEF-018) |
| admin / security | 14 | ✅ | policies CRUD (incl. soft-delete semantics), locked-accounts, sessions, login-attempts (filters), notification config/queue (filters) |
| menu | 11 | ✅ | user menu (DEF-022: 500→200 after builder_pages VARCHAR/UUID fix), admin list, CRUD + 422/400/404 negatives, duplicate-code 400 (DEF-023), update-unknown-404 (DEF-024), system-item delete 404 for tenant user, reorder, sync status/history/preview; auth-required on every group |
| lookups | 8 | ✅ | configuration CRUD + list/filter, lookup data (static_list + search + pagination), cascading-rule create/list + filter; 422/400/404 negatives; auth-required on all endpoints; no defects found |
| settings | 4 | ⬜ | tenant + user settings |
| metadata / data / builder / templates / audit | — | ⬜ | remaining surface |

## 5. Cross-cutting cases (every router)

1. **AuthN**: anonymous request → 401/403; garbage bearer → 401/403.
2. **AuthZ**: low-privilege `user` denied where superadmin is allowed (403).
3. **Validation**: malformed body → 422 with structured `details`.
4. **Not found**: unknown id → 404 (not 500).
5. **Tenant isolation**: a resource created under tenant A is invisible to tenant B.
6. **Lifecycle round-trip**: create → read → update → list (filtered) → delete.

## 6. Exit criteria

- Every operation in the inventory has ≥1 positive and ≥1 negative case.
- No unexpected 5xx; all 5xx are tracked `DEF-NNN` xfails with an owner.
- Suite runs green (`passed` + `xfailed`, zero `failed`) in the dev stack.
