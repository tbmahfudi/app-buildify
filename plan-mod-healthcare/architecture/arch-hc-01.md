---
artifact_id: arch-hc-01
type: arch
module: healthcare-suite
status: Approved
producer: B1 Software Architect
upstream: [vision-02, research-02, epic-01-base-healthcare, BACKLOG.md, arch-00-platform, adr-hc-001, adr-hc-002, adr-hc-003, adr-hc-004]
consumers: [B2 Backend Developer, B3 Frontend Developer, Data Modeler, DevOps]
created: 2026-06-21
---

# Healthcare Module Suite — System Architecture (arch-hc-01)

**Producer:** B1 Software Architect
**Date:** 2026-06-21
**Status:** Approved
**Scope:** Epic-01 through Epic-05 and Epic-07. Epic-06 (Telemedicine) is excluded — pending
legal review (Permenkes No. 20/2019).

---

## 1. Context

App-Buildify is a multi-tenant modular platform (see `plan/architecture/arch-platform.md`).
The Healthcare Module Suite extends it into a **two-sided health service platform** for the
Indonesian market:

- **Provider side (B2B):** Clinic owners and staff manage multi-branch operations — patient
  records, appointments, prescriptions, lab orders, and billing — through the Clinic Portal.
- **Patient side (B2C):** Indonesian patients discover verified clinics, self-register, book
  appointments, and access their health records through the Patient Portal.
- **B2B2C go-to-market:** Health-tech startups onboard clinic portfolios; patients follow.

The suite is composed of one required base module and four optional sub-modules:

| Module | Phase | Depends on |
|--------|-------|-----------|
| `healthcare` (base) | GA | platform core |
| `healthcare_scheduling` | GA with base | base |
| `healthcare_billing` | Month 2–3 post-GA | base |
| `healthcare_pharmacy` | Month 3–4 post-GA | base |
| `healthcare_lab` | Month 4–5 post-GA | base |
| `healthcare_telemedicine` | EXCLUDED (legal gate) | base + scheduling |

**Compliance baseline:** Indonesia PP No. 71/2019 (electronic health records), UU PDP No.
27/2022 (personal data protection). Data residency: Indonesian cloud region (primary).

---

## 2. C4 Model — System Context

```
┌────────────────────────────────────────────────────────────────────────┐
│                         System Context                                 │
│                                                                        │
│  ┌──────────────┐     registers / books / views records               │
│  │   Patient    │────────────────────────────────────────────────────► │
│  │  (public)    │                                                      │
│  └──────────────┘    ┌──────────────────────────────────────────────┐ │
│                      │         App-Buildify                         │ │
│  ┌──────────────┐    │    Healthcare Module Suite                   │ │
│  │ Clinic Owner │───►│                                              │ │
│  │  / Staff     │    │  Two-sided health service platform           │ │
│  └──────────────┘    │  for Indonesian outpatient clinics           │ │
│                      │                                              │ │
│  ┌──────────────┐    │                                              │ │
│  │ Health-Tech  │    │                                              │ │
│  │  Startup     │───►│                                              │ │
│  │ (B2B tenant) │    └──────────────────────────────────────────────┘ │
│  └──────────────┘           │          │          │          │        │
│                             │          │          │          │        │
│                             ▼          ▼          ▼          ▼        │
│                      ┌──────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │
│                      │WhatsApp/ │ │  BPJS  │ │  Drug  │ │  SMTP  │  │
│                      │SMS Notif │ │ Export │ │Interact│ │ Email  │  │
│                      │ Adapter  │ │Adapter │ │Adapter │ │Service │  │
│                      └──────────┘ └────────┘ └────────┘ └────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

**External actors:**
- **Patient** — self-registers; books appointments; views own records.
- **Clinic Owner / Staff** — manages clinic operations (multi-branch).
- **Health-Tech Startup** — B2B tenant; deploys the suite for their clinic clients.

**External systems:**
- **WhatsApp/SMS Notification Adapter** — appointment reminders, OTP delivery (PHI-safe
  system-locked templates).
- **BPJS Export Adapter** — billing module generates BPJS Kesehatan-compatible claim files
  (no live API in v1; file export only).
- **Drug Interaction Adapter** — pharmacy module queries a licensed drug database (MIMS
  Indonesia or equivalent; adapter interface only — DB is tenant-procured).
- **SMTP Email Service** — clinic onboarding confirmation, staff invitations, patient
  notifications (PHI-safe).

---

## 3. C4 Model — Container Diagram

Extends `plan/architecture/arch-platform.md` §2. New containers are marked [HC].

```
                         Browser (Clinic Staff)       Browser (Patient)
                                  │                          │
                                  └──────────────┬───────────┘
                                                 │
                                                 ▼
                          ┌────────────────────────────────────────────┐
                          │          api-gateway (Nginx) :80           │
                          │  Routes /patient/* and /clinics/search →   │
                          │  healthcare-module                         │
                          │  Routes /tenants/* → core-platform         │
                          │  Routes /api/v1/financial/ → financial-mod │
                          │  CORS: patient paths = explicit origins     │
                          │  Rate-limit: public paths (slowapi+Redis)  │
                          └────────────┬───────────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
  ┌───────────────────────┐  ┌──────────────────────┐  ┌───────────────┐
  │    core-platform      │  │  healthcare-module   │  │  financial-   │
  │  FastAPI :8000        │  │  FastAPI :9002 [HC]  │  │  module       │
  │                       │  │                      │  │  FastAPI:9001 │
  │  Auth, Tenants, RBAC  │  │  Base healthcare +   │  │               │
  │  Platform SDK         │  │  all sub-modules     │  │               │
  │  Entity/Page/Workflow │  │  (scheduling,billing,│  │               │
  │                       │  │  pharmacy, lab)      │  │               │
  └───────────────────────┘  └──────────┬───────────┘  └───────────────┘
              │                         │
              └──────────┬──────────────┘
                         │
              ┌──────────┼──────────────┐
              │          │              │
              ▼          ▼              ▼
        ┌──────────┐ ┌────────┐  ┌──────────────┐
        │PostgreSQL│ │ Redis  │  │ Object Store │ [HC]
        │  :5432   │ │ :6379  │  │ (tenant-iso) │
        │  shared  │ │ cache  │  │ logos, docs  │
        │  schema  │ │ rate   │  │              │
        │  + RLS   │ │ limits │  │              │
        └──────────┘ └────────┘  └──────────────┘
```

**New containers [HC]:**
- **healthcare-module FastAPI :9002** — single FastAPI service hosting all healthcare
  sub-module routers; mounts at startup based on which sub-modules are active for each tenant.
  (Follows the platform pattern: financial-module is a single service on :9001.)
- **Object Store** — tenant-isolated blob storage for clinic logos, PDF invoices, lab result
  attachments. Not a new infrastructure component; a new usage pattern on existing storage.

**Database additions [HC]:**
- `patients` table (platform-level — patient universal profiles)
- `branches` table (per tenant — branch metadata)
- `branch_staff` table (user × branch × role assignments)
- `encounters` table (tenant + branch scoped, PHI)
- `appointments` table (`healthcare_scheduling`, tenant + branch scoped)
- `prescriptions` table (`healthcare_pharmacy`, tenant + branch scoped)
- `lab_orders`, `lab_results` tables (`healthcare_lab`, tenant + branch scoped)
- `invoices`, `invoice_items` tables (`healthcare_billing`, tenant + branch scoped)
- `audit_log` table (append-only, PP 71/2019 — platform-level)
- `consent_records` table (patient consent per purpose, UU PDP)

All PHI tables carry `(tenant_id, branch_id)` and are protected by PostgreSQL RLS policies
(ADR-HC-001).

---

## 4. Component Breakdown per Module

### 4.1 Base Module — `healthcare`

```
modules/healthcare/
  backend/
    app/
      routers/
        clinic_onboarding.py    # POST /clinics/register, PUT /tenants/:id/profile
        branches.py             # CRUD branches, staff assignment
        patients.py             # PHI CRUD, branch-scoped
        encounters.py           # SOAP notes, encounter lifecycle
        patient_portal.py       # Public: register, search, profile
        audit.py                # Admin: audit log query/export
        consent.py              # Patient consent management
        locale.py               # PUT /users/me/locale
      models/
        patient.py              # Patient (platform-level universal profile)
        encounter.py            # Encounter (tenant+branch scoped)
        branch.py               # Branch, BranchStaff
        audit_log.py            # Append-only audit log
        consent_record.py       # PDPA consent records
      migrations/               # Alembic — healthcare_alembic_version table
  sdk/
    __init__.py                 # Public exports for sub-modules
    branch_scope.py             # BranchScopeListener, healthcare_branch_session (ADR-HC-001)
    phi_audit.py                # write_phi_read_audit() (ADR-HC-002)
    patient_reader.py           # get_patient() DTO (ADR-HC-002)
    encounter_reader.py         # get_encounter() DTO (ADR-HC-002)
    locale.py                   # resolve_locale(), t() translation fn (ADR-HC-004)
  i18n/
    id-ID.json                  # Bahasa Indonesia (reference locale)
    en-US.json                  # English
    templates/                  # Notification templates (PHI-safe)
  frontend/
    i18n/                       # Frontend translation JSON
    components/                 # Clinic portal + patient portal UI
```

### 4.2 Scheduling Module — `healthcare_scheduling`

Provides online booking, provider calendars per branch, waitlist, patient reminders.

Key components:
- `routers/appointments.py` — book, confirm, cancel, reschedule
- `routers/calendars.py` — provider availability per branch
- `routers/waitlist.py` — waitlist management
- `services/reminder_service.py` — WhatsApp/SMS reminders via notification adapter
- `models/appointment.py`, `provider_calendar.py`, `waitlist_entry.py`
- Cross-module: uses `modules.healthcare.sdk.get_patient()` to resolve patient demographics
  at booking time (ADR-HC-002).

### 4.3 Billing Module — `healthcare_billing`

Encounter-to-invoice workflow, BPJS export, payment tracking.

Key components:
- `routers/invoices.py` — create/view/update invoices from encounters
- `routers/payments.py` — payment recording and status
- `routers/bpjs_export.py` — generate BPJS-compatible claim file (CSV/XML, versioned adapter)
- `adapters/bpjs_adapter_v1.py` — BPJS format adapter (versioned; isolated from business logic)
- Cross-module: uses `modules.healthcare.sdk.get_encounter()` for line item sourcing.
  Enriched by pharmacy (dispensed items) and lab (test charges) if active — graceful
  degradation if sub-modules absent.

### 4.4 Pharmacy Module — `healthcare_pharmacy`

Prescription management, medication catalog per branch, dispensing workflow.

Key components:
- `routers/prescriptions.py` — create/view/dispense prescriptions (linked to encounter)
- `routers/medication_catalog.py` — branch medication inventory CRUD
- `services/drug_interaction.py` — adapter interface to licensed drug database
- `adapters/drug_db_adapter.py` — abstract base; concrete implementations per DB provider
- Cross-module: `modules.healthcare.sdk.get_encounter()` to link prescription to encounter.

### 4.5 Laboratory Module — `healthcare_lab`

Lab test ordering, specimen tracking, result management, critical value alerts.

Key components:
- `routers/lab_orders.py` — create/view lab orders (linked to encounter)
- `routers/lab_results.py` — enter results, manage status, critical value flag
- `routers/specimen_tracking.py` — specimen chain of custody
- `services/critical_value_alert.py` — triggers notification on critical values
- Cross-module: `modules.healthcare.sdk.get_encounter()` and `get_patient()` to link orders.

---

## 5. Data Flows

### 5.1 Patient Booking Flow (End-to-End)

```
Patient Browser
    │
    │  1. GET /api/v1/clinics/search?lat=&lng=&specialty=
    │     (unauthenticated; Redis cache 60 s; no PHI)
    │
    │  2. GET /api/v1/clinics/:slug/branches/:branch_id/profile
    │     (unauthenticated; clinic name, hours, doctors name+specialty only)
    │
    │  [Patient not logged in → Registration Flow]
    │  3. POST /api/v1/patients/register (OTP verify → JWT issued)
    │
    │  [Patient authenticated]
    │  4. GET /api/v1/modules/healthcare/scheduling/branches/:branch_id/availability
    │     Header: Authorization: Bearer <patient_jwt>
    │     Returns: available slots for selected date + provider
    │
    │  5. POST /api/v1/modules/healthcare/scheduling/appointments
    │     Payload: { branch_id, provider_id, slot, appointment_type }
    │     Header: Authorization: Bearer <patient_jwt>
    │     │
    │     └─► healthcare_scheduling service:
    │           a. Validate slot availability (optimistic lock)
    │           b. Call modules.healthcare.sdk.get_patient(patient_id)
    │              → PHI audit log written (event_type="phi.read", source="scheduling")
    │           c. Create appointment record (tenant_id, branch_id, patient_id, provider_id)
    │           d. Emit appointment.created event → reminder_service queue
    │           e. Return 201 { appointment_id, confirmation_code }
    │
    │  6. reminder_service (APScheduler job):
    │     → Fetch PHI-safe template (id-ID or patient locale)
    │     → Send WhatsApp/SMS: clinic name + time only (no patient name, no diagnosis)
    │
    ▼
Patient Portal: confirmation screen with appointment details
```

### 5.2 PHI Audit Trail Flow

```
Any healthcare service call (staff or sub-module) that reads PHI:

  API Handler
      │
      │  Depends(healthcare_branch_session)          ← ADR-HC-001
      │    → validates X-Branch-ID header
      │    → sets app.tenant_id, app.branch_id in DB session
      │    → BranchScopeListener appends WHERE clause
      │
      ├─► Direct PHI read (staff portal):
      │    PHIAuditMiddleware (SQLAlchemy event hook)
      │    → write to audit_log:
      │       event_type="phi.read" | "phi.write"
      │       actor_id, tenant_id, branch_id, resource_type, resource_id
      │       timestamp=utcnow(), ip=request.client.host
      │
      └─► Cross-module PHI read (via SDK):
           modules.healthcare.sdk.get_patient() or get_encounter()
           → write_phi_read_audit() called INSIDE SDK function (ADR-HC-002)
              source_module = caller-declared (e.g. "healthcare_pharmacy")
           → return PatientReadDTO | EncounterReadDTO (read-only)

audit_log table:
  - Append-only (no UPDATE/DELETE at DB level, RLS policy)
  - Retention: 5 years (PP 71/2019)
  - Archival job: APScheduler, monthly batch to cold storage
  - Export: GET /api/v1/admin/audit-logs (platform admin, CSV)
```

---

## 6. Integration Points

### 6.1 WhatsApp / SMS Notification Adapter

- **Interface:** `modules/healthcare/sdk/notifications.py` — `NotificationAdapter` abstract base.
- **Implementations:** `WhatsAppBusinessAdapter`, `SMSFallbackAdapter` (concrete classes).
- **PHI constraint:** Template variables limited to `{{clinic_name}}`, `{{appointment_time}}`,
  `{{branch_address}}`, `{{otp_code}}`. Patient name, diagnosis, doctor name, and medication
  names are **prohibited** in message bodies (vision-02 risk: WhatsApp PHI leakage).
- **OTP delivery:** WhatsApp primary, SMS fallback (automatic on WhatsApp delivery failure).
- **Rate limit on OTP:** 5 attempts per phone per 10 min; 60-second cooldown between resends.

### 6.2 BPJS Export Adapter

- **Interface:** `modules/healthcare_billing/adapters/bpjs_adapter_base.py` — abstract `BPJSAdapter`.
- **Implementation:** `bpjs_adapter_v1.py` — generates BPJS Kesehatan-compatible CSV/XML claim
  file from invoice records. Format is versioned; adapter implementation is isolated from
  billing business logic so format changes require only a new adapter class, not model changes.
- **Not a live API:** File export only in v1. Live BPJS API submission is deferred (scope-out
  register item #3).
- **Export trigger:** `GET /api/v1/tenants/:tenant_id/branches/:branch_id/billing/bpjs-export?period=`
  — returns downloadable file; logged to audit trail.

### 6.3 Drug Interaction Adapter

- **Interface:** `modules/healthcare_pharmacy/adapters/drug_db_adapter.py` — abstract `DrugDBAdapter`
  with method `check_interactions(medication_ids: list[UUID]) -> list[InteractionWarning]`.
- **Implementation:** tenant-configured. Platform provides a `NullDrugDBAdapter` (returns empty
  list) as default; clinic tenants configure a licensed database (e.g. MIMS Indonesia API key)
  in their pharmacy module settings.
- **PHI constraint:** Drug names are clinical identifiers but not patient PHI. Adapter calls do
  not include patient_id; they receive only medication IDs from the branch catalog.

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Endpoint / Flow | Target (p95) | Notes |
|----------------|-------------|-------|
| `GET /api/v1/clinics/search` | < 300 ms | Redis cache 60 s; no PHI |
| `GET /api/v1/clinics/:slug/*/profile` | < 200 ms | Redis cache 5 min |
| Appointment booking (POST) | < 500 ms | Includes SDK PHI read + audit write |
| Encounter SOAP save (PUT) | < 300 ms | Auto-save every 30 s |
| Prescription creation | < 400 ms | Includes drug interaction check |
| Lab order creation | < 400 ms | Includes SDK PHI read |
| Audit log export (CSV) | < 10 s for 30-day range | Paginated; background job for large ranges |
| Patient portal registration (POST) | < 2 s end-to-end | Includes OTP send via WhatsApp |

Patient portal Lighthouse score: ≥ 80 on mid-range Android / 4G (vision-02 Story 1.4.1 AC).

### 7.2 Security

| Concern | Control |
|---------|---------|
| PHI at rest | PostgreSQL `pgcrypto` column-level encryption for `patients.nik`, `patients.dob`, encounter SOAP content. Tenant-isolated encryption keys. |
| PHI in transit | TLS 1.2+ enforced at Nginx gateway. No PHI in HTTP logs (IP only). |
| PHI in notifications | System-locked WhatsApp/SMS templates — no PHI allowed in body. |
| Branch isolation | 3-layer: ORM `BranchScopeListener` + DB RLS + header validation (ADR-HC-001). |
| Public endpoint abuse | hCaptcha + `slowapi` rate limits + OTP attempt limits (ADR-HC-003). |
| Patient JWT | Short-lived access tokens (15 min) + HttpOnly refresh cookie (7 days). |
| Cross-tenant data leak | Platform `TenantScopeListener` + healthcare `BranchScopeListener` in series. |
| Audit log integrity | Append-only table; `INSERT`-only grant at DB level; no `UPDATE`/`DELETE`. |
| PDPA consent | Consent version + timestamp + IP recorded; revocation triggers processing restriction workflow. |
| DPA acceptance gate | No PHI sub-module can activate without `tenant.dpa_accepted = true`. Enforced server-side. |
| No real PHI in dev/staging | Synthetic patient data tooling required before any clinical feature ships (vision-02 Guardrail 4). |

### 7.3 Observability

All observability follows the platform pattern (arch-00-platform) extended with healthcare-specific labels:

| Signal | Implementation | Healthcare additions |
|--------|---------------|---------------------|
| Structured logs | `structlog` JSON | `tenant_id`, `branch_id`, `module`, PHI access events (audit log is separate from application logs) |
| Metrics | Prometheus (optional) | `healthcare_phi_reads_total{module, resource_type}`, `healthcare_audit_writes_total`, `appointment_booking_duration_seconds` |
| Tracing | OpenTelemetry (future) | Span per SDK call; cross-module PHI read traces |
| Health check | `GET /health` (Nginx static) | Healthcare module: `GET /api/v1/modules/healthcare/health` → DB connectivity + Redis connectivity |
| Alerting | Sentry (optional) | PHI audit write failures → P1 alert (data loss risk) |

PHI data must never appear in application logs, Sentry payloads, or metrics labels. Log scrubbing middleware strips fields marked `phi=True` in the response model.

### 7.4 Multi-Tenancy

The healthcare module inherits the platform's shared-schema multi-tenancy model with the
additional branch dimension:

- Every PHI table carries `(tenant_id UUID NOT NULL, branch_id UUID NOT NULL)`.
- PostgreSQL RLS policies enforce `tenant_id` AND `branch_id` isolation at DB level.
- `clinic_owner` bypass: `branch_id = 'ALL'` sentinel in RLS (ADR-HC-001 §D4).
- Sub-module activation is per-tenant: `tenant_modules` table (`tenant_id × module_name × active`).
- DPA acceptance is per-tenant: `tenant.dpa_accepted BOOLEAN NOT NULL DEFAULT FALSE`.
- Drug DB adapter configuration is per-tenant: stored in `tenant_pharmacy_settings`.

### 7.5 Scalability

| Dimension | Approach |
|-----------|---------|
| Horizontal scaling | Healthcare module FastAPI service is stateless; scale replicas behind Nginx upstream. |
| Database | PostgreSQL; connection pooling via `asyncpg` or `psycopg3`. Partitioning of `audit_log` by `tenant_id` + month when table exceeds 100M rows. |
| Caching | Redis for: clinic search results (60 s TTL), branch public profiles (5 min TTL), OTP attempt counters, rate-limit state. |
| Background jobs | APScheduler (platform default): reminder dispatch, audit archival, BPJS export generation. |
| Read replicas | `audit_log` queries and CSV exports routed to a PostgreSQL read replica (reduces load on primary during compliance audits). |
| Multi-branch ceiling | 20 branches per tenant (platform-configurable); no architectural change needed up to ~200 branches. |

---

## 8. Risks

| Risk | Likelihood | Impact | Architectural Mitigation |
|------|-----------|--------|-------------------------|
| Branch isolation bug leaks PHI across branches | Low (3-layer enforcement) | Critical | ADR-HC-001: ORM listener + DB RLS + header validation; mandatory integration tests covering all three layers per PHI model. |
| Patient portal attack surface (registration abuse, scraping) | High | High | ADR-HC-003: hCaptcha + `slowapi` + OTP rate limits + no PHI in public responses; penetration test before GA. |
| i18n completeness gap at launch (missing translation keys) | Medium | Medium | ADR-HC-004: CI key-count check against reference locale (`id-ID`); `t()` function falls back to `en-US`, never raises. |
| BPJS format change invalidates export | Medium | Medium | Versioned adapter pattern (`bpjs_adapter_v1.py`); new format = new class, not model change. |
| PHI in WhatsApp/SMS messages | High (if unchecked) | High | System-locked templates; no clinic-customisable PHI fields; CI lint check on template variables. |
| Drug DB adapter not procured by tenant | High (at launch) | Low | `NullDrugDBAdapter` returns empty warnings; no prescription block; pharmacy still usable without external DB. |
| PP 71/2019 / UU PDP scope broader than anticipated | Medium | High | DPA acceptance gate; consent management built-in; legal counsel review pre-GA (pre-condition from research-02). |
| `audit_log` table growth (5-year retention) | Certain | Medium | Monthly archival APScheduler job; read replica for audit queries; table partitioning plan at 100M rows. |
| Synthetic data tooling absent at dev start | Medium | High | Must be built before first clinical feature (vision-02 Guardrail 4); block sprint-1 merge gate. |

---

## 9. Reference Map

| File | Role in this architecture |
|------|--------------------------|
| `plan/architecture/arch-platform.md` | Platform base architecture extended by this document |
| `plan/architecture/adr-006-sdk-surface-db-and-dependencies.md` | SDK isolation contract; `modules/healthcare/sdk/` follows same pattern |
| `modules/sdk/db.py` | `Base`, `GUID` — healthcare models inherit these |
| `modules/sdk/dependencies.py` | `tenant_scoped_session` — wrapped by `healthcare_branch_session` |
| `infra/nginx/nginx.conf` | Gateway routing — must be extended for `/patient/` and public clinic paths |
| `plan-mod-healthcare/vision/vision-02.md` | Product vision — guardrails, scope, risks |
| `plan-mod-healthcare/research/research-02.md` | Market research — personas, Indonesia compliance requirements |
| `plan-mod-healthcare/epics/epic-01-base-healthcare.md` | Base module stories — ACs drive API and data model design |
| `plan-mod-healthcare/BACKLOG.md` | Epic summary, dependency map, launch sequence |
| `plan-mod-healthcare/architecture/adr-hc-001.md` | Branch Isolation Strategy |
| `plan-mod-healthcare/architecture/adr-hc-002.md` | Cross-Module PHI Data Sharing |
| `plan-mod-healthcare/architecture/adr-hc-003.md` | Two-Sided Access Architecture |
| `plan-mod-healthcare/architecture/adr-hc-004.md` | i18n Architecture |

---

## 10. Hand-Off Notice to B2 (Backend Developer)

**From:** B1 Software Architect
**To:** B2 Backend Developer
**Date:** 2026-06-21

**Start here:**

1. **ADR-HC-001** — implement `modules/healthcare/sdk/branch_scope.py` first. This is the
   mandatory pre-condition for all PHI models. No data model story may merge without passing
   branch isolation integration tests (ORM + RLS + header).

2. **PHI data models** — `patients`, `encounters`, `branches`, `branch_staff` tables in
   `modules/healthcare/backend/app/models/`. All carry `(tenant_id, branch_id)` with `NOT NULL`
   constraints. Use `Base` and `GUID` from `modules/sdk/db.py`.

3. **Audit log table** — `audit_log` must be append-only at the DB grant level before any
   PHI endpoint ships. APScheduler archival job in the same sprint.

4. **Healthcare SDK** — `modules/healthcare/sdk/` must be importable by sub-modules before
   sub-module sprints begin. Expose `get_patient()`, `get_encounter()`, `write_phi_read_audit()`,
   `resolve_locale()`, `t()`.

5. **Patient auth** — `POST /api/v1/patients/register` and `/patients/auth/token` per ADR-HC-003.
   OTP via WhatsApp primary, SMS fallback. hCaptcha verification server-side.

6. **Linting gate extension** — extend `tools/lint/no_direct_backend_import.py` to also reject
   `from modules.healthcare.backend` imports in sub-module code.

7. **Synthetic data tooling** — must exist before first clinical endpoint ships (vision-02
   Guardrail 4). Block sprint-1 merge gate on this.

**Epic-06 (Telemedicine) is excluded from all implementation work.** Do not create any models,
routes, or migrations for `healthcare_telemedicine`. Await legal clearance.
