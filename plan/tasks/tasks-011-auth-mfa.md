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

> **Flow decision (2026-07-14, stakeholder):** registration is **verify-email, no
> auto-login**. `register` always returns `202 "if this email is new, we've sent an
> activation link"` — identical for new vs. existing email, so nothing leaks (**R1**).
> The patient activates via the emailed link, then logs in normally. No portal token is
> issued at register time.

### S1 — Platform account-creation service  `[C2]`  ✅ DONE (PR pending)
- `app/services/account_service.py`: `create_patient_account(...)` creates a login-capable
  `User` (patient semantics), policy-validated password, `is_active=true`,
  `is_verified=false`, `must_set_password=false`.
- Reuses `app.core.auth.hash_password` + `PasswordValidator` policy (**R2**); duplicate
  email/username raises `AccountExistsError` for the caller to keep generic (**R1**);
  savepoint-isolated insert; no 5xx on bad input (ties GH#673).
- 5 unit tests green (weak-pw reject, dup→AccountExists, normalized/hashed fields).

### S2 — `POST /api/v1/patients/register` (verify-email path)  `[C4 + platform seam]`
- Extend `modules/healthcare/backend/routes_patient_auth.py`: register calls S1, creates +
  links `hc_patients.user_id`, generates an **activation token**, sends the activation
  email (SMTP worker), returns **202** generic (no token). Success and `AccountExistsError`
  return the *same* 202 (**R1**).
- Captcha required (**R3**); tenant self-service gate, **default OFF** (**R4**).
- Add `email`/`username`/`password` to `PatientRegisterRequest`; keep OTP route paths.

### S2b — Account activation + login gate  `[C2 + C4]`
- Activation endpoint consumes the token → sets `users.is_verified=true`.
- Platform login (and the `from-platform` seam) reject an unverified patient user until
  activated. Tokens single-use, TTL'd, rate-limited.
- **DoD (S2+S2b):** with OTP disabled, a new patient self-registers → gets an activation
  email → activates → logs in → holds a portal session. e2e covers: register 202 generic
  for both new+duplicate, weak password 422, self-service-off 403, activate happy-path,
  login-before-activation rejected.

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
