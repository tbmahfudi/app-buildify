---
artifact_id: adr-hc-007
type: adr
module: healthcare_emr
status: proposed
producer: B1 Backend Architect
upstream: [BACKLOG.md (v3), adr-hc-001, adr-hc-002, schema-hc-01, epic-10-emr-clinical-coding]
created: 2026-07-02
---

# ADR-HC-007 — Clinical Coding (ICD-10 / ICD-9-CM) & Clinical Notes

## Status

proposed

## Context

BACKLOG v3 extends the EMR domain (module `healthcare_emr`, epic-10, MVP) with **diagnosis coding
(ICD-10)**, **procedure coding (ICD-9-CM)**, and structured **clinical notes** attached to an
encounter. `hc_encounters` (schema-hc-01) already holds the SOAP narrative (PHI-encrypted); it does
not hold coded, queryable diagnoses/procedures or note-type-tagged notes.

Design questions:

1. **Code catalogs** — where do the ICD-10 (diagnosis) and ICD-9-CM (procedure) code *masters* live:
   the platform no-code master-data engine, or dedicated healthcare adapter tables?
2. **Encounter coding** — how are coded diagnoses/procedures and typed clinical notes linked to an
   encounter, and which columns are PHI?
3. **PHI access** — how is coded/clinical data read across modules and audited?

**Constraints:**
- BACKLOG Scope-Out #13: the **licensed ICD dataset is per-tenant procurement** — "Codes loaded as
  platform master-data per tenant; module ships the schema + adapter, not the licensed dataset."
- BACKLOG Reuse Register: Master Data is a **reuse** capability (`backend/app/routers/data_model.py`,
  `lookups.py`, `/api/v1/dynamic_data`); "ICD/drug/test/insurer catalogs → epic-10 (ICD) + adapters."
- ADR-HC-002: PHI reads go through healthcare SDK readers with a mandatory audit entry.
- ADR-HC-001: encounter-linked tables are branch-scoped (`tenant_id` + `branch_id` + RLS `§D4`).

## Decision

### D1 — Code catalogs: dedicated healthcare adapter tables `hc_icd10_codes` / `hc_icd9cm_codes`

The ICD-10 and ICD-9-CM code masters are stored in **dedicated healthcare adapter tables**
`hc_icd10_codes` and `hc_icd9cm_codes` (canonical names per BACKLOG), **not** as generic platform
no-code master-data entities.

```
hc_icd10_codes  (id, tenant_id, code, description, description_id, chapter, category, is_billable, is_active, ...)
hc_icd9cm_codes (id, tenant_id, code, description, description_id, category, is_active, ...)
```

- **Per-tenant, adapter-loaded.** Rows are loaded per tenant by the healthcare ICD adapter from the
  tenant's *own* licensed dataset (Scope-Out #13). `tenant_id` is present on every row so one tenant's
  licensed edition/version never leaks to another. The tables are **tenant-scoped, not
  branch-scoped** — code catalogs are clinic-wide reference data, so `branch_id` is intentionally
  absent (same pattern as `hc_patients` being tenant-wide in ADR-HC-001 §D3).
- **The module ships the schema + adapter, not the data.** The Alembic migration and loader ship
  empty; each tenant populates its edition via the adapter. No ICD content is bundled (Scope-Out #13).

**Why dedicated tables rather than platform no-code entities:**

| Consideration | Verdict |
|---|---|
| Volume & query shape | ICD-10 has ~70k+ codes; diagnosis pickers need fast prefix/description search and hierarchy (chapter/category) traversal. A purpose-built table with proper indexes (and optional trigram/full-text) outperforms generic EAV-style no-code storage. |
| Referential integrity | `hc_diagnoses.icd10_code` / `hc_procedures.icd9cm_code` link to a stable, typed code column; a dedicated table gives a clean FK/validation target. |
| Licensing isolation | Per-tenant `tenant_id` scoping of the licensed dataset is explicit and enforceable at the table; no risk of a shared platform lookup mixing tenants' licensed editions. |
| Versioning | ICD editions change; a dedicated table can carry edition/version metadata and `is_active` without contorting the no-code schema. |

The platform master-data engine remains the reuse choice for **lower-volume** healthcare lookups
(insurer lists, referral sources, etc.); ICD is the exception that warrants a dedicated adapter table,
which BACKLOG explicitly allows ("`hc_icd10_codes`, `hc_icd9cm_codes` (adapter-loaded per tenant) OR
platform no-code entities — ADR-HC-007 decides and documents the choice").

### D2 — Encounter link tables: `hc_diagnoses`, `hc_procedures`, `hc_clinical_notes`

Three new branch-scoped tables attach coded/clinical data to an encounter (canonical names/columns per
BACKLOG):

```
hc_diagnoses (
  id, tenant_id, branch_id, encounter_id → hc_encounters.id,
  icd10_code,            # references hc_icd10_codes.code within the same tenant
  is_primary, sequence,
  created_at
)

hc_procedures (
  id, tenant_id, branch_id, encounter_id → hc_encounters.id,
  icd9cm_code,           # references hc_icd9cm_codes.code within the same tenant
  note,                  # short procedure note; not free-text PHI narrative
  created_at
)

hc_clinical_notes (
  id, tenant_id, branch_id, encounter_id → hc_encounters.id,
  note_type ∈ {progress, nursing, observation, follow_up},
  body [PHI — EncryptedPHIType],
  author_id,             # user_id of the authoring clinician
  created_at, updated_at
)
```

- **`hc_diagnoses`.** `is_primary` marks the principal diagnosis; a partial unique index enforces at
  most one primary per encounter (`WHERE is_primary`). `sequence` orders secondary diagnoses. The
  `icd10_code` is validated against `hc_icd10_codes` for the same `tenant_id` at write time.
- **`hc_procedures`.** `icd9cm_code` validated against `hc_icd9cm_codes` for the tenant. `note` is a
  short structured note (e.g. laterality, count) — **not** a free-text clinical narrative, so it is
  not PHI-encrypted; any narrative belongs in `hc_clinical_notes` or the encounter SOAP fields.
- **`hc_clinical_notes`.** `body` is a free-text clinical narrative and is **PHI**, stored via
  `EncryptedPHIType` (AES-256 at rest, ADR-HC-002 / schema-hc-01 convention), like the `hc_encounters`
  SOAP columns. `note_type` is constrained to the canonical set. `author_id` records the clinician.
- **Immutability.** Consistent with `hc_encounters` (schema-hc-01), diagnoses/procedures/notes for a
  `completed` encounter are not edited in place; corrections append a new note or a superseding
  diagnosis row (amendment pattern), never mutate the original.

### D3 — PHI access via SDK readers + audit (ADR-HC-002)

- The only **PHI-encrypted** column introduced here is `hc_clinical_notes.body`. Coded diagnoses and
  procedures are PHI-by-association (they belong to an encounter/patient) but are not free-text
  narratives.
- Cross-module reads of clinical notes and coded data go through **healthcare SDK readers**
  (`modules/healthcare/sdk/`), extending the ADR-HC-002 pattern (`encounter_reader.py`). A
  `get_clinical_notes(...)` / `get_encounter_coding(...)` SDK function writes a `phi.read` audit
  entry to `hc_audit_log` (`resource_type = 'clinical_note' | 'diagnosis' | 'procedure'`,
  `source_module` = caller) **before** returning data. Sub-modules never import
  `modules.healthcare.backend.*` directly (ADR-HC-002 D1 / ADR-006 lint gate).
- **Reporting caveat (forward-ref ADR-HC-008):** `v_hc_disease_stats` aggregates over `hc_diagnoses`
  by `icd10_code` — it exposes **codes and counts, never `hc_clinical_notes.body` or any patient
  identifier** — so the disease-stats view is PHI-safe by construction.

### D4 — Isolation conformance

`hc_diagnoses`, `hc_procedures`, `hc_clinical_notes` are `__tenant_scoped__` + `__branch_scoped__`
(they inherit the encounter's branch), enforced by `BranchScopeListener` + the ADR-HC-001 `§D4` RLS
policy, and accessed via `healthcare_branch_session`. `hc_icd10_codes` / `hc_icd9cm_codes` are
tenant-scoped reference tables (RLS: `tenant_id = current_setting('app.tenant_id')`).

## Consequences

### Positive
- **Fast, correct coding UX.** Dedicated ICD tables give indexed prefix/description search and a clean
  FK/validation target for `hc_diagnoses`/`hc_procedures`.
- **Licensing-safe.** Per-tenant ICD rows honor Scope-Out #13 — the module ships schema + adapter,
  each tenant loads its own licensed edition; no cross-tenant leakage.
- **Minimal new PHI surface.** Only `hc_clinical_notes.body` is encrypted; coded data stays queryable
  for reporting while remaining RLS-protected.
- **Audit-consistent.** All cross-module clinical reads flow through SDK readers with mandatory audit,
  unchanged from ADR-HC-002.

### Negative
- **Adapter/loader to maintain** per ICD edition and per tenant. Mitigation: the loader is a thin
  adapter; catalog refresh is an operational task, not a schema change.
- **Two coding standards** (ICD-10 for Dx, ICD-9-CM for procedures) means two catalog tables and two
  validators. Mitigation: they share structure and a common adapter interface; documented here.
- **Code validation is app-enforced** (cross-`tenant_id` code existence) rather than a hard FK, to
  avoid coupling encounter writes to catalog-load ordering. Mitigation: covered by a write-path check
  and integration test.

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Store ICD codes as platform no-code master-data entities | Generic EAV storage is slow for ~70k-row prefix/description search and hierarchy traversal; weaker per-tenant licensing isolation; awkward FK/validation target for `hc_diagnoses`/`hc_procedures`. |
| Bundle a default ICD dataset in the module | Violates Scope-Out #13 (licensed data is per-tenant procurement). Module ships schema + adapter only. |
| Put diagnoses/procedures as JSON on `hc_encounters` | Not queryable for `v_hc_disease_stats`; no `is_primary`/`sequence` integrity; blocks per-code reporting. Dedicated link tables chosen. |
| Encrypt `hc_procedures.note` as PHI | The `note` is a short structured qualifier, not a patient narrative; encrypting it would block procedure-level reporting with no PHI benefit. Narrative goes to `hc_clinical_notes.body` (encrypted). |

## Reference Map

| File | Relevance |
|------|-----------|
| `backend/app/routers/data_model.py`, `lookups.py` | Platform no-code master-data engine (reused for non-ICD lookups; not for ICD) |
| `modules/healthcare/backend/models.py` | `hc_encounters` (SOAP PHI) extended by coded diagnoses/procedures/notes |
| `modules/healthcare/sdk/phi_crypto.py` (`EncryptedPHIType`) | PHI encryption for `hc_clinical_notes.body` |
| `plan-mod-healthcare/architecture/adr-hc-002-cross-module-phi-data-sharing.md` | SDK reader + mandatory audit pattern for clinical reads |
| `plan-mod-healthcare/architecture/adr-hc-001-branch-isolation-strategy.md` | Branch isolation + RLS `§D4` for encounter-linked tables |
| `plan-mod-healthcare/architecture/adr-hc-008-reporting-integration.md` | `v_hc_disease_stats` aggregates `hc_diagnoses` PHI-safely |
| `plan-mod-healthcare/architecture/schema-hc-02.md` | DDL for ICD catalogs + coding link tables |
| `plan-mod-healthcare/BACKLOG.md` | v3 Canonical names, Scope-Out #13 |
