# Epic 11 — Module System

> Pluggable architecture for extending the platform with code-delivered (FastAPI microservice) and nocode (user-designed) modules.

---

## Feature 11.1 — Module Registry and Activation `[DONE]`

### Story 11.1.1 — Module Registration `[DONE]`

#### Backend
*As an API, I want modules to self-register by posting a manifest, so that the platform discovers and catalogs available extensions.*
- `POST /api/v1/modules/register` accepts `manifest.json`: `{name, display_name, version, module_type, category, api_prefix, permissions[], menu_items[], routes[], event_subscriptions[], dependencies[]}`
- Manifest validated against JSON schema; structured errors returned on violation
- Registration is idempotent: re-posting the same `name` + `version` updates the existing record
- `status` set to `"available"` after successful registration

#### Frontend
*As a module developer, I want to see my module appear in the platform's module catalog immediately after registration, with its metadata, version, and status, so that I can verify the registration succeeded.*
- Route: `#/modules` → `nocode-modules.html` + `nocode-modules.js`
- Layout: FlexStack(direction=vertical) > page-header, modules-grid
  - page-header: FlexToolbar — "Modules" title | "Register Module" FlexButton(primary) [superadmin only]
  - modules-grid: FlexGrid(columns=auto, gap=md) — one FlexCard per registered module

- `ModuleCard` FlexCard:
  - content: module icon | name | FlexBadge(version) | category FlexBadge(chip) | type label (Code / NoCode) | status FlexBadge (Available / Active / Deprecated)
  - footer: action buttons (see Story 11.1.2)

- `RegisterModal` FlexModal(size=md) triggered by "Register Module":
  - body: JSON FlexTextarea for pasting `manifest.json` | "Validate" FlexButton(ghost)
  - inline validation result: success FlexAlert(type=success) "Valid manifest" or error list per field
  - footer: Cancel | "Register" FlexButton(primary, disabled until validation passes)

- Interactions:
  - click "Register Module": opens RegisterModal
  - click "Validate": POST /modules/validate with manifest JSON → inline validation result shown; Register button enables on success
  - click "Register": POST /modules/register → modal closes; new ModuleCard appears in grid with FlexBadge(color=info) "New"

- States:
  - loading: modules-grid shows skeleton cards while GET /modules resolves
  - empty: "No modules registered yet" + "Register Module" FlexButton(primary) [superadmin only]
  - error: FlexAlert(type=error) "Could not load modules. Retry?"

---

### Story 11.1.2 — Per-Tenant Module Activation `[DONE]`

#### Backend
*As an API, I want to activate a registered module for a specific tenant, so that tenant users gain access to the module's features.*
- `POST /api/v1/modules/{id}/activate` with `{tenant_id}` (or derived from JWT)
- On activation: module menus merged into the core menu tree; module routes registered in the dynamic router; module permissions available in RBAC
- `company.created` event triggers module initialization hooks defined in the manifest

#### Frontend
*As a tenant administrator on the modules page, I want to activate a module with a single "Activate" button click, and then see the module's menu items appear in the navigation sidebar immediately, so that enabling new features requires no technical steps.*
- Route: `#/modules` → modules page (see Story 11.1.1); activation controls are within each ModuleCard footer

- `ModuleCard` footer — per status:
  - available: "Activate" FlexButton(primary)
  - active: "Deactivate" FlexButton(ghost, danger)
  - dependency-unmet: "Activate" FlexButton(primary, disabled) + FlexTooltip "Requires: [Dependency Name]"

- `DeactivateModal` FlexModal(size=sm) triggered by "Deactivate":
  - body: "Deactivating [Module Name] will remove its menu items and features for all users. Continue?"
  - footer: Cancel | "Deactivate" FlexButton(variant=danger)

- Interactions:
  - click "Activate" (deps met): POST /modules/{id}/activate → button shows spinner → on success button changes to "Deactivate" FlexButton(ghost, danger); module menu items animate into sidebar nav
  - click "Deactivate": opens DeactivateModal → confirm: POST /modules/{id}/deactivate → card status updates to Available; menu items removed from sidebar
  - hover disabled "Activate" (deps unmet): FlexTooltip appears listing required dependencies

- States:
  - activating: "Activate" button shows spinner; card non-interactive during activation
  - active: card border highlight + FlexBadge(color=success) "Active" in header

---

### Story 11.1.3 — Module Dependency Management `[DONE]`

#### Backend
*As an API, I want module activation to be blocked if required dependencies are missing or incompatible, so that module integrity is maintained.*
- `ModuleDependency` records `module_id`, `depends_on_module_id`, `version_constraint` (semver range)
- Activation with unmet deps returns 409: `{missing: [{name, required_version, installed_version?}]}`
- Deactivating a module with active dependents blocked unless `force=true`

#### Frontend
*As a tenant administrator trying to activate a module that has unmet dependencies, I want to see a clear list of what I need to install first, with direct links to activate those modules, so that I can resolve the issue without raising a support ticket.*
- Route: `#/modules` → inline within the ModuleCard activation flow (no dedicated route); error state appears inside an activation FlexModal

- `ActivationModal` error view (replaces loading state on 409 response):
  - header: "Dependencies Required"
  - body: FlexStack(gap=sm) — one row per missing dependency: name | required version FlexBadge | "View in Catalog" link
  - footer: Cancel | "Activate Prerequisites First" FlexButton(primary)

- Interactions:
  - POST /modules/{id}/activate → 409 response: activation FlexModal transitions from loading spinner to "Dependencies Required" error view
  - click "View in Catalog" link: navigates to `#/modules` catalog filtered to that module
  - click "Activate Prerequisites First": navigates to `#/modules` with missing module names as filter; modal closes

---

## Feature 11.2 — Module Marketplace UI `[PLANNED]`

### Story 11.2.1 — Module Catalog Browse `[PLANNED]`

#### Backend
*As an API, I want a browsable module catalog endpoint with search and filter capabilities, so that tenants can discover available modules.*
- `GET /api/v1/modules?category=finance&module_type=code&is_installed=false&search=payroll` returns filtered module list
- Module record includes: `name`, `display_name`, `description`, `version`, `author`, `category`, `screenshots`, `permissions_required`, `dependencies`

#### Frontend
*As a tenant administrator on the marketplace page, I want to browse modules in a grid with category filters and a search bar, and open a detailed view for any module before activating it, so that I can make an informed decision.*
- Route: `#/modules/marketplace` → `marketplace.html` + `marketplace-page.js`
- Layout: FlexSplitPane(initial-split=20%) > category-sidebar, main-area
  - category-sidebar: FlexStack(direction=vertical) — category filter tree (Finance / HR / CRM / Operations / etc.)
  - main-area: FlexStack(direction=vertical) > search-bar, modules-grid
    - search-bar: FlexInput(placeholder="Search modules…")
    - modules-grid: FlexGrid(columns=auto, gap=md) — one FlexCard per module

- `MarketplaceCard` FlexCard:
  - content: module icon | name | author | short description | version FlexBadge
  - footer: "Installed" FlexBadge(color=success) [if active] | "Activate" FlexButton(primary) [if not active, disabled + greyed when already installed]

- `ModuleDetailDrawer` FlexDrawer(position=right, size=md) triggered by clicking a card:
  - header: module icon + name + version
  - body: full description | feature list | screenshots carousel | permissions required list | dependencies list
  - footer: "Activate" FlexButton(primary) [or "Installed" FlexBadge if already active]

- Interactions:
  - click category in sidebar: GET /modules?category=X → modules-grid refreshes
  - type in search-bar: debounced 300 ms → GET /modules?search=term → modules-grid refreshes
  - click module card: opens ModuleDetailDrawer
  - click "Activate" (card or drawer footer): triggers activation flow (see Story 11.2.2)

- States:
  - loading: modules-grid shows skeleton cards
  - empty: "No modules found in this category"
  - no-search-results: "No modules match '[term]'"

---

### Story 11.2.2 — One-Click Module Activation from Marketplace `[PLANNED]`

#### Backend
*As an API, the same activation endpoint is used from the marketplace UI, so that no new backend code is needed.*
- `POST /api/v1/modules/{id}/activate` (reused from Story 11.1.2)

#### Frontend
*As a tenant administrator clicking "Activate" in the module detail drawer, I want to see a permissions summary before confirming, and have the module be fully usable immediately after I confirm, so that the activation is transparent and instant.*
- Route: `#/modules/marketplace` → inline within ModuleDetailDrawer (no separate route); confirmation replaces the drawer footer

- `ModuleDetailDrawer` confirmation step (appears after clicking "Activate"):
  - replaces drawer body with:
    - "This module will add the following permissions to your RBAC system:" + permissions list
    - "New menu items:" + menu items list
  - footer: "Cancel" link | "Confirm Activation" FlexButton(primary)

- Interactions:
  - click "Activate" (drawer footer): drawer body transitions to confirmation step
  - click "Cancel": drawer reverts to module detail view
  - click "Confirm Activation": POST /modules/{id}/activate → progress indicator shown in drawer body → on success drawer header updates to "✓ Activated"; sidebar nav updates live; toast "[Module Name] has been activated. New features are available in the navigation."

- States:
  - confirming: drawer body shows permissions + menu items summary; footer shows Confirm + Cancel
  - activating: drawer body shows progress indicator; footer hidden
  - activated: drawer header shows "✓ Activated" FlexBadge(color=success); "Activate" button replaced by "Installed" badge

---

## Feature 11.3 — NoCode Module Builder `[DONE]`

### Story 11.3.1 — User-Designed Module Creation `[DONE]`

#### Backend
*As an API, I want nocode modules to package entities, workflows, and dashboards, so that reusable configurations can be managed as units.*
- `POST /api/v1/nocode-modules` creates a `Module` record with `module_type = "nocode"`, `table_prefix`, `category`, `icon`
- Associated entities via `EntityDefinition.module_id = module.id`
- Publishing a nocode module makes it available for activation in other companies

#### Frontend
*As a tenant administrator on the NoCode modules page, I want to create a module, give it a name and icon, and then associate my existing entities and workflows with it, so that I can bundle related features into a deployable package.*
- Route (list): `#/nocode/modules` → `nocode-modules-list.html` + `nocode-modules-list-page.js`
- Route (detail): `#/nocode/modules/{id}` → `nocode-module-detail.html` + `nocode-module-detail-page.js`
- Layout (list): FlexStack(direction=vertical) > page-header, modules-list
  - page-header: FlexToolbar — "NoCode Modules" title | "New Module" FlexButton(primary)
  - modules-list: FlexDataGrid — columns: Name, Status FlexBadge, Entity Count, Created At

- `NewModuleModal` FlexModal(size=md) triggered by "New Module":
  - fields: Name (FlexInput, required) | Description (FlexTextarea) | Table Prefix (FlexInput, auto-derived from name, editable) | Category (FlexSelect) | Icon picker | Color picker
  - footer: Cancel | "Create Module" FlexButton(primary)

- Layout (detail): FlexStack(direction=vertical) > page-header, content-tabs
  - page-header: FlexToolbar — FlexBreadcrumb | module name | status FlexBadge
  - content-tabs: FlexTabs — Entities | Workflows | Dashboards | Settings

- Per tab body: FlexDataGrid of associated items + "Add Existing" FlexButton(ghost) at top
- Settings tab: module metadata form + "Publish Module" FlexButton(primary)

- Interactions:
  - click "New Module": opens NewModuleModal; Table Prefix auto-derives from Name as user types
  - click "Create Module": POST /nocode-modules → modal closes; redirect to `#/nocode/modules/{id}`
  - click "Add Existing" (any tab): FlexModal(size=sm) search-and-select dialog → select items → POST /nocode-modules/{id}/entities (or /workflows, /dashboards) → item appears in tab grid
  - click "Publish Module" (Settings tab): PATCH /nocode-modules/{id} {status: published} → status FlexBadge updates

- States:
  - loading (list): skeleton rows while GET /nocode-modules resolves
  - empty (list): "No modules yet" + "New Module" FlexButton(primary)
  - tab-empty: "No [entities/workflows/dashboards] added yet" + "Add Existing" FlexButton(primary)

---

### Story 11.3.2 — Module Template Export and Import `[DONE]`

#### Backend
*As an API, I want to export a nocode module as a ZIP package and import it into another tenant, so that configurations can be distributed without manual re-creation.*
- `POST /api/v1/nocode-modules/{id}/export` generates a ZIP: `entities.json`, `fields.json`, `workflows.json`, `dashboards.json`
- `POST /api/v1/nocode-modules/import` accepts a ZIP; creates/updates definitions under the target tenant
- Import is idempotent; returns `{created: N, updated: M, skipped: K}`

#### Frontend
*As a platform superadmin, I want an "Export" button on a module that downloads a ZIP file, and an "Import Module" button that walks me through uploading and previewing the package before committing, so that module distribution is self-service.*
- Route: `#/nocode/modules/{id}` → Settings tab; export and import controls in the Settings tab toolbar
- Layout addition (Settings tab): FlexToolbar — (metadata form) | "Export Module" FlexButton(ghost) | "Import Module" FlexButton(ghost) [superadmin only]

- `ImportModal` FlexModal(size=lg) triggered by "Import Module":
  - FlexStepper(steps=3):
    - Step 1 "Upload": FlexFileUpload (ZIP only) — drop or select file
    - Step 2 "Preview": FlexDataGrid — item name | type | action FlexBadge (Create / Update / Skip); import errors shown per row with reason text
    - Step 3 "Target": Tenant (FlexSelect) + Company (FlexSelect) — superadmin selects import destination
  - footer: Cancel (any step) | Next / "Import" FlexButton(primary)
  - results view (after import): "X items created, Y updated, Z skipped" summary + per-item error list for failures

- Interactions:
  - click "Export Module": POST /nocode-modules/{id}/export → file download starts immediately as `{module_name}_v{version}.zip`
  - click "Import Module": opens ImportModal at Step 1
  - drop/select ZIP (Step 1): file parsed; Next button enables
  - click Next (Step 1 → Step 2): POST /nocode-modules/import/preview → preview grid populates with create/update/skip tags
  - click "Import" (Step 3): POST /nocode-modules/import → FlexProgress during import → results summary shown

- States:
  - previewing: Step 2 grid shows skeleton while preview call resolves
  - importing: "Import" button shows spinner; stepper disabled
  - import-complete: results summary shown in modal; Close FlexButton replaces Import
