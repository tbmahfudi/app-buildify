from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    folder_id: Optional[UUID] = None
    filename: str
    content_type: str
    size_bytes: int
    current_version: int
    tags: List[str] = Field(default_factory=list)
    # Model attribute is `doc_metadata`; expose it to clients as `metadata`.
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="doc_metadata",
        serialization_alias="metadata",
    )
    uploaded_by: Optional[UUID] = None
    is_private: bool = False
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


class UpdateMetadataRequest(BaseModel):
    """Update tags and/or custom metadata on a single document.

    Omitted fields are left unchanged; provided fields replace the stored value.
    """
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class BulkMetadataRequest(BaseModel):
    """Apply a metadata/tag change across many documents (F1.4 bulk edit)."""
    document_ids: List[UUID] = Field(..., min_length=1)
    # Tag operations (mutually usable): replace wins if set, else add/remove apply.
    set_tags: Optional[List[str]] = None
    add_tags: Optional[List[str]] = None
    remove_tags: Optional[List[str]] = None
    # Metadata keys to merge in (shallow). Set a key to null to remove it.
    metadata: Optional[Dict[str, Any]] = None


class BulkMetadataResponse(BaseModel):
    updated: int
