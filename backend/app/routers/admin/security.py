"""
Security Administration Endpoints

Provides endpoints for managing:
- Security policies (password, lockout, session policies)
- Locked accounts (view and unlock)
- Active sessions (view and revoke)
- Login attempts audit
- Notification configuration
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, has_permission, get_current_user
from app.models.security_policy import SecurityPolicy
from app.models.account_lockout import AccountLockout
from app.models.user_session import UserSession
from app.models.login_attempt import LoginAttempt
from app.models.notification_config import NotificationConfig
from app.models.notification_queue import NotificationQueue
from app.models.user import User
from app.schemas.security import (
    SecurityPolicyResponse, SecurityPolicyCreate, SecurityPolicyUpdate,
    LockedAccountResponse, UnlockAccountRequest,
    UserSessionResponse, RevokeSessionRequest,
    LoginAttemptResponse,
    NotificationConfigResponse, NotificationConfigUpdate,
    NotificationQueueResponse
)

router = APIRouter(prefix="/admin/security", tags=["admin", "security"])


# ==================== Security Policies ====================

@router.get("/policies", response_model=List[SecurityPolicyResponse])
def list_security_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("security_policy:read:all"))
):
    """
    List all security policies (system default and tenant-specific).

    Requires: security_policy:read:all
    """
    policies = db.query(SecurityPolicy).filter(
        SecurityPolicy.is_active == True
    ).order_by(
        SecurityPolicy.tenant_id.asc(),
        SecurityPolicy.created_at.desc()
    ).all()

    return policies


@router.get("/policies/{policy_id}", response_model=SecurityPolicyResponse)
def get_security_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("security_policy:read:all"))
):
    """
    Get a specific security policy by ID.

    Requires: security_policy:read:all
    """
    policy = db.query(SecurityPolicy).filter(SecurityPolicy.id == policy_id).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Security policy not found")

    return policy


@router.post("/policies", response_model=SecurityPolicyResponse, status_code=201)
def create_security_policy(
    policy_data: SecurityPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("security_policy:write:all"))
):
    """
    Create a new security policy (system default or tenant-specific).

    Requires: security_policy:write:all

    Note: Only one policy per tenant. If tenant_id is NULL, creates system default.
    """
    # Check if policy already exists for this tenant
    existing = db.query(SecurityPolicy).filter(
        SecurityPolicy.tenant_id == policy_data.tenant_id,
        SecurityPolicy.is_active == True
    ).first()

    if existing:
        tenant_str = f"tenant {policy_data.tenant_id}" if policy_data.tenant_id else "system default"
        raise HTTPException(
            status_code=400,
            detail=f"Security policy already exists for {tenant_str}. Use PUT to update."
        )

    policy = SecurityPolicy(
        **policy_data.dict(exclude={'created_by'}),
        created_by=str(current_user.id)
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    return policy


@router.put("/policies/{policy_id}", response_model=SecurityPolicyResponse)
def update_security_policy(
    policy_id: str,
    policy_data: SecurityPolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("security_policy:write:all"))
):
    """
    Update an existing security policy.

    Requires: security_policy:write:all
    """
    policy = db.query(SecurityPolicy).filter(SecurityPolicy.id == policy_id).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Security policy not found")

    # Update fields
    for field, value in policy_data.dict(exclude_unset=True, exclude={'updated_by'}).items():
        setattr(policy, field, value)

    policy.updated_by = str(current_user.id)
    db.commit()
    db.refresh(policy)

    return policy


@router.delete("/policies/{policy_id}", status_code=204)
def delete_security_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("security_policy:delete:all"))
):
    """
    Delete (deactivate) a security policy.

    Requires: security_policy:delete:all

    Note: Cannot delete system default policy (tenant_id = NULL).
    """
    policy = db.query(SecurityPolicy).filter(SecurityPolicy.id == policy_id).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Security policy not found")

    if policy.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete system default policy. Update it instead."
        )

    policy.is_active = False
    db.commit()


# ==================== Locked Accounts ====================

@router.get("/locked-accounts", response_model=List[LockedAccountResponse])
def list_locked_accounts(
    tenant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("security:view_locked_accounts:all"))
):
    """
    List all currently locked accounts.

    Requires: security:view_locked_accounts:all
    """
    now = datetime.utcnow()

    query = db.query(User).filter(
        User.locked_until != None,
        User.locked_until > now
    )

    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)

    users = query.order_by(User.locked_until.desc()).all()

    return [
        LockedAccountResponse(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            locked_until=user.locked_until,
            failed_attempts=user.failed_login_attempts or 0,
            is_active=user.is_active
        )
        for user in users
    ]


@router.post("/unlock-account", status_code=200)
def unlock_account(
    unlock_data: UnlockAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("security:unlock_account:all"))
):
    """
    Manually unlock a locked user account.

    Requires: security:unlock_account:all
    """
    from app.core.lockout_manager import LockoutManager

    # Get user
    user = db.query(User).filter(User.id == unlock_data.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if actually locked
    lockout_manager = LockoutManager(db)
    if not lockout_manager.is_account_locked(user):
        raise HTTPException(status_code=400, detail="Account is not locked")

    # Unlock
    lockout_manager.unlock_account(
        user=user,
        unlocked_by_id=str(current_user.id),
        reason=unlock_data.reason or "Manual unlock by administrator"
    )

    return {
        "message": "Account unlocked successfully",
        "user_id": str(user.id),
        "email": user.email
    }


# ==================== Active Sessions ====================

@router.get("/sessions", response_model=List[UserSessionResponse])
def list_active_sessions(
    user_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("security:view_sessions:all"))
):
    """
    List active user sessions.

    Requires: security:view_sessions:all
    """
    now = datetime.utcnow()

    query = db.query(UserSession).filter(
        UserSession.revoked_at == None,
        UserSession.expires_at > now
    ).order_by(UserSession.last_activity.desc()).limit(limit)

    if user_id:
        query = query.filter(UserSession.user_id == user_id)

    if tenant_id:
        # Join with User to filter by tenant
        query = query.join(User).filter(User.tenant_id == tenant_id)

    sessions = query.all()

    return sessions


@router.post("/sessions/revoke", status_code=200)
def revoke_session(
    revoke_data: RevokeSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("security:revoke_session:all"))
):
    """
    Revoke a user session.

    Requires: security:revoke_session:all
    """
    from app.core.session_manager import SessionManager

    # Get session
    session = db.query(UserSession).filter(UserSession.id == revoke_data.session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Revoke
    session_manager = SessionManager(db)
    session_manager.revoke_session(session.jti, reason="Admin revocation")

    return {
        "message": "Session revoked successfully",
        "session_id": str(session.id),
        "user_id": str(session.user_id)
    }


@router.post("/sessions/revoke-all/{user_id}", status_code=200)
def revoke_all_user_sessions(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("security:revoke_session:all"))
):
    """
    Revoke all active sessions for a user.

    Requires: security:revoke_session:all
    """
    from app.core.session_manager import SessionManager

    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session_manager = SessionManager(db)
    count = session_manager.revoke_all_user_sessions(user=user, reason="Admin bulk revocation")

    return {
        "message": f"Revoked {count} active sessions",
        "user_id": user_id,
        "sessions_revoked": count
    }


# ==================== Login Attempts ====================

@router.get("/login-attempts", response_model=List[LoginAttemptResponse])
def list_login_attempts(
    email: Optional[str] = Query(None),
    success: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("security:view_login_attempts:all"))
):
    """
    List login attempts for audit.

    Requires: security:view_login_attempts:all
    """
    query = db.query(LoginAttempt).order_by(LoginAttempt.created_at.desc()).limit(limit)

    if email:
        query = query.filter(LoginAttempt.email == email)

    if success is not None:
        query = query.filter(LoginAttempt.success == success)

    attempts = query.all()

    return attempts


# ==================== Notification Configuration ====================

@router.get("/notification-config", response_model=List[NotificationConfigResponse])
def list_notification_configs(
    tenant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("notification_config:read:all"))
):
    """
    List notification configurations.

    Requires: notification_config:read:all
    """
    query = db.query(NotificationConfig).filter(NotificationConfig.is_active == True)

    if tenant_id:
        query = query.filter(
            (NotificationConfig.tenant_id == tenant_id) | (NotificationConfig.tenant_id == None)
        )

    configs = query.all()

    return configs


@router.put("/notification-config/{config_id}", response_model=NotificationConfigResponse)
def update_notification_config(
    config_id: str,
    config_data: NotificationConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("notification_config:write:all"))
):
    """
    Update notification configuration.

    Requires: notification_config:write:all
    """
    config = db.query(NotificationConfig).filter(NotificationConfig.id == config_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Notification config not found")

    # Update fields
    for field, value in config_data.dict(exclude_unset=True, exclude={'updated_by'}).items():
        setattr(config, field, value)

    config.updated_by = str(current_user.id)
    db.commit()
    db.refresh(config)

    return config


@router.get("/notification-queue", response_model=List[NotificationQueueResponse])
def list_notification_queue(
    status: Optional[str] = Query(None),
    notification_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("notification_queue:read:all"))
):
    """
    List notification queue for monitoring.

    Requires: notification_queue:read:all
    """
    query = db.query(NotificationQueue).order_by(
        NotificationQueue.priority.asc(),
        NotificationQueue.created_at.asc()
    ).limit(limit)

    if status:
        query = query.filter(NotificationQueue.status == status)

    if notification_type:
        query = query.filter(NotificationQueue.notification_type == notification_type)

    notifications = query.all()

    return notifications
