---
artifact_id: test-report-e2e-api
type: test-report
producer: D1 QA Engineer
consumers: [C1 Tech Lead, C2 Backend Developer, E1 DevOps Engineer]
upstream: [test-plan-e2e-api]
downstream: []
status: draft
created: 2026-06-16
updated: 2026-06-16
---

# Test Report — Backend API E2E (live container)

## Run summary

| | |
|---|---|
| Date | 2026-06-16 |
| Target | `http://localhost:8000` (container `app_buildify_backend`) |
| Command | `docker exec app_buildify_backend python -m pytest tests/e2e --confcutdir=tests/e2e` |
| Result | **277 passed, 0 failed, 0 xfailed** (77s) — after DEF-001…007 fixes |
| Scope this run | deep: auth, rbac, org, data-model, dynamic-data (+provisioning), workflows, automations, admin/security; health/openapi; all-router GET smoke sweep |

## What is covered now

- **auth** (19) — login (envelope, wrong-pw →401, unknown →401, malformed →422),
  me GET/PUT, refresh (valid/invalid/access-as-refresh), password-policy,
  change-password, reset request/confirm, logout (blacklist + requires-auth).
- **rbac** (23) — permissions catalogue + grouped + categories + by-id,
  roles read + full create/get/update/delete lifecycle, permission assign
  (single bare-array + bulk grant/revoke), groups, user roles/permissions,
  organization-structure. Identity rules enforced (superadmin can't create
  tenant-scoped roles; tenant admin can).
- **org** (22) — tenant CRUD; company→branch→department hierarchy create→
  read→update→delete; tenant-user authz scoping (can create company, denied
  branch create + company delete); 404/422/auth negatives.
- **data-model** (16) — design-time entity + field CRUD, clone, field
  soft-delete/restore/permanent, migration preview, introspection (no DDL/publish).
- **dynamic-data** (14) — self-contained publish→record CRUD, list/search/
  paginate, aggregate, bulk create, metadata, tenant scoping, auth negatives.
- **admin/security** (32) — security policies CRUD (system default vs.
  tenant-specific, duplicate-tenant guard, soft-delete semantics), locked
  accounts, active sessions (list/limit/revoke/revoke-all), login attempts
  (email/success filters), notification config + queue (status filter).
- **Smoke sweep** — OpenAPI-driven, every parameterless GET across all 23
  routers: not-5xx as superadmin + 401/403 as anonymous (~117 endpoints).

## Defects found

### DEF-001 — `GET /api/v1/org/companies` returned 500 — ✅ FIXED 2026-06-16
- **Severity**: High (core org endpoint, broke company listing).
- **Root cause**: an orphan company row (`TESTCOMP`) had `tenant_id = NULL`.
  The `Company` model declares `tenant_id nullable=False`, but the live DB's
  column had drifted to nullable, allowing the bad row. The required
  `CompanyResponse.tenant_id: str` then raised a Pydantic `ValidationError`
  during response serialization → FastAPI returned 500. A single malformed row
  took down the whole list endpoint.
- **Fix** (`backend/scripts/fix_company_tenant_not_null.sql`): deleted the
  tenant-less orphan (no dependent branches/departments), then
  `ALTER TABLE companies ALTER COLUMN tenant_id SET NOT NULL` to restore the
  model invariant and prevent recurrence. Verified: endpoint now returns 200
  with 6 companies; `xfail` removed; full suite green (140 passed).
- **Note**: the superadmin (`users.tenant_id = NULL`) is unaffected — that is a
  different table and a deliberate cross-tenant design; the constraint is on
  `companies` only.
- **Follow-up**: ✅ DONE 2026-06-16 — Alembic's 6 heads were unified with a
  merge revision (`009300f92b21`), and migration `ec859b2a490c` now enforces
  `tenant_id NOT NULL` on companies + branches + departments in version
  control (the latter two were also drifted to nullable). Verified on a fresh
  DB (`alembic upgrade head` → single head, all three NOT NULL) and via a
  down/up round-trip on the dev DB. The one-off `fix_company_tenant_not_null.sql`
  is now superseded.

### DEF-002 — RBAC permission/role/group assignment 500s — ✅ FIXED 2026-06-16
- **Severity**: High (core RBAC: you could not assign permissions to roles,
  members to groups, or roles to groups — all 500).
- **Root cause**: `app/routers/rbac.py` constructed junction rows with the
  wrong keyword — `granted_by_id` / `added_by_id` — but the models
  (`RolePermission`, `GroupRole`, `UserGroup`) name the column
  `granted_by_user_id` / `added_by_user_id` → `TypeError` at 4 sites
  (lines 641, 746, 962, 1047).
- **Fix**: corrected all four kwargs to the actual model column names. Verified
  via the new rbac e2e suite (assign single + bulk now 200).

### DEF-003 — published entities have no backing table → runtime 500 — ✅ FIXED 2026-06-16
- **Severity**: Medium-High (data integrity + poor error surface).
- **Observed**: seeded entities (`customer`, `order`, `generic_contact/document/task`)
  were `status = published` but their tables (`customers`, `orders`,
  `platform_contacts/documents/tasks`) did not exist — collateral of DEF-004/005
  breaking the DDL at publish time. `GET /dynamic-data/customer/records` returned
  **500** (`psycopg2 UndefinedTable`).
- **Fix (two parts)**:
  1. *Runtime hardening* — `routers/dynamic_data.py` now maps a missing backing
     table (Postgres SQLSTATE `42P01`, matched along the exception cause chain)
     to a clean **409** "table not provisioned" at every record endpoint
     (list/get/create/update/delete/bulk/aggregate) instead of a 500.
  2. *Data repair* — regenerated the CREATE DDL via the (now-fixed)
     `MigrationGenerator` and executed it for the 5 distinct missing tables
     (customer/order are shared per-tenant tables → one physical table each).
     All 24 published entities now have backing tables.
- **Regression test**: `tests/e2e/test_dynamic_data_provisioning.py` publishes an
  entity, drops its table out of band, and asserts list+aggregate return 409.

### DEF-006 — `GET /workflows/instances` unreachable (422) — ✅ FIXED 2026-06-16
- **Severity**: Medium (workflow instance listing was impossible).
- **Root cause**: in `routers/workflows.py` the parameterized `GET /{workflow_id}`
  route was declared before the literal `GET /instances`, so FastAPI matched
  `/workflows/instances` against `/{workflow_id}` and 422'd trying to parse
  "instances" as a UUID.
- **Fix**: moved the literal `/instances` list route above `/{workflow_id}`
  (with a comment explaining the ordering requirement). Verified via the
  workflow e2e suite.

### DEF-005 — entity publish generates unquoted string DEFAULTs → 500 — ✅ FIXED 2026-06-16
- **Severity**: High (blocked publishing any entity with a select/enum default,
  e.g. `customer.status`, `order.status`).
- **Root cause**: `migration_generator._generate_field_definition` only quoted
  DEFAULTs for a fixed list of text `field_type`s; `select`/`enum` fields (stored
  as VARCHAR) fell through to an unquoted `DEFAULT active`, which PostgreSQL
  parses as a column reference → `cannot use column reference in DEFAULT
  expression`. Found while repairing DEF-003.
- **Fix**: quote the DEFAULT whenever the field is a string-ish type **or** the
  SQL data type is a character type (VARCHAR/CHAR/TEXT/CITEXT).

### DEF-004 — entity publish generates invalid DDL → 500 — ✅ FIXED 2026-06-16
- **Severity**: High (core NoCode feature: publishing *any* entity failed).
- **Root cause**: `app/services/migration_generator.py._generate_create_table`
  emitted audit columns (`created_at`, `updated_at`, …) unconditionally while
  ALSO emitting the entity's auto-created system fields of the same name →
  `CREATE TABLE ... column "created_at" specified more than once` → 500.
- **Fix**: build a `reserved_col_names` set (id + scope + audit + soft-delete)
  and skip any user/system field that collides with an auto-generated column.
  Verified: publish + full record CRUD cycle now green (dynamic-data suite).

### DEF-007 — 3 admin/security list endpoints 500 when combined with a filter — ✅ FIXED 2026-06-16
- **Severity**: Medium (filters are the primary way an admin narrows these
  audit/monitoring lists; every filtered call failed).
- **Root cause**: `app/routers/admin/security.py` built the base query with
  `.order_by(...).limit(limit)` applied *before* the conditional `.filter(...)`
  calls — SQLAlchemy raises `InvalidRequestError: Query.filter() being called
  on a Query which already has LIMIT or OFFSET applied` the moment a filter is
  appended afterward. Hit in three places: `list_active_sessions` (`user_id`/
  `tenant_id` filters), `list_login_attempts` (`email`/`success` filters),
  `list_notification_queue` (`status`/`notification_type` filters).
- **Fix**: reordered each to apply all conditional `.filter()` calls first and
  append `.order_by().limit()` last, right before `.all()`. Verified via
  `tests/e2e/test_admin_security.py` (email/success/status filter cases) and
  the full suite.

## Environment notes / gotchas (for whoever runs this next)

1. **`max_concurrent_sessions = 3`** evicts the *oldest* session — naive test
   suites that log in repeatedly will silently invalidate a shared token. The
   harness handles this via auto-reauth clients + the `ephemeral` fixture.
2. The stale `tests/conftest.py` (in-process harness) fails to import on the
   current image (`Base` moved out of `app.core.db`) — always pass
   `--confcutdir=tests/e2e`.
3. `requests` is not installed in the running image despite being in
   `requirements.txt`; the suite uses **httpx** (which is present).

## Not yet covered (backlog)

Deep per-router coverage still pending for: reports, dashboards,
modules / module-registry / module-extensions, scheduler,
menu, lookups, settings, metadata, data, builder, templates, audit.
(auth, rbac, org, data-model, dynamic-data, workflows, automations, and
admin/security are now deep.) The smoke sweep already exercises all of them at the GET level. See the
coverage matrix in [`test-plan-e2e-api.md`](../test-plans/test-plan-e2e-api.md).
