# Security Review — Healthcare Module

## Findings

### SEC-001: OTP plaintext logged with phone number
- **Severity**: HIGH
- **Category**: PHI
- **File**: `routes_patient_auth.py` (line 239)
- **Finding**: The OTP code and the patient's raw phone number are written to the application log at INFO level: `logging.getLogger(__name__).info("OTP for %s: %s", payload.phone, code)`. In any environment where INFO logs are shipped to a log aggregator (Datadog, CloudWatch, ELK), both a patient identifier (phone) and a live authentication secret (OTP) are persisted in plaintext.
- **Recommendation**: Remove this log line entirely. If an audit trail is required, log only a HMAC of the phone and record that the OTP was *issued* (not the value itself) at DEBUG level, disabled in production.

---

### SEC-002: HMAC secret for phone hash has insecure default value (no fail-fast)
- **Severity**: HIGH
- **Category**: Crypto
- **File**: `sdk/notification_service.py` (line 16)
- **Finding**: `_HMAC_SECRET = os.environ.get("PHONE_HASH_SECRET", "changeme-set-PHONE_HASH_SECRET-env")`. If `PHONE_HASH_SECRET` is not set, the module silently continues with the literal string `"changeme-set-PHONE_HASH_SECRET-env"` as the HMAC key. Phone hashes stored in `hcs_notification_log` are then effectively reversible because the key is known. Unlike `PHI_ENCRYPTION_KEY`, this does NOT fail-fast at import time.
- **Recommendation**: Replicate the `_load_key()` fail-fast pattern from `phi_crypto.py`: raise `RuntimeError` at module load if `PHONE_HASH_SECRET` is absent or equals the default string.

---

### SEC-003: BPJS export HMAC key has insecure default value (no fail-fast)
- **Severity**: HIGH
- **Category**: Crypto
- **File**: `routes_billing.py` (line 929)
- **Finding**: `secret = os.environ.get("BPJS_EXPORT_HMAC_KEY", "demo-key-replace-in-prod").encode()`. If the env var is unset, patient name hashes in BPJS exports use the known literal `"demo-key-replace-in-prod"`, making them trivially reversible.
- **Recommendation**: Raise `RuntimeError` (or cause startup health-check failure) if `BPJS_EXPORT_HMAC_KEY` is absent or equals the default value.

---

### SEC-004: Four billing tables have no RLS policy applied
- **Severity**: HIGH
- **Category**: AuthZ
- **File**: `migrations/hcb_002_rls_policies.py` (lines 22–30)
- **Finding**: `hcb_002_rls_policies.py` applies `apply_branch_rls` only to `hcb_invoices` and `apply_tenant_rls` only to `hcb_insurance_profiles`. Four additional billing tables — `hcb_service_items`, `hcb_invoice_lines`, `hcb_payments`, and `hcb_bpjs_exports` — appear only in GRANT statements with no `ENABLE ROW LEVEL SECURITY` or policy created. A misconfigured or buggy `healthcare_branch_session` would leave these tables unguarded at the database layer.
- **Recommendation**: Add `apply_branch_rls(op, ...)` (or `apply_tenant_rls`) calls for each of the four unprotected tables in a follow-up migration before production data load.

---

### SEC-005: SQL injection risk — tenant_id and branch_id interpolated directly into SET LOCAL
- **Severity**: MEDIUM
- **Category**: Injection
- **File**: `sdk/branch_scope.py` (lines 164–165)
- **Finding**: Both values are string-interpolated directly into raw SQL:
  ```python
  db.execute(text(f"SET LOCAL app.tenant_id = '{tenant_id}'"))
  db.execute(text(f"SET LOCAL app.branch_id = '{effective_branch_id}'"))
  ```
  PostgreSQL `SET LOCAL` does not support named parameters, so some interpolation is unavoidable. However, `tenant_id` is currently cast from `current_user.tenant_id` (a UUID) and `effective_branch_id` is either a validated UUID or the literal `"ALL"`. If upstream parsing ever returns a non-UUID value (e.g. due to a JWT manipulation or code change), a single-quote would break the string literal boundary.
- **Recommendation**: Explicitly cast `tenant_id` to `uuid.UUID` and assert `effective_branch_id` is either a valid UUID string or exactly `"ALL"` before interpolating.

---

### SEC-006: Three scheduling tables have no RLS policy applied
- **Severity**: MEDIUM
- **Category**: AuthZ
- **File**: `migrations/hcs_002_rls_policies.py`
- **Finding**: `hcs_002_rls_policies.py` applies `apply_branch_rls` only to `hcs_appointments` and `hcs_waitlist`. Three other scheduling tables — `hcs_appointment_slots`, `hcs_provider_schedules`, and `hcs_notification_log` — have grants but no RLS policies or `ENABLE ROW LEVEL SECURITY`.
- **Recommendation**: Apply the appropriate RLS policy to each unprotected scheduling table in a follow-up migration.

---

### SEC-007: Public endpoint exposes branch `contact_phone` without authentication
- **Severity**: MEDIUM
- **Category**: PHI
- **File**: `routes_public.py` (lines 287, 352)
- **Finding**: Both `GET /api/v1/clinics/{slug}` and `GET /api/v1/clinics/{slug}/branches/{branch_id}` select and return `b.contact_phone` from `hc_branches` with no authentication. While this is typically a clinic front-desk number, there is no enforcement that the column only stores business numbers. If personal staff numbers are stored there, they are publicly disclosed.
- **Recommendation**: Confirm via data audit that `contact_phone` never holds personal numbers. If ambiguity exists, remove the field from `PublicBranchDetail` or document and enforce it as a business-only column.

---

### SEC-008: `routes_schedules.py` — dynamic SET clause column names not allowlisted
- **Severity**: LOW
- **Category**: Injection
- **File**: `routes_schedules.py` (lines 191–193)
- **Finding**:
  ```python
  set_clause = ", ".join(f"{k}=:{k}" for k in upd)
  db.execute(text(f"UPDATE hcs_provider_schedules SET {set_clause} ..."), upd)
  ```
  Column names are taken from `upd` which is built from a hard-coded set of `if payload.X is not None` branches. Values are properly parameterised. The risk is that a future developer adding `upd[user_input] = value` would introduce column-name injection without any guard failing.
- **Recommendation**: Add an explicit allowlist assertion before building `set_clause`: e.g. `assert set(upd.keys()) <= {"start_time", "end_time", "slot_duration_minutes", "appointment_types", "is_active"}`.

---

### SEC-009: OTP generated with `random.choices` (non-cryptographic PRNG)
- **Severity**: LOW
- **Category**: Crypto
- **File**: `sdk/otp.py` (line 35)
- **Finding**: `code = "".join(random.choices(string.digits, k=6))` uses Python's `random` module (Mersenne Twister), which is not a cryptographically secure PRNG. The 5-attempt lockout and 60-second cooldown significantly limit exploitation, but using a predictable PRNG for a security token is against best practice.
- **Recommendation**: Replace with `"".join(secrets.choice(string.digits) for _ in range(6))` from the `secrets` module.

---

### SEC-010: `routes_pharmacy.py` and `routes_billing.py` — dynamic WHERE clause pattern is fragile
- **Severity**: LOW
- **Category**: Injection
- **File**: `routes_pharmacy.py` (lines 307, 634); `routes_billing.py` (lines 239, 422)
- **Finding**: WHERE/filter clause strings are assembled by appending hardcoded predicate strings; all user-supplied values use named parameters. The current code is safe, but the pattern will silently become an injection vulnerability if a future filter appends user-controlled text without parameterisation.
- **Recommendation**: Add a comment marking the appended strings as an allowlist, and enforce a code-review gate that any new filter must use `:param` binding.

---

### SEC-011: `branch_scope.py` deferred dependency pattern may silently break on FastAPI upgrades
- **Severity**: LOW
- **Category**: AuthZ
- **File**: `sdk/branch_scope.py` (lines 195–203)
- **Finding**: `_get_tenant_scoped_session()` and `_get_current_user()` return `Depends(...)` objects. The `healthcare_branch_session` signature uses `Depends(_get_tenant_scoped_session)` and `Depends(_get_current_user)`, so FastAPI calls these wrappers and receives a `Depends(...)` object as the result. FastAPI does resolve chained `Depends` objects in some cases, but this non-standard double-wrapping is fragile and could silently fail (resolving the wrong value) on FastAPI version changes.
- **Recommendation**: Resolve the circular import via `TYPE_CHECKING` guards or a dedicated `_deps.py` shim, then import `tenant_scoped_session` and `get_current_user` directly.

---

## Clean Areas (no issues found)

- **`sdk/patient_auth.py`**: JWT validation is correct. `get_current_patient` explicitly checks `roles == ["patient"]`, rejects missing `patient_id`, and rejects staff tokens. Token type `"access"` is enforced.
- **`sdk/phi_crypto.py`**: `PHI_ENCRYPTION_KEY` raises `RuntimeError` at import if absent or malformed — correct fail-fast behaviour. Fernet (AES-128-CBC + HMAC-SHA256) is appropriate for column-level PHI encryption.
- **`sdk/otp.py` (brute-force protection)**: 5-attempt limit per OTP window and 60-second resend cooldown are implemented. Attempts are incremented before the code is checked. OTP and attempt counter are deleted on success.
- **`sdk/branch_scope.py` (header enforcement)**: Missing `X-Branch-ID` header for non-clinic-owner callers returns HTTP 422 — fail-closed. `X-Branch-ID: ALL` is rejected for non-clinic-owners.
- **`sdk/notification_service.py` (templates)**: All notification templates are PHI-safe. No patient name, diagnosis, provider name, or lab values appear in any template. Phone number is logged only as an HMAC hash in `hcs_notification_log`.
- **`routes_public.py` (PHI)**: No patient PHI is returned. Provider objects include only `display_name` and `specialty`; `license_number` and other PHI are explicitly excluded from the query.
- **IDOR — patient routes**: `routes_patient_profile.py` and `routes_patient_appointments.py` consistently filter all queries by `patient.patient_id` from the authenticated JWT. No route accepts a caller-supplied patient ID without binding it to the token claim.
- **Token storage (frontend)**: All `frontend/patient/*.js` files store `access_token` in `sessionStorage` only. `localStorage` is used only for locale preference (`locale`, `hc_locale`) which is non-sensitive.
- **`routes_i18n.py` (path traversal)**: Locale is validated against `_SUPPORTED_LOCALES` before any file path is constructed. Unsupported values fall back to the default locale. No user-controlled string is appended to the file path.
- **BPJS download endpoint**: No path traversal risk. File content is stored as base64 in the `file_reference` DB column and decoded server-side; no OS path is constructed from user input.
- **RLS policies — `hc_002`**: `hc_patients` has tenant-only RLS; `hc_encounters` and `hc_clinic_reviews` have branch RLS. Policies use `current_setting(..., true)` so a missing session variable returns NULL and matches no rows — correctly fail-closed.
- **`hcp_002_rls_policies.py` and `hcl_002_rls_policies.py`**: Pharmacy and lab PHI tables (`hcp_prescriptions`, `hcp_dispensing_records`, `hcl_lab_orders`, `hcl_specimens`, `hcl_results`) all have branch RLS applied.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0     |
| HIGH     | 4     |
| MEDIUM   | 3     |
| LOW      | 4     |
| **Total**| **11**|

### Priority order for remediation

1. **SEC-001** — Remove OTP + phone number from INFO log (active secret + PHI exposure)
2. **SEC-002** — Add startup fail-fast for `PHONE_HASH_SECRET`
3. **SEC-003** — Add startup fail-fast for `BPJS_EXPORT_HMAC_KEY`
4. **SEC-004** — Apply RLS to `hcb_service_items`, `hcb_invoice_lines`, `hcb_payments`, `hcb_bpjs_exports` before production
5. **SEC-006** — Apply RLS to `hcs_appointment_slots`, `hcs_provider_schedules`, `hcs_notification_log`
6. **SEC-005** — Validate UUIDs before interpolating into SET LOCAL
7. **SEC-009** — Replace `random.choices` with `secrets.choice` in OTP generation
