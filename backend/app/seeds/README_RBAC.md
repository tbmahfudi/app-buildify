# RBAC Group-Based Access Control Setup

## Overview

This application uses a **consistent RBAC model** where all users must be assigned to groups, and groups are assigned roles. Direct user-to-role assignments are **deprecated**.

```
User → Group → Role → Permission
```

## Quick Start

### 1. Seed Organization Data (if not done already)

```bash
cd backend
python -m app.seeds.seed_complete_org
```

This creates:
- Tenants
- Companies
- Branches
- Departments
- Users

### 2. Seed RBAC with Groups

```bash
python -m app.seeds.seed_rbac_with_groups
```

This creates:
- Default roles (tenant_admin, manager, employee, etc.)
- Default groups (Administrators, Managers, Employees, etc.)
- Assigns roles to groups
- Assigns existing users to groups based on email patterns

## RBAC Model

### Hierarchy

```
┌──────────┐
│   User   │ (John Doe)
└────┬─────┘
     │ member of
     ▼
┌──────────┐
│  Group   │ (Administrators)
└────┬─────┘
     │ has role
     ▼
┌──────────┐
│   Role   │ (tenant_admin)
└────┬─────┘
     │ contains
     ▼
┌──────────┐
│Permission│ (users:create:tenant)
└──────────┘
```

### Why This Model?

1. **Scalability**: Manage hundreds of users by managing groups
2. **Consistency**: One clear path for permissions
3. **Maintainability**: Change group roles without touching individual users
4. **Auditability**: Clear permission inheritance chain

## Default Groups

The seed creates these groups automatically:

| Group Code | Name | Type | Default Roles | Purpose |
|------------|------|------|---------------|---------|
| `administrators` | Administrators | team | tenant_admin | Full system access |
| `managers` | Managers | team | manager | Supervisory access |
| `employees` | Employees | team | employee | Standard operational access |
| `viewers` | Viewers | team | viewer | Read-only access |
| `finance_team` | Finance Team | department | accountant | Financial operations |
| `hr_team` | HR Team | department | hr_manager | HR operations |
| `it_support` | IT Support | team | it_admin | Technical support |
| `engineering` | Engineering Team | department | developer | Software development |
| `sales_team` | Sales Team | department | sales_rep | Sales operations |
| `marketing_team` | Marketing Team | department | marketer | Marketing operations |

## Default Roles

| Role Code | Name | Type | Key Permissions |
|-----------|------|------|-----------------|
| `tenant_admin` | Tenant Administrator | default | Full tenant access |
| `manager` | Manager | default | Read access to users, groups, roles |
| `employee` | Employee | default | View own profile and permissions |
| `viewer` | Viewer | default | Read-only access |
| `hr_manager` | HR Manager | default | Manage users and groups |
| `it_admin` | IT Administrator | default | Technical system access |
| `accountant` | Accountant | default | Financial access |
| `developer` | Developer | default | Development access |
| `sales_rep` | Sales Representative | default | Sales access |
| `marketer` | Marketing Specialist | default | Marketing access |

## Managing Access

### Add User to Group

```python
from app.models.rbac_junctions import UserGroup

# Via API
POST /rbac/groups/{group_id}/members
{
  "user_ids": ["user-uuid-1", "user-uuid-2"]
}

# Via code
user_group = UserGroup(
    user_id=user_id,
    group_id=group_id
)
db.add(user_group)
db.commit()
```

### Assign Role to Group

```python
from app.models.rbac_junctions import GroupRole

# Via API
POST /rbac/groups/{group_id}/roles
{
  "role_ids": ["role-uuid-1", "role-uuid-2"]
}

# Via code
group_role = GroupRole(
    group_id=group_id,
    role_id=role_id
)
db.add(group_role)
db.commit()
```

### Remove User from Group

```python
# Via API
DELETE /rbac/groups/{group_id}/members/{user_id}

# Via code
user_group = db.query(UserGroup).filter(
    UserGroup.group_id == group_id,
    UserGroup.user_id == user_id
).first()
db.delete(user_group)
db.commit()
```

## Deprecated: Direct Role Assignment

These endpoints are **deprecated** and will return 400 errors:

```
POST /rbac/users/{user_id}/roles          ❌ DEPRECATED
DELETE /rbac/users/{user_id}/roles/{role_id}  ❌ DEPRECATED
```

**Instead**, use group-based assignment:

```
POST /rbac/groups/{group_id}/members      ✅ USE THIS
DELETE /rbac/groups/{group_id}/members/{user_id}  ✅ USE THIS
```

## Creating Custom Groups

### For Specific Projects

```python
# Create project group
project_group = Group(
    tenant_id=tenant_id,
    company_id=company_id,
    code="project_alpha",
    name="Project Alpha Team",
    description="Team working on Project Alpha",
    group_type="project",
    is_active=True
)
db.add(project_group)

# Assign roles
group_role = GroupRole(
    group_id=project_group.id,
    role_id=developer_role_id
)
db.add(group_role)

# Add team members
for user_id in team_member_ids:
    user_group = UserGroup(
        user_id=user_id,
        group_id=project_group.id
    )
    db.add(user_group)

db.commit()
```

### For Departments

```python
# Create department group
dept_group = Group(
    tenant_id=tenant_id,
    company_id=company_id,
    code="customer_success",
    name="Customer Success Team",
    description="Customer support and success operations",
    group_type="department",
    is_active=True
)
db.add(dept_group)

# Assign multiple roles
for role_code in ["support_agent", "customer_manager"]:
    role = db.query(Role).filter(Role.code == role_code).first()
    if role:
        group_role = GroupRole(
            group_id=dept_group.id,
            role_id=role.id
        )
        db.add(group_role)

db.commit()
```

## User Smart Assignment

The seed script automatically assigns users to groups based on email patterns:

```python
EMAIL PATTERN → GROUP
-----------------------------------------
admin, ceo, cto, cfo → administrators
manager, director, lead → managers
hr, people → hr_team
finance, accounting → finance_team
it, tech, support → it_support
dev, engineer, eng → engineering
sales → sales_team
marketing → marketing_team
(default) → employees
```

## Checking User Permissions

### In Python

```python
# Get all user permissions (through groups)
permissions = user.get_permissions()
# Returns: {'users:read:own', 'roles:read:own', ...}

# Get all user roles (through groups)
roles = user.get_roles()
# Returns: {'tenant_admin', 'manager', ...}
```

### In API

```bash
# Get user roles (via groups)
GET /rbac/users/{user_id}/roles

# Response:
{
  "roles": [
    {
      "role_id": "...",
      "role_code": "tenant_admin",
      "role_name": "Tenant Administrator",
      "group_id": "...",
      "group_name": "Administrators",
      "is_active": true
    }
  ]
}

# Get user permissions
GET /rbac/users/{user_id}/permissions

# Response:
{
  "permissions": [
    {
      "id": "...",
      "code": "users:create:tenant",
      "name": "Create Users",
      "category": "rbac"
    },
    ...
  ]
}
```

## Migration from Direct Roles

If you have existing `user_roles` records, they are **ignored** but not deleted. To migrate:

1. Run the RBAC seed: `python -m app.seeds.seed_rbac_with_groups`
2. Users are automatically assigned to groups based on email patterns
3. Verify assignments: `GET /rbac/users/{user_id}/roles`
4. Manually adjust group membership as needed
5. Old `user_roles` records can be cleaned up later (optional)

## Best Practices

### ✅ Do

- Create groups for organizational units (departments, teams, projects)
- Assign roles to groups, not individual users
- Add users to groups to grant them access
- Use descriptive group names and codes
- Document custom groups and their purposes

### ❌ Don't

- Don't try to assign roles directly to users (API will reject)
- Don't create groups for individual users
- Don't mix direct role assignments with group-based assignments
- Don't forget to remove users from groups when they change roles

## Troubleshooting

### User has no permissions

```bash
# Check if user is in any groups
GET /rbac/users/{user_id}/roles

# If no roles returned, add user to appropriate group
POST /rbac/groups/{group_id}/members
{
  "user_ids": ["user_id"]
}
```

### Group has no permissions

```bash
# Check group's roles
GET /rbac/groups/{group_id}

# If no roles, assign appropriate role to group
POST /rbac/groups/{group_id}/roles
{
  "role_ids": ["role_id"]
}
```

### Role has no permissions

```bash
# Check role's permissions
GET /rbac/roles/{role_id}

# If no permissions, assign them
POST /rbac/roles/{role_id}/permissions
{
  "permission_ids": ["perm_id_1", "perm_id_2"]
}
```

## Examples

### Example 1: New Employee Onboarding

```python
# 1. Create user
new_user = User(
    email="jane.doe@company.com",
    full_name="Jane Doe",
    tenant_id=tenant_id,
    # ... other fields
)
db.add(new_user)
db.flush()

# 2. Add to employees group
employees_group = db.query(Group).filter(
    Group.code == "employees",
    Group.tenant_id == tenant_id
).first()

user_group = UserGroup(
    user_id=new_user.id,
    group_id=employees_group.id
)
db.add(user_group)

# 3. Add to department group
engineering_group = db.query(Group).filter(
    Group.code == "engineering",
    Group.tenant_id == tenant_id
).first()

user_group = UserGroup(
    user_id=new_user.id,
    group_id=engineering_group.id
)
db.add(user_group)

db.commit()

# Jane now has: employee + developer roles
```

### Example 2: Promote to Manager

```python
# 1. Remove from employees group
db.query(UserGroup).filter(
    UserGroup.user_id == user_id,
    UserGroup.group_id == employees_group_id
).delete()

# 2. Add to managers group
user_group = UserGroup(
    user_id=user_id,
    group_id=managers_group_id
)
db.add(user_group)

db.commit()

# User now has manager role with supervisory access
```

### Example 3: Create Project Team

```python
# 1. Create project group
project_group = Group(
    tenant_id=tenant_id,
    company_id=company_id,
    code="mobile_app",
    name="Mobile App Project",
    group_type="project",
    is_active=True
)
db.add(project_group)
db.flush()

# 2. Assign developer and designer roles
for role_code in ["developer", "designer"]:
    role = db.query(Role).filter(Role.code == role_code).first()
    if role:
        db.add(GroupRole(group_id=project_group.id, role_id=role.id))

# 3. Add team members
team_emails = ["dev1@company.com", "dev2@company.com", "designer@company.com"]
for email in team_emails:
    user = db.query(User).filter(User.email == email).first()
    if user:
        db.add(UserGroup(user_id=user.id, group_id=project_group.id))

db.commit()
```

## Summary

The group-based RBAC model provides:

✓ **Scalability** - Manage thousands of users efficiently
✓ **Consistency** - One clear permission inheritance path
✓ **Flexibility** - Easily reassign access by moving users between groups
✓ **Auditability** - Clear trail of who has what access and why
✓ **Maintainability** - Change group roles affects all members automatically

For questions or issues, refer to the main RBAC documentation or raise an issue.
