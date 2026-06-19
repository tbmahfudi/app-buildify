# Changelog

All notable changes to App-Buildify are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-06-20

### Added

#### Epic 21 — Risk Retirement
- Self-service custom role CRUD for tenant administrators (`POST/PUT/DELETE /api/v1/rbac/roles`)
- New permission codes: `roles:create:tenant`, `roles:update:tenant`, `roles:delete:tenant`
- Wildcard permission matching (`*:*:platform`, segment-level wildcards) in the RBAC engine (~6 µs hot path)
- Per-entity permission control: `EntityDefinition.permissions` JSONB with role × action matrix; `PUT /api/v1/data-model/entities/{id}` accepts `permissions` field
- Notification queue worker (`notification-worker` container) with SMTP delivery, exponential backoff, and dead-letter handling
- Nine Flex layout components: `flex-stack`, `flex-grid`, `flex-sidebar`, `flex-split-pane`, `flex-container`, `flex-section`, `flex-cluster`, `flex-toolbar`, `flex-masonry`

#### Epic 22 — Tenant Isolation Hardening
- `backend/app/core/scope.py`: `apply_tenant_scope()`, `tenant_scope_dependency`, `TenantScopeMissingError`, `with_admin_cross_tenant_scope()` context manager
- `manage.sh check-tenant-scope` pre-merge gate script
- SQLAlchemy `before_compile` session-event listener that auto-injects tenant scope and raises on missing context
- `tenant_scoped_session(user, db)` FastAPI dependency for per-request scope binding
- `DATABASE_STRATEGY=per_tenant` env var and `tenant_module_databases (tenant_id, module_id, connection_url, status, created_at)` registry table
- `ModuleScopeMiddleware` for automatic per-(tenant, module) database routing with bounded LRU connection pool (50 active pools)
- `scripts/provision-tenant-module-db.py` for per-tenant module database provisioning
- `scripts/migrate-module.py <module_id>` for Alembic fan-out across all tenant-deployed instances (parallel, bounded concurrency = 4)
- `cleanup_tenant_module_dbs(tenant_id)` service; `TENANT_DELETION_POLICY=drop|archive` env var
- `manage.sh tenant deactivate <id>` command
- `manage.sh module migrate-tenant <tenant_id> <module_id>` command with dry-run mode
- `BaseModule.tenant_scoped: bool = True` and `get_tenant_scoped_tables() -> List[str]` to BaseModule SDK
- `docs/platform/TENANT_ISOLATION.md` canonical isolation reference
- 40-scenario adversarial test plan at `tests/test-plans/test-plan-22.md`
- Provisioning status badges (Provisioning / Ready / Failed + retry) on the Modules page

#### Epic 23 — Module Lifecycle and Activation
- `backend/app/core/module_system/manifest.schema.json` and manifest validation on `POST /api/v1/modules/register`
- `POST /api/v1/modules/validate` dry-run endpoint
- `manage.sh module pack <dir>` command producing a content-addressable tarball with `SHA256SUMS`
- `manage.sh module install <tarball>` command with eight-step atomic install and reverse rollback
- `manage.sh module uninstall <name>` two-phase uninstall command
- `BaseModule.post_install()` and `post_enable()` hook wiring via in-process event bus
- `module_activations (tenant_id, module_id, status, activated_at, activated_by, company_id, visibility)` table; `company_id` nullable from day one
- `GET /api/v1/modules` returns `activation_status` per module for the requesting tenant
- `GET /api/v1/modules/{id}/activation-preview` pre-activation summary endpoint
- `POST /api/v1/admin/modules/{id}/deactivate-all` operator endpoint
- Modules list page (`#/settings/modules`) with ModuleCard grid, activation status badges, and Activate / Deactivate actions
- ActivationModal with pre-activation permission and menu-item summary; dependency blocking
- DeactivateModal with explicit data-retention assurance; dependent-blocking
- Full module lifecycle audit trail: `module.installed`, `module.enabled`, `module.disabled`, `module.deactivate_all`, `module.uninstalled` in `audit_logs`
- `GET /api/v1/audit-logs?entity_type=module` for module lifecycle event filtering

#### Epic 24 — Frontend Capability Surfacing
- Forgot-password flow: `#reset-password` and `#reset-password-confirm` routes
- Live password-strength feedback on all password fields (calls `GET /api/v1/auth/password-policy`)
- Notification settings honesty banner (persistent warning when SMTP not configured)
- Data-model entity publish button with migration diff preview
- Automation rule test panel (fire mock event, view action trace)
- Automation execution history (last 50 entries per rule)
- Scheduler job execution log viewer (collapsible per-run log panel)
- NoCode page builder version history sidebar (last 20 versions, diff and restore)
- Workflow simulator panel (manual state-machine transition without live execution)
- Access Control permission matrix table (role × permission, editable)
- Dashboard share (copy link) and snapshot (save named filter state) buttons
- User effective permissions panel on user detail page

### Changed

- Module activation/deactivation paths canonicalized: `/activate` and `/deactivate` replaced by `/enable` and `/disable`; all router registrations at `POST /api/v1/modules/{id}/enable` and `/disable`
- `module-manager.js` updated to call canonical paths and handle structured `{code, message, detail}` error bodies
- All `*Service` classes migrated from ad-hoc `Model.tenant_id == user.tenant_id` literals to `apply_tenant_scope()`
- `DynamicEntityService._get_org_context()` delegates to `scope.py` helper
- Financial module: new tenants get per-tenant database; existing tenants retain shared until manual migration
- `infra/docker-compose.prod.yml` updated with tagged image references, named volumes, health-check dependencies, and `notification-worker` service
- `docs/modules/MODULE_DEVELOPMENT.md` updated with `BaseModule` tenant_scoped contract and packaging/lifecycle hook docs

### Deprecated

- `DATABASE_STRATEGY=separate` — use `per_tenant` instead; will be removed in a future release

### Fixed

- Modules migration CHECK constraint: invalid quoting in `module_registry` Alembic migration caused `ProgrammingError` on fresh DB initialization
- `manage.sh` health URL: healthcheck was pointing to a removed endpoint, causing false "unhealthy" reports
- E2E auth helper race condition causing intermittent 401 failures on the first test in a Playwright suite
- `vitest.config.js` now excludes `tests/e2e/**` to prevent unit-test runs from attempting to execute Playwright specs
- DEF-027: relationship traversal null-pointer on missing related record
- DEF-028: aggregation hint cache not invalidated on entity schema update
- DEF-029: bulk-delete partial-failure rollback leaving orphan records
- DEF-030: entity-version diff rendering blank for added fields
- DEF-031: dynamic-filter URL serialization dropping array parameters

### Security

- Tenant isolation hardened: SQLAlchemy listener converts forgotten `tenant_id` filter from silent cross-tenant data leak to a loud `TenantScopeMissingError`
- Cross-tenant reads now require explicit `with_admin_cross_tenant_scope()` with audit logging and superuser enforcement
- Physical database separation for module data: per-tenant module databases isolate data at the infrastructure level
- 40-scenario adversarial test plan verifying isolation guarantees (all pass)

---

## [1.0.0] - 2026-05-08

Initial platform release covering Epics 1–19 (core authentication, multi-tenancy, user management, RBAC, NoCode entity designer, dynamic CRUD, workflow engine, automation rules, dashboards, reporting, module system, notifications, Flex component library, internationalization, settings, developer SDK, and infrastructure).
