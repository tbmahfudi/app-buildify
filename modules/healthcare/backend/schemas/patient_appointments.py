"""Schemas for T-HC-045 — Cross-Tenant Appointments API."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PatientAppointmentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    appointment_id: str
    clinic_name: str
    branch_name: str
    provider_name: str
    provider_specialty: Optional[str] = None
    appointment_type: str
    scheduled_at: datetime
    status: str


class PatientAppointmentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    appointment_id: str
    clinic_name: str
    branch_name: str
    branch_address: Optional[str] = None
    branch_contact_phone: Optional[str] = None
    provider_name: str
    provider_specialty: Optional[str] = None
    appointment_type: str
    scheduled_at: datetime
    status: str
    notes: Optional[str] = None


class PatientAppointmentListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[PatientAppointmentSummary]
    total: int
    page: int
    page_size: int
