# Epic 18 — Developer Experience & Module SDK

> Tools, conventions, and documentation enabling developers to build and distribute modules on the platform.

---

## Feature 18.1 — Module Development SDK `[DONE / PARTIAL]`

### Story 18.1.1 — Module Manifest Specification `[DONE]`

#### Backend
*As an API, I want a well-defined manifest schema validated at registration time, so that malformed modules are rejected early with clear error messages.*
- Manifest fields: `name`, `display_name`, `version` (semver), `module_type` (`code`/`nocode`), `category`, `api_prefix`, `permissions[]`, `menu_items[]`, `routes[]`, `event_subscriptions[]`, `dependencies[]`
- `POST /api/v1/modules/register` validates against Pydantic schema; returns structured errors: `{field: "permissions[0].code", error: "Permission code must match pattern resource:action:scope"}`
- Versioning enforced: re-registering an existing `name` with a new semver updates the record; downgrade (lower semver) returns 400

#### Frontend
*As a module developer, I want to read a clear reference document that shows exactly what each manifest field does with examples, so that I can write a correct manifest without trial and error.*
- Module catalog page `#/modules` has a "Developer Docs" link opening the manifest spec in a modal
- Manifest spec rendered as a structured reference table: Field | Type | Required | Description | Example
- "Validate Manifest" tool in the modal: paste JSON → "Validate" button → shows per-field errors or "✓ Valid manifest"
- Example `manifest.json` shown for both code modules and nocode modules side-by-side

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
- Module frontend structure documented in `docs/modules/MODULE_FRONTEND_GUIDE.md`:
  - `module.js` — exports `onActivate(router)` and `onDeactivate()` hooks
  - `pages/` — one file per page; each exports a `render(container)` function
  - `i18n/` — locale files per language (see Epic 16)
- `module.js` `onActivate` hook receives the router instance; calls `router.register({path, handler})` for each page
- Module pages import `apiFetch` from `core/api.js` and `hasPermission` from `core/auth-service.js` using relative paths

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
- The Swagger UI is the primary API reference — no custom UI needed
- Admin settings page `#/admin` has a "View API Docs" button that opens `/api/docs` in a new tab
- The API docs link is also available in the user menu for developer tenants

---

### Story 18.2.2 — API Reference Documentation `[DONE]`

#### Backend
*No backend story — this is a documentation artifact.*

#### Frontend
*No specific frontend story — the API reference is a markdown document consumed by developers.*
- `docs/backend/API_REFERENCE.md` documents all router groups with example `curl` requests and response bodies
- Dynamic entity endpoints documented with the correct `/records` suffix (not `/records/{id}`)
- Response envelope shape documented: `{items: [], total: N, page: N, page_size: N, pages: N}`
- Error format documented: `{detail: string, code: string, errors?: [{field, message}]}`
- A note states: "Swagger UI at `/api/docs` is always the authoritative and up-to-date reference"

---

### Story 18.2.3 — Module Development Guide `[PLANNED]`

#### Backend
*No backend story — this is a documentation artifact.*

#### Frontend
*As a third-party developer wanting to build a module, I want a step-by-step guide with a working example module, so that I can build and deploy my first module in under one day.*
- Guide at `docs/modules/MODULE_DEVELOPMENT_GUIDE.md` covers:
  1. Prerequisites and directory structure
  2. Writing `manifest.json` (with annotated example)
  3. Backend: subclassing `BaseModule`, writing endpoints, adding Alembic migrations
  4. Frontend: `module.js` structure, registering routes, using platform utilities
  5. Event bus: subscribing to events, publishing events
  6. Testing: local dev setup with Docker Compose override file
  7. Deployment: registering the module with the platform
- A minimal working "Hello World" module in `modules/example/`:
  - `manifest.json`: declares one menu item and one permission
  - `backend/app/routers/hello.py`: one `GET /hello` endpoint returning `"Hello from {tenant_name}"`
  - `frontend/pages/hello.js`: renders "Hello, [User Name]!" on a page
- Guide includes a checklist: "Before you submit your module" with security, performance, and documentation requirements

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
- Login page dev-mode banner (shown only when `ENVIRONMENT=development`): "Demo credentials" section showing all 5 seeded tenants with their email + password pre-fill buttons
- Clicking a pre-fill button fills the email and password fields; one more click to log in
- Each seeded tenant has a different role set (admin, manager, regular user) so developers can test RBAC
