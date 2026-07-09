"""Pydantic schemas for hc_branches endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class BranchCreate(BaseModel):
    branch_name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=100)
    address_street: str = Field(..., max_length=500)
    address_city: str = Field(..., max_length=100)
    address_province: str = Field(..., max_length=100)
    address_postal_code: Optional[str] = Field(None, max_length=10)
    timezone: str = Field("Asia/Jakarta", max_length=50)
    contact_phone: str = Field(..., max_length=30)
    operating_hours: dict[str, Any] = Field(default_factory=dict)
    status: str = Field("active", pattern="^(active|inactive|suspended)$")
    online_booking: bool = True
    public_visible: bool = True
    default_locale: str = Field("id-ID", pattern="^(id-ID|en-US)$")
    appointment_types: list[Any] = Field(default_factory=list)


class BranchUpdate(BaseModel):
    branch_name: Optional[str] = Field(None, max_length=255)
    address_street: Optional[str] = Field(None, max_length=500)
    address_city: Optional[str] = Field(None, max_length=100)
    address_province: Optional[str] = Field(None, max_length=100)
    address_postal_code: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    contact_phone: Optional[str] = Field(None, max_length=30)
    operating_hours: Optional[dict[str, Any]] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")
    online_booking: Optional[bool] = None
    public_visible: Optional[bool] = None
    default_locale: Optional[str] = Field(None, pattern="^(id-ID|en-US)$")
    appointment_types: Optional[list[Any]] = None


class BranchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    branch_name: str
    slug: str
    address_street: str
    address_city: str
    address_province: str
    address_postal_code: Optional[str]
    timezone: str
    contact_phone: str
    operating_hours: dict[str, Any]
    status: str
    online_booking: bool
    public_visible: bool
    default_locale: str
    appointment_types: list[Any]
    platform_company_id: Optional[str] = None
    platform_branch_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
