from __future__ import annotations
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from modules.sdk.dependencies import tenant_scoped_session
from modules.healthcare.sdk.patient_auth import get_current_patient
from modules.healthcare.sdk.phi_audit import write_event_audit
from modules.healthcare.schemas.waitlist import WaitlistCreate, WaitlistResponse, WaitlistListResponse
from modules.sdk.db import generate_uuid

logger = logging.getLogger(__name__)

router = APIRouter(tags=["healthcare-scheduling-waitlist"])

_OFFER_WINDOW_MINUTES = 15


@router.post(
    "/api/v1/patients/me/waitlist",
    response_model=WaitlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Join waitlist (patient auth)",
)
async def join_waitlist(
    payload: WaitlistCreate,
    request: Request,
    db: Session = Depends(tenant_scoped_session),
    patient_token=Depends(get_current_patient),
):
    branch_row = db.execute(
        text("SELECT tenant_id FROM hc_branches WHERE id=:bid LIMIT 1"),
        {"bid": str(payload.branch_id)},
    ).fetchone()
    if not branch_row:
        raise HTTPException(status_code=404, detail="Branch not found")
    tenant_id = branch_row[0]
    entry_id = str(generate_uuid())
    db.execute(
        text(
            "INSERT INTO hcs_waitlist "
            "(id,tenant_id,branch_id,provider_id,patient_id,appointment_type,"
            "preferred_date,status,created_at,updated_at) "
            "VALUES (:id,:tid,:bid,:pid,:pat,:apt,:pdate,'waiting',NOW(),NOW())"
        ),
        dict(
            id=entry_id, tid=tenant_id, bid=str(payload.branch_id),
            pid=str(payload.provider_id) if payload.provider_id else None,
            pat=patient_token.patient_id, apt=payload.appointment_type,
            pdate=payload.preferred_date,
        ),
    )
    write_event_audit(db=db, actor_id=patient_token.patient_id, actor_type="patient",
                      event_type="waitlist.joined", entity_type="waitlist",
                      entity_id=entry_id, tenant_id=tenant_id,
                      branch_id=str(payload.branch_id), source_module="healthcare_scheduling")
    db.commit()
    row = db.execute(text("SELECT * FROM hcs_waitlist WHERE id=:id"), {"id": entry_id}).mappings().one()
    return WaitlistResponse(**dict(row))


@router.get(
    "/api/v1/patients/me/waitlist",
    response_model=WaitlistListResponse,
    summary="List patient waitlist entries",
)
async def list_waitlist(
    db: Session = Depends(tenant_scoped_session),
    patient_token=Depends(get_current_patient),
):
    rows = db.execute(
        text("SELECT * FROM hcs_waitlist WHERE patient_id=:pid ORDER BY created_at DESC"),
        {"pid": patient_token.patient_id},
    ).mappings().all()
    items = [WaitlistResponse(**dict(r)) for r in rows]
    return WaitlistListResponse(entries=items, total=len(items))


@router.delete(
    "/api/v1/patients/me/waitlist/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave waitlist (patient auth)",
)
async def leave_waitlist(
    entry_id: uuid.UUID,
    db: Session = Depends(tenant_scoped_session),
    patient_token=Depends(get_current_patient),
):
    eid = str(entry_id)
    row = db.execute(
        text("SELECT * FROM hcs_waitlist WHERE id=:id AND patient_id=:pid"),
        dict(id=eid, pid=patient_token.patient_id),
    ).mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Waitlist entry not found")
    db.execute(
        text("UPDATE hcs_waitlist SET status='removed', updated_at=NOW() WHERE id=:id"),
        {"id": eid},
    )
    write_event_audit(db=db, actor_id=patient_token.patient_id, actor_type="patient",
                      event_type="waitlist.left", entity_type="waitlist",
                      entity_id=eid, tenant_id=row["tenant_id"],
                      branch_id=row["branch_id"], source_module="healthcare_scheduling")
    db.commit()


def _offer_waitlist_next(slot_id: str, db: Session) -> None:
    # FIFO auto-offer on slot release.
    # Finds the oldest 'waiting' entry for same branch+provider+appointment_type
    # where preferred_date <= slot.slot_date. Sets status='offered', slot='held'.
    # Stores Redis key hc:waitlist_offer:{entry_id} with 15-min TTL.
    # Background expiry worker (stub -- out of scope Sprint 3):
    #   On key expiry re-run _offer_waitlist_next or release slot to 'available'.
    slot = db.execute(
        text("SELECT * FROM hcs_appointment_slots WHERE id=:sid FOR UPDATE"),
        {"sid": slot_id},
    ).mappings().one_or_none()
    if not slot or slot["status"] not in ("available",):
        return

    candidate = db.execute(
        text(
            "SELECT * FROM hcs_waitlist "
            "WHERE branch_id=:bid "
            "AND (:pid IS NULL OR provider_id=:pid) "
            "AND appointment_type=:apt "
            "AND preferred_date<=:sdate "
            "AND status='waiting' "
            "ORDER BY created_at ASC LIMIT 1"
        ),
        dict(bid=slot["branch_id"], pid=slot["provider_id"],
             apt=slot["appointment_type"], sdate=slot["slot_date"]),
    ).mappings().one_or_none()
    if not candidate:
        return

    offer_expires = datetime.utcnow() + timedelta(minutes=_OFFER_WINDOW_MINUTES)
    db.execute(
        text(
            "UPDATE hcs_waitlist SET status='offered', offered_slot_id=:sid, "
            "offer_expires_at=:exp, updated_at=NOW() WHERE id=:eid"
        ),
        dict(sid=slot_id, exp=offer_expires, eid=str(candidate["id"])),
    )
    db.execute(
        text("UPDATE hcs_appointment_slots SET status='held' WHERE id=:sid"),
        {"sid": slot_id},
    )
    write_event_audit(
        db=db, actor_id="system", actor_type="system",
        event_type="waitlist.offered", entity_type="waitlist",
        entity_id=str(candidate["id"]), tenant_id=candidate["tenant_id"],
        branch_id=str(candidate["branch_id"]), source_module="healthcare_scheduling",
        metadata={"slot_id": slot_id, "offer_expires_at": offer_expires.isoformat()},
    )

    # Store Redis TTL for background expiry worker
    try:
        import os, redis as _redis
        r = _redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
        r.setex(f"hc:waitlist_offer:{candidate['id']}", _OFFER_WINDOW_MINUTES * 60, slot_id)
    except Exception as exc:
        logger.warning("Redis TTL set failed for waitlist offer: %s", exc)

    try:
        from modules.healthcare.sdk.notification_service import NotificationService
        NotificationService(db=db, tenant_id=candidate["tenant_id"], branch_id=candidate["branch_id"])\
            .dispatch_waitlist_offer_notification(str(candidate["id"]))
    except Exception as exc:
        logger.warning("Waitlist offer notification failed: %s", exc)

    db.commit()
