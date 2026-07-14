from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint, func

from .base import GUID, Base, generate_uuid


class UserMFAFactor(Base):
    """A second factor a user can enroll (ADR-011).

    MFA is optional: phone or email OTP now; ``factor_type`` is left open (a short
    string, not an enum) so an authenticator-app (TOTP) factor can be added later
    without a schema change. No credential/secret is stored here — only the
    delivery target and verification state; OTP codes stay in the OTP service.
    """

    __tablename__ = "user_mfa_factors"
    __tenant_scoped__ = False  # keyed on the platform user, not a tenant

    id = Column(GUID, primary_key=True, default=generate_uuid)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 'phone_otp' | 'email_otp' (TOTP reserved for a later factor type).
    factor_type = Column(String(20), nullable=False)
    # Delivery target for the factor: a phone number or an email address.
    target = Column(String(255), nullable=False)

    is_active = Column(Boolean, nullable=False, default=False)
    verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "factor_type", "target", name="uq_user_mfa_factor"),)

    def __repr__(self):
        return f"<UserMFAFactor id={self.id} user={self.user_id} type={self.factor_type} active={self.is_active}>"
