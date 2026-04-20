# Epic 4 — RBAC & Permissions

> Fine-grained Role-Based Access Control with `resource:action:scope` permission model, wildcard support, and enforcement at API and UI layers.

---

## Feature 4.1 — Role Management `[DONE]`

### Story 4.1.1 — System and Custom Role Definitions `[DONE]`

#### Backend
*As an API, I want to create, read, update, and delete tenant-scoped roles, so that administrators can model their organization's actual access structure.*
- `POST /api/v1/rbac/roles` creates a role with `name`, `description`, `is_system` (always false for tenant-created)
- System roles (`SuperAdmin`, `TenantAdmin`, `CompanyAdmin`, `Manager`, `User`) seeded and `is_system = true`; cannot be deleted or modified
- `GET /api/v1/rbac/roles` returns all roles for the current tenant including system roles
- `DELETE /api/v1/rbac/roles/{id}` blocked if any users or groups have this role assigned (returns 409 with dependent count)

#### Frontend
*As a tenant administrator on the RBAC page, I want to see all roles in a list, create new ones, and configure their permissions in a matrix view, so that access control is self-service.*
- Route: `#/rbac` renders `frontend/assets/templates/rbac.html` + `rbac-page.js`
- Left panel: role list with `FlexCard` items — system roles in a "System Roles" section (read-only badge), tenant roles below with Edit/Delete icons
- "New Role" button opens a `FlexModal` with Name and Description fields; optional "Copy permissions from" select to clone an existing role
- Deleting a role with assignments shows a warning: "This role is assigned to X users and Y groups. Remove it from all assignments first."
- System roles: edit icon disabled; hovering shows tooltip "System roles cannot be modified"

---

### Story 4.1.2 — Permission Assignment to Roles `[DONE]`

#### Backend
*As an API, I want to assign and remove permissions from roles, so that role access can be precisely defined.*
- `POST /api/v1/rbac/roles/{id}/permissions` accepts `{permission_ids: []}` and creates `RolePermission` records
- `DELETE /api/v1/rbac/roles/{id}/permissions/{perm_id}` removes a single permission
- `GET /api/v1/rbac/permissions` returns the full permission catalog (resource × action × scope)

#### Frontend
*As a tenant administrator editing a role, I want a permission matrix where rows are resources and columns are actions, and I can toggle individual cells, so that configuring permissions is intuitive and visual.*
- Role detail panel (right side of `#/rbac` when a role is selected) shows a permission matrix
- Rows: resource names (users, entities, reports, dashboards, etc.)
- Columns: actions (create, read, update, delete, export, approve)
- Cells: checkbox toggles; checked = permission granted
- Scope selector at the top of the panel: `platform / tenant / company / branch` — all displayed permissions filtered to the selected scope
- "Select All" row button grants all actions for a resource; "Select All" column header grants one action across all resources
- Auto-save on each toggle (no explicit Save button); a small "Saved" checkmark flashes after each successful API call

---

### Story 4.1.3 — User Role Assignment `[DONE]`

#### Backend
*As an API, I want to assign roles directly to individual users, so that one-off access grants are possible without creating a group.*
- `POST /api/v1/rbac/users/{id}/roles` accepts `{role_ids: []}` and creates `UserRole` records
- `DELETE /api/v1/rbac/users/{id}/roles/{role_id}` removes a direct role assignment
- Effective permissions = union of direct role permissions + all group role permissions

#### Frontend
*As a tenant administrator on a user's detail page, I want to assign and remove roles for that specific user, with a clear display of which roles come from groups vs. direct assignment, so that I understand their full access.*
- User detail page `#/users/{id}` has a "Roles & Permissions" tab
- "Direct Roles" section: shows roles assigned directly to the user with a remove (×) icon each; "Add Role" opens a role search select
- "Group Roles" section: read-only list of roles inherited through group membership; each item shows which group it comes from (e.g. "Manager role via Sales Team group")
- "Effective Permissions" expandable section: full flattened list of all permissions the user has, showing source (direct/group name)
- Permissions searchable with a filter input to find a specific permission code quickly

---

## Feature 4.2 — Permission Engine `[DONE]`

### Story 4.2.1 — Permission Format and Wildcard Matching `[DONE]`

#### Backend
*As an API, I want a permission evaluation engine that supports wildcards and scope hierarchy, so that broad and narrow access can be expressed cleanly.*
- Permission format: `resource:action:scope` (e.g. `invoices:create:company`)
- `require_permission(code)` FastAPI dependency evaluates wildcard matches: `*:*:platform` passes all checks
- `has_permission(user_permissions, required_code)` utility: each segment checked for literal match or `*`
- Permission resolution completes within 5 ms for users with up to 200 permissions

#### Frontend
*As a frontend developer building a new page, I want a simple `hasPermission()` call that I can wrap any button or menu item with, so that the UI automatically adapts to each user's access level without custom logic per component.*
- `auth-service.js` exposes `hasPermission(code)` — checks the in-memory permission set loaded at login
- Usage pattern: `if (!hasPermission('reports:export:company')) button.disabled = true`
- Permission set refreshed automatically when tokens are renewed (in case role changes take effect mid-session)
- Dev-mode: `?debug_perms=1` URL flag renders a floating panel showing the current user's full permission list — useful for QA

---

### Story 4.2.2 — Scope Hierarchy Enforcement `[DONE]`

#### Backend
*As an API, I want data queries automatically filtered to the requesting user's organizational scope, so that cross-scope data leakage is impossible.*
- `_get_org_context(user)` returns a WHERE clause fragment: `{tenant_id, company_id?, branch_id?, department_id?}` based on user's highest authorized scope
- All list endpoints apply this context via SQLAlchemy `filter()` before executing the query
- Scope context derived from the JWT payload only — never from query parameters

#### Frontend
*As a company-level user, I want the platform to automatically show only my company's data across all pages, so that I never accidentally see another subsidiary's records.*
- No specific UI needed — scope enforcement is transparent to the user
- Admin pages show a "Scope: Company — [Company Name]" chip in the page header, so admins know which scope they're operating in
- Superadmin and tenant admin pages show a scope dropdown allowing them to view data from other companies for admin tasks

---

### Story 4.2.3 — Frontend RBAC Filtering `[DONE]`

#### Backend
*As an API, I want the user's full permission list returned in the login response, so that the frontend can cache it and make local permission checks without extra API calls.*
- `POST /auth/login` response includes `user.permissions: [string]` — the complete list of permission codes for the authenticated user
- Superadmin flag (`is_superuser: true`) in the response causes `hasPermission()` to always return `true`

#### Frontend
*As a user with limited permissions, I want the navigation menu to show only the sections I have access to, and action buttons I'm not allowed to use to be hidden — not just disabled, so that the UI feels clean and appropriate for my role.*
- `app.js` `renderMenu()` calls `hasPermission()` for each menu item's `required_permission` and skips rendering items that fail the check
- Page-level: route guards in `router.js` redirect to a 403 page if the user navigates directly to a route they lack permission for
- Component-level: action buttons (Create, Edit, Delete, Export) wrapped in a `showIf(hasPermission(...))` utility — elements not rendered in DOM, not just CSS-hidden
- 403 page: friendly message "You don't have permission to access this section. Contact your administrator if you think this is a mistake."

---

### Story 4.2.4 — Per-Entity Permission Enforcement `[OPEN]`

#### Backend
*As an API, I want entity-level permission rules stored on the entity definition to override global RBAC for that entity's data, so that custom data has fine-grained access control.*
- `EntityDefinition.permissions` JSONB: `{role_name: [actions]}` e.g. `{"Manager": ["read", "create"], "User": ["read"]}`
- `DynamicEntityService` reads `entity.permissions` before any CRUD operation; if the user's role is not listed for the action → 403
- When `permissions` is `null`, global RBAC is the sole check

#### Frontend
*As a tenant administrator designing an entity, I want to configure which roles can perform which actions on that entity's data, so that sensitive custom tables are protected beyond the global RBAC settings.*
- Entity designer page `#/nocode/data-model` → entity edit form → "Access Control" tab
- Permission matrix: rows = roles (fetched from `GET /rbac/roles`), columns = CRUD actions
- Pre-populated from the entity's current `permissions` JSONB
- "Inherit from global RBAC" toggle: when ON, the `permissions` field is `null` and the matrix is shown as read-only grey state
- When OFF: matrix becomes editable; administrator configures per-role access
- Save updates the `EntityDefinition.permissions` JSONB via `PUT /data-model/entities/{id}`
