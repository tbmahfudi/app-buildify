"""
RBAC Management Router
Provides comprehensive endpoints for managing roles, permissions, groups, and user assignments.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.audit import create_audit_log
from app.core.dependencies import get_current_user, get_db, has_permission
from app.models.branch import Branch
from app.models.company import Company
from app.models.department import Department
from app.models.group import Group
from app.models.permission import Permission
from app.models.rbac_junctions import GroupRole, RolePermission, UserGroup, UserRole
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter(prefix="/rbac", tags=["RBAC Management"])
logger = logging.getLogger(__name__)


# ============================================================================
# PERMISSION ENDPOINTS
# ============================================================================

@router.get("/permissions")
async def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("permissions:read:tenant")),
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    company_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all permissions with optional filtering - requires permissions:read:tenant"""
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

    # Note: company_id parameter accepted but not filtered
    # Permissions are system-wide, not company-specific
    # This parameter is here for API consistency but doesn't affect results

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
                "resource": p.resource,
                "action": p.action,
                "scope": p.scope,
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


@router.get("/permissions/grouped")
async def get_grouped_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("permissions:read:tenant")),
    role_id: Optional[str] = None,
    category: Optional[str] = None,
    scope: Optional[str] = None
):
    """
    Get permissions grouped by resource for easy permission management.
    Returns permissions organized by resource with standard CRUD actions and special actions.

    If role_id is provided, includes whether each permission is granted to that role.
    Requires permissions:read:tenant permission.
    """
    query = db.query(Permission).filter(Permission.is_active == True)

    # Apply filters
    if category:
        query = query.filter(Permission.category == category)
    if scope:
        query = query.filter(Permission.scope == scope)

    permissions = query.all()

    # Get role permissions if role_id provided
    role_permission_ids = set()
    if role_id:
        role_perms = db.query(RolePermission.permission_id).filter(
            RolePermission.role_id == role_id
        ).all()
        role_permission_ids = {str(p[0]) for p in role_perms}

    # Standard CRUD actions
    standard_actions = {'read', 'create', 'update', 'delete'}

    # Group by resource and scope
    grouped = {}
    for perm in permissions:
        # Create a key combining resource and scope
        key = f"{perm.resource}:{perm.scope}"

        if key not in grouped:
            grouped[key] = {
                "resource": perm.resource,
                "scope": perm.scope,
                "category": perm.category,
                "standard_actions": {},
                "special_actions": {}
            }

        perm_data = {
            "id": str(perm.id),
            "code": perm.code,
            "name": perm.name,
            "description": perm.description,
            "granted": str(perm.id) in role_permission_ids if role_id else False
        }

        # Categorize as standard or special
        if perm.action in standard_actions:
            grouped[key]["standard_actions"][perm.action] = perm_data
        else:
            grouped[key]["special_actions"][perm.action] = perm_data

    # Convert to list and sort
    result = []
    for key, data in grouped.items():
        result.append({
            "key": key,
            **data
        })

    # Sort by category, then resource
    result.sort(key=lambda x: (x["category"] or "", x["resource"]))

    return {
        "groups": result,
        "total_resources": len(result),
        "role_id": role_id
    }


@router.get("/permissions/{permission_id}")
async def get_permission(
    permission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("permissions:read:tenant"))
):
    """Get permission details including which roles have it - requires permissions:read:tenant"""
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
    current_user: User = Depends(has_permission("roles:read:tenant")),
    role_type: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    tenant_id: Optional[str] = None,
    company_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all roles with optional filtering - requires roles:read:tenant"""
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

    # Company filtering (company_id parameter takes precedence)
    if company_id:
        # When filtering by company, show tenant-level and system roles
        # (company-specific roles don't exist in current schema, so show tenant + system)
        query = query.filter(
            or_(
                Role.tenant_id == current_user.tenant_id,
                Role.tenant_id.is_(None)  # Include system roles
            )
        )
    # Tenant filtering
    elif tenant_id:
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
    current_user: User = Depends(has_permission("roles:read:tenant"))
):
    """Get role details including permissions and assignments - requires roles:read:tenant"""
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

    # Get direct user assignments (DEPRECATED - for backwards compatibility only)
    user_roles = (
        db.query(UserRole)
        .filter(UserRole.role_id == role_id)
        .options(joinedload(UserRole.user))
        .all()
    )

    # Get group assignments (CURRENT - group-based RBAC model)
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
        # DEPRECATED: Direct user-to-role assignments (use groups instead)
        "deprecated_direct_users": [
            {
                "id": str(ur.user.id),
                "email": ur.user.email,
                "full_name": ur.user.full_name,
                "is_active": ur.user.is_active
            }
            for ur in user_roles if ur.user
        ],
        # Current group-based assignments
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
    current_user: User = Depends(has_permission("roles:assign_permissions:tenant"))
):
    """Assign multiple permissions to a role - requires roles:assign_permissions:tenant"""
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

    create_audit_log(
        db,
        action="assign_permissions_to_role",
        entity_type="Role",
        entity_id=role_id,
        user=current_user,
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
    current_user: User = Depends(has_permission("roles:revoke_permissions:tenant"))
):
    """Remove a permission from a role - requires roles:revoke_permissions:tenant"""
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

    create_audit_log(
        db,
        action="remove_permission_from_role",
        entity_type="Role",
        entity_id=role_id,
        user=current_user,
        changes={
            "role_code": role.code,
            "permission_id": str(permission_id)
        }
    )

    return {"message": "Permission removed from role"}


@router.patch("/roles/{role_id}/permissions/bulk")
async def bulk_update_role_permissions(
    role_id: UUID,
    grant_ids: List[UUID],
    revoke_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("roles:assign_permissions:tenant"))
):
    """
    Bulk update role permissions - grant and revoke in a single transaction.
    This is more efficient than multiple individual calls.
    Requires roles:assign_permissions:tenant permission.

    Parameters:
    - grant_ids: List of permission IDs to grant
    - revoke_ids: List of permission IDs to revoke
    """
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

    # Grant new permissions
    granted = []
    for perm_id in grant_ids:
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
            granted.append(str(perm_id))

    # Revoke permissions
    revoked = []
    for perm_id in revoke_ids:
        if str(perm_id) in existing_ids:
            role_perm = db.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == perm_id
            ).first()
            if role_perm:
                db.delete(role_perm)
                revoked.append(str(perm_id))

    db.commit()

    create_audit_log(
        db,
        action="bulk_update_role_permissions",
        entity_type="Role",
        entity_id=role_id,
        user=current_user,
        changes={
            "role_code": role.code,
            "granted": granted,
            "revoked": revoked
        }
    )

    return {
        "message": "Permissions updated successfully",
        "granted": len(granted),
        "revoked": len(revoked),
        "granted_ids": granted,
        "revoked_ids": revoked
    }


# ============================================================================
# GROUP ENDPOINTS
# ============================================================================

@router.get("/groups")
async def list_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("groups:read:tenant")),
    group_type: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    company_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all groups with optional filtering - requires groups:read:tenant"""
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
    current_user: User = Depends(has_permission("groups:read:tenant"))
):
    """Get group details including members and roles - requires groups:read:tenant"""
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
    current_user: User = Depends(has_permission("groups:add_members:tenant"))
):
    """Add multiple users to a group - requires groups:add_members:tenant"""
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

    create_audit_log(
        db,
        action="add_members_to_group",
        entity_type="Group",
        entity_id=group_id,
        user=current_user,
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
    current_user: User = Depends(has_permission("groups:remove_members:tenant"))
):
    """Remove a user from a group - requires groups:remove_members:tenant"""
    user_group = db.query(UserGroup).filter(
        UserGroup.group_id == group_id,
        UserGroup.user_id == user_id
    ).first()

    if not user_group:
        raise HTTPException(status_code=404, detail="User not in group")

    db.delete(user_group)
    db.commit()

    create_audit_log(
        db,
        action="remove_member_from_group",
        entity_type="Group",
        entity_id=group_id,
        user=current_user,
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
    current_user: User = Depends(has_permission("groups:assign_roles:tenant"))
):
    """Assign multiple roles to a group - requires groups:assign_roles:tenant"""
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

    create_audit_log(
        db,
        action="assign_roles_to_group",
        entity_type="Group",
        entity_id=group_id,
        user=current_user,
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
    current_user: User = Depends(has_permission("groups:revoke_roles:tenant"))
):
    """Remove a role from a group - requires groups:revoke_roles:tenant"""
    group_role = db.query(GroupRole).filter(
        GroupRole.group_id == group_id,
        GroupRole.role_id == role_id
    ).first()

    if not group_role:
        raise HTTPException(status_code=404, detail="Role assignment not found")

    db.delete(group_role)
    db.commit()

    create_audit_log(
        db,
        action="remove_role_from_group",
        entity_type="Group",
        entity_id=group_id,
        user=current_user,
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
    current_user: User = Depends(has_permission("users:read_roles:tenant"))
):
    """
    Get all roles for a user through group membership only - requires users:read_roles:tenant

    RBAC Consistency: Roles are assigned to users through groups only.
    Direct user-to-role assignments are deprecated.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get roles through groups ONLY (consistent RBAC model)
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
        "roles": [
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
    current_user: User = Depends(has_permission("users:read_permissions:tenant"))
):
    """Get all effective permissions for a user - requires users:read_permissions:tenant"""
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
    current_user: User = Depends(has_permission("users:assign_roles:tenant"))
):
    """
    DEPRECATED: Direct role assignment is deprecated.
    Use group membership instead: Add user to groups, then assign roles to groups.

    This endpoint now raises an error to enforce consistent RBAC model.
    """
    raise HTTPException(
        status_code=400,
        detail=(
            "Direct role assignment is deprecated. "
            "Please assign users to groups instead, then assign roles to those groups. "
            "Use POST /rbac/groups/{group_id}/members to add users to groups, "
            "and POST /rbac/groups/{group_id}/roles to assign roles to groups."
        )
    )


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: UUID,
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("users:revoke_roles:tenant"))
):
    """
    DEPRECATED: Direct role removal is deprecated.
    Use group membership instead: Remove user from groups or remove roles from groups.

    This endpoint now raises an error to enforce consistent RBAC model.
    """
    raise HTTPException(
        status_code=400,
        detail=(
            "Direct role removal is deprecated. "
            "Please manage roles through groups instead. "
            "Use DELETE /rbac/groups/{group_id}/members/{user_id} to remove users from groups, "
            "or DELETE /rbac/groups/{group_id}/roles/{role_id} to remove roles from groups."
        )
    )


# ============================================================================
# ORGANIZATION STRUCTURE ENDPOINTS
# ============================================================================

@router.get("/organization-structure")
async def get_organization_structure(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("organization:view:tenant")),
    tenant_id: Optional[str] = None
):
    """Get complete organization structure for a tenant - requires organization:view:tenant"""
    # Determine which tenant to query
    query_tenant_id = tenant_id if current_user.is_superuser and tenant_id else current_user.tenant_id

    # If superuser has no tenant and no tenant specified, get first available tenant
    if not query_tenant_id and current_user.is_superuser:
        first_tenant = db.query(Tenant).first()
        if first_tenant:
            query_tenant_id = first_tenant.id
        else:
            # No tenants exist at all
            return {
                "tenant": None,
                "companies": [],
                "groups": [],
                "users": [],
                "roles": []
            }

    # Check if user has a tenant
    if not query_tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant assigned")

    # Get tenant
    tenant = db.query(Tenant).filter(Tenant.id == query_tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant not found: {query_tenant_id}")

    # Get companies
    companies = db.query(Company).filter(Company.tenant_id == query_tenant_id).all()

    # Get branches
    branches = db.query(Branch).filter(Branch.tenant_id == query_tenant_id).all()

    # Get departments
    departments = db.query(Department).filter(Department.tenant_id == query_tenant_id).all()

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

    # Build company hierarchy with branches and departments
    company_hierarchy = []
    for c in companies:
        # Get branches for this company
        company_branches = [b for b in branches if str(b.company_id) == str(c.id)]

        branches_data = []
        for b in company_branches:
            # Get departments for this branch
            branch_departments = [d for d in departments if str(d.branch_id) == str(b.id)]

            branches_data.append({
                "id": str(b.id),
                "name": b.name,
                "code": b.code,
                "is_active": b.is_active,
                "departments": [
                    {
                        "id": str(d.id),
                        "name": d.name,
                        "code": d.code,
                        "is_active": d.is_active
                    }
                    for d in branch_departments
                ]
            })

        # Get departments without branches (company-level departments)
        company_departments = [d for d in departments if d.branch_id is None and str(d.company_id) == str(c.id)]

        company_hierarchy.append({
            "id": str(c.id),
            "name": c.name,
            "is_active": c.is_active,
            "branches": branches_data,
            "departments": [
                {
                    "id": str(d.id),
                    "name": d.name,
                    "code": d.code,
                    "is_active": d.is_active
                }
                for d in company_departments
            ]
        })

    return {
        "tenant": {
            "id": str(tenant.id),
            "name": tenant.name,
            "is_active": tenant.is_active
        },
        "companies": company_hierarchy,
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
    current_user: User = Depends(has_permission("permissions:read:tenant"))
):
    """Get all permission categories with counts - requires permissions:read:tenant"""
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
