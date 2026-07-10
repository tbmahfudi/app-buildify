---
artifact_id: epic-13-communications
status: active
version: 1
module: healthcare_comms
launch_phase: R2
producer: A3 Product Owner
upstream: BACKLOG v3
created: 2026-07-02
---

# Epic 13 — Communications & Notifications

**Module:** `healthcare_comms` (requires `healthcare` base; folds spec module 17 Communication into 7 Notification)
**Launch Phase:** R2
**Summary:** Healthcare **message templates** and **triggers** that ride the **platform notification transport**
(Reuse Register #7 — `core/notification_service.py`, `workers/notification_worker.py`) and the **platform
Scheduler** (Reuse Register — `services/scheduler_engine.py`) to deliver appointment reminders, lab-ready,
prescription-ready, and payment-reminder messages over WhatsApp / SMS / Email. This epic also
**consolidates** the existing `hcs_notification_log` and `sdk/notification_service.py` onto the platform
transport so there is a single delivery path and audit trail.

> **REUSE, do not rebuild.** No queue, worker, retry, channel adapter, or scheduler is built here — those are
> platform capabilities. This epic ships healthcare **templates** (per-channel, localized), **trigger bindings**
> (domain events → notification enqueue), **recipient/consent/opt-out** rules, and the **consolidation** of the
> legacy healthcare notification log/service onto the platform transport.

> **Scope-out (BACKLOG Scope-Out #10 — WA free-form PHI):** WhatsApp messages use **approved template
> messages only**; no free-form clinical/PHI content over WhatsApp. Message bodies are **PHI-minimized** —
> reference codes, clinic name, dates, and a portal link; never diagnoses, results, or drug details in the body.

---

## Feature 13.1 — Healthcare Message Templates

### Story 13.1.1 [OPEN]
**As a** Branch Manager or Clinic Admin,
**I want to** manage healthcare message templates per channel and locale on the platform notification transport,
**so that** every automated healthcare message is consistent, localized, and PHI-safe.

**Backend AC:**
- Register healthcare **notification templates** in the platform template store (`core/notification_service.py`) for four message types × three channels (WhatsApp / SMS / Email) × two locales (id-ID / en-US): appointment reminder, lab-ready, prescription-ready, payment-reminder. No transport code is written.
- Each template declares allowed merge variables from a **PHI-minimized allow-list** (clinic name, branch name, reference code, date/time, amount for payment, portal deep-link) — variables outside the allow-list are rejected at registration; free-form PHI is not permitted (Scope-Out #10).
- WhatsApp templates are marked as **approved-template** type (no free-form send path exposed); SMS/Email support the same variable set.
- Templates are tenant/branch overridable; `GET/PUT /api/v1/tenants/:tenant_id/branches/:branch_id/comms/templates` — auth: Clinic Admin, Branch Manager; edits emit `comms.template_updated` audit event.

**Frontend AC:**
- Route: `/clinic/comms/templates`
- Template list by type × channel × locale; editor with a variable palette limited to the PHI-safe allow-list; live preview per channel.
- WhatsApp editor flags approved-template constraints; free-form/PHI variables not selectable.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/comms/templates`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Komunikasi > Template) + main content; template list (type × channel × locale) left, editor + preview right.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexTable` — templates: Jenis Pesan, Saluran (Channel), Bahasa, Status, Tindakan
  - `FlexTabs` — channel tabs in editor: WhatsApp / SMS / Email
  - `FlexForm` — template body editor with a variable palette (chips): {nama_klinik}, {kode_referensi}, {tanggal}, {jam}, {jumlah}, {tautan_portal} — PHI-safe only
  - `FlexBadge` — approved-template indicator (WhatsApp); PHI-safe indicator
  - `FlexCard` — live per-channel preview (WhatsApp bubble / SMS / Email)
  - `FlexButton` — "Simpan Template" (Save Template)
  - `FlexAlert` — warning if a disallowed variable is attempted
- **Key interactions:**
  - Variable palette offers only PHI-safe merge fields; attempting free-form PHI or an unlisted variable is blocked with an explanation.
  - WhatsApp tab shows the approved-template constraint banner; no free-form field is offered.
  - Live preview renders the message per channel and locale.
- **Empty state:** "Belum ada template khusus. Template default sistem digunakan." (No custom templates. System defaults are used.)
- **Error state:** Disallowed variable: `FlexAlert` "Variabel tidak diizinkan — hanya data non-PHI." (Variable not allowed — non-PHI data only.); save failure `FlexAlert`.
- **i18n:** Message-type labels, channel labels, variable-palette labels, indicators, preview, button, error strings translated (ID / EN); template bodies stored per locale.
- **Mobile:** Secondary; list collapses to cards; editor single-column with preview below.

### Story 13.1.2 [OPEN]
**As a** Clinic Admin,
**I want to** register and map WhatsApp approved templates to healthcare message types,
**so that** WhatsApp sends use pre-approved templates only and never carry free-form PHI (Scope-Out #10).

**Backend AC:**
- `GET/PUT /api/v1/tenants/:tenant_id/branches/:branch_id/comms/whatsapp-templates` — auth: Clinic Admin; maps each healthcare message type (appointment reminder, lab-ready, prescription-ready, payment-reminder) to a provider-approved WhatsApp template id + variable mapping (PHI-safe allow-list only).
- The send path refuses to enqueue a WhatsApp message for a type without an approved-template mapping (falls back to SMS/Email per preference); no free-form WhatsApp send path exists (Scope-Out #10 enforced at the transport binding).
- Approval status per template surfaced (approved / pending / rejected) as reported by the platform channel adapter; mapping changes emit `comms.whatsapp_mapping_updated` audit event. No channel-adapter code is written — this configures the platform transport's WhatsApp channel.

**Frontend AC:**
- Route: `/clinic/comms/whatsapp`
- Per-type approved-template mapping with variable binding to the PHI-safe allow-list; approval-status indicator; test-send (to a staff number) using the approved template.
- Warning that free-form WhatsApp/PHI is not permitted.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/comms/whatsapp`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Komunikasi > WhatsApp) + main content; per-message-type mapping cards.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — per type: approved-template `FlexSelect`, variable-binding rows (PHI-safe allow-list), approval-status `FlexBadge` (Disetujui / Menunggu / Ditolak)
  - `FlexButton` — "Uji Kirim" (Test Send) to a staff number; "Simpan Pemetaan" (Save Mapping)
  - `FlexAlert` — Scope-Out #10 notice: "WhatsApp hanya menggunakan template disetujui — tanpa PHI bebas." (WhatsApp uses approved templates only — no free-form PHI.)
- **Key interactions:** map each message type to an approved WhatsApp template; bind only PHI-safe variables; approval status shown; test-send to a staff number; types without a mapping fall back to SMS/Email (indicated).
- **Empty state:** "Belum ada template WhatsApp dipetakan." (No WhatsApp templates mapped yet.)
- **Error state:** Missing mapping / rejected template: `FlexAlert` explaining the fallback; save failure `FlexAlert`.
- **i18n:** Type labels, approval-status badges, Scope-Out notice, buttons, error strings translated (ID / EN).
- **Mobile:** Secondary; mapping cards single-column.

## Feature 13.2 — Appointment Reminders

### Story 13.2.1 [OPEN]
**As a** Patient,
**I want to** receive an appointment reminder before my visit,
**so that** I don't miss my appointment.

**Backend AC:**
- Bind an appointment-reminder **trigger** to the platform Scheduler (Reuse Register): for each upcoming appointment (epic-02), schedule a reminder at a clinic-configurable lead time (default 24h and 2h); the job enqueues a notification via the platform transport using the appointment-reminder template.
- Channel selection follows patient preference + consent (Feature 13.5) with fallback order WhatsApp → SMS → Email; body is PHI-minimized (clinic, date/time, reference, portal link) per Scope-Out #10.
- Cancellation/reschedule of the appointment cancels/reschedules the pending reminder job; delivery + status recorded via the consolidated log (Feature 13.6).
- No scheduler/worker code is written — only the trigger binding and template selection.

**Frontend AC:**
- Route: `/clinic/comms/settings` — reminder lead-time(s) and default channel configurable per branch.
- Patient portal shows upcoming-reminder indication on the appointment; opt-out respected.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/comms/settings` (reminder config) + patient appointment view indicator
- **Portal:** Clinic Portal (config) / Patient Portal (indicator)
- **Layout:** Sidebar nav (active: Komunikasi > Pengaturan) + main content; reminder settings section.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexForm` — lead-time(s) `FlexInput`/chips (e.g. 24 jam, 2 jam), default channel `FlexSelect`
  - `FlexBadge` — per-appointment "Pengingat aktif" (Reminder scheduled) indicator (patient portal)
  - `FlexButton` — "Simpan Pengaturan" (Save Settings)
- **Key interactions:** configure lead times + default channel per branch; reschedule/cancel of an appointment updates the reminder automatically; patient sees a reminder-scheduled indicator and can opt out (Feature 13.5).
- **Empty state:** Defaults preset (24h + 2h, WhatsApp).
- **Error state:** Save failure `FlexAlert`.
- **i18n:** Lead-time/channel labels, indicator, button, error strings translated (ID / EN).
- **Mobile:** Secondary (config); Primary (patient indicator).

## Feature 13.3 — Result & Prescription Ready Notifications

### Story 13.3.1 [OPEN]
**As a** Patient,
**I want to** be notified when my lab results are ready (published) and when my prescription is ready,
**so that** I can view results in the portal or collect my medication.

**Backend AC:**
- Bind triggers: on lab result **publish** (epic-05 addendum lifecycle → `published`) enqueue a lab-ready notification; on prescription **dispensed/ready** (epic-04) enqueue a prescription-ready notification — both via the platform transport using the respective templates.
- Bodies are PHI-minimized: "[Clinic] — your lab result for order [REF] is ready. View in the portal: [link]" / "[Clinic] — your prescription [REF] is ready for collection." — **no result values or drug names** (Scope-Out #10); the portal link carries the patient to authenticated PHI.
- Channel per patient preference + consent; delivery recorded in the consolidated log.
- No transport code — trigger binding + template only.

**Frontend AC:**
- Patient portal receives an in-app notification with a deep link to the released result (epic-05 Story 5.3.2) or the active prescription list.
- Clinic side: notification status visible on the lab order / prescription (sent / delivered / failed).
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** patient portal notifications + `#/clinic/lab/orders/:order_id` / prescription views (status)
- **Portal:** Patient Portal (receipt) / Clinic Portal (status)
- **Layout:** Reuses existing lab order / prescription pages plus the patient notification center.
- **Components:**
  - `FlexNotification` — patient in-app entry: "Hasil lab siap" / "Resep siap diambil" with deep link
  - `FlexBadge` — clinic-side delivery status on the order/prescription: Terkirim (Sent) / Diterima (Delivered) / Gagal (Failed)
  - `FlexAlert` — failed-delivery notice with retry (platform transport handles retry)
- **Key interactions:** publish/dispense fires the notification automatically; patient taps the deep link → authenticates → sees PHI in the portal (never in the message body); clinic sees per-message delivery status.
- **Empty state:** N/A (event-driven).
- **Error state:** Delivery failure shows "Gagal" badge; platform transport retries per policy.
- **i18n:** Notification copy, status badges, error strings translated (ID / EN).
- **Mobile:** Primary (patient); Secondary (clinic status).

## Feature 13.4 — Payment Reminders

### Story 13.4.1 [OPEN]
**As a** Billing Staff or Branch Manager,
**I want to** send payment reminders for outstanding invoices,
**so that** patients are reminded to settle balances.

**Backend AC:**
- Bind a payment-reminder trigger over outstanding invoices (epic-03 billing): a scheduled job (platform Scheduler) enqueues a payment-reminder notification for invoices unpaid past a clinic-configurable grace period, using the payment-reminder template.
- Body is PHI-minimized: clinic name, invoice reference, amount due, due date, portal payment link — **no line items / clinical detail** (Scope-Out #10).
- Respects patient consent/opt-out; reminders stop when the invoice is paid; delivery recorded in the consolidated log.
- Billing-only (no GL/AR — deferred per BACKLOG); no transport/scheduler code.

**Frontend AC:**
- Route: `/clinic/comms/settings` — payment-reminder grace period + cadence configurable; manual "Send Reminder" from an invoice.
- Reminder history visible per invoice.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/comms/settings` (config) + invoice view "Kirim Pengingat" (Send Reminder)
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Komunikasi > Pengaturan) payment-reminder section; per-invoice reminder action + history.
- **Components:**
  - `FlexForm` — grace period + cadence config
  - `FlexButton` — manual "Kirim Pengingat" on an invoice
  - `FlexTable` — reminder history per invoice: waktu, saluran, status
  - `FlexBadge` — delivery status
- **Key interactions:** configure grace/cadence; automatic reminders on overdue invoices; manual send available; reminders stop on payment; amount + reference only in the body.
- **Empty state:** "Belum ada pengingat terkirim." (No reminders sent yet.)
- **Error state:** Send failure `FlexAlert`.
- **i18n:** Config labels, action label, history headers, status badges, error strings translated (ID / EN); amount currency localized.
- **Mobile:** Secondary.

## Feature 13.5 — Consent, Preferences & Opt-Out

### Story 13.5.1 [OPEN]
**As a** Patient,
**I want to** choose my preferred channel and opt out of non-essential messages,
**so that** I only receive communications I consent to, on the channel I prefer.

**Backend AC:**
- `GET/PUT /api/v1/patients/me/comms-preferences` — auth: Patient; per-category (appointment, results, prescription, payment, marketing) channel preference and opt-out flags; marketing defaults to opt-out.
- The notification-send path checks preferences + consent (epic-01 consent) before enqueuing; suppressed messages are logged as `suppressed_by_preference` (no send). Regulatory/critical messages (e.g., critical-value handling stays in epic-05) are not governed here.
- Opt-out changes emit `comms.preferences_updated` audit event; per Scope-Out #10, WhatsApp remains approved-template only regardless of preference.

**Frontend AC:**
- Route: `/patient/account/communication`
- Per-category channel selection + opt-out toggles; marketing off by default; explanation of essential vs optional messages.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/patient/account/communication`
- **Portal:** Patient Portal
- **Layout:** Mobile-first; account settings; per-category preference cards; bottom nav.
- **Components:**
  - `FlexCard` — per category (Janji Temu, Hasil, Resep, Pembayaran, Promosi): channel `FlexSelect` + opt-out `FlexToggle`
  - `FlexBadge` — "Wajib" (Essential) badge on non-optional categories
  - `FlexButton` — "Simpan Preferensi" (Save Preferences)
  - `FlexAlert` — explanation of essential vs optional
- **Key interactions:** pick channel per category; toggle opt-out (marketing off by default); essential categories cannot be fully disabled; save persists preferences consulted at send time.
- **Empty state:** Defaults preset.
- **Error state:** Save failure `FlexAlert`.
- **i18n:** Category labels, channel options, essential badge, explanation, button, error strings translated (ID / EN).
- **Mobile:** Primary; full-width cards; large toggles.

## Feature 13.6 — Notification Log Consolidation

### Story 13.6.1 [OPEN]
**As a** Platform/Clinic Admin,
**I want to** consolidate the legacy `hcs_notification_log` + `sdk/notification_service.py` onto the platform notification transport with a single audited delivery log,
**so that** there is one delivery path, one status/audit trail, and no duplicate notification code.

**Backend AC:**
- Migrate healthcare send sites currently using `sdk/notification_service.py` to enqueue through the platform transport (`core/notification_service.py`); the legacy healthcare service becomes a thin adapter/shim (or is retired) with no independent delivery logic.
- Consolidate `hcs_notification_log` into the platform notification/delivery log (or make it a read-through view over it): every healthcare message records `(message_type, channel, recipient_ref, template_id, reference_code, status ∈ {queued, sent, delivered, failed, suppressed}, tenant_id, branch_id, at)` — PHI-minimized (no message body PHI stored beyond references).
- A backfill/migration maps historical `hcs_notification_log` rows into the consolidated log; a compatibility read endpoint keeps existing healthcare views working.
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/comms/log?type=&channel=&status=&from=&to=` — auth: Clinic Admin, Branch Manager; paginated; delivery/audit events retained per platform audit policy.

**Frontend AC:**
- Route: `/clinic/comms/log`
- Unified delivery log: filter by type, channel, status, date; per-message status; drill to the source event (appointment/lab/prescription/invoice).
- All labels in active locale; timestamps in branch timezone.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/comms/log`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Komunikasi > Log Pengiriman) + main content; filter toolbar + paginated table.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexToolbar` — filters: type `FlexSelect`, channel `FlexSelect`, status `FlexSelect`, date range `FlexDatepicker`
  - `FlexTable` — columns: Waktu, Jenis, Saluran, Referensi, Status, Sumber
  - `FlexBadge` — status: Antre (Queued) / Terkirim (Sent) / Diterima (Delivered) / Gagal (Failed) / Ditahan (Suppressed)
  - `FlexButton` — drill to source event; "Terapkan Filter"
- **Key interactions:** filter/paginate the unified log; each row links to its source (appointment/lab order/prescription/invoice); no PHI beyond references shown.
- **Empty state:** "Tidak ada pesan untuk filter ini." (No messages for this filter.)
- **Error state:** `FlexAlert` "Gagal memuat log komunikasi" (Failed to load communication log).
- **i18n:** Filter/column labels, status badges, empty/error strings, timestamp format translated (ID / EN).
- **Mobile:** Secondary; table horizontally scrollable; filters in a `FlexDrawer`.

## Story Count: Feature 13.1 (2) + 13.2 (1) + 13.3 (1) + 13.4 (1) + 13.5 (1) + 13.6 (1) = **7 stories**
