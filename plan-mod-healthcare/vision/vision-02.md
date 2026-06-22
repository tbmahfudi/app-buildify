---
artifact_id: vision-02
type: vision
status: review
producer: A1 Product Manager
upstream: stakeholder-direction-2026-06-21
supersedes: vision-01
created: 2026-06-21
---

# Healthcare Module Suite — Product Vision v2

## Geoffrey Moore Vision Statement

**FOR** health-tech startups and healthcare service providers in Indonesia (with worldwide expansion readiness)
**WHO** need a unified digital platform to manage their clinics and serve patients online,
**THE** App-Buildify Healthcare Module Suite is a two-sided health service platform
**THAT** connects patients with registered clinics, enables multi-location clinic operations, and delivers composable clinical workflows — all from a single platform.
**UNLIKE** generic clinic management systems or fragmented point solutions,
**OUR PRODUCT** gives providers a branded, multi-location-ready clinic portal and gives patients a single place to discover, register with, and receive services from any participating clinic — while the platform handles compliance, data isolation, and billing infrastructure.

---

## Problem

### Provider side
Independent clinics and small clinic chains in Indonesia lack affordable, integrated digital infrastructure. Managing appointments, patient records, prescriptions, and billing across even two or three clinic branches requires either expensive EHR systems designed for hospitals or a patchwork of disconnected SaaS tools. Health-tech startups building for this market must rebuild the same compliance and multi-tenancy plumbing for every client engagement.

### Patient side
Patients have no standard way to find verified clinics, book appointments online, or access their own health records across providers. Each clinic has its own registration process, paper forms, and communication channel. There is no continuity of care data between visits to different providers.

### Platform side
The App-Buildify module system provides multi-tenancy, RBAC, and a composable module architecture — but has no healthcare domain model, no patient-facing public access layer, and no multi-location support within a single tenant.

---

## Target Users

### 1. Clinic Owner / Health Service Provider (Primary B2B)
**Who:** Owner or administrator of a single clinic or a chain of 2–20 clinic branches across Indonesian cities.
**Goal:** Digitize clinic operations — patient registration, appointments, medical records, prescriptions, lab orders, and billing — without hiring a software team or buying an expensive hospital-grade EHR.
**Pain points:**
- Managing separate systems per branch with no unified reporting
- Staff manually re-entering patient data from paper forms
- No online booking, so phones are overwhelmed with appointment calls
- Cannot verify patient identity or history when patients visit a different branch

### 2. Patient / Public User (Primary B2C)
**Who:** Indonesian residents seeking outpatient health services from registered clinics on the platform.
**Goal:** Find nearby verified clinics, register as a patient once, book appointments, and access their own health records and prescriptions online.
**Pain points:**
- No central way to discover which clinics are available and accepting new patients
- Must re-register with each clinic separately with the same personal data
- No access to past visit summaries, lab results, or prescriptions after leaving the clinic
- Cannot easily switch providers while keeping their health history

### 3. Health-Tech Startup / System Integrator (B2B builder)
**Who:** Indonesian health-tech startups building clinic management products for their own customers on top of App-Buildify.
**Goal:** Rapidly deploy a compliant, multi-tenant clinic platform for their portfolio of clinic clients without building PHI infrastructure from scratch.
**Pain points:**
- Building multi-tenancy, PHI isolation, and audit logging takes 6–12 months before any clinical feature ships
- Compliance requirements (Indonesia's PP No. 71/2019 on electronic health records, PDPA alignment) are complex and evolving
- Each client clinic needs custom branding and branch configuration

### 4. Clinical Staff (End user within provider)
**Who:** Doctors, nurses, pharmacists, lab technicians working at a registered clinic.
**Goal:** Use a simple, fast digital workflow for patient check-in, encounter notes, prescriptions, and results — without IT overhead.
**Pain points:**
- Paper-based workflows are slow and create data loss risk
- Switching between disconnected apps during a consultation breaks focus
- No visibility into what happened at a patient's previous visit to another branch

---

## Success Metrics (SMART)

| # | Metric | Target | Timeframe |
|---|--------|--------|-----------|
| 1 | Clinic tenants onboarded (base module active) | ≥ 50 clinics | 6 months post-GA |
| 2 | Registered patients (public users) | ≥ 5,000 patients | 6 months post-GA |
| 3 | Sub-module attach rate per clinic tenant | ≥ 70% activate ≥ 1 sub-module | 90 days after base activation |
| 4 | Multi-location clinic tenants (≥ 2 branches) | ≥ 20% of clinic tenants | 12 months post-GA |
| 5 | Clinic onboarding time (base module active → first appointment booked) | ≤ 1 business day | At GA |
| 6 | Platform ARR from healthcare module family | ≥ IDR 1.8B (~USD 120K) | 12 months post-GA |
| 7 | Patient-reported satisfaction (NPS from post-visit survey) | ≥ 40 | 12 months post-GA |

---

## Scope IN

### Platform layer (base `healthcare` module — required)
- Public patient registration: patients create a platform account and a universal health profile
- Clinic discovery: patients search registered clinics by location, specialty, and availability
- Multi-location clinic support: a single clinic tenant can manage multiple branches, each with its own staff, schedule, and inventory — unified under one tenant account
- PHI data models: Patient, Encounter, Provider, Branch, Appointment — shared across all sub-modules
- Compliance baseline: Indonesia PP 71/2019-aligned audit trail, data residency in Indonesia (primary), PDPA-aligned consent management
- Clinic RBAC: roles — Clinic Owner, Branch Manager, Doctor, Nurse, Pharmacist, Lab Tech, Billing Staff, Patient (read-own-only)
- BAA/data processing agreement gate: clinic must accept DPA before activating any sub-module

### Optional sub-modules (each requires base)
- `healthcare_scheduling` — online appointment booking, provider calendars per branch, patient reminders (WhatsApp/SMS, PHI-safe), waitlist
- `healthcare_pharmacy` — prescription management, medication catalog per branch, dispensing workflow, drug interaction adapter
- `healthcare_lab` — laboratory test ordering, specimen tracking, result management, critical value alerts
- `healthcare_billing` — encounter-to-invoice workflow, insurance claim export (BPJS Kesehatan format), payment tracking
- `healthcare_telemedicine` — video consultation sessions, SOAP notes, consent forms, session recording policy

### Architecture
- Two access modes on the same platform: authenticated clinic staff portal + authenticated patient portal (public-facing)
- Worldwide-ready: data residency and locale are configurable per tenant; Indonesian market is the default and launch target
- Multilingual (i18n-first): all UI, notifications, email templates, and printed documents are locale-aware from day one. Launch locales: Bahasa Indonesia (default) + English. Additional locales (Arabic, Mandarin, etc.) are addable via translation files — no code changes required. Each clinic tenant independently selects its preferred language; patients choose their own locale in their profile.

---

## Scope OUT (Non-Goals)

1. **Full EHR / Hospital Information System replacement** — this is an outpatient clinic platform; inpatient, ICU, OR scheduling, and bed management are out of scope.
2. **Direct BPJS Kesehatan API integration** — billing module exports in BPJS-compatible format; live API claim submission via clearinghouse is out of scope for v1.
3. **AI-powered clinical decision support (CDS)** — no diagnostic AI, drug recommendation engines, or predictive analytics in v1.
4. **Native mobile apps** — the patient and clinic portals are responsive web; no iOS/Android native apps in v1.
5. **Drug database bundling** — pharmacy module provides the data model and adapter interface; a licensed drug database (e.g. MIMS Indonesia) is a third-party integration, not bundled.
6. **Cross-platform patient identity federation** — patient records are scoped to this platform; integration with national health identity systems (IHS / SATUSEHAT) is a future phase.

---

## Guardrails

1. **PHI never crosses tenant boundaries** — patient data is always scoped to the clinic tenant that collected it; cross-clinic patient lookup requires explicit patient consent and is a future feature.
2. **Base module is the hard gate** — no sub-module can be activated for a tenant without the base `healthcare` module active; this is enforced server-side, not UI-only.
3. **Compliance defaults are restrictive** — audit logging, consent management, and data retention policies are on by default and require deliberate opt-out (not opt-in).
4. **No real PHI in development or staging environments** — synthetic patient data tooling must exist before any clinical feature ships.
5. **Patient portal is public-facing but authenticated** — patients self-register; no anonymous access to health data.
6. **Indonesia-first defaults** — Bahasa Indonesia and English ship at launch; locale is tenant- and user-configurable. Timezone (WIB/WITA/WIT) and BPJS billing format are Indonesian defaults; both are overridable for worldwide deployments.
7. **i18n-first, not i18n-later** — no hardcoded UI strings anywhere in the module codebase; all copy goes through the translation layer from the first line of code. — language (Bahasa Indonesia), locale, timezone (WIB/WITA/WIT), and BPJS billing format are the defaults; English and other locales are configurable.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Indonesia PDPA / PP 71 scope is broader than anticipated | Medium | High | Engage local legal counsel before architecture is locked; build data residency and consent as first-class module features |
| Patient adoption is slow without clinic network effects | High | High | Go-to-market via health-tech startup partners (B2B2C) rather than direct-to-patient; startups bring their existing clinic portfolios |
| Multi-location data isolation complexity underestimated | Medium | High | B1 must produce a branch-isolation ADR before any sprint; `branch_id` must be a first-class field alongside `tenant_id` |
| BPJS billing format changes | Medium | Medium | Billing export is file-based (not live API); a versioned adapter pattern isolates format changes |
| WhatsApp/SMS reminder PHI leakage | High | High | Reminder templates are system-locked; no PHI (patient name, diagnosis, provider) in any outbound message body |
| Telemedicine regulatory requirements (Permenkes No. 20/2019) | Medium | High | Telemedicine sub-module ships last; legal review gates its GA separately from the rest of the suite |
