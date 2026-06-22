from __future__ import annotations
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.branch_scope import healthcare_branch_session
from modules.healthcare.sdk.patient_auth import get_current_patient
from modules.healthcare.sdk.phi_audit import write_event_audit, write_phi_read_audit
from modules.healthcare.schemas.appointment import (
    SlotResponse, AppointmentCreate, AppointmentReschedule,
    AppointmentResponse, AppointmentListResponse, AppointmentStatusUpdate,
)
from modules.sdk.db import generate_uuid

logger = logging.getLogger(__name__)

router = APIRouter(tags=["healthcare-scheduling-appointments"])

_VALID_TRANSITIONS: dict[str, set] = {
    "confirmed": {"checked_in", "no_show"},
    "checked_in": {"in_progress"},
    "in_progress": {"completed"},
    "completed": set(),
    "no_show": set(),
    "cancelled": set(),
    "flagged_for_review": {"confirmed", "cancelled"},
}
_STAFF_STATUS_INPUTS = {"checked_in", "in_progress", "completed", "no_show"}


# ---------------------------------------------------------------------------
# T-HC-030 -- List available slots
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/clinics/{clinic_slug}/branches/{branch_id}/slots",
    response_model=List[SlotResponse],
    summary="List available slots (patient auth)",
)
async def list_available_slots(
    clinic_slug: str,
    branch_id: uuid.UUID,
    date: str = Query(..., description="YYYY-MM-DD"),
    appointment_type: Optional[str] = Query(None),
    db: Session = Depends(tenant_scoped_session),
    patient_token=Depends(get_current_patient),
):
    branch_row = db.execute(
        text("SELECT tenant_id FROM hc_branches WHERE id=:bid LIMIT 1"),
        {"bid": str(branch_id)},
    ).fetchone()
    if not branch_row:
        raise HTTPException(status_code=404, detail="Branch not found")

    tenant_id = str(branch_row[0])
    q = (
        "SELECT s.id AS slot_id, s.slot_date, s.start_time, s.end_time, s.appointment_type, "
        "p.full_name AS provider_name, p.specialty AS provider_specialty "
        "FROM hcs_appointment_slots s "
        "JOIN hc_providers p ON p.id = s.provider_id "
        # CR-015 fix: add tenant_id filter to prevent cross-tenant slot visibility
        "WHERE s.tenant_id=:tid AND s.branch_id=:bid AND s.slot_date=:dt AND s.status='available'"
    )
    params: dict = dict(tid=tenant_id, bid=str(branch_id), dt=date)
    if appointment_type:
        q += " AND s.appointment_type=:apt"
        params["apt"] = appointment_type
    q += " ORDER BY s.start_time"
    rows = db.execute(text(q), params).mappings().all()

    # FIX-BE-006: Audit slot listing — provider.full_name is a display-name column
    # on hc_providers and is not a patient PHI field; write_event_audit is appropriate.
    write_event_audit(
        db=db,
        actor_id=str(patient_token.patient_id),
        actor_type="patient",
        event_type="slot.list",
        entity_type="appointment_slot",
        entity_id=str(branch_id),
        tenant_id=str(branch_row[0]),
        metadata={"date": date, "appointment_type": appointment_type},
    )

    return [SlotResponse(**dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# T-HC-030 -- Book appointment (atomic SELECT FOR UPDATE)
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/patients/me/appointments",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book appointment (patient auth, atomic)",
)
async def book_appointment(
    payload: AppointmentCreate,
    request: Request,
    db: Session = Depends(tenant_scoped_session),
    patient_token=Depends(get_current_patient),
):
    slot_id = str(payload.slot_id)
    slot = db.execute(
        text("SELECT * FROM hcs_appointment_slots WHERE id=:sid FOR UPDATE"),
        {"sid": slot_id},
    ).mappings().one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot["status"] != "available":
        raise HTTPException(status_code=409, detail="Slot is no longer available")

    branch = db.execute(
        text("SELECT tenant_id FROM hc_branches WHERE id=:bid LIMIT 1"),
        {"bid": slot["branch_id"]},
    ).fetchone()
    tenant_id = branch[0] if branch else slot.get("tenant_id", "")

    appt_id = str(generate_uuid())
    db.execute(
        text(
            "INSERT INTO hcs_appointments "
            "(id,tenant_id,branch_id,provider_id,patient_id,slot_id,appointment_type,"
            "status,scheduled_at,notes,created_at,updated_at) "
            "VALUES (:id,:tid,:bid,:pid,:pat,:sid,:apt,'confirmed',:sched,:notes,NOW(),NOW())"
        ),
        dict(
            id=appt_id, tid=tenant_id, bid=slot["branch_id"], pid=slot["provider_id"],
            pat=patient_token.patient_id, sid=slot_id, apt=payload.appointment_type,
            sched=datetime.combine(slot["slot_date"], slot["start_time"]),
            notes=payload.notes,
        ),
    )
    db.execute(
        text("UPDATE hcs_appointment_slots SET status='booked', appointment_id=:aid WHERE id=:sid"),
        dict(aid=appt_id, sid=slot_id),
    )
    write_event_audit(db=db, actor_id=patient_token.patient_id, actor_type="patient",
                      event_type="appointment.booked", entity_type="appointment",
                      entity_id=appt_id, tenant_id=tenant_id, branch_id=slot["branch_id"],
                      source_module="healthcare_scheduling")
    db.commit()

    try:
        from modules.healthcare.sdk.notification_service import NotificationService
        NotificationService(db=db, tenant_id=tenant_id, branch_id=slot["branch_id"])\
            .dispatch_appointment_notification(appt_id, "appointment_confirmed")
    except Exception as exc:
        logger.warning("Notification dispatch failed: %s", exc)

    try:
        from modules.healthcare.sdk.reminder_scheduler import schedule_appointment_reminders
        schedule_appointment_reminders(appt_id, datetime.combine(slot["slot_date"], slot["start_time"]))
    except Exception as exc:
        logger.warning("Reminder scheduling failed: %s", exc)

    row = db.execute(text("SELECT * FROM hcs_appointments WHERE id=:id"), {"id": appt_id}).mappings().one()
    return AppointmentResponse(**dict(row))


# ---------------------------------------------------------------------------
# T-HC-030 -- List patient appointments
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/patients/me/appointments",
    response_model=AppointmentListResponse,
    summary="List patient appointments",
)
async def list_patient_appointments(
    db: Session = Depends(tenant_scoped_session),
    patient_token=Depends(get_current_patient),
):
    rows = db.execute(
        text("SELECT * FROM hcs_appointments WHERE patient_id=:pid ORDER BY scheduled_at DESC"),
        {"pid": patient_token.patient_id},
    ).mappings().all()
    items = [AppointmentResponse(**dict(r)) for r in rows]

    # FIX-BE-003: PHI audit — appointment rows include 'notes' (clinical notes, PHI).
    # Derive tenant_id from the first appointment row; fall back to empty string
    # (audit failure is swallowed inside write_phi_read_audit — it must not crash the request).
    tenant_id_str = str(items[0].tenant_id) if items else ""
    write_phi_read_audit(
        db=db,
        actor_type="patient",
        actor_id=str(patient_token.patient_id),
        entity_type="appointment_list",
        entity_id=str(patient_token.patient_id),
        tenant_id=tenant_id_str,
    )

    return AppointmentListResponse(appointments=items, total=len(items))


# ---------------------------------------------------------------------------
# T-HC-031 -- Reschedule appointment
# ---------------------------------------------------------------------------

@router.put(
    "/api/v1/patients/me/appointments/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Reschedule appointment (patient auth)",
)
async def reschedule_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentReschedule,
    request: Request,
    db: Session = Depends(tenant_scoped_session),
    patient_token=Depends(get_current_patient),
):
    appt_id = str(appointment_id)
    new_slot_id = str(payload.new_slot_id)

    appt = db.execute(
        text("SELECT * FROM hcs_appointments WHERE id=:id AND patient_id=:pid FOR UPDATE"),
        dict(id=appt_id, pid=patient_token.patient_id),
    ).mappings().one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt["status"] not in ("confirmed", "flagged_for_review"):
        raise HTTPException(status_code=422, detail="Cannot reschedule appointment in current status")

    new_slot = db.execute(
        text("SELECT * FROM hcs_appointment_slots WHERE id=:sid FOR UPDATE"),
        {"sid": new_slot_id},
    ).mappings().one_or_none()
    if not new_slot:
        raise HTTPException(status_code=404, detail="New slot not found")
    if new_slot["status"] != "available":
        raise HTTPException(status_code=409, detail="New slot is not available")

    # Release old slot
    db.execute(
        text("UPDATE hcs_appointment_slots SET status='available', appointment_id=NULL WHERE id=:sid"),
        {"sid": appt["slot_id"]},
    )
    # Cancel old appointment
    db.execute(
        text("UPDATE hcs_appointments SET status='cancelled', cancelled_at=NOW(), "
             "cancellation_reason='rescheduled', updated_at=NOW() WHERE id=:id"),
        {"id": appt_id},
    )
    # Create new appointment
    new_appt_id = str(generate_uuid())
    db.execute(
        text(
            "INSERT INTO hcs_appointments "
            "(id,tenant_id,branch_id,provider_id,patient_id,slot_id,appointment_type,"
            "status,scheduled_at,rescheduled_from_id,notes,created_at,updated_at) "
            "VALUES (:id,:tid,:bid,:pid,:pat,:sid,:apt,'confirmed',:sched,:old,:notes,NOW(),NOW())"
        ),
        dict(
            id=new_appt_id, tid=appt["tenant_id"], bid=appt["branch_id"], pid=appt["provider_id"],
            pat=patient_token.patient_id, sid=new_slot_id, apt=appt["appointment_type"],
            sched=datetime.combine(new_slot["slot_date"], new_slot["start_time"]),
            old=appt_id, notes=appt["notes"],
        ),
    )
    # Book new slot
    db.execute(
        text("UPDATE hcs_appointment_slots SET status='booked', appointment_id=:aid WHERE id=:sid"),
        dict(aid=new_appt_id, sid=new_slot_id),
    )

    write_event_audit(db=db, actor_id=patient_token.patient_id, actor_type="patient",
                      event_type="appointment.rescheduled", entity_type="appointment",
                      entity_id=new_appt_id, tenant_id=appt["tenant_id"], branch_id=appt["branch_id"],
                      source_module="healthcare_scheduling",
                      metadata={"from_appointment_id": appt_id})
    db.commit()

    try:
        from modules.healthcare.routes_waitlist import _offer_waitlist_next
        _offer_waitlist_next(slot_id=appt["slot_id"], db=db)
    except Exception as exc:
        logger.warning("Waitlist offer failed after reschedule: %s", exc)

    row = db.execute(text("SELECT * FROM hcs_appointments WHERE id=:id"), {"id": new_appt_id}).mappings().one()
    return AppointmentResponse(**dict(row))


# ---------------------------------------------------------------------------
# T-HC-031 -- Cancel appointment
# ---------------------------------------------------------------------------

@router.delete(
    "/api/v1/patients/me/appointments/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel appointment (patient auth, cancellation policy enforced)",
)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    request: Request,
    db: Session = Depends(tenant_scoped_session),
    patient_token=Depends(get_current_patient),
):
    appt_id = str(appointment_id)
    appt = db.execute(
        text("SELECT * FROM hcs_appointments WHERE id=:id AND patient_id=:pid FOR UPDATE"),
        dict(id=appt_id, pid=patient_token.patient_id),
    ).mappings().one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt["status"] in ("cancelled", "completed", "no_show"):
        raise HTTPException(status_code=422, detail="Appointment cannot be cancelled in current status")

    # Cancellation policy: default 2h minimum
    cancel_hours_minimum = 2
    scheduled_at = appt["scheduled_at"]
    if isinstance(scheduled_at, str):
        scheduled_at = datetime.fromisoformat(scheduled_at)
    if (scheduled_at - datetime.utcnow()).total_seconds() < cancel_hours_minimum * 3600:
        raise HTTPException(
            status_code=422,
            detail=f"Appointments must be cancelled at least {cancel_hours_minimum} hour(s) in advance",
        )

    db.execute(
        text("UPDATE hcs_appointments SET status='cancelled', cancelled_at=NOW(), updated_at=NOW() WHERE id=:id"),
        {"id": appt_id},
    )
    db.execute(
        text("UPDATE hcs_appointment_slots SET status='available', appointment_id=NULL WHERE id=:sid"),
        {"sid": appt["slot_id"]},
    )
    write_event_audit(db=db, actor_id=patient_token.patient_id, actor_type="patient",
                      event_type="appointment.cancelled", entity_type="appointment",
                      entity_id=appt_id, tenant_id=appt["tenant_id"], branch_id=appt["branch_id"],
                      source_module="healthcare_scheduling")
    db.commit()

    try:
        from modules.healthcare.routes_waitlist import _offer_waitlist_next
        _offer_waitlist_next(slot_id=appt["slot_id"], db=db)
    except Exception as exc:
        logger.warning("Waitlist offer failed after cancel: %s", exc)

    try:
        from modules.healthcare.sdk.notification_service import NotificationService
        NotificationService(db=db, tenant_id=appt["tenant_id"], branch_id=appt["branch_id"])\
            .dispatch_appointment_notification(appt_id, "appointment_cancelled")
    except Exception as exc:
        logger.warning("Cancel notification failed: %s", exc)


# ---------------------------------------------------------------------------
# T-HC-032 -- Status transition (staff-only)
# ---------------------------------------------------------------------------

@router.put(
    "/api/v1/modules/healthcare_scheduling/branches/{branch_id}/appointments/{appointment_id}/status",
    response_model=AppointmentResponse,
    summary="Update appointment status (Nurse / Branch Manager)",
)
async def update_appointment_status(
    branch_id: uuid.UUID,
    appointment_id: uuid.UUID,
    payload: AppointmentStatusUpdate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission([HCRole.nurse, HCRole.branch_manager, HCRole.clinic_owner])),
):
    new_status = payload.status
    if new_status not in _STAFF_STATUS_INPUTS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Allowed values: {sorted(_STAFF_STATUS_INPUTS)}",
        )
    appt_id = str(appointment_id)
    appt = db.execute(
        text("SELECT * FROM hcs_appointments WHERE id=:id AND branch_id=:bid FOR UPDATE"),
        dict(id=appt_id, bid=str(branch_id)),
    ).mappings().one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    current_status = appt["status"]
    if new_status not in _VALID_TRANSITIONS.get(current_status, set()):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid transition: {current_status!r} -> {new_status!r}",
        )

    db.execute(
        text("UPDATE hcs_appointments SET status=:status, updated_at=NOW() WHERE id=:id"),
        dict(status=new_status, id=appt_id),
    )
    write_event_audit(db=db, actor_id=str(current_user.id), actor_type="staff",
                      event_type="appointment.status_changed", entity_type="appointment",
                      entity_id=appt_id, tenant_id=appt["tenant_id"], branch_id=str(branch_id),
                      source_module="healthcare_scheduling",
                      metadata={"from_status": current_status, "to_status": new_status})
    db.commit()

    row = db.execute(text("SELECT * FROM hcs_appointments WHERE id=:id"), {"id": appt_id}).mappings().one()
    return AppointmentResponse(**dict(row))
