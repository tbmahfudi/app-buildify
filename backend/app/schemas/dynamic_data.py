"""
Pydantic Schemas for Dynamic Data API

These schemas provide request/response validation for the dynamic data endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class DynamicDataCreateRequest(BaseModel):
    """Request schema for creating a record"""
    data: Dict[str, Any] = Field(
        ...,
        description="Record data (field name -> value mapping)",
        example={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890"
        }
    )


class DynamicDataUpdateRequest(BaseModel):
    """Request schema for updating a record"""
    data: Dict[str, Any] = Field(
        ...,
        description="Fields to update (partial update supported)",
        example={
            "phone": "+0987654321",
            "status": "active"
        }
    )


class DynamicDataResponse(BaseModel):
    """Response schema for single record"""
    id: str = Field(..., description="Record ID")
    data: Dict[str, Any] = Field(..., description="Record data")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "data": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890",
                    "created_at": "2026-01-11T10:30:00Z",
                    "updated_at": "2026-01-11T10:30:00Z"
                }
            }
        }


class DynamicDataListResponse(BaseModel):
    """Response schema for list of records"""
    items: List[Dict[str, Any]] = Field(..., description="List of records")
    total: int = Field(..., description="Total number of records (before pagination)")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "uuid-1",
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com"
                    },
                    {
                        "id": "uuid-2",
                        "first_name": "Jane",
                        "last_name": "Smith",
                        "email": "jane@example.com"
                    }
                ],
                "total": 150,
                "page": 1,
                "page_size": 25,
                "pages": 6
            }
        }


class DynamicDataBulkCreateRequest(BaseModel):
    """Request schema for bulk create"""
    records: List[Dict[str, Any]] = Field(
        ...,
        description="List of records to create",
        min_length=1,
        example=[
            {"first_name": "John", "last_name": "Doe", "email": "john@example.com"},
            {"first_name": "Jane", "last_name": "Smith", "email": "jane@example.com"}
        ]
    )


class DynamicDataBulkUpdateRequest(BaseModel):
    """Request schema for bulk update"""
    records: List[Dict[str, Any]] = Field(
        ...,
        description="List of records to update (each must include 'id' field)",
        min_length=1,
        example=[
            {"id": "uuid-1", "status": "active"},
            {"id": "uuid-2", "status": "active"}
        ]
    )


class DynamicDataBulkDeleteRequest(BaseModel):
    """Request schema for bulk delete"""
    ids: List[str] = Field(
        ...,
        description="List of record IDs to delete",
        min_length=1,
        example=["uuid-1", "uuid-2", "uuid-3"]
    )


class DynamicDataBulkResponse(BaseModel):
    """Response schema for bulk operations"""
    created: Optional[int] = Field(None, description="Number of records created")
    updated: Optional[int] = Field(None, description="Number of records updated")
    deleted: Optional[int] = Field(None, description="Number of records deleted")
    failed: int = Field(..., description="Number of failed operations")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of errors for failed operations"
    )
    ids: Optional[List[str]] = Field(
        None,
        description="List of created record IDs (for bulk create)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "created": 2,
                "failed": 0,
                "errors": [],
                "ids": ["uuid-1", "uuid-2"]
            }
        }


class FilterCondition(BaseModel):
    """Single filter condition"""
    field: str = Field(..., description="Field name to filter on")
    operator: str = Field(
        ...,
        description="Comparison operator",
        pattern="^(eq|ne|gt|gte|lt|lte|contains|starts_with|ends_with|in|not_in|is_null|is_not_null|like|ilike)$"
    )
    value: Optional[Any] = Field(None, description="Value to compare against")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "email",
                "operator": "contains",
                "value": "@example.com"
            }
        }


class FilterGroup(BaseModel):
    """Group of filter conditions with AND/OR operator"""
    operator: str = Field(
        ...,
        description="Logical operator to combine conditions",
        pattern="^(AND|OR)$"
    )
    conditions: List[Any] = Field(
        ...,
        description="List of conditions or nested filter groups"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "operator": "AND",
                "conditions": [
                    {
                        "field": "email",
                        "operator": "contains",
                        "value": "@example.com"
                    },
                    {
                        "field": "created_at",
                        "operator": "gte",
                        "value": "2026-01-01"
                    }
                ]
            }
        }


class EntityMetadataResponse(BaseModel):
    """Response schema for entity metadata"""
    entity_name: str
    display_name: str
    fields: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "entity_name": "customers",
                "display_name": "Customers",
                "fields": [
                    {
                        "name": "first_name",
                        "label": "First Name",
                        "field_type": "string",
                        "is_required": True
                    },
                    {
                        "name": "email",
                        "label": "Email",
                        "field_type": "email",
                        "is_required": True
                    }
                ],
                "relationships": []
            }
        }


class ValidationErrorResponse(BaseModel):
    """Response schema for validation errors"""
    detail: str = Field(..., description="Error message")
    errors: Optional[List[str]] = Field(None, description="List of specific validation errors")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Validation failed",
                "errors": [
                    "Email is required",
                    "Phone must be <= 20 characters"
                ]
            }
        }


class NotFoundResponse(BaseModel):
    """Response schema for not found errors"""
    detail: str = Field(..., description="Error message")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Record not found: 550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ForbiddenResponse(BaseModel):
    """Response schema for permission denied errors"""
    detail: str = Field(..., description="Error message")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Permission denied: customers:create:tenant"
            }
        }
