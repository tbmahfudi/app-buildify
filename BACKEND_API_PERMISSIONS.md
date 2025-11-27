# Backend API Endpoints and Permission Requirements

## Complete Mapping of All Backend API Functions and Required Permissions

**Generated Date:** 2025-11-27
**Application:** App-Buildify NoCode Platform
**Total Endpoints:** 180+
**Total Router Files:** 13

---

## 📋 Table of Contents

1. [Authentication & User Management](#1-authentication--user-management)
2. [RBAC Management](#2-rbac-management)
3. [Organization Management](#3-organization-management)
4. [Data Management](#4-data-management)
5. [Menu Management](#5-menu-management)
6. [Module Management](#6-module-management)
7. [Security Administration](#7-security-administration)
8. [Dashboard & Reports](#8-dashboard--reports)
9. [Scheduler & Jobs](#9-scheduler--jobs)
10. [Audit & Monitoring](#10-audit--monitoring)
11. [Settings Management](#11-settings-management)
12. [Metadata Management](#12-metadata-management)
13. [Permission Summary](#13-permission-summary)

---

## 1. Authentication & User Management

**Router:** `/backend/app/routers/auth.py`
**Base Path:** `/auth`
**Total Endpoints:** 9

### Endpoints

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| POST | `/login` | `login` | None (public) | None | User login with JWT token generation |
| GET | `/password-policy` | `get_password_policy` | None (public) | None | Get password policy requirements |
| POST | `/refresh` | `refresh` | None | None | Refresh access token using refresh token |
| GET | `/me` | `get_me` | `get_current_user` | `users:read:own` | Get current user profile with roles/permissions |
| PUT | `/me` | `update_me` | `get_current_user` | `users:update:own` | Update current user profile |
| POST | `/change-password` | `change_password` | `get_current_user` | `users:change_password:own` | Change user password with policy validation |
| POST | `/reset-password-request` | `reset_password_request` | None (public) | None | Request password reset token |
| POST | `/reset-password-confirm` | `reset_password_confirm` | None (public) | None | Confirm password reset using token |
| POST | `/logout` | `logout` | `get_current_user` | None | Logout and blacklist token |

### Recommended Permissions

```python
# User Profile Management
users:read:own              # Read own profile
users:update:own            # Update own profile
users:change_password:own   # Change own password
```

**Notes:**
- Login, refresh, password reset are public endpoints
- Profile operations are self-service (own data only)
- Password change includes history tracking and policy validation

---

## 2. RBAC Management

**Router:** `/backend/app/routers/rbac.py`
**Base Path:** `/rbac`
**Total Endpoints:** 20

### 2.1 Permission Endpoints (4)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/permissions` | `list_permissions` | `get_current_user` | `permissions:read:tenant` | List all permissions with filtering |
| GET | `/permissions/grouped` | `get_grouped_permissions` | `get_current_user` | `permissions:read:tenant` | Get permissions grouped by resource |
| GET | `/permissions/{id}` | `get_permission` | `get_current_user` | `permissions:read:tenant` | Get permission details with assigned roles |
| GET | `/permission-categories` | `get_permission_categories` | `get_current_user` | `permissions:read:tenant` | Get all permission categories |

### 2.2 Role Endpoints (5)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/roles` | `list_roles` | `get_current_user` | `roles:read:tenant` | List all roles with filtering |
| GET | `/roles/{id}` | `get_role` | `get_current_user` | `roles:read:tenant` | Get role details with permissions |
| POST | `/roles/{id}/permissions` | `assign_permissions_to_role` | `get_current_user` | `roles:assign_permissions:tenant` | Assign multiple permissions to role |
| DELETE | `/roles/{id}/permissions/{perm_id}` | `remove_permission_from_role` | `get_current_user` | `roles:revoke_permissions:tenant` | Remove permission from role |
| PATCH | `/roles/{id}/permissions/bulk` | `bulk_update_role_permissions` | `get_current_user` | `roles:assign_permissions:tenant` | Bulk grant/revoke permissions |

### 2.3 Group Endpoints (6)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/groups` | `list_groups` | `get_current_user` | `groups:read:tenant` | List all groups with filtering |
| GET | `/groups/{id}` | `get_group` | `get_current_user` | `groups:read:tenant` | Get group details with members/roles |
| POST | `/groups/{id}/members` | `add_members_to_group` | `get_current_user` | `groups:add_members:tenant` | Add multiple users to group |
| DELETE | `/groups/{id}/members/{user_id}` | `remove_member_from_group` | `get_current_user` | `groups:remove_members:tenant` | Remove user from group |
| POST | `/groups/{id}/roles` | `assign_roles_to_group` | `get_current_user` | `groups:assign_roles:tenant` | Assign multiple roles to group |
| DELETE | `/groups/{id}/roles/{role_id}` | `remove_role_from_group` | `get_current_user` | `groups:revoke_roles:tenant` | Remove role from group |

### 2.4 User RBAC Endpoints (4)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/users/{id}/roles` | `get_user_roles` | `get_current_user` | `users:read_roles:tenant` | Get all user roles (direct + groups) |
| GET | `/users/{id}/permissions` | `get_user_permissions` | `get_current_user` | `users:read_permissions:tenant` | Get all effective user permissions |
| POST | `/users/{id}/roles` | `assign_roles_to_user` | `get_current_user` | `users:assign_roles:tenant` | Assign roles directly to user |
| DELETE | `/users/{id}/roles/{role_id}` | `remove_role_from_user` | `get_current_user` | `users:revoke_roles:tenant` | Remove role from user |

### 2.5 Organization Structure (1)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/organization-structure` | `get_organization_structure` | `get_current_user` | `organization:view:tenant` | Get complete org structure |

### Recommended Permissions

```python
# Permission Management (View only for admins)
permissions:read:all            # View all permissions (superuser)
permissions:read:tenant         # View tenant permissions
permissions:create:all          # Create permissions (superuser only)
permissions:update:all          # Update permissions (superuser only)
permissions:delete:all          # Delete permissions (superuser only)

# Role Management
roles:read:all                  # View all roles (superuser)
roles:read:tenant               # View tenant roles
roles:create:tenant             # Create roles
roles:update:tenant             # Update roles
roles:delete:tenant             # Delete roles
roles:assign_permissions:tenant # Assign permissions to roles
roles:revoke_permissions:tenant # Revoke permissions from roles

# Group Management
groups:read:all                 # View all groups (superuser)
groups:read:tenant              # View tenant groups
groups:create:tenant            # Create groups
groups:update:tenant            # Update groups
groups:delete:tenant            # Delete groups
groups:add_members:tenant       # Add users to groups
groups:remove_members:tenant    # Remove users from groups
groups:assign_roles:tenant      # Assign roles to groups
groups:revoke_roles:tenant      # Revoke roles from groups

# User RBAC Operations
users:read_roles:tenant         # View user's roles
users:read_permissions:tenant   # View user's permissions
users:assign_roles:tenant       # Assign roles to users
users:revoke_roles:tenant       # Revoke roles from users

# Organization View
organization:view:tenant        # View organization structure
```

---

## 3. Organization Management

**Router:** `/backend/app/routers/org.py`
**Base Path:** `/org`
**Total Endpoints:** 21

### 3.1 Tenant Endpoints (5)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/tenants` | `list_tenants` | Superuser check | `tenants:read:all` | List all tenants |
| GET | `/tenants/{id}` | `get_tenant` | Superuser check | `tenants:read:all` | Get specific tenant |
| POST | `/tenants` | `create_tenant` | Superuser check | `tenants:create:all` | Create new tenant |
| PUT | `/tenants/{id}` | `update_tenant` | Superuser check | `tenants:update:all` | Update tenant |
| DELETE | `/tenants/{id}` | `delete_tenant` | Superuser check | `tenants:delete:all` | Soft delete tenant |

### 3.2 Company Endpoints (5)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/companies` | `list_companies` | `get_current_user` | `companies:read:tenant` | List companies with pagination |
| GET | `/companies/{id}` | `get_company` | `get_current_user` | `companies:read:tenant` | Get specific company |
| POST | `/companies` | `create_company` | `has_role("admin")` | `companies:create:tenant` | Create new company |
| PUT | `/companies/{id}` | `update_company` | `has_role("admin")` | `companies:update:tenant` | Update company |
| DELETE | `/companies/{id}` | `delete_company` | `has_role("admin")` | `companies:delete:tenant` | Delete company |

### 3.3 Branch Endpoints (5)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/branches` | `list_branches` | `get_current_user` | `branches:read:company` | List branches with filtering |
| GET | `/branches/{id}` | `get_branch` | `get_current_user` | `branches:read:company` | Get specific branch |
| POST | `/branches` | `create_branch` | `has_role("admin")` | `branches:create:company` | Create new branch |
| PUT | `/branches/{id}` | `update_branch` | `has_role("admin")` | `branches:update:company` | Update branch |
| DELETE | `/branches/{id}` | `delete_branch` | `has_role("admin")` | `branches:delete:company` | Delete branch |

### 3.4 Department Endpoints (5)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/departments` | `list_departments` | `get_current_user` | `departments:read:branch` | List departments with filtering |
| GET | `/departments/{id}` | `get_department` | `get_current_user` | `departments:read:branch` | Get specific department |
| POST | `/departments` | `create_department` | `has_role("admin")` | `departments:create:branch` | Create new department |
| PUT | `/departments/{id}` | `update_department` | `has_role("admin")` | `departments:update:branch` | Update department |
| DELETE | `/departments/{id}` | `delete_department` | `has_role("admin")` | `departments:delete:branch` | Delete department |

### 3.5 User Endpoints (1)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/users` | `list_users` | `get_current_user` | `users:read:tenant` | List users (tenant-scoped) |

### Recommended Permissions

```python
# Tenant Management (Superuser only)
tenants:read:all                # View all tenants
tenants:read:own                # View own tenant
tenants:create:all              # Create tenants
tenants:update:all              # Update any tenant
tenants:update:own              # Update own tenant
tenants:delete:all              # Delete tenants

# Company Management
companies:read:all              # View all companies (superuser)
companies:read:tenant           # View tenant companies
companies:read:own              # View own company
companies:create:tenant         # Create companies
companies:update:tenant         # Update any company in tenant
companies:update:own            # Update own company
companies:delete:tenant         # Delete companies

# Branch Management
branches:read:all               # View all branches (superuser)
branches:read:tenant            # View tenant branches
branches:read:company           # View company branches
branches:read:own               # View own branch
branches:create:company         # Create branches
branches:update:company         # Update branches
branches:update:own             # Update own branch
branches:delete:company         # Delete branches

# Department Management
departments:read:all            # View all departments (superuser)
departments:read:tenant         # View tenant departments
departments:read:branch         # View branch departments
departments:read:own            # View own department
departments:create:branch       # Create departments
departments:update:branch       # Update departments
departments:update:own          # Update own department
departments:delete:branch       # Delete departments

# User Management
users:read:all                  # View all users (superuser)
users:read:tenant               # View tenant users
users:read:company              # View company users
users:read:department           # View department users
users:create:tenant             # Create users
users:update:tenant             # Update any user
users:update:own                # Update own profile
users:delete:tenant             # Delete users
users:reset_password:tenant     # Reset user passwords
users:impersonate:all           # Impersonate users (superuser)
```

---

## 4. Data Management

**Router:** `/backend/app/routers/data.py`
**Base Path:** `/data`
**Total Endpoints:** 6

### Generic Data Endpoints

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| POST | `/{entity}/list` | `search_data` | `get_current_user` | `{entity}:read:*` | Generic data search with filters |
| GET | `/{entity}/{id}` | `get_record` | `get_current_user` | `{entity}:read:*` | Get single record by ID |
| POST | `/{entity}` | `create_record` | `get_current_user` | `{entity}:create:*` | Create new record with audit |
| PUT | `/{entity}/{id}` | `update_record` | `get_current_user` | `{entity}:update:*` | Update record with audit |
| DELETE | `/{entity}/{id}` | `delete_record` | `get_current_user` | `{entity}:delete:*` | Delete record with audit |
| POST | `/{entity}/bulk` | `bulk_operation` | `get_current_user` | `{entity}:bulk:*` | Bulk create/update/delete |

### Recommended Permissions

```python
# Generic pattern: {entity}:{action}:{scope}
# Example for 'users' entity:
users:read:tenant               # Read user records
users:create:tenant             # Create users
users:update:tenant             # Update users
users:delete:tenant             # Delete users
users:bulk:tenant               # Bulk operations

# Example for 'products' entity:
products:read:company           # Read products
products:create:company         # Create products
products:update:company         # Update products
products:delete:company         # Delete products
products:bulk:company           # Bulk operations

# Data Export (global capability)
data:export:tenant              # Export data to CSV/Excel
data:import:tenant              # Import data from files
```

**Notes:**
- Dynamic permission checking based on entity type
- Should implement metadata-driven permission validation
- Each entity should have its own permission set

---

## 5. Menu Management

**Router:** `/backend/app/routers/menu.py`
**Base Path:** `/menu`
**Total Endpoints:** 7

### Menu Endpoints

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `` | `get_user_menu` | `get_current_user` | None | Get RBAC-filtered menu for user |
| GET | `/admin` | `get_all_menu_items` | `has_permission("menu:manage:tenant")` | `menu:manage:tenant` | Get all menu items for admin |
| GET | `/{id}` | `get_menu_item` | `has_permission("menu:read:tenant")` | `menu:read:tenant` | Get specific menu item |
| POST | `` | `create_menu_item` | `has_permission("menu:create:tenant")` | `menu:create:tenant` | Create new menu item |
| PUT | `/{id}` | `update_menu_item` | `has_permission("menu:update:tenant")` | `menu:update:tenant` | Update menu item |
| DELETE | `/{id}` | `delete_menu_item` | `has_permission("menu:delete:tenant")` | `menu:delete:tenant` | Soft delete menu item |
| POST | `/reorder` | `reorder_menu_items` | `has_permission("menu:update:tenant")` | `menu:update:tenant` | Reorder menu items |

### Recommended Permissions (Already Implemented ✅)

```python
menu:read:tenant                # View menu items
menu:create:tenant              # Create menu items
menu:update:tenant              # Update menu items
menu:delete:tenant              # Delete menu items
menu:manage:tenant              # Full menu management access
```

**Notes:**
- ✅ Permissions already properly implemented
- User menu is automatically filtered by user's effective permissions
- Menu items have `permission` and `required_roles` fields

---

## 6. Module Management

**Router:** `/backend/app/routers/modules.py`
**Base Path:** `/modules`
**Total Endpoints:** 12

### Module Endpoints

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/available` | `list_available_modules` | `get_current_user` | `modules:list:tenant` | List all available modules |
| GET | `/enabled` | `list_enabled_modules` | `get_current_user` | `modules:view:tenant` | List enabled modules for tenant |
| GET | `/enabled/names` | `list_enabled_module_names` | `get_current_user` | `modules:view:tenant` | Get enabled module names |
| GET | `/enabled/all-tenants` | `list_all_tenants_modules` | `require_superuser` | `modules:view:all` | List modules across all tenants |
| GET | `/{name}` | `get_module_info` | `get_current_user` | `modules:view:tenant` | Get detailed module info |
| GET | `/{name}/manifest` | `get_module_manifest` | `get_current_user` | `modules:view:tenant` | Get module manifest |
| POST | `/install` | `install_module` | `require_superuser` | `modules:install:all` | Install module platform-wide |
| POST | `/uninstall` | `uninstall_module` | `require_superuser` | `modules:uninstall:all` | Uninstall module platform-wide |
| POST | `/enable` | `enable_module` | `get_current_user` | `modules:enable:tenant` | Enable module for tenant |
| POST | `/disable` | `disable_module` | `get_current_user` | `modules:disable:tenant` | Disable module for tenant |
| PUT | `/{name}/configuration` | `update_module_configuration` | `get_current_user` | `modules:configure:tenant` | Update module configuration |
| POST | `/sync` | `sync_modules` | `require_superuser` | `modules:sync:all` | Sync modules from filesystem |

### Recommended Permissions (Partially Implemented ✅)

```python
# Viewing (all authenticated users)
modules:list:tenant             # ✅ List available modules
modules:view:tenant             # ✅ View module details
modules:view:all                # View all modules (superuser)

# Tenant Management (tenant admin)
modules:enable:tenant           # ✅ Enable modules for tenant
modules:disable:tenant          # ✅ Disable modules for tenant
modules:configure:tenant        # ✅ Configure module settings
modules:manage:tenant           # ✅ Full module management

# Platform Management (superuser only)
modules:install:all             # ✅ Install modules platform-wide
modules:uninstall:all           # ✅ Uninstall modules platform-wide
modules:sync:all                # ✅ Sync modules from filesystem
modules:update:all              # Update module versions
modules:updates:view:all        # View available updates
modules:auto_update:all         # Configure auto-updates

# Module Development (developers)
modules:build:tenant            # Build custom modules
modules:test:tenant             # Test modules
modules:package:tenant          # Package modules
modules:publish:marketplace     # Publish to marketplace
```

**Notes:**
- ✅ Core permissions already implemented in seed scripts
- Tenant admins can enable/disable for their tenant
- Superusers can install/uninstall platform-wide

---

## 7. Security Administration

**Router:** `/backend/app/routers/admin/security.py`
**Base Path:** `/admin/security`
**Total Endpoints:** 12

### 7.1 Security Policy Endpoints (5)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/policies` | `list_security_policies` | `has_permission("security_policy:read:all")` | `security_policy:read:all` | List all security policies |
| GET | `/policies/{id}` | `get_security_policy` | `has_permission("security_policy:read:all")` | `security_policy:read:all` | Get specific security policy |
| POST | `/policies` | `create_security_policy` | `has_permission("security_policy:write:all")` | `security_policy:write:all` | Create security policy |
| PUT | `/policies/{id}` | `update_security_policy` | `has_permission("security_policy:write:all")` | `security_policy:write:all` | Update security policy |
| DELETE | `/policies/{id}` | `delete_security_policy` | `has_permission("security_policy:delete:all")` | `security_policy:delete:all` | Deactivate security policy |

### 7.2 Locked Account Endpoints (2)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/locked-accounts` | `list_locked_accounts` | `has_permission("security:view_locked_accounts:all")` | `security:view_locked_accounts:all` | List all locked accounts |
| POST | `/unlock-account` | `unlock_account` | `has_permission("security:unlock_account:all")` | `security:unlock_account:all` | Manually unlock account |

### 7.3 Session Management Endpoints (3)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/sessions` | `list_active_sessions` | `has_permission("security:view_sessions:all")` | `security:view_sessions:all` | List active sessions |
| POST | `/sessions/revoke` | `revoke_session` | `has_permission("security:revoke_session:all")` | `security:revoke_session:all` | Revoke specific session |
| POST | `/sessions/revoke-all/{user_id}` | `revoke_all_user_sessions` | `has_permission("security:revoke_session:all")` | `security:revoke_session:all` | Revoke all user sessions |

### 7.4 Login Audit Endpoints (1)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/login-attempts` | `list_login_attempts` | `has_permission("security:view_login_attempts:all")` | `security:view_login_attempts:all` | List login attempts audit |

### 7.5 Notification Endpoints (3)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/notification-config` | `list_notification_configs` | `has_permission("notification_config:read:all")` | `notification_config:read:all` | List notification configs |
| PUT | `/notification-config/{id}` | `update_notification_config` | `has_permission("notification_config:write:all")` | `notification_config:write:all` | Update notification config |
| GET | `/notification-queue` | `list_notification_queue` | `has_permission("notification_queue:read:all")` | `notification_queue:read:all` | View notification queue |

### Recommended Permissions (Already Implemented ✅)

```python
# Security Policy Management
security_policy:read:all        # ✅ View security policies
security_policy:write:all       # ✅ Create/update policies
security_policy:delete:all      # ✅ Delete policies

# Account Lockout Management
security:view_locked_accounts:all   # ✅ View locked accounts
security:unlock_account:all         # ✅ Unlock accounts

# Session Management
security:view_sessions:all      # ✅ View active sessions
security:revoke_session:all     # ✅ Revoke sessions

# Login Audit
security:view_login_attempts:all    # ✅ View login attempts

# Notification Configuration
notification_config:read:all    # ✅ View notification config
notification_config:write:all   # ✅ Update notification config
notification_queue:read:all     # ✅ View notification queue

# Additional Recommended
security:mfa:configure:tenant   # Configure MFA for tenant
security:ip_whitelist:manage:tenant # Manage IP whitelist
security:password_policy:view:tenant # View password policy
security:password_policy:update:tenant # Update password policy
```

**Notes:**
- ✅ All core security permissions already implemented
- Very granular permission checking
- Audit logging on all operations

---

## 8. Dashboard & Reports

### 8.1 Dashboard Management

**Router:** `/backend/app/routers/dashboards.py`
**Base Path:** `/dashboards`
**Total Endpoints:** 15

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| POST | `` | `create_dashboard` | `get_current_user` | `dashboards:create:tenant` | Create new dashboard |
| GET | `` | `list_dashboards` | `get_current_user` | `dashboards:read:tenant` | List accessible dashboards |
| GET | `/{id}` | `get_dashboard` | `get_current_user` | `dashboards:read:tenant` | Get specific dashboard |
| PUT | `/{id}` | `update_dashboard` | `get_current_user` | `dashboards:update:own` | Update dashboard |
| DELETE | `/{id}` | `delete_dashboard` | `get_current_user` | `dashboards:delete:own` | Soft delete dashboard |
| POST | `/{id}/clone` | `clone_dashboard` | `get_current_user` | `dashboards:clone:tenant` | Clone existing dashboard |
| POST | `/pages` | `create_page` | `get_current_user` | `dashboards:create_page:tenant` | Create dashboard page |
| PUT | `/pages/{page_id}` | `update_page` | `get_current_user` | `dashboards:update_page:own` | Update dashboard page |
| DELETE | `/pages/{page_id}` | `delete_page` | `get_current_user` | `dashboards:delete_page:own` | Delete dashboard page |
| POST | `/widgets` | `create_widget` | `get_current_user` | `dashboards:create_widget:tenant` | Create widget |
| PUT | `/widgets/{widget_id}` | `update_widget` | `get_current_user` | `dashboards:update_widget:own` | Update widget |
| DELETE | `/widgets/{widget_id}` | `delete_widget` | `get_current_user` | `dashboards:delete_widget:own` | Delete widget |
| POST | `/widgets/bulk-update` | `bulk_update_widgets` | `get_current_user` | `dashboards:update_widget:own` | Bulk update widget positions |
| POST | `/widgets/data` | `get_widget_data` | `get_current_user` | `dashboards:read:tenant` | Get widget data |
| POST | `/shares` | `create_share` | `get_current_user` | `dashboards:share:tenant` | Share dashboard |
| POST | `/snapshots` | `create_snapshot` | `get_current_user` | `dashboards:snapshot:tenant` | Create dashboard snapshot |

### 8.2 Report Management

**Router:** `/backend/app/routers/reports.py`
**Base Path:** `/reports`
**Total Endpoints:** 14

#### Report Definitions (5)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| POST | `/definitions` | `create_report_definition` | `get_current_user` | `reports:create:tenant` | Create report definition |
| GET | `/definitions` | `list_report_definitions` | `get_current_user` | `reports:read:tenant` | List accessible reports |
| GET | `/definitions/{id}` | `get_report_definition` | `get_current_user` | `reports:read:tenant` | Get report definition |
| PUT | `/definitions/{id}` | `update_report_definition` | `get_current_user` | `reports:update:own` | Update report definition |
| DELETE | `/definitions/{id}` | `delete_report_definition` | `get_current_user` | `reports:delete:own` | Soft delete report |

#### Report Execution (3)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| POST | `/execute` | `execute_report` | `get_current_user` | `reports:execute:tenant` | Execute report |
| POST | `/execute/export` | `execute_and_export_report` | `get_current_user` | `reports:export:tenant` | Execute and export report |
| GET | `/executions/history` | `get_execution_history` | `get_current_user` | `reports:history:read:tenant` | Get execution history |

#### Report Schedules (4)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| POST | `/schedules` | `create_report_schedule` | `get_current_user` | `reports:schedule:create:tenant` | Create report schedule |
| GET | `/schedules` | `list_report_schedules` | `get_current_user` | `reports:schedule:read:tenant` | List report schedules |
| PUT | `/schedules/{id}` | `update_report_schedule` | `get_current_user` | `reports:schedule:update:own` | Update report schedule |
| DELETE | `/schedules/{id}` | `delete_report_schedule` | `get_current_user` | `reports:schedule:delete:own` | Delete report schedule |

#### Report Templates & Lookup (2)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/templates` | `list_report_templates` | `get_current_user` | `reports:templates:read:tenant` | List report templates |
| POST | `/templates/{id}/use` | `create_from_template` | `get_current_user` | `reports:create:tenant` | Create from template |
| POST | `/lookup` | `get_lookup_data` | `get_current_user` | `reports:read:tenant` | Get lookup data for params |

### Recommended Permissions

```python
# Dashboard Management
dashboards:read:all             # View all dashboards (admin)
dashboards:read:tenant          # View tenant dashboards
dashboards:read:own             # View own dashboards
dashboards:create:tenant        # Create dashboards
dashboards:update:all           # Update any dashboard (admin)
dashboards:update:own           # Update own dashboards
dashboards:delete:all           # Delete any dashboard (admin)
dashboards:delete:own           # Delete own dashboards
dashboards:clone:tenant         # Clone dashboards
dashboards:share:tenant         # Share dashboards
dashboards:snapshot:tenant      # Create snapshots
dashboards:export:tenant        # Export dashboards

# Dashboard Pages
dashboards:create_page:tenant   # Create pages
dashboards:update_page:own      # Update own pages
dashboards:delete_page:own      # Delete own pages

# Dashboard Widgets
dashboards:create_widget:tenant # Create widgets
dashboards:update_widget:own    # Update own widgets
dashboards:delete_widget:own    # Delete own widgets

# Report Management
reports:read:all                # View all reports (admin)
reports:read:tenant             # View tenant reports
reports:read:own                # View own reports
reports:create:tenant           # Create reports
reports:update:all              # Update any report (admin)
reports:update:own              # Update own reports
reports:delete:all              # Delete any report (admin)
reports:delete:own              # Delete own reports

# Report Execution
reports:execute:all             # Execute any report (admin)
reports:execute:tenant          # Execute tenant reports
reports:execute:own             # Execute own reports
reports:export:tenant           # Export report results
reports:history:read:tenant     # View execution history

# Report Scheduling
reports:schedule:create:tenant  # Create schedules
reports:schedule:read:tenant    # View schedules
reports:schedule:update:own     # Update own schedules
reports:schedule:delete:own     # Delete own schedules

# Report Templates
reports:templates:read:tenant   # View templates
reports:templates:create:tenant # Create templates
reports:templates:update:tenant # Update templates
reports:templates:delete:tenant # Delete templates
```

---

## 9. Scheduler & Jobs

**Router:** `/backend/app/routers/scheduler.py`
**Base Path:** `/scheduler`
**Total Endpoints:** 13

### 9.1 Scheduler Configuration (5)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| POST | `/configs` | `create_scheduler_config` | `get_current_user` | `scheduler:config:create:tenant` | Create scheduler config |
| GET | `/configs/effective` | `get_effective_config` | `get_current_user` | `scheduler:config:read:tenant` | Get effective config |
| GET | `/configs/{id}` | `get_scheduler_config` | `get_current_user` | `scheduler:config:read:tenant` | Get specific config |
| PUT | `/configs/{id}` | `update_scheduler_config` | `get_current_user` | `scheduler:config:update:tenant` | Update config |
| DELETE | `/configs/{id}` | `delete_scheduler_config` | `get_current_user` | `scheduler:config:delete:tenant` | Delete config |

### 9.2 Scheduled Jobs (6)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| POST | `/jobs` | `create_scheduler_job` | `get_current_user` | `scheduler:jobs:create:tenant` | Create scheduled job |
| GET | `/jobs` | `list_scheduler_jobs` | `get_current_user` | `scheduler:jobs:read:tenant` | List scheduled jobs |
| GET | `/jobs/{id}` | `get_scheduler_job` | `get_current_user` | `scheduler:jobs:read:tenant` | Get specific job |
| PUT | `/jobs/{id}` | `update_scheduler_job` | `get_current_user` | `scheduler:jobs:update:own` | Update job |
| DELETE | `/jobs/{id}` | `delete_scheduler_job` | `get_current_user` | `scheduler:jobs:delete:own` | Delete job |
| POST | `/jobs/{id}/execute` | `execute_job_manually` | `get_current_user` | `scheduler:jobs:execute:tenant` | Manually trigger job |

### 9.3 Job Executions (3)

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/jobs/{id}/executions` | `list_job_executions` | `get_current_user` | `scheduler:executions:read:tenant` | Get job execution history |
| GET | `/executions/{id}` | `get_job_execution` | `get_current_user` | `scheduler:executions:read:tenant` | Get specific execution |
| GET | `/executions/{id}/logs` | `get_execution_logs` | `get_current_user` | `scheduler:executions:read:tenant` | Get execution logs |

### Recommended Permissions

```python
# Scheduler Configuration
scheduler:config:read:all       # View all configs (admin)
scheduler:config:read:tenant    # View tenant configs
scheduler:config:create:tenant  # Create configs
scheduler:config:update:tenant  # Update configs
scheduler:config:delete:tenant  # Delete configs

# Scheduled Jobs
scheduler:jobs:read:all         # View all jobs (admin)
scheduler:jobs:read:tenant      # View tenant jobs
scheduler:jobs:read:own         # View own jobs
scheduler:jobs:create:tenant    # Create jobs
scheduler:jobs:update:all       # Update any job (admin)
scheduler:jobs:update:own       # Update own jobs
scheduler:jobs:delete:all       # Delete any job (admin)
scheduler:jobs:delete:own       # Delete own jobs
scheduler:jobs:execute:all      # Execute any job (admin)
scheduler:jobs:execute:tenant   # Execute tenant jobs
scheduler:jobs:execute:own      # Execute own jobs

# Job Executions
scheduler:executions:read:all   # View all executions (admin)
scheduler:executions:read:tenant # View tenant executions
scheduler:executions:read:own   # View own executions
scheduler:executions:cancel:tenant # Cancel running jobs
```

---

## 10. Audit & Monitoring

**Router:** `/backend/app/routers/audit.py`
**Base Path:** `/audit`
**Total Endpoints:** 4

### Audit Endpoints

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| POST | `/list` | `list_audit_logs` | `get_current_user` | `audit:read:tenant` | List audit logs with filters |
| GET | `/summary` | `get_audit_summary_short` | `has_role("admin")` | `audit:summary:read:tenant` | Get audit summary (short) |
| GET | `/stats/summary` | `get_audit_summary` | `has_role("admin")` | `audit:summary:read:tenant` | Get audit statistics |
| GET | `/{log_id}` | `get_audit_log` | `get_current_user` | `audit:read:tenant` | Get specific audit log |

### Recommended Permissions

```python
# Audit Logs
audit:read:all                  # View all audit logs (superuser)
audit:read:tenant               # View tenant audit logs
audit:read:company              # View company audit logs
audit:read:department           # View department audit logs
audit:read:own                  # View own audit trail
audit:summary:read:all          # View audit summaries (admin)
audit:summary:read:tenant       # View tenant summaries
audit:export:all                # Export all audit logs (admin)
audit:export:tenant             # Export tenant audit logs
audit:delete:all                # Delete audit logs (superuser only)

# System Logs
logs:read:all                   # View system logs (superuser)
logs:download:all               # Download log files
logs:delete:all                 # Delete old logs

# API Activity
api_activity:read:all           # View all API activity (admin)
api_activity:read:tenant        # View tenant API activity
api_activity:metrics:tenant     # View API metrics

# Analytics
analytics:read:all              # View all analytics (admin)
analytics:read:tenant           # View tenant analytics
analytics:export:tenant         # Export analytics data
```

---

## 11. Settings Management

**Router:** `/backend/app/routers/settings.py`
**Base Path:** `/settings`
**Total Endpoints:** 4

### Settings Endpoints

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/user` | `get_user_settings` | `get_current_user` | `settings:read:own` | Get user settings |
| PUT | `/user` | `update_user_settings` | `get_current_user` | `settings:update:own` | Update user settings |
| GET | `/tenant` | `get_tenant_settings` | `get_current_user` | `settings:read:tenant` | Get tenant settings |
| PUT | `/tenant` | `update_tenant_settings` | `has_role("admin")` | `settings:update:tenant` | Update tenant settings |

### Recommended Permissions

```python
# User Settings
settings:read:own               # Read own settings
settings:update:own             # Update own settings (theme, language, etc.)

# Tenant Settings
settings:read:all               # Read all settings (superuser)
settings:read:tenant            # Read tenant settings
settings:update:all             # Update all settings (superuser)
settings:update:tenant          # Update tenant settings (admin)

# Branding
settings:branding:read:tenant   # View branding settings
settings:branding:update:tenant # Update branding (logo, colors)

# Integration Settings
settings:integration:read:tenant    # View integrations
settings:integration:update:tenant  # Configure integrations

# API Keys
settings:api_keys:read:tenant   # View API keys
settings:api_keys:create:tenant # Generate API keys
settings:api_keys:revoke:tenant # Revoke API keys
settings:api_keys:delete:tenant # Delete API keys

# Email Configuration
settings:email:read:tenant      # View email config
settings:email:update:tenant    # Update email config
settings:email:test:tenant      # Send test emails

# SMS Configuration
settings:sms:read:tenant        # View SMS config
settings:sms:update:tenant      # Update SMS config
settings:sms:test:tenant        # Send test SMS
```

---

## 12. Metadata Management

**Router:** `/backend/app/routers/metadata.py`
**Base Path:** `/metadata`
**Total Endpoints:** 5

### Metadata Endpoints

| Method | Path | Function | Current Permission | Recommended Permission | Description |
|--------|------|----------|-------------------|----------------------|-------------|
| GET | `/entities` | `list_entities` | `get_current_user` | `metadata:read:tenant` | List all entities |
| GET | `/entities/{name}` | `get_entity_metadata` | `get_current_user` | `metadata:read:tenant` | Get entity metadata |
| POST | `/entities` | `create_entity_metadata` | `has_role("admin")` | `metadata:create:tenant` | Create entity metadata |
| PUT | `/entities/{name}` | `update_entity_metadata` | `has_role("admin")` | `metadata:update:tenant` | Update entity metadata |
| DELETE | `/entities/{name}` | `delete_entity_metadata` | `has_role("admin")` | `metadata:delete:tenant` | Soft delete metadata |

### Recommended Permissions

```python
# Metadata Management
metadata:read:all               # View all metadata (superuser)
metadata:read:tenant            # View tenant metadata
metadata:create:tenant          # Create entity metadata
metadata:update:tenant          # Update entity metadata
metadata:delete:tenant          # Delete entity metadata

# Schema Design
metadata:schema:design:tenant   # Design database schemas
metadata:schema:deploy:tenant   # Deploy schema changes
metadata:schema:export:tenant   # Export schemas

# Field Customization
metadata:fields:create:tenant   # Add custom fields
metadata:fields:update:tenant   # Update field definitions
metadata:fields:delete:tenant   # Remove custom fields
```

---

## 13. Permission Summary

### 13.1 Permission Statistics

**Total Recommended Permissions:** 280+

**Breakdown by Category:**
- **User Management:** 17 permissions
- **Role Management:** 10 permissions
- **Permission Management:** 6 permissions
- **Group Management:** 12 permissions
- **Organization Management:** 30 permissions
- **Menu Management:** 5 permissions (✅ implemented)
- **Module Management:** 15 permissions (✅ partially implemented)
- **Security Management:** 17 permissions (✅ implemented)
- **Dashboard Management:** 15 permissions
- **Report Management:** 20 permissions
- **Scheduler Management:** 15 permissions
- **Audit & Monitoring:** 15 permissions
- **Settings Management:** 20 permissions
- **Metadata Management:** 10 permissions
- **Data Management:** 50+ permissions (dynamic per entity)

### 13.2 Permission Implementation Status

#### ✅ Fully Implemented (45 permissions)
- Menu Management (5)
- Module Management (8)
- Security Policy (12)
- Notifications (3)
- Login Attempts (1)
- Sessions (2)
- Locked Accounts (2)
- Financial Module (20) - example implementation

#### ⚠️ Partially Implemented
- RBAC endpoints use `get_current_user` but should use granular permissions
- Organization endpoints use `has_role("admin")` but should use specific permissions
- Data endpoints need entity-specific permission validation

#### ❌ Not Implemented
- Dashboard permissions
- Report permissions
- Scheduler permissions
- Audit permissions (beyond basic read)
- Settings permissions (beyond basic read/write)
- Metadata permissions

### 13.3 Permission Scope Hierarchy

```
all           (Superuser - platform-wide)
  ↓
tenant        (Tenant Admin - entire tenant)
  ↓
company       (Company Manager - within company)
  ↓
branch        (Branch Manager - within branch)
  ↓
department    (Department Head - within department)
  ↓
team          (Team Lead - within team)
  ↓
own           (User - own records only)
```

### 13.4 Permission Format

**Standard Format:** `resource:action:scope`

**Examples:**
```python
# User Management
users:read:tenant               # Read users in tenant
users:create:company            # Create users in company
users:update:own                # Update own profile

# Financial
financial:invoices:approve:company      # Approve invoices in company
financial:reports:export:branch         # Export reports for branch

# Module Management
modules:install:all             # Install modules platform-wide
modules:enable:tenant           # Enable module for tenant
```

### 13.5 Recommended Role Templates with Permissions

#### 1. Superuser (Platform Administrator)
```python
# Grants: all:*:all
- Full access to all resources and scopes
- Tenant management
- Module installation
- System configuration
```

#### 2. Tenant Administrator
```python
# Organization Management
companies:*:tenant
branches:*:tenant
departments:*:tenant

# User & Access Management
users:*:tenant
roles:*:tenant
groups:*:tenant
roles:assign_permissions:tenant
users:assign_roles:tenant

# Settings & Configuration
settings:*:tenant
menu:*:tenant
modules:enable:tenant
modules:disable:tenant
modules:configure:tenant

# Security & Audit
security_policy:*:all
audit:read:tenant
audit:export:tenant

# Dashboard & Reports
dashboards:*:tenant
reports:*:tenant
scheduler:*:tenant
```
**Total:** ~80 permissions

#### 3. Company Manager
```python
# Organization (scoped to company)
branches:*:company
departments:*:company
users:read:company
users:create:company

# Data Management
{entities}:*:company

# Reports
reports:read:company
reports:execute:company
reports:export:company

# Dashboard
dashboards:read:company
dashboards:create:company
```
**Total:** ~40 permissions

#### 4. Department Manager
```python
# Organization (scoped to department)
users:read:department
users:update:department

# Data Management
{entities}:read:department
{entities}:update:department

# Reports
reports:read:department
reports:execute:department
```
**Total:** ~25 permissions

#### 5. Regular User (Employee)
```python
# Own Profile
users:read:own
users:update:own
users:change_password:own

# View Access
dashboards:read:own
reports:read:own
reports:execute:own

# Settings
settings:read:own
settings:update:own

# Data (limited)
{entities}:read:own
{entities}:update:own
```
**Total:** ~15 permissions

#### 6. Security Administrator
```python
# Security Management
security_policy:*:all
security:*:all

# User Access
users:read:tenant
users:reset_password:tenant
users:assign_roles:tenant
users:revoke_roles:tenant

# Audit & Monitoring
audit:*:tenant
logs:read:all
api_activity:*:tenant
analytics:read:tenant

# Session Management
security:view_sessions:all
security:revoke_session:all
```
**Total:** ~30 permissions

#### 7. Module Administrator
```python
# Module Management
modules:*:tenant
modules:install:all (if superuser)
modules:uninstall:all (if superuser)

# Integration
settings:integration:*:tenant

# Audit
audit:read:tenant
```
**Total:** ~15 permissions

#### 8. Report Developer
```python
# Report Management
reports:*:tenant
dashboards:*:tenant

# Scheduler
scheduler:*:tenant

# Data Access
{entities}:read:tenant

# Metadata
metadata:read:tenant

# Audit
audit:read:own
```
**Total:** ~20 permissions

#### 9. Auditor (Read-only)
```python
# Audit Access
audit:read:all
audit:export:all
logs:read:all
api_activity:read:all
analytics:read:all

# Security (read-only)
security_policy:read:all
security:view_locked_accounts:all
security:view_sessions:all
security:view_login_attempts:all

# User Access (read-only)
users:read:tenant
roles:read:tenant
groups:read:tenant
permissions:read:tenant
```
**Total:** ~15 permissions

---

## 14. Implementation Roadmap

### Phase 1: Core RBAC (✅ Mostly Complete)
- [x] Menu permissions
- [x] Module permissions
- [x] Security permissions
- [x] Basic user authentication
- [ ] Implement granular RBAC checks in endpoints

### Phase 2: Organization & User Management
- [ ] Create organization permissions
- [ ] Implement tenant/company/branch/department permissions
- [ ] Add user management permissions
- [ ] Update endpoints to use granular permissions instead of `has_role("admin")`

### Phase 3: Data & Content Management
- [ ] Dashboard permissions
- [ ] Report permissions
- [ ] Scheduler permissions
- [ ] Entity-specific permissions (dynamic)

### Phase 4: Advanced Features
- [ ] Metadata management permissions
- [ ] Settings permissions (granular)
- [ ] Audit export permissions
- [ ] API key management permissions

### Phase 5: Documentation & Testing
- [ ] Document all permissions
- [ ] Create permission testing suite
- [ ] Build permission assignment UI
- [ ] Create role templates in database

---

## 15. Migration Scripts

### Creating New Permissions

```python
# Example: Create dashboard permissions
from app.models.permission import Permission

dashboard_permissions = [
    {
        "code": "dashboards:read:tenant",
        "name": "View Dashboards",
        "description": "View dashboards within tenant",
        "resource": "dashboards",
        "action": "read",
        "scope": "tenant",
        "category": "dashboard"
    },
    {
        "code": "dashboards:create:tenant",
        "name": "Create Dashboards",
        "description": "Create new dashboards",
        "resource": "dashboards",
        "action": "create",
        "scope": "tenant",
        "category": "dashboard"
    },
    # ... more permissions
]

for perm_data in dashboard_permissions:
    perm = Permission(**perm_data, is_active=True)
    db.add(perm)
db.commit()
```

### Updating Endpoint to Use Permissions

**Before:**
```python
@router.get("/dashboards")
def list_dashboards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Manual permission check
    if not current_user.is_superuser:
        # filter by tenant
    return dashboards
```

**After:**
```python
@router.get("/dashboards")
def list_dashboards(
    current_user: User = Depends(has_permission("dashboards:read:tenant")),
    db: Session = Depends(get_db)
):
    # Automatic permission check via dependency
    # No manual check needed
    return dashboards
```

---

## 16. Best Practices

### 16.1 Permission Naming Conventions

✅ **Good:**
```python
users:create:tenant
financial:invoices:approve:company
reports:export:department
```

❌ **Bad:**
```python
CreateUser                      # Not following format
user_create                     # Wrong separator
manage_all_users               # Too broad
```

### 16.2 Scope Selection

- Use **most restrictive scope** that makes sense
- Prefer `tenant` over `all` when possible
- Use `own` for self-service operations
- Use hierarchical scopes (company → branch → department)

### 16.3 Permission Granularity

**Too Coarse (Bad):**
```python
users:manage:tenant             # Too broad - manage means what?
```

**Too Fine (Bad):**
```python
users:update:email:tenant       # Too granular
users:update:name:tenant
users:update:phone:tenant
```

**Just Right (Good):**
```python
users:read:tenant
users:create:tenant
users:update:tenant
users:delete:tenant
users:reset_password:tenant
```

### 16.4 Testing Permissions

```python
# Test permission checking
def test_dashboard_create_permission():
    # User without permission
    response = client.post("/dashboards", headers=user_headers)
    assert response.status_code == 403

    # User with permission
    response = client.post("/dashboards", headers=admin_headers)
    assert response.status_code == 200
```

---

## 17. Appendix

### A. Current Permission Usage

**Files with Permission Checks:**
- `backend/app/routers/menu.py` - 5 permissions
- `backend/app/routers/admin/security.py` - 12 permissions
- `backend/app/routers/rbac.py` - Basic auth only (needs update)
- `backend/app/routers/org.py` - Role checks only (needs update)
- `backend/app/routers/metadata.py` - Role checks only (needs update)

**Total Currently Used:** ~20 unique permissions

### B. Endpoints Needing Permission Updates

**High Priority (Public-facing):**
1. Organization endpoints (`/org/*`)
2. RBAC endpoints (`/rbac/*`)
3. Dashboard endpoints (`/dashboards/*`)
4. Report endpoints (`/reports/*`)

**Medium Priority:**
5. Scheduler endpoints (`/scheduler/*`)
6. Audit endpoints (`/audit/*`)
7. Settings endpoints (`/settings/*`)

**Low Priority:**
8. Metadata endpoints (`/metadata/*`)
9. Data endpoints (`/data/*`)

### C. Permission Seed Script Template

```python
"""
Create [MODULE] permissions and roles
"""
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.rbac_junctions import RolePermission

def seed_[module]_permissions():
    db = SessionLocal()

    try:
        # Define permissions
        permissions = [
            {
                "code": "resource:action:scope",
                "name": "Permission Name",
                "description": "Description",
                "resource": "resource",
                "action": "action",
                "scope": "scope",
                "category": "category"
            },
            # ... more permissions
        ]

        # Create permissions
        created = []
        for perm_data in permissions:
            perm = db.query(Permission).filter(
                Permission.code == perm_data["code"]
            ).first()

            if not perm:
                perm = Permission(**perm_data, is_active=True)
                db.add(perm)
                db.flush()
                print(f"✓ Created: {perm_data['code']}")
                created.append(perm)
            else:
                print(f"• Exists: {perm_data['code']}")
                created.append(perm)

        db.commit()
        print(f"\n✓ Created {len(created)} permissions")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_[module]_permissions()
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-27
**Status:** ✅ Complete

**Next Steps:**
1. Review and approve permission list
2. Create permission seed scripts
3. Update endpoints to use granular permissions
4. Build permission assignment UI
5. Create comprehensive test suite

---
