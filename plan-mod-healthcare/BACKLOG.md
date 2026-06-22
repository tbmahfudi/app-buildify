---
artifact_id: BACKLOG
version: 2
status: active
producer: A3 Product Owner
upstream: vision-02, research-02
supersedes: BACKLOG v1
created: 2026-06-21
---

# Healthcare Module Suite — Product Backlog v2

**Produced by:** A3 Product Owner
**Date:** 2026-06-21
**Upstream:** `plan-mod-healthcare/vision/vision-02.md`, `plan-mod-healthcare/research/research-02.md`
**Supersedes:** BACKLOG.md v1 (written against vision-01)

---

## Epic Summary Table

| Epic | Title | Module | Launch Phase | Stories | Status |
|------|-------|--------|-------------|---------|--------|
| epic-01-base-healthcare | Base Healthcare Module | `healthcare` | GA | 14 | OPEN |
| epic-02-scheduling | Scheduling Module | `healthcare_scheduling` | GA (with base) | 8 | OPEN |
| epic-03-billing | Billing Module | `healthcare_billing` | Month 2–3 post-GA | 7 | OPEN |
| epic-04-pharmacy | Pharmacy Module | `healthcare_pharmacy` | Month 3–4 post-GA | 6 | OPEN |
| epic-05-laboratory | Laboratory Module | `healthcare_lab` | Month 4–5 post-GA | 6 | OPEN |
| epic-06-telemedicine | Telemedicine Module | `healthcare_telemedicine` | Month 6+ (legal gate) | 4 | OPEN |
| epic-07-patient-portal | Patient Portal | cross-module | GA + progressive | 6 | OPEN |
| **TOTAL** | | | | **51** | |

---

## Sub-Module Launch Sequence

```
GA          ──► healthcare (base) + healthcare_scheduling + patient portal (base features)
Month 2–3   ──► healthcare_billing
Month 3–4   ──► healthcare_pharmacy
Month 4–5   ──► healthcare_lab
Month 6+    ──► healthcare_telemedicine  [separate legal gate — Permenkes 20/2019]
```

---

## Cross-Epic Dependency Map

```
epic-01-base-healthcare (required by ALL)
  │
  ├─► epic-02-scheduling       (GA — required by epic-07 patient appointments)
  │       └─► epic-06-telemedicine  (requires scheduling for session appointments)
  │
  ├─► epic-03-billing          (requires base; encounter-to-invoice depends on encounter from base)
  │
  ├─► epic-04-pharmacy         (requires base; prescription links to encounter)
  │
  ├─► epic-05-laboratory       (requires base; lab orders link to encounter; follows pharmacy patterns)
  │
  └─► epic-07-patient-portal   (cross-module; requires base at GA; enriched by each sub-module)
```

**Key dependency notes:**
- **epic-07** (Patient Portal) cannot show lab results without epic-05; cannot show prescriptions without epic-04; cannot show appointments without epic-02. The portal degrades gracefully — sections hidden until their sub-module is active.
- **epic-06** (Telemedicine) requires `healthcare_scheduling` active because sessions are tied to scheduled appointments.
- **epic-03** (Billing) invoice line items are enriched by pharmacy (dispensed medications) and lab (test charges) if those modules are active — billing must handle partial line items when sub-modules are absent.
- **No sub-module can be activated without epic-01 base active** — enforced server-side.

---

## Scope-Out Register

The following items are explicitly out of scope for this release family. Do not create stories for these items; if raised in sprint planning, refer to this register.

| # | Scope-Out Item | Rationale | Revisit Phase |
|---|---------------|-----------|---------------|
| 1 | **Full EHR / Hospital Information System** | Inpatient, ICU, OR scheduling, bed management — wrong segment (outpatient only) | Not planned |
| 2 | **SATUSEHAT / IHS live API integration** | National health identity federation; complex regulatory + technical dependency | v2 or later |
| 3 | **Live BPJS Kesehatan API claim submission** | File export only in v1; live clearinghouse API requires separate certification | v2 |
| 4 | **AI-powered Clinical Decision Support (CDS)** | No diagnostic AI, drug recommendation engines, or predictive analytics | v2 or later |
| 5 | **Native mobile apps (iOS / Android)** | Responsive web only; Android-first mobile web via patient portal | v2 |
| 6 | **Drug database bundling** | Licensed drug DB (MIMS Indonesia or equivalent) is a third-party procurement item; module provides adapter interface only | Per tenant procurement |
| 7 | **Cross-platform patient identity federation** | Patient records are scoped to this platform; cross-provider sharing requires patient consent + future architecture | v2 |
| 8 | **Inpatient / ward management** | Out of scope — outpatient clinic platform only | Not planned |
| 9 | **Direct P2KB / SIP license verification** | Doctor license check is manual workflow in v1; automated P2KB API is future | v2 |
| 10 | **WhatsApp Business API for free-form PHI** | Notification bodies are system-locked; no clinic-customizable PHI fields in outbound messages — regulatory constraint (Permenkes), not a feature gap | Regulatory constraint — no revisit |

---

## Pre-Conditions (from research-02 — must be resolved before B1 starts architecture)

1. **Legal review of PP 71/2019 and UU PDP No. 27/2022** — Jakarta-based health law firm; compliance scope document required as input to B1 ADR.
2. **Branch Isolation ADR** — B1 must produce and get approval for how `branch_id` is enforced at DB row-level security, API middleware, and ORM layer before any data model decisions.

---

## Hand-off Notice

**From:** A3 Product Owner
**To:** B1 (Backend Architect), B2 (Backend Developer), B3 (Frontend Developer)
**Date:** 2026-06-21
**Status:** Backlog v2 complete — ready for architecture and sprint planning

**Priority surfaces for B1 architecture (in order):**
1. Branch isolation ADR (`tenant_id` + `branch_id` row-level security) — pre-condition for all work
2. PHI data model schema (Patient, Encounter, Branch, Provider) — base of all sub-modules
3. Audit log infrastructure — append-only, immutable, PP 71/2019-aligned
4. Two-sided auth model — clinic staff portal + patient portal (separate auth flows, shared identity layer)
5. i18n infrastructure — translation key system, locale resolution order (user > tenant > platform default)

**Priority surfaces for B3 frontend:**
1. Patient self-registration and clinic discovery — mobile-first, Android mid-range, Lighthouse ≥ 80
2. Clinic onboarding wizard — non-technical clinic owner, ≤ 1 business day to live
3. i18n wiring — zero hardcoded strings; `id-ID` and `en-US` at launch; no locale requires code changes

**Artifacts produced:**
- `plan-mod-healthcare/epics/epic-01-base-healthcare.md` (v2, 14 stories)
- `plan-mod-healthcare/epics/epic-02-scheduling.md` (v2, 8 stories)
- `plan-mod-healthcare/epics/epic-03-billing.md` (v2, 7 stories)
- `plan-mod-healthcare/epics/epic-04-pharmacy.md` (v2, 6 stories)
- `plan-mod-healthcare/epics/epic-05-laboratory.md` (v2, 6 stories)
- `plan-mod-healthcare/epics/epic-06-telemedicine.md` (v2, 4 stories)
- `plan-mod-healthcare/epics/epic-07-patient-portal.md` (v2, 6 stories)
- `plan-mod-healthcare/BACKLOG.md` (v2)

**Old epics superseded:** epic-01 through epic-06 (vision-01 era) marked `status: superseded`.
