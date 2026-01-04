"""
Menu Management API Endpoints

Provides REST API for backend-driven RBAC menu system:
- Get user's accessible menu (RBAC-filtered)
- Admin: Manage menu items (CRUD)
- Admin: Reorder menu items
- Tenant-specific menu customization
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.dependencies import get_db, get_current_user, has_permission
from app.core.audit import create_audit_log
from app.models.user import User
from app.models.menu_item import MenuItem
from app.services.menu_service import MenuService
from app.schemas.menu import (
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
    MenuItemTree,
    MenuReorderRequest,
    MenuOperationResponse,
    UserMenuResponse,
    MenuItemListResponse,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=List[MenuItemTree])
async def get_user_menu(
    include_modules: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get menu items accessible to current user based on RBAC.

    This endpoint returns only the menu items the user has permission to access.
    It automatically filters based on:
    - User's roles
    - User's permissions
    - Tenant isolation
    - Module availability

    Args:
        include_modules: Include menu items from installed modules (default: True)

    Returns:
        Hierarchical menu structure with only accessible items
    """
    try:
        menu_tree = await MenuService.get_user_menu(
            db=db,
            user=current_user,
            include_modules=include_modules
        )

        return menu_tree

    except Exception as e:
        logger.error(f"Error fetching user menu: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load menu"
        )


@router.get("/admin", response_model=MenuItemListResponse)
async def get_all_menu_items(
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("menu:manage:tenant"))
):
    """
    Get all menu items for admin management.

    Requires permission: menu:manage:tenant

    Args:
        tenant_id: Optional tenant filter (superuser only)

    Returns:
        List of all menu items (not filtered by RBAC)
    """
    try:
        menu_items = MenuService.get_all_menu_items(
            db=db,
            user=current_user,
            tenant_id=tenant_id
        )

        return MenuItemListResponse(
            items=[MenuItemResponse.from_orm(item) for item in menu_items],
            total=len(menu_items)
        )

    except Exception as e:
        logger.error(f"Error fetching menu items for admin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch menu items"
        )


@router.get("/{menu_id}", response_model=MenuItemResponse)
async def get_menu_item(
    menu_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("menu:read:tenant"))
):
    """
    Get a specific menu item by ID.

    Requires permission: menu:read:tenant
    """
    menu_item = db.query(MenuItem).filter(MenuItem.id == menu_id).first()

    if not menu_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    # Check tenant access
    if not current_user.is_superuser:
        if menu_item.tenant_id and menu_item.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    return MenuItemResponse.from_orm(menu_item)


@router.post("", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    menu_data: MenuItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("menu:create:tenant"))
):
    """
    Create a new menu item.

    Requires permission: menu:create:tenant

    Args:
        menu_data: Menu item data

    Returns:
        Created menu item
    """
    try:
        # Convert to dict
        menu_dict = menu_data.model_dump()

        # Create menu item
        menu_item = MenuService.create_menu_item(
            db=db,
            user=current_user,
            menu_data=menu_dict
        )

        # Audit log
        await create_audit_log(
            db=db,
            user_id=str(current_user.id),
            tenant_id=current_user.tenant_id,
            action="menu.create",
            resource_type="menu_item",
            resource_id=str(menu_item.id),
            details={
                "code": menu_item.code,
                "title": menu_item.title,
                "route": menu_item.route
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return MenuItemResponse.from_orm(menu_item)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating menu item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create menu item"
        )


@router.put("/{menu_id}", response_model=MenuItemResponse)
async def update_menu_item(
    menu_id: str,
    menu_data: MenuItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("menu:update:tenant"))
):
    """
    Update a menu item.

    Requires permission: menu:update:tenant

    Args:
        menu_id: Menu item ID
        menu_data: Updated menu data

    Returns:
        Updated menu item
    """
    try:
        # Convert to dict, excluding None values
        menu_dict = menu_data.model_dump(exclude_none=True)

        # Update menu item
        menu_item = MenuService.update_menu_item(
            db=db,
            user=current_user,
            menu_id=menu_id,
            menu_data=menu_dict
        )

        if not menu_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found or access denied"
            )

        # Audit log
        await create_audit_log(
            db=db,
            user_id=str(current_user.id),
            tenant_id=current_user.tenant_id,
            action="menu.update",
            resource_type="menu_item",
            resource_id=str(menu_item.id),
            details={
                "code": menu_item.code,
                "updates": menu_dict
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return MenuItemResponse.from_orm(menu_item)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating menu item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update menu item"
        )


@router.delete("/{menu_id}", response_model=MenuOperationResponse)
async def delete_menu_item(
    menu_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("menu:delete:tenant"))
):
    """
    Delete a menu item (soft delete).

    Requires permission: menu:delete:tenant

    Args:
        menu_id: Menu item ID

    Returns:
        Operation result
    """
    try:
        # Get menu item for audit
        menu_item = db.query(MenuItem).filter(MenuItem.id == menu_id).first()
        if menu_item:
            menu_code = menu_item.code
            menu_title = menu_item.title
        else:
            menu_code = None
            menu_title = None

        # Delete menu item
        success = MenuService.delete_menu_item(
            db=db,
            user=current_user,
            menu_id=menu_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found, access denied, or cannot delete system menu"
            )

        # Audit log
        await create_audit_log(
            db=db,
            user_id=str(current_user.id),
            tenant_id=current_user.tenant_id,
            action="menu.delete",
            resource_type="menu_item",
            resource_id=menu_id,
            details={
                "code": menu_code,
                "title": menu_title
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return MenuOperationResponse(
            success=True,
            message="Menu item deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting menu item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete menu item"
        )


@router.post("/reorder", response_model=MenuOperationResponse)
async def reorder_menu_items(
    reorder_data: MenuReorderRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("menu:update:tenant"))
):
    """
    Reorder menu items.

    Requires permission: menu:update:tenant

    Args:
        reorder_data: List of menu items with new order positions

    Returns:
        Operation result
    """
    try:
        # Convert to list of dicts
        items = [item.model_dump() for item in reorder_data.items]

        # Reorder menu items
        success = MenuService.reorder_menu_items(
            db=db,
            user=current_user,
            reorder_data=items
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reorder menu items"
            )

        # Audit log
        await create_audit_log(
            db=db,
            user_id=str(current_user.id),
            tenant_id=current_user.tenant_id,
            action="menu.reorder",
            resource_type="menu_item",
            resource_id=None,
            details={
                "item_count": len(items)
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return MenuOperationResponse(
            success=True,
            message=f"Successfully reordered {len(items)} menu items"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering menu items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder menu items"
        )


@router.post("/sync", response_model=MenuOperationResponse)
async def sync_menu_from_json(
    clear_existing: bool = False,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("menu:manage:tenant"))
):
    """
    Sync menu items from menu.json file to database.

    This endpoint reads the frontend/config/menu.json file and imports all menu
    items into the database, creating a backend-driven menu system.

    Requires permission: menu:manage:tenant

    Args:
        clear_existing: If True, delete existing menu items before syncing (default: False)

    Returns:
        Operation result with count of items created
    """
    try:
        # Import the seed function
        from app.seeds.seed_menu_items import seed_menu_items

        # Run the seed function
        items_created = seed_menu_items(clear_existing=clear_existing)

        # Audit log
        await create_audit_log(
            db=db,
            user_id=str(current_user.id),
            tenant_id=current_user.tenant_id,
            action="menu.sync",
            resource_type="menu_item",
            resource_id=None,
            details={
                "items_created": items_created,
                "clear_existing": clear_existing
            },
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None
        )

        return MenuOperationResponse(
            success=True,
            message=f"Successfully synced {items_created} menu items from menu.json"
        )

    except FileNotFoundError as e:
        logger.error(f"menu.json not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="menu.json file not found. Please ensure it exists in frontend/config/menu.json"
        )
    except Exception as e:
        logger.error(f"Error syncing menu from JSON: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync menu: {str(e)}"
        )
