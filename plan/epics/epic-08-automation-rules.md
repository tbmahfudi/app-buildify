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
- Route: `#/nocode/automations` shows the automation rules list; "New Rule" button navigates to the rule builder
- Rule builder page: 3-section vertical form:
  1. **Trigger** section: Entity select, Event type radio (Created / Updated / Deleted / Any), Field conditions builder (same UI as list page filters)
  2. **Conditions** section (optional): additional field-value conditions (e.g. "Only run when `amount > 1000`")
  3. **Actions** section: action list (reorderable cards); "Add Action" button
- Rule builder shows a plain-language summary at the top: "When a [Sales Order] is [Created] and [Status is Submitted], then [Send Notification to Sales Manager]"
- "Save & Activate" and "Save as Draft" buttons in the sticky footer

---

### Story 8.1.2 — Scheduled Triggers `[DONE]`

#### Backend
*As an API, I want scheduled automation rules that execute on a cron or interval basis, so that periodic background tasks are managed centrally.*
- `trigger_type = "scheduled"`, `schedule_type` (`cron`/`interval`/`one_time`), `cron_expression`, `timezone`
- `SchedulerEngine` polls `scheduler_jobs` for due jobs and invokes `AutomationService.execute(rule)`
- Job execution history stored in `scheduler_job_runs`: `{status, started_at, completed_at, output, error}`

#### Frontend
*As a tenant administrator creating a scheduled automation, I want a cron expression builder with a human-readable preview, so that I can set a schedule without learning cron syntax.*
- When "Scheduled" trigger type is selected in the rule builder: a schedule configuration section appears
- Schedule type tabs: "Interval" (every X minutes/hours/days), "Specific Time" (daily at HH:MM), "Cron" (advanced)
- Interval mode: number input + unit select ("Every 30 minutes")
- Specific time mode: time picker + day-of-week checkboxes
- Cron mode: 5-part cron input with a live preview: "Runs every Monday at 08:00 AM UTC"
- "Next 5 runs" preview list below the schedule section so users can verify the schedule is correct
- Timezone select (defaults to tenant's default timezone)

---

### Story 8.1.3 — Automation Actions `[DONE]`

#### Backend
*As an API, I want automation rules to support multiple action types executed in sequence when triggered, so that complex business responses can be automated.*
- Action types: `send_notification`, `update_field`, `create_record`, `call_webhook`, `run_workflow_transition`, `call_api`
- Actions stored as a JSONB array; executed in order; failure logged without rolling back the trigger
- `max_retries` and `retry_delay_seconds` configurable per action

#### Frontend
*As a tenant administrator configuring actions for an automation rule, I want to add multiple actions from a palette, configure each one in an expandable card, and reorder them by dragging, so that multi-step automations are easy to build.*
- Actions section: list of action cards (draggable to reorder with a drag handle icon)
- "Add Action" button opens an action-type picker modal with cards:
  - 📧 Send Notification — recipient (user/role/email), subject, body (template with `{{field_name}}` tokens)
  - ✏️ Update Field — field select, new value (can be a template token from the triggering record)
  - ➕ Create Record — entity select, field mapping form
  - 🌐 Call Webhook — URL input, method select, custom headers, body template
  - 🔄 Run Workflow Transition — workflow select, transition select
  - 🔗 Call API — URL, method, headers, body (with response mapping)
- Each action card has an expand/collapse toggle; collapsed view shows a one-line summary
- Action card header: action type icon + summary text + "Enable/Disable" toggle + "Delete" icon
- Failure behavior select per action: "Continue on failure" / "Stop rule on failure"

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
- Route: `#/settings/integrations` → "Webhooks" tab
- Webhook list shows: URL (truncated), subscribed events as chips, status (Active/Inactive), last delivery status
- "Add Webhook" button opens a `FlexModal` with:
  - URL input (validated as a valid HTTPS URL)
  - Event subscriptions: multi-select checklist grouped by category (Data Events, Workflow Events, System Events)
  - Secret field (auto-generated but editable; masked with a "Reveal" toggle)
- "Test Connection" button in the modal sends a test ping; shows "✓ Connection successful" or the error
- After saving: webhook status shows "Pending Verification" until the validation challenge succeeds

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
- Webhook row in the list has a "View Deliveries" link
- Deliveries page: table with columns: Event Type, Timestamp, Status (Success/Failed/Retrying), HTTP Status Code, Duration
- Expanding a row shows: Request Body (JSON, pretty-printed) and Response Body
- "Redeliver" button on failed rows to manually retry; only available to admin
- Auto-disabled webhooks show a red "Disabled (too many failures)" status badge with a "Re-enable" button that requires confirmation

---

### Story 8.2.3 — Webhook Payload Signing `[PLANNED]`

#### Backend
*As an API, I want to sign webhook payloads with HMAC-SHA256, so that recipients can verify the authenticity of events.*
- Each webhook POST includes `X-Signature: sha256=<hmac>` header using the webhook's configured secret
- HMAC-SHA256 over the raw request body bytes
- Secret rotation: `PUT /api/v1/webhooks/{id}/rotate-secret` issues a new secret; both old and new signatures included during a 24-hour transition window

#### Frontend
*As a tenant administrator rotating a webhook secret, I want a one-click "Rotate Secret" button that explains the transition window and gives me the new secret to update my integration, so that secret rotation doesn't break my webhook receiver.*
- Webhook detail modal has a "Security" section: current secret (masked) + "Rotate Secret" button
- Clicking "Rotate Secret" opens a confirmation modal explaining the 24-hour dual-signing window
- After rotation: the new secret is shown once (with "Copy" button) with a warning: "This is the only time you'll see the new secret. Update your integration now."
- During the transition window: webhook detail shows "Dual-signing active — new secret active, old secret expires in Xh Ym"
