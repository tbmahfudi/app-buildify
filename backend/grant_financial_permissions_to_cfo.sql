-- Grant all financial permissions to CFO users
-- RBAC Structure: Users → Groups → Roles → Permissions

-- Step 1: Check what roles the CFO has
SELECT
    t.code as tenant,
    u.email,
    r.code as role_code,
    r.name as role_name,
    'via group: ' || g.name as source
FROM users u
JOIN tenants t ON t.id = u.tenant_id
LEFT JOIN user_groups ug ON ug.user_id = u.id
LEFT JOIN groups g ON g.id = ug.group_id
LEFT JOIN group_roles gr ON gr.group_id = g.id
LEFT JOIN roles r ON r.id = gr.role_id
WHERE u.email LIKE 'cfo@%'
UNION
SELECT
    t.code as tenant,
    u.email,
    r.code as role_code,
    r.name as role_name,
    'direct' as source
FROM users u
JOIN tenants t ON t.id = u.tenant_id
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN roles r ON r.id = ur.role_id
WHERE u.email LIKE 'cfo@%'
ORDER BY tenant, email;

-- Step 2: Check current financial permissions for CFO roles
SELECT
    t.code as tenant,
    u.email,
    r.code as role_code,
    COUNT(DISTINCT p.code) FILTER (WHERE p.code LIKE 'financial:%') as financial_perms_count,
    STRING_AGG(DISTINCT p.code, ', ' ORDER BY p.code) FILTER (WHERE p.code LIKE 'financial:%') as financial_permissions
FROM users u
JOIN tenants t ON t.id = u.tenant_id
LEFT JOIN user_groups ug ON ug.user_id = u.id
LEFT JOIN groups g ON g.id = ug.group_id
LEFT JOIN group_roles gr ON gr.group_id = g.id
LEFT JOIN roles r ON r.id = gr.role_id
LEFT JOIN role_permissions rp ON rp.role_id = r.id
LEFT JOIN permissions p ON p.id = rp.permission_id
WHERE u.email = 'cfo@fashionhub.com'
GROUP BY t.code, u.email, r.code
ORDER BY t.code, u.email;

-- Step 3: Grant missing financial permissions to CFO roles
WITH cfo_roles AS (
    -- Get all roles for CFO (via groups)
    SELECT DISTINCT r.id as role_id, r.code as role_code, t.code as tenant_code
    FROM users u
    JOIN tenants t ON t.id = u.tenant_id
    JOIN user_groups ug ON ug.user_id = u.id
    JOIN groups g ON g.id = ug.group_id
    JOIN group_roles gr ON gr.group_id = g.id
    JOIN roles r ON r.id = gr.role_id
    WHERE u.email = 'cfo@fashionhub.com'
    UNION
    -- Get all direct roles for CFO
    SELECT DISTINCT r.id as role_id, r.code as role_code, t.code as tenant_code
    FROM users u
    JOIN tenants t ON t.id = u.tenant_id
    JOIN user_roles ur ON ur.user_id = u.id
    JOIN roles r ON r.id = ur.role_id
    WHERE u.email = 'cfo@fashionhub.com'
),
financial_permissions AS (
    SELECT id, code, name
    FROM permissions
    WHERE code IN (
        'financial:accounts:read:company',
        'financial:customers:read:company',
        'financial:invoices:read:company',
        'financial:payments:read:company',
        'financial:journal:read:company',
        'financial:reports:read:company'
    )
)
-- Grant all 6 financial read permissions to CFO roles
INSERT INTO role_permissions (id, role_id, permission_id, created_at)
SELECT
    gen_random_uuid(),
    cr.role_id,
    fp.id,
    NOW()
FROM cfo_roles cr
CROSS JOIN financial_permissions fp
WHERE NOT EXISTS (
    SELECT 1 FROM role_permissions rp
    WHERE rp.role_id = cr.role_id
    AND rp.permission_id = fp.id
)
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Step 4: Verify the grants
SELECT
    t.code as tenant,
    u.email,
    r.code as role_code,
    COUNT(DISTINCT p.code) FILTER (WHERE p.code LIKE 'financial:%') as financial_perms_count,
    STRING_AGG(DISTINCT p.code, ', ' ORDER BY p.code) FILTER (WHERE p.code LIKE 'financial:%') as financial_permissions
FROM users u
JOIN tenants t ON t.id = u.tenant_id
LEFT JOIN user_groups ug ON ug.user_id = u.id
LEFT JOIN groups g ON g.id = ug.group_id
LEFT JOIN group_roles gr ON gr.group_id = g.id
LEFT JOIN roles r ON r.id = gr.role_id
LEFT JOIN role_permissions rp ON rp.role_id = r.id
LEFT JOIN permissions p ON p.id = rp.permission_id
WHERE u.email = 'cfo@fashionhub.com'
GROUP BY t.code, u.email, r.code
ORDER BY t.code, u.email;

-- Summary
SELECT '✅ Granted all 6 financial permissions to CFO roles' as status;
