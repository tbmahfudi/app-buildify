---
artifact_id: schema-hc-03
type: schema-design
module: healthcare (module deltas) + platform (identity/auth tables)
status: proposed
producer: B1 Backend Architect
upstream: [schema-hc-01, schema-hc-02, adr-hc-009, adr-hc-003, adr-hc-001, adr-hc-002, epic-18-patient-portal-authentication]
created: 2026-07-05
updated: 2026-07-06
changelog:
  - "2026-07-06 (B1): §M — per ADR-HC-009 R4 (ratified), hc_patients.user_id gains a real FK →
     users.id in shared-DB deployments (STEP 5); app-enforced fallback retained for split-DB. Consistent
     with ADR-HC-005 addendum A1. R3 (per-tenant patient_account_claim_grace_days) needs NO schema
     touch here — it reuses the existing tenant-settings JSON (no new users/hc_patients column)."
  - "2026-07-06 (B1) v2 — Household / Proxy Access (ADR-HC-009 Revision v2). §M REVISED: hc_patients.user_id
     is now NULLABLE + NOT UNIQUE (owner denormalization only, V-D5) — the UNIQUE index + NOT NULL steps are
     WITHDRAWN; a non-unique lookup index is kept; the R4 FK now sits on a plain (non-unique) column. §M adds
     the new MODULE table hc_patient_relationships (V-D6, RLS-scoped) — the authority for who may act for a
     patient — with UNIQUE(account_user_id,patient_id), a one-self-per-holder partial unique index, and the
     same-tenant (Q2) constraint. §M adds two columns to hc_patient_consents: basis + consented_by_user_id
     (V-D9, proxy-consent attribution). Object Summary + counts updated. Token claims (acct/obo, active
     patient_id) are runtime-only and carry NO schema touch."
---

# Schema Design v3 — Patient Identity & Authentication

> Companion to **ADR-HC-009**. Covers **only** the objects that ADR introduces: three new **PLATFORM**
> identity/auth tables (`user_identities`, `user_mfa`, `user_trusted_devices`), two new **PLATFORM**
> `users` columns (`username`, `must_set_password`), and the **MODULE** `hc_patients.user_id` migration.
> Conventions (UUID PK, UTC timestamps) follow schema-hc-01/02.
>
> **⚠ v2 (2026-07-06) — Household / Proxy Access (ADR-HC-009 Revision v2).** §M is REVISED. The 1:1
> `hc_patients.user_id` → NOT NULL + UNIQUE migration is **withdrawn**: `user_id` is now **nullable + NOT
> UNIQUE** (a convenience owner denormalization). §M adds two **MODULE** objects — the new table
> **`hc_patient_relationships`** (the household/proxy authority; RLS-scoped) and two columns on
> **`hc_patient_consents`** (`basis`, `consented_by_user_id`) for proxy-consent attribution. The three
> PLATFORM tables and the two `users` columns are unchanged by v2.
>
> **PLATFORM vs MODULE.** The identity tables and `users` columns are **PLATFORM** objects (owned by
> `backend/app/models/`, migrated with the platform). `hc_patients`, `hc_patient_relationships`, and
> `hc_patient_consents` are **MODULE** objects (`modules/healthcare/backend/models.py`). Per ADR-HC-009
> D1/D2, identity lives platform-side and PHI lives module-side; this schema keeps that split — no
> credential or OAuth columns are added to any `hc_*` table (the relationship table holds an FK to a
> platform user, not credentials).

## Conventions

| Convention | Rule |
|---|---|
| PK | `VARCHAR(36)` UUID (platform `GUID` type = `String(36)`), server default `gen_random_uuid()` |
| Timestamps | UTC `TIMESTAMP WITHOUT TIME ZONE`, default `NOW()` |
| FK to platform users | `→ users(id) ON DELETE CASCADE` (identity artifacts die with the user) |
| `[PHI]` | none of the tables in this document carry PHI (identity/auth only) |

## Tenancy & RLS applicability

The three new identity tables are **PLATFORM, tenant-scoped by the owning `User`'s tenancy — but
patient identity spans tenants** (ADR-HC-003 §D1: patient `User` carries no single tenant scope for the
patient session; `tenant_id: null` in the minted patient token). Concretely:

- These tables are **keyed on `user_id`**, not on `tenant_id`, and are **not branch-scoped** (they are
  not healthcare branch data; ADR-HC-001 RLS does not apply). Access control is by ownership: a row is
  only ever read/written for its own `user_id` during that user's auth flow. They follow the same
  **platform** access model as the existing `user_sessions`, `password_reset_tokens`,
  `login_attempts`, and `token_blacklist` tables (which are likewise `user_id`-keyed, not RLS-scoped).
- They carry **no `hc_*` prefix** and are **not** registered as healthcare RLS objects; the healthcare
  `current_setting('app.tenant_id'/'app.branch_id')` GUCs are irrelevant to them.
- `hc_patients` is unchanged in tenancy (tenant-scoped module PHI table, schema-hc-01); this document
  only loosens its `user_id` column (v2: nullable + NOT UNIQUE).
- **v2 — `hc_patient_relationships` IS an RLS-scoped module table** (unlike the three PLATFORM identity
  tables above). It is an `hc_*` object carrying `tenant_id` (+ `branch_id`) and is governed by the
  healthcare `current_setting('app.tenant_id'/'app.branch_id')` GUCs (ADR-HC-001), the same as
  `hc_patients`. Patient-portal reads additionally filter on `account_user_id = <caller's platform user>`.
  `hc_patient_consents` is likewise tenant-scoped module PHI (schema-hc-01); v2 only adds two columns.

---

## Part P — Platform identity & auth tables (PLATFORM)

### P.1 `user_identities` — federated (OAuth) identity linkage (ADR-HC-009 D2)

Stores each linked external identity for a platform `User`. Keyed on the provider **subject**
(`provider_subject` = Google `sub`), never on email, so an email change does not break the link and an
email collision cannot hijack an account. Not PHI. **PLATFORM.**

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | VARCHAR(36) | NOT NULL | gen_random_uuid() | PK |
| `user_id` | VARCHAR(36) | NOT NULL | — | FK → users.id ON DELETE CASCADE |
| `provider` | VARCHAR(30) | NOT NULL | — | CHECK IN ('google') at MVP; extensible |
| `provider_subject` | VARCHAR(255) | NOT NULL | — | Provider's stable subject id (Google `sub`) |
| `email` | VARCHAR(255) | NULL | — | Email asserted by the provider at link time |
| `email_verified` | BOOLEAN | NOT NULL | FALSE | Provider's `email_verified` claim |
| `linked_at` | TIMESTAMP | NOT NULL | NOW() | |
| `last_login_at` | TIMESTAMP | NULL | — | Updated on each OAuth login |

```sql
CREATE TABLE user_identities (
    id               VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider         VARCHAR(30) NOT NULL,
    provider_subject VARCHAR(255) NOT NULL,
    email            VARCHAR(255) NULL,
    email_verified   BOOLEAN NOT NULL DEFAULT FALSE,
    linked_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at    TIMESTAMP NULL,
    CONSTRAINT ck_user_identities_provider CHECK (provider IN ('google')),
    CONSTRAINT uq_user_identities_provider_subject UNIQUE (provider, provider_subject)
);
CREATE INDEX idx_user_identities_user_id ON user_identities (user_id);
-- supports the "email matches an existing user" linking-rule lookup (D2)
CREATE INDEX idx_user_identities_provider_email ON user_identities (provider, email);
```

**Linking rule (ADR-HC-009 D2) is app-enforced:** auto-link only when the provider `email_verified` and
the target `users.is_verified` are both true; otherwise require an explicit proof-of-control link step.
`(provider, provider_subject)` uniqueness prevents two platform users claiming the same Google account.

---

### P.2 `user_mfa` — per-user, per-method MFA settings (ADR-HC-009 D3)

Generic MFA framework (OTP is the first method; designed for staff reuse). One row per
`(user_id, method)`. Not PHI. **PLATFORM.**

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | VARCHAR(36) | NOT NULL | gen_random_uuid() | PK |
| `user_id` | VARCHAR(36) | NOT NULL | — | FK → users.id ON DELETE CASCADE |
| `method` | VARCHAR(20) | NOT NULL | — | CHECK IN ('otp_phone') at MVP; extensible (e.g. 'totp') |
| `enabled` | BOOLEAN | NOT NULL | FALSE | |
| `secret` | VARCHAR(255) | NULL | — | Reserved (e.g. TOTP shared secret); NULL for otp_phone |
| `enrolled_at` | TIMESTAMP | NULL | — | Set when the method is enabled |
| `last_verified_at` | TIMESTAMP | NULL | — | Updated on each successful challenge |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

```sql
CREATE TABLE user_mfa (
    id               VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    method           VARCHAR(20) NOT NULL,
    enabled          BOOLEAN NOT NULL DEFAULT FALSE,
    secret           VARCHAR(255) NULL,
    enrolled_at      TIMESTAMP NULL,
    last_verified_at TIMESTAMP NULL,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_user_mfa_method CHECK (method IN ('otp_phone')),
    CONSTRAINT uq_user_mfa_user_method UNIQUE (user_id, method)
);
CREATE INDEX idx_user_mfa_user_id ON user_mfa (user_id);
-- fast "does this user have any enabled factor?" check at login
CREATE INDEX idx_user_mfa_user_enabled ON user_mfa (user_id, enabled);
```

> `secret`, when populated by a future method, must be stored encrypted (platform secret handling,
> not plaintext). For `otp_phone` it stays NULL — the factor is the on-file phone + OTP transport.

---

### P.3 `user_trusted_devices` — remembered-device store (ADR-HC-009 D4)

Lets a verified MFA device skip the second factor for a bounded window. Not PHI. **PLATFORM.**

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | VARCHAR(36) | NOT NULL | gen_random_uuid() | PK |
| `user_id` | VARCHAR(36) | NOT NULL | — | FK → users.id ON DELETE CASCADE |
| `device_hash` | VARCHAR(255) | NOT NULL | — | HMAC of the device secret (raw secret in signed cookie only) |
| `label` | VARCHAR(255) | NULL | — | Best-effort UA/device hint for the security screen |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `expires_at` | TIMESTAMP | NOT NULL | — | ~30-day window (ADR-HC-009 D4) |
| `last_used_at` | TIMESTAMP | NULL | — | Sliding, observability only |
| `revoked_at` | TIMESTAMP | NULL | — | Set on password change / MFA disable / manual revoke |

```sql
CREATE TABLE user_trusted_devices (
    id           VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_hash  VARCHAR(255) NOT NULL,
    label        VARCHAR(255) NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at   TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP NULL,
    revoked_at   TIMESTAMP NULL,
    CONSTRAINT uq_user_trusted_devices_hash UNIQUE (user_id, device_hash)
);
CREATE INDEX idx_user_trusted_devices_user_id ON user_trusted_devices (user_id);
-- login-time lookup: a live, non-revoked device for this user
CREATE INDEX idx_user_trusted_devices_active
    ON user_trusted_devices (user_id, expires_at) WHERE revoked_at IS NULL;
```

**App-enforced (ADR-HC-009 D4):** on **password change/reset** and on **MFA disable**, set
`revoked_at = NOW()` for all of the user's rows (mass-revoke). A device is honoured only when
`revoked_at IS NULL AND expires_at > NOW()` and its cookie HMAC matches `device_hash`.

---

### P.4 `users` — new columns (ALTER, PLATFORM) (ADR-HC-009 D1, D7)

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `username` | VARCHAR(50) | NULL | — | UNIQUE (case-insensitive); optional login identifier (D1) |
| `must_set_password` | BOOLEAN | NOT NULL | FALSE | Migration flag: legacy patient must set a password (D7) |

```sql
ALTER TABLE users
    ADD COLUMN username          VARCHAR(50) NULL,
    ADD COLUMN must_set_password BOOLEAN NOT NULL DEFAULT FALSE;

-- case-insensitive uniqueness; multiple NULLs allowed (staff without a username)
CREATE UNIQUE INDEX uq_users_username_lower
    ON users (LOWER(username)) WHERE username IS NOT NULL;
```

**Login resolution (ADR-HC-009 D1):** if the submitted identifier contains `@`, match `email`;
otherwise match `LOWER(username)`. `email` remains unique/required as today; `username` is additive and
backward-compatible. `must_set_password` gates the `/patient/claim-account` interstitial for backfilled
legacy patients (D7).

---

## Part M — Module: `hc_patients.user_id` (nullable, non-unique) + household/proxy tables (MODULE)

> **⚠ REVISED v2 (2026-07-06) — ADR-HC-009 Revision v2 (V-D5/V-D6/V-D9).** The v1 target of this section —
> `hc_patients.user_id` → **NOT NULL + UNIQUE** (1:1) — is **WITHDRAWN**. Under the household/proxy model one
> account holder owns/manages **many** patients, so `user_id` stays **nullable + NOT UNIQUE** (a convenience
> owner denormalization). This section now covers: (M.1) the loosened `user_id` column + retained non-unique
> index + R4 FK posture; (M.2) the new `hc_patient_relationships` table; (M.3) the two new
> `hc_patient_consents` columns.

### M.1 — `hc_patients.user_id`: nullable, NOT UNIQUE, non-unique lookup index, R4 FK (V-D5)

Today (`modules/healthcare/backend/models.py`): `hc_patients.user_id VARCHAR(36) NULL` (indexed, non-unique).
**v2 keeps it exactly this way** — nullable + non-unique — and does **NOT** add the v1 UNIQUE index or
`SET NOT NULL`. Rationale (ADR-HC-009 V-D5):

- **NOT UNIQUE** — one account holder (`users.id`) owns many `hc_patients` rows (self + dependents), so
  `user_id` legitimately repeats.
- **Nullable** — a clinic-created dependent may have **no login of its own** (managed entirely by the account
  holder); its `user_id` stays NULL and authority comes from the relationship table (M.2), not this column.
- **Owner denormalization invariant (app-maintained).** Where `user_id` is set, it MUST equal the
  `account_user_id` of that patient's `role = 'owner'` relationship row (M.2). It is a denormalized mirror for
  fast owner lookup — **not** the authorization authority. The bridge (V-D7) authorizes via the relationship
  table, never via a bare `user_id`.

```sql
-- v2: NO unique index, NO SET NOT NULL. Retain the existing NON-UNIQUE lookup index:
CREATE INDEX IF NOT EXISTS idx_hc_patients_user_id ON hc_patients (user_id);
-- (The v1 uq_hc_patients_user_id UNIQUE index and ALTER COLUMN ... SET NOT NULL are WITHDRAWN.)
```

**The D7 backfill still runs** (create a platform `User(role=patient)` for every self-owned legacy patient
lacking a login, set `must_set_password`, link `user_id`, and create a `role='self'`/`owner` relationship row
— M.2), because self-owned patients need a login. But **STEP 4 (constrain to UNIQUE + NOT NULL) is removed** —
there is nothing to constrain, since `user_id` is intentionally many-to-one and nullable.

**Referential integrity (R4 posture retained, now on a plain FK).** Per **ADR-HC-009 R4** (topology-dependent,
consistent with ADR-HC-005 addendum A1):

- **Shared-DB (current dev — both in `appdb`):** declare a **real FK** `hc_patients.user_id → users.id`. In v2
  this is a **plain FK on a nullable, non-unique column** (no UNIQUE index backing it):

  ```sql
  -- Shared-DB only — plain (nullable, non-unique) cross-table FK to platform users.
  ALTER TABLE hc_patients
      ADD CONSTRAINT fk_hc_patients_user
          FOREIGN KEY (user_id) REFERENCES users(id);
  ```

- **Split-DB (module and platform in separate DBs):** the cross-service FK is **not declarable**; integrity is
  **app-enforced** at registration/bridge time. Same posture as ADR-HC-005 addendum A1/A3.

### M.2 — New MODULE table `hc_patient_relationships` (V-D6, RLS-scoped)

The **authority for "who may act for this patient."** Module-side, PHI-adjacent, **RLS-scoped** (tenant +
branch GUCs, ADR-HC-001 — like `hc_patients`). Holds an FK to a platform `users.id` (the account holder) but
**no credentials/PHI**. Not itself PHI, but co-located with PHI and access-controlled the same way.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | VARCHAR(36) | NOT NULL | gen_random_uuid() | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL | — | RLS scope; = patient's tenant AND account holder's tenant (Q2) |
| `branch_id` | VARCHAR(36) | NULL | — | FK → hc_branches.id (shared-DB); patient's clinic — routes Q3 staff approval + audit |
| `account_user_id` | VARCHAR(36) | NOT NULL | — | FK → users.id (shared-DB; app-enforced split) — the account holder |
| `patient_id` | VARCHAR(36) | NOT NULL | — | FK → hc_patients.id ON DELETE CASCADE |
| `relationship` | VARCHAR(20) | NOT NULL | — | CHECK IN ('self','spouse','child','parent','other') |
| `role` | VARCHAR(10) | NOT NULL | — | CHECK IN ('owner','proxy') |
| `status` | VARCHAR(10) | NOT NULL | 'active' | CHECK IN ('active','pending','revoked') |
| `basis` | VARCHAR(20) | NOT NULL | — | CHECK IN ('self','parental_guardian','delegated_adult','spousal') (Q1) |
| `granted_by` | VARCHAR(36) | NOT NULL | — | users.id who created the grant |
| `granted_at` | TIMESTAMP | NOT NULL | NOW() | |
| `approved_by_staff_id` | VARCHAR(36) | NULL | — | users.id of the approving clinic staff (Q3); NULL until approved |
| `approved_at` | TIMESTAMP | NULL | — | Set on staff approval |
| `revoked_at` | TIMESTAMP | NULL | — | Set on grant revoke / majority detach (Q4) |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | |

```sql
CREATE TABLE hc_patient_relationships (
    id                   VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id            VARCHAR(36) NOT NULL,
    branch_id            VARCHAR(36) NULL REFERENCES hc_branches(id),
    account_user_id      VARCHAR(36) NOT NULL,        -- FK → users(id): real in shared-DB, app-enforced split
    patient_id           VARCHAR(36) NOT NULL REFERENCES hc_patients(id) ON DELETE CASCADE,
    relationship         VARCHAR(20) NOT NULL,
    role                 VARCHAR(10) NOT NULL,
    status               VARCHAR(10) NOT NULL DEFAULT 'active',
    basis                VARCHAR(20) NOT NULL,
    granted_by           VARCHAR(36) NOT NULL,
    granted_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    approved_by_staff_id VARCHAR(36) NULL,
    approved_at          TIMESTAMP NULL,
    revoked_at           TIMESTAMP NULL,
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_hcpr_relationship CHECK (relationship IN ('self','spouse','child','parent','other')),
    CONSTRAINT ck_hcpr_role         CHECK (role IN ('owner','proxy')),
    CONSTRAINT ck_hcpr_status       CHECK (status IN ('active','pending','revoked')),
    CONSTRAINT ck_hcpr_basis        CHECK (basis IN ('self','parental_guardian','delegated_adult','spousal')),
    -- self implies owner + self-basis (coherence, V-D6)
    CONSTRAINT ck_hcpr_self_coherent CHECK (
        relationship <> 'self' OR (role = 'owner' AND basis = 'self')
    ),
    -- one relationship row per (account holder, patient)
    CONSTRAINT uq_hcpr_account_patient UNIQUE (account_user_id, patient_id)
);

-- exactly one 'self' patient per account holder (partial unique index)
CREATE UNIQUE INDEX uq_hcpr_one_self_per_holder
    ON hc_patient_relationships (account_user_id) WHERE relationship = 'self';

-- household discovery (GET /me/household) + bridge active-set resolution: caller's active rows
CREATE INDEX idx_hcpr_account_active
    ON hc_patient_relationships (account_user_id, status);

-- reverse lookup: who may act for a patient / owner denormalization check
CREATE INDEX idx_hcpr_patient ON hc_patient_relationships (patient_id, status);

-- staff approval queue (Q3): pending rows for a branch
CREATE INDEX idx_hcpr_branch_pending
    ON hc_patient_relationships (branch_id, status) WHERE status = 'pending';
```

**Constraints & app-notes:**

- **`UNIQUE(account_user_id, patient_id)`** — at most one relationship per (holder, patient); re-grant
  updates/reactivates the existing row rather than inserting a duplicate.
- **One `self` per account holder** — the `uq_hcpr_one_self_per_holder` partial unique index. Many managed
  (non-`self`) rows are allowed.
- **Same-tenant (Q2) — half DB, half app.** The DB side: `tenant_id` must equal the joined
  `hc_patients.tenant_id`. In **shared-DB** this can be enforced by a trigger/CHECK (or a composite FK
  `(patient_id, tenant_id) → hc_patients(id, tenant_id)` if a matching unique key exists); in **split-DB** it
  is app-enforced. The **account-holder-tenant** side (`tenant_id` = the platform user's tenant) is
  **always app-enforced** at grant/link time, because `users` is platform-side and may be split-DB. A target
  clinic in a **different tenant** is **rejected (422)** at register/link (epic-18 18.10.2/18.10.3).
- **FK posture (R4).** `account_user_id → users.id` and `branch_id → hc_branches.id` are **real FKs in
  shared-DB**, app-enforced when split — same story as `hc_patients.user_id` (M.1) and ADR-HC-005 addendum A1.
- **Not RLS-exempt.** This table registers as an `hc_*` RLS object (tenant + branch GUCs), unlike the P.1–P.3
  platform identity tables.

### M.3 — `hc_patient_consents` — new columns for proxy-consent attribution (V-D9, MODULE)

Extend the existing `hc_patient_consents` (schema-hc-01) so a consent records **who** consented and on what
**basis** when it is not the patient acting for themselves (Q1 / epic-18 18.10.6). No behavioural change for
self-consent (`basis = 'self'`, `consented_by_user_id` NULL/self).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `basis` | VARCHAR(20) | NOT NULL | 'self' | CHECK IN ('self','parental_guardian','delegated_adult','spousal') |
| `consented_by_user_id` | VARCHAR(36) | NULL | — | users.id of the account holder who consented (NULL when self) |

```sql
ALTER TABLE hc_patient_consents
    ADD COLUMN basis                VARCHAR(20) NOT NULL DEFAULT 'self',
    ADD COLUMN consented_by_user_id VARCHAR(36) NULL;

ALTER TABLE hc_patient_consents
    ADD CONSTRAINT ck_hc_patient_consents_basis
        CHECK (basis IN ('self','parental_guardian','delegated_adult','spousal'));
-- consented_by_user_id → users.id: real FK in shared-DB, app-enforced when split (R4 posture).
```

The existing `patient_id` (for whom), `consent_version`, `accepted_at`, `ip`, `user_agent` columns supply the
rest of the "who / for whom / basis / when / how" record. Consent rows remain immutable/append-only
(schema-hc-01 audit-log permission posture). *Legal note: recording the basis does not warrant its lawfulness —
the operator owns the consent-law posture (ADR-HC-009 V-D9 / epic-18 Q1).*

---

## Object Summary

| Layer | Object | Kind | Key columns | PHI? |
|---|---|---|---|---|
| **PLATFORM** | `user_identities` | New table | `user_id`, `provider`, `provider_subject`, `email`, `email_verified`; UNIQUE(provider, provider_subject) | No |
| **PLATFORM** | `user_mfa` | New table | `user_id`, `method`, `enabled`, `secret`, `enrolled_at`; UNIQUE(user_id, method) | No |
| **PLATFORM** | `user_trusted_devices` | New table | `user_id`, `device_hash`, `expires_at`, `revoked_at`; UNIQUE(user_id, device_hash) | No |
| **PLATFORM** | `users` | ALTER +2 cols | `username` (unique, ci), `must_set_password` | No |
| **MODULE** | `hc_patients` | ALTER `user_id` | **v2:** `user_id` **nullable + NOT UNIQUE** (owner denormalization, V-D5); non-unique lookup index kept; plain FK → users.id in shared-DB (R4), app-enforced when split | user_id is not PHI |
| **MODULE** | `hc_patient_relationships` | **v2: New table** | `account_user_id`(→users.id), `patient_id`(→hc_patients.id), `relationship`, `role`(owner/proxy), `status`(active/pending/revoked), `basis`, `granted_by/at`, `approved_by_staff_id/at`, `revoked_at`, `tenant_id`/`branch_id`; UNIQUE(account_user_id,patient_id); one-`self`-per-holder; same-tenant (Q2) | No (PHI-adjacent, RLS-scoped) |
| **MODULE** | `hc_patient_consents` | **v2: ALTER +2 cols** | `basis` (self/parental_guardian/delegated_adult/spousal), `consented_by_user_id`(→users.id) | No (consent metadata) |

| Kind | Count |
|---|---|
| New platform tables | **3** (`user_identities`, `user_mfa`, `user_trusted_devices`) |
| New module tables (v2) | **1** (`hc_patient_relationships`) |
| Altered platform tables | **1** (`users`, +2 columns) |
| Altered module tables (v2) | **2** (`hc_patients` — `user_id` loosened to nullable + NOT UNIQUE; `hc_patient_consents` +2 cols) |
| New PHI columns | **0** |
| RLS-scoped tables added (v2) | **1** (`hc_patient_relationships` — `hc_*`, tenant+branch GUCs, unlike the `user_id`-keyed platform identity tables) |

---

*Cross-references: ADR-HC-009 (patient identity & auth) incl. **Revision v2 — Household / Proxy Access***
*(V-D5/V-D6/V-D9), ADR-HC-003 §D1 (superseded auth flow; retained `tenant_id:null` claim shape), ADR-HC-001*
*(branch isolation — N/A to the platform identity tables, **but applies to `hc_patient_relationships`**),*
*ADR-HC-002 (PHI SDK readers/audit — `hc_patient_relationships` is RLS-scoped module data), schema-hc-01/02*
*(conventions; `hc_patients` + `hc_patient_consents` base definitions).*
