---
type: tasks
status: review
upstream: [arch-hc-01, schema-hc-01, epic-01-base-healthcare, epic-02-scheduling, epic-03-billing, epic-04-pharmacy, epic-05-laboratory, epic-07-patient-portal]
producer: C1 Tech Lead / Scrum Master
created: 2026-06-21
---

# Healthcare Module Suite — Sprint Backlog

**Produced by:** C1 Tech Lead / Scrum Master
**Date:** 2026-06-21
**Scope:** Epics 01–05 and 07. Epic-06 (Telemedicine) excluded — pending legal gate (Permenkes No. 20/2019).
**Sprint duration:** 2 weeks per sprint

---

## B3 Open Questions — C1 Decisions

### Q2 [RESOLVED by C1] — Cross-Branch View for Branch Managers in v1

**Question:** Should Branch Managers be able to see data across multiple assigned branches from a single view, or is the UI strictly single-branch?

**C1 Decision:** Branch-scoped only in v1. The UI never offers a cross-branch aggregation view for Branch Managers. The `X-Branch-ID` header is always required; the branch context switcher (a dropdown in the clinic portal header) lets a manager switch between their assigned branches — one at a time. No cross-branch read in a single screen.

**Task owner for branch-switcher UI:** C5 (module frontend).
**Task reference:** T-HC-010 (branch CRUD API — Sprint 1) and T-HC-035/T-HC-040 (branch context badge in clinic portal UI — Sprint 4).

**Rationale:** Consistent with ADR-HC-001 §D3 (Branch Manager access = assigned branches only, one at a time) and vision-02 Guardrail 1 (PHI isolation). Cross-branch continuity deferred to a future phase requiring explicit patient consent architecture.

---

### Q4 [RESOLVED by C1] — Notification Template Locale

**Question:** Should notification templates (WhatsApp/SMS, email) use the patient locale, the clinic default locale, or the tenant default?

**C1 Decision:** i18n key system, consistent with ADR-HC-004. Resolution order for notification templates:
1. Patient profile locale (from `hc_patients.locale`)
2. Tenant default locale (`tenants.default_locale`)
3. Platform default (`id-ID`)

The notification service resolves locale at send time using `resolve_locale(patient=patient, tenant=tenant)` from `modules/healthcare/sdk/locale.py`. The Branch Manager notification template preview panel (Story 2.3.1 AC) shows a translated preview toggled by a locale selector (id-ID / en-US). The toggle calls the same translation key system — no special-cased template strings.

**Rationale:** Consistent with ADR-HC-004 §D2 locale resolution chain; ensures patients receive notifications in their preferred language regardless of the clinic default.

---

### Q1 [DEFERRED to A3] — Multi-Clinic Patient Identity Federation

**Question:** In v1, is a patient identity shared across tenants (platform-global patient UUID) or per-tenant?

**Status:** Deferred — requires product decision on cross-clinic patient linkage. Has regulatory implications (UU PDP No. 27/2022 cross-provider consent). A3 to produce decision document before Sprint 2 start.

---

### Q3 [DEFERRED to A3] — BPJS Live API vs. File Export Timeline

**Question:** Is the BPJS Kesehatan live API integration on the roadmap for v1, or is file export final?

**Status:** Deferred — BACKLOG.md Scope-Out Register item #3 states file export only in v1. A3 to confirm whether v2 target date is known. No v1 sprint work blocked by this question.

---

### Q5 [DEFERRED to A3] — Drug Database Licensing

**Question:** Which drug database vendor (MIMS Indonesia or alternative) is selected for the pharmacy drug interaction adapter?

**Status:** Deferred — BACKLOG.md Scope-Out Register item #6: licensed drug DB is a third-party procurement item. A3 to confirm vendor before Sprint 7 start. The adapter interface in T-HC-059 proceeds without a specific vendor — the adapter pattern decouples implementation from vendor choice.

---

## Sprint 0 — Platform Prerequisites

**Sprint Goal:** Deliver the platform-level infrastructure (patient auth, i18n, branch isolation, PHI encryption) that every subsequent sprint depends on. No module-specific code. C2 and C3 only.

**Blocker note:** Nothing in Sprints 1–8 may begin until T-HC-001 through T-HC-008 are merged and verified. T-HC-005 (PHI encryption helper) is a HARD production blocker — Wave 1 migration cannot go to production without it.

| ID | Story Ref | Description | Owner | Effort | Depends-on |
|----|-----------|-------------|-------|--------|------------|
| T-HC-001 | ADR-HC-003 | Implement patient role namespace: new `get_current_patient` FastAPI dependency in `modules/healthcare/sdk/`; patient JWT claims `{ sub: patient_id, roles: ["patient"], tenant_id: null }`; validate in `has_permission` that patient JWT is rejected on clinic-staff endpoints; integration tests patient JWT vs staff endpoints | C2 | M | — |
| T-HC-002 | ADR-HC-003, Story 1.4.1 | OTP flow for patient auth: `POST /api/v1/patients/auth/otp/send` and `POST /api/v1/patients/auth/otp/verify`; phone-based OTP generation (6-digit, 10-min TTL); 5-attempts/phone/10-min rate limit; 60-second resend cooldown; Redis-backed OTP store with TTL; consistent error shape (prevent enumeration) | C2 | M | T-HC-001 |
| T-HC-003 | ADR-HC-003 | hCaptcha server-side verification adapter: verify captcha token on patient registration and OTP-send endpoints before OTP dispatch; adapter pattern (env-var `HCAPTCHA_SECRET_KEY`; replaceable with Cloudflare Turnstile); reject registration with 422 if token invalid; mock bypass for test environments | C2 | S | T-HC-002 |
| T-HC-004 | ADR-HC-004 | Backend i18n framework: implement `t(locale, key, **kwargs)` in `modules/healthcare/sdk/locale.py`; `resolve_locale(request, current_user, tenant)` utility; load JSON translation files at module startup; fallback chain id-ID -> en-US -> key name (never raises KeyError); localised Pydantic validation error handler; create `modules/healthcare/i18n/id-ID.json` and `en-US.json` with common validation and audit key set | C2 | M | — |
| T-HC-005 | ADR-HC-002, migration-plan §Wave 1 | PHI column encryption helper: AES-256 at-rest encryption via `sqlalchemy-utils EncryptedType` (or equivalent); `PHI_ENCRYPTION_KEY` env-var; helpers in `modules/healthcare/sdk/phi_crypto.py`; applied to `hc_patients` PHI columns (full_name, date_of_birth, phone, email, nik, address); integration test confirms ciphertext in DB, plaintext returned on ORM read; HARD production blocker for Wave 1 | C2 | L | T-HC-001 |
| T-HC-006 | ADR-HC-001 | BranchScopeListener ORM hook: SQLAlchemy `SessionEvents.do_orm_execute` hook in `modules/healthcare/sdk/branch_scope.py`; `healthcare_branch_session` FastAPI dependency validates `X-Branch-ID` header, verifies caller has `hc_branch_staff` record, sets `SET LOCAL app.tenant_id` and `SET LOCAL app.branch_id` PostgreSQL session variables; raises HTTP 422 on missing header; clinic_owner bypass (`app.branch_id = 'ALL'`) | C2 | L | T-HC-001 |
| T-HC-007 | ADR-HC-001 §D4, migration-plan | PostgreSQL RLS policy framework: raw SQL RLS policies for all PHI tables (hc_patients tenant-only; hc_encounters, hcs_appointments, hcb_invoices, hcb_insurance_profiles, hcp_prescriptions, hcp_dispensing_log, hcl_test_orders, hcl_results branch-scoped); clinic_owner bypass sentinel; three-layer integration tests (ORM listener + RLS + header validation) for each scoped model | C2 | L | T-HC-006 |
| T-HC-008 | ADR-HC-004 | Frontend i18n wiring: integrate `i18next` into clinic portal and patient portal static JS bundles; locale switcher dropdown (header, both portals, id-ID / en-US); `i18next.changeLanguage()` flow; dynamic JSON fetch from `/modules/healthcare/i18n/{{locale}}.json`; `data-i18n` DOM observer; `PUT /api/v1/users/me/locale` persistence; localStorage fallback; zero hardcoded strings CI linting gate | C3 | M | T-HC-004 |

**Sprint 0 Risks:**
- T-HC-005 (PHI encryption): key management in dev/staging must be confirmed before first PHI write. Encryption key rotation strategy not yet in an ADR — flag to B1.
- T-HC-007 (RLS): requires `alembic_admin` role with `BYPASSRLS` confirmed in all target environments before migration run.
- T-HC-003 (hCaptcha): free-tier rate limits may constrain automated test runs — mock bypass mandatory in CI.

---

## Sprint 1 — Base Module Foundation

**Sprint Goal:** Establish all Wave 1 database migrations, branch management APIs, provider CRUD, RBAC, audit log, and the Healthcare Internal SDK. C4 builds on Sprint 0 platform primitives.

**Prerequisite:** Sprint 0 fully merged (T-HC-001 through T-HC-008).

| ID | Story Ref | Description | Owner | Effort | Depends-on |
|----|-----------|-------------|-------|--------|------------|
| T-HC-009 | migration-plan Wave 1 | Run Wave 1 Alembic migrations: `hc_001_base_tables.py` (hc_branches, hc_providers, hc_branch_staff, hc_patients, hc_patient_consents, hc_encounters, hc_audit_log, hc_clinic_reviews), `hc_002_rls_policies.py`, `hc_003_audit_log_permissions.py` (INSERT-only grant + no-update/delete rules on audit_log), `hc_004_i18n_overrides.py`; verify rollback scripts; confirm `app_user` does NOT have BYPASSRLS | C4 | M | T-HC-005, T-HC-007 |
| T-HC-010 | Story 1.2.1 | Branch CRUD API: `POST/GET/PUT/DELETE /api/v1/modules/healthcare/branches`; 20-branch-per-tenant limit at application layer; all fields per `hc_branches` schema (branch_name, slug, address, timezone, contact_phone, operating_hours, online_booking, default_locale); auth: Clinic Owner; soft delete (`deleted_at`) | C4 | M | T-HC-009 |
| T-HC-011 | Story 1.2.2 | Branch staff assignment API: `POST .../branches/:branch_id/staff` (invite by email; creates `hc_branch_staff` row; sends invitation email); `DELETE .../branches/:branch_id/staff/:user_id`; `GET .../branches/:branch_id/staff`; role validation; clinic_owner sentinel (`branch_id = NULL`); invitation acceptance endpoint | C4 | M | T-HC-010 |
| T-HC-012 | Story 1.2.3 | Provider CRUD API: `POST/GET/PUT/DELETE /api/v1/modules/healthcare/branches/:branch_id/providers`; fields: name, specialty, license_number, is_active; branch-scoped (uses `healthcare_branch_session`); auth: Branch Manager, Clinic Owner; soft delete | C4 | M | T-HC-010, T-HC-006 |
| T-HC-013 | Story 1.5.1, ADR-HC-001 | RBAC middleware: `has_hc_permission(resource, action, scope)` for all healthcare roles (clinic_owner, branch_manager, doctor, nurse, pharmacist, lab_tech, billing_staff, patient); role resolution from `hc_branch_staff`; integration tests — patient JWT rejected on clinic endpoints; cross-branch rejection for branch-scoped staff; clinic_owner cross-branch access confirmed | C4 | L | T-HC-006, T-HC-009 |
| T-HC-014 | Story 1.6.1, ADR-HC-002 | Audit log infrastructure: `write_phi_read_audit()` and `write_event_audit()` in `modules/healthcare/sdk/phi_audit.py`; append-only writes to `hc_audit_log`; `GET /api/v1/modules/healthcare/audit-log?from=&to=&event_type=` — auth: Clinic Owner; verify no UPDATE/DELETE possible via both application path and direct DB | C4 | M | T-HC-009, T-HC-013 |
| T-HC-015 | ADR-HC-002 | Healthcare Internal SDK: `patient_reader.py` (`get_patient(tenant_id, branch_id, patient_id) -> PatientReadDTO`) and `encounter_reader.py` (`get_encounter(...) -> EncounterReadDTO`) in `modules/healthcare/sdk/`; each SDK function calls `write_phi_read_audit()` internally (non-bypassable); DTOs are Pydantic read-only models (no ORM objects returned); CI linting gate extended to reject `from modules.healthcare.backend` imports | C4 | M | T-HC-014, T-HC-005 |
| T-HC-016 | Story 1.6.2 | Patient consent API: `POST /api/v1/modules/healthcare/patients/:patient_id/consents` (DPA acceptance, data_processing consent types); `GET .../consents`; consent records immutable (no UPDATE); consent version tracked; `consent_accepted_at`, `consent_ip`, `consent_user_agent` recorded; audit event on write | C4 | S | T-HC-009, T-HC-013 |
| T-HC-017 | Story 1.7.1 (backend) | Backend locale wiring: `resolve_locale()` called in all healthcare API error responses, email templates, notification templates; i18n override table CRUD — `GET/PUT /api/v1/modules/healthcare/i18n/:locale/:key` — auth: Clinic Owner; overrides stored in `hc_i18n_overrides`; applied on top of file-based defaults | C4 | S | T-HC-004, T-HC-009 |

**Sprint 1 Risks:**
- T-HC-015 (SDK scaffold): all sub-module sprints (3–8) are blocked on this task. Prioritise first in Sprint 1.
- T-HC-013 (RBAC): must cover all role × endpoint combinations. If AC gaps found, C4 to escalate to B1 immediately.

---

## Sprint 2 — Clinic Onboarding + Patient Registration

**Sprint Goal:** Enable clinic self-registration with DPA gate, patient self-registration with OTP, and clinic public discovery. First end-to-end user journeys live.

**Prerequisite:** Sprint 1 fully merged.

| ID | Story Ref | Description | Owner | Effort | Depends-on |
|----|-----------|-------------|-------|--------|------------|
| T-HC-018 | Story 1.1.1 | Clinic signup API: `POST /api/v1/clinics/register` (public); creates tenant + first branch (branch-001); records DPA acceptance (timestamp, IP, user_agent) before tenant status set active; emits `clinic.registered` audit event; returns `tenant_id`, `branch_id`, activation token; locale preference captured | C4 | M | T-HC-013, T-HC-004 |
| T-HC-019 | Story 1.1.1, 1.6.2 | DPA gate enforcement middleware: no PHI module can be activated without `dpa_accepted: true` on tenant; middleware check on all healthcare module routes; `GET /api/v1/modules/healthcare/dpa/status` returns current DPA acceptance version and timestamp | C4 | S | T-HC-018 |
| T-HC-020 | Story 1.4.1 | Patient registration API: `POST /api/v1/patients/register` (public; hCaptcha + OTP verified); creates `hc_patients` record with PHI encryption; records `consent_version`, `consent_accepted_at`, `consent_ip`, `consent_user_agent`; emits `patient.registered` audit event; returns patient JWT (15-min access + 7-day HttpOnly refresh cookie) | C4 | L | T-HC-002, T-HC-003, T-HC-005, T-HC-016 |
| T-HC-021 | Story 1.4.2 | Patient auth token endpoints: `POST /api/v1/patients/auth/token` (returning patient; phone + OTP -> JWT); `POST /api/v1/patients/auth/refresh` (refresh cookie -> new access token); `POST /api/v1/patients/auth/logout` (invalidate refresh cookie); consistent error shape on all failures | C4 | S | T-HC-001, T-HC-002 |
| T-HC-022 | Story 1.3.1 | Clinic search API: `GET /api/v1/clinics/search?specialty=&city=&name=&page=` (public, unauthenticated); no PHI in response; Redis cache 60 s; slowapi rate limit 60 req/IP/min; fields: name, slug, specialty, city, average rating, online_booking status | C4 | M | T-HC-009 |
| T-HC-023 | Story 1.3.2 | Clinic public profile API: `GET /api/v1/clinics/:slug` and `GET /api/v1/clinics/:slug/branches/:branch_id` (public); fields: clinic info, branch details, operating hours, providers (name + specialty only — no PHI), online_booking; Redis cache 5 min; rate limit 120 req/IP/min | C4 | S | T-HC-022 |
| T-HC-024 | Story 1.1.1 | Clinic onboarding wizard UI: 4-step wizard (account creation -> clinic details -> DPA review/accept -> confirmation); route `/onboarding/register`; locale toggle on every step; DPA text in active locale with plain-language summary; OTP resend 60-second countdown; inline field validation; Lighthouse >= 80 | C5 | L | T-HC-018, T-HC-008 |
| T-HC-025 | Story 1.3.1, 1.3.2 | Clinic discovery and public profile UI: route `/clinics` (search page) and `/clinics/:slug/:branch_id` (public profile); mobile-first (Android mid-range / 4G); search filters (specialty, city, name); result cards with rating badge and "Book" CTA; profile page: operating hours, provider list, reviews tab; Lighthouse >= 80 | C5 | L | T-HC-022, T-HC-023, T-HC-008 |
| T-HC-026 | Story 1.4.1 | Patient registration UI: route `/patient/register`; phone input -> OTP entry -> profile form (name, DOB, gender) -> DPA consent review/accept -> confirmation; hCaptcha widget; OTP resend cooldown; mobile-first (full-screen steps); all strings i18n | C5 | M | T-HC-020, T-HC-021, T-HC-008 |

**Sprint 2 Risks:**
- T-HC-020: PHI encryption (T-HC-005) must be production-ready before first patient registration goes live. Key management plan required.
- T-HC-024 / T-HC-025: Lighthouse >= 80 is a launch gate — build Lighthouse CI into DoD for C5 tasks.
- Q1 (patient identity federation) deferred — T-HC-020 implements per-tenant patient identity. A3 decision required before any cross-tenant patient linking.

---

## Sprint 3 — Scheduling Backend

**Sprint Goal:** Deliver all scheduling module backend: Wave 2 migrations, provider calendar and slot APIs, appointment booking/reschedule/cancel, status transitions, notification dispatch, and waitlist.

**Prerequisite:** Sprint 2 merged; T-HC-015 (Healthcare Internal SDK) merged.

| ID | Story Ref | Description | Owner | Effort | Depends-on |
|----|-----------|-------------|-------|--------|------------|
| T-HC-027 | migration-plan Wave 2 | Wave 2 Alembic migrations: `hcs_001_scheduling_tables.py` (hcs_provider_schedules, hcs_appointment_slots, hcs_appointments, hcs_waitlist, hcs_notification_log) + deferred FK `hc_encounters.appointment_id -> hcs_appointments.id`; `hcs_002_rls_policies.py` (RLS on hcs_appointments); verify deferred FK constraint on ORM model | C4 | M | T-HC-009, T-HC-015 |
| T-HC-028 | Story 2.1.1 | Provider schedule CRUD: `POST/GET /api/v1/modules/healthcare_scheduling/branches/:branch_id/schedules`; payload: provider_id, day-of-week blocks, slot_duration, appointment_types; `GET .../schedules/:provider_id` (weekly grid); conflict detection on overlapping blocks; schedule is branch-scoped | C4 | M | T-HC-027, T-HC-012 |
| T-HC-029 | Story 2.1.2 | Provider date/time block API: `POST .../schedules/:provider_id/blocks`; auth: Doctor (own schedule) or Branch Manager; payload: start_datetime, end_datetime, reason, recurrence (none/annual); confirmed appointments in blocked range flagged for manual review (no auto-cancel); notification workflow triggered | C4 | S | T-HC-028 |
| T-HC-030 | Story 2.2.1 | Appointment booking API: `GET /api/v1/clinics/:slug/branches/:branch_id/slots?date=&appointment_type=` (authenticated patient); `POST /api/v1/patients/me/appointments`; atomic slot reservation (SELECT FOR UPDATE); creates hcs_appointments with status confirmed; emits `appointment.booked` audit event; triggers notification workflow | C4 | L | T-HC-027, T-HC-022 |
| T-HC-031 | Story 2.2.2 | Appointment reschedule and cancel API: `PUT /api/v1/patients/me/appointments/:id` (new slot_id; old slot released); `DELETE /api/v1/patients/me/appointments/:id`; cancellation policy enforcement (configurable per tenant: no cancel < N hours); audit events; notification triggers | C4 | M | T-HC-030 |
| T-HC-032 | Story 2.2.3 | Appointment status transition API: `PUT /api/v1/modules/healthcare_scheduling/branches/:branch_id/appointments/:id/status`; valid transitions: confirmed -> checked_in -> in_progress -> completed | no_show; auth: Nurse, Branch Manager; audit event per transition | C4 | S | T-HC-030 |
| T-HC-033 | Story 2.3.1 | Notification dispatch service: WhatsApp Business API adapter (primary) + SMS gateway (fallback after 60 s); PHI-safe system-locked templates (appointment_confirmed, reminder 24h, reminder 2h); locale resolved from patient profile then tenant default (Q4 decision); delivery logged to `hcs_notification_log`; no PHI in message body | C4 | L | T-HC-030, T-HC-004 |
| T-HC-034 | Story 2.4.1 | Waitlist API: `POST /api/v1/patients/me/waitlist`; FIFO per slot; auto-offer on slot cancellation (15-min claim window; WhatsApp/SMS notification); `DELETE .../waitlist/:entry_id`; offer expiry -> next patient notified; `hcs_waitlist` status machine | C4 | M | T-HC-030, T-HC-033 |

**Sprint 3 Risks:**
- T-HC-030 (slot reservation): SELECT FOR UPDATE is minimum; consider Redis distributed lock for peak-load scenarios — escalate to B1 if needed.
- T-HC-033 (notifications): WhatsApp Business API requires pre-registered account with Meta — confirm account status before sprint start.

---

## Sprint 4 — Scheduling Frontend + Patient Booking

**Sprint Goal:** Deliver clinic-side scheduling UI (calendar editor, availability heatmap, appointment queue) and patient-side booking, reschedule, cancel, waitlist, and notification settings flows.

**Prerequisite:** Sprint 3 fully merged.

| ID | Story Ref | Description | Owner | Effort | Depends-on |
|----|-----------|-------------|-------|--------|------------|
| T-HC-035 | Story 2.1.1 | Provider schedule editor UI: route `/clinic/branches/:branch_id/schedules/:provider_id`; weekly drag-to-set grid (Mon–Sun x time slots); slot duration selector; conflict detection + FlexAlert; branch timezone in column headers; save toolbar; tap-to-add mobile fallback; i18n all labels | C5 | L | T-HC-028, T-HC-008 |
| T-HC-036 | Story 2.1.2 | Date/time block UI: calendar view with "Block Date/Time" modal; date-range picker; reason field (internal, not patient-visible); blocked ranges in grey; warning banner if existing appointments affected; recurring (annual) option; i18n | C5 | M | T-HC-029, T-HC-035 |
| T-HC-037 | Story 2.1.3 | Availability heatmap UI: route `/clinic/branches/:branch_id/availability`; heatmap table (rows = doctors, columns = days); colour thresholds (>30% available = green, 1–30% = yellow, 0 = red); date range picker; CSV export; cell click navigates to doctor schedule for that day | C5 | M | T-HC-028, T-HC-008 |
| T-HC-038 | Story 2.2.1 | Patient appointment booking wizard UI: route `/book/:clinic_slug/:branch_id`; 4-step wizard (type -> date -> slot -> confirmation); mobile-first; slot times in patient timezone with clinic timezone reference note; "Add to Calendar" ICS download; slot-taken error handling returns to step 3 | C5 | L | T-HC-030, T-HC-008 |
| T-HC-039 | Story 2.2.2 | Patient reschedule and cancel UI: route `/patient/appointments/:id`; reschedule opens slot-picker modal (pre-filtered same provider); cancel confirmation modal with policy text in active locale; status badge updates post-action | C5 | M | T-HC-031, T-HC-038 |
| T-HC-040 | Story 2.2.3 | Appointment queue UI: route `/clinic/appointments/queue`; live queue list; PHI mask toggle; status badges colour-coded; Check In / Mark No-Show actions; 30-second auto-refresh (WebSocket primary, polling fallback); branch context badge prominent | C5 | M | T-HC-032, T-HC-008 |
| T-HC-041 | Story 2.4.1 | Waitlist UI: route `/patient/waitlist`; entry cards with status badges (Waiting / Offered / Expired / Removed); offer page with 15-min countdown progress bar; in-app offer banner; "Leave Waitlist" confirmation modal; i18n all labels | C5 | M | T-HC-034, T-HC-008 |
| T-HC-042 | Story 2.3.1 | Notification settings UI (clinic): route `/clinic/settings/notifications`; read-only template preview cards; locale toggle (id-ID / en-US) for preview; "Send Test" button (to Branch Manager own number); locked-template notice banner | C5 | S | T-HC-033, T-HC-008 |

**Sprint 4 Risks:**
- T-HC-035 (drag grid): drag on mobile is complex — tap-to-add fallback must be fully implemented and tested, not left as a stub.
- T-HC-038 (booking wizard concurrency): slot-taken race condition between step 3 and confirm must be load-tested.

---

## Sprint 5 — Patient Portal Core

**Sprint Goal:** Deliver the patient portal shell, bottom navigation, profile and health summary, encounter history, unified appointments list, and reviews. Patients can see their full longitudinal record for base module data.

**Prerequisite:** Sprint 4 fully merged.

| ID | Story Ref | Description | Owner | Effort | Depends-on |
|----|-----------|-------------|-------|--------|------------|
| T-HC-043 | Story 7.1.1 | Patient profile and health summary APIs: `GET /api/v1/patients/me/profile`; `PUT /api/v1/patients/me/profile` (email, locale, address; name/DOB blocked in v1); `GET /api/v1/patients/me/summary` (encounter count, active prescriptions count, upcoming appointments count, last clinic visited); all reads emit `patient.profile_accessed` audit event | C4 | M | T-HC-015, T-HC-020 |
| T-HC-044 | Story 7.1.2 | Patient encounter history API: `GET /api/v1/patients/me/encounters?page=&from=&to=` (auth: Patient); cross-tenant list (all tenants with confirmed encounters for this patient); fields: clinic_name, branch_name, encounter_date, provider_name, encounter_summary (if released by clinic); emits `patient.encounters_accessed` audit event | C4 | M | T-HC-015, T-HC-043 |
| T-HC-045 | Story 7.2.1 | Patient appointments cross-tenant API: `GET /api/v1/patients/me/appointments?status=upcoming|past&page=`; aggregates across all tenants where patient has confirmed encounters; fields: clinic_name, branch_name, provider_name, appointment_type, datetime, status, appointment_id | C4 | M | T-HC-030, T-HC-043 |
| T-HC-046 | Story 7.4.1, 7.4.2 | Clinic review APIs: `POST /api/v1/patients/me/reviews` (auth: Patient; requires completed encounter; 1-5 rating; text <= 500 chars; one per encounter; 24h moderation); `GET /api/v1/clinics/:slug/branches/:branch_id/reviews` (public; no PHI — "Patient, Month Year"); `POST .../reviews/:id/response` (auth: Branch Manager, Clinic Owner; also moderated); audit events on both | C4 | M | T-HC-009, T-HC-020 |
| T-HC-047 | Story 7.1.1 | Patient portal shell UI: bottom navigation bar (Beranda / Janji / Rekam Medis / Profil); route guards (patient JWT required); profile card (name, DOB, phone masked, email, locale selector inline); 2x2 health summary widget grid (tappable, navigates to detail); edit mode for email/address/locale; mobile-first | C5 | L | T-HC-043, T-HC-008 |
| T-HC-048 | Story 7.1.2 | Encounter history UI: route `/patient/records/visits`; year-grouped timeline (most recent first); filter by date range and clinic name; encounter card (clinic, branch, date, doctor, summary or grey italic "not shared"); infinite scroll; i18n all labels | C5 | M | T-HC-044, T-HC-047 |
| T-HC-049 | Story 7.2.1 | Patient appointments list UI: route `/patient/appointments`; tabs Upcoming / Past with count badges; appointment cards with colour-coded status badges; Reschedule + Cancel actions (upcoming); "Book Again" shortcut (past); infinite scroll; datetimes in patient timezone | C5 | M | T-HC-045, T-HC-047 |
| T-HC-050 | Story 7.4.1, 7.4.2 | Reviews UI (patient + clinic): NPS prompt card (triggered 2h post-visit; shown once per encounter); route `/patient/appointments/:id/review`; 5-star large-tap selector; 500-char textarea with counter; public clinic profile Ulasan tab (average rating, paginated reviews, no PHI); clinic portal `/clinic/reviews` with Reply flow and moderation notice | C5 | M | T-HC-046, T-HC-047 |

**Sprint 5 Risks:**
- T-HC-044 (cross-tenant aggregation): add DB index on `hc_encounters.patient_id` before this goes to production — high-volume patients could see slow page loads.
- T-HC-050 (NPS 2h trigger): requires background job or webhook from appointment status change event — implementation approach must be confirmed with C4 before C5 starts UI.

---

## Sprint 6 — Billing Module

**Sprint Goal:** Deliver the complete billing module: Wave 3 migrations, encounter-to-invoice workflow, BPJS file export, payment tracking, and patient invoice access.

**Prerequisite:** Sprint 5 merged; Wave 2 migrations complete (T-HC-027).

| ID | Story Ref | Description | Owner | Effort | Depends-on |
|----|-----------|-------------|-------|--------|------------|
| T-HC-051 | migration-plan Wave 3 | Wave 3 Alembic migrations: `hcb_001_billing_tables.py` (hcb_service_items, hcb_insurance_profiles, hcb_invoices, hcb_invoice_lines, hcb_payments, hcb_bpjs_exports); `hcb_002_rls_policies.py` (RLS on hcb_invoices, hcb_insurance_profiles); verify rollback | C4 | M | T-HC-027, T-HC-015 |
| T-HC-052 | Story 3.1.1 | Invoice creation API: `POST /api/v1/modules/healthcare_billing/branches/:branch_id/invoices` (auth: Billing Staff, Branch Manager); pulls service items from encounter via healthcare SDK `get_encounter()`; draft -> finalized (immutable); finalized amendments create credit notes; emits `invoice.created` audit event; IDR currency | C4 | L | T-HC-051, T-HC-015 |
| T-HC-053 | Story 3.1.2 | Patient invoice access API: `GET /api/v1/patients/me/invoices/:invoice_id`; `GET .../invoices/:invoice_id/pdf` (PDF in patient locale; clinic logo, address, invoice number, line items, total, payment status); auth: Patient own invoices only | C4 | M | T-HC-052, T-HC-043 |
| T-HC-054 | Story 3.2.1 | BPJS file export: `POST /api/v1/modules/healthcare_billing/branches/:branch_id/bpjs-exports` (auth: Billing Staff); generates BPJS Kesehatan-compatible claim file (SEP/billing format per confirmed spec); file download endpoint; `hcb_bpjs_exports` records metadata and file reference; no live API in v1 | C4 | L | T-HC-052 |
| T-HC-055 | Story 3.1.1, 3.1.2 | Billing UI (clinic + patient): clinic route `/clinic/billing/invoices/new?encounter_id=`; auto-populated line items; inline qty/price edit; PDF preview modal; finalize confirmation; patient route `/patient/invoices/:invoice_id`; Download PDF button; IDR formatting per active locale; i18n all labels | C5 | L | T-HC-052, T-HC-053, T-HC-008 |

**Sprint 6 Risks:**
- T-HC-054 (BPJS format): BPJS file format specification must be obtained from A3/legal before implementation. Do not start T-HC-054 without confirmed spec.
- Q3 (BPJS live API) remains deferred — this sprint implements file export only per BACKLOG Scope-Out Register.

---

## Sprint 7 — Pharmacy Module

**Sprint Goal:** Deliver the complete pharmacy module: Wave 4 migrations, medication catalog, prescription creation, dispensing workflow, drug interaction adapter stub, low-stock alerting, and patient prescription access.

**Prerequisite:** Sprint 6 merged; Wave 3 migrations complete (T-HC-051).

| ID | Story Ref | Description | Owner | Effort | Depends-on |
|----|-----------|-------------|-------|--------|------------|
| T-HC-056 | migration-plan Wave 4 | Wave 4 Alembic migrations: `hcp_001_pharmacy_tables.py` (hcp_medication_catalog, hcp_prescriptions, hcp_prescription_items, hcp_dispensing_log, hcp_dispensing_items, hcp_drug_interaction_log); `hcp_002_rls_policies.py` (RLS on hcp_prescriptions, hcp_dispensing_log); schedule TTL cleanup job for `hcp_drug_interaction_log` | C4 | M | T-HC-051, T-HC-015 |
| T-HC-057 | Story 4.1.1 | Medication catalog CRUD API: `POST/GET/PUT/DELETE /api/v1/modules/healthcare_pharmacy/branches/:branch_id/catalog`; branch-scoped; stock adjustment emits `pharmacy.stock_adjusted` audit event; `GET .../catalog?search=` accessible to Doctor role; paginated | C4 | M | T-HC-056, T-HC-013 |
| T-HC-058 | Story 4.1.2 | Low-stock alert job: daily background job; identifies `current_stock <= reorder_threshold`; in-app + email to Pharmacist and Branch Manager (no PHI); `GET .../catalog/low-stock` endpoint; low-stock banner in catalog UI populated from this endpoint | C4 | S | T-HC-057 |
| T-HC-059 | Story 4.2.1 | Prescription creation API: `POST /api/v1/modules/healthcare_pharmacy/branches/:branch_id/prescriptions` (auth: Doctor); uses healthcare SDK `get_encounter()` and `get_patient()`; prescription items linked to catalog; drug interaction check via adapter stub (returns empty/no-op if no vendor DB configured — Q5 deferred); emits PHI audit event | C4 | L | T-HC-056, T-HC-015 |
| T-HC-060 | Story 4.3.1 | Dispensing workflow API: `PUT .../prescriptions/:id/dispense` (auth: Pharmacist); creates `hcp_dispensing_log` and `hcp_dispensing_items`; stock decremented on `hcp_medication_catalog`; emits `pharmacy.dispensed` audit event; prescription status -> dispensed | C4 | M | T-HC-059, T-HC-057 |
| T-HC-061 | Story 4.1.1, 4.2.1, 4.3.1 | Pharmacy UI: catalog table with inline stock edit and low-stock badges; "Add Drug" modal; prescription creation form (encounter-linked, catalog search, drug interaction warning if returned); dispensing queue and dispense action; i18n all labels | C5 | XL | T-HC-057, T-HC-059, T-HC-060, T-HC-008 |
| T-HC-062 | Story 7.3.1 | Patient prescriptions cross-tenant API: `GET /api/v1/patients/me/prescriptions` (auth: Patient); cross-tenant; active prescriptions first; fields: clinic_name, drug_name, dose, frequency, duration, dispensed_at, status; audit event per contributing tenant | C4 | M | T-HC-059, T-HC-043 |

**Sprint 7 Risks:**
- Q5 (drug database vendor) deferred — T-HC-059 implements adapter stub returning empty if vendor not configured. Do not block sprint on vendor selection.
- T-HC-061 is XL effort — consider splitting dispensing UI into Sprint 7b if sprint capacity is tight.

---

## Sprint 8 — Laboratory Module

**Sprint Goal:** Deliver the complete laboratory module: Wave 5 migrations, test catalog, order management, specimen tracking, result entry, critical alerting, and patient lab result access.

**Prerequisite:** Sprint 7 merged; Wave 4 migrations complete (T-HC-056).

| ID | Story Ref | Description | Owner | Effort | Depends-on |
|----|-----------|-------------|-------|--------|------------|
| T-HC-063 | migration-plan Wave 5 | Wave 5 Alembic migrations: `hcl_001_lab_tables.py` (hcl_test_catalog, hcl_test_orders, hcl_test_order_items, hcl_specimens, hcl_results, hcl_critical_alerts); `hcl_002_rls_policies.py` (RLS on hcl_test_orders, hcl_results); verify rollback | C4 | M | T-HC-056, T-HC-015 |
| T-HC-064 | Story 5.1.1 | Lab test ordering API: `POST /api/v1/modules/healthcare_lab/branches/:branch_id/lab-orders` (auth: Doctor); uses healthcare SDK `get_encounter()` and `get_patient()`; multi-test order with clinical indication per test; in-app notification to Lab Tech (order ref code only — no PHI in body); emits `lab.order_created` PHI audit event | C4 | M | T-HC-063, T-HC-015 |
| T-HC-065 | Story 5.1.2, 5.2.1 | Specimen collection and result entry APIs: `PUT .../lab-orders/:id/accept` (Lab Tech; ordered -> specimen_pending); specimen collection endpoint per order item; result entry endpoint (numeric/text/categorical; reference range min/max); critical value detection triggers alert creation in `hcl_critical_alerts` | C4 | L | T-HC-064 |
| T-HC-066 | Story 5.3.1 | Critical value alerting: `hcl_critical_alerts` record on result exceeding critical threshold; in-app alert to ordering Doctor (PHI-safe — patient ref + order ref only); `GET .../lab-orders/:id/critical-alerts`; alert acknowledgement endpoint; near-real-time delivery (Redis pub/sub or WebSocket — confirm with B1) | C4 | M | T-HC-065 |
| T-HC-067 | Story 5.3.2 | Patient lab results cross-tenant API: `GET /api/v1/patients/me/lab-results` (auth: Patient); grouped by clinic and date; interpretation badge (normal/abnormal/critical based on reference ranges); PDF download per result; audit event per contributing tenant | C4 | M | T-HC-065, T-HC-043 |
| T-HC-068 | Story 5.1.1, 5.1.2, 5.2.1, 5.3.1 | Lab UI (full): test ordering form (encounter-linked, catalog search autocomplete, multi-select, clinical indication per test); Lab Tech order queue + accept action; specimen collection checklist; result entry form (reference range display); critical alert banner for Doctors; i18n all labels | C5 | XL | T-HC-064, T-HC-065, T-HC-066, T-HC-008 |
| T-HC-069 | Story 7.3.1 | Patient records UI enrichment: add Lab Results sub-tab to `/patient/records` (populated from T-HC-067); Prescriptions sub-tab (populated from T-HC-062); cross-tenant aggregation notice per sub-tab; interpretation badges on lab results; empty state per sub-tab; i18n | C5 | M | T-HC-067, T-HC-062, T-HC-047 |

**Sprint 8 Risks:**
- T-HC-068 (Lab UI full) is XL — specimen tracking and result entry are complex. Consider splitting into 8a (ordering + acceptance) and 8b (results + critical alerts) if capacity constrained.
- T-HC-066 (critical alerts): must be near-real-time. Clarify whether Redis pub/sub or WebSocket is used — escalate to B1 before sprint start if architecture decision is pending.

---

## Task ID Registry

Tasks T-HC-001 through T-HC-069 are allocated across 9 sprints (Sprint 0 through Sprint 8).

**Next available ID:** T-HC-070

---

## Critical Path Summary

The following tasks block the most downstream work and must be prioritised:

| Task | Downstream Blockers | Risk Level |
|------|---------------------|------------|
| T-HC-005 (PHI encryption helper) | T-HC-009, T-HC-020 — no production PHI write possible without it | CRITICAL |
| T-HC-006 (BranchScopeListener) | T-HC-007, T-HC-009, T-HC-013 — all branch-scoped module work | CRITICAL |
| T-HC-009 (Wave 1 migrations) | T-HC-010 through T-HC-017 and all subsequent sprints | CRITICAL |
| T-HC-015 (Healthcare Internal SDK) | T-HC-027, T-HC-051, T-HC-056, T-HC-063 — all sub-module migration waves; T-HC-043, T-HC-044, T-HC-052, T-HC-059, T-HC-064 | CRITICAL |
| T-HC-013 (RBAC middleware) | T-HC-018, T-HC-022, T-HC-028, T-HC-043, T-HC-057 — all authenticated endpoints | HIGH |
| T-HC-004 (Backend i18n framework) | T-HC-008, T-HC-017, T-HC-033 — all localised content and notification templates | HIGH |
| T-HC-030 (Appointment booking API) | T-HC-031, T-HC-032, T-HC-033, T-HC-034, T-HC-038, T-HC-039, T-HC-040, T-HC-041, T-HC-045 | HIGH |
| T-HC-020 (Patient registration API) | T-HC-021, T-HC-026, T-HC-043, T-HC-046 — entire patient-side surface | HIGH |
