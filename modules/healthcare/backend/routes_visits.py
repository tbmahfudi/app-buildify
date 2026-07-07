"""
Healthcare — Visit Registration & Queue Management API.

Epic-09 / ADR-HC-006. Staff-facing (clinic portal). All routes branch-scoped
(X-Branch-ID) with hc_branch_staff RBAC. Queue board = short-poll + queue_version.

    POST /branches/{b}/visits/check-in                 (from appointment)
    POST /branches/{b}/visits/walk-in
    PUT  /branches/{b}/visits/{v}/payment
    PUT  /branches/{b}/visits/{v}/referral
    POST /branches/{b}/visits/{v}/queue-ticket
    GET  /branches/{b}/queue?department_id=&station=
    POST /branches/{b}/queue-tickets/{t}/call | skip | recall
    POST /branches/{b}/queue-tickets/{t}/transfer
    POST /branches/{b}/visits/{v}/encounter            (hand-off to EMR)
"""
from __future__ import annotations
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id

import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import get_current_user, tenant_scoped_session
from modules.healthcare.models import (
    HCDepartment,
    HCEncounter,
    HCPatient,
    HCProvider,
    HCQueueTicket,
    HCVisit,
)
from modules.healthcare.schemas.visit import (
    CheckInRequest,
    EncounterHandoffRequest,
    EncounterHandoffResponse,
    PatientPickerItem,
    PaymentUpdate,
    QueueBoardResponse,
    QueueTicketRequest,
    QueueTicketResponse,
    ReferralUpdate,
    TransferRequest,
    VisitResponse,
    WalkInRequest,
)
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.branch_scope import healthcare_branch_session
from modules.healthcare.sdk.phi_audit import write_event_audit

router = APIRouter(prefix="/api/v1/modules/healthcare", tags=["healthcare-registration"])

_FRONT_DESK = [HCRole.clinic_owner, HCRole.branch_manager, HCRole.nurse, HCRole.billing_staff]
_CLINICAL = [HCRole.clinic_owner, HCRole.branch_manager, HCRole.doctor, HCRole.nurse]


def _audit(db, request, user, branch_id, event, etype, eid):
    write_event_audit(
        db=db, actor_id=str(user.id), actor_type="staff", event_type=event,
        entity_type=etype, entity_id=str(eid), tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch_id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )


def _get_dept(db, tenant_id, branch_id, department_id) -> HCDepartment:
    dept = (
        db.query(HCDepartment)
        .filter(HCDepartment.id == department_id, HCDepartment.tenant_id == tenant_id,
                HCDepartment.branch_id == str(branch_id), HCDepartment.is_active == True)
        .first()
    )
    if not dept:
        raise HTTPException(status_code=422, detail="Active department not found in this branch")
    return dept


def _get_visit(db, tenant_id, branch_id, visit_id) -> HCVisit:
    visit = (
        db.query(HCVisit)
        .filter(HCVisit.id == str(visit_id), HCVisit.tenant_id == tenant_id,
                HCVisit.branch_id == str(branch_id))
        .first()
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit


def _get_ticket(db, tenant_id, branch_id, ticket_id) -> HCQueueTicket:
    t = (
        db.query(HCQueueTicket)
        .filter(HCQueueTicket.id == str(ticket_id), HCQueueTicket.tenant_id == tenant_id,
                HCQueueTicket.branch_id == str(branch_id))
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Queue ticket not found")
    return t


def _mask_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    return ("*" * max(0, len(phone) - 4)) + phone[-4:]


# ---------------------------------------------------------------------------
# Patient picker (front-desk registration helper)
# ---------------------------------------------------------------------------

@router.get("/patients", response_model=list[PatientPickerItem],
            summary="Search tenant patients for registration (masked)")
async def list_patients(q: str = Query("", max_length=100), page_size: int = Query(20, ge=1, le=50),
                        request: Request = None, db: Session = Depends(tenant_scoped_session),
                        current_user=Depends(get_current_user),
                        _=Depends(has_hc_permission(_FRONT_DESK + [HCRole.doctor]))):
    tid = hc_shared_tenant_id()
    # Company isolation (ADR-HC-010): the registry is keyed by Company under the shared
    # SaaS tenant. RLS enforces this, but the dev DB role bypasses RLS, so fence the
    # enumeration on the caller's Company explicitly (defence-in-depth in prod too).
    from modules.healthcare.sdk.branch_scope import resolve_caller_company_id
    caller_company = resolve_caller_company_id(db, str(current_user.id))
    if not caller_company:
        return []  # fail-closed: no resolvable Company -> no registry access
    # full_name is encrypted → cannot WHERE on it; filter in Python over a
    # bounded recent set. Acceptable for the front-desk picker at MVP scale.
    rows = (
        db.query(HCPatient)
        .filter(HCPatient.tenant_id == tid, HCPatient.company_id == caller_company,
                HCPatient.deleted_at.is_(None), HCPatient.status == "active")
        .order_by(HCPatient.created_at.desc())
        .limit(200)
        .all()
    )
    ql = q.lower().strip()
    items = []
    for p in rows:
        name = p.full_name or ""
        if ql and ql not in name.lower():
            continue
        items.append(PatientPickerItem(id=p.id, full_name=name, masked_phone=_mask_phone(p.phone)))
        if len(items) >= page_size:
            break
    return items


# ---------------------------------------------------------------------------
# Registration — check-in / walk-in
# ---------------------------------------------------------------------------

@router.post("/branches/{branch_id}/visits/check-in", response_model=VisitResponse,
             status_code=status.HTTP_201_CREATED, summary="Check in a patient from an appointment")
async def check_in(branch_id: uuid.UUID, payload: CheckInRequest, request: Request,
                   db: Session = Depends(healthcare_branch_session),
                   current_user=Depends(get_current_user),
                   _=Depends(has_hc_permission(_FRONT_DESK))):
    tid = hc_shared_tenant_id()
    _get_dept(db, tid, branch_id, payload.department_id)
    row = db.execute(
        text(
            "SELECT patient_id, status FROM hcs_appointments "
            "WHERE id=:id AND tenant_id=:tid AND branch_id=:bid"
        ),
        {"id": payload.appointment_id, "tid": tid, "bid": str(branch_id)},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=422, detail="Appointment not found in this branch")
    if db.query(HCVisit).filter(HCVisit.appointment_id == payload.appointment_id,
                                HCVisit.tenant_id == tid).first():
        raise HTTPException(status_code=409, detail="Appointment already checked in")

    visit = HCVisit(
        tenant_id=tid, branch_id=str(branch_id), patient_id=str(row[0]),
        appointment_id=payload.appointment_id, visit_type="appointment",
        payment_category=payload.payment_category,
        insurance_profile_id=payload.insurance_profile_id,
        department_id=payload.department_id, status="registered",
    )
    db.add(visit); db.flush()
    _audit(db, request, current_user, branch_id, "visit.checked_in", "visit", visit.id)
    db.commit(); db.refresh(visit)
    return visit


@router.post("/branches/{branch_id}/visits/walk-in", response_model=VisitResponse,
             status_code=status.HTTP_201_CREATED, summary="Register a walk-in patient")
async def walk_in(branch_id: uuid.UUID, payload: WalkInRequest, request: Request,
                  db: Session = Depends(healthcare_branch_session),
                  current_user=Depends(get_current_user),
                  _=Depends(has_hc_permission(_FRONT_DESK))):
    tid = hc_shared_tenant_id()
    _get_dept(db, tid, branch_id, payload.department_id)
    pat = db.execute(
        text(
            "SELECT id FROM hc_patients WHERE id=:id AND tenant_id=:tid AND deleted_at IS NULL"
        ),
        {"id": payload.patient_id, "tid": tid},
    ).fetchone()
    if not pat:
        raise HTTPException(status_code=422, detail="Patient not found in this tenant")

    visit = HCVisit(
        tenant_id=tid, branch_id=str(branch_id), patient_id=payload.patient_id,
        appointment_id=None, visit_type="walk_in",
        payment_category=payload.payment_category,
        insurance_profile_id=payload.insurance_profile_id,
        referral_source=payload.referral_source or "self",
        department_id=payload.department_id, status="registered",
    )
    db.add(visit); db.flush()
    _audit(db, request, current_user, branch_id, "visit.walk_in", "visit", visit.id)
    db.commit(); db.refresh(visit)
    return visit


@router.put("/branches/{branch_id}/visits/{visit_id}/payment", response_model=VisitResponse,
            summary="Set the visit payment category / insurance")
async def set_payment(branch_id: uuid.UUID, visit_id: uuid.UUID, payload: PaymentUpdate,
                      request: Request, db: Session = Depends(healthcare_branch_session),
                      current_user=Depends(get_current_user),
                      _=Depends(has_hc_permission(_FRONT_DESK))):
    tid = hc_shared_tenant_id()
    visit = _get_visit(db, tid, branch_id, visit_id)
    visit.payment_category = payload.payment_category
    visit.insurance_profile_id = payload.insurance_profile_id
    _audit(db, request, current_user, branch_id, "visit.payment_set", "visit", visit.id)
    db.commit(); db.refresh(visit)
    return visit


@router.put("/branches/{branch_id}/visits/{visit_id}/referral", response_model=VisitResponse,
            summary="Set the visit referral source")
async def set_referral(branch_id: uuid.UUID, visit_id: uuid.UUID, payload: ReferralUpdate,
                       request: Request, db: Session = Depends(healthcare_branch_session),
                       current_user=Depends(get_current_user),
                       _=Depends(has_hc_permission(_FRONT_DESK))):
    tid = hc_shared_tenant_id()
    visit = _get_visit(db, tid, branch_id, visit_id)
    visit.referral_source = payload.referral_source
    _audit(db, request, current_user, branch_id, "visit.referral_set", "visit", visit.id)
    db.commit(); db.refresh(visit)
    return visit


# ---------------------------------------------------------------------------
# Queue — ticket issuance, board, lifecycle
# ---------------------------------------------------------------------------

def _next_ticket_number(db, tid, branch_id, dept: HCDepartment, day: date) -> str:
    n = (
        db.query(func.count(HCQueueTicket.id))
        .filter(HCQueueTicket.tenant_id == tid, HCQueueTicket.branch_id == str(branch_id),
                HCQueueTicket.department_id == dept.id, HCQueueTicket.service_day == day)
        .scalar()
    ) or 0
    prefix = (dept.code[:3].upper() if dept.code else "GEN")
    return f"{prefix}{n + 1:03d}"


@router.post("/branches/{branch_id}/visits/{visit_id}/queue-ticket",
             response_model=QueueTicketResponse, status_code=status.HTTP_201_CREATED,
             summary="Issue a queue ticket for a visit")
async def issue_ticket(branch_id: uuid.UUID, visit_id: uuid.UUID, payload: QueueTicketRequest,
                       request: Request, db: Session = Depends(healthcare_branch_session),
                       current_user=Depends(get_current_user),
                       _=Depends(has_hc_permission(_FRONT_DESK))):
    tid = hc_shared_tenant_id()
    visit = _get_visit(db, tid, branch_id, visit_id)
    dept = _get_dept(db, tid, branch_id, visit.department_id)
    day = datetime.utcnow().date()
    ticket = HCQueueTicket(
        tenant_id=tid, branch_id=str(branch_id), visit_id=visit.id, department_id=dept.id,
        ticket_number=_next_ticket_number(db, tid, branch_id, dept, day),
        station=payload.station, status="waiting", service_day=day,
    )
    db.add(ticket)
    visit.status = "waiting"
    db.flush()
    _audit(db, request, current_user, branch_id, "queue.ticket_issued", "queue_ticket", ticket.id)
    db.commit(); db.refresh(ticket)
    return ticket


@router.get("/branches/{branch_id}/queue", response_model=QueueBoardResponse,
            summary="Queue board for a department (today), with queue_version")
async def queue_board(branch_id: uuid.UUID, department_id: str = Query(...),
                      station: Optional[str] = Query(None),
                      db: Session = Depends(healthcare_branch_session),
                      current_user=Depends(get_current_user),
                      _=Depends(has_hc_permission(list(HCRole)))):
    tid = hc_shared_tenant_id()
    day = datetime.utcnow().date()
    q = db.query(HCQueueTicket).filter(
        HCQueueTicket.tenant_id == tid, HCQueueTicket.branch_id == str(branch_id),
        HCQueueTicket.department_id == department_id, HCQueueTicket.service_day == day,
    )
    if station:
        q = q.filter(HCQueueTicket.station == station)
    tickets = q.order_by(HCQueueTicket.created_at).all()
    version = (
        db.query(func.max(HCQueueTicket.updated_at))
        .filter(HCQueueTicket.tenant_id == tid, HCQueueTicket.branch_id == str(branch_id),
                HCQueueTicket.department_id == department_id, HCQueueTicket.service_day == day)
        .scalar()
    )
    return QueueBoardResponse(department_id=department_id, service_day=day,
                              queue_version=version, tickets=tickets)


def _transition(db, request, current_user, branch_id, ticket_id, allowed_from, new_status, event,
                set_called=False, set_served=False):
    tid = hc_shared_tenant_id()
    t = _get_ticket(db, tid, branch_id, ticket_id)
    if t.status not in allowed_from:
        raise HTTPException(status_code=409,
                            detail=f"Cannot {new_status} a ticket in status '{t.status}'")
    t.status = new_status
    if set_called:
        t.called_at = datetime.utcnow()
    if set_served:
        t.served_at = datetime.utcnow()
    _audit(db, request, current_user, branch_id, event, "queue_ticket", t.id)
    db.commit(); db.refresh(t)
    return t


@router.post("/branches/{branch_id}/queue-tickets/{ticket_id}/call",
             response_model=QueueTicketResponse, summary="Call a waiting/recalled ticket")
async def call_ticket(branch_id: uuid.UUID, ticket_id: uuid.UUID, request: Request,
                      db: Session = Depends(healthcare_branch_session),
                      current_user=Depends(get_current_user),
                      _=Depends(has_hc_permission(_FRONT_DESK))):
    return _transition(db, request, current_user, branch_id, ticket_id,
                       ("waiting", "recalled"), "called", "queue.called", set_called=True)


@router.post("/branches/{branch_id}/queue-tickets/{ticket_id}/skip",
             response_model=QueueTicketResponse, summary="Skip a called ticket")
async def skip_ticket(branch_id: uuid.UUID, ticket_id: uuid.UUID, request: Request,
                      db: Session = Depends(healthcare_branch_session),
                      current_user=Depends(get_current_user),
                      _=Depends(has_hc_permission(_FRONT_DESK))):
    return _transition(db, request, current_user, branch_id, ticket_id,
                       ("called",), "skipped", "queue.skipped")


@router.post("/branches/{branch_id}/queue-tickets/{ticket_id}/recall",
             response_model=QueueTicketResponse, summary="Recall a skipped ticket")
async def recall_ticket(branch_id: uuid.UUID, ticket_id: uuid.UUID, request: Request,
                        db: Session = Depends(healthcare_branch_session),
                        current_user=Depends(get_current_user),
                        _=Depends(has_hc_permission(_FRONT_DESK))):
    return _transition(db, request, current_user, branch_id, ticket_id,
                       ("skipped",), "recalled", "queue.recalled")


@router.post("/branches/{branch_id}/queue-tickets/{ticket_id}/serve",
             response_model=QueueTicketResponse, summary="Mark a called ticket served")
async def serve_ticket(branch_id: uuid.UUID, ticket_id: uuid.UUID, request: Request,
                       db: Session = Depends(healthcare_branch_session),
                       current_user=Depends(get_current_user),
                       _=Depends(has_hc_permission(_FRONT_DESK))):
    return _transition(db, request, current_user, branch_id, ticket_id,
                       ("called", "recalled"), "served", "queue.served", set_served=True)


@router.post("/branches/{branch_id}/queue-tickets/{ticket_id}/transfer",
             response_model=QueueTicketResponse, status_code=status.HTTP_201_CREATED,
             summary="Transfer a ticket to another department (closes it, issues a new one)")
async def transfer_ticket(branch_id: uuid.UUID, ticket_id: uuid.UUID, payload: TransferRequest,
                          request: Request, db: Session = Depends(healthcare_branch_session),
                          current_user=Depends(get_current_user),
                          _=Depends(has_hc_permission(_FRONT_DESK))):
    tid = hc_shared_tenant_id()
    src = _get_ticket(db, tid, branch_id, ticket_id)
    if src.status in ("transferred", "served"):
        raise HTTPException(status_code=409, detail=f"Ticket already {src.status}")
    target = _get_dept(db, tid, branch_id, payload.department_id)
    day = datetime.utcnow().date()
    new_ticket = HCQueueTicket(
        tenant_id=tid, branch_id=str(branch_id), visit_id=src.visit_id, department_id=target.id,
        ticket_number=_next_ticket_number(db, tid, branch_id, target, day),
        station=payload.station, status="waiting", service_day=day,
    )
    db.add(new_ticket); db.flush()
    src.status = "transferred"
    src.transferred_to_id = new_ticket.id
    # Route the visit to the target department
    visit = _get_visit(db, tid, branch_id, src.visit_id)
    visit.department_id = target.id
    _audit(db, request, current_user, branch_id, "queue.transferred", "queue_ticket", new_ticket.id)
    db.commit(); db.refresh(new_ticket)
    return new_ticket


# ---------------------------------------------------------------------------
# Hand-off to EMR — open an encounter for the visit
# ---------------------------------------------------------------------------

@router.post("/branches/{branch_id}/visits/{visit_id}/encounter",
             response_model=EncounterHandoffResponse, status_code=status.HTTP_201_CREATED,
             summary="Open a clinical encounter for a visit (hand-off to EMR)")
async def open_encounter(branch_id: uuid.UUID, visit_id: uuid.UUID,
                         payload: EncounterHandoffRequest, request: Request,
                         db: Session = Depends(healthcare_branch_session),
                         current_user=Depends(get_current_user),
                         _=Depends(has_hc_permission(_CLINICAL))):
    tid = hc_shared_tenant_id()
    visit = _get_visit(db, tid, branch_id, visit_id)
    if visit.encounter_id:
        raise HTTPException(status_code=409, detail="Visit already has an encounter")

    provider_id = payload.provider_id
    if not provider_id:
        prov = (
            db.query(HCProvider)
            .filter(HCProvider.user_id == str(current_user.id), HCProvider.tenant_id == tid,
                    HCProvider.branch_id == str(branch_id))
            .first()
        )
        provider_id = prov.id if prov else None
    if not provider_id:
        raise HTTPException(status_code=422,
                            detail="provider_id required (no provider record for the caller)")

    enc = HCEncounter(
        id=str(uuid.uuid4()), tenant_id=tid, branch_id=str(branch_id),
        patient_id=visit.patient_id, provider_id=provider_id,
        appointment_id=visit.appointment_id, status="in_progress",
        started_at=datetime.utcnow(),
    )
    db.add(enc); db.flush()
    visit.encounter_id = enc.id
    visit.status = "in_service"
    _audit(db, request, current_user, branch_id, "visit.encounter_opened", "encounter", enc.id)
    db.commit()
    return EncounterHandoffResponse(visit_id=visit.id, encounter_id=enc.id, status=visit.status)
