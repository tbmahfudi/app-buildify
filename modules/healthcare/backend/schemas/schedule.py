from __future__ import annotations
import uuid
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class ScheduleCreate(BaseModel):
    provider_id: uuid.UUID
    day_of_week: int
    start_time: str   # HH:MM
    end_time: str     # HH:MM
    slot_duration_minutes: int
    appointment_types: List[str]
    room_id: Optional[uuid.UUID] = None

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
    # room_id is tri-state: omitted = leave as-is; null = clear; uuid = assign.
    room_id: Optional[uuid.UUID] = None
    clear_room: bool = False


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
    room_id: Optional[str] = None
    room_code: Optional[str] = None
    room_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def _fmt_time(cls, v):
        # psycopg returns SQL TIME as datetime.time; render as HH:MM for the API.
        return v.strftime("%H:%M") if hasattr(v, "strftime") else v


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


# ---------------------------------------------------------------------------
# Per-date schedule overrides (substitution / unavailability)
# ---------------------------------------------------------------------------

class ScheduleOverrideCreate(BaseModel):
    override_date: date
    status: str  # 'unavailable' | 'substituted'
    substitute_provider_id: Optional[uuid.UUID] = None
    reason: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("unavailable", "substituted"):
            raise ValueError("status must be 'unavailable' or 'substituted'")
        return v

    @model_validator(mode="after")
    def check_substitute(self) -> "ScheduleOverrideCreate":
        if self.status == "substituted" and self.substitute_provider_id is None:
            raise ValueError("substitute_provider_id is required when status is 'substituted'")
        if self.status == "unavailable" and self.substitute_provider_id is not None:
            raise ValueError("substitute_provider_id must be empty when status is 'unavailable'")
        return self


class ScheduleOverrideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    branch_id: str
    schedule_id: str
    override_date: date
    status: str
    substitute_provider_id: Optional[str] = None
    substitute_provider_name: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ScheduleOverrideListResponse(BaseModel):
    overrides: List[ScheduleOverrideResponse]
    total: int
