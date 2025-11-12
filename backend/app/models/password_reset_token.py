from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class PasswordResetToken(Base):
    """
    Secure password reset tokens with expiration.
    Tokens are hashed before storage for security.
    """
    __tablename__ = "password_reset_tokens"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # User reference
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Token (hashed)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)

    # Expiration
    expires_at = Column(DateTime, nullable=False, index=True)

    # Usage tracking
    used_at = Column(DateTime, nullable=True)

    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)

    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="reset_tokens")

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at}, used={self.used_at is not None})>"

    @property
    def is_valid(self) -> bool:
        """Check if token is still valid."""
        from datetime import datetime, timezone
        if self.used_at is not None:
            return False  # Already used
        return datetime.now(timezone.utc) < self.expires_at

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= self.expires_at
