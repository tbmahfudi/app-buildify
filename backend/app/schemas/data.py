from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Literal

class FilterCondition(BaseModel):
    """Filter condition for data search"""
    field: str = Field(..., description="Field name to filter")
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "nin", "contains", "startswith", "endswith"] = Field(..., description="Filter operator")
    value: Any = Field(..., description="Filter value")

class DataSearchRequest(BaseModel):
    """Request for searching/listing data"""
    entity: str = Field(..., description="Entity name to search")
    filters: Optional[List[FilterCondition]] = Field(default_factory=list, description="Filter conditions")
    sort: Optional[List[List[str]]] = Field(default_factory=list, description="Sort configuration [[field, asc/desc]]")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=25, ge=1, le=100, description="Number of items per page")
    search: Optional[str] = Field(None, description="Global search query")
    scope: Optional[Dict[str, Any]] = Field(None, description="Organizational scope filters")
    fields: Optional[List[str]] = Field(None, description="Specific fields to return")

    @field_validator('page_size')
    @classmethod
    def validate_page_size(cls, v):
        if v > 100:
            return 100
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entity": "users",
                "filters": [
                    {"field": "status", "operator": "eq", "value": "active"}
                ],
                "sort": [["created_at", "desc"]],
                "page": 1,
                "page_size": 25,
                "search": "john"
            }
        }
    )

class DataSearchResponse(BaseModel):
    """Response for data search"""
    rows: List[Dict[str, Any]] = Field(..., description="Data rows")
    total: int = Field(..., description="Total count before filtering")
    filtered: int = Field(..., description="Count after filtering")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(default=False, description="Whether there's a next page")
    has_prev: bool = Field(default=False, description="Whether there's a previous page")

class DataCreateRequest(BaseModel):
    """Request to create a record"""
    entity: str = Field(..., description="Entity name")
    data: Dict[str, Any] = Field(..., description="Record data")
    scope: Optional[Dict[str, Any]] = Field(None, description="Organizational scope")
    return_record: bool = Field(default=True, description="Whether to return the created record")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entity": "users",
                "data": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "status": "active"
                }
            }
        }
    )

class DataUpdateRequest(BaseModel):
    """Request to update a record"""
    entity: str = Field(..., description="Entity name")
    id: str = Field(..., description="Record ID")
    data: Dict[str, Any] = Field(..., description="Updated data")
    version: Optional[int] = Field(None, description="Version for optimistic locking")
    partial: bool = Field(default=True, description="Whether to perform partial update (PATCH)")
    return_record: bool = Field(default=True, description="Whether to return the updated record")

class DataDeleteRequest(BaseModel):
    """Request to delete a record"""
    entity: str = Field(..., description="Entity name")
    id: str = Field(..., description="Record ID")
    version: Optional[int] = Field(None, description="Version for optimistic locking")

class DataResponse(BaseModel):
    """Single record response"""
    id: str = Field(..., description="Record ID")
    data: Dict[str, Any] = Field(..., description="Record data")
    version: Optional[int] = Field(None, description="Record version")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

class BulkOperationRequest(BaseModel):
    """Bulk operation request"""
    entity: str = Field(..., description="Entity name")
    operation: Literal["create", "update", "delete", "upsert"] = Field(..., description="Operation type")
    records: List[Dict[str, Any]] = Field(..., description="Records to process")
    batch_size: int = Field(default=100, ge=1, le=1000, description="Batch processing size")
    continue_on_error: bool = Field(default=False, description="Whether to continue on error")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entity": "users",
                "operation": "create",
                "records": [
                    {"name": "User 1", "email": "user1@example.com"},
                    {"name": "User 2", "email": "user2@example.com"}
                ],
                "batch_size": 100
            }
        }
    )

class BulkOperationError(BaseModel):
    """Individual error in bulk operation"""
    index: int = Field(..., description="Record index")
    record: Dict[str, Any] = Field(..., description="Failed record")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")

class BulkOperationResponse(BaseModel):
    """Bulk operation response"""
    total: int = Field(..., description="Total records processed")
    success: int = Field(..., description="Successfully processed count")
    failed: int = Field(..., description="Failed count")
    errors: List[BulkOperationError] = Field(default_factory=list, description="Detailed errors")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    created_ids: Optional[List[str]] = Field(None, description="IDs of created records")

class DataExportRequest(BaseModel):
    """Request to export data"""
    entity: str = Field(..., description="Entity name")
    filters: Optional[List[FilterCondition]] = Field(default_factory=list, description="Filter conditions")
    format: Literal["csv", "xlsx", "json"] = Field(default="csv", description="Export format")
    fields: Optional[List[str]] = Field(None, description="Fields to export")
    include_headers: bool = Field(default=True, description="Include headers in export")

class DataImportRequest(BaseModel):
    """Request to import data"""
    entity: str = Field(..., description="Entity name")
    data: List[Dict[str, Any]] = Field(..., description="Data to import")
    mode: Literal["insert", "update", "upsert"] = Field(default="insert", description="Import mode")
    unique_fields: Optional[List[str]] = Field(None, description="Fields to check for uniqueness")