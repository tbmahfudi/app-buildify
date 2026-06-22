# Healthcare Module Suite — Architecture

## Overview

Two-sided platform: clinic staff portal (desktop-first) + patient portal (mobile-first, Android-optimised). Both sides share the same platform JWT issuer but use different role namespaces.

## Sub-module activation model

```
healthcare (base, required)
├── healthcare_scheduling   (activate independently)
├── healthcare_billing      (activate independently)
├── healthcare_pharmacy     (activate independently)
└── healthcare_lab          (activate independently)
```

Base module is a hard gate — no sub-module can activate without it. Enforced server-side via `required_modules` in each sub-module's manifest.json.

## Key architectural decisions

### ADR-HC-001: Branch Isolation
3-layer enforcement:
1. **BranchScopeListener** (ORM layer): intercepts every query, raises `BranchScopeMissingError` if branch context unset
2. **PostgreSQL RLS** (DB layer): `CREATE POLICY` on all PHI tables using `current_setting('app.branch_id')`
3. **X-Branch-ID header** (HTTP layer): `healthcare_branch_session` dependency validates header, sets `set_config('app.branch_id', ...)` — parameterized, not interpolated

Clinic owners bypass branch scope via sentinel `'ALL'` branch_id. Fail-closed: missing header → HTTP 422.

### ADR-HC-002: Cross-module PHI Sharing
Sub-modules access Patient and Encounter data exclusively via:
- `modules/healthcare/sdk/patient_reader.py` → `get_patient()`
- `modules/healthcare/sdk/encounter_reader.py` → `get_encounter()`

Every SDK call unconditionally writes an audit log entry before returning data.

### ADR-HC-003: Two-sided Auth
- Same JWT issuer for staff and patients
- Patient role namespace: `{roles: ["patient"], tenant_id: null}`
- `get_current_patient()` asserts `roles == ["patient"]` — rejects staff tokens
- Patient tokens: access (15 min HS256) + refresh (7-day); stored in sessionStorage only
- Public endpoints: hCaptcha + Redis rate limiting (60/min/IP)

### ADR-HC-004: i18n Architecture
- Per-module JSON translation files: `modules/healthcare/i18n/id-ID.json` (reference), `en-US.json`
- Locale resolution: user profile → tenant default → platform default (`id-ID`)
- Frontend: `initI18n(locale)` + `t(locale, key)` + `changeLocale()` with MutationObserver
- Backend: `resolve_locale(user, tenant)` + `t(locale, key, **kwargs)`
- 183 translation keys across all sub-modules

## PHI Security

| Control | Implementation |
|---------|---------------|
| Encryption at rest | `EncryptedPHIType` (Fernet AES-256); `PHI_ENCRYPTION_KEY` fail-fast at startup |
| Phone deduplication | HMAC-SHA256 hash stored alongside encrypted column |
| Insurance numbers | Fernet-encrypted TEXT column |
| Audit trail | Append-only `hc_audit_log`; INSERT-only DB grant (REVOKE UPDATE, DELETE) |
| Notification PHI | System-locked templates only; no patient name/diagnosis/values in body |
| BPJS export PHI | HMAC-anonymised names; `BPJS_EXPORT_HMAC_KEY` fail-fast |

## SDK surface

| Component | Purpose |
|-----------|---------|
| `sdk/patient_auth.py` | Patient JWT validation, `get_current_patient`, `has_patient_permission` |
| `sdk/branch_scope.py` | Branch RLS setup, `healthcare_branch_session` dependency |
| `sdk/hc_permissions.py` | Staff RBAC, `has_hc_permission`, `HCRole` enum |
| `sdk/phi_audit.py` | `write_phi_read_audit`, `write_event_audit` |
| `sdk/phi_crypto.py` | `EncryptedPHIType`, `encrypt_phi`, `decrypt_phi` |
| `sdk/patient_reader.py` | PHI-safe `get_patient()` with mandatory audit |
| `sdk/encounter_reader.py` | PHI-safe `get_encounter()` with mandatory audit |
| `sdk/notification_service.py` | PHI-safe WhatsApp/SMS dispatch, `dispatch_to_provider` |
| `sdk/otp.py` | CSPRNG OTP (secrets.choice), Redis-backed attempt limiting |

## Migration chain

```
hc_001 (base tables) → hc_002 → hc_003 → hc_004
→ hc_005 (encounter sharing)
→ hc_006 (review moderation)
→ hcs_001 (scheduling) → hcs_002 (scheduling RLS)
→ hcb_001 (billing) → hcb_002 (billing RLS)
→ hcp_001 (pharmacy) → hcp_002 (pharmacy RLS)
→ hcl_001 (lab) → hcl_002 (lab RLS)
```
Total: 14 migrations across 5 waves.
