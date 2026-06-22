---
type: research
status: review
upstream: vision-02
supersedes: research-01
producer: A2 Business Analyst
created: 2026-06-21
---

# Research Brief v2 — Healthcare Module Suite

**Produced by:** A2 Business Analyst
**Date:** 2026-06-21
**Upstream vision:** `plan-mod-healthcare/vision/vision-02.md`
**Supersedes:** `plan-mod-healthcare/research/research-01.md`

---

## Executive Summary

Vision-02 reframes the Healthcare Module Suite from a single-sided clinic management tool into a
**two-sided health service platform** with the Indonesian market as the primary launch target.
The shift has three structural implications:

1. **Patient-side is a first-class product surface.** Public self-registration, clinic discovery,
   and appointment booking are now platform features — not deferred nice-to-haves. This
   meaningfully increases scope, but also dramatically expands the addressable market and
   creates a network-effect flywheel: more patients attract more clinics, and vice versa.

2. **Multi-location is a core data primitive.** `branch_id` alongside `tenant_id` is a
   fundamental schema decision, not an add-on. Every sub-module, every RBAC assignment, and
   every data-isolation rule must be branch-aware from day one.

3. **B2B2C go-to-market via health-tech startups** reduces cold-start risk. Startups bring
   existing clinic portfolios; the platform captures patients as a downstream effect rather than
   needing to acquire patients directly. This is the correct sequencing for an Indonesian market
   entry where clinic trust and word-of-mouth drive consumer health adoption.

**Primary recommendation: Proceed** — with phased scope and two pre-conditions: (a) a legal
review of PP 71/2019 and PDPA before architecture is locked, and (b) a branch-isolation ADR
signed off by B1 before the first sprint.

---

## Personas

### Persona 1 — Clinic Owner / Chain Operator

| Attribute | Detail |
|-----------|--------|
| **Who** | Owner or administrator of 1–20 clinic branches across Indonesian cities (GP clinics, specialty clinics, dental chains, aesthetic clinics) |
| **Tech fluency** | Low-to-medium; uses WhatsApp Business, Google Sheets, or a single-purpose booking app today |
| **Primary device** | Desktop/laptop for admin; mobile for quick checks |
| **Goals** | Digitize patient registration and appointments; unify reporting across branches; eliminate phone queues; comply with PP 71/2019 without hiring a compliance team |
| **Pain points** | Separate disconnected systems per branch; staff re-entering the same patient data; no unified patient history when a patient visits a different branch; BPJS billing done manually |
| **Decision trigger** | A health-tech startup partner recommends App-Buildify, or competitor clinic in their area visibly upgrades |
| **Key metric** | Time saved per day on admin tasks; no-show reduction; BPJS claim acceptance rate |
| **Quote** | "I have three branches. My staff in Bandung can't see the records from Jakarta. Patients complain every week." |

---

### Persona 2 — Clinical Staff (Doctor / Nurse / Pharmacist)

| Attribute | Detail |
|-----------|--------|
| **Who** | Doctor (GP or specialist), nurse, pharmacist, or lab tech employed at a registered clinic |
| **Tech fluency** | Medium; comfortable with WhatsApp and mobile apps; resistant to complex EHR interfaces learned in hospital |
| **Primary device** | Shared clinic desktop or personal Android phone |
| **Goals** | Fast patient check-in; structured but lightweight encounter notes; digital prescription generation; quick access to previous visit summary |
| **Pain points** | Paper-based workflows create data loss; switching between disconnected apps during consultation breaks focus; no cross-branch patient history; prescription handwriting errors |
| **Decision trigger** | Clinic owner rolls out the platform; onboarding must be completable in under 30 minutes |
| **Key metric** | Time per encounter (target: ≤ 8 minutes for routine); prescription error rate; cross-branch lookup success |
| **Quote** | "The patient said she was here last month — but that was the Depok branch, so I have nothing. I'm starting from scratch." |

---

### Persona 3 — Patient / Public User (Indonesian, Mobile-First)

| Attribute | Detail |
|-----------|--------|
| **Who** | Indonesian resident, 18–55 years old, seeking outpatient healthcare; likely urban or peri-urban; owns an Android smartphone |
| **Tech fluency** | Medium; daily user of Tokopedia, Gojek, WhatsApp; accustomed to app-based booking |
| **Primary device** | Android mobile (≥ 85% of Indonesian smartphone market share) |
| **Language** | Bahasa Indonesia default; English secondary for professional class |
| **Goals** | Find a nearby verified clinic; register once; book an appointment without calling; access their own visit summary and prescription after the appointment |
| **Pain points** | Must re-register with each clinic; appointment booking is phone-only; no digital copy of their prescription or lab results; uncertainty about clinic quality |
| **Decision trigger** | Doctor at a clinic sends a WhatsApp link to book online, or a family member recommends a clinic they found via search |
| **Key metric** | Booking completion rate; repeat booking rate; post-visit record access rate |
| **Compliance note** | Consent for data processing (PDPA-aligned) must be in Bahasa Indonesia; language must be plain, not legal boilerplate |
| **Quote** | "I just want to book and not wait in line. And I keep losing my lab results." |

---

### Persona 4 — Health-Tech Startup (B2B Builder)

| Attribute | Detail |
|-----------|--------|
| **Who** | Indonesian or regional health-tech startup (seed to Series A) building a clinic management or patient-facing product for their own clinic clients on top of App-Buildify |
| **Team size** | 3–15 engineers; speed of deployment is a competitive advantage |
| **Goals** | Deploy a compliant, multi-tenant clinic platform for a portfolio of 5–50 clinic clients without building PHI infrastructure from scratch; white-label the patient portal for their brand |
| **Pain points** | Compliance plumbing (audit logs, consent, data residency) takes 6–12 months before any clinical feature; multi-tenancy bugs burn customer trust; each new clinic client needs branch configuration |
| **Decision trigger** | App-Buildify's module family eliminates 6+ months of infrastructure work; white-label + multi-location support is a direct feature unlock for their pitch to clinic chains |
| **Key metric** | Time from contract signature to first clinic live (target: ≤ 1 business day for base module); number of clinic clients deployable without custom code |
| **Differentiator valued** | Composable sub-modules (pay only for what's needed), BPJS export out of the box, branch-aware RBAC, white-label patient portal |
| **Quote** | "We don't want to build the compliance layer. We want to build the product that sits on top of it." |

---

### Persona 5 — Platform Admin (App-Buildify Ops)

| Attribute | Detail |
|-----------|--------|
| **Who** | App-Buildify internal operations staff responsible for platform health, PHI isolation monitoring, compliance audits, and incident response for healthcare tenants |
| **Goals** | Ensure no PHI crosses tenant or branch boundaries; monitor data residency compliance; run audit log exports for regulatory inquiries; manage BAA/DPA acceptance records |
| **Pain points** | Healthcare module introduces a public-facing patient layer — a new attack surface not present in B2B-only modules; cross-tenant data leakage would be a regulatory and reputational catastrophe |
| **Decision trigger** | Any new healthcare tenant activation; any sub-module enablement; any audit request from a clinic or regulator |
| **Key metric** | Zero cross-tenant PHI incidents; 100% BAA acceptance before sub-module activation; audit log completeness |
| **Quote** | "We need to know that even if a developer makes a query mistake, the row-level policies make it impossible for Patient A's data to appear in Clinic B's API response." |

---

## User Journey Maps

### Journey 1 — Clinic Onboarding (Target: ≤ 1 Business Day)

```
Actor: Clinic Owner (or Health-Tech Startup deploying on behalf of clinic)

Step 1 — Discovery & Sign-up (0–30 min)
  - Owner or startup partner visits the App-Buildify marketplace
  - Selects "Healthcare Module Suite" → clicks "Start Free Trial"
  - Creates platform account (email + phone OTP)
  - Answers clinic profile wizard: clinic name, specialty, city, number of branches,
    preferred language (Bahasa Indonesia / English)
  - Accepts DPA (Data Processing Agreement) — mandatory gate before any PHI module activates

Step 2 — Base Module Activation (30–60 min)
  - Platform provisions tenant + first branch (branch_id: branch-001)
  - Owner configures branch: address, operating hours, timezone (WIB/WITA/WIT), logo
  - Invites first staff members by email; assigns roles (Doctor, Nurse, etc.)
  - Receives activation confirmation email in chosen locale

Step 3 — Sub-module Selection (60–90 min)
  - Owner selects sub-modules from marketplace: e.g., Scheduling + Billing
  - Each sub-module activation confirms the base is active (server-side gate)
  - Owner configures scheduling: appointment types, slot duration, online booking toggle

Step 4 — First Appointment Booked (90 min – end of business day)
  - Staff member (or owner) creates first test patient record
  - Books a test appointment via clinic staff portal
  - Alternatively: patient self-registers on patient portal and books directly
  - Owner receives confirmation: "Your clinic is live on the platform"

Success gate: First confirmed appointment in the system ≤ 1 business day from account creation.

Failure modes to watch:
  - DPA step abandoned (friction too high) → simplify language, offer chat support
  - Staff invitation email goes to spam → add WhatsApp alternative invite
  - Timezone/locale misconfiguration causes wrong slot display → default to WIB, allow per-branch override
```

---

### Journey 2 — Patient Self-Registration + Clinic Discovery + Appointment Booking

```
Actor: Indonesian patient, mobile browser (Android)

Step 1 — Entry point (0–2 min)
  - Receives WhatsApp link from clinic, or searches "klinik [city name]" in browser
  - Lands on patient portal (public-facing, authenticated access only for health data)
  - Sees clinic discovery page: search by location, specialty, availability

Step 2 — Patient Registration (2–5 min)
  - Clicks "Daftar / Register"
  - Enters: full name (sesuai KTP), date of birth, phone number (WhatsApp), email (optional)
  - Verifies phone via OTP
  - Reviews and accepts consent form in Bahasa Indonesia (plain language, PDPA-aligned)
  - Universal health profile created: one account, usable across all registered clinics

Step 3 — Clinic Discovery (5–8 min)
  - Searches by location (GPS or manual city/district entry)
  - Filters: specialty, open today, available slots
  - Views clinic profile: name, address, doctors, services, operating hours
  - Selects clinic and branch

Step 4 — Appointment Booking (8–12 min)
  - Chooses appointment type (e.g., General Consultation)
  - Selects available date and time slot
  - Confirms booking
  - Receives WhatsApp confirmation (message body: appointment reference code + date/time only — NO diagnosis, NO doctor name in body per Permenkes PHI rules)

Step 5 — Post-Visit (after appointment)
  - Logs into patient portal
  - Views visit summary (if clinic staff published it)
  - Downloads prescription (if pharmacy module active)
  - Rates visit experience (NPS prompt)

Success gate: Patient completes booking in ≤ 12 minutes on a mid-range Android device on 4G.

Failure modes:
  - OTP not received (Telkomsel/XL coverage gaps) → add WhatsApp OTP as fallback
  - Consent form language too complex → UX test with Bahasa Indonesia speakers before launch
  - No available slots shown → display next available date rather than blank state
```

---

### Journey 3 — Multi-Branch: Owner Adds a Second Branch and Assigns Staff

```
Actor: Clinic Owner (tenant already active with branch-001)

Step 1 — Add Branch (5–10 min)
  - Owner logs into clinic admin portal
  - Navigates to: Settings → Branches → Add Branch
  - Enters branch details: name, address, city, timezone, operating hours, contact number
  - Platform creates branch-002 under the same tenant_id
  - Branch-002 is isolated: staff, schedules, inventory, and patient encounters are branch-scoped

Step 2 — Configure Branch (10–20 min)
  - Owner sets branch operating hours and appointment types (inherits tenant defaults, overridable)
  - Uploads branch-specific logo (if different from main brand)
  - Enables/disables sub-modules per branch (e.g., branch-002 has no pharmacy module yet)

Step 3 — Assign Staff to Branch (20–30 min)
  - Owner invites new staff by email or phone
  - Assigns role per branch: a doctor can be "Doctor at branch-001" and "Doctor at branch-002"
  - Or staff can be branch-exclusive: "Nurse at branch-002 only"
  - RBAC enforces that branch-002 staff cannot access branch-001 patient data without explicit cross-branch role

Step 4 — Verify Isolation (30–35 min)
  - Owner views unified dashboard: total appointments across all branches today
  - Branch manager for branch-002 logs in: sees only branch-002 data
  - Owner confirms cross-branch patient lookup is visible to them (Owner role spans all branches)

Success gate: Second branch operational (staff assigned, first appointment bookable) within 35 minutes.
```

---

### Journey 4 — Clinical Staff Daily Workflow: Check-in → Encounter → Prescription → Checkout

```
Actor: Doctor at clinic (mobile or desktop, clinic staff portal)

Morning prep (before first patient):
  - Logs in → sees today's appointment queue for their branch
  - Reviews any pre-visit notes or patient history summaries (if returning patient)

Patient check-in (receptionist or nurse):
  - Patient arrives; receptionist searches by name or phone number
  - Confirms appointment; marks patient as "Checked In"
  - Verifies/updates basic vitals (weight, blood pressure, temperature) — nurse-entered
  - Patient is moved to doctor's queue

Encounter (doctor, 5–10 min):
  - Doctor opens patient encounter screen
  - Reviews previous encounters at this branch (and other branches if cross-branch role assigned)
  - Enters SOAP notes (Subjective, Objective, Assessment, Plan) — structured fields + free text
  - Orders lab tests (if lab module active) — lab tech notified
  - Creates prescription (if pharmacy module active)

Prescription (doctor → pharmacist):
  - Doctor selects medications from branch catalog
  - Drug interaction check fires (adapter — requires licensed drug DB integration)
  - Pharmacist receives prescription digitally → dispenses → marks as dispensed
  - Patient receives prescription summary (digital copy via patient portal)

Checkout (billing staff or receptionist):
  - Encounter marked complete
  - Invoice auto-generated from encounter + dispensed medications
  - Payment recorded (cash, transfer, or insurance)
  - BPJS claim data captured for export (if applicable)
  - Patient checkout confirmed; post-visit WhatsApp sent: "Thank you for your visit. Reference: [code]" (no PHI)

End-of-day:
  - Doctor views summary: patients seen, prescriptions issued
  - Branch manager views branch revenue and appointment completion rate

Key timing targets:
  - Check-in to doctor queue: ≤ 3 minutes
  - Encounter documentation: ≤ 5 minutes for routine consultation
  - Prescription to dispensed: ≤ 5 minutes
  - Checkout (invoice + payment): ≤ 2 minutes
```

---

## Competitor Matrix

| Competitor | Category | Strengths | Weaknesses | Indonesian Fit | Differentiator Gap |
|------------|----------|-----------|------------|----------------|--------------------|
| **Halodoc** | Patient-facing / Telemedicine | Massive patient base, BPJS partnership, strong brand | Doctor-on-demand only; no clinic management; no multi-branch ops | High (local, dominant) | No clinic ops tooling; no white-label; no composable modules |
| **Alodokter** | Patient-facing / Telemedicine | Content platform + appointment booking | Clinic-side tooling is thin; no multi-location support | High (local) | No B2B2C startup model; no composable sub-modules |
| **KlikDokter** | Patient-facing / Content | Medical content authority; strong SEO | Appointment booking is secondary; no clinic management layer | Medium (local) | Content-led, not operations-led; no startup partner model |
| **Assist.id** | Clinic Management (SaaS) | Purpose-built for Indonesian clinics; BPJS export; local support | Single-clinic focus; no multi-location; no patient public portal; no white-label | High (local) | No two-sided platform; no startup B2B2C model; no composable modules |
| **Medigo** | Clinic Management (SaaS) | Indonesian market; pharmacy integration | Limited multi-location; smaller ecosystem; no patient self-registration portal | Medium (local) | Weaker on two-sided model and startup white-label |
| **Doctor Anywhere** | Telemedicine + Clinic | Regional presence; telehealth + in-clinic | Singapore-centric; Indonesia is secondary market; complex pricing | Low-medium (regional) | Not Indonesia-first; no composable module system |
| **MyDoc** | Enterprise Telehealth | Strong enterprise features | Expensive; hospital-grade complexity; not SME-friendly | Low (regional) | Wrong segment (enterprise hospitals vs. SME clinics) |
| **Salesforce Health Cloud** | Enterprise CRM/EHR | Feature-complete; global compliance | Extremely expensive; requires SI; overkill for Indonesian SME clinics | Very Low | Wrong ICO; no Indonesian compliance defaults |
| **Bubble / Retool** | Generic NoCode | Flexible; fast to prototype | No healthcare compliance; no PHI isolation; no BPJS; no clinical data model | Low | No domain knowledge; compliance burden falls entirely on builder |

### Differentiation Summary

App-Buildify Healthcare Module Suite is the **only** option that combines:
- Two-sided platform (clinic ops + patient self-service) in a single product
- Composable sub-modules (pay only for what's activated)
- Multi-location / multi-branch support as a first-class data primitive
- White-label and multi-tenant architecture for health-tech startups (B2B2C)
- Indonesia-first compliance defaults (PP 71/2019, BPJS export, Bahasa Indonesia default)
- i18n-first for worldwide expansion without code changes

The nearest local competitor (Assist.id) covers clinic ops but is single-clinic, has no patient portal, and has no startup white-label model. Halodoc and Alodokter have the patient network but no clinic management depth and no B2B2C startup model.

---

## Constraints & Risks

### Regulatory Constraints

| Constraint | Detail | Implication for Architecture |
|------------|--------|------------------------------|
| **Indonesia PP No. 71/2019** | Electronic health records must be stored and managed with specific audit, retention, and access control requirements. Data residency in Indonesia is implied by regulatory context. | Data residency in Indonesian cloud region (AWS ap-southeast-3 Jakarta or equivalent) is mandatory for tenants with Indonesian patients. Audit log must be immutable and exportable. |
| **PDPA Alignment** | Indonesia's Personal Data Protection Law (UU PDP No. 27/2022) requires explicit consent for health data collection and processing. Consent must be revocable, purpose-specific, and recorded. | Consent management is a first-class module feature. Consent records must be timestamped, versioned, and auditable. Patient-facing consent UI must be in Bahasa Indonesia with plain language. |
| **Permenkes No. 20/2019 (Telemedicine)** | Telemedicine services must comply with specific requirements: doctor must be licensed (SIP/STR verified), session recording consent required, specific documentation standards. | Telemedicine sub-module ships last. Legal review gates its GA. Doctor license verification is a manual workflow in v1 (automated SIP check via P2KB is a future phase). |
| **Permenkes on PHI in communications** | Patient health information (diagnosis, medication, provider name) cannot appear in SMS or messaging app notification bodies. | WhatsApp/SMS reminder templates are system-locked. Only appointment reference code, date, time, and clinic name are permitted in the message body. No free-text PHI fields in notification templates. |
| **BPJS Kesehatan Billing Format** | BPJS claim submission requires specific file formats and claim codes. Format version changes occur when Ministry of Health updates tariff schedules. | Billing module produces BPJS-export files via a versioned adapter pattern. Live API submission is out of scope for v1. Format version must be configurable without a code deploy. |

### Technical Constraints

| Constraint | Detail |
|------------|--------|
| **branch_id isolation** | Every PHI record, schedule slot, staff assignment, and RBAC check must carry both `tenant_id` and `branch_id`. Row-level security policies must enforce both dimensions. A query that omits `branch_id` must fail-safe (return empty, not all-branch data). |
| **Patient data scoped to collecting tenant** | In v1, a patient's encounter data at Clinic A is invisible to Clinic B even if the patient presents there. Cross-clinic sharing requires explicit patient consent and is a future feature. The patient's universal profile (demographics, contact info) is platform-owned; encounter data is tenant-owned. |
| **i18n-first** | Zero hardcoded UI strings in module code. All copy — including error messages, validation text, printed documents, and notification templates — goes through the translation layer. Launch locales: `id-ID` (default) and `en-US`. Locale is configurable per tenant and per user. |
| **No real PHI in non-production** | Synthetic patient data tooling must be ready before any clinical feature is testable in staging or CI. This is a blocker for QA. |
| **Public-facing patient portal** | The patient portal is a new attack surface not present in B2B-only modules. It must handle: unauthenticated discovery (clinic search), OTP-gated registration, and authenticated access to PHI. Rate limiting, OTP abuse prevention, and OWASP Top 10 controls are required from day one. |
| **Android-first mobile web** | Patient portal must be performant on mid-range Android devices (2GB RAM, 4G) with Lighthouse performance score ≥ 80. Server-side rendering or aggressive code splitting is required. |

### Business & Go-to-Market Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Slow clinic adoption** — clinics are conservative buyers | Medium | High | Lead with health-tech startup partners who bring existing clinic portfolios; reduce friction with ≤ 1 day onboarding target |
| **Slow patient adoption** — two-sided cold-start problem | High | High | B2B2C model means clinic network is built first; patient adoption follows naturally as clinics activate online booking |
| **PP 71/2019 scope broader than anticipated** | Medium | High | Engage local legal counsel (Jakarta-based health law firm) before B1 begins architecture; build data residency as a configurable first-class feature |
| **Multi-location isolation underestimated** | Medium | High | branch_id ADR must be produced by B1 and reviewed before Sprint 1; no data model decisions before this ADR is approved |
| **BPJS billing format changes mid-development** | Medium | Medium | Versioned adapter pattern; BPJS format version is tenant-configurable; monitor Ministry of Health announcements |
| **WhatsApp/SMS PHI leakage** | High (if not designed correctly) | High | Notification templates are system-locked at platform level; clinic staff cannot customize PHI fields in message bodies |
| **Telemedicine regulatory complexity** | Medium | High | Telemedicine sub-module ships last in the sequence; its GA is gated by a separate legal review |
| **Patient portal security incidents** | Medium | Critical | Public-facing surface requires OWASP review, rate limiting, OTP abuse prevention, and penetration testing before GA |
| **Drug interaction data currency** | Medium | Medium | Pharmacy module defines the adapter interface; a licensed drug DB (MIMS Indonesia or equivalent) is required for production — this is a third-party procurement dependency |

---

## Recommendation

### Decision: **Proceed — with two hard pre-conditions and a phased sub-module sequence**

#### Rationale

1. **Market timing is favorable.** The Indonesian digital health market is expanding rapidly
   post-pandemic. BPJS digitization pressure is pushing small clinics to adopt electronic
   records. Halodoc and Alodokter dominate patient-facing telemedicine but leave a wide gap
   in clinic-side operations and the B2B2C startup model. This gap is App-Buildify's entry point.

2. **B2B2C via startups is the correct go-to-market.** Direct clinic sales are slow and
   trust-dependent. Health-tech startups are faster buyers with existing clinic portfolios.
   They take on the last-mile relationship with clinics; App-Buildify provides the compliant
   infrastructure underneath. This mirrors successful regional plays (e.g., Xendit for payments).

3. **Two-sided platform creates a defensible moat.** Once patients are registered on the
   platform, they create pull for more clinics. Once clinics are live, they drive patient
   registrations. Generic NoCode platforms (Bubble, Retool) cannot replicate this flywheel
   because they lack the clinical data model, PHI isolation, and BPJS compliance defaults.

4. **Multi-location support is a genuine competitive gap.** No local competitor (Assist.id,
   Medigo) offers branch-aware multi-location clinic management with a unified tenant view.
   This is a direct feature unlock for clinic chains and for health-tech startups pitching
   to chain operators.

#### Hard Pre-conditions (must be resolved before B1 begins architecture)

**Pre-condition 1: Legal review of PP 71/2019 and UU PDP No. 27/2022**
Engage a Jakarta-based health law firm to produce a compliance scope document covering:
data residency requirements, audit log specifications, consent management obligations,
and telemedicine-specific requirements under Permenkes 20/2019.
This document is a required input to the B1 architecture ADR.

**Pre-condition 2: Branch Isolation ADR**
B1 must produce an Architecture Decision Record specifically addressing how `branch_id`
is enforced alongside `tenant_id` in row-level security policies, API middleware, and
any ORM/query builder abstractions. The ADR must demonstrate that a query missing
`branch_id` fails-safe (returns empty, not cross-branch data). This ADR must be reviewed
and approved before any data model decisions are made.

#### Recommended Sub-Module Launch Sequence

| Phase | Sub-modules | Rationale |
|-------|-------------|-----------|
| **GA** | `healthcare` (base) + `healthcare_scheduling` | Core clinic ops + online booking; minimum viable two-sided platform |
| **Month 2–3** | `healthcare_billing` | BPJS export is a strong retention driver for clinic owners; high-value feature |
| **Month 3–4** | `healthcare_pharmacy` | Requires licensed drug DB procurement; sequence after base is stable |
| **Month 4–5** | `healthcare_lab` | Depends on pharmacy data model patterns; lower urgency than billing |
| **Month 6+** | `healthcare_telemedicine` | Ships last; requires separate legal review; do not block other sub-modules |

#### What Would Cause a Pivot

- Legal review reveals PP 71/2019 data residency requirements are incompatible with
  existing App-Buildify infrastructure at acceptable cost → re-scope to B2B-only (no patient portal) or delay GA.
- Health-tech startup interviews (recommended: 5–8 interviews before B1 starts) reveal
  demand signal weaker than expected → reduce scope to clinic-ops-only (single-sided) and revisit patient portal in v2.
- B1 branch-isolation ADR reveals multi-location enforcement requires a fundamental
  multi-tenancy refactor of the App-Buildify core → re-sequence to single-branch v1 with multi-branch in v2.

---

## Hand-off Notice to A3 (UX / Design)

**From:** A2 Business Analyst
**To:** A3 UX/Design
**Date:** 2026-06-21
**Status:** Research Brief v2 complete — ready for design phase

**Priority design surfaces (in order):**

1. **Patient self-registration and clinic discovery flow** — mobile-first, Bahasa Indonesia
   default, Android mid-range device performance target. This is the highest-risk UX surface:
   consent form language, OTP flow, and clinic search empty states all need careful testing
   with Indonesian users.

2. **Clinic onboarding wizard** — must be completable by a non-technical clinic owner within
   1 business day. Key steps: DPA acceptance, branch setup, staff invitation, first appointment
   configuration. Minimize decisions required before the clinic is "live."

3. **Clinical staff daily workflow** — doctor encounter screen must be fast and keyboard-friendly.
   The SOAP note entry pattern needs to be validated against actual clinic workflows in
   Indonesia (GP consultation typically 5–10 minutes). Avoid patterns designed for Western
   EHR users.

4. **Multi-branch admin dashboard** — unified tenant view showing all branches; branch-scoped
   view for branch managers. RBAC must be visible and understandable to non-technical clinic owners.

5. **WhatsApp notification templates** — all outbound notification content must be reviewed
   against the PHI-in-message-body constraint (Permenkes). Design the "safe" template set
   before engineering builds the notification service.

**Open questions for A3 to investigate:**
- Do Indonesian clinic owners prefer a mobile app or desktop-first admin portal?
  (Hypothesis: desktop for admin, mobile for quick status checks)
- What is the acceptable number of registration steps before patient drop-off?
  (Benchmark: Gojek/Tokopedia onboarding is 2–3 steps; target similar)
- Should clinic search results surface individual branch locations or clinic brands?
  (Likely: show nearest branch of a clinic brand)

**Upstream artifacts:**
- `plan-mod-healthcare/vision/vision-02.md`
- `plan-mod-healthcare/research/research-02.md` (this document)
