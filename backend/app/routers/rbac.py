"""
RBAC Management Router
Provides comprehensive endpoints for managing roles, permissions, groups, and user assignments.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from typing import List, Optional
from uuid import UUID

from app.core.dependencies import get_db, get_current_user, has_permission
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.group import Group
from app.models.rbac_junctions import UserRole, RolePermission, GroupRole, UserGroup
from app.models.tenant import Tenant
from app.models.company import Company
from app.core.audit import audit_log

router = APIRouter(prefix="/rbac", tags=["RBAC Management"])


# ============================================================================
# PERMISSION ENDPOINTS
# ============================================================================

@router.get("/permissions")
async def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all permissions with optional filtering"""
    query = db.query(Permission)

    # Apply filters
    if category:
        query = query.filter(Permission.category == category)
    if search:
        query = query.filter(
            or_(
                Permission.code.ilike(f"%{search}%"),
                Permission.name.ilike(f"%{search}%"),
                Permission.description.ilike(f"%{search}%")
            )
        )
    if is_active is not None:
        query = query.filter(Permission.is_active == is_active)

    # Order by category and code
    query = query.order_by(Permission.category, Permission.code)

    # Get total count
    total = query.count()

    # Paginate
    permissions = query.offset(skip).limit(limit).all()

    return {
        "items": [
            {
                "id": str(p.id),
                "code": p.code,
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "is_system": p.is_system,
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in permissions
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/permissions/{permission_id}")
async def get_permission(
    permission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get permission details including which roles have it"""
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    # Get roles that have this permission
    role_permissions = (
        db.query(RolePermission)
        .filter(RolePermission.permission_id == permission_id)
        .options(joinedload(RolePermission.role))
        .all()
    )

    return {
        "id": str(permission.id),
        "code": permission.code,
        "name": permission.name,
        "description": permission.description,
        "category": permission.category,
        "is_system": permission.is_system,
        "is_active": permission.is_active,
        "roles": [
            {
                "id": str(rp.role.id),
                "code": rp.role.code,
                "name": rp.role.name,
                "is_active": rp.role.is_active
            }
            for rp in role_permissions if rp.role
        ],
        "created_at": permission.created_at.isoformat() if permission.created_at else None,
        "updated_at": permission.updated_at.isoformat() if permission.updated_at else None
    }


# ============================================================================
# ROLE ENDPOINTS
# ============================================================================

@router.get("/roles")
async def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role_type: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    tenant_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all roles with optional filtering"""
    query = db.query(Role)

    # Apply filters
    if role_type:
        query = query.filter(Role.role_type == role_type)
    if search:
        query = query.filter(
            or_(
                Role.code.ilike(f"%{search}%"),
                Role.name.ilike(f"%{search}%"),
                Role.description.ilike(f"%{search}%")
            )
        )
    if is_active is not None:
        query = query.filter(Role.is_active == is_active)

    # Tenant filtering
    if tenant_id:
        query = query.filter(
            or_(
                Role.tenant_id == tenant_id,
                Role.tenant_id.is_(None)  # Include system roles
            )
        )
    elif not current_user.is_superuser:
        # Non-superusers see only their tenant's roles + system roles
        query = query.filter(
            or_(
                Role.tenant_id == current_user.tenant_id,
                Role.tenant_id.is_(None)
            )
        )

    # Order by role_type and code
    query = query.order_by(Role.role_type, Role.code)

    # Get total count
    total = query.count()

    # Paginate
    roles = query.offset(skip).limit(limit).all()

    return {
        "items": [
            {
                "id": str(r.id),
                "code": r.code,
                "name": r.name,
                "description": r.description,
                "role_type": r.role_type,
                "is_system": r.is_system,
                "is_active": r.is_active,
                "tenant_id": str(r.tenant_id) if r.tenant_id else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            }
            for r in roles
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/roles/{role_id}")
async def get_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get role details including permissions and assignments"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Get permissions
    role_permissions = (
        db.query(RolePermission)
        .filter(RolePermission.role_id == role_id)
        .options(joinedload(RolePermission.permission))
        .all()
    )

    # Get direct user assignments
    user_roles = (
        db.query(UserRole)
        .filter(UserRole.role_id == role_id)
        .options(joinedload(UserRole.user))
        .all()
    )

    # Get group assignments
    group_roles = (
        db.query(GroupRole)
        .filter(GroupRole.role_id == role_id)
        .options(joinedload(GroupRole.group))
        .all()
    )

    return {
        "id": str(role.id),
        "code": role.code,
        "name": role.name,
        "description": role.description,
        "role_type": role.role_type,
        "is_system": role.is_system,
        "is_active": role.is_active,
        "tenant_id": str(role.tenant_id) if role.tenant_id else None,
        "permissions": [
            {
                "id": str(rp.permission.id),
                "code": rp.permission.code,
                "name": rp.permission.name,
                "category": rp.permission.category,
                "is_active": rp.permission.is_active
            }
            for rp in role_permissions if rp.permission
        ],
        "users": [
            {
                "id": str(ur.user.id),
                "email": ur.user.email,
                "full_name": ur.user.full_name,
                "is_active": ur.user.is_active
            }
            for ur in user_roles if ur.user
        ],
        "groups": [
            {
                "id": str(gr.group.id),
                "name": gr.group.name,
                "group_type": gr.group.group_type,
                "is_active": gr.group.is_active
            }
            for gr in group_roles if gr.group
        ],
        "created_at": role.created_at.isoformat() if role.created_at else None,
        "updated_at": role.updated_at.isoformat() if role.updated_at else None
    }


@router.post("/roles/{role_id}/permissions")
async def assign_permissions_to_role(
    role_id: UUID,
    permission_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign multiple permissions to a role"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role.is_system and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot modify system role")

    # Get existing assignments
    existing = db.query(RolePermission.permission_id).filter(
        RolePermission.role_id == role_id
    ).all()
    existing_ids = {str(p[0]) for p in existing}

    # Add new permissions
    added = []
    for perm_id in permission_ids:
        if str(perm_id) not in existing_ids:
            # Verify permission exists
            perm = db.query(Permission).filter(Permission.id == perm_id).first()
            if not perm:
                continue

            role_perm = RolePermission(
                role_id=role_id,
                permission_id=perm_id,
                granted_by_id=current_user.id
            )
            db.add(role_perm)
            added.append(str(perm_id))

    db.commit()

    audit_log(
        db,
        action="assign_permissions_to_role",
        entity_type="Role",
        entity_id=role_id,
        user_id=current_user.id,
        changes={
            "role_code": role.code,
            "permissions_added": added
        }
    )

    return {"message": f"Added {len(added)} permissions to role", "added": added}


@router.delete("/roles/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a permission from a role"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role.is_system and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot modify system role")

    role_perm = db.query(RolePermission).filter(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id
    ).first()

    if not role_perm:
        raise HTTPException(status_code=404, detail="Permission assignment not found")

    db.delete(role_perm)
    db.commit()

    audit_log(
        db,
        action="remove_permission_from_role",
        entity_type="Role",
        entity_id=role_id,
        user_id=current_user.id,
        changes={
            "role_code": role.code,
            "permission_id": str(permission_id)
        }
    )

    return {"message": "Permission removed from role"}


# ============================================================================
# GROUP ENDPOINTS
# ============================================================================

@router.get("/groups")
async def list_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    group_type: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    company_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all groups with optional filtering"""
    query = db.query(Group)

    # Apply filters
    if not current_user.is_superuser:
        query = query.filter(Group.tenant_id == current_user.tenant_id)

    if group_type:
        query = query.filter(Group.group_type == group_type)
    if search:
        query = query.filter(
            or_(
                Group.name.ilike(f"%{search}%"),
                Group.description.ilike(f"%{search}%")
            )
        )
    if is_active is not None:
        query = query.filter(Group.is_active == is_active)
    if company_id:
        query = query.filter(
            or_(
                Group.company_id == company_id,
                Group.company_id.is_(None)  # Include tenant-wide groups
            )
        )

    # Order by group_type and name
    query = query.order_by(Group.group_type, Group.name)

    # Get total count
    total = query.count()

    # Paginate
    groups = query.offset(skip).limit(limit).all()

    return {
        "items": [
            {
                "id": str(g.id),
                "name": g.name,
                "description": g.description,
                "group_type": g.group_type,
                "is_active": g.is_active,
                "tenant_id": str(g.tenant_id) if g.tenant_id else None,
                "company_id": str(g.company_id) if g.company_id else None,
                "created_at": g.created_at.isoformat() if g.created_at else None,
                "updated_at": g.updated_at.isoformat() if g.updated_at else None
            }
            for g in groups
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/groups/{group_id}")
async def get_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get group details including members and roles"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Get members
    user_groups = (
        db.query(UserGroup)
        .filter(UserGroup.group_id == group_id)
        .options(joinedload(UserGroup.user))
        .all()
    )

    # Get roles
    group_roles = (
        db.query(GroupRole)
        .filter(GroupRole.group_id == group_id)
        .options(joinedload(GroupRole.role))
        .all()
    )

    # Calculate effective permissions through roles
    all_permissions = set()
    for gr in group_roles:
        if gr.role and gr.role.is_active:
            role_perms = (
                db.query(RolePermission)
                .filter(RolePermission.role_id == gr.role_id)
                .options(joinedload(RolePermission.permission))
                .all()
            )
            for rp in role_perms:
                if rp.permission and rp.permission.is_active:
                    all_permissions.add(rp.permission.code)

    return {
        "id": str(group.id),
        "name": group.name,
        "description": group.description,
        "group_type": group.group_type,
        "is_active": group.is_active,
        "tenant_id": str(group.tenant_id) if group.tenant_id else None,
        "company_id": str(group.company_id) if group.company_id else None,
        "members": [
            {
                "id": str(ug.user.id),
                "email": ug.user.email,
                "full_name": ug.user.full_name,
                "is_active": ug.user.is_active,
                "joined_at": ug.created_at.isoformat() if ug.created_at else None
            }
            for ug in user_groups if ug.user
        ],
        "roles": [
            {
                "id": str(gr.role.id),
                "code": gr.role.code,
                "name": gr.role.name,
                "is_active": gr.role.is_active
            }
            for gr in group_roles if gr.role
        ],
        "effective_permissions": sorted(list(all_permissions)),
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "updated_at": group.updated_at.isoformat() if group.updated_at else None
    }


@router.post("/groups/{group_id}/members")
async def add_members_to_group(
    group_id: UUID,
    user_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add multiple users to a group"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Get existing members
    existing = db.query(UserGroup.user_id).filter(
        UserGroup.group_id == group_id
    ).all()
    existing_ids = {str(u[0]) for u in existing}

    # Add new members
    added = []
    for user_id in user_ids:
        if str(user_id) not in existing_ids:
            # Verify user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                continue

            user_group = UserGroup(
                user_id=user_id,
                group_id=group_id,
                granted_by_id=current_user.id
            )
            db.add(user_group)
            added.append(str(user_id))

    db.commit()

    audit_log(
        db,
        action="add_members_to_group",
        entity_type="Group",
        entity_id=group_id,
        user_id=current_user.id,
        changes={
            "group_name": group.name,
            "members_added": added
        }
    )

    return {"message": f"Added {len(added)} members to group", "added": added}


@router.delete("/groups/{group_id}/members/{user_id}")
async def remove_member_from_group(
    group_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a user from a group"""
    user_group = db.query(UserGroup).filter(
        UserGroup.group_id == group_id,
        UserGroup.user_id == user_id
    ).first()

    if not user_group:
        raise HTTPException(status_code=404, detail="User not in group")

    db.delete(user_group)
    db.commit()

    audit_log(
        db,
        action="remove_member_from_group",
        entity_type="Group",
        entity_id=group_id,
        user_id=current_user.id,
        changes={
            "removed_user_id": str(user_id)
        }
    )

    return {"message": "User removed from group"}


@router.post("/groups/{group_id}/roles")
async def assign_roles_to_group(
    group_id: UUID,
    role_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign multiple roles to a group"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Get existing assignments
    existing = db.query(GroupRole.role_id).filter(
        GroupRole.group_id == group_id
    ).all()
    existing_ids = {str(r[0]) for r in existing}

    # Add new roles
    added = []
    for role_id in role_ids:
        if str(role_id) not in existing_ids:
            # Verify role exists
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                continue

            group_role = GroupRole(
                group_id=group_id,
                role_id=role_id,
                granted_by_id=current_user.id
            )
            db.add(group_role)
            added.append(str(role_id))

    db.commit()

    audit_log(
        db,
        action="assign_roles_to_group",
        entity_type="Group",
        entity_id=group_id,
        user_id=current_user.id,
        changes={
            "group_name": group.name,
            "roles_added": added
        }
    )

    return {"message": f"Added {len(added)} roles to group", "added": added}


@router.delete("/groups/{group_id}/roles/{role_id}")
async def remove_role_from_group(
    group_id: UUID,
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a role from a group"""
    group_role = db.query(GroupRole).filter(
        GroupRole.group_id == group_id,
        GroupRole.role_id == role_id
    ).first()

    if not group_role:
        raise HTTPException(status_code=404, detail="Role assignment not found")

    db.delete(group_role)
    db.commit()

    audit_log(
        db,
        action="remove_role_from_group",
        entity_type="Group",
        entity_id=group_id,
        user_id=current_user.id,
        changes={
            "role_id": str(role_id)
        }
    )

    return {"message": "Role removed from group"}


# ============================================================================
# USER RBAC ENDPOINTS
# ============================================================================

@router.get("/users/{user_id}/roles")
async def get_user_roles(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all roles for a user (both direct and through groups)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get direct roles
    direct_roles = (
        db.query(UserRole)
        .filter(UserRole.user_id == user_id)
        .options(joinedload(UserRole.role))
        .all()
    )

    # Get roles through groups
    group_roles = (
        db.query(GroupRole)
        .join(UserGroup, UserGroup.group_id == GroupRole.group_id)
        .filter(UserGroup.user_id == user_id)
        .options(joinedload(GroupRole.role), joinedload(GroupRole.group))
        .all()
    )

    return {
        "user_id": str(user_id),
        "email": user.email,
        "full_name": user.full_name,
        "direct_roles": [
            {
                "id": str(ur.role.id),
                "code": ur.role.code,
                "name": ur.role.name,
                "is_active": ur.role.is_active
            }
            for ur in direct_roles if ur.role
        ],
        "group_roles": [
            {
                "role_id": str(gr.role.id),
                "role_code": gr.role.code,
                "role_name": gr.role.name,
                "group_id": str(gr.group.id),
                "group_name": gr.group.name,
                "is_active": gr.role.is_active and gr.group.is_active
            }
            for gr in group_roles if gr.role and gr.group
        ]
    }


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all effective permissions for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Use the model's get_permissions method
    permissions = user.get_permissions() if hasattr(user, 'get_permissions') else set()

    # Get details for each permission
    permission_details = []
    if permissions:
        perms = db.query(Permission).filter(Permission.code.in_(permissions)).all()
        permission_details = [
            {
                "id": str(p.id),
                "code": p.code,
                "name": p.name,
                "category": p.category,
                "description": p.description
            }
            for p in perms
        ]

    return {
        "user_id": str(user_id),
        "email": user.email,
        "full_name": user.full_name,
        "is_superuser": user.is_superuser,
        "permissions": permission_details,
        "permission_codes": sorted(list(permissions))
    }


@router.post("/users/{user_id}/roles")
async def assign_roles_to_user(
    user_id: UUID,
    role_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign multiple roles directly to a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get existing assignments
    existing = db.query(UserRole.role_id).filter(
        UserRole.user_id == user_id
    ).all()
    existing_ids = {str(r[0]) for r in existing}

    # Add new roles
    added = []
    for role_id in role_ids:
        if str(role_id) not in existing_ids:
            # Verify role exists
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                continue

            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                granted_by_id=current_user.id
            )
            db.add(user_role)
            added.append(str(role_id))

    db.commit()

    audit_log(
        db,
        action="assign_roles_to_user",
        entity_type="User",
        entity_id=user_id,
        user_id=current_user.id,
        changes={
            "user_email": user.email,
            "roles_added": added
        }
    )

    return {"message": f"Added {len(added)} roles to user", "added": added}


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: UUID,
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a role from a user"""
    user_role = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id
    ).first()

    if not user_role:
        raise HTTPException(status_code=404, detail="Role assignment not found")

    db.delete(user_role)
    db.commit()

    audit_log(
        db,
        action="remove_role_from_user",
        entity_type="User",
        entity_id=user_id,
        user_id=current_user.id,
        changes={
            "role_id": str(role_id)
        }
    )

    return {"message": "Role removed from user"}


# ============================================================================
# ORGANIZATION STRUCTURE ENDPOINTS
# ============================================================================

@router.get("/organization-structure")
async def get_organization_structure(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: Optional[str] = None
):
    """Get complete organization structure for a tenant"""
    # Determine which tenant to query
    query_tenant_id = tenant_id if current_user.is_superuser and tenant_id else current_user.tenant_id

    # Get tenant
    tenant = db.query(Tenant).filter(Tenant.id == query_tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get companies
    companies = db.query(Company).filter(Company.tenant_id == query_tenant_id).all()

    # Get groups
    groups = db.query(Group).filter(Group.tenant_id == query_tenant_id).all()

    # Get users
    users = db.query(User).filter(User.tenant_id == query_tenant_id).all()

    # Get roles (system + tenant-specific)
    roles = db.query(Role).filter(
        or_(
            Role.tenant_id == query_tenant_id,
            Role.tenant_id.is_(None)
        )
    ).all()

    return {
        "tenant": {
            "id": str(tenant.id),
            "name": tenant.name,
            "is_active": tenant.is_active
        },
        "companies": [
            {
                "id": str(c.id),
                "name": c.name,
                "is_active": c.is_active
            }
            for c in companies
        ],
        "groups": [
            {
                "id": str(g.id),
                "name": g.name,
                "group_type": g.group_type,
                "company_id": str(g.company_id) if g.company_id else None,
                "is_active": g.is_active,
                "member_count": db.query(func.count(UserGroup.user_id)).filter(
                    UserGroup.group_id == g.id
                ).scalar()
            }
            for g in groups
        ],
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "is_superuser": u.is_superuser
            }
            for u in users
        ],
        "roles": [
            {
                "id": str(r.id),
                "code": r.code,
                "name": r.name,
                "role_type": r.role_type,
                "is_system": r.is_system,
                "is_active": r.is_active
            }
            for r in roles
        ]
    }


@router.get("/permission-categories")
async def get_permission_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all permission categories with counts"""
    categories = (
        db.query(
            Permission.category,
            func.count(Permission.id).label('count')
        )
        .group_by(Permission.category)
        .all()
    )

    return {
        "categories": [
            {
                "name": cat[0],
                "count": cat[1]
            }
            for cat in categories if cat[0]
        ]
    }
