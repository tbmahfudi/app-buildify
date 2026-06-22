"""
Healthcare SDK — Patient role namespace and authentication dependency.

T-HC-001

Patient JWT claims shape:
    { sub: patient_id, roles: ["patient"], tenant_id: null, phone: str }

`get_current_patient` raises HTTP 401 if a staff JWT is presented.
`get_current_user` (staff) rejects patient JWTs — enforced in modules/sdk/dependencies.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Reuse the platform JWT decode function — same issuer, different claims
# Import via SDK wrapper to respect the module sandbox boundary (FIX-BE-002)
from modules.sdk.dependencies import decode_token

_security = HTTPBearer()


@dataclass
class PatientTokenData:
    patient_id: str
    phone: str
    roles: list[str]


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
    """
    token = credentials.credentials
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

    return PatientTokenData(patient_id=patient_id, phone=phone, roles=roles)


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


__all__ = [
    "PatientTokenData",
    "get_current_patient",
    "has_patient_permission",
]
