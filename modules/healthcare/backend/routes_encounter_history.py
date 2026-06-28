"""
Healthcare — Encounter History API.

T-HC-044

GET /api/v1/patients/me/encounters              — paginated list with year grouping
GET /api/v1/patients/me/encounters/{encounter_id} — full encounter detail (own records)
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session
from modules.healthcare.models import HCEncounter, HCBranch, HCProvider
from modules.healthcare.sdk.patient_auth import PatientTokenData, get_current_patient
from modules.healthcare.sdk.phi_audit import write_phi_read_audit
from modules.healthcare.schemas.encounter_history import (
    EncounterDetailResponse,
    EncounterHistoryResponse,
    EncounterSummaryItem,
)

router = APIRouter(prefix="/api/v1/patients/me", tags=["encounter-history"])


def _get_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _get_ua(request: Request) -> str:
    return request.headers.get("user-agent", "")


@router.get("/encounters", response_model=EncounterHistoryResponse)
async def list_my_encounters(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    clinic_name: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(tenant_scoped_session),
):
    """Return paginated encounter list for the authenticated patient."""
    pid = patient.patient_id
    tid = patient.require_tenant()

    q = (
        db.query(HCEncounter, HCBranch, HCProvider)
        .join(HCBranch, HCEncounter.branch_id == HCBranch.id)
        .join(HCProvider, HCEncounter.provider_id == HCProvider.id)
        .filter(
            HCEncounter.patient_id == pid,
            HCEncounter.tenant_id == tid,
        )
    )

    if clinic_name:
        q = q.filter(HCBranch.branch_name.ilike(f"%{clinic_name}%"))
    if date_from:
        q = q.filter(HCEncounter.started_at >= date_from)
    if date_to:
        q = q.filter(HCEncounter.started_at <= date_to)

    total = q.count()
    rows = (
        q.order_by(HCEncounter.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items: List[EncounterSummaryItem] = []
    for enc, branch, provider in rows:
        # Audit each PHI encounter returned
        write_phi_read_audit(
            db=db,
            actor_id=pid,
            actor_type="patient",
            entity_type="encounter",
            entity_id=str(enc.id),
            tenant_id=enc.tenant_id,
            branch_id=str(enc.branch_id),
            ip=_get_ip(request),
            ua=_get_ua(request),
        )

        shared = getattr(enc, "shared_with_patient", enc.summary_released)
        items.append(
            EncounterSummaryItem(
                encounter_id=str(enc.id),
                clinic_name=branch.branch_name,
                branch_name=branch.branch_name,
                provider_name=provider.display_name,
                encounter_date=enc.started_at,
                encounter_type=getattr(enc, "encounter_type", "consultation"),
                summary=enc.patient_summary if shared else None,
                summary_shared=bool(shared),
            )
        )

    by_year: dict = defaultdict(list)
    for item in items:
        by_year[item.encounter_date.year].append(item)

    return EncounterHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        by_year=dict(by_year),
    )


@router.get("/encounters/{encounter_id}", response_model=EncounterDetailResponse)
async def get_my_encounter(
    encounter_id: str,
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(tenant_scoped_session),
):
    """Return full encounter detail; enforces patient_id + tenant ownership."""
    pid = patient.patient_id
    tid = patient.require_tenant()

    row = (
        db.query(HCEncounter, HCBranch, HCProvider)
        .join(HCBranch, HCEncounter.branch_id == HCBranch.id)
        .join(HCProvider, HCEncounter.provider_id == HCProvider.id)
        .filter(
            HCEncounter.id == encounter_id,
            HCEncounter.patient_id == pid,  # ownership check
            HCEncounter.tenant_id == tid,   # tenant scope
        )
        .first()
    )

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    enc, branch, provider = row

    # get_encounter() from SDK auto-audits, but we query directly here for the join.
    # Call write_phi_read_audit() explicitly per ADR-HC-002.
    write_phi_read_audit(
        db=db,
        actor_id=pid,
        actor_type="patient",
        entity_type="encounter",
        entity_id=str(enc.id),
        tenant_id=enc.tenant_id,
        branch_id=str(enc.branch_id),
        ip=_get_ip(request),
        ua=_get_ua(request),
    )

    shared = getattr(enc, "shared_with_patient", enc.summary_released)

    return EncounterDetailResponse(
        encounter_id=str(enc.id),
        clinic_name=branch.branch_name,
        branch_name=branch.branch_name,
        provider_name=provider.display_name,
        provider_specialty=provider.specialty,
        encounter_date=enc.started_at,
        status=enc.status,
        summary=enc.patient_summary if shared else None,
        summary_shared=bool(shared),
    )
