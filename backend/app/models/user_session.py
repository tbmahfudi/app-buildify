from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class UserSession(Base):
    """
    Tracks active user sessions for concurrent session management.
    Each session corresponds to a JWT access token.
    """
    __tablename__ = "user_sessions"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # User reference
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # JWT details
    jti = Column(String(255), nullable=False, unique=True, index=True)  # JWT ID from token

    # Device details
    device_id = Column(String(255), nullable=True)  # Browser fingerprint or device ID
    device_name = Column(String(255), nullable=True)  # e.g., "Chrome on Windows", "iPhone 12"
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)

    # Activity tracking
    last_activity = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    # Revocation
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, jti={self.jti}, expires_at={self.expires_at})>"

    @property
    def is_active(self) -> bool:
        """Check if session is still active."""
        from datetime import datetime, timezone
        if self.revoked_at:
            return False
        return datetime.now(timezone.utc) < self.expires_at

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= self.expires_at
