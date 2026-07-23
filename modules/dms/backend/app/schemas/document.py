from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    folder_id: Optional[UUID] = None
    filename: str
    content_type: str
    size_bytes: int
    current_version: int
    uploaded_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DownloadLinkResponse(BaseModel):
    url: str
    expires_in: int


class VersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_no: int
    filename: str
    content_type: str
    size_bytes: int
    uploaded_by: Optional[UUID] = None
    change_comment: Optional[str] = None
    created_at: datetime


class MoveDocumentRequest(BaseModel):
    folder_id: Optional[UUID] = None  # null = move to root
