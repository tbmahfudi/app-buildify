# Environment Configuration

Complete reference for all environment variables used across the platform. Variable names are taken directly from the running Docker Compose configuration.

---

## Backend Core (`backend/.env` / `docker-compose.dev.yml`)

### Database

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `SQLALCHEMY_DATABASE_URL` | Yes | `postgresql+psycopg2://appuser:apppass@postgres:5432/appdb` | Primary database connection (SQLAlchemy DSN format) |
| `DATABASE_POOL_SIZE` | No | `10` | Connection pool size |
| `DATABASE_MAX_OVERFLOW` | No | `20` | Max connections above pool size |

**Supported database drivers**:
```
# PostgreSQL (default)
postgresql+psycopg2://user:pass@host:5432/db

# MySQL
mysql+pymysql://user:pass@host:3306/db

# SQLite (development only)
sqlite:///./dev.db
```

### Authentication

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | — | JWT signing secret (use a strong 64-char random value in production) |
| `ACCESS_TOKEN_EXPIRE_MIN` | No | `30` | Access token lifetime in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifetime in days |

### Application

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ALLOWED_ORIGINS` | No | `*` | CORS allowed origins, comma-separated |
| `DEBUG` | No | `false` | Enable debug mode and hot reload |
| `ENVIRONMENT` | No | `production` | `development` / `staging` / `production` |
| `LOG_LEVEL` | No | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

### Redis (Optional)

Redis is not included in the default dev compose but is used for token revocation if configured.

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No | `redis://:password@redis:6379` | Redis connection URL |

### Monitoring (Optional)

| Variable | Required | Description |
|----------|----------|-------------|
| `SENTRY_DSN` | No | Sentry project DSN for error tracking |
| `PROMETHEUS_ENABLED` | No | Enable `/metrics` Prometheus endpoint (not yet implemented) |

---

## Financial Module

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_STRATEGY` | No | `shared` | `shared` (use core DB) or `separate` |
| `DATABASE_URL` | If shared | — | PostgreSQL URL for shared DB access |
| `MODULE_DATABASE_URL` | If separate | — | Separate DB URL |
| `EVENT_BUS_CONNECTION_STRING` | No | — | PostgreSQL connection for LISTEN/NOTIFY event bus |
| `CORE_PLATFORM_URL` | No | `http://backend:8000` | Core API URL for inter-service calls |
| `MODULE_NAME` | No | `financial` | Module identifier |
| `MODULE_VERSION` | No | `1.0.0` | Module version string |
| `MODULE_PORT` | No | `9001` | Module listen port |
| `DEBUG` | No | `false` | Debug mode |
| `CORS_ORIGINS` | No | `["http://localhost:8080"]` | JSON array of allowed origins |
| `API_PREFIX` | No | `/api/v1` | API route prefix |

---

## Nginx (no env vars — configured via `app.conf`)

The frontend Nginx container is configured via `infra/nginx/app.conf` mounted as a volume. No environment variables are used.

---

## Environment File Examples

### Development

```env
# backend/.env for docker-compose.dev.yml
SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://appuser:apppass@postgres:5432/appdb
SECRET_KEY=dev-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MIN=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:3000
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### Staging

```env
SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://buildify:StrongPass@staging-db:5432/appdb?sslmode=require
SECRET_KEY=<64-char-random-key>
ACCESS_TOKEN_EXPIRE_MIN=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=https://staging.yourapp.com
DEBUG=false
ENVIRONMENT=staging
LOG_LEVEL=INFO
SENTRY_DSN=https://key@sentry.io/project
```

### Production

```env
SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://buildify:VeryStrongPass@prod-db:5432/appdb?sslmode=require
SECRET_KEY=<64-char-random-key>
ACCESS_TOKEN_EXPIRE_MIN=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=https://app.yourcompany.com
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=INFO
SENTRY_DSN=https://key@sentry.io/project
REDIS_URL=redis://:RedisPass@prod-redis:6379
```

---

## Generating Secure Secrets

```bash
# SECRET_KEY (64-char random string)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# PostgreSQL password
python3 -c "import secrets; print(secrets.token_hex(16))"
```

---

## Secret Management in Production

Never store production secrets in `.env` files committed to git. Use:

| Platform | Solution |
|----------|---------|
| AWS | AWS Secrets Manager + ECS task secrets |
| GCP | Google Secret Manager |
| Azure | Azure Key Vault |
| Kubernetes | Sealed Secrets or Vault |
| Self-hosted | HashiCorp Vault |
