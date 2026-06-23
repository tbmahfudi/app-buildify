# Fresh Install Guide

This guide walks you through setting up app-buildify from scratch on a new machine.

---

## Prerequisites

- **Git** — to clone the repository
- **Docker** (v24+) and **Docker Compose** (v2.20+) — all services run in containers
- **WSL2** (Windows only) — the repo lives in a WSL2 Ubuntu instance; Docker Desktop must have WSL2 integration enabled

Verify Docker is working:

```bash
docker --version
docker compose version
```

---

## 1. Clone the Repository

```bash
git clone <repo-url> app-buildify
cd app-buildify
```

---

## 2. Create `infra/.env`

The dev stack reads secrets from `infra/.env`. This file is **gitignored** and must be created manually on every environment.

```bash
cp infra/.env.example infra/.env   # if an example exists, otherwise create from scratch
```

Minimum required contents:

```dotenv
# --- Core platform ---
SECRET_KEY=change-me-in-production
SQLALCHEMY_DATABASE_URL=postgresql+asyncpg://appuser:apppassword@db:5432/app_buildify
REDIS_URL=redis://redis:6379/0

# --- Healthcare module ---
PHI_ENCRYPTION_KEY=<generated-fernet-key>   # see step 3

# --- Messaging (OTP) — optional, falls back to log output if omitted ---
# WHATSAPP_API_URL=https://api.whatsapp.example.com/v1
# WHATSAPP_API_TOKEN=your-token-here
# SMS_GATEWAY_URL=https://sms.example.com/send

# --- Email (dev mailhog defaults shown) ---
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_FROM=noreply@app-buildify.local
SMTP_USE_TLS=false

# --- CORS ---
ALLOWED_ORIGINS=http://localhost:8080
```

See [`ENV_VARS.md`](ENV_VARS.md) for the full reference.

---

## 3. Generate the PHI Encryption Key

The healthcare module encrypts protected health information (PHI) at rest using a [Fernet](https://cryptography.io/en/latest/fernet/) symmetric key.

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output into `infra/.env` as `PHI_ENCRYPTION_KEY=<value>`.

> **Keep this key safe.** Losing it makes encrypted PHI permanently unreadable. Back it up in a secrets manager before deploying to production.

---

## 4. Start the Stack

```bash
docker compose -f infra/docker-compose.dev.yml up -d
```

This starts the following services: `db` (PostgreSQL), `redis`, `backend` (FastAPI), `nginx` (reverse proxy), `mailhog` (SMTP catch-all).

Confirm all containers are healthy:

```bash
docker compose -f infra/docker-compose.dev.yml ps
```

---

## 5. Create Required Database Roles

The migration scripts grant table-level permissions to two roles that must exist before running migrations:

```bash
docker exec -i app_buildify_db psql -U appuser -d app_buildify -c "
  CREATE ROLE IF NOT EXISTS app_user;
  CREATE ROLE IF NOT EXISTS app_readonly_role;
"
```

> **Note:** If `CREATE ROLE IF NOT EXISTS` is not available on your PostgreSQL version, omit the `IF NOT EXISTS` clause and ignore the "role already exists" error.

---

## 6. Run Migrations

```bash
docker exec \
  -e PHI_ENCRYPTION_KEY="$(grep PHI_ENCRYPTION_KEY infra/.env | cut -d= -f2-)" \
  app_buildify_backend \
  alembic upgrade heads
```

This applies all pending migrations, including the 30 healthcare tables across the five healthcare sub-modules (clinical, billing, lab, pharmacy, scheduling).

---

## 7. Seed Initial Data

Populate clinic tenants and a superadmin user:

```bash
docker exec app_buildify_backend python backend/scripts/seed_clinic_tenants.py
```

This script creates the default tenants (`medcare`, `healthpoint`) and the platform superadmin account.

---

## 8. Smoke Test

**Health endpoint:**

```bash
curl -s http://localhost:8080/api/v1/health | python3 -m json.tool
```

Expected response:

```json
{
  "status": "ok"
}
```

**Login as superadmin:**

```bash
curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "superadmin@system.com", "password": "SuperAdmin123!"}' \
  | python3 -m json.tool
```

A successful response returns an `access_token` and `refresh_token`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Container exits immediately | Missing env var in `infra/.env` | Check `docker logs app_buildify_backend` |
| `role "app_user" does not exist` during migration | Roles not created | Re-run step 5 |
| OTP codes appear only in logs | No messaging provider configured | Set `WHATSAPP_API_URL` or `SMS_GATEWAY_URL` in `infra/.env` |
| PHI fields show garbled text | Wrong or missing `PHI_ENCRYPTION_KEY` | Ensure the key in `infra/.env` matches the one used during initial migration |
