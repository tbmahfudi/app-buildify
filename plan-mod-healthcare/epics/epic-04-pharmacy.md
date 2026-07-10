---
artifact_id: epic-04-pharmacy
status: active
version: 2
module: healthcare_pharmacy
launch_phase: Month 3-4 post-GA
producer: A3 Product Owner
upstream: vision-02, research-02
created: 2026-06-21
---

# Epic 04 — Pharmacy Module

**Module:** `healthcare_pharmacy` (requires `healthcare` base)
**Launch Phase:** Month 3–4 post-GA
**Summary:** Per-branch medication catalog, prescription management, dispensing workflow with audit, and drug interaction check adapter.

---

## Feature 4.1 — Medication Catalog

### Story 4.1.1 [OPEN]
**As a** Branch Manager or Pharmacist,
**I want to** maintain a medication catalog for my branch with drug names, dosage forms, and stock levels,
**so that** doctors can prescribe only from available medications at my branch.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/pharmacy/catalog` — auth: Pharmacist, Branch Manager; payload: `drug_name`, `generic_name`, `dosage_form`, `strength`, `unit`, `current_stock`, `reorder_threshold`, `drug_code` (optional, adapter field for external drug DB).
- Catalog is branch-scoped; shared tenant-level drug master data can be imported but overrides are per-branch.
- `GET .../catalog?search=&page=` — returns paginated catalog; accessible to Doctor for prescription creation.
- Stock changes emit `pharmacy.stock_adjusted` audit event.

**Frontend AC:**
- Route: `/clinic/pharmacy/catalog`
- Catalog table: drug name, generic name, form, strength, stock, status (in-stock / low / out).
- "Add Drug" button; inline stock edit; search bar.
- Low-stock badge (below reorder threshold); filter by status.
- All labels in active locale; stock quantities as integer.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/pharmacy/catalog`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Farmasi > Katalog Obat) + main content; search bar + status filter above table; "Tambah Obat" (Add Drug) button top-right; paginated catalog table.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexInput` — search bar (drug name or generic name)
  - `FlexSelect` — status filter (Semua / Tersedia / Stok Rendah / Habis)
  - `FlexTable` — columns: Nama Obat, Nama Generik, Bentuk (Form), Kekuatan (Strength), Stok, Status; sortable; inline stock edit
  - `FlexBadge` — stock status badge: Tersedia (green) / Stok Rendah (amber) / Habis (red)
  - `FlexModal` — "Tambah Obat" form: all catalog fields
  - `FlexInput` — inline stock quantity edit per row (integer; click to edit)
  - `FlexButton` — "Tambah Obat"; save per inline edit
- **Key interactions:**
  - Search: debounced 300 ms; filters table in real-time.
  - Inline stock edit: click stock cell → input field; enter/tab to confirm; emits `pharmacy.stock_adjusted` audit event.
  - "Tambah Obat" modal: all catalog fields; drug code optional; on save, item appears in table.
  - Status filter defaults to "Semua" (All); "Stok Rendah" filter pre-applied if arriving from low-stock banner.
- **Empty state:** "Katalog obat kosong. Tambahkan obat untuk memulai." (Drug catalog is empty. Add drugs to get started.)
- **Error state:** Save failure: `FlexAlert` in modal or inline "Gagal menyimpan data obat" (Failed to save drug data).
- **i18n:** Column headers, status badge labels, form field labels, filter options, modal button labels, empty/error strings translated.
- **Mobile:** Secondary; table collapses to card list; inline edit replaced by "Edit Stok" button → modal.

### Story 4.1.2 [OPEN]
**As a** Pharmacist,
**I want to** receive low-stock alerts for medications approaching the reorder threshold,
**so that** I can reorder before stock runs out.

**Backend AC:**
- Background job runs daily; identifies branch catalog items where `current_stock <= reorder_threshold`.
- Notification sent to Pharmacist and Branch Manager (in-app + email); notification body: drug name, current stock, threshold — no PHI.
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/pharmacy/catalog/low-stock` — auth: Pharmacist, Branch Manager.

**Frontend AC:**
- Route: `/clinic/pharmacy/catalog` — low-stock items surfaced in a banner at the top; filterable.
- Notification center shows low-stock alerts with direct link to catalog item.
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/pharmacy/catalog` (low-stock panel) + notification center
- **Portal:** Clinic Portal
- **Layout:** Low-stock alert shown as a dismissible banner at top of catalog page; also surfaced in notification center sidebar badge.
- **Components:**
  - `FlexAlert` — amber banner at top of catalog: "Ada [N] obat mendekati batas stok minimum." (There are [N] drugs approaching minimum stock.) with "Lihat" (View) link that applies Stok Rendah filter
  - `FlexBadge` — notification center badge count (low-stock count)
  - `FlexNotification` — notification center entry: drug name, current stock, threshold; link to catalog item
  - `FlexButton` — "Abaikan" (Dismiss) banner per session (re-shows on next page load if still low)
- **Key interactions:**
  - Banner "Lihat" link applies "Stok Rendah" filter to catalog table.
  - Notification center entry click navigates directly to catalog item row.
  - Banner is informational only; no action required beyond navigation to catalog.
  - No PHI on this page.
- **Empty state:** Banner and notification hidden when no items below threshold.
- **Error state:** Notification fetch failure: notification center shows last-known count with stale indicator.
- **i18n:** Banner text, notification center entry text, dismiss label, "Lihat" label translated.
- **Mobile:** Secondary; banner full-width; notification center accessible via top-right bell icon.

## Feature 4.2 — Prescription Management

### Story 4.2.1 [OPEN]
**As a** Doctor,
**I want to** create a digital prescription for a patient during an encounter,
**so that** the pharmacist can dispense the correct medications.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/prescriptions` — auth: Doctor; payload: `encounter_id`, `patient_id`, `line_items[]: {drug_catalog_id, dose, frequency, duration, instructions}`.
- Prescription linked to encounter; `status: pending_dispense`.
- Drug interaction check triggered asynchronously (adapter call); result attached to prescription before pharmacist review.
- Prescription creation emits `prescription.created` PHI audit event.

**Frontend AC:**
- Route: `/clinic/encounters/:encounter_id/prescription`
- Drug search within branch catalog (autocomplete); dose/frequency/duration fields per line item; instructions (free text, locale-aware label).
- Drug interaction check result banner (warning / clear / unavailable) displayed after save.
- "Submit Prescription" sends to pharmacist queue.
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id/prescription`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Kunjungan > Resep) + main content; encounter patient strip at top (name with PHI mask toggle); prescription line items below; drug interaction result banner; action toolbar at bottom.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — patient strip: name (masked), DOB, encounter reference
  - `FlexForm` — prescription builder: drug search + per-item fields
  - `FlexInput` — drug autocomplete search within branch catalog
  - `FlexInput` + `FlexSelect` — dose (number), frequency (select), duration (number + unit select) per line item
  - `FlexTextarea` — instructions per line item (locale-aware placeholder)
  - `FlexBadge` — drug interaction result inline per line item + summary banner
  - `FlexAlert` — interaction result banner: green (Tidak ada interaksi — No interactions), amber (Peringatan interaksi: [ringkasan] — Interaction warning: [summary]), grey (Pemeriksaan tidak tersedia — Check unavailable)
  - `FlexCheckbox` — acknowledgement checkbox for amber warning (required before submit)
  - `FlexButton` — "Kirim Resep" (Submit Prescription) primary; "Tambah Obat" (Add Drug) secondary
  - `FlexBadge` — PHI mask toggle on patient strip
- **Key interactions:**
  - Drug autocomplete shows branch catalog only; no out-of-catalog prescribing.
  - Each drug line added → interaction check triggered (async); result badge updates on line item.
  - Amber interaction warning: expandable detail; acknowledgement checkbox must be checked before "Kirim Resep" enabled.
  - Grey (unavailable) state: "Periksa interaksi secara manual" (Verify interactions manually) — does NOT block submission.
  - "Kirim Resep" sends to pharmacist queue; success toast "Resep berhasil dikirim" (Prescription sent successfully).
- **Empty state:** "Belum ada obat ditambahkan. Cari obat untuk memulai." (No drugs added yet. Search for drugs to start.)
- **Error state:** Drug not found in catalog: "Obat tidak ditemukan di katalog cabang ini" (Drug not found in this branch's catalog); submit failure: `FlexAlert` top of form.
- **i18n:** All field labels, frequency options, duration unit options, instruction placeholder, interaction result states, acknowledgement text, button labels, empty/error strings translated.
- **Mobile:** Secondary; line items stack vertically; interaction banner full-width.

### Story 4.2.2 [OPEN]
**As a** Pharmacist,
**I want to** view pending prescriptions in my branch queue and confirm fulfillment details before dispensing,
**so that** I can verify the prescription before releasing medications.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/prescriptions?status=pending_dispense` — auth: Pharmacist, Branch Manager.
- `PUT .../prescriptions/:prescription_id/review` — auth: Pharmacist; can add pharmacist notes; status: `pending_dispense` → `reviewed`.
- Returns drug interaction check result; Pharmacist can flag concern before dispensing.

**Frontend AC:**
- Route: `/clinic/pharmacy/queue`
- Queue list: patient identifier, prescribing doctor, time created, drug count, interaction flag badge.
- Prescription detail panel: line items, drug interaction result, pharmacist notes field.
- "Mark Reviewed" button; "Flag Concern" button (notifies prescribing doctor).
- All labels in active locale; timestamps in branch timezone.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/pharmacy/queue`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Farmasi > Antrean Resep) + main content; queue list left (1/3 width) + prescription detail panel right (2/3 width); branch-scoped.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexTable` — queue list: Pasien (with PHI mask), Dokter Pemeriksa, Waktu Dibuat, Jumlah Obat, Status Interaksi
  - `FlexBadge` — interaction flag: amber "Peringatan Interaksi" / green "Aman" / grey "Tidak Tersedia"; status badge per row
  - `FlexCard` — selected prescription detail: line items, drug interaction result, pharmacist notes `FlexTextarea`
  - `FlexButton` — "Tandai Ditinjau" (Mark Reviewed); "Tandai Masalah" (Flag Concern — notifies prescribing doctor)
  - `FlexAlert` — drug interaction detail in detail panel
  - `FlexBadge` — PHI mask toggle in queue table header
- **Key interactions:**
  - Clicking queue row loads detail in right panel (split-pane on desktop).
  - "Tandai Ditinjau": status → reviewed; row moves to bottom of queue.
  - "Tandai Masalah": opens `FlexModal` with concern note text → notifies prescribing doctor (in-app + optional WhatsApp alert per clinic settings).
  - Interaction result shown per drug line item with expandable detail.
  - Timestamps in branch timezone.
- **Empty state:** "Tidak ada resep menunggu." (No prescriptions pending.)
- **Error state:** `FlexAlert` "Gagal memuat antrean resep" (Failed to load prescription queue).
- **i18n:** Column headers, status badges, interaction labels, button labels, modal text, timestamp format, empty/error strings translated.
- **Mobile:** Secondary; split-pane collapses — queue list full screen; tap row to open detail screen.

## Feature 4.3 — Dispensing Workflow

### Story 4.3.1 [OPEN]
**As a** Pharmacist,
**I want to** record dispensing of a prescription and have stock automatically deducted,
**so that** inventory is accurate and there is a complete dispensing audit trail.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/prescriptions/:prescription_id/dispense` — auth: Pharmacist; payload: `dispensed_items[]: {drug_catalog_id, quantity_dispensed}` (may differ from prescribed if partial).
- Stock deducted from branch catalog atomically; if insufficient stock, returns 422 with `insufficient_stock` error.
- Dispensing record created: `(dispense_id, prescription_id, pharmacist_id, branch_id, tenant_id, dispensed_at, items[])`.
- Status: `reviewed` → `dispensed`; emits `prescription.dispensed` PHI audit event.
- Patient's active prescription list updated in patient portal.

**Frontend AC:**
- Route: `/clinic/pharmacy/prescriptions/:prescription_id/dispense`
- Line items with quantity fields (pre-filled from prescription; editable for partial dispense).
- Stock available shown per line item; warning if quantity > available.
- "Confirm Dispense" button; confirmation modal; post-dispense: status badge updated.
- Partial dispense recorded with reason (free text, internal).

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/pharmacy/prescriptions/:prescription_id/dispense`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Farmasi > Pengeluaran Obat) + main content; prescription summary at top (patient PHI masked); line items with quantity inputs; confirmation toolbar at bottom.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — prescription header: patient identifier (masked), prescribing doctor, date, prescription reference
  - `FlexTable` — line items: Nama Obat, Dosis Resep, Stok Tersedia, Jumlah Dikeluarkan (editable); stock available per row
  - `FlexInput` — quantity dispensed per line item (integer; pre-filled from prescription; editable for partial)
  - `FlexBadge` — stock warning badge if quantity > available ("Stok tidak cukup" — Insufficient stock) per row
  - `FlexBadge` — PHI mask toggle on patient identifier in header
  - `FlexTextarea` — partial dispense reason (free text, internal; visible when quantity < prescribed)
  - `FlexModal` — "Konfirmasi Pengeluaran" (Confirm Dispense) summary + confirmation button
  - `FlexButton` — "Konfirmasi Pengeluaran" primary; "Batal"
  - `FlexAlert` — 422 insufficient stock error; success confirmation
- **Key interactions:**
  - Quantity field editable; if < prescribed quantity, reason `FlexTextarea` appears below that row.
  - Stock available shown per row; if dispensed qty > available: amber badge "Stok tidak cukup" + "Konfirmasi Pengeluaran" disabled until resolved.
  - "Konfirmasi Pengeluaran": opens modal showing dispense summary; "Konfirmasi" → stock deducted, status → dispensed, patient active prescriptions updated.
  - Post-dispense: page shows "Pengeluaran berhasil dicatat" (Dispense successfully recorded) + prescription status badge updates.
- **Empty state:** N/A (dispense page for a specific prescription).
- **Error state:** Insufficient stock API error (422): `FlexAlert` per affected item "Stok [Nama Obat] tidak mencukupi" (Insufficient stock for [Drug Name]); general failure: top-of-page `FlexAlert`.
- **i18n:** Column headers, stock labels, partial reason placeholder, modal text, status labels, error strings, button labels translated.
- **Mobile:** Secondary; table collapses to card per drug; quantity input large; modal full-screen.

## Feature 4.4 — Drug Interaction Check

### Story 4.4.1 [OPEN]
**As a** Doctor,
**I want to** see a drug interaction warning when I prescribe a combination of medications,
**so that** I can avoid potential adverse drug events — even if the external drug database is temporarily unavailable.

**Backend AC:**
- Drug interaction check is an adapter interface: `DrugInteractionAdapter.check(drug_list[]) → InteractionResult`.
- Adapter is pluggable (licensed drug DB such as MIMS Indonesia or equivalent); adapter must be configured per tenant before pharmacy module is GA.
- Graceful degradation: if adapter is unavailable or not configured, response is `{status: "unavailable", message: "interaction check unavailable — verify manually"}` — prescription is NOT blocked; warning displayed.
- Result cached per drug combination for 24h to reduce external API calls.
- Interaction check result stored on prescription record; `check_status: clear | warning | unavailable`.

**Frontend AC:**
- Drug interaction result shown on prescription form after each drug line is added.
- Three states: green "No interactions found", amber "Interaction warning: [summary]" (details expandable), grey "Interaction check unavailable — verify manually".
- Amber warning does NOT prevent submission; requires Doctor to acknowledge (checkbox) before submitting.
- All states rendered in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id/prescription` (inline within prescription form — see Story 4.2.1)
- **Portal:** Clinic Portal
- **Layout:** Drug interaction result is an inline component within the prescription form, not a separate page. Three distinct visual states rendered in active locale.
- **Components:**
  - `FlexAlert` (green variant) — "Tidak ada interaksi ditemukan" (No interactions found) — shown after each drug addition
  - `FlexAlert` (amber variant) — "Peringatan Interaksi: [ringkasan singkat]" (Interaction Warning: [brief summary]) — expandable details; `FlexCheckbox` acknowledgement below
  - `FlexAlert` (grey variant) — "Pemeriksaan interaksi tidak tersedia — verifikasi secara manual" (Interaction check unavailable — verify manually) — no blocking
  - `FlexCheckbox` — "Saya mengakui peringatan ini dan melanjutkan secara klinis" (I acknowledge this warning and proceed clinically) — required for amber state before submission
  - `FlexBadge` — per-drug interaction indicator icon on each line item row
  - `FlexSpinner` — shown while check is running (async, usually <2 s)
- **Key interactions:**
  - Each time a drug is added or removed, interaction check runs asynchronously; spinner shown during check.
  - Green state: no action required; "Kirim Resep" enabled normally.
  - Amber state: expandable detail shows interacting drug pairs + severity level; acknowledgement checkbox required; "Kirim Resep" disabled until checked.
  - Grey state: no action required; "Kirim Resep" enabled (no blocking); grey banner persists as reminder.
  - Result cached per drug combination; if same combination checked within 24h, shows cached result instantly.
- **Empty state:** No alert shown before any drugs are added.
- **Error state:** Same as grey state (unavailable) — no separate error state; graceful degradation is the design intent.
- **i18n:** All three alert state messages, acknowledgement checkbox text, spinner label "Memeriksa interaksi..." (Checking interactions...), interaction severity labels, expandable detail labels translated.
- **Mobile:** Secondary; alerts full-width stacked; acknowledgement checkbox large tap target.

## Story Count: Feature 4.1 (2) + 4.2 (2) + 4.3 (1) + 4.4 (1) = **6 stories**

---

## R2 Gap Addendum (v3)

**Upstream:** BACKLOG v3 (2026-07-02). Closes two R2 dispensing/stock gaps identified in the 20-module
disposition map. New stories continue Feature 4.3 (Dispensing Workflow) and Feature 4.1 (Medication
Catalog) numbering. Existing content above is unchanged. Reuses the platform notification transport
(Reuse Register #7) and scheduler for stock alerts — this addendum specifies healthcare dispensing states
and reorder-alert behavior, not a new notification engine.

### Story 4.3.2 [OPEN]
**As a** Pharmacist,
**I want to** move each prescription through explicit dispensing states — prepare, dispense, reject, and partial-dispense —
**so that** the fulfillment status is unambiguous, auditable, and visible to the doctor and patient at every step.

**Backend AC:**
- Dispensing state machine on the prescription/dispense record: `reviewed → preparing → dispensed | partially_dispensed | rejected`; each transition guarded (no skip-ahead; no transition out of a terminal state except a linked amendment).
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/prescriptions/:prescription_id/prepare` — auth: Pharmacist; `reviewed → preparing`; records `prepared_by`, `prepared_at`; optional `preparation_notes` (internal).
- `POST .../prescriptions/:prescription_id/dispense` (existing, extended) — on submit, if every line's `quantity_dispensed == quantity_prescribed` → status `dispensed`; if at least one line is short but > 0 → status `partially_dispensed` with required `partial_reason` per short line; deducts stock atomically (422 `insufficient_stock` unchanged).
- `PUT .../prescriptions/:prescription_id/reject` — auth: Pharmacist; `preparing | reviewed → rejected`; required `rejection_reason` (controlled vocabulary: out_of_stock, prescription_error, patient_declined, duplicate, other + free text); no stock deducted; emits `prescription.rejected` PHI audit event and notifies the prescribing doctor via the platform notification transport (PHI-safe body: reference code only).
- `partially_dispensed` prescriptions expose a remaining-balance so a follow-up dispense can complete them; a follow-up dispense that clears the balance transitions `partially_dispensed → dispensed`.
- Every transition emits a `prescription.dispense_state_changed` PHI audit event `(prescription_id, from_state, to_state, actor_id, branch_id, tenant_id, at)`; patient portal active-prescription list reflects the current state.

**Frontend AC:**
- Route: `/clinic/pharmacy/prescriptions/:prescription_id/dispense`
- Explicit state control: state pipeline (Ditinjau → Menyiapkan → Dikeluarkan / Sebagian / Ditolak) with the current step highlighted; action buttons offer only the valid next transitions.
- "Prepare" moves to preparing; "Reject" opens a reason modal (controlled vocabulary + free text); partial dispense auto-detected when any dispensed quantity < prescribed, requiring a per-line reason.
- Partially dispensed prescriptions show a "Remaining" column and a "Complete Remaining" action.
- Status badge and pipeline update live; all labels in active locale; timestamps in branch timezone.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/pharmacy/prescriptions/:prescription_id/dispense`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Farmasi > Pengeluaran Obat) + main content; prescription header (patient PHI masked); dispensing state pipeline below header; line-items table; action toolbar at bottom offering only valid transitions.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — prescription header: patient identifier (masked), prescribing doctor, date, reference
  - `FlexProgress` — dispensing state pipeline: Ditinjau (Reviewed) → Menyiapkan (Preparing) → Dikeluarkan (Dispensed) / Sebagian (Partial) / Ditolak (Rejected); current step highlighted; terminal states colour-coded (Dikeluarkan green, Sebagian amber, Ditolak red)
  - `FlexTable` — line items: Nama Obat, Dosis Resep, Stok Tersedia, Jumlah Dikeluarkan (editable), Sisa (Remaining — shown for partial)
  - `FlexInput` — quantity dispensed per line (integer; pre-filled from prescription)
  - `FlexTextarea` — per-line partial reason (appears when dispensed < prescribed)
  - `FlexModal` — "Tolak Resep" (Reject Prescription) reason modal: `FlexSelect` controlled vocabulary (Stok habis / Kesalahan resep / Pasien menolak / Duplikat / Lainnya) + free-text `FlexTextarea`
  - `FlexButton` — context-sensitive: "Siapkan" (Prepare), "Konfirmasi Pengeluaran" (Confirm Dispense), "Tolak" (Reject), "Selesaikan Sisa" (Complete Remaining); only valid next actions enabled
  - `FlexBadge` — status badge; PHI mask toggle on header
  - `FlexAlert` — 422 insufficient stock; reject/partial confirmation; success
- **Key interactions:**
  - Pipeline reflects current state; buttons offer only valid transitions (e.g. "Konfirmasi Pengeluaran" hidden until "Menyiapkan"; "Selesaikan Sisa" only for "Sebagian").
  - "Siapkan": `reviewed → preparing`; optional preparation note.
  - Editing a quantity below prescribed reveals a per-line reason field; submitting a short-but-nonzero set marks the prescription "Sebagian" (partially dispensed) and shows a Remaining balance.
  - "Selesaikan Sisa" reopens the dispense form scoped to the remaining balance; clearing it flips status to "Dikeluarkan".
  - "Tolak": reason modal (controlled vocabulary + free text) required; on confirm status → "Ditolak", no stock deducted, prescribing doctor notified (in-app + optional WhatsApp per clinic settings, PHI-safe reference only).
- **Empty state:** N/A (page scoped to a specific prescription).
- **Error state:** Insufficient stock (422): `FlexAlert` per affected item "Stok [Nama Obat] tidak mencukupi" (Insufficient stock for [Drug Name]); reject without reason: inline "Alasan penolakan wajib diisi" (Rejection reason is required); general failure: top-of-page `FlexAlert`.
- **i18n:** Pipeline step labels, terminal-state labels, column headers (incl. Sisa/Remaining), reject reason vocabulary, partial reason placeholder, all button labels, status badges, error/success strings, timestamp format translated (ID / EN).
- **Mobile:** Secondary; pipeline horizontally scrollable; line-items table collapses to card per drug; reject/partial reason modals full-screen.

### Story 4.1.3 [OPEN]
**As a** Pharmacist or Branch Manager,
**I want to** define a reorder level per catalog item and receive stock alerts when stock falls to or below it,
**so that** I can reorder in time and never dispense from empty stock.

**Backend AC:**
- Each catalog item carries `reorder_threshold` (exists) plus an optional `reorder_quantity` (suggested reorder amount) and `alert_enabled` flag (default true).
- A scheduled job (reuse platform Scheduler — Reuse Register) evaluates each branch catalog once per configured interval (default daily) and also re-evaluates immediately after any stock-decrementing dispense; an item at or below its reorder level with `alert_enabled` raises a `pharmacy.reorder_alert` via the platform notification transport (Reuse Register #7) to Pharmacist + Branch Manager (in-app + email), body: drug name, current stock, reorder level, suggested reorder quantity — no PHI.
- Alerts are de-duplicated: one open alert per catalog item until stock rises above the reorder level (then the alert auto-resolves and can re-fire).
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/pharmacy/catalog/reorder-alerts?status=open` — auth: Pharmacist, Branch Manager; returns open reorder alerts with item, current stock, reorder level, first-raised-at.
- `PUT .../reorder-alerts/:alert_id/acknowledge` — records `acknowledged_by`/`acknowledged_at` (suppresses re-notification but keeps the alert open until restocked); emits `pharmacy.reorder_alert_acknowledged` audit event.

**Frontend AC:**
- Route: `/clinic/pharmacy/catalog` — reorder alerts surfaced in a top banner and a dedicated "Reorder Alerts" panel/tab; each catalog item shows a reorder-level field and a low/at-level indicator.
- Reorder-level editable inline per item; suggested reorder quantity shown; acknowledge action per alert.
- Notification center shows reorder alerts with a direct link to the catalog item.
- All labels in active locale; quantities as integer.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/pharmacy/catalog` (reorder-alerts panel/tab) + notification center
- **Portal:** Clinic Portal
- **Layout:** Reorder alerts as a dismissible top banner plus a "Peringatan Pemesanan Ulang" (Reorder Alerts) tab beside the catalog table; reorder-level column editable inline in the catalog table.
- **Components:**
  - `FlexAlert` — amber banner: "[N] obat berada di atau di bawah level pemesanan ulang." (N drugs at or below reorder level.) with "Lihat" (View) link opening the Reorder Alerts tab
  - `FlexTabs` — Katalog / Peringatan Pemesanan Ulang (count badge)
  - `FlexTable` (alerts tab) — columns: Nama Obat, Stok Saat Ini, Level Pemesanan Ulang, Saran Jumlah, Pertama Muncul, Tindakan
  - `FlexInput` — inline reorder-level edit per catalog row (integer)
  - `FlexBadge` — item indicator: "Di level" (at level, amber) / "Di bawah level" (below level, red)
  - `FlexButton` — "Konfirmasi" (Acknowledge) per alert; "Abaikan" (Dismiss) banner per session
  - `FlexNotification` — notification-center entry: drug name, current stock, reorder level; deep link to catalog item
- **Key interactions:**
  - "Lihat" opens the Reorder Alerts tab; each alert row deep-links to the catalog item.
  - Inline reorder-level edit: click cell → integer input → enter/tab confirms; re-evaluates alert state immediately.
  - "Konfirmasi" acknowledges an alert (stops repeat notifications, keeps it open until restocked); acknowledged rows show a muted state.
  - Alert auto-resolves and disappears when stock rises above the reorder level.
  - No PHI on this page.
- **Empty state:** Banner and alerts tab hidden / "Tidak ada peringatan pemesanan ulang." (No reorder alerts.) when nothing is at or below level.
- **Error state:** Reorder-level save failure: inline "Gagal menyimpan level" (Failed to save level); alert fetch failure: notification center shows last-known count with a stale indicator.
- **i18n:** Banner text, tab labels, column headers, indicator badges, acknowledge/dismiss labels, notification entry text, empty/error strings translated (ID / EN).
- **Mobile:** Secondary; banner full-width; alerts tab as card list; inline edit replaced by an "Edit Level" button → modal.

## R2 Addendum Story Count: Feature 4.3 (1: 4.3.2) + Feature 4.1 (1: 4.1.3) = **2 stories** (epic total: 8)
