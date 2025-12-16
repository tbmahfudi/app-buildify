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
        # Get user permissions and roles (through groups)
        permissions = user.get_permissions()
        roles = list(user.get_roles()) if hasattr(user, 'get_roles') else []

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
        Also includes parent menu items from navigation.menu_items.
        """
        import logging
        logger = logging.getLogger(__name__)

        # Get enabled modules for tenant
        tenant_modules = db.query(TenantModule).filter(
            TenantModule.tenant_id == user.tenant_id,
            TenantModule.is_enabled == True
        ).all()

        module_menu_items = []
        parent_menu_codes = {}  # Track parent menu codes

        for tenant_module in tenant_modules:
            # Get module manifest from the module registry
            if not tenant_module.module or not hasattr(tenant_module.module, 'manifest'):
                continue

            manifest = tenant_module.module.manifest if tenant_module.module.manifest else {}

            if not manifest:
                continue

            module_code = tenant_module.module.name
            logger.info(f"Processing module: {module_code}")

            # Process parent menu items from navigation.menu_items
            navigation = manifest.get('navigation', {})
            menu_items_config = navigation.get('menu_items', [])

            for menu_item_config in menu_items_config:
                # Create parent menu item
                parent_code = menu_item_config.get('code', f"module_{module_code}_parent")
                parent_menu_item = MenuItem(
                    code=parent_code,
                    title=menu_item_config.get('label', module_code.title()),
                    icon=menu_item_config.get('icon', 'ph-duotone ph-square'),
                    route=None,  # Parent items typically don't have routes
                    permission=menu_item_config.get('permission'),
                    order=menu_item_config.get('order', 999),
                    module_code=module_code,
                    is_system=False,
                    parent_id=None,
                    is_active=True,
                    is_visible=True,
                    target='_self',
                    extra_data={'icon_color': menu_item_config.get('icon_color')}
                )

                # Explicitly set id to None to ensure it uses code for matching
                parent_menu_item.id = None

                logger.info(f"Created parent menu: code={parent_code}, id={parent_menu_item.id}")

                # Store parent code for child linking
                parent_menu_codes[parent_code] = parent_menu_item
                module_menu_items.append(parent_menu_item)

            # Process routes that have menu configuration
            for route in manifest.get('routes', []):
                if 'menu' not in route:
                    continue

                # Check permission
                route_permission = route.get('permission')
                if route_permission and route_permission not in permissions:
                    continue

                # Determine parent
                menu_parent = route['menu'].get('parent')
                parent_id = None
                parent_item = None
                if menu_parent and menu_parent in parent_menu_codes:
                    parent_item = parent_menu_codes[menu_parent]
                    # For module items, use the parent's code as parent_id
                    # This ensures consistency when building the tree
                    parent_id = parent_item.code if hasattr(parent_item, 'code') else None
                    logger.info(f"Route {route.get('path')} has parent: {menu_parent}, parent_id set to: {parent_id}")

                # Create virtual MenuItem for module route
                menu_item = MenuItem(
                    code=f"module_{module_code}_{route.get('path', '').replace('#/', '').replace('/', '_')}",
                    title=route['menu'].get('label', route.get('name', 'Unknown')),
                    icon=route['menu'].get('icon', 'ph-duotone ph-square'),
                    route=route.get('path', '').replace('#/', ''),
                    permission=route_permission,
                    order=route['menu'].get('order', 999),
                    module_code=module_code,
                    is_system=False,
                    parent_id=parent_id,
                    is_active=True,
                    is_visible=True,
                    target='_self'
                )

                # Explicitly set id to None
                menu_item.id = None

                logger.info(f"Created menu item: code={menu_item.code}, parent_id={menu_item.parent_id}, id={menu_item.id}")

                module_menu_items.append(menu_item)

        logger.info(f"Total module menu items: {len(module_menu_items)}")
        return module_menu_items

    @staticmethod
    def _build_menu_tree(items: List[MenuItem]) -> List[Dict[str, Any]]:
        """
        Build hierarchical menu structure from flat list.

        Converts MenuItem objects to dictionaries with nested children.
        Filters out parent items that have no accessible children.
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Building menu tree from {len(items)} items")

        # Create lookup map
        item_map = {}
        for item in items:
            item_id = str(item.id) if hasattr(item, 'id') and item.id else item.code
            item_map[item_id] = item
            logger.info(f"  item_map[{item_id}] = {item.code} (parent_id={item.parent_id}, route={item.route})")

        # Build tree
        tree = []
        for item in items:
            item_id = str(item.id) if hasattr(item, 'id') and item.id else item.code

            if not item.parent_id:
                # Root item
                logger.info(f"Processing root item: {item.code} (item_id={item_id})")
                item_dict = MenuService._item_to_dict(item, item_map)
                logger.info(f"  -> has {len(item_dict.get('children', []))} children")

                # Filter out parent menus with no children
                # If the item has no route (parent-only) and no children, skip it
                if not item_dict.get('route') and len(item_dict.get('children', [])) == 0:
                    logger.info(f"  -> Filtering out {item.code} (no route and no children)")
                    continue

                tree.append(item_dict)

        # Sort by order
        tree.sort(key=lambda x: x.get('order', 0))

        logger.info(f"Final tree has {len(tree)} root items")
        return tree

    @staticmethod
    def _item_to_dict(item: MenuItem, item_map: Dict[str, MenuItem]) -> Dict[str, Any]:
        """
        Convert menu item to dictionary with children.

        Recursively builds nested structure.
        """
        import logging
        logger = logging.getLogger(__name__)

        item_id = str(item.id) if hasattr(item, 'id') and item.id else item.code
        logger.info(f"    _item_to_dict: {item.code}, item_id={item_id}")

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

        # Include RBAC information (useful for client-side checks and UI state)
        if item.permission:
            result['permission'] = item.permission
        if item.required_roles:
            result['required_roles'] = item.required_roles

        # Add extra_data if present
        if item.extra_data:
            result['extra_data'] = item.extra_data

        # Add children
        children = []
        for child_id, child in item_map.items():
            # Compare parent_id with item_id, handling both UUID and code-based IDs
            child_parent_id_str = str(child.parent_id) if child.parent_id else None
            if child_parent_id_str:
                logger.info(f"      Checking child {child.code}: parent_id={child_parent_id_str}, item_id={item_id}, match={child_parent_id_str == item_id}")
            if child_parent_id_str and child_parent_id_str == item_id:
                logger.info(f"      -> MATCH! Adding child: {child.code}")
                children.append(child)

        # Sort children by order and convert to dict
        for child in sorted(children, key=lambda x: x.order):
            result['children'].append(MenuService._item_to_dict(child, item_map))

        logger.info(f"    {item.code} has {len(children)} children")
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
