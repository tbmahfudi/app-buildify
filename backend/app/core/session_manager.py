"""
Session Manager

Manages user sessions with support for:
- Session tracking
- Concurrent session limits
- Session termination on password change
- Activity tracking
"""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import ACCESS_TOKEN_EXPIRE_MIN
from app.core.security_config import SecurityConfigService
from app.models.user import User
from app.models.user_session import UserSession


class SessionManager:
    """Manages user session lifecycle and enforcement"""

    def __init__(self, db: Session):
        """
        Initialize session manager with database session.

        Args:
            db: Database session
        """
        self.db = db
        self.security_config = SecurityConfigService(db)

    def create_session(
        self,
        user: User,
        jti: str,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """
        Create a new user session.

        Args:
            user: User instance
            jti: JWT ID from access token
            device_id: Optional device fingerprint
            device_name: Optional device name
            ip_address: IP address
            user_agent: User agent string

        Returns:
            UserSession instance
        """
        # Calculate expiration based on policy
        timeout_minutes = self.security_config.get_config("session_timeout_minutes", user.tenant_id) or ACCESS_TOKEN_EXPIRE_MIN
        absolute_timeout_hours = self.security_config.get_config("session_absolute_timeout_hours", user.tenant_id) or 24

        # Use the shorter of the two timeouts
        timeout_delta = min(
            timedelta(minutes=timeout_minutes),
            timedelta(hours=absolute_timeout_hours)
        )
        expires_at = datetime.utcnow() + timeout_delta

        session = UserSession(
            user_id=str(user.id),
            jti=jti,
            expires_at=expires_at,
            device_id=device_id,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # Enforce concurrent session limit
        self.enforce_concurrent_limit(user)

        return session

    def get_active_sessions(self, user: User) -> List[UserSession]:
        """
        Get all active sessions for a user.

        Args:
            user: User instance

        Returns:
            List of active UserSession instances
        """
        now = datetime.utcnow()

        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == str(user.id),
            UserSession.revoked_at == None,
            UserSession.expires_at > now
        ).order_by(UserSession.last_activity.desc()).all()

        return sessions

    def count_active_sessions(self, user: User) -> int:
        """
        Count active sessions for a user.

        Args:
            user: User instance

        Returns:
            Number of active sessions
        """
        return len(self.get_active_sessions(user))

    def enforce_concurrent_limit(self, user: User) -> int:
        """
        Enforce concurrent session limit by revoking oldest sessions.

        Args:
            user: User instance

        Returns:
            Number of sessions revoked
        """
        max_concurrent = self.security_config.get_config("session_max_concurrent", user.tenant_id) or 0

        if max_concurrent == 0:
            return 0  # Unlimited sessions

        sessions = self.get_active_sessions(user)

        if len(sessions) > max_concurrent:
            # Revoke oldest sessions (keep the most recent max_concurrent)
            to_revoke = sessions[max_concurrent:]
            revoked_count = 0

            for session in to_revoke:
                session.revoked_at = datetime.utcnow()
                revoked_count += 1

            self.db.commit()
            return revoked_count

        return 0

    def revoke_session(self, jti: str, reason: Optional[str] = None) -> bool:
        """
        Revoke a specific session by JWT ID.

        Args:
            jti: JWT ID to revoke
            reason: Optional reason for revocation

        Returns:
            True if session was found and revoked
        """
        session = self.db.query(UserSession).filter(UserSession.jti == jti).first()

        if session:
            session.revoked_at = datetime.utcnow()
            self.db.commit()
            return True

        return False

    def revoke_all_user_sessions(
        self,
        user: User,
        except_jti: Optional[str] = None,
        reason: Optional[str] = None
    ) -> int:
        """
        Revoke all active sessions for a user.

        Args:
            user: User instance
            except_jti: Optional JTI to exclude from revocation (current session)
            reason: Optional reason for revocation

        Returns:
            Number of sessions revoked
        """
        now = datetime.utcnow()

        query = self.db.query(UserSession).filter(
            UserSession.user_id == str(user.id),
            UserSession.revoked_at == None,
            UserSession.expires_at > now
        )

        if except_jti:
            query = query.filter(UserSession.jti != except_jti)

        sessions = query.all()

        revoked_count = 0
        for session in sessions:
            session.revoked_at = now
            revoked_count += 1

        self.db.commit()
        return revoked_count

    def update_activity(self, jti: str) -> bool:
        """
        Update last activity timestamp for a session.

        Args:
            jti: JWT ID

        Returns:
            True if session was found and updated
        """
        session = self.db.query(UserSession).filter(UserSession.jti == jti).first()

        if session:
            session.last_activity = datetime.utcnow()
            self.db.commit()
            return True

        return False

    def cleanup_expired_sessions(self, older_than_hours: int = 24) -> int:
        """
        Delete expired sessions older than specified hours.

        Args:
            older_than_hours: Delete sessions expired this many hours ago

        Returns:
            Number of sessions deleted
        """
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)

        count = self.db.query(UserSession).filter(
            UserSession.expires_at < cutoff
        ).delete()

        self.db.commit()
        return count

    def get_session_by_jti(self, jti: str) -> Optional[UserSession]:
        """
        Get session by JWT ID.

        Args:
            jti: JWT ID

        Returns:
            UserSession if found, None otherwise
        """
        return self.db.query(UserSession).filter(UserSession.jti == jti).first()

    def is_session_valid(self, jti: str) -> bool:
        """
        Check if a session is valid (exists, not revoked, not expired).

        Args:
            jti: JWT ID

        Returns:
            True if session is valid
        """
        session = self.get_session_by_jti(jti)

        if not session:
            return False

        if session.revoked_at:
            return False

        if session.expires_at < datetime.utcnow():
            return False

        return True
