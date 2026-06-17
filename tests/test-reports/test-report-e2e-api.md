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
| Result | **544 passed, 0 failed, 0 xfailed** (~257s) — after DEF-001…026 |
| Scope this run | deep: auth, rbac, org, data-model, dynamic-data (+provisioning), workflows, automations, admin/security, modules / module-registry / module-extensions, reports, scheduler, dashboards, menu, lookups, settings; health/openapi; all-router GET smoke sweep |

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
- **reports** (47) — report definition CRUD lifecycle (create/get/update/
  delete, base_entity derivation from data_source, category filter, 422/404
  negatives); execute (success, unknown-report 404, export-to-csv,
  execution history); preview (flat + designer payload formats, empty-when-
  no-entity, group_by+aggregation, order_by, legit filter); lookup (success,
  search, malicious-input negatives); schedules CRUD lifecycle; templates
  list + use-unknown 404; join-suggestions; auth-required on every group;
  **SQL injection regression coverage** — original exploit payload plus 9
  malicious-identifier payloads (base_entity, column, group_by, order_by
  field/direction, aggregation, lookup entity/display_field/value_field/
  filter_conditions key) all asserted rejected.
- **settings** (23) — user settings: get (auto-create on first access, idempotent),
  update theme/language/timezone/density/preferences dict, get reflects update;
  tenant settings: get (auto-create, idempotent), update primary/secondary color
  and tenant_name, update with explicit own tenant_id; cross-tenant 403; superadmin
  gets defaults for no-tenant context; auth-required on all 4 endpoints;
  **DEF-025 regression** (PUT /settings/tenant 500→200 for tenant users);
  **DEF-026 regression** (PUT /settings/tenant?tenant_id=<own> 403→200).
- **lookups** (36) — configuration CRUD lifecycle (create/get/update/delete);
  list (plain array, source_type filter, unknown-type returns empty list);
  soft-delete verified (deleted config absent from list and returns 404 on get);
  lookup data for static_list (items/total_count/has_more, search filter,
  pagination); cascading-rule create + list (plain array, filter by
  parent_lookup_id, filter by child_lookup_id); 422 on missing required fields
  (name/label/source_type for configs; name/parent_lookup_id for rules);
  400 on duplicate config name; 404 on every unknown-id path; auth-required
  (403) on every endpoint. No RBAC permission gates on this router
  (any authenticated user may CRUD). No defects found.
- **menu** (21) — user menu (RBAC-filtered, all authenticated users); admin
  item list; CRUD lifecycle (create/get/update/delete + 422 on missing required
  fields); duplicate-code 400 (DEF-023 regression); unknown-id 404 for get/
  update/delete; system-item delete blocked for non-superuser (404); reorder
  (single item + empty list); sync status/history/preview + auth-required on
  all sync endpoints; DEF-022 regression (`GET /menu` must return 200 list).
- **dashboards** (29) — dashboard CRUD lifecycle (create/get/update/delete,
  list with category and favorites filters, clone); page create/update/delete
  (incl. page appears in dashboard detail response); widget create/update/delete
  + bulk-update (drag-drop reposition); widget data 404 for unknown widget;
  share creation (user-targeted, unknown-dashboard 400/404); snapshot creation,
  unknown-dashboard 404; auth-required on every group;
  **DEF-019 UUID regression** — all create responses asserted `uuid.UUID(id)` to
  catch any recurrence of the int/default bug.
- **scheduler** (39) — configs CRUD lifecycle (create/get/update/delete,
  effective-config resolution, system-level superuser-only, tenant-level
  requires tenant_id, cross-tenant tenant_id rejected on create); jobs CRUD
  + manual execute, schedule-required validation, unknown-config 400,
  cross-tenant tenant_id rejected on create, list ignores a foreign
  `tenant_id` query param; executions list/get + status filter; execution
  logs; 404 negatives on every by-id endpoint; auth-required on every
  group; **cross-tenant IDOR regression coverage** — every by-id
  get/update/delete/execute/list/logs endpoint asserted 403 for a second
  tenant (DEF-016).

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

### DEF-011 — SQL injection in the report query engine (cross-tenant data exposure) — ✅ FIXED 2026-06-17
- **Severity**: Critical (authenticated SQL injection, exploitable by any user
  holding `reports:execute:tenant` — leaks every tenant's data, not just the
  caller's own).
- **Root cause**: `app/services/report_service.py`'s `_build_and_execute_query`,
  `_build_filter_sql`, and `get_lookup_data` built raw SQL via direct Python
  f-string interpolation of filter values, table names, column names,
  aggregation function names, group_by/order_by fields, and sort direction —
  none escaped, parameterized, or allow-listed.
- **Confirmed exploit**: `POST /api/v1/reports/preview` with
  `base_entity="users"`, a filter on `email` with value `"x' OR '1'='1"` —
  returned all 25 users across every tenant instead of the caller's own.
- **Fix (full scope, per explicit request)**:
  1. All filter *values* are now bound via SQLAlchemy parameters
     (`:f0`, `:f1`, … allocated through a shared counter that survives
     recursive nested filter groups).
  2. Every interpolated *identifier* (base_entity/table, select columns,
     group_by fields, order_by fields, lookup entity/display_field/
     value_field/filter-condition keys) is validated against the table's real,
     live column set fetched via a safely-bound `information_schema.columns`
     query (`_get_table_columns`) — an empty result also rejects unknown
     tables. Validated identifiers are then double-quoted
     (`_quote_identifier`, escaping embedded quotes) as defense-in-depth.
  3. `aggregation` is allow-listed against `{sum, avg, count, min, max, none}`
     and order-by direction against `{asc, desc}`.
  4. A new `ReportQueryValidationError(ValueError)` distinguishes "malformed/
     malicious request" (→ 400) from the pre-existing "not found" `ValueError`
     semantic (→ 404) elsewhere in the same file; wired into
     `execute_report`/`execute_and_export_report` in `routers/reports.py`
     (preview/lookup already mapped generic exceptions to 400, so needed no
     change).
- **Verification**: original exploit payload now returns
  `{'data': [], 'columns': ['id', 'email'], 'row_count': 0}`; 6+ legitimate
  usage patterns (filters, group_by+aggregation, order_by, lookup+search)
  still work; 9+ malicious-identifier payloads across preview and lookup all
  rejected with 400. Regression: `tests/e2e/test_reports.py::TestPreview` /
  `TestLookup`.

### DEF-012 — Tenant Administrator role seeded with zero `reports:*` permissions — not fixed in seed data, worked around in harness
- **Severity**: Medium (the reports feature was unreachable out of the box for
  any seeded tenant user — `ceo@techstart.com`'s "Tenant Administrator" role
  held none of the 13 `reports:*` permission codes despite all of them
  existing in the catalogue).
- **Fix taken**: a session-scoped autouse test fixture
  (`_grant_reports_permissions` in `tests/e2e/test_reports.py`) self-grants
  the 13 `reports:*` permission codes to the caller's own tenant copy of the
  `tenant_admin` role (there are two rows named "Tenant Administrator" — a
  platform template with `tenant_id=NULL` and each tenant's own copy; matched
  by `code == "tenant_admin" and tenant_id == caller's tenant_id`) via the
  existing `POST /rbac/roles/{id}/permissions` endpoint.
- **Not done**: the seed-data script itself was not changed, so a fresh
  database still seeds the Tenant Administrator role without `reports:*`
  permissions. Flag for whoever owns seed data if this should ship fixed.

### DEF-013 — bad seed-data row (`report_type='dashboard'`) broke `GET /reports/definitions` for the entire TechStart tenant — ✅ FIXED 2026-06-17
- **Severity**: High (core report-listing endpoint 500'd for every user in
  the tenant, not just the one bad row's owner).
- **Root cause**: a seeded `report_definitions` row ("Employee Performance
  Dashboard", TechStart tenant) had `report_type='dashboard'`, which is not a
  valid `ReportType` enum value (`tabular|summary|crosstab|metric|chart` —
  confirmed via `app/schemas/report.py` and a grep showing no code anywhere
  handles `'dashboard'` specially, i.e. this is bad data, not an
  unimplemented type). Pydantic response validation rejected the row →
  `ResponseValidationError` → 500 for the whole list endpoint.
- **Fix**: direct data correction,
  `UPDATE report_definitions SET report_type = 'tabular' WHERE report_type = 'dashboard'`
  (mirrors the DEF-001 precedent of fixing bad data rather than papering over
  it in code). Verified zero remaining bad rows.

### DEF-014 — `execute_and_export_report` returned 500 instead of 404 for an unknown report — ✅ FIXED 2026-06-17
- **Severity**: Medium (a clean not-found case surfaced as a server error).
- **Root cause**: `routers/reports.py`'s `execute_and_export_report` raises a
  404 `HTTPException` via `not_found_exception(...)` when the report
  definition doesn't exist, but the function's except chain had no
  `except HTTPException: raise` guard before the trailing
  `except Exception as e: raise HTTPException(500, ...)` — since
  `HTTPException` IS-A `Exception`, the catch-all swallowed the 404 and
  re-raised it as a 500.
- **Fix**: added `except HTTPException: raise` as the first except clause,
  before `ReportQueryValidationError`/`ValueError`/`ImportError`/`Exception`.
  Found via the new negative test
  `test_execute_export_unknown_report_404`.

### DEF-015 — every scheduler create call 500'd; every by-id read/update/delete 422'd — ✅ FIXED 2026-06-17
- **Severity**: Critical (the entire scheduler write surface was broken out of the box).
- **Root cause (two independent bugs compounding each other)**:
  1. `SchedulerConfig`, `SchedulerJob`, `SchedulerJobExecution`, and
     `SchedulerJobLog` all declared `id = Column(GUID, primary_key=True, index=True)`
     with **no `default=generate_uuid`**. Every other GUID-PK model in the codebase
     (`User`, `Tenant`, `Role`, `WorkflowDefinition`, `Automation`, `DataModel`, etc.)
     includes this default. The service layer never explicitly set `id=` either →
     Postgres `NotNullViolation` on every INSERT.
  2. All four Pydantic response schemas and all router path-param annotations typed
     the scheduler IDs as **`int`**, while the actual DB columns (and every FK
     referencing them) are genuinely `uuid` — confirmed via
     `information_schema.columns`. A manually-inserted UUID-keyed row 422'd
     ("unable to parse string as an integer") on any GET/PUT/DELETE by id.
- **Fix**: added `default=generate_uuid` to all four model PK columns
  (`app/models/scheduler.py`); changed every `int` annotation to `UUID` across
  all four response schemas and all router path params
  (`app/schemas/scheduler.py`, `app/routers/scheduler.py`). Also updated the
  single FK reference in `SchedulerJobCreate.config_id` from `int` → `UUID`.
- **Exploit confirmed live** before fix: `POST /api/v1/scheduler/configs` →
  `500 psycopg2.errors.NotNullViolation: null value in column "id"`;
  manually-inserted row → `GET .../configs/<uuid>` →
  `422 Input should be a valid integer, unable to parse string as an integer`.
- **Regression tests**: `TestConfigs::test_create_get_update_delete` (verifies
  `uuid.UUID(cid)` on the returned id); `TestJobs::test_create_get_update_delete`.

### DEF-016 — scheduler IDOR: 8+ endpoints had zero tenant-ownership checks — ✅ FIXED 2026-06-17
- **Severity**: Critical/High (IDOR — any authenticated user with a scheduler
  permission could read, modify, or delete another tenant's scheduler configs,
  jobs, executions, and logs; two create endpoints accepted an arbitrary
  caller-supplied `tenant_id` enabling cross-tenant writes; `list_scheduler_jobs`
  honored an explicit foreign `tenant_id` query param enabling cross-tenant reads).
- **Root cause**: `has_permission(...)` in `app/core/dependencies.py` only checks
  whether the caller's granted permission codes match the required code — it does
  **not** verify that the resource being acted upon belongs to the caller's tenant.
  Tenant-scoping must be enforced explicitly in router or service code. Affected
  endpoints: `get_scheduler_config`, `update_scheduler_config`,
  `delete_scheduler_config`, `update_scheduler_job`, `delete_scheduler_job`,
  `list_job_executions`, `get_job_execution`, `get_execution_logs`. Additionally,
  `create_scheduler_config` and `create_scheduler_job` accepted any `tenant_id`
  in the request body, and `list_scheduler_jobs` honored a foreign `?tenant_id=`
  query param.
- **Note**: DEF-015's type-mismatch (int vs UUID) happened to prevent exploitation
  of DEF-016 for by-id endpoints, since the path param parsed as a 422 before
  reaching the IDOR-vulnerable handler. Fixing DEF-015 without DEF-016 would have
  made the IDOR immediately exploitable.
- **Fix**: added a shared `_enforce_tenant_access(resource_tenant_id, current_user)`
  helper (superuser bypass; `tenant_id=None` resources are superuser-only — closing
  a related loophole where system-level resources were previously visible to any
  tenant caller); applied it to every affected by-id endpoint. Added explicit
  cross-tenant guards on both create endpoints. Changed `list_scheduler_jobs` to
  always force non-superusers to their own `tenant_id` regardless of the query param.
- **Exploit confirmed live** before fix: logged in as `ceo@medcare.com` and
  successfully read/modified a config created by `ceo@techstart.com`.
- **Regression tests**: `TestConfigs::test_cross_tenant_{get,update,delete}_forbidden`;
  `TestJobs::test_cross_tenant_{get,update,delete,execute}_forbidden`;
  `TestExecutions::test_cross_tenant_{list_executions,get_execution}_forbidden`;
  `TestExecutionLogs::test_cross_tenant_get_logs_forbidden`;
  `TestJobs::test_list_jobs_ignores_foreign_tenant_id_query_param`.

### DEF-017 — `list_job_executions` returned 500 instead of 404 when job not found — ✅ FIXED 2026-06-17
- **Severity**: Medium (every request to list executions for a non-existent job
  id surfaced as a server error instead of a clean not-found).
- **Root cause**: `list_job_executions` declared `status: Optional[JobStatus] = Query(...)`
  as a query parameter, which shadowed the `fastapi.status` module imported at
  module level under the same name `status`. When `?status=` was absent the
  parameter defaulted to `None`, so the reference `status.HTTP_404_NOT_FOUND`
  in the not-found HTTPException raised `AttributeError: 'NoneType' object has
  no attribute 'HTTP_404_NOT_FOUND'`, causing a 500 instead of a 404.
  Confirmed via `docker logs` showing the full traceback rooted at
  `app/routers/scheduler.py:460, in list_job_executions`.
- **Fix**: renamed the query parameter to `execution_status` with
  `Query(None, alias="status", ...)` to preserve the external `?status=`
  contract while eliminating the name collision. Updated all internal references.
  Also added a missing `_enforce_tenant_access` call to this endpoint (part of
  DEF-016).
- **Regression test**: `TestExecutions::test_list_executions_with_status_filter_unknown_job_404_not_500`.

### DEF-018 — `SchedulerJob` creation with no schedule info silently succeeded then 500'd on read — ✅ FIXED 2026-06-17
- **Severity**: Medium (a clearly invalid job could be inserted into the DB but
  was then permanently unreadable, causing a confusing 500 on the create
  response itself).
- **Root cause**: `SchedulerJobBase.validate_scheduling` was a pydantic v1
  `@validator('cron_expression')` without `always=True`. In pydantic v1,
  validators without `always=True` are skipped when the field value uses its
  default (i.e., the field was omitted from the request). So submitting a job
  body with no `cron_expression`, `interval_seconds`, or `start_time` bypassed
  request-time validation entirely — the row was inserted into the DB. The
  validator then fired during **response serialization** (pydantic validates
  required fields on the ORM object when serializing the response), raising a
  `ResponseValidationError` → 500. The net result: the insert committed (an
  unscheduled zombie job in the DB), but the response was 500.
  Additionally, the validator was on `cron_expression` (the first of the three
  scheduling fields in declaration order), so even with `always=True` it would
  never have seen `interval_seconds` or `start_time` in the `values` dict (only
  earlier fields are present when a validator runs). Same root issue as two prior
  schema validators in this codebase that were dead code due to identical ordering.
- **Fix**: moved the validator to `start_time` (the last of the three fields,
  so both `cron_expression` and `interval_seconds` are already in `values`),
  added `always=True` so it fires even when `start_time` is omitted. Now a job
  body missing all three fields is cleanly rejected with a 422 at request time,
  and jobs with only `interval_seconds` or only `start_time` are accepted
  correctly.
- **Regression tests**: `TestJobs::test_create_requires_schedule` (422);
  `TestJobs::test_create_get_update_delete` (verifies interval_seconds-only
  job works via the `job` fixture's `cron_expression` path).

### DEF-022 — `GET /menu` (user menu) 500'd for every authenticated user — ✅ FIXED 2026-06-17
- **Severity**: Critical (`GET /menu` is the primary navigation endpoint — every logged-in user is affected; the entire app navigation was broken).
- **Root cause**: `MenuService._get_builder_page_menu_items` filtered
  `BuilderPage.tenant_id == user.tenant_id` where `BuilderPage.tenant_id` is
  `Column(String(36))` (VARCHAR in the live DB) but `user.tenant_id` is a
  `uuid.UUID` object. Postgres raised
  `ProgrammingError: operator does not exist: character varying = uuid`
  → caught by the router's bare `except Exception` → `500 "Failed to load menu"`.
- **Fix**: cast to `str(user.tenant_id)` before the filter in
  `app/services/menu_service.py::_get_builder_page_menu_items`. Analogous to
  every other VARCHAR tenant_id lookup in the codebase.
- **Regression test**: `TestUserMenu::test_returns_list` and
  `TestUserMenu::test_superuser_gets_list`.

### DEF-023 — `POST /menu` with a duplicate `code` returned 500 instead of 400 — ✅ FIXED 2026-06-17
- **Severity**: Medium (every attempt to create a menu item whose `code` already
  exists — a globally unique constraint — surfaced as a server error rather than
  a clean client error; callers couldn't distinguish "conflict" from a real crash).
- **Root cause**: `MenuItem.code` has a DB-level `UNIQUE` constraint. Creating a
  duplicate raised `psycopg2.errors.UniqueViolation` (wrapped as
  `sqlalchemy.exc.IntegrityError`). The `create_menu_item` router handler caught
  `ValueError → 400` and `Exception → 500`; `IntegrityError` is not a
  `ValueError`, so it fell into the generic 500 catch-all.
- **Fix**: added `except IntegrityError: raise HTTPException(400, "A menu item
  with this code already exists")` before the generic catch in `routers/menu.py`.
- **Regression test**: `TestMenuItemCRUD::test_create_duplicate_code_400`.

### DEF-024 — `PUT /menu/{id}` with an unknown ID returned 500 instead of 404 — ✅ FIXED 2026-06-17
- **Severity**: Medium (every update call for a non-existent menu item surfaced
  as a server error — identical root cause to DEF-014).
- **Root cause**: `update_menu_item` raised `HTTPException(404)` inside its
  `try` block when `MenuService.update_menu_item` returned `None`. The handler
  had no `except HTTPException: raise` guard before the trailing
  `except Exception → 500`, so the 404 was swallowed and re-raised as 500.
  Same pattern as DEF-014 (`execute_and_export_report`).
- **Fix**: added `except HTTPException: raise` as the first except clause in
  `update_menu_item` in `routers/menu.py`. The `delete_menu_item` and
  `reorder_menu_items` handlers in the same file already had this guard.
- **Regression test**: `TestMenuItemCRUD::test_update_unknown_404`.

### DEF-019 — every dashboard create call 500'd; every by-id read/update/delete 422'd — ✅ FIXED 2026-06-17
- **Severity**: Critical (the entire dashboard write surface was broken out of the box — same pattern as DEF-015).
- **Root cause (two independent bugs compounding)**:
  1. `Dashboard`, `DashboardPage`, `DashboardWidget`, `DashboardShare`,
     `DashboardSnapshot`, and `WidgetDataCache` all declared
     `id = Column(GUID, primary_key=True, index=True)` with **no `default=generate_uuid`**,
     causing Postgres `NotNullViolation` on every INSERT → 500.
  2. All Pydantic response schemas typed every `id` field as `int` and all
     router path params as `int`, while actual DB columns are genuinely `uuid` →
     422 ("unable to parse string as an integer") on every by-id endpoint.
- **Fix**: added `default=generate_uuid` to all 6 model PK columns
  (`app/models/dashboard.py`); changed every `int` annotation to `UUID` across
  all schemas (`app/schemas/dashboard.py`) and all router path params
  (`app/routers/dashboards.py`).
- **Exploit confirmed live** before fix: `POST /api/v1/dashboards` → 500 with
  `psycopg2.errors.NotNullViolation: null value in column "id"`.
- **Regression tests**: `TestDashboards::test_create_get_update_delete`
  (asserts `uuid.UUID(did)` on the returned id); `TestPages`,
  `TestWidgets`, `TestSharing`, `TestSnapshots` all carry the same assertion.

### DEF-020 — `dashboard_shares.shared_with_role_id` model/schema typed as GUID while DB column is `integer` — ✅ FIXED 2026-06-17
- **Severity**: High (`POST /dashboards/shares` 500'd for any share that set
  `shared_with_role_id` — i.e., role-targeted sharing was completely broken).
- **Root cause**: during the DEF-019 fix pass, `DashboardShare.shared_with_role_id`
  was changed to `GUID` in the model and `UUID` in the schema. The live DB column
  is `integer` (a legacy integer FK), so Postgres rejected the insert with
  `column "shared_with_role_id" is of type integer but expression is of type uuid`.
- **Fix**: reverted `DashboardShare.shared_with_role_id` to `Column(Integer, nullable=True)`
  in the model and to `Optional[int]` in both `DashboardShareCreate` and
  `DashboardShareResponse` in the schema.
- **Found by**: `TestSharing::test_create_share` — first run after DEF-019 fix.

### DEF-021 — `create_snapshot` raised `TypeError: Object of type UUID is not JSON serializable` → 500 — ✅ FIXED 2026-06-17
- **Severity**: High (`POST /dashboards/snapshots` always 500'd when the dashboard
  had any pages or widgets).
- **Root cause**: `DashboardService.create_snapshot` built the `snapshot_data` dict
  by directly including ORM attribute values (`dashboard.id`, `page.id`, `widget.id`),
  which are raw `uuid.UUID` objects. The dict is stored in a Postgres `JSON` column
  via SQLAlchemy's JSON type, which calls `json.dumps` without a custom `default`
  encoder → `TypeError` on any UUID field in the snapshot → 500. Same root cause
  as DEF-008 (audit layer UUID serialization), but in a different service method.
- **Fix**: wrapped every UUID value in the snapshot dict with `str()` in
  `app/services/dashboard_service.py`'s `create_snapshot` method.
- **Found by**: `TestSnapshots::test_create_snapshot` — first run after DEF-019/020 fixes.

### DEF-025 — `PUT /settings/tenant` 500'd for every tenant user — ✅ FIXED 2026-06-17
- **Severity**: High (`PUT /settings/tenant` was always broken for non-superusers — every attempt to update tenant branding/settings returned 500).
- **Root cause**: `update_tenant_settings` resolved `target_tenant = tenant_id or current_user.tenant_id`. When the `tenant_id` query param was absent, `target_tenant` became `current_user.tenant_id` — a `uuid.UUID` object. The subsequent SQLAlchemy filter `TenantSettings.tenant_id == target_tenant` compared against `Column(String(36))` (VARCHAR in the live DB), triggering Postgres "operator does not exist: character varying = uuid" → 500. Same root cause as DEF-022 (`BuilderPage.tenant_id` VARCHAR vs UUID).
- **Fix**: line 209 changed to `target_tenant = tenant_id or (str(current_user.tenant_id) if current_user.tenant_id else None)` in `routers/settings.py`. Always ensures `target_tenant` is a `str` before the DB filter.
- **Regression test**: `TestTenantSettings::test_update_primary_color`.

### DEF-026 — `PUT /settings/tenant?tenant_id=<own-tenant>` returned 403 instead of 200 — ✅ FIXED 2026-06-17
- **Severity**: Medium (any caller explicitly passing their own `tenant_id` was incorrectly blocked).
- **Root cause**: the ownership check on line 215 was `if tenant_id and tenant_id != current_user.tenant_id`. Here `tenant_id` is a `str` from the query param and `current_user.tenant_id` is a `uuid.UUID` object — in Python, `"37ba..." != UUID("37ba...")` is always `True` (different types), so the condition triggered a 403 even for the user's own tenant. The `GET /settings/tenant` handler on line 162 already used `str(tenant_id) != str(current_user.tenant_id)` correctly; the PUT handler was inconsistent.
- **Fix**: changed line 215 to `if tenant_id and str(tenant_id) != str(current_user.tenant_id) and not current_user.is_superuser:` — matching the GET handler's safe comparison. **Pattern**: whenever comparing a `str` query param to a `UUID` model attribute, always normalize both with `str()`.
- **Regression test**: `TestTenantSettings::test_update_with_explicit_own_tenant_id`.

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

Deep per-router coverage still pending for: metadata,
data, builder, templates, audit.
(auth, rbac, org, data-model, dynamic-data, workflows, automations,
admin/security, modules / module-registry / module-extensions, and reports
are now deep.) The smoke sweep already exercises all of them at the GET level.
See the coverage matrix in
[`test-plan-e2e-api.md`](../test-plans/test-plan-e2e-api.md).
