---
artifact_id: epic-09-visit-registration-queue
status: active
version: 1
module: healthcare_registration
launch_phase: MVP
producer: A3 Product Owner
upstream: BACKLOG v3
created: 2026-07-02
---

# Epic 09 — Visit Registration & Queue Management

**Module:** `healthcare_registration` (depends on epic-01 base, epic-02 scheduling, epic-08 departments)
**Launch Phase:** MVP
**Summary:** Staff-facing front-desk workflow that turns an arriving patient into a coded visit and a
routed queue ticket, then hands the visit off to the EMR as an encounter. Covers check-in from an
existing appointment, walk-in registration, payment-category + insurance tagging at registration,
referral capture, per-department queue-number assignment, a real-time queue board with call / skip /
recall / transfer across stations, and the visit → encounter hand-off to EMR (epic-10).

**References:** ADR-HC-006 (visit & queue), schema-hc-02 (`hcr_visits`, `hcr_queue_tickets`).

**Invariants (reused, not re-specified):** platform Auth/RBAC/Audit; branch isolation per adr-hc-001;
PHI via SDK readers + audit per adr-hc-002; i18n id-ID (default) + en-US per adr-hc-004; mobile-first
(front-desk tablets + wall-mounted queue displays). Every new table carries `tenant_id` + `branch_id`;
RLS per schema-hc-01. `hcr_visits.payment_category`, `insurance_profile_id`, and any patient-identifying
reads go through SDK readers with audit. Queue-board updates use **`queue_version` short-polling
(SSE-ready)** per ADR-HC-006 (WebSocket rejected there).

**Canonical tables:**
- `hcr_visits` (id, tenant_id, branch_id, patient_id, appointment_id nullable, visit_type ∈
  {appointment, walk_in}, payment_category, insurance_profile_id nullable, referral_source,
  department_id, status, checked_in_at, encounter_id nullable)
- `hcr_queue_tickets` (id, tenant_id, branch_id, visit_id, department_id, ticket_number, station,
  status ∈ {waiting, called, skipped, recalled, transferred, served}, called_at, served_at)

---

## Feature 9.1 — Patient Check-In & Registration

### Story 9.1.1 [OPEN]
**As a** Front-Desk Staff member,
**I want to** check in a patient who has an existing appointment,
**so that** their scheduled visit becomes an active visit ready for queueing.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/visits/check-in` — auth: Front-Desk / Nurse /
  Branch Manager (platform RBAC); payload: `appointment_id`; derives `patient_id`, `department_id` from
  the appointment (epic-02); sets `visit_type = appointment`, `status = registered`, `checked_in_at`.
- Validates the appointment belongs to this branch and is in a check-in-eligible state (e.g., `booked` /
  `confirmed`) — 409 if already checked in or cancelled; the appointment is transitioned to `arrived`.
- Creates one `hcr_visits` row; `appointment_id` set; patient identity read via SDK reader with audit.
- Emits `hcr_visit.checked_in` PHI audit event (`actor_id`, `tenant_id`, `branch_id`, `patient_id`,
  `visit_id`).

**Frontend AC:**
- Route: `/clinic/registration/check-in`
- Today's appointment list (this branch) with search by patient name / phone / appointment code; each
  row has a "Check In" action.
- On check-in: confirmation with patient summary (name masked-by-default toggle, appointment time,
  department) then routes to payment/insurance tagging (9.2.1).
- Empty state when no appointments today; all labels in active locale; times in branch timezone.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/registration/check-in`
- **Portal:** Clinic Portal (front-desk / registration)
- **Layout:** Sidebar nav (active: Registrasi > Check-In) + main content; search toolbar above a
  paginated table of today's appointments; branch + date context in header.
- **Components:**
  - `FlexSidebar` — clinic portal nav; branch context badge
  - `FlexToolbar` — search `FlexInput` (name/phone/code), date shown read-only (today)
  - `FlexTable` — columns: Waktu, Pasien (masked toggle), Dokter, Departemen, Status, Tindakan
  - `FlexBadge` — appointment status; PHI mask toggle in table header
  - `FlexButton` — per-row "Check In"; primary
  - `FlexModal` — check-in confirmation with patient summary
  - `FlexAlert` — already-checked-in / ineligible-appointment errors
- **Key interactions:**
  - Search debounced (300 ms) across name/phone/appointment code.
  - "Check In" opens a confirmation modal showing patient (masked-by-default), appointment time
    (branch timezone + tz label e.g. WIB), and department; confirm creates the visit and advances to
    payment/insurance tagging.
  - PHI mask toggle masks patient names in the list for a crowded front desk.
  - 409 (already checked in) surfaces inline on the row.
- **Empty state:** "Tidak ada janji temu hari ini di cabang ini." (No appointments today at this branch.)
- **Error state:** Ineligible/already-checked-in `FlexAlert` in the confirmation modal; load failure
  banner with retry.
- **i18n:** Column headers, status/labels, modal text, empty/error strings, timezone labels translated
  (ID / EN).
- **Mobile:** Primary use is a front-desk tablet; table collapses to card list; "Check In" is a
  full-width button per card; large tap targets.

### Story 9.1.2 [OPEN]
**As a** Front-Desk Staff member,
**I want to** register a walk-in patient who has no appointment,
**so that** they can be queued and seen the same as a scheduled patient.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/visits/walk-in` — auth: Front-Desk / Nurse /
  Branch Manager; payload: `patient_id` (existing) **or** an inline new-patient block (name, DOB, phone,
  gender) that creates a branch-scoped patient via the epic-01 patient service, plus target
  `department_id`.
- Sets `visit_type = walk_in`, `appointment_id = null`, `status = registered`, `checked_in_at`; patient
  create/read goes through SDK readers with audit.
- Duplicate-guard: if an active (`registered`/`in_queue`) visit already exists today for the same
  patient + department, returns 409 with the existing `visit_id`.
- Emits `hcr_visit.walk_in_registered` PHI audit event.

**Frontend AC:**
- Route: `/clinic/registration/walk-in`
- Patient search (existing) with a "New patient" fallback inline form (name, DOB, phone, gender); target
  department selector (from epic-08 departments of this branch).
- On submit: advances to payment/insurance tagging (9.2.1); duplicate-active-visit warning offers to
  open the existing visit.
- Mobile-first; all labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/registration/walk-in`
- **Portal:** Clinic Portal (front-desk / registration)
- **Layout:** Sidebar nav (active: Registrasi > Walk-in) + main content; two-step inline flow: (1)
  find-or-create patient, (2) choose department; desktop max-width 720 px card.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexInput` — patient search (name/phone), and new-patient fields (name, phone) when creating
  - `FlexDatepicker` — new patient DOB
  - `FlexSelect` — gender; target department (branch departments, kind-labelled)
  - `FlexButton` — "Pasien Baru" (New Patient) toggle, "Lanjut ke Pembayaran" (Continue to Payment)
  - `FlexBadge` — PHI mask toggle on patient summary
  - `FlexAlert` — duplicate-active-visit warning with "Buka Kunjungan" (Open Visit) action
- **Key interactions:**
  - Search first; if not found, "Pasien Baru" reveals the inline create form (reuses epic-01 patient
    create rules — duplicate-phone check applies).
  - Selecting a department is required to proceed.
  - Duplicate active visit → `FlexAlert` "Pasien sudah memiliki kunjungan aktif di departemen ini
    hari ini." (Patient already has an active visit in this department today.) with an "Open Visit"
    action.
- **Empty state:** N/A (creation flow); patient search shows "Ketik untuk mencari pasien" prompt.
- **Error state:** Inline validation on new-patient fields; duplicate-phone / duplicate-visit surfaced
  inline; API error `FlexAlert` at top.
- **i18n:** All labels, department kind labels, warnings, buttons, error strings translated (ID / EN).
- **Mobile:** Primary (tablet); single-column; inputs full-width; "Lanjut" pinned to bottom.

## Feature 9.2 — Payment Category, Insurance & Referral Capture

### Story 9.2.1 [OPEN]
**As a** Front-Desk Staff member,
**I want to** tag the visit with a payment category and, if applicable, an insurance profile,
**so that** billing and eligibility downstream know how the visit is funded.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/visits/:visit_id/payment` — auth: Front-Desk /
  Branch Manager; payload: `payment_category` (e.g., self_pay, insurance, corporate, BPJS),
  `insurance_profile_id` (nullable; required and validated when category is insurance/BPJS).
- Writes `hcr_visits.payment_category`, `hcr_visits.insurance_profile_id`; `insurance_profile_id` must
  reference a valid insurer profile for the patient (read via SDK reader) — 422 otherwise.
- Editable only while the visit is not yet `served`/`closed`.
- Emits `hcr_visit.payment_tagged` change-audit event; insurance profile reads audited (PHI-adjacent).

**Frontend AC:**
- Route: `/clinic/registration/:visit_id/payment`
- Payment-category selector; conditional insurance-profile picker shown only for insurance/BPJS
  categories; validation prevents proceeding without a required insurance profile.
- Displays the patient/visit summary; on save, advances to referral capture (9.2.2) then queue
  assignment (9.3.1).
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/registration/:visit_id/payment`
- **Portal:** Clinic Portal (front-desk)
- **Layout:** Sidebar nav (active: Registrasi) + main content; visit summary strip on top; payment form
  below; desktop max-width 640 px.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — visit summary strip (patient masked toggle, department, visit type)
  - `FlexSelect` — payment category (Bayar Sendiri / Asuransi / Korporat / BPJS)
  - `FlexSelect` — insurance profile (shown only when category is Asuransi/BPJS; lists patient's insurer
    profiles)
  - `FlexButton` — "Lanjut" (Continue), "Kembali"
  - `FlexBadge` — PHI mask toggle on the summary strip
  - `FlexAlert` — missing-insurance-profile / validation errors
- **Key interactions:**
  - Selecting Asuransi/BPJS reveals the insurance-profile picker; "Lanjut" is disabled until a profile
    is chosen for those categories.
  - Insurance profile options fetched via SDK reader; access audited.
  - "Lanjut" advances to referral capture.
- **Empty state:** Insurance picker empty state: "Pasien belum memiliki profil asuransi." (Patient has no
  insurance profile.) with a hint to add one.
- **Error state:** Inline required-profile error; API 422 `FlexAlert` at top of form.
- **i18n:** Category labels, insurer picker, buttons, empty/error strings translated (ID / EN).
- **Mobile:** Primary; single-column; category select as a sheet; "Lanjut" pinned bottom.

### Story 9.2.2 [OPEN]
**As a** Front-Desk Staff member,
**I want to** record the referral source for the visit,
**so that** referral patterns are captured for reporting and follow-up.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/visits/:visit_id/referral` — auth: Front-Desk /
  Branch Manager; payload: `referral_source` (free text or controlled value, e.g., self, gp_referral,
  internal_department, online), optional referrer detail note.
- Writes `hcr_visits.referral_source`; editable while the visit is open; optional (may be left blank).
- Emits `hcr_visit.referral_captured` change-audit event.

**Frontend AC:**
- Route: `/clinic/registration/:visit_id/referral`
- Referral-source selector with an optional detail note; skippable ("No referral").
- On save/skip, advances to queue assignment (9.3.1).
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/registration/:visit_id/referral`
- **Portal:** Clinic Portal (front-desk)
- **Layout:** Sidebar nav (active: Registrasi) + main content; compact form after the payment step;
  desktop max-width 640 px.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexSelect` — referral source (Mandiri / Rujukan Dokter / Antar-Departemen / Online / Lainnya)
  - `FlexInput` / `FlexTextarea` — optional referrer detail note
  - `FlexButton` — "Lanjut" (Continue), "Lewati" (Skip), "Kembali"
  - `FlexAlert` — save error
- **Key interactions:**
  - Referral is optional; "Lewati" proceeds without a value.
  - Choosing "Lainnya" (Other) reveals the free-text note.
  - "Lanjut" advances to queue-number assignment.
- **Empty state:** N/A (optional single form).
- **Error state:** Save error `FlexAlert` at top; otherwise inline.
- **i18n:** Source labels, note placeholder, buttons, error strings translated (ID / EN).
- **Mobile:** Primary; single-column; buttons pinned bottom.

## Feature 9.3 — Queue Number Assignment

### Story 9.3.1 [OPEN]
**As a** Front-Desk Staff member,
**I want to** assign a per-department queue number to the visit,
**so that** the patient is placed in the correct queue and receives a ticket.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/visits/:visit_id/queue-ticket` — auth:
  Front-Desk / Branch Manager; derives `department_id` from the visit; allocates the next
  `ticket_number` for `(tenant_id, branch_id, department_id, service-day)`; creates `hcr_queue_tickets`
  with `status = waiting`, `station = null`.
- Ticket numbering resets per department per service-day; allocation is concurrency-safe (no duplicate
  numbers under simultaneous check-ins); the visit transitions `registered → in_queue`.
- Emits `hcr_queue_ticket.issued` change-audit event; returns the ticket number and estimated position.

**Frontend AC:**
- Route: `/clinic/registration/:visit_id/queue`
- Confirms department (editable if allowed), issues the ticket, and shows a printable/large ticket
  number with department and estimated wait/position.
- "Print ticket" and "Done" actions; returns to check-in / walk-in list.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/registration/:visit_id/queue`
- **Portal:** Clinic Portal (front-desk)
- **Layout:** Sidebar nav (active: Registrasi) + main content; large ticket-confirmation card centered;
  desktop max-width 560 px.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — issued-ticket card: big `ticket_number`, department name + kind badge, estimated
    position/wait
  - `FlexSelect` — department (editable pre-issue if routing correction is allowed)
  - `FlexButton` — "Terbitkan Tiket" (Issue Ticket), "Cetak Tiket" (Print Ticket), "Selesai" (Done)
  - `FlexAlert` — allocation/validation errors
- **Key interactions:**
  - "Terbitkan Tiket" allocates the next number; the card then shows the large ticket number and
    estimated position.
  - "Cetak Tiket" triggers a print-friendly layout (number, department, timestamp, branch).
  - "Selesai" returns to the registration list.
  - No raw PHI on the ticket (number + department only).
- **Empty state:** N/A.
- **Error state:** Allocation failure `FlexAlert` "Gagal menerbitkan nomor antrean, coba lagi." (Failed
  to issue queue number, try again.)
- **i18n:** Card labels, department/kind labels, buttons, error strings translated (ID / EN).
- **Mobile:** Primary; ticket number very large; buttons full-width pinned bottom.

## Feature 9.4 — Queue Board & Station Operations

### Story 9.4.1 [OPEN]
**As a** clinical or front-desk staff member at a station,
**I want to** view a real-time department queue board,
**so that** I can see who is waiting, called, or served without refreshing.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/queue?department_id=&station=` — auth: any branch
  staff; returns current `hcr_queue_tickets` for the department grouped by status (waiting / called /
  skipped / recalled / served) with ticket numbers and (masked) patient reference.
- Real-time refresh (per ADR-HC-006): the board endpoint returns a monotonic `queue_version`; clients
  short-poll (`?since=<queue_version>`) on a 2–3 s interval and re-render only on version change. The
  contract is SSE-ready — a future `GET .../queue/stream` SSE endpoint can push the same version/delta
  without changing clients. (WebSocket rejected in ADR-HC-006 on branch-isolation + infra grounds.)
- Board reads return no raw PHI (ticket number + masked patient initial only); reads audited at the
  channel-subscription level.

**Frontend AC:**
- Route: `/clinic/queue/board` (station view) and `/display/queue/:department_id` (public wall display)
- Live columns per status; the currently-called ticket highlighted; auto-updates via `queue_version`
  short-polling (2–3 s) with a visible freshness/connection indicator.
- Wall-display variant is large-type, no controls, no PHI (ticket numbers only).
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/queue/board` (staff station) | `#/display/queue/:department_id` (public wall
  display, no auth-sensitive data)
- **Portal:** Clinic Portal (station) / standalone display surface (wall)
- **Layout:** Station: sidebar nav (active: Antrean > Papan) + main board; multi-column status board
  (Menunggu / Dipanggil / Dilewati / Dipanggil Ulang / Dilayani). Wall display: full-screen, no sidebar,
  extra-large type, currently-called ticket dominant.
- **Components:**
  - `FlexSidebar` — station nav (hidden on wall display); branch + department context badge
  - `FlexBoard` / `FlexColumn` — status columns of ticket cards
  - `FlexCard` — ticket card: big number, masked patient initial (station only), station tag
  - `FlexBadge` — live-connection indicator ("Langsung" / "Menyambung ulang..."); status color per column
  - `FlexAlert` — connection-lost / reconnecting banner
- **Key interactions:**
  - `queue_version` short-poll moves cards between columns on each version bump; currently-called ticket
    pulses/highlights.
  - Freshness indicator shows live vs stale; if a poll fails, UI keeps last state and shows
    "Menyambung ulang..." until the next successful poll.
  - Wall display shows ticket numbers only — no patient initials, no PHI.
  - Station board respects PHI masking; only a masked initial is ever shown.
- **Empty state:** "Antrean kosong untuk departemen ini." (Queue is empty for this department.)
- **Error state:** Connection-lost `FlexAlert` "Koneksi papan antrean terputus — mencoba menyambung
  ulang" (Queue board connection lost — reconnecting).
- **i18n:** Column labels, connection indicator, empty/error strings translated (ID / EN); large-type
  wall display uses locale numerals/labels.
- **Mobile:** Station board columns become a swipeable segmented view; wall display targets large screens
  but scales down responsively.

### Story 9.4.2 [OPEN]
**As a** staff member at a station,
**I want to** call, skip, and recall queue tickets,
**so that** I can manage the flow of patients to my station.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/queue-tickets/:ticket_id/call` — auth: branch
  staff at a station; sets `status = called`, `station`, `called_at`; only from `waiting`/`recalled`.
- `POST /.../queue-tickets/:ticket_id/skip` — sets `status = skipped` (from `called`); the patient can be
  recalled later.
- `POST /.../queue-tickets/:ticket_id/recall` — sets `status = recalled` (from `skipped`), re-queuing the
  ticket at a configurable position.
- All transitions are validated against the allowed state machine (invalid transition → 409), bump the
  board's `queue_version` (picked up by the next short-poll), and emit `hcr_queue_ticket.<action>`
  change-audit events; patient identity for the announced call is read via SDK reader with audit.

**Frontend AC:**
- Route: `/clinic/queue/board` (station controls)
- "Call next", per-ticket "Skip" and "Recall" actions; the called ticket shown prominently with the
  station label; announcement/beep hook on call.
- Actions reflect instantly via WS; disabled actions for invalid transitions.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/queue/board` (station controls)
- **Portal:** Clinic Portal (station)
- **Layout:** Board from 9.4.1 plus a station control bar; "Panggil Berikutnya" (Call Next) primary
  button; per-card action buttons.
- **Components:**
  - `FlexToolbar` — station control bar: station selector, "Panggil Berikutnya"
  - `FlexButton` — per-card "Panggil" (Call), "Lewati" (Skip), "Panggil Ulang" (Recall)
  - `FlexCard` — currently-called ticket highlighted with station label
  - `FlexBadge` — status badges; PHI mask on the called-patient initial
  - `FlexAlert` — invalid-transition / announce errors
- **Key interactions:**
  - "Panggil Berikutnya" calls the next waiting ticket to the active station; optional chime/announce
    hook fires.
  - "Lewati" moves a called ticket to skipped; "Panggil Ulang" re-queues a skipped ticket.
  - Invalid transitions (e.g., recall on a served ticket) are disabled; server 409 surfaces as an inline
    error.
  - All changes broadcast to every subscribed board via WS.
- **Empty state:** "Tidak ada pasien menunggu untuk dipanggil." (No patients waiting to be called.)
- **Error state:** Invalid-transition `FlexAlert`; announce/audio failure is non-blocking with a warning.
- **i18n:** Control labels, action buttons, status labels, error strings translated (ID / EN).
- **Mobile:** Station on a tablet; action buttons large; "Panggil Berikutnya" full-width pinned to
  bottom.

### Story 9.4.3 [OPEN]
**As a** Branch Manager or station staff,
**I want to** transfer a queue ticket to another department or station,
**so that** a patient routed incorrectly (or needing another service) moves without re-registering.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/queue-tickets/:ticket_id/transfer` — auth: Branch
  Manager or station staff; payload: target `department_id` and/or `station`.
- Sets the source ticket `status = transferred`; issues a new `hcr_queue_tickets` row in the target
  department (fresh `ticket_number` allocated per that department's numbering) linked to the same
  `visit_id`; updates `hcr_visits.department_id` to the target department.
- Transfer within the same branch only (cross-branch transfer out of scope for MVP → 422); bumps
  `queue_version` for both source and target departments' boards; emits `hcr_queue_ticket.transferred`
  change-audit event.

**Frontend AC:**
- Route: `/clinic/queue/board` (transfer action on a ticket)
- Transfer modal: target department selector (branch departments) and optional station; confirms and
  shows the new ticket number in the target department.
- Source board removes the ticket (transferred); target board shows the new waiting ticket in real time.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/queue/board` (transfer flow)
- **Portal:** Clinic Portal (station)
- **Layout:** Board from 9.4.1 with a per-ticket "Pindahkan" (Transfer) action opening a modal.
- **Components:**
  - `FlexButton` — per-card "Pindahkan" (Transfer)
  - `FlexModal` — transfer modal: target `FlexSelect` department + optional station
  - `FlexBadge` — new-ticket confirmation badge with the allocated target number
  - `FlexAlert` — cross-branch-not-allowed / validation errors
- **Key interactions:**
  - "Pindahkan" opens the modal; choosing a target department (and optional station) confirms the
    transfer.
  - On success the modal shows the new ticket number in the target department; the source card shows a
    "Dipindahkan" (Transferred) state and drops off after animation.
  - Real-time: target department board shows the new waiting ticket immediately via WS.
- **Empty state:** N/A.
- **Error state:** Cross-branch attempt `FlexAlert` "Pemindahan antar-cabang tidak didukung." (Cross-branch
  transfer not supported.); other errors in the modal footer.
- **i18n:** Modal labels, department/station labels, confirmation, error strings translated (ID / EN).
- **Mobile:** Transfer modal full-screen sheet; selectors full-width.

## Feature 9.5 — Visit → Encounter Hand-off to EMR

### Story 9.5.1 [OPEN]
**As a** Doctor or Nurse,
**I want to** promote a called visit into a clinical encounter,
**so that** I can document care in the EMR against this visit.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/visits/:visit_id/encounter` — auth: Doctor / Nurse;
  creates a base `hc_encounters` encounter (epic-01 SOAP model) for the visit's patient/branch, sets
  `hcr_visits.encounter_id`, transitions the ticket `status = served` (`served_at`) and the visit
  `status = in_encounter`.
- Idempotent: if the visit already has an `encounter_id`, returns the existing encounter (200) rather
  than creating a duplicate; requires the visit to be in `in_queue`/`called` state — 409 otherwise.
- Encounter creation reads patient PHI via SDK reader with audit and emits `hcr_visit.encounter_started`
  + the base `encounter.created` PHI audit events; the coding/notes work then lives in epic-10.

**Frontend AC:**
- Route: `/clinic/queue/board` → "Start Encounter" on a called ticket, landing on the EMR encounter
  page (`#/clinic/encounters/:encounter_id`, epic-01/epic-10).
- Confirms patient + visit context; if an encounter already exists, opens it rather than creating a new
  one.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/queue/board` (Start Encounter action) → `#/clinic/encounters/:encounter_id`
- **Portal:** Clinic Portal (clinical station)
- **Layout:** Board from 9.4.1; called-ticket card exposes a primary "Mulai Kunjungan Klinis" (Start
  Encounter) action; on success navigates to the EMR encounter page.
- **Components:**
  - `FlexButton` — "Mulai Kunjungan Klinis" (Start Encounter) on the called ticket
  - `FlexModal` — brief confirm with patient (masked toggle) + department + payment category summary
  - `FlexBadge` — visit status transition indicator; PHI mask toggle
  - `FlexAlert` — invalid-state / hand-off errors
- **Key interactions:**
  - "Mulai Kunjungan Klinis" confirms context then calls the hand-off endpoint; on success the ticket
    marks `served` and the app routes to `#/clinic/encounters/:encounter_id`.
  - If an encounter already exists, the app opens it (no duplicate created).
  - Patient identity revealed here is read via SDK reader and audited.
- **Empty state:** N/A (acts on a specific called ticket).
- **Error state:** 409 invalid-state `FlexAlert` "Kunjungan belum siap untuk memulai encounter." (Visit
  not ready to start an encounter.)
- **i18n:** Action label, confirm summary, error strings translated (ID / EN).
- **Mobile:** Clinical station tablet; confirm modal full-screen; primary action full-width.

## Story Count: Feature 9.1 (2) + 9.2 (2) + 9.3 (1) + 9.4 (3) + 9.5 (1) = **9 stories**
