from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class LoginAttempt(Base):
    """
    Tracks all login attempts (successful and failed) for security audit.
    Used for detecting brute force attacks and enforcing account lockout policies.
    """
    __tablename__ = "login_attempts"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # User reference (nullable for failed attempts with non-existent emails)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    # Login details
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)

    # Result
    success = Column(Boolean, nullable=False, index=True)
    failure_reason = Column(String(255), nullable=True)  # e.g., "invalid_password", "account_locked", "user_not_found"

    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="login_attempts")

    def __repr__(self):
        return f"<LoginAttempt(id={self.id}, email={self.email}, success={self.success}, created_at={self.created_at})>"
