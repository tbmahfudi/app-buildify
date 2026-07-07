from __future__ import annotations
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id
import json
import uuid
import logging
from datetime import time as dtime, date as ddate
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.branch_scope import healthcare_branch_session
from modules.healthcare.sdk.phi_audit import write_event_audit
from modules.healthcare.schemas.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleListResponse,
    DateTimeBlockCreate, DateTimeBlockResponse,
    ScheduleOverrideCreate, ScheduleOverrideResponse, ScheduleOverrideListResponse,
)
from modules.sdk.db import generate_uuid

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/healthcare_scheduling",
    tags=["healthcare-scheduling-schedules"],
)

_MANAGERS = [HCRole.clinic_owner, HCRole.branch_manager]
_VIEWERS = [HCRole.clinic_owner, HCRole.branch_manager, HCRole.doctor]

# Schedule rows always carry the assigned room's code/name for display.
_SCHED_SELECT = (
    "SELECT ps.*, r.code AS room_code, r.name AS room_name "
    "FROM hcs_provider_schedules ps "
    "LEFT JOIN hc_rooms r ON r.id = ps.room_id"
)
# Overrides carry the substitute provider's name for display.
_OVR_SELECT = (
    "SELECT o.*, sp.display_name AS substitute_provider_name "
    "FROM hcs_schedule_overrides o "
    "LEFT JOIN hc_providers sp ON sp.id = o.substitute_provider_id"
)


def _check_room_conflict(
    db: Session, tenant_id: str, branch_id: str, room_id: Optional[str],
    day_of_week: int, start_t: dtime, end_t: dtime,
    exclude_id: Optional[str] = None,
) -> None:
    """A room can host only one provider for a given weekday/time window."""
    if not room_id:
        return
    base = (
        "SELECT ps.id FROM hcs_provider_schedules ps "
        "WHERE ps.tenant_id=:tid AND ps.branch_id=:bid AND ps.room_id=:room "
        "AND ps.day_of_week=:dow AND ps.is_active=true "
        "AND NOT (ps.end_time <= :st OR ps.start_time >= :et)"
    )
    params = dict(tid=tenant_id, bid=branch_id, room=room_id, dow=day_of_week, st=start_t, et=end_t)
    if exclude_id:
        base += " AND ps.id != :excl"
        params["excl"] = exclude_id
    if db.execute(text(base), params).fetchone():
        raise HTTPException(
            status_code=409,
            detail="Room is already assigned to another provider for an overlapping time on this day",
        )


def _room_in_branch(db: Session, tenant_id: str, branch_id: str, room_id: str) -> None:
    ok = db.execute(
        text("SELECT id FROM hc_rooms WHERE id=:rid AND tenant_id=:tid AND branch_id=:bid AND is_active=true"),
        dict(rid=room_id, tid=tenant_id, bid=branch_id),
    ).fetchone()
    if not ok:
        raise HTTPException(status_code=422, detail="Room not found or not active in this branch")


def _provider_in_tenant(db: Session, tenant_id: str, provider_id: str) -> None:
    ok = db.execute(
        text("SELECT id FROM hc_providers WHERE id=:pid AND tenant_id=:tid"),
        dict(pid=provider_id, tid=tenant_id),
    ).fetchone()
    if not ok:
        raise HTTPException(status_code=422, detail="Provider not found")


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
    tid = hc_shared_tenant_id()
    bid = str(branch_id)
    pid = str(payload.provider_id)
    st = _parse_time(payload.start_time)
    et = _parse_time(payload.end_time)
    if st >= et:
        raise HTTPException(status_code=422, detail="start_time must be before end_time")
    _check_overlap(db, tid, bid, pid, payload.day_of_week, st, et)
    room_id = str(payload.room_id) if payload.room_id else None
    if room_id:
        _room_in_branch(db, tid, bid, room_id)
        _check_room_conflict(db, tid, bid, room_id, payload.day_of_week, st, et)
    sid = str(generate_uuid())
    db.execute(
        text(
            "INSERT INTO hcs_provider_schedules "
            "(id, tenant_id, branch_id, provider_id, day_of_week, start_time, end_time, "
            "slot_duration_minutes, appointment_types, room_id, is_active, created_at, updated_at) "
            "VALUES (:id,:tid,:bid,:pid,:dow,:st,:et,:dur,CAST(:types AS jsonb),:room,true,NOW(),NOW())"
        ),
        dict(id=sid, tid=tid, bid=bid, pid=pid, dow=payload.day_of_week, st=st, et=et,
             dur=payload.slot_duration_minutes, types=json.dumps(payload.appointment_types),
             room=room_id),
    )
    write_event_audit(db=db, actor_id=str(current_user.id), actor_type="staff",
                      event_type="schedule.created", entity_type="provider_schedule",
                      entity_id=sid, tenant_id=tid, branch_id=bid,
                      source_module="healthcare_scheduling")
    db.commit()
    row = db.execute(text(_SCHED_SELECT + " WHERE ps.id = :id"), {"id": sid}).mappings().one()
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
    tid = hc_shared_tenant_id()
    bid = str(branch_id)
    if _role == HCRole.doctor:
        rows = db.execute(text(
            _SCHED_SELECT +
            " JOIN hc_providers p ON p.id = ps.provider_id "
            "WHERE ps.tenant_id=:tid AND ps.branch_id=:bid AND ps.is_active=true "
            "AND p.user_id=:uid ORDER BY ps.day_of_week, ps.start_time"
        ), dict(tid=tid, bid=bid, uid=str(current_user.id))).mappings().all()
    else:
        rows = db.execute(text(
            _SCHED_SELECT +
            " WHERE ps.tenant_id=:tid AND ps.branch_id=:bid AND ps.is_active=true "
            "ORDER BY ps.day_of_week, ps.start_time"
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
        _SCHED_SELECT +
        " WHERE ps.tenant_id=:tid AND ps.branch_id=:bid AND ps.provider_id=:pid AND ps.is_active=true "
        "ORDER BY ps.day_of_week, ps.start_time"
    ), dict(tid=hc_shared_tenant_id(), bid=str(branch_id), pid=str(provider_id))).mappings().all()
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
    tid = hc_shared_tenant_id()
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
    # room_id is tri-state: clear_room wins, else a provided uuid assigns.
    if payload.clear_room:
        upd["room_id"] = None
    elif payload.room_id is not None:
        rid = str(payload.room_id)
        _room_in_branch(db, tid, str(branch_id), rid)
        upd["room_id"] = rid

    if upd:
        new_st = upd.get("start_time", existing["start_time"])
        new_et = upd.get("end_time", existing["end_time"])
        _check_overlap(db, tid, str(branch_id), existing["provider_id"],
                       existing["day_of_week"], new_st, new_et, exclude_id=sid)
        new_room = upd.get("room_id", existing["room_id"])
        _check_room_conflict(db, tid, str(branch_id), new_room,
                             existing["day_of_week"], new_st, new_et, exclude_id=sid)
        set_clause = ", ".join(
            (f"{k}=CAST(:{k} AS jsonb)" if k == "appointment_types" else f"{k}=:{k}")
            for k in upd
        )
        upd["id"] = sid
        db.execute(text(f"UPDATE hcs_provider_schedules SET {set_clause}, updated_at=NOW() WHERE id=:id"), upd)
        write_event_audit(db=db, actor_id=str(current_user.id), actor_type="staff",
                          event_type="schedule.updated", entity_type="provider_schedule",
                          entity_id=sid, tenant_id=tid, branch_id=str(branch_id),
                          source_module="healthcare_scheduling")
        db.commit()

    row = db.execute(text(_SCHED_SELECT + " WHERE ps.id=:id"), {"id": sid}).mappings().one()
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
    tid = hc_shared_tenant_id()
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
    tid = hc_shared_tenant_id()
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


# ---------------------------------------------------------------------------
# Per-date schedule overrides — substitution / unavailability
# A weekly schedule recurs every week; an override replaces (or cancels) the
# scheduled provider for ONE specific future date. day_of_week 0=Sunday..6=Sat.
# ---------------------------------------------------------------------------

def _dow_of(d: ddate) -> int:
    """Sunday=0..Saturday=6 (matches JS Date.getDay() and the seed convention)."""
    return (d.weekday() + 1) % 7


def _load_schedule(db: Session, tid: str, bid: str, sid: str) -> dict:
    row = db.execute(
        text("SELECT * FROM hcs_provider_schedules WHERE id=:id AND tenant_id=:tid AND branch_id=:bid"),
        dict(id=sid, tid=tid, bid=bid),
    ).mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return dict(row)


@router.post(
    "/branches/{branch_id}/schedules/{schedule_id}/overrides",
    response_model=ScheduleOverrideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a per-date override (unavailable / substitute doctor)",
)
async def create_override(
    branch_id: uuid.UUID,
    schedule_id: uuid.UUID,
    payload: ScheduleOverrideCreate,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission(_MANAGERS)),
):
    tid = hc_shared_tenant_id()
    bid = str(branch_id)
    sid = str(schedule_id)
    sched = _load_schedule(db, tid, bid, sid)

    if payload.override_date < ddate.today():
        raise HTTPException(status_code=422, detail="override_date must be today or in the future")
    if _dow_of(payload.override_date) != sched["day_of_week"]:
        raise HTTPException(
            status_code=422,
            detail="override_date must fall on the schedule's weekday",
        )

    sub_id = None
    if payload.status == "substituted":
        sub_id = str(payload.substitute_provider_id)
        if sub_id == str(sched["provider_id"]):
            raise HTTPException(status_code=422, detail="Substitute must differ from the scheduled provider")
        _provider_in_tenant(db, tid, sub_id)

    dup = db.execute(
        text("SELECT id FROM hcs_schedule_overrides WHERE schedule_id=:sid AND override_date=:d"),
        dict(sid=sid, d=payload.override_date),
    ).fetchone()
    if dup:
        raise HTTPException(status_code=409, detail="An override already exists for this schedule on that date")

    oid = str(generate_uuid())
    db.execute(
        text(
            "INSERT INTO hcs_schedule_overrides "
            "(id, tenant_id, branch_id, schedule_id, override_date, status, "
            " substitute_provider_id, reason, created_by, created_at, updated_at) "
            "VALUES (:id,:tid,:bid,:sid,:d,:st,:sub,:reason,:by,NOW(),NOW())"
        ),
        dict(id=oid, tid=tid, bid=bid, sid=sid, d=payload.override_date, st=payload.status,
             sub=sub_id, reason=payload.reason, by=str(current_user.id)),
    )
    write_event_audit(db=db, actor_id=str(current_user.id), actor_type="staff",
                      event_type="schedule.override.created", entity_type="schedule_override",
                      entity_id=oid, tenant_id=tid, branch_id=bid,
                      source_module="healthcare_scheduling")
    db.commit()
    row = db.execute(text(_OVR_SELECT + " WHERE o.id=:id"), {"id": oid}).mappings().one()
    return ScheduleOverrideResponse(**dict(row))


@router.get(
    "/branches/{branch_id}/schedules/{schedule_id}/overrides",
    response_model=ScheduleOverrideListResponse,
    summary="List overrides for a schedule (upcoming first)",
)
async def list_schedule_overrides(
    branch_id: uuid.UUID,
    schedule_id: uuid.UUID,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission(_VIEWERS)),
):
    rows = db.execute(
        text(
            _OVR_SELECT +
            " WHERE o.tenant_id=:tid AND o.branch_id=:bid AND o.schedule_id=:sid "
            "ORDER BY o.override_date"
        ),
        dict(tid=hc_shared_tenant_id(), bid=str(branch_id), sid=str(schedule_id)),
    ).mappings().all()
    items = [ScheduleOverrideResponse(**dict(r)) for r in rows]
    return ScheduleOverrideListResponse(overrides=items, total=len(items))


@router.get(
    "/branches/{branch_id}/schedule-overrides",
    response_model=ScheduleOverrideListResponse,
    summary="List all branch overrides in a date range",
)
async def list_branch_overrides(
    branch_id: uuid.UUID,
    date_from: Optional[ddate] = Query(None),
    date_to: Optional[ddate] = Query(None),
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission(_VIEWERS)),
):
    clauses = ["o.tenant_id=:tid", "o.branch_id=:bid"]
    params = dict(tid=hc_shared_tenant_id(), bid=str(branch_id))
    if date_from:
        clauses.append("o.override_date >= :df"); params["df"] = date_from
    if date_to:
        clauses.append("o.override_date <= :dt"); params["dt"] = date_to
    rows = db.execute(
        text(_OVR_SELECT + " WHERE " + " AND ".join(clauses) + " ORDER BY o.override_date"),
        params,
    ).mappings().all()
    items = [ScheduleOverrideResponse(**dict(r)) for r in rows]
    return ScheduleOverrideListResponse(overrides=items, total=len(items))


@router.delete(
    "/branches/{branch_id}/schedule-overrides/{override_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an override (revert to the normal weekly schedule)",
)
async def delete_override(
    branch_id: uuid.UUID,
    override_id: uuid.UUID,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _role=Depends(has_hc_permission(_MANAGERS)),
):
    tid = hc_shared_tenant_id()
    oid = str(override_id)
    result = db.execute(
        text("DELETE FROM hcs_schedule_overrides WHERE id=:id AND tenant_id=:tid AND branch_id=:bid"),
        dict(id=oid, tid=tid, bid=str(branch_id)),
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Override not found")
    write_event_audit(db=db, actor_id=str(current_user.id), actor_type="staff",
                      event_type="schedule.override.deleted", entity_type="schedule_override",
                      entity_id=oid, tenant_id=tid, branch_id=str(branch_id),
                      source_module="healthcare_scheduling")
    db.commit()
