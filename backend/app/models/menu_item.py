from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class MenuItem(Base):
    """
    MenuItem entity - represents a menu item in the application navigation.

    Menu items can be:
    - System-wide (tenant_id=NULL) - visible to all tenants
    - Tenant-specific (tenant_id=UUID) - custom menu items for a tenant
    - Module-based (module_code set) - provided by installed modules

    RBAC is enforced via permission and required_roles fields.
    """
    __tablename__ = "menu_items"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Unique identifier
    code = Column(String(100), unique=True, nullable=False, index=True)

    # Multi-tenancy
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True, index=True)
    # NULL = system menu (all tenants)
    # UUID = tenant-specific menu

    # Hierarchical structure
    parent_id = Column(GUID, ForeignKey("menu_items.id"), nullable=True, index=True)
    order = Column(Integer, default=0, nullable=False, index=True)

    # Display properties
    title = Column(String(100), nullable=False)
    icon = Column(String(100), nullable=True)  # Icon class (e.g., "ph-duotone ph-gauge") or emoji
    route = Column(String(255), nullable=True)  # Frontend route (e.g., "dashboard", "financial/accounts")
    description = Column(Text, nullable=True)

    # RBAC Control
    permission = Column(String(200), nullable=True, index=True)  # e.g., "financial:accounts:read:company"
    required_roles = Column(JSONB, nullable=True)  # Array of role codes: ["admin", "manager"]

    # Behavior
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_visible = Column(Boolean, default=True, nullable=False, index=True)
    target = Column(String(50), default="_self", nullable=False)  # _self, _blank, modal

    # Module Integration
    module_code = Column(String(100), nullable=True, index=True)  # e.g., "financial", "inventory"
    is_system = Column(Boolean, default=True, nullable=False)  # System vs custom menu

    # Extensible metadata (renamed to avoid DB keyword conflicts)
    extra_data = Column(JSONB, nullable=True)  # Additional properties (badges, notifications, etc.)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", backref="custom_menu_items")
    parent = relationship("MenuItem", remote_side=[id], backref="children")

    # Composite indexes for performance
    __table_args__ = (
        Index('ix_menu_tenant_active', 'tenant_id', 'is_active', 'is_visible'),
        Index('ix_menu_parent_order', 'parent_id', 'order'),
        Index('ix_menu_module', 'module_code'),
    )

    def __repr__(self):
        return f"<MenuItem(code={self.code}, title={self.title}, route={self.route})>"

    def to_dict(self, include_children=False):
        """Convert menu item to dictionary."""
        result = {
            'id': str(self.id),
            'code': self.code,
            'title': self.title,
            'icon': self.icon,
            'route': self.route,
            'order': self.order,
            'target': self.target,
            'permission': self.permission,
            'required_roles': self.required_roles,
            'extra_data': self.extra_data,
        }

        if include_children:
            result['children'] = []

        return result
