---
artifact_id: epic-15-insurance-claims
status: active
version: 1
module: healthcare_insurance
launch_phase: R3
producer: A3 Product Owner
upstream: BACKLOG v3
created: 2026-07-02
---

# Epic 15 — Insurance Eligibility & Claims

**Module:** `healthcare_insurance` (requires `healthcare` base + epic-03 billing; extends the existing BPJS export)
**Launch Phase:** R3
**Depth:** Outline (epic header + one-line story list; detailed AC/UILDC deferred to build time).
**Summary:** Insurance eligibility/coverage checks, authorization, and the claim lifecycle
(generate → submit → track → reject/resubmit), extending the existing BPJS export. **Live national-insurance
API is scope-out (inherited)** — this module structures claims and provides submission adapters; live BPJS/payer
integration lands via epic-17.

---

## Feature 15.1 — Eligibility & Coverage
- Story 15.1.1 — Front desk records a patient's insurance profile (payer, member id, plan, coverage class).
- Story 15.1.2 — Staff checks eligibility/coverage for a visit (adapter; manual/offline fallback when no live payer link).

## Feature 15.2 — Authorization
- Story 15.2.1 — Staff requests and records pre-authorization for a covered service, tracking authorization status/number.

## Feature 15.3 — Claim Lifecycle
- Story 15.3.1 — System generates a claim from a billed encounter (charges + diagnoses/procedures from epic-10) in payer format.
- Story 15.3.2 — Billing staff submits the claim (extends BPJS export; adapter-based submission).
- Story 15.3.3 — Staff tracks claim status (submitted → in-review → paid / rejected) with a status timeline.
- Story 15.3.4 — Staff handles a rejected claim: capture rejection reason, correct, and resubmit.

## Story Count: Feature 15.1 (2) + 15.2 (1) + 15.3 (4) = **7 stories**
