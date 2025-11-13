"""
Menu service - business logic for backend-driven RBAC menu system.

Provides functions to:
- Get accessible menu items for a user based on RBAC
- Build hierarchical menu structure
- Filter menus by permissions and roles
- Integrate module menus with core menus
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from app.models.menu_item import MenuItem
from app.models.user import User
from app.models.module_registry import TenantModule


class MenuService:
    """Service for menu operations with RBAC."""

    @staticmethod
    async def get_user_menu(
        db: Session,
        user: User,
        include_modules: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get menu items accessible to user based on RBAC.

        Args:
            db: Database session
            user: Current user
            include_modules: Whether to include module menus

        Returns:
            List of menu items in hierarchical structure
        """
        # Get user permissions and roles
        permissions = user.get_permissions()
        roles = [role.code for role in user.user_roles] if hasattr(user, 'user_roles') else []

        # Get accessible core menu items
        menu_items = MenuService._get_accessible_menu_items(
            db=db,
            user=user,
            permissions=permissions,
            roles=roles
        )

        # Include module menus if requested
        if include_modules:
            module_menus = await MenuService._get_module_menu_items(
                db=db,
                user=user,
                permissions=permissions
            )
            menu_items.extend(module_menus)

        # Build hierarchical structure
        menu_tree = MenuService._build_menu_tree(menu_items)

        return menu_tree

    @staticmethod
    def _get_accessible_menu_items(
        db: Session,
        user: User,
        permissions: Set[str],
        roles: List[str]
    ) -> List[MenuItem]:
        """
        Get menu items user can access from database.

        Filters by:
        - Active and visible status
        - Tenant isolation (system menus + user's tenant menus)
        - RBAC permissions and roles
        """
        # Base query: system menus + tenant menus
        query = db.query(MenuItem).filter(
            MenuItem.is_active == True,
            MenuItem.is_visible == True,
            or_(
                MenuItem.tenant_id == None,  # System menus
                MenuItem.tenant_id == user.tenant_id  # Tenant menus
            )
        )

        all_items = query.all()

        # Filter by RBAC
        accessible_items = []
        for item in all_items:
            if MenuService._is_menu_accessible(item, permissions, roles, user):
                accessible_items.append(item)

        return accessible_items

    @staticmethod
    def _is_menu_accessible(
        item: MenuItem,
        permissions: Set[str],
        roles: List[str],
        user: User
    ) -> bool:
        """
        Check if user can access a menu item.

        Rules:
        1. Superuser can access everything
        2. No restrictions = accessible to all authenticated users
        3. If required_roles specified, user must have at least one
        4. If permission specified, user must have that permission
        """
        # Superuser sees everything
        if user.is_superuser:
            return True

        # No restrictions = accessible to all authenticated users
        if not item.permission and not item.required_roles:
            return True

        # Check role requirements
        if item.required_roles:
            # required_roles is a JSON array, check if user has any of the roles
            if not any(role in roles for role in item.required_roles):
                return False

        # Check permission requirements
        if item.permission:
            if item.permission not in permissions:
                return False

        return True

    @staticmethod
    async def _get_module_menu_items(
        db: Session,
        user: User,
        permissions: Set[str]
    ) -> List[MenuItem]:
        """
        Get menu items from installed modules.

        Queries TenantModule to find enabled modules and their routes,
        then converts them to MenuItem objects for consistency.
        """
        # Get enabled modules for tenant
        tenant_modules = db.query(TenantModule).filter(
            TenantModule.tenant_id == user.tenant_id,
            TenantModule.is_enabled == True
        ).all()

        module_menu_items = []

        for tenant_module in tenant_modules:
            # Get module manifest
            manifest = tenant_module.config if hasattr(tenant_module, 'config') else {}

            if not manifest or 'routes' not in manifest:
                continue

            # Process routes that have menu configuration
            for route in manifest.get('routes', []):
                if 'menu' not in route:
                    continue

                # Check permission
                route_permission = route.get('permission')
                if route_permission and route_permission not in permissions:
                    continue

                # Create virtual MenuItem for module route
                menu_item = MenuItem(
                    code=f"module_{tenant_module.module_code}_{route.get('path', '').replace('#/', '').replace('/', '_')}",
                    title=route['menu'].get('label', route.get('name', 'Unknown')),
                    icon=route['menu'].get('icon', 'ph-duotone ph-square'),
                    route=route.get('path', '').replace('#/', ''),
                    permission=route_permission,
                    order=route['menu'].get('order', 999),
                    module_code=tenant_module.module_code,
                    is_system=False,
                    parent_id=None,  # Module menus are top-level for now
                    is_active=True,
                    is_visible=True,
                    target='_self'
                )

                module_menu_items.append(menu_item)

        return module_menu_items

    @staticmethod
    def _build_menu_tree(items: List[MenuItem]) -> List[Dict[str, Any]]:
        """
        Build hierarchical menu structure from flat list.

        Converts MenuItem objects to dictionaries with nested children.
        """
        # Create lookup map
        item_map = {}
        for item in items:
            item_id = str(item.id) if hasattr(item, 'id') and item.id else item.code
            item_map[item_id] = item

        # Build tree
        tree = []
        for item in items:
            item_id = str(item.id) if hasattr(item, 'id') and item.id else item.code

            if not item.parent_id:
                # Root item
                tree.append(MenuService._item_to_dict(item, item_map))

        # Sort by order
        tree.sort(key=lambda x: x.get('order', 0))

        return tree

    @staticmethod
    def _item_to_dict(item: MenuItem, item_map: Dict[str, MenuItem]) -> Dict[str, Any]:
        """
        Convert menu item to dictionary with children.

        Recursively builds nested structure.
        """
        item_id = str(item.id) if hasattr(item, 'id') and item.id else item.code

        result = {
            'id': item_id,
            'code': item.code,
            'title': item.title,
            'icon': item.icon,
            'route': item.route,
            'order': item.order,
            'target': item.target,
            'children': []
        }

        # Add metadata if present
        if item.metadata:
            result['metadata'] = item.metadata

        # Add children
        children = []
        for child_id, child in item_map.items():
            if child.parent_id and str(child.parent_id) == item_id:
                children.append(child)

        # Sort children by order and convert to dict
        for child in sorted(children, key=lambda x: x.order):
            result['children'].append(MenuService._item_to_dict(child, item_map))

        return result

    @staticmethod
    def get_all_menu_items(
        db: Session,
        user: User,
        tenant_id: Optional[str] = None
    ) -> List[MenuItem]:
        """
        Get all menu items for admin management.

        Args:
            db: Database session
            user: Current user (must have menu:manage permission)
            tenant_id: Optional tenant filter

        Returns:
            List of all menu items
        """
        query = db.query(MenuItem).filter(MenuItem.is_active == True)

        if not user.is_superuser:
            # Filter by tenant
            query = query.filter(
                or_(
                    MenuItem.tenant_id == user.tenant_id,
                    MenuItem.tenant_id == None  # System menus
                )
            )
        elif tenant_id:
            # Superuser with specific tenant filter
            query = query.filter(
                or_(
                    MenuItem.tenant_id == tenant_id,
                    MenuItem.tenant_id == None
                )
            )

        return query.order_by(MenuItem.order).all()

    @staticmethod
    def create_menu_item(
        db: Session,
        user: User,
        menu_data: Dict[str, Any]
    ) -> MenuItem:
        """
        Create a new menu item.

        Args:
            db: Database session
            user: Current user
            menu_data: Menu item data

        Returns:
            Created MenuItem
        """
        from app.models.base import generate_uuid

        # Set tenant_id based on user permissions
        if not user.is_superuser:
            menu_data['tenant_id'] = user.tenant_id

        # Generate ID if not provided
        if 'id' not in menu_data or not menu_data['id']:
            menu_data['id'] = generate_uuid()

        menu_item = MenuItem(**menu_data)
        db.add(menu_item)
        db.commit()
        db.refresh(menu_item)

        return menu_item

    @staticmethod
    def update_menu_item(
        db: Session,
        user: User,
        menu_id: str,
        menu_data: Dict[str, Any]
    ) -> Optional[MenuItem]:
        """
        Update a menu item.

        Args:
            db: Database session
            user: Current user
            menu_id: Menu item ID
            menu_data: Updated data

        Returns:
            Updated MenuItem or None if not found
        """
        menu_item = db.query(MenuItem).filter(MenuItem.id == menu_id).first()

        if not menu_item:
            return None

        # Check tenant access
        if not user.is_superuser:
            if menu_item.tenant_id and menu_item.tenant_id != user.tenant_id:
                return None

        # Update fields
        for key, value in menu_data.items():
            if key != 'id' and hasattr(menu_item, key):
                setattr(menu_item, key, value)

        menu_item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(menu_item)

        return menu_item

    @staticmethod
    def delete_menu_item(
        db: Session,
        user: User,
        menu_id: str
    ) -> bool:
        """
        Delete a menu item (soft delete by setting is_active=False).

        Args:
            db: Database session
            user: Current user
            menu_id: Menu item ID

        Returns:
            True if deleted, False if not found or not allowed
        """
        menu_item = db.query(MenuItem).filter(MenuItem.id == menu_id).first()

        if not menu_item:
            return False

        # Check tenant access
        if not user.is_superuser:
            if menu_item.tenant_id and menu_item.tenant_id != user.tenant_id:
                return False

        # Prevent deletion of system menus by non-superusers
        if menu_item.is_system and not user.is_superuser:
            return False

        # Soft delete
        menu_item.is_active = False
        menu_item.updated_at = datetime.utcnow()
        db.commit()

        return True

    @staticmethod
    def reorder_menu_items(
        db: Session,
        user: User,
        reorder_data: List[Dict[str, Any]]
    ) -> bool:
        """
        Reorder menu items.

        Args:
            db: Database session
            user: Current user
            reorder_data: List of {id, order} dictionaries

        Returns:
            True if successful
        """
        for item_data in reorder_data:
            menu_id = item_data.get('id')
            new_order = item_data.get('order')

            menu_item = db.query(MenuItem).filter(MenuItem.id == menu_id).first()

            if menu_item:
                # Check tenant access
                if not user.is_superuser:
                    if menu_item.tenant_id and menu_item.tenant_id != user.tenant_id:
                        continue

                menu_item.order = new_order
                menu_item.updated_at = datetime.utcnow()

        db.commit()
        return True
