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

from modules.healthcare.models import HCPatient, HCPatientConsent, HCPatientRelationship
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


def _resolve_registration_scope(db: Session, reg_tenant: str) -> tuple[str, Optional[str]]:
    """Resolve (tenant_id, company_id) for a NEW patient under the SaaS model (ADR-HC-010).

    Order of preference:
      1. explicit app.company_id GUC (future portal, schema-hc-04 §C) -> (company.tenant_id, company_id)
      2. migration map (reg_tenant is a legacy per-clinic tenant) -> (saas_tenant, new_company_id)
      3. fallback: (reg_tenant, None) — leaves company_id NULL so the NOT NULL constraint surfaces a
         clear error rather than silently mis-scoping (full slug->Company onboarding is Phase 5).
    """
    try:
        guc = db.execute(text("SELECT current_setting('app.company_id', true)")).fetchone()
        cid = guc[0] if guc and guc[0] else None
        if cid:
            trow = db.execute(
                text("SELECT tenant_id FROM companies WHERE id = :cid LIMIT 1"), {"cid": cid}
            ).fetchone()
            if trow and trow[0]:
                return str(trow[0]), str(cid)
        mrow = db.execute(
            text("SELECT saas_tenant_id, new_company_id FROM saas_migration_map WHERE old_tenant_id = :t LIMIT 1"),
            {"t": reg_tenant},
        ).fetchone()
        if mrow:
            return str(mrow[0]), str(mrow[1])
    except Exception as exc:  # pragma: no cover — defensive
        import logging
        logging.getLogger(__name__).warning("registration scope resolution failed: %s", exc)
    return reg_tenant, None


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
    # Resolve the registration Company + hc tenant (ADR-HC-010): under the shared SaaS
    # tenant, company_id is the NOT NULL isolation key. Prefer an explicit app.company_id
    # GUC (future portal, schema-hc-04 §C); otherwise map the registration tenant → SAAS
    # Company via the migration map so existing per-clinic portal contexts keep working.
    # (Full slug→Company onboarding is Phase 5 / epic-20.)
    tenant_row = db.execute(text("SELECT current_setting('app.tenant_id', true)")).fetchone()
    reg_tenant: str = tenant_row[0] if tenant_row and tenant_row[0] else "global"
    tenant_id, company_id = _resolve_registration_scope(db, reg_tenant)

    patient = HCPatient(
        tenant_id=tenant_id,
        company_id=company_id,
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
        company_id=company_id,
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
    access_token = create_patient_access_token(
        patient_id=patient_id, phone=payload.phone, tenant_id=tenant_id, company_id=company_id)
    refresh_token = create_patient_refresh_token(
        patient_id=patient_id, tenant_id=tenant_id, company_id=company_id)

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
            "SELECT id, tenant_id, company_id FROM hc_patients "
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
    company_id = str(row[2]) if row[2] else None  # ADR-HC-010 D5 Company claim
    access_token = create_patient_access_token(
        patient_id=patient_id, phone=payload.phone, tenant_id=tenant_id, company_id=company_id)
    refresh_token = create_patient_refresh_token(
        patient_id=patient_id, tenant_id=tenant_id, company_id=company_id)

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
# Platform-user → patient session bridge
#
# A platform User carrying the 'patient' role logs in through the normal core
# login (/api/v1/auth/login, served by the platform backend) and receives a
# platform JWT. That JWT cannot authorize the patient portal (its sub is a
# users.id, not an hc_patients.id, and the /patients/me/* routes expect a
# patient token). This endpoint exchanges a valid platform JWT for a patient
# access token, provided the platform user is linked to an hc_patients row
# (hc_patients.user_id = users.id). Both services share SECRET_KEY, so the
# platform token validates here.
# ---------------------------------------------------------------------------

def _resolve_active_patient(db: Session, account_user_id: str, requested_patient_id: Optional[str] = None):
    """
    Resolve the active patient for a household account holder (ADR-HC-009 V-D7).

    Returns (HCPatient, is_self) or (None, False). Authority is the
    hc_patient_relationships table (active rows for this account holder); the
    active patient defaults to the caller's `self` patient, or a specifically
    requested patient when they hold an active relationship to it.
    """
    rels = db.execute(
        text(
            "SELECT patient_id, relationship FROM hc_patient_relationships "
            "WHERE account_user_id = :uid AND status = 'active'"
        ),
        {"uid": account_user_id},
    ).fetchall()

    if not rels:
        # Defensive fallback for a pre-backfill direct link (hc_patients.user_id).
        pat = (
            db.query(HCPatient)
            .filter(
                HCPatient.user_id == account_user_id,
                HCPatient.status == "active",
                HCPatient.deleted_at.is_(None),
            )
            .first()
        )
        return (pat, True) if pat is not None else (None, False)

    rel_map = {str(r[0]): r[1] for r in rels}
    if requested_patient_id is not None:
        if requested_patient_id not in rel_map:
            return None, False  # caller is not authorized to act for this patient
        target_id = requested_patient_id
    else:
        self_ids = [pid for pid, rel in rel_map.items() if rel == "self"]
        target_id = self_ids[0] if self_ids else next(iter(rel_map))

    pat = (
        db.query(HCPatient)
        .filter(
            HCPatient.id == target_id,
            HCPatient.status == "active",
            HCPatient.deleted_at.is_(None),
        )
        .first()
    )
    if pat is None:
        return None, False
    return pat, (rel_map.get(str(pat.id)) == "self")


@router.post(
    "/api/v1/patients/auth/from-platform",
    response_model=PatientTokenResponse,
    summary="Exchange a platform patient-user JWT for a patient portal session",
)
async def patient_session_from_platform(
    request: Request,
    response: Response,
    patient_id: Optional[str] = None,
    db: Session = Depends(_get_public_db),
) -> PatientTokenResponse:
    """Mint a patient portal token for a platform user linked to an hc_patient."""
    import jwt as _jwt

    authz = request.headers.get("authorization", "")
    if not authz.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    platform_token = authz.split(" ", 1)[1].strip()

    secret = os.environ.get("SECRET_KEY", "")
    if not secret:
        raise HTTPException(status_code=500, detail="Server auth misconfigured.")

    try:
        payload = _jwt.decode(platform_token, secret, algorithms=["HS256"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    # Reject patient tokens — this endpoint is for platform-user tokens only.
    if payload.get("roles") == ["patient"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a patient session.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject.",
        )

    # Household model (ADR-HC-009 v2): the account holder may act for a set of
    # patients (self + managed dependents). Authority is hc_patient_relationships;
    # the active patient defaults to `self` or a requested patient the caller is
    # authorized for. The minted token carries the ACTIVE patient's tenant_id plus
    # `acct` (account holder) and `obo` (acting on behalf of a dependent).
    patient, is_self = _resolve_active_patient(db, user_id, requested_patient_id=patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No patient portal profile is linked to this account.",
        )

    active_patient_id = str(patient.id)
    tenant_id = str(patient.tenant_id) if patient.tenant_id else None
    company_id = str(patient.company_id) if patient.company_id else None  # ADR-HC-010 D5
    access_token = create_patient_access_token(
        patient_id=active_patient_id,
        phone=patient.phone,
        tenant_id=tenant_id,
        company_id=company_id,
        account_user_id=user_id,
        on_behalf_of=not is_self,
    )
    refresh_token = create_patient_refresh_token(
        patient_id=active_patient_id, tenant_id=tenant_id, company_id=company_id)

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
        patient_id=active_patient_id,
        message="Portal session created.",
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
        company_id=token_data.company_id,
    )
    new_refresh = create_patient_refresh_token(
        patient_id=token_data.patient_id,
        tenant_id=token_data.tenant_id,
        company_id=token_data.company_id,
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
