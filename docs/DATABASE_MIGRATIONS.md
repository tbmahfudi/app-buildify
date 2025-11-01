# Database Migrations Guide

## Overview

This project uses Alembic for database migrations with support for multiple database backends: PostgreSQL, MySQL, and SQLite.

## Migration Structure

The migrations are organized into **separate branches** for each database type:

- **PostgreSQL**: Migrations prefixed with `pg_*`
- **MySQL**: Migrations prefixed with `mysql_*`
- **SQLite**: Migrations prefixed with `sqlite_*`

### Current Migration Heads

**PostgreSQL Branch:**
```
pg_0d5ad21b0f (create_org_pg)
  └─> pg_a1b2c3d4e5f6 (create_users_pg)
       ├─> pg_c5d6e7f8g9h0 (create_token_blacklist_pg) [HEAD]
       └─> pg_b2c3d4e5f6a7 (create_option_b_tables_pg)
            └─> pg_d8e9f0g1h2i3 (create_tenants_pg)
                 └─> pg_e9f0g1h2i3j4 (update_for_multi_tenant_pg)
                      └─> pg_f0g1h2i3j4k5 (create_rbac_tables_pg)
                           └─> pg_g1h2i3j4k5l6 (create_user_company_access_pg)
                                └─> pg_h2i3j4k5l6m7 (rename_metadata_to_extra_data_pg)
                                     └─> pg_m1n2o3p4q5r6 (create_module_system_pg) [HEAD]
```

**MySQL Branch:**
```
mysql_8c4ee763aa (create_org_mysql)
  └─> mysql_f6e5d4c3b2a1 (create_users_mysql)
       ├─> mysql_a7f6e5d4c3b2 (create_option_b_tables_mysql) [HEAD]
       └─> mysql_d7e8f9g0h1i2 (create_token_blacklist_mysql)
            └─> mysql_m1n2o3p4q5r6 (create_module_system_mysql) [HEAD]
```

## Running Migrations

### Using manage.sh (Recommended)

The `manage.sh` script handles migrations automatically:

```bash
# Complete setup (includes migrations)
./manage.sh setup postgres

# Run migrations only
./manage.sh migrate postgres
```

### Using Makefile

```bash
# Start Docker and run migrations
make docker-up

# Run migrations manually
make migrate-pg    # For PostgreSQL
make migrate-mysql # For MySQL
```

### Manual Alembic Commands

Inside the Docker container:

```bash
# Upgrade all branches to their latest heads
docker compose -f infra/docker-compose.dev.yml exec backend alembic upgrade heads

# Check current revision
docker compose -f infra/docker-compose.dev.yml exec backend alembic current

# View migration history
docker compose -f infra/docker-compose.dev.yml exec backend alembic history

# Show all heads
docker compose -f infra/docker-compose.dev.yml exec backend alembic heads
```

## Important Notes

### Why "heads" (plural)?

Always use `alembic upgrade heads` (with 's') instead of `alembic upgrade head` because this project has multiple migration branches. Using the singular form will fail with:

```
FAILED: Multiple head revisions are present for given argument 'head'
```

### Database-Specific Migrations

Each database type has its own migration branch to handle:
- Database-specific data types (UUID vs VARCHAR for IDs)
- Different SQL syntax requirements
- Database-specific features and constraints

### Switching Databases

To switch between databases:

1. Update `docker-compose.dev.yml` to use the desired database
2. Update the `SQLALCHEMY_DATABASE_URL` environment variable
3. Run migrations: `./manage.sh migrate [postgres|mysql]`
4. Seed data: `./manage.sh seed [postgres|mysql]`

## Troubleshooting

### Multiple Heads Error

If you see:
```
ERROR: Multiple head revisions are present
```

**Solution:** Use `alembic upgrade heads` (plural) instead of `head` (singular).

### Migration Already Applied

If Alembic says a migration is already applied:
```bash
# Check current state
docker compose -f infra/docker-compose.dev.yml exec backend alembic current

# View history
docker compose -f infra/docker-compose.dev.yml exec backend alembic history
```

### Reset Database

To completely reset the database:
```bash
./manage.sh db-reset postgres
```

This will:
1. Stop and remove all containers and volumes
2. Start fresh services
3. Run all migrations
4. Seed test data

## Creating New Migrations

When creating new migrations, use the appropriate prefix:

```bash
# For PostgreSQL
alembic revision -m "pg_description_of_change"

# For MySQL
alembic revision -m "mysql_description_of_change"

# For SQLite
alembic revision -m "sqlite_description_of_change"
```

Make sure to set the correct `down_revision` to maintain the migration chain.

## Migration Best Practices

1. **Always test migrations** on a local database first
2. **Backup production data** before running migrations
3. **Use transactions** for migration safety
4. **Keep migrations small** and focused on one change
5. **Never modify** existing migration files after they've been applied
6. **Test both upgrade and downgrade** paths
7. **Document breaking changes** in migration commit messages

## See Also

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Project README](../README.md)
- [Architecture Guide](./ARCHITECTURE.md)
