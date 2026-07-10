---
artifact_id: epic-20-saas-onboarding
status: active
version: 1
module: healthcare (primary), cross-module (platform org)
launch_phase: MVP
producer: A3 Product Owner (completed by manager after session-limit cutoff)
upstream: [adr-hc-010-saas-tenancy-and-patient-scoping, adr-hc-005 (Amendment v2), adr-hc-009 (Amendment v3), migration-plan-saas-tenancy-01, review-saas-tenancy-01]
created: 2026-07-06
---

# Epic 20 — SaaS Onboarding (Shared-Tenant, Company = Clinic Business)

**Module:** `healthcare` onboarding + platform org. Replaces the tenant-per-clinic signup with the
shared-tenant SaaS model.
**Launch Phase:** MVP (Features 20.1–20.4, 20.6 deep; 20.5 outline).

**Summary:** All clinics live in ONE shared platform **Tenant**. An owner self-registers as a
**Company** (the clinic business); each clinic **site is a Branch** under that Company (Company 1:N
Branch, each Branch 1:1 a platform Branch per ADR-HC-005). Patients are **Company-scoped** (ADR-HC-010);
staff and the `clinic_owner` role are **Company-anchored** (never SaaS-wide). The public portal resolves
a clinic by **Company/Branch slug** and the logged-out landing is a PHI-free **clinic chooser** listing
only Companies/Branches that opted into public visibility. A **dedicated Tenant** is a rare,
approval-gated exception for a multi-company owner wanting a consolidated cross-company view.

## Invariants (reused, not re-specified)
- Company isolation for patients via `hc_patients.company_id` + `app.company_id` RLS GUC, fail-closed, no
  `'ALL'` escape (ADR-HC-010). Branch isolation (adr-hc-001) unchanged for clinical tables.
- `clinic_owner` "all branches" bypass is anchored to the owner's Company (ADR-HC-010) — not the SaaS.
- PHI via SDK readers + audit (adr-hc-002). i18n id-ID default / en-US (adr-hc-004).
- **Confirmed decisions (user 2026-07-06):** `hc_patient_consents` is Company-scoped (defence-in-depth);
  the public clinic directory is **opt-in per Company** (`companies.public_listing`, default false).

---

## Feature 20.1 — Owner Signup & Company Creation

### Story 20.1.1 [OPEN]
**As a** prospective clinic owner,
**I want to** self-register and create my clinic business (Company) on the SaaS,
**so that** I can run one or more clinic sites without provisioning a separate tenant.

**Backend AC:**
- `POST /api/v1/healthcare/onboarding/company` — **NEW** (replaces the tenant-per-clinic
  `routes_clinic_signup.clinic_register`). Public + captcha + email verification. Creates: (1) a platform
  `companies` row under the shared SaaS `Tenant` (`code`/slug unique per tenant, contact,
  `public_listing=false` default); (2) the owner platform `User(role=patient?no → staff owner)` bound to
  the shared tenant + Company; (3) an `hc_branch_staff` **owner sentinel** row (`branch_id NULL`,
  `company_id = <new company>`, role `clinic_owner`) — Company-anchored per ADR-HC-010.
- Idempotent on `companies.code` within the shared tenant → 409 on duplicate slug.
- No new tenant is created (shared-tenant default). Emits `company.created` audit.
- **Architecture note for impl:** the shared `SAAS` tenant id is a config/seed constant
  (migration-plan Phase 0). The owner sentinel MUST carry `company_id` (schema-hc-04) so the owner is not
  a SaaS-wide super-owner.

**Frontend AC:**
- Route: `#/onboarding/company` (public). Wizard: account (email/password) → Company details (name, slug,
  contact, city) → first branch (optional, links to 20.2) → done.
- Slug availability check; `public_listing` toggle (default off) with a "list my clinic publicly" hint.

#### Frontend (UILDC v1.0)
- **Route:** `#/onboarding/company` · **Portal:** Admin/onboarding · **Layout:** desktop-first stepper.
- **Components:** `FlexStepper`; `FlexForm`/`FlexInput` (email, password, company name, slug, contact);
  `FlexToggle` (public_listing); `FlexAlert` (slug taken / success).
- **Key interactions:** slug live-check; submit → owner logged in, lands on the new Company dashboard.
- **i18n / Mobile:** translated; responsive. **Error:** duplicate slug + weak password inline.

---

## Feature 20.2 — Branch (Clinic Site) Management

### Story 20.2.1 [OPEN]
**As a** clinic owner,
**I want to** add and manage clinic sites (Branches) under my Company,
**so that** each physical location is bookable and staffed independently while sharing my patient registry.

**Backend AC:**
- `POST /api/v1/healthcare/companies/{company_id}/branches` — auth: `clinic_owner` of that Company.
  Creates a platform `branches` row under the Company + the linked `hc_branches` site row
  (`platform_company_id`, `platform_branch_id` set 1:1 per ADR-HC-005), with `online_booking` and a
  per-branch `public_visible` flag (gated by the Company `public_listing`).
- `GET/PUT` branch list/detail; branch updates emit `branch.updated` audit. All scoped to the caller's
  Company (deny cross-Company).
- **Architecture note for impl:** reuses the platform org API to create the `branches` row; healthcare
  records the resulting id in `hc_branches.platform_branch_id` (ADR-HC-005 D1).

**Frontend AC:**
- Route: `#/healthcare/branches` — list of sites; add/edit form (name, address, phone, online-booking,
  public-visible). Owner-only.

#### Frontend (UILDC v1.0)
- **Components:** `FlexTable` of branches; `FlexForm` add/edit; `FlexToggle` online-booking + public-visible.
- **i18n / Mobile / Error:** translated; responsive; cross-Company access blocked with a clear message.

---

## Feature 20.3 — Staff Onboarding within the Company

### Story 20.3.1 [OPEN]
**As a** clinic owner,
**I want to** invite staff and assign them to Branches with a role,
**so that** doctors/nurses/managers can operate only within my Company and their assigned sites.

**Backend AC:**
- `POST /api/v1/healthcare/companies/{company_id}/staff` — auth: `clinic_owner`. Creates the platform
  `User` (staff) + `hc_branch_staff` row (`company_id` set, `branch_id` = assigned site, HCRole). Roles
  (`branch_manager`, `doctor`, `nurse`, …) are **enumerated and gated within the Company** — no cross-
  Company staff visibility.
- Branch/staff enumeration endpoints are Company-fenced (ADR-HC-010 §clinic_owner fix).
- Emits `staff.invited` audit.

**Frontend AC:**
- Route: `#/healthcare/staff` — staff list + invite form (email, role, branch). Owner/branch-manager.

#### Frontend (UILDC v1.0)
- **Components:** `FlexTable` staff; `FlexForm` invite (`FlexSelect` role + branch); `FlexAlert`.
- **i18n / Mobile / Error:** translated; responsive; role/branch validation inline.

---

## Feature 20.4 — Portal Clinic Resolution & Logged-out Clinic Chooser

### Story 20.4.1 [OPEN]
**As a** visitor (logged out),
**I want to** choose which clinic's portal to enter,
**so that** I'm not defaulted to an arbitrary clinic (fixes: logged-out portal only showed one clinic).

**Backend AC:**
- `GET /api/v1/clinics` (public, PHI-free) — returns Companies/Branches with `public_listing=true` /
  `public_visible=true` only. The **single cross-Company public read surface**; PHI-free by construction.
- **Re-key** `routes_public._get_profile`, `clinic_search`, and slots resolution from **tenant code →
  Company (and Branch) slug**. `GET /api/v1/patients/me/clinic` returns the patient's **Company** slug
  (not tenant code).
- **Architecture note for impl:** this replaces the `slug = tenants.code` lookup with `companies.code`;
  logged-out default is the chooser, not a hardcoded clinic.

**Frontend AC:**
- Logged-out landing: a clinic chooser (search/list of opted-in clinics) → selecting one enters that
  clinic's portal (`?company=<slug>` / `?branch=`). Booking (epic-18/appointments) resolves to the chosen
  or the logged-in patient's Company.

#### Frontend (UILDC v1.0)
- **Route:** `/portal/healthcare/` (chooser) · **Components:** `FlexSearch` + `FlexCard` list of clinics.
- **Key interactions:** pick clinic → portal home for that Company/Branch. Logged-in patient auto-scoped
  to their Company (via `/me/clinic`). **i18n / Mobile:** translated; mobile-first chooser.

---

## Feature 20.5 — Dedicated-Tenant Request (Outline)

### Story 20.5.1 [OPEN — outline]
**As a** multi-company owner needing a consolidated cross-company view (rare),
**I want to** request my own exclusive Tenant,
**so that** all my Companies live under one tenant I can view together.

- `POST /api/v1/healthcare/onboarding/dedicated-tenant-request` — captures the request (company list,
  justification); **approval-gated, out-of-band/manual** provisioning. No `hc_*` schema differs
  (ADR-HC-005 A4). Admin approval workflow + audit. (Outline: header + one-line ACs; deep design deferred.)

---

## Feature 20.6 — Patient Registration under a Company (Company-scoped)

### Story 20.6.1 [OPEN]
**As a** patient (or an account holder registering a dependent),
**I want** my record created under the clinic's Company,
**so that** my PHI is shared across that Company's sites but never leaks to other Companies.

**Backend AC:**
- Patient registration (self + proxy-dependent, epic-18) **stamps `hc_patients.company_id`** = the
  Company of the clinic being registered at (resolved from the branch/site → Company). `from-platform`
  bridge + `me/*` reads are Company-fenced (ADR-HC-010).
- `hc_patient_consents` rows carry **`company_id`** (re-keyed per confirmation) + the existing
  `basis`/`consented_by_user_id` (proxy consent, ADR-HC-009).
- Cross-Company register/link is rejected **422 `cross_company`** (household within one Company, ADR-HC-009
  Amendment v3).
- **Architecture note for impl:** registration must resolve Company from the active clinic context;
  household/proxy guards change same-tenant → same-Company.

**Frontend AC:**
- Registration/booking always operate within the active Company; the household "add dependent"/"link"
  flows show the Company context and reject cross-Company targets with a clear message.

#### Frontend (UILDC v1.0)
- **Components:** existing registration/household forms + a Company-context banner; `FlexAlert` on
  cross-Company attempts. **i18n / Mobile / Error:** translated; mobile-first; `cross_company` message.

---

## Story Count: 20.1 (1) + 20.2 (1) + 20.3 (1) + 20.4 (1) + 20.5 (1, outline) + 20.6 (1) = **6 stories**

---

## Notes for implementation (backend/endpoint changes this epic implies)
1. **Company signup endpoint** `POST /api/v1/healthcare/onboarding/company` replacing tenant-per-clinic
   `routes_clinic_signup.clinic_register`; owner sentinel row carries `company_id`.
2. **Branch/staff endpoints** Company-scoped; owner/staff enumeration Company-fenced.
3. **Portal re-key**: `routes_public` (`_get_profile`, `clinic_search`, slots) + `/me/clinic` from
   `tenants.code` → `companies.code`; new PHI-free `GET /api/v1/clinics` directory (opt-in only).
4. **Patient registration** stamps `company_id`; `hc_patient_consents` gains `company_id`; household guards
   same-tenant → same-Company (`routes_household.py`).
5. **Config/seed**: the shared `SAAS` tenant id (migration-plan Phase 0). All of the above land AFTER the
   ADR-HC-010 patient-scoping schema + RLS (migration-plan Phases 1–4).
