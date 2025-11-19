# Fix Tenant Company Counts

## Problem
The tenant `current_companies` counter was not being updated when companies were created/deleted. This has been fixed in the backend code, but existing data needs to be recalculated.

## Solution

### Option 1: Run Python Script (Recommended)

```bash
cd backend
python scripts/recalculate_tenant_usage.py
```

This will:
- Count all companies for each tenant
- Count all users for each tenant
- Update the tenant usage counters

### Option 2: Direct SQL (PostgreSQL)

Connect to your PostgreSQL database and run:

```sql
-- Update current_companies count for all tenants
UPDATE tenants t
SET current_companies = (
    SELECT COUNT(*)
    FROM companies c
    WHERE c.tenant_id = t.id
    AND c.deleted_at IS NULL
);

-- Update current_users count for all tenants (optional)
UPDATE tenants t
SET current_users = (
    SELECT COUNT(*)
    FROM users u
    WHERE u.tenant_id = t.id
    AND u.deleted_at IS NULL
);

-- Verify the results
SELECT
    code,
    name,
    current_companies,
    max_companies,
    current_users,
    max_users
FROM tenants
ORDER BY name;
```

### Option 3: Via Docker (if using Docker)

```bash
# Find the PostgreSQL container
docker ps | grep postgres

# Connect to PostgreSQL
docker exec -it <postgres-container-id> psql -U <db-user> -d <db-name>

# Then run the SQL commands from Option 2
```

## What Was Fixed

1. **Backend Code** (`backend/app/routers/org.py`):
   - Added automatic update of `current_companies` when creating a company
   - Added automatic update of `current_companies` when deleting a company
   - Properly counts only non-deleted companies

2. **Utility Script** (`backend/scripts/recalculate_tenant_usage.py`):
   - Recalculates all tenant usage statistics
   - Can be run anytime to sync counters with actual data

## After Running the Fix

1. Restart your backend server (if needed)
2. Refresh the tenant list in the UI
3. The company counts should now display correctly
4. New companies will automatically update the counter
