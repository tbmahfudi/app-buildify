---
id: E3
title: Laboratory Sub-Module
module: healthcare_lab
status: OPEN
depends_on: [healthcare]
---

# Epic 3 — Laboratory Sub-Module (`healthcare_lab`)

## Purpose
Enable lab test ordering, specimen tracking, structured result entry, reference range
management, and critical value alerting within the healthcare suite.

**Dependency:** requires the `healthcare` base module to be active.

---

## Feature 3.1 — Test Ordering

### E3.1.1 — Lab Order Creation [OPEN]
> **As a** clinician,
> **I want** to create a lab order for a patient linked to an encounter,
> **so that** test requests are traceable to a clinical event and routed for processing.

**Backend AC:**
- `POST /api/lab/orders` requires `patient_id`, `encounter_id`, `test_panel_ids[]`, `priority` (`routine` | `stat`), `ordering_provider_id`.
- `encounter_id` must belong to `patient_id`; mismatch returns 422.
- Order status lifecycle: `ordered` → `specimen_collected` → `processing` → `resulted` | `cancelled`.
- Each order generates an audit log entry; PHI is not stored in the log body.
- `stat` priority orders are flagged in the system; no automatic escalation in v1 (operational escalation is out of scope).

**Frontend AC:**
- Lab order creation is accessible from within an open encounter.
- Test panel selector shows a searchable list of configured panels (admin-managed); multi-select is supported.
- Priority toggle defaults to `routine`; `stat` is visually distinct (red label).
- Order confirmation screen shows the order ID and a status tracker (Ordered → Collected → Processing → Resulted).

---

### E3.1.2 — Specimen Collection Recording [OPEN]
> **As a** lab technician,
> **I want** to record that a specimen has been collected for an outstanding lab order,
> **so that** the order progresses to processing and the collection timestamp is tracked.

**Backend AC:**
- `PATCH /api/lab/orders/{id}/collect` requires `collected_by` (user ID), `collected_at` (ISO8601), optional `specimen_type`.
- Transitioning from any state other than `ordered` returns 422.
- Collection event is audit-logged.
- `GET /api/lab/orders?status=ordered` returns orders awaiting collection for the current tenant.

**Frontend AC:**
- Lab worklist shows all orders in `ordered` status; sortable by order time and priority.
- "Record Collection" action opens a side panel with collected-by (pre-filled from current user) and collected-at (pre-filled to now; editable).
- After submission, the order card moves to the "Processing" column in a Kanban-style board.

---

## Feature 3.2 — Result Management

### E3.2.1 — Structured Result Entry and Reference Ranges [OPEN]
> **As a** lab technician,
> **I want** to enter test results with values and reference ranges, and see automatic flagging for out-of-range results,
> **so that** clinicians receive accurate, context-annotated results.

**Backend AC:**
- `POST /api/lab/results` requires `order_id`, `test_id`, `value`, `unit`, `reference_range_low`, `reference_range_high`.
- System automatically computes `flag`: `"normal"` if value within range, `"low"` or `"high"` if outside, `"critical"` if outside configured critical thresholds.
- Results are PHI-adjacent; stored encrypted; audit-logged on read and write.
- Multiple results per order (one per test in the panel) are accepted; order transitions to `resulted` only when all tests in the panel have results.

**Frontend AC:**
- Result entry form is accessible to lab staff; fields include value, unit (dropdown), and reference range (pre-filled from panel configuration).
- Out-of-range values are highlighted immediately (yellow for high/low, red for critical) as the user types.
- Panel completion progress bar shows `X of Y tests resulted`.
- Resulted orders show a summary badge: "All Normal", "Flags Present", or "Critical Values" with appropriate color coding.

---

### E3.2.2 — Critical Value Alert Dispatch [OPEN]
> **As a** clinician,
> **I want** to receive a notification when a lab result for my patient is flagged as critical,
> **so that** I can act on life-threatening values within the required clinical response window.

**Backend AC:**
- When a result is saved with `flag = "critical"`, the system dispatches a notification to the ordering provider via the platform's notification primitive (in-app + email).
- Notification payload includes: order ID, patient reference ID (not name), test name, critical value — no additional PHI.
- Notification dispatch is recorded in the audit log with the target provider ID.
- Critical thresholds are configured per test panel by `admin` role; default thresholds are pre-populated from the panel template at order creation.

**Frontend AC:**
- In-app critical value notifications appear as a persistent banner (not dismissible until acknowledged) in the clinician's dashboard.
- Acknowledging the alert requires clicking "Acknowledge & View Results"; the acknowledgement is timestamped.
- The patient lab results page highlights critical values with a red badge and shows the time the alert was sent and acknowledged.
- Unacknowledged critical alerts persist across sessions until the ordering clinician acknowledges them.

---

## Feature 3.3 — Lab Panel Configuration

### E3.3.1 — Test Panel Setup by Admin [OPEN]
> **As a** tenant admin,
> **I want** to configure lab test panels with default reference ranges and critical thresholds,
> **so that** lab orders reference validated, consistent test definitions.

**Backend AC:**
- `POST /api/lab/panels` accepts `{ name, tests: [{ test_name, unit, ref_low, ref_high, critical_low, critical_high }] }`.
- Panel names must be unique per tenant; duplicate name returns 409.
- Panels can be deactivated; deactivated panels cannot be ordered but historical results remain readable.
- `GET /api/lab/panels` returns active panels; `?include_inactive=true` returns all.

**Frontend AC:**
- Panel configuration is accessible to `admin` role only.
- Panel creation form allows adding multiple tests inline with a "+ Add Test" button.
- Reference range and critical threshold fields are numeric; `critical_low` must be ≤ `ref_low` and `critical_high` must be ≥ `ref_high` (validated on submit).
- Panels in use (referenced by active orders) cannot be deleted; a tooltip explains why.
