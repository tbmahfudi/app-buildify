# Epic 13 — Security & Compliance

> Platform-level and per-tenant security hardening: audit logging, re-authentication, security headers, rate limiting, metrics, and test coverage.

---

## Feature 13.1 — Audit Logging `[DONE]`

### Story 13.1.1 — Comprehensive Audit Trail `[DONE]`

#### Backend
*As an API, I want every significant action written to an append-only audit log, so that all activity is traceable for compliance.*
- `AuditService.log(event_type, actor_user_id, tenant_id, resource_type, resource_id, action, changes, ip, user_agent)` called after every auth event, RBAC change, and data operation
- `audit_logs` table has no UPDATE/DELETE grants in application code; INSERT only
- `GET /api/v1/audit?event_type=&actor_id=&resource_type=&from=&to=&page=&page_size=` for filtered queries

#### Frontend
*As a compliance officer on the audit trail page, I want to search and filter the audit log by user, action type, date range, and resource, and see exactly what changed in each event, so that I can produce evidence of system activity for an audit.*
- Route: `#/audit` renders `audit.html` + `audit-enhanced.js`
- Filter bar: Actor (user search select), Action Type (multi-select checkboxes), Resource Type (select), Date Range (date range picker), Status (Success/Failure/All)
- Audit table: Timestamp | Actor | Action | Resource | Status | IP Address
- Expanding a row shows: full `changes` JSON diff rendered as a colored key-value diff table (old value struck through in red, new value in green)
- "Export Audit Log" button exports the current filtered view as CSV
- Entries are read-only; no edit or delete actions available in the UI

---

### Story 13.1.2 — Entity-Level Audit Logging `[DONE]`

#### Backend
*As an API, I want entity records with `is_audited = true` to log every create, update, and delete with field-level diffs, so that custom data changes are traceable.*
- `DynamicEntityService` calls `AuditService.log()` after each write on audited entities
- Update entries: `changes` contains only modified fields: `{field: {old: value, new: value}}`

#### Frontend
*As a user on a record detail page for an audited entity, I want a "Change History" tab showing who changed what and when, so that I can track how the record evolved.*
- Record detail page "Change History" tab (only visible on entities with `is_audited = true`)
- Timeline of changes: each entry shows timestamp, actor name, and the specific fields that changed
- Changed fields rendered as: "Status: Draft → Posted" or "Amount: $100 → $150"
- "View full audit entry" link opens the audit log page filtered to this specific record

---

## Feature 13.2 — Security Policies `[DONE]`

### Story 13.2.1 — Per-Tenant Security Policy Configuration `[DONE]`

#### Backend
*As an API, I want per-tenant security policy overrides so that each tenant can set their own security requirements.*
- `SecurityPolicy` table: one row per tenant (+ platform default with `tenant_id = NULL`)
- `PUT /api/v1/admin/security/policies/{tenant_id}` (superadmin) and `PUT /api/v1/settings/security` (tenant admin for own tenant)
- Tenant policy overrides platform defaults; missing tenant policy falls back to platform defaults

#### Frontend
*As a tenant administrator on the security settings page, I want a single page with tabbed sections for Password Policy, Account Lockout, and Session Policy, with clear labels and sensible defaults, so that I can configure our security posture without reading documentation.*
- Route: `#/settings/security` renders security policy settings with 3 tabs:
  - **Password Policy** tab: all password rules as toggles + number inputs (min length, max length, expiry days, warning days, grace logins, history count)
  - **Account Lockout** tab: max attempts (number), lockout type radio (Progressive/Fixed), lockout duration (number + unit select), reset window (number + unit)
  - **Session Policy** tab: idle timeout (number + unit), absolute timeout (number + unit), max concurrent sessions (number), single session mode toggle
- Each setting has a help tooltip (?) explaining the impact
- "Reset to Defaults" button restores the platform default values for that tab (with confirmation)
- Unsaved changes indicator per tab; "Save [Tab Name] Policy" button per tab (not global save, to reduce risk of accidental bulk changes)

---

### Story 13.2.2 — Sensitive Operation Re-Authentication `[DONE]`

#### Backend
*As an API, I want certain operations to require the user to re-enter their password if their token is older than a threshold, so that session hijacking cannot cause irreversible damage.*
- `require_reauth` dependency added to sensitive routes (bulk delete, role changes, tenant suspension, etc.)
- If `token_age > reauth_window_minutes`: returns 403 with `{code: "REAUTH_REQUIRED", token_age_minutes: N}`
- `POST /api/v1/auth/reauth` accepts `{password}` and issues a short-lived `reauth_token` (valid for 5 minutes, single-use)

#### Frontend
*As a user trying to delete multiple records, I want the system to ask me to confirm my password if I haven't entered it recently, so that I'm prompted to consciously authorize destructive actions.*
- When any API call returns 403 with `REAUTH_REQUIRED`: a `FlexModal` intercepts the response
- Modal: "Please confirm your password to continue" + password `FlexInput` + "Confirm" button
- On correct password: the original request is retried with the `reauth_token` header; modal closes transparently
- On wrong password: modal shakes, input clears, "Incorrect password. Try again." message shown
- Re-auth event logged in the audit trail with the action that triggered it

---

### Story 13.2.3 — Security Headers Middleware `[DONE]`

#### Backend
*As an API, I want standard security headers on all HTTP responses, so that browser-based attacks are mitigated.*
- `SecurityMiddleware` adds: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Content-Security-Policy`, `Strict-Transport-Security` (in production)
- CSP: `default-src 'self'; script-src 'self' cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' cdn.tailwindcss.com; font-src https://fonts.gstatic.com;`

#### Frontend
*As a security engineer, I want to verify that all required headers are present on every response, so that the platform passes a security header scan without manual configuration.*
- No specific UI needed for header enforcement — it's transparent to users
- Admin security overview page `#/settings/security` → "Security Headers" section shows a checklist of required headers with green checkmarks when detected from a test probe
- "Run Security Check" button performs a self-probe via `GET /api/v1/admin/security/headers-check` and renders the results

---

### Story 13.2.4 — Rate Limiting `[DONE]`

#### Backend
*As an API, I want per-IP rate limiting on all endpoints, so that brute-force attacks and abusive clients are throttled.*
- SlowAPI: login endpoints limited to 10 req/min per IP; general API endpoints to 100 req/min per IP
- Rate-limited requests return 429 with `Retry-After` header
- Limit configurable via `RATE_LIMIT_PER_MINUTE` env var

#### Frontend
*As a developer integrating with the API, I want rate limit information shown in the browser's network tab and also surfaced in a dev overlay, so that I can monitor API consumption during development.*
- `api.js` captures `X-RateLimit-Remaining` response headers and stores them in memory
- Dev-mode overlay (activated by `?debug=1` URL param): floating panel showing current requests-per-minute usage and remaining quota
- On 429: global toast "Request limit reached. Retrying in X seconds" with a countdown; queued requests auto-retry after `Retry-After` seconds

---

## Feature 13.3 — Prometheus Metrics `[PLANNED]`

### Story 13.3.1 — Prometheus `/metrics` Endpoint `[PLANNED]`

#### Backend
*As an API, I want a Prometheus-compatible `/metrics` endpoint exposing HTTP and application metrics, so that platform health can be monitored with standard tooling.*
- `prometheus-client` `make_asgi_app()` mounted at `/metrics`; protected by IP allowlist or bearer token
- Counters: `http_requests_total{method, path, status}`; Histograms: `http_request_duration_seconds{method, path}`
- Gauges: `active_sessions_total`, `db_pool_size`, `db_pool_available`, `notification_queue_length`

#### Frontend
*As a DevOps engineer, I want a system health page in the admin panel that shows live metrics pulled from the Prometheus endpoint, so that I can check platform health without opening Grafana.*
- Route: `#/admin/health` (superadmin only) shows: uptime, requests/sec (last 5 min), error rate %, active sessions, DB pool utilization bar
- Metrics polled every 30 seconds via `GET /api/v1/admin/metrics`
- Each metric rendered as a mini chart (sparkline, last 10 data points)
- Red threshold indicators: error rate > 5% shows in red; DB pool > 90% shows in amber

---

### Story 13.3.2 — Grafana Dashboard Template `[PLANNED]`

#### Backend
*As a DevOps engineer, I want a Grafana provisioning file that auto-configures a platform dashboard, so that observability is set up automatically.*
- `infra/grafana/dashboards/app-buildify.json` — Grafana dashboard JSON
- `infra/grafana/provisioning/` — datasource and dashboard provisioning YAML
- `infra/docker-compose.dev.yml` adds `grafana` and `prometheus` services

#### Frontend
*No frontend story — Grafana is a separate tool. The health page (Story 13.3.1) serves as the in-product equivalent.*

---

## Feature 13.4 — Test Coverage `[IN-PROGRESS]`

### Story 13.4.1 — Backend Unit and Integration Test Suite `[IN-PROGRESS]`

#### Backend
*As a developer, I want backend tests covering all critical paths at 80%+ line coverage, so that regressions are caught in CI before reaching production.*
- `pytest` + `pytest-asyncio` + `httpx` `TestClient`; fixtures in `tests/conftest.py`
- Unit tests: `DynamicQueryBuilder` (filter/sort/aggregate query generation), `PasswordValidator`, `AutomationService`, `WorkflowService`
- Integration tests: full auth flow (login → refresh → logout), RBAC permission evaluation, dynamic entity publish + CRUD lifecycle, financial invoice cycle

#### Frontend
*No specific frontend story — test execution is a CI concern. Coverage reports viewed in CI artifacts.*

---

### Story 13.4.2 — Frontend Component Test Coverage `[IN-PROGRESS]`

#### Backend
*No backend story — this is purely a frontend concern.*

#### Frontend
*As a frontend developer, I want Vitest tests for all 30 Flex components, so that component regressions are caught before they affect users.*
- Currently tested: `FlexAccordion`, `FlexCheckbox`, `FlexInput`, `FlexRadio`, `BaseComponent`
- Remaining components needing tests: `FlexModal`, `FlexDrawer`, `FlexTable`, `FlexDataGrid`, `FlexSelect`, `FlexTextarea`, `FlexStack`, `FlexGrid`, `FlexSidebar`, `FlexStepper`, `FlexPagination`, `FlexAlert`, `FlexButton`, `FlexBadge`, `FlexDropdown`, `FlexTabs`, `FlexTooltip`, `FlexSpinner`, `FlexBreadcrumb`, `FlexCard`
- Each test file covers: renders with default props, renders with all variants, emits expected events on interaction, shows error state correctly
- Coverage threshold enforced in `vitest.config.js`: 80% statements/functions/lines, 75% branches
