"""
Healthcare — Provider CRUD API.

T-HC-012

POST   /api/v1/modules/healthcare/branches/{branch_id}/providers
GET    /api/v1/modules/healthcare/branches/{branch_id}/providers
PUT    /api/v1/modules/healthcare/branches/{branch_id}/providers/{provider_id}
DELETE /api/v1/modules/healthcare/branches/{branch_id}/providers/{provider_id}
"""
from __future__ import annotations
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.models import HCProvider
from modules.healthcare.schemas.provider import ProviderCreate, ProviderUpdate, ProviderResponse
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.branch_scope import healthcare_branch_session
from modules.healthcare.sdk.phi_audit import write_event_audit

router = APIRouter(
    prefix="/api/v1/modules/healthcare",
    tags=["healthcare-providers"],
)


@router.post(
    "/branches/{branch_id}/providers",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a provider for a branch",
)
async def create_provider(
    branch_id: uuid.UUID,
    payload: ProviderCreate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager])),
):
    provider = HCProvider(
        tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch_id),
        user_id=payload.user_id,
        provider_type=payload.provider_type,
        specialty=payload.specialty,
        license_number=payload.license_number,
        display_name=payload.display_name,
        bio=payload.bio,
        is_active=payload.is_active,
    )
    db.add(provider)
    db.flush()

    write_event_audit(
        db=db,
        actor_id=str(current_user.id),
        actor_type="staff",
        event_type="provider.created",
        entity_type="provider",
        entity_id=str(provider.id),
        tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch_id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )

    db.commit()
    db.refresh(provider)
    return provider


@router.get(
    "/branches/{branch_id}/providers",
    response_model=list[ProviderResponse],
    summary="List providers for a branch",
)
async def list_providers(
    branch_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(list(HCRole))),
):
    offset = (page - 1) * page_size
    providers = (
        db.query(HCProvider)
        .filter(
            HCProvider.tenant_id == hc_shared_tenant_id(),
            HCProvider.branch_id == str(branch_id),
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return providers


@router.put(
    "/branches/{branch_id}/providers/{provider_id}",
    response_model=ProviderResponse,
    summary="Update a provider",
)
async def update_provider(
    branch_id: uuid.UUID,
    provider_id: uuid.UUID,
    payload: ProviderUpdate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager])),
):
    provider = (
        db.query(HCProvider)
        .filter(
            HCProvider.id == provider_id,
            HCProvider.tenant_id == hc_shared_tenant_id(),
            HCProvider.branch_id == str(branch_id),
        )
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(provider, field, value)

    write_event_audit(
        db=db,
        actor_id=str(current_user.id),
        actor_type="staff",
        event_type="provider.updated",
        entity_type="provider",
        entity_id=str(provider.id),
        tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch_id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )

    db.commit()
    db.refresh(provider)
    return provider


@router.delete(
    "/branches/{branch_id}/providers/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a provider",
)
async def delete_provider(
    branch_id: uuid.UUID,
    provider_id: uuid.UUID,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager])),
):
    provider = (
        db.query(HCProvider)
        .filter(
            HCProvider.id == provider_id,
            HCProvider.tenant_id == hc_shared_tenant_id(),
            HCProvider.branch_id == str(branch_id),
            HCProvider.is_active == True,
        )
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider.is_active = False

    write_event_audit(
        db=db,
        actor_id=str(current_user.id),
        actor_type="staff",
        event_type="provider.deleted",
        entity_type="provider",
        entity_id=str(provider.id),
        tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch_id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )

    db.commit()
