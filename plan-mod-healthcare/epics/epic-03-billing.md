---
artifact_id: epic-03-billing
status: active
version: 2
module: healthcare_billing
launch_phase: Month 2-3 post-GA
producer: A3 Product Owner
upstream: vision-02, research-02
created: 2026-06-21
---

# Epic 03 — Billing Module

**Module:** `healthcare_billing` (requires `healthcare` base)
**Launch Phase:** Month 2–3 post-GA
**Summary:** Encounter-to-invoice workflow, BPJS Kesehatan file export, payment tracking, and patient insurance/coverage management.

---

## Feature 3.1 — Encounter-to-Invoice

### Story 3.1.1 [OPEN]
**As a** Billing Staff member,
**I want to** generate an invoice from a completed encounter with itemized services,
**so that** the patient is billed accurately for their visit.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/invoices` — auth: Billing Staff, Branch Manager; payload: `encounter_id`; pulls service items from encounter (consultation fee, procedures, medications if pharmacy active, lab tests if lab active).
- Invoice record: `(invoice_id, tenant_id, branch_id, patient_id, encounter_id, line_items[], total_amount, currency: IDR, status: draft, created_at)`.
- `PUT .../invoices/:invoice_id/finalize` — status: draft → finalized; finalized invoices are immutable; amendments create credit notes.
- Invoice creation emits `invoice.created` audit event.

**Frontend AC:**
- Route: `/clinic/billing/invoices/new?encounter_id=`
- Auto-populated line items from encounter; editable quantity/unit price before finalizing.
- Totals panel: subtotal, tax (if applicable, configurable per tenant), total in IDR.
- "Finalize Invoice" button; PDF preview before finalizing.
- All currency amounts formatted per active locale (IDR with Indonesian thousand separator).

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/billing/invoices/new?encounter_id=`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Penagihan > Buat Tagihan) + main content; two-column — line items table (left 65%) + totals panel (right 35%); action toolbar pinned to bottom.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexTable` — line items: Layanan/Produk, Qty, Harga Satuan (Unit Price), Subtotal; inline editable qty/price
  - `FlexInput` — qty and unit price cells (inline edit); tax override field (if applicable)
  - `FlexCard` — totals panel: Subtotal, Pajak (Tax), Total IDR; amounts formatted with Indonesian thousand separator (.) for ID locale
  - `FlexButton` — "Finalisasi Tagihan" (Finalize Invoice) primary; "Pratinjau PDF" (Preview PDF) secondary; "Simpan Draf" (Save Draft)
  - `FlexModal` — PDF preview modal before finalizing
  - `FlexAlert` — auto-populated success note; finalization confirmation
  - `FlexBadge` — PHI mask toggle on patient name in invoice header (masks to initials)
- **Key interactions:**
  - Page loads with line items auto-populated from encounter; doctor/nurse sees read-only; Billing Staff can edit qty/price.
  - "Pratinjau PDF" opens PDF in `FlexModal` rendered in tenant's active locale.
  - "Finalisasi Tagihan": confirmation modal "Tagihan yang sudah difinalisasi tidak dapat diubah." (Finalized invoices cannot be changed.); on confirm → status: finalized; page becomes read-only.
  - All amounts in IDR; period/comma thousand separator follows active locale (ID: `1.000.000`; EN: `1,000,000`).
  - PHI: patient name visible in invoice header with mask toggle.
- **Empty state:** N/A (line items auto-populated from encounter).
- **Error state:** Encounter not found: `FlexAlert` "Kunjungan tidak ditemukan atau belum selesai" (Encounter not found or not completed); save failure inline.
- **i18n:** Column headers, totals labels, tax label, button labels, modal text, currency format, PDF locale, empty/error strings translated.
- **Mobile:** Secondary; totals panel stacks below line items; table horizontally scrollable.

### Story 3.1.2 [OPEN]
**As a** Patient,
**I want to** view and download my invoice after a visit,
**so that** I have a record for reimbursement or insurance purposes.

**Backend AC:**
- `GET /api/v1/patients/me/invoices/:invoice_id` — auth: Patient (own invoices only); returns invoice data.
- `GET /api/v1/patients/me/invoices/:invoice_id/pdf` — generates PDF invoice in patient's locale; includes clinic logo, address, invoice number, line items, total, payment status.

**Frontend AC:**
- Route: `/patient/invoices/:invoice_id`
- Invoice detail view: clinic info, date, line items table, total, payment status badge.
- "Download PDF" button; PDF generated in patient's locale.
- All amounts in IDR with locale-appropriate formatting.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/patient/invoices/:invoice_id`
- **Portal:** Patient Portal
- **Layout:** Mobile-first; invoice detail card; "Unduh PDF" (Download PDF) button prominent; bottom navigation bar.
- **Components:**
  - `FlexCard` — invoice header: clinic logo, name, address, invoice number, date
  - `FlexTable` — line items: nama layanan, qty, harga, subtotal
  - `FlexCard` — totals: subtotal, pajak, total; payment status badge
  - `FlexBadge` — payment status (Lunas / Belum Lunas / Sebagian Dibayar — Paid / Unpaid / Partially Paid)
  - `FlexButton` — "Unduh PDF" (Download PDF) primary; 56 px full-width on mobile
  - `FlexAlert` — download success/failure
- **Key interactions:**
  - "Unduh PDF": triggers PDF generation in patient's locale; file downloads as `tagihan-[invoice_number].pdf`.
  - All amounts in IDR formatted per patient's locale.
  - Payment status badge color: green (Lunas), amber (Sebagian), red (Belum Lunas).
- **Empty state:** N/A (detail page).
- **Error state:** Invoice not found: "Tagihan tidak ditemukan." (Invoice not found.); PDF download failure: `FlexAlert` "Gagal mengunduh PDF" (Failed to download PDF).
- **i18n:** Column headers, totals labels, status badges, download button label, date format in patient locale, currency format, error strings translated.
- **Mobile:** Primary; single-column card; line items table scrollable; PDF button full-width.

## Feature 3.2 — BPJS Kesehatan Export

### Story 3.2.1 [OPEN]
**As a** Billing Staff member,
**I want to** export a BPJS Kesehatan claim file for a billing period,
**so that** I can submit claims to BPJS without manual data re-entry.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/bpjs-exports` — auth: Billing Staff, Branch Manager; payload: `period_from`, `period_to`, `bpjs_format_version` (configurable, default: latest).
- Selects finalized invoices with `insurance_type: BPJS` in the period; generates BPJS-format file (CSV/text per current BPJS specification).
- Export file stored in tenant-isolated storage; download link returned; link expires in 24h.
- Export event logged: `bpjs.export_generated` with period, record count, format version.
- Format version adapter is swappable without code deploy (versioned config).

**Frontend AC:**
- Route: `/clinic/billing/bpjs-export`
- Period selector (month/year); format version shown (read-only); BPJS member IDs completeness check (warning if any invoices in period have missing BPJS ID).
- "Generate Export" button → progress indicator → download link.
- Export history table: date, period, record count, download link (24h expiry badge).

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/billing/bpjs-export`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Penagihan > Ekspor BPJS) + main content; export form at top; export history table below.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexForm` — period selector (month/year `FlexSelect`); BPJS format version label (read-only `FlexBadge`)
  - `FlexAlert` — completeness warning: "Ada [N] tagihan dengan ID BPJS tidak lengkap dalam periode ini." (There are [N] invoices with incomplete BPJS IDs in this period.)
  - `FlexButton` — "Buat Ekspor" (Generate Export); disabled while processing
  - `FlexProgress` — export progress indicator (indeterminate spinner during generation)
  - `FlexTable` — export history: Tanggal Ekspor, Periode, Jumlah Data, Link Unduh, Status Tautan (24j)
  - `FlexBadge` — download link expiry indicator ("Kedaluwarsa dalam Xj" — Expires in Xh; greyed when expired)
- **Key interactions:**
  - Selecting period: completeness check auto-runs and shows warning if any invoices in period have missing BPJS IDs; link to list of affected invoices.
  - "Buat Ekspor": shows progress spinner; on complete, download link appears in history table.
  - Download link valid 24h; expired links show "Kedaluwarsa" badge; re-generate available.
  - Format version shown as read-only info (e.g., "BPJS Format v2024"); tooltip explains adapter versioning.
- **Empty state (history):** "Belum ada ekspor yang dibuat." (No exports generated yet.)
- **Error state:** Generation failure: `FlexAlert` "Ekspor gagal dibuat. Coba lagi." (Export generation failed. Try again.)
- **i18n:** Period selector labels (month names in active locale), format version label, warning text, history table headers, expiry labels, button labels, empty/error strings translated.
- **Mobile:** Secondary; export form single-column; history table scrollable.

## Feature 3.3 — Payment Tracking

### Story 3.3.1 [OPEN]
**As a** Billing Staff member,
**I want to** record a payment against an invoice and generate a receipt,
**so that** the outstanding balance is updated and the patient has proof of payment.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/invoices/:invoice_id/payments` — auth: Billing Staff; payload: `amount`, `payment_method` (cash/transfer/BPJS/insurance), `reference` (optional transfer ref), `paid_at`.
- Partial payments allowed; outstanding_balance = total - sum(payments).
- Invoice status: `finalized` → `partially_paid` → `paid`.
- Receipt generated and linked; payment event logged to audit trail.
- `GET .../invoices/:invoice_id/payments` — payment history for the invoice.

**Frontend AC:**
- Route: `/clinic/billing/invoices/:invoice_id`
- Payment panel: outstanding balance display; "Record Payment" button → modal: amount, method, reference, date.
- Payment history list below invoice; receipt download per payment.
- Status badge updates on payment record.
- All amounts in IDR; dates in branch timezone.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/billing/invoices/:invoice_id`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Penagihan) + main content; invoice header + line items table (read-only after finalization); payment panel below (outstanding balance, payment history, "Catat Pembayaran" button).
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — invoice summary: invoice number, patient name (with PHI mask toggle), date, total, outstanding balance, status badge
  - `FlexTable` — line items (read-only); payment history rows: tanggal, metode, jumlah, referensi, link kuitansi
  - `FlexModal` — "Catat Pembayaran" modal: amount `FlexInput`, payment method `FlexSelect`, reference `FlexInput`, date `FlexDatepicker`
  - `FlexButton` — "Catat Pembayaran" (Record Payment); "Unduh Kuitansi" (Download Receipt) per payment row
  - `FlexBadge` — invoice status badge; payment method badge per row
  - `FlexBadge` — PHI mask toggle on patient name in invoice header
- **Key interactions:**
  - "Catat Pembayaran": opens modal; amount defaults to outstanding balance (editable for partial payment); on confirm → payment recorded, balance updated, status badge updates.
  - Payment method options: Tunai (Cash), Transfer, BPJS, Asuransi (Insurance).
  - Partial payments: outstanding balance recalculates; status badge changes to "Sebagian Dibayar" (Partially Paid).
  - "Unduh Kuitansi": downloads PDF receipt for specific payment in active locale.
  - All amounts in IDR; dates in branch timezone.
- **Empty state (payment history):** "Belum ada pembayaran tercatat." (No payments recorded yet.)
- **Error state:** Payment record failure: `FlexAlert` in modal "Pembayaran gagal dicatat" (Payment could not be recorded).
- **i18n:** Invoice labels, payment method options, modal field labels, status badges, receipt download label, currency format, date format, empty/error strings translated.
- **Mobile:** Secondary; panels stack vertically; modal full-screen.

### Story 3.3.2 [OPEN]
**As a** Branch Manager,
**I want to** view an outstanding balance report for my branch,
**so that** I can follow up on unpaid invoices.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/billing/outstanding?as_of=` — auth: Branch Manager, Clinic Owner; returns list of invoices with `status: finalized | partially_paid`, patient name (first name + last initial for display), amount due, days outstanding.

**Frontend AC:**
- Route: `/clinic/billing/outstanding`
- Table: patient identifier, invoice date, due amount, days outstanding, status badge.
- Sortable by days outstanding; filter by payment method / insurance type.
- Export to CSV; all amounts in IDR.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/billing/outstanding`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Penagihan > Tunggakan) + main content; filter toolbar above table; sortable/filterable table; "Ekspor CSV" button.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexToolbar` — filter row: payment method `FlexSelect`, insurance type `FlexSelect`, days outstanding range `FlexInput`
  - `FlexTable` — columns: Pasien, Tanggal Tagihan, Jumlah Tertunggak (Amount Due), Hari Tertunggak (Days Outstanding), Status; sortable; clickable row to invoice detail
  - `FlexBadge` — status badge per row (Belum Lunas / Sebagian Dibayar)
  - `FlexBadge` — PHI mask toggle in table header (masks patient names to first name + last initial)
  - `FlexButton` — "Ekspor CSV"
  - `FlexPagination` — table pagination
- **Key interactions:**
  - Table default sort: Hari Tertunggak descending (oldest first).
  - Row click: navigates to `/clinic/billing/invoices/:invoice_id`.
  - PHI mask: patient column shows "Budi S." format when masked.
  - "Ekspor CSV": downloads table as CSV with active filters applied; filename includes date in locale format.
- **Empty state:** "Tidak ada tagihan tertunggak." (No outstanding invoices.)
- **Error state:** `FlexAlert` "Gagal memuat data tunggakan" (Failed to load outstanding data).
- **i18n:** Column headers, filter labels, status badges, currency format (IDR), export filename format, empty/error strings translated.
- **Mobile:** Secondary; table scrollable; filter collapses to `FlexDrawer`.

## Feature 3.4 — Insurance & Coverage Management

### Story 3.4.1 [OPEN]
**As a** clinical staff member (Nurse or Billing Staff),
**I want to** record a patient's insurance details (BPJS or private insurance) on their profile,
**so that** invoices can be correctly coded for insurance billing.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/patients/:patient_id/insurance` — auth: Nurse, Billing Staff, Branch Manager; payload: `insurance_type` (BPJS/private), `member_id`, `policy_number` (private), `coverage_class` (BPJS class 1/2/3), `valid_from`, `valid_to`.
- Multiple insurance records allowed per patient (BPJS + supplemental private).
- Insurance record stored as PHI; access logged to audit trail.

**Frontend AC:**
- Route: `/clinic/patients/:patient_id/insurance`
- Insurance list per patient; "Add Insurance" button → form with type-specific fields.
- BPJS type: member ID, coverage class selector. Private type: insurer name, policy number, valid dates.
- Expiry warning badge if valid_to within 30 days.
- All labels in active locale.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/patients/:patient_id/insurance`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Pasien > Asuransi) + main content (within patient detail section); insurance card list; "Tambah Asuransi" (Add Insurance) button top-right.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexCard` — per insurance entry: type badge (BPJS / Swasta), member ID (masked by default — PHI), coverage class (BPJS), policy number, valid dates, expiry warning badge
  - `FlexBadge` — insurance type badge; "Segera Kedaluwarsa" (Expiring Soon) warning badge if valid_to ≤ 30 days
  - `FlexModal` — "Tambah Asuransi" modal: type `FlexSelect` → conditional fields per type
  - `FlexButton` — "Tambah Asuransi"; edit/delete per card
  - `FlexBadge` — PHI mask toggle on member ID and policy number fields (shown as ●●●●● by default)
- **Key interactions:**
  - Insurance type selector: choosing BPJS shows member ID + coverage class (1/2/3) fields; choosing Swasta shows insurer name + policy number + valid date range.
  - Member ID and policy number are PHI-sensitive — shown masked (●●●●) by default; click eye icon to reveal for the current session.
  - Expiry warning: card highlighted with amber border; "Segera Kedaluwarsa dalam [N] hari" (Expiring in [N] days) badge.
  - Deletion: confirmation modal required.
- **Empty state:** "Belum ada data asuransi. Tambahkan asuransi pasien." (No insurance data yet. Add patient insurance.)
- **Error state:** Save failure: `FlexAlert` in modal "Gagal menyimpan data asuransi" (Failed to save insurance data).
- **i18n:** Type options, coverage class labels, field labels, modal text, expiry warning text, mask toggle tooltip, empty/error strings translated.
- **Mobile:** Secondary; cards full-width; modal full-screen.

### Story 3.4.2 [OPEN]
**As a** Billing Staff member,
**I want to** flag an invoice for coverage verification before finalizing,
**so that** BPJS or insurance-covered services are correctly separated from out-of-pocket charges.

**Backend AC:**
- `PUT /api/v1/.../invoices/:invoice_id/coverage-check` — auth: Billing Staff; sets `coverage_status: pending_verification`; records `checked_by`, `checked_at`.
- `PUT .../coverage-check/resolve` — sets `coverage_status: verified | rejected`; `rejection_reason` required if rejected.
- Coverage check status changes logged to audit trail.

**Frontend AC:**
- Route: `/clinic/billing/invoices/:invoice_id`
- Coverage status badge; "Start Coverage Check" button on draft invoices with insurance patient.
- Verification modal: confirm covered services vs. out-of-pocket; add rejection reason if rejected.
- Status history timeline (pending → verified/rejected) visible on invoice detail.

---


#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/billing/invoices/:invoice_id` (coverage check panel within invoice detail)
- **Portal:** Clinic Portal
- **Layout:** Existing invoice detail page (Story 3.3.1); coverage check panel is an additional section below invoice header; status timeline at bottom of panel.
- **Components:**
  - `FlexBadge` — coverage status badge: Belum Diverifikasi (Not Verified, grey) / Verifikasi Tertunda (Pending, amber) / Terverifikasi (Verified, green) / Ditolak (Rejected, red)
  - `FlexButton` — "Mulai Verifikasi Cakupan" (Start Coverage Check) — visible on draft invoices with insured patient
  - `FlexModal` — verification modal: covered services checklist, out-of-pocket items, rejection reason `FlexTextarea` (if rejected)
  - `FlexCard` — status history timeline: Tertunda → Terverifikasi / Ditolak with actor name and timestamp
  - `FlexAlert` — prompt for Billing Staff if patient has insurance but no coverage check started
- **Key interactions:**
  - "Mulai Verifikasi Cakupan": opens modal with invoice line items split into "Ditanggung Asuransi" (Insurance Covered) and "Biaya Sendiri" (Out-of-Pocket) sections.
  - Resolve: "Terverifikasi" or "Ditolak"; rejection requires reason text.
  - Status timeline shows full audit trail of coverage check (Pending → Verified/Rejected) with actor and timestamp.
  - Auto-prompt: if patient has BPJS/insurance and invoice is draft without coverage check, amber `FlexAlert` shown.
- **Empty state (timeline):** No timeline shown until coverage check started.
- **Error state:** Status update failure: `FlexAlert` in modal "Gagal memperbarui status verifikasi" (Failed to update verification status).
- **i18n:** Status badge labels, modal section labels, rejection reason placeholder, timeline labels, alert text, button labels, timestamp format translated.
- **Mobile:** Secondary; panel stacks below invoice; modal full-screen.

## Story Count: Feature 3.1 (2) + 3.2 (1) + 3.3 (2) + 3.4 (2) = **7 stories**
