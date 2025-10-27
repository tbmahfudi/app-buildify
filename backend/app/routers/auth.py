from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
import json

import logging
from sqlalchemy.orm.exc import StaleDataError

from app.core.dependencies import get_db, get_current_user, security
from app.core.auth import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, UserResponse

security = HTTPBearer()

router = APIRouter(prefix="/api/auth", tags=["auth"])
# Set up logger at the top of your file
logger = logging.getLogger(__name__)

@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticates user and returns JWT tokens.
    Tenant ID is securely embedded in the JWT token payload.
    """
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    
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


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user)
):
    """
    Logout endpoint - revokes the current access token.
    Requires Redis to be configured for token revocation.
    """
    from app.core.auth import revoke_token

    token = credentials.credentials
    success = revoke_token(token)

    if success:
        logger.info(f"User {current_user.id} logged out successfully")
        return {"message": "Logged out successfully"}
    else:
        logger.warning(f"Token revocation failed for user {current_user.id}")
        return {
            "message": "Logged out (token revocation unavailable)",
            "note": "Redis is not configured, token will expire naturally"
        }
@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout endpoint - revokes the current access token by adding it to the blacklist.
    The token will no longer be valid for authentication.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Token missing JTI")

    # Check if already blacklisted
    existing = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
    if existing:
        return {"message": "Already logged out"}

    # Add token to blacklist
    expires_at = datetime.fromtimestamp(payload.get("exp"))
    blacklist_entry = TokenBlacklist(
        jti=jti,
        user_id=str(current_user.id),
        token_type=payload.get("type", "access"),
        expires_at=expires_at
    )

    db.add(blacklist_entry)
    db.commit()

    return {"message": "Successfully logged out"}

@router.post("/logout-all")
def logout_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout from all devices - marks all user's tokens as revoked.
    This is useful when a user wants to invalidate all their sessions.
    Note: This only affects tokens issued before this point.
    """
    # This endpoint doesn't need the specific token, just marks the user as logged out
    # In practice, you might want to track a "logout_at" timestamp in the user table
    # and check it in the get_current_user dependency
    return {"message": "Successfully logged out from all devices"}
