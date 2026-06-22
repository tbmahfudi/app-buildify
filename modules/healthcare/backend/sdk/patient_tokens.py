"""
Healthcare SDK — Patient JWT helpers.

T-HC-021

Tokens are HS256 JWTs signed with the SECRET_KEY env var.
Access token:  15-minute expiry.
Refresh token: 7-day expiry.

Claims shape (access):
    { sub: patient_id, phone: str, roles: ["patient"], type: "access", exp, iat }

Claims shape (refresh):
    { sub: patient_id, roles: ["patient"], type: "refresh", exp, iat }
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    import jwt as _jwt  # PyJWT >= 2.0
except ImportError as exc:
    raise ImportError(
        "PyJWT is required for patient token functionality. "
        "Install with: pip install PyJWT"
    ) from exc


ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


def _secret() -> str:
    key = os.environ.get("SECRET_KEY", "")
    if not key:
        raise RuntimeError(
            "SECRET_KEY environment variable is not set. "
            "Patient token signing requires SECRET_KEY."
        )
    return key


@dataclass
class PatientTokenData:
    patient_id: str
    phone: str
    roles: list


def create_patient_access_token(patient_id: str, phone: str) -> str:
    """
    Create a signed HS256 access JWT for a patient.

    Args:
        patient_id: UUID string of the patient record.
        phone:      Patient phone number (non-PHI claim — used for identity binding).

    Returns:
        Encoded JWT string (15-minute expiry).
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": patient_id,
        "phone": phone,
        "roles": ["patient"],
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return _jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def create_patient_refresh_token(patient_id: str) -> str:
    """
    Create a signed HS256 refresh JWT for a patient.

    Args:
        patient_id: UUID string of the patient record.

    Returns:
        Encoded JWT string (7-day expiry).
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": patient_id,
        "roles": ["patient"],
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return _jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_patient_token(token: str) -> PatientTokenData:
    """
    Decode and validate a patient JWT (access or refresh).

    Raises:
        jwt.ExpiredSignatureError: if the token has expired.
        jwt.InvalidTokenError:     if the token is invalid.
        ValueError:                if roles != ["patient"].

    Returns:
        PatientTokenData with patient_id, phone, roles.
    """
    payload = _jwt.decode(token, _secret(), algorithms=[ALGORITHM])

    roles = payload.get("roles", [])
    if roles != ["patient"]:
        raise ValueError("Token does not carry patient role")

    patient_id: Optional[str] = payload.get("sub")
    if not patient_id:
        raise ValueError("Token missing sub claim")

    phone: str = payload.get("phone", "")

    return PatientTokenData(patient_id=patient_id, phone=phone, roles=roles)


__all__ = [
    "PatientTokenData",
    "create_patient_access_token",
    "create_patient_refresh_token",
    "decode_patient_token",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "REFRESH_TOKEN_EXPIRE_DAYS",
]
