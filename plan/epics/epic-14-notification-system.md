# Epic 14 — Notification System

> Queue-based notification delivery for system events via email, SMS, and in-app channels.

---

## Feature 14.1 — Notification Queue `[DONE]`

### Story 14.1.1 — Notification Queuing Architecture `[DONE]`

#### Backend
*As an API, I want all notifications queued asynchronously so that primary operations are not blocked by delivery latency.*
- `NotificationService.queue_notification(type, recipient, template_data, method, priority, scheduled_for?)` creates a `NotificationQueue` record
- Background worker polls for `status=pending` records, attempts delivery, updates `status` to `sent`, `failed`, or `retrying`
- `max_attempts` (default 3), `retry_delay_seconds` (exponential), `priority` (1–10 with higher = sooner) configurable

#### Frontend
*As a tenant administrator on the notification settings page, I want to see a queue status panel showing pending, sent, and failed notifications, so that I can diagnose delivery issues.*
- Route: `#/settings/notifications` → `settings.html` + `settings-page.js` (Queue Status tab)
- Layout: FlexStack(direction=vertical) > status-cards, failed-table
  - status-cards: FlexCluster — three FlexCard(metric): Pending (info) | Sent Today (success) | Failed (danger); each shows count + sparkline (last 24 h)
  - failed-table: FlexDataGrid(server-side) — Timestamp | Type | Recipient | Error Message | Retry Count | "Retry Now" FlexButton(ghost) per row

- Interactions:
  - click "Retry Now" on a failed row: POST /notifications/{id}/retry → row status updates to "Retrying"
  - click "Refresh": GET /notifications/queue/stats → status-cards and failed-table refresh
  - auto-refresh: stats and failed-table poll every 60 s

- States:
  - loading: status-cards show skeleton; failed-table shows skeleton rows
  - no-failures: failed-table shows "No failed notifications"

---

### Story 14.1.2 — Notification Configuration per Tenant `[DONE]`

#### Backend
*As an API, I want per-tenant notification config to control which notification types are enabled and by which method, so that tenants can opt in/out of specific communications.*
- `NotificationConfig` table: `{tenant_id, notification_type, is_enabled, methods: ["email", "sms", "in_app"]}`
- Platform default config (`tenant_id = NULL`) applies if no tenant-specific config exists

#### Frontend
*As a tenant administrator, I want a notification settings table with toggles for each notification type and method, so that I can control exactly which events trigger which communications.*
- Route: `#/settings/notifications` → Notification Types tab
- Layout: FlexStack(direction=vertical) > page-header, types-grid
  - page-header: FlexToolbar — "Notification Types" title
  - types-grid: FlexDataGrid(static) — Notification Type | Email (FlexCheckbox toggle) | SMS (FlexCheckbox toggle) | In-App (FlexCheckbox toggle) | Description | Actions

- Notification types: Account Locked | Password Expiring | Password Changed | Password Reset | Login From New Device | Workflow Approval Request | Scheduled Report

- Interactions:
  - toggle any channel cell: PUT /settings/notifications/{type} {method, is_enabled} immediately (auto-save); small "Saved ✓" indicator flashes beside the cell
  - click "Test" in Actions column: POST /settings/notifications/test {type} → inline toast "[Type] test sent to [admin email/phone]"

---

## Feature 14.2 — Email Delivery `[OPEN]`

### Story 14.2.1 — SMTP Email Delivery Adapter `[OPEN]`

#### Backend
*As an API, I want the notification worker to send emails via SMTP using tenant-configured credentials, so that email notifications are actually delivered.*
- Worker reads `NotificationConfig.smtp_host/port/user/password/from_address/use_tls`
- Sends via `aiosmtplib`; on delivery failure: marks `status=failed`, increments `attempt_count`
- `POST /api/v1/settings/notifications/test-email` sends a test email to the requesting admin's address

#### Frontend
*As a tenant administrator on the email settings page, I want to enter my SMTP credentials, click "Test Connection", and see a clear success or failure message with the SMTP error details, so that I can verify email delivery is working.*
- Route: `#/settings/notifications` → Email Settings tab
- Layout: FlexStack(direction=vertical) > smtp-form, test-result-area
  - smtp-form: FlexForm(columns=2) — Host (FlexInput) | Port (FlexInput, type=number) | Username (FlexInput) | Password (FlexInput, type=password, masked) | From Address (FlexInput, type=email) | From Name (FlexInput) | TLS (FlexCheckbox toggle)
  - form footer: "Save" FlexButton(primary) | "Test Connection" FlexButton(ghost)
  - test-result-area: inline result below footer (hidden until test runs)

- Tab header: connection status FlexBadge — "Configured" (success) / "Not Configured" (neutral) / "Connection Error" (danger)

- Interactions:
  - click "Save": PUT /settings/notifications/smtp → success toast; tab header FlexBadge updates
  - click "Test Connection": POST /settings/notifications/test-email → test-result-area shows "✓ Test email sent to [email]" (FlexAlert, type=success) or "✗ Connection failed: [SMTP error]" (FlexAlert, type=error)

- States:
  - testing: "Test Connection" button shows spinner
  - not-configured: tab header FlexBadge(color=neutral) "Not Configured"

---

### Story 14.2.2 — Email Template System `[OPEN]`

#### Backend
*As an API, I want HTML email templates with variable interpolation for each notification type, so that notifications render correctly with tenant branding.*
- Templates stored as HTML files per notification type in `backend/app/templates/email/`
- Variables: `{{user_name}}`, `{{tenant_name}}`, `{{action_url}}`, `{{expiry_date}}`, `{{reason}}`
- `EmailRenderer.render(template_type, context)` returns HTML and plain-text fallback
- Tenant custom templates optionally stored in `NotificationConfig.custom_templates` JSONB

#### Frontend
*As a tenant administrator, I want to preview each email template with my organization's branding and optionally customize the subject line and body, so that our communications match our brand.*
- Route: `#/settings/notifications` → Email Templates tab
- Layout: FlexStack(direction=vertical) > templates-list
  - templates-list: FlexGrid(columns=auto, gap=md) — one FlexCard per notification type

- Per template FlexCard:
  - content: notification type name | customized FlexBadge(color=info) "Custom" (if overridden)
  - footer: "Preview" FlexButton(ghost) | "Customize" FlexButton(ghost)

- `PreviewModal` FlexModal(size=lg) triggered by "Preview":
  - body: iframe rendering HTML template with tenant branding (logo, colors)
  - footer: Close FlexButton

- `CustomizeModal` FlexModal(size=lg) triggered by "Customize":
  - body: Subject (FlexInput) | body editor (rich text; "HTML" toggle switches to source FlexTextarea) | variable chips below editor (click to insert at cursor)
  - footer: "Reset to Default" FlexButton(ghost, danger) | Cancel | "Save Template" FlexButton(primary)

- Interactions:
  - click "Preview": GET /settings/notifications/templates/{type}/preview → PreviewModal opens with rendered iframe
  - click "Customize": GET /settings/notifications/templates/{type} → CustomizeModal opens with current subject + body
  - click variable chip: inserts `{{variable}}` at current cursor position in editor
  - click "Save Template": PUT /settings/notifications/templates/{type} → modal closes; card shows "Custom" FlexBadge
  - click "Reset to Default": FlexModal(size=sm) confirm → DELETE /settings/notifications/templates/{type} → "Custom" badge removed

---

## Feature 14.3 — SMS and Push Delivery `[PLANNED]`

### Story 14.3.1 — SMS Delivery via Provider `[PLANNED]`

#### Backend
*As an API, I want to send SMS notifications via a configured SMS provider (Twilio), so that OTPs and alerts reach users on their phones.*
- Worker reads `NotificationConfig.sms_provider`, `sms_account_sid`, `sms_auth_token`, `sms_from_number`
- Twilio REST API used for delivery; 160-char limit enforced; longer messages truncated with `[…]`
- `POST /api/v1/settings/notifications/test-sms` sends a test SMS to the admin's phone

#### Frontend
*As a tenant administrator on the SMS settings page, I want to enter my Twilio credentials, test the connection, and see my SMS balance and recent messages, so that I can confirm SMS delivery is working.*
- Route: `#/settings/notifications` → SMS Settings tab
- Layout: FlexStack(direction=vertical) > sms-form, balance-section
  - sms-form: FlexForm(columns=2) — Provider (FlexSelect: Twilio / other) | Account SID (FlexInput) | Auth Token (FlexInput, type=password, masked) | From Number (FlexInput)
  - form footer: "Save" FlexButton(primary) | "Test SMS" FlexButton(ghost)
  - balance-section: FlexCluster — "Account Balance: $X.XX" label + FlexBadge(color=warning) "Low balance" when < $5

- Interactions:
  - click "Save": PUT /settings/notifications/sms → success toast
  - click "Test SMS": FlexModal(size=sm) prompts for recipient phone number → confirm: POST /settings/notifications/test-sms {phone} → inline toast "Test SMS sent to [number]" or error message
  - balance-section auto-fetches on tab load: GET /settings/notifications/sms/balance → balance label updates

- States:
  - testing: "Test SMS" button shows spinner
  - low-balance: FlexBadge(color=warning) "Low balance" shown alongside balance amount

---

### Story 14.3.2 — In-App Notification Center `[PLANNED]`

#### Backend
*As an API, I want in-app notifications stored and retrievable per user, so that users see platform events in the UI without email.*
- `notifications` table: `{user_id, type, title, body, action_url, is_read, created_at}`
- `GET /api/v1/notifications/me?unread=true&page=1` returns paginated unread notifications
- `POST /api/v1/notifications/{id}/read` marks a notification as read
- `POST /api/v1/notifications/read-all` clears the unread count

#### Frontend
*As a user, I want a notification bell in the navigation bar that shows a red badge with my unread count, and clicking it opens a dropdown listing my recent notifications with action links, so that I never miss important alerts while working.*
- No dedicated route for the bell — it lives in the global nav bar; full center at `#/notifications`
- Layout (bell): nav-bar bell icon + FlexBadge(color=danger) unread count (capped at "99+")

- `NotificationDropdown` FlexDropdown (triggered by bell click):
  - header: "Notifications" label | "Mark all as read" link
  - body: FlexStack(gap=xs) — up to 10 recent notification rows
    - per row: type icon | title | body text (truncated 80 chars) | relative time
    - unread row: blue left border; read row: muted opacity
  - footer: "View All" link → `#/notifications`

- Layout (full page `#/notifications`): FlexStack(direction=vertical) > page-header, filter-bar, notifications-list
  - page-header: FlexToolbar — "Notifications" title | "Mark all as read" FlexButton(ghost)
  - filter-bar: FlexCluster — type filter chips
  - notifications-list: infinite-scroll list of notification rows (same row layout as dropdown)

- Interactions:
  - click bell: FlexDropdown opens; GET /notifications/me (10 most recent) → rows render
  - click notification row (dropdown or full page): navigate to `action_url`; POST /notifications/{id}/read → row loses blue border
  - click "Mark all as read": POST /notifications/read-all → all rows muted; bell badge clears
  - click "View All": navigate to `#/notifications`; dropdown closes
  - auto-poll: GET /notifications/me?unread=true every 30 s → bell badge count updates

- States:
  - empty (dropdown): "No new notifications"
  - loading (dropdown): skeleton rows while fetch resolves
