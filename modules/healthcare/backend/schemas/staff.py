"""Pydantic schemas for branch staff endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StaffInvite(BaseModel):
    email: EmailStr
    role: str = Field(..., pattern="^(branch_manager|doctor|nurse|pharmacist|lab_tech|billing_staff)$")


class StaffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    branch_id: Optional[str]
    user_id: str
    role: str
    status: str
    is_active: bool
    invited_at: Optional[datetime]
    accepted_at: Optional[datetime]
    created_at: datetime
