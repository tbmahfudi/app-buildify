# Module Frontend Contract

> Status: implemented (STEP 1 of ADR `plan/architecture/adr-module-frontend-integration.md`).
> This document is the normative contract that module authors and ADR Steps 2/3 follow.

App-Buildify is a Vanilla-JS SPA (hash routing, Tailwind-via-CDN, native ES modules, no
mandatory build) served as static files by nginx. Each enabled module injects its **menus,
routes, and page components** into the running shell. This document defines the exact contract
the shell loads modules by.

---

## 1. On-disk layout

Everything the SPA loads lives under `modules/{name}/frontend/`:

```
modules/{name}/
  manifest.json
  frontend/
    module.js            # OPTIONAL — only if the module needs custom init/services
    pages/foo.js         # page components (the units a route mounts)
    pages/foo.html       # optional HTML template, fetched at /modules/{name}/pages/foo.html
    components/  styles/  i18n.js
```

## 2. URL convention (the double-`frontend` rule)

The nginx alias `location ~ ^/modules/([^/]+)/(.+)$ { alias .../modules/$1/frontend/$2; }`
is **rooted at the module's `frontend/` directory** — it silently inserts `/frontend/`.

**All manifest paths are relative to `frontend/` and MUST NOT start with `frontend/`.**

- Correct: `"component": "pages/dashboard.js"` → URL `/modules/{name}/pages/dashboard.js`
  → on-disk `modules/{name}/frontend/pages/dashboard.js`.
- Wrong: `"component": "frontend/clinic/portal.js"` → URL `/modules/{name}/frontend/...`
  → nginx adds `/frontend/` → `frontend/frontend/...` → **404**.

**Loader hardening:** `BaseModule._resolveComponentUrl()` defensively strips a leading
`frontend/` (and any leading `/`) before building the URL, so a non-conformant manifest still
resolves instead of 404ing. The dev-mode validator warns when it does so — **authors should
still fix the manifest**, the strip is a safety net, not a license.

No nginx change is required; the fix lives entirely in the loader path construction.

## 3. Manifest schema (frontend-relevant fields)

```jsonc
{
  "name": "healthcare",
  "entry_point": null,                 // OPTIONAL. null/absent => generic BaseModule, no module.js needed
  "navigation": {
    "primary_menu": true,
    "menu_items": [                     // REQUIRED for a top-level menu parent + its icon
      { "code": "healthcare", "label": "Healthcare",
        "icon": "ph-duotone ph-heartbeat", "icon_color": "text-rose-600",
        "order": 20, "is_parent": true, "permission": null }
    ]
  },
  "routes": [
    { "path": "#/healthcare/dashboard",
      "name": "Healthcare Dashboard",
      "component": "pages/dashboard.js",   // relative to frontend/, NO leading frontend/
      "export": "default",                 // OPTIONAL named export; default if omitted
      "element": "healthcare-dashboard",   // OPTIONAL custom-element tag (see §4)
      "permission": "healthcare:dashboard:read",
      "menu": { "label": "Dashboard", "icon": "ph-duotone ph-squares-four",
                "order": 21, "parent": "healthcare" } }  // parent === a menu_items[].code
  ]
}
```

Rules:
- Every `routes[].menu.parent` MUST match a `navigation.menu_items[].code`.
- `permission` strings are the RBAC gate. Menus/routes are **server-enforced** by
  `menu_service` + `matches_permission` — unchanged by this step. Never trust client-only checks.

## 4. Page-component contract (what the SPA mounts)

A route's `component` module exports **one of two** shapes. The shell mounts whichever it finds,
so adoption is per-route. **Light DOM is the default** — a page renders Tailwind-class markup into
the shell's `#app-content`, so platform CSS and Phosphor icons work verbatim (no Shadow DOM).

### 4a. Light-DOM page class (default, today's style)

```js
export default class DashboardPage {
  constructor() {}                 // no-arg
  async render() {                 // shell has already set up <div id="app-content"></div>
    document.getElementById('app-content').innerHTML = '...tailwind markup...';
    // optionally fetch('/modules/healthcare/pages/dashboard.html'), wire events, call APIs
  }
  async destroy() {}               // OPTIONAL — called on route change for cleanup
}
```

Export selection (in order): the named export in `route.export` → the `default` export → a sole
class-like named export (back-compat with `export class AccountsPage`).

### 4b. Custom element (opt-in, ADR primary direction)

```js
customElements.define('healthcare-dashboard', class extends HTMLElement {
  connectedCallback() { this.innerHTML = '...tailwind markup...'; }  // light DOM by default
  disconnectedCallback() { /* native teardown */ }
});
```

Declare the tag in the route as `"element": "healthcare-dashboard"`. The shell creates the tag
and appends it into `#app-content`; `connectedCallback()` renders, `disconnectedCallback()` tears
down on route change. Shadow DOM is **opt-in** (and then loses Tailwind-CDN/Phosphor unless tokens
+ `adoptedStyleSheets` are used — see ADR §7.1).

### Lifecycle

On every route change the shell tears down the previously-mounted module page: it calls a page
class's optional `async destroy()`, and removes a custom element from the DOM (firing
`disconnectedCallback()`).

### Error state

If a page fails to load, the shell renders a **clean inline error card** (not a raw 404 / blank
screen) inside `#app-content` and dispatches `route:loaded` with `{ error: true }`.

## 5. Generic loader / graceful degradation (no `module.js` required)

`moduleLoader.loadModule()`:

1. Loads the manifest (from the API: `GET /modules/{name}/manifest`).
2. Runs the **dev-mode validator** (§6) — warn-only, never blocks.
3. Resolves a module instance via `_resolveModuleInstance()`:
   - If `entry_point` is set, dynamic-imports `/modules/{name}/{entry_point}` and instantiates
     the exported class (the custom-init path — e.g. financial's `FinancialModule`).
   - **If `entry_point` is null/absent, OR the entry import 404s / has no class, it falls back to
     a generic `BaseModule` built directly from the manifest.** `BaseModule.registerRoutes()`
     maps `manifest.routes[]` to route handlers — so a **manifest-only module still registers its
     routes** instead of failing the whole loader.
4. Calls `init()` and registers the module with `moduleRegistry`.

A manifest-only module (e.g. healthcare, which has no `module.js`) thus degrades gracefully:
its routes register and `#/{module}/*` resolves, instead of the previous behavior where the
missing `module.js` 404'd and killed the module's entire route table.

## 6. Dev-mode manifest validator

Runs only in dev mode (`window.APP_CONFIG.devMode === true`, or `localhost`/`127.0.0.1`).
Console-warn only — never throws, never blocks loading. Flags:

- missing `navigation.menu_items` (no top-level menu parent will render);
- `menu_items[]` missing an `icon`;
- `routes[].component` starting with `frontend/` (the double-frontend trap);
- `routes[].menu.parent` with no matching `navigation.menu_items[].code` (orphan menu);
- a manifest with neither `entry_point` nor `routes` (registers nothing).

## 7. What stays unchanged (backward compat)

- **Backend & `menu_service` untouched.** Server-driven, RBAC-filtered menus remain authoritative.
- **financial** (custom `module.js`) and **template** keep working exactly as before — the
  generic-loader path is additive, triggered only when `entry_point` is null/absent or fails.
- `loadRoute()` still accepts a legacy handler that returns a bare page class (normalized
  internally to the `{ kind: 'class', PageClass }` descriptor).
