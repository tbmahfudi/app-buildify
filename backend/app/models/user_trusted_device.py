from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint, func

from .base import GUID, Base, generate_uuid


class UserTrustedDevice(Base):
    """A browser the user has told us to remember, so MFA can be skipped on it (ADR-HC-009 D4).

    Only the *HMAC* of the device secret is stored. The raw secret lives solely in a
    signed HttpOnly cookie on the browser, so a database leak alone cannot be replayed
    into a trusted device — an attacker would still need the cookie.

    A row is honoured only while ``revoked_at IS NULL AND expires_at > now()``.
    """

    __tablename__ = "user_trusted_devices"
    __tenant_scoped__ = False  # keyed on the platform user, not a tenant

    id = Column(GUID, primary_key=True, default=generate_uuid)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # HMAC-SHA256 of the device secret. Never the secret itself.
    device_hash = Column(String(255), nullable=False)
    # Best-effort UA hint so the security screen can say "Chrome on Windows".
    label = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "device_hash", name="uq_user_trusted_devices_hash"),)

    def __repr__(self):
        return f"<UserTrustedDevice id={self.id} user={self.user_id} expires={self.expires_at}>"

    @property
    def is_live(self) -> bool:
        """True while this trust may still suppress an MFA challenge."""
        from datetime import datetime

        if self.revoked_at is not None:
            return False
        return datetime.utcnow() < self.expires_at
