"""Pydantic v2 schemas for clinic signup (T-HC-018, T-HC-019) and SaaS Company
onboarding (epic-20 Feature 20.1)."""
from __future__ import annotations

import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class ClinicRegisterRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clinic_name: str
    owner_email: str
    owner_phone: str
    owner_name: str
    city: str
    specialty: str
    dpa_accepted: bool
    dpa_version: str
    locale: str = "id-ID"

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, v: str) -> str:
        if v not in ("id-ID", "en-US"):
            return "id-ID"
        return v


class ClinicRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    branch_id: str
    message: str


class DPAStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dpa_accepted: bool
    dpa_version: Optional[str]
    accepted_at: Optional[str]


# ---------------------------------------------------------------------------
# Feature 20.1 — Owner Signup & Company Creation (shared-tenant SaaS model)
# ---------------------------------------------------------------------------

class CompanyOnboardRequest(BaseModel):
    """Self-service clinic-business (Company) signup on the shared SaaS tenant.

    Replaces the tenant-per-clinic ``ClinicRegisterRequest``: no new platform
    tenant is created — the Company is created under the shared SAAS tenant and
    the owner is a staff user Company-anchored via the ``clinic_owner`` sentinel.
    """

    model_config = ConfigDict(from_attributes=True)

    company_name: str
    slug: str
    owner_email: str
    owner_password: str
    owner_name: str
    owner_phone: Optional[str] = None
    city: Optional[str] = None
    public_listing: bool = False
    dpa_accepted: bool = False
    dpa_version: str = "1.0"
    locale: str = "id-ID"

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, v: str) -> str:
        return v if v in ("id-ID", "en-US") else "id-ID"

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, v: str) -> str:
        # Lowercase, collapse any run of non-alphanumerics to a single hyphen,
        # trim leading/trailing hyphens. companies.code is varchar(32).
        s = re.sub(r"[^a-z0-9]+", "-", (v or "").strip().lower()).strip("-")
        if not (2 <= len(s) <= 32):
            raise ValueError("slug must be 2-32 chars of a-z, 0-9 and hyphens")
        return s

    @field_validator("owner_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v or "") < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class CompanyOnboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: str
    slug: str
    owner_user_id: str
    message: str
