-- ============================================================================
-- RBAC Cleanup and Verification Script
-- ============================================================================
-- This script helps you:
-- 1. Verify all users are properly assigned to groups
-- 2. Compare old vs new permission assignments
-- 3. Safely remove deprecated user_roles data
--
-- Usage:
--   psql -U appuser -d appdb < cleanup_rbac.sql
--   OR copy/paste sections into your DB client
-- ============================================================================

\echo '============================================================================'
\echo 'RBAC CLEANUP AND VERIFICATION'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- SECTION 1: CURRENT STATE ANALYSIS
-- ============================================================================

\echo '1. CURRENT STATE ANALYSIS'
\echo '=========================='
\echo ''

\echo '1.1 Total Users vs Users in Groups:'
SELECT
    (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) as total_users,
    (SELECT COUNT(DISTINCT user_id) FROM user_groups) as users_in_groups,
    (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) -
    (SELECT COUNT(DISTINCT user_id) FROM user_groups) as users_without_groups;

\echo ''
\echo '1.2 Users NOT in any group (these need attention!):'
SELECT
    u.id,
    u.email,
    u.full_name,
    u.is_superuser,
    t.name as tenant_name
FROM users u
LEFT JOIN user_groups ug ON u.id = ug.user_id
LEFT JOIN tenants t ON u.tenant_id = t.id
WHERE ug.user_id IS NULL
  AND u.deleted_at IS NULL
  AND u.is_superuser = false  -- Superusers don't need groups
ORDER BY u.email;

\echo ''
\echo '1.3 Deprecated user_roles records count:'
SELECT COUNT(*) as deprecated_user_roles_count FROM user_roles;

\echo ''
\echo '1.4 Which users have deprecated direct role assignments:'
SELECT
    u.email,
    u.full_name,
    r.code as role_code,
    r.name as role_name,
    ur.created_at as assigned_date
FROM user_roles ur
JOIN users u ON ur.user_id = u.id
JOIN roles r ON ur.role_id = r.id
WHERE u.deleted_at IS NULL
ORDER BY u.email, r.name;

\echo ''
\echo '============================================================================'
\echo 'SECTION 2: GROUP-BASED PERMISSIONS VERIFICATION'
\echo '============================================================================'
\echo ''

\echo '2.1 Users with their groups and roles (through groups):'
SELECT
    u.email,
    u.full_name,
    g.name as group_name,
    r.code as role_code,
    r.name as role_name
FROM users u
LEFT JOIN user_groups ug ON u.id = ug.user_id
LEFT JOIN groups g ON ug.group_id = g.id
LEFT JOIN group_roles gr ON g.id = gr.group_id
LEFT JOIN roles r ON gr.role_id = r.id
WHERE u.deleted_at IS NULL
  AND u.is_superuser = false
ORDER BY u.email, g.name, r.name;

\echo ''
\echo '2.2 Permission count per user (via groups only):'
SELECT
    u.email,
    u.full_name,
    COUNT(DISTINCT p.id) as permission_count,
    STRING_AGG(DISTINCT r.code, ', ' ORDER BY r.code) as roles_via_groups
FROM users u
LEFT JOIN user_groups ug ON u.id = ug.user_id
LEFT JOIN groups g ON ug.group_id = g.id
LEFT JOIN group_roles gr ON g.id = gr.group_id
LEFT JOIN roles r ON gr.role_id = r.id
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permissions p ON rp.permission_id = p.id
WHERE u.deleted_at IS NULL
  AND u.is_superuser = false
GROUP BY u.id, u.email, u.full_name
ORDER BY u.email;

\echo ''
\echo '2.3 Groups with their members and roles:'
SELECT
    g.name as group_name,
    g.code as group_code,
    COUNT(DISTINCT ug.user_id) as member_count,
    STRING_AGG(DISTINCT r.code, ', ' ORDER BY r.code) as assigned_roles
FROM groups g
LEFT JOIN user_groups ug ON g.id = ug.group_id
LEFT JOIN group_roles gr ON g.id = gr.group_id
LEFT JOIN roles r ON gr.role_id = r.id
WHERE g.is_active = true
GROUP BY g.id, g.name, g.code
ORDER BY member_count DESC, g.name;

\echo ''
\echo '============================================================================'
\echo 'SECTION 3: COMPARISON - OLD vs NEW'
\echo '============================================================================'
\echo ''

\echo '3.1 Permission comparison for each user:'
\echo '   (Old = via user_roles, New = via groups)'
WITH old_permissions AS (
    -- Permissions from deprecated user_roles
    SELECT
        u.id as user_id,
        u.email,
        p.code as permission_code
    FROM users u
    JOIN user_roles ur ON u.id = ur.user_id
    JOIN roles r ON ur.role_id = r.id
    JOIN role_permissions rp ON r.id = rp.role_id
    JOIN permissions p ON rp.permission_id = p.id
    WHERE u.deleted_at IS NULL
),
new_permissions AS (
    -- Permissions from groups
    SELECT
        u.id as user_id,
        u.email,
        p.code as permission_code
    FROM users u
    JOIN user_groups ug ON u.id = ug.user_id
    JOIN groups g ON ug.group_id = g.id
    JOIN group_roles gr ON g.id = gr.group_id
    JOIN roles r ON gr.role_id = r.id
    JOIN role_permissions rp ON r.id = rp.role_id
    JOIN permissions p ON rp.permission_id = p.id
    WHERE u.deleted_at IS NULL
)
SELECT
    u.email,
    (SELECT COUNT(DISTINCT permission_code) FROM old_permissions op WHERE op.user_id = u.id) as old_perms,
    (SELECT COUNT(DISTINCT permission_code) FROM new_permissions np WHERE np.user_id = u.id) as new_perms,
    (SELECT COUNT(DISTINCT permission_code) FROM new_permissions np WHERE np.user_id = u.id) -
    (SELECT COUNT(DISTINCT permission_code) FROM old_permissions op WHERE op.user_id = u.id) as difference
FROM users u
WHERE u.deleted_at IS NULL
  AND u.is_superuser = false
  AND (EXISTS (SELECT 1 FROM old_permissions op WHERE op.user_id = u.id)
       OR EXISTS (SELECT 1 FROM new_permissions np WHERE np.user_id = u.id))
ORDER BY u.email;

\echo ''
\echo '3.2 Users who would LOSE permissions if we only use groups:'
\echo '   (These users need group assignments before cleanup!)'
WITH old_permissions AS (
    SELECT DISTINCT u.id as user_id, u.email, p.code
    FROM users u
    JOIN user_roles ur ON u.id = ur.user_id
    JOIN roles r ON ur.role_id = r.id
    JOIN role_permissions rp ON r.id = rp.role_id
    JOIN permissions p ON rp.permission_id = p.id
    WHERE u.deleted_at IS NULL
),
new_permissions AS (
    SELECT DISTINCT u.id as user_id, u.email, p.code
    FROM users u
    JOIN user_groups ug ON u.id = ug.user_id
    JOIN groups g ON ug.group_id = g.id
    JOIN group_roles gr ON g.id = gr.group_id
    JOIN roles r ON gr.role_id = r.id
    JOIN role_permissions rp ON r.id = rp.role_id
    JOIN permissions p ON rp.permission_id = p.id
    WHERE u.deleted_at IS NULL
)
SELECT
    op.email,
    COUNT(*) as permissions_that_would_be_lost,
    STRING_AGG(op.code, ', ' ORDER BY op.code) as lost_permissions
FROM old_permissions op
LEFT JOIN new_permissions np ON op.user_id = np.user_id AND op.code = np.code
WHERE np.code IS NULL
GROUP BY op.user_id, op.email
HAVING COUNT(*) > 0
ORDER BY permissions_that_would_be_lost DESC;

\echo ''
\echo '============================================================================'
\echo 'SECTION 4: PRE-CLEANUP CHECKLIST'
\echo '============================================================================'
\echo ''

\echo '4.1 Summary before cleanup:'
SELECT
    'Total Users' as metric,
    COUNT(*) as count
FROM users
WHERE deleted_at IS NULL AND is_superuser = false
UNION ALL
SELECT
    'Users in Groups',
    COUNT(DISTINCT user_id)
FROM user_groups
UNION ALL
SELECT
    'Users with Direct Roles (deprecated)',
    COUNT(DISTINCT user_id)
FROM user_roles
UNION ALL
SELECT
    'Total Groups',
    COUNT(*)
FROM groups
WHERE is_active = true
UNION ALL
SELECT
    'Total Group-Role Assignments',
    COUNT(*)
FROM group_roles
UNION ALL
SELECT
    'Deprecated user_roles Records',
    COUNT(*)
FROM user_roles;

\echo ''
\echo '4.2 SAFETY CHECK - Users without groups (MUST BE ZERO!):'
SELECT
    CASE
        WHEN COUNT(*) = 0 THEN '✓ SAFE TO PROCEED - All users are in groups'
        ELSE '✗ DANGER - ' || COUNT(*) || ' users have NO groups! Assign them first!'
    END as safety_status
FROM users u
LEFT JOIN user_groups ug ON u.id = ug.user_id
WHERE u.deleted_at IS NULL
  AND u.is_superuser = false
  AND ug.user_id IS NULL;

\echo ''
\echo '============================================================================'
\echo 'SECTION 5: BACKUP CURRENT STATE (RECOMMENDED)'
\echo '============================================================================'
\echo ''
\echo 'Before cleanup, create backup tables:'
\echo ''

-- Create backup of user_roles
CREATE TABLE IF NOT EXISTS user_roles_backup AS
SELECT * FROM user_roles;

\echo '✓ Created backup: user_roles_backup'
\echo ''

-- Verify backup
SELECT
    'user_roles' as original_table,
    COUNT(*) as record_count
FROM user_roles
UNION ALL
SELECT
    'user_roles_backup',
    COUNT(*)
FROM user_roles_backup;

\echo ''
\echo '============================================================================'
\echo 'SECTION 6: CLEANUP (UNCOMMENT TO EXECUTE)'
\echo '============================================================================'
\echo ''
\echo '⚠️  CLEANUP IS COMMENTED OUT BY DEFAULT FOR SAFETY'
\echo '⚠️  Review all checks above, then uncomment to execute'
\echo ''

-- UNCOMMENT THE FOLLOWING LINE TO DELETE DEPRECATED user_roles RECORDS:
-- DELETE FROM user_roles;

\echo '-- To execute cleanup, uncomment the DELETE statement above'
\echo ''

\echo '============================================================================'
\echo 'SECTION 7: POST-CLEANUP VERIFICATION (RUN AFTER CLEANUP)'
\echo '============================================================================'
\echo ''

\echo '7.1 Verify user_roles is empty:'
SELECT
    COUNT(*) as remaining_user_roles,
    CASE
        WHEN COUNT(*) = 0 THEN '✓ Cleanup successful'
        ELSE '✗ Cleanup incomplete'
    END as status
FROM user_roles;

\echo ''
\echo '7.2 Verify all users still have permissions (via groups):'
SELECT
    COUNT(DISTINCT u.id) as users_with_permissions
FROM users u
JOIN user_groups ug ON u.id = ug.user_id
JOIN groups g ON ug.group_id = g.id
JOIN group_roles gr ON g.id = gr.group_id
JOIN roles r ON gr.role_id = r.id
WHERE u.deleted_at IS NULL
  AND u.is_superuser = false;

\echo ''
\echo '7.3 Final state summary:'
SELECT
    'Active Users (non-superuser)' as metric,
    COUNT(*) as count
FROM users
WHERE deleted_at IS NULL AND is_superuser = false
UNION ALL
SELECT
    'Users in Groups',
    COUNT(DISTINCT user_id)
FROM user_groups
UNION ALL
SELECT
    'Active Groups',
    COUNT(*)
FROM groups
WHERE is_active = true
UNION ALL
SELECT
    'Group-Role Assignments',
    COUNT(*)
FROM group_roles
UNION ALL
SELECT
    'Remaining user_roles (should be 0)',
    COUNT(*)
FROM user_roles;

\echo ''
\echo '============================================================================'
\echo 'CLEANUP COMPLETE!'
\echo '============================================================================'
\echo ''
\echo 'Next steps:'
\echo '1. Test user permissions via API: GET /api/rbac/users/{user_id}/roles'
\echo '2. Verify in UI: http://localhost:8080/rbac.html'
\echo '3. If everything works, optionally drop backup table:'
\echo '   DROP TABLE user_roles_backup;'
\echo ''
