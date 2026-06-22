"""Pydantic schemas for audit log endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    actor_id: str
    actor_type: str
    tenant_id: str
    branch_id: Optional[str]
    resource_type: str
    resource_id: str
    source_module: str
    phi_accessed: bool
    ip: Optional[str]
    user_agent: Optional[str]
    metadata_json: Optional[dict[str, Any]]
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
