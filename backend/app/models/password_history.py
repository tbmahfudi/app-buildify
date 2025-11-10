from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, GUID, generate_uuid


class PasswordHistory(Base):
    """
    Password history for preventing password reuse.
    Stores hashed passwords to enforce password history policies.
    """
    __tablename__ = "password_history"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # User reference
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Password hash (same format as users.hashed_password)
    hashed_password = Column(String(255), nullable=False)

    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="password_history")

    def __repr__(self):
        return f"<PasswordHistory(id={self.id}, user_id={self.user_id}, created_at={self.created_at})>"
