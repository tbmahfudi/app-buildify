---
artifact_id: BACKLOG
version: 3
status: active
producer: A3 Product Owner (manager-authored anchor)
upstream: vision-02, research-02, BACKLOG v2, redesign-clinic-management-2026-07
supersedes: BACKLOG v2
created: 2026-07-02
---

# Healthcare Module Suite — Product Backlog v3

**Supersedes:** BACKLOG v2 (2026-06-21). v2's epics 01-07 remain valid and are **kept as-is** (with small
addenda noted below); v3 **restructures the backlog around the full 20-module Clinic Management System
spec**, adds a Reuse Register for cross-cutting platform capabilities, and appends new epics 08-17 + 19 to
close the gaps.

**Redesign decisions (approved 2026-07-02):**
1. Deliverable = redesigned epics/stories **+ new ADRs + DB schema** for new domains (design, not code).
2. Depth = **MVP gaps deep**; later releases at **epic-outline** level.
3. Org = keep `hc_branches`, **add `hc_departments`**, and **link `hc_branches` to the platform
   Company/Branch/Department** (a clinic **is** a platform branch; everything under a Tenant; a dedicated
   tenant only on explicit request). Healthcare-side change only.
4. Finance = **billing/invoicing only — defer GL/AR** (no Financial-microservice wiring this pass).

**SaaS tenancy (2026-07-06, under review — see `architecture/review-saas-tenancy-01.md`):** the product
is moving to a **shared-tenant SaaS** model — **ALL clinics live in ONE shared platform Tenant**; an owner
registers as a **Company** and each clinic **site is a Branch** (Company 1:N Branch); a **dedicated Tenant**
is the rare exception, only for a multi-company owner wanting a consolidated cross-company view. This flips
decision #3's default (single shared tenant, not tenant-per-clinic). **Critical open item:** `hc_patients`
is tenant-scoped, so one shared tenant would pool every clinic's patients — the review recommends
**Company-scoped patient records** (branch-shared within a Company, isolated between Companies) and hands
the enforcement, household-Q2 re-scope, portal Company/Branch resolution, and MedCare/HealthPoint migration
to B1. Backlog impact (ADR-HC-005 default flip, ADR-HC-009 Q2 re-frame, ADR-HC-001 patient RLS, epic-08,
a new company-signup onboarding epic) is enumerated in the review.

---

## Guiding principle — reuse the platform, build only the clinical domain

Of the 20 spec modules, **~9 are cross-cutting platform capabilities that already exist** and MUST be
reused, not rebuilt in healthcare. Healthcare only adds thin adapters/seeds for these. The remaining
modules are the clinical domain that healthcare owns.

### Reuse Register (cross-cutting spec modules → existing platform capability)

| Spec module | Platform capability (reuse) | Key path | HC adapter/seed needed |
|-------------|-----------------------------|----------|------------------------|
| 1 Authentication | JWT access/refresh, password reset/change, lockout, session timeout, OTP transport | `backend/app/routers/auth.py`, `core/auth.py`, `/api/v1/otp` | Patient portal 3-method auth (email/username+password, Google OAuth, OTP) — **EXTEND, see epic-18**. Reuse platform password/JWT/reset/lockout/session + patient `from-platform` bridge. **ADD to platform: Google OAuth + a generic MFA/second-factor framework.** *Note: OTP is now an **optional** MFA second factor / passwordless option — no longer the mandatory/only mechanism; supersedes ADR-HC-003 §D1.* |
| 2 User Management | User CRUD, settings, verification, multi-company access | `backend/app/routers/auth.py`, `org.py`, `models/user.py` | Staff mapped via `hc_branch_staff` (exists) |
| 3 Role & Permission | RBAC roles/permissions/groups, permission matrix, effective perms | `backend/app/routers/rbac.py`, `models/{role,permission,group}.py` | `hc_permissions.py` role seeds (exists) |
| — Sessions & Devices | Active sessions, device mgmt, revocation, concurrent-limit | `backend/app/core/session_manager.py`, `models/user_session.py` | None |
| 6 Audit & Logging | Change/login/access audit with JSON diff | `backend/app/routers/audit.py`, `core/audit.py` | + existing `hc_audit_log` (PHI, append-only) |
| 7 Notification (transport) | Queue + worker, email/SMS/webhook/push, templates | `backend/app/core/notification_service.py`, `workers/notification_worker.py` | HC templates → **epic-13** |
| 15 Reports (engine) | Report designer, query builder, CSV/Excel/PDF, scheduled | `backend/app/routers/reports.py`, `services/report_service.py` | HC datasets/templates → **epic-12** |
| 16 Dashboard (engine) | Dashboard designer, widgets, sharing, snapshots | `backend/app/routers/dashboards.py`, `services/dashboard_service.py` | HC widgets → **epic-12** |
| 5/18 Master Data | No-code entities, fields, relationships, lookups, org-scoping | `backend/app/routers/data_model.py`, `lookups.py`, `/api/v1/dynamic_data` | ICD/drug/test/insurer catalogs → **epic-10** (ICD) + adapters |
| — Scheduler | APScheduler cron/interval jobs, execution logs | `backend/app/routers/scheduler.py`, `services/scheduler_engine.py` | Reminder jobs (reuse for epic-13) |
| — Org hierarchy | Tenant→Company→Branch→Department | `backend/app/routers/org.py`, `models/{tenant,company,branch,department}.py` | Link from `hc_branches` → **epic-08** |
| 14 Finance/Accounting (GL/AR) | Financial microservice — COA/GL/AR/invoices/tax @ :9001 | `modules/financial/backend/` | **DEFERRED** this pass (billing-only) |

> **Do not write healthcare epics that re-specify any Reuse-Register capability.** Those are integration
> points, captured here and referenced from clinical epics — not new backlog work.

---

## 20-module disposition map

| # | Spec module | Disposition | Status | Release | This pass |
|---|-------------|-------------|--------|---------|-----------|
| 1 | Authentication | REUSE platform; **EXTEND for patient portal auth (epic-18)** | Full (staff) / Partial (patient portal) | MVP | Reuse Register + **epic-18 / superseding ADR (B1)** |
| 2 | User Management | REUSE platform | Full | MVP | Reuse Register |
| 3 | Role & Permission | REUSE platform + `hc_permissions` | Full | MVP | Reuse Register |
| 4 | Organization (Clinic/Branch/**Dept**) | EXTEND: link platform org + `hc_departments` | Partial | MVP | **DEEP — epic-08 / ADR-HC-005 / schema-hc-02** |
| 5 | Master Data | REUSE no-code entities + HC adapters | Partial | MVP/R2 | ICD deep (epic-10); rest outline |
| 6 | Audit & Logging | REUSE platform + `hc_audit_log` | Full | MVP | Reuse Register |
| 7 | Notification | REUSE platform + HC templates | Partial | R2 | **DEEP — epic-13** |
| — | Human Resource (Employee/Doctor/Nurse) | EXTEND `hc_providers`/`hc_branch_staff` | Partial | MVP | **DEEP — epic-11** |
| — | Patient (registration/info/history) | EXISTS (epic-01) | Full | MVP | Reference + history addendum |
| — | Appointment (booking/calendar/reminder) | EXISTS (epic-02) | Full | MVP | Reference |
| — | Registration/Visit + **Queue** | NEW | Absent | MVP | **DEEP — epic-09 / ADR-HC-006 / schema-hc-02** |
| — | EMR (SOAP + **ICD-10/ICD-9-CM** + notes) | EXTEND encounters | Partial | MVP | **DEEP — epic-10 / ADR-HC-007 / schema-hc-02** |
| — | Pharmacy | EXISTS (epic-04) + gaps | Full/Partial | R2 | **DEEP addendum** |
| — | Laboratory | EXISTS (epic-05) + gaps | Full/Partial | R2 | **DEEP addendum** |
| — | Radiology / Imaging | NEW | Absent | R3 | Outline — epic-14 |
| — | Billing (charges/invoice/payment) | EXISTS (epic-03) | Full | MVP | Reference (GL/AR deferred) |
| — | Insurance (eligibility/claim) | EXTEND (BPJS export exists) | Partial | R3 | Outline — epic-15 |
| — | Inventory (purchasing/warehouse) | EXTEND (drug stock exists) | Partial | R3 | Outline — epic-16 |
| — | Finance/Accounting (GL/AR) | **DEFERRED** (Financial svc later) | Absent (HC) | R3 | Scope-out (noted) |
| 15 | Reports | REUSE engine + HC datasets | Absent (HC) | MVP | **DEEP — epic-12 / ADR-HC-008** |
| 16 | Dashboard | REUSE engine + HC widgets | Partial | MVP/R3 | **DEEP — epic-12** |
| 17 | Communication (WA/Email/SMS) | REUSE + HC (folded into Notification) | Partial | R2 | **DEEP — epic-13** |
| 18 | System Administration | REUSE no-code + HC settings | Partial | MVP/R2 | Outline |
| 19 | Audit & Compliance | EXISTS (`hc_audit_log`, DPA, consent) | Full | MVP | Reference |
| 20 | Integration (govt/pay/SMS/WA/LIS/PACS) | NEW adapters | Partial | R3+ | Outline — epic-17 |
| — | Telemedicine | EXISTS (epic-06, legal gate) | Planned | R4 | Reference (unchanged) |

---

## Epic Summary Table

| Epic | Title | Module | Launch/Release | Stories | Depth | Status |
|------|-------|--------|----------------|---------|-------|--------|
| epic-01-base-healthcare | Base Healthcare Module | `healthcare` | GA / MVP | 14 | done-spec | OPEN |
| epic-02-scheduling | Scheduling Module | `healthcare_scheduling` | GA / MVP | 8 | done-spec | OPEN |
| epic-03-billing | Billing Module | `healthcare_billing` | R-MVP | 7 | done-spec | OPEN |
| epic-04-pharmacy | Pharmacy Module (+R2 addendum) | `healthcare_pharmacy` | R2 | 6 (+addendum) | deep addendum | OPEN |
| epic-05-laboratory | Laboratory Module (+R2 addendum) | `healthcare_lab` | R2 | 6 (+addendum) | deep addendum | OPEN |
| epic-06-telemedicine | Telemedicine Module | `healthcare_telemedicine` | R4 (legal gate) | 4 | outline | OPEN |
| epic-07-patient-portal | Patient Portal | cross-module | GA + progressive | 6 | done-spec | OPEN |
| **epic-18-patient-portal-authentication** | Patient Portal Authentication (email/username+password, Google OAuth, optional OTP-MFA) | `healthcare` + platform | MVP | 11 | **DEEP** | NEW |
| **epic-08-organization-departments** | Organization: Departments & Platform-Org Linkage (clinic site = platform Branch, 1:1; platform Dept vs clinical `hc_departments` disambiguated) | `healthcare` | MVP | 10 (v2) | **DEEP** | NEW |
| **epic-09-visit-registration-queue** | Visit Registration & Queue Management | `healthcare_registration` | MVP | ~9 | **DEEP** | NEW |
| **epic-10-emr-clinical-coding** | EMR Clinical Coding & Notes (ICD-10/ICD-9-CM) | `healthcare_emr` | MVP | ~8 | **DEEP** | NEW |
| **epic-11-human-resource** | Human Resource: Employee / Doctor / Nurse | `healthcare_hr` | MVP | ~8 | **DEEP** | NEW |
| **epic-12-reporting-dashboard** | Healthcare Reporting & Executive Dashboard | `healthcare_reporting` | MVP | ~9 | **DEEP** | NEW |
| **epic-13-communications** | Communications & Notifications | `healthcare_comms` | R2 | ~7 | **DEEP** | NEW |
| epic-14-radiology | Radiology / Imaging | `healthcare_radiology` | R3 | ~8 | outline | NEW |
| epic-15-insurance-claims | Insurance Eligibility & Claims | `healthcare_insurance` | R3 | ~7 | outline | NEW |
| epic-16-inventory | Inventory: Purchasing & Warehouse | `healthcare_inventory` | R3 | ~6 | outline | NEW |
| epic-17-integrations | External Integrations (pay/SMS/WA/LIS/PACS/govt) | `healthcare_integration` | R3+ | ~10 | outline | NEW |
| epic-19-analytics-bi | Multi-clinic Analytics / BI / Data Warehouse | cross-module | R5 | ~6 | outline | NEW |
| epic-20-saas-onboarding | SaaS Onboarding (shared-tenant; owner=Company, site=Branch; Company-scoped patients) | `healthcare` + platform org | MVP | 6 | deep (20.5 outline) | NEW |

> **SaaS tenancy pivot (2026-07-06):** shared-tenant SaaS model ratified — one shared Tenant; owner=Company; clinic site=Branch; patients Company-scoped; households within a Company; dedicated Tenant only on request. See `architecture/review-saas-tenancy-01.md`, `adr-hc-010-saas-tenancy-and-patient-scoping.md`, `migration-plan-saas-tenancy-01.md`, and epic-20.

---

## Release mapping (reconciled with the user's release plan)

| Release | Spec target | Covered by |
|---------|-------------|-----------|
| **MVP (3–4 mo)** | Auth, Organization, Patient Registration, Appointment, Queue, EMR (basic SOAP), Billing, Reports | Reuse(Auth) + **epic-18** (patient portal auth: password/Google/optional-OTP-MFA) + epic-08 (Org/Dept) + epic-01 (Patient) + epic-02 (Appointment) + **epic-09** (Queue) + epic-01/**epic-10** (EMR+coding) + epic-03 (Billing) + **epic-12** (Reports) + **epic-11** (HR, enabling) |
| **R2** | Pharmacy, Laboratory, Inventory, Notifications | epic-04 (+addendum), epic-05 (+addendum), epic-16 (outline), **epic-13** |
| **R3** | Radiology, Insurance Claims, Accounting, Executive Dashboards | epic-14, epic-15, Finance(deferred→Financial svc), epic-12 (exec dashboard shipped MVP; advanced R3) |
| **R4** | Mobile, Patient Portal, Telemedicine, AI | epic-07 (portal already built at GA; **portal *authentication* is epic-18 at MVP**), epic-06 (telemedicine) |
| **R5** | Multi-clinic analytics, BI, workflow automation, external integrations, data warehouse | epic-19, epic-17 |

> **Deviation note:** the existing build front-ran the user's ordering — **Patient Portal (epic-07)** and
> **Scheduling (epic-02)** already ship at GA/MVP, not R4. They are kept as delivered; the release table
> above reflects *where new work lands*, not a re-sequencing of shipped features.

---

## Cross-Epic Dependency Map (v3 additions)

```
epic-01-base-healthcare (required by ALL)
  ├─► epic-08-organization-departments   (MVP; departments used by epic-09 routing, epic-11 assignment,
  │        epic-12 dept-scoped reports)
  ├─► epic-02-scheduling
  ├─► epic-09-visit-registration-queue    (MVP; check-in consumes appointment (epic-02) OR walk-in;
  │        emits the encounter that epic-10 codes; queue routes by department (epic-08))
  ├─► epic-10-emr-clinical-coding         (MVP; diagnoses/procedures/notes attach to encounter from base;
  │        ICD catalogs via platform master-data)
  ├─► epic-11-human-resource              (MVP; doctor/nurse profiles enrich providers used everywhere)
  ├─► epic-12-reporting-dashboard         (MVP; read-only datasets over base + sub-modules via platform
  │        Reports/Dashboards engine)
  ├─► epic-03-billing ─► epic-15-insurance-claims (R3)
  ├─► epic-04-pharmacy ─► epic-16-inventory (R3)
  ├─► epic-05-laboratory ─► epic-14-radiology (R3, parallel pattern)
  ├─► epic-13-communications              (R2; reuses platform notification transport + scheduler)
  ├─► epic-18-patient-portal-authentication (MVP; depends on PLATFORM auth: password/JWT/reset/lockout/
  │        session + OTP transport; ADDs platform Google OAuth + generic MFA framework; canonical seam is
  │        the existing `from-platform` bridge. Blocks nothing critical — it gates portal *sign-in* for
  │        epic-07's PHI routes. Superseding ADR + schema authored by B1; supersedes ADR-HC-003 §D1.)
  └─► epic-07-patient-portal / epic-06-telemedicine / epic-17 / epic-19
```

---

## Scope-Out Register (v3 — inherits v2, adds finance/imaging notes)

Inherits all 10 items from v2 (full EHR/HIS, live SATUSEHAT, live BPJS API, diagnostic AI, native mobile,
drug-DB bundling, cross-platform identity, inpatient/ward, live P2KB verification, WA free-form PHI).

**Added in v3:**
| # | Item | Rationale | Revisit |
|---|------|-----------|---------|
| 11 | **GL / AR / double-entry accounting inside healthcare** | Reuse the platform Financial microservice (:9001) later; billing-only this pass | R3 |
| 12 | **PACS image storage/DICOM viewer bundling** | Radiology module provides an adapter/report workflow; image storage/viewer is a per-tenant procurement/integration item | epic-17 / per tenant |
| 13 | **ICD-10 / ICD-9-CM code data bundling** | Codes loaded as platform master-data per tenant; module ships the schema + adapter, not the licensed dataset | Per tenant |

---

## Hand-off Notice

**From:** Manager (redesign anchor)  **To:** A3 Product Owner, B1 Backend Architect  **Date:** 2026-07-02

**A3 Product Owner — author (follow the epic-01 format: Feature → Story with Backend-AC + Frontend-AC +
UILDC; frontmatter `artifact_id/status: active/version: 1/module/launch_phase/producer/upstream/created`):**
- Deep: `epics/epic-08-organization-departments.md`, `epic-09-visit-registration-queue.md`,
  `epic-10-emr-clinical-coding.md`, `epic-11-human-resource.md`, `epic-12-reporting-dashboard.md`,
  `epic-13-communications.md`
- Addenda (append a `## R2 Gap Addendum` section): `epic-04-pharmacy.md`, `epic-05-laboratory.md`
- Outline (epic header + one-line story list): `epic-14-radiology.md`, `epic-15-insurance-claims.md`,
  `epic-16-inventory.md`, `epic-17-integrations.md`, `epic-19-analytics-bi.md`

**B1 Backend Architect — author (follow the adr-hc-001 / schema-hc-01 format; conform to
adr-hc-001 branch isolation, adr-hc-002 PHI-via-SDK-readers+audit, adr-hc-003 two-sided auth,
adr-hc-004 i18n):**
- `architecture/adr-hc-005-org-linkage-departments.md`
- `architecture/adr-hc-006-visit-queue.md`
- `architecture/adr-hc-007-clinical-coding.md`
- `architecture/adr-hc-008-reporting-integration.md`
- `architecture/schema-hc-02.md`

**Canonical names (use verbatim across epics + schema for consistency):**
- Org: `hc_branches` gains `platform_company_id`, `platform_branch_id`, `platform_department_id` (nullable);
  new `hc_departments` (id, tenant_id, branch_id, code, name, kind ∈ {medical, pharmacy, laboratory,
  radiology, administration, finance}, is_active).
- Visit/Queue: `hcr_visits` (id, tenant_id, branch_id, patient_id, appointment_id nullable, visit_type
  ∈ {appointment, walk_in}, payment_category, insurance_profile_id nullable, referral_source, department_id,
  status, checked_in_at, encounter_id nullable), `hcr_queue_tickets` (id, tenant_id, branch_id, visit_id,
  department_id, ticket_number, station, status ∈ {waiting, called, skipped, recalled, transferred, served},
  called_at, served_at).
- EMR coding: `hc_diagnoses` (id, tenant_id, encounter_id, icd10_code, is_primary, sequence),
  `hc_procedures` (id, tenant_id, encounter_id, icd9cm_code, note), `hc_clinical_notes` (id, tenant_id,
  encounter_id, note_type ∈ {progress, nursing, observation, follow_up}, body[PHI-encrypted], author_id).
- Code catalogs: `hc_icd10_codes`, `hc_icd9cm_codes` (adapter-loaded per tenant) OR platform no-code
  entities — ADR-HC-007 decides and documents the choice.
- Reporting: read-only views `v_hc_daily_patients`, `v_hc_doctor_productivity`, `v_hc_queue`,
  `v_hc_appointments`, `v_hc_revenue`, `v_hc_disease_stats`, `v_hc_drug_usage`, `v_hc_lab_utilization`
  (no raw PHI columns; branch/tenant scoped).

**Invariants for every new table:** `tenant_id` + (branch-scoped where applicable) `branch_id`; RLS policy per
`schema-hc-01`; PHI columns encrypted via `EncryptedPHIType`; access through SDK readers with audit.
