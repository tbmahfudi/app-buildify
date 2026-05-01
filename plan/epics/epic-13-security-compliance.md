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
- Route: `#/audit` → `audit.html` + `audit-enhanced.js`
- Layout: FlexStack(direction=vertical) > page-header, filter-bar, audit-grid
  - page-header: FlexToolbar — "Audit Trail" title | "Export Audit Log" FlexButton(ghost)
  - filter-bar: FlexCluster — Actor (FlexSelect, user search) | Action Type (FlexSelect, multi-select) | Resource Type (FlexSelect) | Date Range (FlexDatepicker pair) | Status (FlexRadio: All / Success / Failure)
  - audit-grid: FlexDataGrid(server-side, expandable-rows) — Timestamp | Actor | Action | Resource | Status FlexBadge | IP Address

- `AuditGrid` expanded row:
  - `changes` JSON diff rendered as a colored key-value table: old value (strikethrough, red) → new value (green) per field
  - read-only; no edit or delete actions

- Interactions:
  - change any filter field: GET /audit?params → audit-grid refreshes
  - click row expand chevron: expanded row shows changes diff table
  - click "Export Audit Log": GET /audit?format=csv (with current filters) → CSV download

- States:
  - loading: audit-grid shows skeleton rows while fetch resolves
  - empty: "No audit entries match the selected filters"
  - error: FlexAlert(type=error) "Could not load audit log. Retry?"

---

### Story 13.1.2 — Entity-Level Audit Logging `[DONE]`

#### Backend
*As an API, I want entity records with `is_audited = true` to log every create, update, and delete with field-level diffs, so that custom data changes are traceable.*
- `DynamicEntityService` calls `AuditService.log()` after each write on audited entities
- Update entries: `changes` contains only modified fields: `{field: {old: value, new: value}}`

#### Frontend
*As a user on a record detail page for an audited entity, I want a "Change History" tab showing who changed what and when, so that I can track how the record evolved.*
- Route: `#/dynamic/{entity}/{id}` → record detail page; "Change History" FlexTabs tab (visible only when entity has `is_audited = true`)
- Layout addition: FlexTabs tab body — FlexStack(direction=vertical) > change-timeline, view-full-link
  - change-timeline: vertical timeline — one node per change entry: timestamp | actor name | changed-fields list
  - changed-fields: each field rendered as "Field Name: old value → new value"
  - view-full-link: "View full audit entry" link at bottom

- Interactions:
  - click "Change History" tab: GET /audit?resource_type={entity}&resource_id={id} → timeline renders
  - click "View full audit entry": navigates to `#/audit` filtered to this specific record

- States:
  - loading: timeline shows skeleton nodes while fetch resolves
  - empty: "No changes recorded yet"

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
- Route: `#/settings/security` → `settings.html` + `settings-page.js` (Security tab)
- Layout: FlexStack(direction=vertical) > page-header, policy-tabs
  - page-header: FlexToolbar — "Security Settings" title
  - policy-tabs: FlexTabs — Password Policy | Account Lockout | Session Policy

- `PasswordPolicyTab`:
  - fields (each with FlexTooltip(?) help icon): Min Length (FlexInput, type=number) | Max Length (FlexInput, type=number) | Expiry Days (FlexInput, type=number) | Warning Days (FlexInput, type=number) | Grace Logins (FlexInput, type=number) | History Count (FlexInput, type=number) | complexity toggles (FlexCheckbox per rule)
  - footer: unsaved-indicator FlexBadge(color=warning) "Unsaved changes" | "Reset to Defaults" FlexButton(ghost) | "Save Password Policy" FlexButton(primary)

- `AccountLockoutTab`:
  - fields: Max Attempts (FlexInput, type=number) | Lockout Type (FlexRadio: Progressive / Fixed) | Lockout Duration (FlexInput, type=number) + unit FlexSelect | Reset Window (FlexInput, type=number) + unit FlexSelect
  - footer: same pattern as Password Policy tab

- `SessionPolicyTab`:
  - fields: Idle Timeout (FlexInput, type=number) + unit FlexSelect | Absolute Timeout (FlexInput, type=number) + unit FlexSelect | Max Concurrent Sessions (FlexInput, type=number) | Single Session Mode (FlexCheckbox toggle)
  - footer: same pattern

- Interactions:
  - change any field on a tab: unsaved-indicator appears on that tab
  - click "Reset to Defaults": FlexModal(size=sm) confirm → GET /settings/security/defaults → tab fields repopulate
  - click "Save [Tab] Policy": PUT /settings/security with tab-scoped payload → success toast; unsaved-indicator clears

- States:
  - loading: tab fields show skeleton while GET /settings/security resolves
  - unsaved: unsaved-indicator FlexBadge visible on active tab

---

### Story 13.2.2 — Sensitive Operation Re-Authentication `[IN-PROGRESS]`

#### Backend
*As an API, I want certain operations to require the user to re-enter their password if their token is older than a threshold, so that session hijacking cannot cause irreversible damage.*
- `require_reauth` dependency added to sensitive routes (bulk delete, role changes, tenant suspension, etc.)
- If `token_age > reauth_window_minutes`: returns 403 with `{code: "REAUTH_REQUIRED", token_age_minutes: N}`
- `POST /api/v1/auth/reauth` accepts `{password}` and issues a short-lived `reauth_token` (valid for 5 minutes, single-use)

#### Frontend
*As a user trying to delete multiple records, I want the system to ask me to confirm my password if I haven't entered it recently, so that I'm prompted to consciously authorize destructive actions.*
- No dedicated route — re-auth FlexModal is a global interceptor in `api.js`; triggered by any 403 `REAUTH_REQUIRED` response

- `ReauthModal` FlexModal(size=sm, dismissable=false):
  - body: "Please confirm your password to continue" | Password (FlexInput, type=password, autofocus)
  - footer: Cancel | "Confirm" FlexButton(primary)

- Interactions:
  - any API response with 403 `REAUTH_REQUIRED`: ReauthModal opens; original request queued
  - click "Confirm": POST /auth/reauth {password} → on success: original request retried with `reauth_token` header; modal closes transparently
  - incorrect password: modal animates shake; password input clears; inline error "Incorrect password. Try again."
  - click Cancel: queued request cancelled; modal closes; user stays on current page

- States:
  - confirming: "Confirm" button shows spinner; input disabled
  - error: inline error message below password input; input re-enabled for retry

---

### Story 13.2.3 — Security Headers Middleware `[DONE]`

#### Backend
*As an API, I want standard security headers on all HTTP responses, so that browser-based attacks are mitigated.*
- `SecurityMiddleware` adds: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Content-Security-Policy`, `Strict-Transport-Security` (in production)
- CSP: `default-src 'self'; script-src 'self' cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' cdn.tailwindcss.com; font-src https://fonts.gstatic.com;`

#### Frontend
*As a security engineer, I want to verify that all required headers are present on every response, so that the platform passes a security header scan without manual configuration.*
- No dedicated route — header enforcement is transparent to users; verification UI is a section within `#/settings/security`
- Layout addition (Security Headers section, below policy tabs): FlexSection — "Security Headers" heading | checklist of required headers | "Run Security Check" FlexButton(ghost)

- Checklist: one row per header — header name | FlexBadge(color=success) "✓ Present" or FlexBadge(color=danger) "✗ Missing"

- Interactions:
  - click "Run Security Check": GET /admin/security/headers-check → checklist rows update with current pass/fail status

- States:
  - not-run: checklist rows show "—" status; prompt "Click 'Run Security Check' to verify"
  - checking: checklist rows show skeleton while probe resolves
  - all-pass: all rows show FlexBadge(color=success)
  - has-failures: failed rows show FlexBadge(color=danger); FlexAlert(type=warning) "X headers missing or misconfigured"

---

### Story 13.2.4 — Rate Limiting `[DONE]`

#### Backend
*As an API, I want per-IP rate limiting on all endpoints, so that brute-force attacks and abusive clients are throttled.*
- SlowAPI: login endpoints limited to 10 req/min per IP; general API endpoints to 100 req/min per IP
- Rate-limited requests return 429 with `Retry-After` header
- Limit configurable via `RATE_LIMIT_PER_MINUTE` env var

#### Frontend
*As a developer integrating with the API, I want rate limit information shown in the browser's network tab and also surfaced in a dev overlay, so that I can monitor API consumption during development.*
- No dedicated route — rate limit handling is global in `api.js`; dev overlay activated by `?debug=1` URL param

- Dev overlay (floating panel, bottom-right, `?debug=1` only):
  - Requests/min (current) | Remaining quota FlexBadge | resets at timestamp

- Interactions:
  - any API response: `api.js` reads `X-RateLimit-Remaining` header; dev overlay updates
  - any 429 response: global FlexAlert(type=warning) toast "Request limit reached. Retrying in X seconds" with live countdown; queued requests auto-retry after `Retry-After` seconds

- States:
  - normal: dev overlay shows current usage (dev mode only)
  - rate-limited: toast countdown visible; retrying requests queued

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
- Route: `#/admin/health` → `admin-health.html` + `admin-health-page.js` (superadmin only)
- Layout: FlexStack(direction=vertical) > page-header, metrics-grid
  - page-header: FlexToolbar — "System Health" title | "Last updated X seconds ago" label
  - metrics-grid: FlexGrid(columns=3, gap=md) — one FlexCard per metric

- Per metric FlexCard:
  - metric name | current value (large text) | sparkline (last 10 data points) | threshold FlexBadge

- Threshold indicators: error rate > 5% → FlexBadge(color=danger); DB pool > 90% → FlexBadge(color=warning)

- Interactions:
  - auto-poll: GET /admin/metrics every 30 s → all metric cards update; "Last updated" counter resets

- States:
  - loading: metric cards show skeleton sparklines on first load
  - threshold-breach: affected card border highlights red (danger) or amber (warning)
  - error: FlexAlert(type=error) "Could not load metrics. Retry?"

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
- No dedicated route — test execution is a CI concern; no UI page involved

- Currently tested: `FlexAccordion`, `FlexCheckbox`, `FlexInput`, `FlexRadio`, `BaseComponent`
- Remaining: `FlexModal`, `FlexDrawer`, `FlexTable`, `FlexDataGrid`, `FlexSelect`, `FlexTextarea`, `FlexStack`, `FlexGrid`, `FlexSidebar`, `FlexStepper`, `FlexPagination`, `FlexAlert`, `FlexButton`, `FlexBadge`, `FlexDropdown`, `FlexTabs`, `FlexTooltip`, `FlexSpinner`, `FlexBreadcrumb`, `FlexCard`
- Each test file covers: renders with default props, renders with all variants, emits expected events on interaction, shows error state correctly
- Coverage threshold enforced in `vitest.config.js`: 80% statements/functions/lines, 75% branches
