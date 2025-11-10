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
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.core.dependencies import get_db, require_permissions
from app.models import (
    SecurityPolicy, AccountLockout, UserSession, LoginAttempt,
    NotificationConfig, NotificationQueue, User
)
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
async def list_security_policies(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permissions(["security_policy:read:all"]))
):
    """
    List all security policies (system default and tenant-specific).

    Requires: security_policy:read:all
    """
    query = select(SecurityPolicy).where(SecurityPolicy.is_active == True).order_by(
        SecurityPolicy.tenant_id.asc().nullsfirst(),
        SecurityPolicy.created_at.desc()
    )
    result = await db.execute(query)
    policies = result.scalars().all()

    return policies


@router.get("/policies/{policy_id}", response_model=SecurityPolicyResponse)
async def get_security_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permissions(["security_policy:read:all"]))
):
    """
    Get a specific security policy by ID.

    Requires: security_policy:read:all
    """
    query = select(SecurityPolicy).where(SecurityPolicy.id == policy_id)
    result = await db.execute(query)
    policy = result.scalars().first()

    if not policy:
        raise HTTPException(status_code=404, detail="Security policy not found")

    return policy


@router.post("/policies", response_model=SecurityPolicyResponse, status_code=201)
async def create_security_policy(
    policy_data: SecurityPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(["security_policy:write:all"]))
):
    """
    Create a new security policy (system default or tenant-specific).

    Requires: security_policy:write:all

    Note: Only one policy per tenant. If tenant_id is NULL, creates system default.
    """
    # Check if policy already exists for this tenant
    query = select(SecurityPolicy).where(
        SecurityPolicy.tenant_id == policy_data.tenant_id,
        SecurityPolicy.is_active == True
    )
    result = await db.execute(query)
    existing = result.scalars().first()

    if existing:
        tenant_str = f"tenant {policy_data.tenant_id}" if policy_data.tenant_id else "system default"
        raise HTTPException(
            status_code=400,
            detail=f"Security policy already exists for {tenant_str}. Use PUT to update."
        )

    policy = SecurityPolicy(
        **policy_data.dict(exclude={'created_by'}),
        created_by=current_user["user_id"]
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)

    return policy


@router.put("/policies/{policy_id}", response_model=SecurityPolicyResponse)
async def update_security_policy(
    policy_id: str,
    policy_data: SecurityPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(["security_policy:write:all"]))
):
    """
    Update an existing security policy.

    Requires: security_policy:write:all
    """
    query = select(SecurityPolicy).where(SecurityPolicy.id == policy_id)
    result = await db.execute(query)
    policy = result.scalars().first()

    if not policy:
        raise HTTPException(status_code=404, detail="Security policy not found")

    # Update fields
    for field, value in policy_data.dict(exclude_unset=True, exclude={'updated_by'}).items():
        setattr(policy, field, value)

    policy.updated_by = current_user["user_id"]
    await db.commit()
    await db.refresh(policy)

    return policy


@router.delete("/policies/{policy_id}", status_code=204)
async def delete_security_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permissions(["security_policy:delete:all"]))
):
    """
    Delete (deactivate) a security policy.

    Requires: security_policy:delete:all

    Note: Cannot delete system default policy (tenant_id = NULL).
    """
    query = select(SecurityPolicy).where(SecurityPolicy.id == policy_id)
    result = await db.execute(query)
    policy = result.scalars().first()

    if not policy:
        raise HTTPException(status_code=404, detail="Security policy not found")

    if policy.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete system default policy. Update it instead."
        )

    policy.is_active = False
    await db.commit()


# ==================== Locked Accounts ====================

@router.get("/locked-accounts", response_model=List[LockedAccountResponse])
async def list_locked_accounts(
    tenant_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permissions(["security:view_locked_accounts:all"]))
):
    """
    List all currently locked accounts.

    Requires: security:view_locked_accounts:all
    """
    now = datetime.now(timezone.utc)

    query = select(User).where(
        and_(
            User.locked_until != None,
            User.locked_until > now
        )
    )

    if tenant_id:
        query = query.where(User.tenant_id == tenant_id)

    query = query.order_by(desc(User.locked_until))

    result = await db.execute(query)
    users = result.scalars().all()

    return [
        {
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "tenant_id": str(user.tenant_id),
            "locked_until": user.locked_until,
            "failed_attempts": user.failed_login_attempts,
            "is_active": user.is_active
        }
        for user in users
    ]


@router.post("/unlock-account", status_code=200)
async def unlock_account(
    unlock_data: UnlockAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(["security:unlock_account:all"]))
):
    """
    Manually unlock a locked user account.

    Requires: security:unlock_account:all
    """
    from app.core.security_config import get_lockout_policy
    from app.core.lockout_manager import LockoutManager

    # Get user
    query = select(User).where(User.id == unlock_data.user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if actually locked
    is_locked, locked_until = await LockoutManager(
        await get_lockout_policy(db, str(user.tenant_id))
    ).is_account_locked(db, user)

    if not is_locked:
        raise HTTPException(status_code=400, detail="Account is not locked")

    # Unlock
    policy = await get_lockout_policy(db, str(user.tenant_id))
    manager = LockoutManager(policy)
    await manager.unlock_account(
        db, user,
        unlocked_by_id=current_user["user_id"],
        reason=unlock_data.reason or "Manual unlock by administrator"
    )

    return {
        "message": "Account unlocked successfully",
        "user_id": str(user.id),
        "email": user.email
    }


# ==================== Active Sessions ====================

@router.get("/sessions", response_model=List[UserSessionResponse])
async def list_active_sessions(
    user_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permissions(["security:view_sessions:all"]))
):
    """
    List active user sessions.

    Requires: security:view_sessions:all
    """
    now = datetime.now(timezone.utc)

    query = select(UserSession).where(
        and_(
            UserSession.revoked_at == None,
            UserSession.expires_at > now
        )
    ).order_by(desc(UserSession.last_activity)).limit(limit)

    if user_id:
        query = query.where(UserSession.user_id == user_id)

    if tenant_id:
        # Join with User to filter by tenant
        query = query.join(User).where(User.tenant_id == tenant_id)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return sessions


@router.post("/sessions/revoke", status_code=200)
async def revoke_session(
    revoke_data: RevokeSessionRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permissions(["security:revoke_session:all"]))
):
    """
    Revoke a user session.

    Requires: security:revoke_session:all
    """
    from app.core.session_manager import SessionManager
    from app.core.security_config import get_session_policy

    # Get session
    query = select(UserSession).where(UserSession.id == revoke_data.session_id)
    result = await db.execute(query)
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Revoke
    policy = await get_session_policy(db, None)  # System default
    manager = SessionManager(policy)
    await manager.revoke_session(db, session.jti)

    return {
        "message": "Session revoked successfully",
        "session_id": str(session.id),
        "user_id": str(session.user_id)
    }


@router.post("/sessions/revoke-all/{user_id}", status_code=200)
async def revoke_all_user_sessions(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permissions(["security:revoke_session:all"]))
):
    """
    Revoke all active sessions for a user.

    Requires: security:revoke_session:all
    """
    from app.core.session_manager import revoke_all_user_sessions as revoke_all
    from app.core.security_config import get_session_policy

    # Verify user exists
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    policy = await get_session_policy(db, str(user.tenant_id))
    count = await revoke_all(db, user_id, policy)

    return {
        "message": f"Revoked {count} active sessions",
        "user_id": user_id,
        "sessions_revoked": count
    }


# ==================== Login Attempts ====================

@router.get("/login-attempts", response_model=List[LoginAttemptResponse])
async def list_login_attempts(
    email: Optional[str] = Query(None),
    success: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permissions(["security:view_login_attempts:all"]))
):
    """
    List login attempts for audit.

    Requires: security:view_login_attempts:all
    """
    query = select(LoginAttempt).order_by(desc(LoginAttempt.created_at)).limit(limit)

    if email:
        query = query.where(LoginAttempt.email == email)

    if success is not None:
        query = query.where(LoginAttempt.success == success)

    result = await db.execute(query)
    attempts = result.scalars().all()

    return attempts


# ==================== Notification Configuration ====================

@router.get("/notification-config", response_model=List[NotificationConfigResponse])
async def list_notification_configs(
    tenant_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permissions(["notification_config:read:all"]))
):
    """
    List notification configurations.

    Requires: notification_config:read:all
    """
    query = select(NotificationConfig).where(NotificationConfig.is_active == True)

    if tenant_id:
        query = query.where(
            or_(
                NotificationConfig.tenant_id == tenant_id,
                NotificationConfig.tenant_id == None
            )
        )

    result = await db.execute(query)
    configs = result.scalars().all()

    return configs


@router.put("/notification-config/{config_id}", response_model=NotificationConfigResponse)
async def update_notification_config(
    config_id: str,
    config_data: NotificationConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(["notification_config:write:all"]))
):
    """
    Update notification configuration.

    Requires: notification_config:write:all
    """
    query = select(NotificationConfig).where(NotificationConfig.id == config_id)
    result = await db.execute(query)
    config = result.scalars().first()

    if not config:
        raise HTTPException(status_code=404, detail="Notification config not found")

    # Update fields
    for field, value in config_data.dict(exclude_unset=True, exclude={'updated_by'}).items():
        setattr(config, field, value)

    config.updated_by = current_user["user_id"]
    await db.commit()
    await db.refresh(config)

    return config


@router.get("/notification-queue", response_model=List[NotificationQueueResponse])
async def list_notification_queue(
    status: Optional[str] = Query(None),
    notification_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permissions(["notification_queue:read:all"]))
):
    """
    List notification queue for monitoring.

    Requires: notification_queue:read:all
    """
    query = select(NotificationQueue).order_by(
        NotificationQueue.priority.asc(),
        NotificationQueue.created_at.asc()
    ).limit(limit)

    if status:
        query = query.where(NotificationQueue.status == status)

    if notification_type:
        query = query.where(NotificationQueue.notification_type == notification_type)

    result = await db.execute(query)
    notifications = result.scalars().all()

    return notifications
