from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

from .base import BaseResponse

class AuditLogResponse(BaseResponse):
    """Audit log entry response"""
    id: str = Field(..., description="Audit log unique identifier")
    user_id: Optional[str] = Field(None, description="User ID who performed the action")
    user_email: Optional[str] = Field(None, description="User email")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    action: str = Field(..., description="Action performed (create, update, delete, login, etc.)")
    entity_type: Optional[str] = Field(None, description="Type of entity affected")
    entity_id: Optional[str] = Field(None, description="ID of entity affected")
    changes: Optional[Dict[str, Any]] = Field(None, description="Changes made (before/after)")
    context_info: Optional[Dict[str, Any]] = Field(None, description="Additional context information")
    ip_address: Optional[str] = Field(None, description="IP address of the request")
    user_agent: Optional[str] = Field(None, description="User agent string")
    status: str = Field(..., description="Status: success, failure, error")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: Optional[float] = Field(None, description="Operation duration in milliseconds")
    created_at: datetime = Field(..., description="Timestamp of the action")

    @field_validator('entity_id', mode='before')
    @classmethod
    def convert_entity_id_to_str(cls, value):
        """Convert entity_id to string if it's a UUID."""
        from .base import serialize_uuid_field
        return serialize_uuid_field(value)

class AuditLogCreate(BaseModel):
    """Create audit log entry"""
    user_id: Optional[str] = Field(None, description="User ID")
    user_email: Optional[str] = Field(None, description="User email")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    action: str = Field(..., description="Action performed")
    entity_type: Optional[str] = Field(None, description="Entity type")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    changes: Optional[Dict[str, Any]] = Field(None, description="Changes made")
    context_info: Optional[Dict[str, Any]] = Field(None, description="Context information")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    status: Literal["success", "failure", "error"] = Field(..., description="Operation status")
    error_message: Optional[str] = Field(None, description="Error message")
    duration_ms: Optional[float] = Field(None, description="Duration in ms")

class AuditLogListRequest(BaseModel):
    """Request for listing audit logs"""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    user_email: Optional[str] = Field(None, description="Filter by user email")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    action: Optional[str] = Field(None, description="Filter by action")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    entity_id: Optional[str] = Field(None, description="Filter by entity ID")
    status: Optional[Literal["success", "failure", "error"]] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    search: Optional[str] = Field(None, description="Global search query")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Page size")
    sort_by: Optional[str] = Field(default="created_at", description="Sort field")
    sort_order: Optional[Literal["asc", "desc"]] = Field(default="desc", description="Sort order")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action": "login",
                "status": "success",
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-01-31T23:59:59Z",
                "page": 1,
                "page_size": 50
            }
        }
    )

class AuditLogListResponse(BaseModel):
    """List of audit logs"""
    logs: List[AuditLogResponse] = Field(..., description="List of audit log entries")
    total: int = Field(..., description="Total count")
    filtered: int = Field(..., description="Filtered count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(default=False, description="Whether there's a next page")
    has_prev: bool = Field(default=False, description="Whether there's a previous page")

class AuditLogStatsResponse(BaseModel):
    """Audit log statistics"""
    total_logs: int = Field(..., description="Total number of logs")
    success_count: int = Field(..., description="Number of successful operations")
    failure_count: int = Field(..., description="Number of failed operations")
    error_count: int = Field(..., description="Number of errors")
    unique_users: int = Field(..., description="Number of unique users")
    top_actions: List[Dict[str, Any]] = Field(..., description="Top actions by count")
    activity_by_hour: Optional[Dict[str, int]] = Field(None, description="Activity distribution by hour")
    activity_by_day: Optional[Dict[str, int]] = Field(None, description="Activity distribution by day")

class AuditLogExportRequest(BaseModel):
    """Request to export audit logs"""
    filters: Optional[AuditLogListRequest] = Field(None, description="Filters to apply")
    format: Literal["csv", "xlsx", "json"] = Field(default="csv", description="Export format")
    fields: Optional[List[str]] = Field(None, description="Fields to include in export")
    include_changes: bool = Field(default=True, description="Include changes details")