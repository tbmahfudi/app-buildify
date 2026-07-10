---
artifact_id: epic-11-human-resource
status: active
version: 1
module: healthcare_hr
launch_phase: MVP
producer: A3 Product Owner
upstream: BACKLOG v3
created: 2026-07-02
---

# Epic 11 — Human Resource: Employee / Doctor / Nurse

**Module:** `healthcare_hr` (requires `healthcare` base; extends existing `hc_providers` / `hc_branch_staff`)
**Launch Phase:** MVP
**Summary:** Healthcare-specific human-resource layer over the platform's user/RBAC/org capabilities
(Reuse Register #1/#2/#3). Registers clinic employees, captures employment documents and status, licensing
(SIP/STR number) and specialty, and enriches providers with clinical profiles: doctor profile (consultation
fee, practice-schedule link, room assignment) and nurse profile (shift schedule, assigned doctor). This epic
**extends** `hc_providers` and `hc_branch_staff` rather than re-modeling identity — platform users, roles,
and org linkage (epic-08) are reused; only the healthcare employment/clinical attributes are added here.

---

## Feature 11.1 — Employee Registration & Records

### Story 11.1.1 [OPEN]
**As a** Branch Manager or HR Admin,
**I want to** register a clinic employee and link them to the platform user and branch,
**so that** every staff member has a healthcare employment record scoped to the correct branch.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/hr/employees` — auth: Branch Manager, HR Admin, Clinic Owner; payload: `platform_user_id` (existing user) OR invite fields (email/phone), `full_name`, `national_id` (NIK, optional), `employee_type` ∈ {doctor, nurse, pharmacist, lab_tech, radiographer, admin, billing, other}, `hire_date`, `department_id` (epic-08, nullable), `job_title`.
- Creates `hc_employees` record carrying `tenant_id` + `branch_id`; links to the platform user (reused) and, where the employee is a clinician, to a `hc_providers` row (extend, not duplicate); does not re-create identity/roles.
- Employee record is branch-scoped (RLS per schema-hc-01); a user may hold employee records at multiple branches (mirrors `hc_branch_staff`).
- Emits `hr.employee_registered` audit event; PII fields (NIK) encrypted via `EncryptedPHIType`, accessed via SDK readers with audit.

**Frontend AC:**
- Route: `/clinic/hr/employees/new`
- Form: link-existing-user or invite; employee type, department (dropdown from epic-08), job title, hire date; NIK optional.
- On save: employee appears in the branch employee directory; clinician types prompt to continue to license/specialty step.
- All labels in active locale; NIK masked by default.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/hr/employees/new`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: SDM > Karyawan > Tambah) + main content; sectioned single-page form (Identitas, Kepegawaian, Departemen); desktop max-width 800 px.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexForm` — sectioned employee form
  - `FlexSelect` — link existing user (searchable) or "Undang baru" toggle; `employee_type`; `department_id` (from epic-08); job title
  - `FlexInput` — full name, NIK (optional, masked), email/phone (invite path)
  - `FlexDatepicker` — hire date
  - `FlexBadge` — PHI mask toggle on NIK
  - `FlexButton` — "Simpan Karyawan" (Save Employee); "Simpan & Lanjut ke Lisensi" (Save & Continue to License) for clinician types
- **Key interactions:**
  - Toggle between "Tautkan pengguna" (Link user) and "Undang baru" (Invite new); linking reuses the platform user; inviting sends a platform invitation in the tenant's default locale.
  - Selecting a clinical employee type (doctor/nurse) reveals a hint that a clinical profile follows and enables "Simpan & Lanjut ke Lisensi".
  - Department dropdown sourced from epic-08 `hc_departments` for the active branch.
  - NIK masked by default with a reveal toggle (PHI screen privacy).
- **Empty state:** N/A (creation form).
- **Error state:** Duplicate employee for user+branch: inline "Karyawan ini sudah terdaftar di cabang ini" (This employee is already registered at this branch); invalid NIK format inline.
- **i18n:** Section labels, field labels, employee-type options, department labels, button labels, mask tooltip, validation strings translated (ID / EN).
- **Mobile:** Secondary; sections stack; NIK reveal via tap.

### Story 11.1.2 [OPEN]
**As an** HR Admin,
**I want to** upload and manage employment documents for each employee (contract, ID, certificates),
**so that** required documentation is stored securely and expiry is tracked.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/hr/employees/:employee_id/documents` — auth: HR Admin, Branch Manager; multipart; validates type (PDF/PNG/JPG ≤ 5 MB); payload metadata: `doc_type` ∈ {contract, national_id, str, sip, diploma, certification, other}, `issued_date`, `expiry_date` (nullable), `doc_number`.
- Files stored in tenant-isolated object storage; document metadata in `hc_employee_documents` (`tenant_id`, `branch_id`, `employee_id`, `doc_type`, `expiry_date`, `storage_ref`); document bytes accessed via SDK readers with audit.
- `GET .../employees/:employee_id/documents` — lists documents with expiry status (valid / expiring-≤30d / expired).
- Expiring/expired documents raise a `hr.document_expiring` notification via the platform notification transport (Reuse Register #7); document access emits `hr.document_accessed` audit event.

**Frontend AC:**
- Route: `/clinic/hr/employees/:employee_id/documents`
- Document list with type, number, issued/expiry dates, expiry status badge; upload with drag-and-drop and inline preview.
- Expiring/expired documents flagged; download per document (audited).
- All labels in active locale; dates in branch locale format.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/hr/employees/:employee_id/documents`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: SDM > Karyawan) + employee sub-nav tab (Dokumen); main content: upload zone above + documents table below.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexTabs` — employee record tabs: Profil, Dokumen, Status, Profil Klinis
  - `FlexFileUpload` — drag-and-drop (PDF/PNG/JPG ≤ 5 MB) with inline preview; doc-type `FlexSelect`, doc number, issued/expiry `FlexDatepicker`
  - `FlexTable` — columns: Jenis Dokumen, Nomor, Tgl Terbit, Tgl Kedaluwarsa, Status, Tindakan
  - `FlexBadge` — expiry status: Valid (green) / Akan Kedaluwarsa (amber, ≤30d) / Kedaluwarsa (red)
  - `FlexButton` — "Unggah Dokumen" (Upload Document); "Unduh" (Download) per row (audited)
  - `FlexAlert` — expiring-documents banner
- **Key interactions:**
  - Upload: drag-and-drop or picker; type/size validated inline; preview rendered; metadata (type, number, dates) captured before save.
  - Expiry badge auto-computed; expiring/expired surface a banner and feed the notification center.
  - "Unduh" streams the file via SDK reader and writes a `hr.document_accessed` audit event.
- **Empty state:** "Belum ada dokumen. Unggah kontrak, KTP, STR, atau SIP." (No documents yet. Upload contract, ID, STR, or SIP.)
- **Error state:** Type/size error inline under upload zone; save failure `FlexAlert` at top.
- **i18n:** Doc-type options, column headers, status badges, upload/download labels, empty/error strings, date format translated (ID / EN).
- **Mobile:** Secondary; table collapses to card list; upload via file picker.

## Feature 11.2 — Employment Status & Directory

### Story 11.2.1 [OPEN]
**As an** HR Admin or Branch Manager,
**I want to** set and change an employee's employment status,
**so that** access, scheduling, and reporting reflect who is currently active.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/hr/employees/:employee_id/status` — auth: HR Admin, Branch Manager, Clinic Owner; `employment_status` ∈ {active, probation, on_leave, suspended, terminated}; requires `effective_date` and `reason` for suspended/terminated.
- Status transitions guarded; `terminated` revokes the linked platform role assignments at that branch (reuses RBAC — Reuse Register #3) and removes the provider from active scheduling/booking pools (epic-02); a re-hire creates a new status period rather than mutating history.
- Status changes emit `hr.employment_status_changed` audit event; status history retained.
- `GET .../employees?status=&type=&department_id=&search=` — paginated branch directory; excludes terminated by default.

**Frontend AC:**
- Route: `/clinic/hr/employees` (directory) and status control on employee profile.
- Directory: filter by status, type, department; status badge per row.
- Status change: modal with effective date and reason (required for suspend/terminate); confirmation explaining downstream effect (access/scheduling).
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/hr/employees` (directory) | `#/clinic/hr/employees/:employee_id` (status tab)
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: SDM > Karyawan) + main content; filter toolbar + directory table; status control on the employee "Status" tab.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexToolbar` — filters: status `FlexSelect`, type `FlexSelect`, department `FlexSelect`, search `FlexInput`
  - `FlexTable` — columns: Nama, Jenis, Departemen, Jabatan, Status, Tindakan
  - `FlexBadge` — status badge: Aktif (green) / Masa Percobaan (blue) / Cuti (amber) / Ditangguhkan (orange) / Diberhentikan (grey)
  - `FlexModal` — status-change modal: new status `FlexSelect`, effective date `FlexDatepicker`, reason `FlexTextarea` (required for suspend/terminate) + downstream-effect notice
  - `FlexButton` — "Ubah Status" (Change Status); "Terapkan Filter"
- **Key interactions:**
  - "Ubah Status" opens modal; suspend/terminate require a reason and show a notice: "Menghentikan karyawan akan mencabut akses dan menghapus dari penjadwalan." (Terminating an employee will revoke access and remove them from scheduling.)
  - Confirming terminate revokes branch role assignments (RBAC) and removes from booking pools.
  - Directory excludes terminated by default; a filter reveals them (read-only history).
- **Empty state:** "Belum ada karyawan. Tambahkan karyawan untuk memulai." (No employees yet. Add an employee to get started.)
- **Error state:** Missing reason on suspend/terminate: inline "Alasan wajib diisi" (Reason is required); update failure `FlexAlert`.
- **i18n:** Filter/column labels, status badges, modal text incl. downstream notice, button labels, empty/error strings translated (ID / EN).
- **Mobile:** Secondary; table collapses to card list; status change via card action → modal.

## Feature 11.3 — Licensing & Specialty

### Story 11.3.1 [OPEN]
**As a** clinician (Doctor/Nurse) or HR Admin,
**I want to** record a clinician's license/SIP and STR numbers, specialty, and license validity,
**so that** only currently-licensed clinicians practice and licensing is auditable.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/hr/providers/:provider_id/license` — auth: HR Admin, Branch Manager, or the clinician; extends `hc_providers` with `str_number` (registration), `sip_number` (practice permit), `sip_expiry`, `str_expiry`, `specialty` (controlled vocabulary), `sub_specialty` (optional).
- SIP/STR numbers validated for format only (no live P2KB/national verification — Scope-Out inherited); expiry tracked; an expired SIP flags the provider as `license_lapsed` and (per clinic policy) blocks new appointment assignment (epic-02) until renewed.
- Specialty sourced from platform master-data (Reuse Register #5/#18) so it stays consistent with clinic-discovery specialties (epic-01).
- License changes emit `hr.license_updated` audit event; expiring licenses raise `hr.license_expiring` via the platform notification transport.

**Frontend AC:**
- Route: `/clinic/hr/employees/:employee_id` — Clinical Profile tab, License section.
- Fields: STR number, SIP number, respective expiry dates, specialty (searchable), sub-specialty.
- License validity badge (valid / expiring / lapsed); lapsed-license warning with effect on scheduling.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/hr/employees/:employee_id` (Profil Klinis tab, Lisensi section)
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: SDM > Karyawan) + employee tabs; License section within the Clinical Profile tab.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexTabs` — Profil / Dokumen / Status / Profil Klinis
  - `FlexForm` — License section: STR number, SIP number `FlexInput`; STR/SIP expiry `FlexDatepicker`; specialty `FlexSelect` (searchable, from master-data); sub-specialty `FlexSelect`
  - `FlexBadge` — license validity: Valid (green) / Akan Kedaluwarsa (amber) / Kedaluwarsa (red)
  - `FlexAlert` — lapsed-license warning: "SIP kedaluwarsa — dokter tidak dapat menerima janji baru sampai diperbarui." (SIP expired — doctor cannot take new appointments until renewed.)
  - `FlexButton` — "Simpan Lisensi" (Save License)
- **Key interactions:**
  - Specialty searchable dropdown sourced from platform master-data; keeps discovery specialties consistent.
  - Format-only validation on STR/SIP; expiry drives the validity badge; a lapsed SIP shows the scheduling-impact warning.
  - Saving license changes writes an audit event; expiring licenses feed the notification center.
- **Empty state:** License fields empty on first setup with placeholders.
- **Error state:** Invalid number format inline; save failure `FlexAlert`.
- **i18n:** Field labels, specialty vocabulary (active locale), validity badges, lapsed warning, button label, error strings translated (ID / EN).
- **Mobile:** Secondary; single-column form.

## Feature 11.4 — Doctor Profile

### Story 11.4.1 [OPEN]
**As a** Branch Manager or Doctor,
**I want to** configure a doctor's consultation fee, practice-schedule link, and room assignment,
**so that** booking, billing, and queue routing use accurate practice details.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/hr/providers/:provider_id/doctor-profile` — auth: Branch Manager, Clinic Owner, or the doctor; extends `hc_providers` (doctor role): `consultation_fee` (branch currency, integer minor units), `practice_schedule_id` (links to scheduling — epic-02), `room_id`/`room_label` (assigned consultation room at the branch).
- `consultation_fee` is consumed by billing (epic-03) as the default charge for the doctor's consultation; room assignment feeds queue routing (epic-09) and the doctor's calendar.
- Practice-schedule link references an existing epic-02 schedule; changing it does not orphan booked appointments (validation blocks a change that would strand bookings without reassignment).
- Profile changes emit `hr.doctor_profile_updated` audit event.

**Frontend AC:**
- Route: `/clinic/hr/employees/:employee_id` — Clinical Profile tab, Doctor Profile section (visible for doctor type).
- Fields: consultation fee (currency-formatted), practice schedule (link/select from epic-02), room assignment.
- Fee shown in branch currency with locale formatting; schedule link opens the scheduling module.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/hr/employees/:employee_id` (Profil Klinis tab, Profil Dokter section)
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: SDM > Karyawan) + employee tabs; Doctor Profile section within Clinical Profile tab (rendered only for doctor employee type).
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexForm` — Doctor Profile: consultation fee `FlexInput` (currency), practice schedule `FlexSelect` (from epic-02 schedules) + "Buka Jadwal" (Open Schedule) link, room `FlexSelect` (branch rooms)
  - `FlexBadge` — "Terhubung ke penjadwalan" (Linked to scheduling) indicator
  - `FlexButton` — "Simpan Profil Dokter" (Save Doctor Profile)
  - `FlexAlert` — warning if a schedule change would strand booked appointments
- **Key interactions:**
  - Consultation fee entered in branch currency; displayed with locale thousand separators; feeds billing default charge.
  - Practice schedule selected from existing epic-02 schedules; "Buka Jadwal" deep-links to the scheduling module.
  - Room assignment selected from branch rooms; feeds queue routing (epic-09).
  - Attempting a schedule change that would orphan bookings blocks with a reassignment prompt.
- **Empty state:** Fields empty with placeholders; "Belum ada jadwal praktik tertaut." (No practice schedule linked yet.)
- **Error state:** Invalid fee inline; strand-bookings block `FlexAlert`; save failure `FlexAlert`.
- **i18n:** Field labels, currency format per locale, linked-schedule indicator, warnings, button label, error strings translated (ID / EN).
- **Mobile:** Secondary; single-column; schedule link opens scheduling screen.

## Feature 11.5 — Nurse Profile

### Story 11.5.1 [OPEN]
**As a** Branch Manager or Head Nurse,
**I want to** configure a nurse's shift schedule and assigned doctor(s),
**so that** nursing coverage is planned and nurses are paired to the right clinicians.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/hr/providers/:provider_id/nurse-profile` — auth: Branch Manager, Clinic Owner, Head Nurse; extends `hc_providers` (nurse role): `shift_pattern` (references shift-schedule definitions), `assigned_doctor_ids[]` (0..n doctors at the same branch).
- Shift schedule stored as recurring shift assignments (`hc_nurse_shifts`: `tenant_id`, `branch_id`, `provider_id`, `shift_date`/`recurrence`, `shift_type` ∈ {morning, afternoon, night}); overlapping shift validation.
- Assigned-doctor links used by queue/room workflows (epic-09) and reporting (epic-12 doctor utilization by supporting nurse); a nurse may support multiple doctors and vice versa.
- Changes emit `hr.nurse_profile_updated` audit event.

**Frontend AC:**
- Route: `/clinic/hr/employees/:employee_id` — Clinical Profile tab, Nurse Profile section (visible for nurse type).
- Shift schedule editor (recurring shift grid: shift type per day); assigned-doctor multi-select.
- Overlap warnings; weekly shift preview.
- All labels in active locale; times in branch timezone.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/hr/employees/:employee_id` (Profil Klinis tab, Profil Perawat section)
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: SDM > Karyawan) + employee tabs; Nurse Profile section within Clinical Profile tab (rendered only for nurse employee type).
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexGrid` — shift schedule grid (Mon–Sun rows; shift-type selector per day: Pagi / Siang / Malam / Libur)
  - `FlexSelect` — assigned doctors multi-select (branch doctors)
  - `FlexBadge` — shift-type chips (Pagi green, Siang amber, Malam indigo)
  - `FlexButton` — "Simpan Profil Perawat" (Save Nurse Profile)
  - `FlexAlert` — overlapping-shift warning
- **Key interactions:**
  - Shift grid: pick a shift type per day; recurring pattern; a weekly preview summarizes coverage.
  - Overlapping shifts flagged with an amber warning before save.
  - Assigned-doctor multi-select from branch doctors; feeds queue/room workflows and reporting.
  - Times displayed in branch timezone.
- **Empty state:** "Belum ada jadwal shift." (No shift schedule yet.) — grid defaults to Libur.
- **Error state:** Overlap warning inline; save failure `FlexAlert`.
- **i18n:** Day names, shift-type labels, assigned-doctor label, overlap warning, button label, timezone labels, empty/error strings translated (ID / EN).
- **Mobile:** Secondary; shift grid collapses to per-day accordion; multi-select as chip list.

## Feature 11.6 — Provider Directory & Availability

### Story 11.6.1 [OPEN]
**As** clinic staff (Front Desk / Branch Manager),
**I want to** view a branch provider directory with specialty, license status, and today's availability,
**so that** I can route patients and check-in visits to the right clinician (epic-09).

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/hr/providers?type=&specialty=&available_on=` — auth: any branch staff; returns providers (doctors/nurses) with specialty, license validity, room, today's practice/shift status (available / on_leave / off) — no PHI.
- Availability derived from doctor practice schedule (epic-02) and nurse shift schedule (this epic) plus employment status (Feature 11.2); lapsed-license providers flagged and excluded from bookable lists per policy.
- Read-only, feeds epic-09 check-in routing and epic-12 utilization datasets; branch/tenant scoped.

**Frontend AC:**
- Route: `/clinic/hr/directory`
- Provider cards/table: name, role, specialty, license badge, room, today's availability status; filter by specialty/type/availability.
- "Assign to visit" action links into epic-09 check-in (where invoked from that flow).
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/hr/directory`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: SDM > Direktori) + main content; filter toolbar + provider card grid (or table on desktop).
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexToolbar` — filters: specialty `FlexSelect`, type `FlexSelect`, availability `FlexSelect`
  - `FlexCard` — provider card: name, role, specialty, room, today's availability
  - `FlexBadge` — license validity badge; availability badge (Tersedia green / Cuti amber / Libur grey); lapsed-license flag
  - `FlexButton` — "Tugaskan ke Kunjungan" (Assign to Visit) — deep-links into epic-09 check-in when invoked from that flow
- **Key interactions:**
  - Filters narrow the directory by specialty/type/availability; availability computed from schedules + employment status.
  - Lapsed-license providers are visibly flagged and non-bookable per policy.
  - "Tugaskan ke Kunjungan" hands off to epic-09 check-in with the provider preselected.
  - No PHI on this page (provider info only).
- **Empty state:** "Tidak ada penyedia layanan cocok dengan filter." (No providers match the filters.)
- **Error state:** `FlexAlert` "Gagal memuat direktori penyedia" (Failed to load provider directory).
- **i18n:** Filter/card labels, availability + license badges, action label, empty/error strings translated (ID / EN).
- **Mobile:** Primary-capable (front-desk use); card grid single-column; filters in a `FlexDrawer`.

## Feature 11.7 — Employee Self-Service

### Story 11.7.1 [OPEN]
**As an** employee (Doctor/Nurse/Staff),
**I want to** view my own employment record — profile, documents, license status, schedule, and assignments —
**so that** I can confirm my details are correct and see my upcoming shifts/practice schedule.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/hr/employees/me` — auth: the authenticated employee (self only; 403 for other employees); returns own employee record: profile, employment status, documents (metadata + secure download), license validity, doctor/nurse profile, and upcoming schedule/shifts.
- Read-only for the employee (edits go through HR endpoints above); self-access emits a `hr.self_profile_accessed` audit event; document downloads audited as `hr.document_accessed`.
- License-expiry and document-expiry indicators surfaced so the employee is prompted to submit renewals.

**Frontend AC:**
- Route: `/clinic/me/employment`
- Read-only view of profile, documents (with expiry badges + download), license status, and this-week schedule/shifts.
- Expiring license/documents highlighted with guidance to contact HR.
- All labels in active locale; PHI (own NIK) masked by default.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/me/employment`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Saya > Kepegawaian) + main content; read-only profile card + tabbed sections (Dokumen, Lisensi, Jadwal).
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — own profile summary (name, role, department, employment status badge); NIK masked with reveal
  - `FlexTabs` — Dokumen / Lisensi / Jadwal
  - `FlexTable` — documents (type, number, expiry, status, download); this-week schedule/shifts
  - `FlexBadge` — employment status; license validity; document expiry badges; PHI mask toggle
  - `FlexAlert` — "Lisensi/dokumen Anda akan segera kedaluwarsa — hubungi SDM." (Your license/documents are expiring soon — contact HR.)
- **Key interactions:**
  - Entire view is read-only; expiring items highlighted with guidance to contact HR for renewal.
  - Document download streams via SDK reader (audited); own NIK masked with a reveal toggle.
  - Schedule tab shows this week's practice schedule (doctor) or shifts (nurse) in branch timezone.
- **Empty state:** "Belum ada data kepegawaian. Hubungi SDM." (No employment data yet. Contact HR.)
- **Error state:** `FlexAlert` "Gagal memuat data kepegawaian" (Failed to load employment data).
- **i18n:** Tab labels, status/expiry badges, download label, expiry guidance, empty/error strings, mask tooltip translated (ID / EN).
- **Mobile:** Primary-capable (clinicians on the move); tabs scroll; cards single-column.

## Story Count: Feature 11.1 (2) + 11.2 (1) + 11.3 (1) + 11.4 (1) + 11.5 (1) + 11.6 (1) + 11.7 (1) = **8 stories**
