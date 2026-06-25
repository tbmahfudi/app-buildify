"""
Module Management API Endpoints

Provides REST API for managing modules:
- List available modules
- Install/uninstall modules (admin only)
- Enable/disable modules per tenant
- Get module information
- Update module configuration
"""

from fastapi import APIRouter, Depends, HTTPException, Header, status, Request
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
    ActivationPreviewPermission,
    ActivationPreviewMenuItem,
    ActivationPreviewDependency,
    ActivationPreviewResponse,
    ModuleListItemV2,
    ModulesListResponse,
    ModuleEnableResponse,
    ModuleDisableResponse,
    ModuleDeactivateAllResponse,
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
            detail={"code": "service_unavailable", "message": "Module system not initialized", "detail": None}
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
        TenantModule.tenant_id == current_user.tenant_id,  # tenant_scope
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
        Tenant, TenantModule.tenant_id == Tenant.id  # tenant_scope
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
            detail={"code": "not_found", "message": f"Module '{module_name}' not found", "detail": None}
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
            detail={"code": "not_found", "message": f"Module '{module_name}' not found", "detail": None}
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
        detail={"code": "service_unavailable", "message": f"Module manifest not available for '{module_name}'", "detail": None}
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
            detail={"code": "module_install_error", "message": error, "detail": None}
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
            detail={"code": "module_uninstall_error", "message": error, "detail": None}
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
                detail={"code": "module_enable_error", "message": "Only superusers can enable modules for other tenants", "detail": None}
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
                detail={"code": "not_found", "message": f"Tenant with ID '{target_tenant_id}' not found", "detail": None}
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
            detail={"code": "module_enable_error", "message": error, "detail": None}
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

    # T-23.014: call post_enable hook after ModuleActivation is created
    module_name = request_data.module_name
    try:
        _loader = registry.loader
        _instance = _loader.get_module(module_name) or _loader.load_module(module_name)
        if _instance is not None:
            _instance.post_enable(db, target_tenant_id)
            logger.info(f"post_enable hook completed for '{module_name}' tenant={target_tenant_id}")
    except Exception as _hook_err:
        logger.warning(
            f"post_enable hook failed for '{module_name}': {_hook_err}",
            exc_info=True,
        )
        create_audit_log(
            db=db,
            action="module_hook_failure",
            user=current_user,
            entity_type="module",
            entity_id=request_data.module_name,
            context_info={"hook": "post_enable", "error": str(_hook_err)},
            request=http_request,
            status="failure",
        )
        # do NOT raise — hook failure is non-fatal per T-23.014

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
            detail={"code": "module_disable_error", "message": error, "detail": None}
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
            detail={"code": "not_found", "message": f"Module '{module_name}' not found", "detail": None}
        )

    # Get tenant module
    tenant_module = db.query(TenantModule).filter(
        TenantModule.tenant_id == current_user.tenant_id,  # tenant_scope
        TenantModule.module_id == module_entry.id
    ).first()

    if not tenant_module or not tenant_module.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "module_configure_error", "message": f"Module '{module_name}' is not enabled for this tenant", "detail": None}
        )

    # Validate configuration
    module_instance = registry.loader.get_module(module_name)
    if module_instance:
        is_valid, error = module_instance.validate_configuration(request.configuration)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "module_configure_error", "message": f"Invalid configuration: {error}", "detail": None}
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
                detail={"code": "module_register_error", "message": "Module manifest must contain 'name' field", "detail": None}
            )

        # T-23.007: validate manifest against JSON Schema before registration
        try:
            from app.core.module_system.loader import ModuleLoader
            from pathlib import Path as _Path
            _loader = ModuleLoader(_Path("/tmp"))
            _ok, _err = _loader.validate_manifest(manifest)
            if not _ok:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "code": "manifest_invalid",
                        "message": "Manifest validation failed",
                        "detail": {"errors": [_err]},
                    },
                )
        except HTTPException:
            raise
        except Exception as _ve:
            logger.warning(f"Manifest schema validation error: {_ve}")

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

            # T-23.014: call post_install hook if a BaseModule class exists
            try:
                import importlib, sys as _sys
                from pathlib import Path as _Path
                from app.core.module_system.loader import ModuleLoader
                _modules_root = _Path(__file__).parent.parent.parent / "modules"
                _loader = ModuleLoader(_modules_root)
                _instance = _loader.load_module(module_name)
                if _instance is not None:
                    _instance.post_install(db)
                    logger.info(f"post_install hook completed for '{module_name}'")
            except Exception as _hook_err:
                logger.warning(
                    f"post_install hook failed for '{module_name}': {_hook_err}",
                    exc_info=True,
                )
                # log but do NOT roll back — hook failure is non-fatal per T-23.014

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
            detail={"code": "module_register_error", "message": f"Error registering module: {str(e)}", "detail": None}
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
                detail={"code": "not_found", "message": f"Module '{module_name}' not found", "detail": None}
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
            detail={"code": "module_heartbeat_error", "message": f"Error processing heartbeat: {str(e)}", "detail": None}
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
            detail={"code": "module_sync_error", "message": f"Error syncing modules: {str(e)}", "detail": None}
        )


# ── Epic 22.4.2 — provisioning-status endpoint ─────────────────────────────
# Uses a separate router prefix to match /api/v1/modules/{module_id}/...
_modules_v1_router = APIRouter(prefix="/api/v1/modules", tags=["modules-v1"])


@_modules_v1_router.get("/{module_id}/provisioning-status")
async def get_provisioning_status(
    module_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the provisioning status of a per-tenant module DB.

    Story 22.4.2 — polled by the frontend badge after module enable.
    """
    try:
        result = db.execute(
            __import__('sqlalchemy').text(
                "SELECT status, db_name, error_message "
                "FROM tenant_module_databases "
                "WHERE tenant_id = :tenant_id AND module_id = :module_id "
                "LIMIT 1"
            ),
            {"tenant_id": str(current_user.tenant_id), "module_id": module_id},
        ).fetchone()
    except Exception as exc:
        logger.warning(f"provisioning-status query failed: {exc}")
        result = None

    if result is None:
        return {"status": "not_provisioned", "db_name": None, "error_message": None}

    return {
        "status": result[0],
        "db_name": result[1],
        "error_message": result[2],
    }



@_modules_v1_router.get(
    "/{module_id}/activation-preview",
    response_model=ActivationPreviewResponse,
    summary="Get activation preview for a module",
    tags=["modules-v1"],
)
async def get_activation_preview(
    module_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return a preview of what will happen when a tenant activates a module:
    the permissions it will gain, the menu items that will appear, and
    the status of each dependency for the requesting tenant.

    T-23.002 — Story 23.1.1 backend AC.
    """
    # 1. Look up the module by UUID
    module = db.query(ModuleRegistry).filter(ModuleRegistry.id == module_id).first()
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Module '{module_id}' not found", "detail": None},
        )

    manifest: dict = module.manifest or {}

    # 2. Extract permissions
    raw_permissions = manifest.get("permissions") or []
    permissions = [
        ActivationPreviewPermission(
            name=str(p.get("code") or p.get("name") or ""),
            description=p.get("description"),
            resource=p.get("resource"),
            action=p.get("action"),
        )
        for p in raw_permissions
        if isinstance(p, dict)
    ]

    # 3. Extract menu items (try menu_items then routes)
    raw_menu = manifest.get("menu_items") or manifest.get("routes") or []
    menu_items = [
        ActivationPreviewMenuItem(
            label=str(m.get("label") or m.get("name") or m.get("title") or ""),
            route=m.get("route") or m.get("path"),
            icon=m.get("icon"),
        )
        for m in raw_menu
        if isinstance(m, dict)
    ]

    # 4. Resolve dependency status against requesting tenant
    raw_deps = manifest.get("dependencies") or []
    # dependencies_json may be a dict {"required": [...], "optional": [...]}
    # or a plain list — normalise to a flat list of strings/dicts
    if isinstance(raw_deps, dict):
        dep_list = raw_deps.get("required", []) + raw_deps.get("optional", [])
    else:
        dep_list = list(raw_deps)

    dependencies = []
    for dep in dep_list:
        if isinstance(dep, dict):
            dep_name = dep.get("name") or dep.get("module") or ""
            required_version = dep.get("version")
        else:
            dep_name = str(dep)
            required_version = None

        if not dep_name:
            continue

        # Resolve the dependency's ModuleRegistry row (by name)
        dep_module = db.query(ModuleRegistry).filter(ModuleRegistry.name == dep_name).first()

        if dep_module is None:
            dep_status = "not_installed"
            dep_display = dep_name
        else:
            # Check if a TenantModule activation exists for this tenant
            activation = db.query(TenantModule).filter(
                TenantModule.module_id == dep_module.id,
                TenantModule.tenant_id == current_user.tenant_id,
                TenantModule.is_enabled == True,
            ).first()
            dep_status = "active" if activation is not None else "inactive"
            dep_display = dep_module.display_name or dep_name

        dependencies.append(
            ActivationPreviewDependency(
                name=dep_name,
                display_name=dep_display,
                status=dep_status,
                required_version=required_version,
            )
        )

    return ActivationPreviewResponse(
        module_name=module.name,
        display_name=module.display_name or module.name,
        permissions=permissions,
        menu_items=menu_items,
        dependencies=dependencies,
    )


@_modules_v1_router.post(
    "/validate",
    summary="Dry-run manifest validation (no DB write)",
    tags=["modules-v1"],
)
async def validate_manifest_endpoint(
    request_data: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Validate a module manifest against the JSON Schema without writing to the database.

    Developers call this before packaging (manage.sh module pack also calls it).

    Body: {"manifest": {...}}

    Returns:
        200 {"valid": true} on success.
        422 {"code": "manifest_invalid", "message": "...", "detail": {"errors": [...]}} on failure.

    T-23.007 — Story 23.2.1 backend AC.
    """
    from app.core.module_system.loader import ModuleLoader
    from pathlib import Path as _Path

    manifest = request_data.get("manifest")
    if manifest is None or not isinstance(manifest, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "manifest_invalid",
                "message": "Request body must contain a 'manifest' key with a dict value",
                "detail": {"errors": ["'manifest' key missing or not an object"]},
            },
        )

    _loader = ModuleLoader(_Path("/tmp"))
    ok, err = _loader.validate_manifest(manifest)

    if ok:
        return {"valid": True}

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "code": "manifest_invalid",
            "message": "Manifest validation failed",
            "detail": {"errors": [err]},
        },
    )


# ── T-23.018 — GET /api/v1/modules — tenant-scoped module list ──────────────

@_modules_v1_router.get(
    "",
    response_model=ModulesListResponse,
    summary="List all ready, tenant-visible modules with per-tenant activation status",
    tags=["modules-v1"],
)
async def list_modules_v1(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all modules where ``install_status='ready'`` AND
    ``visibility='all_tenants'``, augmented with the requesting tenant's
    ``activation_status`` derived from the ``module_activations`` table.

    ``activation_status`` is ``"active"`` when a ``ModuleActivation`` row
    exists for ``(module_id, tenant_id)`` with ``is_enabled=True``, otherwise
    ``"inactive"``.

    T-23.018 — Story 23.4.1 backend AC.
    """
    # 1. Fetch candidate modules
    modules = (
        db.query(ModuleRegistry)
        .filter(
            ModuleRegistry.install_status == "ready",
            ModuleRegistry.visibility == "all_tenants",
        )
        .all()
    )

    if not modules:
        return ModulesListResponse(modules=[], total=0)

    # 2. Bulk-fetch all activations for the requesting tenant in one query
    module_ids = [m.id for m in modules]
    activations = (
        db.query(TenantModule.module_id)
        .filter(
            TenantModule.module_id.in_(module_ids),
            TenantModule.tenant_id == current_user.tenant_id,
            TenantModule.is_enabled == True,
        )
        .all()
    )
    active_ids = {row[0] for row in activations}

    # 3. Build response items
    items: List[ModuleListItemV2] = []
    for m in modules:
        manifest: dict = m.manifest or {}
        permissions_added = manifest.get("permissions") or []
        menu_items_added = manifest.get("menu_items") or manifest.get("routes") or []
        raw_deps = manifest.get("dependencies") or m.dependencies_json or []
        if isinstance(raw_deps, dict):
            dep_list = raw_deps.get("required", []) + raw_deps.get("optional", [])
        else:
            dep_list = list(raw_deps)

        items.append(
            ModuleListItemV2(
                id=str(m.id),
                name=m.name,
                display_name=m.display_name or m.name,
                description=m.description,
                version=m.version,
                category=m.category,
                status=m.status,
                is_core=m.is_core,
                install_status=m.install_status,
                activation_status="active" if m.id in active_ids else "inactive",
                permissions_added=permissions_added,
                menu_items_added=menu_items_added,
                dependencies=dep_list,
            )
        )

    return ModulesListResponse(modules=items, total=len(items))


# ── T-23.020 — POST /api/v1/modules/{module_id}/enable ──────────────────────

@_modules_v1_router.post(
    "/{module_id}/enable",
    response_model=ModuleEnableResponse,
    summary="Enable a module for the requesting tenant",
    tags=["modules-v1"],
    status_code=200,
)
async def enable_module_v1(
    module_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enable a module for the current tenant.

    Steps:
    1. 404 if module not found.
    2. Permission check — superusers bypass; others need is_tenant_admin or
       the modules:enable:tenant permission on any assigned role.
    3. Dependency check — 409 deps-unmet if any required dep is inactive.
    4. Create / update ModuleActivation row (is_enabled=True).
    5. Merge manifest menu_items into tenant menu_items table.
    6. Seed manifest permissions into permissions table (upsert, is_active=True).
    7. Audit log module.enabled.
    8. Call post_enable(db, tenant_id) hook (non-fatal).

    Returns {status, permissions_added, menu_items_added}.

    T-23.020 -- Story 23.4.2 backend AC.
    """
    from uuid import UUID
    from datetime import datetime, timezone
    from app.models.nocode_module import Module, ModuleActivation, ModuleDependency
    from app.models.menu_item import MenuItem
    from app.models.permission import Permission

    # 1. Lookup module
    try:
        module_uuid = UUID(module_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Module '{module_id}' not found", "detail": None},
        )

    module = db.query(Module).filter(Module.id == module_uuid).first()
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Module '{module_id}' not found", "detail": None},
        )

    # 2. Permission check
    if not current_user.is_superuser:
        has_enable_perm = False
        # Shortcut: tenant admin flag
        if getattr(current_user, "is_tenant_admin", False):
            has_enable_perm = True
        # Check via role permissions
        if not has_enable_perm:
            for role in getattr(current_user, "roles", []) or []:
                for rp in getattr(role, "permissions", []) or []:
                    perm = getattr(rp, "permission", rp)
                    if getattr(perm, "code", None) == "modules:enable:tenant":
                        has_enable_perm = True
                        break
                if has_enable_perm:
                    break
        if not has_enable_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "forbidden",
                    "message": "You do not have permission to enable modules",
                    "detail": None,
                },
            )

    tenant_id = current_user.tenant_id

    # 3. Dependency check
    manifest: dict = module.manifest or {}
    manifest_deps = manifest.get("dependencies") or []
    if isinstance(manifest_deps, dict):
        manifest_deps = manifest_deps.get("required", [])

    structured_deps = (
        db.query(ModuleDependency)
        .filter(
            ModuleDependency.module_id == module_uuid,
            ModuleDependency.dependency_type == "required",
        )
        .all()
    )
    dep_module_ids: set = {d.depends_on_module_id for d in structured_deps}

    manifest_dep_modules: list = []
    if manifest_deps:
        dep_names = [d if isinstance(d, str) else (d.get("name") or "") for d in manifest_deps]
        dep_names = [n for n in dep_names if n]
        if dep_names:
            manifest_dep_modules = db.query(Module).filter(Module.name.in_(dep_names)).all()
            for dm in manifest_dep_modules:
                dep_module_ids.add(dm.id)

    missing = []
    if dep_module_ids:
        active_dep_ids = {
            row[0]
            for row in db.query(ModuleActivation.module_id)
            .filter(
                ModuleActivation.module_id.in_(list(dep_module_ids)),
                ModuleActivation.tenant_id == tenant_id,
                ModuleActivation.is_enabled == True,
            )
            .all()
        }
        for dep in structured_deps:
            if dep.depends_on_module_id not in active_dep_ids:
                dep_mod = dep.depends_on_module
                missing.append({
                    "name": dep_mod.name if dep_mod else str(dep.depends_on_module_id),
                    "id": str(dep.depends_on_module_id),
                })
        manifest_dep_map = {dm.id: dm for dm in manifest_dep_modules}
        for mid, dm in manifest_dep_map.items():
            if mid not in active_dep_ids and not any(m["id"] == str(mid) for m in missing):
                missing.append({"name": dm.name, "id": str(mid)})

    if missing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "dependencies_unmet",
                "message": "Required modules are not active",
                "detail": {"missing": missing},
            },
        )

    # 4. Create / update ModuleActivation
    now = datetime.now(timezone.utc)
    activation = (
        db.query(ModuleActivation)
        .filter(
            ModuleActivation.module_id == module_uuid,
            ModuleActivation.tenant_id == tenant_id,
            ModuleActivation.company_id == None,
            ModuleActivation.branch_id == None,
            ModuleActivation.department_id == None,
        )
        .first()
    )
    if activation is None:
        activation = ModuleActivation(
            module_id=module_uuid,
            tenant_id=tenant_id,
            is_enabled=True,
            enabled_at=now,
            enabled_by_user_id=current_user.id,
        )
        db.add(activation)
    else:
        activation.is_enabled = True
        activation.enabled_at = now
        activation.enabled_by_user_id = current_user.id
        activation.disabled_at = None
        activation.disabled_by_user_id = None

    db.flush()

    # 5. Merge manifest menu_items into tenant menu tree
    raw_menu_items = manifest.get("menu_items") or manifest.get("routes") or []
    menu_items_added: list = []
    try:
        for item in raw_menu_items:
            if not isinstance(item, dict):
                continue
            code = item.get("code") or item.get("id") or item.get("route")
            if not code:
                continue
            tenant_code = f"{module.name}_{code}_{str(tenant_id)[:8]}"
            existing_mi = db.query(MenuItem).filter(MenuItem.code == tenant_code).first()
            if existing_mi is None:
                mi = MenuItem(
                    code=tenant_code,
                    tenant_id=tenant_id,
                    title=item.get("label") or item.get("title") or code,
                    route=item.get("route") or item.get("path"),
                    icon=item.get("icon"),
                    order=item.get("order", 0),
                    module_code=module.name,
                    is_system=False,
                    is_active=True,
                    is_visible=True,
                )
                db.add(mi)
            else:
                existing_mi.is_active = True
            menu_items_added.append(tenant_code)
    except Exception as _mi_err:
        logger.warning(f"[T-23.020] menu_items merge skipped for module '{module.name}': {_mi_err}")

    # 6. Seed RBAC permissions
    raw_perms = manifest.get("permissions") or module.permissions or []
    permissions_added: list = []
    try:
        for perm_def in raw_perms:
            if isinstance(perm_def, str):
                perm_code = perm_def
                parts = perm_code.split(":")
                resource = parts[0] if len(parts) > 0 else perm_code
                action = parts[1] if len(parts) > 1 else "access"
                scope = parts[2] if len(parts) > 2 else "tenant"
                perm_name = perm_code.replace(":", " ").title()
                description = None
                category = module.category
            elif isinstance(perm_def, dict):
                perm_code = perm_def.get("code") or perm_def.get("name") or perm_def.get("id")
                if not perm_code:
                    continue
                parts = perm_code.split(":")
                resource = perm_def.get("resource", parts[0] if parts else perm_code)
                action = perm_def.get("action", parts[1] if len(parts) > 1 else "access")
                scope = perm_def.get("scope", parts[2] if len(parts) > 2 else "tenant")
                perm_name = perm_def.get("name") or perm_code
                description = perm_def.get("description")
                category = perm_def.get("category") or module.category
            else:
                continue

            existing_perm = db.query(Permission).filter(Permission.code == perm_code).first()
            if existing_perm is None:
                perm = Permission(
                    code=perm_code,
                    name=perm_name,
                    description=description,
                    resource=resource,
                    action=action,
                    scope=scope,
                    category=category,
                    is_active=True,
                    is_system=False,
                )
                db.add(perm)
            else:
                existing_perm.is_active = True
            permissions_added.append(perm_code)
    except Exception as _perm_err:
        logger.warning(f"[T-23.020] permission seed skipped for module '{module.name}': {_perm_err}")

    db.commit()

    # 7. Audit log
    create_audit_log(
        db=db,
        action="module.enabled",
        user=current_user,
        entity_type="module",
        entity_id=str(module_uuid),
        context_info={
            "module_name": module.name,
            "tenant_id": str(tenant_id),
            "permissions_added": permissions_added,
            "menu_items_added": menu_items_added,
        },
        request=http_request,
        status="success",
    )

    # 8. post_enable hook (non-fatal)
    try:
        from app.core.module_system.loader import ModuleLoader
        from pathlib import Path as _Path
        _loader = ModuleLoader(_Path("/opt/buildify/modules"))
        _instance = _loader.get_module(module.name) or _loader.load_module(module.name)
        if _instance is not None:
            _instance.post_enable(db, tenant_id)
            logger.info(f"[T-23.020] post_enable hook completed for '{module.name}' tenant={tenant_id}")
    except Exception as _hook_err:
        logger.warning(
            f"[T-23.020] post_enable hook failed for '{module.name}': {_hook_err}",
            exc_info=True,
        )
        create_audit_log(
            db=db,
            action="module_hook_failure",
            user=current_user,
            entity_type="module",
            entity_id=str(module_uuid),
            context_info={"hook": "post_enable", "error": str(_hook_err)},
            request=http_request,
            status="failure",
        )

    return ModuleEnableResponse(
        status="active",
        permissions_added=permissions_added,
        menu_items_added=menu_items_added,
    )


@_modules_v1_router.post(
    "/{module_id}/disable",
    response_model=ModuleDisableResponse,
    summary="Disable a module for the requesting tenant",
    tags=["modules-v1"],
    status_code=200,
)
async def disable_module_v1(
    module_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Disable a module for the current tenant.

    Steps:
    1. 404 if module not found.
    2. Permission check — superusers bypass; others need is_tenant_admin or
       the modules:disable:tenant permission on any assigned role.
    3. Dependents check — 409 dependents-active if any currently active module
       for this tenant lists this module in its manifest.dependencies[].
    4. Set ModuleActivation.is_enabled=False (disabled_at / disabled_by_user_id).
    5. Set MenuItem.is_active=False for all menu items owned by this module.
    6. Set Permission.is_active=False for all RBAC permissions seeded by this module.
    7. Commit all changes.
    8. Audit log module.disabled.

    Returns {status: "inactive", permissions_deactivated, menu_items_deactivated}.

    T-23.022 -- Story 23.4.3 backend AC.
    """
    from uuid import UUID
    from datetime import datetime, timezone
    from app.models.nocode_module import Module, ModuleActivation
    from app.models.menu_item import MenuItem
    from app.models.permission import Permission

    # 1. Lookup module
    try:
        module_uuid = UUID(module_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Module '{module_id}' not found", "detail": None},
        )

    module = db.query(Module).filter(Module.id == module_uuid).first()
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Module '{module_id}' not found", "detail": None},
        )

    # 2. Permission check
    if not current_user.is_superuser:
        has_disable_perm = False
        if getattr(current_user, "is_tenant_admin", False):
            has_disable_perm = True
        if not has_disable_perm:
            for role in getattr(current_user, "roles", []) or []:
                for rp in getattr(role, "permissions", []) or []:
                    perm = getattr(rp, "permission", rp)
                    if getattr(perm, "code", None) == "modules:disable:tenant":
                        has_disable_perm = True
                        break
                if has_disable_perm:
                    break
        if not has_disable_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "forbidden",
                    "message": "You do not have permission to disable modules",
                    "detail": None,
                },
            )

    tenant_id = current_user.tenant_id

    # 3. Dependents check — find other active modules whose manifests list this module as a dependency
    active_activations = (
        db.query(ModuleActivation)
        .filter(
            ModuleActivation.tenant_id == tenant_id,
            ModuleActivation.is_enabled == True,
            ModuleActivation.module_id != module_uuid,
        )
        .all()
    )
    dependents = []
    for act in active_activations:
        other_module = db.query(Module).filter(Module.id == act.module_id).first()
        if other_module is None:
            continue
        other_manifest = other_module.manifest or {}
        other_deps = other_manifest.get("dependencies") or []
        if isinstance(other_deps, dict):
            other_deps = other_deps.get("required", [])
        dep_names = [
            (d if isinstance(d, str) else d.get("name") or "")
            for d in other_deps
        ]
        if module.name in dep_names:
            dependents.append({"name": other_module.name, "id": str(other_module.id)})

    if dependents:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "dependents_active",
                "message": "Other active modules depend on this module",
                "detail": {"dependents": dependents},
            },
        )

    # 4. Set ModuleActivation.is_enabled=False
    now = datetime.now(timezone.utc)
    activation = (
        db.query(ModuleActivation)
        .filter(
            ModuleActivation.module_id == module_uuid,
            ModuleActivation.tenant_id == tenant_id,
            ModuleActivation.company_id == None,
            ModuleActivation.branch_id == None,
            ModuleActivation.department_id == None,
        )
        .first()
    )
    if activation is not None:
        activation.is_enabled = False
        activation.disabled_at = now
        activation.disabled_by_user_id = current_user.id
        activation.enabled_at = None
        activation.enabled_by_user_id = None

    # 5. Deactivate menu items owned by this module for this tenant
    tenant_prefix = f"{module.name}_"
    tenant_suffix = f"_{str(tenant_id)[:8]}"
    menu_items_deactivated: list = []
    try:
        owned_menu_items = (
            db.query(MenuItem)
            .filter(
                MenuItem.tenant_id == tenant_id,
                MenuItem.module_code == module.name,
            )
            .all()
        )
        if not owned_menu_items:
            # Fallback: match by code pattern if module_code column absent / unpopulated
            owned_menu_items = (
                db.query(MenuItem)
                .filter(
                    MenuItem.tenant_id == tenant_id,
                    MenuItem.code.like(f"{module.name}_%"),
                )
                .all()
            )
        for mi in owned_menu_items:
            mi.is_active = False
            menu_items_deactivated.append(mi.code)
    except Exception as _mi_err:
        logger.warning(f"[T-23.022] menu_items deactivation skipped for module '{module.name}': {_mi_err}")

    # 6. Deactivate RBAC permissions seeded by this module
    raw_perms = (module.manifest or {}).get("permissions") or module.permissions or []
    perm_codes = []
    for perm_def in raw_perms:
        if isinstance(perm_def, str):
            perm_codes.append(perm_def)
        elif isinstance(perm_def, dict):
            code = perm_def.get("code") or perm_def.get("name") or perm_def.get("id")
            if code:
                perm_codes.append(code)

    permissions_deactivated: list = []
    try:
        if perm_codes:
            perms_to_deactivate = (
                db.query(Permission)
                .filter(Permission.code.in_(perm_codes))
                .all()
            )
            for p in perms_to_deactivate:
                p.is_active = False
                permissions_deactivated.append(p.code)
    except Exception as _perm_err:
        logger.warning(f"[T-23.022] permission deactivation skipped for module '{module.name}': {_perm_err}")

    # 7. Commit
    db.commit()

    # 8. Audit log
    create_audit_log(
        db=db,
        action="module.disabled",
        user=current_user,
        entity_type="module",
        entity_id=str(module_uuid),
        context_info={
            "module_name": module.name,
            "tenant_id": str(tenant_id),
            "permissions_deactivated": permissions_deactivated,
            "menu_items_deactivated": menu_items_deactivated,
        },
        request=http_request,
        status="success",
    )

    return ModuleDisableResponse(
        status="inactive",
        permissions_deactivated=permissions_deactivated,
        menu_items_deactivated=menu_items_deactivated,
    )


# ---------------------------------------------------------------------------
# T-23.024 — POST /api/v1/modules/admin/{module_id}/deactivate-all
# ---------------------------------------------------------------------------

@_modules_v1_router.post(
    "/admin/{module_id}/deactivate-all",
    response_model=ModuleDeactivateAllResponse,
    summary="Deactivate a module for every tenant (superadmin only)",
    tags=["modules-v1"],
    status_code=200,
)
async def deactivate_module_all_tenants(
    module_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
):
    """
    Superadmin endpoint: disable a module across **all** tenants.

    Steps:
    1. 404 if module not found by UUID.
    2. Superadmin guard (enforced by require_superuser dependency).
    3. Query all ModuleActivation rows for this module where is_enabled=True.
    4. For each: set is_enabled=False, disabled_at=now(),
       write per-tenant audit_log(action="module.disabled",
       context_info={"reason": "deactivate_all"}).
    5. Set Module.install_status='deactivation_pending'.
    6. Commit.
    7. Write summary audit_log(action="module.deactivate_all",
       context_info={"tenants_deactivated": N}).
    8. Return {"status": "deactivation_pending", "tenants_deactivated": N}.

    T-23.024 -- Story 23.5.1 backend AC phase 1.
    """
    from uuid import UUID
    from datetime import datetime, timezone
    from app.models.nocode_module import Module, ModuleActivation

    # 1. Lookup module
    try:
        module_uuid = UUID(module_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Module '{module_id}' not found",
                "detail": None,
            },
        )

    module = db.query(Module).filter(Module.id == module_uuid).first()
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Module '{module_id}' not found",
                "detail": None,
            },
        )

    # 2. Superadmin guard — already enforced by require_superuser dependency above.

    # 3. Fetch all active activations across all tenants for this module
    active_activations = (
        db.query(ModuleActivation)
        .filter(
            ModuleActivation.module_id == module_uuid,
            ModuleActivation.is_enabled == True,
        )
        .all()
    )

    now = datetime.now(timezone.utc)

    # 4. Disable each activation + write per-tenant audit log
    tenants_deactivated = 0
    for activation in active_activations:
        activation.is_enabled = False
        activation.disabled_at = now
        activation.disabled_by_user_id = current_user.id

        create_audit_log(
            db=db,
            action="module.disabled",
            user=current_user,
            entity_type="module",
            entity_id=str(module_uuid),
            context_info={
                "module_name": module.name,
                "tenant_id": str(activation.tenant_id),
                "reason": "deactivate_all",
            },
            request=http_request,
            status="success",
        )
        tenants_deactivated += 1

    # 5. Mark module as deactivation_pending
    module.install_status = "deactivation_pending"

    # 6. Commit all changes
    db.commit()

    # 7. Write summary audit log
    create_audit_log(
        db=db,
        action="module.deactivate_all",
        user=current_user,
        entity_type="module",
        entity_id=str(module_uuid),
        context_info={
            "module_name": module.name,
            "tenants_deactivated": tenants_deactivated,
        },
        request=http_request,
        status="success",
    )

    # 8. Return summary
    return ModuleDeactivateAllResponse(
        status="deactivation_pending",
        tenants_deactivated=tenants_deactivated,
    )


# ---------------------------------------------------------------------------
# T-23.025 — DELETE /api/v1/modules/admin/{module_id}
# ---------------------------------------------------------------------------

@_modules_v1_router.delete(
    "/admin/{module_id}",
    summary="Uninstall a module (superadmin only, X-Confirm-Uninstall: true required)",
    tags=["modules-v1"],
    status_code=204,
)
async def uninstall_module_v1(
    module_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
    x_confirm_uninstall: str = Header(default=None, alias="X-Confirm-Uninstall"),
):
    """
    Hard-delete a module from the platform (superadmin only).

    Guards:
    - Requires X-Confirm-Uninstall: true header.
    - Module must have install_status='deactivation_pending' (set by T-23.024).

    Steps:
    1. Header check: 400 if X-Confirm-Uninstall != 'true'.
    2. 404 if module not found.
    3. State check: 409 if install_status != 'deactivation_pending'.
    4. Epic-22 cleanup stub (no-op — story 22.4.5 not yet merged).
    5. Delete all ModuleActivation rows for this module.
    6. Deactivate all RBAC permissions seeded by this module.
    7. Delete all MenuItem rows with module_code matching this module.
    8. Remove module files via docker exec (non-fatal on failure).
    9. Delete the modules row and commit.
    10. Write audit_log(action='module.uninstalled').

    Returns 204 No Content on success.

    T-23.025 — Story 23.5.1 backend AC phase 2.
    """
    import subprocess
    from uuid import UUID
    from app.models.nocode_module import Module, ModuleActivation
    from app.models.menu_item import MenuItem
    from app.models.permission import Permission

    # 1. Header check
    if x_confirm_uninstall != "true":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "confirm_header_required",
                "message": "X-Confirm-Uninstall: true header is required to uninstall a module",
                "detail": None,
            },
        )

    # 2. Lookup module
    try:
        module_uuid = UUID(module_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Module {module_id} not found", "detail": None},
        )

    module = db.query(Module).filter(Module.id == module_uuid).first()
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Module {module_id} not found", "detail": None},
        )

    # 3. State check — must be deactivation_pending
    if module.install_status != "deactivation_pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "uninstall_not_ready",
                "message": "Module must be deactivated from all tenants first",
                "detail": None,
            },
        )

    module_name = module.name

    # 4. Epic-22 cleanup stub
    # TODO: Epic-22 cleanup service (story 22.4.5) — call cleanup endpoint here once merged
    logger.info(f"[T-23.025] Epic-22 cleanup service: no-op stub for module {module_name} (22.4.5 not yet merged)")

    # 5. Remove all ModuleActivation rows for this module (including disabled ones)
    activations_to_delete = (
        db.query(ModuleActivation)
        .filter(ModuleActivation.module_id == module_uuid)
        .all()
    )
    activation_count = len(activations_to_delete)
    for act in activations_to_delete:
        db.delete(act)
    db.flush()
    logger.info(f"[T-23.025] Deleted {activation_count} ModuleActivation rows for module {module_name}")

    # 6. Deactivate RBAC permissions seeded by this module
    raw_perms = (module.manifest or {}).get("permissions") or module.permissions or []
    perm_codes = []
    for perm_def in raw_perms:
        if isinstance(perm_def, str):
            perm_codes.append(perm_def)
        elif isinstance(perm_def, dict):
            code = perm_def.get("code") or perm_def.get("name") or perm_def.get("id")
            if code:
                perm_codes.append(code)

    permissions_removed: list = []
    if perm_codes:
        try:
            perms = db.query(Permission).filter(Permission.code.in_(perm_codes)).all()
            for p in perms:
                p.is_active = False
                permissions_removed.append(p.code)
            db.flush()
        except Exception as _perm_err:
            logger.warning(f"[T-23.025] Permission deactivation skipped for module {module_name}: {_perm_err}")

    # 7. Delete MenuItem rows owned by this module (all tenants)
    menu_items_removed: list = []
    try:
        owned_items = (
            db.query(MenuItem)
            .filter(MenuItem.module_code == module_name)
            .all()
        )
        if not owned_items:
            # Fallback: match by code pattern
            owned_items = (
                db.query(MenuItem)
                .filter(MenuItem.code.like(f"{module_name}_%"))
                .all()
            )
        for mi in owned_items:
            menu_items_removed.append(mi.code)
            db.delete(mi)
        db.flush()
        logger.info(f"[T-23.025] Deleted {len(menu_items_removed)} MenuItem rows for module {module_name}")
    except Exception as _mi_err:
        logger.warning(f"[T-23.025] Menu item removal skipped for module {module_name}: {_mi_err}")

    # 8. Remove module files from container (non-fatal)
    try:
        result = subprocess.run(
            ["docker", "exec", "app_buildify_backend", "bash", "-c", f"rm -rf /app/modules/{module_name}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info(f"[T-23.025] Removed module files: /app/modules/{module_name}")
        else:
            logger.warning(
                f"[T-23.025] Failed to remove module files for {module_name}: {result.stderr.strip()}"
            )
    except Exception as _fs_err:
        logger.warning(f"[T-23.025] Module file removal failed for {module_name} (non-fatal): {_fs_err}")

    # 9. Delete modules row
    db.delete(module)
    db.commit()
    logger.info(f"[T-23.025] Module {module_name} ({module_id}) deleted from database")

    # 10. Audit log
    create_audit_log(
        db=db,
        action="module.uninstalled",
        user=current_user,
        entity_type="module",
        entity_id=module_id,
        context_info={
            "module_name": module_name,
            "activations_removed": activation_count,
            "permissions_deactivated": permissions_removed,
            "menu_items_removed": menu_items_removed,
        },
        request=http_request,
        status="success",
    )

    # 204 No Content — FastAPI returns empty body automatically
    return None
