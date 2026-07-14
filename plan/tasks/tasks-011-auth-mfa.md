---
id: tasks-011-auth-mfa
status: approved
upstream: adr-011-user-password-primary-otp-mfa, sec-review-011-auth-mfa
owner: C1 (Tech Lead)
date: 2026-07-14
---

# tasks-011 — Platform password auth + optional OTP MFA (patients-first)

Derived from [ADR-011](../architecture/adr-011-user-password-primary-otp-mfa.md)
(Accepted) and [sec-review-011](../architecture/sec-review-011-auth-mfa.md). Each build
PR is re-reviewed by D3 against R1–R11.

## Sprint 1 — restore self-registration (unblocks GH#672)

### S1 — Platform account-creation service  `[C2]`
- Add a platform service (e.g. `app/services/account_service.py` or extend the auth
  service) that creates a `User(role="patient")` with policy-validated password.
- Reuse `app.core.auth.hash_password` + `password_validator.py` (**R2**).
- Enumeration-safe: no distinct existence signal, uniform timing (**R1**).
- `must_set_password=false` for self-signup; audit the creation (**R10**).
- Unit + integration tests incl. weak-password reject, duplicate handled generically.
- **DoD:** service creates a login-capable patient user; tests green; no 5xx on bad input (ties GH#673).

### S2 — `POST /api/v1/patients/register` (password path)  `[C4 + platform seam]`
- Extend `modules/healthcare/backend/routes_patient_auth.py`: new/updated register that
  calls S1, then creates + links `hc_patients.user_id`, then mints a portal token via
  the existing `from-platform` seam (ADR-HC-009 §D6).
- Captcha required (**R3**); tenant self-service gate, **default OFF** (**R4**).
- Add `email`/`username`/`password` to `PatientRegisterRequest`; keep OTP route paths.
- **DoD:** with OTP disabled, a new patient can self-register + immediately hold a portal
  session; e2e covers success, weak password, self-service-off (403), duplicate (generic).

## Sprint 2 — MFA

### S3 — `user_mfa_factors` migration  `[B2]`
- Table: `type ∈ {phone_otp,email_otp}`, `target`, `verified_at`, `is_active`, FK user.
- **PG + MySQL parity** (cf. GH#669). Column shaped to admit TOTP later.

### S4 — MFA enroll / challenge / verify / disable  `[C2]`
- Platform endpoints; add **email** OTP channel to the ADR-009 OTP service (SMTP worker,
  ADR-002-smtp). Prove ownership before activation (**R5**); rate/cost caps, separate
  buckets per channel + `purpose="mfa"` (**R6–R7**); revoke sessions+devices on
  credential change (**R8**); audit (**R10**).

### S5 — Frontend  `[C3]`
- Email+password signup; post-signup "add MFA" flow; retain `/patient/claim-account`
  for legacy D7 users.

## Sprint 3 — cleanup

### S6 — Retire module OTP-as-primary  `[C4]`
- Repoint module OTP to the platform MFA service; remove `HC_PATIENT_OTP_ENABLED` after
  the D7 backfill; kill-switch cleanup.

## Gate
D3 re-reviews S1/S2 and S4 build PRs against sec-review-011. D1 owns enumeration/timing +
migration-parity test coverage.
