from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import json

import logging
from sqlalchemy.orm.exc import StaleDataError

from app.core.dependencies import get_db, get_current_user
from app.core.auth import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
# Set up logger at the top of your file
logger = logging.getLogger(__name__)

@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
    x_tenant_id: Optional[str] = Header(None)
):
    """Login endpoint with optional tenant context"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    
    # Validate tenant access
    if x_tenant_id and user.tenant_id and user.tenant_id != x_tenant_id:
        if not user.is_superuser:
            raise HTTPException(status_code=403, detail="Tenant access denied")
    
    # Parse roles
    try:
        roles = json.loads(user.roles or "[]")
    except:
        roles = []
    
    # Create tokens with user context
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "tenant_id": user.tenant_id,
        "roles": roles
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})
    # Update last login - Fix for StaleDataError
    try:
        logger.info(f"Updating last_login for user {user.id}")
        logger.debug(f"User object state before update: {db.object_session(user)}")
        
        # Ensure the object is in the session
        if user not in db:
            logger.warning(f"User {user.id} not in session, re-querying")
            user = db.query(User).filter(User.id == user.id).first()
            if not user:
                raise HTTPException(status_code=500, detail="User session error")
        
        user.last_login = datetime.utcnow()
        db.flush()  # Flush to see if there are any issues before commit
        logger.debug(f"Flushed successfully, now committing")
        db.commit()
        logger.info(f"Successfully updated last_login for user {user.id}")
        
    except StaleDataError as e:
        logger.error(f"StaleDataError for user {user.id}: {e}")
        db.rollback()
        # Still return tokens even if last_login update fails
        logger.warning("Proceeding with login despite last_login update failure")
    except Exception as e:
        logger.error(f"Unexpected error updating last_login for user {user.id}: {e}")
        db.rollback()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )
    
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh(refresh_req: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    payload = decode_token(refresh_req.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Parse roles
    try:
        roles = json.loads(user.roles or "[]")
    except:
        roles = []
    
    # Generate new tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "tenant_id": user.tenant_id,
        "roles": roles
    }
    
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    try:
        roles = json.loads(current_user.roles or "[]")
    except:
        roles = []
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        tenant_id=current_user.tenant_id,
        roles=roles,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )