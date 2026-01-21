"""
Module Extension API Router

REST API endpoints for managing module extensions (Phase 4 Priority 3):
- Entity extensions
- Screen extensions
- Menu extensions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.dependencies import get_db, get_current_user
from app.schemas.module_extension import (
    EntityExtensionCreate,
    EntityExtensionResponse,
    ScreenExtensionCreate,
    ScreenExtensionResponse,
    MenuExtensionCreate,
    MenuExtensionResponse,
    ExtensionOperationResponse
)
from app.services.module_extension_service import ModuleExtensionService


router = APIRouter(
    prefix="/api/v1/module-extensions",
    tags=["module-extensions"]
)


# ===== Entity Extension Endpoints =====

@router.post("/entity", response_model=ExtensionOperationResponse)
async def create_entity_extension(
    extension_data: EntityExtensionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create entity extension.

    Allows a module to add custom fields to an entity from another module.

    **Example:**
    ```json
    {
        "extending_module_id": "payroll_module_uuid",
        "target_entity_id": "hr_employees_entity_uuid",
        "extension_fields": [
            {
                "name": "bank_account",
                "type": "string",
                "max_length": 50,
                "label": "Bank Account Number",
                "required": true
            },
            {
                "name": "monthly_salary",
                "type": "decimal",
                "precision": 12,
                "scale": 2,
                "label": "Monthly Salary",
                "required": true
            }
        ]
    }
    ```

    **Response:**
    ```json
    {
        "success": true,
        "message": "Entity extension created successfully",
        "data": {
            "id": "extension_uuid",
            "extension_table": "payroll_hr_employees_ext",
            "field_count": 2
        }
    }
    ```
    """
    service = ModuleExtensionService(db, current_user)

    success, message, data = service.create_entity_extension(
        extending_module_id=extension_data.extending_module_id,
        target_entity_id=extension_data.target_entity_id,
        extension_fields=[field.model_dump() for field in extension_data.extension_fields]
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return ExtensionOperationResponse(
        success=success,
        message=message,
        data=data
    )


@router.get("/entity", response_model=List[EntityExtensionResponse])
async def list_entity_extensions(
    target_entity_id: Optional[str] = None,
    extending_module_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List entity extensions.

    **Query Parameters:**
    - `target_entity_id`: Filter by target entity
    - `extending_module_id`: Filter by extending module

    **Example Response:**
    ```json
    [
        {
            "id": "extension_uuid",
            "extending_module": {
                "id": "payroll_module_uuid",
                "name": "payroll",
                "display_name": "Payroll Management"
            },
            "target_entity": {
                "id": "hr_employees_entity_uuid",
                "name": "Employee",
                "label": "Employee"
            },
            "extension_table": "payroll_hr_employees_ext",
            "extension_fields": [...],
            "is_active": true,
            "created_at": "2026-01-20T10:00:00Z"
        }
    ]
    ```
    """
    service = ModuleExtensionService(db, current_user)
    extensions = service.list_entity_extensions(
        target_entity_id=target_entity_id,
        extending_module_id=extending_module_id
    )
    return extensions


@router.get("/entity/{entity_name}/records/{record_id}")
async def get_entity_with_extensions(
    entity_name: str,
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get entity record with all extension data.

    Returns base entity data plus all active extension data.

    **Example Response:**
    ```json
    {
        "id": "employee_uuid",
        "name": "John Doe",
        "email": "john@company.com",
        "hire_date": "2020-01-15",
        "tenant_id": "...",
        "company_id": "...",
        "branch_id": "...",

        "payroll_ext": {
            "bank_account": "1234567890",
            "tax_id": "987-65-4321",
            "payment_method": "bank_transfer",
            "monthly_salary": 5000.00
        },

        "benefits_ext": {
            "health_insurance_plan": "Premium PPO",
            "retirement_contribution_pct": 5.0,
            "life_insurance_amount": 100000.00
        }
    }
    ```
    """
    service = ModuleExtensionService(db, current_user)
    record = service.get_entity_with_extensions(
        entity_name=entity_name,
        record_id=record_id
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record not found: {entity_name}/{record_id}"
        )

    return record


# ===== Screen Extension Endpoints =====

@router.post("/screen", response_model=ExtensionOperationResponse)
async def create_screen_extension(
    extension_data: ScreenExtensionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create screen extension.

    Allows a module to add UI components to screens from other modules.

    **Extension Types:**
    - `tab`: Add a tab to a screen
    - `section`: Add a section within existing tab
    - `widget`: Add a widget/card to a screen
    - `action`: Add a button/action to a screen

    **Example (Tab):**
    ```json
    {
        "extending_module_id": "payroll_module_uuid",
        "target_module_id": "hr_module_uuid",
        "target_screen": "employee_detail",
        "extension_type": "tab",
        "extension_config": {
            "label": "Payroll Info",
            "icon": "money",
            "component_path": "/modules/payroll/components/employee-payroll-tab.js"
        },
        "position": 10,
        "required_permission": "payroll:employee:read"
    }
    ```

    **Example (Widget):**
    ```json
    {
        "extending_module_id": "benefits_module_uuid",
        "target_module_id": "hr_module_uuid",
        "target_screen": "employee_detail",
        "extension_type": "widget",
        "extension_config": {
            "title": "Quick Benefits Summary",
            "component_path": "/modules/benefits/widgets/benefits-summary.js",
            "size": "medium"
        },
        "position": 5
    }
    ```
    """
    service = ModuleExtensionService(db, current_user)

    success, message, data = service.create_screen_extension(
        extending_module_id=extension_data.extending_module_id,
        target_module_id=extension_data.target_module_id,
        target_screen=extension_data.target_screen,
        extension_type=extension_data.extension_type,
        extension_config=extension_data.extension_config,
        position=extension_data.position,
        required_permission=extension_data.required_permission
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return ExtensionOperationResponse(
        success=success,
        message=message,
        data=data
    )


@router.get("/screen", response_model=List[ScreenExtensionResponse])
async def list_screen_extensions(
    target_screen: Optional[str] = None,
    target_module_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List screen extensions.

    **Query Parameters:**
    - `target_screen`: Filter by screen name (e.g., "employee_detail")
    - `target_module_id`: Filter by target module

    Returns extensions ordered by position.

    **Example Response:**
    ```json
    [
        {
            "id": "extension_uuid",
            "extending_module": {
                "id": "payroll_module_uuid",
                "name": "payroll",
                "display_name": "Payroll Management"
            },
            "target_screen": "employee_detail",
            "extension_type": "tab",
            "extension_config": {
                "label": "Payroll Info",
                "icon": "money",
                "component_path": "/modules/payroll/components/employee-payroll-tab.js"
            },
            "position": 10,
            "required_permission": "payroll:employee:read"
        }
    ]
    ```
    """
    service = ModuleExtensionService(db, current_user)
    extensions = service.list_screen_extensions(
        target_screen=target_screen,
        target_module_id=target_module_id
    )
    return extensions


# ===== Menu Extension Endpoints =====

@router.post("/menu", response_model=ExtensionOperationResponse)
async def create_menu_extension(
    extension_data: MenuExtensionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create menu extension.

    Allows a module to add menu items to other modules' menus or to root menu.

    **Example (Submenu):**
    ```json
    {
        "extending_module_id": "payroll_module_uuid",
        "target_module_id": "hr_module_uuid",
        "target_menu_item": "hr_management",
        "menu_config": {
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
                {
                    "label": "Payslips",
                    "route": "payroll/payslips",
                    "icon": "receipt",
                    "permission": "payroll:payslips:read"
                }
            ]
        },
        "position": 10
    }
    ```

    **Example (Link):**
    ```json
    {
        "extending_module_id": "reports_module_uuid",
        "target_module_id": null,
        "target_menu_item": null,
        "menu_config": {
            "type": "link",
            "label": "Reports",
            "route": "reports",
            "icon": "chart-bar"
        },
        "position": 100,
        "required_permission": "reports:view"
    }
    ```
    """
    service = ModuleExtensionService(db, current_user)

    success, message, data = service.create_menu_extension(
        extending_module_id=extension_data.extending_module_id,
        target_module_id=extension_data.target_module_id,
        target_menu_item=extension_data.target_menu_item,
        menu_config=extension_data.menu_config,
        position=extension_data.position,
        required_permission=extension_data.required_permission
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return ExtensionOperationResponse(
        success=success,
        message=message,
        data=data
    )


@router.get("/menu", response_model=List[MenuExtensionResponse])
async def list_menu_extensions(
    target_module_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List menu extensions.

    **Query Parameters:**
    - `target_module_id`: Filter by target module

    Returns extensions ordered by position.

    **Example Response:**
    ```json
    [
        {
            "id": "extension_uuid",
            "extending_module": {
                "id": "payroll_module_uuid",
                "name": "payroll",
                "display_name": "Payroll Management"
            },
            "target_menu_item": "hr_management",
            "menu_config": {
                "type": "submenu",
                "label": "Payroll",
                "icon": "money",
                "items": [...]
            },
            "position": 10,
            "required_permission": null
        }
    ]
    ```
    """
    service = ModuleExtensionService(db, current_user)
    extensions = service.list_menu_extensions(
        target_module_id=target_module_id
    )
    return extensions
