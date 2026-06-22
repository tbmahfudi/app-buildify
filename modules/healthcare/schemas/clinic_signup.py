"""Pydantic v2 schemas for clinic signup (T-HC-018, T-HC-019)."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class ClinicRegisterRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clinic_name: str
    owner_email: str
    owner_phone: str
    owner_name: str
    city: str
    specialty: str
    dpa_accepted: bool
    dpa_version: str
    locale: str = "id-ID"

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, v: str) -> str:
        if v not in ("id-ID", "en-US"):
            return "id-ID"
        return v


class ClinicRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    branch_id: str
    message: str


class DPAStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dpa_accepted: bool
    dpa_version: Optional[str]
    accepted_at: Optional[str]
