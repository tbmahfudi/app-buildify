from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..models.token_blacklist import TokenBlacklist
from ..models.user import User
from .auth import decode_token
from .db import SessionLocal

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate current user from JWT token.
    Tenant ID is now securely extracted from the JWT payload only.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is blacklisted (revoked)
    jti = payload.get("jti")
    if jti:
        blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    # Validate tenant_id from JWT matches user's tenant
    token_tenant_id = payload.get("tenant_id")
    if user.tenant_id and token_tenant_id and str(token_tenant_id) != str(user.tenant_id):
        raise HTTPException(
            status_code=401,
            detail="Token tenant mismatch - please re-authenticate"
        )

    return user

def verify_tenant_access(user: User, tenant_id: str) -> None:
    """
    Verify that the current user has access to the specified tenant.
    Superusers can access any tenant. Regular users can only access their own tenant.

    Args:
        user: The current authenticated user
        tenant_id: The tenant ID to verify access to

    Raises:
        HTTPException: If user doesn't have access to the tenant
    """
    if user.is_superuser:
        return  # Superusers can access any tenant

    if not user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="User has no tenant assignment"
        )

    if str(user.tenant_id) != str(tenant_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: You don't have permission to access this tenant's data"
        )

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser required")
    return current_user

def has_permission(permission: str):
    """
    Dependency to check if user has a specific permission.
    Uses the RBAC system to check permissions.

    Args:
        permission: Permission code to check (e.g., "users:create:tenant")

    Returns:
        Function that validates the permission
    """
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        # Superusers have all permissions
        if current_user.is_superuser:
            return current_user

        # Get user permissions from RBAC system
        user_permissions = current_user.get_permissions() if hasattr(current_user, 'get_permissions') else set()

        if permission not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker

def has_any_permission(permissions: List[str]):
    """
    Dependency to check if user has any of the specified permissions.

    Args:
        permissions: List of permission codes

    Returns:
        Function that validates user has at least one permission
    """
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        # Superusers have all permissions
        if current_user.is_superuser:
            return current_user

        # Get user permissions from RBAC system
        user_permissions = current_user.get_permissions() if hasattr(current_user, 'get_permissions') else set()

        if not any(perm in user_permissions for perm in permissions):
            raise HTTPException(
                status_code=403,
                detail=f"One of these permissions required: {', '.join(permissions)}"
            )
        return current_user
    return permission_checker

def has_role(role_code: str):
    """
    Dependency to check if user has a specific role.

    RBAC Consistency: Roles are assigned through groups only.
    Uses User.get_roles() which returns roles from group membership.

    Args:
        role_code: Role code to check (e.g., "tenant_admin", "manager")

    Returns:
        Function that validates the user has the role
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Superusers have all roles
        if current_user.is_superuser:
            return current_user

        # Get user roles from RBAC system (via groups)
        user_role_codes = current_user.get_roles() if hasattr(current_user, 'get_roles') else set()

        if role_code not in user_role_codes:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{role_code}' required"
            )
        return current_user
    return role_checker