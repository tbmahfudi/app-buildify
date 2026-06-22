from __future__ import annotations
import json
import uuid
import logging
from datetime import time as dtime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.branch_scope import healthcare_branch_session
from modules.healthcare.sdk.phi_audit import write_event_audit
from modules.healthcare.schemas.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleListResponse,
    DateTimeBlockCreate, DateTimeBlockResponse,
)
from modules.sdk.db import generate_uuid

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/healthcare_scheduling",
    tags=["healthcare-scheduling-schedules"],
)

_MANAGERS = [HCRole.clinic_owner, HCRole.branch_manager]


def _parse_time(t_str: str) -> dtime:
    try:
        h, m = t_str.split(":")
        return dtime(int(h), int(m))
    except Exception:
        raise HTTPException(status_code=422, detail=f"Invalid time format: {t_str!r} -- expected HH:MM")


def _check_overlap(
    db: Session, tenant_id: str, branch_id: str, provider_id: str,
    day_of_week: int, start_t: dtime, end_t: dtime,
    exclude_id: Optional[str] = None,
) -> None:
    base = (
        "SELECT id FROM hcs_provider_schedules "
        "WHERE tenant_id = :tid AND branch_id = :bid AND provider_id = :pid "
        "AND day_of_week = :dow AND is_active = true "
        "AND NOT (end_time <= :st OR start_time >= :et)"
    )
    params = dict(tid=tenant_id, bid=branch_id, pid=provider_id, dow=day_of_week, st=start_t, et=end_t)
    if exclude_id:
        base += " AND id != :excl"
        params["excl"] = exclude_id
    if db.execute(text(base), params).fetchone():
        raise HTTPException(status_code=409, detail="Schedule overlaps with existing active block for this provider/day")


@router.post(
    "/branches/{branch_id}/schedules",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create provider schedule",
)
async def create_schedule(
    branch_id: uuid.UUID,
    payload: ScheduleCreate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission(_MANAGERS)),
):
    tid = str(current_user.tenant_id)
    bid = str(branch_id)
    pid = str(payload.provider_id)
    st = _parse_time(payload.start_time)
    et = _parse_time(payload.end_time)
    if st >= et:
        raise HTTPException(status_code=422, detail="start_time must be before end_time")
    _check_overlap(db, tid, bid, pid, payload.day_of_week, st, et)
    sid = str(generate_uuid())
    db.execute(
        text(
            "INSERT INTO hcs_provider_schedules "
            "(id, tenant_id, branch_id, provider_id, day_of_week, start_time, end_time, "
            "slot_duration_minutes, appointment_types, is_active, created_at, updated_at) "
            "VALUES (:id,:tid,:bid,:pid,:dow,:st,:et,:dur,:types::jsonb,true,NOW(),NOW())"
        ),
        dict(id=sid, tid=tid, bid=bid, pid=pid, dow=payload.day_of_week, st=st, et=et,
             dur=payload.slot_duration_minutes, types=json.dumps(payload.appointment_types)),
    )
    write_event_audit(db=db, actor_id=str(current_user.id), actor_type="staff",
                      event_type="schedule.created", entity_type="provider_schedule",
                      entity_id=sid, tenant_id=tid, branch_id=bid,
                      source_module="healthcare_scheduling")
    db.commit()
    row = db.execute(text("SELECT * FROM hcs_provider_schedules WHERE id = :id"), {"id": sid}).mappings().one()
    return ScheduleResponse(**dict(row))


@router.get(
    "/branches/{branch_id}/schedules",
    response_model=ScheduleListResponse,
    summary="List all branch schedules (weekly grid)",
)
async def list_schedules(
    branch_id: uuid.UUID,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager, HCRole.doctor])),
):
    tid = str(current_user.tenant_id)
    bid = str(branch_id)
    if _role == HCRole.doctor:
        rows = db.execute(text(
            "SELECT ps.* FROM hcs_provider_schedules ps "
            "JOIN hc_providers p ON p.id = ps.provider_id "
            "WHERE ps.tenant_id=:tid AND ps.branch_id=:bid AND ps.is_active=true "
            "AND p.user_id=:uid ORDER BY ps.day_of_week, ps.start_time"
        ), dict(tid=tid, bid=bid, uid=str(current_user.id))).mappings().all()
    else:
        rows = db.execute(text(
            "SELECT * FROM hcs_provider_schedules "
            "WHERE tenant_id=:tid AND branch_id=:bid AND is_active=true "
            "ORDER BY day_of_week, start_time"
        ), dict(tid=tid, bid=bid)).mappings().all()
    items = [ScheduleResponse(**dict(r)) for r in rows]
    return ScheduleListResponse(schedules=items, total=len(items))


@router.get(
    "/branches/{branch_id}/schedules/{provider_id}",
    response_model=ScheduleListResponse,
    summary="Get provider weekly schedule",
)
async def get_provider_schedule(
    branch_id: uuid.UUID,
    provider_id: uuid.UUID,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager, HCRole.doctor])),
):
    rows = db.execute(text(
        "SELECT * FROM hcs_provider_schedules "
        "WHERE tenant_id=:tid AND branch_id=:bid AND provider_id=:pid AND is_active=true "
        "ORDER BY day_of_week, start_time"
    ), dict(tid=str(current_user.tenant_id), bid=str(branch_id), pid=str(provider_id))).mappings().all()
    items = [ScheduleResponse(**dict(r)) for r in rows]
    return ScheduleListResponse(schedules=items, total=len(items))


@router.put(
    "/branches/{branch_id}/schedules/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Update schedule",
)
async def update_schedule(
    branch_id: uuid.UUID,
    schedule_id: uuid.UUID,
    payload: ScheduleUpdate,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission(_MANAGERS)),
):
    tid = str(current_user.tenant_id)
    sid = str(schedule_id)
    existing = db.execute(
        text("SELECT * FROM hcs_provider_schedules WHERE id=:id AND tenant_id=:tid"),
        dict(id=sid, tid=tid),
    ).mappings().one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Schedule not found")

    upd: dict = {}
    if payload.start_time is not None:
        upd["start_time"] = _parse_time(payload.start_time)
    if payload.end_time is not None:
        upd["end_time"] = _parse_time(payload.end_time)
    if payload.slot_duration_minutes is not None:
        upd["slot_duration_minutes"] = payload.slot_duration_minutes
    if payload.appointment_types is not None:
        upd["appointment_types"] = json.dumps(payload.appointment_types)
    if payload.is_active is not None:
        upd["is_active"] = payload.is_active

    if upd:
        new_st = upd.get("start_time", existing["start_time"])
        new_et = upd.get("end_time", existing["end_time"])
        _check_overlap(db, tid, str(branch_id), existing["provider_id"],
                       existing["day_of_week"], new_st, new_et, exclude_id=sid)
        set_clause = ", ".join(f"{k}=:{k}" for k in upd)
        upd["id"] = sid
        db.execute(text(f"UPDATE hcs_provider_schedules SET {set_clause}, updated_at=NOW() WHERE id=:id"), upd)
        write_event_audit(db=db, actor_id=str(current_user.id), actor_type="staff",
                          event_type="schedule.updated", entity_type="provider_schedule",
                          entity_id=sid, tenant_id=tid, branch_id=str(branch_id),
                          source_module="healthcare_scheduling")
        db.commit()

    row = db.execute(text("SELECT * FROM hcs_provider_schedules WHERE id=:id"), {"id": sid}).mappings().one()
    return ScheduleResponse(**dict(row))


@router.delete(
    "/branches/{branch_id}/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate schedule (soft delete)",
)
async def deactivate_schedule(
    branch_id: uuid.UUID,
    schedule_id: uuid.UUID,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission(_MANAGERS)),
):
    tid = str(current_user.tenant_id)
    sid = str(schedule_id)
    result = db.execute(
        text("UPDATE hcs_provider_schedules SET is_active=false, updated_at=NOW() WHERE id=:id AND tenant_id=:tid"),
        dict(id=sid, tid=tid),
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Schedule not found")
    write_event_audit(db=db, actor_id=str(current_user.id), actor_type="staff",
                      event_type="schedule.deactivated", entity_type="provider_schedule",
                      entity_id=sid, tenant_id=tid, branch_id=str(branch_id),
                      source_module="healthcare_scheduling")
    db.commit()


# ---------------------------------------------------------------------------
# T-HC-029 -- Date/Time Block
# ---------------------------------------------------------------------------

@router.post(
    "/branches/{branch_id}/schedules/{provider_id}/blocks",
    response_model=DateTimeBlockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Block a date/time range for provider (T-HC-029)",
)
async def block_datetime_range(
    branch_id: uuid.UUID,
    provider_id: uuid.UUID,
    payload: DateTimeBlockCreate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager, HCRole.doctor])),
):
    tid = str(current_user.tenant_id)
    bid = str(branch_id)
    pid = str(provider_id)

    # Doctors may only block their own schedule
    if _role == HCRole.doctor:
        check = db.execute(
            text("SELECT id FROM hc_providers WHERE user_id=:uid AND tenant_id=:tid AND id=:pid LIMIT 1"),
            dict(uid=str(current_user.id), tid=tid, pid=pid),
        ).fetchone()
        if not check:
            raise HTTPException(status_code=403, detail="Doctors may only block their own schedule")

    affected = db.execute(
        text(
            "SELECT id FROM hcs_appointments "
            "WHERE tenant_id=:tid AND branch_id=:bid AND provider_id=:pid "
            "AND status='confirmed' AND scheduled_at BETWEEN :start AND :end"
        ),
        dict(tid=tid, bid=bid, pid=pid, start=payload.start_datetime, end=payload.end_datetime),
    ).fetchall()
    flagged_ids = [str(r[0]) for r in affected]

    if flagged_ids:
        db.execute(
            text(
                "UPDATE hcs_appointments SET status='flagged_for_review', updated_at=NOW() "
                "WHERE id = ANY(:ids)"
            ),
            {"ids": flagged_ids},
        )
        # TODO: trigger notification workflow for flagged appointments (T-HC-033 integration)

    write_event_audit(
        db=db, actor_id=str(current_user.id), actor_type="staff",
        event_type="schedule.blocked", entity_type="provider",
        entity_id=pid, tenant_id=tid, branch_id=bid,
        source_module="healthcare_scheduling",
        metadata={
            "start_datetime": payload.start_datetime.isoformat(),
            "end_datetime": payload.end_datetime.isoformat(),
            "reason": payload.reason,
            "recurrence": payload.recurrence,
            "flagged_appointments": flagged_ids,
        },
    )
    db.commit()

    return DateTimeBlockResponse(
        provider_id=pid, branch_id=bid,
        start_datetime=payload.start_datetime, end_datetime=payload.end_datetime,
        reason=payload.reason, recurrence=payload.recurrence,
        flagged_appointment_ids=flagged_ids,
    )
