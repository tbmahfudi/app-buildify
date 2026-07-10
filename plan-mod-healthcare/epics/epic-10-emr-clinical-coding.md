---
artifact_id: epic-10-emr-clinical-coding
status: active
version: 1
module: healthcare_emr
launch_phase: MVP
producer: A3 Product Owner
upstream: BACKLOG v3
created: 2026-07-02
---

# Epic 10 — EMR Clinical Coding & Notes (ICD-10 / ICD-9-CM)

**Module:** `healthcare_emr` (extends the epic-01 SOAP encounter `hc_encounters`)
**Launch Phase:** MVP
**Summary:** Layers structured clinical coding and note types onto the existing SOAP encounter. Covers
ICD-10 diagnosis typeahead over per-tenant master-data, attaching multiple diagnoses to an encounter
with primary/secondary + sequence, ICD-9-CM procedure coding, and clinical note types (progress,
nursing, observation, follow-up) added to `hc_encounters`.

**References:** ADR-HC-007 (clinical coding), schema-hc-02 (`hc_diagnoses`, `hc_procedures`,
`hc_clinical_notes`, `hc_icd10_codes` / `hc_icd9cm_codes`).

**Scope note (Scope-Out #13):** ICD-10 / ICD-9-CM code sets are **per-tenant master data** — the module
ships the schema + lookup adapter, not the licensed dataset. Codes are loaded via platform no-code
master-data / adapter per tenant (ADR-HC-007 decides catalog table vs. no-code entity). Lookups here
query whatever ADR-HC-007 selects; this epic references them as `hc_icd10_codes` / `hc_icd9cm_codes`.

**Invariants (reused, not re-specified):** platform Auth/RBAC/Audit; branch isolation per adr-hc-001;
**PHI via SDK readers + audit** per adr-hc-002; i18n id-ID (default) + en-US per adr-hc-004; mobile-first.
Coding/notes rows carry `tenant_id`; encounter linkage carries the encounter's branch scope; RLS per
schema-hc-01. `hc_clinical_notes.body` is **PHI-encrypted** (`EncryptedPHIType`) and read only through
SDK readers with audit. Diagnosis/procedure code *values* are not PHI, but their attachment to an
encounter is a clinical (auditable) act.

**Canonical tables:**
- `hc_diagnoses` (id, tenant_id, encounter_id, icd10_code, is_primary, sequence)
- `hc_procedures` (id, tenant_id, encounter_id, icd9cm_code, note)
- `hc_clinical_notes` (id, tenant_id, encounter_id, note_type ∈ {progress, nursing, observation,
  follow_up}, body[PHI-encrypted], author_id)
- `hc_icd10_codes`, `hc_icd9cm_codes` (adapter-loaded per tenant — per ADR-HC-007)

---

## Feature 10.1 — ICD-10 Diagnosis Lookup

### Story 10.1.1 [OPEN]
**As a** Doctor,
**I want to** search ICD-10 codes with a fast typeahead,
**so that** I can find the right diagnosis code without memorizing it.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/icd10/search?q=&page=` — auth: Doctor / Nurse (platform RBAC);
  typeahead over per-tenant `hc_icd10_codes` (code + title, matched on both), tenant-scoped; returns
  paginated `{ code, title, chapter }`; min 2 chars; results ranked (exact code prefix first, then title
  match).
- Backed by the per-tenant master-data catalog selected in ADR-HC-007; returns empty (not 404) when the
  tenant has not loaded a code set, with a `catalog_loaded: false` flag so the UI can prompt setup.
- Not PHI (reference data); reads may be lightly audited but do not require PHI-reader treatment.

**Frontend AC:**
- Route: used inline within the encounter coding panel (`/clinic/encounters/:encounter_id`, Diagnoses
  tab); a debounced typeahead field.
- Shows code + title per suggestion; keyboard-navigable; "no results" and "catalog not loaded" states
  distinguished.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id` (Diagnosa / Diagnoses tab — typeahead)
- **Portal:** Clinic Portal (clinical)
- **Layout:** Encounter page (epic-01 SOAP) with an added Diagnosa tab; typeahead field at the top of the
  tab with a results dropdown.
- **Components:**
  - `FlexSidebar` — clinical nav; branch context badge
  - `FlexInput` — ICD-10 typeahead (debounced 300 ms; min 2 chars)
  - `FlexList` — suggestion dropdown: `code` (mono) + `title`; keyboard up/down/enter navigable
  - `FlexBadge` — chapter tag per suggestion
  - `FlexAlert` — "catalog not loaded" prompt
- **Key interactions:**
  - Typing ≥ 2 chars triggers debounced search; matches on code prefix and title substring; selection
    stages a diagnosis for attachment (10.1.2).
  - When `catalog_loaded = false`, dropdown shows "Kode ICD-10 belum dimuat untuk klinik ini. Hubungi
    admin." (ICD-10 codes not loaded for this clinic. Contact admin.)
  - Reference data only — no PHI in this control.
- **Empty state:** No matches: "Tidak ada kode cocok untuk '[q]'." (No matching codes for '[q]'.)
- **Error state:** Search API failure: inline `FlexAlert` under the field with retry.
- **i18n:** Field placeholder, no-results / catalog-not-loaded / error strings translated (ID / EN); code
  titles served in the tenant's loaded language.
- **Mobile:** Typeahead full-width; dropdown as a full-screen sheet on narrow viewport; large tap targets.

## Feature 10.2 — Encounter Diagnoses (Primary/Secondary + Sequence)

### Story 10.2.1 [OPEN]
**As a** Doctor,
**I want to** attach one or more ICD-10 diagnoses to an encounter,
**so that** the encounter is coded for clinical, billing, and reporting use.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/encounters/:encounter_id/diagnoses` — auth:
  Doctor (encounter owner) for an open/in-progress encounter; payload: `icd10_code`, `is_primary`,
  `sequence`.
- Creates `hc_diagnoses` `(id, tenant_id, encounter_id, icd10_code, is_primary, sequence)`; validates
  `icd10_code` exists in the tenant's `hc_icd10_codes` (422 otherwise) and is unique per
  `(encounter_id, icd10_code)` (409 on duplicate).
- Multiple diagnoses allowed per encounter; write blocked once the encounter is `completed` (amendments
  follow the epic-01 amendment flow).
- Emits `hc_diagnosis.attached` PHI audit event (diagnosis attached to a patient encounter).

**Frontend AC:**
- Route: `/clinic/encounters/:encounter_id` (Diagnoses tab)
- Add-diagnosis row using the 10.1.1 typeahead + primary/secondary choice; attached diagnoses listed
  with code, title, primary flag, sequence.
- Duplicate/invalid-code errors inline; list disabled once encounter completed.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id` (Diagnosa tab — attach)
- **Portal:** Clinic Portal (clinical)
- **Layout:** Diagnosa tab: typeahead + "Tambah" row above a table of attached diagnoses.
- **Components:**
  - `FlexInput` — ICD-10 typeahead (from 10.1.1)
  - `FlexToggle` / `FlexRadio` — Primer (Primary) / Sekunder (Secondary)
  - `FlexTable` — attached diagnoses: Urutan (Sequence), Kode, Judul, Primer/Sekunder, Tindakan
  - `FlexBadge` — "Primer" badge; encounter status badge (read-only when completed)
  - `FlexButton` — "Tambah Diagnosa" (Add Diagnosis), per-row "Hapus"
  - `FlexAlert` — duplicate / invalid-code / completed-lock errors
- **Key interactions:**
  - Select a code via typeahead, choose Primer/Sekunder, "Tambah Diagnosa" attaches and appends to the
    table.
  - Duplicate code inline "Diagnosa ini sudah ditambahkan" (This diagnosis is already added).
  - When the encounter is `completed`, add/remove controls are disabled with a note pointing to the
    amendment flow.
  - Attaching a diagnosis is an audited clinical act (PHI audit).
- **Empty state:** "Belum ada diagnosa. Cari kode ICD-10 untuk menambahkan." (No diagnoses yet. Search an
  ICD-10 code to add.)
- **Error state:** Inline duplicate/invalid; API error `FlexAlert` above the table.
- **i18n:** Labels, primary/secondary options, table headers, empty/error strings translated (ID / EN).
- **Mobile:** Table collapses to card list; typeahead + add controls stack; large tap targets.

### Story 10.2.2 [OPEN]
**As a** Doctor,
**I want to** set exactly one primary diagnosis and order the remaining diagnoses by sequence,
**so that** the coding correctly reflects the principal condition and its ranking.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/encounters/:encounter_id/diagnoses/:diagnosis_id` —
  auth: Doctor (encounter owner); editable: `is_primary`, `sequence`.
- Enforces **exactly one** `is_primary = true` per encounter: setting a new primary atomically clears the
  previous primary (single-primary invariant validated server-side; 409 if the write would leave zero or
  two primaries).
- `PUT /.../diagnoses/reorder` — accepts an ordered list of `diagnosis_id` and rewrites `sequence`
  contiguously (1..N) in one transaction.
- Edits emit `hc_diagnosis.updated` / `hc_diagnosis.reordered` PHI audit events; blocked on completed
  encounters.

**Frontend AC:**
- Route: `/clinic/encounters/:encounter_id` (Diagnoses tab)
- Drag-to-reorder the diagnosis list (sequence); a single "Primary" selector (radio) enforcing exactly
  one primary; changing primary updates the previous one automatically.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id` (Diagnosa tab — order & primary)
- **Portal:** Clinic Portal (clinical)
- **Layout:** The attached-diagnoses table from 10.2.1 with drag handles and a single-select primary
  column.
- **Components:**
  - `FlexTable` — draggable rows (sequence); drag handle per row
  - `FlexRadio` — single "Primer" selector across rows (exactly one selected)
  - `FlexBadge` — sequence number; "Primer" badge
  - `FlexButton` — "Simpan Urutan" (Save Order) if reorder is explicit
  - `FlexAlert` — single-primary / completed-lock errors
- **Key interactions:**
  - Drag a row to change sequence; sequence numbers renumber 1..N on drop.
  - Selecting a different "Primer" radio clears the previous primary automatically (exactly-one
    invariant); the server rejects any state with zero/two primaries.
  - Disabled when encounter completed.
- **Empty state:** Inherits the 10.2.1 empty state (no diagnoses).
- **Error state:** Single-primary violation `FlexAlert` "Harus ada tepat satu diagnosa primer." (There
  must be exactly one primary diagnosis.)
- **i18n:** Column labels, primary label, save/reorder buttons, error strings translated (ID / EN).
- **Mobile:** Reorder via up/down arrows per card (drag on touch as available); primary via a radio per
  card.

## Feature 10.3 — ICD-9-CM Procedure Coding

### Story 10.3.1 [OPEN]
**As a** Doctor,
**I want to** search ICD-9-CM procedure codes with typeahead,
**so that** I can find the correct procedure code quickly.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/icd9cm/search?q=&page=` — auth: Doctor / Nurse; typeahead over
  per-tenant `hc_icd9cm_codes` (code + title), tenant-scoped; paginated; min 2 chars; ranked like the
  ICD-10 search; `catalog_loaded` flag when the tenant has no procedure code set.
- Reference data (not PHI); backed by the ADR-HC-007-selected catalog.

**Frontend AC:**
- Route: inline within `/clinic/encounters/:encounter_id` (Procedures tab); debounced typeahead showing
  code + title.
- "No results" and "catalog not loaded" states distinguished; all labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id` (Prosedur / Procedures tab — typeahead)
- **Portal:** Clinic Portal (clinical)
- **Layout:** Prosedur tab with a typeahead field + results dropdown, mirroring the ICD-10 lookup.
- **Components:**
  - `FlexInput` — ICD-9-CM typeahead (debounced 300 ms; min 2 chars)
  - `FlexList` — suggestion dropdown: code (mono) + title; keyboard-navigable
  - `FlexAlert` — "catalog not loaded" prompt
- **Key interactions:**
  - Typing ≥ 2 chars searches; selection stages a procedure for attachment (10.3.2).
  - `catalog_loaded = false` shows "Kode ICD-9-CM belum dimuat untuk klinik ini." (ICD-9-CM codes not
    loaded for this clinic.)
- **Empty state:** No matches: "Tidak ada kode prosedur cocok." (No matching procedure codes.)
- **Error state:** Search failure inline `FlexAlert` with retry.
- **i18n:** Placeholder, no-results / catalog / error strings translated (ID / EN).
- **Mobile:** Full-width typeahead; dropdown as full-screen sheet.

### Story 10.3.2 [OPEN]
**As a** Doctor,
**I want to** attach ICD-9-CM procedures (with an optional note) to an encounter,
**so that** procedures performed are coded for billing and reporting.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/encounters/:encounter_id/procedures` — auth:
  Doctor (encounter owner) on an open/in-progress encounter; payload: `icd9cm_code`, optional `note`.
- Creates `hc_procedures` `(id, tenant_id, encounter_id, icd9cm_code, note)`; validates `icd9cm_code`
  exists in the tenant's `hc_icd9cm_codes` (422 otherwise); multiple procedures per encounter allowed;
  duplicate `(encounter_id, icd9cm_code)` returns 409.
- `DELETE /.../procedures/:procedure_id` removes an attached procedure (open encounter only).
- Writes blocked once the encounter is `completed`; emits `hc_procedure.attached` / `hc_procedure.removed`
  PHI audit events. The `note` field is free text kept per procedure (not the encrypted clinical-note body).

**Frontend AC:**
- Route: `/clinic/encounters/:encounter_id` (Procedures tab)
- Add-procedure row using the 10.3.1 typeahead + optional note; attached procedures listed with code,
  title, note.
- Duplicate/invalid-code errors inline; list disabled once encounter completed.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id` (Prosedur tab — attach)
- **Portal:** Clinic Portal (clinical)
- **Layout:** Prosedur tab: typeahead + optional note + "Tambah" above a table of attached procedures.
- **Components:**
  - `FlexInput` — ICD-9-CM typeahead (from 10.3.1)
  - `FlexTextarea` — optional per-procedure note
  - `FlexTable` — attached procedures: Kode, Judul, Catatan, Tindakan
  - `FlexButton` — "Tambah Prosedur" (Add Procedure), per-row "Hapus"
  - `FlexAlert` — duplicate / invalid-code / completed-lock errors
- **Key interactions:**
  - Select a code, optionally add a note, "Tambah Prosedur" appends to the table.
  - Duplicate code inline "Prosedur ini sudah ditambahkan"; disabled when encounter completed.
  - Attaching a procedure is an audited clinical act.
- **Empty state:** "Belum ada prosedur. Cari kode ICD-9-CM untuk menambahkan." (No procedures yet. Search
  an ICD-9-CM code to add.)
- **Error state:** Inline duplicate/invalid; API error `FlexAlert` above the table.
- **i18n:** Labels, table headers, note placeholder, empty/error strings translated (ID / EN).
- **Mobile:** Table collapses to card list; note field expands per card; large tap targets.

## Feature 10.4 — Clinical Note Types on the Encounter

### Story 10.4.1 [OPEN]
**As a** Doctor,
**I want to** add a progress or follow-up note to an encounter,
**so that** the clinical narrative beyond the SOAP fields is captured and auditable.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/encounters/:encounter_id/notes` — auth: Doctor;
  payload: `note_type` ∈ {progress, follow_up}, `body`; creates `hc_clinical_notes` `(id, tenant_id,
  encounter_id, note_type, body[PHI-encrypted], author_id)` with `author_id` = caller.
- `body` stored via `EncryptedPHIType`; created/read only through SDK readers with audit; multiple notes
  per encounter allowed; notes are layered onto the existing SOAP encounter (they do not replace SOAP
  fields).
- Notes are append-only clinical entries: after the encounter is `completed`, new notes may still be
  added as addenda (each stamped with `author_id` + timestamp) but existing note bodies are immutable.
- Emits `hc_clinical_note.created` PHI audit event.

**Frontend AC:**
- Route: `/clinic/encounters/:encounter_id` (Notes tab)
- Note composer with a note-type selector (Progress / Follow-up here; nursing/observation in 10.4.2) and
  a rich-text/free-text body; notes listed newest-first with author + timestamp.
- PHI body masked-by-default toggle; all labels in active locale; times in branch timezone.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id` (Catatan / Notes tab)
- **Portal:** Clinic Portal (clinical)
- **Layout:** Catatan tab: composer at top (note-type selector + body), note timeline below (newest
  first); patient strip with mask toggle carried from the encounter page.
- **Components:**
  - `FlexSelect` — note type (Kemajuan / Tindak Lanjut) for this story
  - `FlexTextarea` — note body (PHI)
  - `FlexTimeline` / `FlexList` — notes newest-first: type badge, author, timestamp (branch tz), body
  - `FlexBadge` — note-type badge; PHI mask toggle on note bodies
  - `FlexButton` — "Simpan Catatan" (Save Note)
  - `FlexAlert` — save error / immutable-note notice
- **Key interactions:**
  - Choose note type, write body, "Simpan Catatan" appends to the timeline with author + timestamp.
  - Note bodies are PHI: masked-by-default with a per-note reveal toggle; reveal read via SDK reader,
    audited.
  - After completion, existing notes are read-only; new addenda still allowed.
  - Timestamps shown in branch timezone with tz label (e.g., WIB).
- **Empty state:** "Belum ada catatan klinis untuk kunjungan ini." (No clinical notes for this visit yet.)
- **Error state:** Save failure `FlexAlert` "Gagal menyimpan catatan, coba lagi." (Failed to save note,
  try again.)
- **i18n:** Note-type labels, composer labels, timeline labels, timestamp/tz format, empty/error strings
  translated (ID / EN).
- **Mobile:** Composer collapses to a bottom sheet; timeline as a scrollable card list; reveal/mask per
  card.

### Story 10.4.2 [OPEN]
**As a** Nurse,
**I want to** add nursing and observation notes to an encounter,
**so that** the nursing record is captured alongside the physician's documentation.

**Backend AC:**
- Uses the same `POST /.../encounters/:encounter_id/notes` endpoint with `note_type` ∈ {nursing,
  observation}; auth: Nurse (or Doctor); `author_id` = caller; `body` PHI-encrypted via SDK readers +
  audit.
- Note-type authorization matrix (platform RBAC): nurses may author nursing/observation notes;
  physicians may author any type; the endpoint rejects (403) a note type the caller's role may not author.
- Nursing/observation notes coexist with progress/follow-up notes on the same encounter timeline and are
  filterable by type; emits `hc_clinical_note.created` PHI audit event.

**Frontend AC:**
- Route: `/clinic/encounters/:encounter_id` (Notes tab) — the note-type selector exposes Nursing /
  Observation for authorized roles; a type filter on the timeline.
- Role-appropriate note types only; PHI body masked-by-default; all labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id` (Catatan tab — nursing/observation)
- **Portal:** Clinic Portal (clinical — nursing)
- **Layout:** Same Catatan tab as 10.4.1; the note-type selector shows the types the caller's role may
  author; a type-filter chip row above the timeline.
- **Components:**
  - `FlexSelect` — note type (Keperawatan / Observasi, plus Kemajuan / Tindak Lanjut for physicians)
  - `FlexTextarea` — note body (PHI)
  - `FlexCluster` — timeline type filter chips (Semua / Kemajuan / Keperawatan / Observasi / Tindak
    Lanjut)
  - `FlexTimeline` / `FlexList` — filtered notes newest-first
  - `FlexBadge` — note-type badge (color per type); PHI mask toggle
  - `FlexButton` — "Simpan Catatan"
  - `FlexAlert` — unauthorized-type / save error
- **Key interactions:**
  - The note-type dropdown is filtered to the caller's allowed types (nurse → nursing/observation);
    attempting an unauthorized type is prevented client-side and rejected server-side (403).
  - Type-filter chips filter the timeline by note type.
  - PHI bodies masked-by-default; reveal audited.
- **Empty state:** "Belum ada catatan untuk jenis ini." (No notes of this type yet.)
- **Error state:** Unauthorized-type `FlexAlert` "Peran Anda tidak dapat membuat jenis catatan ini."
  (Your role cannot create this note type.)
- **i18n:** Note-type labels, filter chips, composer labels, empty/error strings translated (ID / EN).
- **Mobile:** Filter chips scroll horizontally; composer as bottom sheet; timeline card list.

### Story 10.4.3 [OPEN]
**As a** Doctor or Nurse,
**I want to** view a consolidated coding & notes summary for the encounter,
**so that** I can review all diagnoses, procedures, and notes in one place before completing the visit.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/encounters/:encounter_id/coding-summary` — auth:
  Doctor / Nurse on the encounter; returns diagnoses (with primary/sequence + resolved titles),
  procedures (with resolved titles + notes), and clinical-note metadata (type, author, timestamp — note
  **bodies fetched separately** via SDK readers on reveal, not in the summary payload).
- Read composed via SDK readers with audit; branch/tenant scoped; no encrypted note bodies in the summary
  response (only metadata) to minimize PHI surface.
- Read emits a `hc_encounter.coding_summary_viewed` PHI audit event.

**Frontend AC:**
- Route: `/clinic/encounters/:encounter_id` (Summary tab)
- Read-only consolidated view: primary diagnosis highlighted, secondary diagnoses in sequence,
  procedures list, and a notes index (type + author + time) with per-note reveal.
- Feeds the "Complete Encounter" confirmation (epic-01) — warns if no primary diagnosis is set.
- All labels in active locale; PHI masked-by-default.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/encounters/:encounter_id` (Ringkasan / Summary tab)
- **Portal:** Clinic Portal (clinical)
- **Layout:** Ringkasan tab: three read-only sections — Diagnosa, Prosedur, Catatan — stacked; a
  completion-readiness banner at top.
- **Components:**
  - `FlexCard` — sections for Diagnosa, Prosedur, Catatan (index)
  - `FlexBadge` — "Primer" highlight on the primary diagnosis; note-type badges; PHI mask toggle
  - `FlexTable` — diagnoses (sequence/code/title/primary), procedures (code/title/note)
  - `FlexList` — notes index (type, author, timestamp) with per-item "Tampilkan" (Reveal)
  - `FlexAlert` — "no primary diagnosis" completion warning
  - `FlexButton` — "Selesaikan Kunjungan" (Complete Encounter) hook (epic-01 flow)
- **Key interactions:**
  - Read-only aggregation of diagnoses, procedures, and note metadata; note bodies revealed on demand via
    SDK reader (audited).
  - A completion-readiness banner warns "Belum ada diagnosa primer" (No primary diagnosis) and can block
    or soft-warn on Complete per epic-01 rules.
  - PHI masked-by-default across the summary.
- **Empty state:** Per section: "Belum ada diagnosa / prosedur / catatan." (No diagnoses / procedures /
  notes yet.)
- **Error state:** Summary load failure `FlexAlert` "Gagal memuat ringkasan encounter." (Failed to load
  encounter summary.)
- **i18n:** Section titles, table headers, badges, completion warning, empty/error strings translated
  (ID / EN); timestamps in branch tz.
- **Mobile:** Sections stack; tables collapse to card lists; notes index as a card list with reveal.

## Story Count: Feature 10.1 (1) + 10.2 (2) + 10.3 (2) + 10.4 (3) = **8 stories**
