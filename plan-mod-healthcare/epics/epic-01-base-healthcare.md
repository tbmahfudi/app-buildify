---
artifact_id: epic-01-base-healthcare
status: active
version: 2
module: healthcare
launch_phase: GA
producer: A3 Product Owner
upstream: vision-02, research-02
created: 2026-06-21
---

# Epic 01 — Base Healthcare Module

**Module:** `healthcare` (required by all sub-modules)
**Launch Phase:** GA
**Summary:** Foundation layer — clinic onboarding, multi-branch management, PHI data models,
patient self-registration and clinic discovery, platform RBAC, audit/compliance, and i18n framework.

---

## Feature 1.1 — Clinic Registration & Onboarding

### Story 1.1.1 [OPEN]
**As a** Clinic Owner,
**I want to** register my clinic on the platform and complete DPA acceptance,
**so that** my clinic is provisioned as a tenant and I can activate clinical modules.

**Backend AC:**
- `POST /api/v1/clinics/register` — public endpoint; creates `tenant` + first `branch` (branch-001); requires: clinic name, specialty, city, locale preference, owner email + phone OTP.
- DPA acceptance is recorded with timestamp, IP, user agent before tenant is set to `status: active`; no PHI module can be activated without `dpa_accepted: true`.
- Tenant provisioning emits `clinic.registered` audit event (immutable log, PP 71/2019).
- Response includes `tenant_id`, `branch_id`, and activation token.

**Frontend AC:**
- Route: `/onboarding/register`
- Clinic profile wizard: 4 steps — account creation → clinic details → DPA review/accept → confirmation.
- DPA text rendered in selected locale (Bahasa Indonesia default); plain-language summary above the legal text.
- Locale toggle (id-ID / en-US) available on every step.
- Empty/error state: inline field validation; OTP resend with 60-second cooldown.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/onboarding/register`
- **Portal:** Clinic Portal (public onboarding flow, pre-authentication)
- **Layout:** Full-page centered wizard; no sidebar; progress stepper at top (4 steps: Akun → Profil Klinik → Persetujuan DPA → Konfirmasi). Desktop max-width 640 px card; mobile full-screen.
- **Components:**
  - `FlexStepper` — 4-step horizontal progress indicator
  - `FlexForm` — field groups per step with inline validation
  - `FlexInput` — clinic name, email, phone, OTP boxes
  - `FlexSelect` — specialty (searchable dropdown), locale (ID / EN)
  - `FlexButton` — primary "Lanjut" (Next), secondary "Kembali" (Back)
  - `FlexModal` — DPA full text with plain-language summary panel (step 3)
  - `FlexAlert` — OTP resend countdown, validation errors
- **Key interactions:**
  - Step 1: user enters email + phone → OTP sent via WhatsApp; 6-box OTP input with auto-focus progression; resend enabled after 60-second countdown.
  - Step 2: clinic name, specialty, city, locale preference entered.
  - Step 3: DPA text rendered in selected locale; plain-language summary above legal text; "Saya Menyetujui" (I Agree) checkbox must be checked to proceed.
  - Step 4: confirmation screen with `tenant_id` reference code and "Mulai Setup Klinik" (Start Clinic Setup) button.
  - Locale toggle (ID / EN) visible on every step header — switching re-renders all labels immediately.
- **Empty state:** N/A (creation flow).
- **Error state:** Inline field errors below each input in active locale; OTP mismatch shows "Kode tidak valid, coba lagi" (Invalid code, try again); server error shows `FlexAlert` banner "Terjadi kesalahan, silakan coba lagi" (An error occurred, please try again).
- **i18n:** All step labels, field labels, placeholder text, DPA plain-language summary, button labels, OTP messages, and error strings must be translated (ID / EN). DPA legal text stored per locale.
- **Mobile:** Mobile-first; each step is full-screen scroll; stepper collapses to "Langkah 1 dari 4"; OTP boxes large (48 px tap target); "Lanjut" button pinned to bottom.

### Story 1.1.2 [OPEN]
**As a** Clinic Owner,
**I want to** configure my clinic profile (name, logo, specialty, contact details) after registration,
**so that** my clinic appears correctly in patient-facing search results.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/profile` — auth: Clinic Owner role; validates logo file type (PNG/JPG ≤ 2 MB); specialty from controlled vocabulary list.
- Logo stored in tenant-isolated object storage; URL returned in profile response.
- Profile changes logged to audit trail with `changed_by` user ID.

**Frontend AC:**
- Route: `/clinic/settings/profile`
- Editable fields: clinic name, specialty (searchable dropdown), logo upload with preview, contact phone, website (optional).
- All labels and validation messages in active locale.
- Unsaved-changes warning on navigation away.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/settings/profile`
- **Portal:** Clinic Portal
- **Layout:** Sidebar navigation (active: Settings > Profil Klinik) + main content area; two-column form on desktop (labels left, fields right); single-column on mobile.
- **Components:**
  - `FlexSidebar` — clinic portal navigation; branch context badge in header
  - `FlexForm` — editable profile fields
  - `FlexInput` — clinic name, contact phone, website URL
  - `FlexSelect` — specialty (searchable dropdown)
  - `FlexFileUpload` — logo upload with image preview (PNG/JPG ≤ 2 MB); drag-and-drop on desktop
  - `FlexButton` — "Simpan" (Save), "Batal" (Cancel)
  - `FlexAlert` — unsaved-changes warning banner on navigation away
  - `FlexBadge` — branch context indicator in header
- **Key interactions:**
  - User edits any field → unsaved-changes indicator appears in page header.
  - Logo upload: drag-and-drop or click; preview renders inline; file size/type error shown immediately.
  - "Simpan" → save confirmation toast (bottom-right); profile published to patient-facing search.
  - Navigating away with unsaved changes triggers `FlexModal` confirmation: "Perubahan belum disimpan. Keluar?" (Unsaved changes. Leave?).
  - PHI-sensitive field: none on this page (clinic profile only).
- **Empty state:** Fields empty on first setup; placeholder text in active locale for each field.
- **Error state:** Inline validation per field; logo type/size error inline under upload zone; API save error shows `FlexAlert` at top of form.
- **i18n:** All field labels, placeholders, validation messages, toast, and modal text translated (ID / EN). Specialty vocabulary list served in active locale.
- **Mobile:** Secondary use case (staff likely on desktop); single-column layout; logo upload via file picker (no drag-and-drop).

## Feature 1.2 — Multi-Branch Management

### Story 1.2.1 [OPEN]
**As a** Clinic Owner,
**I want to** add a new branch to my clinic tenant,
**so that** I can manage multiple clinic locations under one account.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches` — auth: Clinic Owner; required fields: branch name, address, city, timezone (WIB/WITA/WIT), operating hours, contact number.
- New `branch_id` generated; all records created within branch carry both `tenant_id` and `branch_id`.
- Branch creation emits `branch.created` audit event.
- Max branches per tenant is platform-configurable (default: 20).

**Frontend AC:**
- Route: `/clinic/branches/new`
- Form: branch name, address (street, city, province, postal code), timezone selector (defaults to WIB), operating hours grid (Mon–Sun, open/close times), contact number.
- Success state: confirmation banner; redirect to branch settings page.
- All labels in active locale; timezone labels show both code (WIB) and offset (UTC+7).

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/branches/new`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Cabang > Tambah Cabang) + main content; single-page form with logical sections (Informasi Cabang, Alamat, Jam Operasional); desktop max-width 800 px.
- **Components:**
  - `FlexSidebar` — clinic portal nav; active branch context shown
  - `FlexForm` — sectioned form
  - `FlexInput` — branch name, street address, city, province, postal code, contact number
  - `FlexSelect` — province (dropdown), timezone (WIB UTC+7 / WITA UTC+8 / WIT UTC+9; label shows both code and offset)
  - `FlexGrid` — operating hours grid (Mon–Sun rows; open/close time pickers per row; toggle "Tutup" (Closed) per day)
  - `FlexButton` — "Simpan Cabang" (Save Branch), "Batal"
  - `FlexAlert` — success confirmation banner after save
- **Key interactions:**
  - Timezone selector defaults to WIB; changing timezone re-renders operating hours time labels to show local time.
  - Operating hours: each day row has toggle "Buka" / "Tutup"; if "Buka", open/close time pickers are enabled.
  - On save: success banner "Cabang berhasil ditambahkan" (Branch successfully added); redirect to branch settings page.
- **Empty state:** N/A (creation form).
- **Error state:** Inline validation; max-branch limit error: `FlexAlert` "Batas cabang telah tercapai" (Branch limit reached).
- **i18n:** All labels, timezone labels (code + offset in active locale), day names (Mon–Sun abbreviated per locale), validation messages translated.
- **Mobile:** Secondary; grid collapses to accordion per day for operating hours; timezone label truncated to code only.

### Story 1.2.2 [OPEN]
**As a** Clinic Owner,
**I want to** assign staff members to specific branches with specific roles,
**so that** access control is enforced per branch and staff only see their branch's data.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/staff` — auth: Clinic Owner or Branch Manager; payload: user email or phone, role (Doctor/Nurse/Pharmacist/Lab Tech/Billing Staff).
- A user can hold different roles at different branches; `branch_staff` join table stores `(user_id, branch_id, role)`.
- Staff invitation email/WhatsApp sent in tenant's default locale.
- Assignment emits `staff.assigned` audit event with role and branch.

**Frontend AC:**
- Route: `/clinic/branches/:branch_id/staff`
- Staff list with role badges; "Invite Staff" button opens modal: email input + role selector.
- Shows pending invitations with resend/revoke options.
- Role labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/branches/:branch_id/staff`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Cabang > Tim) + main content; staff list table above; "Undang Staf" (Invite Staff) button top-right.
- **Components:**
  - `FlexSidebar` — nav; branch context badge shows active branch name
  - `FlexTable` — columns: Nama, Email, Peran (Role), Status (Aktif / Menunggu), Tindakan
  - `FlexBadge` — role labels per row (color-coded per role); pending invitation badge
  - `FlexModal` — invite modal: email/phone input + role `FlexSelect`
  - `FlexButton` — "Undang Staf", "Kirim Ulang" (Resend), "Cabut" (Revoke) per row
  - `FlexAlert` — success/error feedback
- **Key interactions:**
  - "Undang Staf" opens `FlexModal`; user enters email/phone + selects role from locale-translated dropdown.
  - Submit sends invitation via email/WhatsApp in tenant's default locale.
  - Pending invitations show "Menunggu" (Pending) badge with "Kirim Ulang" and "Cabut" actions.
  - PHI-sensitive: staff names/emails are not PHI but the page includes a mask toggle for screen privacy in crowded environments.
- **Empty state:** "Belum ada staf terdaftar. Undang staf untuk memulai." (No staff registered yet. Invite staff to get started.)
- **Error state:** Invalid email format inline; API error in modal footer as `FlexAlert`.
- **i18n:** Role labels, table headers, action labels, invitation modal labels, status badges, empty/error strings translated.
- **Mobile:** Table collapses to card list; each card shows name, role badge, status, action button.

### Story 1.2.3 [OPEN]
**As a** Branch Manager,
**I want to** configure branch-specific settings (operating hours, appointment types, locale override),
**so that** my branch operates independently within the tenant.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/settings` — auth: Clinic Owner or Branch Manager for that branch.
- Overridable settings: operating hours, appointment types, locale, timezone; inherit from tenant defaults if not set.
- Settings changes logged to audit trail.

**Frontend AC:**
- Route: `/clinic/branches/:branch_id/settings`
- Sections: Operating Hours, Appointment Types, Locale & Timezone.
- "Inheriting from clinic defaults" indicator per field with override toggle.
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/branches/:branch_id/settings`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Cabang > Pengaturan) + main content; tabbed sections: Jam Operasional, Jenis Janji, Bahasa & Zona Waktu.
- **Components:**
  - `FlexSidebar` — nav; active branch indicator in header
  - `FlexTabs` — three setting sections
  - `FlexForm` — settings per tab
  - `FlexSelect` — locale, timezone
  - `FlexGrid` — operating hours (same as 1.2.1)
  - `FlexBadge` — "Mewarisi dari klinik" (Inheriting from clinic) indicator per field group
  - `FlexButton` — toggle "Timpa" (Override) per field group; "Simpan"
- **Key interactions:**
  - Each field group shows "Mewarisi dari klinik" badge if not overridden; "Timpa" button enables edit mode for that group.
  - Reverting an override shows confirmation modal "Kembalikan ke default klinik?" (Revert to clinic defaults?).
  - Changes logged to audit trail; no PHI on this page.
- **Empty state:** N/A (settings always populated with inherited defaults).
- **Error state:** Inline validation; save error `FlexAlert` at tab top.
- **i18n:** All section labels, field labels, override/inherit indicators, button labels, modal text translated.
- **Mobile:** Secondary; tabs collapse to accordion; override toggles remain functional.

## Feature 1.3 — PHI Data Models

### Story 1.3.1 [OPEN]
**As a** clinical staff member (Doctor or Nurse),
**I want to** create and view a patient record scoped to my branch,
**so that** patient PHI is correctly isolated and I can access it for care.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/patients` — auth: Doctor, Nurse, or Branch Manager; required fields: full name (KTP), date of birth, phone, gender, NIK (optional).
- Patient record carries `tenant_id` + `branch_id`; row-level security policy prevents cross-branch reads without explicit cross-branch role.
- Patient creation emits `patient.created` PHI audit event with `actor_id`, `tenant_id`, `branch_id`, timestamp.
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/patients/:patient_id` — returns patient profile; 403 if caller's branch_id does not match (unless cross-branch role).

**Frontend AC:**
- Route: `/clinic/patients/new` and `/clinic/patients/:patient_id`
- New patient form: name, DOB, phone (WhatsApp), NIK (optional), gender, address (optional).
- Patient detail page: demographics panel, encounter history list (most recent first), active prescriptions (if pharmacy module active).
- Empty state for encounter history: "No visits recorded yet."
- All labels and PHI field descriptions in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/patients/new` (creation) | `#/clinic/patients/:patient_id` (detail)
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Pasien) + main content. New patient: single-page form. Patient detail: two-panel — demographics sidebar (left 30%) + content area (right 70%) with tabs: Kunjungan, Resep Aktif.
- **Components:**
  - `FlexSidebar` — clinic portal nav; branch context badge
  - `FlexForm` — new patient form (name, DOB, phone, NIK optional, gender, address optional)
  - `FlexInput` — text inputs; phone with WhatsApp icon
  - `FlexSelect` — gender
  - `FlexDatepicker` — date of birth
  - `FlexTable` — encounter history list (most recent first): tanggal, dokter, ringkasan
  - `FlexCard` — active prescriptions (if pharmacy module active)
  - `FlexBadge` — PHI mask toggle button (eye icon) in demographics panel header — masks name, DOB, NIK on click for screen privacy
  - `FlexButton` — "Simpan Pasien", "Kunjungan Baru" (New Encounter)
- **Key interactions:**
  - PHI mask toggle: clicking eye icon in demographics panel replaces name, DOB, NIK with "●●●●●●"; toggle state per session, not persisted.
  - New patient form: NIK field marked optional with "(Opsional)" label; phone field with WhatsApp indicator.
  - Patient detail: encounter history sorted newest-first; clicking row navigates to encounter detail.
  - Branch context visible in header; patient record is branch-scoped.
- **Empty state (encounter history):** "Belum ada kunjungan tercatat." (No visits recorded yet.)
- **Error state:** Inline validation; duplicate phone check shows "Nomor ini sudah terdaftar di cabang ini" (This number is already registered at this branch).
- **i18n:** All form labels, gender options, tab labels, table headers, empty/error strings, PHI mask tooltip translated.
- **Mobile:** Secondary; demographics panel stacks above tabs; table collapses to card list.

### Story 1.3.2 [OPEN]
**As a** Doctor,
**I want to** open and document a patient encounter (SOAP notes),
**so that** the clinical record is complete and auditable.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/patients/:patient_id/encounters` — auth: Doctor; creates encounter with status `open`; records `provider_id`, `branch_id`, `tenant_id`, `started_at`.
- `PUT /api/v1/.../encounters/:encounter_id` — SOAP fields (subjective, objective, assessment, plan) as structured JSON + free text; encounter status transitions: open → in_progress → completed.
- Encounter record is immutable once `completed`; amendments create a new linked amendment record.
- All encounter writes emit PHI audit events.

**Frontend AC:**
- Route: `/clinic/encounters/:encounter_id`
- SOAP note editor: 4 labeled sections, each with structured inputs + free-text area.
- Auto-save every 30 seconds with "Saved" indicator.
- "Complete Encounter" button triggers confirmation modal.
- Locale-aware field labels; date/time in branch timezone.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Pasien > Kunjungan) + main content; split-pane — patient summary strip at top (name with mask toggle, DOB, branch); SOAP editor below in 4 labeled sections; action toolbar pinned to bottom.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexSplitPane` — top patient strip + SOAP editor area
  - `FlexForm` — 4 SOAP sections (Subjektif, Objektif, Penilaian, Rencana); each with structured inputs + `FlexTextarea`
  - `FlexBadge` — encounter status badge (Terbuka / Sedang Berjalan / Selesai); PHI mask toggle on patient strip
  - `FlexButton` — "Selesaikan Kunjungan" (Complete Encounter) — primary; triggers `FlexModal` confirmation
  - `FlexAlert` — auto-save indicator "Tersimpan" (Saved) / "Menyimpan..." (Saving...)
  - `FlexToolbar` — bottom: auto-save status, "Selesaikan Kunjungan" button
- **Key interactions:**
  - Auto-save every 30 seconds; "Tersimpan pukul [HH:MM]" shown in toolbar; manual save also available.
  - "Selesaikan Kunjungan" opens confirmation modal "Setelah diselesaikan, catatan tidak dapat diubah." (Once completed, notes cannot be edited.); confirm locks encounter.
  - PHI mask toggle on patient strip masks name and DOB from view.
  - Date/time displayed in branch timezone with timezone label (e.g., WIB).
  - Completed encounter: all fields become read-only; amendment link shown if amendment is needed (future flow).
- **Empty state:** SOAP sections start empty; structured fields show placeholder text per locale.
- **Error state:** Auto-save failure: `FlexAlert` warning "Penyimpanan otomatis gagal — periksa koneksi" (Auto-save failed — check connection); complete-encounter API error shown in modal.
- **i18n:** SOAP section labels, field placeholders, status badges, auto-save text, modal text, error strings, timezone labels translated.
- **Mobile:** Secondary; sections stack vertically; bottom toolbar remains pinned.

## Feature 1.4 — Patient Self-Registration & Clinic Discovery

### Story 1.4.1 [OPEN]
**As a** Patient (public user),
**I want to** create a platform account with phone OTP verification and consent in Bahasa Indonesia,
**so that** I can access health services across registered clinics.

**Backend AC:**
- `POST /api/v1/patients/register` — public endpoint; fields: full name (KTP), date of birth, phone (WhatsApp, OTP-verified), email (optional); consent version recorded with timestamp.
- OTP: 6-digit, 5-minute TTL, rate-limited (max 5 attempts per phone per 10 min); WhatsApp primary, SMS fallback.
- Consent record: `(patient_id, consent_version, accepted_at, ip, user_agent)` — immutable; PDPA-aligned.
- Universal patient profile created: platform-owned demographics; encounter data is tenant-owned (separate models).

**Frontend AC:**
- Route: `/register` (public)
- Step 1: phone number + OTP; Step 2: name, DOB, gender; Step 3: consent form.
- Consent form in Bahasa Indonesia by default with plain-language summary; toggle to English.
- OTP input: 6-box input with auto-focus progression; resend after 60 s.
- Mobile-first layout; Lighthouse performance ≥ 80 on mid-range Android / 4G.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/register` (public, unauthenticated)
- **Portal:** Patient Portal
- **Layout:** Mobile-first full-screen wizard; 3 steps (Nomor HP → Data Diri → Persetujuan); no sidebar; app logo + locale toggle in top bar; progress dots below header.
- **Components:**
  - `FlexStepper` — 3-step dot indicator (mobile-optimised)
  - `FlexForm` — fields per step
  - `FlexInput` — phone number (step 1), OTP 6-box (step 1), full name, NIK (step 2)
  - `FlexSelect` — gender (step 2)
  - `FlexDatepicker` — date of birth (step 2); mobile-native date picker on Android
  - `FlexCard` — consent summary card (step 3) with plain-language summary; full text expandable
  - `FlexCheckbox` — "Saya menyetujui ketentuan layanan dan kebijakan privasi" (I agree to terms and privacy policy)
  - `FlexButton` — "Lanjut" (Next) pinned to bottom; large tap target (56 px height); "Kirim Ulang OTP" (Resend OTP)
  - `FlexAlert` — OTP errors, validation errors
- **Key interactions:**
  - Step 1: phone entry → "Kirim OTP" (Send OTP); OTP arrives via WhatsApp; 6-box input with auto-advance on each digit; resend button activates after 60-second countdown.
  - Step 2: name, DOB (mobile date picker), gender.
  - Step 3: consent in Bahasa Indonesia (default); locale toggle switches consent text language; plain-language summary shown first, full text expandable; checkbox required.
  - On complete: welcome screen with patient name and "Temukan Klinik" (Discover Clinics) CTA.
  - Lighthouse performance target ≥ 80 on mid-range Android / 4G.
- **Empty state:** N/A (registration flow).
- **Error state:** OTP invalid: "Kode tidak sesuai. Sisa percobaan: [N]" (Code does not match. Attempts remaining: [N]); max attempts: "Terlalu banyak percobaan, coba lagi dalam 10 menit" (Too many attempts, try again in 10 minutes); field errors inline below each input.
- **i18n:** All step labels, field labels, placeholder text, consent plain-language summary, OTP messages, error strings translated (ID default / EN). Consent legal text stored per locale.
- **Mobile:** Primary; full-screen each step; OTP boxes 48 px minimum tap target; "Lanjut" button 56 px height, full-width, pinned bottom; bottom navigation hidden on registration flow.

### Story 1.4.2 [OPEN]
**As a** Patient,
**I want to** search for clinics by location and specialty,
**so that** I can find and book services at a nearby verified clinic.

**Backend AC:**
- `GET /api/v1/clinics/search?lat=&lng=&specialty=&city=&page=` — public endpoint; returns paginated list of active branches with clinic name, address, distance, specialties, operating status (open now / next open time).
- Results filtered to branches with `status: active` and `online_booking: true`.
- No PHI returned in search results.

**Frontend AC:**
- Route: `/discover` (public)
- Search bar with GPS location button; city/district text input fallback.
- Specialty filter chips (scrollable); "Open Now" toggle.
- Result cards: clinic brand name, branch address, distance, specialty tags, "Book Appointment" CTA.
- Empty state: "No clinics found nearby. Try expanding your search area." (in active locale).
- All strings in active locale (id-ID default).

---


#### Frontend (UILDC v1.0)

- **Route:** `#/discover` (public, authenticated patient)
- **Portal:** Patient Portal
- **Layout:** Mobile-first; top search bar (sticky); specialty filter chips row (horizontally scrollable); card list below; bottom navigation bar (Home, Janji, Rekam Medis, Profil).
- **Components:**
  - `FlexInput` — search bar with GPS location button (left icon) + city text fallback
  - `FlexCluster` — horizontally scrollable specialty filter chips
  - `FlexBadge` — "Buka Sekarang" (Open Now) toggle chip; active filters highlighted
  - `FlexCard` — clinic result card: logo, clinic name, branch address, distance, specialty tags, "Buat Janji" (Book Appointment) CTA button
  - `FlexSpinner` — loading state while fetching results
  - `FlexPagination` — load-more button (infinite scroll on mobile)
  - `FlexAlert` — location permission denied message
- **Key interactions:**
  - GPS button requests location; on grant, results sorted by distance; on deny: `FlexAlert` "Aktifkan lokasi atau ketik nama kota Anda" (Enable location or type your city name).
  - Typing in search bar triggers debounced search (300 ms).
  - Specialty chip tap filters results immediately; multiple chips can be active.
  - "Buka Sekarang" toggle filters to currently-open branches.
  - Card "Buat Janji" CTA navigates to `#/book/:clinic_slug/:branch_id`.
  - All results in active locale; distance in km.
- **Empty state:** "Tidak ada klinik ditemukan di sekitar Anda. Coba perluas area pencarian." (No clinics found nearby. Try expanding your search area.)
- **Error state:** Search API failure: "Gagal memuat hasil. Tarik untuk memuat ulang." (Failed to load results. Pull to refresh.)
- **i18n:** Search placeholder, filter chip labels, "Buka Sekarang", card labels (distance, specialty tags), empty/error strings, CTA button translated.
- **Mobile:** Primary; single-column card list; chips scroll horizontally; bottom nav always visible; pull-to-refresh on card list.

### Story 1.4.3 [OPEN]
**As a** Patient,
**I want to** view a clinic branch's public profile page,
**so that** I can learn about the clinic before booking.

**Backend AC:**
- `GET /api/v1/clinics/:clinic_slug/branches/:branch_id/profile` — public; returns: name, address, specialties, operating hours, available appointment types, doctor list (name + specialty only, no PHI), average rating.
- No internal IDs or PHI exposed.

**Frontend AC:**
- Route: `/clinics/:clinic_slug/:branch_slug`
- Sections: Clinic info, Operating hours, Doctors, Services, Ratings summary.
- "Book Appointment" CTA scrolls to appointment booking section (if scheduling module active).
- Operating hours displayed in patient's local timezone with "Open Now" / "Closes at HH:MM" badge.
- All content in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinics/:clinic_slug/:branch_slug` (public)
- **Portal:** Patient Portal (public profile, accessible before login)
- **Layout:** Mobile-first; hero section (clinic logo + name + specialty tags); tabbed sections below (Info, Jam Buka, Dokter, Layanan, Ulasan); sticky "Buat Janji" CTA bar pinned to bottom on mobile.
- **Components:**
  - `FlexCard` — hero card with clinic brand, specialty badges, distance (if location available)
  - `FlexTabs` — Info / Jam Buka (Hours) / Dokter / Layanan / Ulasan tabs
  - `FlexBadge` — "Buka Sekarang" / "Tutup — Buka [HH:MM]" (Open Now / Closed — Opens at) status badge; "Buka Sekarang" in green, "Tutup" in grey
  - `FlexCard` — doctor card (name + specialty only; no PHI)
  - `FlexTable` — operating hours (day, open time, close time) in patient's local timezone
  - `FlexButton` — "Buat Janji" (Book Appointment) — sticky CTA on mobile; primary button in hero section on desktop
  - `FlexPagination` — reviews tab
- **Key interactions:**
  - Timezone display: operating hours shown in patient's local timezone; footnote "Zona waktu klinik: [WIB/WITA/WIT]" (Clinic timezone: ...).
  - "Buat Janji" CTA scrolls to appointment booking section if scheduling module active; else navigates to scheduling flow `#/book/:clinic_slug/:branch_id`.
  - Unauthenticated user clicking "Buat Janji" redirected to `#/login` with return URL preserved.
  - Ratings tab shows average (star display), review count, and paginated review cards (no PHI — "Pasien, [bulan] [tahun]").
- **Empty state (reviews tab):** "Belum ada ulasan. Jadilah yang pertama memberikan ulasan!" (No reviews yet. Be the first to review!)
- **Error state:** Page load failure: full-page "Profil klinik tidak dapat dimuat. Coba lagi." (Clinic profile could not be loaded. Try again.)
- **i18n:** All section labels, tab names, operating hours day names, timezone labels, status badges, CTA text, review display format translated.
- **Mobile:** Primary; tabs scroll horizontally; sticky "Buat Janji" bar 56 px pinned to bottom above bottom nav; doctor cards in single-column list.

## Feature 1.5 — Platform RBAC

### Story 1.5.1 [OPEN]
**As a** Clinic Owner,
**I want to** have a role system that restricts each staff member to actions appropriate for their job,
**so that** PHI is accessed only by authorized personnel and branch data is isolated.

**Backend AC:**
- Roles: `clinic_owner` (all branches), `branch_manager` (assigned branches), `doctor` (assigned branches), `nurse` (assigned branches), `pharmacist` (assigned branches), `lab_tech` (assigned branches), `billing_staff` (assigned branches), `patient` (own records only).
- All API endpoints check `(caller_role, tenant_id, branch_id)` triple; middleware rejects mismatches with 403.
- Role assignments stored in `branch_staff` table; `clinic_owner` role spans all branches by policy.
- Role changes emit `rbac.role_changed` audit event.

**Frontend AC:**
- Route: `/clinic/team` (Clinic Owner / Branch Manager view)
- Role matrix table: staff name, email, role per branch.
- Role change dropdown per row; confirmation modal before applying.
- Role labels in active locale with tooltip descriptions of permissions.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/team`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Tim Klinik) + main content; role matrix table showing staff × branch × role; Clinic Owner sees all branches; Branch Manager sees only their branch(es).
- **Components:**
  - `FlexSidebar` — nav; branch context badge in header (shows "Semua Cabang" for Clinic Owner view)
  - `FlexTable` — columns: Nama Staf, Email, Cabang, Peran (Role), Tindakan; sortable by name/branch
  - `FlexSelect` — role change dropdown per row (in-line edit)
  - `FlexBadge` — role badge per row (color-coded: doctor=blue, nurse=green, pharmacist=orange, etc.)
  - `FlexModal` — confirmation modal before applying role change "Ubah peran [Nama] menjadi [Peran]?" (Change [Name]'s role to [Role]?)
  - `FlexTooltip` — permission description on role badge hover
  - `FlexButton` — "Undang Staf", confirm/cancel in modal
- **Key interactions:**
  - Role change dropdown opens inline; selecting new role triggers confirmation modal.
  - Tooltip on each role label explains permissions in plain language (in active locale).
  - PHI mask toggle in table header masks all staff names to first name + last initial for screen privacy.
  - Branch filter chip row if Clinic Owner has multiple branches.
- **Empty state:** "Belum ada staf di tim ini." (No staff in this team yet.)
- **Error state:** Role change API failure: inline row error "Perubahan gagal disimpan" (Change could not be saved).
- **i18n:** Role labels, permission tooltip text, modal text, table headers, empty/error strings translated.
- **Mobile:** Secondary; table collapses to card list per staff member; role shown as badge; "Ubah Peran" (Change Role) action in card footer.

## Feature 1.6 — Audit Trail & Compliance

### Story 1.6.1 [OPEN]
**As a** Platform Admin,
**I want to** have an immutable, exportable audit log for all PHI access and modification events,
**so that** the platform meets PP 71/2019 compliance requirements and regulatory inquiries can be answered.

**Backend AC:**
- All PHI create/read/update/delete operations write to `audit_log` table: `(event_id, event_type, actor_id, tenant_id, branch_id, resource_type, resource_id, timestamp, ip, metadata_json)`.
- `audit_log` is append-only; no UPDATE/DELETE permitted on audit rows; enforced at DB policy level.
- `GET /api/v1/admin/audit-logs?tenant_id=&from=&to=&event_type=` — platform admin only; paginated; exportable as CSV.
- Data retention: minimum 5 years per PP 71/2019; automated archival job; deletion requires explicit legal hold release.

**Frontend AC:**
- Route: `/admin/audit-logs` (Platform Admin only)
- Filterable table: date range, tenant, event type, actor.
- "Export CSV" button; export filename includes date range in active locale format.
- Timestamp displayed in UTC with local timezone offset shown.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/admin/audit-logs`
- **Portal:** Clinic Portal (Platform Admin role only)
- **Layout:** Sidebar nav (active: Kepatuhan > Log Audit) + main content; filter toolbar above table; paginated table; "Ekspor CSV" (Export CSV) button top-right.
- **Components:**
  - `FlexSidebar` — admin nav; no branch context (platform-wide view)
  - `FlexToolbar` — filter row: date range `FlexDatepicker`, tenant `FlexSelect`, event type `FlexSelect`, actor `FlexInput`
  - `FlexTable` — columns: Waktu (UTC + local offset), Tenant, Cabang, Jenis Acara, Aktor, Sumber Daya; sortable by timestamp
  - `FlexBadge` — event type color-coded (PHI read = amber, PHI write = red, admin = blue)
  - `FlexButton` — "Ekspor CSV"; "Terapkan Filter" (Apply Filter)
  - `FlexPagination` — table pagination
  - `FlexAlert` — export success/failure
- **Key interactions:**
  - Date range picker defaults to last 7 days; max range 90 days per query.
  - "Ekspor CSV" triggers server-side export; filename includes date range in locale format (e.g., `audit-log_2026-06-01_2026-06-21.csv`).
  - Timestamp column shows UTC time with local offset: "2026-06-21 08:00 UTC (+7 WIB)".
  - Row click expands metadata JSON in a `FlexDrawer` on the right.
  - PHI mask toggle in table header masks `actor_id` and `resource_id` columns for screen sharing.
- **Empty state:** "Tidak ada log ditemukan untuk filter yang dipilih." (No logs found for the selected filters.)
- **Error state:** Export failure: `FlexAlert` "Ekspor gagal. Coba kurangi rentang tanggal." (Export failed. Try reducing the date range.)
- **i18n:** Filter labels, column headers, event type labels, export filename format, empty/error strings, timestamp format translated.
- **Mobile:** Secondary (admin tool); table horizontally scrollable; filter toolbar collapses to `FlexDrawer`.

### Story 1.6.2 [OPEN]
**As a** Patient,
**I want to** manage my consent for data processing,
**so that** I can understand and control how my health data is used, per UU PDP No. 27/2022.

**Backend AC:**
- `GET /api/v1/patients/me/consents` — returns list of active and revoked consents with version, accepted_at, purpose.
- `POST /api/v1/patients/me/consents/:consent_id/revoke` — records revocation timestamp; triggers downstream data-use restriction workflow.
- Consent revocation does not delete historical data; it restricts future processing; business logic enforces this per purpose category.
- Revocation event emitted to audit log.

**Frontend AC:**
- Route: `/patient/account/consent`
- Consent list: each entry shows purpose, accepted date, status (Active / Revoked), link to full consent text.
- "Revoke" button per active consent; confirmation modal explaining consequences in plain Bahasa Indonesia.
- All text in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/patient/account/consent`
- **Portal:** Patient Portal
- **Layout:** Mobile-first; account settings section; card list of active and revoked consents; bottom navigation bar.
- **Components:**
  - `FlexCard` — per consent entry: purpose label, accepted date, status badge (Aktif / Dicabut), "Lihat Ketentuan" (View Terms) link, "Cabut Persetujuan" (Revoke Consent) button
  - `FlexBadge` — status badge (green = Aktif, grey = Dicabut)
  - `FlexModal` — revocation confirmation modal: plain Bahasa Indonesia explanation of consequences; "Ya, Cabut" (Yes, Revoke) / "Batal" (Cancel) buttons
  - `FlexButton` — "Cabut Persetujuan" per active consent
  - `FlexAlert` — success confirmation after revocation
- **Key interactions:**
  - "Lihat Ketentuan" opens full consent text in `FlexModal` in active locale.
  - "Cabut Persetujuan" opens confirmation modal explaining consequences in plain Indonesian: "Mencabut persetujuan ini akan menghentikan penggunaan data Anda untuk [tujuan]. Data historis tidak akan dihapus." (Revoking this consent will stop your data being used for [purpose]. Historical data will not be deleted.)
  - After revocation: consent card status badge changes to "Dicabut"; revocation timestamp shown.
- **Empty state:** "Tidak ada persetujuan aktif." (No active consents.) — shown if all revoked.
- **Error state:** Revocation API failure: `FlexAlert` "Pencabutan gagal, silakan coba lagi" (Revocation failed, please try again) in modal footer.
- **i18n:** Consent purpose labels, status badges, modal explanation text, button labels, date format, empty/error strings translated (ID default).
- **Mobile:** Primary; full-width cards; "Cabut Persetujuan" button large tap target; modal full-screen on narrow viewport.

## Feature 1.7 — Multilingual & Locale

### Story 1.7.1 [OPEN]
**As a** platform user (any role),
**I want to** select my preferred language (Bahasa Indonesia or English),
**so that** the interface, notifications, and documents are displayed in my chosen language.

**Backend AC:**
- `PUT /api/v1/users/me/locale` — auth: any authenticated user; accepts `locale` from allowed list (`id-ID`, `en-US`); stored on user profile.
- All API-generated content (email subjects, notification templates, PDF documents) reads `locale` from user or tenant default.
- Tenant default locale configurable: `PUT /api/v1/tenants/:tenant_id/settings` — `default_locale` field.
- No hardcoded strings in any API response body; all user-facing strings use translation keys.

**Frontend AC:**
- Route: locale toggle available in header on every page (staff portal and patient portal).
- Locale change: instant re-render without page reload; persisted to user profile if authenticated, to `localStorage` if unauthenticated.
- All UI strings, validation messages, empty states, date formats, and number formats respect active locale.
- New locale additions require only a translation JSON file drop — no code changes.

---


#### Frontend (UILDC v1.0)

- **Route:** Locale toggle available in page header on every route (both portals)
- **Portal:** Both (Clinic Portal and Patient Portal)
- **Layout:** Locale toggle is a persistent UI element in the page header — not a separate page. Clinic portal: top-right of sidebar header. Patient portal: top-right of app bar.
- **Components:**
  - `FlexDropdown` — locale toggle: "ID" / "EN" options; active locale highlighted; accessible (keyboard-navigable)
  - `FlexBadge` — active locale indicator on header (e.g., "ID" badge)
  - `FlexAlert` — brief "Bahasa diubah" (Language changed) toast on switch (auto-dismiss 2 seconds)
- **Key interactions:**
  - Clicking locale toggle dropdown shows ID / EN options.
  - Selecting a locale: instant re-render of all UI strings without page reload; date/number/currency formats update to match locale.
  - If authenticated: locale preference saved to user profile (`PUT /api/v1/users/me/locale`).
  - If unauthenticated: locale persisted to `localStorage`; applied on next visit.
  - New locale additions (e.g., Arabic) require only a translation JSON file addition — no code changes.
- **Empty state:** N/A.
- **Error state:** Profile update failure (locale save): silent failure with `localStorage` fallback; user sees correct locale regardless; background retry on next page load.
- **i18n:** Toggle labels (ID / EN), toast message translated. All downstream strings updated per locale selection. Date formats: `DD MMMM YYYY` (ID) / `MMMM DD, YYYY` (EN); currency: IDR with Indonesian thousand separator (.) for ID locale; comma-separated for EN.
- **Mobile:** Both portals; locale toggle visible in mobile header; tap target ≥ 44 px.

## Story Count: Feature 1.1 (2) + 1.2 (3) + 1.3 (2) + 1.4 (3) + 1.5 (1) + 1.6 (2) + 1.7 (1) = **14 stories**
