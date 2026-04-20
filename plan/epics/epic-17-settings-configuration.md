# Epic 17 — Settings & Configuration

> User-level preferences and system-level settings with a layered override model.

---

## Feature 17.1 — User Settings `[DONE]`

### Story 17.1.1 — User Preferences `[DONE]`

#### Backend
*As an API, I want to persist user preferences and return them on login, so that the UI reflects each user's personal configuration.*
- `GET /api/v1/settings/user` returns `{theme, language, timezone, density, sidebar_state, preferences: {}}`
- `PUT /api/v1/settings/user` updates any subset of the above
- Settings applied to `appState` on login; used by `theme-manager.js` and i18next

#### Frontend
*As a user on the settings page, I want to see all my preferences grouped into clear sections (Appearance, Language, Region) with instant feedback when I change a setting, so that customizing my experience is satisfying.*
- Route: `#/settings` renders `settings.html` + `settings.js`
- **Appearance section**: Theme toggle (Light / Dark / System) — changing theme immediately updates the page without a save button; animated transition
- **Display section**: Density radio (Comfortable / Normal / Compact) — updates all padding/spacing instantly via CSS class on `<body>`
- **Language section**: Language select — triggers immediate language switch as described in Epic 16
- **Region section**: Timezone select (searchable), Date Format select (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD), Time Format (12h/24h)
- All settings auto-save (debounced 500ms after change); a subtle "Saved" indicator flashes in the section header after each save
- Sidebar Collapsed/Expanded preference persists: remembered after page reload

---

### Story 17.1.2 — Dark/Light Theme Switching `[DONE]`

#### Backend
*No backend story — theme is stored in `user_settings.theme` and applied client-side.*

#### Frontend
*As a user, I want the entire application to switch between light and dark mode based on my preference, with all components adapting correctly, so that I can use the platform comfortably in any lighting condition.*
- `theme-manager.js` applies the theme by adding `class="dark"` to `<html>` element (Tailwind dark mode)
- `"System"` option uses `window.matchMedia('(prefers-color-scheme: dark)')` and listens for changes
- All Flex components use Tailwind `dark:` variants for dark mode colors — no separate component stylesheet needed
- Theme switching is instant (no page reload, no flash of wrong theme on load)
- Theme stored in both `localStorage` (for immediate load before API call completes) and `UserSettings` (for persistence across devices)

---

## Feature 17.2 — Tenant and System Settings `[DONE]`

### Story 17.2.1 — Tenant Branding Configuration `[DONE]`

#### Backend
*As an API, I want tenant branding settings returned in the tenant config endpoint, so that the frontend applies the correct brand on load.*
- `GET /api/v1/settings/tenant` returns `{tenant_name, logo_url, primary_color, secondary_color, theme_config, custom_app_name?}`
- Called once on app initialization; result cached in `appState`

#### Frontend
*As a tenant administrator on the branding page, I want to change the app name, logo, and primary color and immediately see my changes reflected in the navigation bar and login page preview, so that I can iterate on branding without repeatedly publishing changes.*
- Route: `#/settings/branding`
- Settings form: App Name (text), Tagline (text), Logo URL (with inline preview), Favicon URL, Primary Color (hex color picker + swatch), Secondary Color
- Live preview panel (split-pane): mini version of the sidebar and top nav updating in real time as settings change
- "Preview Login Page" button renders the login page in a modal with the current branding applied
- "Save Branding" calls `PUT /settings/tenant`; after save, reloads app branding by re-fetching `GET /settings/tenant` and re-applying CSS tokens

---

### Story 17.2.2 — System Configuration (Superadmin) `[DONE]`

#### Backend
*As an API, I want superadmin-only endpoints to manage platform-level defaults and feature flags, so that global platform behavior can be configured without code changes.*
- `PUT /api/v1/admin/security/policies/default` updates the platform default security policy
- `GET /api/v1/admin/tenants/stats` returns platform-wide usage statistics

#### Frontend
*As a superadmin on the platform administration page, I want a dedicated admin section with platform health, tenant statistics, and default configuration panels, so that I can manage the platform without looking at the database.*
- Route: `#/admin` (superadmin-only; tenant admin sees 403 page)
- Admin dashboard cards: Total Tenants | Active Users (24h) | Registered Modules | Platform Version
- "Platform Defaults" section: same security policy form as tenant settings but labeled "Platform Default"
- "Tenant Statistics" table: sortable by users, modules, last activity, subscription tier
- "Feature Flags" section: toggles for experimental platform features (e.g. "Enable Marketplace UI")

---

### Story 17.2.3 — Menu Management `[DONE]`

#### Backend
*As an API, I want menu items to be configurable per tenant with hierarchy and permission guards, so that each tenant's navigation matches their active modules.*
- `GET /api/v1/menu` returns the menu tree filtered by the current user's permissions
- `POST/PUT/DELETE /api/v1/menu/items` CRUD for menu items; tenant admin manages their own tenant's menu
- Menu items have: `label`, `icon`, `route`, `parent_id`, `sort_order`, `required_permission`, `module_id`

#### Frontend
*As a tenant administrator on the menu management page, I want to drag menu items to reorder them and nest them under parent items, and add custom links for external tools, so that the navigation sidebar is organized for our team's workflow.*
- Route: `#/settings/menu-management` renders `menu-management.html`
- Drag-and-drop tree: each menu item is a draggable card; dragging onto another item makes it a child (indent indicator shown during drag)
- Adding a menu item: "Add Menu Item" button opens a modal with: Label, Icon (icon picker), Route (internal `#/` or external URL), Parent (select from existing items), Required Permission (select)
- Editing: click the pencil icon on any item to open the same modal pre-populated
- Module-provided menu items shown with a module badge and cannot be deleted (only moved/renamed)
- "Preview Menu" button shows the sidebar navigation as users will see it

---

## Feature 17.3 — White-Label Theming `[PLANNED]`

### Story 17.3.1 — CSS Custom Property Token System `[PLANNED]`

#### Backend
*No backend story — CSS token system is a frontend concern.*

#### Frontend
*As a developer building a new component, I want to use CSS custom property tokens (`--flex-color-primary`, `--flex-spacing-md`) rather than hardcoded values, so that components adapt automatically to any tenant's brand configuration.*
- CSS token dictionary defined in `frontend/assets/css/tokens.css`: color tokens, spacing tokens (xs/sm/md/lg/xl), typography tokens (font-family, font-sizes, line-heights), border-radius tokens, shadow tokens
- All Flex components updated to use token variables exclusively (zero hardcoded hex colors or px values)
- Tenant `theme_config` JSON mapped to CSS tokens in `theme-manager.js`: `primary_color → --flex-color-primary`
- Token reference documentation in `docs/frontend/TOKENS.md` with a visual swatch for all color tokens

---

### Story 17.3.2 — Full White-Label Branding `[PLANNED]`

#### Backend
*As an API, I want extended branding settings (custom app name, favicon, login background) stored in tenant settings, so that full white-label deployments replace all platform vendor references.*
- `TenantSettings` extended with: `custom_app_name`, `favicon_url`, `login_background_url`, `login_logo_url`, `hide_powered_by`
- `GET /settings/tenant` returns the extended fields; `PUT /settings/tenant` accepts them

#### Frontend
*As an enterprise tenant that has purchased white-label rights, I want to replace every occurrence of "App-Buildify" with my own product name and replace the login page imagery with my own, so that our clients see only our brand.*
- Login page reads `login_background_url` (sets CSS `background-image`) and `login_logo_url` (renders instead of the default logo)
- Browser tab title set from `custom_app_name` via `document.title`
- "Powered by App-Buildify" footer link hidden when `hide_powered_by: true`
- All `App-Buildify` string references in the UI read from `appState.branding.app_name` (configurable) rather than being hardcoded
- Branding settings form on `#/settings/branding` has a "White-Label" section (only visible to tenants with white-label entitlement)
