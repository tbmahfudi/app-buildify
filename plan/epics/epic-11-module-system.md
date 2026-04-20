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
- Route: `#/modules` renders `nocode-modules.html` + `nocode-modules.js`
- Module catalog shows all registered modules as cards: icon, name, version badge, category chip, type (Code/NoCode), status badge (Available / Active / Deprecated)
- "Register Module" button (superadmin only) opens a modal with a JSON textarea for pasting `manifest.json` + a "Validate" button that checks the schema before submission
- After registration: new module card appears in the catalog with a "New" badge

---

### Story 11.1.2 — Per-Tenant Module Activation `[DONE]`

#### Backend
*As an API, I want to activate a registered module for a specific tenant, so that tenant users gain access to the module's features.*
- `POST /api/v1/modules/{id}/activate` with `{tenant_id}` (or derived from JWT)
- On activation: module menus merged into the core menu tree; module routes registered in the dynamic router; module permissions available in RBAC
- `company.created` event triggers module initialization hooks defined in the manifest

#### Frontend
*As a tenant administrator on the modules page, I want to activate a module with a single "Activate" button click, and then see the module's menu items appear in the navigation sidebar immediately, so that enabling new features requires no technical steps.*
- Module catalog card has an "Activate" button for available modules and a "Deactivate" button for active ones
- Clicking "Activate": spinner on the button; on success the button changes to "Active" (green) and the module's menu items animate into the sidebar navigation
- Clicking "Deactivate": confirmation modal "Deactivating [Module Name] will remove its menu items and features for all users. Continue?"
- If the module has dependencies not met: "Activate" button disabled with a tooltip "Requires: [Dependency Name]"

---

### Story 11.1.3 — Module Dependency Management `[DONE]`

#### Backend
*As an API, I want module activation to be blocked if required dependencies are missing or incompatible, so that module integrity is maintained.*
- `ModuleDependency` records `module_id`, `depends_on_module_id`, `version_constraint` (semver range)
- Activation with unmet deps returns 409: `{missing: [{name, required_version, installed_version?}]}`
- Deactivating a module with active dependents blocked unless `force=true`

#### Frontend
*As a tenant administrator trying to activate a module that has unmet dependencies, I want to see a clear list of what I need to install first, with direct links to activate those modules, so that I can resolve the issue without raising a support ticket.*
- When the 409 response is received: the modal changes from a loading state to a "Dependencies Required" error view
- Error view lists each missing dependency with: name, required version, a "View in Catalog" link
- "Activate Prerequisites First" CTA button navigates to the catalog filtered to the missing modules

---

## Feature 11.2 — Module Marketplace UI `[PLANNED]`

### Story 11.2.1 — Module Catalog Browse `[PLANNED]`

#### Backend
*As an API, I want a browsable module catalog endpoint with search and filter capabilities, so that tenants can discover available modules.*
- `GET /api/v1/modules?category=finance&module_type=code&is_installed=false&search=payroll` returns filtered module list
- Module record includes: `name`, `display_name`, `description`, `version`, `author`, `category`, `screenshots`, `permissions_required`, `dependencies`

#### Frontend
*As a tenant administrator on the marketplace page, I want to browse modules in a grid with category filters and a search bar, and open a detailed view for any module before activating it, so that I can make an informed decision.*
- Route: `#/modules/marketplace` (separate view from the current modules management page)
- Page layout: left sidebar = category filter tree (Finance, HR, CRM, Operations, etc.); main area = module grid
- Search bar at the top filters modules by name and description
- Module card: icon, name, author, short description, version, "Installed" or "Activate" badge
- Clicking a card opens a `FlexDrawer` detail panel: full description, feature list, screenshots carousel, permissions required, dependencies, "Activate" button
- "Installed" badge and greyed-out "Activate" button for already-active modules

---

### Story 11.2.2 — One-Click Module Activation from Marketplace `[PLANNED]`

#### Backend
*As an API, the same activation endpoint is used from the marketplace UI, so that no new backend code is needed.*
- `POST /api/v1/modules/{id}/activate` (reused from Story 11.1.2)

#### Frontend
*As a tenant administrator clicking "Activate" in the module detail drawer, I want to see a permissions summary before confirming, and have the module be fully usable immediately after I confirm, so that the activation is transparent and instant.*
- Clicking "Activate" in the detail drawer opens a confirmation step within the same drawer:
  - "This module will add the following permissions to your RBAC system: [list]"
  - "New menu items: [list]"
  - "Confirm Activation" button (green) + "Cancel" link
- After confirmation: progress indicator; on success the drawer header shows "✓ Activated"; sidebar nav updates live
- Toast: "[Module Name] has been activated. New features are available in the navigation."

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
- Route: `#/nocode/modules` renders the nocode modules list with status and entity count
- "New Module" button opens a `FlexModal` wizard: Name, Description, Table Prefix (auto-derived, editable), Category, Icon picker, Color picker
- After creation: module detail page `#/nocode/modules/{id}` shows tabs: "Entities", "Workflows", "Dashboards", "Settings"
- Each tab has an "Add Existing" button that opens a search-and-select dialog for associating items with the module
- "Publish Module" button in the Settings tab transitions `status → published`

---

### Story 11.3.2 — Module Template Export and Import `[DONE]`

#### Backend
*As an API, I want to export a nocode module as a ZIP package and import it into another tenant, so that configurations can be distributed without manual re-creation.*
- `POST /api/v1/nocode-modules/{id}/export` generates a ZIP: `entities.json`, `fields.json`, `workflows.json`, `dashboards.json`
- `POST /api/v1/nocode-modules/import` accepts a ZIP; creates/updates definitions under the target tenant
- Import is idempotent; returns `{created: N, updated: M, skipped: K}`

#### Frontend
*As a platform superadmin, I want an "Export" button on a module that downloads a ZIP file, and an "Import Module" button that walks me through uploading and previewing the package before committing, so that module distribution is self-service.*
- Module detail Settings tab has "Export Module" button → immediately downloads `{module_name}_v{version}.zip`
- "Import Module" button opens a `FlexModal`:
  - Step 1: File upload (`FlexFileUpload`) for the ZIP
  - Step 2: Preview — shows what will be created/updated: entity list, workflow list, dashboard list with create/update/skip tags
  - Step 3: Tenant/Company selector (for superadmin importing to a specific tenant)
  - "Import" button runs the import; results shown: "15 items created, 3 updated, 1 skipped"
- Import errors shown per-item with the reason (e.g. "Entity 'sales_order' conflicts with existing entity")
