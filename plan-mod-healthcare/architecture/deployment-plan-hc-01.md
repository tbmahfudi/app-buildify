# Healthcare Module — Deployment Plan v1.0

_Generated: 2026-06-22 | Author: E1 DevOps Engineer_

---

## 1. Required Environment Variables

| Variable | Purpose | How to generate | Fail behaviour if missing |
|---|---|---|---|
| `PHI_ENCRYPTION_KEY` | Fernet AES-256 key for PHI columns (`sdk/phi_crypto.py`) | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | `RuntimeError` at module import |
| `PHONE_HASH_SECRET` | HMAC key for phone deduplication in `sdk/notification_service.py` | `openssl rand -hex 32` | `RuntimeError` at module import |
| `BPJS_EXPORT_HMAC_KEY` | HMAC key for BPJS export anonymisation in `routes_billing.py` | `openssl rand -hex 32` | BPJS export endpoint raises 500 |
| `HCAPTCHA_SECRET_KEY` | hCaptcha verification (use `"test"` in CI/staging) | From [hcaptcha.com](https://hcaptcha.com) dashboard | All captcha verifications fail — patient registration blocked |
| `REDIS_URL` | OTP storage, rate limiting, appointment reminders, waitlist | `redis://localhost:6379/0` (default — override in production) | OTP login fails; rate limiting disabled; reminders silently skipped |
| `WHATSAPP_API_URL` | WhatsApp Business API endpoint for patient notifications | From Meta Business dashboard | Falls back to SMS gateway |
| `WHATSAPP_API_TOKEN` | WhatsApp auth bearer token | From Meta Business dashboard | Falls back to SMS gateway |
| `SMS_GATEWAY_URL` | SMS fallback when WhatsApp unavailable | From SMS provider dashboard | Notifications silently skipped entirely |
| `SECRET_KEY` | JWT signing key for patient session tokens (`sdk/patient_tokens.py`) | `openssl rand -hex 64` | Patient token validation always fails — all authenticated patient routes return 401 |
| `PHONE_HASH_KEY` | HMAC key for phone hashing in `routes_patient_auth.py` | `openssl rand -hex 32` | Falls back to insecure default `"changeme-set-PHONE_HASH_KEY"` — **must be set in production** |

---

## 2. Optional / Defaulted Variables

| Variable | Default | Notes |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | Required variable with a safe default for local dev; override in production with auth credentials |
| `HCAPTCHA_SECRET_KEY` | `""` (empty string) | Set to `"test"` in CI/staging to bypass captcha verification |
| `PHONE_HASH_KEY` | `"changeme-set-PHONE_HASH_KEY"` | **Insecure default — must be overridden in production before first patient registration** |

---

## 3. Migration Run Order

The dependency chain (derived from `down_revision` fields across all 14 migration files):

```
platform_head → hc001 → hc002 → hc003 → hc004 → hcs001 → hcs002 → hcb001 → hcb002 → hcp001 → hcp002 → hcl001 → hcl002
                                                      ↑
                                                    hc005 → hc006
```

**Note on hc005:** `hc_005_encounter_sharing` has `down_revision = "hcs001"`, branching from the scheduling chain. Alembic will resolve the DAG automatically with `alembic upgrade head`.

### Step-by-step

| # | Revision ID | File | What it creates | Upgrade command | Rollback command |
|---|---|---|---|---|---|
| 1 | `hc001` | `hc_001_base_tables.py` | All Healthcare core tables: `hc_branches`, `hc_patients`, `hc_encounters`, `hc_clinic_reviews`, `hc_audit_log`, and supporting base tables | `alembic upgrade hc001` | `alembic downgrade base` |
| 2 | `hc002` | `hc_002_rls_policies.py` | PostgreSQL Row Level Security policies on PHI tables via `apply_tenant_rls` / `apply_branch_rls` helpers | `alembic upgrade hc002` | `alembic downgrade hc001` |
| 3 | `hc003` | `hc_003_audit_permissions.py` | INSERT-only DB grants on `hc_audit_log`; pg rules blocking UPDATE/DELETE on audit table | `alembic upgrade hc003` | `alembic downgrade hc002` |
| 4 | `hc004` | `hc_004_i18n_overrides.py` | `hc_i18n_overrides` table for per-tenant translation key overrides | `alembic upgrade hc004` | `alembic downgrade hc003` |
| 5 | `hcs001` | `hcs_001_scheduling_tables.py` | Scheduling tables: `hcs_provider_schedules`, `hcs_appointment_slots`, `hcs_appointments`, `hcs_waitlist`, `hcs_reminders` | `alembic upgrade hcs001` | `alembic downgrade hc004` |
| 6 | `hcs002` | `hcs_002_rls_policies.py` | Branch-scoped and tenant-scoped RLS on all scheduling tables | `alembic upgrade hcs002` | `alembic downgrade hcs001` |
| 7 | `hcb001` | `hcb_001_billing_tables.py` | Billing tables: invoices, line items, payments, BPJS claim records | `alembic upgrade hcb001` | `alembic downgrade hcs002` |
| 8 | `hcb002` | `hcb_002_rls_policies.py` | Tenant + branch RLS on billing tables | `alembic upgrade hcb002` | `alembic downgrade hcb001` |
| 9 | `hcp001` | `hcp_001_pharmacy_tables.py` | Pharmacy tables: `hcp_medications` catalog, `hcp_drug_interactions`, `hcp_prescriptions`, `hcp_prescription_lines`, `hcp_dispensing_records` | `alembic upgrade hcp001` | `alembic downgrade hcb002` |
| 10 | `hcp002` | `hcp_002_rls_policies.py` | RLS on pharmacy tables: branch-scoped (prescriptions, dispensing), tenant-scoped (catalog, drug interactions) | `alembic upgrade hcp002` | `alembic downgrade hcp001` |
| 11 | `hcl001` | `hcl_001_lab_tables.py` | Laboratory tables: `hcl_test_panels` catalog, `hcl_lab_orders`, `hcl_order_lines`, `hcl_specimens`, `hcl_results` | `alembic upgrade hcl001` | `alembic downgrade hcp002` |
| 12 | `hcl002` | `hcl_002_rls_policies.py` | RLS on laboratory tables: branch-scoped (orders, specimens, results), tenant-scoped (test panels catalog) | `alembic upgrade hcl002` | `alembic downgrade hcl001` |
| 13 | `hc005` | `hc_005_encounter_sharing.py` | Adds `shared_with_patient` boolean column to `hc_encounters` | `alembic upgrade hc005` | `alembic downgrade hcs001` |
| 14 | `hc006` | `hc_006_review_moderation.py` | Adds moderation columns to `hc_clinic_reviews`: `status`, `response_text`, `response_at`, `moderation_released_at` | `alembic upgrade hc006` | `alembic downgrade hc005` |

### Single-command full upgrade (recommended for clean environments)

```bash
alembic upgrade head
```

### Single-command full rollback

```bash
alembic downgrade base
```

---

## 4. Deployment Sequence

### Pre-flight checklist

```bash
# Verify all required env vars are set before proceeding
for var in PHI_ENCRYPTION_KEY PHONE_HASH_SECRET BPJS_EXPORT_HMAC_KEY HCAPTCHA_SECRET_KEY REDIS_URL SECRET_KEY PHONE_HASH_KEY; do
    if [ -z "${!var}" ]; then echo "MISSING: $var"; else echo "OK: $var"; fi
done
```

### Step 1 — Set all required environment variables

```bash
export PHI_ENCRYPTION_KEY="<fernet-key>"
export PHONE_HASH_SECRET="<openssl-hex-32>"
export BPJS_EXPORT_HMAC_KEY="<openssl-hex-32>"
export HCAPTCHA_SECRET_KEY="<from-hcaptcha-dashboard>"
export REDIS_URL="redis://:STRONG_PASSWORD@redis-host:6379/0"
export WHATSAPP_API_URL="https://graph.facebook.com/v18.0/PHONE_NUMBER_ID/messages"
export WHATSAPP_API_TOKEN="<meta-bearer-token>"
export SMS_GATEWAY_URL="<sms-provider-endpoint>"
export SECRET_KEY="<openssl-hex-64>"
export PHONE_HASH_KEY="<openssl-hex-32>"
```

### Step 2 — Run migrations in order

```bash
# Recommended: single command resolves full DAG
alembic upgrade head

# Or step-by-step (see Section 3 for individual commands):
alembic upgrade hc001   # base tables
alembic upgrade hc002   # core RLS policies
alembic upgrade hc003   # audit log permissions
alembic upgrade hc004   # i18n overrides
alembic upgrade hcs001  # scheduling tables
alembic upgrade hcs002  # scheduling RLS
alembic upgrade hcb001  # billing tables
alembic upgrade hcb002  # billing RLS
alembic upgrade hcp001  # pharmacy tables
alembic upgrade hcp002  # pharmacy RLS
alembic upgrade hcl001  # lab tables
alembic upgrade hcl002  # lab RLS
alembic upgrade hc005   # encounter sharing column
alembic upgrade hc006   # review moderation columns
```

### Step 3 — Deploy application

Deploy the new container/binary via blue-green or rolling strategy. Confirm the new instance passes all health checks before routing live traffic.

### Step 4 — Verify health checks

See Section 7 for the full post-deploy verification suite.

---

## 5. Zero-Downtime Notes

### Additive-only migrations (safe while old app version still runs)

These migrations only add new tables or nullable columns; the previous app version is unaffected.

| Revision | Why it is safe |
|---|---|
| `hc001` | Creates new tables from scratch |
| `hc003` | Adds DB grants only; no schema change |
| `hc004` | Creates new table `hc_i18n_overrides` |
| `hcs001` | Creates new scheduling tables |
| `hcb001` | Creates new billing tables |
| `hcp001` | Creates new pharmacy tables |
| `hcl001` | Creates new lab tables |
| `hc005` | Adds nullable `shared_with_patient` boolean to `hc_encounters` — old app reads rows fine |
| `hc006` | Adds nullable moderation columns to `hc_clinic_reviews` — old app reads rows fine |

### Migrations requiring a maintenance window or careful ordering

These migrations install PostgreSQL RLS policies. Once applied, connections that do not set `app.current_tenant_id` / `app.current_branch_id` session variables return empty result sets instead of errors — causing silent data gaps for app versions that do not yet set those variables.

| Revision | Risk | Mitigation |
|---|---|---|
| `hc002` | RLS on core PHI tables | Deploy new app version immediately after; do not leave old app running against this DB |
| `hcs002` | RLS on scheduling tables | Same |
| `hcb002` | RLS on billing tables | Same |
| `hcp002` | RLS on pharmacy tables | Same |
| `hcl002` | RLS on lab tables | Same |

**Recommended strategy:** apply all DDL-only migrations while old app runs (safe additive changes), then open a brief maintenance window to apply the five RLS migration pairs followed immediately by the new app deployment.

---

## 6. Rollback Plan

### Failure at migration stage

```bash
# Check current applied revision
alembic current

# Roll back the last applied revision
alembic downgrade -1

# Roll back to a known-good revision, e.g. before RLS wave:
alembic downgrade hc004   # reverts hcs001 and all subsequent revisions

# Full clean rollback
alembic downgrade base
```

Restart the previous app version and confirm health checks pass before re-opening traffic.

### Failure at app deploy stage (migrations already applied)

1. Revert the deploy to the previous container/binary.
2. All additive migrations (`hc001`, `hc004`, `hcs001`, `hcb001`, `hcp001`, `hcl001`, `hc005`, `hc006`) are compatible with the old app — new tables/columns are ignored.
3. If RLS migrations were applied and the old app does not set tenant session variables, roll back the RLS layers:

```bash
alembic downgrade hcl001   # removes hcl002 (lab RLS)
alembic downgrade hcp001   # removes hcp002 (pharmacy RLS)
alembic downgrade hcb001   # removes hcb002 (billing RLS)
alembic downgrade hcs001   # removes hcs002 (scheduling RLS)
alembic downgrade hc004    # removes hc002 (core RLS) — WARNING: also removes hc003 audit grants
```

4. Restore traffic to old app version.
5. Investigate root cause before re-attempting deployment.

---

## 7. Post-deploy Health Checks

Run these in order after deployment. All should respond within 2 seconds.

```bash
# 1. Clinic search — confirms core tables, RLS, and GET routing
curl -sf -H "X-Tenant-Id: test-tenant" \
  http://localhost:8000/api/v1/clinics/search | python3 -m json.tool
# Expected: HTTP 200, JSON with "results": [] or populated list

# 2. Patient OTP registration — confirms Redis, PHONE_HASH_KEY, OTP flow
curl -sf -X POST http://localhost:8000/api/v1/patients/register \
  -H "Content-Type: application/json" \
  -d '{"phone": "+621234567890"}' | python3 -m json.tool
# Expected: HTTP 200 or 201, JSON with OTP reference token

# 3. i18n translation keys — confirms hc_i18n_overrides table and i18n route
curl -sf http://localhost:8000/api/v1/modules/healthcare/i18n/id-ID | python3 -m json.tool
# Expected: HTTP 200, JSON object with Indonesian translation keys

# 4. Redis connectivity
redis-cli -u "$REDIS_URL" PING
# Expected: PONG

# 5. General health endpoint
curl -sf http://localhost:8000/api/v1/health | python3 -m json.tool
# Expected: HTTP 200 with {"status": "ok"} or equivalent
```

---

## 8. Security Configuration Notes

### PHI_ENCRYPTION_KEY rotation

**This procedure must be rehearsed in staging before any production key rotation.**

1. Generate a new Fernet key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
2. Add `PHI_ENCRYPTION_KEY_OLD=<current-key>` alongside `PHI_ENCRYPTION_KEY=<new-key>` in the environment.
3. Run the key-rotation script (TBD — to be authored by backend team) that reads each PHI column with the old key and re-encrypts with the new key.
4. Remove `PHI_ENCRYPTION_KEY_OLD` from env after successful rotation.
5. Minimum rotation frequency: annually, or immediately upon suspected key compromise.

### Redis security

- **Production:** always include a password: `redis://:STRONG_PASSWORD@redis-host:6379/0`
- Enable `requirepass` in `redis.conf`.
- Use TLS: `rediss://:PASSWORD@redis-host:6380/0` for encrypted connections.
- Restrict Redis network access to the application subnet only — never expose publicly.

### WhatsApp / Meta configuration

- Register and verify the production phone number with Meta before the first notification attempt; unregistered numbers cause silent send failures.
- Store `WHATSAPP_API_TOKEN` in a secrets manager (AWS Secrets Manager, HashiCorp Vault, Kubernetes Secrets) — never in `.env` files.
- Use System User tokens (non-expiring) rather than user access tokens to avoid token expiry disrupting notifications.

### PHONE_HASH_KEY

- The default value `"changeme-set-PHONE_HASH_KEY"` is insecure and publicly known. Setting a strong secret is **mandatory before first patient registration in production**.
- Changing this key post-launch will break deduplication lookups for all existing patient records — plan any key rotation carefully with a re-hash migration.

### General secret management

- Inject all secrets at runtime via a secrets manager or secure environment injection; never commit to source control.
- Rotate `SECRET_KEY` (JWT signing) and `PHONE_HASH_SECRET` at minimum annually or upon suspected compromise.
- Audit secret access regularly in your secrets manager's access logs.

---

_End of deployment plan. Review with platform team and security team before first production deployment._
