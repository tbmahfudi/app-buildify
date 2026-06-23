# Environment Variables Reference

All environment variables for the app-buildify platform and healthcare module.

---

## `infra/.env` File

The dev stack is configured via `infra/.env`. This file is **gitignored** and must be created manually on each environment. It is loaded by `infra/docker-compose.dev.yml` and injected into the relevant containers.

**Template:**

```dotenv
# Core platform
SECRET_KEY=change-me-in-production
SQLALCHEMY_DATABASE_URL=postgresql+asyncpg://appuser:apppassword@db:5432/app_buildify
REDIS_URL=redis://redis:6379/0

# Healthcare module
PHI_ENCRYPTION_KEY=

# OTP messaging (optional)
# WHATSAPP_API_URL=
# WHATSAPP_API_TOKEN=
# SMS_GATEWAY_URL=

# Email
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_FROM=noreply@app-buildify.local
SMTP_USE_TLS=false

# CORS
ALLOWED_ORIGINS=http://localhost:8080

# Token lifetimes
ACCESS_TOKEN_EXPIRE_MIN=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## Variable Reference

### Core Platform

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | `dev-secret-key-change-in-production` | JWT signing key. Use a long random string in production. |
| `SQLALCHEMY_DATABASE_URL` | Yes | — | PostgreSQL connection string. Format: `postgresql+asyncpg://user:pass@host:port/dbname` |
| `REDIS_URL` | Yes | `redis://redis:6379/0` | Redis connection URL. Required for OTP codes, rate limiting, and session caching. |
| `ALLOWED_ORIGINS` | No | `http://localhost:8080` | Comma-separated list of CORS allowed origins. |
| `ACCESS_TOKEN_EXPIRE_MIN` | No | `30` | JWT access token lifetime in minutes. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | JWT refresh token lifetime in days. |
| `HOST_PROJECT_ROOT` | No | `/home/mahfudi/app-buildify` | Absolute host path to the project root. Used for standalone/module installs that need to mount host directories. |

### Healthcare Module

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PHI_ENCRYPTION_KEY` | Yes (healthcare) | — | Fernet symmetric key for encrypting Protected Health Information fields. Generate with: `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Must remain constant — changing it requires re-encrypting all PHI data. |

### OTP / Messaging

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WHATSAPP_API_URL` | No | — | WhatsApp Business API endpoint for sending OTP codes (e.g. `https://api.whatsapp.example.com/v1`). If unset, WhatsApp delivery is skipped. |
| `WHATSAPP_API_TOKEN` | No | — | Bearer token for authenticating with the WhatsApp API. Required if `WHATSAPP_API_URL` is set. |
| `SMS_GATEWAY_URL` | No | — | SMS gateway endpoint for OTP fallback delivery. Used when WhatsApp is not configured. If neither `WHATSAPP_API_URL` nor `SMS_GATEWAY_URL` is set, OTP codes are written to the backend log only (suitable for development). |

### Email (SMTP)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SMTP_HOST` | No | `mailhog` | SMTP server hostname. In dev, the stack includes a Mailhog container that catches all outbound email. |
| `SMTP_PORT` | No | `1025` | SMTP server port. |
| `SMTP_FROM` | No | `noreply@app-buildify.local` | From address used on all outbound email. |
| `SMTP_USE_TLS` | No | `false` | Set to `true` to enable STARTTLS. Required for most production SMTP providers. |

---

## Notes

- All variables marked **Yes (healthcare)** are only required if the healthcare module is enabled. The platform will start without them, but healthcare routes will fail.
- Never commit `infra/.env` to version control. The file is listed in `.gitignore`.
- In CI/CD pipelines, inject secrets via your pipeline's secret store rather than a `.env` file.
