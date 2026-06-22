---
artifact_id: epic-07-patient-portal
status: active
version: 2
module: healthcare (primary), cross-module
launch_phase: GA (base features) + progressive as sub-modules activate
producer: A3 Product Owner
upstream: vision-02, research-02
created: 2026-06-21
---

# Epic 07 — Patient Portal

**Module:** Patient-facing surface spanning `healthcare` base and all sub-modules. Backend functionality lives in the relevant sub-module; this epic describes the patient's view and experience.
**Launch Phase:** Core (7.1, 7.2) ships at GA. 7.3 and 7.4 become relevant as sub-modules activate.
**Summary:** Patient profile and health summary, appointment management, cross-clinic records access, and clinic ratings.

---

## Feature 7.1 — Patient Profile & Health Summary

### Story 7.1.1 [OPEN]
**As a** Patient,
**I want to** view and update my personal profile and see a summary of my recent health activity,
**so that** I can keep my information current and understand my care history at a glance.

**Backend AC:**
- `GET /api/v1/patients/me/profile` — auth: Patient; returns platform-owned demographics (name, DOB, phone, email, locale, gender).
- `PUT /api/v1/patients/me/profile` — auth: Patient; updatable fields: email, locale preference, address; name and DOB changes require identity re-verification workflow (future scope — blocked for v1, show "contact support" link).
- `GET /api/v1/patients/me/summary` — returns: count of past encounters (across all clinics patient has visited), active prescriptions count, upcoming appointments count, last clinic visited (name + date).
- All reads emit `patient.profile_accessed` audit event.

**Frontend AC:**
- Route: `/patient/profile`
- Profile card: name, DOB, phone (masked), email, locale selector.
- Health summary widgets: upcoming appointments (count + next appointment date), recent visits (last 3 clinics), active prescriptions (count), pending lab results (count).
- "Edit" mode for updatable fields; name/DOB change: tooltip "Contact your clinic to update name or date of birth."
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/patient/profile`
- **Portal:** Patient Portal
- **Layout:** Mobile-first; profile card at top; health summary widget row (2×2 grid of summary cards); bottom navigation bar (Beranda / Janji / Rekam Medis / Profil — Home / Appointments / Records / Profile).
- **Components:**
  - `FlexCard` — profile card: avatar initial, name, DOB, phone (masked — ••••1234), email, locale selector
  - `FlexSelect` — locale selector (ID / EN) inline within profile card
  - `FlexGrid` — 2×2 health summary widget grid: Janji Mendatang (Upcoming Appt), Kunjungan Terakhir (Last Visit), Resep Aktif (Active Prescriptions), Hasil Lab Tertunda (Pending Lab Results)
  - `FlexCard` — each summary widget: count/value, label, CTA link to detail page
  - `FlexButton` — "Edit Profil" mode toggle; "Simpan" on save; "Batal"
  - `FlexTooltip` — on name/DOB field in edit mode: "Hubungi klinik Anda untuk mengubah nama atau tanggal lahir." (Contact your clinic to update name or date of birth.)
  - `FlexAlert` — save success/failure
- **Key interactions:**
  - "Edit Profil": enables email and address fields; name + DOB read-only with tooltip.
  - Locale change in profile card: instant re-render; preference saved to profile.
  - Summary widget tap: navigates to relevant section (e.g., `#/patient/appointments` for upcoming).
  - Phone shown masked by default (last 4 digits visible); no unmask toggle (PHI — patient's own but masked for public screen sharing).
- **Empty state (widgets):** Each widget shows "0" or "Tidak ada" (None) with descriptive sub-label.
- **Error state:** Save failure: `FlexAlert` below profile card "Gagal menyimpan perubahan profil" (Failed to save profile changes).
- **i18n:** Profile field labels, widget labels and CTA links, tooltip text, edit/save/cancel button labels, phone mask format, date format in patient locale, empty/error strings translated (ID default).
- **Mobile:** Primary; profile card full-width; 2×2 grid adapts to 2 columns on narrow screen; bottom nav always visible.

### Story 7.1.2 [OPEN]
**As a** Patient,
**I want to** see a list of my past encounters across all clinics I have visited,
**so that** I have a longitudinal view of my care.

**Backend AC:**
- `GET /api/v1/patients/me/encounters?page=&from=&to=` — auth: Patient; returns encounters across all tenants the patient has a record at; each entry includes: `clinic_name`, `branch_name`, `encounter_date`, `provider_name` (first name + specialty), `encounter_summary` (if released by clinic).
- Encounter summary is a clinic-controlled field; clinics opt-in to releasing a patient-readable summary.
- Access emits `patient.encounters_accessed` audit event.

**Frontend AC:**
- Route: `/patient/records/visits`
- Timeline list: chronological, most recent first; grouped by year.
- Each item: clinic name, branch, date, provider name, summary (or "Summary not shared by clinic" if not released).
- Filter: date range, clinic name.
- All labels in active locale; dates in patient's locale format.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/patient/records/visits`
- **Portal:** Patient Portal
- **Layout:** Mobile-first; year-grouped timeline list; filter bar (date range, clinic name); bottom navigation bar.
- **Components:**
  - `FlexSidebar` — not applicable (patient portal uses bottom nav)
  - `FlexToolbar` — filter row: date range `FlexDatepicker`, clinic name `FlexInput` (search)
  - `FlexCard` — per encounter entry: clinic name + branch, date, doctor name + specialty, summary text (or "Ringkasan tidak dibagikan oleh klinik" — Summary not shared by clinic)
  - `FlexBadge` — year divider header between groups
  - `FlexPagination` — load more (infinite scroll on mobile)
  - `FlexAlert` — filter active indicator (showing N results)
- **Key interactions:**
  - Timeline most-recent-first; year headers as dividers.
  - Encounter card shows summary if released by clinic; grey italic text if not: "Ringkasan tidak dibagikan oleh klinik ini." (Summary not shared by this clinic.)
  - Filter: date range and clinic name are additive; "Hapus Filter" (Clear Filter) chip resets.
  - No PHI beyond patient's own data; patient viewing own records.
- **Empty state:** "Belum ada riwayat kunjungan." (No visit history yet.)
- **Error state:** "Gagal memuat riwayat kunjungan. Tarik untuk memuat ulang." (Failed to load visit history. Pull to refresh.)
- **i18n:** Filter labels, year divider format, doctor label format, summary-not-shared text, date format in patient locale (e.g., "21 Juni 2026"), empty/error strings translated.
- **Mobile:** Primary; card full-width; year headers sticky while scrolling; filter collapses to icon button → bottom sheet.

## Feature 7.2 — My Appointments

### Story 7.2.1 [OPEN]
**As a** Patient,
**I want to** view all my upcoming and past appointments across all clinics from a single screen,
**so that** I have a unified calendar of my healthcare.

**Backend AC:**
- `GET /api/v1/patients/me/appointments?status=upcoming|past&page=` — auth: Patient; returns appointments across all tenants; each entry: `clinic_name`, `branch_name`, `provider_name`, `appointment_type`, `datetime`, `status`, `appointment_id`.
- Upcoming: status in `confirmed`, `checked_in`; Past: `completed`, `no_show`, `cancelled`.

**Frontend AC:**
- Route: `/patient/appointments`
- Tabs: Upcoming / Past.
- Appointment card: clinic + branch name, doctor name, type, date/time, status badge.
- Upcoming: "Reschedule" and "Cancel" action links (delegates to scheduling module flow, Story 2.2.2).
- Past: "Book Again" shortcut (pre-fills same clinic/doctor in booking flow).
- All labels in active locale; datetimes in patient's local timezone.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/patient/appointments`
- **Portal:** Patient Portal
- **Layout:** Mobile-first; tabs (Mendatang / Selesai — Upcoming / Past); appointment card list per tab; bottom navigation bar (Janji tab active).
- **Components:**
  - `FlexTabs` — Mendatang / Selesai tabs with count badges
  - `FlexCard` — appointment card: clinic + branch name, doctor name, appointment type, date/time, status badge; action links below
  - `FlexBadge` — status badge: Dikonfirmasi (blue) / Check-In (green) / Selesai (teal) / Dibatalkan (grey) / Tidak Hadir (red)
  - `FlexButton` (text link style) — "Jadwalkan Ulang" (Reschedule) and "Batalkan" (Cancel) on upcoming cards; "Buat Ulang Janji" (Book Again) on past cards
  - `FlexPagination` — infinite scroll per tab
- **Key interactions:**
  - "Mendatang" tab default on page load.
  - "Jadwalkan Ulang": navigates to `#/patient/appointments/:id` (reschedule flow — Story 2.2.2).
  - "Batalkan": navigates to `#/patient/appointments/:id` (cancel flow — Story 2.2.2).
  - "Buat Ulang Janji" (past tab): navigates to booking flow `#/book/:clinic_slug/:branch_id` pre-filled with same clinic/doctor.
  - Date/time shown in patient's local timezone; if different from clinic timezone, note "(Zona waktu klinik: WIB)" below.
- **Empty state (Mendatang):** "Tidak ada janji mendatang. Temukan klinik dan buat janji." (No upcoming appointments. Find a clinic and book.) with "Temukan Klinik" (Find a Clinic) CTA.
- **Empty state (Selesai):** "Belum ada riwayat janji." (No appointment history yet.)
- **Error state:** "Gagal memuat janji. Tarik untuk memuat ulang." (Failed to load appointments. Pull to refresh.)
- **i18n:** Tab labels, status badge labels, action link text, date/time format in patient locale, timezone note, empty state text + CTA, error string translated.
- **Mobile:** Primary; full-width cards; action links below card content; bottom nav visible; infinite scroll.

## Feature 7.3 — My Records Access

### Story 7.3.1 [OPEN]
**As a** Patient,
**I want to** access my lab results and prescriptions from clinics I have visited,
**so that** I have a complete digital record of my care without calling each clinic.

**Backend AC:**
- `GET /api/v1/patients/me/prescriptions` — auth: Patient; returns active and past prescriptions from all tenants; each entry: `clinic_name`, `drug_name`, `dose`, `frequency`, `duration`, `dispensed_at`, `status` (active/completed/cancelled).
- `GET /api/v1/patients/me/lab-results` — same cross-tenant aggregation (see Story 5.3.2).
- Data limited to tenants where patient has a confirmed encounter; no cross-tenant access without encounter link.
- Each aggregation access emits audit event per contributing tenant.

**Frontend AC:**
- Route: `/patient/records` with sub-tabs: Lab Results / Prescriptions.
- Lab Results tab: list grouped by clinic and date; interpretation badge; download PDF.
- Prescriptions tab: active prescriptions highlighted at top; past prescriptions below.
- Empty state: "No records yet — visit a clinic to see your results here."
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/patient/records`
- **Portal:** Patient Portal
- **Layout:** Mobile-first; sub-tabs (Hasil Lab / Resep — Lab Results / Prescriptions); content per tab; bottom navigation bar (Rekam Medis active).
- **Components:**
  - `FlexTabs` — Hasil Lab / Resep tabs (reuses Epic 05 Story 5.3.2 for Lab Results tab)
  - **Prescriptions tab:**
    - `FlexCard` — active prescriptions section header "Resep Aktif" (Active Prescriptions) with count badge; active prescriptions listed first
    - `FlexCard` — per prescription: clinic name, drug name, dose, frequency, duration, dispensed date, status badge
    - `FlexBadge` — status badge: Aktif (green) / Selesai (grey) / Dibatalkan (red)
    - `FlexPagination` — load more for past prescriptions
  - `FlexAlert` — cross-tenant data notice: "Data dari semua klinik yang pernah Anda kunjungi." (Data from all clinics you have visited.)
- **Key interactions:**
  - Prescriptions tab: active prescriptions pinned at top; past prescriptions below in reverse chronological order.
  - Lab Results tab: same as Story 5.3.2.
  - Cross-tenant aggregation: all clinics the patient has an encounter with are included; data limited to tenants with confirmed encounters.
  - No cross-clinic PHI mixing; each entry clearly labels its source clinic.
- **Empty state:** "Belum ada rekam medis. Kunjungi klinik untuk melihat data Anda di sini." (No records yet. Visit a clinic to see your data here.) — shown on both tabs if empty.
- **Error state:** Per tab: "Gagal memuat data. Tarik untuk memuat ulang." (Failed to load data. Pull to refresh.)
- **i18n:** Tab labels, prescription status badges, active section header, cross-tenant notice, date/dispensed format in patient locale, empty/error strings translated.
- **Mobile:** Primary; full-width cards; active prescriptions visually distinguished (colored border or top section); bottom nav visible.

## Feature 7.4 — Clinic Reviews & Ratings

### Story 7.4.1 [OPEN]
**As a** Patient,
**I want to** submit a rating and review for a clinic branch after my visit,
**so that** other patients can make informed decisions and clinics get actionable feedback.

**Backend AC:**
- `POST /api/v1/patients/me/reviews` — auth: Patient; payload: `branch_id`, `encounter_id` (must be `completed` encounter for this patient at this branch), `rating` (1–5 integer), `review_text` (optional, ≤ 500 chars); one review per encounter.
- Review is pending moderation (Platform Admin can remove violating content); visible after 24h if not moderated.
- `GET /api/v1/clinics/:clinic_slug/branches/:branch_id/reviews?page=` — public; returns approved reviews; no patient PHI in response (reviewer shown as "Patient, [month] [year]").
- Review creation emits `review.submitted` audit event.

**Frontend AC:**
- Route: post-visit NPS prompt in patient portal (`/patient/appointments/:appointment_id/review`); also accessible from `/patient/records/visits`.
- Rating: 5-star selector; review text (optional, character counter).
- Trigger: NPS prompt shown 2 hours after appointment status = `completed`.
- Clinic profile public page (`/clinics/:slug/:branch`) shows average rating, review count, and paginated reviews.
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/patient/appointments/:appointment_id/review` (NPS prompt) | `#/patient/records/visits` (secondary entry) | `#/clinics/:slug/:branch` (public rating display)
- **Portal:** Patient Portal (submission) + Public (display)
- **Layout:**
  - Rating submission: mobile-first; NPS prompt appears 2 hours post-visit as in-app card overlay or push notification; dedicated page is single-card centered layout.
  - Public display: within clinic profile page tabs (Ulasan tab).
- **Components:**
  - `FlexCard` — NPS prompt card: clinic name, visit date, "Bagaimana pengalaman Anda?" (How was your experience?)
  - `FlexBadge` — 5-star rating selector (large tappable stars; 44 px each)
  - `FlexTextarea` — optional review text (max 500 chars); character counter
  - `FlexButton` — "Kirim Ulasan" (Submit Review) primary; "Lewati" (Skip) text link
  - **Public display (clinic profile):**
    - `FlexCard` — average rating card: star display, average score, total review count
    - `FlexCard` — per review: "Pasien, [Bulan] [Tahun]" (Patient, [Month] [Year]); star rating; review text; clinic response (if any)
    - `FlexPagination` — load more reviews
- **Key interactions:**
  - NPS prompt: appears 2h after appointment status = `completed`; can be "Lewati"d; shown max once per encounter.
  - Star selector: tapping star sets rating; tapping again deselects (forces re-selection).
  - Review text: optional; character counter shows "450/500 karakter tersisa" (450/500 characters remaining).
  - "Kirim Ulasan" → success "Terima kasih atas ulasan Anda!" (Thank you for your review!); review enters 24h moderation.
  - Public page: reviews show after moderation; no patient PHI (shown as "Pasien, Juni 2026").
- **Empty state (public):** "Belum ada ulasan. Jadilah yang pertama!" (No reviews yet. Be the first!)
- **Error state:** Submit failure: `FlexAlert` "Gagal mengirim ulasan. Coba lagi." (Failed to submit review. Try again.)
- **i18n:** Prompt text, star labels (1-5 description in active locale), review text placeholder, character counter format, submit/skip labels, success message, public reviewer format, empty/error strings translated.
- **Mobile:** Primary; NPS prompt full-width overlay card; stars large (44 px); textarea comfortable height; "Kirim Ulasan" 56 px full-width pinned bottom.

### Story 7.4.2 [OPEN]
**As a** Branch Manager,
**I want to** respond to patient reviews,
**so that** we can acknowledge feedback publicly and show prospective patients that we are responsive.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/reviews/:review_id/response` — auth: Branch Manager, Clinic Owner; one response per review; response is publicly visible.
- Response creation emits `review.response_posted` audit event.
- Response is also pending moderation.

**Frontend AC:**
- Route: `/clinic/reviews` (Branch Manager / Clinic Owner view)
- Review list with rating, text, date, and response status.
- "Reply" button → text area → "Post Response".
- Published responses shown on public clinic profile page below the original review.
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/reviews`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Ulasan Klinik) + main content; review list with rating, text, date, response status; "Balas" (Reply) button per unresponded review.
- **Components:**
  - `FlexSidebar` — nav; branch context badge (reviews are branch-scoped)
  - `FlexTable` (or `FlexCard` list) — review rows: Bintang, Teks Ulasan, Tanggal, Status Balasan; clickable row for detail
  - `FlexBadge` — response status: Belum Dibalas (Unanswered, amber) / Sudah Dibalas (Responded, green)
  - `FlexCard` — review detail expand: full review text + response area
  - `FlexTextarea` — response text area (on "Balas" click); max chars per clinic config
  - `FlexButton` — "Balas" (Reply) per unanswered review; "Posting Balasan" (Post Response) in reply area; "Batal"
  - `FlexAlert` — post success; moderation notice "Balasan Anda dalam review moderasi (maks. 24 jam)" (Your response is under moderation — max 24h)
  - `FlexFilter` (tab or select) — filter: Semua / Belum Dibalas / Sudah Dibalas
- **Key interactions:**
  - "Balas": expands text area below review row; "Posting Balasan" submits; success alert with moderation notice.
  - Posted response appears on public clinic profile page below original review after moderation.
  - Branch filter: Clinic Owner can switch between branches; Branch Manager sees only their branch.
  - Review text longer than 3 lines truncated with "Lihat selengkapnya" (See more) expand.
- **Empty state:** "Belum ada ulasan untuk cabang ini." (No reviews for this branch yet.)
- **Error state:** Post failure: `FlexAlert` in reply area "Gagal memposting balasan" (Failed to post response).
- **i18n:** Filter labels, status badges, response text placeholder, post/cancel button labels, moderation notice, success/error messages, date format, empty state text translated.
- **Mobile:** Secondary (staff tool); list collapses to cards; reply text area full-width; post button full-width.

## Story Count: Feature 7.1 (2) + 7.2 (1) + 7.3 (1) + 7.4 (2) = **6 stories**
