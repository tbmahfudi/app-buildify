import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.audit import create_audit_log
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.config import ACCESS_TOKEN_EXPIRE_MIN
from app.core.dependencies import get_current_user, get_db
from app.core.lockout_manager import LockoutManager
from app.core.notification_service import NotificationService
from app.core.password_history import PasswordHistoryService
from app.core.password_validator import PasswordValidator

# Import security services
from app.core.security_config import SecurityConfigService
from app.core.session_manager import SessionManager
from app.models.login_attempt import LoginAttempt
from app.models.password_reset_token import PasswordResetToken
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.models.user_session import UserSession
from app.models.tenant import Tenant
from app.models.company import Company
from app.models.branch import Branch
from app.models.department import Department
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    ProfileUpdate,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.security import PasswordPolicyRequirements, PasswordStrengthCheck

security = HTTPBearer()

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
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
    Integrates with security policy system for lockout, sessions, and login attempt tracking.
    """
    # Get request metadata
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # Initialize security services
    lockout_manager = LockoutManager(db)
    session_manager = SessionManager(db)

    # Find user by identifier (ADR-HC-009 D1): an '@' means email, otherwise it is
    # a username (case-insensitive). Patients may log in with either.
    identifier = credentials.email
    if "@" in identifier:
        user = db.query(User).filter(User.email == identifier).first()
    else:
        user = db.query(User).filter(func.lower(User.username) == identifier.lower()).first()

    # Record failed login attempt if user not found or password incorrect
    if not user or not verify_password(credentials.password, user.hashed_password):
        # Record failed login attempt
        login_attempt = LoginAttempt(
            user_id=str(user.id) if user else None,
            email=credentials.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            failure_reason="Invalid credentials"
        )
        db.add(login_attempt)
        db.commit()

        # If user exists, record failed attempt for lockout tracking
        if user:
            lockout_manager.record_failed_login(user)

        # Audit failed login attempt
        create_audit_log(
            db=db,
            action="login",
            user=user,
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

    # Check if account is locked
    if lockout_manager.is_account_locked(user):
        locked_until = user.locked_until

        # Record failed login attempt due to lockout
        login_attempt = LoginAttempt(
            user_id=str(user.id),
            email=credentials.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            failure_reason=f"Account locked until {locked_until}"
        )
        db.add(login_attempt)
        db.commit()

        # Audit lockout attempt
        create_audit_log(
            db=db,
            action="login",
            user=user,
            entity_type="user",
            entity_id=str(user.id),
            request=request,
            status="failure",
            error_message=f"Account locked until {locked_until}"
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked until {locked_until}. Please try again later or contact support."
        )

    # Check if account is active
    if not user.is_active:
        # Record failed login attempt
        login_attempt = LoginAttempt(
            user_id=str(user.id),
            email=credentials.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            failure_reason="User account is inactive"
        )
        db.add(login_attempt)
        db.commit()

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

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Check password expiration
    security_config = SecurityConfigService(db)
    password_expired = False
    grace_login_allowed = False

    if user.password_expires_at and user.password_expires_at < datetime.utcnow():
        password_expired = True
        # Check if grace logins are allowed
        grace_logins = security_config.get_config("password_grace_logins", user.tenant_id)
        if grace_logins and user.grace_logins_remaining and user.grace_logins_remaining > 0:
            grace_login_allowed = True
            user.grace_logins_remaining -= 1
        else:
            # Record failed login attempt due to password expiration
            login_attempt = LoginAttempt(
                user_id=str(user.id),
                email=credentials.email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason="Password expired"
            )
            db.add(login_attempt)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Password has expired. Please reset your password."
            )

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

    # Decode token to get JTI for session tracking
    access_token_payload = decode_token(access_token)
    jti = access_token_payload.get("jti") if access_token_payload else None

    # Create user session
    if jti:
        try:
            session_manager.create_session(
                user=user,
                jti=jti,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            logger.warning(f"Failed to create session for user {user.id}: {e}")
            # Continue with login even if session creation fails

    # Record successful login attempt
    login_attempt = LoginAttempt(
        user_id=str(user.id),
        email=credentials.email,
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        failure_reason=None
    )
    db.add(login_attempt)

    # Reset failed login attempts on successful login
    lockout_manager.reset_failed_attempts(user)

    # Update last login
    try:
        user.last_login = datetime.utcnow()
        db.commit()
        logger.info(f"Successfully updated last_login for user {user.id}")
    except Exception as e:
        logger.error(f"Error updating last_login for user {user.id}: {e}")
        db.rollback()
        db.commit()  # Commit the login attempt even if last_login fails

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

    # If password expired but grace login allowed, include warning in response
    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MIN * 60
    }

    if password_expired and grace_login_allowed:
        logger.info(f"User {user.id} logged in with expired password. Grace logins remaining: {user.grace_logins_remaining}")

    return TokenResponse(**response_data)


@router.get("/config")
def get_auth_config(
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get auth configuration for the frontend.
    Public endpoint — returns platform default when no tenant_id is provided.
    """
    svc = SecurityConfigService(db)
    timeout = svc.get_config("session_timeout_minutes", tenant_id) or 30
    return {"idle_timeout_minutes": int(timeout)}


@router.get("/password-policy", response_model=PasswordPolicyRequirements)
def get_password_policy(
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get password policy requirements for display to users.
    This is a public endpoint (no authentication required) to show password requirements
    during registration or password change.
    """
    security_config = SecurityConfigService(db)

    # Get password policy configuration
    min_length = security_config.get_config("password_min_length", tenant_id) or 8
    require_uppercase = security_config.get_config("password_require_uppercase", tenant_id)
    require_lowercase = security_config.get_config("password_require_lowercase", tenant_id)
    require_digit = security_config.get_config("password_require_digit", tenant_id)
    require_special = security_config.get_config("password_require_special_char", tenant_id)
    min_unique_chars = security_config.get_config("password_min_unique_chars", tenant_id)
    allow_common = security_config.get_config("password_allow_common", tenant_id)
    expiration_days = security_config.get_config("password_expiration_days", tenant_id) or 0
    warning_days = security_config.get_config("password_expiration_warning_days", tenant_id) or 0
    grace_logins = security_config.get_config("password_grace_logins", tenant_id) or 0

    # Build requirements list
    requirements = []
    requirements.append(f"At least {min_length} characters long")

    if require_uppercase:
        requirements.append("At least one uppercase letter (A-Z)")

    if require_lowercase:
        requirements.append("At least one lowercase letter (a-z)")

    if require_digit:
        requirements.append("At least one number (0-9)")

    if require_special:
        requirements.append("At least one special character (!@#$%^&*)")

    if min_unique_chars and min_unique_chars > 0:
        requirements.append(f"At least {min_unique_chars} unique characters")

    if not allow_common:
        requirements.append("Cannot be a commonly used password")

    if expiration_days > 0:
        requirements.append(f"Password expires after {expiration_days} days")

    return PasswordPolicyRequirements(
        requirements=requirements,
        expiration_days=expiration_days,
        warning_days=warning_days,
        grace_logins=grace_logins
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

    # Enforce idle session timeout
    session_manager = SessionManager(db)
    security_config = SecurityConfigService(db)
    idle_timeout_minutes = security_config.get_config("session_timeout_minutes", user.tenant_id) or 30

    # Find the most recent active session for this user
    active_session = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == str(user.id),
            UserSession.revoked_at == None,
            UserSession.expires_at > datetime.utcnow(),
        )
        .order_by(UserSession.last_activity.desc())
        .first()
    )

    if active_session and active_session.last_activity:
        idle_seconds = (datetime.utcnow() - active_session.last_activity).total_seconds()
        if idle_seconds / 60 > idle_timeout_minutes:
            raise HTTPException(status_code=401, detail="Session expired due to inactivity")

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

    # Bump last_activity on the session so active users stay logged in
    if active_session:
        session_manager.update_activity(active_session.jti)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MIN * 60  # Convert minutes to seconds
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile (incl. resolved tenant/company/branch names)."""
    # Get user roles and permissions from RBAC system
    roles = list(current_user.get_roles()) if hasattr(current_user, 'get_roles') else []
    permissions = list(current_user.get_permissions()) if hasattr(current_user, 'get_permissions') else []

    # Resolve human-readable org context. The platform superadmin has no tenant
    # and is shown as "System"; all other levels are null-safe lookups.
    is_system = bool(current_user.is_superuser and not current_user.tenant_id)
    tenant_name = "System" if is_system else None
    company_name = branch_name = department_name = None

    def _name(model, pk):
        if not pk:
            return None
        obj = db.query(model).filter(model.id == pk).first()
        return obj.name if obj else None

    if not is_system:
        if current_user.tenant_id:
            tenant_name = _name(Tenant, current_user.tenant_id)
        company_name = _name(Company, current_user.default_company_id)
        branch_name = _name(Branch, current_user.branch_id)
        department_name = _name(Department, current_user.department_id)

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        display_name=current_user.display_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        default_company_id=str(current_user.default_company_id) if current_user.default_company_id else None,
        branch_id=str(current_user.branch_id) if current_user.branch_id else None,
        department_id=str(current_user.department_id) if current_user.department_id else None,
        is_system=is_system,
        tenant_name=tenant_name,
        company_name=company_name,
        branch_name=branch_name,
        department_name=department_name,
        roles=roles,
        permissions=permissions,
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

    if profile_data.display_name is not None:
        # Truncate display_name to 50 characters if needed
        display_name = profile_data.display_name[:50] if profile_data.display_name else None
        current_user.display_name = display_name

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
        display_name=current_user.display_name,
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
    """
    Change current user password with password policy validation and history tracking.
    """
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

    # Initialize security services
    security_config = SecurityConfigService(db)
    password_validator = PasswordValidator(db, current_user.tenant_id)
    password_history_service = PasswordHistoryService(db)
    notification_service = NotificationService(db)
    session_manager = SessionManager(db)

    # Validate new password against policy
    validation_result = password_validator.validate_password(
        password=password_data.new_password,
        user=current_user
    )

    if not validation_result["is_valid"]:
        # Audit failed password change
        create_audit_log(
            db=db,
            action="change_password",
            user=current_user,
            entity_type="user",
            entity_id=str(current_user.id),
            request=request,
            status="failure",
            error_message=f"Password validation failed: {', '.join(validation_result['errors'])}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet requirements: {', '.join(validation_result['errors'])}"
        )

    # Check password history
    if not password_history_service.is_password_allowed(current_user, password_data.new_password):
        history_count = security_config.get_config("password_history_count", current_user.tenant_id) or 5
        create_audit_log(
            db=db,
            action="change_password",
            user=current_user,
            entity_type="user",
            entity_id=str(current_user.id),
            request=request,
            status="failure",
            error_message="Password reuse detected"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reuse any of your last {history_count} passwords"
        )

    # Update password
    new_hashed_password = hash_password(password_data.new_password)
    current_user.hashed_password = new_hashed_password
    current_user.password_changed_at = datetime.utcnow()

    # Calculate password expiration
    expiration_days = security_config.get_config("password_expiration_days", current_user.tenant_id)
    if expiration_days and expiration_days > 0:
        current_user.password_expires_at = datetime.utcnow() + timedelta(days=expiration_days)
    else:
        current_user.password_expires_at = None

    # Reset password expiration flags
    current_user.require_password_change = False
    grace_logins = security_config.get_config("password_grace_logins", current_user.tenant_id) or 0
    current_user.grace_logins_remaining = grace_logins

    current_user.updated_at = datetime.utcnow()

    try:
        # Save password to history
        password_history_service.add_password_to_history(current_user, new_hashed_password)

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

        # Queue notification
        try:
            notification_service.queue_notification(
                tenant_id=current_user.tenant_id,
                user_id=str(current_user.id),
                notification_type="password_changed",
                recipient=current_user.email,
                subject="Password Changed",
                message=f"Your password has been successfully changed.",
                template_data={
                    "user_name": current_user.full_name or current_user.email,
                    "change_time": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to queue password change notification for user {current_user.id}: {e}")

        # Terminate other sessions if policy requires it
        terminate_sessions = security_config.get_config("session_terminate_on_password_change", current_user.tenant_id)
        if terminate_sessions:
            try:
                # Get current session JTI from request token
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    token_payload = decode_token(token)
                    current_jti = token_payload.get("jti") if token_payload else None

                    # Revoke all sessions except current one
                    session_manager.revoke_all_user_sessions(
                        user=current_user,
                        except_jti=current_jti,
                        reason="Password changed"
                    )
                    logger.info(f"Revoked all other sessions for user {current_user.id} after password change")
            except Exception as e:
                logger.warning(f"Failed to revoke sessions for user {current_user.id}: {e}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to change password for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

    return {"message": "Password changed successfully"}


@router.post("/reset-password-request")
def reset_password_request(
    reset_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request a password reset token. Sends an email with the reset link.
    This is a public endpoint (no authentication required).
    """
    # Find user by email
    user = db.query(User).filter(User.email == reset_data.email).first()

    # Always return success message to prevent email enumeration
    # But only actually send email if user exists
    if user:
        security_config = SecurityConfigService(db)
        notification_service = NotificationService(db)

        # Check if user account is active
        if not user.is_active:
            logger.warning(f"Password reset requested for inactive user: {user.id}")
            # Still return success to prevent enumeration
            return {"message": "If an account with that email exists, a password reset link has been sent."}

        # Check rate limiting - get max attempts from policy
        max_attempts = security_config.get_config("password_reset_max_attempts", user.tenant_id) or 3
        token_expire_hours = security_config.get_config("password_reset_token_expire_hours", user.tenant_id) or 24

        # Count recent reset attempts (within last hour)
        recent_attempts = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == str(user.id),
            PasswordResetToken.created_at > datetime.utcnow() - timedelta(hours=1),
            PasswordResetToken.is_used == False
        ).count()

        if recent_attempts >= max_attempts:
            logger.warning(f"Too many password reset attempts for user: {user.id}")
            # Still return success to prevent enumeration
            return {"message": "If an account with that email exists, a password reset link has been sent."}

        # Invalidate any existing unused tokens
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == str(user.id),
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).update({"is_used": True})

        # Generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=token_expire_hours)

        # Create reset token record
        token_record = PasswordResetToken(
            user_id=str(user.id),
            token=reset_token,
            expires_at=expires_at,
            ip_address=request.client.host if request.client else None
        )
        db.add(token_record)
        db.commit()

        # Queue notification
        try:
            # In production, this would be a proper reset link
            reset_link = f"https://yourapp.com/reset-password?token={reset_token}"

            notification_service.queue_notification(
                tenant_id=user.tenant_id,
                user_id=str(user.id),
                notification_type="password_reset",
                recipient=user.email,
                subject="Password Reset Request",
                message=f"Click the link to reset your password: {reset_link}",
                template_data={
                    "user_name": user.full_name or user.email,
                    "reset_link": reset_link,
                    "expires_hours": token_expire_hours
                }
            )
            logger.info(f"Password reset email queued for user: {user.id}")
        except Exception as e:
            logger.error(f"Failed to queue password reset notification for user {user.id}: {e}")

        # Audit password reset request
        create_audit_log(
            db=db,
            action="password_reset_request",
            user=user,
            entity_type="user",
            entity_id=str(user.id),
            request=request,
            status="success"
        )

    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password-confirm")
def reset_password_confirm(
    reset_data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset using the token sent via email.
    This is a public endpoint (no authentication required).
    """
    # Find valid reset token
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == reset_data.token,
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Get user
    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify new password matches confirmation
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match"
        )

    # Initialize security services
    security_config = SecurityConfigService(db)
    password_validator = PasswordValidator(db, user.tenant_id)
    password_history_service = PasswordHistoryService(db)
    notification_service = NotificationService(db)
    session_manager = SessionManager(db)

    # Validate new password against policy
    validation_result = password_validator.validate_password(
        password=reset_data.new_password,
        user=user
    )

    if not validation_result["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet requirements: {', '.join(validation_result['errors'])}"
        )

    # Check password history
    if not password_history_service.is_password_allowed(user, reset_data.new_password):
        history_count = security_config.get_config("password_history_count", user.tenant_id) or 5
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reuse any of your last {history_count} passwords"
        )

    # Update password
    new_hashed_password = hash_password(reset_data.new_password)
    user.hashed_password = new_hashed_password
    user.password_changed_at = datetime.utcnow()

    # Calculate password expiration
    expiration_days = security_config.get_config("password_expiration_days", user.tenant_id)
    if expiration_days and expiration_days > 0:
        user.password_expires_at = datetime.utcnow() + timedelta(days=expiration_days)
    else:
        user.password_expires_at = None

    # Reset password expiration flags
    user.require_password_change = False
    grace_logins = security_config.get_config("password_grace_logins", user.tenant_id) or 0
    user.grace_logins_remaining = grace_logins

    user.updated_at = datetime.utcnow()

    # Mark token as used
    token_record.is_used = True
    token_record.used_at = datetime.utcnow()

    try:
        # Save password to history
        password_history_service.add_password_to_history(user, new_hashed_password)

        db.commit()

        # Audit password reset
        create_audit_log(
            db=db,
            action="password_reset_confirm",
            user=user,
            entity_type="user",
            entity_id=str(user.id),
            request=request,
            status="success"
        )

        logger.info(f"User {user.id} successfully reset their password")

        # Queue notification
        try:
            notification_service.queue_notification(
                tenant_id=user.tenant_id,
                user_id=str(user.id),
                notification_type="password_changed",
                recipient=user.email,
                subject="Password Reset Successful",
                message=f"Your password has been successfully reset.",
                template_data={
                    "user_name": user.full_name or user.email,
                    "reset_time": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to queue password reset notification for user {user.id}: {e}")

        # Revoke all user sessions for security
        try:
            session_manager.revoke_all_user_sessions(
                user=user,
                reason="Password reset"
            )
            logger.info(f"Revoked all sessions for user {user.id} after password reset")
        except Exception as e:
            logger.warning(f"Failed to revoke sessions for user {user.id}: {e}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reset password for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

    return {"message": "Password has been reset successfully. You can now log in with your new password."}



@router.get("/me/sessions")
def list_my_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None,
):
    """List current user's active sessions. Story 1.2.3"""
    from app.core.session_manager import SessionManager
    mgr = SessionManager(db)
    sessions = mgr.get_active_sessions(current_user)
    current_jti = None
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            import jwt as pyjwt
            payload = pyjwt.decode(token, options={"verify_signature": False})
            current_jti = payload.get("jti")
    except Exception:
        pass
    return {
        "items": [
            {
                "id": str(s.jti),
                "jti": str(s.jti),
                "device_hint": getattr(s, "device_hint", None) or getattr(s, "user_agent", None),
                "ip_address": getattr(s, "ip_address", None),
                "last_seen": s.last_activity.isoformat() if s.last_activity else None,
                "created_at": s.created_at.isoformat() if hasattr(s, "created_at") and s.created_at else None,
                "is_current": str(s.jti) == current_jti,
            }
            for s in sessions
        ],
        "total": len(sessions),
    }


@router.delete("/me/sessions/{session_jti}")
def terminate_session(
    session_jti: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
):
    """Terminate a specific session. Story 1.2.3"""
    from app.core.session_manager import SessionManager
    from app.core.audit import create_audit_log
    mgr = SessionManager(db)
    from app.models.user_session import UserSession
    session = db.query(UserSession).filter(
        UserSession.jti == session_jti,
        UserSession.user_id == str(current_user.id),
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    success = mgr.revoke_session(session_jti, reason="user_terminated")
    if not success:
        raise HTTPException(status_code=400, detail="Session could not be revoked")
    create_audit_log(db=db, action="session_terminated", user=current_user,
                     entity_type="session", entity_id=session_jti,
                     request=http_request, status="success")
    return {"message": "Session terminated"}


@router.delete("/me/sessions")
def terminate_all_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
):
    """Terminate all sessions except current. Story 1.2.3"""
    from app.core.session_manager import SessionManager
    from app.core.audit import create_audit_log
    current_jti = None
    try:
        token = http_request.headers.get("Authorization", "").replace("Bearer ", "") if http_request else ""
        if token:
            import jwt as pyjwt
            payload = pyjwt.decode(token, options={"verify_signature": False})
            current_jti = payload.get("jti")
    except Exception:
        pass
    mgr = SessionManager(db)
    count = mgr.revoke_all_user_sessions(current_user, except_jti=current_jti)
    create_audit_log(db=db, action="sessions_terminated_all", user=current_user,
                     entity_type="user", entity_id=str(current_user.id),
                     context_info={"count": count},
                     request=http_request, status="success")
    return {"message": f"Terminated {count} sessions", "count": count}


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

    # Mirror revocation into Redis for fast lookup (non-fatal)
    try:
        import os as _os, redis as _redis
        _redis_url = _os.environ.get("REDIS_URL", "")
        if _redis_url:
            _ttl = max(0, int(payload.get("exp", 0)) - int(__import__("time").time()))
            if _ttl > 0:
                _r = _redis.from_url(_redis_url, socket_timeout=1)
                _r.setex(f"blacklist:{jti}", _ttl, "1")
    except Exception:
        pass

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
