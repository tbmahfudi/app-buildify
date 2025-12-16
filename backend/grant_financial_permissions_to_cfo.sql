-- Grant all financial permissions to CFO and finance-related groups
-- This ensures CFOs can see all financial menu items

-- First, let's see what we have
SELECT
    t.code as tenant,
    u.email,
    g.name as group_name,
    COUNT(DISTINCT p.code) FILTER (WHERE p.code LIKE 'financial:%') as financial_perms_count
FROM users u
JOIN tenants t ON t.id = u.tenant_id
LEFT JOIN user_groups ug ON ug.user_id = u.id
LEFT JOIN groups g ON g.id = ug.group_id
LEFT JOIN group_permissions gp ON gp.group_id = g.id
LEFT JOIN permissions p ON p.id = gp.permission_id
WHERE u.email LIKE 'cfo@%'
GROUP BY t.code, u.email, g.name
ORDER BY t.code, u.email;

-- Get CFO groups for FASHIONHUB
WITH cfo_groups AS (
    SELECT DISTINCT g.id as group_id, g.name as group_name, t.code as tenant_code
    FROM users u
    JOIN tenants t ON t.id = u.tenant_id
    JOIN user_groups ug ON ug.user_id = u.id
    JOIN groups g ON g.id = ug.group_id
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
-- Grant all financial read permissions to CFO groups
INSERT INTO group_permissions (id, group_id, permission_id, created_at)
SELECT
    gen_random_uuid(),
    cg.group_id,
    fp.id,
    NOW()
FROM cfo_groups cg
CROSS JOIN financial_permissions fp
WHERE NOT EXISTS (
    SELECT 1 FROM group_permissions gp
    WHERE gp.group_id = cg.group_id
    AND gp.permission_id = fp.id
)
ON CONFLICT DO NOTHING;

-- Verify the grants
SELECT
    t.code as tenant,
    u.email,
    g.name as group_name,
    STRING_AGG(p.code, ', ' ORDER BY p.code) as permissions
FROM users u
JOIN tenants t ON t.id = u.tenant_id
JOIN user_groups ug ON ug.user_id = u.id
JOIN groups g ON g.id = ug.group_id
JOIN group_permissions gp ON gp.group_id = g.id
JOIN permissions p ON p.id = gp.permission_id
WHERE u.email = 'cfo@fashionhub.com'
  AND p.code LIKE 'financial:%'
GROUP BY t.code, u.email, g.name
ORDER BY t.code, u.email;
