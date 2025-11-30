-- ============================================================================
-- QUICK RBAC VERIFICATION
-- ============================================================================
-- Quick checks to verify all users have groups and are properly configured
-- ============================================================================

\echo '========================================='
\echo 'QUICK RBAC VERIFICATION'
\echo '========================================='
\echo ''

-- Check 1: All users in groups?
\echo '1. Users without groups (should be empty):'
SELECT
    u.id,
    u.email,
    u.full_name,
    t.name as tenant_name
FROM users u
LEFT JOIN user_groups ug ON u.id = ug.user_id
LEFT JOIN tenants t ON u.tenant_id = t.id
WHERE ug.user_id IS NULL
  AND u.deleted_at IS NULL
  AND u.is_superuser = false;

\echo ''

-- Check 2: Summary
\echo '2. Summary:'
SELECT
    (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL AND is_superuser = false) as total_users,
    (SELECT COUNT(DISTINCT user_id) FROM user_groups) as users_in_groups,
    (SELECT COUNT(*) FROM user_roles) as deprecated_user_roles,
    (SELECT COUNT(*) FROM groups WHERE is_active = true) as active_groups;

\echo ''

-- Check 3: Permission counts
\echo '3. Permissions per user (via groups):'
SELECT
    u.email,
    COUNT(DISTINCT g.id) as group_count,
    COUNT(DISTINCT r.id) as role_count,
    COUNT(DISTINCT p.id) as permission_count
FROM users u
LEFT JOIN user_groups ug ON u.id = ug.user_id
LEFT JOIN groups g ON ug.group_id = g.id
LEFT JOIN group_roles gr ON g.id = gr.group_id
LEFT JOIN roles r ON gr.role_id = r.id
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permissions p ON rp.permission_id = p.id
WHERE u.deleted_at IS NULL
  AND u.is_superuser = false
GROUP BY u.id, u.email
ORDER BY permission_count DESC, u.email;

\echo ''

-- Check 4: Safety check
\echo '4. SAFETY CHECK:'
SELECT
    CASE
        WHEN (SELECT COUNT(*) FROM users u
              LEFT JOIN user_groups ug ON u.id = ug.user_id
              WHERE u.deleted_at IS NULL
                AND u.is_superuser = false
                AND ug.user_id IS NULL) = 0
        THEN '✓ SAFE - All users are in groups'
        ELSE '✗ UNSAFE - Some users have no groups!'
    END as status;

\echo ''
\echo '========================================='
