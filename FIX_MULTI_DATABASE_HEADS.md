# Fix: Multiple Database Type Heads in Alembic

## The Problem

Your project supports multiple database types (PostgreSQL, MySQL, SQLite), and each has its own migration branch:

```
Multiple heads are present for given argument 'head':
  - mysql_a7f6e5d4c3b2
  - mysql_m1n2o3p4q5r6
  - pg_merge_all_heads (PostgreSQL)
  - sqlite_m1n2o3p4q5r6
```

When you run `alembic upgrade head`, Alembic doesn't know which database type you want to upgrade because there are multiple "heads" (one per database type).

## Quick Fix (Automated)

```bash
cd /home/user/app-buildify/backend
./fix_multi_db_heads.sh
```

This will upgrade only the PostgreSQL migrations.

## Manual Fix (Recommended)

Since you're using **PostgreSQL**, target only the PostgreSQL migrations:

### Method 1: Upgrade to PostgreSQL Head Directly

```bash
# Clear the version table
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "DELETE FROM alembic_version;"

# Upgrade ONLY PostgreSQL migrations (not head, but the specific pg revision)
docker exec app_buildify_backend bash -c "cd /app && alembic upgrade pg_merge_all_heads"

# Verify
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "SELECT * FROM alembic_version;"
```

### Method 2: Use Branch-Specific Upgrade

If your migrations have branch labels, you can use:

```bash
# Upgrade PostgreSQL branch only
docker exec app_buildify_backend bash -c "cd /app && alembic upgrade postgresql@head"
```

### Method 3: Bypass Alembic (Most Reliable)

If Alembic continues to cause issues, apply the SQL directly:

```bash
# 1. Apply the schema changes manually
docker cp backend/fix_audit_logs_schema.sql app_buildify_postgresql:/tmp/
docker exec app_buildify_postgresql psql -U appuser -d appdb -f /tmp/fix_audit_logs_schema.sql

# 2. Clear and set the version to pg_merge_all_heads
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "DELETE FROM alembic_version;"
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "INSERT INTO alembic_version (version_num) VALUES ('pg_merge_all_heads');"

# 3. Verify
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "SELECT * FROM alembic_version;"
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "\d audit_logs" | grep -E "company_id|branch_id|department_id"
```

## Why This Happens

This is actually a **correct** Alembic setup for multi-database support:

1. Your project has separate migration branches for PostgreSQL, MySQL, and SQLite
2. Each branch has its own "head" (latest migration)
3. Alembic doesn't know which database you're using when you run `alembic upgrade head`

The solution is to either:
- Target the specific database head (e.g., `pg_merge_all_heads` for PostgreSQL)
- Use branch labels if configured (e.g., `postgresql@head`)
- Manually apply SQL and stamp the version

## Verify the Fix

After running the fix:

```bash
# 1. Check alembic version
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "SELECT * FROM alembic_version;"
# Should show: pg_merge_all_heads (or a PostgreSQL revision)

# 2. Verify audit_logs table has new columns
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'audit_logs'
AND column_name IN ('company_id', 'branch_id', 'department_id', 'request_method', 'request_path', 'error_code', 'duration_ms')
ORDER BY column_name;
"

# Should show 7 rows with these columns

# 3. Restart the application
cd /home/user/app-buildify
docker-compose -f infra/docker-compose.dev.yml restart

# 4. Test the application
# - Audit page: http://localhost:8080/#audit (should work without errors)
# - Users page: http://localhost:8080/#users (should display users)
```

## Understanding the Migration Structure

Your project has this structure:

```
migrations/
├── pg_*.py       (PostgreSQL migrations)
├── mysql_*.py    (MySQL migrations)
└── sqlite_*.py   (SQLite migrations)
```

Each database type has its own migration chain. This is useful for:
- Supporting multiple databases in development/production
- Database-specific features or syntax
- Testing with different databases

## Future Migrations

When running migrations in the future, always specify the database type:

```bash
# For PostgreSQL (what you're using)
docker exec app_buildify_backend bash -c "cd /app && alembic upgrade pg_merge_all_heads"

# Or if branch labels are set up
docker exec app_buildify_backend bash -c "cd /app && alembic upgrade postgresql@head"

# Check current version
docker exec app_buildify_backend bash -c "cd /app && alembic current"

# List all heads
docker exec app_buildify_backend bash -c "cd /app && alembic heads"
```

## Clean Up (Optional)

If you're ONLY using PostgreSQL and want to simplify the migration setup, you could:

1. Remove MySQL and SQLite migration files (but keep this optional for future flexibility)
2. Configure Alembic to use branch labels
3. Or just always target the specific PostgreSQL head

However, keeping all database migrations is fine and doesn't cause problems as long as you target the correct one.

## Troubleshooting

### Still seeing "Multiple heads" error?

Make sure you're not running `alembic upgrade head`. Instead use:
- `alembic upgrade pg_merge_all_heads` (specific revision)
- `alembic upgrade postgresql@head` (if branch labels are configured)

### Columns still missing from audit_logs?

Apply the SQL directly:
```bash
docker cp backend/fix_audit_logs_schema.sql app_buildify_postgresql:/tmp/
docker exec app_buildify_postgresql psql -U appuser -d appdb -f /tmp/fix_audit_logs_schema.sql
```

### Version table shows wrong version?

Clear and set it manually:
```bash
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "DELETE FROM alembic_version;"
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "INSERT INTO alembic_version (version_num) VALUES ('pg_merge_all_heads');"
```

## Summary

This is not an error in your setup - it's a feature! Your project supports multiple databases. You just need to tell Alembic which database you're using by targeting the specific head for PostgreSQL instead of the generic "head" command.

**The fix:** Use `alembic upgrade pg_merge_all_heads` instead of `alembic upgrade head`.
