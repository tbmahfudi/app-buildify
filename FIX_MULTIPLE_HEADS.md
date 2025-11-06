# Fix Alembic Multiple Heads Error

## Problem
Running `alembic upgrade head` results in:
```
Multiple head revisions are present for given argument 'head'
```

## Root Cause
The Docker container hasn't detected the new merge migration file (`pg_merge_all_heads.py`) yet, so Alembic still sees the old multiple heads.

## Solution

### Option 1: Restart Backend and Run Migration (Recommended)

```bash
# From the project root directory
cd /home/user/app-buildify

# Restart the backend container to reload migration files
docker-compose -f infra/docker-compose.dev.yml restart backend

# Wait a few seconds for the container to start
sleep 5

# Enter the backend container
docker exec -it app_buildify_backend bash

# Inside the container, check what Alembic sees
cd /app
alembic heads

# You should now see only ONE head: pg_merge_all_heads
# If you still see multiple heads, exit and try Option 2

# Run the migration
alembic upgrade head

# Exit the container
exit
```

### Option 2: Full Container Restart

If Option 1 doesn't work, do a full restart:

```bash
cd /home/user/app-buildify/infra

# Stop all containers
docker-compose -f docker-compose.dev.yml down

# Start all containers
docker-compose -f docker-compose.dev.yml up -d

# Wait for containers to be ready
sleep 10

# Enter the backend container
docker exec -it app_buildify_backend bash

# Inside the container
cd /app
alembic upgrade head

# Exit
exit
```

### Option 3: Manual SQL Migration (Bypass Alembic)

If Alembic continues to have issues, you can apply the schema changes directly:

```bash
# Copy the SQL file to the PostgreSQL container
docker cp backend/fix_audit_logs_schema.sql app_buildify_postgresql:/tmp/

# Execute the SQL directly
docker exec -it app_buildify_postgresql psql -U appuser -d appdb -f /tmp/fix_audit_logs_schema.sql

# Verify the columns were added
docker exec -it app_buildify_postgresql psql -U appuser -d appdb -c "\d audit_logs"
```

After running Option 3, you still need to update the Alembic version table:

```bash
# Connect to the database
docker exec -it app_buildify_postgresql psql -U appuser -d appdb

# Inside psql, update the alembic_version table to mark migrations as applied
# First, check current version
SELECT * FROM alembic_version;

# Update to the merge head (only if you manually applied the SQL)
UPDATE alembic_version SET version_num = 'pg_merge_all_heads';

# Exit psql
\q
```

## Verification

After applying the migration, verify the changes:

```bash
# Check that audit_logs has the new columns
docker exec -it app_buildify_postgresql psql -U appuser -d appdb -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'audit_logs'
ORDER BY column_name;
"

# You should see columns like:
# - company_id (uuid)
# - branch_id (uuid)
# - department_id (uuid)
# - request_method (character varying)
# - request_path (character varying)
# - error_code (character varying)
# - duration_ms (character varying)
```

## What This Migration Does

The merge migration (`pg_merge_all_heads`) combines three separate migration branches:
1. `pg_fix_dept_constraint` - Department constraints
2. `pg_add_audit_org_fields` - Audit log organizational fields
3. `pg_merge_heads` - Earlier merge of token and branch migrations

The actual schema change (`pg_add_audit_org_fields`) adds these columns to `audit_logs`:
- `company_id`, `branch_id`, `department_id` - For organizational context
- `request_method`, `request_path` - For HTTP request tracking
- `error_code`, `duration_ms` - For error tracking and performance monitoring

## Troubleshooting

### If you still see multiple heads:

1. **Check the migration file exists in the container:**
   ```bash
   docker exec -it app_buildify_backend ls -la /app/app/alembic/versions/pg_merge_all_heads.py
   ```

   If the file doesn't exist, the volume mount might not be working. Try:
   ```bash
   docker cp backend/app/alembic/versions/pg_merge_all_heads.py app_buildify_backend:/app/app/alembic/versions/
   ```

2. **Check Alembic can see the migration:**
   ```bash
   docker exec -it app_buildify_backend bash -c "cd /app && python -c \"from app.alembic import versions; import os; print([f for f in os.listdir('app/alembic/versions') if 'merge' in f])\""
   ```

3. **Clear Alembic cache (if it exists):**
   ```bash
   docker exec -it app_buildify_backend bash -c "cd /app && find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; alembic upgrade head"
   ```

### If migration fails with "relation already exists":

Some migrations might have already been partially applied. Check with:
```bash
docker exec -it app_buildify_postgresql psql -U appuser -d appdb -c "\d audit_logs"
```

If the columns already exist, you can stamp the database with the head:
```bash
docker exec -it app_buildify_backend bash -c "cd /app && alembic stamp head"
```

## After Successful Migration

Once the migration succeeds:
1. Restart the application: `docker-compose -f infra/docker-compose.dev.yml restart`
2. Test the audit page: `http://localhost:8080/#audit`
3. Test the users page: `http://localhost:8080/#users`

All database errors should be resolved!
