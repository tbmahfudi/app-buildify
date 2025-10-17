# Frontend Architecture Analysis

## Tech Stack & Entry Points

- Static HTML shell (`index.html`) loads Tailwind CSS, Bootstrap Icons, and mounts a vanilla JavaScript SPA into `#app`, delegating bootstrapping to a dedicated module loader (`assets/js/app-entry.js`) so markup stays free of inline scripts. 【F:frontend/index.html†L1-L17】【F:frontend/assets/js/app-entry.js†L1-L7】
- The authenticated experience is rendered from the reusable `main.html` template, which reuses the same module loader to initialize navigation, metadata-driven CRUD wiring, and Tailwind-styled shell chrome. 【F:frontend/assets/templates/main.html†L1-L84】【F:frontend/assets/js/app-entry.js†L1-L7】
- Login is a standalone Tailwind page whose layout is purely declarative; interactions now live in `assets/js/login-page.js`, which calls the shared `login` helper, persists tokens, and redirects to the SPA shell. 【F:frontend/assets/templates/login.html†L1-L88】【F:frontend/assets/js/login-page.js†L1-L27】【F:frontend/assets/js/api.js†L41-L63】

## Application Boot Sequence & Navigation
- `initApp` checks for a stored access token via the shared `tokens` helper, resolves the current user via `/auth/me`, persists them in `localStorage`, and falls back to the login page on failure, establishing a lightweight auth guard. 【F:frontend/assets/js/api.js†L1-L63】【F:frontend/assets/js/app.js†L9-L60】
- Sidebar navigation is data-driven through `config/menu.json`; menu links are constructed dynamically and styled to reflect the active hash route. 【F:frontend/assets/js/app.js†L66-L91】【F:frontend/config/menu.json†L1-L28】
- Routing is hash-based: templates are fetched from `/assets/templates/<route>.html`, injected into `#content`, and a `route:loaded` custom event is emitted so feature modules can self-initialize. 【F:frontend/assets/js/app.js†L94-L118】

## Data & Metadata Services
- `api.js` encapsulates token persistence, tenant scoping, and refresh-token retries, ensuring all downstream fetches inherit authorization headers automatically. 【F:frontend/assets/js/api.js†L1-L63】
- `data-service.js` provides CRUD helpers backed by `/data/*` endpoints, normalizing payload shapes for list pagination, single-record retrieval, mutation, and bulk actions. 【F:frontend/assets/js/data-service.js†L6-L108】
- `metadata-service.js` caches entity metadata in-memory, supports cache busting, and exposes permission helpers for role-aware UI decisions. 【F:frontend/assets/js/metadata-service.js†L6-L74】

## Metadata-Driven CRUD Framework
- `generic-entity-page.js` listens for entity routes (`companies`, `branches`, `departments`), shows a loading state, and instantiates an `EntityManager` per entity. 【F:frontend/assets/js/generic-entity-page.js†L1-L30】
- `EntityManager` orchestrates metadata retrieval, renders a Bootstrap card scaffold, binds action buttons, and coordinates a modal form plus a dynamic table. 【F:frontend/assets/js/entity-manager.js†L9-L209】
- `DynamicTable` builds sortable, paginated Bootstrap tables from metadata definitions and delegates row-level actions back to the manager. 【F:frontend/assets/js/dynamic-table.js†L7-L307】
- `DynamicForm` converts metadata field descriptors into validated Bootstrap form controls, supporting multiple field types and value normalization. 【F:frontend/assets/js/dynamic-form.js†L1-L286】

## Feature Modules
- `companies.js` now powers the Tailwind-styled companies CRUD screen, wiring modal toggles via data attributes, surfacing loading/empty states, and coordinating API calls without relying on Bootstrap. 【F:frontend/assets/js/companies.js†L1-L289】
- `settings.js` initializes once per route load, hydrates preference forms, gates tenant controls to admins, and emits Tailwind toast alerts when persisting user or tenant settings. 【F:frontend/assets/js/settings.js†L1-L299】
- The audit trail route instantiates `AuditWidget`, which fetches `/audit/list`, renders a Tailwind timeline with expandable change/context panels, and surfaces filtering plus pagination controls. 【F:frontend/assets/js/audit-page.js†L1-L23】【F:frontend/assets/js/audit-widget.js†L6-L400】

## UX Structure & Styling
- Tailwind drives the static layout, spacing, and modal presentation across templates, while legacy metadata-driven widgets still render Bootstrap-flavored markup—creating a hybrid layer that will gradually trend Tailwind-first as bespoke pages migrate. 【F:frontend/assets/templates/main.html†L14-L83】【F:frontend/assets/js/entity-manager.js†L9-L209】

## Tailwind-First Layout & Script Separation Strategy
- Consolidate Tailwind usage around a generated stylesheet (e.g., `postcss` + `tailwind.config.js`) so the CDN script can be replaced with purged, versioned CSS in `assets/css/app.css`, ensuring consistent theming across templates and widgets while improving load performance.
- Keep HTML templates presentational by routing all behavior through entry modules (`app-entry.js`, `login-page.js`) and feature scripts; when new routes emerge, follow the same pattern by exporting `attach`/`detach` hooks so layout files remain declarative.
- Move repeated layout primitives (nav, sidebar, cards) into Tailwind component partials or server-rendered includes, letting scripts target semantic IDs/data attributes rather than brittle class selectors.
- Introduce a lightweight bundler (Vite/Rollup) to compile the module graph, run Tailwind JIT, and emit cache-busted assets; this enforces the separation-of-concerns workflow while keeping the vanilla JS architecture intact.

## Opportunities & Risks
- Central routing lacks guardrails for missing templates beyond a simple "Page not found" message; adding route-to-template validation or fallback components would improve resilience. 【F:frontend/assets/js/app.js†L100-L118】
- The coexistence of bespoke Tailwind CRUD (`companies.js`) and metadata-driven Bootstrap CRUD (`EntityManager`) signals an in-progress migration—auditing route collisions and consolidating patterns would reduce duplication. 【F:frontend/assets/js/generic-entity-page.js†L10-L30】【F:frontend/assets/js/companies.js†L1-L289】
- `apiFetch` retries once on 401 but does not synchronize token refresh across tabs; incorporating a shared refresh lock or broadcast channel would prevent race conditions. 【F:frontend/assets/js/api.js†L20-L37】
- UI modules rely on global DOM queries and assume template structure; adopting a component registry or lightweight framework could curb fragility as templates evolve. 【F:frontend/assets/js/entity-manager.js†L33-L209】【F:frontend/assets/js/audit-widget.js†L62-L333】
