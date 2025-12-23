# UI Builder RBAC Configuration

## Overview

This document describes the permissions, role, and group configuration for the UI Builder feature.

## Permissions

The UI Builder uses **8 permissions** for fine-grained access control:

| Permission Code | Name | Description |
|----------------|------|-------------|
| `builder:design:tenant` | Design UI Pages | Create and design UI pages using the builder |
| `builder:pages:read:tenant` | View Builder Pages | View list of builder pages |
| `builder:pages:create:tenant` | Create Builder Pages | Create new builder pages |
| `builder:pages:edit:tenant` | Edit Builder Pages | Edit existing builder pages |
| `builder:pages:delete:tenant` | Delete Builder Pages | Delete builder pages |
| `builder:publish:tenant` | Publish Pages | Publish builder pages to production |
| `builder:manage-permissions:tenant` | Manage Page Permissions | Assign permissions to builder pages |
| `builder:manage-menus:tenant` | Manage Page Menus | Create menu entries for builder pages |

## Role

**UI Builder Administrator** (`ui_builder_admin`)
- System role (available to all tenants)
- Has all 8 builder permissions
- Cannot be deleted (system role)

## Group Assignment

The `UI Builder Administrator` role is automatically assigned to the **Administrators** group.

All users in the Administrators group will have full access to the UI Builder.

## Setup Instructions

**Important**: Run **both** seed scripts in order to set up the UI Builder completely.

### 1. Run the RBAC Seed Script

This creates permissions, role, and assigns to the Administrators group.

```bash
# Using Docker (recommended)
docker exec -it app_buildify_backend python -m app.seeds.seed_builder_rbac

# Or from the backend directory
cd backend
python -m app.seeds.seed_builder_rbac
```

### 2. Run the Menu Seed Script

This creates menu items in the database for the UI Builder navigation.

```bash
# Using Docker (recommended)
docker exec -it app_buildify_backend python -m app.seeds.seed_builder_menu

# Or from the backend directory
cd backend
python -m app.seeds.seed_builder_menu
```

**Why both scripts?**
- The application uses a **database-driven menu system**
- Menu items must exist in the `menu_items` table to appear in navigation
- The static `menu.json` is only used as a fallback

### 3. Verify the Setup

After running both seed scripts, you should see:

```
✅ UI BUILDER RBAC SEEDED SUCCESSFULLY

What was created:
  • 8 UI Builder permissions
  • 1 UI Builder Admin role (system role)
  • Role assigned to Administrators group
```

### 3. Access the UI Builder

Users in the **Administrators** group can now access:
- **Developer Tools → UI Builder → Page Designer** - Design and create pages
- **Developer Tools → UI Builder → Manage Pages** - View and manage all pages

## Assigning to Other Groups

To give UI Builder access to other groups:

1. Navigate to: **Users & Access Control → Roles**
2. Find the **UI Builder Administrator** role
3. Assign it to any group you want

Or via SQL:

```sql
-- Find the role ID
SELECT id, name FROM roles WHERE code = 'ui_builder_admin';

-- Find the group ID
SELECT id, name FROM groups WHERE code = 'your_group_code';

-- Assign role to group
INSERT INTO group_roles (id, group_id, role_id)
VALUES (gen_random_uuid(), '<group_id>', '<role_id>');
```

## Custom Permissions

For more granular control, you can create custom roles with specific permissions:

**Example: Builder Viewer Role** (read-only access)
- `builder:pages:read:tenant`

**Example: Builder Designer Role** (can design but not publish)
- `builder:design:tenant`
- `builder:pages:read:tenant`
- `builder:pages:create:tenant`
- `builder:pages:edit:tenant`

**Example: Builder Publisher Role** (can publish pages)
- `builder:pages:read:tenant`
- `builder:publish:tenant`

## Troubleshooting

### "Administrators group not found"

Run the RBAC seed first:

```bash
python -m app.seeds.seed_rbac_with_groups
```

### Permissions not working

1. Check if the user is in the Administrators group
2. Verify the role is assigned to the group:
   ```sql
   SELECT g.name as group_name, r.name as role_name
   FROM group_roles gr
   JOIN groups g ON gr.group_id = g.id
   JOIN roles r ON gr.role_id = r.id
   WHERE r.code = 'ui_builder_admin';
   ```

3. Verify user has the permissions:
   ```sql
   SELECT DISTINCT p.code, p.name
   FROM permissions p
   JOIN role_permissions rp ON p.id = rp.permission_id
   JOIN roles r ON rp.role_id = r.id
   JOIN group_roles gr ON r.id = gr.role_id
   JOIN user_groups ug ON gr.group_id = ug.group_id
   WHERE ug.user_id = '<user_id>'
   AND p.code LIKE 'builder:%';
   ```

## Permission Scopes

All builder permissions use `tenant` scope, meaning:
- Users can only access builder pages within their own tenant
- Superusers can access builder pages across all tenants
- Company/branch/department scopes are not used for builder

## Migration Notes

The UI Builder was moved from a module to core application feature. The permissions remain the same, but:
- No longer requires module installation
- Available to all users with appropriate permissions
- Integrated into core menu under "Developer Tools"
