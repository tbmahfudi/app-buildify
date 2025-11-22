# Security Policy Seed Scripts

This directory contains seed scripts for initializing the security policy system.

## Overview

The security policy system requires two sets of data:
1. **Permissions and Roles** - RBAC permissions for security management
2. **Default Security Policy** - System-wide default security settings

## Prerequisites

Ensure you have installed the async database drivers:

```bash
# For PostgreSQL
pip install asyncpg

# For MySQL
pip install aiomysql

# For SQLite
pip install aiosqlite
```

## Seed Scripts

### 1. Security Permissions and Roles

**Script**: `seed_security_permissions.py`

Creates RBAC permissions and roles for security management:
- **Permissions**: security_policy:*, security:*, notification_config:*
- **Roles**: security_admin, security_viewer, support_admin

**Run**:
```bash
cd /home/user/app-buildify/backend
python app/scripts/seed_security_permissions.py
```

### 2. Default Security Policy

**Script**: `seed_default_security_policy.py`

Creates a system-wide default security policy that serves as the fallback for all tenants.

**Default Settings**:
- **Password**: 12 chars min, requires uppercase/lowercase/digit/special, expires in 90 days
- **Lockout**: 5 max attempts, 30 min lockout (progressive)
- **Session**: 60 min idle timeout, 12 hour absolute timeout, 3 max concurrent
- **Reset**: 24 hour token expiration, 5 max attempts

**Run**:
```bash
cd /home/user/app-buildify/backend
python app/scripts/seed_default_security_policy.py
```

## Quick Start (Run All Seeds)

Run both seed scripts in order:

```bash
cd /home/user/app-buildify/backend

# 1. Seed permissions and roles
python app/scripts/seed_security_permissions.py

# 2. Seed default security policy
python app/scripts/seed_default_security_policy.py
```

## What Each Script Does

### seed_security_permissions.py
- Creates security-related permissions
- Creates predefined roles (security_admin, security_viewer, support_admin)
- Assigns permissions to roles
- Safe to run multiple times (checks for existing data)

### seed_default_security_policy.py
- Creates system default security policy (tenant_id = NULL)
- Policy applies to all tenants that don't have custom policies
- Safe to run multiple times (checks if system policy exists)

## After Seeding

1. **Assign Roles**: Go to `Administration > Access Control` and assign security roles to users
2. **View Policies**: Navigate to `System Settings > Security` or `Administration > Auth Policies`
3. **Create Tenant Policies**: Optionally create tenant-specific policies to override system defaults

## Troubleshooting

### ModuleNotFoundError: No module named 'asyncpg'
Install the async database driver:
```bash
pip install asyncpg  # For PostgreSQL
```

### "System default security policy already exists"
This is normal - the script detects existing policies and won't create duplicates.

### Permission denied or connection errors
Ensure:
- Database is running and accessible
- `.env` file has correct `DATABASE_URL`
- Database migrations have been run (`alembic upgrade head`)

## Security Policy Hierarchy

```
┌─────────────────────────────────────┐
│   Tenant-Specific Policy (DB)      │  ← Highest Priority
├─────────────────────────────────────┤
│   System Default Policy (DB)        │  ← Created by seed_default_security_policy.py
├─────────────────────────────────────┤
│   Environment Variables (.env)      │
├─────────────────────────────────────┤
│   Code Defaults (Pydantic)          │  ← Lowest Priority
└─────────────────────────────────────┘
```

## Customizing Default Policy

To customize the default policy settings, edit `seed_default_security_policy.py` and modify the policy values before running, or use the web UI to update the policy after creation.

## Related Documentation

- Main docs: `/docs/README.md`
- Security config: `/backend/app/core/security_config.py`
- API endpoints: `/backend/app/routers/admin/security.py`
