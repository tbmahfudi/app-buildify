"""
Healthcare — Patient consent API.

T-HC-016

POST /api/v1/modules/healthcare/patients/{patient_id}/consents
     auth: patient (own record only); immutable; records ip + ua; writes audit
GET  /api/v1/patients/me/consents
     auth: patient (own record only) — FIX-BE-001
GET  /api/v1/modules/healthcare/branches/{branch_id}/patients/{patient_id}/consents
     auth: clinic_owner or branch_manager staff — FIX-BE-001
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.models import HCPatient, HCPatientConsent
from modules.healthcare.schemas.patient import ConsentCreate, ConsentResponse
from modules.healthcare.sdk.hc_permissions import HCRole, get_caller_hc_role, has_hc_permission
from modules.healthcare.sdk.patient_auth import get_current_patient, get_patient_db
from modules.healthcare.sdk.phi_audit import write_event_audit, write_phi_read_audit

router = APIRouter(
    prefix="/api/v1/modules/healthcare",
    tags=["healthcare-patients"],
)


@router.post(
    "/patients/{patient_id}/consents",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record patient consent (patient auth, own record only)",
)
async def create_patient_consent(
    patient_id: uuid.UUID,
    payload: ConsentCreate,
    request: Request,
    db: Session = Depends(get_patient_db),
    patient_token=Depends(get_current_patient),
):
    # Patient can only record consent for their own record
    if str(patient_id) != patient_token.patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You may only manage consents for your own record",
        )

    # Verify patient exists (uses tenant scope from session)
    patient = db.query(HCPatient).filter(HCPatient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    consent = HCPatientConsent(
        tenant_id=patient.tenant_id,
        patient_id=str(patient_id),
        consent_type=payload.consent_type,
        consent_version=payload.consent_version,
        status="active",
        accepted_at=datetime.utcnow(),
        ip=ip,
        user_agent=ua,
        purpose_description=payload.purpose_description,
    )
    db.add(consent)
    db.flush()

    write_event_audit(
        db=db,
        actor_id=patient_token.patient_id,
        actor_type="patient",
        event_type="consent.recorded",
        entity_type="patient_consent",
        entity_id=str(consent.id),
        tenant_id=patient.tenant_id,
        ip=ip,
        ua=ua,
    )

    db.commit()
    db.refresh(consent)
    return consent


# ---------------------------------------------------------------------------
# FIX-BE-001 / FIX-BE-004 — Patient path: own consents only
# TC-AUTH-005, TC-AUTH-006, TC-AUDIT-004
# ---------------------------------------------------------------------------

@router.get(
    "/patients/me/consents",
    response_model=list[ConsentResponse],
    summary="List own consents (patient auth only)",
)
async def list_my_consents(
    db: Session = Depends(get_patient_db),
    current_patient=Depends(get_current_patient),
):
    """
    Patient-facing endpoint. A patient may only read their own consent records.

    Calls write_phi_read_audit() before returning data — consent records
    contain consent_type, consent_version, ip, user_agent, accepted_at (PHI).
    """
    tid = current_patient.require_tenant()
    patient = (
        db.query(HCPatient)
        .filter(
            HCPatient.id == current_patient.patient_id,
            HCPatient.tenant_id == tid,
        )
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    consents = (
        db.query(HCPatientConsent)
        .filter(
            HCPatientConsent.patient_id == str(current_patient.patient_id),
            HCPatientConsent.tenant_id == tid,
        )
        .order_by(HCPatientConsent.created_at.desc())
        .all()
    )

    # FIX-BE-004: PHI audit before returning consent data
    write_phi_read_audit(
        db=db,
        actor_type="patient",
        actor_id=str(current_patient.patient_id),
        entity_type="patient_consent",
        entity_id=str(current_patient.patient_id),
        tenant_id=str(patient.tenant_id),
    )

    return consents


# ---------------------------------------------------------------------------
# FIX-BE-001 / FIX-BE-004 — Staff path: clinic_owner or branch_manager
# TC-AUTH-005, TC-AUTH-006, TC-AUDIT-004
# ---------------------------------------------------------------------------

@router.get(
    "/branches/{branch_id}/patients/{patient_id}/consents",
    response_model=list[ConsentResponse],
    summary="List patient consents for a branch patient (clinic_owner or branch_manager)",
)
async def list_patient_consents_staff(
    branch_id: uuid.UUID,
    patient_id: uuid.UUID,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager])),
):
    """
    Staff-facing endpoint. Requires clinic_owner or branch_manager role.

    Calls write_phi_read_audit() before returning data — consent records
    contain consent_type, consent_version, ip, user_agent, accepted_at (PHI).
    """
    patient = db.query(HCPatient).filter(HCPatient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    consents = (
        db.query(HCPatientConsent)
        .filter(HCPatientConsent.patient_id == str(patient_id))
        .order_by(HCPatientConsent.created_at.desc())
        .all()
    )

    # FIX-BE-004: PHI audit before returning consent data
    write_phi_read_audit(
        db=db,
        actor_type="staff",
        actor_id=str(current_user.id),
        entity_type="patient_consent",
        entity_id=str(patient_id),
        tenant_id=str(patient.tenant_id),
    )

    return consents
