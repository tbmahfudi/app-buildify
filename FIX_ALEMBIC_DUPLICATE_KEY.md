# Fix: Alembic Duplicate Key Error

## Error Message
```
ERROR:  duplicate key value violates unique constraint "alembic_version_pkc"
DETAIL:  Key (version_num)=(pg_merge_all_heads) already exists.
```

## What This Means
The `alembic_version` table already has the `pg_merge_all_heads` version recorded, but Alembic is trying to insert it again. This typically happens when a migration partially succeeded or the version table got into an inconsistent state.

## Quick Fix (Automated)

Run the automated fix script:

```bash
cd /home/user/app-buildify/backend
chmod +x fix_alembic_duplicate.sh
./fix_alembic_duplicate.sh
```

This script will:
1. Check the current version state
2. Clear the alembic_version table
3. Stamp it with the merge head
4. Try to upgrade again

## Manual Fix (Step by Step)

If the automated script doesn't work, follow these steps:

### Step 1: Check Current State

```bash
# Check what version is recorded in the database
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "SELECT * FROM alembic_version;"

# Check what Alembic thinks
docker exec app_buildify_backend bash -c "cd /app && alembic current"

# Check available heads
docker exec app_buildify_backend bash -c "cd /app && alembic heads"
```

### Step 2: Clear and Re-Stamp

```bash
# Clear the version table
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "DELETE FROM alembic_version;"

# Stamp with the merge head (tells Alembic this migration is done)
docker exec app_buildify_backend bash -c "cd /app && alembic stamp pg_merge_all_heads"

# Verify
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "SELECT * FROM alembic_version;"
```

You should now see:
```
 version_num
--------------------
 pg_merge_all_heads
(1 row)
```

### Step 3: Apply Audit Logs Schema Changes

Now the merge migration is recorded, but we still need to apply the actual schema changes for audit_logs. Try:

```bash
docker exec app_buildify_backend bash -c "cd /app && alembic upgrade head"
```

If this still fails, go to Step 4.

### Step 4: Manual SQL Application (Bypass Alembic)

If Alembic continues to have issues, apply the schema changes directly:

```bash
# Copy SQL file to PostgreSQL container
docker cp backend/fix_audit_logs_schema.sql app_buildify_postgresql:/tmp/

# Execute the SQL
docker exec app_buildify_postgresql psql -U appuser -d appdb -f /tmp/fix_audit_logs_schema.sql

# Verify columns were added
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "\d audit_logs"
```

You should see these new columns:
- company_id (uuid)
- branch_id (uuid)
- department_id (uuid)
- request_method (character varying)
- request_path (character varying)
- error_code (character varying)
- duration_ms (character varying)

### Step 5: Update Alembic Version Table

After manually applying the SQL, tell Alembic the migrations are done:

```bash
# Mark all migrations as applied
docker exec app_buildify_backend bash -c "cd /app && alembic stamp head"

# Verify
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "SELECT * FROM alembic_version;"
```

## Understanding the Issue

The `alembic_version` table tracks which migrations have been applied. It has a primary key on `version_num`, so each version can only appear once. The error occurred because:

1. A migration ran (or partially ran) and inserted `pg_merge_all_heads` into the table
2. Then when you tried to run the migration again, it tried to insert the same version again
3. PostgreSQL rejected it because of the unique constraint

The fix is to either:
- Use `alembic stamp` to mark migrations as applied without running them
- Clear the version table and stamp with the correct version
- Manually apply SQL changes and then stamp

## Verification

After applying the fix, verify everything works:

```bash
# Check Alembic is happy
docker exec app_buildify_backend bash -c "cd /app && alembic current"

# Should show something like:
# pg_add_audit_org_fields (head)

# Check audit_logs table has new columns
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'audit_logs'
AND column_name IN ('company_id', 'branch_id', 'department_id', 'request_method', 'request_path', 'error_code', 'duration_ms')
ORDER BY column_name;
"

# Restart the application
docker-compose -f infra/docker-compose.dev.yml restart

# Test the audit page - should work without errors
# http://localhost:8080/#audit
```

## If Nothing Works

As a last resort, you can reset the entire migration system:

```bash
# WARNING: This will lose track of what migrations have been applied
# Only use if you're sure the database schema is correct

# Clear the version table
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "DELETE FROM alembic_version;"

# Manually apply the audit_logs changes
docker cp backend/fix_audit_logs_schema.sql app_buildify_postgresql:/tmp/
docker exec app_buildify_postgresql psql -U appuser -d appdb -f /tmp/fix_audit_logs_schema.sql

# Stamp with head (marks all migrations as done)
docker exec app_buildify_backend bash -c "cd /app && alembic stamp head"
```

## Prevention

To avoid this in the future:
- Don't interrupt migrations mid-execution
- Don't manually edit the `alembic_version` table unless you know what you're doing
- Use `alembic stamp` instead of manual SQL when you need to mark migrations as applied
- Always backup your database before running migrations in production

## Need Help?

If you're still stuck, check:
1. Docker containers are running: `docker ps`
2. Backend logs: `docker logs app_buildify_backend`
3. Database logs: `docker logs app_buildify_postgresql`
4. That the migration files exist in the container:
   ```bash
   docker exec app_buildify_backend ls -la /app/app/alembic/versions/ | grep merge
   ```
