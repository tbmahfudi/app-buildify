# Deployment Guide

## Overview

App-Buildify is containerized with Docker and orchestrated via Docker Compose. The stack includes a PostgreSQL database, a core FastAPI backend, the financial module backend, and an Nginx frontend server.

---

## Services

| Service | Container Name | Image | Port | Description |
|---------|---------------|-------|------|-------------|
| `postgres` | `app_buildify_postgresql` | postgres:15-alpine | 5432 | Primary PostgreSQL database |
| `backend` | `app_buildify_backend` | Built from `backend/Dockerfile` | 8000 | Core FastAPI platform |
| `financial-module` | `app_buildify_financial` | Built from `modules/financial/backend/Dockerfile` | 9001 | Financial module API |
| `frontend` | `app_buildify_frontend` | nginx:1.27-alpine | 8080 → 80 | SPA + static files + API proxy |

> **Note**: Redis is optional and not included in the default dev compose. Add it if you need token revocation blacklisting or caching.

---

## Infrastructure Files

```
infra/
├── docker-compose.dev.yml     # Development compose (used by Makefile)
├── docker-compose.prod.yml    # Production compose skeleton
└── nginx/
    ├── app.conf               # Frontend Nginx config (SPA + API proxy)
    └── nginx.conf             # Standalone API gateway config (multi-upstream)
```

---

## Nginx Routing (`infra/nginx/app.conf`)

The `app.conf` is mounted into the frontend Nginx container and handles all routing:

| Pattern | Destination | Notes |
|---------|------------|-------|
| `/api/v1/financial/*` | `http://financial-module:9001` | Financial module API |
| `/api/v1/hr/*`, `/api/v1/clinic/*` | `http://<module>-module:9001` | Other module APIs (pattern-based) |
| `/api/` | `http://backend:8000` | Core platform API |
| `/modules/<name>/<file>` | `/usr/share/nginx/modules/<name>/frontend/<file>` | Module frontend assets |
| Static files (`*.js`, `*.css`, `*.png`...) | `/usr/share/nginx/html` | Cached 1 day |
| `/*` (fallback) | `/index.html` | SPA catch-all |

---

## Development Setup

### 1. Configure environment

```bash
cp backend/.env.example backend/.env
```

Key settings in `backend/.env` — see actual variable names:

```env
SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://appuser:apppass@postgres:5432/appdb
SECRET_KEY=dev-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MIN=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:3000
```

### 2. Start all services

```bash
docker-compose -f infra/docker-compose.dev.yml up -d
# or via Makefile:
make docker-up
```

### 3. Run migrations

```bash
# Core platform migrations
docker-compose -f infra/docker-compose.dev.yml exec backend alembic upgrade head

# or with make:
make migrate-pg
```

### 4. Seed initial data

```bash
make seed
```

### 5. Access the application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8080 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Financial Module | http://localhost:9001 |

---

## Docker Compose — Dev Reference

**File**: `infra/docker-compose.dev.yml`

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: apppass
      POSTGRES_DB: appdb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d appdb"]
      interval: 5s

  backend:
    build: ../backend
    ports: ["8000:8000"]
    environment:
      SQLALCHEMY_DATABASE_URL: postgresql+psycopg2://appuser:apppass@postgres:5432/appdb
      SECRET_KEY: dev-secret-key
      ACCESS_TOKEN_EXPIRE_MIN: 30
      REFRESH_TOKEN_EXPIRE_DAYS: 7
      ALLOWED_ORIGINS: http://localhost:8080,http://localhost:3000
    volumes:
      - ../backend:/app       # hot reload
      - ../frontend:/frontend:ro
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  financial-module:
    build: ../modules/financial/backend
    ports: ["9001:9001"]
    environment:
      DATABASE_STRATEGY: shared
      DATABASE_URL: postgresql://appuser:apppass@postgres:5432/appdb
      EVENT_BUS_CONNECTION_STRING: postgresql://appuser:apppass@postgres:5432/appdb
      MODULE_NAME: financial
      MODULE_VERSION: 1.0.0
      MODULE_PORT: 9001
    volumes:
      - ../modules/financial/backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload

  frontend:
    image: nginx:1.27-alpine
    ports: ["8080:80"]
    volumes:
      - ../frontend:/usr/share/nginx/html:ro
      - ../modules:/usr/share/nginx/modules:ro
      - ../infra/nginx/app.conf:/etc/nginx/conf.d/default.conf:ro
```

---

## Production Setup

**File**: `infra/docker-compose.prod.yml`

The production compose is intentionally minimal — it references pre-built images:

```yaml
services:
  backend:
    image: ghcr.io/YOUR_GH_OWNER/app-backend:${TAG}
    env_file: .env
    restart: unless-stopped

  frontend:
    image: ghcr.io/YOUR_GH_OWNER/app-frontend:${TAG}
    restart: unless-stopped

  nginx:
    image: nginx:1.27-alpine
    volumes:
      - ./nginx/app.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on: [backend, frontend]
    ports: ["80:80"]
    restart: unless-stopped
```

> Update `YOUR_GH_OWNER` to your actual GitHub organization/user before use.

Build and push images to your container registry, then deploy with:

```bash
TAG=v1.2.3 docker-compose -f infra/docker-compose.prod.yml up -d
```

---

## Database Migrations

Managed by **Alembic**.

```bash
# Apply all pending migrations
docker-compose exec backend alembic upgrade head

# Roll back one migration
docker-compose exec backend alembic downgrade -1

# Check current state
docker-compose exec backend alembic current

# Generate migration from model changes
docker-compose exec backend alembic revision --autogenerate -m "add new table"
```

---

## Environment Variables

See [Environment Variables Reference](./ENVIRONMENT.md) for the complete list.

**Critical variables that differ from defaults:**

| Variable | Dev Value | Production |
|----------|-----------|-----------|
| `SQLALCHEMY_DATABASE_URL` | `postgresql+psycopg2://appuser:apppass@postgres:5432/appdb` | Managed DB URL + `?sslmode=require` |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Strong 64-char random key |
| `ALLOWED_ORIGINS` | `http://localhost:8080` | Your production domain(s) |
| `DEBUG` | `true` | `false` |

---

## Health Checks

| URL | Service | Notes |
|-----|---------|-------|
| `GET http://localhost/health` | Nginx | Returns `healthy` (200) |
| `GET http://localhost:8000/health` | Backend | API health |
| `GET http://localhost:9001/health` | Financial module | Module health |

---

## Logging

All containers write structured logs to stdout.

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f financial-module
docker-compose logs -f frontend
```

---

## Adding a New Module

1. Create your module under `modules/<name>/`
2. Add the module service to `infra/docker-compose.dev.yml`
3. Add the module's API route pattern to `infra/nginx/app.conf`:
   ```nginx
   location ~ ^/api/(v[0-9]+)/(financial|hr|clinic|<your-module>)/(.+)$ {
       proxy_pass http://$2-module:9001/api/$1/$2/$3$is_args$args;
       ...
   }
   ```
4. Serve module frontend assets via the `/modules/<name>/` path
5. Register the module via `POST /api/v1/modules/register`

See [Module Development Guide](../archive/MODULE_DEVELOPMENT_GUIDE.md) for full details.

---

## Backup

### PostgreSQL

```bash
# Backup
docker-compose exec postgres pg_dump -U appuser appdb > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U appuser appdb < backup.sql
```

---

## Related Documents

- [Production Checklist](./PRODUCTION.md)
- [Environment Variables](./ENVIRONMENT.md)
- [Module Development Guide](../archive/MODULE_DEVELOPMENT_GUIDE.md)
