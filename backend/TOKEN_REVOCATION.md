# Token Revocation System

This document describes the token revocation system implemented to replace Redis with database-backed token blacklisting.

## Overview

The system uses **PostgreSQL UNLOGGED tables** or **MySQL MEMORY tables** for high-performance token revocation without requiring Redis.

## Architecture

### Components

1. **TokenBlacklist Model** (`app/models/token_blacklist.py`)
   - Stores revoked tokens with JTI (JWT ID)
   - Uses UNLOGGED table for PostgreSQL (survives restarts but faster than regular tables)
   - Uses MEMORY table for MySQL (stored in RAM, lost on restart)
   - Automatically indexed for fast lookups

2. **Token Generation** (`app/core/auth.py`)
   - All tokens now include a unique `jti` (JWT ID) field
   - JTI is a UUID v4 for uniqueness
   - Both access and refresh tokens have JTI

3. **Token Validation** (`app/core/dependencies.py`)
   - `get_current_user` checks if token JTI is in blacklist
   - Returns 401 Unauthorized if token is revoked
   - Fast lookup via indexed JTI field

4. **Logout Endpoints** (`app/routers/auth.py`)
   - `POST /api/auth/logout` - Revokes current token
   - `POST /api/auth/logout-all` - Placeholder for revoking all user tokens

### Database Tables

#### PostgreSQL (UNLOGGED)
```sql
CREATE UNLOGGED TABLE token_blacklist (
    jti VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    token_type VARCHAR(20) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    blacklisted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### MySQL (MEMORY)
```sql
CREATE TABLE token_blacklist (
    jti VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    token_type VARCHAR(20) NOT NULL,
    expires_at DATETIME NOT NULL,
    blacklisted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=MEMORY;
```

## Why This Approach?

### PostgreSQL UNLOGGED Tables
- **Pros:**
  - 2-3x faster writes than regular tables
  - No WAL (Write-Ahead Logging) overhead
  - Data survives server restarts
  - Perfect for temporary data that can be regenerated
  - Still supports indexes and queries

- **Cons:**
  - Data lost on crash (acceptable for token blacklist)
  - Not replicated in streaming replication

### MySQL MEMORY Tables
- **Pros:**
  - Stored entirely in RAM
  - Extremely fast read/write operations
  - Perfect for temporary session data
  - Low disk I/O

- **Cons:**
  - Data lost on server restart (acceptable for token blacklist)
  - Limited by available RAM
  - Fixed-length row format

## Performance Comparison

| Operation | Redis | PostgreSQL UNLOGGED | MySQL MEMORY |
|-----------|-------|---------------------|--------------|
| Write | ~10-20μs | ~100-200μs | ~50-100μs |
| Read | ~10-20μs | ~50-100μs | ~30-60μs |
| Startup | Instant | Table reload | Instant (empty) |
| Persistence | Optional | Yes | No |

## Usage

### Logout (Revoke Current Token)
```bash
POST /api/auth/logout
Authorization: Bearer <token>
```

### Response
```json
{
  "message": "Successfully logged out"
}
```

### Check if Token is Valid
Any authenticated endpoint will return 401 if the token is blacklisted:
```json
{
  "detail": "Token has been revoked"
}
```

## Maintenance

### Cleanup Expired Tokens

The blacklist can grow over time. Use the cleanup utility to remove expired tokens:

```python
from app.core.token_cleanup import cleanup_expired_tokens
from app.core.db import SessionLocal

db = SessionLocal()
try:
    removed = cleanup_expired_tokens(db)
    print(f"Removed {removed} expired tokens")
finally:
    db.close()
```

### Recommended Cleanup Schedule

Run cleanup:
- **Daily** for low-traffic applications
- **Hourly** for medium-traffic applications
- **Every 15-30 minutes** for high-traffic applications

### Cron Job Example

Add to crontab:
```bash
# Cleanup expired tokens every hour
0 * * * * cd /path/to/backend && python -c "from app.core.token_cleanup import cleanup_expired_tokens; from app.core.db import SessionLocal; db = SessionLocal(); cleanup_expired_tokens(db); db.close()"
```

### FastAPI Background Task (Recommended)

Add to `app/main.py`:
```python
from fastapi_utils.tasks import repeat_every
from app.core.token_cleanup import cleanup_expired_tokens
from app.core.db import SessionLocal

@app.on_event("startup")
@repeat_every(seconds=3600)  # Run every hour
async def cleanup_tokens():
    db = SessionLocal()
    try:
        cleanup_expired_tokens(db)
    finally:
        db.close()
```

## Migration

### Apply Migrations

```bash
# PostgreSQL
alembic upgrade pg_c5d6e7f8g9h0

# MySQL
alembic upgrade mysql_d7e8f9g0h1i2

# SQLite (dev/testing)
alembic upgrade sqlite_e8f9g0h1i2j3
```

## Monitoring

### Get Blacklist Statistics

```python
from app.core.token_cleanup import get_blacklist_stats
from app.core.db import SessionLocal

db = SessionLocal()
try:
    stats = get_blacklist_stats(db)
    print(f"Total: {stats['total']}, Active: {stats['active']}, Expired: {stats['expired']}")
finally:
    db.close()
```

## Troubleshooting

### Issue: MySQL server restarts and all sessions are lost
**Solution:** This is expected behavior with MEMORY tables. Users will need to log in again. Consider using InnoDB if persistence is required, but performance will be slower.

### Issue: PostgreSQL UNLOGGED table data lost after crash
**Solution:** This is expected behavior. UNLOGGED tables don't write to WAL. After a crash, the table is truncated. Users will need to log in again.

### Issue: Blacklist table growing too large
**Solution:** Ensure cleanup job is running regularly. Check `get_blacklist_stats()` to see how many expired tokens remain.

### Issue: Slow token validation
**Solution:** Ensure indexes are created. Check query performance with EXPLAIN:
```sql
EXPLAIN SELECT * FROM token_blacklist WHERE jti = 'some-uuid';
```

## Security Considerations

1. **Token Expiration:** Tokens naturally expire based on `ACCESS_TOKEN_EXPIRE_MIN` and `REFRESH_TOKEN_EXPIRE_DAYS`
2. **JTI Uniqueness:** Each token has a unique JTI (UUID v4), preventing collisions
3. **Database Access:** Token blacklist requires database access for every authenticated request
4. **Cleanup Required:** Regular cleanup prevents DoS via blacklist table growth

## Future Enhancements

1. **Logout All Devices:** Implement user-level token revocation timestamp
2. **Suspicious Activity:** Auto-revoke tokens on suspicious activity detection
3. **Rate Limiting:** Add rate limiting to logout endpoint
4. **Metrics:** Track logout frequency and blacklist size over time
