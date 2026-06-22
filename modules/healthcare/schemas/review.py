"""Schemas for T-HC-046 — Clinic Review APIs."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    encounter_id: str
    branch_id: str
    rating: int = Field(..., ge=1, le=5)
    text: Optional[str] = Field(None, max_length=500)


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rating: int
    text: Optional[str] = None
    created_at: datetime
    display_name: str   # e.g. "Pasien, Juni 2025" — no real patient data


class ReviewListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[ReviewResponse]
    total: int
    page: int
    page_size: int


class ReviewReplyCreate(BaseModel):
    response_text: str = Field(..., max_length=500)
