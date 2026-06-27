---
artifact_id: test-plan-23
type: test-plan
producer: D1 QA Engineer
consumers: [C1 Tech Lead, A3 Product Owner, E2 Technical Writer]
upstream: [epic-23-module-lifecycle-and-activation, tasks-23]
downstream: [test-report-23]
status: approved
created: 2026-06-26
updated: 2026-06-26
---

# Test Plan -- Epic 23: Module Lifecycle and Activation

> **Format**: structured test plan covering automated integration coverage already in place and manual runbook steps required on a live stack. Each scenario maps to a story AC from epic-23-module-lifecycle-and-activation.md. The companion test-report-23.md records execution results.

---

## 1. Scope

### In scope

| Story | Feature | Coverage type |
|-------|---------|---------------|
| 23.1.1 | API Contract -- enable/disable cycle, dep-unmet 409, system module 403 | Integration (automated) + manual |
| 23.2.1 | Manifest JSON schema validation -- per-field 422, semver rejection, dry-run /validate | Manual |
| 23.2.2 | manage.sh module pack -- determinism, SHA256SUMS, pre-pack validation | Manual (CLI) |
| 23.3.1 | manage.sh module install -- 8-step pipeline, idempotency, rollback on forced failure | Manual (CLI) |
| 23.3.2 | BaseModule.post_install / post_enable hook wiring | Integration (automated) |
| 23.4.1 | Modules page -- ModuleCard render, loading/empty/error states | Manual (browser) |
| 23.4.2 | ActivationModal -- preview fetch, deps-unmet disabled state, confirm flow | Manual (browser) |
| 23.4.3 | DeactivateModal -- data-safe warning, dependents blocking, confirm flow | Manual (browser) |
| 23.5.1 | Operator uninstall -- phase 1 deactivate-all, phase 2 DELETE, manage.sh module uninstall | Manual (CLI + API) |
| 23.5.2 | Audit trail -- all 5 lifecycle events written and queryable | E2E (automated, xfail) + manual |

### Out of scope

- Company-level activation UI (Persona C, deferred to v2)
- module_tenant_whitelist + visibility=whitelist UI (column in schema; whitelist table deferred)
- Module version upgrade / semver-bump migration fan-out (future epic)
- Performance / load testing of enable/disable hot paths
- D3 Security Engineer sec-review-23 (commissioned separately after sprint)
- E2 Technical Writer release-notes-epic-23 (commissioned after D3 sign-off)
- Regression of Epic 21 scenarios (RBAC, dynamic CRUD, notifications) -- covered separately in test-plan-21

---

## 2. Test Environments

| Environment | Purpose | Notes |
|-------------|---------|-------|
| SQLite in-memory (pytest conftest db_session) | Integration tests -- fast, isolated, no Docker required | Used by test_module_lifecycle.py and test_module_hook.py; ModuleRegistryService not available; auth stubbed via dependency_overrides |
| Dev stack (Docker Compose) | Manual browser + CLI smoke tests | docker compose up from repo root; app_buildify_backend + app_buildify_frontend + app_buildify_db; Postgres; manage.sh runs inside or alongside container |
| E2E stack | test_audit_logs_module.py -- black-box HTTP against live backend | Requires running dev stack; su/user/anon client fixtures from e2e conftest; structural tests run unconditionally; event-presence tests are xfail(strict=False) pending DEF-032 |

---

## 3. Test Scenarios

### S1 -- API Contract (Story 23.1.1)

#### TC-23-001 Enable/Disable cycle (Integration)

- AC ref: epic-23 S23.1.1 backend -- canonical paths
- Task: T-23.005
- Type: Integration (SQLite)
- File: backend/tests/integration/test_module_lifecycle.py TestEnableDisableCycle

Setup: Seed a Module row with install_status=ready, visibility=all_tenants, is_installed=True.

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST /api/v1/modules/{id}/enable with tenant-admin auth | 200 {"status": "active"} |
| 2 | GET /api/v1/modules | activation_status=active for the module |
| 3 | POST /api/v1/modules/{id}/disable | 200 {"status": "inactive"} |
| 4 | GET /api/v1/modules | activation_status=inactive for the module |
| 5 | POST /api/v1/modules/{id}/enable again | 200 {"status": "active"} (re-enable succeeds) |

#### TC-23-002 Dependency-unmet 409 (Integration)

- AC ref: epic-23 S23.1.1 backend -- dep-unmet 409
- Task: T-23.005
- Type: Integration (SQLite)
- File: backend/tests/integration/test_module_lifecycle.py TestDepUnmet409

Setup: Seed provider module (inactive) and consumer module whose manifest declares provider as dependency.

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST /api/v1/modules/{consumer_id}/enable (provider inactive) | 409 {"detail": {"code": "dependencies_unmet", "missing": [...]}} |
| 2 | POST /api/v1/modules/{provider_id}/enable | 200 active |
| 3 | POST /api/v1/modules/{consumer_id}/enable | 200 active |

Note: if the manifest-dep check path is not yet wired in T-23.020, step 1 may return 200 -- test carries xfail(strict=False) guard until confirmed.

#### TC-23-003 System module 403 on delete (Integration)

- AC ref: epic-23 S23.1.1 backend -- system module 403
- Task: T-23.005
- Type: Integration (SQLite)
- File: backend/tests/integration/test_module_lifecycle.py TestSystemModuleProtected

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST /api/v1/module-registry/uninstall as tenant-admin | 401 or 403 (require_superuser guard) |
| 2 | Same call as superuser with is_core=True module | Non-200 (400/403/404/503); xfail if 200 returned (T-23.025 is_core guard not yet in new admin endpoint) |

#### TC-23-004 Structured error bodies (Manual)

- AC ref: epic-23 S23.1.1 backend -- structured errors
- Task: T-23.003
- Type: Manual (dev stack)

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST /api/v1/modules/{id}/enable with unmet deps | 409 body with keys code, message, detail.missing |
| 2 | Force a validation error on any module endpoint | Response body has code, message, detail -- no bare 422 string |

#### TC-23-005 activation-preview endpoint (Manual)

- AC ref: epic-23 S23.1.1 backend -- activation-preview
- Task: T-23.002
- Type: Manual (dev stack)

| Step | Action | Expected |
|------|--------|----------|
| 1 | GET /api/v1/modules/{id}/activation-preview | 200 {"permissions": [...], "menu_items": [...], "dependencies": [...]} |
| 2 | Preview for module with inactive dependency | dependencies[n].status is inactive; response still 200 (preview is read-only) |

---

### S2 -- Packaging Pipeline (Stories 23.2.1 and 23.2.2)

#### TC-23-006 Manifest schema validation -- 422 on violation (Manual)

- AC ref: epic-23 S23.2.1 backend -- schema file
- Task: T-23.006, T-23.007
- Type: Manual (dev stack)

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST /api/v1/modules/register with missing required name field | 422 {"errors": [{"field": "name", "message": "..."}]} |
| 2 | POST /api/v1/modules/register with "version": "not-semver" | 422 with field version in errors |
| 3 | POST /api/v1/modules/register with valid manifest | 200 or 201 -- no errors |

#### TC-23-007 Dry-run validate endpoint (Manual)

- AC ref: epic-23 S23.2.1 backend -- validate endpoint
- Task: T-23.007
- Type: Manual (dev stack)

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST /api/v1/modules/validate with invalid manifest | Same 422 structure as /register; no DB row created |
| 2 | POST /api/v1/modules/validate with valid manifest | 200; SELECT COUNT(*) FROM modules unchanged |

#### TC-23-008 manage.sh module pack determinism (Manual)

- AC ref: epic-23 S23.2.2 backend -- pack command
- Task: T-23.008, T-23.009
- Type: Manual (CLI)

Prerequisites: module directory with valid manifest.json, backend/ subdir, optionally frontend/, migrations/, install.sh.

| Step | Action | Expected |
|------|--------|----------|
| 1 | manage.sh module pack <module_dir> | Produces <name>_<version>.tar.gz in current dir or --out dir |
| 2 | tar -tzf <tarball> | Contains manifest.json, SHA256SUMS, backend/, install.sh |
| 3 | Run pack twice on same dir | Both tarballs have identical SHA256SUMS (normalised timestamps) |
| 4 | manage.sh module pack <dir_with_bad_manifest> | Exits non-zero; error output mentions validation failure |

---

### S3 -- Install Pipeline (Stories 23.3.1 and 23.3.2)

#### TC-23-009 Install pipeline -- happy path steps 1-8 (Manual)

- AC ref: epic-23 S23.3.1 backend -- install steps 1-8
- Task: T-23.010, T-23.011
- Type: Manual (CLI against dev stack)

| Step | Action | Expected |
|------|--------|----------|
| 1 | manage.sh module install <tarball> | Per-step structured log: SHA256 verify pass, validate pass, install_status=in_progress, migrations pass, service copy pass, assets copy pass, register pass, install_status=ready |
| 2 | GET /api/v1/modules | Newly installed module present with activation_status=inactive |
| 3 | POST /api/v1/modules/{id}/enable | 200 active |

#### TC-23-010 Install idempotency (Manual)

- AC ref: epic-23 S23.3.1 backend -- idempotency
- Task: T-23.012
- Type: Manual (CLI)

| Step | Action | Expected |
|------|--------|----------|
| 1 | manage.sh module install <tarball> (already installed) | Exit 0; output contains "already installed" |
| 2 | Module state in DB | Unchanged -- no duplicate rows |

#### TC-23-011 Install rollback on failure (Manual)

- AC ref: epic-23 S23.3.1 backend -- rollback on failure
- Task: T-23.011
- Type: Manual (CLI -- forced failure injection)

Method: corrupt the tarball after checksum step, or block /register endpoint to force a step-7 failure.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Trigger install; inject failure at step 5 (service copy) | Completed steps reversed; install_status=failed; error_message populated |
| 2 | Module state in DB | No row with install_status=ready; no orphaned migration |
| 3 | Platform state | Previously working modules unaffected |

#### TC-23-012 post_install hook sentinel (Integration)

- AC ref: epic-23 S23.3.2 backend -- hook wiring
- Task: T-23.015
- Type: Integration (SQLite)
- File: backend/tests/integration/modules_lifecycle/test_module_hook.py TestPostInstallHookSentinel

| Step | Action | Expected |
|------|--------|----------|
| 1 | Register stub module whose post_install writes AuditLog(action="test_sentinel_post_install") | 200; success=True |
| 2 | Query audit_logs for action="test_sentinel_post_install" | Row exists; entity_type=module, status=success |

#### TC-23-013 module.installed baseline audit from /register (Integration)

- AC ref: epic-23 S23.5.2 -- consolidation (T-23.027)
- Task: T-23.027
- Type: Integration (SQLite)
- File: backend/tests/integration/modules_lifecycle/test_module_hook.py test_register_endpoint_writes_module_installed_audit

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST /api/v1/module-registry/register with valid manifest | 200; AuditLog(action="module.installed", entity_type="module") row present in DB |

---

### S4 -- Tenant Activation UI (Stories 23.4.1, 23.4.2, 23.4.3)

#### TC-23-014 ModuleCard render -- all states (Manual browser)

- AC ref: epic-23 S23.4.1 frontend
- Task: T-23.019
- Type: Manual (dev stack browser)

Prerequisites: dev stack running; at least one module with install_status=ready; navigate to #/settings/modules.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Load page with no installed modules | Empty state: package icon + "No modules are installed on this platform yet." |
| 2 | Load page with 1+ installed modules | FlexGrid of ModuleCards; each card shows icon, name, version badge, category badge, description (2-line clamp) |
| 3 | Active module card | status-badge = green "Active"; action-button = ghost danger "Deactivate" |
| 4 | Inactive module card | status-badge = neutral "Available"; action-button = primary "Activate" |
| 5 | Throttle network to simulate loading | 6 skeleton FlexCard placeholders with animate-pulse |
| 6 | Block GET /api/v1/modules to simulate error | FlexAlert error + "Retry?" link; clicking Retry re-calls GET /modules |

#### TC-23-015 ActivationModal -- preview and confirm flow (Manual browser)

- AC ref: epic-23 S23.4.2 frontend
- Task: T-23.021
- Type: Manual (dev stack browser)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Activate" on an Available card | Modal opens; skeleton rows shown while preview fetches |
| 2 | Preview loaded (deps met) | Permissions section and menu-items section populated; Confirm button enabled |
| 3 | Preview loaded (dep inactive) | Dependencies section shows inactive dep in red; warning FlexAlert visible; Confirm button disabled |
| 4 | Click "Confirm Activation" | Buttons disabled; spinner + "Activating..." on Confirm |
| 5 | Activation success | Modal closes; card patches to Active state without full page reload |
| 6 | Activation API error | FlexAlert error above footer with message; buttons re-enabled |
| 7 | Click "Cancel" | Modal closes; card state unchanged |

#### TC-23-016 DeactivateModal -- safety message and blocking (Manual browser)

- AC ref: epic-23 S23.4.3 frontend
- Task: T-23.023
- Type: Manual (dev stack browser)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Deactivate" on Active card (no dependents) | Modal opens; safety FlexAlert (warning) visible; Deactivate button enabled |
| 2 | Click "Deactivate" to confirm | Spinner + "Deactivating..."; on success: modal closes; card patches to Available state |
| 3 | Click "Deactivate" on module with active dependents | Modal opens; error FlexAlert lists blocking module names; Deactivate button disabled |
| 4 | Click "Cancel" | Modal closes; no state change |
| 5 | Deactivation API error | FlexAlert error above footer; buttons re-enabled |

#### TC-23-017 Card in-place patch on activation events (Manual browser)

- AC ref: epic-23 S23.4.1 frontend -- on activation/deactivation success event
- Task: T-23.019
- Type: Manual (dev stack browser)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Activate a module via ActivationModal | Card status-badge changes to "Active"; button changes to "Deactivate" -- no page reload |
| 2 | Deactivate via DeactivateModal | Card status-badge changes to "Available"; button changes to "Activate" -- no page reload |

---

### S5 -- Operator Uninstall (Story 23.5.1)

#### TC-23-018 Phase 1 -- deactivate-all (Manual)

- AC ref: epic-23 S23.5.1 backend -- phase 1
- Task: T-23.024
- Type: Manual (dev stack API)

Prerequisites: module activated for 2+ tenants; superadmin credentials.

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST /api/v1/admin/modules/{id}/deactivate-all as superadmin | 200 {"tenants_deactivated": N}; module install_status=deactivation_pending |
| 2 | POST /api/v1/audit/list (entity_type=module, action=module.disabled) | One row per deactivated tenant |
| 3 | POST /api/v1/audit/list (action=module.deactivate_all) | Summary row present |
| 4 | Same call as non-superuser | 403 |

#### TC-23-019 Phase 2 -- hard DELETE (Manual)

- AC ref: epic-23 S23.5.1 backend -- phase 2
- Task: T-23.025
- Type: Manual (dev stack API)

| Step | Action | Expected |
|------|--------|----------|
| 1 | DELETE /api/v1/admin/modules/{id} without X-Confirm-Uninstall: true header | 400 or 422 (header required) |
| 2 | DELETE with confirm header when install_status != deactivation_pending | 409 or 400 (phase 1 not complete) |
| 3 | After phase 1: DELETE with confirm header | 200; module files removed; module_activations rows deleted; RBAC seeds removed; modules row deleted |
| 4 | GET /api/v1/modules | Module no longer in list |
| 5 | POST /api/v1/audit/list (action=module.uninstalled) | Row present |

#### TC-23-020 manage.sh module uninstall CLI flow (Manual)

- AC ref: epic-23 S23.5.1 backend -- CLI
- Task: T-23.026
- Type: Manual (CLI)

| Step | Action | Expected |
|------|--------|----------|
| 1 | manage.sh module uninstall <name> | Phase 1 runs; summary printed (N tenants deactivated); confirmation prompt displayed |
| 2 | Enter y at prompt | Phase 2 runs; module removed; exit 0 |
| 3 | Enter n at prompt | Abort; module remains in deactivation_pending; exit 0 with message |

---

### S6 -- Audit Events (Story 23.5.2)

#### TC-23-021 All 5 lifecycle events queryable (Manual -- post DEF-032 resolution)

- AC ref: epic-23 S23.5.2 backend
- Task: T-23.027, T-23.028
- Type: Manual (dev stack)

Run a full lifecycle sequence on a test module:

| Step | Trigger | Expected audit event |
|------|---------|---------------------|
| 1 | manage.sh module install <tarball> | module.installed |
| 2 | POST /api/v1/modules/{id}/enable | module.enabled |
| 3 | POST /api/v1/modules/{id}/disable | module.disabled |
| 4 | POST /api/v1/admin/modules/{id}/deactivate-all | module.deactivate_all |
| 5 | DELETE /api/v1/admin/modules/{id} with confirm header | module.uninstalled |

For each action, verify via POST /api/v1/audit/list:
- entity_type = module
- entity_id = <module_id>
- performed_by populated
- metadata contains version and (where relevant) affected_tenant_count
- Platform-level events (module.installed, module.uninstalled): tenant_id = null
- Tenant-level events (module.enabled, module.disabled): tenant_id populated

#### TC-23-022 Audit endpoint structural contract (E2E automated)

- AC ref: epic-23 S23.5.2 backend
- Task: T-23.028
- Type: E2E (automated -- runs unconditionally)
- File: backend/tests/e2e/test_audit_logs_module.py TestAuditModuleStructural

| Test | Assertion |
|------|-----------|
| test_audit_list_requires_auth | Anon request returns 401 or 403 |
| test_audit_list_module_filter_returns_200 | Superuser request returns 200 |
| test_audit_list_module_response_shape | Response has logs (list) and total (int) keys |
| test_audit_list_all_entries_have_correct_entity_type | Every returned entry has entity_type=module |
| test_audit_list_action_filter_scopes_results | action=module.installed filter returns only that action |
| test_audit_list_entries_have_required_fields | Every entry has id, action, entity_type, created_at |
| test_audit_list_low_privilege_user_result | Tenant user gets 200 or 403 (not 500) |

---

## 4. Existing Automated Coverage

### File 1 -- backend/tests/integration/test_module_lifecycle.py

10 tests across 3 classes. Uses SQLite in-memory DB; auth stubbed via dependency_overrides.

| Class | Tests | Coverage |
|-------|-------|---------|
| TestEnableDisableCycle | 5 | TC-23-001: enable, GET activation_status=active, disable, GET activation_status=inactive, re-enable |
| TestDepUnmet409 | 2 | TC-23-002: 409 on unmet dep; 200 when dep is active; xfail guard for manifest-dep path |
| TestSystemModuleProtected | 3 | TC-23-003: 403 for tenant-admin uninstall; non-200 for superuser on core module (xfail); 404 guard on core module lookup |

Coverage gaps: structured error body shape (TC-23-004) is manual only; activation-preview endpoint (TC-23-005) not exercised in SQLite; post_enable hook sentinel not implemented.

### File 2 -- backend/tests/integration/modules_lifecycle/test_module_hook.py

2 tests. Uses SQLite in-memory DB with real ModuleLoader pointed at a temp stub directory.

| Test | Coverage |
|------|---------|
| test_post_install_writes_sentinel_to_audit_log | TC-23-012: confirms post_install() called by /register handler; sentinel AuditLog row exists after call |
| test_register_endpoint_writes_module_installed_audit | TC-23-013: confirms module.installed audit row written on every /register call regardless of hook presence |

Coverage gaps: post_enable() hook sentinel not implemented; confirmed indirectly via TC-23-001 enable flow only.

### File 3 -- backend/tests/e2e/test_audit_logs_module.py

13 tests total. Requires live dev stack; uses black-box HTTP clients (su, user, anon fixtures).

| Tests | Type | Status |
|-------|------|--------|
| 7 in TestAuditModuleStructural | E2E structural | Run unconditionally; must all pass (TC-23-022) |
| 6 event-presence tests | E2E functional | xfail(strict=False) pending DEF-032; auto-promote to PASS once a loadable module is wired up |

---

## 5. Manual Test Steps (Live Stack Required)

These scenarios cannot be executed in the SQLite integration environment and require the dev Docker Compose stack.

### Prerequisites

- docker compose up -d from the repo root
- curl -s http://localhost:8000/health confirms backend healthy
- Obtain superadmin token via POST /auth/login; store as TOKEN environment variable
- bash manage.sh --help confirms manage.sh is executable

### M-01 Pack a test module

Create /tmp/test_mod/ with:
- manifest.json: {"name": "test-smoke-module", "display_name": "Smoke Test Module", "version": "1.0.0", "module_type": "code", "category": "test", "api_prefix": "/api/v1/smoke", "permissions": [{"code": "smoke:read", "name": "Smoke Read", "description": "Read smoke"}], "menu_items": [{"label": "Smoke", "route": "#/smoke", "icon": "ph-flask"}], "dependencies": []}
- Empty backend/ subdirectory
- Empty migrations/ subdirectory

Run: bash manage.sh module pack /tmp/test_mod --out /tmp

Expected: /tmp/test-smoke-module_1.0.0.tar.gz created; exit 0.
Verify: tar -tzf /tmp/test-smoke-module_1.0.0.tar.gz lists SHA256SUMS and manifest.json.

### M-02 Install the test module

Run: bash manage.sh module install /tmp/test-smoke-module_1.0.0.tar.gz

Expected: 8-step structured log each showing pass; final output indicates install_status=ready; exit 0.

Verify via API: GET /api/v1/modules with bearer token; find test-smoke-module entry with activation_status=inactive. Store the id as MODULE_ID.

### M-03 Activate and deactivate via API

Enable: POST /api/v1/modules/$MODULE_ID/enable with bearer token.
Expected: 200 {"status": "active", "permissions_added": [...], "menu_items_added": [...]}.

Disable: POST /api/v1/modules/$MODULE_ID/disable with bearer token.
Expected: 200 {"status": "inactive"}.

### M-04 Browser smoke test (activation UI)

1. Navigate to http://localhost:8080/#/settings/modules
2. Verify test-smoke-module card shows neutral "Available" badge and primary "Activate" button
3. Click "Activate" -- verify ActivationModal opens; permissions and menu item listed; skeleton loading state first
4. Click "Confirm Activation" -- verify card patches to green "Active" badge + "Deactivate" button; no page reload
5. Click "Deactivate" -- verify DeactivateModal opens with warning FlexAlert about data preservation
6. Click "Deactivate" to confirm -- verify card patches back to neutral "Available" badge + "Activate" button

### M-05 Operator uninstall (CLI)

Run: bash manage.sh module uninstall test-smoke-module

Expected: phase 1 output (N tenants deactivated); confirmation prompt appears.
Enter y: phase 2 runs; module removed; exit 0.

Verify removed: GET /api/v1/modules should not include test-smoke-module.

### M-06 Audit log verification (post DEF-032 resolution)

After completing M-02 through M-05, verify all 5 event types via POST /api/v1/audit/list.

For each action in [module.installed, module.enabled, module.disabled, module.deactivate_all, module.uninstalled]:
- POST /api/v1/audit/list with body {"entity_type": "module", "action": "<action>", "page": 1, "page_size": 10}
- Expected: total >= 1

Note: the audit endpoint is POST /api/v1/audit/list with filter in the request body. The spec references GET /api/v1/audit-logs?entity_type=module but the actual implementation in backend/app/routers/audit.py uses the POST form (confirmed in tests/smoke_checklist.md).

---

## 6. Known Defects

### DEF-032 -- Module class unloadable; lifecycle HTTP API returns 400

Scope: backend/tests/e2e/test_audit_logs_module.py -- 6 event-presence tests marked xfail(strict=False).

Root cause: Seed modules exist in the modules DB table but have no corresponding backend/modules/<name>/module.py + permissions.py on disk. Every call to /module-registry/enable, /disable, /uninstall, /deactivate-all that requires loading the module class returns HTTP 400. None of the 5 lifecycle audit events (module.enabled, module.disabled, module.deactivate_all, module.uninstalled, module.installed from enable path) can be generated via the HTTP API against seed modules.

Impact: Manual steps M-03 through M-06 are blocked against seed modules. The workaround is to use the test-smoke-module stub built in M-01/M-02, which bypasses the seed-module class problem. The 6 xfail E2E tests auto-promote to PASSED once any loadable module is present in the dev stack.

Status: open; no fix assigned as of 2026-06-26.

Blocks: TC-23-021 (live audit event verification against seed data) and M-06 against seed modules.

---

## 7. DoD Checklist

Gates that must all be PASS (or formally DEFERRED with written note accepted by A3) before Epic 23 is CLOSED:

- [ ] TC-23-001 -- all 5 TestEnableDisableCycle subtests pass in test_module_lifecycle.py
- [ ] TC-23-002 -- xfail guard on manifest-dep path resolved; test passes without xfail bypass, OR T-23.020 manifest-dep check confirmed working and guard removed
- [ ] TC-23-003 -- non-200 responses confirmed for system-module uninstall; xfail guard on T-23.025 is_core path resolved once admin endpoint ships
- [ ] TC-23-012 -- post_install sentinel test passes in test_module_hook.py
- [ ] TC-23-013 -- module.installed baseline audit test passes in test_module_hook.py
- [ ] TC-23-022 -- all 7 tests in TestAuditModuleStructural pass unconditionally on dev stack
- [ ] M-01 + M-02 -- manage.sh module pack produces valid deterministic tarball; manage.sh module install completes all 8 steps with structured per-step log on dev stack
- [ ] M-03 -- enable/disable cycle via API succeeds on dev stack; response bodies match structured error spec
- [ ] M-04 -- browser smoke: ModuleCard renders in all states; ActivationModal and DeactivateModal function correctly; cards patch in-place on success events without page reload
- [ ] M-05 -- manage.sh module uninstall completes both phases with confirmation prompt; module absent from GET /api/v1/modules after completion
- [ ] M-06 -- all 5 audit event types (module.installed, module.enabled, module.disabled, module.deactivate_all, module.uninstalled) present in POST /api/v1/audit/list after full lifecycle sequence, OR DEF-032 documented as accepted blocker with resolution timeline
- [ ] Story 23.1.1 gate -- API contract documented in docs/backend/MODULE_API.md (T-23.001); all gate tasks T-23.001 through T-23.005 confirmed DONE before any other item was started
- [ ] Story 23.3.2 -- either post_install and post_enable hooks confirmed working in integration test, OR story formally marked [DEFERRED] per its own AC with written note
- [ ] No regressions -- test-plan-21 scenarios (RBAC, dynamic CRUD, password-reset notifications) pass against dev stack
- [ ] D3 Security Engineer -- sec-review-23.md published with verdict CLEAR TO SHIP (priority: T-23.020 permission seeding and T-23.022 permission revocation)
- [ ] E2 Technical Writer -- release-notes-epic-23.md published after D3 sign-off

---

## 8. How to Run

### Automated integration tests (no Docker required)

```
docker exec app_buildify_backend python -m pytest \
  backend/tests/integration/test_module_lifecycle.py \
  backend/tests/integration/modules_lifecycle/test_module_hook.py \
  -v --tb=short
```

### E2E structural tests (dev stack required)

```
docker exec app_buildify_backend python -m pytest \
  backend/tests/e2e/test_audit_logs_module.py \
  --confcutdir=backend/tests/e2e -v --tb=short
```

Structural tests (TestAuditModuleStructural) must all pass.
xfail tests show x (expected DEF-032 failure) or X (unexpected pass meaning DEF-032 is resolved).

### Manual steps

Follow section 5 (M-01 through M-06) in order on a running dev stack. Record each outcome in tests/test-reports/test-report-23.md. Every failed step must produce a clear error with actionable detail -- silent failures are not acceptable.
