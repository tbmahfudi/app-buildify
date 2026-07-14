# Handoff — ADR-011 (password-primary auth + OTP-as-MFA), continue at S4

**For a new session.** Written 2026-07-14. Everything below is on `main` unless noted.

## What this initiative is
GH#672 was reframed into a platform-wide change: **username/email + password is the
primary credential for all users** (patients first); **OTP is an optional MFA factor**
(phone or email), enrolled after signup — not a registration gate; all platform-owned.
Design of record: **[ADR-011](architecture/adr-011-user-password-primary-otp-mfa.md)**
(Accepted) + **[sec-review-011](architecture/sec-review-011-auth-mfa.md)** (D3, 11 binding
requirements R1–R11) + task slate **[tasks-011](tasks/tasks-011-auth-mfa.md)**.

**Locked flow:** register is **verify-email, no auto-login** — `POST /patients/register`
always returns `202 "if new, check inbox"` (identical for new/duplicate → no enumeration),
activation link, then normal login. No token at register.

## Done & merged
- **S1** (`#683`, `d616bf0`) — `backend/app/services/account_service.py::create_patient_account`.
  Mints a platform `User` (patient), reuses password policy + `hash_password`,
  `AccountExistsError` for enum-safety, SAVEPOINT insert, `is_verified=False`,
  `must_set_password=False`. 5 unit tests (`backend/tests/unit/test_account_service.py`).
- **S2/S2b** (`#686`, `83d2e42`) — `modules/healthcare/backend/routes_patient_auth.py`:
  `POST /patients/register` (captcha → consent → per-tenant self-service gate default-OFF →
  S1 → link `hc_patients.user_id` → Redis activation token 24h + stub email → 202) and
  `POST /patients/activate` (single-use token → `users.is_verified=true`); `from-platform`
  seam 403s unverified patients. D1 e2e: `backend/tests/e2e/test_patient_registration.py`
  (4 pass live vs :9002, 1 skip — see limitation below).
- **S3** (`#685`, `782f793`) — `user_mfa_factors` table + `UserMFAFactor` model
  (`backend/app/models/user_mfa_factor.py`, migration `postgresql/pg_user_mfa_factors.py`).
  Fresh-DB verified.

## NEXT: S4 — MFA enroll/challenge/verify/disable (+ email-OTP channel)
Build on `user_mfa_factors` (S3) and the ADR-009 OTP service. Platform endpoints:
enroll a factor → send OTP to the target → verify → set `is_active=true`/`verified_at`;
disable. Add an **email** OTP channel to the OTP service (SMTP worker, ADR-002-smtp).
**D3 requirements that gate this PR:** R5 (prove target ownership before activating),
R6/R7 (rate + cost caps, separate buckets per channel + `purpose="mfa"`), R8 (revoke
sessions + trusted devices on credential change), R10 (audit enroll/verify/disable).
D3 re-reviews the S4 build PR against sec-review-011. Then S5 (frontend) and S6 (retire
the module's OTP-as-primary; `HC_PATIENT_OTP_ENABLED` → per-user MFA state).

## Gotchas / context a new session needs
- **Repo is in WSL** at `/home/mahfudi/app-buildify` (not `C:\app-buildify`). Use
  `wsl.exe -d Ubuntu -- bash -lc '…'`. `gh` is a shell function — flaky under inline
  `bash -lc`; run gh from a **script file** (`bash /path/script.sh`). Edit WSL files via
  the UNC path `\\wsl.localhost\Ubuntu\home\mahfudi\app-buildify\…`.
- **Healthcare service** runs as its own image on **:9002**, live-mounts
  `modules/healthcare/backend` → `/app/modules/healthcare`, **no `--reload`** → after
  editing module code run `docker restart app_buildify_healthcare`. Its platform `app`
  is baked (built FROM the backend image), so a NEW platform file (e.g. an S4 service)
  isn't visible there until image rebuild — for a quick dev test,
  `docker cp <file> app_buildify_healthcare:/app/app/…` then restart.
- **Happy-path e2e limitation:** `register` 202 needs a resolved Company context
  (`app.company_id` GUC); public self-registration scope resolution is Phase 5 / epic-20.
  The register-202→activate→login e2e is skipped until that's wired.
- **MySQL migration parity is deferred to GH#669** — the MySQL alembic tree has **9
  unmerged heads**; add the `user_mfa_factors` MySQL twin as part of that consolidation.
- **Two pre-existing bugs found & filed as background tasks** (not blocking):
  `clear_all_data` FK-ordering in `seed_complete_org.py`; and the **PasswordValidator API
  drift** in `auth.py` (change-password/reset construct `PasswordValidator(db, tenant_id)`
  and call `.validate_password(...)`, but the class is `PasswordValidator(policy)` with
  `.validate_strength/full` — likely broken). S4 should use the coherent API + the
  `account_service._load_password_policy` pattern.
- **Stacked-PR lesson:** don't stack a PR on another PR's branch here — squash-merging the
  base then deleting it closed the stacked PR (#684). Branch build PRs off `main` and
  cherry-pick, or merge the base and rebase before it's deleted.

## Related
[ADR-HC-009](../plan-mod-healthcare/architecture/adr-hc-009-patient-identity-and-auth.md)
(patient identity; §D6 from-platform seam, §D7 legacy backfill), ADR-009 (OTP as platform
service), ADR-002-smtp (email worker).
