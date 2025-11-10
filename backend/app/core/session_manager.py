"""
Session Manager

Manages user sessions with support for:
- Session tracking
- Concurrent session limits
- Session termination on password change
- Activity tracking
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete

from app.models import UserSession, User
from app.core.security_config import SessionSecurityConfig


class SessionManager:
    """Manages user session lifecycle and enforcement"""

    def __init__(self, policy: SessionSecurityConfig):
        self.policy = policy

    async def create_session(
        self,
        db: AsyncSession,
        user_id: str,
        jti: str,
        expires_at: datetime,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """
        Create a new user session.

        Args:
            db: Database session
            user_id: User ID
            jti: JWT ID from access token
            expires_at: Session expiration time
            device_id: Optional device fingerprint
            device_name: Optional device name
            ip_address: IP address
            user_agent: User agent string

        Returns:
            UserSession instance
        """
        session = UserSession(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
            device_id=device_id,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Enforce concurrent session limit
        await self.enforce_concurrent_limit(db, user_id)

        return session

    async def get_active_sessions(
        self,
        db: AsyncSession,
        user_id: str
    ) -> List[UserSession]:
        """
        Get all active sessions for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of active UserSession instances
        """
        now = datetime.now(timezone.utc)

        query = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.revoked_at == None,
                UserSession.expires_at > now
            )
        ).order_by(UserSession.last_activity.desc())

        result = await db.execute(query)
        return result.scalars().all()

    async def count_active_sessions(
        self,
        db: AsyncSession,
        user_id: str
    ) -> int:
        """
        Count active sessions for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Number of active sessions
        """
        sessions = await self.get_active_sessions(db, user_id)
        return len(sessions)

    async def enforce_concurrent_limit(
        self,
        db: AsyncSession,
        user_id: str
    ) -> int:
        """
        Enforce concurrent session limit by revoking oldest sessions.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Number of sessions revoked
        """
        if self.policy.max_concurrent == 0:
            return 0  # Unlimited sessions

        sessions = await self.get_active_sessions(db, user_id)

        if len(sessions) > self.policy.max_concurrent:
            # Revoke oldest sessions (keep the most recent max_concurrent)
            to_revoke = sessions[self.policy.max_concurrent:]
            revoked_count = 0

            for session in to_revoke:
                session.revoked_at = datetime.now(timezone.utc)
                revoked_count += 1

            await db.commit()
            return revoked_count

        return 0

    async def revoke_session(
        self,
        db: AsyncSession,
        jti: str
    ) -> bool:
        """
        Revoke a specific session by JWT ID.

        Args:
            db: Database session
            jti: JWT ID to revoke

        Returns:
            True if session was found and revoked
        """
        query = select(UserSession).where(UserSession.jti == jti)
        result = await db.execute(query)
        session = result.scalars().first()

        if session:
            session.revoked_at = datetime.now(timezone.utc)
            await db.commit()
            return True

        return False

    async def revoke_all_sessions(
        self,
        db: AsyncSession,
        user_id: str,
        except_jti: Optional[str] = None
    ) -> int:
        """
        Revoke all active sessions for a user.

        Args:
            db: Database session
            user_id: User ID
            except_jti: Optional JTI to exclude from revocation (current session)

        Returns:
            Number of sessions revoked
        """
        now = datetime.now(timezone.utc)

        query = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.revoked_at == None,
                UserSession.expires_at > now
            )
        )

        if except_jti:
            query = query.where(UserSession.jti != except_jti)

        result = await db.execute(query)
        sessions = result.scalars().all()

        revoked_count = 0
        for session in sessions:
            session.revoked_at = now
            revoked_count += 1

        await db.commit()
        return revoked_count

    async def update_activity(
        self,
        db: AsyncSession,
        jti: str
    ) -> bool:
        """
        Update last activity timestamp for a session.

        Args:
            db: Database session
            jti: JWT ID

        Returns:
            True if session was found and updated
        """
        query = select(UserSession).where(UserSession.jti == jti)
        result = await db.execute(query)
        session = result.scalars().first()

        if session:
            session.last_activity = datetime.now(timezone.utc)
            await db.commit()
            return True

        return False

    async def cleanup_expired_sessions(
        self,
        db: AsyncSession,
        older_than_hours: int = 24
    ) -> int:
        """
        Delete expired sessions older than specified hours.

        Args:
            db: Database session
            older_than_hours: Delete sessions expired this many hours ago

        Returns:
            Number of sessions deleted
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)

        result = await db.execute(
            delete(UserSession).where(UserSession.expires_at < cutoff)
        )
        await db.commit()
        return result.rowcount

    async def get_session_by_jti(
        self,
        db: AsyncSession,
        jti: str
    ) -> Optional[UserSession]:
        """
        Get session by JWT ID.

        Args:
            db: Database session
            jti: JWT ID

        Returns:
            UserSession if found, None otherwise
        """
        query = select(UserSession).where(UserSession.jti == jti)
        result = await db.execute(query)
        return result.scalars().first()

    async def is_session_valid(
        self,
        db: AsyncSession,
        jti: str
    ) -> bool:
        """
        Check if a session is valid (exists, not revoked, not expired).

        Args:
            db: Database session
            jti: JWT ID

        Returns:
            True if session is valid
        """
        session = await self.get_session_by_jti(db, jti)

        if not session:
            return False

        if session.revoked_at:
            return False

        if session.expires_at < datetime.now(timezone.utc):
            return False

        return True


async def revoke_all_user_sessions(
    db: AsyncSession,
    user_id: str,
    policy: SessionSecurityConfig,
    except_jti: Optional[str] = None
) -> int:
    """
    Convenience function to revoke all sessions for a user.
    Used when password is changed and policy requires session termination.

    Args:
        db: Database session
        user_id: User ID
        policy: Session security policy
        except_jti: Optional current session to preserve

    Returns:
        Number of sessions revoked
    """
    manager = SessionManager(policy)
    return await manager.revoke_all_sessions(db, user_id, except_jti)
