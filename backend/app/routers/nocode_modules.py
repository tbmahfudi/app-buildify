"""
No-Code Module API Endpoints

REST API for Module System Foundation (Phase 4 Priority 1).
Provides endpoints for module CRUD, dependencies, and versioning.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.dependencies import get_db, get_current_user
from app.services.nocode_module_service import NocodeModuleService
from app.schemas.nocode_module import (
    NocodeModuleCreate,
    NocodeModuleUpdate,
    NocodeModuleResponse,
    NocodeModuleListResponse,
    ModuleDependencyCreate,
    ModuleDependencyResponse,
    ModuleDependentResponse,
    DependencyCompatibilityCheck,
    ModuleVersionCreate,
    ModuleVersionResponse,
    ModuleVersionListResponse,
    ModuleOperationResponse,
    ValidationResponse,
    ModuleComponentsResponse,
    ModulePublishRequest,
)
from app.models.user import User

router = APIRouter(prefix="/api/v1/nocode-modules", tags=["nocode-modules"])


# ==================== Module CRUD ====================

@router.post("", response_model=ModuleOperationResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    module_data: NocodeModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new no-code module.

    Creates a module with semantic versioning (starts at 1.0.0).
    Module name and table_prefix must be unique.
    """
    service = NocodeModuleService(db, current_user)

    success, message, data = await service.create_module(
        name=module_data.name,
        display_name=module_data.display_name,
        description=module_data.description,
        table_prefix=module_data.table_prefix,
        category=module_data.category,
        icon=module_data.icon,
        color=module_data.color,
        is_platform_level=module_data.is_platform_level
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return ModuleOperationResponse(success=True, message=message, data=data)


@router.get("", response_model=NocodeModuleListResponse)
async def list_modules(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    include_platform: bool = Query(True, description="Include platform-level templates"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all modules accessible to the current user.

    Includes tenant-specific modules and optionally platform-level templates.
    """
    service = NocodeModuleService(db, current_user)

    modules = await service.list_modules(
        status=status_filter,
        category=category,
        include_platform=include_platform
    )

    return NocodeModuleListResponse(
        modules=[NocodeModuleResponse(**m) for m in modules],
        total=len(modules)
    )


@router.get("/{module_id}", response_model=NocodeModuleResponse)
async def get_module(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific module.
    """
    service = NocodeModuleService(db, current_user)

    module = await service.get_module(module_id)

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module with ID '{module_id}' not found"
        )

    return NocodeModuleResponse(**module)


@router.put("/{module_id}", response_model=ModuleOperationResponse)
async def update_module(
    module_id: str,
    module_data: NocodeModuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update module metadata.

    Note: Module name and table_prefix cannot be changed after creation.
    """
    service = NocodeModuleService(db, current_user)

    success, message = await service.update_module(
        module_id=module_id,
        display_name=module_data.display_name,
        description=module_data.description,
        category=module_data.category,
        icon=module_data.icon,
        color=module_data.color,
        config=module_data.config
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return ModuleOperationResponse(success=True, message=message)


@router.post("/{module_id}/publish", response_model=ModuleOperationResponse)
async def publish_module(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Publish module (draft → active).

    Validates all dependencies before publishing.
    """
    service = NocodeModuleService(db, current_user)

    success, message = await service.publish_module(module_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return ModuleOperationResponse(success=True, message=message)


@router.delete("/{module_id}", response_model=ModuleOperationResponse)
async def delete_module(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete module.

    Only allowed if:
    - Module is not core
    - No other modules depend on it
    """
    service = NocodeModuleService(db, current_user)

    success, message = await service.delete_module(module_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return ModuleOperationResponse(success=True, message=message)


# ==================== Dependencies ====================

@router.get("/{module_id}/dependencies", response_model=List[ModuleDependencyResponse])
async def list_dependencies(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all dependencies for a module.

    Shows which modules this module depends on.
    """
    service = NocodeModuleService(db, current_user)

    dependencies = await service.list_dependencies(module_id)

    return [ModuleDependencyResponse(**dep) for dep in dependencies]


@router.post("/{module_id}/dependencies", response_model=ModuleOperationResponse)
async def add_dependency(
    module_id: str,
    dependency_data: ModuleDependencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a dependency between modules.

    Checks for circular dependencies before adding.
    """
    service = NocodeModuleService(db, current_user)

    success, message = await service.add_dependency(
        module_id=module_id,
        depends_on_module_id=dependency_data.depends_on_module_id,
        dependency_type=dependency_data.dependency_type,
        min_version=dependency_data.min_version,
        max_version=dependency_data.max_version,
        reason=dependency_data.reason
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return ModuleOperationResponse(success=True, message=message)


@router.delete("/{module_id}/dependencies/{dependency_id}", response_model=ModuleOperationResponse)
async def remove_dependency(
    module_id: str,
    dependency_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a dependency.
    """
    service = NocodeModuleService(db, current_user)

    success, message = await service.remove_dependency(module_id, dependency_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return ModuleOperationResponse(success=True, message=message)


@router.get("/{module_id}/dependents", response_model=List[ModuleDependentResponse])
async def list_dependents(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List modules that depend on this module.

    Shows which other modules would be affected if this module is changed.
    """
    service = NocodeModuleService(db, current_user)

    dependents = await service.list_dependents(module_id)

    return [ModuleDependentResponse(**dep) for dep in dependents]


@router.get("/{module_id}/dependencies/check", response_model=DependencyCompatibilityCheck)
async def check_dependency_compatibility(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if all dependencies are satisfied.

    Validates:
    - Dependency modules are active
    - Version constraints are met
    """
    service = NocodeModuleService(db, current_user)

    is_compatible, issues = await service.check_dependency_compatibility(module_id)

    return DependencyCompatibilityCheck(
        is_compatible=is_compatible,
        issues=issues
    )


# ==================== Versioning ====================

@router.get("/{module_id}/versions", response_model=ModuleVersionListResponse)
async def list_versions(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all versions of a module.

    Shows version history with snapshots.
    """
    service = NocodeModuleService(db, current_user)

    versions = await service.list_versions(module_id)

    return ModuleVersionListResponse(
        versions=[ModuleVersionResponse(**v) for v in versions],
        total=len(versions)
    )


@router.post("/{module_id}/versions", response_model=ModuleOperationResponse)
async def create_version(
    module_id: str,
    version_data: ModuleVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new version of the module.

    Increments version based on change_type:
    - major: Breaking changes (1.0.0 → 2.0.0)
    - minor: New features (1.0.0 → 1.1.0)
    - patch: Bug fixes (1.0.0 → 1.0.1)
    - hotfix: Urgent fixes (same as patch)

    Creates a complete snapshot of the module state.
    """
    service = NocodeModuleService(db, current_user)

    success, message, new_version = await service.increment_version(
        module_id=module_id,
        change_type=version_data.change_type,
        change_summary=version_data.change_summary,
        changelog=version_data.changelog,
        breaking_changes=version_data.breaking_changes
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return ModuleOperationResponse(
        success=True,
        message=message,
        data={"new_version": new_version}
    )


# ==================== Validation Helpers ====================

@router.post("/validate/prefix", response_model=ValidationResponse)
async def validate_prefix(
    table_prefix: str = Query(..., description="Table prefix to validate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate if a table prefix is available.

    Checks:
    - Format (1-10 lowercase alphanumeric, no underscore)
    - Uniqueness (not already in use)
    """
    service = NocodeModuleService(db, current_user)

    is_valid, message = await service.validate_prefix(table_prefix)

    return ValidationResponse(is_valid=is_valid, message=message)


@router.post("/validate/name", response_model=ValidationResponse)
async def validate_name(
    name: str = Query(..., description="Module name to validate"),
    is_platform_level: bool = Query(False, description="Check at platform level"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate if a module name is available.

    Checks name uniqueness at tenant or platform level.
    """
    service = NocodeModuleService(db, current_user)

    is_valid, message = await service.validate_name(name, is_platform_level)

    return ValidationResponse(is_valid=is_valid, message=message)


# ==================== Module Components ====================

@router.get("/{module_id}/components", response_model=ModuleComponentsResponse)
async def get_module_components(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all components belonging to a module.

    Returns entities, workflows, automations, lookups, reports, and dashboards.
    """
    service = NocodeModuleService(db, current_user)

    # Get module
    module = await service.get_module(module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module with ID '{module_id}' not found"
        )

    # Create snapshot (which includes all components)
    from app.models.nocode_module import Module
    module_obj = db.query(Module).filter(Module.id == module_id).first()
    snapshot = await service._create_module_snapshot(module_obj)

    return ModuleComponentsResponse(
        module_id=module_id,
        module_name=module['name'],
        components=snapshot,
        component_counts=snapshot.get('component_counts', {})
    )
