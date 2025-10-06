from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AuditLogResponse(BaseModel):
    """Audit log entry response"""
    id: str
    user_id: Optional[str]
    user_email: Optional[str]
    tenant_id: Optional[str]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    changes: Optional[Dict[str, Any]] = None
    context_info: Optional[Dict[str, Any]] = None
    ip_address: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditLogListRequest(BaseModel):
    """Request for listing audit logs"""
    user_id: Optional[str] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 50

class AuditLogListResponse(BaseModel):
    """List of audit logs"""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int