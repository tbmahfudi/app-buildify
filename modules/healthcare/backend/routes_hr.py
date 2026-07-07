"""
Healthcare — HR: Doctors/Providers & Rooms API.

Epic-11 (core slice: rooms + doctor/provider management). Staff-facing,
branch-scoped, hc_branch_staff RBAC. Extends hc_providers with license /
doctor-profile / employment fields and adds hc_rooms.

    POST/GET/PUT  /branches/{b}/rooms[/{id}]
    POST/GET      /branches/{b}/hr/providers
    PUT           /branches/{b}/hr/providers/{id}                 (basic)
    PUT           /branches/{b}/hr/providers/{id}/doctor-profile  (fee, room)
    PUT           /branches/{b}/hr/providers/{id}/license         (STR/SIP, specialty)
    PUT           /branches/{b}/hr/providers/{id}/status          (employment)
"""
from __future__ import annotations
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from modules.sdk.dependencies import get_current_user
from modules.healthcare.models import HCProvider, HCRoom
from modules.healthcare.schemas.hr import (
    DoctorProfileUpdate,
    LicenseUpdate,
    ProviderBasicUpdate,
    ProviderHRCreate,
    ProviderHRResponse,
    RoomCreate,
    RoomResponse,
    RoomUpdate,
    StatusUpdate,
)
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.branch_scope import healthcare_branch_session
from modules.healthcare.sdk.phi_audit import write_event_audit

router = APIRouter(prefix="/api/v1/modules/healthcare", tags=["healthcare-hr"])

_MANAGE = [HCRole.clinic_owner, HCRole.branch_manager]


def _audit(db, request, user, branch_id, event, etype, eid):
    write_event_audit(db=db, actor_id=str(user.id), actor_type="staff", event_type=event,
                      entity_type=etype, entity_id=str(eid), tenant_id=hc_shared_tenant_id(),
                      branch_id=str(branch_id),
                      ip=request.client.host if request.client else None,
                      ua=request.headers.get("user-agent"))


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

@router.post("/branches/{branch_id}/rooms", response_model=RoomResponse,
             status_code=status.HTTP_201_CREATED, summary="Create a room")
async def create_room(branch_id: uuid.UUID, payload: RoomCreate, request: Request,
                      db: Session = Depends(healthcare_branch_session),
                      current_user=Depends(get_current_user),
                      _=Depends(has_hc_permission(_MANAGE))):
    tid = hc_shared_tenant_id()
    if db.query(HCRoom).filter(HCRoom.tenant_id == tid, HCRoom.branch_id == str(branch_id),
                               HCRoom.code == payload.code).first():
        raise HTTPException(status_code=409, detail="Room code already exists in this branch")
    room = HCRoom(tenant_id=tid, branch_id=str(branch_id), code=payload.code, name=payload.name,
                  room_type=payload.room_type, is_active=payload.is_active)
    db.add(room); db.flush()
    _audit(db, request, current_user, branch_id, "room.created", "room", room.id)
    db.commit(); db.refresh(room)
    return room


@router.get("/branches/{branch_id}/rooms", response_model=list[RoomResponse], summary="List rooms")
async def list_rooms(branch_id: uuid.UUID, is_active: Optional[bool] = Query(None),
                     db: Session = Depends(healthcare_branch_session),
                     current_user=Depends(get_current_user),
                     _=Depends(has_hc_permission(list(HCRole)))):
    q = db.query(HCRoom).filter(HCRoom.tenant_id == hc_shared_tenant_id(),
                                HCRoom.branch_id == str(branch_id))
    if is_active is not None:
        q = q.filter(HCRoom.is_active == is_active)
    return q.order_by(HCRoom.code).all()


@router.put("/branches/{branch_id}/rooms/{room_id}", response_model=RoomResponse,
            summary="Update or disable a room")
async def update_room(branch_id: uuid.UUID, room_id: uuid.UUID, payload: RoomUpdate, request: Request,
                      db: Session = Depends(healthcare_branch_session),
                      current_user=Depends(get_current_user),
                      _=Depends(has_hc_permission(_MANAGE))):
    room = db.query(HCRoom).filter(HCRoom.id == str(room_id),
                                   HCRoom.tenant_id == hc_shared_tenant_id(),
                                   HCRoom.branch_id == str(branch_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(room, f, v)
    _audit(db, request, current_user, branch_id, "room.updated", "room", room.id)
    db.commit(); db.refresh(room)
    return room


# ---------------------------------------------------------------------------
# Providers (doctors / nurses / …)
# ---------------------------------------------------------------------------

def _prov_resp(db, p: HCProvider) -> ProviderHRResponse:
    room_name = None
    if p.room_id:
        r = db.query(HCRoom.name).filter(HCRoom.id == p.room_id).first()
        room_name = r[0] if r else None
    return ProviderHRResponse(
        id=p.id, branch_id=p.branch_id, user_id=p.user_id, provider_type=p.provider_type,
        display_name=p.display_name, specialty=p.specialty, sub_specialty=p.sub_specialty,
        license_number=p.license_number, str_number=p.str_number, sip_number=p.sip_number,
        str_expiry=p.str_expiry, sip_expiry=p.sip_expiry, consultation_fee=p.consultation_fee,
        room_id=p.room_id, room_name=room_name, employment_status=p.employment_status,
        is_active=p.is_active, created_at=p.created_at,
    )


def _get_provider(db, tid, branch_id, provider_id) -> HCProvider:
    p = db.query(HCProvider).filter(HCProvider.id == str(provider_id), HCProvider.tenant_id == tid,
                                    HCProvider.branch_id == str(branch_id)).first()
    if not p:
        raise HTTPException(status_code=404, detail="Provider not found")
    return p


def _check_room(db, tid, branch_id, room_id):
    if room_id and not db.query(HCRoom).filter(HCRoom.id == room_id, HCRoom.tenant_id == tid,
                                               HCRoom.branch_id == str(branch_id)).first():
        raise HTTPException(status_code=422, detail="Room not found in this branch")


@router.post("/branches/{branch_id}/hr/providers", response_model=ProviderHRResponse,
             status_code=status.HTTP_201_CREATED, summary="Create a provider (doctor/nurse/…)")
async def create_provider(branch_id: uuid.UUID, payload: ProviderHRCreate, request: Request,
                          db: Session = Depends(healthcare_branch_session),
                          current_user=Depends(get_current_user),
                          _=Depends(has_hc_permission(_MANAGE))):
    tid = hc_shared_tenant_id()
    _check_room(db, tid, branch_id, payload.room_id)
    p = HCProvider(
        id=str(uuid.uuid4()), tenant_id=tid, branch_id=str(branch_id), user_id=payload.user_id,
        provider_type=payload.provider_type, display_name=payload.display_name,
        specialty=payload.specialty, sub_specialty=payload.sub_specialty,
        license_number=payload.license_number, str_number=payload.str_number,
        sip_number=payload.sip_number, str_expiry=payload.str_expiry, sip_expiry=payload.sip_expiry,
        consultation_fee=payload.consultation_fee, room_id=payload.room_id, is_active=payload.is_active,
    )
    db.add(p); db.flush()
    _audit(db, request, current_user, branch_id, "provider.created", "provider", p.id)
    db.commit(); db.refresh(p)
    return _prov_resp(db, p)


@router.get("/branches/{branch_id}/hr/providers", response_model=list[ProviderHRResponse],
            summary="Provider directory")
async def list_providers(branch_id: uuid.UUID, type: Optional[str] = Query(None),
                         specialty: Optional[str] = Query(None), q: Optional[str] = Query(None),
                         db: Session = Depends(healthcare_branch_session),
                         current_user=Depends(get_current_user),
                         _=Depends(has_hc_permission(list(HCRole)))):
    query = db.query(HCProvider).filter(HCProvider.tenant_id == hc_shared_tenant_id(),
                                        HCProvider.branch_id == str(branch_id))
    if type:
        query = query.filter(HCProvider.provider_type == type)
    if specialty:
        query = query.filter(HCProvider.specialty.ilike(f"%{specialty}%"))
    if q:
        query = query.filter(HCProvider.display_name.ilike(f"%{q}%"))
    return [_prov_resp(db, p) for p in query.order_by(HCProvider.display_name).all()]


@router.put("/branches/{branch_id}/hr/providers/{provider_id}", response_model=ProviderHRResponse,
            summary="Update basic provider fields")
async def update_provider(branch_id: uuid.UUID, provider_id: uuid.UUID, payload: ProviderBasicUpdate,
                          request: Request, db: Session = Depends(healthcare_branch_session),
                          current_user=Depends(get_current_user),
                          _=Depends(has_hc_permission(_MANAGE))):
    p = _get_provider(db, hc_shared_tenant_id(), branch_id, provider_id)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, f, v)
    _audit(db, request, current_user, branch_id, "provider.updated", "provider", p.id)
    db.commit(); db.refresh(p)
    return _prov_resp(db, p)


@router.put("/branches/{branch_id}/hr/providers/{provider_id}/doctor-profile",
            response_model=ProviderHRResponse, summary="Set consultation fee + room assignment")
async def set_doctor_profile(branch_id: uuid.UUID, provider_id: uuid.UUID, payload: DoctorProfileUpdate,
                             request: Request, db: Session = Depends(healthcare_branch_session),
                             current_user=Depends(get_current_user),
                             _=Depends(has_hc_permission(_MANAGE))):
    tid = hc_shared_tenant_id()
    p = _get_provider(db, tid, branch_id, provider_id)
    data = payload.model_dump(exclude_unset=True)
    if "room_id" in data:
        _check_room(db, tid, branch_id, data["room_id"])
    for f, v in data.items():
        setattr(p, f, v)
    _audit(db, request, current_user, branch_id, "provider.doctor_profile_set", "provider", p.id)
    db.commit(); db.refresh(p)
    return _prov_resp(db, p)


@router.put("/branches/{branch_id}/hr/providers/{provider_id}/license",
            response_model=ProviderHRResponse, summary="Set STR/SIP license + specialty")
async def set_license(branch_id: uuid.UUID, provider_id: uuid.UUID, payload: LicenseUpdate,
                      request: Request, db: Session = Depends(healthcare_branch_session),
                      current_user=Depends(get_current_user),
                      _=Depends(has_hc_permission(_MANAGE))):
    p = _get_provider(db, hc_shared_tenant_id(), branch_id, provider_id)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, f, v)
    _audit(db, request, current_user, branch_id, "provider.license_set", "provider", p.id)
    db.commit(); db.refresh(p)
    return _prov_resp(db, p)


@router.put("/branches/{branch_id}/hr/providers/{provider_id}/status",
            response_model=ProviderHRResponse, summary="Set employment status")
async def set_status(branch_id: uuid.UUID, provider_id: uuid.UUID, payload: StatusUpdate,
                     request: Request, db: Session = Depends(healthcare_branch_session),
                     current_user=Depends(get_current_user),
                     _=Depends(has_hc_permission(_MANAGE))):
    p = _get_provider(db, hc_shared_tenant_id(), branch_id, provider_id)
    p.employment_status = payload.employment_status
    _audit(db, request, current_user, branch_id, "provider.status_set", "provider", p.id)
    db.commit(); db.refresh(p)
    return _prov_resp(db, p)
