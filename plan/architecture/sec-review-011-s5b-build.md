---
id: sec-review-011-s5b-build
status: approve
upstream: adr-011-user-password-primary-otp-mfa, sec-review-011-auth-mfa, adr-hc-009-patient-identity-and-auth
reviewer: D3 (Security)
date: 2026-07-15
---

# sec-review-011 — S5b build re-review (MFA login challenge + trusted devices)

Re-review of the S5b build against the binding requirements R1–R11 and ADR-HC-009
§D3/§D4. Gate: `tasks-011` — "D3 re-reviews each build PR against sec-review-011".

**Verdict: Approve.**

## What changed the risk picture

S4 was approved on the understanding that it delivered "enroll / challenge / verify /
disable". It did not deliver *challenge*: `auth.py` contained no MFA code path, so an
enrolled factor had no effect on login. The S5 profile card then displayed that factor as
**Active**. The system was telling users they had a second factor while accepting a
password alone — a misstatement of security posture, and the most serious issue in this
initiative to date. S5b closes it. That alone justifies the approval.

## Findings against the binding requirements

| Req | Status | Notes |
|-----|--------|-------|
| **R5** — ownership before activation | ✅ unchanged | Challenge only ever targets a factor that is already `is_active`, i.e. already round-trip proven. |
| **R6** — rate/cost caps | ✅ | Challenge sends reuse `purpose="mfa"` and the per-target/account/IP daily caps. The cooldown change (below) does **not** weaken a cap. |
| **R7** — generic failures, lockout, no code logging | ✅ | Verify delegates to `otp.verify_otp`; failures stay generic; the code is never logged. |
| **R8** — revoke on credential change | ✅ **now actually satisfied** | Was a no-op seam returning 0. Now revokes; proven live (1 live trust → password change → 0 live, 1 `revoked_at`, cookie no longer suppresses the challenge). |
| **R9** — lockout reuse + MFA attempt cap | ✅ | Password leg unchanged (`lockout_manager`). MFA verify inherits the OTP attempt counter + lockout. |
| **R10** — audit | ✅ | New actions: `mfa_challenge`, `mfa_login_verify` (success **and** failure), `trusted_device_add`, `trusted_device_revoke`. Actor + IP + UA via `create_audit_log(request=...)`. |
| **R11** — PHI boundary | ✅ | `user_trusted_devices` is keyed on `users.id`; no PHI, no credential material. |

R1–R4 are registration-path requirements and are untouched by this build.

## Design decisions worth recording

**The challenge token is not an access token.** `type: "mfa_challenge"`, so every normal
auth path rejects it. This is what keeps a half-authenticated caller out of protected
routes — including the healthcare `from-platform` bridge, which is the specific concern
D3 raised in §D3. Covered by a test that feeds a real access token to `/auth/mfa/verify`
and expects 401.

**Single-use is enforced on success, not on attempt.** Burning the challenge on a wrong
code would mean one guess per dispatched code: a single typo would cost the user another
SMS (real money, R6) and a fresh login. Guess-limiting already exists and is the right
control for it (R7/R9 attempt lockout). The replay that "single-use" exists to stop is
redeeming one challenge for two sessions, and that is what `burn_challenge` prevents —
atomically, so concurrent verifies cannot both win.

**Trusted devices store only an HMAC.** The raw secret exists solely in an HttpOnly
cookie. A dump of `user_trusted_devices` is therefore not replayable, and because the HMAC
is keyed with `SECRET_KEY` it is not brute-forceable offline from the table alone. This is
deliberately the same posture we take with passwords. Note the asymmetry with the access
token, which lives in `localStorage` and *is* script-readable — the trusted-device secret
is strictly better protected than the session it can create, which is the correct
direction for a control that skips a factor.

**Cooldown no longer blocks a login.** Found by driving the flow: enroll → login returned
**429**, because the challenge's dispatch hit the enrollment code's 60s resend cooldown and
that surfaced as the login response. A legitimate user was locked out of signing in for the
cooldown window. Now a cooldown (`OTPCooldownError`) means "a usable code is already in
flight" and the challenge proceeds with it; a **daily cap** is a real refusal and still
propagates. `verify_otp` also clears the cooldown when it consumes a code, which keeps the
invariant honest (a live cooldown implies a live, unconsumed code) — without it the
enrollment code is consumed while its cooldown ticks on, and the challenge would hand back
a token the user could not answer. `has_live_code()` guards the reuse path rather than
trusting the invariant silently. No cap is relaxed by any of this.

## Residual risks

- **Cookie `Secure` is off in development** (`ENVIRONMENT == "development"`), because the
  dev stack is plain http and a Secure cookie would never return. On staging/production the
  flag is set. Worth a deploy-time assertion that `ENVIRONMENT` is not left at
  `development`.
- **No captcha on the login-triggered challenge send** (R3 names "MFA challenge send").
  Accepted: the send is reachable only *after* a correct password, so it is not an
  anonymous amplification vector, and the R6 per-target/account/IP caps bound the spend.
  Revisit if the challenge is ever dispatched pre-authentication.
- **A challenge always targets `factors[0]`** (oldest active). A user with several factors
  cannot choose. `methods` is returned so the UI can offer selection later; not a security
  gap.
- **MySQL parity still deferred** (GH#669), consistent with `pg_user_mfa_factors`.

## Cross-cutting note for the initiative

**S6's flag removal must not proceed as written.** Removing `HC_PATIENT_OTP_ENABLED` is gated
on the D7 backfill, which has not run: 0 users carry `must_set_password`, and
`/patient/claim-account` does not exist. The flag is the documented kill-switch *during*
migration; deleting it before the migration exists removes the migration path. See
`tasks-011` S6b.

> **Correction (2026-07-16).** This section originally added "4 of 7 `hc_patients` have a
> phone and a NULL `user_id`" as impact evidence. That figure is wrong and overstated the
> urgency: one of the four is a **dependent child** whose NULL `user_id` is correct by
> design (**V-D5** — a managed dependent has no login; authority flows through
> `hc_patient_relationships`), and the other three are **demo seed fixtures**
> (`seed_demo.py`) created deliberately as phone+OTP-only. **No real user is affected.**
> D7 is an S6b unblocker, not a live-impact fix. The security argument for not deleting the
> flag early is unchanged — it rests on the migration path, not on user impact.
