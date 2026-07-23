from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[UUID] = None


class FolderRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class FolderMove(BaseModel):
    parent_id: Optional[UUID] = None  # null = move to root


class FolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    parent_id: Optional[UUID] = None
    created_at: datetime


class FolderListResponse(BaseModel):
    folders: List[FolderResponse]
