from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

from .base import BaseResponse

# Company Schemas
class CompanyBase(BaseModel):
    """Base company schema"""
    code: str = Field(..., max_length=32, description="Company code")
    name: str = Field(..., max_length=255, description="Company name")

class CompanyCreate(CompanyBase):
    """Create company request"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "COMP001",
                "name": "Example Company"
            }
        }
    )

class CompanyUpdate(BaseModel):
    """Update company request"""
    code: Optional[str] = Field(None, max_length=32, description="Company code")
    name: Optional[str] = Field(None, max_length=255, description="Company name")

class CompanyResponse(CompanyBase, BaseResponse):
    """Company response"""
    id: str = Field(..., description="Company unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

# Branch Schemas
class BranchBase(BaseModel):
    """Base branch schema"""
    company_id: str = Field(..., description="Company ID")
    code: str = Field(..., max_length=32, description="Branch code")
    name: str = Field(..., max_length=255, description="Branch name")

class BranchCreate(BranchBase):
    """Create branch request"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "code": "BR001",
                "name": "Main Branch"
            }
        }
    )

class BranchUpdate(BaseModel):
    """Update branch request"""
    code: Optional[str] = Field(None, max_length=32, description="Branch code")
    name: Optional[str] = Field(None, max_length=255, description="Branch name")

class BranchResponse(BranchBase, BaseResponse):
    """Branch response"""
    id: str = Field(..., description="Branch unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

# Department Schemas
class DepartmentBase(BaseModel):
    """Base department schema"""
    company_id: str = Field(..., description="Company ID")
    branch_id: Optional[str] = Field(None, description="Branch ID (optional)")
    code: str = Field(..., max_length=32, description="Department code")
    name: str = Field(..., max_length=255, description="Department name")

class DepartmentCreate(DepartmentBase):
    """Create department request"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "branch_id": "123e4567-e89b-12d3-a456-426614174001",
                "code": "DEPT001",
                "name": "IT Department"
            }
        }
    )

class DepartmentUpdate(BaseModel):
    """Update department request"""
    branch_id: Optional[str] = Field(None, description="Branch ID")
    code: Optional[str] = Field(None, max_length=32, description="Department code")
    name: Optional[str] = Field(None, max_length=255, description="Department name")

class DepartmentResponse(DepartmentBase, BaseResponse):
    """Department response"""
    id: str = Field(..., description="Department unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

# List responses
class CompanyListResponse(BaseModel):
    """List of companies response"""
    items: List[CompanyResponse] = Field(..., description="List of companies")
    total: int = Field(..., description="Total count")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Page size")

class BranchListResponse(BaseModel):
    """List of branches response"""
    items: List[BranchResponse] = Field(..., description="List of branches")
    total: int = Field(..., description="Total count")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Page size")

class DepartmentListResponse(BaseModel):
    """List of departments response"""
    items: List[DepartmentResponse] = Field(..., description="List of departments")
    total: int = Field(..., description="Total count")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Page size")