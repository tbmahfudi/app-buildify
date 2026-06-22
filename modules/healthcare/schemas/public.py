"""Pydantic v2 schemas for public clinic APIs (T-HC-022, T-HC-023).

NO PHI fields — every field here is public non-sensitive data.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ClinicSearchItem(BaseModel):
    """Public clinic search result — zero PHI."""
    model_config = ConfigDict(from_attributes=True)

    clinic_name: str
    slug: str
    specialty_tags: List[str]
    city: str
    average_rating: Optional[float]
    online_booking: bool
    branch_count: int


class ClinicSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[ClinicSearchItem]
    total: int
    page: int
    page_size: int


class PublicProviderSummary(BaseModel):
    """Provider info exposed on public profile — name + specialty ONLY, no PHI."""
    model_config = ConfigDict(from_attributes=True)

    name: str
    specialty: str


class PublicBranchDetail(BaseModel):
    """Single branch detail for public profile."""
    model_config = ConfigDict(from_attributes=True)

    branch_id: str
    branch_name: str
    address_city: str
    address_street: str
    contact_phone: Optional[str] = None  # FIX-BE-005: nullable — branches may have no phone
    online_booking: bool
    providers: List[PublicProviderSummary]


class ClinicPublicProfile(BaseModel):
    """Public clinic profile — no PHI."""
    model_config = ConfigDict(from_attributes=True)

    clinic_name: str
    slug: str
    specialty_tags: List[str]
    city: str
    average_rating: Optional[float]
    branches: List[PublicBranchDetail]
