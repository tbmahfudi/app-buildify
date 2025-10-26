from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
import json
from .db import SessionLocal
from .auth import decode_token
from ..models.user import User

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
    if user.tenant_id and token_tenant_id != user.tenant_id:
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

    if user.tenant_id != tenant_id:
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

def has_role(role: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        try:
            user_roles = json.loads(current_user.roles or "[]")
        except:
            user_roles = []
        
        if role not in user_roles and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail=f"Role '{role}' required")
        return current_user
    return role_checker