"""
Healthcare SDK — Patient role namespace and authentication dependency.

T-HC-001 / Phase 2 (public-portal) — tenant enforcement

Patient JWT claims shape:
    { sub: patient_id, roles: ["patient"], tenant_id: <uuid|null>, phone: str }

`get_current_patient` raises HTTP 401 if a staff JWT is presented.
`get_current_user` (staff) rejects patient JWTs — enforced in modules/sdk/dependencies.py.

SECURITY (Phase 2): the patient access token carries an optional `tenant_id`
claim (minted at register / login / refresh — see routes_patient_auth.py). Every
`/api/v1/patients/me/*` query MUST be scoped to BOTH the patient_id (token `sub`)
AND this tenant_id so a patient can never read another tenant's data. The helper
`PatientTokenData.require_tenant()` returns the tenant_id and rejects (HTTP 401)
any token minted without the claim — the secure default per the ADR.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Reuse the platform JWT decode function — same issuer, different claims
# Import via SDK wrapper to respect the module sandbox boundary (FIX-BE-002)
from modules.sdk.dependencies import decode_token

# auto_error=False on the optional scheme so we can treat "no header" as anon
_security = HTTPBearer()
_security_optional = HTTPBearer(auto_error=False)


@dataclass
class PatientTokenData:
    patient_id: str
    phone: str
    roles: list[str]
    tenant_id: Optional[str] = None

    def require_tenant(self) -> str:
        """
        Return the token's tenant_id, or raise HTTP 401 if absent.

        Secure default (ADR): a patient token minted without a tenant_id claim
        cannot be scoped safely, so cross-tenant data access is DENIED rather
        than silently widened. All `/patients/me/*` data queries call this.
        """
        if not self.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Patient token is missing tenant scope. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return self.tenant_id


def _decode_patient_payload(token: str) -> PatientTokenData:
    """Decode + validate a patient access JWT into PatientTokenData (or raise 401)."""
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    roles: list[str] = payload.get("roles", [])

    # Explicitly reject staff JWTs at the patient boundary
    if roles != ["patient"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Patient credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    patient_id: Optional[str] = payload.get("sub") or payload.get("patient_id")
    if not patient_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid patient token: missing patient_id",
            headers={"WWW-Authenticate": "Bearer"},
        )

    phone: str = payload.get("phone", "")
    tenant_id: Optional[str] = payload.get("tenant_id")

    return PatientTokenData(
        patient_id=patient_id,
        phone=phone,
        roles=roles,
        tenant_id=tenant_id,
    )


def get_current_patient(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> PatientTokenData:
    """
    FastAPI dependency — validates JWT and asserts caller is a patient.

    Raises HTTP 401 if:
    - Token is invalid or expired
    - Token type is not "access"
    - roles does not equal ["patient"]
    - patient_id claim is absent

    NOTE: this returns the token data including `tenant_id`. Data routes must
    call `patient.require_tenant()` and add `AND tenant_id = :tid` to every query.
    """
    return _decode_patient_payload(credentials.credentials)


def get_current_patient_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security_optional),
) -> Optional[PatientTokenData]:
    """
    FastAPI dependency for mixed (public + patient) endpoints.

    Returns PatientTokenData when a valid patient access token is presented, or
    None when no Authorization header is present. A present-but-invalid token
    still raises 401 (a malformed credential is never silently treated as anon).
    """
    if credentials is None:
        return None
    return _decode_patient_payload(credentials.credentials)


def has_patient_permission(resource: str, action: str):
    """
    Dependency factory — checks that the patient has permission for resource:action.

    For v1 the patient role is monolithic (all patients have the same permissions
    on their own records). Future phases can extend this with fine-grained scopes.

    Usage::

        @router.get("/patients/me")
        async def get_my_profile(
            _=Depends(has_patient_permission("patient_profile", "read")),
            patient=Depends(get_current_patient),
        ):
            ...
    """
    def _checker(
        patient: PatientTokenData = Depends(get_current_patient),
    ) -> PatientTokenData:
        # v1: any authenticated patient may perform any patient-scoped action.
        # Resource and action are validated to be non-empty strings as a guard
        # against misconfigured callers.
        if not resource or not action:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="resource and action must be non-empty strings",
            )
        return patient

    return _checker


def get_patient_db():
    """
    Plain DB session for patient / public routes.

    Patient endpoints must NOT use the staff `tenant_scoped_session` dependency:
    that one re-authenticates a platform staff `User` from the bearer and rejects
    patient JWTs, so every patient route 401'd ("User not found"). Patient routes
    already scope themselves explicitly via `patient.require_tenant()` + an
    `AND tenant_id = :tid` filter (and `appuser` bypasses RLS), so a plain session
    is correct and sufficient here.
    """
    from app.core.dependencies import get_db as _platform_get_db
    yield from _platform_get_db()


__all__ = [
    "PatientTokenData",
    "get_current_patient",
    "get_current_patient_optional",
    "has_patient_permission",
    "get_patient_db",
]
