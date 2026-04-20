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
- Route: `#/tenants` renders `frontend/assets/templates/tenants.html` + `tenants.js`
- "New Tenant" button opens a `FlexModal` with fields: Tenant Name, Slug (auto-generated from name, editable), Domain, Admin Email, Admin Password
- Slug field: auto-derives from name (lowercase, hyphens), shows a live preview of the tenant URL
- On submit: spinner shown; on success modal closes and the new tenant appears at the top of the tenant list
- Tenant list shows: name, slug, plan tier badge, active/suspended status chip, user count, created date
- Row actions: Edit, Suspend/Activate, View Users

---

### Story 2.1.2 — Tenant Settings and Branding `[DONE]`

#### Backend
*As an API, I want to store and serve per-tenant branding configuration, so that the frontend can apply tenant-specific visual identity.*
- `GET /api/v1/settings/tenant` returns `{tenant_name, logo_url, primary_color, secondary_color, theme_config}`
- `PUT /api/v1/settings/tenant` updates branding; tenant admin scope only

#### Frontend
*As a tenant administrator on the branding settings page, I want to upload my logo and pick my brand colors, so that the platform shows my company's identity to all users.*
- Route: `#/settings/branding` with fields: Company Name, Logo URL (text input with live preview), Primary Color (color picker hex input + swatch), Secondary Color
- Logo preview renders inline at 120×40 px (the sidebar logo dimensions)
- Primary color swatch updates a preview sidebar snippet in real time
- "Save Branding" button calls `PUT /settings/tenant`; on success applies changes immediately by updating CSS variables via `theme-manager.js`
- Changes take effect for all users of the tenant without page reload (CSS custom properties overridden at `:root`)

---

### Story 2.1.3 — Tenant Suspension and Deactivation `[DONE]`

#### Backend
*As an API, I want to suspend a tenant so that all their users receive 403 responses, preserving data while blocking access.*
- `PATCH /api/v1/org/tenants/{id}` with `{is_active: false}` suspends the tenant
- `TenantMiddleware` checks `tenant.is_active` on every authenticated request; if false → 403 with `TENANT_SUSPENDED`

#### Frontend
*As a superadmin on the tenant detail page, I want to suspend or reactivate a tenant with a confirmation dialog, so that I don't accidentally lock out a client.*
- Tenant list row and tenant detail page both have a "Suspend" / "Activate" toggle button
- Clicking "Suspend" opens a `FlexModal`: "Are you sure you want to suspend [Tenant Name]? All users will lose access immediately." with a required Reason text field
- Confirming calls `PATCH /org/tenants/{id}`; the tenant row status chip updates to "Suspended" (red)
- "Activate" has a simpler modal: "Restore access for [Tenant Name]?" — no reason field required
- Suspended tenants highlighted with a red background row tint in the list

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
- Route: `#/companies` renders a card grid of all companies
- Each card shows: company name, code, currency, timezone, active user count
- "Add Company" button opens a `FlexDrawer` (right side) with fields: Name, Code, Country, Currency (searchable select), Timezone (searchable select), Fiscal Year Start month (select)
- Edit: clicking a card's edit icon opens the same drawer pre-populated
- Delete: confirmation modal; blocked if company has active users (shows count with a warning)
- Company card click navigates to `#/companies/{id}` detail page showing branches, departments, and modules

---

### Story 2.2.2 — Branch Management `[DONE]`

#### Backend
*As an API, I want to manage branches within a company, so that data can be scoped to physical or virtual office locations.*
- `POST /api/v1/org/branches` with `company_id`, `name`, `code`, `address`, optional `parent_branch_id`
- Branch hierarchy unlimited depth; `parent_branch_id` self-references `Branch.id`

#### Frontend
*As a company administrator on the branches page, I want to see branches in a tree structure and add child branches under parent ones, so that I can model our office hierarchy accurately.*
- Route: `#/branches` shows a collapsible tree list; root branches expand to reveal child branches
- "Add Branch" button opens `FlexModal` with fields: Name, Code, Address, Parent Branch (select, optional)
- Selecting a parent branch in the modal visually indents the preview in the list
- Inline edit: clicking the branch name opens an inline edit field (no drawer needed for simple name changes)
- "Add child branch" icon on each row opens the same modal with the parent pre-selected

---

### Story 2.2.3 — Department Management `[DONE]`

#### Backend
*As an API, I want to create departments under branches with a designated manager, so that department-level data scoping can be enforced.*
- `POST /api/v1/org/departments` with `branch_id`, `name`, `code`, `manager_user_id`
- `GET /api/v1/org/departments?branch_id=` returns departments for a specific branch

#### Frontend
*As a company administrator, I want to create departments and assign a manager for each, so that approval workflows route correctly to the right person.*
- Route: `#/departments` shows a table with columns: Department Name, Branch, Manager, Member Count, Actions
- "Add Department" button opens `FlexModal` with fields: Name, Code, Branch (select), Manager (user search select)
- Manager field uses a type-ahead search `FlexSelect` that queries `GET /users?search=`
- Department row: "Manage Members" button opens a side drawer listing users in the department with add/remove controls

---

### Story 2.2.4 — User-Company Access Control `[DONE]`

#### Backend
*As an API, I want to control which companies a user can access, so that multi-company tenants enforce data isolation per subsidiary.*
- `user_company_access` junction table checked on every company-scoped request
- `POST /api/v1/users/{id}/companies` grants access; `DELETE /api/v1/users/{id}/companies/{company_id}` revokes
- Users can switch their active company via `PATCH /api/v1/users/me/active-company`

#### Frontend
*As a user with access to multiple companies, I want to switch my active company from a dropdown in the navigation bar, so that I can work across subsidiaries without logging out.*
- Company switcher dropdown in the top navigation (only visible if the user has access to > 1 company)
- Dropdown shows: list of accessible companies with the active company highlighted with a checkmark
- Selecting a company calls `PATCH /users/me/active-company`; page reloads to apply the new company context
- Active company name shown in the top nav beside the switcher icon
- Tenant admin `#/users/{id}` detail page has a "Company Access" tab: checklist of all companies; toggle each to grant/revoke access

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
- Route: `#/settings/subscription` shows: current tier badge, usage bars (users X/Y, modules X/Y, entities X/Y, API calls this month)
- Usage bars turn amber at 80% and red at 100%
- "Compare Plans" section below shows a feature matrix table for all tiers
- "Upgrade" button on each higher tier (links to billing contact or payment page — out of scope for v1)

---

### Story 2.3.2 — User and Module Limits per Tier `[PLANNED]`

#### Backend
*As an API, I want to reject user creation and module activation when a tenant has reached their tier limits, so that resource usage is bounded.*
- `POST /users` and `POST /modules/{id}/activate` check current counts against tier limits
- Returns 402 with `TIER_LIMIT_EXCEEDED` and `{resource, current, limit, upgrade_tier}` in the response body

#### Frontend
*As a tenant administrator who has hit the user limit, I want to see a clear upgrade prompt when I try to add a new user, so that I understand why the action failed and what to do next.*
- When `POST /users` returns 402: instead of a generic error, show an inline banner inside the "New User" modal: "You've reached the [X]-user limit on your [Tier] plan. Upgrade to add more users."
- "Upgrade Plan" link in the banner navigates to `#/settings/subscription`
- Same UX pattern for module activation limit: banner inside the module activation modal

---

### Story 2.3.3 — API Rate Limits per Tier `[PLANNED]`

#### Backend
*As an API, I want to apply per-tenant API rate limits based on their subscription tier, so that free-tier tenants cannot degrade shared infrastructure.*
- SlowAPI `limiter.limit()` decorator reads the tenant's tier from `request.state.tenant`
- Rate limits: Free=60rpm, Basic=300rpm, Premium=1000rpm, Enterprise=configurable
- Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

#### Frontend
*As a developer using the API, I want rate limit information visible in the developer settings page, so that I can monitor my API usage and plan around limits.*
- `#/settings/api` page shows current month's API call count, daily trend chart, and rate limit tier
- Rate limit headers from API responses stored in `api.js` and surfaced in a dev-mode overlay (toggled by `?debug=1`)
- When 429 is received: global toast "API rate limit reached. Requests will resume in X seconds"
