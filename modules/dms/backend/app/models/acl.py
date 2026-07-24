"""Row-level ACL model (E3).

A grant of a capability (view/edit/manage) to a user or group on a folder or
document. Resolution + inheritance live in AclService.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from ..core.database import Base

# Capability ordering: a higher level implies the lower ones.
CAPABILITY_RANK = {"view": 1, "edit": 2, "manage": 3}


class DmsAcl(Base):
    __tablename__ = "dms_acls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    resource_type = Column(String(16), nullable=False)   # folder | document
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    principal_type = Column(String(16), nullable=False)  # user | group
    principal_id = Column(UUID(as_uuid=True), nullable=False)
    capability = Column(String(16), nullable=False)       # view | edit | manage
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
