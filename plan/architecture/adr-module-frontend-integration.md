---
status: draft
author: B1 (Architect)
date: 2026-06-28
title: Dynamic module frontend integration (static-deployable micro-frontends)
supersedes: []
related: [adr-005-module-packaging-format.md, adr-010-public-portal-framework.md, arch-mod-template.md]
---

# ADR: Dynamic Module Frontend Integration

## Context

App-Buildify is a multi-tenant no-code platform. The platform shell is a **Vanilla-JS SPA**
(`frontend/assets/js/app.js`) using Tailwind-via-CDN, Phosphor icons, native ES modules, hash
routing, and **no build step**. It is served as plain static files by nginx
(`infra/nginx/app.conf`). Modules are enabled per-tenant; each enabled module needs to inject its
**menus, routes/links, and page components** into the running SPA.

A hard constraint governs every decision here: **the entire frontend must deploy on any plain
static web server** (nginx / Apache / S3 / CDN) with **no Node SSR and no server runtime**. The
backend (FastAPI) exists, but it must never be *required* to render or assemble frontend HTML.

This ADR reviews how module frontends load **today**, documents where it breaks, and recommends a
single standardized contract going forward.

---

## 1. Current-State Assessment

### 1.1 How a module frontend is *supposed* to load today

There are **two parallel, partially-overlapping** integration paths. Both are real and both run.

**A. Client-side dynamic loader (JS module system)** — `frontend/assets/js/core/module-system/`:

1. `initApp()` (app.js:72) calls `moduleLoader.loadAllModules()`.
2. `fetchEnabledModules()` -> `GET /module-registry/enabled/names` returns enabled module names
   for the tenant.
3. For each name, `loadModule()`:
   - `loadManifest()` -> `GET /modules/{name}/manifest` (manifest comes from the **API**, not a static file).
   - Computes `entryPoint = manifest.entry_point || 'module.js'` and dynamic-imports
     `/modules/{name}/{entryPoint}`.
   - Finds a class via `moduleExports.default` or `{Pascal}Module`, `new`s it, calls `init()`.
4. The module's `init()` builds `this.routes` (each with an async `handler()` that dynamic-imports
   a page class) and `this.menuItems`; `moduleRegistry.register(module)` collects them.
5. **Routing** (`loadRoute()`, app.js:1658): after a long `if`-ladder of core routes, it calls
   `moduleRegistry.findRoute('#/'+route)`. If found, it does `new PageClass(); await page.render()`.
   The page is expected to render into `#app-content`. If **not** found, it falls through to
   `resourceLoader.loadTemplate(route)` -> 404.

**B. Server-driven menu** — `backend/app/services/menu_service.py::_get_module_menu_items`:
- Independently of the JS loader, `GET /menu?include_modules=true` reads each enabled module's
  manifest server-side and synthesizes `MenuItem`s from `manifest.navigation.menu_items` (parents,
  with `code`/`icon`/`icon_color`/`order`) and `manifest.routes[].menu` (children, gated by
  `routes[].permission` via `matches_permission`). This is the **authoritative, RBAC-filtered**
  menu the SPA actually renders (`loadMenuFromBackend()`, app.js:533).
- `loadMenuFromStatic()` (the legacy path) instead pulls `moduleRegistry.getAccessibleMenuItems()`
  from the **client** loader. Only reachable when `APP_CONFIG.useDynamicMenu === false`.

So in production: **menus come from the backend manifest reader (path B); route resolution &
page rendering come from the client loader (path A).** The two paths read the *same manifest* but
via different code and with different field expectations.

**nginx URL convention** (`app.conf`):
```
location ~ ^/modules/([^/]+)/(.+)$ {
  alias /usr/share/nginx/modules/$1/frontend/$2;
}
```
The alias **silently inserts `/frontend/`**. So `/modules/financial/pages/accounts.js` resolves to
the on-disk file `modules/financial/frontend/pages/accounts.js`. The URL namespace is *rooted at
the module's `frontend/` directory* — component paths in the manifest must be relative to
`frontend/`, **not** include it.

### 1.2 Where it breaks (verified on disk)

The **financial** and **template** modules are correctly shaped; **healthcare** violates the
(undocumented) contract on every axis:

| Concern | financial (works) | healthcare (broken) |
|---|---|---|
| Entry point JS | `frontend/module.js` exists; manifest `entry_point: "module.js"` | **no `module.js` anywhere**; manifest has **no `entry_point`** -> loader imports `/modules/healthcare/module.js` -> **404** -> no routes registered |
| `navigation.menu_items` | present (parent + icon) | **absent** -> backend builds child menu items whose `parent` (`"healthcare"`) resolves to **no parent** |
| Component path | `"pages/accounts.js"` (relative to `frontend/`) | `"frontend/clinic/portal.js"` -> URL `/modules/healthcare/frontend/...` -> nginx adds `/frontend/` -> `frontend/frontend/...` -> **404 (double-frontend)** |
| Component file exists | yes | `clinic/portal.js` **does not exist** (manifest declares pages never built); siblings like `appointment-queue.js` exist |

Net effect: **every `#/healthcare/*` route 404s**, no healthcare menu parent renders, and the
declared dashboard/portal page is vaporware.

### 1.3 Why it is fragile / inconsistent

- **Two manifest readers, one schema, no validation.** The JS loader and `menu_service` both parse
  the manifest but expect different shapes; nothing fails loudly when a module omits `entry_point`,
  `navigation`, or ships a wrong `component` path. Failures are `console.error` + 404.
- **The `module.js` boilerplate is pure ceremony and is duplicated.** `financial/frontend/module.js`
  re-declares routes/menus that **already exist in the manifest**, by hand, and re-implements what
  `BaseModule` already does generically. `BaseModule.registerRoutes()` can build the exact same
  route table straight from `manifest.routes`, yet financial doesn't extend `BaseModule` and
  healthcare ships no class at all. The class is an undocumented, inconsistent requirement.
- **Path convention is implicit.** The `/frontend/` alias is a trap; only tribal knowledge keeps
  authors from the double-frontend bug.
- **No page-component interface spec.** By observation the contract is: `export` a class with a
  no-arg `constructor()` and `async render()` that writes into `#app-content`. This is nowhere
  documented and not enforced.

---

## 2. Requirements

1. **Dynamic, per-tenant** menu + route + component integration for **any** enabled module.
2. **Framework-agnostic** page contract so module teams build pages independently.
3. **Static-deployable**: works on any web server, **no SSR, no server runtime** to assemble HTML.
4. **Secure**: preserve existing **server-side RBAC** menu/route gating (`menu_service` +
   `matches_permission`); never rely on client-only permission checks for trust.
5. **Incremental / low-rewrite**: keep the Vanilla-JS SPA and the working financial-style modules.
6. **Loud failure / validatable**: a malformed module manifest should be detectable at install time.

---

## 3. Options Analysis

### Option 1 — Keep Vanilla-JS, **standardize the ES-module dynamic-import contract** (manifest-driven, drop the hand-written class)
Make the manifest the single source of truth. The generic `BaseModule` (already present) builds
routes/menus from `manifest.routes`; a module's `module.js` becomes **optional** (only for custom
init). Fix the path convention, add `navigation.menu_items`, document the page interface.
- **Pros:** zero new tooling; matches current architecture; financial already ~95% conformant;
  smallest migration; pure static files; backend RBAC untouched.
- **Cons:** no JS-level isolation (shared globals/CSS); versioning is by-URL only; still hand-written
  page classes (but that's the page author's normal job).

### Option 2 — **Import maps** + native ES modules
Add an import map so modules can resolve shared deps (`@platform/api`) by bare specifier.
- **Pros:** static-deployable; native; removes hard-coded `/assets/js/...` paths inside modules.
- **Cons:** import maps are **document-level**, not composable at runtime per-module; doesn't itself
  solve menu/route/component wiring. Useful as a **complement**, not a primary answer.

### Option 3 — **Web Components / Custom Elements** as the page contract
Page = a custom element `<healthcare-dashboard>`; SPA mounts it into `#app-content`.
- **Pros:** framework-agnostic; native; static-deployable; real **style/DOM isolation** via Shadow
  DOM; clean lifecycle; works with any inner framework (Lit/Preact/vanilla).
- **Cons:** Shadow DOM **breaks Tailwind-via-CDN and Phosphor** (global stylesheet/icon font don't
  pierce shadow boundaries) unless per-component styling is reworked; bigger rewrite of existing
  pages; current pages reach into `#app-content` directly. **Strong long-term target, costly now.**

### Option 4 — **Module Federation** (Vite/Webpack remotes)
Runtime-loaded remote bundles with shared-dependency negotiation.
- **Pros:** mature micro-frontend isolation/versioning; independent deploys.
- **Cons:** **introduces a mandatory bundler/build per module** and a host build; heavy conceptual
  load; the remoteEntry contract is static-host-able but the **authoring** workflow is the opposite
  of the current no-build ethos. Overkill for a hash-routed vanilla SPA. **Rejected for now.**

### Option 5 — **Lightweight framework** (Preact/Vue/Lit) outputting static assets
Adopt e.g. Preact + a Vite build that emits static JS/CSS.
- **Pros:** better DX; Lit pairs naturally with Web Components; **can** be fully static (no SSR).
- **Cons:** introduces a **build step** the platform currently doesn't have (Tailwind is CDN, no
  Vite); two rendering paradigms during migration; learning curve. Static constraint is satisfiable
  but the cost is not justified **as a frontend-integration mechanism**.

### Comparison

| Criteria | 1. Std ES-module | 2. Import maps | 3. Web Components | 4. Module Federation | 5. Framework+Vite |
|---|---|---|---|---|---|
| Static-deployable (no SSR) | Yes | Yes | Yes | Yes (remotes) | Yes (if no SSR) |
| No-build vs build | **No build** | No build | No build | **Build req.** | **Build req.** |
| Learning curve | Lowest | Low | Medium | High | Medium-High |
| Isolation (CSS/JS) | Weak | Weak | **Strong (Shadow)** | Strong | Medium |
| Versioning | URL-based | URL-based | URL-based | **First-class** | Bundle-based |
| RBAC fit (server menu/route) | **Native (unchanged)** | Native | Native | Needs glue | Needs glue |
| Migration cost (this repo) | **Lowest** | Low | High | Very High | High |
| Ecosystem | N/A | Native | Growing | Mature | Mature |

---

## 4. Recommendation

**Adopt Option 1: a standardized, manifest-driven ES-module micro-frontend contract**, with
**Option 2 (import maps)** as an optional convenience and **Option 3 (Web Components)** named as the
**future isolation target** (non-blocking). This is the only option that satisfies *all* hard
constraints — static-deployable, no-build, low migration — while preserving the existing
server-side RBAC menu pipeline verbatim.

### 4.1 The Module Frontend Contract (normative)

**On-disk layout** (everything the SPA loads lives under `modules/{name}/frontend/`):
```
modules/{name}/
  manifest.json
  frontend/
    module.js            # OPTIONAL — only if custom init is needed
    pages/foo.js         # page components
    pages/foo.html       # optional page templates fetched at /modules/{name}/pages/foo.html
    components/  styles/  i18n.js
```

**URL convention (fixes the double-frontend bug):** the nginx `/modules/{name}/(.+)` alias is
rooted at `frontend/`. **All manifest paths are relative to `frontend/` and MUST NOT start with
`frontend/`.** Loader URL = `/modules/{name}/{path}`.

**Manifest schema (relevant fields):**
```jsonc
{
  "name": "healthcare",
  "entry_point": null,                 // OPTIONAL. null/absent => generic BaseModule, no module.js needed
  "navigation": {
    "primary_menu": true,
    "menu_items": [                     // REQUIRED for a top-level parent + its icon
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
      "permission": "healthcare:dashboard:read",
      "menu": { "label": "Dashboard", "icon": "ph-duotone ph-squares-four",
                "order": 21, "parent": "healthcare" } }   // parent === a menu_items[].code
  ]
}
```
Rules: every `routes[].menu.parent` MUST match a `navigation.menu_items[].code`. `permission`
strings are the RBAC gate (server-enforced; unchanged).

**Page-component interface (what the SPA calls):** a page module exports a class (default, or the
name given in `route.export`) with:
```js
export default class DashboardPage {
  constructor() {}                 // no-arg
  async render() {                 // SPA has already set content.innerHTML = '<div id="app-content"></div>'
    document.getElementById('app-content').innerHTML = '...';
    // optionally fetch('/modules/healthcare/pages/dashboard.html'), wire events, call module APIs
  }
  // optional: async destroy() {} for cleanup on route change
}
```
This is exactly what financial's `AccountsPage` already does and what `loadRoute()` already
invokes (`new PageClass(); await page.render()`). No app.js change is required to honor it.

**Generic loader (eliminate per-module `module.js` boilerplate):** when `entry_point` is
null/absent, `moduleLoader.loadModule()` instantiates the generic `BaseModule` directly from the
manifest. `BaseModule.registerRoutes()` already maps `manifest.routes[]` -> route handlers that
dynamic-import `/modules/{name}/{component}`. A custom `module.js` remains supported for modules
that need bespoke init/services (financial keeps working as-is, or is simplified later).

**Menus stay server-driven (RBAC preserved):** no change to `menu_service` is required — once a
module supplies `navigation.menu_items` + `routes[].menu` with correct `parent` codes and
`permission`s, the existing `_get_module_menu_items` builds the RBAC-filtered tree. Client-side
`moduleRegistry` menu building is retained only for the legacy `useDynamicMenu=false` fallback.

### 4.2 Optional import map (Option 2)
Add to `index.html` so modules import shared platform code by bare specifier instead of fragile
relative/absolute paths:
```html
<script type="importmap">
{ "imports": { "@platform/api": "/assets/js/api.js", "@platform/ui": "/assets/js/ui-utils.js" } }
</script>
```
Purely static; no build. Lets module pages do `import { apiFetch } from '@platform/api'`.

---

## 5. Migration Path

**Phase 0 — Codify (this ADR + docs).** Publish the contract in `docs/modules/CREATING_A_MODULE.md`
and `arch-mod-template.md`; add a JSON Schema for the manifest. Backward-compatible: existing
financial/template modules already conform.

**Phase 1 — Loader hardening (small, central, backward-compatible).** In `module-loader.js`: when
`entry_point` is null/absent, instantiate generic `BaseModule` instead of 404ing on
`module.js`. Add a dev-mode manifest validator (path starts-with-`frontend/` warning; orphan
`menu.parent`; missing component file). No change to nginx or `menu_service`. Existing modules
unaffected.

**Phase 2 — Fix healthcare as the reference module.** In `modules/healthcare/manifest.json`:
(a) add `navigation.menu_items` with a `healthcare` parent + icon; (b) strip the `frontend/`
prefix from every `component` (`frontend/clinic/portal.js` -> `clinic/portal.js`); (c) point each
route at a component that **actually exists** (e.g. map dashboard to a real page, wrap existing
`clinic/appointment-queue.js` to the page-class interface, or build the missing `clinic/dashboard.js`).
Leave `entry_point: null` so the generic loader drives it. Verify `#/healthcare/*` renders and the
Healthcare menu parent appears, RBAC-gated.

**Phase 3 — Normalize page components.** Ensure each module page exports the standard
`{ constructor(); async render() }` class; adopt the optional import map; converge financial onto
the generic loader (delete redundant hand-written `module.js` route/menu duplication) where safe.

**Phase 4 (future, non-blocking) — Web Components isolation.** Offer an optional custom-element page
contract for modules needing CSS/DOM isolation, once Tailwind/Phosphor-in-shadow is solved.

**What each module author must provide:** a manifest with `navigation.menu_items` (parent+icon),
`routes[]` with `frontend/`-relative `component` paths, `menu.parent` codes matching a
`menu_items[].code`, correct `permission` strings, and page classes implementing
`constructor()/render()`. `module.js` only if custom init is needed.

**Backward-compat:** modules shipping a working `module.js` (financial) keep functioning unchanged;
the generic-loader path is additive (triggered only when `entry_point` is null/absent).

---

## 6. Risks / Open Questions (for C-stage)

1. **Manifest source of truth.** Loader reads manifest from the **API** (`/modules/{name}/manifest`)
   while `menu_service` reads it from the DB-registered module record. Confirm both reflect the same
   on-disk `manifest.json` after install/upgrade, or drift will reappear.
2. **No JS/CSS isolation in Option 1.** Module global leakage and Tailwind class collisions are
   possible. Acceptable short-term; Web Components (Phase 4) is the mitigation.
3. **Healthcare missing pages.** Some declared components were never built — Phase 2 needs a build-
   vs-trim decision per route (out of architecture scope; flag to module owner).
4. **`destroy()`/cleanup on route change.** `loadRoute()` currently doesn't call a page teardown;
   long-lived listeners/timers in module pages could leak. Define and wire an optional lifecycle.
5. **i18n loading.** Modules ship `i18n.js`; standardize when/how the SPA loads module translation
   bundles (currently ad hoc).
6. **Validation gate at install.** Decide where the manifest JSON Schema is enforced (CI, install
   API, or admin module-install UI) so a broken module is rejected before it reaches a tenant.
