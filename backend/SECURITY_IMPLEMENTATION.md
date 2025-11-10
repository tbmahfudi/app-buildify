

# Security Policy Implementation Guide

## Overview

This document describes the comprehensive security policy system implemented for password management, account lockout, session security, and notifications. The system is fully configurable with support for:

- **Tenant-level customization** (superadmin configurable)
- **Grandfathered users** (existing users with weak passwords not forced to update)
- **No superuser bypass** (admins subject to same lockout policies)
- **Flexible notification system** with queue-based delivery
- **Grace period support** for password expiration

---

## Architecture

### Configuration Hierarchy

The security configuration follows a 4-tier hierarchy:

```
1. Tenant-specific policy (database) → Highest priority
2. System default policy (database, tenant_id=NULL)
3. Environment variables (.env file)
4. Code defaults (in Pydantic models) → Lowest priority
```

### Components Implemented

#### ✅ Database Layer
- **Migrations**: `pg_security_policy_system.py` and `mysql_security_policy_system.py`
- **New Tables**:
  - `password_history` - Tracks password history to prevent reuse
  - `login_attempts` - Records all login attempts for audit
  - `account_lockouts` - Tracks account lockouts
  - `user_sessions` - Manages active user sessions
  - `security_policies` - Stores tenant-level security configurations
  - `notification_queue` - Queue for async notifications
  - `notification_config` - Notification delivery configuration
  - `password_reset_tokens` - Secure password reset tokens

#### ✅ Models
Location: `app/models/`
- `password_history.py` - PasswordHistory model
- `login_attempt.py` - LoginAttempt model
- `account_lockout.py` - AccountLockout model with `is_active` property
- `user_session.py` - UserSession model with `is_active`, `is_expired` properties
- `security_policy.py` - SecurityPolicy model with `to_dict()` method
- `notification_queue.py` - NotificationQueue model with `can_retry`, `is_ready` properties
- `notification_config.py` - NotificationConfig model with `get_methods_for_notification_type()`
- `password_reset_token.py` - PasswordResetToken model with `is_valid`, `is_expired` properties

#### ✅ Core Services
Location: `app/core/`

1. **`security_config.py`** - Configuration Management
   - `PasswordPolicyConfig` - Password strength and lifecycle
   - `AccountLockoutConfig` - Lockout policies
   - `SessionSecurityConfig` - Session management
   - `PasswordResetConfig` - Reset policies
   - `SecurityConfig` - Master config combining all policies
   - `get_security_config(db, tenant_id)` - Get config with hierarchy fallback

2. **`common_passwords.py`** - Common Password Blocking
   - List of top 100 common passwords
   - `is_common_password(password)` - Check against list

3. **`password_validator.py`** - Password Validation
   - `PasswordValidator` class with:
     - `validate_strength()` - Check strength requirements
     - `validate_history()` - Check password history
     - `validate_full()` - Combined validation
     - `get_policy_description()` - Get human-readable requirements
   - `PasswordValidationError` - Exception for validation failures
   - `validate_password()` - Convenience function

4. **`password_history.py`** - Password History Management
   - `PasswordHistoryService` class with:
     - `add_to_history()` - Add password to history
     - `cleanup_old_history()` - Remove old entries
     - `record_password_change()` - Full password change workflow

5. **`lockout_manager.py`** - Account Lockout Management
   - `LockoutManager` class with:
     - `record_login_attempt()` - Record success/failure
     - `get_recent_failed_attempts()` - Count failures
     - `calculate_lockout_duration()` - Fixed or progressive
     - `apply_lockout()` - Lock account
     - `check_and_apply_lockout()` - Check and auto-lock
     - `unlock_account()` - Manual admin unlock
     - `reset_failed_attempts()` - Reset on successful login
     - `is_account_locked()` - Check lock status

6. **`session_manager.py`** - Session Management
   - `SessionManager` class with:
     - `create_session()` - Create new session
     - `get_active_sessions()` - Get user's active sessions
     - `count_active_sessions()` - Count active sessions
     - `enforce_concurrent_limit()` - Revoke oldest if over limit
     - `revoke_session()` - Revoke by JTI
     - `revoke_all_sessions()` - Revoke all for user
     - `update_activity()` - Update last activity
     - `cleanup_expired_sessions()` - Cleanup old sessions
     - `is_session_valid()` - Check session validity

7. **`notification_service.py`** - Notification Queueing
   - `NotificationService` class with:
     - `queue_notification()` - Queue generic notification
     - `get_notification_config()` - Get tenant config
     - `notify_account_locked()` - Queue lockout notification
     - `notify_password_expiring()` - Queue expiry warning
     - `notify_password_changed()` - Queue change confirmation
     - `notify_password_reset()` - Queue reset link

---

## Configuration

### Environment Variables

All security policies can be configured via environment variables in `.env`:

```bash
# Password Policy
PASSWORD_MIN_LENGTH=12
PASSWORD_MAX_LENGTH=128
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL_CHAR=true
PASSWORD_MIN_UNIQUE_CHARS=4
PASSWORD_MAX_REPEATING_CHARS=3
PASSWORD_ALLOW_COMMON=false
PASSWORD_ALLOW_USERNAME=false
PASSWORD_HISTORY_COUNT=5
PASSWORD_EXPIRATION_DAYS=90
PASSWORD_EXPIRATION_WARNING_DAYS=14
PASSWORD_GRACE_LOGINS=3

# Account Lockout Policy
LOGIN_MAX_ATTEMPTS=5
LOGIN_LOCKOUT_DURATION_MIN=15
LOGIN_LOCKOUT_TYPE=progressive  # 'fixed' or 'progressive'
LOGIN_RESET_ATTEMPTS_AFTER_MIN=60
LOGIN_NOTIFY_USER_ON_LOCKOUT=true

# Session Security Policy
SESSION_TIMEOUT_MINUTES=30
SESSION_ABSOLUTE_TIMEOUT_HOURS=8
SESSION_MAX_CONCURRENT=3  # 0 = unlimited
SESSION_TERMINATE_ON_PASSWORD_CHANGE=true

# Password Reset Policy
PASSWORD_RESET_TOKEN_EXPIRE_HOURS=1
PASSWORD_RESET_MAX_ATTEMPTS=3
PASSWORD_RESET_NOTIFY_USER=true
```

### Database Configuration (Superadmin)

Superadmins can override policies per-tenant by creating `SecurityPolicy` records:

```python
from app.models import SecurityPolicy

# System default (applies to all tenants without specific policy)
system_policy = SecurityPolicy(
    tenant_id=None,  # NULL = system default
    policy_name="System Default Security Policy",
    policy_type="combined",
    password_min_length=12,
    password_require_uppercase=True,
    # ... other settings
    is_active=True
)

# Tenant-specific (overrides system default)
tenant_policy = SecurityPolicy(
    tenant_id="tenant-uuid-here",
    policy_name="ACME Corp Custom Policy",
    policy_type="combined",
    password_min_length=16,  # Stricter than system default
    login_max_attempts=3,
    # ... other settings
    is_active=True
)
```

---

## Usage Examples

### 1. Validate Password on User Registration

```python
from app.core.security_config import get_password_policy
from app.core.password_validator import validate_password, PasswordValidationError

async def register_user(db, email, password, tenant_id):
    # Get policy for tenant (or system default)
    policy = await get_password_policy(db, tenant_id)

    # Validate password
    is_valid, errors = await validate_password(
        db=db,
        password=password,
        policy=policy,
        user_email=email,
        raise_on_error=True  # Raises PasswordValidationError
    )

    # Create user...
```

### 2. Handle Login with Lockout Check

```python
from app.core.security_config import get_lockout_policy
from app.core.lockout_manager import LockoutManager

async def login(db, email, password):
    user = await get_user_by_email(db, email)
    policy = await get_lockout_policy(db, str(user.tenant_id))
    manager = LockoutManager(policy)

    # Check if account is locked
    is_locked, locked_until = await manager.is_account_locked(db, user)
    if is_locked:
        raise HTTPException(
            status_code=403,
            detail=f"Account locked until {locked_until}"
        )

    # Verify password
    if not verify_password(password, user.hashed_password):
        # Record failed attempt
        await manager.record_login_attempt(
            db, str(user.id), email, success=False,
            failure_reason="invalid_password"
        )

        # Check if should lock
        should_lock, locked_until = await manager.check_and_apply_lockout(
            db, user, email
        )

        if should_lock:
            # Send notification
            from app.core.notification_service import notify_account_locked
            await notify_account_locked(db, email, locked_until, str(user.id), str(user.tenant_id))

        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Success - reset attempts
    await manager.reset_failed_attempts(db, user)
    await manager.record_login_attempt(db, str(user.id), email, success=True)

    # Create session...
```

### 3. Change Password with History Check

```python
from app.core.security_config import get_password_policy, get_session_policy
from app.core.password_validator import validate_password
from app.core.password_history import record_password_change
from app.core.session_manager import revoke_all_user_sessions

async def change_password(db, user, new_password, current_jti=None):
    # Get policies
    password_policy = await get_password_policy(db, str(user.tenant_id))
    session_policy = await get_session_policy(db, str(user.tenant_id))

    # Validate new password (includes history check)
    is_valid, errors = await validate_password(
        db=db,
        password=new_password,
        policy=password_policy,
        user_id=str(user.id),
        user_email=user.email,
        raise_on_error=True
    )

    # Hash and record
    new_hash = get_password_hash(new_password)
    await record_password_change(db, user, new_hash, password_policy)

    # Revoke sessions if policy requires
    if session_policy.terminate_on_password_change:
        await revoke_all_user_sessions(db, str(user.id), session_policy, except_jti=current_jti)

    # Send notification
    from app.core.notification_service import notify_password_changed
    await notify_password_changed(db, user.email, str(user.id), str(user.tenant_id))
```

### 4. Create Session with Concurrent Limit

```python
from app.core.security_config import get_session_policy
from app.core.session_manager import SessionManager

async def create_access_token(db, user, jti, expires_at):
    policy = await get_session_policy(db, str(user.tenant_id))
    manager = SessionManager(policy)

    # Create session (automatically enforces concurrent limit)
    session = await manager.create_session(
        db=db,
        user_id=str(user.id),
        jti=jti,
        expires_at=expires_at,
        device_id=get_device_fingerprint(),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    return session
```

---

## Integration TODO

The following components still need to be integrated into the authentication system:

### ⚠️ Required Integration Steps

1. **Update `app/routers/auth.py`**:
   - Import new services
   - Add lockout check to `/auth/login`
   - Record login attempts (success/failure)
   - Create sessions in user_sessions table
   - Add password validation to password change endpoints
   - Implement password expiration checks

2. **Create Password Expiration Middleware**:
   - Check `user.password_expires_at` on each request
   - If expired and `grace_logins_remaining > 0`, decrement and warn
   - If expired and no grace logins, force password change
   - Send expiry warnings based on `password_expiration_warning_days`

3. **Create Admin Endpoints** (`app/routers/admin/security.py`):
   - `GET /admin/security/policies` - List security policies
   - `POST /admin/security/policies` - Create/update tenant policy
   - `GET /admin/security/locked-accounts` - View locked accounts
   - `POST /admin/security/unlock/{user_id}` - Manual unlock
   - `GET /admin/security/active-sessions` - View all active sessions
   - `DELETE /admin/security/sessions/{session_id}` - Revoke session
   - `GET /admin/notification/config` - Get notification config
   - `PUT /admin/notification/config` - Update notification config

4. **Create Password Reset Endpoints** (`app/routers/auth.py`):
   - `POST /auth/forgot-password` - Request reset
   - `POST /auth/reset-password` - Reset with token
   - Use `PasswordResetToken` model
   - Queue notifications via notification service

5. **Implement Notification Processor**:
   - Background task to process `notification_queue`
   - Support email delivery (SMTP)
   - Support webhook delivery (HTTP POST)
   - Extensible for SMS/push notifications
   - Update status and retry failed deliveries

6. **Create Scheduled Tasks**:
   - Daily: Check for expiring passwords, send warnings
   - Hourly: Cleanup expired sessions
   - Hourly: Process notification queue
   - Daily: Cleanup old login attempts (> 90 days)

---

## Security Features Summary

### ✅ HIGH PRIORITY (Implemented)

1. **Password Strength Validation**
   - Configurable length (12-128 chars default)
   - Character complexity requirements
   - Common password blocking (top 100 list)
   - Username/email similarity check
   - Unique character and repeating character limits

2. **Account Lockout**
   - Configurable max attempts (5 default)
   - Progressive lockout (5min → 15min → 1hr → 24hr)
   - Fixed lockout option
   - Automatic lockout expiration
   - Manual admin unlock support
   - Login attempt audit trail

3. **Password History**
   - Configurable history count (5 default)
   - Prevents password reuse
   - Automatic cleanup of old history

4. **Session Management**
   - Concurrent session limits (3 default)
   - Session revocation on password change
   - Activity tracking
   - Device fingerprinting support

### ✅ MEDIUM PRIORITY (Implemented)

5. **Password Expiration**
   - Configurable expiration (90 days default)
   - Warning period (14 days default)
   - Grace logins (3 default)
   - Automatic expiration date calculation

6. **Concurrent Session Limits**
   - Configurable limit (3 default)
   - Automatic oldest session revocation
   - Session listing and management

7. **Password Reset**
   - Model and token system implemented
   - Secure token hashing
   - Configurable expiration (1 hour default)

8. **Common Password Blocking**
   - Top 100 most common passwords
   - Case-insensitive matching

### 🔄 Notification System (Foundation Complete)

9. **Notification Queue**
   - Queue-based architecture
   - Priority support
   - Retry logic
   - Multiple delivery methods:
     - ✅ Email (queued)
     - ✅ SMS (queued)
     - ✅ Webhook (queued)
     - ⚠️ Delivery processor needed

10. **Notification Types**:
    - ✅ Account locked
    - ✅ Password expiring
    - ✅ Password changed
    - ✅ Password reset
    - ⚠️ Login from new device (queuing ready)

### 📋 Not Implemented (Future)

- Multi-factor authentication (2FA/TOTP)
- Biometric authentication
- Risk-based authentication
- Device trust/remember
- IP whitelist/blacklist
- Geolocation-based security
- Advanced threat detection

---

## Database Migrations

To apply the security system:

```bash
# PostgreSQL
cd backend
alembic upgrade head

# Or run migration directly
python -m alembic upgrade pg_security_policy_system
```

The migration adds:
- 8 new tables
- 7 new columns to users table
- Appropriate indexes for performance
- Foreign key constraints

---

## Testing Checklist

### Password Policy
- [ ] Password too short rejected
- [ ] Password missing uppercase rejected
- [ ] Password missing digit rejected
- [ ] Common password ("password123") rejected
- [ ] Password containing email rejected
- [ ] Password reuse (history) rejected
- [ ] Valid strong password accepted

### Account Lockout
- [ ] 5 failed attempts locks account
- [ ] Lockout duration increases progressively
- [ ] Account auto-unlocks after duration
- [ ] Admin can manually unlock
- [ ] Successful login resets counter
- [ ] Superuser subject to lockout (no bypass)

### Session Management
- [ ] 4th concurrent session revokes oldest
- [ ] Password change revokes all sessions
- [ ] Expired sessions not valid
- [ ] Session activity updates

### Password Expiration
- [ ] Password expires after 90 days
- [ ] Warning sent 14 days before
- [ ] Grace logins work correctly
- [ ] Forced password change after grace period

### Notifications
- [ ] Lockout notification queued
- [ ] Password expiry warning queued
- [ ] Password change confirmation queued
- [ ] Notifications respect tenant config

### Tenant Customization
- [ ] Tenant-specific policy overrides system default
- [ ] System default applies when no tenant policy
- [ ] Environment variables used as fallback
- [ ] Superadmin can create/update policies

---

## Grandfathered Users

Existing users with weak passwords are **grandfathered**:

1. Old passwords remain valid until changed
2. `require_password_change` flag NOT automatically set
3. Password expiration starts from `password_changed_at` (NULL for old users = no expiration yet)
4. On next password change, new policies apply

To force all users to update:

```sql
UPDATE users SET require_password_change = true, grace_logins_remaining = 3;
```

---

## Grace Period

New strict policies can be rolled out with a grace period:

1. Deploy new policy configuration
2. Set `PASSWORD_GRACE_LOGINS=10` for 30 days
3. Monitor compliance
4. Reduce to `PASSWORD_GRACE_LOGINS=3` after grace period
5. Eventually set `PASSWORD_GRACE_LOGINS=0` to force immediate compliance

---

## Performance Considerations

- **Login attempts**: Indexed by `email` and `created_at` for fast recent attempt queries
- **Password history**: Indexed by `user_id` and `created_at` for fast history checks
- **User sessions**: Indexed by `user_id`, `revoked_at`, `expires_at` for active session queries
- **Notification queue**: Indexed by `status`, `priority`, `scheduled_for` for queue processing

Consider:
- Archiving old login attempts (>90 days)
- Archiving old lockout records
- Regular cleanup of expired sessions
- Cleanup of processed notifications

---

## Support & Maintenance

For questions or issues:
1. Check this implementation guide
2. Review code in `app/core/` for service logic
3. Review models in `app/models/` for data structure
4. Check `backend/.env.example` for configuration options

---

## Version

- **Implementation Date**: 2025-11-10
- **Status**: Core foundation complete, integration pending
- **Compatibility**: PostgreSQL, MySQL, SQLite
