# Module frontend — build-optional workflow

A module's frontend is **static-deployable** and loads at runtime; **building a module never
requires building the platform** (ADR: `plan/architecture/adr-module-frontend-integration.md`,
contract: `docs/modules/MODULE_FRONTEND_CONTRACT.md`).

There are two equally-valid ways to author a module page:

## 1. No-build (plain ES module)

Edit `frontend/module.js` (and `frontend/pages/*.js`) directly — plain ES modules using
`window.apiFetch` and the platform component library. nginx serves them as-is at
`/modules/<name>/...`. Nothing to build. This is the simplest path and the default template.

## 2. Build-optional (Lit + Vite)

For richer pages, author Lit custom elements in `frontend-src/` and compile them to
self-contained static bundles under `frontend/pages/`:

```bash
cd modules/template
npm install      # vite + lit, module-local; does NOT touch the platform
npm run build    # frontend-src/example-page.js -> frontend/pages/example-page.js (Lit inlined)
```

- Output is a plain ES `.js` (no SSR, no Node at request time, Lit bundled in) that nginx serves
  at `/modules/TEMPLATE/pages/example-page.js`.
- Base class `frontend-src/base-page.js` (`ModulePage`) renders into the **light DOM** so the
  platform's Tailwind classes, CSS variables and Phosphor icons apply.
- Reference the built bundle from a manifest route, e.g.:
  ```json
  { "path": "#/template/example", "name": "Example",
    "component": "pages/example-page.js",
    "menu": { "label": "Example", "icon": "ph-duotone ph-placeholder", "parent": "TEMPLATE" } }
  ```
  (`component` is relative to `frontend/` — never prefix it with `frontend/`.)

`node_modules/` and the generated `frontend/pages/` are git-ignored; commit `frontend-src/`,
`package.json`, `vite.config.js`, and (for a real module) run the build in CI or commit the
static output to `frontend/`.

## Manifest validation

Every manifest is validated against `docs/modules/module-manifest.schema.json` — the backend
(`core/module_system/manifest_validation.py`) logs contract violations on manifest sync, and the
client loader warns in dev. Keep those in sync with the schema.
