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
| reports | 17 | ⬜ | definitions, parameters, run, export, schedules, history |
| dashboards | 16 | ⬜ | dashboards, KPI/chart widgets, sharing, filters, drill-down |
| modules / module-registry / module-extensions | 44 | ⬜ | enable/disable, manifest, extensions |
| scheduler | 14 | ⬜ | jobs, configs (hierarchical), runs |
| admin / security | 28 | ⬜ | policies, sessions, login-attempts, notification config/queue |
| menu | 11 | ⬜ | menu tree, admin, sync preview/status/history |
| lookups | 8 | ⬜ | configurations, cascading-rules, options |
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
