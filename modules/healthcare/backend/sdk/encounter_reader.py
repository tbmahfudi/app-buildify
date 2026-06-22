"""
Healthcare Internal SDK — Encounter reader.

T-HC-015  CRITICAL

EncounterReadDTO is the only object returned to callers — no ORM objects escape.
get_encounter() calls write_phi_read_audit() BEFORE returning data.
Branch scope is enforced: encounter's branch_id must match the supplied branch_id.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session


class EncounterNotFoundError(Exception):
    """Raised when encounter does not exist, tenant/branch mismatch, or access denied."""


class EncounterReadDTO(BaseModel):
    """Read-only DTO for encounter data — no ORM object returned."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    branch_id: str
    patient_id: uuid.UUID
    provider_id: uuid.UUID
    encounter_date: datetime
    status: str
    chief_complaint: Optional[str] = None  # maps to soap_subjective
    notes: Optional[str] = None            # maps to soap_notes


def get_encounter(
    db: Session,
    tenant_id: str,
    branch_id: str,
    encounter_id: str,
    actor_id: str,
    actor_type: str = "staff",
    ip: Optional[str] = None,
    ua: Optional[str] = None,
) -> EncounterReadDTO:
    """
    Retrieve an encounter scoped to tenant_id AND branch_id.

    PHI read audit is written BEFORE returning data.

    Args:
        db:           Active SQLAlchemy session.
        tenant_id:    Tenant scope.
        branch_id:    Branch scope — encounter must belong to this branch.
        encounter_id: UUID of the encounter.
        actor_id:     ID of the requesting user (for audit log).
        actor_type:   'staff', 'patient', or 'system'.
        ip:           Request IP.
        ua:           User-Agent.

    Returns:
        EncounterReadDTO — decrypted PHI fields.

    Raises:
        EncounterNotFoundError: if not found or scope mismatch.
    """
    from modules.healthcare.models import HCEncounter
    from modules.healthcare.sdk.phi_audit import write_phi_read_audit

    encounter = (
        db.query(HCEncounter)
        .filter(
            HCEncounter.id == encounter_id,
            HCEncounter.tenant_id == tenant_id,
            HCEncounter.branch_id == branch_id,
        )
        .first()
    )

    if encounter is None:
        raise EncounterNotFoundError(
            f"Encounter {encounter_id!r} not found in tenant {tenant_id!r} "
            f"branch {branch_id!r}"
        )

    # Audit BEFORE returning any PHI
    write_phi_read_audit(
        db=db,
        actor_id=actor_id,
        actor_type=actor_type,
        entity_type="encounter",
        entity_id=str(encounter.id),
        tenant_id=tenant_id,
        branch_id=branch_id,
        ip=ip,
        ua=ua,
    )

    return EncounterReadDTO(
        id=encounter.id,
        tenant_id=encounter.tenant_id,
        branch_id=encounter.branch_id,
        patient_id=encounter.patient_id,
        provider_id=encounter.provider_id,
        encounter_date=encounter.started_at,
        status=encounter.status,
        chief_complaint=encounter.soap_subjective,
        notes=encounter.soap_notes,
    )


__all__ = [
    "EncounterReadDTO",
    "EncounterNotFoundError",
    "get_encounter",
]
