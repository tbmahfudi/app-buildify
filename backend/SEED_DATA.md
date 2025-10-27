# Multi-Tenant Organization Seed Data

Comprehensive seed data script for testing the multi-tenant architecture with realistic organizational structures.

## Overview

The seed script creates **5 complete organizational scenarios** with proper multi-tenant isolation, demonstrating various company structures and use cases.

## Scenarios Included

### 1. Tech Startup 🚀
- **Company:** TechStart Innovations Inc.
- **Structure:** Flat, single location
- **Size:** 25 employees
- **Features:** Engineering, Product, Sales, Operations
- **Tenant Tier:** Premium

### 2. Retail Chain 🛍️
- **Company:** FashionHub Retail Ltd.
- **Structure:** Multi-location, standard hierarchy
- **Size:** 200 employees, 15 stores
- **Features:** Corporate HQ, multiple store locations, distribution center
- **Tenant Tier:** Premium

### 3. Healthcare Network 🏥
- **Company:** MedCare Health System
- **Structure:** Complex multi-facility
- **Size:** 1000+ employees
- **Features:** 3 hospitals, 12 clinics, specialized departments
- **Tenant Tier:** Enterprise

### 4. Remote-First Tech 🌐
- **Company:** CloudWork Solutions
- **Structure:** Virtual, no physical offices
- **Size:** 150 employees worldwide
- **Features:** Fully remote teams, virtual departments
- **Tenant Tier:** Premium

### 5. Financial Services 💼
- **Company:** FinTech Capital Partners
- **Structure:** Regulatory compliance focus
- **Size:** 500 employees
- **Features:** Trading, compliance, risk management
- **Tenant Tier:** Enterprise

## Quick Start

### 1. Run Migrations

First, ensure all database migrations are applied:

```bash
cd backend
alembic upgrade head
```

### 2. Run Seed Script

```bash
python -m app.seeds.seed_complete_org
```

You'll be prompted:
```
Do you want to clear existing data? (yes/no):
```

- **yes** - Clears all existing tenants, companies, users, etc. (⚠️ destructive)
- **no** - Adds seed data to existing database

### 3. Start the API

```bash
uvicorn app.main:app --reload
```

## Test Credentials

### Superuser (Cross-Tenant Access)

```
Email:    superadmin@system.com
Password: SuperAdmin123!
```

This account can access all tenants and has full administrative privileges.

### Tenant Users

All regular users have the password: **`password123`**

#### Tech Startup
```
ceo@techstart.com
cto@techstart.com
dev1@techstart.com
dev2@techstart.com
pm@techstart.com
```

#### Retail Chain
```
ceo@fashionhub.com
cfo@fashionhub.com
hr@fashionhub.com
manager.nyc1@fashionhub.com
sales.nyc1@fashionhub.com
```

#### Healthcare
```
ceo@medcare.com
cmo@medcare.com
er.doc@medcare.com
nurse.lead@medcare.com
```

#### Remote Tech
```
ceo@cloudwork.com
eng@cloudwork.com
dev1@cloudwork.com
```

#### Financial Services
```
ceo@fintech.com
compliance@fintech.com
trader@fintech.com
```

## What Gets Created

For each scenario:

### 1. Tenant
- Unique tenant entity
- Subscription tier (premium/enterprise)
- Usage limits (companies, users, storage)
- Tenant settings (branding, features)

### 2. Company
- Linked to tenant via `tenant_id`
- Company-specific metadata
- Unique code per tenant

### 3. Branches
- Physical or virtual locations
- Linked to both tenant and company
- Various types (HQ, stores, facilities)

### 4. Departments
- Organizational units
- Can be company-wide or branch-specific
- Hierarchical structure support

### 5. Users
- Assigned to tenant
- Default company assignment
- Branch and department assignments
- User settings and preferences

## Database Schema Verification

After seeding, verify the data:

```sql
-- Check tenants
SELECT id, code, name, subscription_tier FROM tenants;

-- Check companies per tenant
SELECT t.code as tenant, c.code, c.name
FROM companies c
JOIN tenants t ON c.tenant_id = t.id;

-- Check users per tenant
SELECT t.code as tenant, COUNT(*) as user_count
FROM users u
JOIN tenants t ON u.tenant_id = t.id
GROUP BY t.code;

-- Verify tenant isolation
SELECT u.email, t.code as tenant, c.name as company
FROM users u
LEFT JOIN tenants t ON u.tenant_id = t.id
LEFT JOIN companies c ON u.default_company_id = c.id
ORDER BY t.code, u.email;
```

## API Testing

### 1. Login as Tenant User

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "ceo@techstart.com",
  "password": "password123"
}
```

Response includes:
- `access_token` - Use in Authorization header
- `refresh_token` - For token refresh
- `expires_in` - Token expiration (1800 seconds = 30 minutes)

### 2. Get Current User

```bash
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

Verify tenant_id matches expected tenant.

### 3. Test Multi-Tenant Isolation

Try accessing data from a different tenant - should be blocked:

```bash
# Login as Tech Startup user
POST /api/v1/auth/login
{ "email": "ceo@techstart.com", "password": "password123" }

# Try to access Retail Chain data (should fail)
GET /api/v1/companies/{retail_company_id}
Authorization: Bearer {techstart_access_token}

# Should return 403 Forbidden
```

### 4. Test Superuser Access

```bash
# Login as superuser
POST /api/v1/auth/login
{ "email": "superadmin@system.com", "password": "SuperAdmin123!" }

# Can access any tenant's data
GET /api/v1/companies/{any_company_id}
Authorization: Bearer {superuser_access_token}

# Should succeed
```

## Customizing Seed Data

### Add New Scenario

Edit `backend/app/seeds/seed_complete_org.py` and add to `SEED_DATA` dictionary:

```python
SEED_DATA = {
    # ... existing scenarios ...

    "my_scenario": {
        "tenant": {
            "code": "MYCOMPANY",
            "name": "My Company Tenant",
            "subscription_tier": "premium",
            "max_companies": 1,
            "max_users": 100
        },
        "company": {
            "code": "MYCOMPANY",
            "name": "My Company Inc.",
            "description": "Description"
        },
        "branches": [
            {"code": "HQ", "name": "Headquarters", "description": "Main office"}
        ],
        "departments": [
            {"code": "DEPT1", "name": "Department 1", "branch": "HQ"}
        ],
        "users": [
            {
                "email": "user@mycompany.com",
                "name": "User Name",
                "is_superuser": False,
                "dept": "DEPT1",
                "branch": "HQ"
            }
        ]
    }
}
```

### Modify User Count

Add more users to any scenario:

```python
"users": [
    {"email": "user1@company.com", "name": "User 1", "is_superuser": False, "dept": "ENG"},
    {"email": "user2@company.com", "name": "User 2", "is_superuser": False, "dept": "ENG"},
    # ... add as many as needed
]
```

## Troubleshooting

### Migration Errors

If you get foreign key errors:

```bash
# Check migration status
alembic current

# Upgrade to latest
alembic upgrade head

# If issues persist, check migration order in versions/
ls -l backend/app/alembic/versions/pg_*.py
```

### Seed Script Errors

If seeding fails:

1. **Check database connection:**
   ```python
   # In app/core/db.py
   SQLALCHEMY_DATABASE_URL = "postgresql://user:pass@localhost/dbname"
   ```

2. **Clear data and retry:**
   ```bash
   python -m app.seeds.seed_complete_org
   # Answer "yes" to clear existing data
   ```

3. **Check for unique constraint violations:**
   - Ensure tenant codes are unique
   - Ensure company codes are unique per tenant
   - Ensure user emails are unique

### Login Failures

If authentication fails:

1. **Verify user exists:**
   ```sql
   SELECT email, is_active, is_verified FROM users WHERE email = 'ceo@techstart.com';
   ```

2. **Check password:**
   - All seeded users have password: `password123`
   - Superuser password: `SuperAdmin123!`

3. **Verify JWT configuration:**
   ```python
   # In app/core/config.py
   SECRET_KEY = "..." # Should be set
   ACCESS_TOKEN_EXPIRE_MIN = 30
   ```

## Data Volume

After running the seed script with all 5 scenarios:

- **Tenants:** 5
- **Companies:** 5
- **Branches:** ~20
- **Departments:** ~50
- **Users:** ~25
- **Settings:** ~30

Total database size: < 5 MB

## Next Steps

1. **Implement RBAC:**
   - Create Permissions
   - Create Roles
   - Assign Permissions to Roles
   - Assign Roles to Users/Groups

2. **Add Multi-Company Access:**
   - Create UserCompanyAccess records
   - Test user access to multiple companies
   - Implement company switching

3. **Test Features:**
   - Audit logging
   - Token revocation
   - Permission checks
   - Tenant isolation

4. **Performance Testing:**
   - Query performance with tenant filters
   - Index effectiveness
   - Multi-tenant data separation

## References

- [Multi-Tenant Architecture Documentation](./MODELS_UPDATE_SUMMARY.md)
- [Security Documentation](./SECURITY.md)
- [Token Revocation](./TOKEN_REVOCATION.md)
- [API Documentation](/api/docs)

---

**Last Updated:** 2025-10-27
**Version:** 1.0.0
