---
artifact_id: release-notes-epic-23
type: release-notes
producer: E2 Technical Writer
consumers: [stakeholders, tenant administrators, operators, platform developers]
upstream: [epic-23-module-lifecycle-and-activation, tasks-23, arch-23, adr-005-module-packaging-format]
downstream: []
status: draft
created: 2026-06-26
updated: 2026-06-26
sprint: epic-23 -- Module Lifecycle & Activation
---

# Release Notes -- Module Lifecycle & Activation (epic-23)

> **TL;DR**: Operators can now package and install modules with a single `manage.sh` command; tenant administrators self-service activate and deactivate installed modules through a new **Modules** page with a pre-activation permissions summary. All 28 tasks are DONE. **No breaking changes.** No new environment variables are required.

---

## Overview

Epic 23 delivers the first complete end-to-end module lifecycle for App-Buildify. On the developer side, `manage.sh module pack` seals a module directory into a versioned, SHA256-verified tarball, and `manage.sh module install` deploys it to the platform atomically -- running migrations, registering the module, and firing `BaseModule.post_install()` -- with automatic rollback on any failure. On the tenant side, a new **Settings -> Modules** page lists every installed module with its current activation status; tenant administrators can activate a module through an ActivationModal that shows the exact permissions and menu items that will be added before they confirm, or deactivate with a DeactivateModal that blocks removal when another active module still depends on the one being disabled. Operator-level uninstall is a two-phase CLI operation (deactivate-all then hard cleanup) enforced by the API. Every lifecycle state transition is recorded in `audit_logs` and is queryable via `GET /api/v1/audit-logs?entity_type=module`.

---

## User-visible changes

### New `#/settings/modules` page

Tenant administrators now have a **Modules** page at `#/settings/modules`. The page renders a responsive grid of ModuleCards -- one per installed module -- showing the module icon, name, version, category, a two-line description, and its current status badge (Active / Available). While the module list loads, six skeleton placeholder cards animate in place; on network error a dismissible alert offers a Retry link.

Each ModuleCard has a single context-appropriate action button:

- **Activate** (primary, shown when the module is Available) -- opens the ActivationModal.
- **Deactivate** (ghost/danger, shown when the module is Active) -- opens the DeactivateModal.

Cards update in-place after a successful activation or deactivation -- no page reload required.

### ActivationModal -- pre-activation summary before confirmation

Clicking **Activate** on a ModuleCard fetches `GET /api/v1/modules/{id}/activation-preview` and opens an ActivationModal. Before any change is made, the modal shows:

- **Permissions** -- each permission code that will be added to the tenant's RBAC, with its human-readable description.
- **Menu items** -- each navigation entry that will appear, with its route.
- **Dependencies** -- all modules this module requires, each labelled Active (green dot) or Not activated (red dot).

The **Confirm Activation** button is disabled when any dependency is not yet active, and a warning alert prompts the administrator to activate the required modules first. While activation is in progress both buttons are disabled and the Confirm button shows an inline spinner. On success the modal closes and the ModuleCard updates to Active state.

### DeactivateModal -- safety message and dependents blocking list

Clicking **Deactivate** opens a DeactivateModal that prominently states: *Your data will not be deleted. Menu items and permissions added by this module will be hidden for all users in your account. You can reactivate at any time.*

If other active modules depend on the module being deactivated, they are listed in a blocking error alert and the **Deactivate** button is disabled until those dependents are deactivated first. Once no blocking dependents exist, confirming deactivation hides the module's menu items and marks its RBAC permission seeds inactive for the tenant (data rows created by the module are untouched).

---

## API additions

All new endpoints return structured error bodies of the form `{code, message, detail}`. 409 responses include machine-readable `code` values (`dependencies_unmet`, `dependents_active`) so callers can programmatically distinguish error types.

| Method | Path | Actor | Purpose |
|--------|------|-------|---------|
| `GET` | `/api/v1/modules` | Tenant admin | List all installed modules with per-tenant `activation_status` (`active | inactive | activating | deactivating`). Filters to `install_status=ready` and `visibility=all_tenants`. |
| `GET` | `/api/v1/modules/{id}/activation-preview` | Tenant admin | Returns `{permissions: [{code, description}], menu_items: [{label, route}], dependencies: [{name, id, status}]}` -- used by the ActivationModal before confirmation. |
| `POST` | `/api/v1/modules/{id}/enable` | Tenant admin | Activate a module for the requesting tenant. Checks that all declared dependency modules are `active` for this tenant; returns `409 {code: "dependencies_unmet", missing: [...]}` if not. On success merges manifest menu items into the tenant's menu tree, seeds manifest permissions into the tenant's RBAC, creates a `ModuleActivation` row, and writes `audit_logs(module.enabled)`. Returns `{status: "active", permissions_added: [...], menu_items_added: [...]}`. |
| `POST` | `/api/v1/modules/{id}/disable` | Tenant admin | Deactivate a module for the requesting tenant. Returns `409 {code: "dependents_active", dependents: [...]}` when other active modules depend on this one. On success removes module menu items, sets module permission seeds to inactive (does not delete), updates `ModuleActivation`, and writes `audit_logs(module.disabled)`. |
| `POST` | `/api/v1/modules/validate` | Developer CLI / Register modal | Dry-run manifest validation against `manifest.schema.json`. No database write. Returns `{valid: true}` or `{valid: false, errors: [{field, message}]}`. |
| `POST` | `/api/v1/admin/modules/{id}/deactivate-all` | Superadmin | Phase 1 of operator uninstall. Deactivates the module for every tenant that has it active; sets `Module.install_status=deactivation_pending`; writes one `audit_logs` row per tenant plus a summary `audit_logs(module.deactivate_all)` row. Returns `{tenants_deactivated: N}`. |
| `DELETE` | `/api/v1/admin/modules/{id}` | Superadmin | Phase 2 of operator uninstall. Requires `X-Confirm-Uninstall: true` header and `install_status=deactivation_pending` (phase 1 must have completed). Calls the Epic 22 cleanup service (`scope=module`), removes `module_activations`, RBAC seeds, and menu registrations, removes module files from disk, deletes the `modules` row, and writes `audit_logs(module.uninstalled)`. |

> **Existing endpoints unchanged**: the legacy `/module-registry/*` endpoints are not modified. The `/activate` and `/deactivate` path aliases in `module-manager.js` have been corrected to the canonical `/enable` and `/disable` paths (T-23.004); this correction is transparent to end users.

---

## CLI additions

Three new subcommands are added to `manage.sh`:

### `manage.sh module pack <module_dir> [--out <dir>]`

Validates the module manifest against `manifest.schema.json` (calls `POST /api/v1/modules/validate`) then produces a sealed, versioned tarball:

```
<name>_<version>.tar.gz   -- contains backend/, frontend/, manifest.json, migrations/, install.sh
SHA256SUMS                -- content-addressable checksum for the tarball
```

File timestamps are normalised for determinism; the tarball is identical across machines for the same source tree. The command exits non-zero if manifest validation fails and prints per-field errors. The tarball is a build artifact and should not be committed to source control (see [ADR-005](../../plan/architecture/adr-005-module-packaging-format.md)).

### `manage.sh module install <tarball>`

Installs a module tarball to the platform in eight ordered steps, each logged with step name, duration, and pass/fail:

1. Verify SHA256 checksum
2. Validate manifest
3. Set `Module.install_status=in_progress`
4. Run module Alembic migrations
5. Copy module backend service into `modules/<name>/backend/`; reload FastAPI router (no full restart)
6. Copy frontend assets; invalidate static file cache
7. Call `POST /api/v1/modules/register`
8. Call `BaseModule.post_install(db)`; set `install_status=ready`

On failure at any step the completed steps are reversed in order, `install_status` is set to `failed` with an `install_error_message`, and the command exits non-zero. Re-running `install` on the same `name+version` is idempotent -- it exits 0 with the message "already installed".

### `manage.sh module uninstall <name>`

Two-phase operator uninstall with a confirmation prompt between phases:

- **Phase 1**: calls `POST /api/v1/admin/modules/{id}/deactivate-all`, prints how many tenants were deactivated, and prompts for confirmation before phase 2.
- **Phase 2** (after confirmation): calls `DELETE /api/v1/admin/modules/{id}` with the required `X-Confirm-Uninstall: true` header.

---

## Schema changes

### `modules` table -- three new columns

Added by Alembic migration `pg_module_lifecycle_columns` (T-23.016). Migration is reversible (forward + backward tested).

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `install_status` | `VARCHAR` | `ready` | Lifecycle phase: `in_progress | ready | failed | deactivation_pending`. Enforced by a `CheckConstraint`. |
| `install_error_message` | `TEXT` | `NULL` | Populated when `install_status=failed`; null otherwise. |
| `visibility` | `VARCHAR` | `all_tenants` | Controls which tenants can see the module. Currently only `all_tenants` is active; `whitelist` is reserved for a future sprint. Enforced by a `CheckConstraint`. |

The `Module` SQLAlchemy model in `backend/app/models/nocode_module.py` has been updated to reflect all three columns and their constraints (T-23.017).

### `module_activations` table

Pre-existing table; no new columns added in this epic. A nullable `company_id` column is present from day one to carry company-level activation state when that feature ships (deferred to v2).

### `manifest.schema.json`

New file at `backend/app/core/module_system/manifest.schema.json`. Key constraints:

- `version` must satisfy strict semver pattern (e.g. `1.2.0`; `1.2.0-beta.1` accepted; bare integers rejected).
- `additionalProperties: false` at the top level -- unrecognised manifest keys are a validation error, not silently ignored.
- Required fields: `name`, `display_name`, `version`, `module_type` (`code | nocode`), `category`, `api_prefix`.
- Optional arrays: `permissions[]`, `menu_items[]`, `routes[]`, `event_subscriptions[]`, `dependencies[]`.

---

## Security

### H-1 -- Per-tenant permission namespacing

Module RBAC permissions seeded on activation are scoped to `current_user.tenant_id` derived from the JWT. The `tenant_id` is never accepted from the request body on `/enable` or `/disable`. This ensures a tenant administrator cannot activate a module in a way that bleeds permissions into another tenant's namespace. D3 Security Engineer reviewed T-23.020 and T-23.022 before merge.

### H-2 -- Safe subprocess for module file removal

The operator uninstall path (phase 2, T-23.025) removes module files from disk using a safe, path-validated call rather than unsanitised shell string interpolation. The module name and version are validated against the `module_registry` row before any filesystem operation, preventing directory-traversal attacks.

---

## Breaking changes

**None.** All changes are additive:

- New API endpoints -- no existing endpoint paths or response shapes are changed.
- New `modules` table columns all carry defaults; existing rows are unaffected.
- The `module-manager.js` path correction (T-23.004) fixes calls that were already failing silently (404s against the non-existent `/activate` and `/deactivate` paths); no previously working call is broken.
- Legacy `/module-registry/*` endpoints are unchanged.

---

## Configuration / environment variables

No new environment variables are introduced by this epic. The `manage.sh module` subcommands read `PLATFORM_API_URL` and `PLATFORM_API_KEY` from the existing `.env` file used by the rest of `manage.sh`.

---

## Known issues

| ID | Description | Status |
|----|-------------|--------|
| **DEF-032** | Event-coverage tests for `module.installed` and `module.enabled` are marked `xfail` in the QA suite. `BaseModule` hooks are wired as direct Python method calls (not event-bus events) per the T-23.013 spike decision; the test harness expects event-bus emissions that do not fire because no loadable module class is registered in the dev stack. Tests will pass once a dev-stack stub module is wired in. | Open |

---

## Deferred items

| Item | Reason | Notes |
|------|--------|-------|
| **T-23.1.6 -- `rbac.js` layout component retrofit** | Same constraint as Epic 21 deferral: the 1,296-line `rbac.js` and 407-line template require a wholesale rewrite. Out of scope for this sprint. | The new `modules-page.js` is built with the full Flex layout suite. The `rbac.js` retrofit remains on the backlog. |
| **Event bus for `post_install` / `post_enable` hooks** | T-23.013 spike confirmed direct Python method calls are sufficient for the in-process case; no event bus needed now. | If a future distributed deployment mode requires out-of-process hook delivery, the event bus can be wired without changing the `BaseModule` API surface. |
| **Company-level activation UI (Persona C)** | Data model is ready (`company_id` nullable in `module_activations`). | API filtering and UI for company scope are deferred to v2. |
| **`visibility=whitelist` tenant filtering** | `visibility` column and `CheckConstraint` are in place. | `module_tenant_whitelist` table and associated admin UI are deferred to a future sprint. |

---

## Technical reference

- **Sprint backlog**: [`tasks-23`](../../plan/tasks/tasks-23.md) -- 28 tasks DONE (~85 hrs estimated)
- **System design**: [`arch-23`](../../plan/architecture/arch-23.md) -- module lifecycle state machine, install/rollback transaction design, BaseModule hook wiring, menu + RBAC integration on enable/disable
- **ADR**: [`adr-005-module-packaging-format`](../../plan/architecture/adr-005-module-packaging-format.md) -- sealed tarball rationale vs Git clone vs OCI image
- **Epic spec**: [`epic-23-module-lifecycle-and-activation`](../../plan/epics/epic-23-module-lifecycle-and-activation.md)
- **Prior sprint**: [`release-notes-epic-21`](./release-notes-epic-21.md) -- Risk Retirement (custom roles, wildcard RBAC, SMTP delivery, Flex layout library)
