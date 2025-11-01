# Testing the Migration Fix

## What Was Fixed

Two critical migration issues were resolved:

### Issue 1: Mixed Database Migrations
`alembic upgrade heads` was trying to run ALL migration branches (SQLite, MySQL, PostgreSQL) simultaneously, causing:
- SQLite migrations to run on PostgreSQL databases
- Foreign key errors like "relation 'tenants' does not exist"
- Migration failures during db-reset

**Solution**: Updated `manage.sh` to target the correct migration head for each database type.

### Issue 2: Invalid Column Rename Migration
The `pg_h2i3j4k5l6m7` migration was trying to rename `metadata` to `extra_data`, but:
- Tables were created with `extra_data` column from the start
- The `metadata` column never existed in fresh PostgreSQL databases
- This caused "column 'metadata' does not exist" errors

**Solution**: Updated the migration to check if columns exist before attempting renames, making it safe for both fresh and existing databases.

## How to Test

### 1. Test Fresh Database Setup

```bash
# Complete reset and setup
./manage.sh db-reset postgres
```

**Expected output:**
```
[INFO] Resetting database...
[INFO] Starting services with postgres...
[INFO] Waiting for database to be ready...
[INFO] Running database migrations...
[INFO] Running online migrations for: postgresql
[INFO] Upgrading to postgres head: pg_m1n2o3p4q5r6
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> pg_0d5ad21b0f, Create organization tables (PostgreSQL)
INFO  [alembic.runtime.migration] Running upgrade pg_0d5ad21b0f -> pg_a1b2c3d4e5f6, Create users table (PostgreSQL)
...
[INFO] Migrations completed successfully
[INFO] Seeding database...
[INFO] Database reset completed successfully
```

### 2. Test Migration Only

```bash
# Start services
./manage.sh start postgres

# Wait for database to be ready
sleep 10

# Run migrations
./manage.sh migrate postgres
```

**Expected output:**
```
[INFO] Running database migrations...
[INFO] Running online migrations for: postgresql
[INFO] Upgrading to postgres head: pg_m1n2o3p4q5r6
[INFO] Migrations completed successfully
```

### 3. Verify Tables Exist

```bash
# Open database shell
./manage.sh db-shell

# Inside psql, list tables
\dt

# Check tenants table specifically
\d tenants

# Exit
\q
```

**Expected**: You should see the `tenants` table and all other tables listed.

### 4. Test Application Access

After migrations complete:

1. **Backend API**: http://localhost:8000
2. **API Docs**: http://localhost:8000/docs
3. **Frontend**: http://localhost:8080

Try creating a test request in the Swagger UI to verify the database is working.

## What Should NOT Happen

❌ **No longer seeing:**
- `Running upgrade  -> 001_sqlite_complete` (on PostgreSQL)
- `Running upgrade sqlite_...` messages (on PostgreSQL)
- `relation "tenants" does not exist` errors
- `column "metadata" does not exist` errors
- Mixed migration branches running together

✅ **Should see:**
- Only `pg_*` migrations running for PostgreSQL
- Only `mysql_*` migrations running for MySQL
- Clean, sequential migration execution
- Successful table creation
- For the metadata rename migration (pg_h2i3j4k5l6m7), you'll see:
  * `Column 'tenants.extra_data' already exists, skipping rename`
  * `Column 'companies.extra_data' already exists, skipping rename`
  * Similar messages for branches, departments, and users tables

## Migration Heads Reference

The correct migration heads for each database:

- **PostgreSQL**: `pg_m1n2o3p4q5r6` (Create module system)
- **MySQL**: `mysql_m1n2o3p4q5r6` (Create module system)
- **SQLite**: `sqlite_m1n2o3p4q5r6` (Create module system)

## Troubleshooting

### If you still see errors:

1. **Check Docker services are running:**
   ```bash
   ./manage.sh status
   ```

2. **Check logs:**
   ```bash
   ./manage.sh logs backend
   ./manage.sh logs postgres
   ```

3. **Verify database type:**
   ```bash
   docker compose -f infra/docker-compose.dev.yml exec backend env | grep SQLALCHEMY_DATABASE_URL
   ```

4. **Manual migration check:**
   ```bash
   docker compose -f infra/docker-compose.dev.yml exec backend alembic current
   docker compose -f infra/docker-compose.dev.yml exec backend alembic heads
   ```

### If migrations are already partially applied:

```bash
# Check current migration state
docker compose -f infra/docker-compose.dev.yml exec backend alembic current

# If stuck with mixed branches, reset:
./manage.sh db-reset postgres
```

## For MySQL

To test with MySQL:

1. **Uncomment MySQL service** in `infra/docker-compose.dev.yml`
2. **Comment out PostgreSQL** backend dependency
3. **Update backend environment** to use MySQL URL
4. **Run tests:**
   ```bash
   ./manage.sh setup mysql
   ```

## For SQLite (Non-Docker)

```bash
cd backend

# Ensure .env has SQLite URL
echo "SQLALCHEMY_DATABASE_URL=sqlite:///./app.db" > .env

# Run migrations
python run_migrations.py

# Or use alembic directly
alembic upgrade sqlite_m1n2o3p4q5r6
```

## Success Criteria

✅ `./manage.sh db-reset postgres` completes without errors
✅ All PostgreSQL migrations run in correct order
✅ `tenants` table and all other tables are created
✅ No `column "metadata" does not exist` errors
✅ Metadata rename migration skips gracefully (columns already correct)
✅ Seeding completes successfully
✅ Backend API is accessible and functional
✅ No SQLite or MySQL migrations run on PostgreSQL

## Related Files Changed

### Fix #1: Database-Specific Migration Heads
- `manage.sh`: Updated `run_migrations()` function (line 133-164)
- `backend/app/alembic/env.py`: Simplified `run_migrations_online()` function

### Fix #2: Column Rename Migration Safety
- `backend/app/alembic/versions/pg_h2i3j4k5l6m7_rename_metadata_to_extra_data_pg.py`:
  * Added `column_exists()` helper function
  * Added existence checks before column renames
  * Made migration safe for fresh and existing databases
