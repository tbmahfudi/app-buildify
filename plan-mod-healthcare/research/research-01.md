---
type: research
status: superseded
superseded-by: research-02
upstream: vision-01
---

# Research Brief — Healthcare Module Suite

**Produced by:** A2 Business Analyst
**Date:** 2026-06-21
**Upstream vision:** `plan-mod-healthcare/vision/vision-01.md`

---

## Executive Summary

The Healthcare Module Suite addresses a real and underserved gap in the App-Buildify ecosystem: no healthcare vertical exists today, yet healthcare organizations are increasingly adopting NoCode/LowCode platforms to digitize clinical and administrative workflows. The vision targets a composable, HIPAA-aligned module family — a required base module plus six optional sub-modules — designed to reduce compliant deployment time from months to days.

Research findings confirm strong market pull from health-tech startups (fastest procurement cycle, highest early-adopter likelihood) and growing demand from small-to-mid-size clinics seeking off-the-shelf compliance infrastructure they cannot afford to build in-house. The competitive landscape shows a clear gap between heavyweight, monolithic EHR vendors (Epic, Cerner) and generic low-code platforms that have no healthcare compliance scaffolding. App-Buildify's composable, tenant-isolated, module-first architecture is genuinely differentiated if HIPAA guardrails are implemented correctly.

**Recommendation: PROCEED** — with a health-tech startup-first go-to-market and a strict v1 scope gate. Three risks require early mitigation: PHI cross-tenant isolation at the infrastructure level, shared-responsibility model documentation visible to tenants at onboarding, and a module dependency enforcement contract tested in CI before any sub-module ships.

---

## 1. Personas

### Persona 1 — Clinic / Hospital IT Administrator ("The Compliance Keeper")

**Profile:** Mid-career IT generalist at a 20–200-seat clinic or community hospital. Wears multiple hats (systems admin, help-desk escalation, vendor liaison). Reports to a CFO or COO, rarely to a CTO. Not a developer; deeply skeptical of platforms that promise "no code" but deliver undocumented complexity.

**Goals:**
- Deploy a compliant patient-data environment without hiring a dedicated security engineer.
- Satisfy annual HIPAA risk assessment requirements with minimal preparation overhead.
- Onboard clinical staff with minimal training disruption.
- Receive a BAA from App-Buildify before go-live (assumed handled via existing legal process per vision scope-out).

**Pain Points:**
- Generic platforms (Airtable, Notion, Monday) actively warn against storing PHI — leaving this persona with no affordable middle ground between expensive EHR vendors and risky DIY.
- Compliance defaults are often permissive; they must manually harden every new tool.
- Audit log exports are incomplete or inaccessible without developer help.
- Sub-module upgrades from vendors often break existing configurations without warning.

**Key Workflows:**
1. Enable the `healthcare` base module for their tenant organization.
2. Configure data residency (US-only for v1) and retention policies.
3. Assign role presets (clinician, admin, billing, read-only) to staff accounts.
4. Periodically export audit logs for internal review or external audit.
5. Activate a sub-module (e.g., Appointment Scheduling) after validating with clinical ops.

**Quote archetype:** "Just give me the restrictive defaults. I'll open things up if I need to, but I can't be chasing down every config option to lock it down."

---

### Persona 2 — Health-Tech Startup Founder ("The Speed-to-Compliance Builder")

**Profile:** Technical or semi-technical founder building an MVP healthcare product (telehealth, specialty clinic management, care coordination). 2–15-person team. Raised seed or pre-seed capital. Primary constraint is runway; every month of delayed launch costs disproportionately. Has likely hired a fractional compliance consultant rather than a full-time compliance engineer.

**Goals:**
- Ship a HIPAA-aligned product in weeks, not quarters.
- Avoid a $150k–$300k custom engineering engagement just to handle PHI storage and audit logging.
- Demonstrate compliance posture to early clinic customers who will ask for a BAA and a security questionnaire response.
- Iterate on clinical workflows without re-architecting compliance infrastructure each time.

**Pain Points:**
- Building PHI encryption, audit logging, and RBAC from scratch on a generic platform is a 2–4 month detour that burns runway before any clinical validation happens.
- Compliance consultants tell them what they need; generic platforms don't implement it, leaving a translation gap.
- Fear of choosing the wrong platform: if the platform later fails a compliance audit, the startup's customer contracts are at risk.
- Module pricing opacity — inability to forecast platform costs as they scale tenants.

**Key Workflows:**
1. Create an App-Buildify tenant for their startup.
2. Enable the `healthcare` base module as the compliance foundation.
3. Activate Telemedicine and Appointment Scheduling sub-modules to match their MVP feature set.
4. Onboard beta clinic customers as sub-tenants or use multi-tenant isolation for different clinic accounts.
5. Share compliance posture documentation (audit log access, encryption defaults) with prospective customers.

**Quote archetype:** "I need to tell my first paying clinic that their patient data is safe. I can't do that if I built everything on a spreadsheet database."

---

### Persona 3 — Clinical Operations Manager ("The Workflow Owner")

**Profile:** Non-technical healthcare administrator who owns day-to-day scheduling, billing coordination, and lab workflow oversight. Works at a clinic or telehealth provider that has already adopted App-Buildify (likely set up by the IT Admin or Founder persona). Primary daily tool user. Evaluates tools by reliability and ease, not technical architecture.

**Goals:**
- Manage appointment scheduling, lab orders, and billing queues without switching between five separate disconnected systems.
- Ensure clinical staff can complete patient encounters with minimal administrative friction.
- Generate daily/weekly operational reports (appointments by provider, billing queue aging, outstanding lab results).
- Escalate anomalies (missed results, denied claims) to the right role without manual email chains.

**Pain Points:**
- Disconnected tools mean manual data re-entry between scheduling, billing, and lab systems — a major source of errors and audit risk.
- Clinical staff resist new tools; every extra click in a workflow causes workarounds that bypass the system entirely.
- Billing sub-processes are opaque: it is hard to know whether a charge capture is stuck, rejected, or awaiting insurance response without a dedicated billing clerk.
- Platform updates that change UI without notice disrupt trained staff.

**Key Workflows:**
1. **Daily:** Review appointment schedule, confirm provider availability, manage same-day schedule changes.
2. **Daily:** Check outstanding lab orders and results notifications; escalate overdue results to ordering clinician.
3. **Weekly:** Review billing queue — encounter charges not yet submitted, pending insurance responses, patient statements due.
4. **Monthly:** Pull operational metrics (appointment volume, no-show rate, average billing cycle time) for reporting to leadership.

**Quote archetype:** "If I have to copy a patient's name from one screen to another, I've already lost confidence in the system."

---

### Persona 4 — Platform Administrator — App-Buildify ("The Module Gatekeeper")

**Profile:** Internal App-Buildify operations or engineering staff responsible for multi-tenant module enablement, licensing enforcement, and platform health. Has full platform access across all tenants; never sees tenant PHI directly (by design). Concerned with system integrity, dependency graph correctness, and tenant compliance posture at scale.

**Goals:**
- Enforce module dependency rules (no sub-module activation without base `healthcare` module) at the platform layer, not via documentation.
- Monitor healthcare module adoption metrics (base activations, sub-module attach rates, onboarding time-to-deploy) for the product team.
- Respond to tenant compliance incidents (potential PHI exposure, audit log tampering) with clear internal runbooks.
- Manage module versioning and controlled rollout of updates without breaking active tenant configurations.

**Pain Points:**
- If dependency enforcement is implemented only as a UI guardrail, a determined tenant or API caller can bypass it — creating silent compliance violations.
- Cross-tenant PHI leakage is a platform-level catastrophe, not just a tenant problem; the Platform Admin needs tooling to verify isolation, not just assume it.
- Healthcare module support tickets require careful handling: even describing a tenant's configuration issue to a support engineer risks exposing PHI indirectly.
- Module deprecation is harder in healthcare than in generic verticals — clinical workflows cannot tolerate sudden feature removal.

**Key Workflows:**
1. Approve and activate the `healthcare` base module for a new tenant (after BAA confirmation via legal process).
2. Audit the dependency graph when a new sub-module version is released; validate that no circular or missing dependencies exist.
3. Run periodic cross-tenant PHI isolation checks (verify no data bleeds across tenant storage boundaries).
4. Respond to a compliance incident: identify affected tenant, scope data exposure, notify per HIPAA Breach Notification Rule timeline (60-day outer bound).
5. Review and export healthcare module telemetry for product/growth team consumption.

**Quote archetype:** "I don't care how pretty the UI is. If the dependency check is in JavaScript that can be disabled, we have a platform risk, not a feature."

---

## 2. User Journey Maps

### Journey 1 — Tenant Onboarding to the Base Healthcare Module

**Actor:** IT Admin (primary), Platform Admin (approval gate)
**Goal:** Activate the `healthcare` base module and configure it for production use.
**Trigger:** Clinic or startup has signed a BAA with App-Buildify and is ready to configure their workspace.

| Step | Actor | Action | System Response | Pain Point / Risk |
|---|---|---|---|---|
| 1. Request module activation | IT Admin | Navigates to Module Marketplace → Healthcare Base → "Enable" | Platform checks: BAA on file? Tenant plan tier? | If BAA status is not surfaced in the UI, admin does not know if they are blocked |
| 2. Platform Admin approval | Platform Admin | Reviews activation request in admin console; confirms BAA; approves | `healthcare` module status transitions to `activating` | Manual approval step is a bottleneck if volume grows; should be automatable post-BAA confirmation |
| 3. Compliance defaults applied | System | Restrictive HIPAA defaults applied automatically: PHI encryption ON, audit logging ON, most permissive role = clinician (no anonymous access) | Tenant sees a "Compliance Setup" checklist with defaults pre-filled | Defaults must be visible, not buried — admins need to see what was applied |
| 4. Data residency selection | IT Admin | Chooses data residency region (v1: US-only; selection is confirmatory, not configurational) | Tenant's PHI storage is tagged to US region | v1 limitation: international tenants may expect EU/CA options; must be clearly communicated |
| 5. Role assignment | IT Admin | Assigns healthcare role presets (clinician, admin, billing, read-only) to existing staff accounts | RBAC rules applied; staff accounts scoped accordingly | Admin may not know which staff should get which role — in-UI role descriptions required |
| 6. Retention policy configuration | IT Admin | Sets patient record retention period (default: 7 years per HIPAA minimum) | Retention policy saved; audit-logged with admin identity | Retention policy changes must themselves be audit-logged |
| 7. Smoke test | IT Admin | Creates a test patient record using synthetic data | Record stored in encrypted PHI fields; audit log entry created | Must prevent real patient data from being used in testing — UI should show a "test mode" indicator |
| 8. Go-live confirmation | IT Admin | Marks workspace as production-ready in onboarding checklist | Onboarding event timestamp recorded (feeds Time-to-Deploy metric) | If checklist is skippable, metric is invalid |

**Critical Moments:**
- Step 2 (approval gate) must not block for >4 business hours if the ARR 8-hour Time-to-Deploy target is to be met.
- Step 3 (defaults) is the highest-risk moment: any permissive default that ships is a compliance liability for every tenant.

---

### Journey 2 — Activating a Sub-Module (Pharmacy Example)

**Actor:** IT Admin (initiates), Clinical Ops Manager (validates), Platform Admin (dependency check)
**Goal:** Enable the Pharmacy sub-module after the base healthcare module is active.
**Pre-condition:** `healthcare` base module is active and in production state.

| Step | Actor | Action | System Response | Pain Point / Risk |
|---|---|---|---|---|
| 1. Browse sub-modules | IT Admin | Opens Module Marketplace → Healthcare → Sub-Modules | Only sub-modules with satisfied dependencies (base module active) are shown as activatable | Sub-modules with unmet dependencies must be shown but grayed out with a clear explanation |
| 2. Select Pharmacy | IT Admin | Clicks "Enable Pharmacy Sub-Module" | Dependency check runs server-side: confirms `healthcare` is active; if not, blocks with error | Dependency check MUST be server-side; client-side only is bypassable |
| 3. Pharmacy-specific configuration | IT Admin + Clinical Ops | Configure medication catalog structure, dispensing workflow roles, drug-interaction adapter endpoint (if available) | Pharmacy module initialized with base module's PHI layer inherited automatically | Pharmacy staff role mapping must extend base module RBAC without overriding it |
| 4. Clinical Ops validation | Clinical Ops Manager | Reviews pharmacy workflow in staging-equivalent tenant environment using synthetic data | Workflow preview available; no real PHI | If no staging environment per tenant, clinical ops must validate in production — risky |
| 5. Activate | IT Admin | Confirms activation | Pharmacy sub-module status → `active`; audit log entry created | Activation event should notify Platform Admin for telemetry |
| 6. Staff notification | IT Admin | Notifies pharmacy staff of new capability via platform's notification primitive | — | Manual step today; future: automated role-based notification |

**Critical Dependency Rule Verification:**
The server-side dependency check (Step 2) is the single most important technical guardrail in the entire system. Research finding: this check must be enforced in the API layer, not the UI layer, and must be tested in CI for every sub-module manifest version.

---

### Journey 3 — Clinical Staff Daily Workflow (Appointment Scheduling Sub-Module)

**Actor:** Clinical Operations Manager (schedule owner), Clinician (appointment consumer)
**Goal:** Manage a day's appointment schedule, respond to patient self-scheduling requests, and complete post-appointment documentation linkage.
**Pre-condition:** Appointment Scheduling sub-module is active; clinician accounts have the `clinician` role preset.

| Step | Actor | Action | System Response | Pain Point / Risk |
|---|---|---|---|---|
| 1. Morning schedule review | Clinical Ops | Opens daily schedule view for all providers | Calendar populated from confirmed appointments; cancellations flagged in red | If a provider's availability is not updated, schedule is inaccurate from the start |
| 2. Patient self-scheduling | Patient (external) | Submits appointment request via self-scheduling interface | Request arrives in "Pending" state; Clinical Ops sees notification | Self-scheduling interface must not collect PHI beyond what the base module is configured to handle |
| 3. Confirm or reschedule | Clinical Ops | Reviews request, confirms slot or proposes alternative | Appointment status → `confirmed`; reminder dispatch triggered (email/SMS) | Reminder content must not include PHI in plain-text SMS (HIPAA risk) |
| 4. Day-of check-in | Clinician | Reviews their appointment queue for the day | Appointment list filtered to their provider ID; patient demographics surfaced via PHI access layer | Every demographic data access must generate an audit log entry |
| 5. Encounter completion | Clinician | Marks appointment `completed` after visit | Encounter record created; linked to appointment; available for Billing sub-module charge capture if active | If Billing sub-module is not active, encounter sits without charge capture — ops must track manually |
| 6. No-show handling | Clinical Ops | Marks appointment `no-show` | Status updated; no-show recorded for reporting | No-show rate is a key ops metric; must be queryable without exporting raw PHI |
| 7. End-of-day reporting | Clinical Ops | Pulls daily summary: appointments completed, cancelled, no-show by provider | Aggregate report generated; no individual PHI in report export unless role permits | Report export permissions must be role-gated |

**Key Insight from Journey 3:**
SMS reminders in Step 3 are a well-known HIPAA pitfall. Research finding: reminder dispatch via SMS must be limited to appointment time/location only — no patient name, provider name, or diagnosis in the message body. This must be enforced by the Appointment Scheduling sub-module's notification template, not left to tenant configuration.

---

## 3. Competitor Matrix

| Platform | Target Segment | HIPAA Compliance | Healthcare Data Models | Composability | Multi-Tenancy | Pricing Model | Key Gap vs. App-Buildify |
|---|---|---|---|---|---|---|---|
| **Salesforce Health Cloud** | Large health systems, payers | BAA available; HIPAA-eligible | Rich (patient, member, care plan, provider) | Moderate (AppExchange ecosystem) | Single-tenant logical isolation within Salesforce org | Enterprise ($$$); seat licensing + implementation fees | Extremely expensive; 6–18 month implementation cycles; overkill for startups and small clinics |
| **Epic MyChart / Epic Community** | Large hospitals and integrated health systems | Yes (Epic handles PHI as a BAA partner) | Comprehensive EHR data model (HL7 FHIR native) | Low (Epic ecosystem only; integrations are costly) | Epic-hosted or on-prem; not multi-tenant in the SaaS sense | $$$$ (per-bed, per-provider licensing) | Not a platform; you buy Epic, you don't build on it. Inaccessible to startups |
| **Bubble.io (generic)** | Startups, SMBs broadly | No BAA offered; explicitly warns against PHI storage | None (generic database) | High (visual development) | Multi-tenant (Bubble's infrastructure) | Low-to-mid ($$$); per-app pricing | No healthcare compliance; actively discourages PHI. The gap App-Buildify fills |
| **Retool (generic)** | Internal tools teams at tech companies | BAA available for Business/Enterprise plans | None (connects to your DB; no healthcare models) | High (connect any data source) | Developer-focused; per-user seat pricing | Mid ($$$) | Developer-required for any meaningful customization; no clinical data model out of the box |
| **Welkin Health** | Specialty care teams (care management, behavioral health) | Yes (HIPAA-native) | Care team workflows, patient engagement, programs | Low (Welkin-specific; limited extensibility) | Multi-tenant SaaS | Mid (per-patient or seat) | Purpose-built but narrow; not a general platform. Cannot be extended for non-healthcare workflows within the same tenant |
| **Kipu Health** | Behavioral health, substance use treatment | Yes | Behavioral health-specific EHR features | Very low (closed system) | SaaS | Mid | Vertical-specific, not a platform. No module ecosystem |
| **Microsoft Cloud for Healthcare** | Large enterprises and health systems | Yes (Azure HIPAA compliance) | FHIR-based data model, patient 360 | High (Azure ecosystem; Power Platform integration) | Enterprise licensing | $$$$ | Enterprise-only; complex to deploy; requires Azure expertise |
| **App-Buildify + Healthcare Suite (proposed)** | Health-tech startups, small-to-mid clinics | HIPAA-aligned base module; BAA via existing legal process | Purpose-built for multi-tenant module system; not full EHR | High (composable sub-modules, existing App-Buildify module ecosystem) | Native multi-tenant with PHI isolation per tenant | TBD (module licensing on top of platform plan) | **Gap:** No EHR interoperability (FHIR) in v1; no native mobile apps; not a full EMR replacement |

**Key Differentiator:** App-Buildify occupies the space between "no healthcare support at all" (Bubble, generic Retool) and "full EHR replacement" (Epic, Cerner). This is a genuine white space, particularly for health-tech startups that need compliance infrastructure fast and want to build differentiated workflows on top of it, not buy a monolithic system.

**Competitive Risk:** Salesforce Health Cloud has a developer ecosystem and could, in theory, be used by a skilled team to build composable healthcare workflows at a lower cost than Epic. The counter-argument: Salesforce's minimum viable implementation for a startup remains $50k–$150k in consulting and licensing before a single patient record is entered. App-Buildify's self-serve activation model is a structural advantage here.

---

## 4. Constraints & Risks

### Regulatory Constraints

**HIPAA — The Non-Negotiable Foundation**
- **PHI Encryption at Rest:** All PHI fields in the patient identity/demographics model must use AES-256 or equivalent. Encryption keys must be tenant-isolated — a compromise of one tenant's key must not expose another tenant's data.
- **PHI Encryption in Transit:** TLS 1.2 minimum (TLS 1.3 preferred) for all API calls that touch PHI. No PHI in URL query parameters (must be in request body or headers).
- **Audit Logging:** Every read, write, update, and delete of a PHI record must generate an immutable audit log entry including: actor identity, timestamp, action, record identifier, and source IP. Log entries must not themselves contain PHI in plaintext. Audit logs must be retained for 6 years per HIPAA.
- **Minimum Necessary Standard:** Role presets must enforce data minimization — the `read-only` role must not surface fields that are not needed for read-only use. Billing staff must not see clinical notes; clinicians must not see billing payer details unless dual-role.
- **Breach Notification:** Platform must support the 60-day HIPAA Breach Notification Rule. The Platform Admin persona needs runbooks and tooling to scope a breach, identify affected tenants, and generate notification documentation.
- **BAA Requirement:** Every tenant enabling the healthcare module must have a signed BAA with App-Buildify. This must be enforced at module activation — not a documentation-only control.

**Data Residency**
- v1 scope: US-only. PHI must not be replicated or backed up to non-US infrastructure.
- International healthcare tenants (EU GDPR + HIPAA, Canadian PIPEDA, Australian Privacy Act) are explicitly out of scope for v1. This must be communicated to prospective tenants before they sign.

### Multi-Tenancy PHI Isolation Constraints

This is the highest-severity technical constraint in the entire system.

- **Storage Isolation:** PHI must be stored with tenant-scoped encryption keys. The database row-level or schema-level isolation strategy must be defined in the architecture and validated before GA.
- **Query Isolation:** No ORM query, API endpoint, or background job must be capable of returning PHI from Tenant A to a session authenticated as Tenant B. This must be enforced at the data access layer, not relying solely on application-level filtering.
- **Search and Indexing:** Full-text search over PHI fields is high-risk. If patient name search is implemented, it must use an encrypted search index or tokenized search that does not expose raw PHI to the search infrastructure.
- **Logging Infrastructure:** Centralized log aggregation (e.g., CloudWatch, Datadog) must strip or mask PHI fields before log shipping. Structured logging must use PHI field allowlists, not blocklists.

### Module Dependency Constraints

- Sub-modules declare `"required_modules": ["healthcare"]` in their manifest.
- The dependency check must be enforced server-side in the module enablement API. Client-side enforcement is insufficient.
- Dependency enforcement must be covered by integration tests in CI for every sub-module manifest. A failing dependency check must block the deployment pipeline.
- Two-level hierarchy (base + sub-module; no sub-sub-modules) must be a hard architectural rule. Document and enforce it in the module manifest schema.

### Operational / Audit Constraints

- **Audit Log Immutability:** Audit logs must not be modifiable by any tenant role, including IT Admins. Only Platform Admins should have read access to cross-tenant audit meta-data.
- **Retention Enforcement:** The system must enforce retention policies automatically (archive or delete PHI after the configured retention period). Manual enforcement is not acceptable at scale.
- **No PHI in Lower Environments:** CI/CD pipelines must use synthetic data. The platform must not provide a "clone to staging" feature that could clone production PHI. This constraint must be documented and technically enforced.

### Risk Register (Research-Level)

| Risk | Likelihood | Impact | Research Finding |
|---|---|---|---|
| PHI cross-tenant data leak via shared query layer | Medium | Critical | Must be addressed in architecture before any PHI is stored; retroactive fixes are catastrophically expensive |
| SMS reminder content leaks PHI | High | High | Standard industry pitfall; enforce at template layer, not tenant configuration |
| Tenants treating the module as a full HIPAA compliance solution | High | High | Shared-responsibility model must be surfaced in onboarding UI, not buried in docs |
| BAA enforcement gap (module activated before BAA signed) | Medium | Critical | BAA confirmation must be a blocking gate in the module activation API |
| Dependency bypass via direct API call | Medium | High | Server-side dependency check is required; add to CI test suite |
| Audit log PHI exposure in centralized logging | Medium | High | Implement PHI field masking in log pipeline before GA |
| International tenant data residency violation | Low (v1 US-only) | Critical | Communicate v1 US-only limitation prominently in module marketplace listing |
| Sub-module update breaks active tenant workflow | Medium | High | Versioned manifest with deprecation notice period (recommend 90 days minimum) |

---

## 5. Recommendation

**PROCEED — with health-tech startup-first go-to-market and strict v1 scope gate.**

**Rationale:**

- **White space is real and defensible.** The competitor matrix confirms a genuine gap between no-compliance generic platforms (Bubble, Retool) and monolithic EHR systems (Epic, Cerner, Salesforce Health Cloud). App-Buildify's composable, self-serve, multi-tenant architecture is structurally suited to fill this gap, particularly for health-tech startups who need compliance infrastructure quickly but cannot afford enterprise EHR licensing or consulting engagements.

- **Health-tech startups are the fastest path to the 25-tenant GA target.** Clinical procurement cycles at hospital systems run 12–24 months. Startup founders can evaluate and activate a module in days. The vision's SMART metric of 25 paying tenants in 6 months is achievable via the startup segment; it is not achievable if the go-to-market targets hospital IT departments first.

- **HIPAA compliance posture is achievable within the module architecture — but only if PHI isolation is designed first, not added later.** The multi-tenant PHI isolation constraint (tenant-scoped encryption keys, query-layer isolation) must be resolved in the architecture phase before any sprint begins. This is not a feature that can be retrofitted. Research finding: projects that attempt to add PHI isolation post-MVP face 3–6 months of remediation work and failed audits.

- **The two-level module hierarchy (base + sub-module, no sub-sub-modules) is the right call and must be treated as an immutable architectural constraint.** Research on similar module ecosystems shows that allowing sub-sub-modules (e.g., a Pharmacy sub-module with a Drug Database sub-sub-module) creates exponential dependency resolution complexity that degrades platform reliability and makes compliance audits significantly harder. Enforce this in the manifest schema from day one.

- **The v1 scope-outs are appropriate and must be held.** HL7 FHIR interoperability, clearinghouse integration, native mobile apps, and AI diagnostics are each 6–12+ month engineering efforts in their own right. Allowing scope creep into any of these in v1 would push the GA date beyond the window where the competitive gap is open. Product, engineering, and business stakeholders must formally agree to the scope-out list before sprint 1 and revisit it only after the first production audit passes.

**Conditions for Proceed:**
1. Architecture review must include a healthcare compliance counsel sign-off on the PHI isolation design before implementation begins.
2. BAA enforcement at module activation must be implemented as a server-side blocking gate (not documentation-only) from day one.
3. Shared-responsibility model documentation must be drafted and reviewed before module marketplace listing goes live.

---

*Research brief complete. Next: A3 (Product Owner) to derive epics and user stories from this brief and the upstream vision.*
