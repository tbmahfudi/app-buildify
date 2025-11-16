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

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

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

# Tenant Schemas
class TenantBase(BaseModel):
    """Base tenant schema"""
    name: str = Field(..., max_length=255, description="Tenant name")
    code: str = Field(..., max_length=50, description="Tenant code (unique)")
    description: Optional[str] = Field(None, description="Tenant description")
    subscription_tier: Optional[str] = Field("free", description="Subscription tier (free, basic, premium, enterprise)")
    subscription_status: Optional[str] = Field("active", description="Subscription status (active, suspended, cancelled)")
    max_companies: Optional[int] = Field(10, description="Maximum number of companies")
    max_users: Optional[int] = Field(500, description="Maximum number of users")
    max_storage_gb: Optional[int] = Field(10, description="Maximum storage in GB")
    is_active: Optional[bool] = Field(True, description="Whether tenant is active")
    is_trial: Optional[bool] = Field(False, description="Whether tenant is in trial")
    contact_name: Optional[str] = Field(None, max_length=255, description="Contact person name")
    contact_email: Optional[str] = Field(None, max_length=255, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")
    primary_color: Optional[str] = Field(None, max_length=7, description="Primary brand color (hex)")

class TenantCreate(TenantBase):
    """Create tenant request"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Acme Corporation",
                "code": "ACME",
                "description": "Acme Corporation - Premium Tenant",
                "subscription_tier": "premium",
                "max_companies": 50,
                "max_users": 1000,
                "contact_email": "admin@acme.com"
            }
        }
    )

class TenantUpdate(BaseModel):
    """Update tenant request"""
    name: Optional[str] = Field(None, max_length=255, description="Tenant name")
    code: Optional[str] = Field(None, max_length=50, description="Tenant code")
    description: Optional[str] = Field(None, description="Tenant description")
    subscription_tier: Optional[str] = Field(None, description="Subscription tier")
    subscription_status: Optional[str] = Field(None, description="Subscription status")
    max_companies: Optional[int] = Field(None, description="Maximum number of companies")
    max_users: Optional[int] = Field(None, description="Maximum number of users")
    max_storage_gb: Optional[int] = Field(None, description="Maximum storage in GB")
    is_active: Optional[bool] = Field(None, description="Whether tenant is active")
    is_trial: Optional[bool] = Field(None, description="Whether tenant is in trial")
    contact_name: Optional[str] = Field(None, max_length=255, description="Contact person name")
    contact_email: Optional[str] = Field(None, max_length=255, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")
    primary_color: Optional[str] = Field(None, max_length=7, description="Primary brand color")

class TenantResponse(BaseResponse):
    """Tenant response"""
    id: str = Field(..., description="Tenant unique identifier")
    name: str = Field(..., description="Tenant name")
    code: str = Field(..., description="Tenant code")
    description: Optional[str] = Field(None, description="Tenant description")
    subscription_tier: str = Field(..., description="Subscription tier")
    subscription_status: str = Field(..., description="Subscription status")
    subscription_start: Optional[datetime] = Field(None, description="Subscription start date")
    subscription_end: Optional[datetime] = Field(None, description="Subscription end date")
    max_companies: int = Field(..., description="Maximum number of companies")
    max_users: int = Field(..., description="Maximum number of users")
    max_storage_gb: int = Field(..., description="Maximum storage in GB")
    current_companies: int = Field(..., description="Current number of companies")
    current_users: int = Field(..., description="Current number of users")
    current_storage_gb: int = Field(..., description="Current storage usage in GB")
    is_active: bool = Field(..., description="Whether tenant is active")
    is_trial: bool = Field(..., description="Whether tenant is in trial")
    contact_name: Optional[str] = Field(None, description="Contact person name")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    primary_color: Optional[str] = Field(None, description="Primary brand color")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)

class TenantListResponse(BaseModel):
    """List of tenants response"""
    items: List[TenantResponse] = Field(..., description="List of tenants")
    total: int = Field(..., description="Total count")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Page size")