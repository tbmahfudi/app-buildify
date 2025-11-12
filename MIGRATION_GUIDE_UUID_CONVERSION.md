# UUID Primary Key Migration Guide

## Overview

This guide covers the migration from Integer to UUID primary keys for Report, Dashboard, and Scheduler tables implemented in Phase 1.

**Migration Files:**
- PostgreSQL: `pg_r4_convert_primary_keys_to_uuid.py`
- MySQL: `mysql_r4_convert_primary_keys_to_uuid.py`

**Tables Affected:** 14 tables across 3 feature areas

---

## ⚠️ **CRITICAL WARNINGS**

### 🔴 **This is a BREAKING DATABASE CHANGE**

1. **Backup Required**: MUST backup database before running
2. **Downtime Required**: Plan for maintenance window
3. **No Rollback**: Migration intentionally does not support downgrade
4. **API Breaking Change**: All IDs change from integers to UUIDs

### 🔴 **Data Compatibility**

- **Existing Integer IDs** will be replaced with generated UUIDs
- **Foreign key relationships** will be automatically updated
- **API responses** will return UUIDs instead of integers
- **Frontend code** may need updates if it expects numeric IDs

---

## 📋 Pre-Migration Checklist

### 1. **Backup Database**

```bash
# PostgreSQL
pg_dump -h localhost -U your_user -d app_buildify > backup_$(date +%Y%m%d).sql

# MySQL
mysqldump -u your_user -p app_buildify > backup_$(date +%Y%m%d).sql
```

### 2. **Verify Current Database State**

```bash
cd backend

# Check migration status
alembic current

# Expected output should show you're on pg_s1 or mysql_security_policy_system
```

### 3. **Test on Development/Staging First**

**DO NOT** run this migration directly on production without testing!

### 4. **Review Affected Tables**

**Report Tables (5):**
- `report_definitions` - Primary key and related FKs
- `report_executions` - Primary key and FK to report_definitions
- `report_schedules` - Primary key and FK to report_definitions
- `report_templates` - Primary key only
- `report_cache` - Primary key and FK to report_definitions

**Dashboard Tables (6):**
- `dashboards` - Primary key and related FKs
- `dashboard_pages` - Primary key and FK to dashboards
- `dashboard_widgets` - Primary key, FK to dashboard_pages, FK to report_definitions
- `dashboard_shares` - Primary key and FK to dashboards
- `dashboard_snapshots` - Primary key and FK to dashboards
- `widget_data_cache` - Primary key and FK to dashboard_widgets

**Scheduler Tables (4):**
- `scheduler_configs` - Primary key and related FKs
- `scheduler_jobs` - Primary key and FK to scheduler_configs
- `scheduler_job_executions` - Primary key and FK to scheduler_jobs
- `scheduler_job_logs` - Primary key and FK to scheduler_job_executions

---

## 🚀 Running the Migration

### Development Environment

```bash
cd /home/user/app-buildify/backend

# Set your database connection
export DATABASE_URL="postgresql://user:password@localhost/app_buildify_dev"
# OR for MySQL:
# export DATABASE_URL="mysql+pymysql://user:password@localhost/app_buildify_dev"

# Run the migration
alembic upgrade head

# Verify migration completed
alembic current
# Should show: pg_r4 (head) or mysql_r4 (head)
```

### Staging Environment

```bash
# 1. Schedule maintenance window
# 2. Notify team/users
# 3. Create backup
# 4. Run migration with monitoring

cd /home/user/app-buildify/backend

# Run with verbose output
alembic upgrade head --sql > migration.sql  # Review SQL first
alembic upgrade head  # Execute

# Verify
alembic current
psql -d app_buildify_staging -c "SELECT id FROM report_definitions LIMIT 1"
# Should show UUID format
```

### Production Environment

```bash
# ⚠️ PRODUCTION DEPLOYMENT PROCESS ⚠️

# 1. Schedule maintenance window (2-4 hours recommended)
# 2. Communicate downtime to users
# 3. Enable maintenance mode
# 4. Stop application servers
# 5. Create full database backup
# 6. Verify backup integrity
# 7. Run migration
# 8. Verify data integrity
# 9. Update frontend if needed
# 10. Start application servers
# 11. Monitor for errors
# 12. Disable maintenance mode

cd /home/user/app-buildify/backend

# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -Fc app_buildify > "backup_prod_${TIMESTAMP}.dump"

# Run migration
alembic upgrade head 2>&1 | tee "migration_${TIMESTAMP}.log"

# Verify
alembic current
```

---

## 🔍 Post-Migration Verification

### 1. **Check Migration Status**

```bash
alembic current
# Expected: pg_r4 (head) or mysql_r4 (head)
```

### 2. **Verify UUID Format**

```sql
-- PostgreSQL
SELECT
    id,
    pg_typeof(id) as id_type
FROM report_definitions
LIMIT 5;

-- MySQL
SELECT
    id,
    LENGTH(id) as id_length  -- Should be 36
FROM report_definitions
LIMIT 5;
```

Expected output:
```
id                                   | id_type
-------------------------------------+---------
550e8400-e29b-41d4-a716-446655440000 | uuid
```

### 3. **Verify Foreign Key Relationships**

```sql
-- Check report executions link to valid reports
SELECT COUNT(*) as orphaned_executions
FROM report_executions re
LEFT JOIN report_definitions rd ON re.report_definition_id = rd.id
WHERE rd.id IS NULL;

-- Should return 0

-- Check dashboard widgets link to valid pages
SELECT COUNT(*) as orphaned_widgets
FROM dashboard_widgets dw
LEFT JOIN dashboard_pages dp ON dw.page_id = dp.id
WHERE dp.id IS NULL;

-- Should return 0

-- Check scheduler jobs link to valid configs
SELECT COUNT(*) as orphaned_jobs
FROM scheduler_jobs sj
LEFT JOIN scheduler_configs sc ON sj.config_id = sc.id
WHERE sc.id IS NULL;

-- Should return 0
```

### 4. **Test API Endpoints**

```bash
# Test report endpoint
curl -X GET http://localhost:8000/reports/definitions \
  -H "Authorization: Bearer YOUR_TOKEN"

# Verify response contains UUID-formatted IDs
# Expected: "id": "550e8400-e29b-41d4-a716-446655440000"
# NOT: "id": 123
```

### 5. **Check Application Logs**

```bash
# Monitor for UUID-related errors
tail -f /var/log/app-buildify/application.log | grep -i "uuid\|guid"
```

---

## 🐛 Troubleshooting

### Issue: Migration Fails with "constraint does not exist"

**Cause:** Foreign key constraint names may differ in your database

**Solution:**
```sql
-- List all constraints
SELECT conname, contype
FROM pg_constraint
WHERE conrelid = 'report_executions'::regclass;

-- Update migration file with actual constraint names
```

### Issue: "duplicate key value violates unique constraint"

**Cause:** Existing data conflicts with new UUIDs

**Solution:**
```sql
-- Check for duplicate records
SELECT report_definition_id, COUNT(*)
FROM report_executions
GROUP BY report_definition_id
HAVING COUNT(*) > 1;

-- Resolve duplicates before re-running migration
```

### Issue: Frontend shows "Invalid ID format" errors

**Cause:** Frontend code expects integer IDs

**Solution:**
Update frontend JavaScript/TypeScript:
```javascript
// Before
const reportId = parseInt(response.id);

// After
const reportId = response.id; // Already a UUID string
```

### Issue: Migration takes too long

**Cause:** Large dataset

**Solution:**
- Run during low-traffic period
- Consider pagination for very large tables
- Monitor database performance: `SELECT * FROM pg_stat_activity;`

---

## 🔄 Rollback Plan

### ⚠️ **Important: No Automatic Rollback**

The migration intentionally does **NOT** support automatic downgrade because:
1. UUID → Integer conversion risks data loss
2. Generated UUIDs can't map back to original integers
3. External systems may have stored new UUIDs

### Manual Rollback Process

If you **MUST** rollback:

1. **Stop Application**
2. **Restore from Backup**
   ```bash
   # PostgreSQL
   pg_restore -d app_buildify backup_20251112.dump

   # MySQL
   mysql -u user -p app_buildify < backup_20251112.sql
   ```
3. **Reset Migration State**
   ```bash
   alembic downgrade pg_s1  # or mysql_security_policy_system
   ```
4. **Revert Code Changes**
   ```bash
   git revert <commit-hash>
   ```

---

## 📊 Performance Considerations

### Migration Duration Estimates

| Records | PostgreSQL | MySQL |
|---------|-----------|-------|
| < 1K    | 1-2 min   | 2-3 min |
| 1K-10K  | 5-10 min  | 10-15 min |
| 10K-100K | 30-60 min | 45-90 min |
| > 100K  | 1-3 hours | 2-4 hours |

### Index Rebuild

Migration automatically rebuilds primary key indexes. Monitor with:

```sql
-- PostgreSQL
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE tablename IN ('report_definitions', 'dashboards', 'scheduler_configs');
```

---

## 🎯 Frontend Impact & Updates

### API Response Changes

**Before (Integer IDs):**
```json
{
  "id": 123,
  "name": "Sales Report",
  "report_definition_id": 45
}
```

**After (UUID IDs):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Sales Report",
  "report_definition_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
}
```

### Required Frontend Updates

#### 1. **Remove Integer Parsing**

```javascript
// ❌ REMOVE THIS
const reportId = parseInt(data.id);

// ✅ USE THIS
const reportId = data.id; // String UUID
```

#### 2. **Update URL Patterns**

```javascript
// ❌ OLD
const url = `/api/reports/${123}`;

// ✅ NEW
const url = `/api/reports/550e8400-e29b-41d4-a716-446655440000`;
```

#### 3. **Update Form Validation**

```javascript
// ❌ OLD
if (typeof reportId !== 'number') { ... }

// ✅ NEW
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
if (!UUID_REGEX.test(reportId)) { ... }
```

#### 4. **Update Storage Keys**

```javascript
// ❌ OLD
localStorage.setItem('selectedReport', 123);

// ✅ NEW
localStorage.setItem('selectedReport', '550e8400-e29b-41d4-a716-446655440000');
```

---

## ✅ Success Criteria

Migration is successful when:

- ✅ All 14 tables have UUID primary keys
- ✅ All foreign keys reference correct UUIDs
- ✅ No orphaned records exist
- ✅ API endpoints return UUID-formatted IDs
- ✅ Application starts without errors
- ✅ All CRUD operations work correctly
- ✅ Foreign key constraints are intact
- ✅ Indexes are rebuilt and functioning

---

## 📞 Support

If you encounter issues:

1. **Check logs**: `/var/log/app-buildify/`
2. **Review SQL**: `alembic upgrade head --sql`
3. **Database state**: `alembic current`
4. **Restore backup** if critical

**Emergency Rollback:**
```bash
# Stop app → Restore backup → Reset migration state → Start app
```

---

## 📝 Additional Notes

### Database-Specific Considerations

**PostgreSQL:**
- Uses native `UUID` type with `uuid-ossp` extension
- UUIDs stored as 16 bytes (efficient)
- Automatic UUID generation via `uuid_generate_v4()`

**MySQL:**
- Uses `CHAR(36)` to store UUIDs
- UUIDs stored as strings (36 bytes)
- UUID generation via `UUID()` function

### Future Migrations

All future tables should use UUID primary keys from the start to maintain consistency.

---

**Migration Created:** 2025-11-12
**Phase:** 1 - Critical Architecture Fixes
**Breaking Change:** Yes
**Requires Downtime:** Yes
