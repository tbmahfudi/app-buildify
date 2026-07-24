from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateShareRequest(BaseModel):
    document_id: UUID
    expires_in_hours: Optional[int] = Field(None, ge=1, le=24 * 365,
                                            description="Hours until the link expires; omit for no expiry")
    max_downloads: Optional[int] = Field(None, ge=1, le=100000,
                                         description="Cap on total downloads; omit for unlimited")


class ShareResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    token: str
    expires_at: Optional[datetime] = None
    max_downloads: Optional[int] = None
    download_count: int
    is_revoked: bool
    created_at: datetime
    # Relative public path the caller can hand out (host is the platform origin).
    public_path: Optional[str] = None


class ShareListResponse(BaseModel):
    shares: List[ShareResponse]
