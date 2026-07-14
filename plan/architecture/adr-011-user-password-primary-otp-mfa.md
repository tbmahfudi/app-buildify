# ADR-011 — User + Password as Primary Auth; OTP as Optional MFA (platform-native)

| Field | Value |
|-------|-------|
| **Status** | Proposed (awaiting team review) |
| **Date** | 2026-07-14 |
| **Deciders** | _pending_ — proposed by B1 (Software Architect); needs D3 (Security), A3 (Product Owner), and healthcare module owner sign-off |
| **Supersedes** | Revises the auth-method framing of ADR-HC-009 (§D6 "OTP optional login option"); builds on ADR-009 (OTP as a Platform Service) |
| **Tracking** | GH#672 (originally "password self-registration"), GH#673 (login hardening, already shipped) |

> **This ADR is a design proposal, not an accepted decision.** It exists to be
> reviewed *before* any implementation, because the change touches platform-wide
> authentication. Do not begin C-stage build until Status is `Accepted`.

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

## Open questions for review

1. **Scope of "all users."** Does password-primary + OTP-MFA apply to *staff/platform*
   users too, or only patients in this iteration? (Staff already password-login; the
   MFA-enrollment piece is the new shared part.)
2. **Registration endpoint ownership.** One platform `POST /api/v1/auth/register` that
   both staff-invite and patient-self-signup reuse, vs. a patient-specific
   `POST /api/v1/patients/register` that internally calls platform account creation?
3. **Self-service vs. invite.** Is *open* self-registration (anyone can create a
   patient account) acceptable tenant-wide, or must it be tenant-gated / captcha-only /
   invite-only per deployment? (Enumeration + spam surface.)
4. **Email OTP delivery.** Reuse the SMTP worker (ADR-002-smtp) for email OTP, or a
   separate transactional channel? Rate-limit shared with phone OTP or separate?
5. **MFA data model.** Single `user_mfa_factors` table (type ∈ {phone,email,totp?}) vs.
   columns on `users`. Is TOTP/authenticator-app in scope now or later?
6. **`HC_PATIENT_OTP_ENABLED` retirement.** Confirm we replace the env flag with
   per-user MFA state, and the migration path for deployments currently relying on it.

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
