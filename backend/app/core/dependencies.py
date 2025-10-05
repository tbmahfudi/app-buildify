from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
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
    db: Session = Depends(get_db),
    x_tenant_id: Optional[str] = Header(None)
) -> User:
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
    
    # Validate tenant access
    if x_tenant_id and user.tenant_id and user.tenant_id != x_tenant_id:
        if not user.is_superuser:
            raise HTTPException(status_code=403, detail="Tenant access denied")
    
    return user

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