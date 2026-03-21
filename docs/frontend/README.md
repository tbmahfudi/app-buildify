# Frontend Architecture

## Overview

The frontend is a **Vanilla JavaScript (ES6+)** single-page application. It uses a custom **Flex Component Library** for UI components with zero npm runtime dependencies. Styling is provided by **Tailwind CSS** (CDN) and icons by **Phosphor Icons**.

---

## Technology Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| Vanilla JavaScript | ES6+ | Application logic |
| Flex Component Library | Internal | UI components and layouts |
| Tailwind CSS | Latest (CDN) | Utility-first styling |
| Phosphor Icons | 2.1.2 | Icon set |
| i18next | 23+ | Internationalization |
| Vitest | 1.0+ | Unit testing |
| @testing-library/dom | 9.3+ | DOM testing utilities |

---

## Directory Structure

```
frontend/
├── index.html                      # Single HTML entry point
├── Dockerfile                      # Production container
├── assets/
│   ├── css/
│   │   └── app.css                 # Global custom styles
│   ├── js/
│   │   ├── app-entry.js            # Bootstrap (loads main template)
│   │   ├── app.js                  # App init, auth, menu, routing
│   │   ├── api.js                  # HTTP client + token management
│   │   ├── auth-service.js         # Login/logout/session UI
│   │   ├── router.js               # Hash-based SPA router
│   │   ├── ui-utils.js             # Toast notifications, spinners
│   │   ├── i18n.js                 # i18next initialization
│   │   ├── entity-manager.js       # Dynamic entity CRUD operations
│   │   ├── dynamic-form.js         # Auto-generated form builder (76KB)
│   │   ├── dynamic-table.js        # Auto-generated table component
│   │   │
│   │   ├── nocode/                 # NoCode platform tools
│   │   │   ├── nocode-data-model.js     # Entity designer UI
│   │   │   ├── nocode-workflows.js      # Workflow builder UI
│   │   │   ├── nocode-automations.js    # Automation rule builder
│   │   │   └── nocode-lookups.js        # Lookup configuration UI
│   │   │
│   │   ├── core/                   # Core component infrastructure
│   │   │   ├── base-component.js        # BaseComponent lifecycle class
│   │   │   ├── flex-responsive.js       # Breakpoint detection singleton
│   │   │   └── module-system/           # Frontend module loader
│   │   │
│   │   ├── layout/                 # Layout components
│   │   │   ├── flex-stack.js            # Vertical / horizontal stack
│   │   │   ├── flex-grid.js             # Responsive column grid
│   │   │   ├── flex-container.js        # Max-width wrapper
│   │   │   ├── flex-section.js          # Full-width page section
│   │   │   ├── flex-sidebar.js          # Collapsible sidebar
│   │   │   ├── flex-cluster.js          # Horizontal wrapping group
│   │   │   ├── flex-toolbar.js          # Top/bottom toolbar
│   │   │   ├── flex-masonry.js          # Masonry-style grid
│   │   │   └── flex-split-pane.js       # Resizable split panels
│   │   │
│   │   ├── components/             # UI components
│   │   │   ├── flex-card.js             # Card container
│   │   │   ├── flex-modal.js            # Modal dialog
│   │   │   ├── flex-tabs.js             # Tab navigation
│   │   │   ├── flex-datagrid.js         # Feature-rich data grid
│   │   │   ├── flex-badge.js            # Badge / tag label
│   │   │   └── flex-stepper.js          # Step progress indicator
│   │   │
│   │   ├── rbac/
│   │   │   ├── rbac.js                  # Permission filtering utilities
│   │   │   └── rbac-manager.js          # RBAC management UI
│   │   │
│   │   ├── services/
│   │   │   └── base-service.js          # Base service class for API calls
│   │   │
│   │   ├── dashboard-service.js    # Dashboard page logic
│   │   ├── report-service.js       # Report page logic
│   │   ├── menu-management.js      # Menu admin UI
│   │   ├── module-manager.js       # Module management UI
│   │   ├── settings.js             # Settings page
│   │   ├── users.js                # User management page
│   │   ├── tenants.js              # Tenant management page
│   │   └── companies.js            # Company management page
│   │
│   ├── templates/
│   │   ├── main.html               # App shell (nav + content area)
│   │   ├── dashboard.html          # Dashboard template
│   │   ├── login-page.html         # Login form
│   │   ├── builder.html            # NoCode app builder
│   │   ├── reports-designer.html   # Report designer
│   │   └── ...                     # Additional page templates
│   │
│   └── i18n/                       # Translation files
│       ├── en/
│       │   ├── common.json
│       │   ├── pages.json
│       │   └── menu.json
│       ├── de/
│       ├── es/
│       ├── fr/
│       └── id/
│
├── config/
│   └── menu.json                   # Core menu definition
│
└── components/                     # High-level page components
    ├── dashboard-designer.js
    ├── report-designer.js
    ├── visual-dashboard-canvas.js
    └── ...
```

---

## Application Bootstrap

```
index.html
  └── app-entry.js
        ├── Show loading screen
        ├── Initialize i18next (i18n.js)
        └── Fetch and inject main.html
              └── app.js (init)
                    ├── Check stored tokens (api.js)
                    ├── Authenticated?
                    │     ├── No  → Show login-page.html
                    │     └── Yes → Load user profile + permissions
                    │               Load core menu + module menus
                    │               Apply RBAC filtering
                    │               Init router.js
                    │               Navigate to default route
                    └── Listen for route changes
```

---

## Routing

Hash-based routing via `router.js`:

| Route | Module | Notes |
|-------|--------|-------|
| `#/dashboard` | `dashboard-service.js` | Default home |
| `#/users` | `users.js` | User management |
| `#/rbac` | `rbac-manager.js` | RBAC admin |
| `#/tenants` | `tenants.js` | Tenant admin |
| `#/companies` | `companies.js` | Company management |
| `#/nocode/data-model` | `nocode-data-model.js` | Entity designer |
| `#/nocode/workflows` | `nocode-workflows.js` | Workflow builder |
| `#/nocode/automations` | `nocode-automations.js` | Automation rules |
| `#/menu` | `menu-management.js` | Menu config |
| `#/settings` | `settings.js` | User/system settings |
| `#/modules` | `module-manager.js` | Module management |
| `#/financial/*` | Financial module | Dynamically loaded |

**Dynamic module routes** are registered at runtime when the module's manifest is loaded.

---

## State Management

No global state library is used. State is managed as module-level variables in `app.js`:

```javascript
const appState = {
  user: null,          // Authenticated user object
  currentRoute: null   // Active route hash
}
```

**User object shape**:
```javascript
{
  id: "uuid",
  email: "user@example.com",
  full_name: "Jane Doe",
  tenant_id: "uuid",
  company_ids: ["uuid"],
  roles: [{ id, name, code }],
  permissions: [{ id, code, resource, action, scope }]
}
```

Public API:
```javascript
getAppState()      // Returns appState copy
getCurrentUser()   // Returns appState.user
```

---

## API Client (`api.js`)

Centralizes all HTTP communication and token management.

**Token storage**: `localStorage` (keys: `access_token`, `refresh_token`, `tenant_id`)

**Core methods**:

```javascript
// Authenticated fetch — automatically injects Authorization header
apiFetch(url, options)

// Auto-refreshes token if expired (transparent to callers)
apiGet(url)
apiPost(url, body)
apiPut(url, body)
apiDelete(url)

// Auth-specific
login(email, password)
logout()
refreshToken()
setTenant(tenantId)
```

**Auto-refresh logic**: If a `401` is received, the client attempts a single token refresh before retrying. If refresh fails, the user is redirected to login.

---

## RBAC on the Frontend

**File**: `assets/js/rbac/rbac.js`

```javascript
// Filter menu items — removes items the user cannot access
filterMenuByRole(menuItems, user)

// Check a single permission
hasPermission('resource:action:scope')

// Apply visibility rules to DOM elements
applyRBACToElements(elements, user)
```

> Frontend RBAC is for UX only — backend enforces all permissions.

---

## Menu System

The menu is built from two sources merged at runtime:

1. **Core menu** — `frontend/config/menu.json` (always loaded)
2. **Module menus** — Each enabled module's `manifest.json` contributes its menu items

After merging, `filterMenuByRole()` removes items the user cannot access, and the sidebar is rendered.

---

## Internationalization

See [I18N.md](./I18N.md) for full details.

**Quick setup**:
```javascript
import i18next from 'i18next'
// ...initialized in i18n.js

t('common:greeting')     // "Hello"
t('pages:dashboard.title') // "Dashboard"
```

Supported languages: `en`, `de`, `es`, `fr`, `id`

---

## Testing

```bash
npm install
npm test              # Run all tests
npm run test:ui       # Open Vitest UI browser
npm run coverage      # Generate coverage report
```

**Coverage thresholds** (vitest.config.js):
- Statements: 80%
- Branches: 75%
- Functions: 80%
- Lines: 80%

---

## Related Documents

- [Component Library](./COMPONENT_LIBRARY.md)
- [Internationalization](./I18N.md)
- [Platform Overview](../platform/OVERVIEW.md)
