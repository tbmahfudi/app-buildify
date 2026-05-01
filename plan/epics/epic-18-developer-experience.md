# Epic 18 — Developer Experience & Module SDK

> Tools, conventions, and documentation enabling developers to build and distribute modules on the platform.

---

## Feature 18.1 — Module Development SDK `[DONE / PARTIAL]`

### Story 18.1.1 — Module Manifest Specification `[IN-PROGRESS]`

#### Backend
*As an API, I want a well-defined manifest schema validated at registration time, so that malformed modules are rejected early with clear error messages.*
- Manifest fields: `name`, `display_name`, `version` (semver), `module_type` (`code`/`nocode`), `category`, `api_prefix`, `permissions[]`, `menu_items[]`, `routes[]`, `event_subscriptions[]`, `dependencies[]`
- `POST /api/v1/modules/register` validates against Pydantic schema; returns structured errors: `{field: "permissions[0].code", error: "Permission code must match pattern resource:action:scope"}`
- Versioning enforced: re-registering an existing `name` with a new semver updates the record; downgrade (lower semver) returns 400

#### Frontend
*As a module developer, I want to read a clear reference document that shows exactly what each manifest field does with examples, so that I can write a correct manifest without trial and error.*
- Route: `#/modules` → module catalog page; "Developer Docs" link in page-header toolbar triggers docs modal
- Layout addition (page-header): FlexToolbar — (existing controls) | "Developer Docs" FlexButton(ghost)

- `DeveloperDocsModal` FlexModal(size=lg):
  - body: FlexTabs — Reference | Validate | Examples
    - Reference tab: structured table — Field | Type | Required | Description | Example (one row per manifest field)
    - Validate tab: JSON FlexTextarea (paste manifest) + "Validate" FlexButton(ghost) | result area (per-field errors or FlexAlert(type=success) "✓ Valid manifest")
    - Examples tab: side-by-side code blocks — code module `manifest.json` | nocode module `manifest.json`
  - footer: Close FlexButton

- Interactions:
  - click "Developer Docs": opens DeveloperDocsModal on Reference tab
  - paste JSON + click "Validate": POST /modules/validate → result area renders errors or success
  - switch tabs: content swaps; no API calls on Reference or Examples tabs

---

### Story 18.1.2 — Base Module Class `[DONE]`

#### Backend
*As a module developer, I want a `BaseModule` abstract class that handles authentication, RBAC, and tenant context automatically, so that I only write business logic.*
- `BaseModule` (in `backend/app/core/module_system/base_module.py`) provides:
  - `get_current_tenant_id(request)` — extracts tenant ID from JWT
  - `require_permission(code)` — FastAPI dependency factory; same as core platform
  - `get_db()` — SQLAlchemy session with tenant context pre-applied
  - `publish_event(event_type, payload)` — wraps `EventPublisher`
- Module developer subclasses `BaseModule`, overrides `get_router()` returning a FastAPI `APIRouter`
- `BaseModule.register(app)` mounts the router at the configured `api_prefix`

#### Frontend
*As a module developer building a frontend page for my module, I want to follow a documented file structure and reuse the platform's `apiFetch()` and `hasPermission()` utilities, so that my module's UI integrates seamlessly.*
- No dedicated route — module frontend conventions are a developer guide concern; documented in `docs/modules/MODULE_FRONTEND_GUIDE.md`

- Required module file structure:
  - `module.js` — exports `onActivate(router)` and `onDeactivate()` hooks
  - `pages/` — one file per page; each exports a `render(container)` function
  - `i18n/` — locale files per language (see Epic 16)
- `onActivate` hook calls `router.register({path, handler})` for each page
- Module pages import `apiFetch` from `core/api.js` and `hasPermission` from `core/auth-service.js`

---

### Story 18.1.3 — Event Bus Integration for Modules `[DONE]`

#### Backend
*As an API, I want modules to subscribe to platform events via their manifest and handle them in a registered callback, so that inter-module communication is decoupled.*
- Manifest `event_subscriptions`: `[{"event_type": "tenant.created", "handler": "on_tenant_created"}]`
- `ModuleRegistryService` registers the handler function at module load time
- `EventSubscriber` polls `events` table for unprocessed events matching subscribed types and invokes registered handlers
- `EventPublisher.publish(event_type, payload, tenant_id)` available to any module handler

#### Frontend
*No specific frontend story — event bus is a backend concern. Module frontend reacts to state changes via standard API polling or the in-app notification system.*

---

## Feature 18.2 — API Documentation and Developer Tooling `[DONE / PLANNED]`

### Story 18.2.1 — Swagger/OpenAPI Interactive Documentation `[DONE]`

#### Backend
*As an API, I want auto-generated interactive documentation so that developers can explore endpoints without reading source code.*
- FastAPI generates OpenAPI 3.0 spec for all routes
- Swagger UI at `/api/docs`; Redoc at `/api/redoc`
- All routes annotated: `summary`, `description`, `tags`, `response_model`, `responses` (including error codes)
- JWT auth: "Authorize" button in Swagger accepts a Bearer token for authenticated requests

#### Frontend
*As a developer evaluating the platform, I want to open `/api/docs` in my browser and test any endpoint interactively with a real token, so that I can understand the API in minutes.*
- No dedicated route — Swagger UI at `/api/docs` is the primary interface; no custom platform UI needed
- Layout additions:
  - `#/admin` page: "View API Docs" FlexButton(ghost) in page-header → opens `/api/docs` in new tab
  - User menu: "API Docs" link for developer tenants → opens `/api/docs` in new tab

---

### Story 18.2.2 — API Reference Documentation `[IN-PROGRESS]`

#### Backend
*No backend story — this is a documentation artifact.*

#### Frontend
*No specific frontend story — the API reference is a markdown document consumed by developers.*
- No dedicated route — `docs/backend/API_REFERENCE.md` is a static document; no UI involved
- Documents all router groups with example `curl` requests and response bodies
- Dynamic entity endpoints documented with the correct `/records` suffix
- Response envelope: `{items: [], total: N, page: N, page_size: N, pages: N}`
- Error format: `{detail: string, code: string, errors?: [{field, message}]}`
- Note: "Swagger UI at `/api/docs` is always the authoritative and up-to-date reference"

---

### Story 18.2.3 — Module Development Guide `[PLANNED]`

#### Backend
*No backend story — this is a documentation artifact.*

#### Frontend
*As a third-party developer wanting to build a module, I want a step-by-step guide with a working example module, so that I can build and deploy my first module in under one day.*
- No dedicated route — documentation artifact; no UI involved
- Guide at `docs/modules/MODULE_DEVELOPMENT_GUIDE.md` — 7 sections:
  1. Prerequisites and directory structure
  2. Writing `manifest.json` (annotated example)
  3. Backend: subclassing `BaseModule`, endpoints, Alembic migrations
  4. Frontend: `module.js` structure, registering routes, platform utilities
  5. Event bus: subscribing and publishing events
  6. Testing: local dev setup with Docker Compose override
  7. Deployment: registering the module with the platform
- Example "Hello World" module in `modules/example/`: `manifest.json` + `backend/app/routers/hello.py` + `frontend/pages/hello.js`
- Guide ends with a pre-submission checklist: security, performance, and documentation requirements

---

### Story 18.2.4 — Seed and Example Data Scripts `[DONE]`

#### Backend
*As a developer, I want seed scripts that populate realistic demo data, so that local development has representative content from the first `make seed`.*
- `backend/app/seeds/` contains 30+ seed files; `seeds/main.py` runs them in dependency order
- Seed creates: 1 superadmin user, 5 tenant organizations (TechStart, FashionHub, MedCare, CloudWork, FinTech), companies/branches/departments per tenant, system roles and permissions, sample entities with published status
- Financial module seed: default Chart of Accounts + 3 sample invoices + 2 payments for each company
- Seeds are idempotent: `INSERT ... ON CONFLICT DO NOTHING` or existence checks before creation

#### Frontend
*As a developer running the platform locally for the first time, I want pre-populated demo credentials and an onboarding message on the login page, so that I can explore all features without any setup.*
- Route: `#/login` → login page; dev-mode banner shown only when `ENVIRONMENT=development`
- Layout addition (login page — below login form): FlexSection "Demo Credentials" — one row per seeded tenant: tenant name | email | FlexButton(ghost) "Fill"

- Interactions:
  - click "Fill" on a tenant row: email and password fields populated with that tenant's credentials; user clicks "Sign In" to complete login

- States:
  - dev-mode: "Demo Credentials" section visible; each tenant shows role summary (Admin / Manager / User)
  - production: section not rendered
