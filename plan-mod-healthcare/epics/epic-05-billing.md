---
id: E5
title: Billing Sub-Module
module: healthcare_billing
status: OPEN
depends_on: [healthcare]
---

# Epic 5 — Billing Sub-Module (`healthcare_billing`)

## Purpose
Enable encounter-to-claim workflow, insurance plan configuration, payment tracking,
and Explanation of Benefits (EOB) management within the healthcare suite.

**Dependency:** requires the `healthcare` base module to be active.

---

## Feature 5.1 — Encounter-to-Claim Workflow

### E5.1.1 — Charge Capture from Encounter [OPEN]
> **As a** billing staff member,
> **I want** to capture charges from a completed encounter,
> **so that** every billable clinical event has a corresponding charge record ready for claim preparation.

**Backend AC:**
- `POST /api/billing/charges` requires `encounter_id`, `charge_codes[]` (CPT-like, free text in v1), `provider_id`, `service_date`.
- `encounter_id` must be in `completed` status; charges against open encounters return 422.
- Charge record status lifecycle: `draft` → `ready` → `claimed` → `paid` | `denied`.
- Charge records are tenant-scoped; `billing` role is required; `clinician` and `viewer` cannot create charges.
- PHI-adjacent: charge records link to patient via encounter; access is audit-logged.

**Frontend AC:**
- Billing queue shows completed encounters with no associated charges highlighted as "Pending Charge Capture".
- Charge entry form pre-fills provider and service date from the encounter; charge codes are free-text in v1 with a "+ Add Code" button for multiple codes.
- After submission, charges appear in "Ready to Claim" status in the billing dashboard.
- Clinicians do not see the billing queue; it is visible only to `billing` and `admin` roles.

---

### E5.1.2 — Claim Preparation and Export [OPEN]
> **As a** billing staff member,
> **I want** to prepare a structured claim record and export it for submission,
> **so that** claim data is complete and formatted for manual or future automated clearinghouse submission.

**Backend AC:**
- `POST /api/billing/claims` aggregates `charge_ids[]` + `patient_id` + `payer_id` into a claim record.
- Claim export (`GET /api/billing/claims/{id}/export`) returns a JSON document matching a defined claim schema (v1 internal schema; not X12 837 in v1).
- Export action is audit-logged.
- Claim status transitions from `ready` → `claimed` on export; subsequent exports are permitted (idempotent) but each export is logged.
- Claims cannot include charges from different patients; mixed-patient claim returns 422.

**Frontend AC:**
- "Prepare Claim" button appears on ready charges; multi-select allows batching charges into one claim.
- Claim detail screen shows patient info (from base module, role-gated), payer, charges, and totals.
- "Export Claim" downloads the JSON file; a toast confirms the download and notes that electronic submission is a manual step in v1.
- Exported claims show a "Claimed" badge; charges within move to `claimed` status in the queue.

---

## Feature 5.2 — Insurance Verification

### E5.2.1 — Insurance Plan Configuration [OPEN]
> **As a** billing admin,
> **I want** to configure insurance payer plans available to patients in my tenant,
> **so that** billing staff can select the correct payer when preparing claims.

**Backend AC:**
- `POST /api/billing/payers` accepts `{ payer_name, payer_id_code, address, contact_phone, plan_types[] }`.
- Payer records are tenant-scoped; not PHI; not encrypted at rest.
- `GET /api/billing/payers` returns active payers; supports name search.
- Deactivating a payer (`PATCH …/payers/{id}` `{"active": false}`) does not affect historical claims referencing it.

**Frontend AC:**
- Payer management is accessible to `admin` and `billing` roles.
- Payer list shows name, payer code, and active status in a table with inline search.
- "Add Payer" form validates payer code format (alphanumeric, 2–10 characters).
- Inactive payers are hidden from the claim preparation payer selector but remain in the payer management list.

---

### E5.2.2 — Patient Insurance Enrollment [OPEN]
> **As a** billing staff member,
> **I want** to record a patient's insurance plan enrollment,
> **so that** claims can reference the correct payer and member information.

**Backend AC:**
- `POST /api/billing/patient-insurance` requires `patient_id`, `payer_id`, `member_id`, `group_id`, `effective_date`, `termination_date` (nullable).
- A patient may have multiple active insurance plans (primary, secondary); `priority` field (`1` = primary) distinguishes them.
- Insurance records are PHI-adjacent; stored encrypted; access is audit-logged.
- `GET /api/billing/patient-insurance?patient_id={id}` returns active plans sorted by priority.

**Frontend AC:**
- Insurance enrollment is accessible from the patient's billing tab; `billing` and `admin` roles only.
- Form supports adding multiple plans with a priority selector (Primary / Secondary / Tertiary).
- Overlapping date ranges for the same payer are flagged with a warning (not a hard block in v1).
- Active insurance plans are shown on the claim preparation screen as a selectable list.

---

## Feature 5.3 — Payment Tracking and EOB

### E5.3.1 — Payment Recording against a Claim [OPEN]
> **As a** billing staff member,
> **I want** to record payments received against a claim,
> **so that** the billing dashboard reflects accurate outstanding balances.

**Backend AC:**
- `POST /api/billing/payments` requires `claim_id`, `amount`, `payment_date`, `payment_source` (`insurance` | `patient`), `reference_number`.
- Payments can be partial; multiple payments per claim are supported.
- After payment(s) are recorded, the claim's `balance_due` is recalculated: `total_charges - sum(payments)`.
- Claim status transitions to `paid` when `balance_due == 0`.
- All payment records are audit-logged.

**Frontend AC:**
- Claim detail screen shows a "Payments" section with a list of recorded payments and the current balance.
- "Record Payment" form defaults payment date to today; payment source and reference number are required.
- Balance due is updated instantly after submission (optimistic update confirmed on API response).
- Claims with `balance_due > 0` and no payment activity for >30 days are flagged in the billing dashboard as "Aging".

---

### E5.3.2 — EOB Management [OPEN]
> **As a** billing staff member,
> **I want** to attach and view Explanation of Benefits documents to a claim,
> **so that** denial reasons and adjustment notes are stored alongside the claim record.

**Backend AC:**
- `POST /api/billing/claims/{id}/eob` accepts a file upload (PDF or structured JSON EOB); stores in tenant-scoped object storage.
- EOB files are not PHI themselves but are linked to PHI-bearing claims; access requires `billing` or `admin` role and is audit-logged.
- `GET /api/billing/claims/{id}/eob` returns a signed URL valid for 15 minutes.
- Each claim may have multiple EOBs (e.g., primary + secondary insurer responses).

**Frontend AC:**
- Claim detail screen has an "EOB Documents" section with a file upload dropzone and a list of previously uploaded EOBs.
- Uploaded EOBs show file name, upload date, and uploader.
- Clicking an EOB opens a preview in a modal (PDF viewer); the signed URL is fetched on click, not pre-loaded.
- "Denied" claims without an attached EOB are flagged in the billing queue with a "Missing EOB" badge.
