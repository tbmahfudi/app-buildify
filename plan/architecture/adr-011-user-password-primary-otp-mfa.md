# ADR-011 — User + Password as Primary Auth; OTP as Optional MFA (platform-native)

| Field | Value |
|-------|-------|
| **Status** | **Accepted** (stakeholder, 2026-07-14) |
| **Date** | 2026-07-14 |
| **Deciders** | B1 (Architect, proposer); D3 (Security) — reviewed, see [sec-review-011](sec-review-011-auth-mfa.md); A3 (Product Owner) — resolutions below; **Stakeholder — accepted 2026-07-14** |
| **Supersedes** | Revises the auth-method framing of ADR-HC-009 (§D6 "OTP optional login option"); builds on ADR-009 (OTP as a Platform Service) |
| **Tracking** | GH#672 (originally "password self-registration"), GH#673 (login hardening, already shipped); tasks in [tasks-011](../tasks/tasks-011-auth-mfa.md) |

> **Accepted.** Team review complete (D3 security requirements R1–R11 + A3 product
> resolutions below) and stakeholder-accepted 2026-07-14. C-stage build proceeds per
> [tasks-011](../tasks/tasks-011-auth-mfa.md); D3 re-reviews each build PR against
> sec-review-011.

---

## Context

**Where we are today.** Patient self-registration lives entirely in the healthcare
module (`modules/healthcare/backend/routes_patient_auth.py`) and is gated on **phone
OTP**: `POST /api/v1/patients/register` hard-requires a Redis `otp_verified:{phone}`
key, and the only way to obtain one (`otp/send` + `otp/verify`) is itself gated on
`HC_PATIENT_OTP_ENABLED`. With OTP off by default (GH#666/#671), self-registration is
completely disabled — which is GH#672.

ADR-HC-009 already established that **patient credentials live on the platform `users`
table** (`hashed_password`, `username`, `must_set_password`), linked to PHI via
`hc_patients.user_id`, and that `from-platform` is the single seam every auth method
flows through to obtain a patient token. ADR-009 already made **OTP a platform
service** (`/api/v1/otp/send|verify`). The pieces exist; the *primary* path does not.

**Stakeholder direction (2026-07-14).** Rather than bolt a password path onto the
module's OTP flow, the primary registration/login for **all** users (patients
included) should be **username/email + password**, owned by the **platform** (not the
module). **OTP becomes an optional, user-selectable MFA factor** (phone *or* email),
enrolled *after* an account exists — not a precondition to having one.

---

## Decision (proposed)

### 1. Password is the primary, platform-native credential
Registration and login are platform endpoints keyed on **username/email + password**,
reusing the existing platform machinery (`password_validator.py`, `hash_password`,
`lockout_manager.py`, `session_manager.py`). No module implements its own credential
storage or hashing. Patient accounts are ordinary platform `User` rows with
`role="patient"` and `must_set_password=false` (they chose a password at signup).

### 2. OTP is demoted to an optional MFA factor (phone or email)
OTP is **no longer** a registration gate or a standalone primary login. It becomes a
**second factor** a user can enroll after signup:
- **Phone OTP** — existing ADR-009 SMS/WhatsApp channel.
- **Email OTP** — new channel on the same platform OTP service (extends ADR-009).

MFA enrollment/verification is a platform capability (challenge → verify → enroll),
reusing the trusted-device/challenge contract sketched in ADR-HC-009 §D4/§D6.

### 3. The healthcare module becomes a thin caller
The module stops owning a registration flow. Patient self-registration =
platform account creation (role `patient`) **+** create/link the `hc_patients` PHI row
(`user_id`), then mint a portal token through the existing `from-platform` seam
(ADR-HC-009 §D6). The module's `otp/send|verify|token` routes are retired or repointed
at the platform MFA/OTP service; `HC_PATIENT_OTP_ENABLED` is superseded by per-user MFA
enrollment state.

### 4. Backward compatibility with legacy OTP-only patients
The ADR-HC-009 §D7 backfill (platform `User` per legacy OTP patient, placeholder hash,
`must_set_password=true`, `/patient/claim-account` interstitial) is **retained** — those
users set a password on next login. No patient is stranded.

---

## Platform impact surface (why this needs review)

| Area | Change | Risk |
|------|--------|------|
| `backend/app/routers/auth.py` | New/extended registration; login already accepts username OR email (D1) | Public auth contract |
| Platform `User` model + migration | MFA-enrollment columns/table (factor type, target, verified_at); reuse `must_set_password` | Schema change; MySQL+PG parity (cf. GH#669) |
| Platform OTP service (ADR-009) | Add **email** OTP channel + `purpose="mfa"` | Delivery adapter, rate limits |
| New MFA subsystem | enroll / challenge / verify / disable endpoints + trusted-device | New security-critical surface |
| `modules/healthcare/backend/routes_patient_auth.py` | `register` delegates to platform; OTP routes become MFA-only | Module/platform boundary |
| Frontend | Signup = email+password; post-signup "add MFA" flow; `/patient/claim-account` retained | UX + SPA routing |
| Docs / seeds | Update ADR-HC-009 cross-refs; seed patient users with passwords | — |

---

## Open questions — recommended resolutions (A3 product + D3 security)

These are the team's recommended answers; the stakeholder confirms or overrides at accept.

1. **Scope of "all users."** → **Patients-only for iteration 1**, but build the MFA
   subsystem as a *shared platform capability* so staff adopt it next with no rework.
   Rationale: bounded blast radius; patients are the #672 driver; staff already
   password-login.
2. **Registration endpoint ownership.** → **One platform account-creation service**,
   fronted by a patient-facing `POST /api/v1/patients/register` that calls it. Keeps the
   public patient contract stable while all credential logic lives platform-side.
3. **Self-service vs. invite.** → **Tenant setting, default OFF** (invite/staff-created
   only); captcha always required when self-service is on. Backs D3-**R4**. This is the
   main enumeration/spam control.
4. **Email OTP delivery.** → **Reuse the SMTP worker** (ADR-002-smtp); **separate**
   rate-limit bucket per channel + `purpose="mfa"` (D3-**R6**).
5. **MFA data model.** → New **`user_mfa_factors`** table (`type ∈ {phone_otp,
   email_otp}`, `target`, `verified_at`, `is_active`). **TOTP/authenticator-app deferred**
   — design the table to admit it later.
6. **`HC_PATIENT_OTP_ENABLED` retirement.** → Replace with **per-user MFA enrollment
   state**; keep the env var as a temporary **kill-switch** during migration, remove
   after the D7 backfill completes.

## A3 — proposed epic / story slate (build only after accept)

Epic: *Platform-native password auth + optional OTP MFA (patients-first)*.

1. **S1 — Platform account-creation service** (role=patient), password-policy reuse,
   enumeration-safe (D3 R1–R2). +`must_set_password=false` for self-signup.
2. **S2 — `POST /api/v1/patients/register`** delegates to S1, creates+links
   `hc_patients.user_id`, mints token via `from-platform` seam. Captcha (R3), tenant
   self-service gate (R4).
3. **S3 — `user_mfa_factors` migration** (PG + MySQL parity, cf. GH#669).
4. **S4 — MFA enroll/challenge/verify/disable** endpoints; email-OTP channel on the
   platform OTP service; rate limits (R5–R7); revoke-on-change (R8); audit (R10).
5. **S5 — Frontend:** email+password signup; post-signup "add MFA" flow; retain
   `/patient/claim-account` for legacy D7 users.
6. **S6 — Retire module OTP-as-primary**; repoint to platform MFA; kill-switch cleanup.

**Sequencing:** S1→S2 unblock #672's core (self-registration works). S3→S4→S5 deliver
MFA. S6 last. D3 re-reviews S1/S2 and S4 build PRs against sec-review-011.

---

## Security considerations (for D3 review)

- **Enumeration:** registration and "email/username exists" must return generic
  responses (ADR-HC-009 §D1 already mandates this for login). Timing-safe.
- **Password policy:** reuse `password_validator.py` — no weaker path via the module.
- **MFA enrollment abuse:** verify ownership of the phone/email before enrolling;
  rate-limit challenges; revoke trusted devices on password change (ADR-HC-009 §D4).
- **PHI boundary:** the `hc_patients` row still holds no credential; password stays on
  `users` (ADR-HC-009 invariant).
- **GH#673 (shipped):** `verify_password` already returns False on malformed hashes —
  the new register path must not reintroduce a 500 on bad input.

---

## Consequences

**Positive:** one credential model platform-wide; OTP stops being a signup blocker;
consistent password policy + lockout + sessions; MFA becomes opt-in and auditable;
the healthcare module shrinks to a PHI/linkage concern.

**Negative / cost:** a new security-critical MFA subsystem to build and audit; schema
migration with MySQL/PG parity; frontend signup + MFA-enrollment work; coordinated
retirement of the module's OTP routes and the `HC_PATIENT_OTP_ENABLED` flag.

---

## Review routing

- **B1 (Architect):** owns this ADR — resolve the 6 open questions with reviewers.
- **D3 (Security):** review the enumeration/MFA/rate-limit surface; produce
  `sec-review` before build.
- **A3 (Product Owner):** confirm scope (patients-only vs. all users; self-service vs.
  invite) and cut the epic/stories.
- **Healthcare module owner (C4/C5):** confirm the module-delegates-to-platform seam.

**Gate:** flip Status → `Accepted` only after D3 + A3 sign-off. Then C1 writes tasks.
