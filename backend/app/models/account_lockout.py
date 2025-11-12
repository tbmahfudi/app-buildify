from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class AccountLockout(Base):
    """
    Tracks account lockouts due to failed login attempts.
    Supports both automatic and manual lockouts/unlocks.
    """
    __tablename__ = "account_lockouts"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # User reference
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Lockout details
    locked_at = Column(DateTime, server_default=func.now(), nullable=False)
    locked_until = Column(DateTime, nullable=False, index=True)
    lockout_reason = Column(String(255), nullable=True)
    attempt_count = Column(Integer, nullable=False)  # Number of failed attempts that triggered lockout

    # Unlock details (for manual unlocks by admins)
    unlocked_at = Column(DateTime, nullable=True)
    unlocked_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Admin who unlocked
    unlock_reason = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="lockouts", foreign_keys=[user_id])
    unlocked_by_user = relationship("User", foreign_keys=[unlocked_by])

    def __repr__(self):
        return f"<AccountLockout(id={self.id}, user_id={self.user_id}, locked_until={self.locked_until})>"

    @property
    def is_active(self) -> bool:
        """Check if lockout is still active."""
        from datetime import datetime, timezone
        if self.unlocked_at:
            return False  # Manually unlocked
        return datetime.now(timezone.utc) < self.locked_until
