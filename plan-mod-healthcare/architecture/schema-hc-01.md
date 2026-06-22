---
artifact_id: schema-hc-01
type: schema-design
module: healthcare (base) + healthcare_scheduling + healthcare_billing + healthcare_pharmacy + healthcare_lab
status: Draft
producer: B2 Data Engineer
upstream: [adr-hc-001, adr-hc-002, adr-hc-003, adr-hc-004, epic-01, epic-02, epic-03, epic-04, epic-05, epic-07]
created: 2026-06-21
---

# Schema Design — Healthcare Module Suite

> Epic-06 (Telemedicine) is **excluded** from this design — pending legal review.

## Conventions

| Convention | Rule |
|---|---|
| `tenant_id` | `VARCHAR(36) NOT NULL` — enforced on every table, indexed |
| `branch_id` | `VARCHAR(36) NOT NULL` — enforced on all branch-scoped tables; `NULL` only for explicitly tenant-wide entities (see §1.3) |
| `[PHI]` | Table contains Protected Health Information; all PHI columns encrypted at rest with AES-256 (ADR-HC-002); access audit-logged via `hc_audit_log` |
| PK | UUID v4 (`GUID`), generated server-side |
| Timestamps | UTC `TIMESTAMP WITHOUT TIME ZONE`; display in branch/patient timezone is a UI concern |
| RLS | Row-Level Security on all PHI tables (ADR-HC-001 §D4): `tenant_id = current_setting('app.tenant_id') AND (branch_id = current_setting('app.branch_id') OR current_setting('app.branch_id') = 'ALL')` |
| Soft delete | `deleted_at TIMESTAMP NULL` where logically deletable; immutable audit/clinical records have no `deleted_at` |

---

## Module: healthcare (base)

### Table: `hc_branches`

Branch registry per tenant. Supports stories 1.2.1, 1.2.2, 1.2.3.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `branch_name` | VARCHAR(255) | NOT NULL | — | |
| `slug` | VARCHAR(100) | NOT NULL | — | UNIQUE(tenant_id, slug) |
| `address_street` | VARCHAR(500) | NOT NULL | — | |
| `address_city` | VARCHAR(100) | NOT NULL | — | |
| `address_province` | VARCHAR(100) | NOT NULL | — | |
| `address_postal_code` | VARCHAR(10) | NULL | — | |
| `timezone` | VARCHAR(50) | NOT NULL | 'Asia/Jakarta' | CHECK IN ('Asia/Jakarta','Asia/Makassar','Asia/Jayapura') and any valid IANA tz |
| `contact_phone` | VARCHAR(30) | NOT NULL | — | |
| `operating_hours` | JSONB | NOT NULL | '{}' | Structured Mon–Sun open/close blocks |
| `status` | VARCHAR(20) | NOT NULL | 'active' | CHECK IN ('active','inactive','suspended') |
| `online_booking` | BOOLEAN | NOT NULL | TRUE | |
| `default_locale` | VARCHAR(10) | NOT NULL | 'id-ID' | CHECK IN ('id-ID','en-US') |
| `appointment_types` | JSONB | NOT NULL | '[]' | Branch-specific override; inherits tenant defaults if empty |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |
| `deleted_at` | TIMESTAMP | NULL | — | Soft delete |

**PK:** `id`
**FKs:** `tenant_id` → `tenants.id`
**Indexes:**
- `idx_hc_branches_tenant_id` ON `(tenant_id)`
- `idx_hc_branches_tenant_slug` ON `(tenant_id, slug)` UNIQUE
- `idx_hc_branches_status` ON `(tenant_id, status)`
- `idx_hc_branches_created_at` ON `(created_at)`

**Notes:** `branch_id` column not applicable — this IS the branch registry. Tenant-wide entity (no `branch_id` FK on itself). Max 20 branches per tenant enforced at application layer.

---

### Table: `hc_branch_staff`

Staff ↔ branch assignments with role. Supports stories 1.2.2, 1.5.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `branch_id` | VARCHAR(36) | NULL | — | FK → hc_branches.id; NULL = clinic_owner cross-branch sentinel (ADR-HC-001 §D3) |
| `user_id` | VARCHAR(36) | NOT NULL | — | FK → users.id |
| `role` | VARCHAR(30) | NOT NULL | — | CHECK IN ('clinic_owner','branch_manager','doctor','nurse','pharmacist','lab_tech','billing_staff') |
| `is_active` | BOOLEAN | NOT NULL | TRUE | |
| `invited_at` | TIMESTAMP | NULL | — | Set on invitation send |
| `accepted_at` | TIMESTAMP | NULL | — | Set when user accepts invitation |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `tenant_id` → `tenants.id`; `branch_id` → `hc_branches.id` (NULL allowed for clinic_owner); `user_id` → `users.id`
**Unique constraint:** `(tenant_id, branch_id, user_id, role)` — a user may hold one role per branch (or NULL branch for owner)
**Indexes:**
- `idx_hc_branch_staff_tenant_id` ON `(tenant_id)`
- `idx_hc_branch_staff_branch_id` ON `(branch_id)` WHERE `branch_id IS NOT NULL`
- `idx_hc_branch_staff_user_id` ON `(user_id, tenant_id)`
- `idx_hc_branch_staff_role` ON `(tenant_id, branch_id, role)`
- `idx_hc_branch_staff_created_at` ON `(created_at)`

---

### Table: `hc_patients` [PHI]

Platform-level patient profiles. `tenant_id` present (for data ownership); `branch_id` is NULL — patients belong to the clinic (tenant), not a branch. Supports stories 1.3.1, 1.4.1, 7.1.1.

> **PHI encryption required (ADR-HC-002):** `full_name`, `date_of_birth`, `phone`, `email`, `nik`, `address` must be encrypted at rest with AES-256 before storage. Decryption occurs in application layer only, never in raw SQL reads.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK — platform-assigned patient ID |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `full_name` | TEXT (encrypted) | NOT NULL | — | [PHI] KTP legal name |
| `date_of_birth` | DATE (encrypted) | NOT NULL | — | [PHI] |
| `phone` | VARCHAR(30) (encrypted) | NOT NULL | — | [PHI] WhatsApp-capable; E.164 format |
| `email` | VARCHAR(255) (encrypted) | NULL | — | [PHI] |
| `gender` | VARCHAR(10) | NOT NULL | — | CHECK IN ('male','female','other') |
| `nik` | VARCHAR(20) (encrypted) | NULL | — | [PHI] Indonesian national ID; UNIQUE per tenant if present |
| `address` | TEXT (encrypted) | NULL | — | [PHI] |
| `locale` | VARCHAR(10) | NOT NULL | 'id-ID' | Patient-preferred locale |
| `consent_version` | VARCHAR(20) | NOT NULL | — | Version of consent accepted at registration |
| `consent_accepted_at` | TIMESTAMP | NOT NULL | — | |
| `consent_ip` | VARCHAR(45) | NOT NULL | — | IPv4 or IPv6 |
| `consent_user_agent` | TEXT | NOT NULL | — | |
| `status` | VARCHAR(20) | NOT NULL | 'active' | CHECK IN ('active','suspended','deleted') |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |
| `deleted_at` | TIMESTAMP | NULL | — | |

**PK:** `id`
**FKs:** `tenant_id` → `tenants.id`
**Indexes:**
- `idx_hc_patients_tenant_id` ON `(tenant_id)`
- `idx_hc_patients_created_at` ON `(created_at)`
- `idx_hc_patients_status` ON `(tenant_id, status)`

**RLS:** tenant-scoped only (no branch filter — patient is tenant-wide per ADR-HC-001 §D3 and Story 1.3.1 rationale). RLS policy: `tenant_id = current_setting('app.tenant_id')`.

**Notes:** `branch_id` intentionally absent. Cross-branch reads of the patient profile are permitted within the same tenant, with audit logging. Branch-level PHI isolation is enforced at the `hc_encounters` level.

---

### Table: `hc_patient_consents`

DPA/consent records per patient per clinic. Immutable after creation. Supports stories 1.4.1, 1.6.2.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `patient_id` | UUID | NOT NULL | — | FK → hc_patients.id |
| `consent_type` | VARCHAR(50) | NOT NULL | — | CHECK IN ('dpa_acceptance','data_processing','marketing') |
| `consent_version` | VARCHAR(20) | NOT NULL | — | e.g. 'v1.2' |
| `status` | VARCHAR(20) | NOT NULL | 'active' | CHECK IN ('active','revoked') |
| `accepted_at` | TIMESTAMP | NOT NULL | — | |
| `revoked_at` | TIMESTAMP | NULL | — | |
| `ip` | VARCHAR(45) | NOT NULL | — | |
| `user_agent` | TEXT | NOT NULL | — | |
| `purpose_description` | TEXT | NULL | — | Plain-language purpose per UU PDP No. 27/2022 |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `tenant_id` → `tenants.id`; `patient_id` → `hc_patients.id`
**Indexes:**
- `idx_hc_patient_consents_tenant_id` ON `(tenant_id)`
- `idx_hc_patient_consents_patient_id` ON `(patient_id)`
- `idx_hc_patient_consents_status` ON `(patient_id, status)`
- `idx_hc_patient_consents_created_at` ON `(created_at)`

**Notes:** No UPDATE or DELETE permitted (append-only); revocation appends a new row with `status='revoked'`. Enforced via DB trigger or application-layer policy.

---

### Table: `hc_providers`

Doctors, nurses, etc. per branch. Supports stories 1.2.2, 1.5.1, 1.4.3, 2.1.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `user_id` | VARCHAR(36) | NOT NULL | — | FK → users.id; links to platform user account |
| `provider_type` | VARCHAR(30) | NOT NULL | — | CHECK IN ('doctor','nurse','pharmacist','lab_tech','billing_staff') |
| `specialty` | VARCHAR(100) | NULL | — | Clinical specialty (doctors) |
| `license_number` | VARCHAR(50) | NULL | — | Professional license (SIP/STR number) |
| `display_name` | VARCHAR(255) | NOT NULL | — | Name shown on public profile (first name + title) |
| `bio` | TEXT | NULL | — | Public-facing bio; no PHI |
| `is_active` | BOOLEAN | NOT NULL | TRUE | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `tenant_id` → `tenants.id`; `branch_id` → `hc_branches.id`; `user_id` → `users.id`
**Unique constraint:** `(tenant_id, branch_id, user_id)` — one provider record per user per branch
**Indexes:**
- `idx_hc_providers_tenant_id` ON `(tenant_id)`
- `idx_hc_providers_branch_id` ON `(tenant_id, branch_id)`
- `idx_hc_providers_user_id` ON `(user_id)`
- `idx_hc_providers_specialty` ON `(tenant_id, branch_id, specialty)` WHERE `specialty IS NOT NULL`
- `idx_hc_providers_created_at` ON `(created_at)`

---

### Table: `hc_encounters` [PHI]

Clinical encounters per branch. Supports stories 1.3.1, 1.3.2, 7.1.2.

> **PHI encryption required (ADR-HC-002):** `soap_subjective`, `soap_objective`, `soap_assessment`, `soap_plan`, `soap_notes` must be encrypted at rest with AES-256.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `patient_id` | UUID | NOT NULL | — | FK → hc_patients.id |
| `provider_id` | UUID | NOT NULL | — | FK → hc_providers.id |
| `appointment_id` | UUID | NULL | — | FK → hcs_appointments.id; NULL for walk-in |
| `status` | VARCHAR(20) | NOT NULL | 'open' | CHECK IN ('open','in_progress','completed','cancelled') |
| `started_at` | TIMESTAMP | NOT NULL | NOW() | |
| `completed_at` | TIMESTAMP | NULL | — | |
| `soap_subjective` | TEXT (encrypted) | NULL | — | [PHI] Patient complaint narrative |
| `soap_objective` | TEXT (encrypted) | NULL | — | [PHI] Clinical observations |
| `soap_assessment` | TEXT (encrypted) | NULL | — | [PHI] Diagnosis / differential |
| `soap_plan` | TEXT (encrypted) | NULL | — | [PHI] Treatment plan |
| `soap_notes` | TEXT (encrypted) | NULL | — | [PHI] Additional clinical notes |
| `patient_summary` | TEXT | NULL | — | Clinic-controlled patient-readable summary; released explicitly by clinic |
| `summary_released` | BOOLEAN | NOT NULL | FALSE | |
| `summary_released_at` | TIMESTAMP | NULL | — | |
| `amendment_of_id` | UUID | NULL | — | FK → hc_encounters.id; self-ref for amendments |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `tenant_id` → `tenants.id`; `branch_id` → `hc_branches.id`; `patient_id` → `hc_patients.id`; `provider_id` → `hc_providers.id`; `appointment_id` → `hcs_appointments.id` (deferred FK, NULL-safe); `amendment_of_id` → `hc_encounters.id` (self-ref)
**Indexes:**
- `idx_hc_encounters_tenant_branch` ON `(tenant_id, branch_id)`
- `idx_hc_encounters_patient_id` ON `(tenant_id, patient_id)`
- `idx_hc_encounters_provider_id` ON `(branch_id, provider_id)`
- `idx_hc_encounters_status` ON `(tenant_id, branch_id, status)`
- `idx_hc_encounters_started_at` ON `(tenant_id, branch_id, started_at)`
- `idx_hc_encounters_created_at` ON `(created_at)`

**RLS policy:** `tenant_id = current_setting('app.tenant_id') AND (branch_id = current_setting('app.branch_id') OR current_setting('app.branch_id') = 'ALL')`

**Notes:** Encounters are immutable once `status = 'completed'`. Amendments create a new row with `amendment_of_id` pointing to the original. The original's `status` is NOT changed.

---

### Table: `hc_audit_log`

Append-only PHI access audit. Supports story 1.6.1. INSERT-only grant to application DB user.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `event_type` | VARCHAR(100) | NOT NULL | — | e.g. 'phi.read', 'phi.write', 'phi.delete', 'patient.created', 'appointment.booked' |
| `actor_id` | VARCHAR(36) | NOT NULL | — | user_id or patient_id of actor |
| `actor_type` | VARCHAR(20) | NOT NULL | — | CHECK IN ('staff','patient','system') |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NULL | — | NULL for tenant-wide events |
| `resource_type` | VARCHAR(50) | NOT NULL | — | e.g. 'patient', 'encounter', 'prescription', 'lab_result' |
| `resource_id` | VARCHAR(36) | NOT NULL | — | UUID of the accessed resource |
| `source_module` | VARCHAR(50) | NOT NULL | — | e.g. 'healthcare', 'healthcare_pharmacy', 'healthcare_lab' |
| `ip` | VARCHAR(45) | NULL | — | Request IP; NULL for system events |
| `metadata_json` | JSONB | NULL | — | Additional context (e.g. purpose, changed fields) |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | Immutable |

**PK:** `id`
**Indexes:**
- `idx_hc_audit_log_tenant_id` ON `(tenant_id, created_at DESC)` — primary query path for compliance export
- `idx_hc_audit_log_actor_id` ON `(actor_id, created_at DESC)`
- `idx_hc_audit_log_resource` ON `(resource_type, resource_id)`
- `idx_hc_audit_log_event_type` ON `(tenant_id, event_type, created_at DESC)`
- `idx_hc_audit_log_created_at` ON `(created_at)`

**Notes:** No UPDATE or DELETE permitted. Enforced by: (1) DB-level REVOKE UPDATE, DELETE ON `hc_audit_log` FROM app_user; (2) RLS policy blocking non-INSERT DML. Data retention minimum 5 years (PP 71/2019). Partitioned by `created_at` (monthly or yearly) recommended for archival.

---

### Table: `hc_i18n_overrides`

Per-tenant translation overrides for UI strings. Supports story 1.7.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `locale` | VARCHAR(10) | NOT NULL | — | CHECK IN ('id-ID','en-US') |
| `translation_key` | VARCHAR(255) | NOT NULL | — | Dot-notation key, e.g. 'patient.registration.title' |
| `translation_value` | TEXT | NOT NULL | — | Override value for this tenant |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**Unique constraint:** `(tenant_id, locale, translation_key)`
**Indexes:**
- `idx_hc_i18n_overrides_tenant_locale` ON `(tenant_id, locale)`
- `idx_hc_i18n_overrides_created_at` ON `(created_at)`

---

## Module: healthcare_scheduling

### Table: `hcs_provider_schedules`

Recurring availability per provider per branch. Supports story 2.1.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `provider_id` | UUID | NOT NULL | — | FK → hc_providers.id |
| `day_of_week` | SMALLINT | NOT NULL | — | CHECK IN (0..6): 0=Monday |
| `start_time` | TIME | NOT NULL | — | Local branch time |
| `end_time` | TIME | NOT NULL | — | CHECK end_time > start_time |
| `slot_duration_minutes` | SMALLINT | NOT NULL | 30 | CHECK IN (15,30,45,60) |
| `appointment_types` | JSONB | NOT NULL | '[]' | Array of allowed appointment type codes |
| `max_concurrent_slots` | SMALLINT | NOT NULL | 1 | Parallel booking capacity |
| `effective_from` | DATE | NOT NULL | — | |
| `effective_to` | DATE | NULL | — | NULL = indefinite |
| `is_active` | BOOLEAN | NOT NULL | TRUE | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `provider_id` → `hc_providers.id`
**Indexes:**
- `idx_hcs_provider_schedules_tenant_id` ON `(tenant_id)`
- `idx_hcs_provider_schedules_branch_provider` ON `(branch_id, provider_id)`
- `idx_hcs_provider_schedules_day` ON `(branch_id, provider_id, day_of_week)`
- `idx_hcs_provider_schedules_created_at` ON `(created_at)`

---

### Table: `hcs_appointment_slots`

Generated time slots from schedule. Supports stories 2.1.1, 2.1.2, 2.2.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `provider_id` | UUID | NOT NULL | — | FK → hc_providers.id |
| `schedule_id` | UUID | NOT NULL | — | FK → hcs_provider_schedules.id |
| `slot_start` | TIMESTAMP | NOT NULL | — | UTC |
| `slot_end` | TIMESTAMP | NOT NULL | — | UTC |
| `appointment_type` | VARCHAR(50) | NOT NULL | — | |
| `status` | VARCHAR(20) | NOT NULL | 'available' | CHECK IN ('available','booked','blocked','cancelled') |
| `blocked_reason` | TEXT | NULL | — | Internal note; story 2.1.2 |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `provider_id` → `hc_providers.id`; `schedule_id` → `hcs_provider_schedules.id`
**Unique constraint:** `(branch_id, provider_id, slot_start)` — no double-booking at DB level
**Indexes:**
- `idx_hcs_slots_tenant_id` ON `(tenant_id)`
- `idx_hcs_slots_availability` ON `(branch_id, provider_id, slot_start, status)` — primary query path for booking flow
- `idx_hcs_slots_status` ON `(branch_id, status, slot_start)`
- `idx_hcs_slots_created_at` ON `(created_at)`

---

### Table: `hcs_appointments` [PHI]

Booked appointments (patient ↔ provider ↔ branch). Supports stories 2.2.1, 2.2.2, 2.2.3, 7.2.1.

> **PHI encryption required (ADR-HC-002):** `patient_notes` must be encrypted at rest.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `patient_id` | UUID | NOT NULL | — | FK → hc_patients.id |
| `provider_id` | UUID | NOT NULL | — | FK → hc_providers.id |
| `slot_id` | UUID | NOT NULL | — | FK → hcs_appointment_slots.id |
| `appointment_type` | VARCHAR(50) | NOT NULL | — | |
| `status` | VARCHAR(30) | NOT NULL | 'confirmed' | CHECK IN ('confirmed','checked_in','in_progress','completed','cancelled','no_show','rescheduled') |
| `reference_code` | VARCHAR(20) | NOT NULL | — | Human-readable reference; UNIQUE |
| `patient_notes` | TEXT (encrypted) | NULL | — | [PHI] Patient-entered notes at booking time |
| `cancellation_reason` | TEXT | NULL | — | Internal; no PHI |
| `rescheduled_to_id` | UUID | NULL | — | FK → hcs_appointments.id; self-ref |
| `cancelled_at` | TIMESTAMP | NULL | — | |
| `checked_in_at` | TIMESTAMP | NULL | — | |
| `completed_at` | TIMESTAMP | NULL | — | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `patient_id` → `hc_patients.id`; `provider_id` → `hc_providers.id`; `slot_id` → `hcs_appointment_slots.id`; `rescheduled_to_id` → `hcs_appointments.id`
**Indexes:**
- `idx_hcs_appointments_tenant_id` ON `(tenant_id)`
- `idx_hcs_appointments_branch_patient` ON `(branch_id, patient_id)`
- `idx_hcs_appointments_branch_status` ON `(branch_id, status)`
- `idx_hcs_appointments_provider_date` ON `(branch_id, provider_id, slot_id)`
- `idx_hcs_appointments_patient_status` ON `(patient_id, status)` — patient portal cross-tenant query
- `idx_hcs_appointments_reference_code` ON `(reference_code)` UNIQUE
- `idx_hcs_appointments_created_at` ON `(created_at)`

**RLS policy:** `tenant_id = current_setting('app.tenant_id') AND (branch_id = current_setting('app.branch_id') OR current_setting('app.branch_id') = 'ALL')`

---

### Table: `hcs_waitlist`

Waitlist entries per slot/provider. Supports story 2.4.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `patient_id` | UUID | NOT NULL | — | FK → hc_patients.id |
| `provider_id` | UUID | NULL | — | FK → hc_providers.id; NULL = any provider |
| `appointment_type` | VARCHAR(50) | NOT NULL | — | |
| `preferred_date_from` | DATE | NOT NULL | — | |
| `preferred_date_to` | DATE | NOT NULL | — | CHECK preferred_date_to >= preferred_date_from |
| `status` | VARCHAR(20) | NOT NULL | 'waiting' | CHECK IN ('waiting','offered','expired','booked','removed') |
| `offered_slot_id` | UUID | NULL | — | FK → hcs_appointment_slots.id; set when slot offered |
| `offer_expires_at` | TIMESTAMP | NULL | — | 15-minute claim window |
| `position` | INTEGER | NOT NULL | — | FIFO position; managed by application layer |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `patient_id` → `hc_patients.id`; `provider_id` → `hc_providers.id`; `offered_slot_id` → `hcs_appointment_slots.id`
**Indexes:**
- `idx_hcs_waitlist_tenant_id` ON `(tenant_id)`
- `idx_hcs_waitlist_branch_status` ON `(branch_id, status, position)`
- `idx_hcs_waitlist_patient_id` ON `(patient_id, status)` — patient portal view
- `idx_hcs_waitlist_created_at` ON `(created_at)`

---

### Table: `hcs_notification_log`

Outbound notification records. Supports story 2.3.1. No PHI in message body (enforced by CHECK constraint).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | |
| `appointment_id` | UUID | NOT NULL | — | FK → hcs_appointments.id |
| `notification_type` | VARCHAR(50) | NOT NULL | — | CHECK IN ('appointment_confirmed','appointment_reminder_24h','appointment_reminder_2h','appointment_cancelled','appointment_rescheduled','waitlist_offer') |
| `channel` | VARCHAR(20) | NOT NULL | — | CHECK IN ('whatsapp','sms','email','in_app') |
| `recipient_phone_hash` | VARCHAR(64) | NOT NULL | — | SHA-256 hash of recipient phone — NO raw phone stored here |
| `template_key` | VARCHAR(100) | NOT NULL | — | Translation template key used; no PHI in body |
| `locale` | VARCHAR(10) | NOT NULL | 'id-ID' | |
| `status` | VARCHAR(20) | NOT NULL | 'pending' | CHECK IN ('pending','sent','failed','delivered') |
| `sent_at` | TIMESTAMP | NULL | — | |
| `delivered_at` | TIMESTAMP | NULL | — | |
| `failure_reason` | TEXT | NULL | — | |
| `retry_count` | SMALLINT | NOT NULL | 0 | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `appointment_id` → `hcs_appointments.id`
**CHECK constraint:** Application-layer enforcement that `template_key` does not reference PHI columns (no patient name, diagnosis, or doctor name in template key patterns that would include PHI).
**Indexes:**
- `idx_hcs_notification_log_tenant_id` ON `(tenant_id)`
- `idx_hcs_notification_log_branch_id` ON `(branch_id)`
- `idx_hcs_notification_log_appointment_id` ON `(appointment_id)`
- `idx_hcs_notification_log_status` ON `(status, created_at)`
- `idx_hcs_notification_log_created_at` ON `(created_at)`

---

## Module: healthcare_billing

### Table: `hcb_service_items`

Billable service catalog per branch. Supports story 3.1.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `service_code` | VARCHAR(50) | NOT NULL | — | ICD-10 or internal code |
| `service_name` | VARCHAR(255) | NOT NULL | — | |
| `service_name_id` | VARCHAR(255) | NULL | — | Bahasa Indonesia name |
| `category` | VARCHAR(50) | NOT NULL | — | e.g. 'consultation','procedure','lab','pharmacy' |
| `unit_price` | NUMERIC(14,2) | NOT NULL | — | IDR, CHECK >= 0 |
| `currency` | VARCHAR(3) | NOT NULL | 'IDR' | ISO 4217 |
| `tax_rate` | NUMERIC(5,4) | NOT NULL | 0.0000 | e.g. 0.1100 for 11% PPN |
| `bpjs_tariff` | NUMERIC(14,2) | NULL | — | BPJS reimbursement rate |
| `is_bpjs_eligible` | BOOLEAN | NOT NULL | FALSE | |
| `is_active` | BOOLEAN | NOT NULL | TRUE | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`
**Unique constraint:** `(tenant_id, branch_id, service_code)`
**Indexes:**
- `idx_hcb_service_items_tenant_id` ON `(tenant_id)`
- `idx_hcb_service_items_branch_id` ON `(branch_id)`
- `idx_hcb_service_items_code` ON `(branch_id, service_code)`
- `idx_hcb_service_items_created_at` ON `(created_at)`

---

### Table: `hcb_invoices` [PHI]

Encounter-linked invoices. Supports stories 3.1.1, 3.1.2, 3.4.2.

> **PHI encryption required (ADR-HC-002):** `hcb_invoices` links `patient_id` and `encounter_id` which are PHI pointers. The table itself must be covered by RLS. No clinical content stored here — financial data only.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `patient_id` | UUID | NOT NULL | — | FK → hc_patients.id |
| `encounter_id` | UUID | NOT NULL | — | FK → hc_encounters.id |
| `invoice_number` | VARCHAR(50) | NOT NULL | — | Human-readable; UNIQUE per tenant |
| `status` | VARCHAR(30) | NOT NULL | 'draft' | CHECK IN ('draft','finalized','partially_paid','paid','voided') |
| `currency` | VARCHAR(3) | NOT NULL | 'IDR' | |
| `subtotal` | NUMERIC(14,2) | NOT NULL | 0 | |
| `tax_amount` | NUMERIC(14,2) | NOT NULL | 0 | |
| `total_amount` | NUMERIC(14,2) | NOT NULL | 0 | |
| `outstanding_balance` | NUMERIC(14,2) | NOT NULL | 0 | Recomputed on each payment |
| `insurance_type` | VARCHAR(20) | NULL | — | CHECK IN ('BPJS','private',NULL) |
| `coverage_status` | VARCHAR(30) | NULL | — | CHECK IN ('pending_verification','verified','rejected',NULL) |
| `coverage_checked_by` | VARCHAR(36) | NULL | — | user_id |
| `coverage_checked_at` | TIMESTAMP | NULL | — | |
| `bpjs_member_id` | VARCHAR(30) | NULL | — | From hcb_insurance_profiles; denormalised for export |
| `finalized_at` | TIMESTAMP | NULL | — | Immutable after this point |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `patient_id` → `hc_patients.id`; `encounter_id` → `hc_encounters.id`
**Unique constraint:** `(tenant_id, invoice_number)`
**Indexes:**
- `idx_hcb_invoices_tenant_id` ON `(tenant_id)`
- `idx_hcb_invoices_branch_status` ON `(branch_id, status)`
- `idx_hcb_invoices_patient_id` ON `(patient_id)`
- `idx_hcb_invoices_encounter_id` ON `(encounter_id)`
- `idx_hcb_invoices_outstanding` ON `(branch_id, status, outstanding_balance)` WHERE `outstanding_balance > 0`
- `idx_hcb_invoices_created_at` ON `(created_at)`

**RLS policy:** same branch-scoped RLS as `hc_encounters`.

---

### Table: `hcb_invoice_lines`

Line items per invoice. Supports story 3.1.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `invoice_id` | UUID | NOT NULL | — | FK → hcb_invoices.id |
| `service_item_id` | UUID | NOT NULL | — | FK → hcb_service_items.id |
| `service_code` | VARCHAR(50) | NOT NULL | — | Snapshot at invoice time |
| `service_name` | VARCHAR(255) | NOT NULL | — | Snapshot |
| `quantity` | NUMERIC(10,2) | NOT NULL | 1 | |
| `unit_price` | NUMERIC(14,2) | NOT NULL | — | Snapshot at invoice time |
| `discount_amount` | NUMERIC(14,2) | NOT NULL | 0 | |
| `line_total` | NUMERIC(14,2) | NOT NULL | — | Computed: (unit_price * quantity) - discount_amount |
| `is_bpjs_covered` | BOOLEAN | NOT NULL | FALSE | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `invoice_id` → `hcb_invoices.id`; `service_item_id` → `hcb_service_items.id`
**Indexes:**
- `idx_hcb_invoice_lines_tenant_id` ON `(tenant_id)`
- `idx_hcb_invoice_lines_invoice_id` ON `(invoice_id)`
- `idx_hcb_invoice_lines_created_at` ON `(created_at)`

---

### Table: `hcb_payments`

Payment records against invoices. Supports story 3.3.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `invoice_id` | UUID | NOT NULL | — | FK → hcb_invoices.id |
| `amount` | NUMERIC(14,2) | NOT NULL | — | CHECK > 0 |
| `currency` | VARCHAR(3) | NOT NULL | 'IDR' | |
| `payment_method` | VARCHAR(20) | NOT NULL | — | CHECK IN ('cash','transfer','BPJS','insurance','other') |
| `reference` | VARCHAR(100) | NULL | — | Bank transfer ref or receipt number |
| `paid_at` | TIMESTAMP | NOT NULL | — | |
| `recorded_by` | VARCHAR(36) | NOT NULL | — | user_id of billing staff |
| `receipt_url` | TEXT | NULL | — | Object storage URL for receipt PDF |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `invoice_id` → `hcb_invoices.id`
**Indexes:**
- `idx_hcb_payments_tenant_id` ON `(tenant_id)`
- `idx_hcb_payments_invoice_id` ON `(invoice_id)`
- `idx_hcb_payments_branch_date` ON `(branch_id, paid_at)`
- `idx_hcb_payments_created_at` ON `(created_at)`

---

### Table: `hcb_insurance_profiles` [PHI]

Patient insurance data. Supports story 3.4.1.

> **PHI encryption required (ADR-HC-002):** `member_id`, `policy_number` must be encrypted at rest.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `patient_id` | UUID | NOT NULL | — | FK → hc_patients.id |
| `insurance_type` | VARCHAR(20) | NOT NULL | — | CHECK IN ('BPJS','private') |
| `member_id` | VARCHAR(50) (encrypted) | NOT NULL | — | [PHI] BPJS member no. or insurer member ID |
| `policy_number` | VARCHAR(50) (encrypted) | NULL | — | [PHI] Private insurance policy number |
| `insurer_name` | VARCHAR(100) | NULL | — | Private insurer name; no PHI |
| `coverage_class` | VARCHAR(10) | NULL | — | BPJS class 1/2/3 or NULL |
| `valid_from` | DATE | NOT NULL | — | |
| `valid_to` | DATE | NULL | — | NULL = ongoing |
| `is_active` | BOOLEAN | NOT NULL | TRUE | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `patient_id` → `hc_patients.id`
**Indexes:**
- `idx_hcb_insurance_profiles_tenant_id` ON `(tenant_id)`
- `idx_hcb_insurance_profiles_branch_patient` ON `(branch_id, patient_id)`
- `idx_hcb_insurance_profiles_patient_id` ON `(patient_id, insurance_type)`
- `idx_hcb_insurance_profiles_created_at` ON `(created_at)`

**RLS policy:** same branch-scoped RLS.

---

### Table: `hcb_bpjs_exports`

BPJS export job records (file metadata only; no claim content stored in this table). Supports story 3.2.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `period_from` | DATE | NOT NULL | — | |
| `period_to` | DATE | NOT NULL | — | |
| `format_version` | VARCHAR(20) | NOT NULL | — | BPJS format version code |
| `record_count` | INTEGER | NOT NULL | 0 | |
| `status` | VARCHAR(20) | NOT NULL | 'pending' | CHECK IN ('pending','processing','completed','failed') |
| `file_url` | TEXT | NULL | — | Signed object storage URL; NULL until completed |
| `file_expires_at` | TIMESTAMP | NULL | — | Download link expiry (24h from generation) |
| `generated_by` | VARCHAR(36) | NOT NULL | — | user_id |
| `error_message` | TEXT | NULL | — | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`
**Indexes:**
- `idx_hcb_bpjs_exports_tenant_id` ON `(tenant_id)`
- `idx_hcb_bpjs_exports_branch_id` ON `(branch_id)`
- `idx_hcb_bpjs_exports_period` ON `(branch_id, period_from, period_to)`
- `idx_hcb_bpjs_exports_created_at` ON `(created_at)`

---

## Module: healthcare_pharmacy

### Table: `hcp_medication_catalog`

Drug master per branch (adapter-sourced or manually entered). Supports stories 4.1.1, 4.1.2.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `drug_name` | VARCHAR(255) | NOT NULL | — | Trade name |
| `generic_name` | VARCHAR(255) | NOT NULL | — | INN generic name |
| `dosage_form` | VARCHAR(50) | NOT NULL | — | e.g. 'tablet','capsule','syrup','injection' |
| `strength` | VARCHAR(50) | NOT NULL | — | e.g. '500mg', '10mg/5ml' |
| `unit` | VARCHAR(20) | NOT NULL | — | e.g. 'tablet', 'ml', 'vial' |
| `drug_code` | VARCHAR(50) | NULL | — | External adapter drug code (MIMS or equivalent) |
| `current_stock` | INTEGER | NOT NULL | 0 | CHECK >= 0 |
| `reorder_threshold` | INTEGER | NOT NULL | 0 | CHECK >= 0 |
| `is_active` | BOOLEAN | NOT NULL | TRUE | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`
**Indexes:**
- `idx_hcp_medication_catalog_tenant_id` ON `(tenant_id)`
- `idx_hcp_medication_catalog_branch_id` ON `(branch_id)`
- `idx_hcp_medication_catalog_search` ON `(branch_id, drug_name, generic_name)` — full-text search candidate
- `idx_hcp_medication_catalog_low_stock` ON `(branch_id, current_stock, reorder_threshold)` WHERE `is_active = TRUE`
- `idx_hcp_medication_catalog_created_at` ON `(created_at)`

---

### Table: `hcp_prescriptions` [PHI]

Prescriptions per encounter. Supports stories 4.2.1, 4.2.2.

> **PHI encryption required (ADR-HC-002):** `hcp_prescriptions` links `patient_id` and `encounter_id`. The table is PHI by association and must be RLS-protected.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `encounter_id` | UUID | NOT NULL | — | FK → hc_encounters.id |
| `patient_id` | UUID | NOT NULL | — | FK → hc_patients.id |
| `prescribing_provider_id` | UUID | NOT NULL | — | FK → hc_providers.id |
| `status` | VARCHAR(30) | NOT NULL | 'pending_dispense' | CHECK IN ('pending_dispense','reviewed','dispensed','cancelled') |
| `pharmacist_notes` | TEXT | NULL | — | Internal pharmacist notes; no PHI per se |
| `interaction_check_status` | VARCHAR(20) | NOT NULL | 'pending' | CHECK IN ('pending','clear','warning','unavailable') |
| `interaction_check_result` | JSONB | NULL | — | Adapter response; cached 24h |
| `interaction_checked_at` | TIMESTAMP | NULL | — | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `encounter_id` → `hc_encounters.id`; `patient_id` → `hc_patients.id`; `prescribing_provider_id` → `hc_providers.id`
**Indexes:**
- `idx_hcp_prescriptions_tenant_id` ON `(tenant_id)`
- `idx_hcp_prescriptions_branch_status` ON `(branch_id, status)`
- `idx_hcp_prescriptions_encounter_id` ON `(encounter_id)`
- `idx_hcp_prescriptions_patient_id` ON `(patient_id)` — patient portal cross-tenant query
- `idx_hcp_prescriptions_created_at` ON `(created_at)`

**RLS policy:** same branch-scoped RLS.

---

### Table: `hcp_prescription_items`

Line items per prescription. Supports story 4.2.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | |
| `prescription_id` | UUID | NOT NULL | — | FK → hcp_prescriptions.id |
| `drug_catalog_id` | UUID | NOT NULL | — | FK → hcp_medication_catalog.id |
| `dose` | VARCHAR(50) | NOT NULL | — | e.g. '1 tablet' |
| `frequency` | VARCHAR(50) | NOT NULL | — | e.g. '3x daily' |
| `duration_days` | SMALLINT | NOT NULL | — | CHECK > 0 |
| `instructions` | TEXT | NULL | — | Free text; no PHI |
| `interaction_flagged` | BOOLEAN | NOT NULL | FALSE | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `prescription_id` → `hcp_prescriptions.id`; `drug_catalog_id` → `hcp_medication_catalog.id`
**Indexes:**
- `idx_hcp_prescription_items_tenant_id` ON `(tenant_id)`
- `idx_hcp_prescription_items_prescription_id` ON `(prescription_id)`
- `idx_hcp_prescription_items_drug_id` ON `(drug_catalog_id)`
- `idx_hcp_prescription_items_created_at` ON `(created_at)`

---

### Table: `hcp_dispensing_log` [PHI]

Dispensing records with stock deduction. Supports story 4.3.1.

> **PHI encryption required (ADR-HC-002):** This table links `prescription_id` → `patient_id`. RLS-protected as PHI.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `prescription_id` | UUID | NOT NULL | — | FK → hcp_prescriptions.id |
| `pharmacist_id` | UUID | NOT NULL | — | FK → hc_providers.id |
| `dispensed_at` | TIMESTAMP | NOT NULL | NOW() | |
| `is_partial` | BOOLEAN | NOT NULL | FALSE | |
| `partial_reason` | TEXT | NULL | — | Internal; no PHI |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `prescription_id` → `hcp_prescriptions.id`; `pharmacist_id` → `hc_providers.id`
**Indexes:**
- `idx_hcp_dispensing_log_tenant_id` ON `(tenant_id)`
- `idx_hcp_dispensing_log_branch_id` ON `(branch_id)`
- `idx_hcp_dispensing_log_prescription_id` ON `(prescription_id)`
- `idx_hcp_dispensing_log_dispensed_at` ON `(branch_id, dispensed_at)`
- `idx_hcp_dispensing_log_created_at` ON `(created_at)`

**RLS policy:** same branch-scoped RLS.

#### Sub-table: `hcp_dispensing_items`

Line items per dispensing event (stock deduction detail).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | |
| `dispense_id` | UUID | NOT NULL | — | FK → hcp_dispensing_log.id |
| `drug_catalog_id` | UUID | NOT NULL | — | FK → hcp_medication_catalog.id |
| `prescription_item_id` | UUID | NOT NULL | — | FK → hcp_prescription_items.id |
| `quantity_dispensed` | INTEGER | NOT NULL | — | CHECK > 0 |
| `stock_before` | INTEGER | NOT NULL | — | Snapshot for audit |
| `stock_after` | INTEGER | NOT NULL | — | Snapshot for audit |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

**Indexes:**
- `idx_hcp_dispensing_items_dispense_id` ON `(dispense_id)`
- `idx_hcp_dispensing_items_drug_id` ON `(drug_catalog_id)`

---

### Table: `hcp_drug_interaction_log`

Adapter check results cache (no PHI — drug codes only). Supports story 4.4.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `drug_codes_hash` | VARCHAR(64) | NOT NULL | — | SHA-256 of sorted drug_codes array — cache key |
| `drug_codes` | JSONB | NOT NULL | — | Array of drug codes checked; no patient linkage |
| `check_status` | VARCHAR(20) | NOT NULL | — | CHECK IN ('clear','warning','unavailable') |
| `interaction_summary` | TEXT | NULL | — | Brief description if warning; no PHI |
| `adapter_version` | VARCHAR(20) | NOT NULL | — | Drug DB adapter version |
| `checked_at` | TIMESTAMP | NOT NULL | NOW() | |
| `expires_at` | TIMESTAMP | NOT NULL | — | checked_at + 24h |

**PK:** `id`
**Unique constraint:** `(tenant_id, drug_codes_hash)` — cache lookup key
**Indexes:**
- `idx_hcp_drug_interaction_log_tenant_hash` ON `(tenant_id, drug_codes_hash)`
- `idx_hcp_drug_interaction_log_expires_at` ON `(expires_at)` — TTL cleanup job

---

## Module: healthcare_lab

### Table: `hcl_test_catalog`

Available tests per branch. Supports story 5.1.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `test_code` | VARCHAR(50) | NOT NULL | — | e.g. LOINC code or internal |
| `test_name` | VARCHAR(255) | NOT NULL | — | |
| `test_name_id` | VARCHAR(255) | NULL | — | Bahasa Indonesia name |
| `category` | VARCHAR(50) | NOT NULL | — | e.g. 'haematology','biochemistry','microbiology' |
| `specimen_types` | JSONB | NOT NULL | '[]' | Allowed specimen types for this test |
| `default_reference_range_low` | NUMERIC(12,4) | NULL | — | Default; overridable per result |
| `default_reference_range_high` | NUMERIC(12,4) | NULL | — | |
| `default_unit` | VARCHAR(20) | NULL | — | e.g. 'mg/dL', 'g/L' |
| `turnaround_hours` | SMALLINT | NULL | — | Expected TAT |
| `is_active` | BOOLEAN | NOT NULL | TRUE | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`
**Unique constraint:** `(tenant_id, branch_id, test_code)`
**Indexes:**
- `idx_hcl_test_catalog_tenant_id` ON `(tenant_id)`
- `idx_hcl_test_catalog_branch_id` ON `(branch_id)`
- `idx_hcl_test_catalog_code` ON `(branch_id, test_code)`
- `idx_hcl_test_catalog_created_at` ON `(created_at)`

---

### Table: `hcl_test_orders` [PHI]

Lab orders per encounter. Supports stories 5.1.1, 5.1.2.

> **PHI encryption required (ADR-HC-002):** PHI by association (`patient_id`, `encounter_id`). RLS-protected.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `patient_id` | UUID | NOT NULL | — | FK → hc_patients.id |
| `encounter_id` | UUID | NOT NULL | — | FK → hc_encounters.id |
| `ordering_provider_id` | UUID | NOT NULL | — | FK → hc_providers.id |
| `reference_code` | VARCHAR(20) | NOT NULL | — | UNIQUE; shown in notifications (no PHI) |
| `status` | VARCHAR(30) | NOT NULL | 'ordered' | CHECK IN ('ordered','specimen_pending','collected','processing','resulted','released','cancelled') |
| `accepted_by` | VARCHAR(36) | NULL | — | user_id of lab tech |
| `accepted_at` | TIMESTAMP | NULL | — | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `patient_id` → `hc_patients.id`; `encounter_id` → `hc_encounters.id`; `ordering_provider_id` → `hc_providers.id`
**Unique constraint:** `(reference_code)`
**Indexes:**
- `idx_hcl_test_orders_tenant_id` ON `(tenant_id)`
- `idx_hcl_test_orders_branch_status` ON `(branch_id, status)`
- `idx_hcl_test_orders_patient_id` ON `(patient_id)` — patient portal cross-tenant
- `idx_hcl_test_orders_encounter_id` ON `(encounter_id)`
- `idx_hcl_test_orders_created_at` ON `(created_at)`

**RLS policy:** same branch-scoped RLS.

#### Sub-table: `hcl_test_order_items`

Individual test lines per order.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | |
| `order_id` | UUID | NOT NULL | — | FK → hcl_test_orders.id |
| `test_catalog_id` | UUID | NOT NULL | — | FK → hcl_test_catalog.id |
| `clinical_indication` | TEXT | NULL | — | Free text; no sensitive clinical PHI stored here |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

**Indexes:**
- `idx_hcl_test_order_items_order_id` ON `(order_id)`

---

### Table: `hcl_specimens`

Specimen tracking (collection → processing). Supports story 5.2.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `order_id` | UUID | NOT NULL | — | FK → hcl_test_orders.id |
| `order_item_id` | UUID | NOT NULL | — | FK → hcl_test_order_items.id |
| `specimen_type` | VARCHAR(50) | NOT NULL | — | e.g. 'whole_blood','urine','serum' |
| `container_barcode` | VARCHAR(50) | NULL | — | Optional barcode scan |
| `collector_id` | VARCHAR(36) | NOT NULL | — | user_id of lab tech |
| `collection_time` | TIMESTAMP | NOT NULL | — | |
| `status` | VARCHAR(20) | NOT NULL | 'collected' | CHECK IN ('collected','processing','resulted','rejected') |
| `rejection_reason` | TEXT | NULL | — | Required if status = 'rejected' |
| `recollection_of_id` | UUID | NULL | — | FK → hcl_specimens.id; self-ref for re-collection |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `order_id` → `hcl_test_orders.id`; `order_item_id` → `hcl_test_order_items.id`; `recollection_of_id` → `hcl_specimens.id`
**Indexes:**
- `idx_hcl_specimens_tenant_id` ON `(tenant_id)`
- `idx_hcl_specimens_branch_id` ON `(branch_id)`
- `idx_hcl_specimens_order_id` ON `(order_id)`
- `idx_hcl_specimens_status` ON `(branch_id, status)`
- `idx_hcl_specimens_barcode` ON `(container_barcode)` WHERE `container_barcode IS NOT NULL`
- `idx_hcl_specimens_created_at` ON `(created_at)`

---

### Table: `hcl_results` [PHI]

Test results with reference ranges. Supports stories 5.3.1, 5.3.2.

> **PHI encryption required (ADR-HC-002):** `result_notes` may contain clinical interpretation referencing the patient. Must be encrypted at rest. Full table RLS-protected.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `order_id` | UUID | NOT NULL | — | FK → hcl_test_orders.id |
| `order_item_id` | UUID | NOT NULL | — | FK → hcl_test_order_items.id |
| `specimen_id` | UUID | NOT NULL | — | FK → hcl_specimens.id |
| `value` | VARCHAR(100) | NOT NULL | — | Result value as string (numeric or qualitative) |
| `unit` | VARCHAR(20) | NULL | — | |
| `reference_range_low` | NUMERIC(12,4) | NULL | — | |
| `reference_range_high` | NUMERIC(12,4) | NULL | — | |
| `interpretation` | VARCHAR(20) | NOT NULL | — | CHECK IN ('Normal','Abnormal','Critical') |
| `result_notes` | TEXT (encrypted) | NULL | — | [PHI] Optional lab notes |
| `entered_by` | VARCHAR(36) | NOT NULL | — | user_id of lab tech |
| `is_released` | BOOLEAN | NOT NULL | FALSE | |
| `released_at` | TIMESTAMP | NULL | — | |
| `released_by` | VARCHAR(36) | NULL | — | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `order_id` → `hcl_test_orders.id`; `order_item_id` → `hcl_test_order_items.id`; `specimen_id` → `hcl_specimens.id`
**Indexes:**
- `idx_hcl_results_tenant_id` ON `(tenant_id)`
- `idx_hcl_results_branch_id` ON `(branch_id)`
- `idx_hcl_results_order_id` ON `(order_id)`
- `idx_hcl_results_interpretation` ON `(branch_id, interpretation)` WHERE `interpretation = 'Critical'`
- `idx_hcl_results_released` ON `(order_id, is_released)`
- `idx_hcl_results_created_at` ON `(created_at)`

**RLS policy:** same branch-scoped RLS.

---

### Table: `hcl_critical_alerts`

Critical value alert records + acknowledgement. Supports story 5.4.1.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `result_id` | UUID | NOT NULL | — | FK → hcl_results.id |
| `order_id` | UUID | NOT NULL | — | FK → hcl_test_orders.id |
| `ordering_provider_id` | UUID | NOT NULL | — | FK → hc_providers.id |
| `alert_status` | VARCHAR(20) | NOT NULL | 'unacknowledged' | CHECK IN ('unacknowledged','acknowledged','escalated_manager','escalated_owner') |
| `escalation_level` | SMALLINT | NOT NULL | 0 | 0=initial, 1=manager, 2=owner |
| `acknowledged_by` | VARCHAR(36) | NULL | — | user_id |
| `acknowledged_at` | TIMESTAMP | NULL | — | |
| `notification_sent_at` | TIMESTAMP | NOT NULL | NOW() | |
| `next_escalation_at` | TIMESTAMP | NULL | — | NULL once acknowledged |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `result_id` → `hcl_results.id`; `order_id` → `hcl_test_orders.id`; `ordering_provider_id` → `hc_providers.id`
**Unique constraint:** `(result_id)` — one alert record per result
**Indexes:**
- `idx_hcl_critical_alerts_tenant_id` ON `(tenant_id)`
- `idx_hcl_critical_alerts_branch_status` ON `(branch_id, alert_status)`
- `idx_hcl_critical_alerts_unacknowledged` ON `(next_escalation_at)` WHERE `alert_status != 'acknowledged'` — escalation job query
- `idx_hcl_critical_alerts_provider_id` ON `(ordering_provider_id, alert_status)`
- `idx_hcl_critical_alerts_created_at` ON `(created_at)`

---

## Patient Portal Tables (additional — Epic 07)

Patient portal surface adds no new base tables. It reuses:

| Epic 07 Feature | Tables accessed |
|---|---|
| 7.1.1 Patient profile | `hc_patients` |
| 7.1.2 Past encounters | `hc_encounters` (cross-tenant read via patient_session) |
| 7.2.1 My appointments | `hcs_appointments` (cross-tenant by patient_id) |
| 7.3.1 My prescriptions | `hcp_prescriptions`, `hcp_prescription_items` |
| 7.3.1 My lab results | `hcl_results`, `hcl_test_orders` |
| 7.4 Reviews | `hc_clinic_reviews` (below) |

### Table: `hc_clinic_reviews`

Patient reviews and ratings per branch. No PHI. Supports stories 7.4.1, 7.4.2.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `patient_id` | UUID | NOT NULL | — | FK → hc_patients.id; NOT exposed in public API |
| `encounter_id` | UUID | NOT NULL | — | FK → hc_encounters.id; one review per encounter |
| `rating` | SMALLINT | NOT NULL | — | CHECK BETWEEN 1 AND 5 |
| `review_text` | TEXT | NULL | — | Optional; CHECK char_length <= 500; no PHI |
| `status` | VARCHAR(20) | NOT NULL | 'pending_moderation' | CHECK IN ('pending_moderation','approved','removed') |
| `moderated_at` | TIMESTAMP | NULL | — | |
| `moderated_by` | VARCHAR(36) | NULL | — | platform admin user_id |
| `staff_response` | TEXT | NULL | — | Branch manager public response |
| `staff_response_at` | TIMESTAMP | NULL | — | |
| `staff_response_by` | VARCHAR(36) | NULL | — | user_id of branch manager |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

**PK:** `id`
**FKs:** `branch_id` → `hc_branches.id`; `patient_id` → `hc_patients.id`; `encounter_id` → `hc_encounters.id`
**Unique constraint:** `(encounter_id)` — one review per encounter
**Indexes:**
- `idx_hc_clinic_reviews_tenant_id` ON `(tenant_id)`
- `idx_hc_clinic_reviews_branch_status` ON `(branch_id, status, created_at DESC)` — public listing query
- `idx_hc_clinic_reviews_patient_id` ON `(patient_id)`
- `idx_hc_clinic_reviews_created_at` ON `(created_at)`

---

## Table Count Summary

| Module | Tables | PHI Tables |
|---|---|---|
| healthcare (base) | 8 (`hc_branches`, `hc_branch_staff`, `hc_patients`, `hc_patient_consents`, `hc_providers`, `hc_encounters`, `hc_audit_log`, `hc_i18n_overrides`) + 1 portal (`hc_clinic_reviews`) = **9** | `hc_patients`, `hc_encounters` = **2** |
| healthcare_scheduling | 5 (`hcs_provider_schedules`, `hcs_appointment_slots`, `hcs_appointments`, `hcs_waitlist`, `hcs_notification_log`) | `hcs_appointments` = **1** |
| healthcare_billing | 6 (`hcb_service_items`, `hcb_invoices`, `hcb_invoice_lines`, `hcb_payments`, `hcb_insurance_profiles`, `hcb_bpjs_exports`) | `hcb_invoices`, `hcb_insurance_profiles` = **2** |
| healthcare_pharmacy | 5 (`hcp_medication_catalog`, `hcp_prescriptions`, `hcp_prescription_items`, `hcp_dispensing_log`, `hcp_drug_interaction_log`) + 1 sub (`hcp_dispensing_items`) = **6** | `hcp_prescriptions`, `hcp_dispensing_log` = **2** |
| healthcare_lab | 5 (`hcl_test_catalog`, `hcl_test_orders`, `hcl_specimens`, `hcl_results`, `hcl_critical_alerts`) + 2 sub (`hcl_test_order_items`, patient view table) = **7** | `hcl_test_orders`, `hcl_results` = **2** |
| **TOTAL** | **33** | **9** |

---

*Epic-06 (Telemedicine) excluded — pending legal review.*
