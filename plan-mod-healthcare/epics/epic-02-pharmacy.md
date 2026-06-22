---
id: E2
title: Pharmacy Sub-Module
module: healthcare_pharmacy
status: OPEN
depends_on: [healthcare]
---

# Epic 2 — Pharmacy Sub-Module (`healthcare_pharmacy`)

## Purpose
Enable prescription management, medication catalog administration, dispensing workflow,
and drug-interaction warning surfaces within the healthcare suite.

**Dependency:** requires the `healthcare` base module to be active.

---

## Feature 2.1 — Medication Catalog

### E2.1.1 — Medication Catalog Management [OPEN]
> **As a** pharmacy admin,
> **I want** to maintain a searchable medication catalog with dosage forms and strengths,
> **so that** prescribers can select from validated, tenant-approved medications.

**Backend AC:**
- `POST /api/pharmacy/medications` creates a catalog entry: `{ name, generic_name, ndc_code, dosage_forms[], strengths[], active }`.
- NDC code format is validated (10 or 11 digits); invalid format returns 422.
- `GET /api/pharmacy/medications?q={term}` supports prefix search on name and generic name.
- Deactivating a medication (`PATCH …/medications/{id}` `{"active": false}`) does not invalidate historical prescriptions referencing it.
- Catalog entries are tenant-scoped; tenants cannot see other tenants' catalogs.

**Frontend AC:**
- Medication catalog screen is accessible to `admin` and `clinician` roles; editing is `admin`-only.
- Search box with typeahead filters the catalog list in real time (debounced, ≥2 characters).
- "Add Medication" form shows NDC format hint and validates on blur.
- Inactive medications are shown in a separate "Inactive" tab with a "Reactivate" action.

---

### E2.1.2 — Drug Interaction Warning Surface [OPEN]
> **As a** clinician,
> **I want** to see a flag when a new prescription conflicts with a patient's existing active prescriptions,
> **so that** I can make an informed prescribing decision before finalizing the order.

**Backend AC:**
- `POST /api/pharmacy/interaction-check` accepts `{ patient_id, ndc_code }` and returns a list of potential interactions from the configured adapter endpoint (or an empty list if no adapter is configured).
- If the adapter is unavailable, the endpoint returns a 200 with `{ "adapter_status": "unavailable", "interactions": [] }` — not a 5xx, to avoid blocking prescription workflow.
- Interaction check results are not stored as PHI; they are transient responses.
- The adapter endpoint URL is configured per tenant by `admin` role; no default vendor is bundled.

**Frontend AC:**
- During prescription creation, after selecting a medication, an interaction check fires automatically.
- If interactions are returned, a yellow warning banner lists each interaction with severity label.
- The prescriber can proceed despite warnings (override), which requires a free-text override reason; the reason is stored on the prescription record.
- If the adapter is unavailable, a gray "Interaction check unavailable" notice is shown (not a blocking error).

---

## Feature 2.2 — Prescription Management

### E2.2.1 — Prescription Creation [OPEN]
> **As a** clinician,
> **I want** to create a prescription linked to a patient and encounter,
> **so that** medication orders are traceable to a clinical event.

**Backend AC:**
- `POST /api/pharmacy/prescriptions` requires `patient_id`, `encounter_id`, `medication_id`, `dose`, `frequency`, `quantity`, `refills`, `prescriber_id`.
- `encounter_id` must belong to the same `patient_id`; mismatch returns 422.
- Prescription status lifecycle: `draft` → `active` → `dispensed` | `cancelled` | `expired`.
- Prescriptions are PHI-adjacent (linked to patient); creation triggers an audit log entry.
- `prescriber_id` must match a `provider` record with `clinician` role in the same tenant.

**Frontend AC:**
- Prescription creation is launched from within an open encounter; patient and encounter context are pre-filled.
- Medication selector uses the catalog search component; free-text entry is not permitted.
- Dose, frequency, and quantity fields have numeric guards; unit selectors (mg, mL, etc.) are dropdowns.
- Submitted prescriptions show in a "Pending Dispensing" queue visible to pharmacy staff.

---

### E2.2.2 — Prescription Cancellation and Refill Tracking [OPEN]
> **As a** clinician or pharmacy admin,
> **I want** to cancel an active prescription and track remaining refills,
> **so that** medication orders remain accurate and refill limits are enforced.

**Backend AC:**
- `PATCH /api/pharmacy/prescriptions/{id}/cancel` requires a `reason`; transitions status to `cancelled`; audit-logged.
- Cancellation is blocked if the prescription is already in `dispensed` or `expired` state; returns 422.
- `refills_remaining` counter is decremented by 1 on each dispense event; reaching 0 transitions status to `expired` after last dispense.
- `GET /api/pharmacy/prescriptions/{id}` exposes `refills_remaining` and `dispense_history[]`.

**Frontend AC:**
- Active prescription cards show a "Cancel" button (clinician/admin only) and a refill badge (`X refills remaining`).
- Cancel action opens a modal with a required reason text area and a confirmation step.
- Refill history is expandable per prescription showing dispense date and dispensing user.
- Expired prescriptions are visually differentiated (gray badge "Expired") and sorted to the bottom of the list.

---

## Feature 2.3 — Dispensing Workflow

### E2.3.1 — Medication Dispensing and Inventory Acknowledgement [OPEN]
> **As a** pharmacy staff member,
> **I want** to record a dispense event against an active prescription,
> **so that** the medication fulfillment is tracked and refill count is accurately maintained.

**Backend AC:**
- `POST /api/pharmacy/dispenses` requires `prescription_id`, `dispensed_quantity`, `dispensed_by` (user ID with pharmacy-staff permission).
- Dispensing against a `cancelled`, `expired`, or `draft` prescription returns 422.
- Each dispense event decrements `refills_remaining` and stores: `{ dispense_id, prescription_id, dispensed_quantity, dispensed_at, dispensed_by }`.
- Dispense events are audit-logged (PHI-adjacent: patient identity not stored in log, only resource ID).

**Frontend AC:**
- Dispensing queue shows all prescriptions in `active` status for the current tenant.
- Pharmacy staff selects a prescription and enters the dispensed quantity (pre-filled from prescribed quantity; editable for partial dispenses).
- Successful dispense shows a confirmation with dispense ID and updated refill count.
- Prescriptions with `refills_remaining = 0` after dispense are automatically removed from the active queue.
