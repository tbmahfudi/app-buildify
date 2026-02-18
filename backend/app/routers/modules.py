"""
Module Management API Endpoints

Provides REST API for managing modules:
- List available modules
- Install/uninstall modules (admin only)
- Enable/disable modules per tenant
- Get module information
- Update module configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user, require_superuser
from app.core.module_system.registry import ModuleRegistryService
from app.core.audit import create_audit_log
from app.models.user import User
from app.models.module_registry import ModuleRegistry, TenantModule
from app.schemas.module import (
    ModuleListItem,
    ModuleInfo,
    ModuleInstallRequest,
    ModuleUninstallRequest,
    ModuleEnableRequest,
    ModuleDisableRequest,
    ModuleConfigurationUpdate,
    ModuleOperationResponse,
    AvailableModulesResponse,
    EnabledModulesResponse,
    AllTenantsModulesResponse,
    TenantModuleInfo,
    TenantModuleInfoWithTenant,
    ModuleManifest,
    ModuleRegistrationRequest,
    ModuleRegistrationResponse,
    ModuleHeartbeatRequest,
    ModuleHeartbeatResponse,
)
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/module-registry", tags=["module-registry"])

# Global module registry service instance
# This will be initialized in main.py
module_registry: ModuleRegistryService = None


def get_module_registry() -> ModuleRegistryService:
    """Get the global module registry service"""
    if module_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Module system not initialized"
        )
    return module_registry


@router.get("/available", response_model=AvailableModulesResponse)
async def list_available_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all available modules with their installation status.

    Returns:
        List of modules with basic information
    """
    modules = db.query(ModuleRegistry).all()

    return AvailableModulesResponse(
        modules=[
            ModuleListItem(
                name=m.name,
                display_name=m.display_name,
                version=m.version,
                description=m.description,
                category=m.category,
                is_installed=m.is_installed,
                is_core=m.is_core,
                subscription_tier=m.subscription_tier,
                status=m.status,
            )
            for m in modules
        ],
        total=len(modules)
    )


@router.get("/enabled", response_model=EnabledModulesResponse)
async def list_enabled_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List modules enabled for the current user's tenant.

    Returns:
        List of enabled modules with configuration
    """
    tenant_modules = db.query(TenantModule).join(ModuleRegistry).filter(
        TenantModule.tenant_id == current_user.tenant_id,
        TenantModule.is_enabled == True,
        ModuleRegistry.is_installed == True
    ).all()

    return EnabledModulesResponse(
        modules=[
            TenantModuleInfo(
                module_name=tm.module.name,
                display_name=tm.module.display_name,
                version=tm.module.version,
                is_enabled=tm.is_enabled,
                is_configured=tm.is_configured,
                configuration=tm.configuration,
                enabled_at=tm.enabled_at,
                last_used_at=tm.last_used_at,
            )
            for tm in tenant_modules
        ],
        total=len(tenant_modules)
    )


@router.get("/enabled/names", response_model=List[str])
async def list_enabled_module_names(
    current_user: User = Depends(get_current_user),
    registry: ModuleRegistryService = Depends(get_module_registry)
):
    """
    Get list of enabled module names for current tenant.

    Useful for frontend to know which modules to load.

    Returns:
        List of module names
    """
    return registry.get_enabled_modules_for_tenant(current_user.tenant_id)


@router.get("/enabled/all-tenants", response_model=AllTenantsModulesResponse)
async def list_all_tenants_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """
    List all enabled modules across all tenants (superuser only).

    This endpoint is useful for system administrators to see which modules
    are enabled for which tenants.

    Returns:
        List of enabled modules with tenant information
    """
    from app.models.tenant import Tenant

    # Get all enabled modules with tenant information
    tenant_modules = db.query(TenantModule, Tenant).join(
        ModuleRegistry, TenantModule.module_id == ModuleRegistry.id
    ).join(
        Tenant, TenantModule.tenant_id == Tenant.id
    ).filter(
        TenantModule.is_enabled == True,
        ModuleRegistry.is_installed == True
    ).all()

    return AllTenantsModulesResponse(
        modules=[
            TenantModuleInfoWithTenant(
                module_name=tm.module.name,
                display_name=tm.module.display_name,
                version=tm.module.version,
                is_enabled=tm.is_enabled,
                is_configured=tm.is_configured,
                configuration=tm.configuration,
                enabled_at=tm.enabled_at,
                last_used_at=tm.last_used_at,
                tenant_id=str(tenant.id),
                tenant_name=tenant.name,
                tenant_code=tenant.code
            )
            for tm, tenant in tenant_modules
        ],
        total=len(tenant_modules)
    )


@router.get("/{module_name}", response_model=ModuleInfo)
async def get_module_info(
    module_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific module.

    Args:
        module_name: Name of the module

    Returns:
        Detailed module information
    """
    module = db.query(ModuleRegistry).filter(
        ModuleRegistry.name == module_name
    ).first()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_name}' not found"
        )

    return ModuleInfo(
        name=module.name,
        display_name=module.display_name,
        version=module.version,
        description=module.description,
        category=module.category,
        tags=module.tags,
        author=module.author,
        license=module.license,
        is_installed=module.is_installed,
        is_core=module.is_core,
        subscription_tier=module.subscription_tier,
        dependencies=module.dependencies_json,
        status=module.status,
        homepage=module.homepage,
        repository=module.repository,
        support_email=module.support_email,
    )


@router.get("/{module_name}/manifest")
async def get_module_manifest(
    module_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full manifest for a module.

    Fetches the manifest directly from the module's backend service
    to ensure we always get the latest version.

    Args:
        module_name: Name of the module

    Returns:
        Full module manifest
    """
    import httpx

    module = db.query(ModuleRegistry).filter(
        ModuleRegistry.name == module_name
    ).first()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_name}' not found"
        )

    # Get backend service URL from module's manifest (stored in database)
    backend_service_url = None
    if module.manifest and isinstance(module.manifest, dict):
        backend_service_url = module.manifest.get('backend_service_url')

    # Try to fetch manifest from module backend service if URL is available
    if backend_service_url:
        manifest_url = f"{backend_service_url}/manifest"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(manifest_url)

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(
                        f"Failed to fetch manifest from {manifest_url}: {response.status_code}"
                    )
        except Exception as e:
            logger.warning(f"Error fetching manifest from module service: {e}")
    else:
        logger.warning(f"No backend_service_url found in manifest for module '{module_name}'")

    # Fallback to database if module service is unavailable
    if module.manifest:
        return module.manifest

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Module manifest not available for '{module_name}'"
    )


@router.post("/install", response_model=ModuleOperationResponse)
async def install_module(
    request_data: ModuleInstallRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
    registry: ModuleRegistryService = Depends(get_module_registry)
):
    """
    Install a module platform-wide.

    Requires superuser permissions.

    Args:
        request_data: Module installation request

    Returns:
        Operation result
    """
    success, error = registry.install_module(request_data.module_name, current_user.id)

    if not success:
        # Audit failed installation
        create_audit_log(
            db=db,
            action="module_install",
            user=current_user,
            entity_type="module",
            entity_id=request_data.module_name,
            request=http_request,
            status="failure",
            error_message=error
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Audit successful installation
    create_audit_log(
        db=db,
        action="module_install",
        user=current_user,
        entity_type="module",
        entity_id=request_data.module_name,
        request=http_request,
        status="success"
    )

    return ModuleOperationResponse(
        success=True,
        message=f"Module '{request_data.module_name}' installed successfully",
        module_name=request_data.module_name
    )


@router.post("/uninstall", response_model=ModuleOperationResponse)
async def uninstall_module(
    request_data: ModuleUninstallRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
    registry: ModuleRegistryService = Depends(get_module_registry)
):
    """
    Uninstall a module platform-wide.

    Requires superuser permissions.

    Args:
        request_data: Module uninstallation request

    Returns:
        Operation result
    """
    success, error = registry.uninstall_module(request_data.module_name)

    if not success:
        # Audit failed uninstallation
        create_audit_log(
            db=db,
            action="module_uninstall",
            user=current_user,
            entity_type="module",
            entity_id=request_data.module_name,
            request=http_request,
            status="failure",
            error_message=error
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Audit successful uninstallation
    create_audit_log(
        db=db,
        action="module_uninstall",
        user=current_user,
        entity_type="module",
        entity_id=request_data.module_name,
        request=http_request,
        status="success"
    )

    return ModuleOperationResponse(
        success=True,
        message=f"Module '{request_data.module_name}' uninstalled successfully",
        module_name=request_data.module_name
    )


@router.post("/enable", response_model=ModuleOperationResponse)
async def enable_module(
    request_data: ModuleEnableRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    registry: ModuleRegistryService = Depends(get_module_registry)
):
    """
    Enable a module for a tenant.

    If tenant_id is provided in request, it will be used (superuser only).
    Otherwise, module will be enabled for current user's tenant.

    Args:
        request_data: Module enable request with optional tenant_id and configuration

    Returns:
        Operation result
    """
    # Determine which tenant to enable for
    target_tenant_id = request_data.tenant_id

    # If tenant_id is provided and differs from current user's tenant
    if target_tenant_id and target_tenant_id != current_user.tenant_id:
        # Only superusers can enable modules for other tenants
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can enable modules for other tenants"
            )
    else:
        # Use current user's tenant
        target_tenant_id = current_user.tenant_id

    # Verify tenant exists if enabling for a different tenant
    if target_tenant_id != current_user.tenant_id:
        from app.models.tenant import Tenant
        tenant = db.query(Tenant).filter(Tenant.id == target_tenant_id).first()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with ID '{target_tenant_id}' not found"
            )

    success, error = registry.enable_module_for_tenant(
        request_data.module_name,
        target_tenant_id,
        current_user.id,
        request_data.configuration
    )

    if not success:
        # Audit failed enable
        create_audit_log(
            db=db,
            action="module_enable",
            user=current_user,
            entity_type="module",
            entity_id=request_data.module_name,
            context_info={"tenant_id": target_tenant_id},
            request=http_request,
            status="failure",
            error_message=error
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Audit successful enable
    create_audit_log(
        db=db,
        action="module_enable",
        user=current_user,
        entity_type="module",
        entity_id=request_data.module_name,
        context_info={"tenant_id": target_tenant_id},
        request=http_request,
        status="success"
    )

    return ModuleOperationResponse(
        success=True,
        message=f"Module '{request_data.module_name}' enabled for tenant",
        module_name=request_data.module_name
    )


@router.post("/disable", response_model=ModuleOperationResponse)
async def disable_module(
    request_data: ModuleDisableRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    registry: ModuleRegistryService = Depends(get_module_registry)
):
    """
    Disable a module for current tenant.

    Args:
        request_data: Module disable request

    Returns:
        Operation result
    """
    # TODO: Add permission check

    success, error = registry.disable_module_for_tenant(
        request_data.module_name,
        current_user.tenant_id,
        current_user.id
    )

    if not success:
        # Audit failed disable
        create_audit_log(
            db=db,
            action="module_disable",
            user=current_user,
            entity_type="module",
            entity_id=request_data.module_name,
            context_info={"tenant_id": current_user.tenant_id},
            request=http_request,
            status="failure",
            error_message=error
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Audit successful disable
    create_audit_log(
        db=db,
        action="module_disable",
        user=current_user,
        entity_type="module",
        entity_id=request_data.module_name,
        context_info={"tenant_id": current_user.tenant_id},
        request=http_request,
        status="success"
    )

    return ModuleOperationResponse(
        success=True,
        message=f"Module '{request_data.module_name}' disabled for tenant",
        module_name=request_data.module_name
    )


@router.put("/{module_name}/configuration", response_model=ModuleOperationResponse)
async def update_module_configuration(
    module_name: str,
    request: ModuleConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    registry: ModuleRegistryService = Depends(get_module_registry)
):
    """
    Update module configuration for current tenant.

    Args:
        module_name: Name of the module
        request: New configuration values

    Returns:
        Operation result
    """
    # Get module
    module_entry = db.query(ModuleRegistry).filter(
        ModuleRegistry.name == module_name
    ).first()

    if not module_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_name}' not found"
        )

    # Get tenant module
    tenant_module = db.query(TenantModule).filter(
        TenantModule.tenant_id == current_user.tenant_id,
        TenantModule.module_id == module_entry.id
    ).first()

    if not tenant_module or not tenant_module.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Module '{module_name}' is not enabled for this tenant"
        )

    # Validate configuration
    module_instance = registry.loader.get_module(module_name)
    if module_instance:
        is_valid, error = module_instance.validate_configuration(request.configuration)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid configuration: {error}"
            )

    # Update configuration
    tenant_module.configuration = request.configuration
    tenant_module.is_configured = True
    db.commit()

    return ModuleOperationResponse(
        success=True,
        message=f"Configuration updated for module '{module_name}'",
        module_name=module_name
    )


@router.post("/register", response_model=ModuleRegistrationResponse)
async def register_module(
    request_data: ModuleRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a module with the core platform.

    This endpoint is called by modules during their startup to register
    themselves with the core platform. The module sends its manifest and
    service URLs, and the core platform stores this information in the database.

    This endpoint does NOT require authentication as it's called during
    module startup before any user authentication is available.

    Args:
        request_data: Module registration request with manifest and service URLs

    Returns:
        Registration response with success status
    """
    from datetime import datetime

    try:
        # Extract module information from manifest
        manifest = request_data.manifest
        module_name = manifest.get('name')

        if not module_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Module manifest must contain 'name' field"
            )

        # Add backend_service_url to manifest if not present
        if 'backend_service_url' not in manifest:
            manifest['backend_service_url'] = request_data.backend_service_url

        # Check if module already exists
        existing_module = db.query(ModuleRegistry).filter(
            ModuleRegistry.name == module_name
        ).first()

        if existing_module:
            # Update existing module
            existing_module.display_name = manifest.get('display_name', module_name)
            existing_module.version = manifest.get('version', '1.0.0')
            existing_module.description = manifest.get('description')
            existing_module.category = manifest.get('category')
            existing_module.tags = manifest.get('tags')
            existing_module.author = manifest.get('author')
            existing_module.license = manifest.get('license')
            existing_module.manifest = manifest
            existing_module.dependencies_json = manifest.get('dependencies')
            existing_module.subscription_tier = manifest.get('subscription_tier')
            existing_module.api_prefix = manifest.get('api', {}).get('prefix')
            existing_module.status = manifest.get('status', 'available')
            existing_module.homepage = manifest.get('homepage')
            existing_module.repository = manifest.get('repository')
            existing_module.support_email = manifest.get('support_email')
            existing_module.updated_at = datetime.utcnow()

            # Mark as installed if not already
            if not existing_module.is_installed:
                existing_module.is_installed = True
                existing_module.installed_at = datetime.utcnow()

            db.commit()
            db.refresh(existing_module)

            logger.info(f"Module '{module_name}' re-registered and updated")

            return ModuleRegistrationResponse(
                success=True,
                message=f"Module '{module_name}' re-registered successfully",
                module_name=module_name,
                registered_at=datetime.utcnow(),
                should_install=False
            )
        else:
            # Create new module entry
            from app.models.base import generate_uuid

            new_module = ModuleRegistry(
                id=generate_uuid(),
                name=module_name,
                display_name=manifest.get('display_name', module_name),
                module_type='code',
                version=manifest.get('version', '1.0.0'),
                description=manifest.get('description'),
                category=manifest.get('category'),
                tags=manifest.get('tags'),
                author=manifest.get('author'),
                license=manifest.get('license'),
                is_installed=True,
                is_core=manifest.get('is_core', False),
                installed_at=datetime.utcnow(),
                manifest=manifest,
                configuration=manifest.get('configuration'),
                dependencies_json=manifest.get('dependencies'),
                subscription_tier=manifest.get('subscription_tier'),
                api_prefix=manifest.get('api', {}).get('prefix'),
                status=manifest.get('status', 'available'),
                homepage=manifest.get('homepage'),
                repository=manifest.get('repository'),
                support_email=manifest.get('support_email')
            )

            db.add(new_module)
            db.commit()
            db.refresh(new_module)

            logger.info(f"Module '{module_name}' registered successfully (new)")

            return ModuleRegistrationResponse(
                success=True,
                message=f"Module '{module_name}' registered successfully",
                module_name=module_name,
                registered_at=datetime.utcnow(),
                should_install=True
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering module: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering module: {str(e)}"
        )


@router.post("/{module_name}/heartbeat", response_model=ModuleHeartbeatResponse)
async def module_heartbeat(
    module_name: str,
    request_data: ModuleHeartbeatRequest,
    db: Session = Depends(get_db)
):
    """
    Receive heartbeat from a module.

    Modules can optionally send periodic heartbeats to indicate they are
    still running and healthy. This updates the module's last_seen timestamp.

    This endpoint does NOT require authentication.

    Args:
        module_name: Name of the module sending heartbeat
        request_data: Heartbeat data

    Returns:
        Heartbeat acknowledgment
    """
    from datetime import datetime

    try:
        module = db.query(ModuleRegistry).filter(
            ModuleRegistry.name == module_name
        ).first()

        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module '{module_name}' not found"
            )

        # Update last seen timestamp
        module.updated_at = datetime.utcnow()

        # Update version if changed
        if request_data.version and request_data.version != module.version:
            logger.info(f"Module '{module_name}' version changed: {module.version} -> {request_data.version}")
            module.version = request_data.version

        # Update status if provided
        if request_data.status:
            module.status = request_data.status

        db.commit()

        return ModuleHeartbeatResponse(
            success=True,
            message="Heartbeat received",
            last_seen=module.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing heartbeat from '{module_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing heartbeat: {str(e)}"
        )


@router.post("/sync", response_model=ModuleOperationResponse)
async def sync_modules(
    current_user: User = Depends(require_superuser),
    registry: ModuleRegistryService = Depends(get_module_registry)
):
    """
    Sync modules from filesystem with database.

    Discovers new modules and updates existing ones.
    Requires superuser permissions.

    Returns:
        Operation result
    """
    try:
        registry.sync_modules()
        return ModuleOperationResponse(
            success=True,
            message="Modules synced successfully"
        )
    except Exception as e:
        logger.error(f"Error syncing modules: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing modules: {str(e)}"
        )
