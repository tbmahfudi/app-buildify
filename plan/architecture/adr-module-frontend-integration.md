---
status: approved
author: B1 (Architect)
date: 2026-06-28
title: Dynamic module frontend integration (static-deployable micro-frontends)
supersedes: []
related: [adr-005-module-packaging-format.md, adr-010-public-portal-framework.md, arch-mod-template.md]
---

# ADR: Dynamic Module Frontend Integration

## Changelog / Revisions

- **rev2 (2026-06-28, B1)** — **Build step is now ACCEPTABLE.** The hard constraint relaxed from
  "no build" to "the *built output* must be static and deployable on any web server (nginx / Apache
  / S3 / CDN) with no SSR and no Node/server runtime at request time." A bundler like Vite that
  emits plain `.html/.js/.css` now fully satisfies the constraint. Consequently: re-evaluated and
  **re-ranked** all options (§3); **Web Components + Lit (build-optional)** is now the primary
  recommendation, replacing rev1's "standardized no-build ES module" pick; added §3.x updated
  comparison table; added a new **§7 Stakeholder Questions** answering, each in its own subsection,
  (Q1) *can a module use the platform CSS by default?*, (Q2) *can each module's frontend be
  developed independently?*, (Q3) *can it support the no-code functionality?*. Sections §1
  (current-state), §2 (requirements) and §6 (risks) are largely unchanged from rev1; §4/§5 updated
  to match the new recommendation. `status` remains `draft`.
- **rev1 (2026-06-28, B1)** — initial draft; recommended a standardized no-build manifest-driven ES
  module contract (Option 1) because a build step was then disallowed.

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

> **rev2 note on the relaxed constraint.** The constraint is now *static-deployable **output***, not
> *no-build*. So "needs a build" is no longer disqualifying — it is just one cost line among several.
> Vite `build` emits a directory of plain `index-*.js` / `*.css` / `*.html` assets that nginx (or the
> existing `/modules/{name}/...` alias) serves verbatim — no SSR, no Node at request time. Options 3,
> 4 and 5 are therefore re-scored *in scope*, and the ranking changes. The decisive differentiators
> become **isolation strength**, **no-code coexistence** (the existing `dynamic-route-registry` /
> `dynamic-form` pipeline must keep working), and **independent dev**, with build/operational cost as
> the main counterweight.

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

### Option 3 — **Web Components / Custom Elements (+ optional Lit, build-optional)** as the page contract  ⭐ rev2 PRIMARY
Page = a custom element `<healthcare-dashboard>`; SPA mounts it into `#app-content`. A page may be
authored as **plain vanilla** (no build) or with **Lit** (tiny ~5 KB base, compiled with Vite to a
static bundle). Shadow DOM is **opt-in per page**, not mandatory.
- **Pros:** framework-agnostic, native, static-deployable; **strongest isolation available** (opt-in
  Shadow DOM for CSS/DOM encapsulation); clean, standard lifecycle (`connectedCallback` /
  `disconnectedCallback` — solves the rev1 "no `destroy()`" gap); the element-mount contract is a
  *superset* of today's `new PageClass(); render()` call, so it **unifies hand-coded and no-code
  pages under one contract** (see §7.3); build is *optional* per module, so low-complexity modules
  stay no-build while complex ones may opt into Lit+Vite.
- **Cons (now manageable, not blocking):** Shadow DOM, when used, **does block Tailwind-via-CDN and
  the Phosphor icon font** (global stylesheets/`@font-face` don't pierce shadow boundaries). The
  practical answer (§7.1) is **light-DOM-by-default** (full platform Tailwind styling, zero ceremony)
  with shadow isolation as an explicit opt-out — so this con only applies to modules that *choose*
  isolation. Migrating existing pages to custom elements is mechanical but non-trivial.

### Option 4 — **Module Federation** (Vite remotes)
Runtime-loaded remote bundles with shared-dependency negotiation.
- **Pros:** mature micro-frontend isolation/versioning; **first-class independent deploys** and
  shared-dep dedup; remoteEntry is static-hostable (satisfies the relaxed constraint).
- **Cons:** introduces a **mandatory bundler/build per module AND a host build** (the platform shell
  itself must become a Federation host — a large change to a hash-routed vanilla SPA); heaviest
  conceptual + operational load; couples module and host build toolchains/versions; the no-code
  pipeline (plain runtime innerHTML rendering, no bundle) does **not** map onto a remoteEntry, so
  no-code pages would need a parallel path. **Power exceeds the need; rejected as primary.**

### Option 5 — **Single shared framework (Preact/Vue) + Vite** for all module pages
Adopt one app framework and a Vite build that emits static JS/CSS.
- **Pros:** good DX; fully static (no SSR) output.
- **Cons:** forces **one framework on every module team** (the opposite of framework-agnostic
  independent dev); a mandatory build for *every* module including trivial ones; two rendering
  paradigms during migration; does not itself provide isolation. Lit (Option 3) gives the framework
  ergonomics *without* mandating it platform-wide, so Option 5 is dominated by Option 3.

### Comparison (rev2 — build now allowed)

| Criteria | 1. Std ES-module | 2. Import maps | **3. Web Components (+Lit)** | 4. Module Federation | 5. Framework+Vite |
|---|---|---|---|---|---|
| Static-deployable output (no SSR) | Yes | Yes | **Yes** | Yes (remotes) | Yes |
| Build required | No build | No build | **Optional** (per module) | **Mandatory** (module + host) | **Mandatory** (all modules) |
| Isolation (CSS/JS) | Weak | Weak | **Strong (opt-in Shadow), light DOM default** | Strong | Medium |
| Q1 — platform CSS by default | Yes (light DOM, but no isolation option) | Yes | **Yes by default (light DOM); opt-out to shadow** | Awkward | Yes |
| Q2 — independent dev | Partial (URL contract) | Partial | **Yes (own repo/Vite, custom-element contract)** | **Yes (remotes)** | Partial |
| Q3 — no-code coexistence | Coexists (separate path) | Coexists | **Unifies (no-code wraps as element)** | Parallel path needed | Coexists |
| Lifecycle / teardown | Manual | Manual | **Native (`disconnectedCallback`)** | Framework | Framework |
| Versioning | URL-based | URL-based | URL-based (+ bundle hash if built) | **First-class** | Bundle-based |
| RBAC fit (server menu/route) | **Native (unchanged)** | Native | **Native (unchanged)** | Needs glue | Native |
| Migration cost (this repo) | **Lowest** | Low | **Medium** (incremental, opt-in) | Very High | High |
| Operational / build cost | None | None | Low (build optional) | **High** | Medium-High |

---

## 4. Recommendation

**rev2: Adopt Option 3 — a Web-Components / custom-element page contract, build-optional, with Lit
as the recommended (but not mandated) authoring helper.** Keep **Option 1's manifest-driven loader
and the unchanged server-side RBAC menu pipeline** as the *delivery substrate* (the custom-element
contract rides on top of the existing manifest + `/modules/{name}/...` loading), and keep **Option 2
(import maps)** as an optional convenience for sharing `@platform/*` code.

Rationale under the relaxed constraint: the element-mount contract is a **superset** of today's
`new PageClass(); await page.render()` call — `loadRoute()` can `customElements`-mount instead — so
migration is *incremental and opt-in* rather than a rewrite; it gives the **strongest available
isolation** (opt-in Shadow DOM) while defaulting to **light DOM so platform Tailwind styling Just
Works** (§7.1); it provides a **native lifecycle** (`disconnectedCallback`) that fixes rev1's
teardown gap; and crucially it **unifies hand-coded module pages and no-code-generated pages under
one route/menu/component contract** (§7.3) instead of leaving them on divergent code paths. Module
Federation (Option 4) was rejected as primary because its mandatory host+module build and its poor
fit with the runtime no-code pipeline cost far more than the problem warrants; a single shared
framework (Option 5) was rejected because it forbids the framework-agnostic independent dev that
Option 3 preserves.

**Honest trade-off:** Option 3 introduces an *optional* Vite build for modules that opt into Lit or
Shadow-DOM-bundled CSS. That adds real operational surface — a per-module `package.json`, a build to
run in CI, and lockfile/dependency upkeep — that the platform does **not** have today. We mitigate
by making build strictly opt-in: a module can remain a no-build vanilla custom element and pay none
of that cost. Teams only adopt Vite when they want Lit ergonomics or shipped-in-shadow CSS.

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

---

## 7. Stakeholder Questions (rev2)

### 7.1 Q1 — "Can a module use the platform CSS by default?"

**Yes — by default, fully, with zero ceremony, because the recommended default is *light DOM*, not
Shadow DOM.**

The platform styles everything with **Tailwind utility classes delivered via CDN**
(`<script src="https://cdn.tailwindcss.com">` in `index.html`) plus the **Phosphor icon font**.
These are *global* stylesheets and an `@font-face` font. The well-known constraint with Web
Components is that **Shadow DOM blocks both**: Tailwind utility classes applied inside a shadow root
don't match (the global stylesheet doesn't cross the boundary), and the Phosphor `@font-face` isn't
visible inside the shadow tree. So if every module page were a *shadow* custom element, the answer
would be "no, not by default" — and that would be a regression from today.

The recommendation avoids that trap by making **light DOM the default**:

- **Default: light-DOM custom element (no `attachShadow`).** The element renders its markup into its
  own light children, so it lives in the *same* DOM/CSS scope as the shell. Every platform Tailwind
  class (`flex`, `text-gray-900`, `rounded-lg`, …) and every `ph-duotone ph-…` icon works exactly as
  it does in the existing `dynamic-route-registry` pages — which already render Tailwind-class
  `innerHTML` strings into a plain container. A module page gets the platform design system for
  free, identical to a current `AccountsPage`. **This is the default, opt-out story the stakeholder
  asked for.**

- **Opt-out: shadow isolation, with three ways to still inherit the design system** for a module that
  *deliberately* wants DOM/CSS encapsulation:
  1. **Shared design tokens via CSS custom properties.** CSS custom properties **do** inherit across
     shadow boundaries. We expose platform tokens (`--color-primary`, `--radius`, `--space-*`, font
     family, etc.) on `:root`; a shadowed module reads them with `var(--color-primary)` and stays
     on-brand without needing the global stylesheet.
  2. **`adoptedStyleSheets` (constructable stylesheets) — the recommended mechanism.** Ship a single
     shared, parsed `CSSStyleSheet` (a compiled platform/Tailwind base) and *adopt* it into each
     shadow root: `shadowRoot.adoptedStyleSheets = [platformSheet]`. One parsed sheet is shared by
     all shadow roots (no duplication), giving shadowed modules the platform utilities **inside** the
     boundary. This is the practical answer to "Tailwind won't pierce shadow" — you don't pierce it,
     you *adopt* a built Tailwind sheet into each root.
  3. **`::part` / exposed parts** for cases where the *shell* needs to theme into a module element.
- **Icons inside shadow:** because the Phosphor `@font-face` is global, shadowed modules either keep
  icons in light-DOM slots, adopt the Phosphor stylesheet via `adoptedStyleSheets`, or use inline SVG
  icons. Light-DOM modules need none of this.

**Net default + opt-out:** *By default a module uses the platform CSS (light DOM, Tailwind-CDN
classes work verbatim, like the no-code pages do today). A module may opt into Shadow-DOM isolation;
when it does, it opts into the platform design system via shared design tokens + an adopted Tailwind
base stylesheet (`adoptedStyleSheets`), not via the global CDN sheet.* Because Tailwind is still CDN
today, the immediate practical posture is **light-DOM-by-default**; the adopted-stylesheet path
becomes relevant only once a module ships a built Tailwind sheet for its shadow root.

### 7.2 Q2 — "Can each module's frontend be developed independently?"

**Yes.** The contract is a thin, stable boundary that a module team can build, test, version and
deploy without touching the platform repo or any other module.

- **Repo layout — both supported.** The runtime contract is "static files served under
  `/modules/{name}/frontend/...`", so the *source* can live either (a) **in-repo** at
  `modules/<name>/frontend/` (today's layout; simplest), or (b) in a **separate repo** whose CI
  produces a `frontend/dist/` that is dropped into the same on-disk location at install/upgrade. The
  platform doesn't care which — it only loads URLs.
- **Independent build.** A module owns its own (optional) `package.json` + `vite.config`. `vite build`
  emits hashed static assets (`pages/dashboard-*.js`, `*.css`) under the module's `frontend/` tree.
  No platform build is involved; no shared lockfile. A no-build module skips this entirely.
- **The runtime contract the platform loads them by** (the actual boundary):
  1. The module ships a `manifest.json` declaring `navigation.menu_items` (parents+icons) and
     `routes[]` (path, `component` path relative to `frontend/`, `menu.parent`, `permission`).
  2. Each declared `component` exports either today's `{ constructor(); async render() }` page class
     **or** a **custom element** (`customElements.define('mod-foo-dashboard', …)` with a tag named in
     the route). The shell mounts whichever it finds — both are honored, so adoption is per-page.
  3. The platform discovers enabled modules at runtime via `GET /module-registry/enabled/names` and
     loads each one's manifest + components on demand (`module-loader.js`). Nothing is hard-wired in
     `app.js`.
- **Versioning.** Per-module: the manifest carries `version`; built assets are content-hashed; the
  module record in the DB tracks the installed version. Modules version and deploy on their own
  cadence; the platform only requires manifest-schema compatibility.
- **Boundary discipline.** A module team must NOT reach into platform internals beyond the published
  `@platform/*` import-map specifiers (`@platform/api`, `@platform/ui`) and the documented page/
  element interface. That keeps platform refactors from breaking modules and vice-versa.

So a module team can: clone only their module, `vite build` (or not), run it against any deployed
platform, bump their manifest `version`, and ship `frontend/` — no platform-repo PR, no coordination
with other module teams.

### 7.3 Q3 — "Can it support the no-code functionality?" (most important)

**Yes — and the recommended model *unifies* hand-coded and no-code-generated pages rather than
bolting a second pipeline alongside them. The no-code pipeline is preserved unchanged and is, in
fact, the template for how module pages should register.**

How no-code works today (verified): `dynamic-route-registry.js` registers all published entities at
startup (`registerAllPublishedEntities()` → `GET /data-model/entities?status=published`), and at
route time `loadRoute()` calls `dynamicRouteRegistry.handleRoute(route, content)` **first** (app.js
line ~1687) for any `#/dynamic/{entity}/{list|create|{id}|{id}/edit}` URL. It fetches entity
metadata (`/metadata/entities/{entity}`) and renders CRUD UI by composing `DynamicTable` and
`DynamicForm` — which build their UI from metadata produced by `runtime_model_generator.py` /
`dynamic_entity_service.py`. The whole thing renders **Tailwind-class innerHTML into a plain
container — i.e. light DOM, no build, no Shadow DOM.** That is exactly the recommended *default* mode
for module pages (§7.1), so the two are natively compatible.

Concretely, the chosen approach supports no-code three ways:

1. **No-code pages surfaced as module frontends.** A no-code-generated CRUD page is just a renderer
   that writes Tailwind markup into a container. Wrapping it as the standard contract is mechanical:
   a generic `<nocode-entity-page entity="customers" action="list">` light-DOM custom element whose
   `connectedCallback()` delegates to the existing `dynamicRouteRegistry.handleRoute(...)`/
   `DynamicTable`/`DynamicForm` code. No-code thus emits **the same kind of artifact** module pages
   emit, under the same route/menu/component contract — `loadRoute()`'s existing "try dynamic first"
   branch becomes one registered route family instead of a special-case `if`.

2. **A module can be PARTLY no-code and PARTLY hand-coded.** Because the contract is per-route, a
   single module's `manifest.routes[]` can mix: some routes point at **auto-generated** entity CRUD
   (`component` = the generic no-code element, parameterized by entity name from metadata), while
   others point at **hand-coded** custom-element pages (e.g. a bespoke `<healthcare-clinic-board>`).
   They share one menu tree, one RBAC gate, and one mount mechanism. A team scaffolds CRUD for free
   and hand-writes only the screens that need bespoke logic.

3. **The no-code builder emits/registers module pages the same way.** The no-code Data-Model designer
   (`nocode-data-model.js`) already has "create page / add entity to menu" quick actions. Under this
   model those actions emit a route entry in the **same** shape (`path` + `component` +
   `menu.parent` + `permission`) that a hand-coded module route uses — so a generated page flows
   through the identical menu (`menu_service._get_module_menu_items`, RBAC-filtered) and routing
   path. One contract, one renderer interface, two producers (human and builder).

**Non-breakage guarantee.** The recommendation does **not** require touching
`dynamic-route-registry.js`, `dynamic-form.js`, or any backend metadata/`data-model` router. The
"try dynamic route first" branch in `loadRoute()` stays; the custom-element mount is *added* as an
alternative to `new PageClass(); render()` at the module-route branch (line ~1994), which is a
superset of the current call. Light-DOM default means no-code's Tailwind output keeps rendering
verbatim. The unification is an *additive* convergence onto one component contract — it cannot
bypass or regress the no-code pipeline because it literally reuses it.
