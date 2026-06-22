"""Schemas for T-HC-043 — Patient Profile & Summary API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class PatientProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str
    date_of_birth: str
    email: Optional[str] = None
    address: Optional[str] = None
    masked_phone: str          # e.g. "****1234"
    locale: str
    gender: str
    created_at: datetime


class PatientProfileUpdate(BaseModel):
    email: Optional[str] = None
    address: Optional[str] = None
    locale: Optional[str] = None

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("id-ID", "en-US"):
            raise ValueError("locale must be one of: id-ID, en-US")
        return v


class PatientSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_visits: int
    upcoming_appointments: int
    active_clinics: int
    last_visit_date: Optional[datetime] = None
