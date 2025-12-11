-- ============================================================
-- Enable Financial Module for TECHSTART and FASHIONHUB
-- ============================================================

-- Step 1: Register Financial Module in module_registry
-- ============================================================
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
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    version = EXCLUDED.version,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    is_installed = true;

-- Verify registration
SELECT id, name, display_name, version, is_installed
FROM module_registry
WHERE name = 'financial';

-- Step 2: Enable for TECHSTART Tenant
-- ============================================================
WITH tenant_info AS (
    SELECT id as tenant_id FROM tenants WHERE code = 'TECHSTART'
),
module_info AS (
    SELECT id as module_id FROM module_registry WHERE name = 'financial'
)
INSERT INTO tenant_modules (
    id,
    tenant_id,
    module_id,
    is_enabled,
    is_configured,
    configuration,
    enabled_at,
    created_at
)
SELECT
    gen_random_uuid(),
    t.tenant_id,
    m.module_id,
    true,
    true,
    '{"default_currency": "USD", "fiscal_year_start": "01-01", "enable_multi_currency": false, "tax_rate": 0, "invoice_prefix": "TS"}'::jsonb,
    NOW(),
    NOW()
FROM tenant_info t, module_info m
ON CONFLICT (tenant_id, module_id)
DO UPDATE SET
    is_enabled = true,
    enabled_at = NOW();

-- Verify TECHSTART enablement
SELECT
    t.code as tenant_code,
    t.name as tenant_name,
    m.name as module_name,
    tm.is_enabled,
    tm.enabled_at
FROM tenant_modules tm
JOIN tenants t ON t.id = tm.tenant_id
JOIN module_registry m ON m.id = tm.module_id
WHERE t.code = 'TECHSTART'
AND m.name = 'financial';

-- Step 3: Enable for FASHIONHUB Tenant
-- ============================================================
WITH tenant_info AS (
    SELECT id as tenant_id FROM tenants WHERE code = 'FASHIONHUB'
),
module_info AS (
    SELECT id as module_id FROM module_registry WHERE name = 'financial'
)
INSERT INTO tenant_modules (
    id,
    tenant_id,
    module_id,
    is_enabled,
    is_configured,
    configuration,
    enabled_at,
    created_at
)
SELECT
    gen_random_uuid(),
    t.tenant_id,
    m.module_id,
    true,
    true,
    '{"default_currency": "USD", "fiscal_year_start": "01-01", "enable_multi_currency": false, "tax_rate": 0, "invoice_prefix": "FH"}'::jsonb,
    NOW(),
    NOW()
FROM tenant_info t, module_info m
ON CONFLICT (tenant_id, module_id)
DO UPDATE SET
    is_enabled = true,
    enabled_at = NOW();

-- Verify FASHIONHUB enablement
SELECT
    t.code as tenant_code,
    t.name as tenant_name,
    m.name as module_name,
    tm.is_enabled,
    tm.enabled_at
FROM tenant_modules tm
JOIN tenants t ON t.id = tm.tenant_id
JOIN module_registry m ON m.id = tm.module_id
WHERE t.code = 'FASHIONHUB'
AND m.name = 'financial';

-- Final Verification: List all enabled modules for both tenants
-- ============================================================
SELECT
    t.code as tenant_code,
    t.name as tenant_name,
    m.name as module_name,
    m.display_name,
    tm.is_enabled,
    tm.enabled_at,
    tm.configuration
FROM tenant_modules tm
JOIN tenants t ON t.id = tm.tenant_id
JOIN module_registry m ON m.id = tm.module_id
WHERE t.code IN ('TECHSTART', 'FASHIONHUB')
AND m.name = 'financial'
ORDER BY t.code;

-- ============================================================
-- SUCCESS! Financial module enabled for TECHSTART and FASHIONHUB
-- ============================================================
