# RBAC SQL Cleanup Scripts

Quick reference for cleaning up deprecated RBAC data and verifying group assignments.

---

## 📋 Available Scripts

| Script | Purpose | Safe to Run |
|--------|---------|-------------|
| `verify_rbac.sql` | Quick verification - shows users without groups | ✅ Yes (read-only) |
| `cleanup_rbac.sql` | Comprehensive analysis and optional cleanup | ✅ Yes (cleanup commented out) |
| `cleanup_user_roles.sql` | Interactive cleanup of deprecated user_roles | ⚠️ Destructive (has safety checks) |

---

## 🚀 Quick Start

### Option 1: Using manage.sh (Recommended)

```bash
# Verify all users are in groups
./manage.sh db-shell postgres
\i backend/app/seeds/verify_rbac.sql
\q
```

### Option 2: Direct psql

```bash
# PostgreSQL
psql -U appuser -d appdb -f backend/app/seeds/verify_rbac.sql

# Or via Docker
docker compose -f infra/docker-compose.dev.yml exec postgres psql -U appuser -d appdb -f /app/backend/app/seeds/verify_rbac.sql
```

---

## 📊 1. verify_rbac.sql (Quick Check)

**Purpose:** Quick read-only verification of RBAC state.

### What it checks:

✅ Users without groups (should be empty)
✅ Summary counts (users, groups, permissions)
✅ Permission count per user
✅ Safety status

### Usage:

```bash
# Via manage.sh
./manage.sh db-shell postgres
\i backend/app/seeds/verify_rbac.sql

# Expected output:
1. Users without groups (should be empty):
   (empty result = good)

2. Summary:
   total_users | users_in_groups | deprecated_user_roles | active_groups
   ------------|-----------------|----------------------|---------------
   25          | 25              | 15                   | 10

3. Permissions per user (via groups):
   email                  | group_count | role_count | permission_count
   -----------------------|-------------|------------|------------------
   admin@company.com      | 1           | 1          | 25
   user@company.com       | 1           | 1          | 3

4. SAFETY CHECK:
   ✓ SAFE - All users are in groups
```

### Interpreting Results:

| Status | Action |
|--------|--------|
| "✓ SAFE - All users are in groups" | Safe to proceed with cleanup |
| "✗ UNSAFE - Some users have no groups!" | Run `./manage.sh seed-rbac` first |

---

## 🔍 2. cleanup_rbac.sql (Comprehensive Analysis)

**Purpose:** Detailed analysis with optional cleanup (commented out by default).

### What it does:

📊 Section 1: Current state analysis
📊 Section 2: Group-based permissions verification
📊 Section 3: Comparison of old vs new permissions
📊 Section 4: Pre-cleanup checklist
💾 Section 5: Creates backup table
🗑️ Section 6: Cleanup (commented out - requires manual uncommenting)
✅ Section 7: Post-cleanup verification

### Usage:

```bash
# Run full analysis
./manage.sh db-shell postgres
\i backend/app/seeds/cleanup_rbac.sql

# Or via psql
psql -U appuser -d appdb -f backend/app/seeds/cleanup_rbac.sql
```

### Key Sections:

#### Section 3.2 - Most Important!

Shows users who would **LOSE permissions** if we delete user_roles:

```sql
3.2 Users who would LOSE permissions if we only use groups:
   (These users need group assignments before cleanup!)

email                  | permissions_that_would_be_lost | lost_permissions
-----------------------|--------------------------------|------------------
user@example.com       | 5                              | users:read, ...
```

**If this shows any users:** Run `./manage.sh seed-rbac` to assign them to groups first!

#### Section 4.2 - Safety Check

```sql
4.2 SAFETY CHECK - Users without groups (MUST BE ZERO!)
✓ SAFE TO PROCEED - All users are in groups
```

or

```sql
✗ DANGER - 3 users have NO groups! Assign them first!
```

### To Actually Delete:

1. Review all sections
2. Ensure Section 3.2 is empty (no users losing permissions)
3. Ensure Section 4.2 shows "SAFE TO PROCEED"
4. Uncomment this line in Section 6:

```sql
-- DELETE FROM user_roles;  ← UNCOMMENT THIS LINE
```

5. Run the script again

---

## 🗑️ 3. cleanup_user_roles.sql (Interactive Cleanup)

**Purpose:** Safe, interactive deletion of deprecated user_roles with built-in safety checks.

### Features:

✅ Automatic safety check (aborts if users have no groups)
✅ Creates backup table automatically
✅ Shows what will be deleted
✅ Requires confirmation before deletion
✅ Post-cleanup verification

### Usage:

```bash
# Interactive cleanup
./manage.sh db-shell postgres
\i backend/app/seeds/cleanup_user_roles.sql
```

### Workflow:

```
Step 1: Safety check
   ✓ SAFE: All users are in groups

Step 2: Creating backup...
   ✓ Backup created: user_roles_backup

Step 3: Records to be deleted:
   user_roles_to_delete: 15

Step 4: Users affected:
   email                  | role_assignments
   -----------------------|------------------
   admin@company.com      | 3
   user@company.com       | 2

Step 5: Confirmation
   ⚠️  Are you sure you want to delete these records?
   ⚠️  Press Ctrl+C to cancel, or press Enter to continue...
   [Press Enter]

Step 6: Deletion
   ✓ Deleted deprecated user_roles records

Step 7: Verification
   remaining_user_roles | backed_up_records
   ---------------------|-------------------
   0                    | 15

CLEANUP COMPLETE!
```

### If Something Goes Wrong:

Restore from backup:

```sql
-- Restore deleted records
INSERT INTO user_roles SELECT * FROM user_roles_backup;

-- Verify
SELECT COUNT(*) FROM user_roles;

-- Drop backup when satisfied
DROP TABLE user_roles_backup;
```

---

## 🔄 Complete Cleanup Workflow

### Step 1: Ensure Users are in Groups

```bash
# Run RBAC seed to assign users to groups
./manage.sh seed-rbac
```

### Step 2: Verify

```bash
# Quick verification
./manage.sh db-shell postgres
\i backend/app/seeds/verify_rbac.sql
\q
```

Expected output:
- ✓ Users without groups: (empty)
- ✓ SAFETY CHECK: SAFE

### Step 3: Comprehensive Analysis (Optional)

```bash
./manage.sh db-shell postgres
\i backend/app/seeds/cleanup_rbac.sql
\q
```

Review all sections, especially:
- Section 3.2 (users losing permissions - should be empty)
- Section 4.2 (safety check - should be SAFE)

### Step 4: Backup Database (Recommended)

```bash
./manage.sh backup
```

### Step 5: Cleanup

**Option A: Interactive (Recommended)**

```bash
./manage.sh db-shell postgres
\i backend/app/seeds/cleanup_user_roles.sql
# Follow prompts
\q
```

**Option B: Via cleanup_rbac.sql**

1. Edit `cleanup_rbac.sql`
2. Uncomment the DELETE line in Section 6
3. Run: `./manage.sh db-shell postgres`
4. Run: `\i backend/app/seeds/cleanup_rbac.sql`

### Step 6: Verify via API

```bash
# Check user permissions still work
curl http://localhost:8000/api/rbac/users/{user_id}/roles

# Should return roles via groups only
{
  "roles": [
    {
      "role_name": "tenant_admin",
      "group_name": "Administrators"  ← Shows group source
    }
  ]
}
```

### Step 7: Verify in UI

Visit: http://localhost:8080/rbac.html

Check users still have correct permissions.

### Step 8: Drop Backup (Optional)

Once satisfied everything works:

```sql
DROP TABLE user_roles_backup;
```

---

## 🛡️ Safety Features

All scripts include safety checks:

1. **verify_rbac.sql**
   - Read-only, completely safe

2. **cleanup_rbac.sql**
   - Cleanup is commented out by default
   - Creates backup before deletion
   - Shows detailed comparison

3. **cleanup_user_roles.sql**
   - Aborts if users have no groups
   - Creates automatic backup
   - Requires manual confirmation
   - Shows what will be deleted

---

## ❓ FAQ

### Q: Do I need to run cleanup?

**A:** No, it's optional. The system works fine with deprecated user_roles records (they're just ignored).

### Q: What if users don't have groups?

**A:** Run `./manage.sh seed-rbac` first. It auto-assigns users to groups based on email patterns.

### Q: Can I restore after deletion?

**A:** Yes, all cleanup scripts create `user_roles_backup` table. Restore with:
```sql
INSERT INTO user_roles SELECT * FROM user_roles_backup;
```

### Q: Will users lose permissions?

**A:** No, if they're properly assigned to groups. The scripts verify this before deletion.

### Q: How do I check if cleanup worked?

**A:**
1. Run `verify_rbac.sql` - should show 0 deprecated_user_roles
2. Check API: `GET /api/rbac/users/{user_id}/roles`
3. Check UI: http://localhost:8080/rbac.html

---

## 📞 Troubleshooting

### "UNSAFE - Some users have no groups!"

**Solution:**
```bash
./manage.sh seed-rbac
```

This automatically assigns users to groups based on email patterns.

### "X users would LOSE permissions"

**Solution:**
These users have direct role assignments but no group assignments.

1. Identify which users: See Section 3.2 of `cleanup_rbac.sql`
2. Manually add them to appropriate groups:

```sql
-- Find appropriate group
SELECT * FROM groups WHERE is_active = true;

-- Add user to group
INSERT INTO user_groups (id, user_id, group_id, created_at)
VALUES (
    gen_random_uuid(),
    'user-uuid-here',
    'group-uuid-here',
    NOW()
);
```

3. Run verification again

### Restore from Backup

```sql
-- If cleanup went wrong
TRUNCATE user_roles;
INSERT INTO user_roles SELECT * FROM user_roles_backup;

-- Verify
SELECT COUNT(*) FROM user_roles;
```

---

## 📝 Summary

| Task | Command |
|------|---------|
| Quick verification | `\i backend/app/seeds/verify_rbac.sql` |
| Full analysis | `\i backend/app/seeds/cleanup_rbac.sql` |
| Interactive cleanup | `\i backend/app/seeds/cleanup_user_roles.sql` |
| Assign users to groups | `./manage.sh seed-rbac` |
| Backup database | `./manage.sh backup` |
| Restore from backup | See scripts above |

---

**Remember:** Cleanup is optional. The system works correctly without it!
