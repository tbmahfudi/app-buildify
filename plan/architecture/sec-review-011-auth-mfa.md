# sec-review-011 — Security Review of ADR-011 (password-primary auth + OTP-as-MFA)

| Field | Value |
|-------|-------|
| **Reviewer** | D3 (Security Engineer) |
| **Target** | [ADR-011](adr-011-user-password-primary-otp-mfa.md) (Status: Proposed) |
| **Date** | 2026-07-14 |
| **Verdict** | **Approve-with-requirements** — the direction is sound; the requirements below are binding on the implementation, and D3 re-reviews the build PR before merge. |

---

## Threat surface introduced

Public, unauthenticated **account creation** + a new **MFA enrollment/challenge**
subsystem on the platform. Primary abuse vectors: account enumeration, credential
stuffing, MFA-enrollment abuse (binding an attacker factor / spamming a victim's
phone/email), and OTP brute force / cost-amplification (SMS/email fan-out).

## Binding requirements (R#)

**Registration**
- **R1 — No enumeration.** Register and any "email/username available?" path MUST
  return a generic outcome; do not leak existence via status code, body, or timing.
  Prefer "if this address is new, an account/verification was created" semantics over a
  distinct `409`. Constant-time-ish handling.
- **R2 — Password policy reuse.** Hash via `app.core.auth.hash_password`; validate via
  `password_validator.py`. No module code path may create a `User` with a weaker/no
  policy check. (Regression guard ties to GH#673 — never 500 on bad input.)
- **R3 — Captcha mandatory** on public registration and on MFA challenge send
  (reuse the module's existing `require_captcha`, promoted to platform).
- **R4 — Self-service is opt-in per tenant.** Open self-registration MUST be a tenant
  setting, default **OFF**; when off, accounts are invite/staff-created only. (Backs A3-Q3.)

**MFA enrollment / OTP**
- **R5 — Prove ownership before activating a factor.** A phone/email factor is only
  `is_active` after a send→verify round-trip to that target. Enrolling never trusts a
  client-asserted "verified" flag.
- **R6 — Rate limits & cost caps.** Reuse ADR-009 buckets with a distinct
  `purpose="mfa"`; separate buckets per channel (phone vs email) and per
  target+IP+account; hard daily cap to bound SMS/email spend. Resend cooldown enforced.
- **R7 — Generic OTP failures**, attempt counters with lockout, codes never logged
  (already honored in the module today — preserve when moving to platform).

**Session / recovery / audit**
- **R8 — Revoke on credential change.** Password change/reset revokes all sessions and
  all trusted devices (extends the existing `revoke_all_user_sessions`; ADR-HC-009 §D4).
- **R9 — Lockout reuse.** Failed password logins go through `lockout_manager.py`; MFA
  verify has its own attempt cap.
- **R10 — Audit** every: registration, MFA enroll/verify/disable, `must_set_password`
  clear, trusted-device add/revoke. Actor + IP + UA.
- **R11 — PHI boundary intact.** No credential/MFA secret on `hc_patients`; all on
  `users` / `user_mfa_factors`. (ADR-HC-009 invariant.)

## Residual risks accepted (for now)
- **TOTP/authenticator app** deferred (A3-Q5) → phone/email OTP only this round; both
  are deliverable-channel-dependent. Acceptable; revisit for high-assurance tenants.
- **Email OTP** is weaker than phone for account-takeover if the mailbox is
  compromised — acceptable as an *optional* second factor, not sole protection.

## Re-review gate
D3 signs off the **implementation PR** against R1–R11 (not this ADR alone). Migration
parity (PG+MySQL, cf. GH#669) and the enumeration/timing behavior get explicit test
coverage from D1.
