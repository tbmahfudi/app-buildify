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
- Route: `#/settings` → `settings.html` + `settings.js`
- Layout: FlexStack(direction=vertical) > page-header, settings-sections
  - page-header: FlexToolbar — "Settings" title
  - settings-sections: FlexStack(gap=lg) — one FlexSection per group

- `AppearanceSection`: Theme (FlexRadio: Light / Dark / System)
- `DisplaySection`: Density (FlexRadio: Comfortable / Normal / Compact)
- `LanguageSection`: Language (FlexSelect, see Epic 16)
- `RegionSection`: Timezone (FlexSelect, searchable) | Date Format (FlexSelect: DD/MM/YYYY / MM/DD/YYYY / YYYY-MM-DD) | Time Format (FlexRadio: 12h / 24h)

- Interactions:
  - change Theme: `theme-manager.js` applies immediately with animated transition; no save button needed
  - change Density: CSS class swapped on `<body>` immediately
  - change any setting: PUT /settings/user (debounced 500 ms) → "Saved ✓" indicator flashes in the section header
  - sidebar collapse/expand: preference persisted to `localStorage` and `UserSettings`; restored on next load

- States:
  - loading: sections show skeleton fields while GET /settings/user resolves
  - saving (per section): "Saved ✓" indicator briefly visible after debounced save

---

### Story 17.1.2 — Dark/Light Theme Switching `[DONE]`

#### Backend
*No backend story — theme is stored in `user_settings.theme` and applied client-side.*

#### Frontend
*As a user, I want the entire application to switch between light and dark mode based on my preference, with all components adapting correctly, so that I can use the platform comfortably in any lighting condition.*
- No dedicated route — theme is applied globally via `theme-manager.js`; no isolated UI

- `theme-manager.js` behavior:
  - Light / Dark: adds/removes `class="dark"` on `<html>` (Tailwind dark mode); instant, no page reload
  - System: reads `window.matchMedia('(prefers-color-scheme: dark)')` and listens for OS changes
  - On load: reads from `localStorage` before API call completes (prevents flash of wrong theme)
  - All Flex components use Tailwind `dark:` variants — no separate stylesheet

- Interactions:
  - OS color scheme changes (System mode): `matchMedia` listener fires → theme toggles automatically
  - theme stored to `localStorage` immediately + `UserSettings` (debounced) for cross-device persistence

---

## Feature 17.2 — Tenant and System Settings `[DONE]`

### Story 17.2.1 — Tenant Branding Configuration `[DONE]`

#### Backend
*As an API, I want tenant branding settings returned in the tenant config endpoint, so that the frontend applies the correct brand on load.*
- `GET /api/v1/settings/tenant` returns `{tenant_name, logo_url, primary_color, secondary_color, theme_config, custom_app_name?}`
- Called once on app initialization; result cached in `appState`

#### Frontend
*As a tenant administrator on the branding page, I want to change the app name, logo, and primary color and immediately see my changes reflected in the navigation bar and login page preview, so that I can iterate on branding without repeatedly publishing changes.*
- Route: `#/settings/branding` → `settings.html` + `settings-page.js` (Branding tab)
- Layout: FlexSplitPane(initial-split=55%) > branding-form, preview-panel
  - branding-form: FlexForm — App Name (FlexInput) | Tagline (FlexInput) | Logo URL (FlexInput + inline logo preview) | Favicon URL (FlexInput) | Primary Color (hex FlexInput + color swatch picker) | Secondary Color (hex FlexInput + swatch)
  - branding-form footer: FlexToolbar — "Preview Login Page" FlexButton(ghost) | "Save Branding" FlexButton(primary)
  - preview-panel: FlexCard — mini sidebar + top nav rendering; updates in real time as form values change

- `LoginPreviewModal` FlexModal(size=lg) triggered by "Preview Login Page":
  - body: iframe rendering the login page with current branding applied
  - footer: Close FlexButton

- Interactions:
  - change any branding field: preview-panel re-renders immediately with new values
  - click "Preview Login Page": opens LoginPreviewModal
  - click "Save Branding": PUT /settings/tenant → success toast → GET /settings/tenant → CSS tokens re-applied across app

- States:
  - loading: branding-form shows skeleton fields while GET /settings/tenant resolves
  - saving: "Save Branding" button shows spinner; form disabled

---

### Story 17.2.2 — System Configuration (Superadmin) `[DONE]`

#### Backend
*As an API, I want superadmin-only endpoints to manage platform-level defaults and feature flags, so that global platform behavior can be configured without code changes.*
- `PUT /api/v1/admin/security/policies/default` updates the platform default security policy
- `GET /api/v1/admin/tenants/stats` returns platform-wide usage statistics

#### Frontend
*As a superadmin on the platform administration page, I want a dedicated admin section with platform health, tenant statistics, and default configuration panels, so that I can manage the platform without looking at the database.*
- Route: `#/admin` → `admin.html` + `admin-page.js` (superadmin only; tenant admin redirected to 403 page)
- Layout: FlexStack(direction=vertical) > page-header, stats-cards, admin-sections
  - page-header: FlexToolbar — "Platform Administration" title
  - stats-cards: FlexCluster — Total Tenants | Active Users (24h) | Registered Modules | Platform Version (FlexCard metric per item)
  - admin-sections: FlexStack(gap=lg) — Platform Defaults | Tenant Statistics | Feature Flags

- `PlatformDefaultsSection`: same security policy form as `#/settings/security` labeled "Platform Default"; saved via PUT /admin/security/policies/default

- `TenantStatisticsSection`: FlexDataGrid — Tenant Name | Users | Modules | Last Activity | Subscription Tier; sortable columns

- `FeatureFlagsSection`: FlexStack(gap=sm) — one FlexCheckbox toggle row per experimental feature (e.g. "Enable Marketplace UI")

- Interactions:
  - toggle a feature flag: PUT /admin/feature-flags/{key} {enabled} → toggle updates immediately
  - click column header in tenant statistics: GET /admin/tenants/stats?sort_by=X → grid re-renders sorted

- States:
  - loading: stats-cards show skeleton; tenant grid shows skeleton rows
  - error: FlexAlert(type=error) "Could not load admin data. Retry?"

---

### Story 17.2.3 — Menu Management `[DONE]`

#### Backend
*As an API, I want menu items to be configurable per tenant with hierarchy and permission guards, so that each tenant's navigation matches their active modules.*
- `GET /api/v1/menu` returns the menu tree filtered by the current user's permissions
- `POST/PUT/DELETE /api/v1/menu/items` CRUD for menu items; tenant admin manages their own tenant's menu
- Menu items have: `label`, `icon`, `route`, `parent_id`, `sort_order`, `required_permission`, `module_id`

#### Frontend
*As a tenant administrator on the menu management page, I want to drag menu items to reorder them and nest them under parent items, and add custom links for external tools, so that the navigation sidebar is organized for our team's workflow.*
- Route: `#/settings/menu-management` → `menu-management.html` + `menu-management-page.js`
- Layout: FlexStack(direction=vertical) > page-header, menu-tree
  - page-header: FlexToolbar — "Menu Management" title | "Add Menu Item" FlexButton(primary) | "Preview Menu" FlexButton(ghost)
  - menu-tree: FlexStack(gap=xs) — draggable card per menu item, indented per nesting level

- Per menu item card: drag handle | icon | label | module FlexBadge (if module-provided) | pencil edit icon | × delete icon (hidden for module-provided items)

- `MenuItemModal` FlexModal(size=sm) triggered by "Add Menu Item" or pencil icon:
  - fields: Label (FlexInput) | Icon (icon picker) | Route (FlexInput: internal `#/` or external URL) | Parent (FlexSelect from existing items) | Required Permission (FlexSelect)
  - footer: Cancel | Save FlexButton(primary)

- `PreviewMenuModal` FlexModal(size=md) triggered by "Preview Menu":
  - body: rendered sidebar navigation as users will see it (read-only)
  - footer: Close FlexButton

- Interactions:
  - drag card to new position: reorder updates `sort_order`; PUT /menu/items/{id} on drop
  - drag card onto another card: child indent indicator shown during drag → on drop becomes child of target
  - click pencil: opens MenuItemModal pre-populated with item data
  - click ×: DELETE /menu/items/{id} → item removed from tree
  - click "Preview Menu": opens PreviewMenuModal

- States:
  - loading: menu-tree shows skeleton cards
  - empty: "No menu items yet" + "Add Menu Item" FlexButton(primary)

---

## Feature 17.3 — White-Label Theming `[PLANNED]`

### Story 17.3.1 — CSS Custom Property Token System `[PLANNED]`

#### Backend
*No backend story — CSS token system is a frontend concern.*

#### Frontend
*As a developer building a new component, I want to use CSS custom property tokens (`--flex-color-primary`, `--flex-spacing-md`) rather than hardcoded values, so that components adapt automatically to any tenant's brand configuration.*
- No dedicated route — CSS token system is a developer convention; no UI page involved

- Token dictionary: `frontend/assets/css/tokens.css`
  - color tokens | spacing tokens (xs/sm/md/lg/xl) | typography tokens (font-family, sizes, line-heights) | border-radius tokens | shadow tokens
- All Flex components use token variables exclusively — zero hardcoded hex colors or px values
- `theme-manager.js` maps tenant `theme_config` JSON to CSS tokens: `primary_color → --flex-color-primary`
- Token reference: `docs/frontend/TOKENS.md` with visual color swatches for all tokens

---

### Story 17.3.2 — Full White-Label Branding `[PLANNED]`

#### Backend
*As an API, I want extended branding settings (custom app name, favicon, login background) stored in tenant settings, so that full white-label deployments replace all platform vendor references.*
- `TenantSettings` extended with: `custom_app_name`, `favicon_url`, `login_background_url`, `login_logo_url`, `hide_powered_by`
- `GET /settings/tenant` returns the extended fields; `PUT /settings/tenant` accepts them

#### Frontend
*As an enterprise tenant that has purchased white-label rights, I want to replace every occurrence of "App-Buildify" with my own product name and replace the login page imagery with my own, so that our clients see only our brand.*
- Route: `#/settings/branding` → White-Label section added at the bottom of the branding form (visible only to tenants with white-label entitlement)
- Layout addition (branding form — White-Label section): FlexSection — Custom App Name (FlexInput) | Login Background URL (FlexInput) | Login Logo URL (FlexInput) | "Hide Powered by App-Buildify" FlexCheckbox toggle

- Global behavior (applied from `appState.branding` on load):
  - Login page: `login_background_url` → CSS `background-image`; `login_logo_url` → logo image
  - Browser tab: `document.title` set from `custom_app_name`
  - "Powered by App-Buildify" footer: hidden when `hide_powered_by: true`
  - All platform name references read from `appState.branding.app_name` — no hardcoded strings

- Interactions:
  - change any White-Label field + "Save Branding": PUT /settings/tenant → app reloads branding; tab title and login page update
  - toggle "Hide Powered By": footer link hidden/shown immediately on next page load after save
