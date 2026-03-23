# Enable Financial Module for Frontend

## Problem
The financial menu is not showing in the frontend because **the module is not enabled for your tenant** in the backend database.

## Solution

The financial module needs to be registered in the `module_registry` table and enabled in the `tenant_modules` table for each tenant that should have access to it.

---

## Method 1: Using the Enable Script (Recommended)

### If Using Docker:

```bash
# Enable for TECHSTART
docker exec -it buildify-core python enable_financial_module.py TECHSTART

# Enable for FASHIONHUB
docker exec -it buildify-core python enable_financial_module.py FASHIONHUB

# Enable for both at once
docker exec -it buildify-core python enable_financial_module.py TECHSTART FASHIONHUB
```

### If Running Backend Locally:

```bash
cd backend
python enable_financial_module.py TECHSTART FASHIONHUB
```

---

## Method 2: Manual Database Insertion

If you have direct database access, you can run these SQL commands:

### Step 1: Register the Financial Module

```sql
-- Register financial module in module_registry
INSERT INTO module_registry (
    id,
    name,
    display_name,
    version,
    description,
    category,
    is_installed,
    is_enabled,
    is_core,
    status,
    installed_at,
    created_at
) VALUES (
    gen_random_uuid(),
    'financial',
    'Financial Management',
    '1.0.0',
    'Financial management user interface',
    'business',
    true,
    false,
    false,
    'available',
    NOW(),
    NOW()
) ON CONFLICT (name) DO NOTHING;
```

### Step 2: Enable for TECHSTART Tenant

```sql
-- Get tenant and module IDs
WITH tenant_info AS (
    SELECT id as tenant_id FROM tenants WHERE code = 'TECHSTART'
),
module_info AS (
    SELECT id as module_id FROM module_registry WHERE name = 'financial'
)
-- Enable module for tenant
INSERT INTO tenant_modules (
    id,
    tenant_id,
    module_id,
    is_enabled,
    configuration,
    enabled_at,
    created_at
)
SELECT
    gen_random_uuid(),
    t.tenant_id,
    m.module_id,
    true,
    '{"default_currency": "USD", "fiscal_year_start": "01-01", "invoice_prefix": "TS"}'::jsonb,
    NOW(),
    NOW()
FROM tenant_info t, module_info m
ON CONFLICT (tenant_id, module_id)
DO UPDATE SET
    is_enabled = true,
    enabled_at = NOW();
```

### Step 3: Enable for FASHIONHUB Tenant

```sql
-- Get tenant and module IDs
WITH tenant_info AS (
    SELECT id as tenant_id FROM tenants WHERE code = 'FASHIONHUB'
),
module_info AS (
    SELECT id as module_id FROM module_registry WHERE name = 'financial'
)
-- Enable module for tenant
INSERT INTO tenant_modules (
    id,
    tenant_id,
    module_id,
    is_enabled,
    configuration,
    enabled_at,
    created_at
)
SELECT
    gen_random_uuid(),
    t.tenant_id,
    m.module_id,
    true,
    '{"default_currency": "USD", "fiscal_year_start": "01-01", "invoice_prefix": "FH"}'::jsonb,
    NOW(),
    NOW()
FROM tenant_info t, module_info m
ON CONFLICT (tenant_id, module_id)
DO UPDATE SET
    is_enabled = true,
    enabled_at = NOW();
```

---

## Method 3: Using Backend API (If Backend is Running)

If your backend is running, you can use the REST API:

### Step 1: Login and Get Token

```bash
# Login as admin user
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ceo@techstart.com",
    "password": "password123"
  }'

# Save the access_token from response
```

### Step 2: Enable Module via API

```bash
# Enable financial module for tenant
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "financial",
    "configuration": {
      "default_currency": "USD",
      "fiscal_year_start": "01-01",
      "enable_multi_currency": false,
      "tax_rate": 0,
      "invoice_prefix": "INV"
    }
  }'
```

---

## Verification

### Check if Module is Enabled

**Option 1: Via API**
```bash
curl "http://localhost:8000/api/v1/modules/enabled/names" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Should return: ["financial"]
```

**Option 2: Via Database**
```sql
-- Check enabled modules for a tenant
SELECT
    t.code as tenant_code,
    t.name as tenant_name,
    m.name as module_name,
    tm.is_enabled,
    tm.enabled_at
FROM tenant_modules tm
JOIN tenants t ON t.id = tm.tenant_id
JOIN module_registry m ON m.id = tm.module_id
WHERE t.code IN ('TECHSTART', 'FASHIONHUB')
AND m.name = 'financial';
```

**Option 3: Via Frontend Debug Tool**

Open in browser: `http://localhost:8080/debug-financial-module.html`

This tool will:
- Check authentication status
- Verify backend module enablement
- Check frontend module loading
- Verify permissions
- Display diagnostic information

---

## After Enabling

### 1. Restart Backend (if running)

```bash
# If using Docker
docker-compose restart core-platform

# If running locally
# Stop and restart your backend server
```

### 2. Clear Browser Cache & Reload Frontend

```bash
# In browser
1. Open Developer Console (F12)
2. Right-click refresh button → "Empty Cache and Hard Reload"
```

### 3. Login and Test

```bash
# Open: http://localhost:8080
# Login with:
#   - ceo@techstart.com / password123
#   OR
#   - ceo@fashionhub.com / password123

# Navigate to: #/financial/dashboard
```

---

## Troubleshooting

### Module Still Not Showing?

**Check Backend Logs**:
```bash
docker-compose logs -f core-platform
# Look for module loading errors
```

**Check Browser Console**:
```
F12 → Console Tab
# Look for JavaScript errors related to module loading
```

**Verify Database**:
```sql
-- Check if module is registered
SELECT * FROM module_registry WHERE name = 'financial';

-- Check if enabled for tenant
SELECT
    tm.*,
    t.code as tenant_code,
    m.name as module_name
FROM tenant_modules tm
JOIN tenants t ON t.id = tm.tenant_id
JOIN module_registry m ON m.id = tm.module_id
WHERE t.code = 'TECHSTART'
AND m.name = 'financial';
```

### Permission Issues?

The user needs the permission: `financial:accounts:read:company`

Check user permissions:
```sql
-- Check user permissions (if using RBAC)
SELECT
    u.email,
    p.name as permission
FROM users u
JOIN user_roles ur ON ur.user_id = u.id
JOIN role_permissions rp ON rp.role_id = ur.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE u.email = 'ceo@techstart.com'
AND p.name LIKE 'financial:%';
```

---

## Summary

1. **Enable module** using the script or SQL
2. **Restart backend** server
3. **Clear browser cache** and reload
4. **Login** with tenant user
5. **See financial menu** appear! 🎉

The financial module should now be visible in the sidebar menu under "Financial" with sub-items for Dashboard, Accounts, Invoices, Payments, and Reports.
