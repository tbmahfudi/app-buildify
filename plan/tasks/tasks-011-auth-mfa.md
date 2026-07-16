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

### S4 — MFA enroll / challenge / verify / disable  `[C2]`  ✅ DONE
- Platform endpoints; add **email** OTP channel to the ADR-009 OTP service (SMTP worker,
  ADR-002-smtp). Prove ownership before activation (**R5**); rate/cost caps, separate
  buckets per channel + `purpose="mfa"` (**R6–R7**); revoke sessions+devices on
  credential change (**R8**); audit (**R10**).
- **Shipped** (`feat/011-s4-mfa-endpoints`): `app/routers/mfa.py` +
  `app/services/mfa_service.py` (`GET/POST /mfa/factors`, `.../verify`, `.../resend`,
  `DELETE`); factor `is_active` only after a verified OTP round-trip (**R5**). OTP service
  (`app/routers/otp.py`) made channel-aware: **email** channel via SMTP (ADR-002-smtp,
  MailHog in dev), `purpose="mfa"`, per-(channel,target) daily cap + separate buckets
  (**R6**), attempt lockout preserved (**R7**), codes never logged. Audit on
  enroll/verify/disable (**R10**). **R8**: `change-password` / `reset-password-confirm`
  now revoke all *other* sessions + a trusted-device seam (`revoke_all_trusted_devices`,
  no-op until S5's "remember device" storage lands — flagged for D3). Also fixed
  pre-existing drift that 500'd the whole password/reset flow: `PasswordValidator(db,…)`
  → `PasswordValidator(load_password_policy(…))`, and `NotificationService(db)` (async-only)
  → direct sync `NotificationQueue` insert (`_queue_email`). Tests: `tests/unit/
  test_mfa_service.py`, `tests/unit/test_otp_channels.py`, `tests/e2e/test_mfa.py`
  (happy path verified live). **D3 re-review pending** against sec-review-011.

### S5 — Frontend  `[C3]`  🟡 PARTIAL
- Email+password signup; post-signup "add MFA" flow; retain `/patient/claim-account`
  for legacy D7 users.
- **Shipped — "add MFA" flow:** Two-Factor Authentication card on the profile page
  (`frontend/assets/templates/profile.html` + `frontend/assets/js/profile-page.js`):
  list factors, enroll phone/email → send OTP → verify & activate → remove, against the
  S4 `/api/v1/mfa/*` endpoints. Target-escaped, busy-guards, reuses `apiFetch`/`showAlert`.
- **Deferred:** public email+password *signup* UX is blocked on the register-202 happy
  path (needs resolved `app.company_id` Company context — Phase 5 / epic-20).
- **Correction (2026-07-15):** an earlier revision of this line claimed "Legacy D7
  `/patient/claim-account` already exists". **It does not.** There is no such route in
  the codebase (`POST /api/v1/patients/claim-account` → 404, no matching source), and no
  D7 backfill has run. See S6 below.

### S5b — MFA challenge at login + trusted devices  `[C2 + C3]`  ✅ DONE
Not in the original slate — opened because S4 shipped MFA **enrolled but unenforced**.
`auth.py` had no MFA code path at all: a user could activate a factor, see it as *Active*
in the S5 card, and still sign in with a password alone. The S4 story title said
"enroll / **challenge** / verify / disable"; the challenge half was never built.

- **D3 challenge** (`app/services/mfa_challenge_service.py`, `auth.py`): `POST /auth/login`
  returns **202** `{mfa_required, mfa_token, methods, sent_to}` for a user with an active
  factor and dispatches an OTP; new `POST /auth/mfa/verify` trades `{mfa_token, code,
  remember_device?}` for real tokens. Challenge JWT is `type="mfa_challenge"` (never
  accepted as an access token), 5-min TTL, single-use — burned on **success** only, since
  guess-limiting is the OTP attempt lockout's job (R7/R9) and burning on a typo would cost
  a second SMS (R6).
- **D4 trusted devices** (`user_trusted_devices` + `app/services/trusted_device_service.py`):
  `remember_device` mints a high-entropy secret, stores only its **HMAC**, and returns the
  raw secret in an HttpOnly/SameSite=Lax cookie; a match suppresses the challenge for 30
  days. `GET/DELETE /api/v1/mfa/devices` for the security screen.
- **R8 closed for real.** `revoke_all_trusted_devices` shipped in S4 as a documented no-op
  seam; it now revokes. Verified live: password change → 0 live trusts, cookie no longer
  skips MFA. Also revoked on MFA disable (D4).
- **Frontend:** login code step + remember-device + resend/cancel; remembered-devices list
  on the profile card. `api.js login()` now returns `{mfaRequired}` — `res.ok` is **true**
  for a 202, so the old code stored `undefined` tokens and "succeeded" silently.
- **Also fixed:** `POST /org/users` + `/org/users/{id}/reset-password` always 500'd
  (`get_password_hash` → `hash_password`); OTP resend cooldown blocked MFA logins.
- Tests: 33 unit + 15 backend e2e + 5 Playwright. Full e2e 732 passed / 0 errors.

## Sprint 3 — cleanup

### S6 — Retire module OTP-as-primary  `[C4]`  🟡 PARTIAL — repoint done, flag removal still blocked

S6 has two independent halves. The **repoint** is done; the **flag removal** stays blocked
on D7.

#### S6a — Repoint module OTP → platform OTP service  ✅ DONE
- `routes_patient_auth.py` (`otp_send`, `otp_verify`, `patient_token`) now call the platform
  `app.routers.otp` `send_otp`/`verify_otp` with `purpose="patient_login"`,
  `channel="phone"`. The module's parallel implementation
  (`modules/healthcare/backend/sdk/otp.py`, imported as `modules.healthcare.sdk.otp`) is
  **deleted**. Public HTTP contract unchanged.
- **This closed a real R6 hole.** The module implementation had **no daily cap of any kind**
  — only a 60s resend cooldown — so with `HC_PATIENT_OTP_ENABLED=true` an attacker could
  pump unbounded SMS at any phone. The platform service applies the per-target/account/IP
  daily caps. It also adds purpose separation and tenant namespacing (the module keyed on a
  bare `otp:{phone}`, global across tenants).

#### S6b — Remove `HC_PATIENT_OTP_ENABLED`  ⛔ BLOCKED — precondition unmet
- **Blocked (verified 2026-07-15).** A3-Q6 gates removal on the D7 backfill completing.
  It has not:
  - `SELECT count(*) FROM users WHERE must_set_password` → **0** — the backfill has never run.
  - `/patient/claim-account`, the interstitial D7 relies on to let a legacy patient set a
    password, **does not exist** (404, no source).
- **Correction (2026-07-16) — an earlier revision of this section overstated the impact.**
  It claimed "**4 of 7** `hc_patients` have a phone and a NULL `user_id` … legacy OTP-only
  patients with no platform account", implying four real stranded patients. Checked against
  the DB, that is wrong twice over:
  - It is **3**, not 4. The fourth (`503ef94f`) is a **dependent child** with an `active`
    `owner` relationship held by its parent. Under **V-D5** a managed dependent
    *legitimately has no login of its own* — `hc_patients.user_id` is nullable **precisely**
    for this case. It is not a backfill target; schema-hc-03 §M.1 scopes the backfill to
    "every **self-owned** legacy patient lacking a login". Backfilling it would hand a minor
    their own account, which **V-D10** says may only happen via the staff-mediated majority
    transition.
  - The remaining **3 are demo seed data** (`modules/healthcare/backend/seed_demo.py`,
    MedCare), created deliberately as phone+OTP-only fixtures to exercise the OTP flow.
    They are not real patients, and they are "stranded" only because the demo's own login
    path is off by default.
  - **So D7 is an S6b unblocker and genuinely-missing code — not a live patient-impact fix.**
    There are currently **zero** real users affected.
- The flag is still the documented "temporary kill-switch **during** migration", and it is
  still the only route by which a legacy patient could authenticate, so removing it before
  the migration exists still destroys the migration path. The reason to build D7 is to
  finish the migration, not to rescue anyone today.
- **Unblocks S6b:** (1) build the D7 backfill (platform `User` per **self-owned** legacy
  patient, placeholder hash, `must_set_password=true`, link `user_id`, **plus** a
  `relationship='self'`/`role='owner'` row per schema-hc-03 §M.1), (2) build
  `/patient/claim-account`, (3) run the backfill, then (4) delete the routes + flag.
  Steps 1–3 are ADR-HC-009 D7 work, not ADR-011. Note **V-D5 withdrew** the old D7 step 4
  (`user_id` → NOT NULL + UNIQUE) — there is nothing to constrain.
- **Also out of scope for the repoint, and D7-blocked:** D6's "route OTP-passwordless through
  a platform token" — `patient_token` still mints a patient token **directly**, so those
  sessions escape platform lockout/revoke-all. It cannot be fixed until legacy patients
  *have* a platform user, i.e. until the backfill runs.

## Gate
D3 re-reviews S1/S2 and S4 build PRs against sec-review-011. D1 owns enumeration/timing +
migration-parity test coverage.
