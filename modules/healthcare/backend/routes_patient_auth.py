"""
Healthcare — Patient registration and authentication API.

T-HC-020  POST /api/v1/patients/register              (PUBLIC)
          POST /api/v1/patients/activate               (PUBLIC)
          POST /api/v1/patients/auth/staff-link/confirm(PUBLIC)
          POST /api/v1/patients/auth/from-platform     (PUBLIC)
          POST /api/v1/patients/auth/refresh           (PUBLIC)
          POST /api/v1/patients/auth/logout            (PUBLIC)

Phone/OTP patient login (otp/send, otp/verify, auth/token) and the OTP-gated
claim-account endpoint were removed with ADR-011 S6b once the D7 backfill left no
OTP-only patients. Patient auth is now password-primary (email+password + platform
MFA), with the platform login → from-platform bridge minting the portal session;
any straggler backfilled account is onboarded via staff-link + password reset.
"""
from __future__ import annotations

import json
import logging
import os
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.dependencies import get_db as _platform_get_db
from app.core.security_config import SecurityConfigService
from app.models.user import User as _User
from app.services.account_service import (
    AccountExistsError,
    WeakPasswordError,
    create_patient_account,
)

def _get_public_db():
    """Plain unauthenticated DB session for public endpoints."""
    yield from _platform_get_db()

from modules.healthcare.models import HCPatient, HCPatientConsent
from modules.healthcare.schemas.patient_auth import (
    ActivateRequest,
    ActivateResponse,
    PatientRegisterRequest,
    PatientTokenResponse,
    RegisterAcceptedResponse,
    StaffLinkConfirmRequest,
    StaffLinkConfirmResponse,
)
from modules.healthcare.sdk.captcha import require_captcha
from modules.healthcare.sdk.patient_tokens import (
    create_patient_access_token,
    create_patient_refresh_token,
    decode_patient_token,
)
from modules.healthcare.sdk.phi_audit import write_event_audit

router = APIRouter(tags=["healthcare-patient-auth"])

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


# ---------------------------------------------------------------------------
# ADR-011 — password self-registration (verify-email, no auto-login)
# ---------------------------------------------------------------------------

_ACTIVATION_TTL = 24 * 3600  # 24h to click the activation link
_REGISTER_ACCEPTED_MSG = (
    "If this email is not already registered, we've sent an activation link. "
    "Please check your inbox to finish creating your account."
)


def _activation_key(token: str) -> str:
    return f"patient_activation:{token}"


def _self_service_enabled(db: Session, tenant_id: Optional[str]) -> bool:
    """Whether open patient self-registration is enabled for this tenant.

    Default OFF (sec-review-011 R4): a tenant must explicitly turn on
    `patient_self_registration_enabled`. Fail closed if config is unavailable.
    """
    try:
        val = SecurityConfigService(db).get_config("patient_self_registration_enabled", tenant_id)
        return str(val).strip().lower() in ("1", "true", "yes", "on") if val is not None else False
    except Exception:  # pragma: no cover - defensive: config error must not open the gate
        return False


def _dispatch_activation_email(email: str, token: str) -> None:
    """Send the account-activation link.

    Mirrors the OTP dispatch stub: in dev this logs the event (the token is never
    logged — it's an authentication secret); production wires the SMTP worker
    (ADR-002-smtp) here. The activation URL embeds the opaque token.
    """
    logging.getLogger(__name__).info("activation email dispatched", extra={"event": "patient.activation_sent"})


# ---------------------------------------------------------------------------
# T-HC-020 — Patient registration
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/patients/register",
    response_model=RegisterAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Register a new patient with email + password (public, verify-email)",
)
async def patient_register(
    payload: PatientRegisterRequest,
    request: Request,
    _captcha=Depends(require_captcha),
    db: Session = Depends(_get_public_db),
) -> RegisterAcceptedResponse:
    """
    Register a new patient with email + password (ADR-011, verify-email flow).

    captcha -> consent -> tenant self-service gate -> create the platform account
    (S1) -> create + link the hc_patients PHI row -> issue an activation token +
    email. Always returns the SAME 202 whether the email is new or already
    registered (sec-review-011 R1 — no enumeration). No portal token is issued at
    registration; the patient activates via the emailed link, then logs in.
    """
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    # Consent gate (the registrant's own submission — safe to be specific).
    if not payload.consent_accepted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Consent must be accepted to register.",
        )

    # Resolve the registration scope (ADR-HC-010): tenant_id + company_id.
    tenant_row = db.execute(text("SELECT current_setting('app.tenant_id', true)")).fetchone()
    reg_tenant: str = tenant_row[0] if tenant_row and tenant_row[0] else "global"
    tenant_id, company_id = _resolve_registration_scope(db, reg_tenant)

    # Self-service gate — default OFF per tenant (sec-review-011 R4).
    if not _self_service_enabled(db, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration is not enabled. Please contact your clinic to be invited.",
        )

    # Create the platform account (credential lives on the platform users table).
    #  - WeakPasswordError: the registrant's own password -> specific 422.
    #  - AccountExistsError: fall through to the SAME generic 202 (no enumeration).
    # end_user_module joins the account to the manifest-declared 'patients' group in the
    # shared tenant (ADR-012 D5). Without it the account has no 'patient' role and
    # app.js:112 drops the patient in the staff SPA on their first password login.
    try:
        user = create_patient_account(
            db,
            tenant_id=tenant_id,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            username=payload.username,
            phone=payload.phone,
            default_company_id=company_id,
            end_user_module="healthcare",
        )
    except WeakPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Password does not meet requirements.", "errors": exc.errors},
        )
    except AccountExistsError:
        db.rollback()
        return RegisterAcceptedResponse(message=_REGISTER_ACCEPTED_MSG)

    # Create the PHI patient row, linked to the platform account (hc_patients.user_id).
    patient = HCPatient(
        tenant_id=tenant_id,
        company_id=company_id,
        user_id=str(user.id),
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

    # Issue a single-use activation token (Redis, TTL) and email the link.
    token = secrets.token_urlsafe(32)
    _get_redis().set(_activation_key(token), str(user.id), ex=_ACTIVATION_TTL)
    _dispatch_activation_email(user.email, token)

    return RegisterAcceptedResponse(message=_REGISTER_ACCEPTED_MSG)


@router.post(
    "/api/v1/patients/activate",
    response_model=ActivateResponse,
    summary="Activate a patient account via the emailed token (public)",
)
async def patient_activate(
    payload: ActivateRequest,
    db: Session = Depends(_get_public_db),
) -> ActivateResponse:
    """Consume a single-use activation token and mark the platform user verified.

    Generic error on any invalid/expired/used token (no enumeration).
    """
    r = _get_redis()
    key = _activation_key(payload.token)
    user_id = r.get(key)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired activation link.",
        )
    if isinstance(user_id, bytes):
        user_id = user_id.decode()

    db.execute(text("UPDATE users SET is_verified = true WHERE id = :uid"), {"uid": user_id})
    db.commit()
    r.delete(key)  # single-use

    return ActivateResponse(activated=True, message="Account activated. You can now sign in.")


@router.post(
    "/api/v1/patients/auth/staff-link/confirm",
    response_model=StaffLinkConfirmResponse,
    summary="Confirm a staff-initiated account link via the emailed token (public)",
)
async def staff_link_confirm(
    payload: StaffLinkConfirmRequest,
    db: Session = Depends(_get_public_db),
) -> StaffLinkConfirmResponse:
    """Consume a single-use staff-link token and write the real email onto the account.

    Public by design: the token IS the credential. Clicking it is what proves the holder
    controls that mailbox — which is the whole difference between ``confirm`` mode and
    ``force`` mode (see routes_household.staff_link_account, ADR-HC-009 V-D10).

    Grants no credential: ``must_set_password`` stays True, so the holder still has to go
    through the platform's ordinary password-reset flow, which is what actually lifts the
    gate. All this does is make that flow reachable at an address they demonstrably own.

    Generic error on any invalid/expired/used token (no enumeration).
    """
    r = _get_redis()
    key = f"patient_staff_link:{payload.token}"
    raw = r.get(key)
    if raw is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This link is invalid or has expired. Please ask the clinic to resend it.",
        )

    try:
        data = json.loads(raw)
        user_id = data["user_id"]
        email_norm = data["email"]
        patient_id = data.get("patient_id")
    except Exception:  # noqa: BLE001 — a malformed payload is a broken token
        r.delete(key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This link is invalid or has expired. Please ask the clinic to resend it.",
        )

    user = db.query(_User).filter(_User.id == str(user_id)).first()
    if user is None or not getattr(user, "must_set_password", False):
        # Claimed (or gone) since the link was sent — the address is theirs now, so this
        # token must not repoint it. Burn the token either way.
        r.delete(key)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This account has already been set up. Please sign in or reset your password.",
        )

    # Re-check at redemption, not just at issue: another account may have taken the address
    # during the 24h window.
    taken = (
        db.query(_User)
        .filter(func.lower(_User.email) == email_norm, _User.id != user.id)
        .first()
    )
    if taken is not None:
        r.delete(key)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That email is no longer available. Please contact the clinic.",
        )

    user.email = email_norm
    # They just proved control of the mailbox by clicking, so this address IS verified —
    # unlike the force path, where staff asserted it on their behalf.
    user.is_verified = True

    # Audit before the commit — write_event_audit only add()s + flush()es (it does not
    # commit), so auditing after db.commit() would silently drop the row.
    write_event_audit(
        db=db,
        actor_id=str(user.id),
        actor_type="patient",
        event_type="patient.staff_link_confirmed",
        entity_type="hc_patient",
        entity_id=str(patient_id) if patient_id else str(user.id),
        tenant_id=str(user.tenant_id),
        metadata={"user_id": str(user.id)},
    )
    db.commit()

    r.delete(key)  # single use

    return StaffLinkConfirmResponse(
        confirmed=True,
        message=(
            "Your email is linked. Use 'forgot password' on this address to set your "
            "password and sign in."
        ),
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

    # Activation gate (ADR-011): a patient who registered via email+password must
    # activate before a portal session is granted.
    verified_row = db.execute(
        text("SELECT is_verified FROM users WHERE id = :uid"), {"uid": user_id}
    ).fetchone()
    if verified_row is not None and not verified_row[0]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please activate your account via the link we emailed you before signing in.",
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
