# Epic 8 — Automation Rules

> Event-driven and scheduled automation rules that trigger actions when configurable conditions are met.

---

## Feature 8.1 — Automation Rule Configuration `[DONE]`

### Story 8.1.1 — Database Event Triggers `[DONE]`

#### Backend
*As an API, I want automation rules that fire when entity records are created, updated, or deleted, so that downstream side effects are handled automatically.*
- Automation rule: `trigger_type = "database_event"`, `entity_id`, `event_type` (`create`/`update`/`delete`/`any`), `trigger_timing` (`before`/`after`)
- `trigger_conditions` JSONB: `[{"field": "status", "operator": "eq", "value": "submitted"}]` — evaluated against the record
- After the triggering operation: `EventPublisher.publish()` enqueues matching rules for `AutomationService` to execute

#### Frontend
*As a tenant administrator on the automation builder page, I want to create a rule by selecting a trigger event, defining conditions on the record's fields, and then adding actions, all in a guided form — so that I can automate business logic without writing code.*
- Route (list): `#/nocode/automations` → `automations.html` + `automations-page.js`
- Route (builder): `#/nocode/automations/new` and `#/nocode/automations/{id}/edit` → `automation-builder.html` + `automation-builder-page.js`
- Layout (builder): FlexStack(direction=vertical) > summary-banner, trigger-section, conditions-section, actions-section, sticky-footer
  - summary-banner: FlexSection — plain-language rule summary "When a [Entity] is [Event] and [conditions], then [actions]" (updates live as form fills)
  - trigger-section: FlexSection — Entity (FlexSelect) | Event type (FlexRadio: Created / Updated / Deleted / Any) | Field conditions builder (same filter-row UI as list page)
  - conditions-section: FlexAccordion (collapsed, optional) — additional field-value conditions
  - actions-section: FlexSection — draggable action cards list | "Add Action" FlexButton(ghost)
  - sticky-footer: FlexToolbar — Cancel | Save as Draft | Save & Activate (primary)

- Interactions:
  - change Entity or Event type: summary-banner updates live
  - click "Save & Activate": POST /nocode/automations → rule activates immediately
  - click "Save as Draft": POST /nocode/automations {status: draft} → returns to list with "Draft" FlexBadge

- States:
  - loading (list): FlexDataGrid skeleton while GET /nocode/automations resolves
  - empty (list): "No automation rules yet" + "New Rule" FlexButton(primary)
  - saving: footer buttons show spinner; form disabled

---

### Story 8.1.2 — Scheduled Triggers `[DONE]`

#### Backend
*As an API, I want scheduled automation rules that execute on a cron or interval basis, so that periodic background tasks are managed centrally.*
- `trigger_type = "scheduled"`, `schedule_type` (`cron`/`interval`/`one_time`), `cron_expression`, `timezone`
- `SchedulerEngine` polls `scheduler_jobs` for due jobs and invokes `AutomationService.execute(rule)`
- Job execution history stored in `scheduler_job_runs`: `{status, started_at, completed_at, output, error}`

#### Frontend
*As a tenant administrator creating a scheduled automation, I want a cron expression builder with a human-readable preview, so that I can set a schedule without learning cron syntax.*
- Route: `#/nocode/automations/new` → automation builder trigger-section (see Story 8.1.1), shown when "Scheduled" trigger type is selected

- Schedule configuration section (appears when Scheduled selected):
  - FlexTabs: Interval | Specific Time | Cron
    - Interval tab: number (FlexInput) + unit (FlexSelect: minutes / hours / days) → summary "Every 30 minutes"
    - Specific Time tab: time picker (HH:MM FlexInput) + day-of-week FlexCheckbox group
    - Cron tab: 5-part cron FlexInput (minute / hour / day / month / weekday) + live human-readable preview "Runs every Monday at 08:00 AM UTC"
  - "Next 5 runs" preview list below tabs (computed client-side from cron expression)
  - Timezone (FlexSelect, searchable, defaults to tenant timezone)

- Interactions:
  - switch schedule tab: inputs swap; next-5-runs list recalculates
  - change any interval / time / cron input: next-5-runs list and human-readable preview update immediately (client-side)

---

### Story 8.1.3 — Automation Actions `[IN-PROGRESS]`

#### Backend
*As an API, I want automation rules to support multiple action types executed in sequence when triggered, so that complex business responses can be automated.*
- Action types: `send_notification`, `update_field`, `create_record`, `call_webhook`, `run_workflow_transition`, `call_api`
- Actions stored as a JSONB array; executed in order; failure logged without rolling back the trigger
- `max_retries` and `retry_delay_seconds` configurable per action

#### Frontend
*As a tenant administrator configuring actions for an automation rule, I want to add multiple actions from a palette, configure each one in an expandable card, and reorder them by dragging, so that multi-step automations are easy to build.*
- Route: `#/nocode/automations/new` → actions-section of automation builder (see Story 8.1.1)

- FlexModal(size=md) — action type picker, triggered by "Add Action"
  - icon-card grid: Send Notification | Update Field | Create Record | Call Webhook | Run Workflow Transition | Call API
  - select a card: modal closes; new action card appended to actions list

- Action card (per action in the list):
  - header: drag handle | action type icon | one-line summary | Enable/Disable FlexCheckbox | × Delete
  - body (expanded): type-specific config fields:
    - Send Notification: Recipient (FlexSelect: user/role/email) | Subject (FlexInput) | Body (FlexTextarea, `{{field_name}}` token auto-complete)
    - Update Field: Field (FlexSelect) | New Value (FlexInput, token auto-complete)
    - Create Record: Entity (FlexSelect) | field mapping rows
    - Call Webhook / Call API: URL (FlexInput) | Method (FlexSelect) | Headers (key-value rows) | Body (FlexTextarea, template)
    - Run Workflow Transition: Workflow (FlexSelect) | Transition (FlexSelect)
  - footer row: Failure behavior (FlexSelect: Continue on failure / Stop rule on failure)

- Interactions:
  - click "Add Action": opens action type picker FlexModal
  - drag action card via handle: reorders cards; order updates live
  - click card header (not controls): expands/collapses card body
  - type `{{` in body/value fields: token auto-complete dropdown shows triggering record's field names

---

## Feature 8.2 — Webhook Outbound Integration `[PLANNED]`

### Story 8.2.1 — Webhook Endpoint Registration `[PLANNED]`

#### Backend
*As an API, I want tenants to register external URLs as webhook recipients, so that external systems receive platform events.*
- `POST /api/v1/webhooks` registers a webhook with `url`, `events: [event_type]`, `secret`, `is_active`
- Validation challenge: platform sends a `GET` request to the URL with a challenge parameter; URL must echo it back
- `webhooks` table with per-tenant isolation

#### Frontend
*As a tenant administrator on the integrations settings page, I want to add a webhook URL, select which events to subscribe to, and test the connection, so that I can connect the platform to external tools like Slack or Zapier.*
- Route: `#/settings/integrations` → `settings.html` + `settings-page.js` (Webhooks tab)
- Layout: FlexStack(direction=vertical) > page-header, webhooks-list
  - page-header: FlexToolbar — "Webhooks" title | "Add Webhook" FlexButton(primary)
  - webhooks-list: FlexDataGrid — URL (truncated), subscribed events (FlexBadge chips), Status (FlexBadge), Last Delivery Status, Actions

- FlexModal(size=md) — "Add Webhook" form
  - fields: URL (FlexInput, type=url, HTTPS required) | Events (multi-select checklist grouped by category: Data Events | Workflow Events | System Events) | Secret (FlexInput, auto-generated, masked, "Reveal" toggle)
  - "Test Connection" FlexButton(ghost): POST test ping → inline "✓ Connection successful" or error message
  - footer: Cancel | Save Webhook (primary)
  - on save: webhook row appears with FlexBadge(color=warning) "Pending Verification" until challenge succeeds

- Interactions:
  - click "Add Webhook": opens FlexModal(size=md)
  - click "Test Connection": sends test ping; result shown inline in modal (no close)
  - click "Reveal" on secret: toggles masked/unmasked display

- States:
  - loading: FlexDataGrid skeleton while GET /webhooks resolves
  - empty: "No webhooks configured yet" + "Add Webhook" FlexButton(primary)
  - pending-verification: FlexBadge(color=warning) on new webhook row

---

### Story 8.2.2 — Webhook Delivery and Retry `[PLANNED]`

#### Backend
*As an API, I want failed webhook deliveries retried with exponential backoff, so that transient failures don't cause missed events.*
- Webhook calls enqueued via the automation action system; delivered asynchronously
- Retry schedule on non-2xx: 1s, 5s, 30s, 5m, 30m, 1h (6 attempts total)
- After all retries: endpoint auto-disabled; admin notification queued
- `webhook_deliveries` table records each attempt: `request_body`, `response_status`, `response_body`, `duration_ms`, `attempted_at`

#### Frontend
*As a tenant administrator, I want to see a delivery log for each webhook endpoint showing every event sent, the response received, and whether it succeeded or failed, so that I can diagnose integration issues.*
- Route: `#/settings/integrations/webhooks/{id}/deliveries` → webhook deliveries page
- Layout: FlexStack(direction=vertical) > page-header, deliveries-grid
  - page-header: FlexToolbar — FlexBreadcrumb | webhook URL | status FlexBadge

- FlexDataGrid(server-side, expandable-rows) — deliveries via GET /webhooks/{id}/deliveries
  - columns: Event Type, Timestamp, Status (FlexBadge: Success/Failed/Retrying), HTTP Status Code, Duration
  - expanded row: Request Body (JSON, pretty-printed, read-only code block) | Response Body (code block)
  - row action: "Redeliver" FlexButton(ghost) [admin only, failed rows only]

- Interactions:
  - click "View Deliveries" on webhook row: navigates to deliveries page
  - click row expand chevron: shows Request Body + Response Body
  - click "Redeliver" on failed row: POST /webhooks/{id}/deliveries/{delivery_id}/redeliver → row status updates to "Retrying"
  - click "Re-enable" on auto-disabled webhook: opens confirm FlexModal → PATCH /webhooks/{id} {is_active: true}

- States:
  - loading: FlexDataGrid skeleton
  - empty: "No deliveries yet"
  - auto-disabled: FlexAlert(type=error) "Disabled (too many failures)" at top + "Re-enable" FlexButton

---

### Story 8.2.3 — Webhook Payload Signing `[PLANNED]`

#### Backend
*As an API, I want to sign webhook payloads with HMAC-SHA256, so that recipients can verify the authenticity of events.*
- Each webhook POST includes `X-Signature: sha256=<hmac>` header using the webhook's configured secret
- HMAC-SHA256 over the raw request body bytes
- Secret rotation: `PUT /api/v1/webhooks/{id}/rotate-secret` issues a new secret; both old and new signatures included during a 24-hour transition window

#### Frontend
*As a tenant administrator rotating a webhook secret, I want a one-click "Rotate Secret" button that explains the transition window and gives me the new secret to update my integration, so that secret rotation doesn't break my webhook receiver.*
- Route: `#/settings/integrations` → webhook detail FlexModal (Security section)

- Webhook detail FlexModal — Security section:
  - current secret: masked FlexInput + "Reveal" toggle
  - "Rotate Secret" FlexButton(ghost, danger)
  - during transition window: FlexAlert(type=info) "Dual-signing active — new secret active, old secret expires in Xh Ym"

- FlexModal(size=sm) — rotate confirm, triggered by "Rotate Secret"
  - body: "Rotating the secret starts a 24-hour dual-signing window. Both old and new secrets will be accepted during this period."
  - footer: Cancel | Rotate Secret (FlexButton, variant=danger)
  - on confirm: PUT /webhooks/{id}/rotate-secret → new secret shown once in a read-only FlexInput with "Copy" FlexButton + FlexAlert(type=warning) "This is the only time you'll see the new secret. Update your integration now."

- Interactions:
  - click "Rotate Secret": opens rotate confirm FlexModal(size=sm)
  - confirm rotation: new secret displayed once with Copy button; FlexAlert warning shown
  - click "Copy": copies secret to clipboard; button label → "Copied ✓"
  - close modal after rotation: new secret no longer retrievable; transition window indicator appears in Security section
