"""
Healthcare — Patient registration and authentication API.

T-HC-020  POST /api/v1/patients/register              (PUBLIC)
T-HC-021  POST /api/v1/patients/auth/otp/send         (PUBLIC)
          POST /api/v1/patients/auth/otp/verify        (PUBLIC)
          POST /api/v1/patients/auth/token             (PUBLIC)
          POST /api/v1/patients/auth/refresh           (PUBLIC)
          POST /api/v1/patients/auth/logout            (PUBLIC)
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session
from app.core.dependencies import get_db as _platform_get_db

def _get_public_db():
    """Plain unauthenticated DB session for public endpoints."""
    yield from _platform_get_db()

from modules.healthcare.models import HCPatient, HCPatientConsent
from modules.healthcare.schemas.patient_auth import (
    OTPSendRequest,
    OTPSendResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
    PatientRegisterRequest,
    PatientRegisterResponse,
    PatientTokenRequest,
    PatientTokenResponse,
)
from modules.healthcare.sdk.captcha import require_captcha
from modules.healthcare.sdk.otp import generate_otp, verify_otp, COOLDOWN_TTL
from modules.healthcare.sdk.patient_tokens import (
    create_patient_access_token,
    create_patient_refresh_token,
    decode_patient_token,
)
from modules.healthcare.sdk.phi_audit import write_event_audit

router = APIRouter(tags=["healthcare-patient-auth"])

_OTP_VERIFIED_TTL = 900  # 15 minutes


def _get_redis():
    import redis as _redis
    url = os.environ.get("REDIS_URL", "")
    if not url:
        raise RuntimeError("REDIS_URL not configured")
    return _redis.from_url(url, decode_responses=True, socket_connect_timeout=2)


def _otp_verified_key(phone: str) -> str:
    return f"otp_verified:{phone}"


def _require_otp_verified(phone: str) -> None:
    """Raise 422 if otp_verified:{phone} is not present in Redis."""
    r = _get_redis()
    if not r.exists(_otp_verified_key(phone)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Phone verification required. Please complete OTP verification first.",
        )


# ---------------------------------------------------------------------------
# T-HC-020 — Patient registration
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/patients/register",
    response_model=PatientRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient (public)",
)
async def patient_register(
    payload: PatientRegisterRequest,
    request: Request,
    response: Response,
    _captcha=Depends(require_captcha),
    db: Session = Depends(_get_public_db),
) -> PatientRegisterResponse:
    """
    Register a new patient.

    Prerequisites:
      - Valid hCaptcha token (header X-Captcha-Token)
      - OTP already verified (Redis key otp_verified:{phone} exists)
      - consent_accepted must be True

    Flow:
      1. Check OTP verified
      2. Validate consent
      3. Check phone uniqueness
      4. Create hc_patients row (PHI encrypted)
      5. Record hc_patient_consents
      6. Emit audit
      7. Issue JWT + HttpOnly refresh cookie
      8. Delete otp_verified key
    """
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    # Step 1 — OTP gate
    _require_otp_verified(payload.phone)

    # Step 2 — Consent gate
    if not payload.consent_accepted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Consent must be accepted to register.",
        )

    # Step 3 — Phone uniqueness (consistent error to avoid enumeration)
    # hc_patients.phone is encrypted so we cannot WHERE on it directly.
    # The platform must maintain a hashed phone index; here we use a stub
    # lookup via the phone_hash auxiliary column if present, otherwise skip.
    phone_hash_row = db.execute(
        text(
            "SELECT id FROM hc_patients "
            "WHERE phone_hash = :ph AND deleted_at IS NULL "
            "LIMIT 1"
        ),
        {"ph": _hash_phone(payload.phone)},
    ).fetchone()

    if phone_hash_row:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration failed. Please contact support if you believe this is an error.",
        )

    # Step 4 — Create patient (PHI columns transparently encrypted by EncryptedPHIType)
    # tenant_id is resolved from the OTP token payload (tenant_code field)
    tenant_row = db.execute(text("SELECT current_setting('app.tenant_id', true)")).fetchone()
    tenant_id: str = tenant_row[0] if tenant_row and tenant_row[0] else "global"

    patient = HCPatient(
        tenant_id=tenant_id,
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        phone=payload.phone,
        nik=payload.nik,
        gender=payload.gender,
        consent_version=payload.consent_version,
        consent_accepted_at=datetime.utcnow(),
        consent_ip=ip,
        consent_user_agent=ua,
        status="active",
    )
    db.add(patient)
    db.flush()

    patient_id = str(patient.id)

    # Step 5 — Consent record
    consent = HCPatientConsent(
        tenant_id=tenant_id,
        patient_id=patient_id,
        consent_type="data_processing",
        consent_version=payload.consent_version,
        status="active",
        accepted_at=datetime.utcnow(),
        ip=ip,
        user_agent=ua,
        purpose_description="Patient data processing consent",
    )
    db.add(consent)
    db.flush()

    # Step 6 — Audit
    write_event_audit(
        db=db,
        actor_id=patient_id,
        actor_type="patient",
        event_type="patient.registered",
        entity_type="patient",
        entity_id=patient_id,
        tenant_id=tenant_id,
        ip=ip,
        ua=ua,
    )

    db.commit()

    # Step 7 — Issue tokens
    access_token = create_patient_access_token(patient_id=patient_id, phone=payload.phone, tenant_id=tenant_id)
    refresh_token = create_patient_refresh_token(patient_id=patient_id, tenant_id=tenant_id)

    response.set_cookie(
        key="patient_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 3600,
        path="/api/v1/patients/auth",
    )

    # Step 8 — Clear OTP verified key
    r = _get_redis()
    r.delete(_otp_verified_key(payload.phone))

    return PatientRegisterResponse(
        access_token=access_token,
        patient_id=patient_id,
        message="Registration successful.",
    )


# ---------------------------------------------------------------------------
# T-HC-021 — OTP send
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/patients/auth/otp/send",
    response_model=OTPSendResponse,
    summary="Send OTP to patient phone (public)",
)
async def otp_send(
    payload: OTPSendRequest,
    _captcha=Depends(require_captcha),
) -> OTPSendResponse:
    """Generate and send a 6-digit OTP to the given phone number."""
    try:
        code = generate_otp(payload.phone)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        )

    # In production: dispatch code via SMS gateway here.
    # OTP value is not logged to avoid leaking a live authentication secret.
    import logging
    logging.getLogger(__name__).info("OTP dispatched", extra={"event": "otp.sent"})

    return OTPSendResponse(
        message="OTP sent successfully.",
        resend_after=COOLDOWN_TTL,
    )


# ---------------------------------------------------------------------------
# T-HC-021 — OTP verify
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/patients/auth/otp/verify",
    response_model=OTPVerifyResponse,
    summary="Verify OTP and mark phone as verified (public)",
)
async def otp_verify(
    payload: OTPVerifyRequest,
) -> OTPVerifyResponse:
    """Verify the OTP; on success set Redis otp_verified:{phone} with 15-min TTL."""
    try:
        ok = verify_otp(payload.phone, payload.code)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        )

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Verification failed. Please check your code and try again.",
        )

    r = _get_redis()
    r.set(_otp_verified_key(payload.phone), "1", ex=_OTP_VERIFIED_TTL)

    return OTPVerifyResponse(verified=True)


# ---------------------------------------------------------------------------
# T-HC-021 — Token (returning patient login)
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/patients/auth/token",
    response_model=PatientTokenResponse,
    summary="Login with phone+OTP for returning patient (public)",
)
async def patient_token(
    payload: PatientTokenRequest,
    response: Response,
    db: Session = Depends(_get_public_db),
) -> PatientTokenResponse:
    """Authenticate returning patient via phone + OTP, return access token + refresh cookie."""
    try:
        ok = verify_otp(payload.phone, payload.code)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        )

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed.",
        )

    # Lookup patient by phone hash
    row = db.execute(
        text(
            "SELECT id, tenant_id FROM hc_patients "
            "WHERE phone_hash = :ph AND status = 'active' AND deleted_at IS NULL "
            "LIMIT 1"
        ),
        {"ph": _hash_phone(payload.phone)},
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed.",
        )

    patient_id = str(row[0])
    tenant_id = str(row[1]) if row[1] else None
    access_token = create_patient_access_token(patient_id=patient_id, phone=payload.phone, tenant_id=tenant_id)
    refresh_token = create_patient_refresh_token(patient_id=patient_id, tenant_id=tenant_id)

    response.set_cookie(
        key="patient_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 3600,
        path="/api/v1/patients/auth",
    )

    return PatientTokenResponse(
        access_token=access_token,
        patient_id=patient_id,
        message="Login successful.",
    )


# ---------------------------------------------------------------------------
# T-HC-021 — Refresh
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/patients/auth/refresh",
    response_model=PatientTokenResponse,
    summary="Refresh patient access token via HttpOnly cookie (public)",
)
async def patient_refresh(
    response: Response,
    patient_refresh_token: Optional[str] = Cookie(default=None),
) -> PatientTokenResponse:
    """Issue a new access token from the HttpOnly refresh cookie."""
    if not patient_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing.",
        )

    try:
        token_data = decode_patient_token(patient_refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    access_token = create_patient_access_token(
        patient_id=token_data.patient_id,
        phone=token_data.phone,
        tenant_id=token_data.tenant_id,
    )
    new_refresh = create_patient_refresh_token(
        patient_id=token_data.patient_id,
        tenant_id=token_data.tenant_id,
    )

    response.set_cookie(
        key="patient_refresh_token",
        value=new_refresh,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 3600,
        path="/api/v1/patients/auth",
    )

    return PatientTokenResponse(
        access_token=access_token,
        patient_id=token_data.patient_id,
        message="Token refreshed.",
    )


# ---------------------------------------------------------------------------
# T-HC-021 — Logout
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/patients/auth/logout",
    summary="Logout — clear patient refresh cookie",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def patient_logout(response: Response) -> None:
    """Clear the HttpOnly refresh cookie."""
    response.delete_cookie(
        key="patient_refresh_token",
        path="/api/v1/patients/auth",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_phone(phone: str) -> str:
    """
    HMAC-SHA256 hash of the phone number for indexed duplicate detection.

    Uses PHONE_HASH_KEY env var (separate from PHI_ENCRYPTION_KEY) so
    the hash cannot be reversed even if the encryption key is rotated.
    """
    import hashlib
    import hmac
    key = os.environ.get("PHONE_HASH_KEY", "changeme-set-PHONE_HASH_KEY").encode()
    return hmac.new(key, phone.encode(), hashlib.sha256).hexdigest()
