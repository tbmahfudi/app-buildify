"""
Healthcare — Clinic signup and DPA status API.

T-HC-018  POST /api/v1/clinics/register  (PUBLIC)
T-HC-019  GET  /api/v1/modules/healthcare/dpa/status  (Clinic Owner)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.models import HCBranch, HCBranchStaff, HCPatientConsent
from modules.healthcare.schemas.clinic_signup import (
    ClinicRegisterRequest,
    ClinicRegisterResponse,
    DPAStatusResponse,
)
from modules.healthcare.sdk.captcha import require_captcha
from modules.healthcare.sdk.dpa_gate import require_dpa
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.locale import t
from modules.healthcare.sdk.phi_audit import write_event_audit

router = APIRouter(tags=["healthcare-clinic-signup"])


@router.post(
    "/api/v1/clinics/register",
    response_model=ClinicRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new clinic (public)",
)
async def clinic_register(
    payload: ClinicRegisterRequest,
    request: Request,
    _captcha=Depends(require_captcha),
    db: Session = Depends(tenant_scoped_session),
) -> ClinicRegisterResponse:
    """
    Public endpoint — creates a new tenant + branch + clinic_owner user,
    records the DPA consent, and emits an audit event.

    Steps:
      1. Validate hCaptcha (dependency)
      2. Reject if dpa_accepted != True
      3. Create tenant row (via platform bridge / raw SQL stub)
      4. Create branch row
      5. Create platform user for owner
      6. Create hc_branch_staff row (role=clinic_owner, branch_id=NULL)
      7. Record DPA in hc_patient_consents (consent_type='clinic_dpa')
      8. Emit audit
      9. Return ClinicRegisterResponse
    """
    locale = payload.locale

    # Step 2 — DPA gate
    if not payload.dpa_accepted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=t(locale, "error.dpa_required"),
        )

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    # Step 3 — Create tenant (platform responsibility; we generate tenant_id here
    #           and pass it to the platform bridge in a full implementation).
    #           For module-level isolation we use a stub that inserts into
    #           the platform tenants table via raw SQL.
    tenant_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO tenants (id, name, status, created_at, updated_at) "
            "VALUES (:id, :name, 'active', NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {"id": tenant_id, "name": payload.clinic_name},
    )

    # Step 4 — Create branch
    branch_id = str(uuid.uuid4())
    slug = payload.clinic_name.lower().replace(" ", "-")[:100]
    branch = HCBranch(
        id=branch_id,
        tenant_id=tenant_id,
        branch_name=payload.clinic_name,
        slug=slug,
        address_street="",
        address_city=payload.city,
        address_province="",
        contact_phone=payload.owner_phone,
        default_locale=locale,
        status="active",
    )
    db.add(branch)
    db.flush()

    # Step 5 — Create platform user for owner
    owner_user_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, name, status, created_at, updated_at) "
            "VALUES (:id, :tid, :email, :name, 'active', NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {
            "id": owner_user_id,
            "tid": tenant_id,
            "email": payload.owner_email,
            "name": payload.owner_name,
        },
    )

    # Step 6 — Create hc_branch_staff (clinic_owner, branch_id=NULL sentinel)
    staff = HCBranchStaff(
        tenant_id=tenant_id,
        branch_id=None,  # NULL = clinic owner sentinel
        user_id=owner_user_id,
        role=HCRole.clinic_owner,
        status="active",
        is_active=True,
    )
    db.add(staff)
    db.flush()

    # Step 7 — Record DPA consent
    #   For clinic DPA we store entity_id in patient_id column with a sentinel UUID
    #   that matches the tenant_id so require_dpa() can locate it.
    dpa_record = HCPatientConsent(
        tenant_id=tenant_id,
        patient_id=tenant_id,  # DPA sentinel: patient_id == tenant_id
        consent_type="clinic_dpa",
        consent_version=payload.dpa_version,
        status="active",
        accepted_at=datetime.utcnow(),
        ip=ip,
        user_agent=ua,
        purpose_description="Clinic Data Processing Agreement acceptance",
    )
    db.add(dpa_record)
    db.flush()

    # Step 8 — Emit audit
    write_event_audit(
        db=db,
        actor_id=owner_user_id,
        actor_type="staff",
        event_type="clinic.registered",
        entity_type="tenant",
        entity_id=tenant_id,
        tenant_id=tenant_id,
        ip=ip,
        ua=ua,
    )

    db.commit()

    return ClinicRegisterResponse(
        tenant_id=tenant_id,
        branch_id=branch_id,
        message=t(locale, "clinic.registered"),
    )


# ---------------------------------------------------------------------------
# T-HC-019 — DPA status endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/modules/healthcare/dpa/status",
    response_model=DPAStatusResponse,
    summary="DPA acceptance status for this tenant (Clinic Owner)",
)
async def dpa_status(
    _role=Depends(has_hc_permission([HCRole.clinic_owner])),
    current_user=Depends(get_current_user),
    db: Session = Depends(tenant_scoped_session),
) -> DPAStatusResponse:
    """Return DPA acceptance status for the authenticated clinic owner's tenant."""
    tenant_id = str(current_user.tenant_id)

    row = db.execute(
        text(
            "SELECT consent_version, accepted_at "
            "FROM hc_patient_consents "
            "WHERE tenant_id = :tid "
            "AND consent_type = 'clinic_dpa' "
            "AND status = 'active' "
            "ORDER BY accepted_at DESC "
            "LIMIT 1"
        ),
        {"tid": tenant_id},
    ).fetchone()

    if row is None:
        return DPAStatusResponse(dpa_accepted=False, dpa_version=None, accepted_at=None)

    return DPAStatusResponse(
        dpa_accepted=True,
        dpa_version=row[0],
        accepted_at=row[1].isoformat() if row[1] else None,
    )
