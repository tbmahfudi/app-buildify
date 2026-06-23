# Healthcare Module Setup Guide

This guide covers everything needed to bring the healthcare module online after the core platform is already running.

---

## Prerequisites

- The platform stack must be running (`docker compose -f infra/docker-compose.dev.yml ps` shows all services healthy)
- Redis must be reachable — the OTP service stores codes and rate-limit counters in Redis
- `REDIS_URL` must be set in `infra/.env`

---

## 1. PHI Encryption Key

The healthcare module encrypts Protected Health Information (PHI) fields at rest using a Fernet symmetric key.

**Generate a key:**

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Add it to `infra/.env`:**

```dotenv
PHI_ENCRYPTION_KEY=<paste-generated-key-here>
```

**Restart the backend** so it picks up the new env var:

```bash
docker compose -f infra/docker-compose.dev.yml restart backend
```

> **Warning:** The same key must be used for every migration run and every backend restart. Rotating the key requires re-encrypting all existing PHI rows — do not change it arbitrarily.

---

## 2. Required Database Roles

The healthcare migrations grant privileges to two roles. Both must exist before running migrations:

```bash
docker exec -i app_buildify_db psql -U appuser -d app_buildify -c "
  CREATE ROLE IF NOT EXISTS app_user;
  CREATE ROLE IF NOT EXISTS app_readonly_role;
"
```

---

## 3. Run Healthcare Migrations

```bash
docker exec \
  -e PHI_ENCRYPTION_KEY="$(grep PHI_ENCRYPTION_KEY infra/.env | cut -d= -f2-)" \
  app_buildify_backend \
  alembic upgrade heads
```

Migrations are located in `backend/app/alembic/versions/postgresql/` with the following prefixes:

| Prefix | Sub-module |
|--------|-----------|
| `hc_*` | Core (patients, branches, staff, providers, consents, encounters, reviews, audit, i18n) |
| `hcb_*` | Billing |
| `hcl_*` | Lab |
| `hcp_*` | Pharmacy |
| `hcs_*` | Scheduling |

---

## 4. Verify Tables Were Created

```bash
docker exec -i app_buildify_db psql -U appuser -d app_buildify -c "\dt hc*"
```

You should see approximately 30 tables, including:

- `hc_patients`, `hc_branches`, `hc_branch_staff`, `hc_providers`
- `hc_patient_consents`, `hc_encounters`, `hc_clinic_reviews`
- `hc_audit_log`, `hc_i18n_overrides`
- Billing, lab, pharmacy, and scheduling sub-module tables

---

## 5. OTP Messaging Configuration

The OTP service (`POST /api/v1/otp/send`) tries providers in this order:

1. **WhatsApp** — if `WHATSAPP_API_URL` and `WHATSAPP_API_TOKEN` are set
2. **SMS** — if `SMS_GATEWAY_URL` is set
3. **Log only** — if neither is configured (development mode: the 6-digit code appears in `docker logs app_buildify_backend`)

### WhatsApp configuration

```dotenv
WHATSAPP_API_URL=https://api.whatsapp.example.com/v1
WHATSAPP_API_TOKEN=your-bearer-token
```

### SMS gateway configuration

```dotenv
SMS_GATEWAY_URL=https://sms.example.com/send
```

### Development (no provider)

Leave both unset. OTP codes will be printed to the backend log:

```bash
docker logs -f app_buildify_backend | grep OTP
```

---

## 6. Test the Public Portal

The healthcare public portal is served by nginx at `/portal/healthcare/`.

```bash
curl -s "http://localhost:8080/portal/healthcare/?clinic=medcare"
```

A successful response returns the SPA HTML. Open it in a browser for the full UI:

```
http://localhost:8080/portal/healthcare/?clinic=medcare
http://localhost:8080/portal/healthcare/?clinic=healthpoint
```

---

## 7. Test the OTP Flow

### Send an OTP

```bash
curl -s -X POST http://localhost:8080/api/v1/otp/send \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890"}' \
  | python3 -m json.tool
```

Expected response:

```json
{
  "message": "OTP sent",
  "expires_in": 600
}
```

If no messaging provider is configured, check the backend logs for the code:

```bash
docker logs app_buildify_backend 2>&1 | grep -i "otp"
```

### Verify an OTP

```bash
curl -s -X POST http://localhost:8080/api/v1/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890", "code": "123456"}' \
  | python3 -m json.tool
```

Expected response:

```json
{
  "otp_token": "<single-use-token>",
  "expires_in": 300
}
```

The returned `otp_token` is valid for 5 minutes and can be exchanged for a session during patient registration or login.

### Rate limits

- **Send:** 5 attempts per phone number per 10 minutes
- **Resend cooldown:** 60 seconds between successive send requests

---

## 8. Patient Registration Example

```bash
curl -s -X POST http://localhost:8080/api/v1/healthcare/patients/register \
  -H "Content-Type: application/json" \
  -d '{
    "otp_token": "<token-from-verify>",
    "clinic_code": "medcare",
    "full_name": "Jane Doe",
    "date_of_birth": "1990-05-15",
    "phone": "+1234567890"
  }' \
  | python3 -m json.tool
```

---

## Reference

### Default tenant codes

| Tenant | Code |
|--------|------|
| MedCare Clinic | `medcare` |
| HealthPoint | `healthpoint` |

### Superadmin credentials (dev only)

| Field | Value |
|-------|-------|
| Email | `superadmin@system.com` |
| Password | `SuperAdmin123!` |

> Never use these credentials in a production environment.
