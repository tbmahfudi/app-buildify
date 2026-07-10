---
artifact_id: adr-hc-009
type: adr
module: healthcare
status: Accepted
producer: B1 Software Architect
upstream: [epic-18-patient-portal-authentication, adr-hc-003, adr-hc-001, adr-hc-002, adr-hc-004, BACKLOG.md (v3), schema-hc-01, schema-hc-02]
created: 2026-07-05
updated: 2026-07-06
changelog:
  - "2026-07-06 (B1) v2 — REVISION: Household / Proxy Access. Per epic-18 v2 (Feature 18.10) and the four
     user rulings (Q1 allow adult-for-adult consent; Q2 within-one-tenant; Q3 clinic-staff approval to link
     an existing patient; Q4 clinic-mediated majority transition), the 1:1 identity model is superseded by a
     household / proxy model: one platform account holder owns/manages many hc_patients. D5 (user_id NOT
     NULL + UNIQUE) and D6 (single-patient bridge) are SUPERSEDED — see the new 'Revision v2' section below.
     Prior decisions are annotated, not rewritten. Adds a module-side relationship table
     (hc_patient_relationships), an active-patient-scoped bridge + switch endpoint, staff link-approval and
     staff majority-detach workflows, and a proxy-consent basis + on_behalf_of audit thread."
---

# ADR-HC-009 — Patient Identity & Authentication (Password / Google / OTP-MFA)

## Status

Accepted (v1) — **amended by Revision v2 (2026-07-06), Household / Proxy Access (see the dedicated
section below). D5 and D6 are SUPERSEDED by v2; all other decisions stand.**

## Supersedes

**This ADR supersedes ADR-HC-003 §D1's authentication flow** (the OTP/phone-only patient
`register`/`token` steps). The **claim shape of the patient JWT is retained verbatim** from
ADR-HC-003 §D1: `{ "sub": patient_id, "patient_id": "...", "roles": ["patient"], "tenant_id": null }`,
minted through the canonical `POST /api/v1/patients/auth/from-platform` bridge. What is retired is the
premise that OTP/phone is the **only** and **mandatory** authentication mechanism. Under this ADR,
patient authentication supports **three** methods — (1) email/username + password, (2) Google OAuth,
(3) phone OTP — and OTP becomes **optional** (a passwordless login option and an optional MFA second
factor), never mandatory. ADR-HC-003 §D2 (gateway route namespace separation) and §D3 (rate
limiting / CAPTCHA / CORS for public endpoints) remain in force and are **extended**, not replaced, by
this ADR (D9). ADR-HC-001 (branch isolation), ADR-HC-002 (PHI via SDK readers + audit), and
ADR-HC-004 (i18n) are unchanged and conformed to below.

## Context

Epic-18 ratifies a new patient sign-in surface for the healthcare portal. The invariants
(epic-18 "Identity & tenancy invariants"):

- **Identity = platform.** One patient ↔ exactly one platform `User(role=patient)` holding
  email/username, password hash, linked Google identity, and MFA settings. Patient credentials live on
  the platform `users` table (`hashed_password`), reusing the platform's password hashing, policy,
  history, lockout, session, and reset machinery (`backend/app/core/auth.py`,
  `password_validator.py`, `lockout_manager.py`, `session_manager.py`,
  `backend/app/routers/auth.py`). There is **no separate module credential store.**
- **PHI = module.** One patient ↔ exactly one `hc_patients` row (encrypted PHI + consent), linked to
  the platform user by `hc_patients.user_id`. PHI is read only through SDK readers with audit
  (ADR-HC-002).
- **Cross-tenant patient token.** The minted patient token carries `tenant_id: null`,
  `roles: ["patient"]` (ADR-HC-003 §D1 claim shape). Patient identity spans tenants; branch isolation
  (ADR-HC-001) is unaffected.

Today's ground truth (the starting point this ADR changes):

- Platform `POST /api/v1/auth/login` (`backend/app/routers/auth.py`) authenticates **by email only**
  (`User.email == credentials.email`); the platform `users` table has **no `username` column** and no
  `role` column (roles resolve via User→Group→Role, `seed_rbac_with_groups.py`; a `patient` role and a
  `patients` group already exist). The platform access token payload carries
  `{ sub, email, tenant_id, permissions }` — **no `roles` claim**.
- The module bridge `POST /api/v1/patients/auth/from-platform`
  (`modules/healthcare/backend/routes_patient_auth.py`) already exists: it validates a platform JWT,
  loads the active `hc_patients` where `user_id = sub`, and mints the patient token via
  `create_patient_access_token` (`modules/healthcare/backend/sdk/patient_tokens.py`). Both services
  share `SECRET_KEY`.
- The module OTP path (`/patients/auth/otp/*`, `/patients/auth/token`) mints a patient token
  **directly**, with no platform token in between. `hc_patients.user_id` is currently
  `VARCHAR(36) NULL` (added out-of-band by ALTER; phone+OTP patients leave it NULL).
- The platform has **no social login** today and **no generic MFA framework**; a generic OTP transport
  exists (`backend/app/routers/otp.py`, purposes incl. `staff_2fa`) and the module has its own OTP SDK
  (`modules/healthcare/sdk/otp.py`).

The decisions below resolve the 10 hand-off items in epic-18 §"Hand-off to B1".

## Decision

### D1 — Patient password on the platform `User`; login accepts username OR email

Patient credentials are stored on the platform `users.hashed_password`. No module credential columns
are added (the `hc_patients` PHI row never holds a password). Registration and reset reuse the platform
password policy, history, and hashing.

Platform `POST /api/v1/auth/login` is **email-first today** and must be extended to accept an
**identifier that is either an email or a username**:

- Add a nullable, unique `users.username` column (schema-hc-03 §P.4). It is optional for staff
  (unchanged behavior) and set for patients who choose a username at registration.
- Login resolves the user by: if the submitted identifier contains `@`, match on `email`; otherwise
  match on `username` (case-insensitive, `lower(username)`). The lookup remains a single
  `User` fetch; lockout, active-check, password-expiry, and session creation are unchanged.
- The failure response stays generic ("Incorrect email/username or password") — no enumeration.

This is a **platform** change (login router + `LoginRequest` schema accept `identifier` in addition to
the legacy `email` field, kept backward-compatible). It applies to all users, not only patients.

### D2 — Google identity in a new platform `user_identities` table; verified-email linking rule

Google (and any future OAuth provider) identity is stored in a **new platform-owned** table
`user_identities`, **not** a column on `hc_patients` (PHI stays module-side; identity stays
platform-side, matching D1's separation).

```
user_identities (
  id, user_id → users.id,
  provider,                 -- 'google' (extensible: 'apple', 'microsoft', ...)
  provider_subject,         -- Google 'sub' (stable per-user id), NOT the email
  email, email_verified,    -- email/verified as asserted by the provider at link time
  linked_at, last_login_at,
  UNIQUE (provider, provider_subject)
)
```

**Account-linking rule (anti-takeover).** On `google/callback`, after verifying the Google ID token
signature/audience/issuer and extracting `(sub, email, email_verified)`:

1. **Returning** — a `user_identities` row exists for `(google, sub)`: load its `User`, issue tokens.
   The link is keyed on the provider `sub`, never on email, so a user changing their Google email does
   not break the link and an attacker cannot hijack by email alone.
2. **First-time, provider `email_verified = true` AND a platform `User` exists with a **verified**
   matching email** (`User.is_verified = true` and `User.email = provider email`): **auto-link** —
   create the `user_identities` row for that user, issue tokens. Auto-link requires **both** sides
   verified.
3. **First-time, email matches an existing `User` but either side is unverified**: **do NOT auto-link.**
   Require an **explicit link step** — the user must prove control of the existing account (sign in
   with password, or complete an email-verification/OTP challenge) before the Google identity is
   attached. This prevents account takeover via an unverified-email collision.
4. **First-time, no email match**: **create** a platform `User(role=patient)` from the Google profile
   (`email`, `full_name`, `is_verified = email_verified`), assign the `patient` role + `patients`
   group (D8), create the linked `hc_patients` PHI shell, then require **consent capture + phone
   collection** (module PHI — cannot be skipped) before the portal is usable.

**Endpoints (PLATFORM, new):**

- `GET /api/v1/auth/oauth/google/start` — builds the Google authorization URL with **PKCE** and a
  signed, single-use **`state`** value (CSRF binding; stored server-side in Redis with a short TTL and
  bound to the browser via an HttpOnly cookie). Returns the redirect URL (or 302).
- `GET /api/v1/auth/oauth/google/callback` — validates `state` (CSRF), exchanges `code` + PKCE
  verifier, verifies the Google ID token, then runs the linking rule above and issues platform tokens
  (or an MFA challenge, D3) or routes to the completion/link step.

**Config.** `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and the allow-listed
`GOOGLE_OAUTH_REDIRECT_URIS` are **platform** configuration (env / secret store), not per-tenant and
not in the healthcare module. The redirect URI(s) are registered in the Google Cloud console and must
match exactly. Secret handling is covered in Consequences.

### D3 — Generic platform MFA framework; OTP as the first method; challenge/verify contract

MFA is a **generic platform** capability (designed so staff MFA can reuse it later), backed by a new
platform table `user_mfa` (schema-hc-03 §P.2):

```
user_mfa ( id, user_id → users.id, method, enabled, secret, enrolled_at, last_verified_at,
           UNIQUE (user_id, method) )
```

`method = 'otp_phone'` is the first (and, at MVP, only) method; `secret` is reserved for future
methods (e.g. TOTP shared secret) and is NULL for `otp_phone` (the factor is the on-file phone + the
OTP transport). OTP enrollment/challenge reuse the existing OTP transport (module
`modules/healthcare/sdk/otp.py` / platform `backend/app/routers/otp.py`, purpose `staff_2fa`
generalized).

**Enrollment (patient-scoped, MODULE endpoints setting PLATFORM state):**
`POST /api/v1/patients/me/mfa/enroll` (send + verify OTP → insert/enable `user_mfa` row) and
`.../disable` (fresh OTP or password re-auth → disable). This keeps patient-scoped endpoints in the
module while MFA state lives on the platform; the module writes platform state through the platform
SDK.

**Challenge/verify contract (PLATFORM, shared by password and OAuth entry paths):**

- When a login (`POST /api/v1/auth/login`) or the OAuth callback authenticates a user that has an
  `enabled` `user_mfa` row **and** the request does not present a valid trusted-device token (D4), the
  endpoint returns **`202` with `{ "mfa_required": true, "mfa_token": <short-lived, single-purpose
  challenge JWT>, "methods": ["otp_phone"] }`** instead of full access/refresh tokens. The `mfa_token`
  is a platform-signed JWT (`type: "mfa_challenge"`, ~5-minute TTL, bound to `user_id` and the login
  request), and an OTP is dispatched to the on-file phone.
- `POST /api/v1/auth/mfa/verify` (PLATFORM, new) accepts `{ mfa_token, code, remember_device? }`.
  On success it issues full platform access/refresh tokens (and, if `remember_device`, registers a
  trusted device, D4). The `mfa_token` is single-use.
- Only **after full platform tokens** does the SPA call `from-platform` (D6) to mint the patient
  token. The bridge is never reachable with a half-authenticated (MFA-pending) session because the
  `mfa_token` is not a normal access token.

MFA is **optional for patients** (opt-in via enrollment). Whether staff MFA is ever made **mandatory**
is deliberately out of scope here (open question, see Consequences) — the framework supports it but
this ADR does not enable it.

### D4 — Trusted-device store (`user_trusted_devices`)

A new platform table `user_trusted_devices` (schema-hc-03 §P.3) lets a verified MFA device skip the
second factor for a bounded window:

```
user_trusted_devices ( id, user_id → users.id, device_hash, label, created_at, expires_at,
                       last_used_at, revoked_at, UNIQUE (user_id, device_hash) )
```

- `device_hash` is an **HMAC** of a high-entropy device secret minted at `remember_device` time and
  stored in a signed, HttpOnly cookie bound to the browser (the raw secret is never stored server-side;
  only its HMAC is). On subsequent logins the platform re-derives the HMAC from the cookie and matches
  a non-expired, non-revoked row for the `user_id`; a match **suppresses** the MFA challenge (D3).
- Window: **30 days** (`expires_at = now + 30d`), configurable via platform security config; sliding
  `last_used_at` for observability.
- **Revocation:** all of a user's trusted devices are revoked on **password change / reset** (extends
  the existing `revoke_all_user_sessions` on password change in `auth.py`) and on **MFA disable**. A
  patient can also list/revoke devices from the security screen.

### D5 — `hc_patients.user_id` → NOT NULL + UNIQUE (one patient ↔ one platform user)

> **⚠ SUPERSEDED by Revision v2 → V-D5 (2026-07-06).** The household/proxy model makes the account
> holder ↔ patient relationship **1:N**. `hc_patients.user_id` is now **nullable + NOT UNIQUE**; authority
> to act for a patient moves to the new `hc_patient_relationships` table. Read V-D5 below; the text here is
> retained as v1 history only.

The invariant "one patient ↔ one platform user" is enforced in schema: `hc_patients.user_id` becomes
**NOT NULL** with a **UNIQUE** index. Migration ordering to get there safely is in D7 and detailed in
schema-hc-03 §M. Until the backfill + flag steps complete, the column stays nullable; the NOT NULL +
UNIQUE constraint is added **last**, after every legacy row has a linked platform user.

### D6 — `from-platform` is the single seam; OTP-passwordless routes through a platform token

> **⚠ PARTIALLY SUPERSEDED by Revision v2 → V-D7 (2026-07-06).** `from-platform` **remains the single
> seam** (that part stands), but it no longer loads "the single `hc_patients WHERE user_id = sub`." It now
> resolves the **authorized same-tenant patient set** and mints a token **scoped to an active `patient_id`**,
> with a companion `switch` endpoint. The 403-if-none gate is retained. Read V-D7 below.

The canonical `POST /api/v1/patients/auth/from-platform` bridge (already implemented) is the **single
seam** every method flows through to obtain a patient token — password login, Google OAuth, and OTP
all end by exchanging a **platform** JWT for the patient token. The bridge keeps its existing
authorization gate (active `hc_patients` where `user_id = sub`; 403 if none).

**OTP-passwordless (Story 18.4.3): route through a platform token, not a direct mint.** The legacy
`/patients/auth/token` path mints a patient token directly. We change it (module side) to, on OTP
success: resolve `hc_patients → user_id → platform User`, mint a **platform** access token for that
user (via the platform token helper / an internal platform-issued token), then call `from-platform`.

- **Trade-off.** *Direct mint* is minimal-change but produces a patient session with **no platform
  session record**, so it escapes platform lockout, session listing, and revoke-all (D8) — an
  inconsistent, harder-to-govern session model. *Route-through-platform* costs one extra internal hop
  and requires every OTP-passwordless patient to have a `user_id` (guaranteed by D5/D7), but yields a
  **single, uniform session model**: every patient session is backed by a platform session and is
  governed by platform revoke-all, lockout, and audit.
- **Decision: route through a platform token.** Consistency and revocability outweigh the extra hop.
- If a patient has MFA enabled, **passwordless-OTP itself satisfies the factor** — the OTP *is* the
  authentication, so no second OTP challenge is issued for this path (recommended in epic-18 18.4.3).

### D7 — Migration: backfill platform users for legacy OTP-only patients; `must_set_password` + grace

Legacy patients exist as `hc_patients` rows with `user_id = NULL` (phone+OTP only). Migration
(MODULE-driven, creating PLATFORM users) proceeds in this order (schema-hc-03 §M):

1. **Add** `users.must_set_password BOOLEAN NOT NULL DEFAULT FALSE` and `users.username` (D1),
   nullable/unique. Ensure `hc_patients.user_id` is still nullable.
2. **Backfill:** for every `hc_patients` with `user_id IS NULL`, create a platform
   `User(role=patient)` seeded from the patient's name (and a placeholder/unusable password hash),
   set `is_verified = false`, assign the `patient` role + `patients` group, and set the new
   `hc_patients.user_id`. The account is **login-only via OTP** until a password is set.
3. **Set flags:** on the backfilled users set `must_set_password = true`.
4. **Constrain:** once **no** `hc_patients.user_id` is NULL, add `NOT NULL` and the `UNIQUE` index
   (D5). This is the last step so it cannot fail mid-backfill.

Runtime companion: on the next OTP login of a `must_set_password` user, the SPA routes through a
**"set a password" (+ optional link Google) interstitial** (`/patient/claim-account`), skippable within
a grace period, then enforced. `must_set_password` is the persisted flag driving this; the placeholder
credential means the account cannot be password-logged-in until the patient sets one.

### D8 — Sessions/logout: logout clears both; patient token is server-side revocable via jti

**Logout clears both tokens** (the already-implemented contract): the SPA calls platform
`POST /api/v1/auth/logout` (blacklists the platform token by `jti`, `tokens`/`TokenBlacklist`) **and**
module `POST /api/v1/patients/auth/logout` (clears the `patient_refresh_token` HttpOnly cookie).
Platform session listing / single-revoke / revoke-all (`/api/v1/auth/me/sessions*`) surface patient
sessions the same way as staff, because every patient session is now backed by a platform session
(D6).

**Make the patient token server-side revocable so platform revoke-all invalidates it.** Today the
patient token is a self-expiring JWT with **no `jti`**, so a platform "revoke all sessions" cannot
reach it. We add a **`sid` (session id / jti) claim** to the patient token that carries the **platform
session `jti`** from which it was bridged, plus keep the short 15-minute access TTL. The module
`get_current_patient` dependency (and refresh) check the shared blacklist / platform session state for
that `sid`; when the platform session is revoked, the bridged patient token stops refreshing and its
short access TTL bounds residual validity. This binds the patient session lifetime to the platform
session lifetime without operating a second revocation store.

- **Passwordless-OTP** (D6) also routes through a platform token, so it inherits the same `sid`
  binding — revoke-all reaches it too.

### D9 — Abuse & audit: extend rate-limit/CAPTCHA to OAuth+MFA; lockout on patient login; split audit

- **Rate limiting (extends ADR-HC-003 §D3).** Add `slowapi` limits to the **new** endpoints:
  `/auth/oauth/google/start`, `/auth/oauth/google/callback`, `/auth/mfa/verify`, and the module
  `/patients/me/mfa/*`. Keep the existing limits on `/patients/register`, `/patients/auth/otp/*`,
  `/patients/auth/token`. CAPTCHA (`sdk/captcha.py`) gates the public write endpoints (register,
  otp/send, passwordless token) and escalates on the OAuth start endpoint on repeated failure.
- **Lockout.** The platform `LockoutManager` + login-attempt tracking now applies to
  `role=patient` logins (patients have passwords) — no code path change beyond D1's identifier
  resolution; lockout is per-`User`.
- **Audit split (keep PHI out of platform audit).**
  - **Identity events → platform audit** (`create_audit_log`, `audit_logs`): `user.created`,
    `user.login`, `user.oauth_login`, `user.oauth_linked`, `user.mfa_enrolled`, `user.mfa_disabled`,
    `user.mfa_challenge`, `user.mfa_passed`, `user.trusted_device_added`, `user.password_reset`,
    `user.password_changed`, `user.logout`.
  - **PHI-scoped events → module `hc_audit_log`** (ADR-HC-002): `patient.registered`,
    `patient.session_created`, `patient.session_ended`, `patient.migrated_to_platform_user`. These
    never carry decrypted PHI; they reference `patient_id` only.
  - No PHI (name, DOB, NIK, phone) is written to the platform `audit_logs`.

### D10 — Retain the patient JWT claim shape and ADR-HC-001/002 conformance

The minted patient token retains ADR-HC-003 §D1's shape: `roles: ["patient"]`, `tenant_id: null`,
`patient_id` present — plus the new `sid` claim (D8). The `get_current_patient` dependency and gateway
route separation (ADR-HC-003 §D2) are unchanged. PHI continues to be read only via SDK readers with
audit (ADR-HC-002); branch isolation (ADR-HC-001) is unaffected because patient identity spans tenants
(`tenant_id: null`).

## Consequences

### Positive

- **One identity, one credential store.** All three methods resolve to a single platform
  `User(role=patient)`; password/policy/history/lockout/reset/session all reuse the platform, no
  duplicate auth stack.
- **Uniform, revocable sessions.** Routing every method (incl. passwordless-OTP) through a platform
  token + the `sid`-bound patient token gives a single session model governed by platform revoke-all,
  lockout, and audit (D6, D8).
- **Generic, reusable MFA + trusted-device framework** (D3, D4) — staff MFA can reuse it later without
  new tables.
- **Anti-takeover linking** (D2) — provider-`sub` keying + verified-only auto-link closes the classic
  "unverified email collision" account-takeover vector.
- **PHI/identity separation preserved** — Google links and MFA live on platform tables; `hc_patients`
  gains no credential/identity columns beyond the existing `user_id`.

### Negative / Security & Ops

- **New public attack surface.** Google `start`/`callback` and `mfa/verify` are new
  unauthenticated/pre-auth endpoints. Mitigation: PKCE + signed single-use `state` (CSRF), rate limits
  + CAPTCHA (D9), strict ID-token validation (signature, `aud`, `iss`, `exp`, `email_verified`), exact
  redirect-URI allow-list.
- **Google OAuth secret management.** `GOOGLE_OAUTH_CLIENT_SECRET` is a new production secret. It must
  be provisioned in the platform secret store (not committed, not per-tenant), rotated on a schedule,
  and scoped to the exact registered redirect URIs. Client id/secret provisioning is an **operational
  prerequisite** the manager must surface (open question below).
- **Migration risk.** The backfill creates one platform `User` per legacy patient; a partial run
  leaves some `user_id` NULL, which is why NOT NULL + UNIQUE is the **last** step (D7). Placeholder
  credentials mean those users can only OTP-login until they set a password — the grace interstitial
  must be shipped with the migration or legacy patients are stuck at OTP-only (acceptable, but must be
  communicated).
- **`must_set_password` + trusted-device cookie** add two new client-visible states; the SPA must
  handle the `202 mfa_required` and `claim-account` interstitials on every entry path.
- **Cross-service coupling on `SECRET_KEY`.** The bridge and both token issuers share `SECRET_KEY`;
  the new `sid` binding also couples patient-token validity to platform session state (a shared
  blacklist/session lookup). Mitigation: this coupling is intentional (single revocation authority)
  and already partly present (shared secret for `from-platform`).

## Ratified refinements (2026-07-06)

The user ratified four refinements to the decisions above. These **annotate/amend** the existing
decisions — they do not rewrite them.

### R1 — Google OAuth credential provisioning is an explicit operational prerequisite (amends D2 / Consequences)

Provisioning the Google OAuth credentials is a **hard operational prerequisite**, recorded here (and in
Consequences → "Google OAuth secret management") as a blocker on the OAuth feature:

- **User/ops** (not the module) creates the OAuth client in the **Google Cloud console**, registers the
  exact allow-listed redirect URIs, and loads `GOOGLE_OAUTH_CLIENT_ID` + `GOOGLE_OAUTH_CLIENT_SECRET`
  (and `GOOGLE_OAUTH_REDIRECT_URIS`) into the **platform secret store** (not committed, not per-tenant,
  rotated on a schedule).
- **Dev/engineering** only wires the config plumbing (reads the values from the secret store/env; exact
  redirect-URI allow-list; PKCE + signed `state`). No dev action can substitute for the credentials.
- **Feature 18.3 (Google OAuth sign-in) is BLOCKED until the credentials are provisioned.** The
  password (D1) and OTP (D6) paths do not depend on this and can ship independently.
- **No schema change.**

### R2 — Staff MFA stays opt-in this phase; staff-mandatory MFA out of scope (annotates D3)

MFA is **opt-in for BOTH patients and staff** this phase. This resolves the open question left in D3 /
Consequences ("whether staff MFA is ever made mandatory"):

- **Staff-mandatory MFA is explicitly OUT OF SCOPE** for this phase — a future product ruling, not an
  architecture decision. The `user_mfa` framework (D3) is generic and **can** support mandatory staff
  MFA later (per-role enforcement policy) with **no schema change**; this ADR does not enable it.
- Patients remain opt-in (unchanged). No behavior change for staff beyond the existing opt-in
  enrollment path being available to them via the same generic framework.
- **No schema change.**

### R3 — Legacy claim-account grace = persistent soft nudge + optional per-tenant hard cutoff (amends D7)

D7's "skippable within a grace period, then enforced" is refined:

- Backfilled `must_set_password = true` patients get a **persistent soft nudge** to claim their account
  (set a password, optionally link Google) on **every** entry — the `/patient/claim-account`
  interstitial is shown and **skippable indefinitely by default** (no hard lock-out by default), so a
  legacy OTP-only patient is never stranded.
- Optionally, a tenant may configure a **hard cutoff**: after **N days** from the backfill/first-nudge,
  a still-unclaimed (`must_set_password = true`) patient is **blocked from non-claim login** until they
  set a password. `null` / unset = **no hard cutoff** (soft nudge forever).
- **Where the cutoff config lives — tenant setting, reusing existing tenant-settings JSON (no new
  column).** The cutoff is a **per-tenant security-policy setting** under the key
  **`patient_account_claim_grace_days`** (integer days; `null` = no hard cutoff). It is stored in the
  existing tenant-settings / security-policy JSON blob (`TenantSettings`), **not** a new column — this
  is a per-tenant policy knob, consistent with other security-policy settings, and avoids a schema
  migration. The claim-account flow reads this key at login: if set and
  `now > backfilled_at + N days` and `must_set_password` still true → block with a "set your password
  to continue" state; otherwise show the skippable soft nudge.
- **Schema touch:** **none required** on `users`/`hc_patients` — reuses the tenant-settings JSON. (If a
  tenant-settings store does not already expose a security-policy JSON blob, adding the
  `patient_account_claim_grace_days` key to whatever tenant-settings mechanism exists is the intended
  path; prefer the JSON key over a dedicated column. Flagged for the manager to confirm the exact
  `TenantSettings` key path — see the open question below.)

### R4 — Cross-DB `hc_patients.user_id` integrity: real FK when shared-DB, app-enforced fallback when split (amends D5 / schema-hc-03 §M)

D5 makes `hc_patients.user_id` NOT NULL + UNIQUE. This refinement pins the **referential** integrity to
platform `users`, made **consistent with ADR-HC-005 addendum A1** (org-linkage cross-DB posture):

- **Shared-DB deployments (current dev — healthcare + platform both in `appdb`):** declare a **real FK
  `hc_patients.user_id → users.id`** (in addition to the NOT NULL + UNIQUE from D5). The DB enforces
  that every patient references an existing platform user.
- **Split-DB deployments (module and platform in separate databases):** the cross-service FK is not
  declarable; integrity stays **app-enforced** at registration/bridge time (the documented fallback),
  with the NOT NULL + UNIQUE constraints still enforced within the module DB.
- This is deliberately the **same cross-DB posture** as ADR-HC-005 addendum A1/A3
  (`hc_branches.platform_*` and `hc_departments.platform_department_id`): real FK when shared, app-
  enforced when split — one integrity story across both ADRs.

### Ratified-refinements decision log

| # | Ratified | Amends | Schema touch |
|---|---|---|---|
| R1 | Google OAuth creds are an ops prerequisite; Feature 18.3 blocked until provisioned; dev wires config only | D2 / Consequences | none |
| R2 | MFA opt-in for patients **and** staff; staff-mandatory MFA out of scope (future product ruling; framework supports it) | D3 / Consequences | none |
| R3 | Claim-account = persistent soft nudge + optional per-tenant hard cutoff via `patient_account_claim_grace_days` (tenant-settings JSON, `null` = none) | D7 | none (reuse tenant-settings JSON, no new column) |
| R4 | `hc_patients.user_id` real FK → `users.id` in shared-DB; app-enforced fallback when split | D5 / schema-hc-03 §M | schema-hc-03 §M annotated (conditional FK) |

**Open question flagged for the manager (R3):** confirm the exact tenant-settings key path/mechanism
for `patient_account_claim_grace_days` (which `TenantSettings` / security-policy JSON field). The
decision to reuse the tenant-settings JSON over a new column is made; only the concrete key location
needs the platform-settings owner's confirmation.

---

## Revision v2 (2026-07-06) — Household / Proxy Access

**Trigger.** Epic-18 v2 introduced a new requirement: **one platform account holder may be linked to many
`hc_patients`** — their own "self" patient PLUS zero-or-more dependents (spouse, children, elderly parents)
they register and manage from a single login (epic-18 "Impact Review" + **Feature 18.10**,
Stories 18.10.1–18.10.6). This **supersedes the 1:1 identity model** (D5) and the single-patient bridge (D6).

**Four product/legal rulings by the user (recorded in epic-18 §"Product/legal decisions … RESOLVED")** are
baked in below and drive the design:

| # | Ruling | Design consequence |
|---|---|---|
| **Q1** | **ALLOW** adult-for-adult consent — an account holder may manage & consent for another *competent adult*; consent must record who/for-whom/basis. | Consent-basis field + `on_behalf_of` audit (V-D9). Operator owns the consent-law posture (note carried below). |
| **Q2** | **WITHIN ONE TENANT** — the household is confined to the account holder's tenant; a dependent at a different-tenant clinic is rejected. | Same-tenant constraint on the relationship table (V-D6); **token stays simple** — `tenant_id: null` claim shape retained but the resolved patient set is same-tenant (V-D7). |
| **Q3** | **CLINIC-STAFF APPROVAL** to link an *existing* patient — the account holder's request creates a `pending` relationship a **staff member at the patient's clinic** approves. | `pending → active` state machine + a branch-scoped staff approval endpoint; no self-service OTP claim (V-D8). |
| **Q4** | **CLINIC-MEDIATED** majority transition — staff detach a minor dependent → convert to self-owned, revoke prior proxy grants pending re-consent. | Staff-mediated detach endpoint; relationship → `self`/owner, prior grants `revoked` (V-D10). |

This revision does **not** touch D1 (patient password on platform `User`), D2 (`user_identities`), D3 (MFA),
D4 (trusted devices), D9 (abuse/audit split), or D10 (claim shape) except where explicitly threaded below.
The `tenant_id: null` / `roles: ["patient"]` patient-JWT claim shape (ADR-HC-003 §D1, D10) is **retained
verbatim**; V-D7 only *adds* the active-`patient_id` scoping (which the token already carried as `sub`).

### V-D5 — Supersede D5: `hc_patients.user_id` is nullable + NOT UNIQUE (owner denormalization only)

D5's "NOT NULL + UNIQUE" is **withdrawn.** Under the household model:

- `hc_patients.user_id` is **nullable** — a clinic-created dependent may have **no login of its own** (a
  child/elderly parent managed entirely by the account holder). The registration flow in epic-18 18.10.2
  creates such dependents with null credentials.
- `hc_patients.user_id` is **NOT UNIQUE** — a single account holder (one `users.id`) **owns many**
  `hc_patients` rows (self + dependents), so `user_id` repeats across rows.
- `user_id` is **retained only as a convenience denormalization of the owner** (the account holder who owns
  the row). It is **not** the authorization authority anymore. **Authority to act for a patient flows through
  the new `hc_patient_relationships` table** (V-D6): a caller may act for patient P iff an `active`
  relationship row exists linking `account_user_id = caller` to `patient_id = P`. Where `user_id` is set it
  MUST equal the `account_user_id` of that patient's `role = owner` relationship (a denormalized mirror,
  app-maintained; see schema-hc-03 §M for the invariant note).
- **Referential integrity (carries R4 forward):** the `hc_patients.user_id → users.id` posture is unchanged
  from R4 — **real FK in shared-DB**, app-enforced when split — but the FK is now on a **nullable, non-unique**
  column (a plain FK, no UNIQUE index). The relationship table's `account_user_id` FK carries the same
  shared-DB-FK / split-DB-app-enforced posture (schema-hc-03 §M).
- **Migration impact.** The D7 backfill still runs (every self-owned legacy patient gets a platform user and
  a `role = self`/`owner` relationship row), but STEP 4 of schema-hc-03 §M — "add UNIQUE index, then NOT
  NULL" — is **removed**. `user_id` keeps its existing **non-unique** lookup index. See schema-hc-03 §M v2.

### V-D6 — New relationship / guardianship table `hc_patient_relationships` (MODULE, RLS-scoped)

The authority for "who may act for this patient" is a new **module-side** table, `hc_patient_relationships`
(chosen name; epic-18 18.10.1 floated `hc_patient_guardianships` / `hc_patient_links` — this ADR fixes the
name to `hc_patient_relationships`, which covers self + guardianship + delegated-adult + spousal uniformly).
It is **PHI-adjacent and RLS-scoped** (tenant + patient scope), living beside `hc_patients` in the module DB
(full DDL in schema-hc-03 §M v2). Columns and semantics:

| Column | Meaning |
|---|---|
| `id` | PK (UUID). |
| `tenant_id` | Tenant scope (RLS). Equals the patient's tenant AND the account holder's tenant — the **same-tenant (Q2) invariant**. |
| `branch_id` | Nullable — the patient's clinic/branch context (`hc_branches.id`, adr-hc-001) captured for the staff-approval routing (Q3) and audit; nullable because a tenant-wide patient may predate a branch assignment. |
| `account_user_id` | FK → `users.id` — the **account holder** (the platform login that acts). Same-DB real FK / split-DB app-enforced (R4 posture). |
| `patient_id` | FK → `hc_patients.id` — the managed patient. |
| `relationship` | ENUM/CHECK `('self','spouse','child','parent','other')` — the real-world tie. Drives the consent **basis** default (V-D9). |
| `role` | CHECK `('owner','proxy')` — `owner` = the account that owns/created the record (may consent + manage); `proxy` = an additional account granted access (e.g. the second parent, 18.10.5). |
| `status` | CHECK `('active','pending','revoked')` — `pending` = awaiting clinic-staff approval (Q3); `active` = usable; `revoked` = terminated (grant revoke or majority detach). |
| `basis` | CHECK `('self','parental_guardian','delegated_adult','spousal')` — the **legal basis** for acting/consenting, per Q1. Denormalized here (mirrors the consent row's basis, V-D9) so the bridge can gate without a consent join. |
| `granted_by` | `users.id` of who created the grant (the account holder for self/owner registration; either parent for a proxy grant). |
| `granted_at` | Timestamp of grant creation. |
| `approved_by_staff_id` | Nullable `users.id` of the **clinic staff** who approved a `pending` link (Q3); NULL for `self`/owner rows and directly-created owner-dependent rows that need no approval. |
| `approved_at` | Nullable timestamp of staff approval. |
| `revoked_at` | Nullable timestamp of revoke / majority detach. |
| `created_at` / `updated_at` | Row audit timestamps. |

**Constraints (see schema-hc-03 §M v2 for exact DDL):**

1. **`UNIQUE(account_user_id, patient_id)`** — an account holder has at most one relationship row per patient
   (a grant is not duplicated; re-grant reactivates/updates the existing row).
2. **Exactly one `self` per account holder** — a **partial unique index** on `account_user_id WHERE
   relationship = 'self'`. An account holder has exactly one self patient (their own record); everyone else is
   a managed dependent. (Enforces "one self" without forbidding many managed rows.)
3. **Same-tenant (Q2)** — `tenant_id` on the relationship row must equal both the patient's `tenant_id` and
   the account holder's tenant. The DB CHECK can only assert the relationship row's own `tenant_id` matches
   the joined `hc_patients.tenant_id` (a real FK/trigger in shared-DB); the account-holder-tenant side is
   **app-enforced** at grant/link time (the account holder's platform tenant is read from the platform user
   and compared) because `users` is platform-side and may be split-DB. Cross-tenant link/register requests
   are **rejected with 422** (epic-18 18.10.2/18.10.3 AC).
4. **`role`/`relationship` coherence** — `relationship = 'self'` implies `role = 'owner'` and `basis =
   'self'` (a CHECK); a non-self row may be `owner` (the registering account) or `proxy` (an additional grant).

**Multi-owner semantics (resolves epic-18 18.10.5 open "can two accounts both be owner?"):** **one `owner`
per patient**, plus zero-or-more `proxy` grants. The account that registers/creates the dependent is the
`owner`; a second parent (18.10.5 "both parents manage a child") gets a `proxy` grant (still full act-on-behalf
access, but not "owner"). This keeps a single, unambiguous consent-owner per patient. (Alternative — multiple
co-owners — rejected: it muddies who owns the consent-law posture the operator is on the hook for under Q1.)

**RLS applicability.** Unlike the D2/D3/D4 platform identity tables (which are `user_id`-keyed, not RLS), this
is a **module, patient-scoped table** and **IS** an `hc_*` RLS object: it carries `tenant_id` (+ `branch_id`)
and is governed by the healthcare `current_setting('app.tenant_id'/'app.branch_id')` GUCs (adr-hc-001), the
same as `hc_patients`. Patient-portal reads of a caller's own household are additionally filtered by
`account_user_id = <caller's platform user>` in the query (the portal session knows the account holder).

### V-D7 — Supersede D6: bridge resolves the same-tenant set → active-patient token; `switch` endpoint

The `from-platform` bridge **remains the single seam** (D6 stands on that point), but its resolution changes:

**`POST /api/v1/patients/auth/from-platform` (revised).** After validating the platform JWT (`sub` = account
holder `users.id`):

1. Resolve the **authorized patient set** = all `hc_patients` P such that an **`active`**
   `hc_patient_relationships` row exists with `account_user_id = sub` and `patient_id = P.id` (self + owned +
   proxied), **within the account holder's tenant** (Q2 — the set is single-tenant by construction, so no
   cross-tenant token is ever needed).
2. **Choose the active patient:** if the request carries a `patient_id` (query/body) and it is in the set,
   that is the active patient; else default to the caller's `self` patient; else, if the set has exactly one
   member, that member.
3. **If the set is empty → 403** (unchanged gate from D6 — "no patient portal profile linked").
4. **If the set has >1 member and none was pre-selected**, the bridge MAY return the selectable set (see the
   `household` endpoint below) instead of assuming one — epic-18 18.6.1/18.10.4 AC. (Recommended: default to
   `self` and let the SPA switch, so the happy path is one call; return the set only when there is no `self`.)
5. Mint the patient token **scoped to the active `patient_id`** — the token's `sub`/`patient_id` = active
   patient (this is already how the token carries the patient; V-D7 only formalizes that the active patient is
   *chosen from a set* rather than *the only one*). Claim shape is **unchanged** (`roles: ["patient"]`,
   `tenant_id`: the active patient's tenant — a concrete tenant, not the account-holder-null; `sid` per D8).
   Add an **`acct` claim = the account holder `users.id`** and an **`obo` (on_behalf_of) boolean/flag** set
   true when `active patient ≠ self`, so downstream PHI readers can thread proxy attribution (V-D9) without a
   DB round-trip. `phone` remains the active patient's phone.

**Household discovery — separate endpoint, not a claim.** The full authorized set is **not** stuffed into the
token (keeps it small and avoids a re-mint when the set changes). Instead:

- **`GET /api/v1/patients/me/household` (MODULE, patient-authenticated)** — returns the caller's authorized
  set (self first, then managed) with relationship + minimal display fields (name, clinic/branch, DOB) for the
  switcher UI (epic-18 18.10.1). PHI-read-audited (adr-hc-002; each listed patient's minimal PHI read is
  logged). Authorization: the caller's `acct` claim = the account holder; rows filtered by
  `account_user_id = acct AND status = 'active'`.

**Switch — re-mint, not multi-scope.** 

- **`POST /api/v1/patients/auth/switch` (MODULE)** — body `{ patient_id }`. Validates the target is in the
  caller's `active` set for `account_user_id = acct` (403 otherwise), then **re-mints** the patient token
  scoped to the new active `patient_id` (new `obo`, same `acct`, same `sid`). The prior scoped access token is
  short-lived (15 min, D8) so it self-expires; the refresh cookie is rotated to the new scope. (Equivalently, a
  `patient_id` param on `from-platform` re-scopes — the dedicated `switch` endpoint is the clearer contract and
  is what epic-18 18.10.4 specifies.)

**Interaction with D8 (`sid` / revoke-all).** The `sid` claim continues to carry the **platform session
`jti`**; switching **re-mints under the same `sid`** (same platform session, different active patient), so a
switch does not create a new platform session. Platform **revoke-all** invalidates the platform session `jti`,
which invalidates **every** scoped patient token minted under it (all household members) — one revocation
authority, unchanged from D8. Grant-revoke and majority-detach (V-D10) invalidate a *specific* pairing by
flipping the relationship to `revoked`: the next `from-platform`/`switch`/`refresh` for that `patient_id` fails
the "in the active set" check, and the 15-min access TTL bounds any residual validity.

**OTP-passwordless (D6) still routes through a platform token**, so it too resolves the household set and lands
on `self` by default — unchanged mechanism, now household-aware.

### V-D8 — Link an existing patient by clinic-staff approval (Q3): `pending → active` state machine

Epic-18 18.10.3 + Q3: an account holder may request to link an **existing** `hc_patients` record (created at a
clinic before they had an account). **No self-service OTP claim** — a **staff member at the patient's clinic**
approves.

**State machine.**

```
(none) --request--> pending --staff approve--> active
                       \--staff reject-------> revoked   (terminal; request closed)
                       \--account cancels-----> revoked
```

**Request side (account holder, MODULE, patient-authenticated as the account holder's portal session):**

- **`POST /api/v1/patients/me/household/link`** — body identifies the target patient by a **non-enumerating**
  identifier (e.g. clinic + medical-record-number, or a clinic-issued reference), NOT by a probe that reveals
  existence. Creates a `hc_patient_relationships` row `status = 'pending'`, `role = 'proxy'` (or `owner` per
  policy — recommend `proxy` for links; direct registration remains the `owner` path), `relationship` as
  claimed, `granted_by = account_user_id`, `branch_id` = the patient's clinic.
- **Anti-enumeration.** The endpoint returns a **uniform response** ("if a matching record exists, your request
  has been sent to the clinic for approval") **regardless** of whether the identifier matched — it never
  confirms existence before approval. A non-matching request either creates no row or a self-expiring
  placeholder; either way the response is identical. Rate-limited + CAPTCHA per D9 / epic-18 18.8.
- Emits `patient.link_requested` (module `hc_audit_log`, PHI-scoped, references `patient_id` only).

**Approval side (clinic staff, MODULE, staff-authenticated):**

- **`POST /api/v1/patients/branches/{branch_id}/household/link-requests/{relationship_id}/approve`** and the
  matching **`/reject`**, plus a queue **`GET /api/v1/patients/branches/{branch_id}/household/link-requests`**
  (lists `pending` rows for that branch). These are **branch-scoped staff endpoints** following the existing
  healthcare staff pattern (`/branches/{branch_id}/…`, `hc_branch_staff` RBAC, `X-Branch-ID` staff auth,
  adr-hc-001 branch isolation). The staff caller MUST be an active `hc_branch_staff` at the patient's
  `branch_id`; the permission is a **new HCRole capability `patient_link:approve`** granted to
  `branch_manager` and `clinic_owner` (and optionally `doctor`/`nurse` per operator policy) — the same
  role-gating shape the other `/branches/{branch_id}/…` routes use. On approve: set `status = 'active'`,
  `approved_by_staff_id = <staff user>`, `approved_at = now`. Emits `patient.link_approved` /
  `patient.link_rejected` (module audit).
- A `pending` relationship is **not** in the account holder's active set, so V-D7's bridge/switch cannot mint a
  token for it until approved.

### V-D9 — Proxy consent basis + `on_behalf_of` audit (Q1 / epic-18 18.10.6)

**Consent basis (Q1 = allow adult-for-adult).** Extend `hc_patient_consents` with a **`basis`** column —
CHECK `('self','parental_guardian','delegated_adult','spousal')` — and a **`consented_by_user_id`** column
(nullable `users.id`) recording **who** consented when it is not the patient themselves. Combined with the
existing `patient_id` (for whom), `consent_version`, `accepted_at`, `ip`, `user_agent`, this satisfies "who
consented, for whom, on what basis, when" (18.10.6 AC). For a self patient, `basis = 'self'` and
`consented_by_user_id = NULL` (or = the patient's own user). For proxy consent, `basis` reflects the
relationship (`parental_guardian` for a minor child, `delegated_adult`/`spousal` for a competent adult per Q1)
and `consented_by_user_id` = the account holder. (Full DDL in schema-hc-03 §M v2.)

> **Legal-responsibility note (carried from epic-18 Q1).** Allowing an account holder to consent for another
> **competent adult** is the **operator's explicit product choice**. This design **records** proxy consent
> faithfully (basis + who + for-whom + version + IP/UA + immutable audit) but the **operator owns the
> consent-law posture** — the architecture does not warrant that adult-for-adult delegation is lawful in a
> given jurisdiction. The consent-basis field exists precisely so the operator can demonstrate the basis
> claimed at consent time.

**`on_behalf_of` audit thread (token → SDK readers → `hc_audit_log`).** When the active patient ≠ self, every
PHI read/write must be attributed as "account holder acting on behalf of patient":

- The **token** carries `acct` (account holder) + `obo` (true when active ≠ self) from V-D7.
- **SDK PHI readers** (`get_current_patient` in `sdk/patient_auth.py`) are extended to surface `acct` and
  `obo` on `PatientTokenData` (new optional fields; the existing `patient_id`/`tenant_id` contract is
  unchanged). `write_phi_read_audit` / `write_event_audit` (`sdk/phi_audit.py`) gain an **`on_behalf_of`**
  attribution: when `obo` is set, the audit row's `actor_id` = the account holder (`acct`), `actor_type =
  'patient'`, and `metadata.on_behalf_of = patient_id` (the managed patient). When active = self, behaviour is
  unchanged (`actor_id = patient_id`). This keeps the attribution **inside module `hc_audit_log`** (PHI-scoped,
  adr-hc-002); **no PHI and no proxy relationship is written to the platform `audit_logs`** (D9 split
  preserved — identity events to platform audit, patient/PHI events to module audit).
- Portal UI shows a persistent "acting on behalf of {name}" banner whenever `obo` (epic-18 18.10.6 FE AC).

### V-D10 — Clinic-mediated majority transition (Q4)

Epic-18 18.10.5 + Q4: transitioning a minor dependent to self-ownership is **staff-mediated**, not automatic
and not self-service.

- **`POST /api/v1/patients/branches/{branch_id}/household/{patient_id}/detach` (MODULE, staff-authenticated,
  branch-scoped)** — same staff-auth shape as V-D8 (`hc_branch_staff` at the patient's branch; new HCRole
  capability `patient_link:detach` for `branch_manager`/`clinic_owner`). On execution:
  1. The dependent's `hc_patients` row is **converted to self-owned**: the relationship where `patient_id` =
     the dependent and `role = 'owner'` (the parent's grant) is set `status = 'revoked'`, `revoked_at = now`;
     a **new `self`/`owner` relationship** is created binding the patient to **their own** platform user (which
     must exist — if the now-adult has no login yet, the flow provisions/claims one via the D7 backfill/claim
     path first) with `relationship = 'self'`, `basis = 'self'`.
  2. **All prior `proxy` grants** on that patient are set `status = 'revoked'` — access by former proxies stops
     immediately (their next bridge/switch/refresh fails the active-set check, V-D7).
  3. Prior proxy grants that should continue **require re-consent** — they must be re-requested (V-D8) and
     re-approved; the majority transition does not silently preserve them.
  4. `hc_patients.user_id` is repointed to the now-adult's own user (owner denormalization, V-D5).
  5. Emits `patient.majority_detached` + `patient.grants_revoked` (module audit).
- **Config.** The age-of-majority threshold is a **per-tenant policy setting** (reusing the tenant-settings
  JSON, consistent with R3's `patient_account_claim_grace_days` pattern — **no new column**); it only *flags*
  candidates for staff review — the transition itself is always a **staff action** (Q4), never automatic.

### V-D11 — Consequences & security (household / proxy)

**Positive.**

- **Token stays simple (Q2 payoff).** Because the household is single-tenant, the minted token needs **no
  multi-tenant patient set**; the `tenant_id: null` claim shape (ADR-HC-003 §D1, D10) is retained and each
  scoped token carries the active patient's concrete tenant. No new cross-tenant token machinery.
- **One revocation authority preserved.** The `sid`-bound patient token (D8) still ties all household sessions
  to the platform session; revoke-all reaches every scoped token. Grant-level revoke is handled by the
  relationship `status` + short access TTL — no second revocation store.
- **Clear consent ownership.** One `owner` per patient + the consent-basis field give a single, auditable
  answer to "who consented for this patient, on what basis."

**Negative / Security.**

- **New proxy attack surface.** "Act on behalf of another patient" is a powerful capability. Mitigations:
  authority flows **only** through `active` relationship rows (never a bare `user_id`); linking an existing
  record requires **clinic-staff approval** (Q3, V-D8) — an account holder cannot unilaterally attach a
  stranger; the link-request endpoint is **anti-enumerating** + rate-limited + CAPTCHA (D9); the `switch`
  endpoint re-validates the active set on every re-mint.
- **"Act on behalf" audit is mandatory, not optional.** Every non-self PHI access MUST be recorded as
  `on_behalf_of` (V-D9). This is a hard requirement, not best-effort — the `obo` claim + threaded audit make it
  automatic, but reviewers must verify no PHI route bypasses the SDK readers.
- **Elevated consent-law responsibility (Q1).** Adult-for-adult consent shifts real legal exposure onto the
  operator. The design records the basis faithfully but **does not** and **cannot** validate lawfulness — this
  MUST be surfaced to the operator (carried in V-D9's legal note and flagged to the manager).
- **Same-tenant enforcement has an app-enforced half.** The relationship-row↔patient tenant match can be a DB
  CHECK/FK (shared-DB) but the account-holder-tenant side is app-enforced (platform `users` may be split-DB) —
  a bug there could admit a cross-tenant link. Covered by the grant/link validation + the branch-scoped staff
  approval, but it is an app-integrity point to test.

### Revision-v2 decision log

| # | Decision | Supersedes / amends | Schema touch |
|---|---|---|---|
| V-D5 | `hc_patients.user_id` **nullable + NOT UNIQUE**; owner denormalization only; authority via relationship table; R4 FK posture retained on a plain (non-unique) FK | **Supersedes D5** | schema-hc-03 §M v2 (drop UNIQUE + NOT NULL steps; keep non-unique index) |
| V-D6 | New module table **`hc_patient_relationships`** (RLS-scoped): account_user_id, patient_id, relationship, role(owner/proxy), status(active/pending/revoked), basis, granted_by/at, approved_by_staff_id/at, revoked_at, tenant/branch; UNIQUE(account_user_id,patient_id); one-`self`-per-holder; same-tenant (Q2) | New (18.10.1) | schema-hc-03 §M v2 (new table DDL) |
| V-D7 | Bridge resolves same-tenant **set** → mints **active-`patient_id`**-scoped token (+`acct`/`obo` claims); `GET /me/household`; `POST /auth/switch` re-mints under same `sid`; revoke-all reaches all | **Supersedes D6** (seam retained) | none (token claims are runtime; no schema) |
| V-D8 | Link existing patient = **clinic-staff approval** (Q3): `pending→active` state machine, branch-scoped staff approve/reject/queue endpoints (`patient_link:approve` for branch_manager/clinic_owner), anti-enumerating request side | New (18.10.3) | uses `hc_patient_relationships.status`/`approved_by_staff_id` (V-D6) |
| V-D9 | Consent **basis** + `consented_by_user_id` on `hc_patient_consents` (Q1); `on_behalf_of` thread token(`acct`/`obo`)→SDK readers→`hc_audit_log`; PHI stays out of platform audit | Extends 18.1.1 / D9 | schema-hc-03 §M v2 (2 cols on `hc_patient_consents`) |
| V-D10 | **Clinic-mediated** majority transition (Q4): staff `…/detach` endpoint (`patient_link:detach`), relationship→`self`/owner, all prior proxy grants→`revoked` pending re-consent; age threshold = per-tenant JSON setting | New (18.10.5) | none (reuses V-D6 columns + tenant-settings JSON) |

## Amendment v3 (2026-07-06) — Household / proxy scope moves from "within one tenant" to "within one Company" (RULING 2)

**Trigger.** ADR-HC-010 (shared-tenant SaaS) collapses all clinics into one shared platform Tenant, so
`tenant_id` no longer isolates a clinic. Revision v2's Q2 ruling — *"a household is within ONE tenant"*
— was chosen precisely because **tenant == clinic**; under one shared tenant it would let an account
holder's household span **every clinic on the SaaS** and the same-tenant guards would guard nothing.
The user **RATIFIED (RULING 2): the household/proxy "within one tenant" guards become "within one
Company."** This amendment re-scopes V-D6/V-D7 (and the `routes_household.py` guards) from tenant to
**Company**. It **annotates, does not rewrite,** Revision v2; every other v2 decision stands.

### AM3-1 — V-D6 same-tenant (Q2) invariant → same-**Company**

The `hc_patient_relationships` same-tenant constraint (V-D6 constraint #3) is re-scoped to
**same-Company**:

- The relationship row's `tenant_id` remains the shared `SAAS` tenant; the isolating check becomes
  **`relationship.company_id == patient.company_id == account-holder's Company`** (Company = the patient
  registry's Company, ADR-HC-010 D1). Because `hc_patient_relationships` is co-located with `hc_patients`
  and RLS-scoped, and the patient's Company is now `hc_patients.company_id`, the relationship inherits
  the Company fence via its `patient_id` FK. **Schema:** the relationship table does **not** need its
  own `company_id` column — it derives the patient's Company through `patient_id` (and the RLS
  `app.company_id` GUC fences the table the same as `hc_patients`). If a denormalized `company_id` is
  wanted for the staff-approval-queue index, it is optional and app-maintained (flagged, not required).
- The **DB side** of the invariant (relationship↔patient) becomes `patient.company_id` equality
  (shared-DB trigger/CHECK or via the RLS GUC); the **account-holder-Company** side stays **app-enforced**
  at grant/link time (the platform user's Company is read and compared) — same half-DB/half-app posture
  V-D6 already documented, one level down (tenant→Company).

### AM3-2 — V-D7 bridge resolves the same-**Company** set; token gains `company_id`

- The bridge (`from-platform`) resolves the **authorized set within the account holder's Company** (not
  tenant). The set is single-Company by construction, so the token stays simple — **the `tenant_id: null`
  / concrete-active-tenant claim shape is retained verbatim** (Revision v2's payoff holds one level
  down). The minted token **gains a `company_id` claim** = the active patient's Company (ADR-HC-010 D5),
  so patient-portal reads set `app.company_id` and are Company-fenced without a DB round-trip. `acct` and
  `obo` are unchanged.
- `switch` re-mints within the same Company (the household is single-Company), same `sid`.

### AM3-3 — `routes_household.py` guards: same-tenant → same-Company; 422 "cross-tenant" → 422 "cross-company"

The existing same-tenant guards become same-Company (ground truth: `routes_household.py`):

- **`request_link`** (L246–248): `if str(target.tenant_id) != caller_tenant: return generic` becomes a
  **Company** comparison — `target.company_id != caller_company` (the caller's Company comes from the
  patient token's new `company_id` claim, ADR-HC-010 D5). The anti-enumeration generic response is
  unchanged; the *reason* for the silent deny moves from cross-tenant to **cross-Company**.
- **`register_dependent`** (L291, L311): the dependent's `tenant_id` is the shared tenant; its
  **`company_id`** is stamped from the account holder's Company (the new patient inherits the account
  holder's clinic business). A dependent implicitly belongs to the account holder's Company.
- **`_resolve_active_patient`** (`routes_patient_auth.py` L366+): the resolved set is already
  relationship-driven and Company-fenced by the RLS `app.company_id` GUC; no cross-Company set can form.
- **`get_my_clinic` (`/me/clinic`, L99–114):** re-resolves from `tenants.code`/`name` to the patient's
  **Company** (`companies.code`/`name`), per ADR-HC-010 D6. The staff approval queue and the branch-
  scoped staff endpoints (V-D8/V-D10) are unaffected in shape — the approving staff are at the patient's
  Branch, which is within the patient's Company; only the "same boundary" invariant moves tenant→Company.
- The user-facing 422 error code **`cross_tenant` → `cross_company`** (translatable, ADR-HC-004), where a
  cross-boundary link/register is rejected non-silently (i.e. the non-anti-enumeration paths).

### AM3-4 — Token-claims decision (does the token need a `company_id`?)

**Yes — the patient token gains a `company_id` claim** (ADR-HC-010 D5). Revision v2 kept the token slim
(active `patient_id` + `acct`/`obo`, no household set). AM3 adds exactly **one** claim, `company_id`, so
the portal can (a) fence Company-scoped reads via `app.company_id` and (b) compare the caller's Company
in `request_link` without a DB hit. It is additive and backward-compatible: a legacy token without
`company_id` falls back to a DB lookup on the active patient's `company_id` (mirroring the existing
`acct` fallback in `_account_holder_id`). No multi-Company token machinery is introduced (the household
is single-Company by RULING 2).

### Amendment-v3 decision log

| # | Decision | Amends | Schema touch |
|---|---|---|---|
| AM3-1 | Same-tenant (Q2) invariant → **same-Company**; relationship derives Company via `patient_id`/`hc_patients.company_id` (optional denormalized `company_id` for the queue index) | V-D6 constraint #3 | none required (derives via ADR-HC-010 `hc_patients.company_id`); optional denorm column |
| AM3-2 | Bridge resolves the same-**Company** set; token gains a **`company_id`** claim; slim claim shape retained | V-D7 / D6 | none (runtime claim) |
| AM3-3 | `routes_household.py` same-tenant guards → same-Company; `/me/clinic` → Company; 422 `cross_tenant` → `cross_company` | V-D7 / `routes_household.py` | none |
| AM3-4 | Patient token **gains `company_id`** (additive, backward-compatible); no multi-Company token | D10 / V-D7 | none (runtime claim) |

**Cross-references:** ADR-HC-010 (shared-tenant SaaS; `hc_patients.company_id`; `app.company_id` GUC;
token `company_id`), ADR-HC-005 Amendment v2 (shared-tenant default; Company = clinic-business
boundary), schema-hc-04 (patient-scoping DDL).

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| **Separate patient auth service** (dedicated issuer for patients) | Operational overhead in MVP; ADR-HC-003 already chose a single JWT issuer. Re-affirmed: the platform `users` table + reuse of platform auth machinery is simpler and keeps one credential store. Future extraction remains possible (same JWT format). |
| **Store the Google link on `hc_patients`** (a `google_sub` column on the PHI row) | Puts identity/linkage on the PHI/module side, violating the identity=platform / PHI=module separation; couples OAuth to the encrypted PHI store; blocks staff reuse. Rejected in favor of platform `user_identities`. |
| **Auto-link Google by email match regardless of verification** | Classic account-takeover vector (attacker registers/controls an unverified email). Rejected: auto-link requires **both** provider `email_verified` and platform `is_verified`; otherwise explicit proof-of-control (D2). |
| **Mandatory MFA for all patients** | Raises friction on a public consumer portal and is not required by the ratified model; OTP-only legacy users would be locked out. MFA is opt-in for patients. (Whether MFA should be mandatory for **staff** is left open, not decided here.) |
| **Keep OTP-passwordless as a direct patient-token mint** (no platform token) | Produces sessions outside platform lockout/revoke-all/audit — an inconsistent session model. Rejected in favor of route-through-platform (D6), accepting one extra internal hop. |
| **MFA state as columns on `users`** (`mfa_enabled`, `mfa_method`) instead of `user_mfa` | Cannot represent multiple methods per user (future TOTP + OTP); harder to add per-method `secret`/`enrolled_at`. A dedicated `user_mfa` table (UNIQUE per method) is chosen for extensibility. |
| **Separate patient-token revocation store** (own blacklist) | A second revocation authority to operate and reconcile. Binding the patient token to the platform session `jti` (`sid` claim, D8) reuses the platform blacklist/session state — one authority. |
| **v2: Carry the whole household set in the token** (a `patients: [...]` claim) | Bloats the token, forces a re-mint whenever the set changes (grant/revoke), and duplicates authority state already in the relationship table. Rejected in favour of a slim active-`patient_id` token + a `GET /me/household` discovery endpoint (V-D7). |
| **v2: Multiple co-owners per patient** | Muddies who owns the Q1 consent-law posture and complicates majority detach (whose grant survives?). Rejected: exactly one `owner` + zero-or-more `proxy` grants (V-D6). |
| **v2: Self-service OTP claim to link an existing patient** (no staff) | User ruling Q3 is explicit: linking an existing record requires **clinic-staff approval**. A self-service OTP-to-patient-phone claim was considered in epic-18 18.10.3 but overruled — it risks silent attachment to records the requester should not reach. Rejected per Q3 (V-D8). |
| **v2: Automatic majority transition at the age threshold** | User ruling Q4 requires a **clinic-mediated** transition. Auto-detach could revoke a parent's access before the clinic has re-established the now-adult's own login/consent. The threshold only flags candidates; staff execute (V-D10). |
| **v2: Allow cross-tenant households** | User ruling Q2 confines the household to one tenant. Cross-tenant would force a multi-tenant patient set into the token and break the simple `tenant_id: null` claim shape + branch isolation (adr-hc-001). Rejected per Q2. |

## Reference Map

| File | Relevance |
|------|-----------|
| `backend/app/routers/auth.py` | Platform login/reset/change/logout/sessions — extended for D1 (username-or-email), D3 (MFA challenge), D4 (device revoke on password change) |
| `backend/app/models/user.py` | `users` table — gains `username`, `must_set_password` (schema-hc-03) |
| `backend/app/routers/otp.py`, `modules/healthcare/sdk/otp.py` | OTP transport reused by the MFA `otp_phone` method (D3) |
| `backend/app/seeds/seed_rbac_with_groups.py` | `patient` role + `patients` group assigned to OAuth-created and backfilled users (D2, D7) |
| `modules/healthcare/backend/routes_patient_auth.py` | `from-platform` bridge — the single seam (D6); OTP path re-routed through a platform token |
| `modules/healthcare/backend/sdk/patient_tokens.py` | Patient token claims — gains `sid` (D8); retains `roles:["patient"]`, `tenant_id:null` (D10) |
| `modules/healthcare/backend/models.py` | ~~`hc_patients.user_id` → NOT NULL + UNIQUE (D5)~~ **v2: `user_id` nullable + NOT UNIQUE (V-D5); new `hc_patient_relationships` table (V-D6); `hc_patient_consents` + `basis`/`consented_by_user_id` (V-D9)** — schema-hc-03 §M v2 |
| `modules/healthcare/backend/routes_patient_auth.py` | v2: `from-platform` resolves the same-tenant set → active-`patient_id` token (V-D7); new `POST /auth/switch`, `GET /me/household`, `POST /me/household/link`, and branch-scoped staff `/branches/{branch_id}/household/link-requests…/{approve,reject}` + `…/{patient_id}/detach` (V-D8, V-D10) |
| `modules/healthcare/backend/sdk/patient_auth.py`, `sdk/phi_audit.py` | v2: `PatientTokenData` gains `acct`/`obo`; audit writers thread `on_behalf_of` into `hc_audit_log` (V-D9) |
| `plan-mod-healthcare/architecture/adr-hc-003-two-sided-access-architecture.md` | §D1 superseded (auth flow); §D2/§D3 retained + extended |
| `plan-mod-healthcare/architecture/schema-hc-03.md` | DDL for `user_identities`, `user_mfa`, `user_trusted_devices`, `users` columns, and the `hc_patients.user_id` migration |
| `plan-mod-healthcare/epics/epic-18-patient-portal-authentication.md` | Upstream epic; per-story "Architecture note for B1" lines resolved by D1–D10 |
