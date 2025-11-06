# Fixes Applied - 2025-11-06

This document describes the fixes applied to resolve multiple issues with the application.

## Issues Fixed

### 1. User Dropdown Menu Not Working in main.html

**Problem:** The user dropdown menu was not appearing when hovering or clicking on the user button in `/assets/templates/main.html`.

**Root Cause:** Bootstrap JS was interfering with Tailwind's CSS-only `group-hover:` functionality.

**Solution:** Added JavaScript event handlers to ensure the dropdown works with both hover and click interactions.

**Files Modified:**
- `frontend/assets/templates/main.html` - Added JavaScript dropdown handler

### 2. Users Table Showing "No Users Found"

**Problem:** The users table was displaying "no users found" even though the API endpoint `/api/v1/data/users/list` was returning data.

**Root Cause:** Mismatch between API response structure and frontend expectations:
- Backend returns `rows` field in `DataSearchResponse`
- Frontend was expecting `items` field

**Solution:** Updated frontend JavaScript to use the correct field name `data.rows` instead of `data.items`.

**Files Modified:**
- `frontend/assets/js/users.js` - Changed `data.items` to `data.rows`

### 3. Audit Page Error (Database Schema Mismatch)

**Problem:** Audit page was throwing a database error:
```
psycopg2.errors.UndefinedColumn: column audit_logs.company_id does not exist
```

**Root Cause:** The SQLAlchemy model for `AuditLog` defines columns (`company_id`, `branch_id`, `department_id`, `request_method`, `request_path`, `error_code`, `duration_ms`) that don't exist in the database table.

**Solution:** Created migration files to add the missing columns.

**Files Created:**
- `backend/app/alembic/versions/pg_add_audit_org_fields.py` - Alembic migration file
- `backend/fix_audit_logs_schema.sql` - Direct SQL migration file

### 4. Audit Enhanced JS Field Mapping

**Problem:** Similar to users table, audit logs were expecting wrong field name.

**Root Cause:**
- Backend returns `logs` field in `AuditLogListResponse`
- Frontend was expecting `items` field

**Solution:** Updated frontend JavaScript to use the correct field name `data.logs` instead of `data.items`.

**Files Modified:**
- `frontend/assets/js/audit-enhanced.js` - Changed `data.items` to `data.logs`

### 5. Alembic Multiple Heads Error

**Problem:** Running `alembic upgrade head` resulted in "multiple heads" error.

**Root Cause:** The migration history had multiple branches that weren't merged:
- `pg_add_audit_org_fields` (new audit columns)
- `pg_fix_dept_constraint` (department constraints)
- `pg_merge_heads` (earlier merge attempt)

**Solution:** Created a merge migration `pg_merge_all_heads` that combines all three branches into a single head.

**Files Created:**
- `backend/app/alembic/versions/pg_merge_all_heads.py` - Merge migration

## How to Apply Database Migration

You need to apply the database migration to add missing columns to the `audit_logs` table.

**Important:** The "multiple heads" error has been fixed with the `pg_merge_all_heads` migration. Running `alembic upgrade head` will now work correctly.

### Option 1: Using Alembic (Recommended)

```bash
# Enter the backend container
docker exec -it app_buildify_backend bash

# Run the migration (this will apply the merge and audit_logs changes)
cd /app
alembic upgrade head

# Exit container
exit
```

### Option 2: Using Direct SQL

If Alembic doesn't work, you can apply the SQL directly:

```bash
# Copy the SQL file to the PostgreSQL container
docker cp backend/fix_audit_logs_schema.sql app_buildify_postgresql:/tmp/

# Execute the SQL
docker exec -it app_buildify_postgresql psql -U appuser -d appdb -f /tmp/fix_audit_logs_schema.sql
```

### Option 3: Manual SQL Execution

Connect to your PostgreSQL database and run:

```sql
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS company_id UUID;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS branch_id UUID;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS department_id UUID;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS request_method VARCHAR(10);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS request_path VARCHAR(500);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS error_code VARCHAR(50);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS duration_ms VARCHAR(20);

CREATE INDEX IF NOT EXISTS ix_audit_logs_company_id ON audit_logs(company_id);
CREATE INDEX IF NOT EXISTS ix_audit_company_created ON audit_logs(company_id, created_at);
CREATE INDEX IF NOT EXISTS ix_audit_tenant_company ON audit_logs(tenant_id, company_id);
```

## Testing the Fixes

After applying all fixes:

1. **Restart the frontend container** (or just refresh the page since it's static files):
   ```bash
   docker-compose -f infra/docker-compose.dev.yml restart frontend
   ```

2. **Test the user dropdown**:
   - Visit `http://localhost:8080/assets/templates/main.html`
   - Hover over or click the user button in the top-right corner
   - The dropdown menu should appear

3. **Test the users table**:
   - Navigate to the Users page
   - The table should display user data instead of "no users found"

4. **Test the audit page**:
   - Navigate to the Audit page
   - No database errors should appear in the logs
   - Audit logs should display correctly

## Summary of Changes

- ✅ Fixed JavaScript import paths in main.html (from relative to absolute)
- ✅ Fixed user dropdown menu in main.html (added JavaScript handlers)
- ✅ Fixed users table data mapping (items → rows)
- ✅ Fixed audit logs data mapping (items → logs)
- ✅ Created migration to add missing audit_logs columns
- ✅ Fixed API response field mapping consistency

## Git Commits

All changes have been committed to the branch: `claude/update-main-template-011CUs1H4Ztnvd4MbpV9k7qs`

Commits:
1. `fix: Update JavaScript import paths to use absolute paths in main.html`
2. `fix: Correct API response field mapping in users and audit pages`
3. `fix: Add dropdown menu JavaScript handlers and audit_logs schema migration`
