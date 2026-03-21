# Environment Configuration

Complete reference for all environment variables used across the platform.

---

## Backend Core (`backend/.env`)

### Database

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql://user:pass@host:5432/db` | Primary database connection |
| `DATABASE_POOL_SIZE` | No | `10` | SQLAlchemy connection pool size |
| `DATABASE_MAX_OVERFLOW` | No | `20` | Max connections above pool size |
| `DATABASE_POOL_TIMEOUT` | No | `30` | Seconds to wait for a connection |

### Redis

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | Yes | `redis://:password@host:6379` | Redis connection URL |
| `REDIS_DB` | No | `0` | Redis database index |
| `REDIS_TOKEN_BLACKLIST_TTL` | No | `3600` | Token blacklist entry TTL (seconds) |

### JWT & Authentication

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | Yes | — | Signing key (32+ chars recommended) |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifetime |

### Application

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEBUG` | No | `false` | Enable debug mode (hot reload, verbose errors) |
| `ENVIRONMENT` | No | `production` | `development` / `staging` / `production` |
| `LOG_LEVEL` | No | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `ALLOWED_ORIGINS` | No | `*` | CORS origins (comma-separated) |
| `RATE_LIMIT` | No | `100/minute` | Default rate limit per IP |
| `PORT` | No | `8000` | Uvicorn listen port |

### Monitoring (Optional)

| Variable | Required | Description |
|----------|----------|-------------|
| `SENTRY_DSN` | No | Sentry project DSN for error tracking |
| `PROMETHEUS_ENABLED` | No | Enable `/metrics` endpoint |

---

## Financial Module (`modules/financial/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_STRATEGY` | No | `shared` | `shared` (use core DB) or `separate` |
| `MODULE_DATABASE_URL` | If separate | — | DB URL when using separate database |
| `CORE_PLATFORM_URL` | Yes | `http://core-platform:8000` | Internal URL of core API |
| `MODULE_API_KEY` | Yes | — | Shared secret for authentication with core |
| `PORT` | No | `9001` | Module service listen port |
| `DEBUG` | No | `false` | Debug mode |
| `LOG_LEVEL` | No | `INFO` | Log level |

---

## Docker Compose Overrides

For local development, you can create `docker-compose.override.yml` to override settings without modifying the main compose file:

```yaml
# docker-compose.override.yml
services:
  core-platform:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ./backend:/app   # Hot reload in dev
```

---

## Environment File Examples

### Development (`.env`)

```env
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/buildify
REDIS_URL=redis://redis:6379
JWT_SECRET_KEY=dev-secret-key-not-for-production
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=http://localhost,http://localhost:5173
RATE_LIMIT=1000/minute
```

### Staging (`.env.staging`)

```env
DATABASE_URL=postgresql://buildify_user:StrongPass123@staging-db:5432/buildify?sslmode=require
REDIS_URL=redis://:RedisPass123@staging-redis:6379
JWT_SECRET_KEY=<64-char-random-staging-key>
DEBUG=false
ENVIRONMENT=staging
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://staging.yourapp.com
RATE_LIMIT=200/minute
SENTRY_DSN=https://key@sentry.io/project
```

### Production (`.env.production`)

```env
DATABASE_URL=postgresql://buildify_user:VeryStrongPass@prod-rds:5432/buildify?sslmode=require
REDIS_URL=redis://:VeryStrongRedisPass@prod-elasticache:6379
JWT_SECRET_KEY=<64-char-random-production-key>
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://app.yourcompany.com
RATE_LIMIT=100/minute
SENTRY_DSN=https://key@sentry.io/project
PROMETHEUS_ENABLED=true
```

---

## Secret Management Recommendations

For production, avoid storing secrets in `.env` files on disk. Instead, use:

| Platform | Solution |
|----------|---------|
| AWS | AWS Secrets Manager + ECS task secrets |
| GCP | Google Secret Manager |
| Azure | Azure Key Vault |
| Kubernetes | Kubernetes Secrets (base64) or Vault |
| Self-hosted | HashiCorp Vault |

Inject secrets as environment variables at container startup time.
