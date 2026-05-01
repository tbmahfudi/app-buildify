# Epic 4 — RBAC & Permissions

> Fine-grained Role-Based Access Control with `resource:action:scope` permission model, wildcard support, and enforcement at API and UI layers.

---

## Feature 4.1 — Role Management `[IN-PROGRESS]`

### Story 4.1.1 — System and Custom Role Definitions `[IN-PROGRESS]`

#### Backend
*As an API, I want to create, read, update, and delete tenant-scoped roles, so that administrators can model their organization's actual access structure.*
- `POST /api/v1/rbac/roles` creates a role with `name`, `description`, `is_system` (always false for tenant-created)
- System roles (`SuperAdmin`, `TenantAdmin`, `CompanyAdmin`, `Manager`, `User`) seeded and `is_system = true`; cannot be deleted or modified
- `GET /api/v1/rbac/roles` returns all roles for the current tenant including system roles
- `DELETE /api/v1/rbac/roles/{id}` blocked if any users or groups have this role assigned (returns 409 with dependent count)

#### Frontend
*As a tenant administrator on the RBAC page, I want to see all roles in a list, create new ones, and configure their permissions in a matrix view, so that access control is self-service.*
- Route: `#/rbac` → `rbac.html` + `rbac-page.js`
- Layout: FlexSplitPane(initial-split=30%) > roles-panel, detail-panel
  - roles-panel: FlexStack(direction=vertical) > roles-header, system-roles-section, tenant-roles-section
    - roles-header: FlexToolbar — "Roles" title | "New Role" FlexButton(primary)
    - system-roles-section: FlexStack — section label "System Roles" | FlexCard per system role (read-only FlexBadge, edit icon disabled)
    - tenant-roles-section: FlexStack — FlexCard per custom role (Edit | Delete icons)
  - detail-panel: permission matrix (see Story 4.1.2)

- FlexModal(size=sm) — "New Role" form, triggered by toolbar button
  - fields: Name (FlexInput, required) | Description (FlexTextarea) | Copy permissions from (FlexSelect, optional)
  - footer: Cancel | Create Role (primary)

- Interactions:
  - click "New Role": opens FlexModal(size=sm)
  - click role card: loads permission matrix in detail-panel for that role
  - hover disabled edit icon (system role): FlexTooltip "System roles cannot be modified"
  - click Delete on a role with assignments: FlexAlert(type=warning) inline "This role is assigned to X users and Y groups. Remove it from all assignments first." — delete blocked

- States:
  - loading: role cards show skeleton while GET /rbac/roles resolves
  - empty (tenant roles): "No custom roles yet" + "New Role" FlexButton(primary)
  - error: FlexAlert(type=error) "Could not load roles. Retry?"

---

### Story 4.1.2 — Permission Assignment to Roles `[DONE]`

#### Backend
*As an API, I want to assign and remove permissions from roles, so that role access can be precisely defined.*
- `POST /api/v1/rbac/roles/{id}/permissions` accepts `{permission_ids: []}` and creates `RolePermission` records
- `DELETE /api/v1/rbac/roles/{id}/permissions/{perm_id}` removes a single permission
- `GET /api/v1/rbac/permissions` returns the full permission catalog (resource × action × scope)

#### Frontend
*As a tenant administrator editing a role, I want a permission matrix where rows are resources and columns are actions, and I can toggle individual cells, so that configuring permissions is intuitive and visual.*
- Route: `#/rbac` → detail-panel of the split-pane (see Story 4.1.1)

- Permission matrix panel — shown when a role is selected
  - scope selector (FlexSelect): platform | tenant | company | branch — filters matrix to selected scope
  - matrix table: rows = resource names (users, entities, reports, dashboards…) | columns = actions (create, read, update, delete, export, approve)
  - each cell: FlexCheckbox toggle; checked = permission granted
  - row header: "Select All" button grants all actions for that resource
  - column header: "Select All" button grants that action across all resources

- Interactions:
  - change scope selector: matrix re-filters to show only permissions for selected scope
  - toggle a matrix cell: POST /rbac/roles/{id}/permissions or DELETE /rbac/roles/{id}/permissions/{perm_id} (auto-save, no submit button) → small "Saved ✓" indicator flashes beside the cell
  - click row "Select All": grants all actions for that resource in one call
  - click column "Select All": grants that action for all resources in one call

- States:
  - loading: matrix shows skeleton while GET /rbac/permissions resolves
  - saving (per-cell): spinner micro-icon beside toggled cell; other cells remain interactive
  - no-role-selected: detail-panel shows empty state "Select a role to configure its permissions"

---

### Story 4.1.3 — User Role Assignment `[DONE]`

#### Backend
*As an API, I want to assign roles directly to individual users, so that one-off access grants are possible without creating a group.*
- `POST /api/v1/rbac/users/{id}/roles` accepts `{role_ids: []}` and creates `UserRole` records
- `DELETE /api/v1/rbac/users/{id}/roles/{role_id}` removes a direct role assignment
- Effective permissions = union of direct role permissions + all group role permissions

#### Frontend
*As a tenant administrator on a user's detail page, I want to assign and remove roles for that specific user, with a clear display of which roles come from groups vs. direct assignment, so that I understand their full access.*
- Route: `#/users/{id}` → user detail page "Roles & Permissions" tab

- FlexDrawer content (within user detail FlexTabs — Roles & Permissions tab):
  - Direct Roles section: FlexBadge per directly-assigned role + × remove icon | "Add Role" FlexButton (opens role FlexSelect)
  - Group Roles section: read-only list — role name | "via [Group Name]" FlexBadge per inherited role
  - Effective Permissions section: FlexAccordion (collapsed by default) — full flattened permission list; source shown per entry (direct / group name) | filter FlexInput at top

- Interactions:
  - click × on a direct role: DELETE /rbac/users/{id}/roles/{role_id} → badge removed
  - click "Add Role": opens role FlexSelect dropdown; select to POST /rbac/users/{id}/roles → new badge appears
  - type in Effective Permissions filter: client-side filters permission list by code string
  - click "Effective Permissions" accordion header: expands/collapses the full permission list

- States:
  - loading: sections show skeleton while GET /rbac/users/{id}/roles resolves
  - no-direct-roles: "No direct roles assigned" + "Add Role" FlexButton

---

## Feature 4.2 — Permission Engine `[IN-PROGRESS]`

### Story 4.2.1 — Permission Format and Wildcard Matching `[IN-PROGRESS]`

#### Backend
*As an API, I want a permission evaluation engine that supports wildcards and scope hierarchy, so that broad and narrow access can be expressed cleanly.*
- Permission format: `resource:action:scope` (e.g. `invoices:create:company`)
- `require_permission(code)` FastAPI dependency evaluates wildcard matches: `*:*:platform` passes all checks
- `has_permission(user_permissions, required_code)` utility: each segment checked for literal match or `*`
- Permission resolution completes within 5 ms for users with up to 200 permissions

#### Frontend
*As a frontend developer building a new page, I want a simple `hasPermission()` call that I can wrap any button or menu item with, so that the UI automatically adapts to each user's access level without custom logic per component.*
- No dedicated route — `hasPermission()` is a shared utility in `auth-service.js`, used everywhere

- Interactions:
  - login / token refresh: full permission list loaded into in-memory set from login response `user.permissions[]`
  - any `hasPermission(code)` call: checks in-memory set; superadmin flag (`is_superuser: true`) always returns true
  - token renewal: permission set refreshed in case role changes took effect mid-session
  - append `?debug_perms=1` to any URL: floating dev overlay appears showing the current user's full permission list (QA tool)

---

### Story 4.2.2 — Scope Hierarchy Enforcement `[DONE]`

#### Backend
*As an API, I want data queries automatically filtered to the requesting user's organizational scope, so that cross-scope data leakage is impossible.*
- `_get_org_context(user)` returns a WHERE clause fragment: `{tenant_id, company_id?, branch_id?, department_id?}` based on user's highest authorized scope
- All list endpoints apply this context via SQLAlchemy `filter()` before executing the query
- Scope context derived from the JWT payload only — never from query parameters

#### Frontend
*As a company-level user, I want the platform to automatically show only my company's data across all pages, so that I never accidentally see another subsidiary's records.*
- No dedicated route — scope context is transparent; enforcement is entirely server-side

- Interactions:
  - all page loads: data returned is already scope-filtered; no user action required
  - admin pages only: "Scope: Company — [Company Name]" FlexBadge shown in the page header so admins know which scope they're viewing
  - superadmin / tenant admin: scope FlexSelect in the page header allows switching to view another company's data for admin tasks → page re-fetches with selected scope context

---

### Story 4.2.3 — Frontend RBAC Filtering `[DONE]`

#### Backend
*As an API, I want the user's full permission list returned in the login response, so that the frontend can cache it and make local permission checks without extra API calls.*
- `POST /auth/login` response includes `user.permissions: [string]` — the complete list of permission codes for the authenticated user
- Superadmin flag (`is_superuser: true`) in the response causes `hasPermission()` to always return `true`

#### Frontend
*As a user with limited permissions, I want the navigation menu to show only the sections I have access to, and action buttons I'm not allowed to use to be hidden — not just disabled, so that the UI feels clean and appropriate for my role.*
- No dedicated route — permission filtering is applied globally across all routes and components

- Interactions:
  - app load / menu render: `renderMenu()` calls `hasPermission()` per menu item; items that fail are not rendered in the DOM (not CSS-hidden)
  - navigate directly to a restricted route: `router.js` guard intercepts → redirects to 403 page
  - any Create / Edit / Delete / Export button: wrapped in `showIf(hasPermission(...))` — element absent from DOM when permission missing; no disabled state shown

- States:
  - 403 page: FlexSection(centered) — "You don't have permission to access this section. Contact your administrator if you think this is a mistake." + "Go to Dashboard" FlexButton

---

### Story 4.2.4 — Per-Entity Permission Enforcement `[OPEN]`

#### Backend
*As an API, I want entity-level permission rules stored on the entity definition to override global RBAC for that entity's data, so that custom data has fine-grained access control.*
- `EntityDefinition.permissions` JSONB: `{role_name: [actions]}` e.g. `{"Manager": ["read", "create"], "User": ["read"]}`
- `DynamicEntityService` reads `entity.permissions` before any CRUD operation; if the user's role is not listed for the action → 403
- When `permissions` is `null`, global RBAC is the sole check

#### Frontend
*As a tenant administrator designing an entity, I want to configure which roles can perform which actions on that entity's data, so that sensitive custom tables are protected beyond the global RBAC settings.*
- Route: `#/nocode/data-model` → entity edit form → "Access Control" tab

- Permission matrix panel (within entity edit form):
  - "Inherit from global RBAC" FlexCheckbox (toggle) at the top
  - matrix table: rows = roles (from GET /rbac/roles) | columns = CRUD actions (create, read, update, delete)
  - pre-populated from entity's current `permissions` JSONB
  - footer: "Save Access Control" FlexButton(primary)

- Interactions:
  - toggle "Inherit from global RBAC" ON: `permissions` set to null; matrix shown in read-only grey state
  - toggle "Inherit from global RBAC" OFF: matrix becomes editable; all cells unlocked
  - toggle a matrix cell: updates local state only (no auto-save)
  - click "Save Access Control": PUT /data-model/entities/{id} with updated `permissions` JSONB → success toast | error FlexAlert(type=error)

- States:
  - inherit-mode: matrix cells greyed out and non-interactive; toggle clearly ON
  - custom-mode: matrix cells interactive; toggle OFF
  - loading: matrix shows skeleton while GET /rbac/roles resolves
