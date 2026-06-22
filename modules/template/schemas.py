"""Pydantic schemas for the TEMPLATE module."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class ItemListResponse(BaseModel):
    items: List[ItemResponse]
    total: int
    page: int
    page_size: int
