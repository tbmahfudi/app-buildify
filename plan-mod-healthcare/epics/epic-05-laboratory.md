---
artifact_id: epic-05-laboratory
status: active
version: 2
module: healthcare_lab
launch_phase: Month 4-5 post-GA
producer: A3 Product Owner
upstream: vision-02, research-02
created: 2026-06-21
---

# Epic 05 — Laboratory Module

**Module:** `healthcare_lab` (requires `healthcare` base)
**Launch Phase:** Month 4–5 post-GA
**Summary:** Lab test ordering, specimen tracking, result entry and patient access, and critical value alerting.

---

## Feature 5.1 — Test Ordering

### Story 5.1.1 [OPEN]
**As a** Doctor,
**I want to** order one or more laboratory tests for a patient during an encounter,
**so that** the lab tech is notified and the order is tracked end-to-end.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/lab-orders` — auth: Doctor; payload: `encounter_id`, `patient_id`, `tests[]: {test_code, test_name, clinical_indication}`.
- Order record: `(order_id, tenant_id, branch_id, patient_id, encounter_id, ordering_provider_id, tests[], status: ordered, created_at)`.
- Lab tech at the branch receives in-app notification (no PHI in notification body — order reference code only).
- Order creation emits `lab.order_created` PHI audit event.

**Frontend AC:**
- Route: `/clinic/encounters/:encounter_id/lab-orders/new`
- Test search from branch-configured test catalog (name or code); multi-select.
- Clinical indication field per test (free text).
- "Submit Order" → order reference code displayed; order appears in lab tech queue.
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id/lab-orders/new`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Laboratorium > Permintaan Baru) + main content; encounter patient strip at top (PHI masked); test search + multi-select list; clinical indication fields per selected test; submit toolbar at bottom.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — patient strip: name (PHI masked), encounter reference
  - `FlexInput` — test search autocomplete (name or code) from branch catalog
  - `FlexCheckbox` — multi-select for tests from search results
  - `FlexForm` — clinical indication `FlexTextarea` per selected test
  - `FlexBadge` — selected test count chip; per-test remove button
  - `FlexBadge` — PHI mask toggle on patient strip
  - `FlexButton` — "Kirim Permintaan Lab" (Submit Lab Order) primary
  - `FlexAlert` — order reference code on success; error state
- **Key interactions:**
  - Searching tests: autocomplete shows name + code; multi-select supported.
  - Each selected test shows a clinical indication `FlexTextarea` below it.
  - "Kirim Permintaan Lab": success shows order reference code "Permintaan lab #[REF] berhasil dikirim ke teknisi" (Lab order #[REF] successfully sent to lab tech); lab tech receives in-app notification (no PHI in notification body).
  - Removing a test: removes its indication field.
- **Empty state (search results):** "Tidak ada tes ditemukan. Periksa katalog lab cabang." (No tests found. Check branch lab catalog.)
- **Error state:** Submit failure: `FlexAlert` "Gagal mengirim permintaan lab" (Failed to submit lab order).
- **i18n:** Search placeholder, indication placeholder ("Indikasi klinis" — Clinical indication), button labels, success/error messages, reference code format translated.
- **Mobile:** Secondary; test search and indication fields stack; submit button pinned bottom.

### Story 5.1.2 [OPEN]
**As a** Lab Tech,
**I want to** view and accept incoming lab orders assigned to my branch,
**so that** I can begin specimen collection for each order.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/lab-orders?status=ordered` — auth: Lab Tech, Branch Manager.
- `PUT .../lab-orders/:order_id/accept` — auth: Lab Tech; status: `ordered` → `specimen_pending`; records `accepted_by`, `accepted_at`.

**Frontend AC:**
- Route: `/clinic/lab/orders`
- Order queue: patient identifier (name + DOB last 2 digits for identification), ordering doctor, tests requested, order time.
- "Accept Order" button per row; bulk accept supported.
- All labels in active locale; timestamps in branch timezone.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/lab/orders`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Laboratorium > Antrean) + main content; filter tabs (Baru / Diterima / Selesai); order queue table; bulk-accept toolbar.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexTabs` — Baru (ordered) / Diterima (specimen pending) / Selesai (resulted); count badge per tab
  - `FlexTable` — columns: Pasien (identifier + DOB last 2 digits), Dokter Pemeriksa, Tes Diminta (count), Waktu Permintaan, Tindakan
  - `FlexBadge` — PHI mask toggle (masks patient name to identifier only); "Terima Semua" (Accept All) checkbox in header for bulk accept
  - `FlexButton` — "Terima" (Accept) per row; "Terima Semua" bulk action
  - `FlexAlert` — bulk accept success/failure
- **Key interactions:**
  - "Terima" per row: status `ordered` → `specimen_pending`; row moves to "Diterima" tab.
  - "Terima Semua": bulk accept all rows on current "Baru" tab; confirmation modal for bulk actions.
  - Row click: navigates to order detail (`#/clinic/lab/orders/:order_id`).
  - Timestamps in branch timezone.
  - Patient identifier shows name + last 2 digits of DOB (e.g., "Budi S. – ••/••/89") — partial PHI for identification without full disclosure; mask toggle reveals full name.
- **Empty state:** "Tidak ada permintaan lab baru." (No new lab orders.)
- **Error state:** `FlexAlert` "Gagal memuat antrean lab" (Failed to load lab queue).
- **i18n:** Tab labels, column headers, action labels, bulk confirm modal text, PHI identifier format, timestamp format, empty/error strings translated.
- **Mobile:** Secondary; tabs scroll horizontally; table collapses to card list; bulk accept not available on mobile.

## Feature 5.2 — Specimen Tracking

### Story 5.2.1 [OPEN]
**As a** Lab Tech,
**I want to** record specimen collection and track each specimen through processing,
**so that** there is a complete chain of custody for every sample.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/lab-orders/:order_id/specimens` — auth: Lab Tech; payload: per-test: `specimen_type`, `collection_time`, `collector_id`, `container_barcode` (optional).
- `PUT .../specimens/:specimen_id/status` — valid transitions: `collected` → `processing` → `resulted` | `rejected` (with `rejection_reason`).
- All status changes emit `lab.specimen_status_changed` audit event with actor and timestamp.

**Frontend AC:**
- Route: `/clinic/lab/orders/:order_id`
- Specimen collection form per test: type selector, collection time (defaults to now), barcode scan field (optional).
- Status tracker: visual pipeline (Collected → Processing → Resulted / Rejected).
- Rejection path: reason required; re-collection option (creates new specimen linked to same order).
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/lab/orders/:order_id`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Laboratorium) + main content; order header (patient PHI masked); per-test specimen section with status pipeline visual; action area per specimen.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — order header: reference code, patient identifier (PHI masked), ordering doctor, order time
  - `FlexSection` — per-test specimen block: test name, status pipeline, collection form / rejection form
  - `FlexProgress` — status pipeline visualization: Dikumpulkan (Collected) → Diproses (Processing) → Dihasil (Resulted) / Ditolak (Rejected); step indicators
  - `FlexForm` — collection form per test: specimen type `FlexSelect`, collection time `FlexDatepicker` (defaults to now), barcode scan `FlexInput` (optional)
  - `FlexSelect` — rejection reason if status → Ditolak
  - `FlexBadge` — PHI mask toggle in order header
  - `FlexButton` — "Catat Pengumpulan" (Record Collection), "Mulai Pemrosesan" (Start Processing), "Tolak Spesimen" (Reject Specimen), "Kumpulkan Ulang" (Re-collect — links new specimen to same order)
- **Key interactions:**
  - Per-test: "Catat Pengumpulan" records specimen; status pipeline advances to "Dikumpulkan".
  - "Mulai Pemrosesan": advances to "Diproses".
  - "Tolak Spesimen": rejection reason required; status → "Ditolak"; "Kumpulkan Ulang" option appears.
  - "Kumpulkan Ulang": creates new specimen record linked to same order; pipeline resets for new specimen.
  - Collection time defaults to current branch timezone time; editable.
  - Barcode scan field: placeholder "Scan atau ketik barcode" (Scan or type barcode).
- **Empty state:** N/A (page always loaded for an existing order).
- **Error state:** Status update failure: `FlexAlert` per section "Gagal memperbarui status spesimen" (Failed to update specimen status).
- **i18n:** Specimen type options, status pipeline labels, rejection reason options, form field labels, button labels, timestamp format, error strings translated.
- **Mobile:** Secondary; sections stack; pipeline displayed as horizontal scroll; action buttons below each section.

## Feature 5.3 — Result Management

### Story 5.3.1 [OPEN]
**As a** Lab Tech,
**I want to** enter test results with reference ranges,
**so that** the ordering doctor and patient can interpret the results correctly.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/lab-orders/:order_id/results` — auth: Lab Tech; payload: per-test: `value`, `unit`, `reference_range_low`, `reference_range_high`, `interpretation` (Normal/Abnormal/Critical), `result_notes` (optional).
- Result creation changes specimen status to `resulted`; order status to `resulted` when all tests have results.
- If `interpretation: Critical` → triggers critical value alert workflow (Feature 5.4).
- Result creation emits `lab.result_entered` PHI audit event.

**Frontend AC:**
- Route: `/clinic/lab/orders/:order_id/results`
- Per-test result entry form: value input, unit (auto-filled from test config), reference range fields, interpretation selector.
- "Out of range" visual flag if value outside reference range.
- "Submit Results" finalizes; results become visible to doctor and patient.
- All labels in active locale; numeric values formatted per locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/lab/orders/:order_id/results`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Laboratorium) + main content; order header (PHI masked); per-test result entry form; submit toolbar at bottom.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — order header: patient identifier (PHI masked), ordering doctor, reference
  - `FlexForm` — per-test result entry: value `FlexInput` (numeric), unit (auto-filled, read-only), reference range low/high `FlexInput`, interpretation `FlexSelect` (Normal / Abnormal / Kritis — Critical)
  - `FlexBadge` — "Di luar rentang" (Out of range) amber badge if value outside reference range (auto-evaluated)
  - `FlexBadge` — "KRITIS" (CRITICAL) red badge if interpretation = Kritis; warning note: "Peringatan kritis akan dikirim ke dokter pemeriksa" (Critical alert will be sent to ordering doctor)
  - `FlexTextarea` — result notes per test (optional)
  - `FlexButton` — "Kirim Hasil" (Submit Results) primary; disabled until all tests have values
  - `FlexAlert` — success: "Hasil berhasil dikirim dan tersedia untuk dokter dan pasien" (Results submitted and available to doctor and patient); critical path warning
  - `FlexBadge` — PHI mask toggle in header
- **Key interactions:**
  - Auto out-of-range detection: value typed → compared against reference range → amber badge shown if outside range.
  - Critical interpretation selection: red "KRITIS" badge appears; warning note that critical alert will fire automatically on submit.
  - "Kirim Hasil": finalizes results; triggers patient portal visibility (if released); critical alert fires if any test = Kritis.
  - Numeric values formatted per locale (e.g., decimal separator: comma for ID, period for EN).
- **Empty state:** Result fields empty; value placeholders show "Masukkan nilai" (Enter value).
- **Error state:** Submit failure: `FlexAlert` "Gagal mengirim hasil lab" (Failed to submit lab results).
- **i18n:** Interpretation options, range labels, badge text, warning note, submit button, success/error messages, numeric format per locale translated.
- **Mobile:** Secondary; form single-column; badges prominent.

### Story 5.3.2 [OPEN]
**As a** Patient,
**I want to** access my lab results in the patient portal after the lab has released them,
**so that** I have a digital copy and can discuss results with my doctor.

**Backend AC:**
- `GET /api/v1/patients/me/lab-results` — auth: Patient; returns results from all tenants/branches the patient has visited; each result has `clinic_name`, `branch_name`, `test_name`, `result_date`, `value`, `unit`, `reference_range`, `interpretation`.
- Results only visible after `status: released` (set by Lab Tech or Branch Manager); `released_at` recorded.
- Access emits `lab.patient_accessed_result` PHI audit event.

**Frontend AC:**
- Route: `/patient/records/lab-results`
- Results list: grouped by visit date; each row shows test name, result, range, interpretation badge (Normal / Abnormal / Critical).
- "Download PDF" per result set.
- Unreleased results: "Results pending — your clinic will notify you when ready."
- All labels in active locale; dates in patient's locale format.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/patient/records/lab-results`
- **Portal:** Patient Portal
- **Layout:** Mobile-first; results list grouped by visit date; sub-tabs (Lab / Resep — within `/patient/records`); bottom navigation bar.
- **Components:**
  - `FlexTabs` — within records page: Hasil Lab / Resep (Lab Results / Prescriptions)
  - `FlexCard` — per result group (visit): clinic name, branch, date; expandable to show test rows
  - `FlexTable` — test result rows per visit: Nama Tes, Hasil, Satuan, Rentang Normal, Interpretasi badge; compact on mobile
  - `FlexBadge` — interpretation badge: Normal (green) / Abnormal (amber) / Kritis (red)
  - `FlexButton` — "Unduh PDF" (Download PDF) per result group
  - `FlexAlert` — pending results notice per visit
- **Key interactions:**
  - Results grouped by clinic visit; most recent first; tap card to expand result rows.
  - "Unduh PDF": downloads result PDF in patient's locale for that visit.
  - Unreleased results: card shows "Hasil sedang diproses — klinik Anda akan memberitahu Anda saat siap." (Results are being processed — your clinic will notify you when ready.) with no data rows.
  - Interpretation badge click: expands brief explanation of what the result means (plain language, in active locale).
- **Empty state:** "Belum ada hasil lab. Kunjungi klinik untuk melihat hasil Anda di sini." (No lab results yet. Visit a clinic to see your results here.)
- **Error state:** "Gagal memuat hasil lab. Tarik untuk memuat ulang." (Failed to load lab results. Pull to refresh.)
- **i18n:** Tab labels, result group header format (clinic name, date), column headers, interpretation badge labels, pending notice text, download label, date format in patient locale, empty/error strings translated.
- **Mobile:** Primary; card-based grouping; expand/collapse; test rows compact (name + result + badge); PDF button full-width within card.

## Feature 5.4 — Critical Value Alerts

### Story 5.4.1 [OPEN]
**As a** Doctor,
**I want to** receive an immediate alert when a lab result for my patient is marked Critical,
**so that** I can take urgent clinical action without delay.

**Backend AC:**
- When `interpretation: Critical` is submitted, `lab.critical_value_alert` event fires immediately.
- Alert delivery: in-app notification + WhatsApp/SMS to ordering provider (PHI-safe body: "[Clinic] — Lab alert for order [REF]. Please review immediately." — no diagnosis or result value in body).
- Alert requires acknowledgement: `POST .../results/:result_id/critical-alert/acknowledge` — auth: Doctor or Branch Manager; records `acknowledged_by`, `acknowledged_at`.
- Unacknowledged critical alerts escalate to Branch Manager after 30 minutes; further escalate to Clinic Owner after 60 minutes.

**Frontend AC:**
- In-app: persistent red banner on staff portal for unacknowledged critical alerts; auto-dismisses on acknowledgement.
- Route: `/clinic/lab/orders/:order_id/results` — "Acknowledge Critical Alert" button prominent at top of page.
- Alert history: acknowledgement log with timestamp visible to Branch Manager.
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/lab/orders/:order_id/results` (acknowledgement button in situ) + persistent alert in clinic portal header
- **Portal:** Clinic Portal
- **Layout:** Critical alert appears as a persistent red banner at the top of every clinic portal page (above the sidebar) until acknowledged. Acknowledgement is done from the result detail page.
- **Components:**
  - `FlexAlert` (red, persistent) — critical alert banner: "Peringatan Kritis: Ada [N] hasil lab kritis belum dikonfirmasi." (Critical Alert: There are [N] unacknowledged critical lab results.); "Lihat Sekarang" (View Now) CTA; does NOT auto-dismiss
  - `FlexButton` — "Konfirmasi Peringatan Kritis" (Acknowledge Critical Alert) — prominent red primary button at top of result detail page; visible until acknowledged
  - `FlexCard` — acknowledgement log section at bottom of result page: columns Dikonfirmasi Oleh, Waktu, Peran; visible to Branch Manager
  - `FlexBadge` — "KRITIS" red badge on each result row flagged as critical
  - `FlexAlert` (escalation notice) — amber banner on Branch Manager's portal if unacknowledged after 30 min: "Eskalasi: Hasil kritis untuk [REF] belum dikonfirmasi dokter." (Escalation: Critical result for [REF] not yet acknowledged by doctor.)
- **Key interactions:**
  - Red persistent banner appears on all staff portal pages when unacknowledged critical alert exists.
  - "Lihat Sekarang" navigates to result detail page.
  - "Konfirmasi Peringatan Kritis" button: one-click acknowledge; records `acknowledged_by` + `acknowledged_at`; banner auto-dismisses if no more unacknowledged alerts.
  - Escalation: after 30 min without acknowledgement, Branch Manager sees amber escalation alert. After 60 min, Clinic Owner sees escalation.
  - Acknowledgement log visible to Branch Manager at bottom of result page (audit trail).
- **Empty state (log):** "Belum ada konfirmasi." (No acknowledgements yet.) — shown before acknowledge action.
- **Error state:** Acknowledgement failure: `FlexAlert` inline "Konfirmasi gagal — coba lagi" (Acknowledgement failed — try again).
- **i18n:** Alert banner text, CTA label, acknowledgement button label, log column headers, escalation notice text, KRITIS badge label, error string, timestamp format translated.
- **Mobile:** Secondary; red banner full-width; acknowledge button large and prominent; log collapses to card.

## Story Count: Feature 5.1 (2) + 5.2 (1) + 5.3 (2) + 5.4 (1) = **6 stories**

---

## R2 Gap Addendum (v3)

**Upstream:** BACKLOG v3 (2026-07-02). Closes two R2 laboratory gaps: a controlled result lifecycle with
verification/approval before patients can see results, and specimen barcode / label printing for chain of
custody. New stories continue Feature 5.3 (Result Management) and Feature 5.2 (Specimen Tracking)
numbering. Existing content above is unchanged.

### Story 5.3.3 [OPEN]
**As a** Lab Tech, Lab Verifier, and Branch Manager,
**I want to** move each result through an explicit lifecycle — input → verify → approve → publish —
**so that** no result reaches the ordering doctor or the patient until a second qualified person has verified and approved it.

**Backend AC:**
- Result lifecycle state machine per result set: `entered → verified → approved → published` (plus `rejected_back` returning a result to `entered` for correction); each transition guarded; a published result is immutable except via a linked amendment.
- `POST .../lab-orders/:order_id/results` (existing) — creates results in state `entered` (does NOT auto-publish; supersedes any prior implicit "submit makes visible" behavior).
- `PUT .../results/:result_id/verify` — auth: Lab Tech / Lab Verifier **other than the entering user** (segregation of duties enforced; 403 if same actor); `entered → verified`; records `verified_by`, `verified_at`.
- `PUT .../results/:result_id/approve` — auth: Lab Verifier or Branch Manager; `verified → approved`; records `approved_by`, `approved_at`.
- `PUT .../results/:result_id/publish` — auth: Lab Verifier or Branch Manager; `approved → published`; sets `released_at`; this is the transition that makes the result visible in the patient portal (aligns with Story 5.3.2 `status: released`) and notifies the ordering doctor + patient (PHI-safe body).
- `PUT .../results/:result_id/reject-back` — auth: verifier/approver; required `reason`; returns result to `entered`; original entering tech notified.
- Critical-value alert (Feature 5.4) fires at the `verified` transition (so urgent action is not gated on final publish), while patient visibility remains gated on `published`.
- Every transition emits a `lab.result_lifecycle_changed` PHI audit event `(result_id, from_state, to_state, actor_id, branch_id, tenant_id, at)`.

**Frontend AC:**
- Route: `/clinic/lab/orders/:order_id/results`
- Lifecycle pipeline (Dimasukkan → Diverifikasi → Disetujui → Dipublikasikan) with current step highlighted; action buttons offer only valid next transitions and respect the caller's role.
- Segregation-of-duties guard: the "Verify" action is disabled for the user who entered the result, with an explanatory tooltip.
- "Reject Back" opens a reason modal and returns the result to input for correction.
- Result visibility to patient explained inline: "Hasil menjadi terlihat oleh pasien setelah dipublikasikan." (Results become visible to the patient once published.)
- All labels in active locale; timestamps in branch timezone.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/lab/orders/:order_id/results`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Laboratorium) + main content; order header (PHI masked); per-result lifecycle pipeline above the result values; role-aware action toolbar.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — order header: patient identifier (PHI masked), ordering doctor, reference
  - `FlexProgress` — lifecycle pipeline: Dimasukkan (Entered) → Diverifikasi (Verified) → Disetujui (Approved) → Dipublikasikan (Published); current step highlighted
  - `FlexForm` — result values (as Story 5.3.1); read-only once verified
  - `FlexBadge` — lifecycle state badge; "KRITIS" badge; PHI mask toggle
  - `FlexModal` — "Kembalikan untuk Koreksi" (Reject Back) reason modal
  - `FlexButton` — role/state-aware: "Verifikasi" (Verify), "Setujui" (Approve), "Publikasikan" (Publish), "Kembalikan untuk Koreksi" (Reject Back); only valid actions enabled
  - `FlexTooltip` — on disabled "Verifikasi" for the entering user: "Verifikasi harus dilakukan oleh petugas berbeda" (Verification must be done by a different staff member)
  - `FlexAlert` — audit note "Hasil menjadi terlihat oleh pasien setelah dipublikasikan."; success/error
- **Key interactions:**
  - Pipeline reflects state; buttons offer only valid transitions for the caller's role.
  - "Verifikasi" disabled (with tooltip) for the user who entered the result — segregation of duties.
  - "Kembalikan untuk Koreksi" requires a reason and returns the result to "Dimasukkan"; the entering tech is notified.
  - Critical results surface the acknowledgement path (Feature 5.4) from the "Diverifikasi" step onward; patient visibility only at "Dipublikasikan".
  - Values become read-only once verified; further edits require reject-back.
- **Empty state:** N/A (page scoped to an order with results).
- **Error state:** Same-actor verify attempt: inline "Anda tidak dapat memverifikasi hasil yang Anda masukkan" (You cannot verify a result you entered); transition failure: `FlexAlert` at top.
- **i18n:** Pipeline step labels, state badges, all action labels, segregation tooltip, reject-back reason modal, visibility note, error/success strings, timestamp format translated (ID / EN).
- **Mobile:** Secondary; pipeline horizontally scrollable; actions stack below results; reject-back modal full-screen.

### Story 5.2.2 [OPEN]
**As a** Lab Tech,
**I want to** generate a unique barcode per specimen and print a specimen label,
**so that** every sample is uniquely identified, scannable through processing, and correctly matched to its order without transcription error.

**Backend AC:**
- On specimen creation, the system assigns a unique, tenant/branch-scoped `specimen_barcode` (deterministic, collision-free; format documented in schema-hc-02) if not supplied by an external analyzer; stored on the specimen record and unique per tenant.
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/lab-orders/:order_id/specimens/:specimen_id/label` — auth: Lab Tech / Branch Manager; returns a print-ready label payload (barcode symbology + human-readable fields): specimen barcode, order reference, specimen type, collection time, and a minimal patient identifier (name initials + partial DOB — PHI-minimized per adr-hc-002); full name never on the label.
- `POST .../specimens/:specimen_id/label/print` — records a `lab.label_printed` audit event `(specimen_id, actor_id, branch_id, tenant_id, at, copies)`; supports reprint with a reprint flag and audit.
- Barcode is the lookup key for specimen status updates: scanning a barcode resolves to the specimen for the collect/process/result/reject transitions in Story 5.2.1.
- `GET .../specimens/lookup?barcode=` — auth: Lab Tech; resolves a scanned barcode to its specimen/order (branch-scoped; 404 cross-branch).

**Frontend AC:**
- Route: `/clinic/lab/orders/:order_id`
- Per-specimen "Print Label" action generates a print-ready label preview (barcode + human-readable order ref, specimen type, collection time, minimal patient identifier) and opens the browser print dialog; reprint available with a reprint indicator.
- A barcode scan/search field at the top of the lab queue and order pages resolves a scanned barcode directly to the specimen for status updates.
- Label deliberately omits full patient name (PHI-minimized); a note explains this.
- All labels in active locale; label field labels localized; barcode value itself is locale-neutral.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/lab/orders/:order_id` (per-specimen label action) + barcode scan field on `#/clinic/lab/orders`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Laboratorium) + main content; per-test specimen block gains a "Cetak Label" (Print Label) action; a barcode scan `FlexInput` sits in the toolbar of the order and queue pages.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexInput` — barcode scan/search field (toolbar): placeholder "Pindai atau ketik barcode" (Scan or type barcode); auto-submits on scanner return
  - `FlexButton` — "Cetak Label" (Print Label) per specimen; "Cetak Ulang" (Reprint) when already printed
  - `FlexModal` — label preview: barcode graphic + human-readable Referensi Pesanan, Jenis Spesimen, Waktu Pengumpulan, initials + partial DOB; "Cetak" (Print) triggers browser print dialog
  - `FlexBadge` — "Sudah dicetak" (Printed) / "Cetak ulang" (Reprint) indicator; PHI mask toggle on order header
  - `FlexAlert` — note: "Label tidak memuat nama lengkap pasien demi privasi." (Label omits full patient name for privacy.); scan-not-found error
- **Key interactions:**
  - "Cetak Label" opens a label preview modal with a rendered barcode and the minimal human-readable fields; "Cetak" opens the browser print dialog; a print event is audited.
  - Reprint shows a "Cetak ulang" indicator and is separately audited.
  - Barcode scan field: scanning (or typing + enter) resolves to the matching specimen and jumps to it for a status update; unknown/cross-branch barcode shows a not-found alert.
  - Label preview shows only initials + partial DOB, never the full name.
- **Empty state:** N/A (per existing order); scan field shows placeholder until used.
- **Error state:** Barcode not found / cross-branch: `FlexAlert` "Barcode tidak ditemukan di cabang ini" (Barcode not found in this branch); print/label fetch failure: inline `FlexAlert`.
- **i18n:** "Cetak Label"/"Cetak Ulang", label field labels, scan placeholder, privacy note, printed/reprint badges, not-found/error strings translated (ID / EN); barcode value locale-neutral.
- **Mobile:** Secondary; label preview modal full-screen; scan field supports device camera barcode input where available.

## R2 Addendum Story Count: Feature 5.3 (1: 5.3.3) + Feature 5.2 (1: 5.2.2) = **2 stories** (epic total: 8)
