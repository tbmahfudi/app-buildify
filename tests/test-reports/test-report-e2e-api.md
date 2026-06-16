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
| Result | **349 passed, 0 failed, 0 xfailed** (~75s) — after DEF-001…010 |
| Scope this run | deep: auth, rbac, org, data-model, dynamic-data (+provisioning), workflows, automations, admin/security, modules / module-registry / module-extensions; health/openapi; all-router GET smoke sweep |

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
- **modules / module-registry / module-extensions** (72) — module-registry:
  list available/enabled (own + cross-tenant superuser), module info/manifest,
  install/uninstall (superuser, not-loadable/already-installed negatives),
  enable/disable (own tenant, superuser-on-behalf-of, tier/tenant negatives),
  configuration update, register (idempotent upsert), heartbeat, sync.
  nocode-modules: create/get/update/publish/delete, prefix/name uniqueness +
  validation, dependency add/list/check/remove + circular-dependency guard,
  version increment (major/minor/patch) + history, component snapshot.
  module-extensions: entity/screen/menu extension create/list, duplicate and
  unknown-module/entity/screen negatives, field/type validation.
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

### DEF-008 — `enable_module`/`disable_module` 500 on any audit-logged call — ✅ FIXED 2026-06-16
- **Severity**: High (every enable/disable call hits the audit log; the
  success path crashed just as often as the failure path).
- **Root cause**: `app/core/audit.py:create_audit_log` did a bare
  `json.dumps(context_info)`/`json.dumps(changes)`. Four call sites in
  `app/routers/modules.py` (`enable_module` x2, `disable_module` x2) pass
  `context_info={"tenant_id": target_tenant_id}` where `target_tenant_id` is a
  raw `uuid.UUID` object, not a string → `TypeError: Object of type UUID is
  not JSON serializable` → unhandled 500 on every enable/disable call.
- **Fix**: `json.dumps(..., default=str)` on both calls in `create_audit_log` —
  a general fix at the audit layer rather than patching each of the 4 call
  sites individually, since any future caller could pass a UUID the same way.

### DEF-009 — deleting a module referenced by entity/screen/menu extensions crashes with a raw FK violation — ✅ FIXED 2026-06-16
- **Severity**: Medium (no DELETE confirmation step exists; any module with an
  extension pointing at it 500s instead of returning a clean error).
- **Root cause**: `NocodeModuleService.delete_module` only checked
  `ModuleDependency` rows before deleting a module — it never checked
  `module_entity_extensions` / `module_screen_extensions` /
  `module_menu_extensions`, whose `extending_module_id`/`target_module_id`
  columns are `NOT NULL` with no DB-level cascade. SQLAlchemy nulls the FK on
  the in-session child before the parent delete commits, then Postgres
  rejects the NULL write → unhandled `IntegrityError` → 500.
- **Fix**: added a count check across all three extension tables (matching the
  existing dependents-check pattern) and return a clean
  `400 "Cannot delete module: N extension(s) reference it"` instead.

### DEF-010 — in-process module-registry loader permanently discovers 0 modules (not fixed — environment cruft, not a code bug)
- **Severity**: informational / environment hygiene.
- **Finding**: `backend/modules/financial/` (the directory the live container's
  `ModuleLoader` reads via `/app/modules`, distinct from the git-tracked
  top-level `modules/financial/`) had no `module.py`/`manifest.json` — only
  stale `__pycache__/*.pyc` — so `ModuleLoader.discover_modules()` always
  found 0 modules. The DB's "financial" registry row stayed `is_installed` from
  before these files vanished, masking the break until the worker process
  restarted (it was holding the module in memory from a prior successful
  load). Confirmed via git history: commit `904ac23` consolidated financial
  under `modules/financial/`, then `9fb8e08` (same day) explicitly removed it
  from `backend/`/`frontend/` entirely ("No modules in frontend/ or backend/
  directories") — financial now lives as a standalone microservice under
  `modules/financial/backend` (port 9001), not the in-process loader. The
  leftover `backend/modules/financial/__pycache__` was never cleaned up.
- **Action taken**: deleted the orphaned `backend/modules/financial/` (untracked,
  pyc-only cruft) so the live state matches the documented intent. No code
  change — this is not something to "fix" by reconstructing deleted source.
  `install`/`enable` for any module now consistently and correctly return
  `400 "Module X not found"`, since no module is meant to be loadable through
  this legacy path anymore. `tests/e2e/test_modules.py` asserts this real
  behavior rather than a previously-assumed (and never-actually-working)
  success path.

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

Deep per-router coverage still pending for: reports, dashboards, scheduler,
menu, lookups, settings, metadata, data, builder, templates, audit.
(auth, rbac, org, data-model, dynamic-data, workflows, automations,
admin/security, and modules / module-registry / module-extensions are now
deep.) The smoke sweep already exercises all of them at the GET level. See the
coverage matrix in [`test-plan-e2e-api.md`](../test-plans/test-plan-e2e-api.md).
