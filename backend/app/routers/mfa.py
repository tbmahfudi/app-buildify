"""
MFA endpoints (ADR-011 S4) — enroll / verify / list / disable a second factor.

Platform-owned, authenticated (``get_current_user``). Enrolling a phone/email
factor sends an OTP to the target over the ADR-009 OTP service with
``purpose="mfa"``; the factor only becomes ``is_active`` after the returned code
is verified (sec-review-011 R5 — ownership is proven by the round-trip, never by
a client-asserted flag). Every enroll/verify/disable is audited with actor+IP+UA
(R10). Rate/cost caps + attempt lockout live in the OTP service (R6/R7).
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.audit import create_audit_log
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.routers import otp
from app.services import mfa_service

router = APIRouter(prefix="/api/v1/mfa", tags=["mfa"])


class MFAFactorResponse(BaseModel):
    id: str
    factor_type: str
    target: str
    is_active: bool

    @classmethod
    def from_model(cls, f) -> "MFAFactorResponse":
        return cls(id=str(f.id), factor_type=f.factor_type, target=f.target, is_active=f.is_active)


class MFAEnrollRequest(BaseModel):
    factor_type: str  # 'phone_otp' | 'email_otp'
    target: str  # phone number or email address


class MFAEnrollResponse(BaseModel):
    factor_id: str
    message: str
    resend_after: int


class MFAVerifyRequest(BaseModel):
    code: str


def _tenant_code(user: User) -> str:
    # MFA is platform/per-user, but the OTP buckets are keyed by a tenant namespace;
    # use the user's tenant when present so caps don't collide across tenants.
    return str(user.tenant_id) if user.tenant_id else "platform"


def _client_ip(request: Request) -> Optional[str]:
    return request.client.host if request.client else None


@router.get("/factors", response_model=List[MFAFactorResponse])
def list_mfa_factors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    factors = mfa_service.list_factors(db, current_user.id)
    return [MFAFactorResponse.from_model(f) for f in factors]


@router.post("/factors", response_model=MFAEnrollResponse)
def enroll_mfa_factor(
    body: MFAEnrollRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enroll a pending factor and send a verification code to its target (R5)."""
    try:
        factor, channel = mfa_service.get_or_create_pending_factor(
            db, user_id=current_user.id, factor_type=body.factor_type, target=body.target
        )
    except mfa_service.InvalidFactorError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except mfa_service.AlreadyEnrolledError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This factor is already enrolled and active"
        )

    # Ownership is only proven by the send->verify round-trip; the row stays
    # inactive until POST /factors/{id}/verify succeeds.
    resend_after = otp.send_otp(
        channel=channel,
        target=factor.target,
        purpose="mfa",
        tenant_code=_tenant_code(current_user),
        account_id=str(current_user.id),
        ip=_client_ip(request),
    )

    create_audit_log(
        db=db,
        action="mfa_enroll",
        user=current_user,
        entity_type="user_mfa_factor",
        entity_id=str(factor.id),
        changes={"factor_type": factor.factor_type},
        request=request,
        status="success",
    )
    return MFAEnrollResponse(
        factor_id=str(factor.id), message="Verification code sent", resend_after=resend_after
    )


@router.post("/factors/{factor_id}/resend", response_model=MFAEnrollResponse)
def resend_mfa_code(
    factor_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-send the enrollment code (cooldown enforced by the OTP service, R6)."""
    factor = mfa_service.get_factor(db, current_user.id, factor_id)
    if factor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factor not found")
    if factor.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Factor already verified")

    channel = mfa_service.channel_for_factor(factor.factor_type)
    resend_after = otp.send_otp(
        channel=channel,
        target=factor.target,
        purpose="mfa",
        tenant_code=_tenant_code(current_user),
        account_id=str(current_user.id),
        ip=_client_ip(request),
    )
    create_audit_log(
        db=db,
        action="mfa_resend",
        user=current_user,
        entity_type="user_mfa_factor",
        entity_id=str(factor.id),
        request=request,
        status="success",
    )
    return MFAEnrollResponse(
        factor_id=str(factor.id), message="Verification code re-sent", resend_after=resend_after
    )


@router.post("/factors/{factor_id}/verify", response_model=MFAFactorResponse)
def verify_mfa_factor(
    factor_id: str,
    body: MFAVerifyRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify the code and activate the factor (R5 ownership proof)."""
    factor = mfa_service.get_factor(db, current_user.id, factor_id)
    if factor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factor not found")

    if factor.is_active:
        # Idempotent: already proven; nothing to do.
        return MFAFactorResponse.from_model(factor)

    channel = mfa_service.channel_for_factor(factor.factor_type)
    try:
        otp.verify_otp(
            channel=channel,
            target=factor.target,
            purpose="mfa",
            tenant_code=_tenant_code(current_user),
            code=body.code,
        )
    except HTTPException:
        # Generic failure surfaced by the OTP service (R7); audit the attempt.
        create_audit_log(
            db=db,
            action="mfa_verify",
            user=current_user,
            entity_type="user_mfa_factor",
            entity_id=str(factor.id),
            request=request,
            status="failure",
        )
        raise

    factor = mfa_service.activate_factor(db, factor)
    create_audit_log(
        db=db,
        action="mfa_verify",
        user=current_user,
        entity_type="user_mfa_factor",
        entity_id=str(factor.id),
        changes={"factor_type": factor.factor_type},
        request=request,
        status="success",
    )
    return MFAFactorResponse.from_model(factor)


@router.delete("/factors/{factor_id}")
def disable_mfa_factor(
    factor_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a factor (R10 audited)."""
    removed = mfa_service.disable_factor(db, current_user.id, factor_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factor not found")
    create_audit_log(
        db=db,
        action="mfa_disable",
        user=current_user,
        entity_type="user_mfa_factor",
        entity_id=str(factor_id),
        request=request,
        status="success",
    )
    return {"message": "Factor removed"}
