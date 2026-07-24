"""ACL & privacy endpoints — mounted at {API_PREFIX}/acls (E3).

Managing privacy/grants requires the resource-type admin permission:
  folder   -> dms:folder:manage:company
  document -> dms:document:delete:company
Checked inside the handler (it varies by the {resource_type} path param).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import Principal, get_principal, tenant_session
from ..models.acl import CAPABILITY_RANK
from ..schemas.acl import (
    AclListResponse,
    AclResponse,
    EffectiveAccessResponse,
    GrantRequest,
    SetPrivacyRequest,
)
from ..services.acl_service import AclError, AclService
from ..services.audit_service import AuditService
from ..services.document_service import DocumentService

router = APIRouter()

_ADMIN_PERM = {"folder": "dms:folder:manage:company", "document": "dms:document:delete:company"}


def _require_admin(principal: Principal, resource_type: str) -> None:
    perm = _ADMIN_PERM.get(resource_type)
    if perm is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid resource type")
    if not principal.has_permission(perm):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, f"Missing required permission: {perm}"
        )


@router.put("/{resource_type}/{resource_id}/privacy", status_code=status.HTTP_204_NO_CONTENT)
async def set_privacy(
    resource_type: str,
    resource_id: str,
    body: SetPrivacyRequest,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(tenant_session),
):
    _require_admin(principal, resource_type)
    try:
        await AclService.set_privacy(
            db, tenant_id=principal.tenant_id, resource_type=resource_type,
            resource_id=resource_id, is_private=body.is_private,
        )
    except AclError as e:
        raise HTTPException(e.status_code, str(e))
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="acl.privacy", entity_type=resource_type, entity_id=str(resource_id),
        detail={"is_private": body.is_private},
    )


@router.post("/{resource_type}/{resource_id}/grants", response_model=AclResponse,
             status_code=status.HTTP_201_CREATED)
async def grant(
    resource_type: str,
    resource_id: str,
    body: GrantRequest,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(tenant_session),
):
    _require_admin(principal, resource_type)
    try:
        acl = await AclService.grant(
            db, tenant_id=principal.tenant_id, created_by=principal.user_id,
            resource_type=resource_type, resource_id=resource_id,
            principal_type=body.principal_type, principal_id=str(body.principal_id),
            capability=body.capability,
        )
    except AclError as e:
        raise HTTPException(e.status_code, str(e))
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="acl.grant", entity_type=resource_type, entity_id=str(resource_id),
        detail={"principal_type": body.principal_type,
                "principal_id": str(body.principal_id), "capability": body.capability},
    )
    return AclResponse.model_validate(acl)


@router.get("/{resource_type}/{resource_id}/grants", response_model=AclListResponse)
async def list_grants(
    resource_type: str,
    resource_id: str,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(tenant_session),
):
    _require_admin(principal, resource_type)
    acls = await AclService.list_for_resource(
        db, tenant_id=principal.tenant_id, resource_type=resource_type, resource_id=resource_id
    )
    return AclListResponse(acls=[AclResponse.model_validate(a) for a in acls])


@router.delete("/grants/{acl_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_grant(
    acl_id: str,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(tenant_session),
):
    # Either coarse admin perm can revoke a grant (folder or document).
    if not (principal.has_permission(_ADMIN_PERM["folder"])
            or principal.has_permission(_ADMIN_PERM["document"])):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted to manage ACLs")
    ok = await AclService.revoke(db, tenant_id=principal.tenant_id, acl_id=acl_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Grant not found")
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="acl.revoke", entity_type="acl", entity_id=str(acl_id),
    )


@router.get("/document/{document_id}/effective", response_model=EffectiveAccessResponse)
async def effective_access(
    document_id: str,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(tenant_session),
):
    doc = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    restricted = await AclService.is_restricted(db, tenant_id=principal.tenant_id, document=doc)
    group_ids = await AclService.user_group_ids(db, principal.user_id)
    is_admin = principal.has_permission(_ADMIN_PERM["document"])
    is_owner = bool(doc.uploaded_by and str(doc.uploaded_by) == str(principal.user_id))

    if not restricted or is_admin or is_owner:
        cap = "manage"
    else:
        cap = await AclService.effective_capability(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            group_ids=group_ids, document=doc,
        )
    rank = CAPABILITY_RANK.get(cap, 0) if cap else 0
    return EffectiveAccessResponse(
        document_id=doc.id, restricted=restricted,
        capability=cap if restricted else None,
        can_view=rank >= 1, can_edit=rank >= 2, can_manage=rank >= 3,
    )
