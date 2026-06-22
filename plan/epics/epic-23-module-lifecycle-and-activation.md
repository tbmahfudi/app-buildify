---
artifact_id: epic-23-module-lifecycle-and-activation
type: epic
producer: A3 Product Owner
consumers: [B1 Software Architect, B2 Data Engineer, B3 UX Designer, C1 Tech Lead]
upstream: [vision-03-module-lifecycle-and-activation, research-03-module-lifecycle-and-activation]
downstream: []
status: approved
created: 2026-06-18
updated: 2026-06-18
shape: feature
sprint_target: epic-23 sprint 1
decisions:
  - Story 23.1.1 (API contract) is the gate — no other story may start until it is DONE
  - Packaging format is a sealed tarball (not Git clone) to guarantee dev = prod parity
  - manage.sh is the canonical CLI entry point for developer-side operations (pack, install, uninstall)
  - Tenant activation is at tenant scope; company-level activation (Persona C) deferred to v2 but data model must carry nullable company_id from day one
  - Uninstall is two-phase (deactivate-all then hard-cleanup) and operator-only; tenant admins may only deactivate
  - Uninstall cleanup reuses the Epic 22 story 22.4.5 cleanup service (scope=module) — no parallel code path
  - post_install/post_enable hook wiring is included in story 23.3.2; if a spike finds the event bus insufficient, hooks are descoped to a follow-up
  - 9 stories total across 5 features — under the A3 soft cap of 15
open_questions:
  - Should the pre-activation summary modal be skippable on re-activation? Recommend yes — B3 UX call
  - manage.sh module install trigger in CI/CD: SSH-exec or HTTP webhook to a deploy agent? B1 architecture call
  - module_activations table: should visibility (available to all tenants vs whitelist) be in this epic or deferred? Recommend: add visibility flag to data model now, UI deferred
---

# Epic 23 — Module Lifecycle & Activation

> **SaaS module delivery pipeline** per [`vision-03-module-lifecycle-and-activation`](../vision/vision-03-module-lifecycle-and-activation.md): the platform developer builds, packages, and installs modules with one command; tenant administrators self-service activate and deactivate installed modules. Closes the audit-11 activation-API drift, wires the BaseModule hooks, and delivers the first end-to-end module lifecycle.

---

## Feature 23.1 — API Contract Alignment `[OPEN]`

### Story 23.1.1 — Canonical lifecycle API contract + frontend fix `[OPEN]`

> **Gate story.** All other stories in this epic depend on this contract being settled and the frontend fixed. No parallel work may start until this story is DONE.

#### Backend
*As the platform engineering team, I want a documented, tested, and stable module lifecycle API contract so that the frontend, CLI tooling, and all future stories build against a consistent surface.*
- Audit all existing module endpoints in `backend/app/routers/modules.py`; document the canonical lifecycle state machine: `registered -> installed -> active -> inactive -> uninstalled`
- Confirm the canonical paths: `POST /api/v1/modules/{id}/install`, `POST /api/v1/modules/{id}/enable`, `POST /api/v1/modules/{id}/disable`, `DELETE /api/v1/modules/{id}` (uninstall, operator-only)
- Add `GET /api/v1/modules` response schema: `{id, name, display_name, description, version, category, status, permissions_added, menu_items_added, dependencies}`
- Add `GET /api/v1/modules/{id}/activation-preview` -> `{permissions: [{code, description}], menu_items: [{label, route}], dependencies: [{name, status}]}` — used by the pre-activation modal
- All endpoints return structured error bodies: `{code, message, detail}` — no bare 422/500 strings
- Integration tests covering: install -> enable -> disable -> re-enable cycle; dependency-unmet 409; system module 403 on delete

#### Frontend
*As the platform developer, I want the existing `frontend/assets/js/module-manager.js` updated to call the correct endpoint paths so that the activation UI works without silent 404 failures.*
- Audit `module-manager.js` against the canonical contract from the backend AC
- Replace all calls to the non-existent `/activate` / `/deactivate` paths with the correct `/install` + `/enable` / `/disable` paths
- Update response-shape handling to match the new structured error body
- No visual changes to the modules page — this story is a contract fix, not a UI redesign

---

## Feature 23.2 — Module Packaging Pipeline `[OPEN]`

### Story 23.2.1 — Manifest JSON schema validation `[OPEN]`

#### Backend
*As the platform developer registering a module, I want the platform to validate the full manifest against a JSON schema on registration so that a malformed manifest is rejected with per-field errors before it can cause a silent install failure.*
- Create `backend/app/core/module_system/manifest.schema.json` covering all required and optional manifest fields: `name`, `display_name`, `version` (semver), `module_type` (code|nocode), `category`, `api_prefix`, `permissions[]`, `menu_items[]`, `routes[]`, `event_subscriptions[]`, `dependencies[]`
- `POST /api/v1/modules/register` validates the incoming manifest against the schema using `jsonschema`; returns `422` with `{errors: [{field, message}]}` on violation
- Registration rejects manifests with non-semver `version` values
- A `POST /api/v1/modules/validate` endpoint (dry-run, no DB write) returns the same validation result — used by the Register modal and `manage.sh module pack`
- Closes audit-11 story 11.1.1 gap

#### Frontend
*No frontend story — the Register modal already calls /validate; it will automatically surface the new per-field errors once the endpoint is fixed.*

---

### Story 23.2.2 — `manage.sh module pack` command `[OPEN]`

#### Backend
*As the platform developer, I want a `manage.sh module pack` command that produces a sealed, versioned tarball artifact from a module directory so that I have a reproducible deployable that is identical between dev and prod.*
- `manage.sh module pack <module_dir> [--out <dir>]` produces `<name>_<version>.tar.gz` containing: `backend/` (module FastAPI service), `frontend/` (JS assets if any), `manifest.json`, `migrations/` (Alembic versions), `install.sh` (idempotency script)
- Pack command runs `POST /api/v1/modules/validate` against the manifest before producing the tarball; exits non-zero if validation fails
- The tarball is content-addressable: includes a `SHA256SUMS` file; `module install` verifies the checksum before applying
- Pack is runnable in dev with no prod dependencies; only requires the module directory

#### Frontend
*No frontend story — developer CLI tool only.*

---

## Feature 23.3 — Production Install Pipeline `[OPEN]`

### Story 23.3.1 — `manage.sh module install` with atomic rollback `[OPEN]`

#### Backend
*As the platform developer, I want `manage.sh module install <tarball>` to install a module to the platform in a single command with automatic rollback on failure so that production is never left in a partial state.*
- `manage.sh module install <tarball>` performs in order:
  1. Verify SHA256 checksum
  2. Validate manifest (calls `POST /api/v1/modules/validate`)
  3. Record install attempt in `module_registry` with `install_status=in_progress`
  4. Run module Alembic migrations against the platform DB (`alembic upgrade head` scoped to the module's migration path)
  5. Copy module backend service into the modules directory; reload the FastAPI router (no full restart)
  6. Copy module frontend assets; invalidate static file cache
  7. Call `POST /api/v1/modules/register` with the manifest
  8. Set `module_registry.install_status=ready`
- On failure at any step: reverse completed steps in reverse order; set `install_status=failed` with `error_message`; exit non-zero
- Idempotent: re-running install on the same `name+version` is a no-op (returns exit 0 with a message "already installed")
- Output: structured log lines with step name, duration, and pass/fail per step

#### Frontend
*No frontend story — developer CLI tool only.*

---

### Story 23.3.2 — `BaseModule` hook wiring `[OPEN]`

#### Backend
*As a module developer, I want `BaseModule.post_install()` and `BaseModule.post_enable()` to fire reliably on the correct lifecycle event so that modules can run initialisation logic (seed data, default config, default roles) without me wiring the subscription manually.*
- Spike first (before implementing): verify the existing in-process event bus (`backend/app/core/event_bus.py` or equivalent) can deliver `module.installed` and `module.enabled` events synchronously within the install/enable request; document findings
- If spike passes: wire `module.installed` -> `BaseModule.post_install()` and `module.enabled` -> `BaseModule.post_enable()` in the module loader (`backend/app/core/module_system/loader.py`)
- If spike fails (bus insufficient): document the gap, descope hook wiring to a follow-up, and mark this story `[DEFERRED]` with a note — DO NOT block the epic on it
- Add an integration test: install a test module stub with a `post_install` that writes a sentinel row; assert the row exists after `manage.sh module install`
- Closes audit-11 cross-cutting gap

#### Frontend
*No frontend story — internal hook wiring.*

---

## Feature 23.4 — Tenant Activation UI `[OPEN]`

### Story 23.4.1 — Modules list page `[OPEN]`

#### Backend
*As a tenant administrator, I want `GET /api/v1/modules` to return all installed modules with my tenant's activation status so that the UI can show which are active and which are available.*
- `GET /api/v1/modules` (tenant-scoped): returns list with `activation_status` field per module: `active | inactive | activating | deactivating`
- `activation_status` is derived from `module_activations` table (new: `tenant_id`, `module_id`, `status`, `activated_at`, `activated_by`)
- `company_id` column present in `module_activations` and nullable from day one (company-level activation deferred to v2)
- `visibility` column on `module_registry`: default `all_tenants`; reserved for future whitelist support
- Superadmin sees all tenants' activation states via `GET /api/v1/admin/modules/activations`

#### Frontend
*As a tenant administrator, I want a Modules page that lists all installed modules with their status so that I can see at a glance what is available and what I have already activated.*

- Page Layout:
  - Route: `#/settings/modules` -> existing `modules.html` + new `modules-page.js`
  - Root: FlexStack(direction=vertical, gap=lg) > page-header-zone, modules-grid-zone

- Zone — page-header-zone:
  - FlexToolbar: left=[FlexBreadcrumb([{label:"Settings", href:"#/settings"}, {label:"Modules"}])] | right=[] (tenant admin has no install action)

- Zone — modules-grid-zone:
  - FlexGrid(columns=auto-fill minmax(280px,1fr), gap=md)
  - One ModuleCard per module returned by `GET /api/v1/modules`

- Component Spec — ModuleCard (FlexCard, variant=outlined):
  - header: FlexCluster(align=center, gap=sm) > module-icon(48px, rounded-lg) | FlexStack(gap=xs) > name(h3, font-semibold) | FlexBadge(chip, color=neutral) version
  - body: FlexStack(gap=xs) > FlexBadge(chip, color=neutral) category | p(2-line clamp, color=text-muted) description
  - footer: FlexCluster(justify=space-between, align=center) > status-badge | action-button
    - status-badge: FlexBadge(color=success, icon=ph-check-circle) "Active" [is_enabled=true] | FlexBadge(color=neutral) "Available" [is_enabled=false]
    - action-button: FlexButton(variant=primary, size=sm) "Activate" [is_enabled=false] | FlexButton(variant=ghost, size=sm, color=danger) "Deactivate" [is_enabled=true]

- States:
  - loading: FlexGrid with 6 skeleton FlexCard placeholders (animate-pulse) while GET /modules resolves
  - empty: FlexStack(align=center, gap=md) > ph-package(64px, color=text-muted) | p "No modules are installed on this platform yet."
  - error: FlexAlert(type=error, dismissible=false) "Could not load modules. Retry?" — Retry link re-calls GET /modules

- Interactions:
  - click "Activate" on card: open ActivationModal (story 23.4.2) with module context
  - click "Deactivate" on card: open DeactivateModal (story 23.4.3) with module context
  - on activation success event: patch card in-place — status-badge=Active, action-button="Deactivate"
  - on deactivation success event: patch card in-place — status-badge=Available, action-button="Activate"

------

### Story 23.4.2 — Module activate flow with pre-activation summary `[OPEN]`

#### Backend
*As a tenant administrator, I want to activate a module for my tenant so that my team gains access to its features.*
- `POST /api/v1/modules/{id}/enable` (renamed from `/activate` per story 23.1.1 contract)
  - Checks dependencies: all declared dependency modules must have `activation_status=active` for this tenant; returns 409 `{code: "dependencies_unmet", missing: [{name, id}]}` if not
  - On success: creates `module_activations` row with `status=active`; merges module menu items into the tenant's menu tree; seeds module RBAC permissions into the tenant's permission set
  - Writes `audit_logs` row: `action=module.enabled`, `entity_type=module`, `entity_id=module_id`, `tenant_id`
  - Returns `{status: "active", permissions_added: [...], menu_items_added: [...]}`

#### Frontend
*As a tenant administrator, I want a pre-activation summary modal that shows exactly what the module will add before I confirm, so that I can activate confidently.*

- Component Spec — ActivationModal (FlexModal, size=md, backdropDismiss=false):
  - header: FlexCluster(align=center, gap=sm) > module-icon(32px) | "Activate [Module Name]"
  - body: FlexStack(gap=md) >
    - preview-loading state: FlexStack(gap=sm) > 3x skeleton-row(animate-pulse, h=16px, rounded)
    - preview-loaded state: FlexStack(gap=md) >
      - FlexAlert(type=info, icon=ph-info) "The following will be added to your account:"
      - permissions-section: FlexStack(gap=xs) > span("Permissions", font-semibold, size=sm) | [per permission: FlexCluster(gap=sm) > ph-lock-simple(16px, color=text-muted) | span(permission.description)]
      - menu-items-section: FlexStack(gap=xs) > span("Menu items", font-semibold, size=sm) | [per item: FlexCluster(gap=sm) > ph-list(16px, color=text-muted) | span(item.label) | FlexBadge(chip, color=neutral, size=xs) item.route]
      - dependencies-section (render only when preview.dependencies.length > 0):
        - span("Requires", font-semibold, size=sm)
        - [per dep: FlexCluster(gap=sm) > status-dot(green=active, red=inactive) | span(dep.name) | FlexBadge(color=success) "Active" or FlexBadge(color=danger) "Not activated"]
        - FlexAlert(type=warning, icon=ph-warning) "Activate required modules first." [shown only when any dep is inactive]
  - footer: FlexButton(variant=ghost) "Cancel" | FlexButton(variant=primary, id=confirm-btn) "Confirm Activation" [disabled when any dep inactive]

- States:
  - preview-loading: skeleton rows in modal body; Confirm button disabled
  - deps-unmet: Confirm button disabled; warning FlexAlert visible in body
  - activating: both footer buttons disabled; Confirm shows inline spinner + label "Activating..."
  - activated: modal closes; modules-page patches ModuleCard to Active state
  - error: FlexAlert(type=error) "Activation failed: [message]" shown above footer; buttons re-enabled

- Interactions:
  - [triggered by "Activate" click on ModuleCard]: GET /modules/{id}/activation-preview -> populate body; open modal
  - click "Cancel": close modal; no state change
  - click "Confirm Activation" (deps met): POST /modules/{id}/enable -> on success: close modal, emit 'module:activated'; on error: show error FlexAlert

------

### Story 23.4.3 — Module deactivate flow `[OPEN]`

#### Backend
*As a tenant administrator, I want to deactivate a module for my tenant so that its features are hidden, without losing any data my team has created.*
- `POST /api/v1/modules/{id}/disable`
  - Checks dependents: if other active modules depend on this module, returns 409 `{code: "dependents_active", dependents: [{name, id}]}`
  - On success: updates `module_activations` row to `status=inactive`; removes module menu items from tenant's menu tree; disables module RBAC seeds (marks inactive, does not delete)
  - Data rows created by the module are NOT touched — they belong to the tenant
  - Writes `audit_logs` row: `action=module.disabled`, `entity_type=module`, `entity_id=module_id`

#### Frontend
*As a tenant administrator, I want a deactivation confirmation that explicitly tells me my data will not be deleted so that I can deactivate without anxiety.*

- Component Spec — DeactivateModal (FlexModal, size=sm, backdropDismiss=true):
  - header: "Deactivate [Module Name]?"
  - body: FlexStack(gap=md) >
    - FlexAlert(type=warning, icon=ph-shield-warning) "Your data will not be deleted. Menu items and permissions added by this module will be hidden for all users in your account. You can reactivate at any time."
    - dependents-section (render only when dependents list is non-empty):
      - FlexAlert(type=error, icon=ph-link-break) "The following active modules depend on this one and must be deactivated first:"
      - FlexStack(gap=xs) > [per dependent: FlexCluster(gap=sm) > ph-cube(16px) | span(dependent.name)]
  - footer: FlexButton(variant=ghost) "Cancel" | FlexButton(variant=danger, id=deactivate-btn) "Deactivate" [disabled when dependents non-empty]

- States:
  - dependents-blocking: Deactivate button disabled; error FlexAlert lists blocking modules
  - deactivating: both buttons disabled; Deactivate shows inline spinner + label "Deactivating..."
  - deactivated: modal closes; modules-page patches ModuleCard to Available state
  - error: FlexAlert(type=error) "Deactivation failed: [message]" above footer; buttons re-enabled

- Interactions:
  - [triggered by "Deactivate" click on ModuleCard]: check module dependents from cached GET /modules response; open modal
  - click "Cancel": close modal; no state change
  - click "Deactivate" (no blocking dependents): POST /modules/{id}/disable -> on success: close modal, emit 'module:deactivated'; on error: show error FlexAlert

------

## Feature 23.5 — Operator Uninstall & Audit Trail `[OPEN]`

### Story 23.5.1 — Operator uninstall (two-phase) `[OPEN]`

#### Backend
*As the platform operator (superadmin), I want to uninstall a module from the platform in two phases — deactivate-all then hard-cleanup — so that removal is safe, reversible at phase 1, and leaves no orphaned data.*
- Phase 1 — `POST /api/v1/admin/modules/{id}/deactivate-all` (superadmin only):
  - Deactivates the module for every tenant that has it active
  - Sets `module_registry.status = deactivation_pending`
  - Writes one `audit_logs` row per tenant: `action=module.deactivated`, plus a summary row `action=module.deactivate_all`
  - Returns `{tenants_deactivated: N}`
- Phase 2 — `DELETE /api/v1/admin/modules/{id}` (superadmin only, requires `X-Confirm-Uninstall: true` header):
  - Callable only when `module_registry.status = deactivation_pending` (phase 1 must have completed)
  - Calls Epic 22 cleanup service with `scope=module, module_id=id` to drop per-tenant module DBs if `DATABASE_STRATEGY=per_tenant`
  - Removes `module_activations` rows, RBAC permission seeds, menu item registrations for this module
  - Removes module backend service from modules directory; removes frontend assets
  - Deletes `module_registry` row
  - Writes `audit_logs` row: `action=module.uninstalled`
- A `manage.sh module uninstall <name>` command runs both phases sequentially with a confirmation prompt between them

#### Frontend
*No dedicated uninstall UI — operator performs uninstall via `manage.sh` CLI. The Modules page (story 23.4.1) will reflect the module disappearing from the list after uninstall.*

---

### Story 23.5.2 — Audit trail for all module lifecycle events `[OPEN]`

#### Backend
*As a platform operator or tenant administrator reviewing the audit log, I want every module lifecycle state change to appear in `audit_logs` with full context so that I can answer "who activated what module and when" without querying raw DB tables.*
- Verify and consolidate audit log writes across all stories in this epic; ensure every state transition writes exactly one row:
  - `module.installed` (platform-level, no tenant_id)
  - `module.enabled` (per-tenant activation)
  - `module.disabled` (per-tenant deactivation)
  - `module.deactivate_all` (operator action)
  - `module.uninstalled` (platform-level)
- Standard fields: `action`, `entity_type=module`, `entity_id=module_id`, `tenant_id` (null for platform-level events), `performed_by`, `metadata` (JSON: version, affected_tenant_count where relevant)
- `GET /api/v1/audit-logs?entity_type=module` returns paginated module lifecycle events
- Superadmin audit view surfaces module events alongside other platform events (no UI change needed — existing audit log page handles `entity_type` filtering)

#### Frontend
*No new frontend story — existing audit log page (`#/audit`) already handles entity_type filtering. Verify `entity_type=module` filter works and returns the new events.*

---

## Sprint-Level Definition of Done

This epic is `[DONE]` when:

- [ ] Story 23.1.1 gate is DONE and the API contract is documented in a decision log or ADR
- [ ] All 9 stories meet their Backend AC
- [ ] Stories 23.4.1, 23.4.2, 23.4.3 frontend sections render correctly in a real browser against the live dev stack
- [ ] `manage.sh module pack` produces a valid tarball; `manage.sh module install` installs it idempotently with rollback on forced failure
- [ ] `BaseModule.post_install` fires in integration test (or story 23.3.2 is formally `[DEFERRED]` per its own AC)
- [ ] All module lifecycle events appear in `GET /api/v1/audit-logs?entity_type=module`
- [ ] No regression in any `test-plan-21` scenario (RBAC, dynamic CRUD, notifications)
- [ ] D3 Security Engineer publishes `sec-review-23.md` with verdict CLEAR TO SHIP
- [ ] E2 Technical Writer publishes `release-notes-epic-23.md`

---

## Hand-off

This epic is `status: review`. Once approved (human stakeholder per A3 spec):
- **B1 Software Architect** — author `arch-23.md` covering: module lifecycle state machine, tarball packaging format, install/rollback transaction design, BaseModule hook event bus wiring, coordination with Epic 22 cleanup service
- **B2 Data Engineer** — `schema-23.md` covering: `module_activations` table (with nullable `company_id` and `visibility` flag), `module_registry` install_status column additions
- **B3 UX Designer** — UILDC detail for stories 23.4.1, 23.4.2, 23.4.3 (ModuleCard, ActivationModal, DeactivateModal)
- **C1 Tech Lead** — `tasks-23.md` once B1/B2/B3 approved; first task MUST implement story 23.1.1 (API contract gate)
