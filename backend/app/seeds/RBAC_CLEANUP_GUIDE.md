# RBAC Cleanup Guide

## Overview

After implementing the consistent group-based RBAC model (User → Group → Role → Permission), certain data structures and endpoints have become **deprecated** but are retained for backwards compatibility.

This document explains what's deprecated, what's still needed, and how to clean up if desired.

---

## ✅ What's Still Active and Used

### Database Tables (Active)

| Table | Status | Purpose |
|-------|--------|---------|
| `permissions` | ✅ Active | Stores all permission definitions |
| `roles` | ✅ Active | Stores role definitions |
| `groups` | ✅ Active | Stores group definitions |
| `role_permissions` | ✅ Active | Maps permissions to roles |
| `group_roles` | ✅ Active | Maps roles to groups (MAIN PATH) |
| `user_groups` | ✅ Active | Maps users to groups (MAIN PATH) |

### Code Files (Active)

- ✅ `backend/app/models/permission.py` - Permission model
- ✅ `backend/app/models/role.py` - Role model
- ✅ `backend/app/models/group.py` - Group model
- ✅ `backend/app/models/rbac_junctions.py` - All junction tables (including deprecated UserRole)
- ✅ `backend/app/routers/rbac.py` - RBAC API endpoints
- ✅ `backend/app/seeds/seed_rbac_with_groups.py` - **New group-based seed**
- ✅ `backend/app/seeds/seed_financial_rbac.py` - Uses groups ✓
- ✅ `backend/app/seeds/seed_menu_management_rbac.py` - Uses groups ✓
- ✅ `backend/app/seeds/seed_module_management_rbac.py` - Uses groups ✓

---

## ⚠️ What's Deprecated (But Kept for Compatibility)

### Database Tables (Deprecated)

| Table | Status | Why Kept | Impact |
|-------|--------|----------|--------|
| `user_roles` | ⚠️ **DEPRECATED** | Backwards compatibility | Records are **IGNORED** by application code |

**Explanation:**
- The `user_roles` table still exists in the database
- The `UserRole` model still exists in code
- **BUT**: The application code completely ignores this table
- `User.get_roles()` and `User.get_permissions()` only read from groups
- Any existing `user_roles` records have **no effect** on user permissions

### API Endpoints (Deprecated)

| Endpoint | Method | Status | Returns |
|----------|--------|--------|---------|
| `/rbac/users/{user_id}/roles` | POST | ⚠️ **DEPRECATED** | 400 Error with migration instructions |
| `/rbac/users/{user_id}/roles/{role_id}` | DELETE | ⚠️ **DEPRECATED** | 400 Error with migration instructions |

**Error Response:**
```json
{
  "detail": "Direct role assignment is deprecated. Please assign users to groups instead, then assign roles to those groups. Use POST /rbac/groups/{group_id}/members to add users to groups, and POST /rbac/groups/{group_id}/roles to assign roles to groups."
}
```

---

## 🗑️ Cleanup Options

### Option 1: Keep Everything (Recommended)

**Do nothing.** The system works correctly as-is:
- Old `user_roles` records are harmless (they're just ignored)
- Deprecated endpoints provide helpful error messages
- No breaking changes for anyone with old code

**Advantages:**
- ✅ Safe and backwards compatible
- ✅ Historical data preserved
- ✅ No migration needed

**Disadvantages:**
- ❌ Database has unused records
- ❌ Deprecated code still exists

---

### Option 2: Remove Old user_roles Records (Optional)

If you want to clean up the database, you can delete old `user_roles` records:

```sql
-- WARNING: Only do this if you're CERTAIN you don't need this data
-- Backup first!

-- 1. Check how many records exist
SELECT COUNT(*) FROM user_roles;

-- 2. See which users have direct role assignments
SELECT u.email, r.name
FROM user_roles ur
JOIN users u ON ur.user_id = u.id
JOIN roles r ON ur.role_id = r.id;

-- 3. Delete all user_roles records (if desired)
-- DELETE FROM user_roles;
```

**⚠️ WARNING:**
- This is **irreversible** (unless you have backups)
- Only do this if you're certain users are properly assigned to groups
- Verify user permissions before and after

**Verification Steps:**
```bash
# Before deletion - check user has permissions
GET /api/rbac/users/{user_id}/roles

# After deletion - verify permissions are same (via groups)
GET /api/rbac/users/{user_id}/roles
```

---

### Option 3: Remove Deprecated Endpoints (Not Recommended)

You could remove the deprecated POST/DELETE endpoints from `backend/app/routers/rbac.py`.

**NOT RECOMMENDED because:**
- ❌ Breaking change for any existing clients
- ❌ Error messages are helpful for migration
- ❌ Doesn't save much code (just 2 functions)

If you really want to do this:

1. Remove these functions from `backend/app/routers/rbac.py`:
   - `assign_roles_to_user()` (line ~983)
   - `remove_role_from_user()` (line ~1007)

2. Any code calling these endpoints will get 404 instead of helpful 400 error

---

### Option 4: Remove UserRole Model (Not Recommended)

You could remove the `UserRole` model entirely from the codebase.

**NOT RECOMMENDED because:**
- ❌ Database table still exists (requires migration)
- ❌ Breaks backwards compatibility completely
- ❌ Makes future data recovery impossible
- ❌ Complex migration needed

If you really want to do this:

1. Create Alembic migration to drop `user_roles` table
2. Remove `UserRole` class from `backend/app/models/rbac_junctions.py`
3. Remove `user_roles` relationship from `User` model
4. Remove `user_roles` relationship from `Role` model
5. Update all imports
6. Test thoroughly

**This is a LOT of work for minimal benefit.**

---

## 📊 Current System Status

After the RBAC consistency implementation:

### Permission Flow (Current - Correct)
```
User → UserGroup → Group → GroupRole → Role → RolePermission → Permission
```

### Old Flow (Deprecated - Ignored)
```
User → UserRole → Role → RolePermission → Permission
❌ This path is IGNORED by application code
```

---

## 🔍 How to Verify Your System

### Check if any user_roles exist:

```sql
SELECT COUNT(*) as user_role_count FROM user_roles;
```

If count > 0, those records are being ignored.

### Check user permissions are correct:

```bash
# Get user roles (should show roles via groups only)
curl http://localhost:8000/api/rbac/users/{user_id}/roles

# Should return:
{
  "roles": [
    {
      "role_name": "tenant_admin",
      "group_name": "Administrators",  ← Shows which group granted this
      ...
    }
  ]
}
```

### Verify deprecated endpoints are blocked:

```bash
# Try direct role assignment (should fail with 400)
curl -X POST http://localhost:8000/api/rbac/users/{user_id}/roles \
  -H "Content-Type: application/json" \
  -d '{"role_ids": ["..."]}'

# Should return:
{
  "detail": "Direct role assignment is deprecated. ..."
}
```

---

## 📝 Migration Checklist

If you had old direct role assignments and want to migrate:

- [ ] Run `./manage.sh seed-rbac` to create groups
- [ ] Verify users were auto-assigned to groups based on email
- [ ] Manually adjust group membership if needed via:
  - `POST /api/rbac/groups/{group_id}/members`
- [ ] Verify each user has correct permissions:
  - `GET /api/rbac/users/{user_id}/roles`
  - `GET /api/rbac/users/{user_id}/permissions`
- [ ] (Optional) Backup database
- [ ] (Optional) Delete old `user_roles` records
- [ ] Update any client code using deprecated endpoints

---

## 🎯 Recommended Action

**Do nothing.**

The system is working correctly:
- ✅ All permissions flow through groups
- ✅ Old data is harmless (ignored)
- ✅ Deprecated endpoints provide helpful errors
- ✅ Fully backwards compatible

Only clean up if:
- You have a specific need to remove old data
- You're certain all users are properly assigned to groups
- You have backups

---

## 📞 Support

If you need help:
1. Read: `backend/app/seeds/README_RBAC.md`
2. Check: API docs at http://localhost:8000/docs
3. Verify: User permissions via RBAC UI at http://localhost:8080/rbac.html

---

## Summary

| Item | Status | Action Needed |
|------|--------|---------------|
| Group-based RBAC | ✅ Active | None - working correctly |
| `user_roles` table | ⚠️ Deprecated | Optional cleanup |
| Direct assignment endpoints | ⚠️ Deprecated | None - helpful errors |
| Existing seed files | ✅ Good | None - already use groups |
| User permissions | ✅ Correct | Verify via API |

**Bottom line:** The system is consistent and working. Old data is harmless.
