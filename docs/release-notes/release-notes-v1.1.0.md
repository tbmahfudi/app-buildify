---
artifact_id: release-notes-v1.1.0
type: release-notes
producer: E2 Technical Writer
consumers: [stakeholders, tenant administrators, operators, developers]
upstream: [release-notes-epic-21, epic-22-tenant-isolation-hardening, epic-23-module-lifecycle-and-activation, epic-24-frontend-capability-surfacing]
downstream: []
status: approved
created: 2026-06-20
updated: 2026-06-20
version: 1.1.0
---

# Release Notes — v1.1.0

> **Release date**: 2026-06-20
>
> **TL;DR**: v1.1.0 completes four consecutive sprints (Epics 21–24), retiring all five platform risks, delivering production-grade tenant isolation with per-tenant module databases, wiring the full module lifecycle pipeline, and surfacing 14 previously hidden backend capabilities in the UI. Two new SMTP env vars are required. One endpoint path changed (`/activate` → `/enable`, `/deactivate` → `/disable`).

---

## What's New

### Epic 21 — Risk Retirement

All five risks from the original platform vision are now retired end-to-end.

**Self-service custom roles** — Tenant administrators can create, edit, and delete custom roles from the Access Control page. System roles remain immutable. Deleting a role that still has assigned users or groups returns a dependency count.

**Wildcard permissions work** — Granting `*:*:platform` or any segment-level wildcard (`users:*:tenant`) now correctly matches all in-scope permissions. The check path runs in ~6 µs, well under the 5 ms requirement.

**Per-entity permission control** — Each NoCode entity now has an Access Control section. Toggle "Inherit from global RBAC" off and assign role × action matrices (create/read/update/delete) per entity.

**Password-reset emails deliver** — The notification queue worker is live. Password-reset emails deliver via SMTP using either per-tenant credentials (`notification_config`) or system env vars. Failures retry with exponential backoff, dead-letter after max attempts, and appear in the audit log.

**Flex layout library complete** — All nine layout primitives ship: `flex-stack`, `flex-grid`, `flex-sidebar`, `flex-split-pane`, `flex-container`, `flex-section`, `flex-cluster`, `flex-toolbar`, `flex-masonry`.

New permission codes: `roles:create:tenant`, `roles:update:tenant`, `roles:delete:tenant`. Tenants with `*:*:tenant` get these automatically.

---

### Epic 22 — Tenant Isolation Hardening

Two-layer logical isolation for the shared core database plus a physical database-per-tenant for module data. All 14 stories implemented.

**Centralized scope helper** (`backend/app/core/scope.py`) — `apply_tenant_scope(query, model, user)` and `tenant_scope_dependency` replace all ad-hoc `Model.tenant_id == user.tenant_id` literals. A `manage.sh check-tenant-scope` script enforces the convention as a pre-merge gate.

**Named cross-tenant API** — `with_admin_cross_tenant_scope()` context manager makes every legitimate cross-tenant read intentional, code-reviewable, and audit-logged (`tenant.cross_scope.enter` / `.exit`). Misuse without superuser privileges raises `PermissionError`.

**SQLAlchemy session-event listener** — A `before_compile` listener auto-injects `WHERE tenant_id = <scope>` on every tenant-scoped query. A forgotten filter becomes a loud `TenantScopeMissingError` (HTTP 500 + audit log entry `tenant.scope_missing`) instead of a silent cross-tenant data leak.

**Per-request scope binding** — `tenant_scoped_session(user, db)` FastAPI dependency binds the tenant scope to the SQLAlchemy session for the lifetime of every authenticated request. Public routes opt out explicitly.

**Database-per-tenant for module data** — New `DATABASE_STRATEGY=per_tenant` extends ADR-001. A `tenant_module_databases` registry table maps `(tenant_id, module_id)` to connection URLs. `ModuleScopeMiddleware` routes each request to the correct per-tenant module database automatically.

**Provisioning workflow** — Module-enable for a new (tenant, module) pair auto-provisions a fresh database (60-second gate passed). Failures are recorded with status `failed` and surfaced as a retry badge in the Modules UI.

**Alembic fan-out** — `scripts/migrate-module.py <module_id>` runs Alembic upgrade across all tenant-deployed instances of a module in parallel (bounded concurrency = 4). Partial failures are logged; the script exits non-zero with a summary.

**Tenant offboarding** — `manage.sh tenant deactivate <id>` calls `cleanup_tenant_module_dbs()`, archiving or dropping per-tenant module databases per `TENANT_DELETION_POLICY=drop|archive` (default `archive`).

**Financial module migrated** — New tenants enabling the financial module get a per-tenant database. Existing tenants stay on shared until `manage.sh module migrate-tenant <tenant_id> financial` is run (dry-run mode available).

**SDK update** — `BaseModule` gains `tenant_scoped: bool = True` and `get_tenant_scoped_tables() -> List[str]`. Existing modules default to `tenant_scoped=true` with no change required.

**Documentation** — `docs/platform/TENANT_ISOLATION.md` is the single canonical reference for how tenant isolation is enforced, including a "how to add a new tenant-scoped table" runbook.

---

### Epic 23 — Module Lifecycle and Activation

End-to-end module delivery pipeline: developer packages a module, platform installs it, tenant administrators self-service activate or deactivate it.

**API contract alignment** — All module endpoints use the canonical state machine (`registered → installed → active → inactive → uninstalled`) with paths `POST /api/v1/modules/{id}/install`, `/enable`, `/disable`, `DELETE /api/v1/modules/{id}`. `module-manager.js` updated to match.

**Manifest validation** — `POST /api/v1/modules/validate` (dry-run) and validation on `POST /api/v1/modules/register` enforce a JSON schema covering all manifest fields including semver `version`. Per-field errors returned on 422.

**`manage.sh module pack`** — Produces a sealed, content-addressable tarball (`<name>_<version>.tar.gz` + `SHA256SUMS`) from a module directory. Validates the manifest before producing the artifact.

**`manage.sh module install`** — Atomically installs a module in eight steps (checksum verify, manifest validate, migration, backend copy, frontend copy, register). Rolls back completed steps in reverse order on any failure. Idempotent on re-run.

**BaseModule hooks** — `post_install()` and `post_enable()` fire via the in-process event bus on `module.installed` and `module.enabled` events.

**Modules list page** (`#/settings/modules`) — Tenant administrators see all installed modules with activation status. Each module card shows version, category, description, a status badge (Active / Available), and an Activate or Deactivate button.

**Activation flow** — Clicking Activate opens a pre-activation summary modal showing exactly which permissions and menu items the module will add, plus dependency status. Confirm is blocked until all dependencies are active.

**Deactivation flow** — Clicking Deactivate opens a confirmation modal explicitly stating that data will not be deleted. The button is blocked if other active modules depend on this one.

**Operator uninstall** — Two-phase: `POST /api/v1/admin/modules/{id}/deactivate-all` then `DELETE /api/v1/admin/modules/{id}` (requires `X-Confirm-Uninstall: true` header). `manage.sh module uninstall <name>` runs both phases with a confirmation prompt.

**Full audit trail** — Every module lifecycle state change (`module.installed`, `module.enabled`, `module.disabled`, `module.deactivate_all`, `module.uninstalled`) writes an `audit_logs` row. Filterable via `GET /api/v1/audit-logs?entity_type=module`.

---

### Epic 24 — Frontend Capability Surfacing

14 stories wiring existing backend endpoints to previously missing or broken UI surfaces.

**Forgot-password flow** — `#reset-password` and `#reset-password-confirm` routes are live on the login page, including email input, success state ("Check your inbox"), and token-missing/expired error states.

**Notification honesty banner** — The Notifications settings tab shows a persistent warning that email delivery is not yet active until SMTP is configured. In-app notifications remain active.

**Duplicate route cleanup** — `#reports-designer` and `#reports/designer` redirect to the canonical `#report-designer`. The redundant template file has been removed.

**Live password-strength feedback** — A strength meter appears below all password fields. It calls `GET /api/v1/auth/password-policy` once on load and evaluates rules client-side as you type.

**Publish button with migration diff preview** — The data-model entity editor shows a diff of pending field changes before publishing. The Publish button is disabled until the diff is reviewed.

**Automation rule test panel** — A "Test rule" panel lets you fire a mock event against an automation rule and see the action trace without creating real records.

**Automation execution history** — The Automation Rules page surfaces the last 50 execution log entries per rule, with status, timestamp, and error detail.

**Job execution log viewer** — The Scheduler page shows a collapsible log panel for each scheduled job run.

**Page version history sidebar** — The NoCode page builder shows a sidebar listing the last 20 saved versions with diff and restore controls.

**Dev-tool screens removed from production nav** — Debug and test-harness routes no longer appear in the main navigation.

**Workflow simulator panel** — A thin MVP simulator panel in the Workflow designer fires the state machine through manual transitions without creating a live execution.

**Permission matrix table** — The Access Control page renders the full role × permission matrix as an editable table.

**Dashboard share and snapshot buttons** — Dashboard share (copy link) and snapshot (save current filter state as a named view) buttons are wired to existing endpoints.

**User effective permissions panel** — The user detail page shows the computed effective permission set, accounting for role assignments, group memberships, and wildcard expansion.

---

## Breaking Changes

### Module endpoint path change

The activation and deactivation paths changed in Epic 23 to align with the canonical API contract:

| Before (incorrect path) | After (canonical) |
|---|---|
| `POST /api/v1/module-registry/enable` | `POST /api/v1/modules/{id}/enable` |
| `POST /api/v1/module-registry/disable` | `POST /api/v1/modules/{id}/disable` |
| `POST /api/v1/modules/{id}/activate` | `POST /api/v1/modules/{id}/enable` |
| `POST /api/v1/modules/{id}/deactivate` | `POST /api/v1/modules/{id}/disable` |

The frontend `module-manager.js` has been updated. Custom integrations calling the old paths must update.

### `DATABASE_STRATEGY=separate` deprecated

`separate` is deprecated in favour of `per_tenant`. It continues to work in this release but will be removed in a future release.

---

## Bug Fixes

- **Modules migration CHECK constraint** — Fixed invalid quoting in the `module_registry` Alembic migration that caused a `ProgrammingError` on fresh database initialization.
- **`manage.sh` health URL** — Fixed the healthcheck URL in the dev management script, which was pointing to a removed endpoint and causing false "unhealthy" reports on `manage.sh status`.
- **E2E auth helper** — Fixed an authentication race condition in the Playwright E2E test helper that caused intermittent 401 failures on the first test in a suite.
- **`vitest` excluding E2E specs** — Fixed `vitest.config.js` to exclude `tests/e2e/**` so unit-test runs no longer attempt to execute Playwright specs.
- **DEF-027–031** — Five defects found and fixed during the Epic 24 E2E data-router deep-coverage run: relationship traversal null-pointer, aggregation hint cache invalidation, bulk-delete partial-failure rollback, entity-version diff rendering, and dynamic-filter URL serialization.

---

## Infrastructure

**Production Docker Compose** (`infra/docker-compose.prod.yml`) — Updated with tagged image references, named volumes, health-check dependencies (backend waits for postgres and redis), and `notification-worker` service.

**`notification-worker` service** — Defined in both dev and prod compose files. Runs as a separate container by default (`NOTIFICATION_WORKER_INPROCESS=false`).

**Per-tenant module database foundation** — `tenant_module_databases` registry, `ModuleScopeMiddleware`, connection-pool management (bounded 50 active pools, LRU eviction), and Alembic fan-out tooling are all production-ready.

---

## Security

Epic 22 closes the highest residual platform risk from the post-Epic-21 security review:

- Centralized `scope.py` helper eliminates ad-hoc `tenant_id` filter literals.
- SQLAlchemy listener turns a forgotten filter from a silent cross-tenant data leak into a loud error.
- `with_admin_cross_tenant_scope()` makes every legitimate cross-tenant read auditable and intentional.
- Physical database separation for module data means a bug in one tenant's module cannot expose another tenant's module data.
- 40-scenario adversarial test plan (`tests/test-plans/test-plan-22.md`) — all scenarios pass.

---

## Developer Experience

**`manage.sh` improvements**:
- `manage.sh check-tenant-scope` — greps for ad-hoc `tenant_id ==` literal patterns; exits non-zero if any remain.
- `manage.sh module pack <dir>` — produces a sealed module tarball with checksum file.
- `manage.sh module install <tarball>` — atomic install with rollback.
- `manage.sh module uninstall <name>` — two-phase uninstall with confirmation prompt.
- `manage.sh tenant deactivate <id>` — offboards a tenant including per-tenant module database cleanup.
- `manage.sh module migrate-tenant <tenant_id> <module_id>` — migrates a tenant's module from shared to per-tenant storage (dry-run available).

**Playwright E2E suite** — 47 tests covering authentication, data-router deep paths, relationship traversal, aggregation, bulk operations, and entity versioning. DEF-027–031 resolved.

**`docs/platform/TENANT_ISOLATION.md`** — Canonical reference for the two-layer isolation model, named cross-tenant API, per-tenant module database model, and runbook for adding new tenant-scoped tables.

---

## Configuration Changes

### New environment variables (SMTP — required for email delivery)

```bash
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
SMTP_USE_TLS=true
NOTIFICATION_WORKER_INPROCESS=false
NOTIFICATION_WORKER_POLL_SECONDS=5
NOTIFICATION_WORKER_BATCH_SIZE=20
```

### New environment variables (module database strategy)

```bash
DATABASE_STRATEGY=per_tenant
TENANT_DELETION_POLICY=archive
```

### Database migrations

Run `alembic upgrade head` to apply:
- `tenant_module_databases` table (Epic 22)
- `module_activations` table with nullable `company_id` and `visibility` columns (Epic 23)
- `module_registry.install_status` column additions (Epic 23)

---

## Known Issues / Deferred Work

| Item | Status |
|---|---|
| `rbac.js` retrofit with new layout primitives | DEFERRED |
| Frontend wildcard-permission mirror in `rbac.js:132 hasPermission()` | OPEN |
| Email template system (per-tenant Jinja2 templates) | DEFERRED |
| LISTEN/NOTIFY low-latency wakeup for notification worker | OPEN |
| Company-level module activation UI | DEFERRED (v2) |
| CI/CD pipeline (Epics 19.4.1–19.4.2) | PLANNED |

---

## Technical Reference

- Sprint backlogs: `plan/tasks/tasks-21.md`, `tasks-22.md`, `tasks-23.md`
- Architecture: `plan/architecture/arch-21.md`, `arch-22.md`, `arch-23.md`
- ADRs: `adr-002-smtp-worker-placement`, `adr-003-per-tenant-module-databases`, `adr-005`
- Security reviews: `sec-review-21.md`, `sec-review-22.md`, `sec-review-23.md`
- Test plans: `tests/test-plans/test-plan-21.md`, `test-plan-22.md`
- Tenant isolation reference: `docs/platform/TENANT_ISOLATION.md`
- Module development guide: `docs/modules/MODULE_DEVELOPMENT.md`
