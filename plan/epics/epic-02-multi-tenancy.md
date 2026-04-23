# Epic 2 — Multi-Tenancy & Organization Management

> Fully isolated multi-tenant architecture with a four-level org hierarchy: Tenant → Company → Branch → Department.

---

## Feature 2.1 — Tenant Lifecycle Management `[DONE]`

### Story 2.1.1 — Tenant Provisioning `[DONE]`

#### Backend
*As an API, I want to create isolated tenant organizations with their own data scope, so that multiple clients share infrastructure without data leakage.*
- `POST /api/v1/org/tenants` creates a `Tenant` record; seeds default roles, security policy, and notification config
- `tenant_id` FK enforced on all tenant-scoped tables via SQLAlchemy column defaults
- `tenant.created` event published to the event bus for module initialization hooks
- Only superadmin (`is_superuser = true`) can call this endpoint; returns 403 otherwise

#### Frontend
*As a superadmin on the tenants management page, I want to fill out a form to create a new tenant with its name, slug, and initial admin credentials, so that I can onboard a new client in under a minute.*
- Route: `#/tenants` → `tenants.html` + `tenants.js`
- Layout: FlexStack(direction=vertical) > page-header, content-area
  - page-header: FlexToolbar — "Tenants" title | "New Tenant" FlexButton(primary)
  - content-area: FlexDataGrid

- FlexDataGrid(server-side) — tenant list via GET /org/tenants
  - columns: Name, Slug, Plan Tier (FlexBadge), Status (FlexBadge, Active/Suspended), User Count, Created Date, Actions
  - row action: Edit | Suspend/Activate | View Users

- FlexModal(size=md) — "New Tenant" form, triggered by toolbar button
  - fields: Tenant Name (FlexInput, required) | Slug (FlexInput, auto-derived from name, editable, live URL preview) | Domain (FlexInput) | Admin Email (FlexInput, type=email) | Admin Password (FlexInput, type=password)
  - footer: Cancel | Create Tenant (primary, spinner on submit)
  - on success: modal closes; new tenant row at top of grid

- Interactions:
  - click "New Tenant": opens FlexModal(size=md) new-tenant form
  - type in Tenant Name: Slug auto-derives (lowercase, hyphens); live tenant URL preview updates below slug field
  - submit form: POST /org/tenants → spinner → on success modal closes; new row at top of grid
  - click Edit on row: opens pre-populated FlexModal
  - click Suspend/Activate on row: opens confirm FlexModal (see Story 2.1.3)

- States:
  - loading: FlexDataGrid shows skeleton rows while GET /org/tenants resolves
  - empty: "No tenants yet" + "New Tenant" FlexButton(primary)
  - error: FlexAlert(type=error) "Could not load tenants. Retry?"

---

### Story 2.1.2 — Tenant Settings and Branding `[DONE]`

#### Backend
*As an API, I want to store and serve per-tenant branding configuration, so that the frontend can apply tenant-specific visual identity.*
- `GET /api/v1/settings/tenant` returns `{tenant_name, logo_url, primary_color, secondary_color, theme_config}`
- `PUT /api/v1/settings/tenant` updates branding; tenant admin scope only

#### Frontend
*As a tenant administrator on the branding settings page, I want to upload my logo and pick my brand colors, so that the platform shows my company's identity to all users.*
- Route: `#/settings/branding` → `settings.html` + `settings-page.js` (Branding section)
- Layout: FlexGrid(columns=2) > form-col, preview-col
  - form-col: FlexStack(direction=vertical) — Company Name (FlexInput) | Logo URL (FlexInput, type=url) | Primary Color (hex FlexInput + color swatch) | Secondary Color (hex FlexInput + color swatch) | "Save Branding" FlexButton(primary)
  - preview-col: FlexSection(sticky) — live sidebar snippet showing logo at 120×40px and primary color applied

- Interactions:
  - type in Logo URL: logo preview updates in real time at 120×40px
  - change Primary Color: preview sidebar snippet updates immediately (client-side CSS variable swap)
  - click "Save Branding": PUT /settings/tenant → on success applies CSS variables via theme-manager.js for all tenant users without page reload | error FlexAlert(type=error)

- States:
  - saving: "Save Branding" button shows spinner; all inputs disabled

---

### Story 2.1.3 — Tenant Suspension and Deactivation `[DONE]`

#### Backend
*As an API, I want to suspend a tenant so that all their users receive 403 responses, preserving data while blocking access.*
- `PATCH /api/v1/org/tenants/{id}` with `{is_active: false}` suspends the tenant
- `TenantMiddleware` checks `tenant.is_active` on every authenticated request; if false → 403 with `TENANT_SUSPENDED`

#### Frontend
*As a superadmin on the tenant detail page, I want to suspend or reactivate a tenant with a confirmation dialog, so that I don't accidentally lock out a client.*
- Route: `#/tenants` → operates on tenant list rows (and tenant detail page)

- FlexModal(size=sm) — suspend confirm, triggered by "Suspend" action on a row
  - body: "Are you sure you want to suspend [Tenant Name]? All users will lose access immediately."
  - fields: Reason (FlexTextarea, required)
  - footer: Cancel | Suspend Tenant (FlexButton, variant=danger)
  - on confirm: PATCH /org/tenants/{id} {is_active: false} → status chip updates to FlexBadge(color=danger) "Suspended"; row tinted red

- FlexModal(size=sm) — reactivate confirm, triggered by "Activate" action on a suspended row
  - body: "Restore access for [Tenant Name]?"
  - footer: Cancel | Activate Tenant (FlexButton, variant=primary)
  - on confirm: PATCH /org/tenants/{id} {is_active: true} → status chip updates to FlexBadge(color=success) "Active"; row tint removed

- Interactions:
  - click "Suspend" on tenant row: opens suspend FlexModal(size=sm) with required reason field
  - confirm suspend: PATCH /org/tenants/{id} → badge → "Suspended" (red); row background → red tint
  - click "Activate" on suspended row: opens reactivate FlexModal(size=sm) (no reason field)
  - confirm activate: PATCH /org/tenants/{id} → badge → "Active" (green); row tint removed
  - keyboard Escape: closes modal without action

---

## Feature 2.2 — Organization Hierarchy `[DONE]`

### Story 2.2.1 — Company Management `[DONE]`

#### Backend
*As an API, I want to create and manage company records within a tenant, so that each legal entity has its own data scope and settings.*
- `POST /api/v1/org/companies` creates a company with `name`, `code`, `currency`, `timezone`, `fiscal_year_start`
- `GET /api/v1/org/companies` returns all companies for the current tenant (superadmin can pass `?tenant_id=`)
- `company.created` event published for module initialization hooks (e.g. Financial module seeds default chart of accounts)

#### Frontend
*As a tenant administrator on the companies page, I want to create and manage companies using a drawer form, so that I can set up multiple legal entities without leaving the page.*
- Route: `#/companies` → `companies.html` + `companies-page.js`
- Layout: FlexStack(direction=vertical) > page-header, companies-grid
  - page-header: FlexToolbar — "Companies" title | "Add Company" FlexButton(primary)
  - companies-grid: FlexGrid(columns=3, gap=md) — FlexCard per company (name, code, currency, timezone, active user count, edit/delete icons)

- FlexDrawer(position=right, size=md) — company form, triggered by "Add Company" or card edit icon
  - fields: Name (FlexInput, required) | Code (FlexInput) | Country (FlexSelect) | Currency (FlexSelect, searchable) | Timezone (FlexSelect, searchable) | Fiscal Year Start (FlexSelect, month)
  - footer: Cancel | Save Company (primary, spinner on submit)
  - on edit: drawer pre-populated with existing values

- FlexModal(size=sm) — delete confirm, triggered by card delete icon
  - body: "Delete [Company Name]?"
  - on blocked (active users exist): body replaced with FlexAlert(type=warning) "Cannot delete — [N] active users. Remove users first."
  - footer: Cancel | Delete (FlexButton, variant=danger) [hidden when blocked]

- Interactions:
  - click "Add Company": opens empty FlexDrawer(position=right)
  - click edit icon on card: opens FlexDrawer pre-populated
  - click delete icon on card: opens delete confirm FlexModal (or blocked warning)
  - click company card (not icons): navigates to `#/companies/{id}` detail page

- States:
  - loading: FlexGrid shows 6 skeleton cards while GET /org/companies resolves
  - empty: "No companies yet" + "Add Company" FlexButton(primary)
  - error: FlexAlert(type=error) "Could not load companies. Retry?"

---

### Story 2.2.2 — Branch Management `[DONE]`

#### Backend
*As an API, I want to manage branches within a company, so that data can be scoped to physical or virtual office locations.*
- `POST /api/v1/org/branches` with `company_id`, `name`, `code`, `address`, optional `parent_branch_id`
- Branch hierarchy unlimited depth; `parent_branch_id` self-references `Branch.id`

#### Frontend
*As a company administrator on the branches page, I want to see branches in a tree structure and add child branches under parent ones, so that I can model our office hierarchy accurately.*
- Route: `#/branches` → `branches.html` + `branches-page.js`
- Layout: FlexStack(direction=vertical) > page-header, branch-tree
  - page-header: FlexToolbar — "Branches" title | "Add Branch" FlexButton(primary)
  - branch-tree: FlexSection — collapsible tree; root branches expand to reveal child branches

- FlexModal(size=sm) — branch form, triggered by "Add Branch" or "Add child branch" icon on a row
  - fields: Name (FlexInput, required) | Code (FlexInput) | Address (FlexTextarea) | Parent Branch (FlexSelect, optional)
  - footer: Cancel | Save Branch (primary)

- Interactions:
  - click branch row expand chevron: expands/collapses child branches
  - click "Add Branch": opens FlexModal(size=sm) with Parent Branch empty
  - click "Add child branch" icon on a row: opens FlexModal with Parent Branch pre-selected
  - click branch name inline: name becomes an inline FlexInput; Enter confirms; Escape cancels
  - select Parent Branch in modal: list preview shows visual indent where the new branch will appear

- States:
  - loading: tree shows skeleton rows while GET /org/branches resolves
  - empty: "No branches yet" + "Add Branch" FlexButton(primary)

---

### Story 2.2.3 — Department Management `[DONE]`

#### Backend
*As an API, I want to create departments under branches with a designated manager, so that department-level data scoping can be enforced.*
- `POST /api/v1/org/departments` with `branch_id`, `name`, `code`, `manager_user_id`
- `GET /api/v1/org/departments?branch_id=` returns departments for a specific branch

#### Frontend
*As a company administrator, I want to create departments and assign a manager for each, so that approval workflows route correctly to the right person.*
- Route: `#/departments` → `departments.html` + `departments-page.js`
- Layout: FlexStack(direction=vertical) > page-header, content-area
  - page-header: FlexToolbar — "Departments" title | "Add Department" FlexButton(primary)
  - content-area: FlexDataGrid

- FlexDataGrid(server-side) — department list via GET /org/departments
  - columns: Department Name, Branch, Manager, Member Count, Actions
  - row action: Edit | Manage Members

- FlexModal(size=sm) — department form, triggered by "Add Department" or row Edit
  - fields: Name (FlexInput, required) | Code (FlexInput) | Branch (FlexSelect) | Manager (FlexSelect, searchable type-ahead, queries GET /users?search=)
  - footer: Cancel | Save Department (primary)

- FlexDrawer(position=right, size=md) — "Manage Members", triggered by row action
  - members list: avatar + name per row | "Remove" icon
  - footer: "Add Members" FlexButton → opens user search FlexModal

- Interactions:
  - click "Add Department": opens FlexModal(size=sm) empty form
  - click Edit on row: opens FlexModal pre-populated
  - type in Manager field: debounced → GET /users?search=[term] → dropdown results update
  - click "Manage Members" on row: opens FlexDrawer(position=right)
  - click "Remove" on member row: DELETE /org/departments/{id}/members/{user_id} → row removed

- States:
  - loading: FlexDataGrid shows skeleton rows while GET /org/departments resolves
  - empty: "No departments yet" + "Add Department" FlexButton(primary)
  - error: FlexAlert(type=error) "Could not load departments. Retry?"

---

### Story 2.2.4 — User-Company Access Control `[DONE]`

#### Backend
*As an API, I want to control which companies a user can access, so that multi-company tenants enforce data isolation per subsidiary.*
- `user_company_access` junction table checked on every company-scoped request
- `POST /api/v1/users/{id}/companies` grants access; `DELETE /api/v1/users/{id}/companies/{company_id}` revokes
- Users can switch their active company via `PATCH /api/v1/users/me/active-company`

#### Frontend
*As a user with access to multiple companies, I want to switch my active company from a dropdown in the navigation bar, so that I can work across subsidiaries without logging out.*
- No dedicated route — company switcher is a FlexDropdown in the global top nav (hidden when user has access to only 1 company)
- Route (admin): `#/users/{id}` → user detail page "Company Access" tab

- Interactions:
  - click company switcher in top nav: opens FlexDropdown listing accessible companies; active company highlighted with checkmark
  - select a company from dropdown: PATCH /users/me/active-company → page reloads with new company context applied
  - toggle company checkbox on "Company Access" tab (admin): POST /users/{id}/companies or DELETE /users/{id}/companies/{company_id} → checkbox state updates in place

- States:
  - single-company: company switcher hidden from top nav
  - switching: spinner shown in top nav while PATCH /users/me/active-company resolves; inputs disabled

---

## Feature 2.3 — Subscription Tier Enforcement `[PLANNED]`

### Story 2.3.1 — Subscription Tier Model `[PLANNED]`

#### Backend
*As an API, I want to read a tenant's subscription tier and enforce corresponding limits as middleware, so that feature access is controlled programmatically.*
- `subscription_tier` enum field on `Tenant` model: `free`, `basic`, `premium`, `enterprise`
- `TierLimitsConfig` (YAML or DB table) defines per-tier limits: `max_users`, `max_modules`, `max_entities`, `api_rpm`
- `TenantTierMiddleware` reads the tenant's tier from the JWT claim and compares current usage against limits before routing

#### Frontend
*As a tenant administrator on the subscription settings page, I want to see my current tier, usage statistics, and a comparison table of what each tier offers, so that I know when I need to upgrade.*
- Route: `#/settings/subscription` → `settings.html` + `settings-page.js` (Subscription section)
- Layout: FlexStack(direction=vertical) > tier-section, usage-section, compare-section
  - tier-section: FlexCluster — current tier FlexBadge | plan name | "Upgrade" FlexButton(primary)
  - usage-section: FlexGrid(columns=2) — usage bars (users X/Y, modules X/Y, entities X/Y, API calls this month); bars amber at 80%, red at 100%
  - compare-section: feature matrix FlexTable — columns per tier (Free | Basic | Premium | Enterprise) | "Upgrade" FlexButton on each higher-tier column

- States:
  - loading: usage bars show skeleton while GET /settings/subscription resolves
  - at-limit: usage bar at 100% shown in red; FlexAlert(type=warning) "You've reached your [resource] limit" above the bar

---

### Story 2.3.2 — User and Module Limits per Tier `[PLANNED]`

#### Backend
*As an API, I want to reject user creation and module activation when a tenant has reached their tier limits, so that resource usage is bounded.*
- `POST /users` and `POST /modules/{id}/activate` check current counts against tier limits
- Returns 402 with `TIER_LIMIT_EXCEEDED` and `{resource, current, limit, upgrade_tier}` in the response body

#### Frontend
*As a tenant administrator who has hit the user limit, I want to see a clear upgrade prompt when I try to add a new user, so that I understand why the action failed and what to do next.*
- No dedicated route — limit errors surface inline inside existing modals

- Interactions:
  - POST /users returns 402: inline FlexAlert(type=warning) appears inside "New User" modal — "You've reached the [X]-user limit on your [Tier] plan. Upgrade to add more users." + "Upgrade Plan" link → navigates to `#/settings/subscription`
  - module activation returns 402: same FlexAlert pattern inside the module activation modal
  - form submit button remains disabled while limit banner is visible

---

### Story 2.3.3 — API Rate Limits per Tier `[PLANNED]`

#### Backend
*As an API, I want to apply per-tenant API rate limits based on their subscription tier, so that free-tier tenants cannot degrade shared infrastructure.*
- SlowAPI `limiter.limit()` decorator reads the tenant's tier from `request.state.tenant`
- Rate limits: Free=60rpm, Basic=300rpm, Premium=1000rpm, Enterprise=configurable
- Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

#### Frontend
*As a developer using the API, I want rate limit information visible in the developer settings page, so that I can monitor my API usage and plan around limits.*
- Route: `#/settings/api` → `settings.html` + `settings-page.js` (API section)
- Layout: FlexStack(direction=vertical) > usage-section, debug-section
  - usage-section: FlexGrid(columns=2) — current month API call count | daily trend chart | rate limit tier FlexBadge
  - debug-section: dev-mode rate-limit overlay (visible only when `?debug=1` in URL) — last response headers: X-RateLimit-Limit | X-RateLimit-Remaining | X-RateLimit-Reset

- Interactions:
  - any API response returns 429: global FlexAlert(type=warning) toast "API rate limit reached. Requests will resume in X seconds"
  - append `?debug=1` to any page URL: dev-mode overlay visible showing live rate limit headers from latest API response

- States:
  - loading: usage stats show skeleton while data resolves
  - near-limit (≥80%): usage count turns amber
  - at-limit: usage count turns red; FlexAlert(type=error) shown above usage section
