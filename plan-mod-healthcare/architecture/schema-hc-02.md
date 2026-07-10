---
artifact_id: schema-hc-02
type: schema-design
module: healthcare + healthcare_registration + healthcare_emr + healthcare_reporting
status: proposed
producer: B1 Backend Architect
upstream: [schema-hc-01, adr-hc-001, adr-hc-002, adr-hc-005, adr-hc-006, adr-hc-007, adr-hc-008, BACKLOG.md (v3)]
created: 2026-07-02
updated: 2026-07-06
changelog:
  - "2026-07-06 (B1): §A.2 hc_departments gains optional nullable platform_department_id FK →
     departments.id (no unique) per ADR-HC-005 addendum A3 / epic-08 v2 Story 8.2.4 (accepted).
     No other tables/columns changed; 8.1.3/8.1.4/8.1.5 reuse the existing three hc_branches.platform_*
     columns in §A.1."
---

# Schema Design v2 — Healthcare Org, Visit/Queue, Clinical Coding & Reporting

> Extends `schema-hc-01`. This document covers **only new objects** introduced by ADR-HC-005..008:
> the `hc_branches` platform-linkage columns, `hc_departments` + `hc_provider_departments`
> (ADR-HC-005), `hcr_visits` + `hcr_queue_tickets` (ADR-HC-006), `hc_icd10_codes` / `hc_icd9cm_codes`
> + `hc_diagnoses` / `hc_procedures` / `hc_clinical_notes` (ADR-HC-007), and eight reporting views
> (ADR-HC-008). Conventions, PHI encryption (`EncryptedPHIType`, AES-256), and the RLS style are
> inherited **verbatim** from `schema-hc-01` §Conventions.

## Conventions (inherited from schema-hc-01)

| Convention | Rule |
|---|---|
| `tenant_id` | `VARCHAR(36) NOT NULL`, indexed |
| `branch_id` | `VARCHAR(36) NOT NULL` on branch-scoped tables; healthcare `branch_id` = `hc_branches.id` (ADR-HC-005) |
| `[PHI]` | AES-256 encrypted at rest via `EncryptedPHIType`; access audit-logged via `hc_audit_log` (ADR-HC-002) |
| PK | UUID v4 (`GUID`), server-side |
| Timestamps | UTC `TIMESTAMP WITHOUT TIME ZONE` |
| **RLS (branch-scoped)** | `tenant_id = current_setting('app.tenant_id') AND (branch_id = current_setting('app.branch_id') OR current_setting('app.branch_id') = 'ALL')` |
| **RLS (tenant-scoped)** | `tenant_id = current_setting('app.tenant_id')` |
| Soft delete | `deleted_at TIMESTAMP NULL` where logically deletable; clinical/coding records are immutable (no `deleted_at`) |

> DDL below is Postgres. `gen_random_uuid()` (pgcrypto/pg13+) stands in for the app's `GUID` default;
> encrypted columns are `BYTEA`/`TEXT` at the DB level, mapped by `EncryptedPHIType` in the ORM.

---

## Part A — Organization & Departments (ADR-HC-005)

### A.1 `hc_branches` — new platform-linkage columns (ALTER)

Read-only FK linkage to the platform org hierarchy. Healthcare owns these columns; platform tables
(`companies`, `branches`, `departments`) are **not** modified. All nullable (ADR-HC-005 D1).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `platform_company_id` | VARCHAR(36) | NULL | — | FK → `companies.id` |
| `platform_branch_id` | VARCHAR(36) | NULL | — | FK → `branches.id`; 1:1 with the clinic |
| `platform_department_id` | VARCHAR(36) | NULL | — | FK → `departments.id`; optional roll-up |

```sql
ALTER TABLE hc_branches
    ADD COLUMN platform_company_id    VARCHAR(36) NULL,
    ADD COLUMN platform_branch_id     VARCHAR(36) NULL,
    ADD COLUMN platform_department_id VARCHAR(36) NULL;

ALTER TABLE hc_branches
    ADD CONSTRAINT fk_hc_branches_platform_company
        FOREIGN KEY (platform_company_id)    REFERENCES companies(id),
    ADD CONSTRAINT fk_hc_branches_platform_branch
        FOREIGN KEY (platform_branch_id)     REFERENCES branches(id),
    ADD CONSTRAINT fk_hc_branches_platform_department
        FOREIGN KEY (platform_department_id) REFERENCES departments(id);

-- 1:1 clinic ⇄ platform branch (allow multiple NULLs)
CREATE UNIQUE INDEX uq_hc_branches_platform_branch
    ON hc_branches (platform_branch_id) WHERE platform_branch_id IS NOT NULL;

CREATE INDEX idx_hc_branches_platform_company ON hc_branches (platform_company_id);
```

**App-enforced invariant (ADR-HC-005 D1):** on linkage, `hc_branches.tenant_id = branches.tenant_id`
(not expressible as a DB CHECK across the FK). `hc_branches` remains tenant-scoped (RLS unchanged); no
new PHI. Existing rows migrate with all three columns NULL.

---

### A.2 `hc_departments` — clinical departments (ADR-HC-005 D2)

Branch-scoped. `kind` drives queue routing (ADR-HC-006), coding scope (ADR-HC-007), reporting
(ADR-HC-008). Not PHI.

> **Delta (2026-07-06, ADR-HC-005 addendum A3 / epic-08 Story 8.2.4 accepted):** adds the optional,
> nullable `platform_department_id` FK below. It is a **reporting-alignment pointer only** to a
> platform org-chart `departments` node — **default NULL, no unique constraint** (many clinical
> departments MAY roll up to one platform Department, N:1). It does **not** couple the clinical
> `kind` taxonomy or branch-scoping to the platform tree, and is **distinct** from
> `hc_branches.platform_department_id` (§A.1), which rolls up the *whole clinic site*. Validation is
> app-enforced fail-closed (422 out-of-tenant/company, 503 when platform-org lookup unavailable),
> same posture as §A.1 and ADR-HC-009 D5 (real FK in shared `appdb`; app-enforced when split-DB).
> **ORM:** add `platform_department_id = Column(String(36), ForeignKey("departments.id"),
> nullable=True)` to `HCDepartment` in `modules/healthcare/backend/models.py` (after the `kind`
> column, currently line 131).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `code` | VARCHAR(50) | NOT NULL | — | Short department code |
| `name` | VARCHAR(255) | NOT NULL | — | |
| `kind` | VARCHAR(20) | NOT NULL | — | CHECK IN ('medical','pharmacy','laboratory','radiology','administration','finance') |
| `platform_department_id` | VARCHAR(36) | NULL | — | FK → departments.id; optional org-chart roll-up (no unique) — ADR-HC-005 addendum A3 |
| `is_active` | BOOLEAN | NOT NULL | TRUE | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

```sql
CREATE TABLE hc_departments (
    id                     VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id              VARCHAR(36) NOT NULL,
    branch_id              VARCHAR(36) NOT NULL REFERENCES hc_branches(id),
    code                   VARCHAR(50) NOT NULL,
    name                   VARCHAR(255) NOT NULL,
    kind                   VARCHAR(20) NOT NULL,
    -- optional org-chart roll-up (ADR-HC-005 addendum A3 / Story 8.2.4); nullable, NOT unique (N:1);
    -- reporting-alignment only, no lifecycle coupling; app-validated same-tenant/company, fail-closed.
    platform_department_id VARCHAR(36) NULL REFERENCES departments(id),
    is_active              BOOLEAN NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_hc_departments_code UNIQUE (tenant_id, branch_id, code),
    CONSTRAINT ck_hc_departments_kind
        CHECK (kind IN ('medical','pharmacy','laboratory','radiology','administration','finance'))
);
CREATE INDEX idx_hc_departments_tenant_id     ON hc_departments (tenant_id);
CREATE INDEX idx_hc_departments_tenant_branch ON hc_departments (tenant_id, branch_id);
CREATE INDEX idx_hc_departments_kind          ON hc_departments (tenant_id, branch_id, kind);
CREATE INDEX idx_hc_departments_platform_dept ON hc_departments (platform_department_id)
    WHERE platform_department_id IS NOT NULL;
CREATE INDEX idx_hc_departments_created_at    ON hc_departments (created_at);

ALTER TABLE hc_departments ENABLE ROW LEVEL SECURITY;
CREATE POLICY rls_hc_departments ON hc_departments
    USING (tenant_id = current_setting('app.tenant_id')
       AND (branch_id = current_setting('app.branch_id')
            OR current_setting('app.branch_id') = 'ALL'));
```

---

### A.3 `hc_provider_departments` — provider ↔ department assignment (ADR-HC-005 D3)

Branch-scoped join table. Not PHI.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `provider_id` | UUID | NOT NULL | — | FK → hc_providers.id |
| `department_id` | UUID | NOT NULL | — | FK → hc_departments.id |
| `is_primary` | BOOLEAN | NOT NULL | FALSE | Provider's home department |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

```sql
CREATE TABLE hc_provider_departments (
    id            VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     VARCHAR(36) NOT NULL,
    branch_id     VARCHAR(36) NOT NULL REFERENCES hc_branches(id),
    provider_id   VARCHAR(36) NOT NULL REFERENCES hc_providers(id),
    department_id VARCHAR(36) NOT NULL REFERENCES hc_departments(id),
    is_primary    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_hc_provider_departments
        UNIQUE (tenant_id, branch_id, provider_id, department_id)
);
CREATE INDEX idx_hc_provider_departments_tenant_id  ON hc_provider_departments (tenant_id);
CREATE INDEX idx_hc_provider_departments_provider   ON hc_provider_departments (branch_id, provider_id);
CREATE INDEX idx_hc_provider_departments_department ON hc_provider_departments (branch_id, department_id);
-- at most one primary (home) department per provider per branch
CREATE UNIQUE INDEX uq_hc_provider_departments_primary
    ON hc_provider_departments (tenant_id, branch_id, provider_id) WHERE is_primary;

ALTER TABLE hc_provider_departments ENABLE ROW LEVEL SECURITY;
CREATE POLICY rls_hc_provider_departments ON hc_provider_departments
    USING (tenant_id = current_setting('app.tenant_id')
       AND (branch_id = current_setting('app.branch_id')
            OR current_setting('app.branch_id') = 'ALL'));
```

**App-enforced:** `provider_id` and `department_id` must share the row's `(tenant_id, branch_id)`.

---

## Part B — Visit / Registration & Queue (ADR-HC-006)

### B.1 `hcr_visits` [PHI-by-association] — check-in / registration

Branch-scoped. No free-text clinical content; PHI-by-association (`patient_id`, `encounter_id`) —
RLS-protected, no `EncryptedPHIType` column (same stance as `hcb_invoices` in schema-hc-01).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `patient_id` | UUID | NOT NULL | — | FK → hc_patients.id |
| `appointment_id` | UUID | NULL | — | FK → hcs_appointments.id; NULL for walk-in |
| `visit_type` | VARCHAR(20) | NOT NULL | — | CHECK IN ('appointment','walk_in') |
| `payment_category` | VARCHAR(30) | NOT NULL | — | CHECK IN ('self_pay','bpjs','private_insurance','corporate') |
| `insurance_profile_id` | UUID | NULL | — | FK → hcb_insurance_profiles.id; NULL for self-pay |
| `referral_source` | VARCHAR(50) | NOT NULL | 'self' | e.g. 'self','gp_referral','internal','corporate' |
| `department_id` | UUID | NOT NULL | — | FK → hc_departments.id (routing, ADR-HC-005) |
| `status` | VARCHAR(20) | NOT NULL | 'registered' | CHECK IN ('registered','waiting','in_service','completed','cancelled') |
| `checked_in_at` | TIMESTAMP | NOT NULL | NOW() | |
| `encounter_id` | UUID | NULL | — | FK → hc_encounters.id; set when clinician opens encounter |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

```sql
CREATE TABLE hcr_visits (
    id                   VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id            VARCHAR(36) NOT NULL,
    branch_id            VARCHAR(36) NOT NULL REFERENCES hc_branches(id),
    patient_id           VARCHAR(36) NOT NULL REFERENCES hc_patients(id),
    appointment_id       VARCHAR(36) NULL REFERENCES hcs_appointments(id),
    visit_type           VARCHAR(20) NOT NULL,
    payment_category     VARCHAR(30) NOT NULL,
    insurance_profile_id VARCHAR(36) NULL REFERENCES hcb_insurance_profiles(id),
    referral_source      VARCHAR(50) NOT NULL DEFAULT 'self',
    department_id        VARCHAR(36) NOT NULL REFERENCES hc_departments(id),
    status               VARCHAR(20) NOT NULL DEFAULT 'registered',
    checked_in_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    encounter_id         VARCHAR(36) NULL REFERENCES hc_encounters(id),
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_hcr_visits_visit_type
        CHECK (visit_type IN ('appointment','walk_in')),
    CONSTRAINT ck_hcr_visits_payment_category
        CHECK (payment_category IN ('self_pay','bpjs','private_insurance','corporate')),
    CONSTRAINT ck_hcr_visits_status
        CHECK (status IN ('registered','waiting','in_service','completed','cancelled')),
    -- appointment visits must carry an appointment; walk-ins must not
    CONSTRAINT ck_hcr_visits_appt_link
        CHECK ((visit_type = 'appointment' AND appointment_id IS NOT NULL)
            OR (visit_type = 'walk_in'     AND appointment_id IS NULL))
);
CREATE INDEX idx_hcr_visits_tenant_id      ON hcr_visits (tenant_id);
CREATE INDEX idx_hcr_visits_branch_status  ON hcr_visits (branch_id, status);
CREATE INDEX idx_hcr_visits_branch_day     ON hcr_visits (branch_id, checked_in_at);
CREATE INDEX idx_hcr_visits_patient_id     ON hcr_visits (patient_id);
CREATE INDEX idx_hcr_visits_appointment_id ON hcr_visits (appointment_id) WHERE appointment_id IS NOT NULL;
CREATE INDEX idx_hcr_visits_encounter_id   ON hcr_visits (encounter_id) WHERE encounter_id IS NOT NULL;
CREATE INDEX idx_hcr_visits_department     ON hcr_visits (branch_id, department_id, status);
CREATE INDEX idx_hcr_visits_created_at     ON hcr_visits (created_at);

ALTER TABLE hcr_visits ENABLE ROW LEVEL SECURITY;
CREATE POLICY rls_hcr_visits ON hcr_visits
    USING (tenant_id = current_setting('app.tenant_id')
       AND (branch_id = current_setting('app.branch_id')
            OR current_setting('app.branch_id') = 'ALL'));
```

---

### B.2 `hcr_queue_tickets` — queue lifecycle

Branch-scoped. Not PHI (numbers/status/timestamps only). Transfer to another department closes the
ticket and links a new ticket via `transferred_to_id` (ADR-HC-006 D2).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `visit_id` | UUID | NOT NULL | — | FK → hcr_visits.id |
| `department_id` | UUID | NOT NULL | — | FK → hc_departments.id |
| `ticket_number` | VARCHAR(20) | NOT NULL | — | Human-facing; unique per branch/dept/day |
| `station` | VARCHAR(50) | NULL | — | Counter/room the ticket is called to |
| `status` | VARCHAR(20) | NOT NULL | 'waiting' | CHECK IN ('waiting','called','skipped','recalled','transferred','served') |
| `service_day` | DATE | NOT NULL | — | Local service date; ticket-number scope |
| `transferred_to_id` | UUID | NULL | — | FK → hcr_queue_tickets.id; self-ref on transfer |
| `called_at` | TIMESTAMP | NULL | — | |
| `served_at` | TIMESTAMP | NULL | — | |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

```sql
CREATE TABLE hcr_queue_tickets (
    id                VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         VARCHAR(36) NOT NULL,
    branch_id         VARCHAR(36) NOT NULL REFERENCES hc_branches(id),
    visit_id          VARCHAR(36) NOT NULL REFERENCES hcr_visits(id),
    department_id     VARCHAR(36) NOT NULL REFERENCES hc_departments(id),
    ticket_number     VARCHAR(20) NOT NULL,
    station           VARCHAR(50) NULL,
    status            VARCHAR(20) NOT NULL DEFAULT 'waiting',
    service_day       DATE NOT NULL,
    transferred_to_id VARCHAR(36) NULL REFERENCES hcr_queue_tickets(id),
    called_at         TIMESTAMP NULL,
    served_at         TIMESTAMP NULL,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_hcr_queue_tickets_status
        CHECK (status IN ('waiting','called','skipped','recalled','transferred','served')),
    CONSTRAINT uq_hcr_queue_tickets_number
        UNIQUE (branch_id, department_id, service_day, ticket_number)
);
CREATE INDEX idx_hcr_queue_tickets_tenant_id   ON hcr_queue_tickets (tenant_id);
CREATE INDEX idx_hcr_queue_tickets_visit_id    ON hcr_queue_tickets (visit_id);
-- primary queue-board query: current tickets for a dept, ordered
CREATE INDEX idx_hcr_queue_tickets_board
    ON hcr_queue_tickets (branch_id, department_id, service_day, status, created_at);
CREATE INDEX idx_hcr_queue_tickets_created_at  ON hcr_queue_tickets (created_at);

ALTER TABLE hcr_queue_tickets ENABLE ROW LEVEL SECURITY;
CREATE POLICY rls_hcr_queue_tickets ON hcr_queue_tickets
    USING (tenant_id = current_setting('app.tenant_id')
       AND (branch_id = current_setting('app.branch_id')
            OR current_setting('app.branch_id') = 'ALL'));
```

> Queue-board delivery is **short-polling** of a branch-scoped read endpoint with a `queue_version`
> (max `updated_at` per department) for a future SSE upgrade — ADR-HC-006 D3. No schema impact.

---

## Part C — Clinical Coding & Notes (ADR-HC-007)

### C.1 `hc_icd10_codes` — diagnosis code catalog (tenant-scoped, adapter-loaded)

Tenant-scoped reference (no `branch_id`). Loaded per tenant from the tenant's licensed dataset
(Scope-Out #13); module ships schema + adapter, not data. Not PHI.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `code` | VARCHAR(10) | NOT NULL | — | ICD-10 code, e.g. 'J45.909' |
| `description` | VARCHAR(500) | NOT NULL | — | English description |
| `description_id` | VARCHAR(500) | NULL | — | Bahasa Indonesia description |
| `chapter` | VARCHAR(10) | NULL | — | ICD-10 chapter |
| `category` | VARCHAR(10) | NULL | — | 3-char category (e.g. 'J45') |
| `is_billable` | BOOLEAN | NOT NULL | TRUE | Leaf/billable code |
| `is_active` | BOOLEAN | NOT NULL | TRUE | |
| `edition` | VARCHAR(20) | NULL | — | Dataset edition/version |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

```sql
CREATE TABLE hc_icd10_codes (
    id             VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      VARCHAR(36) NOT NULL,
    code           VARCHAR(10) NOT NULL,
    description    VARCHAR(500) NOT NULL,
    description_id VARCHAR(500) NULL,
    chapter        VARCHAR(10) NULL,
    category       VARCHAR(10) NULL,
    is_billable    BOOLEAN NOT NULL DEFAULT TRUE,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    edition        VARCHAR(20) NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_hc_icd10_codes UNIQUE (tenant_id, code)
);
CREATE INDEX idx_hc_icd10_codes_tenant_id ON hc_icd10_codes (tenant_id);
CREATE INDEX idx_hc_icd10_codes_category  ON hc_icd10_codes (tenant_id, category);
-- prefix/description search for the diagnosis picker
CREATE INDEX idx_hc_icd10_codes_code_prefix ON hc_icd10_codes (tenant_id, code text_pattern_ops);
CREATE INDEX idx_hc_icd10_codes_desc_trgm  ON hc_icd10_codes USING gin (description gin_trgm_ops);

ALTER TABLE hc_icd10_codes ENABLE ROW LEVEL SECURITY;
CREATE POLICY rls_hc_icd10_codes ON hc_icd10_codes
    USING (tenant_id = current_setting('app.tenant_id'));
```

### C.2 `hc_icd9cm_codes` — procedure code catalog (tenant-scoped, adapter-loaded)

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `code` | VARCHAR(10) | NOT NULL | — | ICD-9-CM procedure code |
| `description` | VARCHAR(500) | NOT NULL | — | English description |
| `description_id` | VARCHAR(500) | NULL | — | Bahasa Indonesia description |
| `category` | VARCHAR(10) | NULL | — | Procedure category |
| `is_active` | BOOLEAN | NOT NULL | TRUE | |
| `edition` | VARCHAR(20) | NULL | — | Dataset edition/version |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

```sql
CREATE TABLE hc_icd9cm_codes (
    id             VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      VARCHAR(36) NOT NULL,
    code           VARCHAR(10) NOT NULL,
    description    VARCHAR(500) NOT NULL,
    description_id VARCHAR(500) NULL,
    category       VARCHAR(10) NULL,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    edition        VARCHAR(20) NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_hc_icd9cm_codes UNIQUE (tenant_id, code)
);
CREATE INDEX idx_hc_icd9cm_codes_tenant_id   ON hc_icd9cm_codes (tenant_id);
CREATE INDEX idx_hc_icd9cm_codes_code_prefix ON hc_icd9cm_codes (tenant_id, code text_pattern_ops);
CREATE INDEX idx_hc_icd9cm_codes_desc_trgm   ON hc_icd9cm_codes USING gin (description gin_trgm_ops);

ALTER TABLE hc_icd9cm_codes ENABLE ROW LEVEL SECURITY;
CREATE POLICY rls_hc_icd9cm_codes ON hc_icd9cm_codes
    USING (tenant_id = current_setting('app.tenant_id'));
```

> `code` values are validated against these catalogs at write time for the same `tenant_id`
> (app-enforced, ADR-HC-007 D2); no hard FK from encounter-coding rows to catalog rows, to decouple
> encounter writes from catalog-load ordering.

### C.3 `hc_diagnoses` [PHI-by-association] — encounter diagnoses (ICD-10)

Branch-scoped. Immutable (no `deleted_at`; corrections append/supersede). Not encrypted (codes only).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `encounter_id` | UUID | NOT NULL | — | FK → hc_encounters.id |
| `icd10_code` | VARCHAR(10) | NOT NULL | — | references hc_icd10_codes.code (same tenant) |
| `is_primary` | BOOLEAN | NOT NULL | FALSE | Principal diagnosis |
| `sequence` | SMALLINT | NOT NULL | 1 | Ordering of secondary Dx |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

```sql
CREATE TABLE hc_diagnoses (
    id           VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    VARCHAR(36) NOT NULL,
    branch_id    VARCHAR(36) NOT NULL REFERENCES hc_branches(id),
    encounter_id VARCHAR(36) NOT NULL REFERENCES hc_encounters(id),
    icd10_code   VARCHAR(10) NOT NULL,
    is_primary   BOOLEAN NOT NULL DEFAULT FALSE,
    sequence     SMALLINT NOT NULL DEFAULT 1,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_hc_diagnoses_tenant_id    ON hc_diagnoses (tenant_id);
CREATE INDEX idx_hc_diagnoses_encounter_id ON hc_diagnoses (encounter_id);
CREATE INDEX idx_hc_diagnoses_icd10_code   ON hc_diagnoses (tenant_id, icd10_code);  -- v_hc_disease_stats
-- at most one primary diagnosis per encounter
CREATE UNIQUE INDEX uq_hc_diagnoses_primary
    ON hc_diagnoses (encounter_id) WHERE is_primary;

ALTER TABLE hc_diagnoses ENABLE ROW LEVEL SECURITY;
CREATE POLICY rls_hc_diagnoses ON hc_diagnoses
    USING (tenant_id = current_setting('app.tenant_id')
       AND (branch_id = current_setting('app.branch_id')
            OR current_setting('app.branch_id') = 'ALL'));
```

### C.4 `hc_procedures` [PHI-by-association] — encounter procedures (ICD-9-CM)

Branch-scoped. `note` is a short structured qualifier — **not** a PHI narrative (ADR-HC-007 D2).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `encounter_id` | UUID | NOT NULL | — | FK → hc_encounters.id |
| `icd9cm_code` | VARCHAR(10) | NOT NULL | — | references hc_icd9cm_codes.code (same tenant) |
| `note` | VARCHAR(255) | NULL | — | Short structured note (e.g. laterality); no narrative |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |

```sql
CREATE TABLE hc_procedures (
    id           VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    VARCHAR(36) NOT NULL,
    branch_id    VARCHAR(36) NOT NULL REFERENCES hc_branches(id),
    encounter_id VARCHAR(36) NOT NULL REFERENCES hc_encounters(id),
    icd9cm_code  VARCHAR(10) NOT NULL,
    note         VARCHAR(255) NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_hc_procedures_tenant_id    ON hc_procedures (tenant_id);
CREATE INDEX idx_hc_procedures_encounter_id ON hc_procedures (encounter_id);
CREATE INDEX idx_hc_procedures_icd9cm_code  ON hc_procedures (tenant_id, icd9cm_code);

ALTER TABLE hc_procedures ENABLE ROW LEVEL SECURITY;
CREATE POLICY rls_hc_procedures ON hc_procedures
    USING (tenant_id = current_setting('app.tenant_id')
       AND (branch_id = current_setting('app.branch_id')
            OR current_setting('app.branch_id') = 'ALL'));
```

### C.5 `hc_clinical_notes` [PHI] — typed clinical notes

Branch-scoped. **`body` is PHI — `EncryptedPHIType` (AES-256 at rest)**, accessed via SDK readers +
audit (ADR-HC-002, ADR-HC-007 D3).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | UUID | NOT NULL | gen_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | FK → tenants.id |
| `branch_id` | VARCHAR(36) | NOT NULL | — | FK → hc_branches.id |
| `encounter_id` | UUID | NOT NULL | — | FK → hc_encounters.id |
| `note_type` | VARCHAR(20) | NOT NULL | — | CHECK IN ('progress','nursing','observation','follow_up') |
| `body` | TEXT (encrypted) | NOT NULL | — | [PHI] Clinical narrative |
| `author_id` | VARCHAR(36) | NOT NULL | — | user_id of authoring clinician |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

```sql
CREATE TABLE hc_clinical_notes (
    id           VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    VARCHAR(36) NOT NULL,
    branch_id    VARCHAR(36) NOT NULL REFERENCES hc_branches(id),
    encounter_id VARCHAR(36) NOT NULL REFERENCES hc_encounters(id),
    note_type    VARCHAR(20) NOT NULL,
    body         TEXT NOT NULL,          -- EncryptedPHIType (AES-256) in ORM
    author_id    VARCHAR(36) NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_hc_clinical_notes_type
        CHECK (note_type IN ('progress','nursing','observation','follow_up'))
);
CREATE INDEX idx_hc_clinical_notes_tenant_id    ON hc_clinical_notes (tenant_id);
CREATE INDEX idx_hc_clinical_notes_encounter    ON hc_clinical_notes (encounter_id, note_type);
CREATE INDEX idx_hc_clinical_notes_created_at   ON hc_clinical_notes (created_at);

ALTER TABLE hc_clinical_notes ENABLE ROW LEVEL SECURITY;
CREATE POLICY rls_hc_clinical_notes ON hc_clinical_notes
    USING (tenant_id = current_setting('app.tenant_id')
       AND (branch_id = current_setting('app.branch_id')
            OR current_setting('app.branch_id') = 'ALL'));
```

---

## Part D — Reporting Views (ADR-HC-008)

All views are **read-only, PHI-free aggregates**, filter on the ADR-HC-001 session GUCs, and are
created `WITH (security_invoker = true)` so the querying role's base-table RLS also applies. No view
selects any `EncryptedPHIType` column or patient identifier. `current_setting(..., true)` (missing_ok)
avoids errors when a GUC is unset; a NULL GUC yields no rows (fail-closed).

```sql
-- D.1  v_hc_daily_patients — patient/visit volume per branch per day
CREATE VIEW v_hc_daily_patients WITH (security_invoker = true) AS
SELECT tenant_id, branch_id,
       date_trunc('day', checked_in_at)::date AS service_day,
       COUNT(*)                                AS visit_count,
       COUNT(DISTINCT patient_id)              AS distinct_patients,
       COUNT(*) FILTER (WHERE visit_type = 'walk_in')     AS walk_in_count,
       COUNT(*) FILTER (WHERE visit_type = 'appointment') AS appointment_count
FROM hcr_visits
WHERE tenant_id = current_setting('app.tenant_id', true)
  AND (branch_id = current_setting('app.branch_id', true)
       OR current_setting('app.branch_id', true) = 'ALL')
GROUP BY tenant_id, branch_id, service_day;

-- D.2  v_hc_doctor_productivity — encounters per provider per day
CREATE VIEW v_hc_doctor_productivity WITH (security_invoker = true) AS
SELECT e.tenant_id, e.branch_id, e.provider_id,
       date_trunc('day', e.started_at)::date AS service_day,
       COUNT(*)                               AS encounter_count,
       COUNT(*) FILTER (WHERE e.status = 'completed') AS completed_count
FROM hc_encounters e
WHERE e.tenant_id = current_setting('app.tenant_id', true)
  AND (e.branch_id = current_setting('app.branch_id', true)
       OR current_setting('app.branch_id', true) = 'ALL')
GROUP BY e.tenant_id, e.branch_id, e.provider_id, service_day;

-- D.3  v_hc_queue — wait/service metrics per branch per department per day
CREATE VIEW v_hc_queue WITH (security_invoker = true) AS
SELECT t.tenant_id, t.branch_id, t.department_id, t.service_day,
       COUNT(*)                                                       AS ticket_count,
       COUNT(*) FILTER (WHERE t.status = 'served')                    AS served_count,
       COUNT(*) FILTER (WHERE t.status = 'skipped')                   AS skipped_count,
       AVG(EXTRACT(EPOCH FROM (t.called_at - t.created_at)))          AS avg_wait_seconds,
       AVG(EXTRACT(EPOCH FROM (t.served_at - t.called_at)))           AS avg_service_seconds
FROM hcr_queue_tickets t
WHERE t.tenant_id = current_setting('app.tenant_id', true)
  AND (t.branch_id = current_setting('app.branch_id', true)
       OR current_setting('app.branch_id', true) = 'ALL')
GROUP BY t.tenant_id, t.branch_id, t.department_id, t.service_day;

-- D.4  v_hc_appointments — booking/attendance per branch per day per status
CREATE VIEW v_hc_appointments WITH (security_invoker = true) AS
SELECT tenant_id, branch_id,
       date_trunc('day', created_at)::date AS service_day,
       status,
       COUNT(*)                             AS appointment_count
FROM hcs_appointments
WHERE tenant_id = current_setting('app.tenant_id', true)
  AND (branch_id = current_setting('app.branch_id', true)
       OR current_setting('app.branch_id', true) = 'ALL')
GROUP BY tenant_id, branch_id, service_day, status;

-- D.5  v_hc_revenue — invoiced/paid per branch per day per payer
CREATE VIEW v_hc_revenue WITH (security_invoker = true) AS
SELECT i.tenant_id, i.branch_id,
       date_trunc('day', i.created_at)::date AS service_day,
       COALESCE(i.insurance_type, 'self_pay') AS payer,
       COUNT(*)                               AS invoice_count,
       SUM(i.total_amount)                    AS invoiced_total,
       SUM(i.total_amount - i.outstanding_balance) AS collected_total
FROM hcb_invoices i
WHERE i.tenant_id = current_setting('app.tenant_id', true)
  AND (i.branch_id = current_setting('app.branch_id', true)
       OR current_setting('app.branch_id', true) = 'ALL')
GROUP BY i.tenant_id, i.branch_id, service_day, payer;

-- D.6  v_hc_disease_stats — diagnosis frequency (codes + counts only; no PHI)
CREATE VIEW v_hc_disease_stats WITH (security_invoker = true) AS
SELECT d.tenant_id, d.branch_id, d.icd10_code,
       date_trunc('month', d.created_at)::date AS period_month,
       COUNT(*)                                 AS diagnosis_count,
       COUNT(*) FILTER (WHERE d.is_primary)     AS primary_count
FROM hc_diagnoses d
WHERE d.tenant_id = current_setting('app.tenant_id', true)
  AND (d.branch_id = current_setting('app.branch_id', true)
       OR current_setting('app.branch_id', true) = 'ALL')
GROUP BY d.tenant_id, d.branch_id, d.icd10_code, period_month;

-- D.7  v_hc_drug_usage — dispense volume per drug per period
CREATE VIEW v_hc_drug_usage WITH (security_invoker = true) AS
SELECT di.tenant_id, di.branch_id, di.drug_catalog_id,
       date_trunc('month', dl.dispensed_at)::date AS period_month,
       COUNT(*)                                     AS dispense_lines,
       SUM(di.quantity_dispensed)                   AS total_quantity
FROM hcp_dispensing_items di
JOIN hcp_dispensing_log dl ON dl.id = di.dispense_id
WHERE di.tenant_id = current_setting('app.tenant_id', true)
  AND (di.branch_id = current_setting('app.branch_id', true)
       OR current_setting('app.branch_id', true) = 'ALL')
GROUP BY di.tenant_id, di.branch_id, di.drug_catalog_id, period_month;

-- D.8  v_hc_lab_utilization — test order/result volume per test per period
CREATE VIEW v_hc_lab_utilization WITH (security_invoker = true) AS
SELECT oi.tenant_id, oi.branch_id, oi.test_catalog_id,
       date_trunc('month', o.created_at)::date AS period_month,
       COUNT(*)                                 AS ordered_count,
       COUNT(*) FILTER (WHERE o.status IN ('resulted','released')) AS resulted_count
FROM hcl_test_order_items oi
JOIN hcl_test_orders o ON o.id = oi.order_id
WHERE oi.tenant_id = current_setting('app.tenant_id', true)
  AND (oi.branch_id = current_setting('app.branch_id', true)
       OR current_setting('app.branch_id', true) = 'ALL')
GROUP BY oi.tenant_id, oi.branch_id, oi.test_catalog_id, period_month;
```

**Binding (ADR-HC-008 D3):** each view is registered as a read-only, system-managed
`EntityDefinition` (via `backend/app/routers/data_model.py`) with fields mapped to its columns and
`RelationshipDefinition` joins on shared non-PHI dimensions (`branch_id`, `provider_id`,
`department_id`, `service_day`). The platform Reports/Dashboards engines bind widgets/reports to these
entities unchanged. The epic-12 reporting adapter sets `app.tenant_id` (and `app.branch_id`,
defaulting to `'ALL'` for owner-level exec dashboards) on the reporting DB session.

---

## Object Summary

| Part / ADR | New objects |
|---|---|
| A — ADR-HC-005 | `hc_branches` +3 columns (ALTER); `hc_departments` (incl. optional `platform_department_id` FK, addendum A3); `hc_provider_departments` |
| B — ADR-HC-006 | `hcr_visits`; `hcr_queue_tickets` |
| C — ADR-HC-007 | `hc_icd10_codes`; `hc_icd9cm_codes`; `hc_diagnoses`; `hc_procedures`; `hc_clinical_notes` |
| D — ADR-HC-008 | Views: `v_hc_daily_patients`, `v_hc_doctor_productivity`, `v_hc_queue`, `v_hc_appointments`, `v_hc_revenue`, `v_hc_disease_stats`, `v_hc_drug_usage`, `v_hc_lab_utilization` |

| Kind | Count |
|---|---|
| New tables | **9** (`hc_departments`, `hc_provider_departments`, `hcr_visits`, `hcr_queue_tickets`, `hc_icd10_codes`, `hc_icd9cm_codes`, `hc_diagnoses`, `hc_procedures`, `hc_clinical_notes`) |
| Altered tables | **1** (`hc_branches`) |
| New PHI-encrypted columns | **1** (`hc_clinical_notes.body`) |
| PHI-by-association (RLS only) | `hcr_visits`, `hc_diagnoses`, `hc_procedures` |
| Reporting views | **8** (all PHI-free) |

---

*Cross-references: ADR-HC-005 (org/dept), ADR-HC-006 (visit/queue), ADR-HC-007 (coding),*
*ADR-HC-008 (reporting), ADR-HC-001 (branch isolation + RLS), ADR-HC-002 (PHI SDK readers + audit).*
