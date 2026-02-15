"""
Module Extension Models

Models for module extension framework (Phase 4 Priority 3):
- ModuleEntityExtension: Entity field extensions
- ModuleScreenExtension: Screen UI extensions (tabs, sections, widgets)
- ModuleMenuExtension: Menu item extensions
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime, UniqueConstraint, CheckConstraint, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, GUID, generate_uuid


class ModuleEntityExtension(Base):
    """
    Module Entity Extensions

    Allows modules to add fields to entities from other modules.

    Example:
    - Payroll module extends HR module's Employee entity
    - Extension table: payroll_hr_employees_ext
    - Adds fields: bank_account, tax_id, monthly_salary, etc.

    The extension table is created dynamically and has a foreign key
    to the base entity table.
    """
    __tablename__ = 'module_entity_extensions'

    # Identity
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Extension source (module adding the extension)
    extending_module_id = Column(
        GUID,
        ForeignKey('modules.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Extension target
    target_module_id = Column(
        GUID,
        ForeignKey('modules.id', ondelete='CASCADE'),
        nullable=False
    )
    target_entity_id = Column(
        GUID,
        ForeignKey('entity_definitions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Extension details
    extension_table = Column(String(100), nullable=False)  # e.g., "payroll_hr_employees_ext"
    extension_fields = Column(JSON, nullable=False, default=list)  # Field definitions

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(GUID, ForeignKey('users.id'))

    # Relationships
    extending_module = relationship(
        "Module",
        foreign_keys=[extending_module_id],
        backref="entity_extensions_created"
    )
    target_module = relationship(
        "Module",
        foreign_keys=[target_module_id],
        backref="entity_extensions_received"
    )
    target_entity = relationship("EntityDefinition", backref="extensions")
    creator = relationship("User", foreign_keys=[created_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            'extending_module_id', 'target_entity_id',
            name='unique_module_entity_extension'
        ),
        Index('idx_entity_extensions_extending', 'extending_module_id'),
        Index('idx_entity_extensions_target', 'target_entity_id'),
    )

    def __repr__(self):
        return f"<ModuleEntityExtension(table='{self.extension_table}', active={self.is_active})>"


class ModuleScreenExtension(Base):
    """
    Module Screen Extensions

    Allows modules to add UI components to screens from other modules.

    Extension Types:
    - tab: Add a tab to a screen (e.g., Payroll tab on Employee detail)
    - section: Add a section within existing tab
    - widget: Add a widget/card to a screen
    - action: Add a button/action to a screen

    Example:
    - Payroll module adds "Payroll Info" tab to HR module's Employee detail screen
    - Benefits module adds "Benefits" tab to same screen
    - Each module can see and edit only its own extension data
    """
    __tablename__ = 'module_screen_extensions'

    # Identity
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Extension source (module adding the extension)
    extending_module_id = Column(
        GUID,
        ForeignKey('modules.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Extension target
    target_module_id = Column(
        GUID,
        ForeignKey('modules.id', ondelete='CASCADE'),
        nullable=False
    )
    target_screen = Column(String(100), nullable=False)  # e.g., "employee_detail"

    # Extension details
    extension_type = Column(
        String(50),
        nullable=False
    )  # tab, section, widget, action
    extension_config = Column(JSON, nullable=False)  # Configuration (label, icon, component, etc.)
    position = Column(Integer, default=999)  # Display order

    # Status
    is_active = Column(Boolean, default=True)

    # Permissions
    required_permission = Column(String(200))  # e.g., "payroll:employee:read"

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(GUID, ForeignKey('users.id'))

    # Relationships
    extending_module = relationship(
        "Module",
        foreign_keys=[extending_module_id],
        backref="screen_extensions_created"
    )
    target_module = relationship(
        "Module",
        foreign_keys=[target_module_id],
        backref="screen_extensions_received"
    )
    creator = relationship("User", foreign_keys=[created_by])

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "extension_type IN ('tab', 'section', 'widget', 'action')",
            name='valid_screen_extension_type'
        ),
        Index('idx_screen_extensions_target', 'target_module_id', 'target_screen'),
        Index('idx_screen_extensions_extending', 'extending_module_id'),
    )

    def __repr__(self):
        return f"<ModuleScreenExtension(type='{self.extension_type}', screen='{self.target_screen}')>"


class ModuleMenuExtension(Base):
    """
    Module Menu Extensions

    Allows modules to add menu items to other modules' menus or to root menu.

    Example:
    - Payroll module adds "Payroll" submenu under HR Management menu
    - Benefits module adds "Benefits" submenu under HR Management menu
    - Each extension can have multiple child menu items

    Menu Structure:
    {
      "type": "submenu",
      "label": "Payroll",
      "icon": "money",
      "items": [
        {
          "label": "Payroll Runs",
          "route": "payroll/runs",
          "icon": "calendar",
          "permission": "payroll:runs:read"
        },
        ...
      ]
    }
    """
    __tablename__ = 'module_menu_extensions'

    # Identity
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Extension source (module adding the extension)
    extending_module_id = Column(
        GUID,
        ForeignKey('modules.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Extension target (NULL = add to root menu)
    target_module_id = Column(
        GUID,
        ForeignKey('modules.id', ondelete='CASCADE')
    )
    target_menu_item = Column(String(100))  # Parent menu item (e.g., "hr_management")

    # Menu item details
    menu_config = Column(JSON, nullable=False)  # Menu configuration
    position = Column(Integer, default=999)  # Display order

    # Status
    is_active = Column(Boolean, default=True)

    # Permissions
    required_permission = Column(String(200))  # Required to see this menu item

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(GUID, ForeignKey('users.id'))

    # Relationships
    extending_module = relationship(
        "Module",
        foreign_keys=[extending_module_id],
        backref="menu_extensions_created"
    )
    target_module = relationship(
        "Module",
        foreign_keys=[target_module_id],
        backref="menu_extensions_received"
    )
    creator = relationship("User", foreign_keys=[created_by])

    # Constraints
    __table_args__ = (
        Index('idx_menu_extensions_target', 'target_module_id'),
        Index('idx_menu_extensions_extending', 'extending_module_id'),
    )

    def __repr__(self):
        target = self.target_menu_item or 'root'
        return f"<ModuleMenuExtension(target='{target}', active={self.is_active})>"
