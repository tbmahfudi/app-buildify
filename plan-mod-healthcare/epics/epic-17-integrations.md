---
artifact_id: epic-17-integrations
status: active
version: 1
module: healthcare_integration
launch_phase: R3+
producer: A3 Product Owner
upstream: BACKLOG v3
created: 2026-07-02
---

# Epic 17 — External Integrations (pay / SMS / WA / Email / LIS / PACS / govt)

**Module:** `healthcare_integration` (requires `healthcare` base; provides adapters consumed by other epics)
**Launch Phase:** R3+
**Depth:** Outline (epic header + one-line story list; detailed AC/UILDC deferred to build time).
**Summary:** External-system adapters: payment gateway; SMS/WhatsApp/Email gateways (wire the platform
notification transport used by epic-13 to real providers); LIS (lab), PACS (imaging); and national adapters
(national-insurance/BPJS, ePrescription, national reporting/SATUSEHAT). **Live national integrations and PACS
viewer bundling remain scope-out (Scope-Out #12 and inherited items)** — this epic delivers the adapter
interfaces and per-tenant configuration, not bundled third-party services.

---

## Feature 17.1 — Payment Gateway
- Story 17.1.1 — Configure a payment-gateway adapter per tenant (keys, environment) for billing/portal payments.
- Story 17.1.2 — Process a patient payment and reconcile gateway callbacks against invoices (epic-03).

## Feature 17.2 — Messaging Gateways
- Story 17.2.1 — Wire the SMS gateway to the platform notification transport (epic-13) per tenant.
- Story 17.2.2 — Wire the WhatsApp Business API (approved templates only — Scope-Out #10) per tenant.
- Story 17.2.3 — Wire the Email gateway (SMTP/API) to the platform transport per tenant.

## Feature 17.3 — Clinical System Integrations
- Story 17.3.1 — LIS adapter: push lab orders / pull results into epic-05.
- Story 17.3.2 — PACS adapter: attach imaging study references for epic-14 (no DICOM viewer bundled — Scope-Out #12).

## Feature 17.4 — National / Regulatory Adapters
- Story 17.4.1 — National-insurance (BPJS) adapter: eligibility/claim submission for epic-15.
- Story 17.4.2 — ePrescription adapter for regulated electronic prescribing.
- Story 17.4.3 — National reporting (SATUSEHAT-style) adapter for mandated data submission (live integration scope-out; adapter + mapping only).

## Story Count: Feature 17.1 (2) + 17.2 (3) + 17.3 (2) + 17.4 (3) = **10 stories**
