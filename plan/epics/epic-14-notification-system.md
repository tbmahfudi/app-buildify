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
- Route: `#/settings/notifications` → "Queue Status" tab
- Status cards: Pending (blue), Sent Today (green), Failed (red) — counts with a mini sparkline chart (last 24 hours)
- "Failed Notifications" table: timestamp, type, recipient, error message, retry count, "Retry Now" button
- Auto-refreshes every 60 seconds; manual "Refresh" button

---

### Story 14.1.2 — Notification Configuration per Tenant `[DONE]`

#### Backend
*As an API, I want per-tenant notification config to control which notification types are enabled and by which method, so that tenants can opt in/out of specific communications.*
- `NotificationConfig` table: `{tenant_id, notification_type, is_enabled, methods: ["email", "sms", "in_app"]}`
- Platform default config (`tenant_id = NULL`) applies if no tenant-specific config exists

#### Frontend
*As a tenant administrator, I want a notification settings table with toggles for each notification type and method, so that I can control exactly which events trigger which communications.*
- Route: `#/settings/notifications` → "Notification Types" tab
- Table: Notification Type | Email toggle | SMS toggle | In-App toggle | Description
- Types listed: Account Locked, Password Expiring, Password Changed, Password Reset, Login From New Device, Workflow Approval Request, Scheduled Report
- Toggling any cell immediately calls `PUT /settings/notifications/{type}` (auto-save, no Save button)
- "Test" button per row (in an Actions column) sends a test notification of that type to the current admin's email/phone

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
- Route: `#/settings/notifications` → "Email Settings" tab
- SMTP form: Host, Port (number), Username, Password (masked), From Address, From Name, TLS toggle
- "Test Connection" button sends a test email to the admin's email address
- Test result displayed inline: "✓ Test email sent to [email]" (green) or "✗ Connection failed: [SMTP error]" (red)
- Connection status chip shown in the tab header: "Configured" (green) / "Not Configured" (grey) / "Connection Error" (red)

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
- Route: `#/settings/notifications` → "Email Templates" tab
- Template list: one card per notification type with a "Preview" button and "Customize" button
- "Preview" opens a modal with an iframe rendering the HTML template with the tenant's branding (logo, colors)
- "Customize" opens an email editor: Subject line input + rich text editor for the body (or HTML source mode toggle)
- Template variables shown as chips below the editor (click to insert at cursor)
- "Reset to Default" button restores the built-in template with a confirmation

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
- Route: `#/settings/notifications` → "SMS Settings" tab
- Form: Provider (select: Twilio / other), Account SID, Auth Token (masked), From Number
- "Test SMS" button sends a test message to the admin's registered phone number (entered in a prompt)
- Twilio account balance shown (fetched from Twilio API): "Account Balance: $X.XX" with a warning if < $5

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
- Bell icon in the top navigation bar; red badge with unread count (max "99+")
- Clicking bell opens a `FlexDropdown` panel: "Notifications" header + "Mark all as read" link
- Panel lists the 10 most recent notifications: icon (by type) | title | body (truncated 80 chars) | relative time
- Unread notifications have a blue left border; read ones are muted
- Each notification: clicking the body or an "Open" link navigates to the `action_url`
- "View All" link at the bottom navigates to `#/notifications` — a full-page notifications center with infinite scroll and type filters
- Polling: `GET /notifications/me?unread=true` polled every 30 seconds to update the badge count
