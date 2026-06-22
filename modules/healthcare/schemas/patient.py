"""Pydantic schemas for patient and consent endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ConsentCreate(BaseModel):
    consent_type: str = Field(..., pattern="^(dpa_acceptance|data_processing|marketing)$")
    consent_version: str = Field(..., max_length=20)
    purpose_description: Optional[str] = None


class ConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    patient_id: uuid.UUID
    consent_type: str
    consent_version: str
    status: str
    accepted_at: datetime
    revoked_at: Optional[datetime]
    ip: str
    purpose_description: Optional[str]
    created_at: datetime
