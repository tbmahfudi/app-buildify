from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    id: UUID
    filename: str
    folder_id: Optional[UUID] = None
    content_type: str
    size_bytes: int
    current_version: int
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_private: bool = False
    uploaded_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    rank: float = 0.0
    snippet: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    page: int
    page_size: int
