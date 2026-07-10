"""Pydantic schemas for Visit Registration & Queue (epic-09 / ADR-HC-006)."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

_PAYMENT = "^(self_pay|bpjs|private_insurance|corporate)$"


class CheckInRequest(BaseModel):
    appointment_id: str
    department_id: str
    payment_category: str = Field(..., pattern=_PAYMENT)
    insurance_profile_id: Optional[str] = None


class WalkInRequest(BaseModel):
    patient_id: str
    department_id: str
    payment_category: str = Field(..., pattern=_PAYMENT)
    insurance_profile_id: Optional[str] = None
    referral_source: str = Field("self", max_length=50)


class PaymentUpdate(BaseModel):
    payment_category: str = Field(..., pattern=_PAYMENT)
    insurance_profile_id: Optional[str] = None


class ReferralUpdate(BaseModel):
    referral_source: str = Field(..., max_length=50)


class VisitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    patient_id: str
    appointment_id: Optional[str]
    visit_type: str
    payment_category: str
    insurance_profile_id: Optional[str]
    referral_source: str
    department_id: str
    status: str
    checked_in_at: datetime
    encounter_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class QueueTicketRequest(BaseModel):
    station: Optional[str] = Field(None, max_length=50)


class QueueTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    visit_id: str
    department_id: str
    ticket_number: str
    station: Optional[str]
    status: str
    service_day: date
    transferred_to_id: Optional[str]
    called_at: Optional[datetime]
    served_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class QueueBoardResponse(BaseModel):
    department_id: str
    service_day: date
    queue_version: Optional[datetime] = None
    tickets: List[QueueTicketResponse]


class TransferRequest(BaseModel):
    department_id: str
    station: Optional[str] = Field(None, max_length=50)


class PatientPickerItem(BaseModel):
    id: str
    full_name: str
    masked_phone: Optional[str] = None


class EncounterHandoffRequest(BaseModel):
    # Optional — falls back to the calling user's own provider record.
    provider_id: Optional[str] = None


class EncounterHandoffResponse(BaseModel):
    visit_id: str
    encounter_id: str
    status: str
