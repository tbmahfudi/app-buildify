# sec-review-011 (S4 build) — D3 re-review of PR #687

| Field | Value |
|-------|-------|
| **Reviewer** | D3 (Security Engineer) |
| **Target** | PR #687 — ADR-011 S4 (MFA enroll/verify/disable + email OTP channel), branch `feat/011-s4-mfa-endpoints` |
| **Baseline** | [sec-review-011](sec-review-011-auth-mfa.md) R1–R11 |
| **Date** | 2026-07-15 |
| **Verdict** | **Approve.** One binding gap (R6 per-account/IP caps) and one minor gap (R10 resend audit) were found during review and **remediated in the same PR**; re-verified. Trusted-device revocation (R8) is an accepted, tracked no-op seam until S5. |

---

## Scope reviewed
`app/routers/mfa.py`, `app/services/mfa_service.py`, `app/routers/otp.py`,
`app/routers/auth.py`, `app/core/session_manager.py`, and tests. Registration
requirements R1–R4 are S1/S2 scope (already merged) and out of scope here.

## Findings & disposition

### 🔴 F1 — R6 buckets were per-target only (BINDING) → **FIXED**
`send_otp` originally keyed the daily cap on the delivery target alone. Because MFA
enrollment is authenticated but accepts an **arbitrary** target, one account could fan
one OTP email/SMS out to many distinct addresses (bounded only per-target-per-day) —
the "spamming a victim / cost-amplification" threat named in the baseline. sec-review
R6 requires buckets "per target+IP+account."
**Remediation:** added separate daily caps per **account** (`OTP_ACCOUNT_DAILY_CAP`,
default 20) and per **source IP** (`OTP_IP_DAILY_CAP`, default 30) alongside the
per-target cap; the MFA router passes `account_id` + client IP. **Live-verified:** 22
enrollments to distinct targets from one account → exactly 20×200 then 2×429. Unit
tests: `test_account_cap_blocks_fanout_to_many_targets`, `test_ip_cap_blocks_after_limit`,
`test_account_and_ip_counters_bumped_on_send`.

### 🟡 F2 — R10 resend not audited → **FIXED**
`POST /factors/{id}/resend` triggers a send (a cost/security event) but wasn't audited.
Added an `mfa_resend` audit entry (actor+IP+UA). Enroll/verify/disable were already
audited.

### 🟠 F3 — R8 trusted-device revocation is a no-op (ACCEPTED, TRACKED)
No trusted-device storage exists anywhere in the platform yet ("remember this device"
is S5). Both credential-change paths already call
`session_manager.revoke_all_trusted_devices()`, which returns 0 until that storage lands.
**Accepted** because R8's *session* revocation is fully implemented and verified (change
revokes other sessions, current survives; reset revokes all). **Condition:** wiring the
seam is a **binding acceptance criterion for S5** — must not ship the device surface
without it.

## Requirements met (confirmed)
- **R5** — factor `is_active` flips only after a verified send→verify round-trip; never
  trusts a client flag. Live-verified (enroll inactive → verify → active).
- **R6** — distinct `purpose="mfa"`, per-channel + per-target + per-account + per-IP
  buckets, resend cooldown, hard daily caps. *(after F1)*
- **R7** — generic OTP failures, per-code attempt lockout (`MAX_ATTEMPTS=5`), codes never
  logged (log lines carry only purpose/channel/tenant).
- **R8** — sessions revoked on password change/reset (verified); device seam per F3.
- **R9** — password-login lockout path unchanged; MFA verify has its own attempt cap.
- **R10** — enroll/verify/disable/resend audited with actor+IP+UA. *(resend after F2)*
- **R11** — no credential/MFA secret on `hc_patients`; only target + state on
  `user_mfa_factors`.
- **R2 (bonus)** — S4 restored password-policy validation on change/reset, which was
  `500`-ing before due to `PasswordValidator`/`NotificationService` API drift (ties to
  the GH#673 "never 500 on bad input" guard).

## Residual risks (unchanged from baseline, still accepted)
- TOTP deferred (`factor_type` left open); email OTP weaker than phone (optional 2nd
  factor only).
- Email OTP is dispatched via direct `smtplib` in a daemon thread (low-latency), so it
  bypasses the NotificationQueue worker's retry/config — acceptable for OTP; not a
  security defect.

## Follow-ups for D1 / #669
- MySQL `user_mfa_factors` parity → GH#669.
- Enumeration/timing coverage remains D1's (registration surface, not S4).
