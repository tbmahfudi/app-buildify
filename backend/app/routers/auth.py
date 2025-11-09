from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from sqlalchemy.orm.exc import StaleDataError

from app.core.dependencies import get_db, get_current_user
from app.core.auth import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import ACCESS_TOKEN_EXPIRE_MIN
from app.core.audit import create_audit_log
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, UserResponse, ProfileUpdate, PasswordChangeRequest

security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["auth"])
# Set up logger at the top of your file
logger = logging.getLogger(__name__)

@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticates user and returns JWT tokens.
    Tenant ID is securely embedded in the JWT token payload.
    """
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        # Audit failed login attempt
        create_audit_log(
            db=db,
            action="login",
            user=None,
            entity_type="user",
            entity_id=credentials.email,
            request=request,
            status="failure",
            error_message="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        # Audit inactive user login attempt
        create_audit_log(
            db=db,
            action="login",
            user=user,
            entity_type="user",
            entity_id=str(user.id),
            request=request,
            status="failure",
            error_message="User account is inactive"
        )
        raise HTTPException(status_code=403, detail="Inactive user")

    # Get user permissions from RBAC system
    permissions = list(user.get_permissions()) if hasattr(user, 'get_permissions') else []

    # Create tokens with user context
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "permissions": permissions
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

    # Audit successful login
    create_audit_log(
        db=db,
        action="login",
        user=user,
        entity_type="user",
        entity_id=str(user.id),
        request=request,
        status="success"
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MIN * 60  # Convert minutes to seconds
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

    # Get user permissions from RBAC system
    permissions = list(user.get_permissions()) if hasattr(user, 'get_permissions') else []

    # Generate new tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "permissions": permissions
    }

    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MIN * 60  # Convert minutes to seconds
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    # Get user permissions from RBAC system
    # For backward compatibility with UserResponse schema, convert permissions to roles list
    permissions = list(current_user.get_permissions()) if hasattr(current_user, 'get_permissions') else []

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        default_company_id=str(current_user.default_company_id) if current_user.default_company_id else None,
        branch_id=str(current_user.branch_id) if current_user.branch_id else None,
        department_id=str(current_user.department_id) if current_user.department_id else None,
        roles=permissions,  # Using permissions instead of deprecated roles field
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login
    )

@router.put("/me", response_model=UserResponse)
def update_me(
    profile_data: ProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    # Check if email is being changed and if it's already in use
    if profile_data.email and profile_data.email != current_user.email:
        existing_user = db.query(User).filter(User.email == profile_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = profile_data.email

    # Update other fields
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name

    if profile_data.phone is not None:
        current_user.phone = profile_data.phone

    current_user.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(current_user)

        # Audit profile update
        create_audit_log(
            db=db,
            action="update_profile",
            user=current_user,
            entity_type="user",
            entity_id=str(current_user.id),
            request=request,
            status="success"
        )

        logger.info(f"User {current_user.id} updated their profile")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

    # Get user permissions
    permissions = list(current_user.get_permissions()) if hasattr(current_user, 'get_permissions') else []

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        default_company_id=str(current_user.default_company_id) if current_user.default_company_id else None,
        branch_id=str(current_user.branch_id) if current_user.branch_id else None,
        department_id=str(current_user.department_id) if current_user.department_id else None,
        roles=permissions,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login
    )

@router.post("/change-password")
def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        create_audit_log(
            db=db,
            action="change_password",
            user=current_user,
            entity_type="user",
            entity_id=str(current_user.id),
            request=request,
            status="failure",
            error_message="Invalid current password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Verify new password matches confirmation
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match"
        )

    # Import here to avoid circular dependency
    from app.core.auth import hash_password

    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    current_user.updated_at = datetime.utcnow()

    try:
        db.commit()

        # Audit password change
        create_audit_log(
            db=db,
            action="change_password",
            user=current_user,
            entity_type="user",
            entity_id=str(current_user.id),
            request=request,
            status="success"
        )

        logger.info(f"User {current_user.id} changed their password")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to change password for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

    return {"message": "Password changed successfully"}


@router.post("/logout")
def logout(
    request: Request,
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

    # Audit successful logout
    create_audit_log(
        db=db,
        action="logout",
        user=current_user,
        entity_type="user",
        entity_id=str(current_user.id),
        request=request,
        status="success"
    )

    logger.info(f"User {current_user.id} logged out successfully")
    return {"message": "Successfully logged out"}
