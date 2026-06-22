"""Pydantic schemas for provider endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderCreate(BaseModel):
    user_id: str
    provider_type: str = Field(..., pattern="^(doctor|nurse|pharmacist|lab_tech|billing_staff)$")
    specialty: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    display_name: str = Field(..., max_length=255)
    bio: Optional[str] = None
    is_active: bool = True


class ProviderUpdate(BaseModel):
    specialty: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    display_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    is_active: Optional[bool] = None


class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    branch_id: str
    user_id: str
    provider_type: str
    specialty: Optional[str]
    license_number: Optional[str]
    display_name: str
    bio: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
