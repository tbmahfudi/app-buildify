"""Pydantic schemas for organization (department + platform-org linkage) endpoints.

Epic-08 / ADR-HC-005.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

_KIND = "^(medical|pharmacy|laboratory|radiology|administration|finance)$"


# --- Departments -----------------------------------------------------------

class DepartmentCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    kind: str = Field(..., pattern=_KIND)
    is_active: bool = True


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    kind: Optional[str] = Field(None, pattern=_KIND)
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    code: str
    name: str
    kind: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Provider <-> department assignment ------------------------------------

class DepartmentMemberCreate(BaseModel):
    provider_id: str
    is_primary: bool = False


class DepartmentMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    provider_id: str
    department_id: str
    is_primary: bool
    created_at: datetime


# --- Platform-org linkage --------------------------------------------------

class OrgLinkageUpdate(BaseModel):
    platform_company_id: Optional[uuid.UUID] = None
    platform_branch_id: Optional[uuid.UUID] = None
    platform_department_id: Optional[uuid.UUID] = None


class OrgLinkageResponse(BaseModel):
    branch_id: str
    platform_company_id: Optional[uuid.UUID] = None
    platform_branch_id: Optional[uuid.UUID] = None
    platform_department_id: Optional[uuid.UUID] = None


class OrgContextResponse(BaseModel):
    """Resolved platform-org context (names) for the linked branch."""
    branch_id: str
    linked: bool
    company_id: Optional[uuid.UUID] = None
    company_name: Optional[str] = None
    platform_branch_id: Optional[uuid.UUID] = None
    platform_branch_name: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    department_name: Optional[str] = None
