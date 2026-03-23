# Deployment Guide

## Overview

App-Buildify is containerized with Docker and orchestrated via Docker Compose. The stack consists of:

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `postgres` | postgres:15-alpine | 5432 | Primary database |
| `redis` | redis:7-alpine | 6379 | Cache and session store |
| `core-platform` | python:3.11-slim | 8000 | Core FastAPI backend |
| `financial-module` | python:3.11-slim | 9001 | Financial module backend |
| `api-gateway` | nginx:alpine | 80 / 443 | Reverse proxy and static files |
| `frontend` | node:20-alpine | 5173 (dev) | Frontend app |

---

## Environment Configuration

All environment variables are loaded from `backend/.env`. Copy the example file to get started:

```bash
cp backend/.env.example backend/.env
```

### Core Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `REDIS_URL` | Yes | — | Redis connection string |
| `JWT_SECRET_KEY` | Yes | — | JWT signing secret (32+ chars) |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `DEBUG` | No | `false` | Enable debug mode |
| `ENVIRONMENT` | No | `production` | `development` / `staging` / `production` |
| `RATE_LIMIT` | No | `100/minute` | Default rate limit |
| `ALLOWED_ORIGINS` | No | `*` | CORS allowed origins (comma-separated) |
| `SENTRY_DSN` | No | — | Sentry error tracking DSN |

### Database URL Formats

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@host:5432/dbname

# MySQL
DATABASE_URL=mysql+pymysql://user:password@host:3306/dbname

# SQLite (development only)
DATABASE_URL=sqlite:///./dev.db
```

### Module Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_STRATEGY` | `shared` (default) or `separate` |
| `MODULE_DATABASE_URL` | Used when `DATABASE_STRATEGY=separate` |
| `CORE_PLATFORM_URL` | Internal URL of core platform for inter-service calls |
| `MODULE_API_KEY` | Shared secret for module-to-platform authentication |

---

## Docker Compose Reference

```yaml
# docker-compose.yml (simplified)
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: buildify
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}

  core-platform:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    env_file:
      - backend/.env

  financial-module:
    build: ./modules/financial
    ports:
      - "9001:9001"
    depends_on:
      - postgres

  api-gateway:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./frontend:/usr/share/nginx/html
    depends_on:
      - core-platform
```

---

## Nginx API Gateway

**Config**: `infra/nginx/nginx.conf`

```nginx
server {
    listen 80;

    # Frontend static files
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Core platform API
    location /api/ {
        proxy_pass http://core-platform:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Financial module API (routed by path prefix)
    location /api/v1/financial/ {
        proxy_pass http://financial-module:9001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Deployment Environments

### Development

```bash
cp backend/.env.example backend/.env
# Edit .env: set DEBUG=true, use default passwords
docker-compose up -d
make migrate-pg
make seed
```

### Staging

1. Set `ENVIRONMENT=staging` and `DEBUG=false`
2. Use strong random values for `JWT_SECRET_KEY` and `REDIS_PASSWORD`
3. Set `ALLOWED_ORIGINS` to the staging domain
4. Optionally set `SENTRY_DSN` for error tracking

### Production

Follow the [Production Checklist](./PRODUCTION.md) before deploying.

Key differences:
- TLS termination at Nginx (or external load balancer)
- PostgreSQL and Redis on managed services (not in Docker)
- `DEBUG=false`, `ENVIRONMENT=production`
- Strong, unique secrets for all keys
- Prometheus + Grafana or external APM for monitoring

---

## Database Migrations

Migrations are managed by **Alembic** and must be run after each deployment.

```bash
# Apply all pending migrations (Docker)
docker-compose exec core-platform alembic upgrade head

# Apply locally
cd backend
alembic upgrade head

# Check current migration state
alembic current

# Roll back last migration
alembic downgrade -1
```

**Seeding** (initial setup only):
```bash
docker-compose exec core-platform python -m app.seeds.seed_org
docker-compose exec core-platform python -m app.seeds.seed_users
```

---

## Health Checks

| Endpoint | Service | Description |
|----------|---------|-------------|
| `GET /health` | Core Platform | API health status |
| `GET /health` | Financial Module | Module health status |
| `GET /` | Nginx | Static file serving |

---

## Logging

**Backend**: Structured JSON logs via `structlog` written to stdout.

```bash
# View all logs
docker-compose logs -f

# View core platform logs only
docker-compose logs -f core-platform

# View nginx access logs
docker-compose logs -f api-gateway
```

**Log levels** (set via `LOG_LEVEL` env var):
- `DEBUG` — verbose, development only
- `INFO` — normal operations (default)
- `WARNING` — unexpected but non-fatal
- `ERROR` — failures requiring attention

---

## Scaling

**Horizontal scaling** (multiple backend instances):

```bash
docker-compose up -d --scale core-platform=3
```

Requires:
- Nginx load balancer config with upstream pool
- Redis for shared session state (already implemented)
- Sticky sessions or stateless JWT (already implemented)

---

## Backup

### PostgreSQL

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres buildify > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U postgres buildify < backup.sql
```

### Redis

Redis is used for ephemeral data (token blacklist, sessions). No backup required unless you need to preserve active sessions across restarts.

---

## Related Documents

- [Production Checklist](./PRODUCTION.md)
- [Environment Configuration](./ENVIRONMENT.md)
- [Platform Overview](../platform/OVERVIEW.md)
- [Getting Started](../platform/GETTING_STARTED.md)
