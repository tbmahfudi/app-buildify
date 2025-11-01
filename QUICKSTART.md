# Quick Start Guide - Fix "tenants table does not exist"

> **✅ Migration fix has been applied!** The issue with mixed database migrations has been resolved. The commands below should now work correctly.

## TL;DR - Fastest Solution

```bash
# Make sure you're in the project root directory
./manage.sh setup postgres
```

That's it! This command will:
1. Build Docker images
2. Start all services (database, backend, frontend)
3. **Run migrations** (creates tenants table and all other tables - PostgreSQL migrations only)
4. Seed the database with test data

---

## If Services Are Already Running

If you already have Docker services running and just need to run migrations:

```bash
./manage.sh migrate postgres
```

---

## Step-by-Step Guide

### 1. First Time Setup

```bash
# Build and start everything from scratch
./manage.sh setup postgres
```

This runs the complete setup. Wait for it to finish, then access:
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:8080

### 2. If You Get "tenants does not exist" Error

**If services are running:**
```bash
./manage.sh migrate postgres
```

**If services are not running:**
```bash
# Start services first
./manage.sh start postgres

# Wait for services to be ready (about 10 seconds)
sleep 10

# Run migrations
./manage.sh migrate postgres
```

### 3. Start Over (Reset Everything)

```bash
# This will wipe all data and start fresh
./manage.sh db-reset
```

---

## Common Commands

```bash
# Start services
./manage.sh start postgres

# Stop services
./manage.sh stop

# View logs
./manage.sh logs

# View specific service logs
./manage.sh logs backend
./manage.sh logs postgres

# Check status
./manage.sh status

# Run migrations
./manage.sh migrate postgres

# Seed database with test data
./manage.sh seed

# Open backend shell
./manage.sh shell

# Open database shell
./manage.sh db-shell

# Help
./manage.sh help
```

---

## Using MySQL Instead of PostgreSQL

Replace `postgres` with `mysql` in any command:

```bash
./manage.sh setup mysql
./manage.sh migrate mysql
./manage.sh start mysql
```

**Note:** You'll need to uncomment the MySQL service in `infra/docker-compose.dev.yml`

---

## Troubleshooting

### "Services are not running"
```bash
./manage.sh start postgres
sleep 10
./manage.sh migrate postgres
```

### "Docker command not found"
Install Docker Desktop or Docker Engine for your operating system.

### "Permission denied" on manage.sh
```bash
chmod +x manage.sh
```

### Check Service Health
```bash
./manage.sh status
```

This shows which services are up and responding.

### View Backend Logs
```bash
./manage.sh logs backend
```

Look for any error messages that might indicate what's wrong.

### Database Connection Issues

Check if the database is running:
```bash
docker compose -f infra/docker-compose.dev.yml ps
```

You should see `postgres` service with status "Up (healthy)"

---

## Without Docker

If you're not using Docker, see [FIX_TENANTS_TABLE.md](FIX_TENANTS_TABLE.md) for alternative methods using:
- `python run_migrations.py`
- `./fix-db.sh`
- Direct Alembic commands

---

## What Gets Created

The migrations create these tables:
- ✓ `tenants` - Multi-tenant organization management
- ✓ `companies` - Companies within tenants
- ✓ `branches` - Branch locations
- ✓ `departments` - Department organization
- ✓ `users` - User accounts
- ✓ `roles` - RBAC roles
- ✓ `permissions` - RBAC permissions
- ✓ `groups` - User groups
- ✓ And more...

---

## Next Steps After Migration

1. **Access API Documentation**: http://localhost:8000/docs
2. **Test the API**: Use the interactive Swagger UI
3. **Login**: Use seeded test users (see `backend/SEED_DATA.md`)
4. **Develop**: Backend code auto-reloads on changes

---

## Need More Help?

- **Detailed troubleshooting**: See [FIX_TENANTS_TABLE.md](FIX_TENANTS_TABLE.md)
- **Backend documentation**: See [backend/README.md](backend/README.md)
- **All manage.sh commands**: Run `./manage.sh help`
