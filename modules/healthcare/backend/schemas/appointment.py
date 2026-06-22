from __future__ import annotations
import uuid
from datetime import datetime, date, time
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    slot_id: str
    slot_date: date
    start_time: time
    end_time: time
    appointment_type: str
    provider_name: str
    provider_specialty: Optional[str] = None


class AppointmentCreate(BaseModel):
    slot_id: uuid.UUID
    appointment_type: str
    notes: Optional[str] = None


class AppointmentReschedule(BaseModel):
    new_slot_id: uuid.UUID


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    branch_id: str
    provider_id: str
    slot_id: str
    appointment_type: str
    status: str
    scheduled_at: datetime
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    rescheduled_from_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AppointmentListResponse(BaseModel):
    appointments: List[AppointmentResponse]
    total: int


class AppointmentStatusUpdate(BaseModel):
    status: str
