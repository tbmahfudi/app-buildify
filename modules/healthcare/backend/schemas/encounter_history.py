"""Schemas for T-HC-044 — Encounter History API."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class EncounterSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    encounter_id: str
    clinic_name: str
    branch_name: str
    provider_name: str
    encounter_date: datetime
    encounter_type: str
    summary: Optional[str] = None
    summary_shared: bool = False


class EncounterHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[EncounterSummaryItem]
    total: int
    page: int
    page_size: int
    by_year: Dict[int, List[EncounterSummaryItem]] = {}


class EncounterDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    encounter_id: str
    clinic_name: str
    branch_name: str
    provider_name: str
    provider_specialty: Optional[str] = None
    encounter_date: datetime
    status: str
    summary: Optional[str] = None
    summary_shared: bool = False
