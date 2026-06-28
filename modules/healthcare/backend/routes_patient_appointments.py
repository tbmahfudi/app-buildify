"""
Healthcare — Cross-Tenant Appointments API.

T-HC-045

GET /api/v1/patients/me/appointments              — aggregated across all tenants
GET /api/v1/patients/me/appointments/{id}         — full detail (own only)

Cross-tenant query: bypasses branch RLS by using a platform-level session
and filtering directly by patient_id (not PHI in this context — it is the
caller's own ID from the JWT).
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session
from modules.healthcare.models import HCBranch, HCProvider
from modules.healthcare.sdk.patient_auth import PatientTokenData, get_current_patient, get_patient_db
from modules.healthcare.sdk.phi_audit import write_phi_read_audit
from modules.healthcare.schemas.patient_appointments import (
    PatientAppointmentDetail,
    PatientAppointmentListResponse,
    PatientAppointmentSummary,
)

router = APIRouter(prefix="/api/v1/patients/me", tags=["patient-appointments"])


def _get_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _get_ua(request: Request) -> str:
    return request.headers.get("user-agent", "")


_UPCOMING_STATUSES = ("'confirmed'", "'checked_in'", "'in_progress'")
_PAST_STATUSES = ("'completed'", "'cancelled'")


@router.get("/appointments", response_model=PatientAppointmentListResponse)
async def list_my_appointments(
    request: Request,
    filter_status: str = Query("upcoming", alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(get_patient_db),
):
    """
    Return cross-tenant appointment list for the authenticated patient.

    Uses direct patient_id filter — bypasses branch RLS intentionally.
    No diagnosis / encounter notes returned.
    """
    pid = patient.patient_id
    tid = patient.require_tenant()

    if filter_status == "upcoming":
        status_clause = "AND a.status IN ('confirmed','checked_in','in_progress')"
        order_clause = "ORDER BY a.scheduled_at ASC"
    elif filter_status == "past":
        status_clause = "AND a.status IN ('completed','cancelled')"
        order_clause = "ORDER BY a.scheduled_at DESC"
    else:  # "all"
        status_clause = ""
        order_clause = "ORDER BY a.scheduled_at DESC"

    count_sql = text(
        f"SELECT COUNT(*) FROM hcs_appointments a "
        f"WHERE a.patient_id = :pid AND a.tenant_id = :tid {status_clause}"
    )
    total = db.execute(count_sql, {"pid": pid, "tid": tid}).scalar() or 0

    rows_sql = text(
        f"""
        SELECT
            a.id            AS appointment_id,
            b.branch_name   AS clinic_name,
            b.branch_name   AS branch_name,
            p.display_name  AS provider_name,
            p.specialty     AS provider_specialty,
            a.appointment_type,
            a.scheduled_at,
            a.status
        FROM hcs_appointments a
        JOIN hc_branches  b ON b.id = a.branch_id
        JOIN hc_providers p ON p.id = a.provider_id
        WHERE a.patient_id = :pid AND a.tenant_id = :tid
        {status_clause}
        {order_clause}
        LIMIT :limit OFFSET :offset
        """
    )
    rows = db.execute(
        rows_sql,
        {"pid": pid, "tid": tid, "limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()

    items: List[PatientAppointmentSummary] = []
    for row in rows:
        items.append(
            PatientAppointmentSummary(
                appointment_id=str(row.appointment_id),
                clinic_name=row.clinic_name,
                branch_name=row.branch_name,
                provider_name=row.provider_name,
                provider_specialty=row.provider_specialty,
                appointment_type=row.appointment_type,
                scheduled_at=row.scheduled_at,
                status=row.status,
            )
        )

    # Audit once for the list access
    write_phi_read_audit(
        db=db,
        actor_id=pid,
        actor_type="patient",
        entity_type="appointment_list",
        entity_id=pid,
        tenant_id=tid,
        ip=_get_ip(request),
        ua=_get_ua(request),
        metadata={"filter_status": filter_status, "count": len(items)},
    )

    return PatientAppointmentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/appointments/{appointment_id}", response_model=PatientAppointmentDetail)
async def get_my_appointment(
    appointment_id: str,
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(get_patient_db),
):
    """Return full appointment detail — ownership enforced via patient_id + tenant_id filter."""
    pid = patient.patient_id
    tid = patient.require_tenant()

    row = db.execute(
        text(
            """
            SELECT
                a.id               AS appointment_id,
                b.branch_name      AS clinic_name,
                b.branch_name      AS branch_name,
                b.address_street   AS branch_address,
                b.contact_phone    AS branch_contact_phone,
                p.display_name     AS provider_name,
                p.specialty        AS provider_specialty,
                a.appointment_type,
                a.scheduled_at,
                a.status,
                a.notes
            FROM hcs_appointments a
            JOIN hc_branches  b ON b.id = a.branch_id
            JOIN hc_providers p ON p.id = a.provider_id
            WHERE a.id = :aid AND a.patient_id = :pid AND a.tenant_id = :tid
            LIMIT 1
            """
        ),
        {"aid": appointment_id, "pid": pid, "tid": tid},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    write_phi_read_audit(
        db=db,
        actor_id=pid,
        actor_type="patient",
        entity_type="appointment",
        entity_id=appointment_id,
        tenant_id=tid,
        ip=_get_ip(request),
        ua=_get_ua(request),
    )

    return PatientAppointmentDetail(
        appointment_id=str(row.appointment_id),
        clinic_name=row.clinic_name,
        branch_name=row.branch_name,
        branch_address=row.branch_address,
        branch_contact_phone=row.branch_contact_phone,
        provider_name=row.provider_name,
        provider_specialty=row.provider_specialty,
        appointment_type=row.appointment_type,
        scheduled_at=row.scheduled_at,
        status=row.status,
        notes=row.notes,
    )
