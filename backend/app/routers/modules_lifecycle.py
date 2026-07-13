"""
Module Lifecycle API  — /api/v1/modules

New RESTful endpoints for Epic-23 Module Lifecycle & Activation.
Legacy endpoints remain at /api/v1/module-registry (backward compat).

T-23.002  GET  /{name}/activation-preview
T-23.003  Structured {code, message, detail} error shape on all endpoints here.
T-23.020  POST /{name}/enable      (dep-check, menu merge, RBAC seed — stub until T-23.020)
T-23.022  POST /{name}/disable     (dependents check, menu remove — stub until T-23.022)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import create_audit_log
from app.core.dependencies import get_current_user, get_db, require_superuser
from app.models.menu_item import MenuItem
from app.models.module_registry import ModuleRegistry, TenantModule
from app.models.permission import Permission
from app.models.user import User
from app.schemas.module import (
    ActivationPreviewDependency,
    ActivationPreviewMenuItem,
    ActivationPreviewPermission,
    ActivationPreviewResponse,
    ModuleListItemV2,
    ModuleOperationResponse,
    ModulesListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/modules", tags=["modules"])


def module_error(code: str, message: str, http_status: int = 400, detail=None):
    """Raise a structured {code, message, detail} HTTPException (T-23.003)."""
    raise HTTPException(
        status_code=http_status,
        detail={"code": code, "message": message, "detail": detail},
    )


# ── GET /api/v1/modules ───────────────────────────────────────────────────────


@router.get("", response_model=ModulesListResponse)
async def list_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List installed modules with per-tenant activation status.
    Only returns modules with install_status=ready (or is_installed=True for legacy rows).
    """
    # T-23.018: only show modules that are fully installed and visible to all tenants.
    # NULL install_status = legacy row (pre-migration) — treated as ready.
    from sqlalchemy import or_

    modules = (
        db.query(ModuleRegistry)
        .filter(
            ModuleRegistry.is_installed == True,
            or_(
                ModuleRegistry.install_status == None,
                ModuleRegistry.install_status == "ready",
            ),
        )
        .all()
    )
    # Honour visibility column (Python-side for SQLite compat in tests)
    modules = [m for m in modules if getattr(m, "visibility", "all_tenants") in ("all_tenants", None)]

    # Build a set of enabled module IDs for this tenant
    enabled_ids = {
        tm.module_id
        for tm in db.query(TenantModule)
        .filter(
            TenantModule.tenant_id == current_user.tenant_id,  # tenant_scope
            TenantModule.is_enabled == True,
        )
        .all()
    }

    items = []
    for m in modules:
        items.append(
            ModuleListItemV2(
                name=m.name,
                display_name=m.display_name,
                version=m.version,
                description=m.description,
                category=m.category,
                is_core=m.is_core,
                install_status=getattr(m, "install_status", "ready") or "ready",
                activation_status="active" if m.id in enabled_ids else "inactive",
            )
        )

    return ModulesListResponse(modules=items, total=len(items))


# ── GET /api/v1/modules/{module_name}/activation-preview ─────────────────────


@router.get("/{module_name}/activation-preview", response_model=ActivationPreviewResponse)
async def activation_preview(
    module_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the permissions, menu items, and dependency status that will be
    applied when a tenant activates this module.  Used by ActivationModal (T-23.021).
    """
    module = db.query(ModuleRegistry).filter(ModuleRegistry.name == module_name).first()

    if not module:
        module_error("MODULE_NOT_FOUND", f"Module '{module_name}' is not installed.", 404)

    if not module.is_installed:
        module_error("INSTALL_NOT_READY", f"Module '{module_name}' is not installed.", 400)

    manifest: dict = module.manifest or {}

    # ── Permissions ──────────────────────────────────────────────────────────
    raw_perms = manifest.get("permissions", []) or []
    permissions = [
        ActivationPreviewPermission(
            name=p.get("name", p) if isinstance(p, dict) else str(p),
            description=p.get("description") if isinstance(p, dict) else None,
            resource=p.get("resource") if isinstance(p, dict) else None,
            action=p.get("action") if isinstance(p, dict) else None,
        )
        for p in raw_perms
    ]

    # ── Menu Items ───────────────────────────────────────────────────────────
    frontend_cfg: dict = manifest.get("frontend", {}) or {}
    raw_menu = frontend_cfg.get("menu_items", []) or manifest.get("menu_items", []) or []
    menu_items = [
        ActivationPreviewMenuItem(
            label=item.get("label", "") if isinstance(item, dict) else str(item),
            route=item.get("route") if isinstance(item, dict) else None,
            icon=item.get("icon") if isinstance(item, dict) else None,
        )
        for item in raw_menu
    ]

    # ── Dependencies ─────────────────────────────────────────────────────────
    raw_deps: dict = manifest.get("dependencies", {}) or {}
    # dependencies can be {"required": ["dep_name", ...]} or {"dep_name": ">=1.0"}
    dep_names: list = []
    if isinstance(raw_deps, dict):
        dep_names = list(raw_deps.get("required", raw_deps.keys()))
    elif isinstance(raw_deps, list):
        dep_names = raw_deps

    enabled_names = {
        tm.module.name
        for tm in db.query(TenantModule)
        .filter(
            TenantModule.tenant_id == current_user.tenant_id,  # tenant_scope
            TenantModule.is_enabled == True,
        )
        .all()
        if tm.module
    }

    dependencies = []
    for dep_name in dep_names:
        dep_module = db.query(ModuleRegistry).filter(ModuleRegistry.name == dep_name).first()
        if dep_module is None:
            dep_status = "not_installed"
        elif dep_name in enabled_names:
            dep_status = "active"
        else:
            dep_status = "inactive"

        dependencies.append(
            ActivationPreviewDependency(
                name=dep_name,
                display_name=dep_module.display_name if dep_module else dep_name,
                status=dep_status,
                required_version=raw_deps.get(dep_name) if isinstance(raw_deps, dict) else None,
            )
        )

    return ActivationPreviewResponse(
        module_name=module.name,
        display_name=module.display_name,
        permissions=permissions,
        menu_items=menu_items,
        dependencies=dependencies,
    )


# ── POST /api/v1/modules/{module_name}/enable ─────────────────────────────────


@router.post("/{module_name}/enable", response_model=ModuleOperationResponse)
async def enable_module(
    module_name: str,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Activate a module for the current tenant.
    T-23.020: dep-check 409, merges manifest menu_items into tenant tree, seeds manifest permissions into RBAC.
    """
    module = db.query(ModuleRegistry).filter(ModuleRegistry.name == module_name).first()

    if not module:
        module_error("MODULE_NOT_FOUND", f"Module '{module_name}' is not installed.", 404)

    if not module.is_installed:
        module_error("INSTALL_NOT_READY", f"Module '{module_name}' is not ready to enable.", 400)

    if module.is_core:
        module_error("SYSTEM_MODULE_PROTECTED", f"Core module '{module_name}' cannot be toggled.", 403)

    # Check dependency satisfaction (preview check — full enforcement in T-23.020)
    manifest: dict = module.manifest or {}
    raw_deps = manifest.get("dependencies", {}) or {}
    dep_names = list(raw_deps.get("required", raw_deps.keys())) if isinstance(raw_deps, dict) else raw_deps
    if dep_names:
        enabled_names = {
            tm.module.name
            for tm in db.query(TenantModule)
            .filter(
                TenantModule.tenant_id == current_user.tenant_id,  # tenant_scope
                TenantModule.is_enabled == True,
            )
            .all()
            if tm.module
        }
        unmet = [d for d in dep_names if d not in enabled_names]
        if unmet:
            module_error(
                "DEPS_UNMET",
                f"Activate required modules first: {', '.join(unmet)}",
                409,
                {"unmet_dependencies": unmet},
            )

    # Create or update TenantModule
    from datetime import datetime

    tenant_module = (
        db.query(TenantModule)
        .filter(
            TenantModule.tenant_id == current_user.tenant_id,  # tenant_scope
            TenantModule.module_id == module.id,
        )
        .first()
    )

    if tenant_module:
        if tenant_module.is_enabled:
            module_error("ALREADY_ENABLED", f"Module '{module_name}' is already active.", 409)
        tenant_module.is_enabled = True
        tenant_module.enabled_at = datetime.utcnow()
    else:
        from app.models.base import generate_uuid

        tenant_module = TenantModule(
            id=generate_uuid(),
            tenant_id=current_user.tenant_id,
            module_id=module.id,
            is_enabled=True,
            enabled_at=datetime.utcnow(),
            enabled_by_user_id=current_user.id,
        )
        db.add(tenant_module)

    db.commit()

    # T-23.020: merge manifest menu_items into tenant menu tree
    _manifest: dict = module.manifest or {}
    _frontend_cfg: dict = _manifest.get("frontend", {}) or {}
    _raw_menu = _frontend_cfg.get("menu_items", []) or _manifest.get("menu_items", []) or []
    for _mi in _raw_menu:
        _code = f"mod__{module_name}__{_mi.get('route', _mi.get('label', 'item')).replace('/', '_')}"
        _existing_mi = db.query(MenuItem).filter(MenuItem.code == _code).first()
        if _existing_mi:
            # re-activate if previously deactivated
            _existing_mi.is_active = True
            _existing_mi.tenant_id = current_user.tenant_id
        else:
            from app.models.base import generate_uuid as _gen_uuid

            db.add(
                MenuItem(
                    id=_gen_uuid(),
                    code=_code,
                    tenant_id=current_user.tenant_id,
                    title=_mi.get("label", module.display_name),
                    icon=_mi.get("icon"),
                    route=_mi.get("route"),
                    order=_mi.get("order", 100),
                    permission=_mi.get("permission"),
                    module_code=module_name,
                    is_system=False,
                    is_active=True,
                    is_visible=True,
                )
            )

    # T-23.020: seed manifest permissions into tenant RBAC (upsert, non-fatal)
    try:
        _raw_perms = _manifest.get("permissions", []) or []
        for _perm in _raw_perms:
            _pcode = _perm if isinstance(_perm, str) else _perm.get("code", "")
            if not _pcode:
                continue
            _existing_p = db.query(Permission).filter(Permission.code == _pcode).first()
            if not _existing_p:
                _parts = (_pcode + "::").split(":")
                db.add(
                    Permission(
                        id=_gen_uuid(),
                        code=_pcode,
                        name=_perm.get("name", _pcode) if isinstance(_perm, dict) else _pcode,
                        description=_perm.get("description") if isinstance(_perm, dict) else None,
                        resource=_parts[0] or module_name,
                        action=_parts[1] or "access",
                        scope=_parts[2] or "tenant",
                        category=module_name,
                        is_active=True,
                        is_system=False,
                    )
                )
        db.commit()
    except Exception as _rbac_err:
        logger.warning(f"RBAC seed failed for '{module_name}': {_rbac_err}", exc_info=True)
        db.rollback()

    # T-23.014: call post_enable hook (non-fatal on failure)
    try:
        from pathlib import Path as _Path

        from app.core.module_system.loader import ModuleLoader

        _modules_root = _Path(__file__).parent.parent.parent / "modules"
        _loader = ModuleLoader(_modules_root)
        _instance = _loader.load_module(module_name)
        if _instance is not None:
            _instance.post_enable(db, str(current_user.tenant_id))
            logger.info(f"post_enable hook completed for '{module_name}'")
    except Exception as _hook_err:
        logger.warning(
            f"post_enable hook failed for '{module_name}': {_hook_err}",
            exc_info=True,
        )

    create_audit_log(
        db=db,
        action="module.enabled",
        user=current_user,
        entity_type="module",
        entity_id=module_name,
        context_info={"tenant_id": str(current_user.tenant_id)},
        request=http_request,
        status="success",
    )

    return ModuleOperationResponse(
        success=True,
        message=f"Module '{module_name}' activated.",
        module_name=module_name,
    )


# ── POST /api/v1/modules/{module_name}/disable ────────────────────────────────


@router.post("/{module_name}/disable", response_model=ModuleOperationResponse)
async def disable_module(
    module_name: str,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deactivate a module for the current tenant.
    T-23.022: dependents check 409, removes module menu items, sets module permissions is_active=False.
    """
    module = db.query(ModuleRegistry).filter(ModuleRegistry.name == module_name).first()

    if not module:
        module_error("MODULE_NOT_FOUND", f"Module '{module_name}' is not installed.", 404)

    if module.is_core:
        module_error("SYSTEM_MODULE_PROTECTED", f"Core module '{module_name}' cannot be toggled.", 403)

    tenant_module = (
        db.query(TenantModule)
        .filter(
            TenantModule.tenant_id == current_user.tenant_id,  # tenant_scope
            TenantModule.module_id == module.id,
        )
        .first()
    )

    if not tenant_module or not tenant_module.is_enabled:
        module_error("ALREADY_DISABLED", f"Module '{module_name}' is not active for this tenant.", 409)

    # T-23.022: check whether any active modules depend on this one
    _active_dep_names = []
    _all_tenant_modules = (
        db.query(TenantModule)
        .filter(
            TenantModule.tenant_id == current_user.tenant_id,  # tenant_scope
            TenantModule.is_enabled == True,
            TenantModule.module_id != module.id,
        )
        .all()
    )
    for _tm in _all_tenant_modules:
        _dep_mod = _tm.module
        if _dep_mod is None:
            continue
        _dep_manifest: dict = _dep_mod.manifest or {}
        _raw_req = _dep_manifest.get("dependencies", {}) or {}
        _dep_names = list(_raw_req.get("required", _raw_req.keys())) if isinstance(_raw_req, dict) else _raw_req
        if module_name in _dep_names:
            _active_dep_names.append(_dep_mod.name)
    if _active_dep_names:
        module_error(
            "DEPENDENTS_ACTIVE",
            f"Deactivate dependent modules first: {', '.join(_active_dep_names)}",
            409,
            {"dependents": _active_dep_names},
        )

    from datetime import datetime

    tenant_module.is_enabled = False
    tenant_module.disabled_at = datetime.utcnow()
    tenant_module.disabled_by_user_id = current_user.id
    db.commit()

    # T-23.022: deactivate this module's menu items for the tenant
    try:
        _menu_rows = (
            db.query(MenuItem)
            .filter(
                MenuItem.module_code == module_name,
                MenuItem.tenant_id == current_user.tenant_id,  # tenant_scope
            )
            .all()
        )
        for _row in _menu_rows:
            _row.is_active = False

        # T-23.022: set module permissions inactive
        _manifest_d: dict = module.manifest or {}
        _raw_perms_d = _manifest_d.get("permissions", []) or []
        for _perm_d in _raw_perms_d:
            _pcode_d = _perm_d if isinstance(_perm_d, str) else _perm_d.get("code", "")
            if not _pcode_d:
                continue
            _p = db.query(Permission).filter(Permission.code == _pcode_d).first()
            if _p:
                _p.is_active = False

        db.commit()
    except Exception as _cleanup_err:
        logger.warning(f"Menu/RBAC cleanup failed for '{module_name}': {_cleanup_err}", exc_info=True)
        db.rollback()

    create_audit_log(
        db=db,
        action="module.disabled",
        user=current_user,
        entity_type="module",
        entity_id=module_name,
        context_info={"tenant_id": str(current_user.tenant_id)},
        request=http_request,
        status="success",
    )

    return ModuleOperationResponse(
        success=True,
        message=f"Module '{module_name}' deactivated.",
        module_name=module_name,
    )


# ---------------------------------------------------------------------------
# T-23.007  POST /api/v1/modules/validate  — dry-run manifest validation
# ---------------------------------------------------------------------------

from typing import Optional as _Optional

from pydantic import BaseModel as _BaseModel


class ManifestValidateRequest(_BaseModel):
    manifest: dict


class ManifestValidateResponse(_BaseModel):
    valid: bool
    errors: _Optional[list] = None


@router.post("/validate", response_model=ManifestValidateResponse, tags=["modules"])
def validate_manifest(
    payload: ManifestValidateRequest,
) -> ManifestValidateResponse:
    """
    Dry-run manifest validation — no DB writes.
    Returns 200 {valid:true} or 422 {valid:false, errors:[...]}.
    """
    from pathlib import Path

    from app.core.module_system.loader import ModuleLoader

    loader = ModuleLoader(Path("/tmp"))  # path unused for schema-only validation
    ok, err = loader.validate_manifest(payload.manifest)

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"valid": False, "errors": [err]},
        )

    return ManifestValidateResponse(valid=True)


# ── Admin router: /api/v1/admin/modules ──────────────────────────────────────
# T-23.024  POST /api/v1/admin/modules/{id}/deactivate-all  (superadmin only)
# T-23.025  DELETE /api/v1/admin/modules/{id}               (superadmin only)

admin_router = APIRouter(prefix="/api/v1/admin/modules", tags=["admin-modules"])


@admin_router.post("/{module_id}/deactivate-all", response_model=ModuleOperationResponse)
async def admin_deactivate_all(
    module_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
):
    """
    T-23.024: Deactivate a module for ALL tenants that have it enabled.
    Superadmin only. Sets install_status=deactivation_pending, then disables
    every TenantModule row. Non-fatal per-tenant failures are logged.
    """
    module = (
        db.query(ModuleRegistry)
        .filter(
            ModuleRegistry.id == module_id,
        )
        .first()
    )
    if not module:
        # try by name as fallback
        module = db.query(ModuleRegistry).filter(ModuleRegistry.name == module_id).first()
    if not module:
        module_error("MODULE_NOT_FOUND", f"Module '{module_id}' not found.", 404)

    if module.is_core:
        module_error("SYSTEM_MODULE_PROTECTED", "Core modules cannot be deactivated.", 403)

    # Mark as deactivation_pending
    module.install_status = "deactivation_pending"
    db.commit()

    tenant_modules = (
        db.query(TenantModule)
        .filter(
            TenantModule.module_id == module.id,
            TenantModule.is_enabled == True,
        )
        .all()
    )

    from datetime import datetime

    deactivated = []
    failed = []
    for tm in tenant_modules:
        try:
            # Deactivate menu items for this tenant
            db.query(MenuItem).filter(
                MenuItem.module_code == module.name,
                MenuItem.tenant_id == tm.tenant_id,  # tenant_scope
            ).update({"is_active": False})

            tm.is_enabled = False
            tm.disabled_at = datetime.utcnow()
            tm.disabled_by_user_id = current_user.id
            db.commit()
            deactivated.append(str(tm.tenant_id))
        except Exception as _e:
            logger.warning(f"deactivate-all: tenant {tm.tenant_id} failed: {_e}")
            db.rollback()
            failed.append(str(tm.tenant_id))

    # Deactivate module permissions globally
    try:
        _manifest_da: dict = module.manifest or {}
        for _perm_da in _manifest_da.get("permissions", []) or []:
            _pc = _perm_da if isinstance(_perm_da, str) else _perm_da.get("code", "")
            if _pc:
                _p = db.query(Permission).filter(Permission.code == _pc).first()
                if _p:
                    _p.is_active = False
        db.commit()
    except Exception as _pe:
        logger.warning(f"deactivate-all: permission cleanup failed: {_pe}")
        db.rollback()

    create_audit_log(
        db=db,
        action="module.admin_deactivate_all",
        user=current_user,
        entity_type="module",
        entity_id=module.name,
        context_info={"deactivated_tenants": deactivated, "failed_tenants": failed},
        request=http_request,
        status="success",
    )

    return ModuleOperationResponse(
        success=True,
        message=f"Module '{module.name}' deactivated for {len(deactivated)} tenant(s).",
        module_name=module.name,
    )


@admin_router.delete("/{module_id}", response_model=ModuleOperationResponse)
async def admin_uninstall_module(
    module_id: str,
    http_request: Request,
    x_confirm_uninstall: _Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
):
    """
    T-23.025: Permanently uninstall a module.
    Requires header X-Confirm-Uninstall: true.
    Sets is_installed=False, removes all TenantModule rows, menu items, and module permissions.
    """
    # Check confirmation header
    confirm = http_request.headers.get("x-confirm-uninstall", "")
    if confirm.lower() != "true":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONFIRMATION_REQUIRED", "message": "Send header X-Confirm-Uninstall: true to confirm."},
        )

    module = (
        db.query(ModuleRegistry)
        .filter(
            ModuleRegistry.id == module_id,
        )
        .first()
    )
    if not module:
        module = db.query(ModuleRegistry).filter(ModuleRegistry.name == module_id).first()
    if not module:
        module_error("MODULE_NOT_FOUND", f"Module '{module_id}' not found.", 404)

    if module.is_core:
        module_error("SYSTEM_MODULE_PROTECTED", "Core modules cannot be uninstalled.", 403)

    # Check no tenants have it enabled
    active_count = (
        db.query(TenantModule)
        .filter(
            TenantModule.module_id == module.id,
            TenantModule.is_enabled == True,
        )
        .count()
    )
    if active_count > 0:
        module_error(
            "DEPENDENTS_ACTIVE",
            f"Module is still active for {active_count} tenant(s). Run deactivate-all first.",
            409,
            {"active_tenant_count": active_count},
        )

    # Remove all TenantModule rows
    db.query(TenantModule).filter(TenantModule.module_id == module.id).delete()

    # Remove all menu items created by this module
    db.query(MenuItem).filter(MenuItem.module_code == module.name).delete()

    # Deactivate permissions seeded by this module
    _manifest_ui: dict = module.manifest or {}
    for _perm_ui in _manifest_ui.get("permissions", []) or []:
        _pcu = _perm_ui if isinstance(_perm_ui, str) else _perm_ui.get("code", "")
        if _pcu:
            _pu = db.query(Permission).filter(Permission.code == _pcu).first()
            if _pu and not _pu.is_system:
                db.delete(_pu)

    # Mark module as uninstalled
    module.is_installed = False
    module.install_status = None
    db.commit()

    create_audit_log(
        db=db,
        action="module.uninstalled",
        user=current_user,
        entity_type="module",
        entity_id=module.name,
        context_info={"module_id": str(module.id)},
        request=http_request,
        status="success",
    )

    return ModuleOperationResponse(
        success=True,
        message=f"Module '{module.name}' uninstalled.",
        module_name=module.name,
    )
