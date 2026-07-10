"""Pydantic schemas for HR: Doctors/Providers + Rooms (epic-11)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

_PTYPE = "^(doctor|nurse|pharmacist|lab_tech|billing_staff)$"
_EMP = "^(active|probation|on_leave|suspended|terminated)$"


# --- Rooms -----------------------------------------------------------------

class RoomCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    room_type: Optional[str] = Field(None, max_length=30)
    is_active: bool = True


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    room_type: Optional[str] = Field(None, max_length=30)
    is_active: Optional[bool] = None


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    branch_id: str
    code: str
    name: str
    room_type: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Providers (doctors / nurses) ------------------------------------------

class ProviderHRCreate(BaseModel):
    display_name: str = Field(..., max_length=255)
    provider_type: str = Field(..., pattern=_PTYPE)
    user_id: Optional[str] = None
    specialty: Optional[str] = Field(None, max_length=100)
    sub_specialty: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    str_number: Optional[str] = Field(None, max_length=50)
    sip_number: Optional[str] = Field(None, max_length=50)
    str_expiry: Optional[date] = None
    sip_expiry: Optional[date] = None
    consultation_fee: Optional[int] = Field(None, ge=0)
    room_id: Optional[str] = None
    is_active: bool = True


class DoctorProfileUpdate(BaseModel):
    consultation_fee: Optional[int] = Field(None, ge=0)
    room_id: Optional[str] = None
    sub_specialty: Optional[str] = Field(None, max_length=100)


class LicenseUpdate(BaseModel):
    str_number: Optional[str] = Field(None, max_length=50)
    sip_number: Optional[str] = Field(None, max_length=50)
    str_expiry: Optional[date] = None
    sip_expiry: Optional[date] = None
    specialty: Optional[str] = Field(None, max_length=100)
    sub_specialty: Optional[str] = Field(None, max_length=100)


class ProviderBasicUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    specialty: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class StatusUpdate(BaseModel):
    employment_status: str = Field(..., pattern=_EMP)


class ProviderHRResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    branch_id: str
    user_id: Optional[str]
    provider_type: str
    display_name: str
    specialty: Optional[str]
    sub_specialty: Optional[str]
    license_number: Optional[str]
    str_number: Optional[str]
    sip_number: Optional[str]
    str_expiry: Optional[date]
    sip_expiry: Optional[date]
    consultation_fee: Optional[int]
    room_id: Optional[str]
    room_name: Optional[str] = None
    employment_status: str
    is_active: bool
    created_at: datetime
