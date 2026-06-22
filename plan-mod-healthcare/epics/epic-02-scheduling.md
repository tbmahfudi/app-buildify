---
artifact_id: epic-02-scheduling
status: active
version: 2
module: healthcare_scheduling
launch_phase: GA (with base)
producer: A3 Product Owner
upstream: vision-02, research-02
created: 2026-06-21
---

# Epic 02 — Scheduling Module

**Module:** `healthcare_scheduling` (requires `healthcare` base)
**Launch Phase:** GA — ships alongside base module
**Summary:** Provider calendars per branch, patient appointment booking, PHI-safe WhatsApp/SMS reminders, and waitlist management.

---

## Feature 2.1 — Provider Calendar & Availability

### Story 2.1.1 [OPEN]
**As a** Branch Manager,
**I want to** define working hours and appointment slot templates for each doctor at my branch,
**so that** patients can see accurate available slots when booking.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/schedules` — auth: Branch Manager or Clinic Owner; payload: `provider_id`, day-of-week availability blocks, slot duration (minutes), appointment types supported.
- Schedules are branch-scoped; a doctor with roles at two branches has independent schedules per branch.
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/schedules/:provider_id` — returns weekly schedule grid.

**Frontend AC:**
- Route: `/clinic/branches/:branch_id/schedules/:provider_id`
- Weekly grid editor: drag to set availability blocks per day; slot duration selector (15/30/45/60 min).
- Save confirmation; conflict detection if overlapping blocks.
- All labels in active locale; times in branch timezone.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/branches/:branch_id/schedules/:provider_id`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Jadwal) + main content; weekly grid editor (Mon–Sun columns, time-slot rows); doctor selector at top; save toolbar pinned at bottom.
- **Components:**
  - `FlexSidebar` — nav; branch context badge in header
  - `FlexSelect` — doctor selector (top of page); branch-scoped doctor list
  - `FlexGrid` — weekly availability grid: 7 columns (days) × time slots; drag to define availability blocks
  - `FlexSelect` — slot duration selector (15 / 30 / 45 / 60 menit)
  - `FlexBadge` — conflict warning badge on overlapping blocks
  - `FlexButton` — "Simpan Jadwal" (Save Schedule), "Batal"
  - `FlexAlert` — conflict detection warning; save success/failure
  - `FlexTooltip` — slot details on hover (time, appointment types)
- **Key interactions:**
  - Drag on grid to create availability block; drag edge to resize; click block to edit or delete.
  - Slot duration dropdown re-renders grid row height.
  - Conflict detection: overlapping blocks highlighted in red with `FlexAlert` "Blok waktu tumpang tindih terdeteksi" (Overlapping time blocks detected).
  - All times displayed in branch timezone (WIB/WITA/WIT shown in column header).
  - PHI mask toggle: N/A (no patient PHI on this page).
- **Empty state:** Empty grid with instructional placeholder "Seret untuk menambahkan blok ketersediaan" (Drag to add availability blocks).
- **Error state:** Save failure: `FlexAlert` at top of grid "Gagal menyimpan jadwal" (Failed to save schedule).
- **i18n:** Day abbreviations (Mon–Sun), time format (24h per locale or 12h), slot duration labels, alert/error strings, button labels translated.
- **Mobile:** Secondary; grid scrollable horizontally; drag interactions replaced by tap-to-add flow with time pickers.

### Story 2.1.2 [OPEN]
**As a** Doctor,
**I want to** block specific dates or time ranges (leave, holidays),
**so that** those slots are unavailable for patient booking.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/schedules/:provider_id/blocks` — auth: Doctor (own schedule) or Branch Manager; payload: `start_datetime`, `end_datetime`, `reason` (internal, not patient-visible), recurrence (none/annual).
- Blocked slots excluded from availability responses; existing confirmed appointments in blocked range trigger a notification workflow (flag for manual review, do not auto-cancel).

**Frontend AC:**
- Route: calendar view on `/clinic/branches/:branch_id/schedules/:provider_id`
- "Block Date/Time" button; date-range picker; reason field (internal label).
- Blocked ranges shown in grey on calendar; hover tooltip shows reason.
- Warning banner if existing appointments fall in blocked range.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/branches/:branch_id/schedules/:provider_id` (calendar view)
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav + main content; calendar view (weekly or monthly toggle); "Blokir Tanggal/Waktu" (Block Date/Time) button top-right; blocked ranges shown in grey.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexToolbar` — week/month toggle; date navigator arrows; "Blokir Tanggal/Waktu" button
  - `FlexGrid` — calendar grid (reuses schedule grid); blocked ranges in grey with strikethrough pattern
  - `FlexModal` — block creation modal: date-range `FlexDatepicker`, reason `FlexInput` (internal label), recurrence `FlexSelect` (none/annual)
  - `FlexTooltip` — hover on blocked range shows reason label
  - `FlexAlert` — warning banner if existing appointments fall in blocked range
  - `FlexBadge` — count of affected appointments in warning banner
- **Key interactions:**
  - "Blokir Tanggal/Waktu" opens modal; date-range picker; reason (internal, not patient-visible).
  - If existing confirmed appointments in the selected range: warning banner "Ada [N] janji yang terpengaruh. Tindak lanjuti secara manual." (There are [N] appointments affected. Follow up manually.)
  - Blocked range appears in grey on calendar; hover tooltip shows reason.
  - Recurring block (annual): same date range blocked for next 3 years.
- **Empty state:** Calendar shows no blocks — normal availability grid visible.
- **Error state:** Block save failure: `FlexAlert` in modal "Gagal menyimpan blokir" (Failed to save block).
- **i18n:** Modal labels, recurrence options, warning banner text, reason field placeholder, tooltip label, error strings translated.
- **Mobile:** Secondary; modal full-screen; date-range picker uses native Android date picker.

### Story 2.1.3 [OPEN]
**As a** Branch Manager,
**I want to** view aggregate slot availability across all doctors at my branch for today and the next 7 days,
**so that** I can identify under-staffed periods.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/availability/summary?from=&to=` — auth: Branch Manager or Clinic Owner; returns per-doctor, per-day slot count (total / booked / available).

**Frontend AC:**
- Route: `/clinic/branches/:branch_id/availability`
- Heatmap-style table: rows = doctors, columns = days; color coding (green = available, yellow = mostly booked, red = fully booked).
- Date range picker; export to CSV.
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/branches/:branch_id/availability`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Jadwal > Ketersediaan) + main content; date range picker top; heatmap table below; "Ekspor CSV" button top-right.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexDatepicker` — date range selector (default: today + 7 days)
  - `FlexTable` — heatmap table: rows = doctors, columns = days; each cell shows available/booked/total slot counts
  - `FlexBadge` — color-coded cell backgrounds (green = available slots, yellow = mostly booked, red = fully booked, grey = blocked/off)
  - `FlexButton` — "Ekspor CSV"
  - `FlexTooltip` — cell hover shows: total, booked, available slot counts
  - `FlexAlert` — export feedback
- **Key interactions:**
  - Date range picker updates table on change.
  - Cell click navigates to doctor's schedule for that day (`#/clinic/branches/:branch_id/schedules/:provider_id?date=`).
  - "Ekspor CSV" downloads table as CSV with date range in filename.
  - Color thresholds: 0 available = red; 1–30% available = yellow; >30% available = green.
- **Empty state:** "Tidak ada jadwal terdaftar untuk periode ini." (No schedules registered for this period.)
- **Error state:** `FlexAlert` "Gagal memuat data ketersediaan" (Failed to load availability data).
- **i18n:** Column day labels (date + day name in active locale), row doctor name labels, legend labels (Tersedia / Hampir Penuh / Penuh), export filename format, empty/error strings translated.
- **Mobile:** Secondary; table horizontally scrollable; heatmap cells 40 px minimum width.

## Feature 2.2 — Patient Appointment Booking

### Story 2.2.1 [OPEN]
**As a** Patient,
**I want to** browse available appointment slots at a clinic branch and book one,
**so that** I can confirm a visit without calling the clinic.

**Backend AC:**
- `GET /api/v1/clinics/:clinic_slug/branches/:branch_id/slots?date=&appointment_type=` — public (authenticated patient); returns available slots with `slot_id`, `start_time`, `provider_name` (first name + specialty only).
- `POST /api/v1/patients/me/appointments` — auth: Patient; payload: `slot_id`, `appointment_type`, `notes` (optional, patient-entered, stored but not sent in notifications).
- Booking creates `appointment` record with `tenant_id`, `branch_id`, `patient_id`, `provider_id`, `slot_id`, `status: confirmed`.
- Appointment creation emits `appointment.booked` audit event (PHI: patient_id, branch_id, slot_id).

**Frontend AC:**
- Route: `/book/:clinic_slug/:branch_id` (patient portal)
- Step 1: appointment type selector; Step 2: date picker showing available days; Step 3: slot time selector; Step 4: confirmation summary.
- Slot times shown in patient's local timezone with branch timezone displayed as reference.
- Confirmation page: appointment reference code + date/time; "Add to calendar" button (ICS file).
- Empty state if no slots: "Next available: [date]."
- All strings in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/book/:clinic_slug/:branch_id`
- **Portal:** Patient Portal
- **Layout:** Mobile-first; 4-step wizard (Jenis Janji → Pilih Tanggal → Pilih Waktu → Konfirmasi); progress dots at top; sticky "Lanjut" button pinned to bottom.
- **Components:**
  - `FlexStepper` — 4-step dot progress indicator
  - `FlexCard` — appointment type selector cards (step 1; large tap targets)
  - `FlexDatepicker` — date picker showing only available days highlighted (step 2); mobile calendar
  - `FlexGrid` — time slot grid (step 3); available slots as tappable chips; slot time + doctor name
  - `FlexCard` — confirmation summary card (step 4): clinic, branch, doctor, date/time, type, reference code
  - `FlexButton` — "Lanjut" (Next) pinned bottom; "Kembali" (Back) text link top-left
  - `FlexAlert` — slot no-longer-available error; success confirmation
  - `FlexBadge` — "Tambah ke Kalender" (Add to Calendar) on confirmation (ICS download)
- **Key interactions:**
  - Step 2: unavailable days greyed out; available days bold; tapping day advances to step 3.
  - Step 3: slot times shown in patient's local timezone; branch timezone noted as "(Zona waktu klinik: WIB)".
  - Step 4: appointment reference code displayed prominently; "Tambah ke Kalender" button downloads ICS.
  - If selected slot taken by another user between selection and confirm: error "Slot telah diambil. Pilih waktu lain." (Slot taken. Choose another time.) — returns to step 3.
  - Unauthenticated user: redirected to `#/login` with return URL preserved.
- **Empty state (step 3):** "Tidak ada slot tersedia pada tanggal ini. Pilih tanggal lain." (No slots available on this date. Choose another date.) with link back to step 2.
- **Error state:** API failure: `FlexAlert` "Gagal memuat slot. Tarik untuk memuat ulang." (Failed to load slots. Pull to refresh.)
- **i18n:** Step labels, appointment type names, date labels, time labels, timezone note, confirmation text, "Tambah ke Kalender", empty/error strings translated.
- **Mobile:** Primary; each step full-screen; slot chips 48 px height; "Lanjut" 56 px full-width pinned bottom.

### Story 2.2.2 [OPEN]
**As a** Patient,
**I want to** reschedule or cancel an upcoming appointment,
**so that** I can manage changes to my schedule without calling the clinic.

**Backend AC:**
- `PUT /api/v1/patients/me/appointments/:appointment_id` — auth: Patient (own appointment only); payload: new `slot_id`; validates new slot is available; old slot released.
- `DELETE /api/v1/patients/me/appointments/:appointment_id` — auth: Patient; cancels appointment; slot released; cancellation policy enforced (configurable per tenant: e.g., no cancellation <2h before).
- Status change emits `appointment.rescheduled` or `appointment.cancelled` audit event.
- Cancellation/reschedule triggers notification workflow (PHI-safe).

**Frontend AC:**
- Route: `/patient/appointments/:appointment_id`
- "Reschedule" button: opens slot picker pre-filtered to same provider; "Cancel" button: confirmation modal with cancellation policy text in active locale.
- Post-action: confirmation banner with new reference code (reschedule) or "Your appointment has been cancelled" (cancel).

---


#### Frontend (UILDC v1.0)

- **Route:** `#/patient/appointments/:appointment_id`
- **Portal:** Patient Portal
- **Layout:** Mobile-first; appointment detail card view; action buttons below card; bottom navigation bar.
- **Components:**
  - `FlexCard` — appointment detail: clinic name, branch, doctor, type, date/time, status badge, reference code
  - `FlexBadge` — status badge (Dikonfirmasi / Selesai / Dibatalkan / Tidak Hadir)
  - `FlexButton` — "Jadwalkan Ulang" (Reschedule) primary; "Batalkan Janji" (Cancel) secondary (destructive color)
  - `FlexModal` — slot picker modal for reschedule (inline booking flow: date → time → confirm); cancel confirmation modal with cancellation policy text
  - `FlexAlert` — post-action confirmation banner
- **Key interactions:**
  - "Jadwalkan Ulang": opens `FlexModal` with slot picker pre-filtered to same provider; patient selects new slot; confirm → success banner "Jadwal berhasil diubah" (Schedule successfully changed) with new reference code.
  - "Batalkan Janji": opens confirmation modal with cancellation policy text in active locale (e.g., "Pembatalan <2 jam tidak dapat dilakukan" — Cancellation < 2h before is not permitted); "Ya, Batalkan" / "Kembali".
  - Post-cancel: status badge updates to "Dibatalkan"; actions removed from card.
  - Cancellation policy text pulled from tenant config (locale-aware).
- **Empty state:** N/A (detail page for a specific appointment).
- **Error state:** Reschedule slot taken: `FlexAlert` in modal "Slot telah diambil, pilih waktu lain"; cancel blocked by policy: error in modal footer.
- **i18n:** Status badges, action button labels, modal text, cancellation policy text, confirmation banner text, date/time format in patient locale translated.
- **Mobile:** Primary; full-width card; action buttons stacked; modal full-screen on narrow viewport.

### Story 2.2.3 [OPEN]
**As a** clinical staff member (Receptionist/Nurse),
**I want to** mark a patient as Checked In when they arrive,
**so that** the doctor can see their live queue.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/appointments/:appointment_id/status` — auth: Nurse, Branch Manager; valid transitions: `confirmed` → `checked_in` → `in_progress` → `completed` | `no_show`.
- Status change emits audit event with actor_id and timestamp.

**Frontend AC:**
- Route: `/clinic/appointments/queue` (branch-scoped live view)
- Appointment queue list: patient name, appointment time, status badge, "Check In" / "Mark No-Show" action buttons.
- Auto-refreshes every 30 seconds (or WebSocket if available).
- Queue sorted by appointment time; "In Progress" patients visually highlighted.
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/appointments/queue`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Antrian) + main content; live queue list; auto-refresh indicator top-right; branch-scoped (active branch shown in header).
- **Components:**
  - `FlexSidebar` — nav; branch context badge (prominent — queue is branch-specific)
  - `FlexTable` — queue rows: Nama Pasien (with mask toggle), Waktu Janji, Status, Tindakan; sorted by appointment time
  - `FlexBadge` — status badges color-coded: Dikonfirmasi (grey), Check-In (blue), Sedang Berjalan (green), Selesai (teal), Tidak Hadir (red)
  - `FlexButton` — "Check In" and "Tandai Tidak Hadir" (Mark No-Show) per row; change on status
  - `FlexAlert` — auto-refresh status indicator ("Diperbarui pukul HH:MM" / "Memperbarui..." — Updated at HH:MM / Updating...)
  - `FlexBadge` — PHI mask toggle in table header (masks patient names to initial only)
- **Key interactions:**
  - Queue auto-refreshes every 30 seconds; WebSocket connection used if available (graceful fallback to polling).
  - "Check In": status transitions `confirmed` → `checked_in`; row background highlights.
  - "Tandai Tidak Hadir": confirmation click required (row action changes to confirm); status → `no_show`; row moves to bottom.
  - "Sedang Berjalan" rows (in-progress) highlighted with left border color accent.
  - PHI mask: patient names masked to "Tn. A." or "Ny. B." format on toggle.
  - Date/time in branch timezone; today's date shown in page header.
- **Empty state:** "Tidak ada janji hari ini." (No appointments today.)
- **Error state:** Connection loss: `FlexAlert` sticky "Koneksi terputus — data mungkin tidak terkini" (Connection lost — data may be outdated).
- **i18n:** Status labels, action button labels, auto-refresh indicator text, mask toggle tooltip, empty/error strings translated.
- **Mobile:** Secondary (clinic tool); table scrollable; status badges and action buttons remain visible; reduced columns on narrow screen.

## Feature 2.3 — Notifications

### Story 2.3.1 [OPEN]
**As a** Patient,
**I want to** receive a WhatsApp (or SMS fallback) confirmation and reminder for my appointment,
**so that** I don't forget my scheduled visit — without any PHI appearing in the message body.

**Backend AC:**
- Notification triggers: `appointment.booked` (immediate), `appointment.reminder` (24h before), `appointment.reminder` (2h before).
- Message body is system-locked template: `[Clinic Name] — Kode Janji: [REF_CODE], Tanggal: [DATE], Jam: [TIME]` — NO patient name, doctor name, specialty, or diagnosis in body; full PHI visible only in authenticated portal.
- Delivery via WhatsApp Business API (primary); SMS gateway (fallback if WhatsApp delivery fails after 60 s).
- Delivery status logged per notification; failures visible to Branch Manager.
- Templates stored per locale; `id-ID` and `en-US` required at launch.

**Frontend AC:**
- Notification templates are system-managed (not editable by clinic staff — PHI leakage prevention).
- Route: `/clinic/settings/notifications` (read-only template preview for Branch Manager).
- Preview shows template for each trigger in each locale; "Send Test" button sends to Branch Manager's own number.
- Patient portal: `/patient/notifications` — notification history list; date, type, delivery status.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/settings/notifications` (staff template preview) | `#/patient/notifications` (patient notification history)
- **Portal:** Both
- **Layout:**
  - Clinic: sidebar nav (active: Pengaturan > Notifikasi) + main content; read-only template preview cards; "Kirim Tes" (Send Test) button per template.
  - Patient: mobile-first; notification history list; bottom navigation bar.
- **Components:**
  - **Clinic side:** `FlexCard` per notification template (trigger name, locale, preview text, "Kirim Tes" button); `FlexSelect` for locale preview toggle (ID / EN); `FlexAlert` for test send feedback
  - **Patient side:** `FlexCard` per notification entry (date, type label, delivery status badge); `FlexBadge` delivery status (Terkirim / Gagal); bottom nav bar
- **Key interactions:**
  - Clinic: templates are read-only (no PHI leakage); "Kirim Tes" sends to Branch Manager's own number; locale toggle switches template preview language.
  - Banner note: "Template ini dikunci untuk mencegah kebocoran data pasien." (These templates are locked to prevent patient data leakage.)
  - Patient: notification history shows appointment reminders and confirmations by date; tapping notification card navigates to relevant appointment (`#/patient/appointments/:id`).
- **Empty state (patient):** "Belum ada notifikasi." (No notifications yet.)
- **Error state (clinic test send):** `FlexAlert` "Tes gagal dikirim ke [number]" (Test failed to send to [number]).
- **i18n:** Template trigger labels, locale selector, template preview text (ID/EN), patient notification type labels, delivery status labels, empty/error strings translated.
- **Mobile:** Patient side is primary; clinic settings side is secondary; template cards full-width on mobile.

## Feature 2.4 — Waitlist Management

### Story 2.4.1 [OPEN]
**As a** Patient,
**I want to** join a waitlist for a fully-booked slot,
**so that** I am automatically offered the slot if a cancellation occurs.

**Backend AC:**
- `POST /api/v1/patients/me/waitlist` — auth: Patient; payload: `branch_id`, `provider_id`, `preferred_date_range`, `appointment_type`.
- Waitlist entries are FIFO per slot; when a slot is released (cancellation), first matching waitlist patient receives a WhatsApp/SMS notification (PHI-safe template) with a time-limited claim link (15-minute window).
- If claim window expires, next waitlist patient is notified.
- `DELETE /api/v1/patients/me/waitlist/:entry_id` — patient can remove themselves.

**Frontend AC:**
- Route: `/patient/waitlist`
- Waitlist entries: clinic/branch name, preferred date range, status (Waiting / Offered / Expired / Removed).
- "Leave Waitlist" button per entry.
- Offer notification: in-app banner + WhatsApp/SMS; offer page shows slot details + "Confirm Booking" / "Decline" buttons with 15-minute countdown timer.
- All strings in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/patient/waitlist`
- **Portal:** Patient Portal
- **Layout:** Mobile-first; waitlist card list; bottom navigation bar; waitlist offer appears as in-app banner + dedicated offer page.
- **Components:**
  - `FlexCard` — per waitlist entry: clinic/branch name, preferred date range, appointment type, status badge
  - `FlexBadge` — status: Menunggu (Waiting, grey) / Ditawarkan (Offered, amber) / Kedaluwarsa (Expired, red) / Dihapus (Removed, grey)
  - `FlexButton` — "Keluar Antrean" (Leave Waitlist) per entry
  - `FlexAlert` — in-app offer banner (amber, full-width) when slot is offered; "Lihat Penawaran" (View Offer) CTA
  - `FlexCard` — offer page (`#/patient/waitlist/offer/:entry_id`): slot details, "Konfirmasi Booking" (Confirm Booking) and "Tolak" (Decline) buttons, countdown timer
  - `FlexProgress` — 15-minute countdown progress bar on offer page
- **Key interactions:**
  - Offer arrives: in-app banner + WhatsApp/SMS; banner shows clinic name + slot date/time; "Lihat Penawaran" navigates to offer page.
  - Offer page: slot details + 15-minute countdown; "Konfirmasi Booking" → booking confirmed, status updated to Dikonfirmasi; "Tolak" → entry status Kedaluwarsa.
  - Countdown expires: offer page shows "Penawaran kedaluwarsa" (Offer expired); entry status updates.
  - "Keluar Antrean": confirmation modal "Yakin ingin keluar dari antrean ini?" (Sure you want to leave this waitlist?).
- **Empty state:** "Anda tidak sedang dalam antrean apapun." (You are not on any waitlists.)
- **Error state:** Booking confirmation failure: `FlexAlert` "Konfirmasi gagal. Slot mungkin sudah diambil." (Confirmation failed. Slot may already be taken.)
- **i18n:** Status badge labels, offer banner text, offer page text, countdown label, action button labels, modal text, empty/error strings translated (ID default).
- **Mobile:** Primary; full-width cards; offer banner full-width sticky at top; countdown progress bar prominently displayed; offer page full-screen.

## Story Count: Feature 2.1 (3) + 2.2 (3) + 2.3 (1) + 2.4 (1) = **8 stories**
