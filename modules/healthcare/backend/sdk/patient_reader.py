"""
Healthcare Internal SDK — Patient reader.

T-HC-015  CRITICAL

PatientReadDTO is the only object returned to callers — no ORM objects escape.
get_patient() calls write_phi_read_audit() BEFORE returning data.

Raises PatientNotFoundError if patient is absent or belongs to a different tenant.
"""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session


class PatientNotFoundError(Exception):
    """Raised when patient does not exist or does not belong to the requested tenant."""


class PatientReadDTO(BaseModel):
    """Read-only DTO for patient data — no ORM object returned to callers."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    full_name: str
    date_of_birth: str
    phone: str
    gender: str
    blood_type: Optional[str] = None  # reserved for future PHI field


def get_patient(
    db: Session,
    tenant_id: str,
    patient_id: str,
    actor_id: str,
    actor_type: str = "staff",
    ip: Optional[str] = None,
    ua: Optional[str] = None,
) -> PatientReadDTO:
    """
    Retrieve a patient by ID, scoped to tenant_id.

    PHI read audit is written BEFORE returning data (ADR-HC-002 §D2).

    Args:
        db:          Active SQLAlchemy session.
        tenant_id:   Tenant scope — patient must belong to this tenant.
        patient_id:  UUID of the patient to retrieve.
        actor_id:    ID of the requesting user/patient (for audit log).
        actor_type:  'staff', 'patient', or 'system'.
        ip:          Request IP for audit trail.
        ua:          User-Agent header for audit trail.

    Returns:
        PatientReadDTO — decrypted PHI fields.

    Raises:
        PatientNotFoundError: if patient not found or tenant mismatch.
    """
    from modules.healthcare.models import HCPatient
    from modules.healthcare.sdk.phi_audit import write_phi_read_audit

    patient = (
        db.query(HCPatient)
        .filter(
            HCPatient.id == patient_id,
            HCPatient.tenant_id == tenant_id,
            HCPatient.deleted_at.is_(None),
        )
        .first()
    )

    if patient is None:
        raise PatientNotFoundError(
            f"Patient {patient_id!r} not found in tenant {tenant_id!r}"
        )

    # Audit BEFORE returning any PHI
    write_phi_read_audit(
        db=db,
        actor_id=actor_id,
        actor_type=actor_type,
        entity_type="patient",
        entity_id=str(patient.id),
        tenant_id=tenant_id,
        ip=ip,
        ua=ua,
    )

    return PatientReadDTO(
        id=patient.id,
        tenant_id=patient.tenant_id,
        full_name=patient.full_name or "",
        date_of_birth=patient.date_of_birth or "",
        phone=patient.phone or "",
        gender=patient.gender,
    )


__all__ = [
    "PatientReadDTO",
    "PatientNotFoundError",
    "get_patient",
]
