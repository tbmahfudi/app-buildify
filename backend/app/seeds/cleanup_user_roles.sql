-- ============================================================================
-- CLEANUP DEPRECATED user_roles
-- ============================================================================
-- This script safely removes deprecated user_roles records
--
-- PREREQUISITES:
-- 1. Run verify_rbac.sql first to ensure all users are in groups
-- 2. Backup your database
-- 3. Verify users have permissions via groups
-- ============================================================================

\echo '========================================='
\echo 'CLEANUP DEPRECATED user_roles'
\echo '========================================='
\echo ''

-- Safety check
\echo 'SAFETY CHECK:'
DO $$
DECLARE
    users_without_groups INTEGER;
BEGIN
    SELECT COUNT(*) INTO users_without_groups
    FROM users u
    LEFT JOIN user_groups ug ON u.id = ug.user_id
    WHERE u.deleted_at IS NULL
      AND u.is_superuser = false
      AND ug.user_id IS NULL;

    IF users_without_groups > 0 THEN
        RAISE EXCEPTION 'UNSAFE: % users have no groups! Run ./manage.sh seed-rbac first', users_without_groups;
    ELSE
        RAISE NOTICE '✓ SAFE: All users are in groups';
    END IF;
END $$;

\echo ''

-- Create backup
\echo 'Creating backup...'
DROP TABLE IF EXISTS user_roles_backup;
CREATE TABLE user_roles_backup AS SELECT * FROM user_roles;

\echo '✓ Backup created: user_roles_backup'
\echo ''

-- Show what will be deleted
\echo 'Records to be deleted:'
SELECT COUNT(*) as user_roles_to_delete FROM user_roles;

\echo ''
\echo 'Users affected:'
SELECT
    u.email,
    COUNT(*) as role_assignments
FROM user_roles ur
JOIN users u ON ur.user_id = u.id
GROUP BY u.id, u.email
ORDER BY role_assignments DESC;

\echo ''

-- Confirm and delete
\echo '⚠️  Are you sure you want to delete these records?'
\echo '⚠️  Press Ctrl+C to cancel, or press Enter to continue...'
\prompt 'Press Enter to continue' confirmation

-- Delete
DELETE FROM user_roles;

\echo ''
\echo '✓ Deleted deprecated user_roles records'
\echo ''

-- Verify
\echo 'Verification:'
SELECT
    (SELECT COUNT(*) FROM user_roles) as remaining_user_roles,
    (SELECT COUNT(*) FROM user_roles_backup) as backed_up_records;

\echo ''
\echo '========================================='
\echo 'CLEANUP COMPLETE!'
\echo '========================================='
\echo ''
\echo 'Backup saved in: user_roles_backup'
\echo 'To restore: INSERT INTO user_roles SELECT * FROM user_roles_backup;'
\echo 'To drop backup: DROP TABLE user_roles_backup;'
\echo ''
