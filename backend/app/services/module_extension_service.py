"""
Module Extension Service

Service layer for managing module extensions (Phase 4 Priority 3):
- Entity extensions: Add fields to entities from other modules
- Screen extensions: Add UI components to screens from other modules
- Menu extensions: Add menu items to other modules' menus
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import re

from app.core.logging_config import get_logger
from app.models.module_extension import (
    ModuleEntityExtension,
    ModuleScreenExtension,
    ModuleMenuExtension
)
from app.models.nocode_module import NocodeModule
from app.models.data_model import EntityDefinition


logger = get_logger(__name__)


class ModuleExtensionService:
    """
    Service for managing module extensions.

    Handles creation and management of:
    - Entity field extensions
    - Screen UI extensions
    - Menu item extensions
    """

    def __init__(self, db: Session, current_user):
        """
        Initialize service.

        Args:
            db: Database session
            current_user: Current user for permission checking and audit
        """
        self.db = db
        self.current_user = current_user

    # ===== Entity Extensions =====

    def create_entity_extension(
        self,
        extending_module_id: str,
        target_entity_id: str,
        extension_fields: List[dict]
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Create entity extension.

        Allows extending_module to add custom fields to target_entity.

        Args:
            extending_module_id: Module creating the extension
            target_entity_id: Entity being extended
            extension_fields: List of field definitions to add

        Returns:
            Tuple of (success, message, extension_data)

        Example:
            create_entity_extension(
                extending_module_id="payroll_module_id",
                target_entity_id="hr_employees_entity_id",
                extension_fields=[
                    {
                        "name": "bank_account",
                        "type": "string",
                        "max_length": 50,
                        "label": "Bank Account Number"
                    },
                    {
                        "name": "monthly_salary",
                        "type": "decimal",
                        "precision": 12,
                        "scale": 2,
                        "label": "Monthly Salary"
                    }
                ]
            )
        """
        # Get extending module
        extending_module = self.db.query(NocodeModule).filter(
            NocodeModule.id == extending_module_id
        ).first()

        if not extending_module:
            return False, "Extending module not found", None

        # Get target entity
        target_entity = self.db.query(EntityDefinition).filter(
            EntityDefinition.id == target_entity_id
        ).first()

        if not target_entity:
            return False, "Target entity not found", None

        # Get target module (entity's module)
        if not target_entity.module_id:
            return False, "Target entity does not belong to any module", None

        target_module = self.db.query(NocodeModule).filter(
            NocodeModule.id == target_entity.module_id
        ).first()

        # Check if extension already exists
        existing = self.db.query(ModuleEntityExtension).filter(
            ModuleEntityExtension.extending_module_id == extending_module_id,
            ModuleEntityExtension.target_entity_id == target_entity_id
        ).first()

        if existing:
            return False, f"Extension already exists from {extending_module.name} to {target_entity.name}", None

        # Generate extension table name
        # Format: {extending_prefix}_{target_prefix}_{target_entity}_ext
        extension_table = self._generate_extension_table_name(
            extending_module.table_prefix,
            target_module.table_prefix,
            target_entity.table_name
        )

        # Validate extension fields
        valid, message = self._validate_extension_fields(extension_fields)
        if not valid:
            return False, message, None

        # Create extension record
        extension = ModuleEntityExtension(
            extending_module_id=extending_module_id,
            target_module_id=target_module.id,
            target_entity_id=target_entity_id,
            extension_table=extension_table,
            extension_fields=extension_fields,
            is_active=True,
            created_by=self.current_user.id
        )

        self.db.add(extension)
        self.db.commit()
        self.db.refresh(extension)

        logger.info(
            f"Created entity extension: {extending_module.name} → {target_entity.name}",
            extra={
                'extending_module': extending_module.name,
                'target_entity': target_entity.name,
                'extension_table': extension_table,
                'field_count': len(extension_fields)
            }
        )

        return True, "Entity extension created successfully", {
            'id': str(extension.id),
            'extension_table': extension_table,
            'field_count': len(extension_fields)
        }

    def list_entity_extensions(
        self,
        target_entity_id: Optional[str] = None,
        extending_module_id: Optional[str] = None
    ) -> List[dict]:
        """
        List entity extensions.

        Args:
            target_entity_id: Filter by target entity
            extending_module_id: Filter by extending module

        Returns:
            List of extension records
        """
        query = self.db.query(ModuleEntityExtension)

        if target_entity_id:
            query = query.filter(ModuleEntityExtension.target_entity_id == target_entity_id)

        if extending_module_id:
            query = query.filter(ModuleEntityExtension.extending_module_id == extending_module_id)

        extensions = query.all()

        return [
            {
                'id': str(ext.id),
                'extending_module': {
                    'id': str(ext.extending_module.id),
                    'name': ext.extending_module.name,
                    'display_name': ext.extending_module.display_name
                },
                'target_entity': {
                    'id': str(ext.target_entity.id),
                    'name': ext.target_entity.name,
                    'label': ext.target_entity.label
                },
                'extension_table': ext.extension_table,
                'extension_fields': ext.extension_fields,
                'is_active': ext.is_active,
                'created_at': ext.created_at.isoformat() if ext.created_at else None
            }
            for ext in extensions
        ]

    def get_entity_with_extensions(
        self,
        entity_name: str,
        record_id: str
    ) -> Optional[dict]:
        """
        Get entity record with all extension data.

        Joins base entity data with all active extensions.

        Args:
            entity_name: Entity name (e.g., "Employee")
            record_id: Record UUID

        Returns:
            Record data with extensions

        Example response:
            {
                "id": "...",
                "name": "John Doe",
                "email": "john@company.com",
                "payroll_ext": {
                    "bank_account": "1234567890",
                    "monthly_salary": 5000.00
                },
                "benefits_ext": {
                    "health_insurance_plan": "Premium PPO"
                }
            }
        """
        # Get entity definition
        entity = self.db.query(EntityDefinition).filter(
            EntityDefinition.name == entity_name
        ).first()

        if not entity:
            return None

        # Get base entity data
        base_query = f"""
            SELECT * FROM {entity.table_name}
            WHERE id = :record_id
            AND tenant_id = :tenant_id
        """

        base_result = self.db.execute(
            text(base_query),
            {
                'record_id': record_id,
                'tenant_id': str(self.current_user.tenant_id)
            }
        ).first()

        if not base_result:
            return None

        # Convert to dict
        record = dict(base_result._mapping)

        # Get all active extensions for this entity
        extensions = self.db.query(ModuleEntityExtension).join(
            NocodeModule,
            ModuleEntityExtension.extending_module_id == NocodeModule.id
        ).filter(
            ModuleEntityExtension.target_entity_id == entity.id,
            ModuleEntityExtension.is_active == True,
            NocodeModule.status == 'active'
        ).all()

        # Join extension data
        for ext in extensions:
            ext_data = self._get_extension_data(
                ext.extension_table,
                record_id
            )
            if ext_data:
                # Add extension data with prefix
                ext_key = f"{ext.extending_module.table_prefix}_ext"
                record[ext_key] = ext_data

        return record

    # ===== Screen Extensions =====

    def create_screen_extension(
        self,
        extending_module_id: str,
        target_module_id: str,
        target_screen: str,
        extension_type: str,
        extension_config: dict,
        position: int = 999,
        required_permission: Optional[str] = None
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Create screen extension.

        Allows extending_module to add UI components to target screens.

        Args:
            extending_module_id: Module creating the extension
            target_module_id: Module owning the screen
            target_screen: Screen identifier (e.g., "employee_detail")
            extension_type: Type of extension (tab, section, widget, action)
            extension_config: Configuration for the extension
            position: Display order
            required_permission: Permission required to see this extension

        Returns:
            Tuple of (success, message, extension_data)

        Example:
            create_screen_extension(
                extending_module_id="payroll_module_id",
                target_module_id="hr_module_id",
                target_screen="employee_detail",
                extension_type="tab",
                extension_config={
                    "label": "Payroll Info",
                    "icon": "money",
                    "component_path": "/modules/payroll/components/employee-payroll-tab.js"
                },
                required_permission="payroll:employee:read"
            )
        """
        # Validate extension_type
        valid_types = ['tab', 'section', 'widget', 'action']
        if extension_type not in valid_types:
            return False, f"Invalid extension_type. Must be one of: {', '.join(valid_types)}", None

        # Validate modules exist
        extending_module = self.db.query(NocodeModule).filter(
            NocodeModule.id == extending_module_id
        ).first()

        target_module = self.db.query(NocodeModule).filter(
            NocodeModule.id == target_module_id
        ).first()

        if not extending_module:
            return False, "Extending module not found", None

        if not target_module:
            return False, "Target module not found", None

        # Create extension
        extension = ModuleScreenExtension(
            extending_module_id=extending_module_id,
            target_module_id=target_module_id,
            target_screen=target_screen,
            extension_type=extension_type,
            extension_config=extension_config,
            position=position,
            required_permission=required_permission,
            is_active=True,
            created_by=self.current_user.id
        )

        self.db.add(extension)
        self.db.commit()
        self.db.refresh(extension)

        logger.info(
            f"Created screen extension: {extending_module.name} → {target_module.name}.{target_screen}",
            extra={
                'extending_module': extending_module.name,
                'target_screen': target_screen,
                'extension_type': extension_type
            }
        )

        return True, "Screen extension created successfully", {
            'id': str(extension.id),
            'extension_type': extension_type,
            'target_screen': target_screen
        }

    def list_screen_extensions(
        self,
        target_screen: Optional[str] = None,
        target_module_id: Optional[str] = None
    ) -> List[dict]:
        """
        List screen extensions.

        Args:
            target_screen: Filter by screen name
            target_module_id: Filter by target module

        Returns:
            List of screen extensions ordered by position
        """
        query = self.db.query(ModuleScreenExtension).filter(
            ModuleScreenExtension.is_active == True
        )

        if target_screen:
            query = query.filter(ModuleScreenExtension.target_screen == target_screen)

        if target_module_id:
            query = query.filter(ModuleScreenExtension.target_module_id == target_module_id)

        # Order by position
        extensions = query.order_by(ModuleScreenExtension.position).all()

        return [
            {
                'id': str(ext.id),
                'extending_module': {
                    'id': str(ext.extending_module.id),
                    'name': ext.extending_module.name,
                    'display_name': ext.extending_module.display_name
                },
                'target_screen': ext.target_screen,
                'extension_type': ext.extension_type,
                'extension_config': ext.extension_config,
                'position': ext.position,
                'required_permission': ext.required_permission
            }
            for ext in extensions
        ]

    # ===== Menu Extensions =====

    def create_menu_extension(
        self,
        extending_module_id: str,
        menu_config: dict,
        target_module_id: Optional[str] = None,
        target_menu_item: Optional[str] = None,
        position: int = 999,
        required_permission: Optional[str] = None
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Create menu extension.

        Allows extending_module to add menu items.

        Args:
            extending_module_id: Module creating the extension
            menu_config: Menu configuration
            target_module_id: Module to add menu to (None = root menu)
            target_menu_item: Parent menu item (None = top level)
            position: Display order
            required_permission: Permission required to see this menu

        Returns:
            Tuple of (success, message, extension_data)

        Example:
            create_menu_extension(
                extending_module_id="payroll_module_id",
                target_module_id="hr_module_id",
                target_menu_item="hr_management",
                menu_config={
                    "type": "submenu",
                    "label": "Payroll",
                    "icon": "money",
                    "items": [
                        {
                            "label": "Payroll Runs",
                            "route": "payroll/runs",
                            "icon": "calendar"
                        }
                    ]
                },
                position=10
            )
        """
        # Validate extending module exists
        extending_module = self.db.query(NocodeModule).filter(
            NocodeModule.id == extending_module_id
        ).first()

        if not extending_module:
            return False, "Extending module not found", None

        # Validate target module if specified
        if target_module_id:
            target_module = self.db.query(NocodeModule).filter(
                NocodeModule.id == target_module_id
            ).first()

            if not target_module:
                return False, "Target module not found", None

        # Create extension
        extension = ModuleMenuExtension(
            extending_module_id=extending_module_id,
            target_module_id=target_module_id,
            target_menu_item=target_menu_item,
            menu_config=menu_config,
            position=position,
            required_permission=required_permission,
            is_active=True,
            created_by=self.current_user.id
        )

        self.db.add(extension)
        self.db.commit()
        self.db.refresh(extension)

        logger.info(
            f"Created menu extension: {extending_module.name}",
            extra={
                'extending_module': extending_module.name,
                'target_menu_item': target_menu_item or 'root'
            }
        )

        return True, "Menu extension created successfully", {
            'id': str(extension.id),
            'target_menu_item': target_menu_item or 'root'
        }

    def list_menu_extensions(
        self,
        target_module_id: Optional[str] = None
    ) -> List[dict]:
        """
        List menu extensions.

        Args:
            target_module_id: Filter by target module

        Returns:
            List of menu extensions ordered by position
        """
        query = self.db.query(ModuleMenuExtension).filter(
            ModuleMenuExtension.is_active == True
        )

        if target_module_id:
            query = query.filter(ModuleMenuExtension.target_module_id == target_module_id)

        # Order by position
        extensions = query.order_by(ModuleMenuExtension.position).all()

        return [
            {
                'id': str(ext.id),
                'extending_module': {
                    'id': str(ext.extending_module.id),
                    'name': ext.extending_module.name,
                    'display_name': ext.extending_module.display_name
                },
                'target_menu_item': ext.target_menu_item,
                'menu_config': ext.menu_config,
                'position': ext.position,
                'required_permission': ext.required_permission
            }
            for ext in extensions
        ]

    # ===== Helper Methods =====

    def _generate_extension_table_name(
        self,
        extending_prefix: str,
        target_prefix: str,
        target_table: str
    ) -> str:
        """
        Generate extension table name.

        Format: {extending_prefix}_{target_prefix}_{target_entity}_ext

        Example:
            payroll_hr_employees_ext
        """
        # Remove target prefix from table name if present
        if target_table.startswith(f"{target_prefix}_"):
            entity_name = target_table[len(target_prefix) + 1:]
        else:
            entity_name = target_table

        return f"{extending_prefix}_{target_prefix}_{entity_name}_ext"

    def _validate_extension_fields(self, fields: List[dict]) -> Tuple[bool, str]:
        """
        Validate extension field definitions.

        Args:
            fields: List of field definitions

        Returns:
            Tuple of (valid, message)
        """
        if not fields:
            return False, "At least one field is required"

        for field in fields:
            # Required fields
            if 'name' not in field:
                return False, "Field name is required"

            if 'type' not in field:
                return False, f"Field type is required for field '{field['name']}'"

            # Validate field name (lowercase, alphanumeric, underscore)
            if not re.match(r'^[a-z][a-z0-9_]*$', field['name']):
                return False, f"Invalid field name: {field['name']}. Must start with letter, lowercase, alphanumeric and underscore only"

            # Validate field type
            valid_types = ['string', 'text', 'integer', 'decimal', 'boolean', 'date', 'datetime', 'json']
            if field['type'] not in valid_types:
                return False, f"Invalid field type: {field['type']}. Must be one of: {', '.join(valid_types)}"

        return True, "Valid"

    def _get_extension_data(
        self,
        extension_table: str,
        record_id: str
    ) -> Optional[dict]:
        """
        Get data from extension table.

        Args:
            extension_table: Extension table name
            record_id: Base record ID

        Returns:
            Extension data dict or None
        """
        # Build query to get extension data
        # Note: Assumes extension table has foreign key named after base entity
        # For hr_employees, the FK would be employee_id
        query = f"""
            SELECT * FROM {extension_table}
            WHERE employee_id = :record_id
            AND tenant_id = :tenant_id
        """

        try:
            result = self.db.execute(
                text(query),
                {
                    'record_id': record_id,
                    'tenant_id': str(self.current_user.tenant_id)
                }
            ).first()

            if not result:
                return None

            return dict(result._mapping)

        except Exception as e:
            logger.error(f"Error fetching extension data from {extension_table}: {str(e)}")
            return None
