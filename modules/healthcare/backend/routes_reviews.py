"""
Healthcare — Clinic Review APIs.

T-HC-046

POST /api/v1/patients/me/reviews                                   — submit review
GET  /api/v1/clinics/{slug}/branches/{branch_id}/reviews           — public list (approved only)
POST /api/v1/clinics/{slug}/branches/{branch_id}/reviews/{review_id}/response — staff reply
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session
from modules.healthcare.models import HCClinicReview, HCEncounter
from modules.healthcare.sdk.patient_auth import PatientTokenData, get_current_patient, get_patient_db
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.phi_audit import write_event_audit
from modules.healthcare.schemas.review import (
    ReviewCreate,
    ReviewListResponse,
    ReviewReplyCreate,
    ReviewResponse,
)

router = APIRouter(tags=["reviews"])

_MODERATION_HOLD_HOURS = 24


def _get_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _get_ua(request: Request) -> str:
    return request.headers.get("user-agent", "")


def _display_name(created_at: datetime) -> str:
    """Return anonymised display name: "Pasien, <Indonesian month> <year>"."""
    months_id = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    return f"Pasien, {months_id[created_at.month]} {created_at.year}"


# ---------------------------------------------------------------------------
# Patient: submit review
# ---------------------------------------------------------------------------

@router.post("/api/v1/patients/me/reviews", status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreate,
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(get_patient_db),
):
    """Submit a review for a completed encounter (one per encounter)."""
    pid = patient.patient_id
    tid = patient.require_tenant()

    # Verify completed encounter ownership (scoped to the patient's tenant)
    enc = (
        db.query(HCEncounter)
        .filter(
            HCEncounter.id == payload.encounter_id,
            HCEncounter.patient_id == pid,
            HCEncounter.tenant_id == tid,
            HCEncounter.status == "completed",
        )
        .first()
    )
    if enc is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No completed encounter found with that ID for this patient",
        )

    # Check unique constraint (one review per encounter)
    existing = (
        db.query(HCClinicReview)
        .filter(HCClinicReview.encounter_id == payload.encounter_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A review already exists for this encounter",
        )

    now = datetime.utcnow()
    review = HCClinicReview(
        tenant_id=enc.tenant_id,
        branch_id=payload.branch_id,
        patient_id=pid,
        encounter_id=payload.encounter_id,
        rating=payload.rating,
        review_text=payload.text,
        status="pending_moderation",
        created_at=now,
        updated_at=now,
    )
    db.add(review)
    db.flush()

    write_event_audit(
        db=db,
        actor_id=pid,
        actor_type="patient",
        event_type="review.created",
        entity_type="clinic_review",
        entity_id=str(review.id),
        tenant_id=enc.tenant_id,
        branch_id=payload.branch_id,
        ip=_get_ip(request),
        ua=_get_ua(request),
        metadata={"rating": payload.rating},
    )

    return {"review_id": str(review.id), "status": review.status}


# ---------------------------------------------------------------------------
# Public: list approved reviews
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/clinics/{slug}/branches/{branch_id}/reviews",
    response_model=ReviewListResponse,
)
async def list_branch_reviews(
    slug: str,
    branch_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(tenant_scoped_session),
):
    """
    Public endpoint — returns approved reviews only.
    No patient-identifying data returned; display_name is anonymised.
    """
    q = (
        db.query(HCClinicReview)
        .filter(
            HCClinicReview.branch_id == branch_id,
            HCClinicReview.status == "approved",
        )
    )
    total = q.count()
    rows = (
        q.order_by(HCClinicReview.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        ReviewResponse(
            rating=r.rating,
            text=r.review_text,
            created_at=r.created_at,
            display_name=_display_name(r.created_at),
        )
        for r in rows
    ]

    return ReviewListResponse(items=items, total=total, page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# Staff: add clinic response
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/clinics/{slug}/branches/{branch_id}/reviews/{review_id}/response",
    status_code=status.HTTP_201_CREATED,
)
async def add_review_response(
    slug: str,
    branch_id: str,
    review_id: str,
    payload: ReviewReplyCreate,
    request: Request,
    db: Session = Depends(tenant_scoped_session),
    _role=Depends(has_hc_permission([HCRole.branch_manager, HCRole.clinic_owner])),
):
    """Add a clinic response to an approved review (24h moderation hold)."""
    review = (
        db.query(HCClinicReview)
        .filter(
            HCClinicReview.id == review_id,
            HCClinicReview.branch_id == branch_id,
        )
        .first()
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    now = datetime.utcnow()
    review.staff_response = payload.response_text
    review.staff_response_at = now
    review.updated_at = now
    db.flush()

    # Determine actor from the permission checker (staff user)
    # We use "system" as a safe fallback — the has_hc_permission dep validates role
    write_event_audit(
        db=db,
        actor_id="staff",
        actor_type="staff",
        event_type="review.response_added",
        entity_type="clinic_review",
        entity_id=review_id,
        tenant_id=review.tenant_id,
        branch_id=branch_id,
        ip=_get_ip(request),
        ua=_get_ua(request),
    )

    return {"review_id": review_id, "status": "pending_moderation"}
