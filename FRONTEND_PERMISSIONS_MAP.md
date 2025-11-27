# Frontend Screens and Permission Requirements

## Complete Mapping of All Frontend Screens, Functions, and Required Permissions

**Generated Date:** 2025-11-27
**Application:** App-Buildify NoCode Platform

---

## 📋 Table of Contents

1. [Dashboard](#1-dashboard)
2. [System Management](#2-system-management)
   - [Administration](#administration)
   - [System Settings](#system-settings)
   - [Module Management](#module-management)
   - [Monitoring & Audit](#monitoring--audit)
3. [User Profile](#3-user-profile)
4. [Help & Support](#4-help--support)
5. [Authentication](#5-authentication)
6. [Permission Summary](#6-permission-summary)

---

## 1. Dashboard

**Route:** `#dashboard`
**Template:** `/assets/templates/dashboard.html`

### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Dashboard | Load and display dashboard | `dashboard:view:tenant` | Default landing page |
| View Widgets | Display dashboard widgets | `dashboard:view:tenant` | Includes charts, metrics |
| Edit Dashboard | Customize dashboard layout | `dashboard:edit:tenant` | Drag-drop widgets |
| Create Custom Dashboard | Build new dashboards | `dashboard:create:tenant` | Dashboard designer |
| Delete Dashboard | Remove custom dashboards | `dashboard:delete:tenant` | |
| Share Dashboard | Share with other users | `dashboard:share:tenant` | |
| Export Dashboard | Export to PDF/image | `dashboard:export:tenant` | |

### Recommended Permissions
```
dashboard:view:tenant       - View dashboards (all users)
dashboard:edit:own         - Edit own dashboards
dashboard:edit:tenant      - Edit all dashboards (admin)
dashboard:create:tenant    - Create new dashboards
dashboard:delete:tenant    - Delete dashboards
dashboard:share:tenant     - Share dashboards
dashboard:export:tenant    - Export dashboards
```

---

## 2. System Management

### Administration

#### 2.1 Tenants & Organizations

**Route:** `#tenants`
**Template:** `/assets/templates/tenants.html`
**Script:** `/assets/js/tenants.js`
**Required Role:** `superuser`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Tenants List | Display all tenants | `tenants:read:all` | Superuser only |
| View Tenant Details | View specific tenant info | `tenants:read:all` | Includes companies, branches |
| Create Tenant | Add new tenant | `tenants:create:all` | Superuser only |
| Update Tenant | Modify tenant details | `tenants:update:all` | Name, settings, status |
| Delete Tenant | Remove tenant | `tenants:delete:all` | With confirmation |
| Activate/Deactivate Tenant | Change tenant status | `tenants:update:all` | |
| View Companies | List companies in tenant | `companies:read:tenant` | Organization hierarchy |
| Create Company | Add company to tenant | `companies:create:tenant` | |
| Update Company | Modify company details | `companies:update:tenant` | |
| Delete Company | Remove company | `companies:delete:tenant` | |
| View Branches | List branches | `branches:read:company` | |
| Create Branch | Add branch to company | `branches:create:company` | |
| Update Branch | Modify branch details | `branches:update:company` | |
| Delete Branch | Remove branch | `branches:delete:company` | |
| View Departments | List departments | `departments:read:branch` | |
| Create Department | Add department | `departments:create:branch` | |
| Update Department | Modify department | `departments:update:branch` | |
| Delete Department | Remove department | `departments:delete:branch` | |

##### Recommended Permissions
```
# Tenant Management (Superuser only)
tenants:read:all
tenants:create:all
tenants:update:all
tenants:delete:all

# Company Management (Tenant Admin)
companies:read:tenant
companies:create:tenant
companies:update:tenant
companies:delete:tenant

# Branch Management (Company Admin)
branches:read:company
branches:create:company
branches:update:company
branches:delete:company

# Department Management (Branch Manager)
departments:read:branch
departments:create:branch
departments:update:branch
departments:delete:branch
```

#### 2.2 Users & Access Control (RBAC)

**Route:** `#rbac`
**Template:** `/assets/templates/rbac.html`
**Script:** `/assets/js/rbac-manager.js`
**Required Role:** `admin`

##### Features & Functions

###### Dashboard Tab
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View RBAC Dashboard | Display statistics | `rbac:dashboard:view:tenant` | Overview of roles, users, permissions |
| View User Count | See total users | `users:read:tenant` | |
| View Role Count | See total roles | `roles:read:tenant` | |
| View Permission Count | See total permissions | `permissions:read:tenant` | |
| View Group Count | See total groups | `groups:read:tenant` | |

###### Roles Tab
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Roles List | Display all roles | `roles:read:tenant` | Paginated table |
| Search Roles | Filter roles | `roles:read:tenant` | By name, code |
| View Role Details | See role info | `roles:read:tenant` | With assigned permissions |
| Create Role | Add new role | `roles:create:tenant` | Name, code, description |
| Update Role | Modify role | `roles:update:tenant` | Change name, status |
| Delete Role | Remove role | `roles:delete:tenant` | With validation |
| View Role Permissions | List permissions for role | `permissions:read:tenant` | |
| Assign Permissions to Role | Grant permissions | `roles:assign_permissions:tenant` | Bulk operation |
| Remove Permission from Role | Revoke permission | `roles:revoke_permissions:tenant` | |
| Bulk Update Permissions | Grant/revoke multiple | `roles:assign_permissions:tenant` | Efficient bulk API |
| View Role Users | List users with role | `users:read:tenant` | Direct assignments |
| View Role Groups | List groups with role | `groups:read:tenant` | |

###### Permissions Tab
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Permissions List | Display all permissions | `permissions:read:tenant` | All system permissions |
| View Grouped Permissions | By resource/category | `permissions:read:tenant` | Organized view |
| Search Permissions | Filter permissions | `permissions:read:tenant` | By code, name, category |
| Filter by Category | Show specific category | `permissions:read:tenant` | financial, security, etc |
| Filter by Scope | Show by scope | `permissions:read:tenant` | all, tenant, company |
| Create Permission | Add new permission | `permissions:create:all` | Superuser only |
| Update Permission | Modify permission | `permissions:update:all` | Superuser only |
| Delete Permission | Remove permission | `permissions:delete:all` | Superuser only |
| View Permission Details | See full info | `permissions:read:tenant` | |

###### Users Tab
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Users List | Display all users | `users:read:tenant` | Paginated table |
| Search Users | Filter users | `users:read:tenant` | By name, email |
| View User Details | See user info | `users:read:tenant` | Profile, roles, permissions |
| View User Roles | List assigned roles | `users:read:tenant` | Direct + group roles |
| View User Permissions | Effective permissions | `permissions:read:tenant` | Calculated from roles |
| Assign Roles to User | Grant roles | `users:assign_roles:tenant` | Multiple roles |
| Remove Role from User | Revoke role | `users:revoke_roles:tenant` | |
| View User Groups | List user's groups | `groups:read:tenant` | |

###### Groups Tab
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Groups List | Display all groups | `groups:read:tenant` | Department, team, project |
| Search Groups | Filter groups | `groups:read:tenant` | By name, type |
| View Group Details | See group info | `groups:read:tenant` | With members and roles |
| Create Group | Add new group | `groups:create:tenant` | Name, type, scope |
| Update Group | Modify group | `groups:update:tenant` | Change name, status |
| Delete Group | Remove group | `groups:delete:tenant` | With validation |
| View Group Members | List users in group | `users:read:tenant` | |
| Add Members to Group | Assign users | `groups:add_members:tenant` | Bulk operation |
| Remove Member from Group | Remove user | `groups:remove_members:tenant` | |
| View Group Roles | List assigned roles | `roles:read:tenant` | |
| Assign Roles to Group | Grant roles | `groups:assign_roles:tenant` | Multiple roles |
| Remove Role from Group | Revoke role | `groups:revoke_roles:tenant` | |
| View Group Permissions | Effective permissions | `permissions:read:tenant` | From assigned roles |

###### Organization Tab
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Organization Structure | Display hierarchy | `organization:view:tenant` | Tree view |
| View Tenant Details | See tenant info | `tenants:read:own` | Current tenant |
| View All Companies | List companies | `companies:read:tenant` | |
| View All Branches | List branches | `branches:read:tenant` | |
| View All Departments | List departments | `departments:read:tenant` | |
| View All Groups | List groups | `groups:read:tenant` | By org level |

##### Recommended Permissions
```
# RBAC Dashboard
rbac:dashboard:view:tenant

# Role Management
roles:read:tenant
roles:create:tenant
roles:update:tenant
roles:delete:tenant
roles:assign_permissions:tenant
roles:revoke_permissions:tenant

# Permission Management (Superuser only)
permissions:read:tenant
permissions:create:all
permissions:update:all
permissions:delete:all

# User Role Management
users:read:tenant
users:assign_roles:tenant
users:revoke_roles:tenant

# Group Management
groups:read:tenant
groups:create:tenant
groups:update:tenant
groups:delete:tenant
groups:add_members:tenant
groups:remove_members:tenant
groups:assign_roles:tenant
groups:revoke_roles:tenant

# Organization View
organization:view:tenant
```

#### 2.3 User Management (Legacy)

**Route:** `#users`
**Template:** `/assets/templates/users.html`
**Script:** `/assets/js/users.js`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Users List | Display all users | `users:read:tenant` | |
| Search Users | Filter by name/email | `users:read:tenant` | |
| Filter by Role | Show specific role | `users:read:tenant` | |
| Filter by Status | Active/inactive | `users:read:tenant` | |
| View User Details | See full profile | `users:read:tenant` | |
| Create User | Add new user | `users:create:tenant` | Admin role required |
| Update User | Modify user details | `users:update:tenant` | Own or admin |
| Delete User | Remove user | `users:delete:tenant` | Admin only |
| Activate/Deactivate User | Change status | `users:update:tenant` | |
| Reset Password | Force password reset | `users:reset_password:tenant` | |
| View User Activity | See audit logs | `audit:read:tenant` | |

##### Recommended Permissions
```
users:read:tenant          - View users list
users:read:own            - View own profile
users:create:tenant       - Create new users (admin)
users:update:tenant       - Update any user (admin)
users:update:own          - Update own profile
users:delete:tenant       - Delete users (admin)
users:reset_password:tenant - Reset user passwords
```

### System Settings

#### 2.4 General Settings

**Route:** `#settings`
**Template:** `/assets/templates/settings.html`
**Script:** `/assets/js/settings.js`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Settings | Display current settings | `settings:read:tenant` | |
| Update Company Info | Modify company details | `settings:update:tenant` | Admin only |
| Update System Config | Change system settings | `settings:update:all` | Superuser only |
| Update Branding | Change logo, colors | `settings:branding:tenant` | |
| Update Theme | Change UI theme | `settings:theme:own` | User preference |
| Update Language | Change locale | `settings:language:own` | User preference |
| View API Keys | Display API credentials | `settings:api_keys:read:tenant` | |
| Generate API Key | Create new key | `settings:api_keys:create:tenant` | Admin only |
| Revoke API Key | Disable key | `settings:api_keys:revoke:tenant` | |

##### Recommended Permissions
```
settings:read:tenant
settings:update:tenant
settings:branding:tenant
settings:theme:own
settings:language:own
settings:api_keys:read:tenant
settings:api_keys:create:tenant
settings:api_keys:revoke:tenant
```

#### 2.5 Integration Settings

**Route:** `#settings-integration`
**Template:** `/assets/templates/settings-integration.html`
**Script:** `/assets/js/settings-integration.js`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Integrations | Display available integrations | `integrations:read:tenant` | |
| Configure Integration | Set up integration | `integrations:configure:tenant` | API keys, webhooks |
| Enable Integration | Activate integration | `integrations:enable:tenant` | |
| Disable Integration | Deactivate integration | `integrations:disable:tenant` | |
| Test Integration | Verify connection | `integrations:test:tenant` | |
| View Integration Logs | See activity logs | `integrations:logs:read:tenant` | |

##### Recommended Permissions
```
integrations:read:tenant
integrations:configure:tenant
integrations:enable:tenant
integrations:disable:tenant
integrations:test:tenant
integrations:logs:read:tenant
```

#### 2.6 Security Settings

**Route:** `#settings-security`
**Template:** `/assets/templates/settings-security.html`
**Script:** `/assets/js/settings-security.js`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Security Policy | Display current policy | `security_policy:read:all` | |
| Update Security Policy | Modify policy | `security_policy:write:all` | Password rules, session timeout |
| View Locked Accounts | List locked users | `security:view_locked_accounts:all` | |
| Unlock Account | Manually unlock user | `security:unlock_account:all` | |
| View Active Sessions | Display user sessions | `security:view_sessions:all` | |
| Revoke Session | Force logout | `security:revoke_session:all` | |
| Revoke All User Sessions | Logout all sessions | `security:revoke_session:all` | |
| View Login Attempts | See audit trail | `security:view_login_attempts:all` | |
| Configure MFA | Set up 2FA | `security:mfa:configure:tenant` | |

##### Recommended Permissions
```
# Security Policy Management
security_policy:read:all
security_policy:write:all
security_policy:delete:all

# Account Lockout Management
security:view_locked_accounts:all
security:unlock_account:all

# Session Management
security:view_sessions:all
security:revoke_session:all

# Login Audit
security:view_login_attempts:all

# MFA Configuration
security:mfa:configure:tenant
```

#### 2.7 Notification Settings

**Route:** `#settings-notifications`
**Template:** `/assets/templates/settings-notifications.html`
**Script:** `/assets/js/settings-notifications.js`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Notification Config | Display settings | `notification_config:read:all` | |
| Update Notification Config | Modify settings | `notification_config:write:all` | Email, SMS, in-app |
| View Notification Queue | See pending notifications | `notification_queue:read:all` | |
| Test Email Notification | Send test email | `notification_config:write:all` | |
| View User Preferences | Personal notification settings | `notifications:preferences:read:own` | |
| Update User Preferences | Change preferences | `notifications:preferences:write:own` | |

##### Recommended Permissions
```
notification_config:read:all
notification_config:write:all
notification_queue:read:all
notifications:preferences:read:own
notifications:preferences:write:own
```

#### 2.8 Menu Management

**Route:** `#menu-management`
**Template:** `/assets/templates/menu-management.html`
**Script:** `/assets/js/menu-management.js`
**Required Permission:** `menu:manage:tenant`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Menu Items | Display menu tree | `menu:read:tenant` | Hierarchical view |
| Search Menu Items | Filter menu items | `menu:read:tenant` | |
| Expand/Collapse All | Toggle tree view | `menu:read:tenant` | |
| View Menu Details | See item details | `menu:read:tenant` | Route, icon, permissions |
| Create Menu Item | Add new item | `menu:create:tenant` | Parent/child support |
| Update Menu Item | Modify item | `menu:update:tenant` | Change route, icon, order |
| Delete Menu Item | Remove item | `menu:delete:tenant` | With validation |
| Reorder Menu Items | Change order | `menu:update:tenant` | Drag-drop or manual |
| Assign Permission to Menu | Set required permission | `menu:update:tenant` | RBAC integration |
| Set Required Roles | Define role requirements | `menu:update:tenant` | |

##### Recommended Permissions
```
menu:read:tenant
menu:create:tenant
menu:update:tenant
menu:delete:tenant
menu:manage:tenant      - Full menu management access
```

### Module Management

#### 2.9 Installed Modules

**Route:** `#modules`
**Template:** `/assets/templates/modules.html`
**Required Permission:** `modules:manage:tenant`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Modules List | Display installed modules | `modules:list:tenant` | |
| Search Modules | Filter modules | `modules:list:tenant` | |
| View Module Details | See module info | `modules:view:tenant` | Version, dependencies |
| Enable Module | Activate for tenant | `modules:enable:tenant` | Tenant admin |
| Disable Module | Deactivate for tenant | `modules:disable:tenant` | Tenant admin |
| Configure Module | Update settings | `modules:configure:tenant` | Module-specific config |
| Install Module | Platform-wide install | `modules:install:all` | Superuser only |
| Uninstall Module | Platform-wide removal | `modules:uninstall:all` | Superuser only |
| Sync Modules | Refresh from filesystem | `modules:sync:all` | Superuser only |
| View Module Permissions | See module permissions | `permissions:read:tenant` | |

##### Recommended Permissions
```
# Viewing (all users)
modules:list:tenant
modules:view:tenant

# Tenant Management (tenant admin)
modules:enable:tenant
modules:disable:tenant
modules:configure:tenant
modules:manage:tenant

# Platform Management (superuser)
modules:install:all
modules:uninstall:all
modules:sync:all
```

#### 2.10 Module Marketplace

**Route:** `#modules-marketplace`
**Template:** TBD

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Marketplace | Browse available modules | `marketplace:browse:tenant` | |
| Search Modules | Find modules | `marketplace:browse:tenant` | |
| View Module Details | See info & reviews | `marketplace:browse:tenant` | |
| Install from Marketplace | Download & install | `modules:install:all` | Superuser only |
| Purchase Module | Buy premium module | `marketplace:purchase:tenant` | Payment required |

##### Recommended Permissions
```
marketplace:browse:tenant
marketplace:purchase:tenant
```

#### 2.11 Module Updates

**Route:** `#modules-updates`
**Template:** TBD

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Available Updates | List updates | `modules:updates:view:all` | |
| Update Module | Apply update | `modules:update:all` | Superuser only |
| Auto-Update Settings | Configure auto-update | `modules:auto_update:all` | |

##### Recommended Permissions
```
modules:updates:view:all
modules:update:all
modules:auto_update:all
```

#### 2.12 Module Builder

**Route:** `#modules-builder`
**Template:** TBD

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| Create New Module | Build custom module | `modules:build:tenant` | |
| Edit Module Code | Modify source | `modules:build:tenant` | Code editor |
| Test Module | Run tests | `modules:test:tenant` | |
| Package Module | Create distributable | `modules:package:tenant` | |
| Publish Module | Share to marketplace | `marketplace:publish:tenant` | |

##### Recommended Permissions
```
modules:build:tenant
modules:test:tenant
modules:package:tenant
marketplace:publish:tenant
```

### Monitoring & Audit

#### 2.13 Audit Trail

**Route:** `#audit`
**Template:** `/assets/templates/audit.html`
**Script:** `/assets/js/audit-page.js`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Audit Logs | Display all logs | `audit:read:tenant` | |
| Search Audit Logs | Filter logs | `audit:read:tenant` | By user, action, entity |
| Filter by User | Show specific user | `audit:read:tenant` | |
| Filter by Action | Show specific action | `audit:read:tenant` | CREATE, UPDATE, DELETE |
| Filter by Entity | Show entity type | `audit:read:tenant` | users, roles, etc |
| Filter by Date Range | Time period | `audit:read:tenant` | |
| View Audit Details | See full log entry | `audit:read:tenant` | Before/after values |
| Export Audit Logs | Download logs | `audit:export:tenant` | CSV, JSON |
| View IP Address | See request origin | `audit:read:tenant` | Security tracking |
| View User Agent | See client info | `audit:read:tenant` | |

##### Recommended Permissions
```
audit:read:tenant
audit:read:own           - View own audit trail
audit:export:tenant
audit:export:all         - Export all logs (admin)
```

#### 2.14 System Logs

**Route:** `#system-logs`
**Template:** TBD

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View System Logs | Display error logs | `logs:read:all` | Superuser only |
| Search Logs | Filter logs | `logs:read:all` | By level, message |
| Filter by Level | ERROR, WARN, INFO | `logs:read:all` | |
| View Log Details | See stack trace | `logs:read:all` | |
| Download Logs | Export log files | `logs:download:all` | |

##### Recommended Permissions
```
logs:read:all
logs:download:all
```

#### 2.15 API Activity

**Route:** `#api-activity`
**Template:** TBD

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View API Calls | Display API activity | `api_activity:read:tenant` | |
| Search API Calls | Filter calls | `api_activity:read:tenant` | By endpoint, user |
| View Request Details | See payload | `api_activity:read:tenant` | |
| View Response | See response data | `api_activity:read:tenant` | |
| View Performance Metrics | API statistics | `api_activity:metrics:tenant` | |

##### Recommended Permissions
```
api_activity:read:tenant
api_activity:metrics:tenant
```

#### 2.16 Usage Analytics

**Route:** `#usage-analytics`
**Template:** TBD

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Usage Reports | Display analytics | `analytics:read:tenant` | |
| View User Activity | User engagement | `analytics:read:tenant` | |
| View Feature Usage | Feature adoption | `analytics:read:tenant` | |
| Export Reports | Download analytics | `analytics:export:tenant` | |

##### Recommended Permissions
```
analytics:read:tenant
analytics:export:tenant
```

---

## 3. User Profile

**Route:** `#profile`
**Template:** `/assets/templates/profile.html`
**Script:** `/assets/js/profile-page.js`

### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Profile | Display user profile | `users:read:own` | Always allowed |
| Update Profile | Modify own details | `users:update:own` | Name, email, etc |
| Change Password | Update password | `users:change_password:own` | Always allowed |
| Update Avatar | Change profile picture | `users:update:own` | Image upload |
| View Permissions | See own permissions | `permissions:read:own` | |
| View Roles | See assigned roles | `roles:read:own` | |
| View Groups | See group membership | `groups:read:own` | |
| Update Preferences | Change settings | `settings:update:own` | Theme, language |
| View Activity Log | Personal audit trail | `audit:read:own` | |

### Recommended Permissions
```
users:read:own
users:update:own
users:change_password:own
permissions:read:own
roles:read:own
groups:read:own
settings:update:own
audit:read:own
```

---

## 4. Help & Support

### 4.1 Developer Tools

#### Sample Reports & Dashboards

**Route:** `#sample-reports-dashboards`
**Template:** `/assets/templates/sample-reports-dashboards.html`
**Script:** `/assets/js/sample-reports-dashboards-page.js`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Samples | Browse examples | Public | No permission required |
| Create Report | Build new report | `reports:create:tenant` | Report designer |
| Edit Report | Modify report | `reports:update:tenant` | |
| Delete Report | Remove report | `reports:delete:tenant` | |
| Run Report | Execute report | `reports:run:tenant` | |
| Export Report | Download results | `reports:export:tenant` | PDF, CSV, Excel |
| Schedule Report | Automate execution | `reports:schedule:tenant` | |
| Share Report | Share with users | `reports:share:tenant` | |

##### Recommended Permissions
```
reports:create:tenant
reports:update:tenant
reports:delete:tenant
reports:run:tenant
reports:export:tenant
reports:schedule:tenant
reports:share:tenant
```

#### Components Showcase

**Route:** `#components-showcase`
**Template:** `/assets/templates/components-showcase.html`
**Script:** `/assets/js/showcase.js`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Components | Browse UI components | Public | No permission required |

#### Scheduler

**Route:** `#scheduler`
**Template:** `/assets/templates/scheduler.html`
**Script:** `/assets/js/scheduler.js`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Scheduled Jobs | List all jobs | `scheduler:read:tenant` | |
| Create Job | Schedule new job | `scheduler:create:tenant` | |
| Update Job | Modify job | `scheduler:update:tenant` | |
| Delete Job | Remove job | `scheduler:delete:tenant` | |
| Run Job Manually | Execute now | `scheduler:execute:tenant` | |
| View Job History | See execution logs | `scheduler:history:read:tenant` | |
| Enable/Disable Job | Activate/deactivate | `scheduler:update:tenant` | |

##### Recommended Permissions
```
scheduler:read:tenant
scheduler:create:tenant
scheduler:update:tenant
scheduler:delete:tenant
scheduler:execute:tenant
scheduler:history:read:tenant
```

---

## 5. Authentication

### 5.1 Login

**Route:** `#login`
**Template:** `/assets/templates/login.html`
**Script:** `/assets/js/login-page.js`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| Login | Authenticate user | Public | No permission required |
| Forgot Password | Request password reset | Public | Email required |
| MFA Verification | Two-factor auth | Public | If enabled |

### 5.2 Auth Policies

**Route:** `#auth-policies`
**Template:** `/assets/templates/auth-policies.html`
**Script:** `/assets/js/auth-policies-page.js`

##### Features & Functions
| Feature | Action | Required Permission | Notes |
|---------|--------|---------------------|-------|
| View Auth Policies | Display policies | `auth_policies:read:tenant` | |
| Update Auth Policies | Modify policies | `auth_policies:update:tenant` | OAuth, SAML, LDAP |

##### Recommended Permissions
```
auth_policies:read:tenant
auth_policies:update:tenant
```

---

## 6. Permission Summary

### 6.1 Permission Format

All permissions follow the format: `resource:action:scope`

**Examples:**
- `users:create:tenant` - Create users within tenant
- `roles:update:tenant` - Update roles for tenant
- `audit:export:all` - Export all audit logs (superuser)
- `settings:update:own` - Update own settings

### 6.2 Scope Levels (Hierarchical)

1. **all** - System-wide (superuser only)
2. **tenant** - Entire tenant
3. **company** - Specific company within tenant
4. **branch** - Branch level
5. **department** - Department level
6. **own** - User's own records only

### 6.3 Complete Permission List by Category

#### User Management (25 permissions)
```
users:read:all
users:read:tenant
users:read:company
users:read:department
users:read:own
users:create:tenant
users:update:all
users:update:tenant
users:update:own
users:delete:all
users:delete:tenant
users:reset_password:all
users:reset_password:tenant
users:change_password:own
users:assign_roles:tenant
users:revoke_roles:tenant
users:impersonate:all         # Superuser feature
```

#### Role Management (8 permissions)
```
roles:read:all
roles:read:tenant
roles:read:own
roles:create:tenant
roles:update:tenant
roles:delete:tenant
roles:assign_permissions:tenant
roles:revoke_permissions:tenant
```

#### Permission Management (5 permissions - Superuser only)
```
permissions:read:all
permissions:read:tenant
permissions:read:own
permissions:create:all
permissions:update:all
permissions:delete:all
```

#### Group Management (12 permissions)
```
groups:read:all
groups:read:tenant
groups:read:company
groups:read:own
groups:create:tenant
groups:update:tenant
groups:delete:tenant
groups:add_members:tenant
groups:remove_members:tenant
groups:assign_roles:tenant
groups:revoke_roles:tenant
```

#### Tenant/Organization Management (16 permissions)
```
tenants:read:all
tenants:read:own
tenants:create:all
tenants:update:all
tenants:delete:all
companies:read:tenant
companies:create:tenant
companies:update:tenant
companies:delete:tenant
branches:read:company
branches:create:company
branches:update:company
branches:delete:company
departments:read:branch
departments:create:branch
departments:update:branch
departments:delete:branch
organization:view:tenant
```

#### Menu Management (5 permissions)
```
menu:read:tenant
menu:create:tenant
menu:update:tenant
menu:delete:tenant
menu:manage:tenant
```

#### Module Management (9 permissions)
```
modules:list:tenant
modules:view:tenant
modules:enable:tenant
modules:disable:tenant
modules:configure:tenant
modules:manage:tenant
modules:install:all
modules:uninstall:all
modules:sync:all
modules:update:all
modules:updates:view:all
modules:auto_update:all
modules:build:tenant
modules:test:tenant
modules:package:tenant
```

#### Security Management (12 permissions)
```
security_policy:read:all
security_policy:write:all
security_policy:delete:all
security:view_locked_accounts:all
security:unlock_account:all
security:view_sessions:all
security:revoke_session:all
security:view_login_attempts:all
security:mfa:configure:tenant
```

#### Notification Management (5 permissions)
```
notification_config:read:all
notification_config:write:all
notification_queue:read:all
notifications:preferences:read:own
notifications:preferences:write:own
```

#### Settings Management (10 permissions)
```
settings:read:all
settings:read:tenant
settings:update:all
settings:update:tenant
settings:branding:tenant
settings:theme:own
settings:language:own
settings:api_keys:read:tenant
settings:api_keys:create:tenant
settings:api_keys:revoke:tenant
```

#### Integration Management (6 permissions)
```
integrations:read:tenant
integrations:configure:tenant
integrations:enable:tenant
integrations:disable:tenant
integrations:test:tenant
integrations:logs:read:tenant
```

#### Audit & Monitoring (12 permissions)
```
audit:read:all
audit:read:tenant
audit:read:own
audit:export:all
audit:export:tenant
logs:read:all
logs:download:all
api_activity:read:tenant
api_activity:metrics:tenant
analytics:read:tenant
analytics:export:tenant
```

#### Dashboard & Reports (13 permissions)
```
dashboard:view:tenant
dashboard:edit:own
dashboard:edit:tenant
dashboard:create:tenant
dashboard:delete:tenant
dashboard:share:tenant
dashboard:export:tenant
reports:create:tenant
reports:update:tenant
reports:delete:tenant
reports:run:tenant
reports:export:tenant
reports:schedule:tenant
reports:share:tenant
```

#### Scheduler (6 permissions)
```
scheduler:read:tenant
scheduler:create:tenant
scheduler:update:tenant
scheduler:delete:tenant
scheduler:execute:tenant
scheduler:history:read:tenant
```

#### Marketplace (3 permissions)
```
marketplace:browse:tenant
marketplace:purchase:tenant
marketplace:publish:tenant
```

#### Auth Policies (2 permissions)
```
auth_policies:read:tenant
auth_policies:update:tenant
```

#### RBAC Dashboard (1 permission)
```
rbac:dashboard:view:tenant
```

### 6.4 Total Permission Count

**Total:** 180+ permissions

**Breakdown by Access Level:**
- **Superuser only:** ~30 permissions (all, install, uninstall, etc.)
- **Tenant Admin:** ~80 permissions (tenant-level management)
- **Department/Company Manager:** ~40 permissions (scoped management)
- **Regular Users:** ~30 permissions (own, read-only)

---

## 7. Recommended Role Templates

### Superuser (Platform Administrator)
Full access to all features including platform-wide operations.
- All permissions with scope `all`
- Tenant/module/permission management
- System configuration
- **Total Permissions:** ~180

### Tenant Administrator
Full management within a single tenant.
```
# User & Access Management
users:*:tenant
roles:*:tenant
groups:*:tenant

# Organization Management
companies:*:tenant
branches:*:tenant
departments:*:tenant

# Configuration
settings:*:tenant
menu:*:tenant
modules:enable:tenant
modules:disable:tenant
modules:configure:tenant

# Security & Audit
security_policy:*:all
audit:*:tenant

# Dashboard & Reports
dashboard:*:tenant
reports:*:tenant
```
**Total Permissions:** ~80

### Department Manager
Manage specific department or company.
```
# User Management (scoped)
users:read:department
users:update:department
groups:*:department

# View Access
dashboard:view:tenant
reports:run:tenant

# Own Settings
settings:*:own
audit:read:own
```
**Total Permissions:** ~30

### Regular User (Employee)
Basic access for end users.
```
# Own Profile
users:read:own
users:update:own
users:change_password:own

# View Permissions
dashboard:view:tenant
reports:run:tenant

# Own Settings
settings:*:own
permissions:read:own
roles:read:own
audit:read:own
```
**Total Permissions:** ~15

### Security Administrator
Manage security policies and user access.
```
# Security Management
security_policy:*:all
security:*:all

# User Management
users:read:tenant
users:reset_password:tenant
users:assign_roles:tenant

# Audit & Monitoring
audit:*:tenant
logs:read:all
api_activity:*:tenant
```
**Total Permissions:** ~25

### Module Administrator
Manage modules and integrations.
```
# Module Management
modules:*:tenant
modules:install:all (if superuser)
modules:uninstall:all (if superuser)

# Integration Management
integrations:*:tenant

# View Access
dashboard:view:tenant
audit:read:tenant
```
**Total Permissions:** ~15

### Report Developer
Create and manage reports/dashboards.
```
# Report & Dashboard Management
reports:*:tenant
dashboard:*:tenant
scheduler:*:tenant

# View Access
audit:read:tenant
analytics:read:tenant
```
**Total Permissions:** ~15

### Security Viewer
Read-only security monitoring.
```
# View Security
security_policy:read:all
security:view_*:all

# View Audit
audit:read:tenant
logs:read:all
api_activity:read:tenant
```
**Total Permissions:** ~10

---

## 8. Implementation Notes

### 8.1 Permission Checking in Frontend

**Programmatic Check:**
```javascript
import { can, hasRole, hasPermission } from './rbac.js';

// Check single permission
if (can('users:create:tenant')) {
  // Show create user button
}

// Check role
if (hasRole('admin')) {
  // Show admin features
}

// Check multiple permissions (OR logic)
if (hasAnyPermission(['users:update:tenant', 'users:update:own'])) {
  // Allow edit
}
```

**Declarative Check (HTML):**
```html
<!-- Show only if user has admin role -->
<button data-rbac-role="admin">Admin Panel</button>

<!-- Show only if user has permission -->
<button data-rbac-permission="users:create:tenant">Add User</button>
```

### 8.2 Permission Checking in Backend

**Route Protection:**
```python
from app.core.dependencies import has_permission, has_role, require_superuser

@router.get("/users")
async def list_users(
    current_user: User = Depends(has_permission("users:read:tenant"))
):
    # Handler code
    pass

# Multiple permission check (OR logic)
@router.get("/data")
async def get_data(
    current_user: User = Depends(has_any_permission([
        "data:read:tenant",
        "data:read:company"
    ]))
):
    pass

# Role-based check
@router.get("/admin")
async def admin_panel(
    current_user: User = Depends(has_role("admin"))
):
    pass

# Superuser only
@router.post("/modules/install")
async def install_module(
    current_user: User = Depends(require_superuser)
):
    pass
```

### 8.3 Menu-Based RBAC

Menu items in the database have:
- `permission` field (e.g., "menu:manage:tenant")
- `required_roles` field (JSON array of role codes)

The backend automatically filters menu items based on:
1. User's effective permissions (from roles + groups)
2. User's roles

Frontend receives only accessible menu items.

### 8.4 Field-Level RBAC

Dynamic forms support field-level permissions:
```javascript
import { canViewField, canEditField } from './rbac.js';

// Check if user can view field
if (canViewField(fieldMetadata)) {
  // Show field
}

// Check if user can edit field
if (canEditField(fieldMetadata)) {
  // Make field editable
} else {
  // Show as read-only with lock icon
}
```

---

## 9. Migration & Seeding

### Creating Permissions

Run seed scripts to create permissions:

```bash
# Security permissions
python -m backend.app.scripts.seed_security_permissions

# Menu management permissions
python -m backend.app.seeds.seed_menu_management_rbac TENANT_CODE

# Module management permissions
python -m backend.app.seeds.seed_module_management_rbac TENANT_CODE

# Financial module permissions (example)
python -m backend.app.seeds.seed_financial_rbac
```

### Custom Permission Creation

```python
from app.models.permission import Permission

permission = Permission(
    code="reports:export:tenant",
    name="Export Reports",
    description="Export reports to PDF/Excel",
    resource="reports",
    action="export",
    scope="tenant",
    category="reports",
    is_active=True
)
db.add(permission)
db.commit()
```

---

## 10. Best Practices

### 10.1 Permission Naming

- Use lowercase
- Format: `resource:action:scope`
- Be specific and descriptive
- Group related permissions by resource

✅ **Good:**
- `users:create:tenant`
- `financial:invoices:approve:company`
- `reports:export:department`

❌ **Bad:**
- `CreateUser` (not following format)
- `user_create` (wrong separator)
- `manage_everything` (too broad)

### 10.2 Scope Granularity

Use appropriate scope for each permission:
- **all**: Superuser/platform operations
- **tenant**: Tenant-wide management
- **company/branch/department**: Organizational units
- **own**: User's own records

### 10.3 Role Design

- Create roles based on job functions
- Avoid creating too many roles (combine related permissions)
- Use groups to assign roles to multiple users
- Review and audit role assignments regularly

### 10.4 Testing Permissions

- Test with non-admin users
- Verify both frontend and backend enforcement
- Check edge cases (no permissions, multiple roles)
- Test permission inheritance through groups

---

## 11. Appendix

### A. Existing Backend Permissions

Currently implemented in seed scripts:

**Security (12 permissions)**
- security_policy:read:all
- security_policy:write:all
- security_policy:delete:all
- security:view_locked_accounts:all
- security:unlock_account:all
- security:view_sessions:all
- security:revoke_session:all
- security:view_login_attempts:all
- notification_config:read:all
- notification_config:write:all
- notification_queue:read:all

**Menu Management (5 permissions)**
- menu:read:tenant
- menu:create:tenant
- menu:update:tenant
- menu:delete:tenant
- menu:manage:tenant

**Module Management (8 permissions)**
- modules:list:tenant
- modules:view:tenant
- modules:enable:tenant
- modules:disable:tenant
- modules:configure:tenant
- modules:manage:tenant
- modules:install:all
- modules:uninstall:all
- modules:sync:all

**Financial (20 permissions)**
- financial:accounts:read:company
- financial:accounts:create:company
- financial:accounts:update:company
- financial:accounts:delete:company
- financial:transactions:read:company
- financial:transactions:create:company
- financial:transactions:update:company
- financial:transactions:delete:company
- financial:transactions:post:company
- financial:invoices:read:company
- financial:invoices:create:company
- financial:invoices:update:company
- financial:invoices:delete:company
- financial:invoices:send:company
- financial:payments:read:company
- financial:payments:create:company
- financial:payments:update:company
- financial:payments:delete:company
- financial:reports:read:company
- financial:reports:export:company

### B. Frontend Routes Reference

| Route | Template | Script | Required Permission |
|-------|----------|--------|---------------------|
| #dashboard | dashboard.html | N/A | dashboard:view:tenant |
| #tenants | tenants.html | tenants.js | tenants:read:all (superuser) |
| #rbac | rbac.html | rbac-manager.js | rbac:dashboard:view:tenant |
| #users | users.html | users.js | users:read:tenant |
| #settings | settings.html | settings.js | settings:read:tenant |
| #settings-integration | settings-integration.html | settings-integration.js | integrations:read:tenant |
| #settings-security | settings-security.html | settings-security.js | security_policy:read:all |
| #settings-notifications | settings-notifications.html | settings-notifications.js | notification_config:read:all |
| #menu-management | menu-management.html | menu-management.js | menu:manage:tenant |
| #modules | modules.html | N/A | modules:manage:tenant |
| #audit | audit.html | audit-page.js | audit:read:tenant |
| #profile | profile.html | profile-page.js | users:read:own |
| #sample-reports-dashboards | sample-reports-dashboards.html | sample-reports-dashboards-page.js | Public |
| #components-showcase | components-showcase.html | showcase.js | Public |
| #scheduler | scheduler.html | scheduler.js | scheduler:read:tenant |
| #auth-policies | auth-policies.html | auth-policies-page.js | auth_policies:read:tenant |

---

**Document Version:** 1.0
**Last Updated:** 2025-11-27
**Status:** ✅ Complete

---
