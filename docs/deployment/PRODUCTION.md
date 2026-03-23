# Production Checklist

Use this checklist before deploying to production.

---

## Security

- [ ] **JWT_SECRET_KEY** is a strong random secret (32+ characters), not the default
- [ ] **Database password** is strong and unique — not `postgres`/`password`
- [ ] **Redis password** is set via `requirepass` in redis config
- [ ] **Default admin password** has been changed after first login
- [ ] **DEBUG=false** in all production `.env` files
- [ ] **ENVIRONMENT=production** is set
- [ ] **ALLOWED_ORIGINS** is restricted to your actual domain(s)
- [ ] **TLS/HTTPS** is enabled at Nginx or your load balancer
- [ ] **Sentry DSN** is configured for error tracking
- [ ] `.env` files are **not committed to git** (in `.gitignore`)
- [ ] **Database SSL** is enabled: append `?sslmode=require` to `DATABASE_URL`
- [ ] **Redis TLS** is configured if using managed Redis
- [ ] **Content Security Policy** headers are reviewed and tightened

---

## Database

- [ ] Migrations are up to date: `alembic upgrade head`
- [ ] Initial seed data has been applied (once)
- [ ] Database backups are scheduled (minimum daily)
- [ ] A restore procedure has been tested
- [ ] Connection pooling is configured (PgBouncer or SQLAlchemy pool settings)
- [ ] Database is on a managed service (RDS, Cloud SQL, etc.) or properly secured VM

---

## Infrastructure

- [ ] All services have restart policies (`restart: unless-stopped`)
- [ ] Health check endpoints are reachable
- [ ] Resource limits are set for containers (CPU, memory)
- [ ] Volumes for PostgreSQL data are on persistent storage
- [ ] Log rotation is configured (Docker `--log-opt max-size`)
- [ ] Monitoring/alerting is set up (Prometheus + Grafana, or external APM)

---

## Application

- [ ] Rate limiting values are appropriate for your expected traffic
- [ ] Session timeout and password policies are configured per your security requirements
- [ ] All enabled modules are tested in staging before production
- [ ] Module API keys are rotated from development defaults
- [ ] Scheduler jobs are validated and set to appropriate schedules

---

## Networking

- [ ] Firewall rules allow only necessary ports (80, 443 to internet; 8000, 9001, 5432, 6379 internal only)
- [ ] Internal service communication is on a private Docker network
- [ ] Nginx proxy timeouts are tuned for your largest API responses
- [ ] HTTP → HTTPS redirect is in place

---

## Deployment Process

- [ ] Images are built from a clean git state (no uncommitted changes)
- [ ] Image tags are versioned (not just `latest`)
- [ ] Deployment is tested in staging with production-equivalent data
- [ ] A rollback plan exists (previous image tags are retained)
- [ ] Migrations have been tested for rollback (`alembic downgrade`)
- [ ] Zero-downtime deployment strategy is in place if required

---

## Environment Variables Checklist

```env
# Required - must be set
DATABASE_URL=postgresql://user:strong-password@host:5432/buildify?sslmode=require
REDIS_URL=redis://:redis-password@redis-host:6379
JWT_SECRET_KEY=<64-char-random-string>

# Required - must be changed from defaults
DEBUG=false
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com

# Recommended
SENTRY_DSN=https://<key>@sentry.io/<project>
LOG_LEVEL=INFO
RATE_LIMIT=100/minute

# Module (if using financial module)
MODULE_API_KEY=<strong-random-key>
CORE_PLATFORM_URL=http://core-platform:8000
```

---

## Generating Secure Secrets

```bash
# JWT_SECRET_KEY (64 chars)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Redis password (32 chars)
python3 -c "import secrets; print(secrets.token_hex(16))"

# Module API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Smoke Tests After Deployment

1. `GET /health` returns `200` on all services
2. Login with admin credentials succeeds
3. API `GET /api/v1/users` returns data with valid token
4. Frontend loads without console errors
5. A data model can be created and a record saved
6. Audit log shows the operations above
