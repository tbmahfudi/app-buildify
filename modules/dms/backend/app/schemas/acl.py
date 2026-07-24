from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SetPrivacyRequest(BaseModel):
    is_private: bool


class GrantRequest(BaseModel):
    principal_type: Literal["user", "group"]
    principal_id: UUID
    capability: Literal["view", "edit", "manage"]


class AclResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resource_type: str
    resource_id: UUID
    principal_type: str
    principal_id: UUID
    capability: str
    created_at: datetime


class AclListResponse(BaseModel):
    acls: List[AclResponse]


class EffectiveAccessResponse(BaseModel):
    document_id: UUID
    restricted: bool
    capability: Optional[str] = None  # None => not ACL-restricted, or no grant
    can_view: bool
    can_edit: bool
    can_manage: bool
