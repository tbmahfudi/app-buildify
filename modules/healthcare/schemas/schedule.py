from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator


class ScheduleCreate(BaseModel):
    provider_id: uuid.UUID
    day_of_week: int
    start_time: str   # HH:MM
    end_time: str     # HH:MM
    slot_duration_minutes: int
    appointment_types: List[str]

    @field_validator("day_of_week")
    @classmethod
    def validate_day(cls, v: int) -> int:
        if not 0 <= v <= 6:
            raise ValueError("day_of_week must be 0-6")
        return v

    @field_validator("slot_duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("slot_duration_minutes must be positive")
        return v


class ScheduleUpdate(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    slot_duration_minutes: Optional[int] = None
    appointment_types: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    branch_id: str
    provider_id: str
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int
    appointment_types: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ScheduleListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    schedules: List[ScheduleResponse]
    total: int


class DateTimeBlockCreate(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    reason: str
    recurrence: str = "none"  # none | annual

    @field_validator("recurrence")
    @classmethod
    def validate_recurrence(cls, v: str) -> str:
        if v not in ("none", "annual"):
            raise ValueError("recurrence must be 'none' or 'annual'")
        return v


class DateTimeBlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    provider_id: str
    branch_id: str
    start_datetime: datetime
    end_datetime: datetime
    reason: str
    recurrence: str
    flagged_appointment_ids: List[str]
