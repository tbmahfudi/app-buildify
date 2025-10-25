from sqlalchemy import Column, String, Text, DateTime, func, UniqueConstraint
from .base import Base, GUID, generate_uuid


class UserSettings(Base):
    """User-specific settings and preferences"""
    __tablename__ = "user_settings"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Foreign key
    user_id = Column(GUID, nullable=False, index=True)

    # Settings (JSON)
    theme = Column(String(20), default="light")  # light, dark
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    density = Column(String(20), default="normal")  # compact, normal, comfortable

    # Preferences (JSON)
    preferences = Column(Text, nullable=True)  # JSON: custom preferences

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', name='uq_user_settings'),
    )

    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, theme={self.theme})>"


class TenantSettings(Base):
    """Tenant-wide settings"""
    __tablename__ = "tenant_settings"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Foreign key
    tenant_id = Column(GUID, nullable=False, unique=True, index=True)

    # Branding
    tenant_name = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=True)  # Hex color
    secondary_color = Column(String(7), nullable=True)

    # Theme (JSON)
    theme_config = Column(Text, nullable=True)  # JSON: CSS variables

    # Features (JSON)
    enabled_features = Column(Text, nullable=True)  # JSON: feature flags

    # Settings (JSON)
    settings = Column(Text, nullable=True)  # JSON: misc settings

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(GUID, nullable=True)

    def __repr__(self):
        return f"<TenantSettings(tenant_id={self.tenant_id}, tenant_name={self.tenant_name})>"
