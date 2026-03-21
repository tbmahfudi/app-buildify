# Authentication & Security

## Authentication Flow

```
Client                          Backend                         Redis
  │                                │                              │
  │  POST /auth/login              │                              │
  │  { email, password }           │                              │
  │ ─────────────────────────────► │                              │
  │                                │  Validate password (bcrypt)  │
  │                                │  Check lockout state         │
  │                                │  Generate access_token (JWT) │
  │                                │  Generate refresh_token (JWT)│
  │                                │  Store session in DB         │
  │  200 { access_token,           │                              │
  │         refresh_token }        │                              │
  │ ◄───────────────────────────── │                              │
  │                                │                              │
  │  GET /api/v1/users             │                              │
  │  Authorization: Bearer <token> │                              │
  │ ─────────────────────────────► │                              │
  │                                │  Decode JWT (PyJWT)          │
  │                                │  Check token blacklist ──────►
  │                                │                       ◄──────│
  │                                │  Load user from DB           │
  │                                │  Check permissions (RBAC)    │
  │  200 [ users... ]              │                              │
  │ ◄───────────────────────────── │                              │
```

---

## JWT Tokens

### Access Token

- **Algorithm**: HS256
- **Default expiry**: 30 minutes (configurable)
- **Payload**:
  ```json
  {
    "sub": "<user_uuid>",
    "tenant_id": "<tenant_uuid>",
    "exp": 1234567890,
    "iat": 1234567890,
    "jti": "<unique-token-id>"
  }
  ```

### Refresh Token

- **Default expiry**: 7 days (configurable)
- Stored in DB (`user_sessions`) and used to issue new access tokens
- Invalidated on logout

### Token Revocation

- Redis stores blacklisted `jti` values with TTL matching token expiry
- Every authenticated request checks the Redis blacklist
- On logout, the access token `jti` is added to Redis

---

## Password Security

### Hashing

Passwords are hashed with **bcrypt** via `passlib`:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

### Password Policy (configurable per tenant)

| Setting | Default | Description |
|---------|---------|-------------|
| `min_length` | 8 | Minimum password length |
| `require_uppercase` | true | At least one uppercase letter |
| `require_lowercase` | true | At least one lowercase letter |
| `require_digit` | true | At least one number |
| `require_special` | true | At least one special character |
| `history_count` | 5 | Cannot reuse last N passwords |
| `max_age_days` | 90 | Password expiration in days |
| `warn_before_days` | 7 | Show warning N days before expiry |

### Password History

Previous password hashes are stored in `password_history`. On each password change, the service validates the new password isn't in the history.

---

## Account Lockout

Configured via `SecurityPolicy.lockout_policy`:

| Setting | Default | Description |
|---------|---------|-------------|
| `max_attempts` | 5 | Failed attempts before lockout |
| `lockout_duration_minutes` | 15 | How long the account is locked |
| `lockout_type` | `progressive` | `fixed` or `progressive` |
| `progressive_multiplier` | 2 | Duration multiplier for progressive lockout |

**Progressive lockout** example: 15 min → 30 min → 60 min → ...

The `LoginAttempt` table records each failed attempt. The `LockoutManager` evaluates the lockout state on each login request.

---

## Session Management

Configured via `SecurityPolicy.session_policy`:

| Setting | Default | Description |
|---------|---------|-------------|
| `idle_timeout_minutes` | 30 | Lock after N minutes of inactivity |
| `absolute_timeout_hours` | 8 | Force re-login after N hours regardless |
| `max_concurrent_sessions` | 3 | Maximum simultaneous sessions per user |
| `single_session_mode` | false | Only allow one active session at a time |

The `SessionManager` tracks last activity and enforces timeout policies.

---

## Rate Limiting

Implemented with **SlowAPI** (Starlette middleware):

- Default: `100 requests/minute` per IP
- Login endpoint: `10 requests/minute` per IP (stricter)
- Configurable via `RATE_LIMIT` environment variable
- Returns `429 Too Many Requests` when exceeded

---

## Security Headers

`SecurityMiddleware` (`app/core/security_middleware.py`) adds these headers to all responses:

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'...
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
```

---

## RBAC Permission Enforcement

Every protected endpoint uses the `require_permission` dependency:

```python
@router.post("/users")
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("users:create:tenant")),
    current_user: User = Depends(get_current_user),
):
    ...
```

The permission check:
1. Loads the user's effective permissions (direct roles + group roles)
2. Checks if any permission code matches the required code
3. Raises `403 Forbidden` if not matched

---

## Audit Logging

All security-relevant events are logged to `audit_logs`:

| Event Type | Trigger |
|-----------|---------|
| `auth.login.success` | Successful login |
| `auth.login.failed` | Failed login attempt |
| `auth.logout` | Logout |
| `auth.token.refresh` | Token refresh |
| `auth.password.changed` | Password change |
| `auth.password.reset` | Password reset |
| `user.lockout` | Account locked |
| `user.unlocked` | Account unlocked |
| `rbac.role.assigned` | Role assigned to user |
| `data.*` | Any data modification |

Each audit record includes: `user_id`, `tenant_id`, `action`, `resource`, `resource_id`, `old_value`, `new_value`, `ip_address`, `user_agent`, `created_at`.

---

## Security Configuration API

Tenant admins can configure security policies via `/admin/security/policy`:

```json
{
  "password_policy": {
    "min_length": 10,
    "require_uppercase": true,
    "require_special": true,
    "history_count": 10,
    "max_age_days": 60
  },
  "session_policy": {
    "idle_timeout_minutes": 20,
    "absolute_timeout_hours": 8,
    "max_concurrent_sessions": 2
  },
  "lockout_policy": {
    "max_attempts": 3,
    "lockout_duration_minutes": 30,
    "lockout_type": "progressive"
  }
}
```

---

## Security Recommendations for Production

1. **Set a strong `JWT_SECRET_KEY`** (32+ random bytes)
2. **Enable HTTPS** via Nginx TLS termination
3. **Change default admin password** immediately after setup
4. **Use environment variables** — never commit `.env` files
5. **Configure `SENTRY_DSN`** for error monitoring
6. **Review and tighten CSP headers** for your specific asset sources
7. **Enable Redis AUTH** — set a Redis password in production
8. **Rotate JWT keys periodically** and invalidate all sessions on rotation
9. **Store tokens in httpOnly cookies** instead of localStorage (XSS mitigation)
10. **Enable database connection pooling** and SSL (`sslmode=require` in DATABASE_URL)
