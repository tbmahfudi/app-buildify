-- Default System Security Policy Seed
-- This SQL creates a default system-wide security policy
-- Compatible with PostgreSQL, MySQL, and SQLite

-- Check if system default policy exists before inserting
-- Note: SQLite doesn't support IF NOT EXISTS for inserts, so run this carefully

INSERT INTO security_policies (
    id,
    tenant_id,
    policy_name,
    policy_type,
    -- Password Policy
    password_min_length,
    password_max_length,
    password_require_uppercase,
    password_require_lowercase,
    password_require_digit,
    password_require_special_char,
    password_min_unique_chars,
    password_max_repeating_chars,
    password_allow_common,
    password_allow_username,
    password_history_count,
    password_expiration_days,
    password_expiration_warning_days,
    password_grace_logins,
    -- Account Lockout Policy
    login_max_attempts,
    login_lockout_duration_min,
    login_lockout_type,
    login_reset_attempts_after_min,
    login_notify_user_on_lockout,
    -- Session Policy
    session_timeout_minutes,
    session_absolute_timeout_hours,
    session_max_concurrent,
    session_terminate_on_password_change,
    -- Password Reset Policy
    password_reset_token_expire_hours,
    password_reset_max_attempts,
    password_reset_notify_user,
    -- Metadata
    is_active,
    created_at
)
SELECT
    -- Generate UUID (different syntax for different databases)
    -- PostgreSQL: gen_random_uuid()
    -- MySQL: UUID()
    -- SQLite: use hex(randomblob(16))
    lower(hex(randomblob(16))),  -- SQLite UUID
    NULL,  -- tenant_id = NULL means system default
    'Default System Security Policy',
    'combined',
    -- Password Policy Settings
    12,    -- password_min_length
    128,   -- password_max_length
    1,     -- password_require_uppercase (true)
    1,     -- password_require_lowercase (true)
    1,     -- password_require_digit (true)
    1,     -- password_require_special_char (true)
    8,     -- password_min_unique_chars
    2,     -- password_max_repeating_chars
    0,     -- password_allow_common (false)
    0,     -- password_allow_username (false)
    5,     -- password_history_count
    90,    -- password_expiration_days
    14,    -- password_expiration_warning_days
    3,     -- password_grace_logins
    -- Account Lockout Settings
    5,     -- login_max_attempts
    30,    -- login_lockout_duration_min
    'progressive',  -- login_lockout_type
    60,    -- login_reset_attempts_after_min
    1,     -- login_notify_user_on_lockout (true)
    -- Session Settings
    60,    -- session_timeout_minutes
    12,    -- session_absolute_timeout_hours
    3,     -- session_max_concurrent
    1,     -- session_terminate_on_password_change (true)
    -- Password Reset Settings
    24,    -- password_reset_token_expire_hours
    5,     -- password_reset_max_attempts
    1,     -- password_reset_notify_user (true)
    -- Metadata
    1,     -- is_active (true)
    CURRENT_TIMESTAMP  -- created_at
WHERE NOT EXISTS (
    SELECT 1 FROM security_policies WHERE tenant_id IS NULL AND is_active = 1
);

-- Verify the insert
SELECT
    policy_name,
    CASE WHEN tenant_id IS NULL THEN 'SYSTEM DEFAULT' ELSE 'TENANT' END as scope,
    password_min_length,
    password_expiration_days,
    login_max_attempts,
    session_timeout_minutes
FROM security_policies
WHERE tenant_id IS NULL AND is_active = 1;
