"""
Healthcare — Patient Profile & Summary API.

T-HC-043

GET  /api/v1/patients/me/profile   — returns decrypted PHI; audits every call
PUT  /api/v1/patients/me/profile   — updates email / address / locale only
GET  /api/v1/patients/me/summary   — aggregate counts; no PHI
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session
from modules.healthcare.models import HCEncounter, HCPatient
from modules.healthcare.sdk.patient_auth import PatientTokenData, get_current_patient
from modules.healthcare.sdk.phi_audit import write_event_audit, write_phi_read_audit
from modules.healthcare.schemas.patient_profile import (
    PatientProfileResponse,
    PatientProfileUpdate,
    PatientSummaryResponse,
)

router = APIRouter(prefix="/api/v1/patients/me", tags=["patient-profile"])


def _get_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _get_ua(request: Request) -> str:
    return request.headers.get("user-agent", "")


def _mask_phone(phone: str) -> str:
    """Return last-4 digits masked: ****1234."""
    if not phone:
        return "****"
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) >= 4:
        return "*" * (len(digits) - 4) + digits[-4:]
    return "*" * len(digits)


@router.get("/profile", response_model=PatientProfileResponse)
async def get_my_profile(
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(tenant_scoped_session),
):
    """Return decrypted PHI profile for the authenticated patient."""
    tid = patient.require_tenant()
    row = (
        db.query(HCPatient)
        .filter(
            HCPatient.id == patient.patient_id,
            HCPatient.tenant_id == tid,
            HCPatient.deleted_at.is_(None),
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Audit BEFORE returning PHI (ADR-HC-002 §D2)
    write_phi_read_audit(
        db=db,
        actor_id=patient.patient_id,
        actor_type="patient",
        entity_type="patient",
        entity_id=str(row.id),
        tenant_id=row.tenant_id,
        ip=_get_ip(request),
        ua=_get_ua(request),
    )

    return PatientProfileResponse(
        full_name=row.full_name or "",
        date_of_birth=row.date_of_birth or "",
        email=row.email,
        address=row.address,
        masked_phone=_mask_phone(row.phone or ""),
        locale=row.locale,
        gender=row.gender,
        created_at=row.created_at,
    )


@router.put("/profile", response_model=PatientProfileResponse)
async def update_my_profile(
    payload: PatientProfileUpdate,
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(tenant_scoped_session),
):
    """Update allowed profile fields (email, address, locale) — NOT name/dob/phone."""
    tid = patient.require_tenant()
    row = (
        db.query(HCPatient)
        .filter(
            HCPatient.id == patient.patient_id,
            HCPatient.tenant_id == tid,
            HCPatient.deleted_at.is_(None),
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    if payload.email is not None:
        row.email = payload.email
    if payload.address is not None:
        row.address = payload.address
    if payload.locale is not None:
        row.locale = payload.locale

    row.updated_at = datetime.utcnow()
    db.flush()

    write_event_audit(
        db=db,
        actor_id=patient.patient_id,
        actor_type="patient",
        event_type="patient.profile_updated",
        entity_type="patient",
        entity_id=str(row.id),
        tenant_id=row.tenant_id,
        ip=_get_ip(request),
        ua=_get_ua(request),
    )

    # Return updated profile (audit the read too)
    write_phi_read_audit(
        db=db,
        actor_id=patient.patient_id,
        actor_type="patient",
        entity_type="patient",
        entity_id=str(row.id),
        tenant_id=row.tenant_id,
        ip=_get_ip(request),
        ua=_get_ua(request),
    )

    return PatientProfileResponse(
        full_name=row.full_name or "",
        date_of_birth=row.date_of_birth or "",
        email=row.email,
        address=row.address,
        masked_phone=_mask_phone(row.phone or ""),
        locale=row.locale,
        gender=row.gender,
        created_at=row.created_at,
    )


@router.get("/summary", response_model=PatientSummaryResponse)
async def get_my_summary(
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(tenant_scoped_session),
):
    """Return aggregate counts — no PHI fields, just statistics."""
    pid = patient.patient_id
    tid = patient.require_tenant()

    # Total completed visits
    total_visits = (
        db.query(func.count(HCEncounter.id))
        .filter(
            HCEncounter.patient_id == pid,
            HCEncounter.tenant_id == tid,
            HCEncounter.status == "completed",
        )
        .scalar()
        or 0
    )

    # Upcoming appointments (confirmed / checked_in / in_progress)
    upcoming_count = db.execute(
        text(
            "SELECT COUNT(*) FROM hcs_appointments "
            "WHERE patient_id = :pid AND tenant_id = :tid "
            "AND status IN ('confirmed','checked_in','in_progress')"
        ),
        {"pid": pid, "tid": tid},
    ).scalar() or 0

    # Distinct clinics (branches) with at least one encounter in this tenant
    active_clinics = (
        db.query(func.count(func.distinct(HCEncounter.branch_id)))
        .filter(
            HCEncounter.patient_id == pid,
            HCEncounter.tenant_id == tid,
        )
        .scalar()
        or 0
    )

    # Last visit date
    last_visit = (
        db.query(func.max(HCEncounter.completed_at))
        .filter(
            HCEncounter.patient_id == pid,
            HCEncounter.tenant_id == tid,
            HCEncounter.status == "completed",
        )
        .scalar()
    )

    # Audit once for summary (even though no PHI returned, it IS patient-scoped access)
    row = (
        db.query(HCPatient)
        .filter(HCPatient.id == pid, HCPatient.tenant_id == tid)
        .first()
    )
    tenant_id = row.tenant_id if row else tid
    write_phi_read_audit(
        db=db,
        actor_id=pid,
        actor_type="patient",
        entity_type="patient",
        entity_id=pid,
        tenant_id=tenant_id,
        ip=_get_ip(request),
        ua=_get_ua(request),
        metadata={"access_type": "summary"},
    )

    return PatientSummaryResponse(
        total_visits=total_visits,
        upcoming_appointments=upcoming_count,
        active_clinics=active_clinics,
        last_visit_date=last_visit,
    )
