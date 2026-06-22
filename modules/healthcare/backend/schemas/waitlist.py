from __future__ import annotations
import uuid
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class WaitlistCreate(BaseModel):
    branch_id: uuid.UUID
    provider_id: Optional[uuid.UUID] = None
    appointment_type: str
    preferred_date: date


class WaitlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    branch_id: str
    provider_id: Optional[str] = None
    appointment_type: str
    preferred_date: date
    status: str
    offered_slot_id: Optional[str] = None
    offer_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class WaitlistListResponse(BaseModel):
    entries: List[WaitlistResponse]
    total: int
