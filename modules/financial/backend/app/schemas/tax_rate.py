"""
Tax Rate Pydantic Schemas

Request/response schemas for Tax Rate operations.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator


# Base schema with common fields
class TaxRateBase(BaseModel):
    """Base tax rate schema with common fields"""
    code: str = Field(..., min_length=1, max_length=50, description="Tax rate code")
    name: str = Field(..., min_length=1, max_length=255, description="Tax rate name")
    description: Optional[str] = None
    rate_percentage: Decimal = Field(..., ge=0, le=100, description="Tax rate percentage")
    tax_type: str = Field(..., description="Tax type")
    tax_authority: Optional[str] = Field(None, max_length=255)
    tax_jurisdiction: Optional[str] = Field(None, max_length=100)
    effective_from: date = Field(..., description="Effective from date")
    effective_to: Optional[date] = None
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    is_compound: bool = Field(default=False, description="Whether tax is compound")
    tax_account_id: Optional[str] = Field(None, description="Tax collection account ID")
    applies_to_sales: bool = Field(default=True)
    applies_to_purchases: bool = Field(default=False)
    country_code: Optional[str] = Field(None, max_length=2)
    state_code: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    extra_data: Optional[str] = None

    @validator('tax_type')
    def validate_tax_type(cls, v):
        """Validate tax type"""
        allowed_types = ['sales_tax', 'vat', 'gst', 'excise', 'service_tax', 'other']
        if v not in allowed_types:
            raise ValueError(f"Tax type must be one of {allowed_types}")
        return v

    @validator('effective_to')
    def validate_effective_dates(cls, v, values):
        """Ensure effective_to is after effective_from"""
        if v is not None and 'effective_from' in values:
            if v < values['effective_from']:
                raise ValueError("Effective to date cannot be before effective from date")
        return v

    @validator('rate_percentage')
    def validate_rate_percentage(cls, v):
        """Ensure rate has max 2 decimal places"""
        if v.as_tuple().exponent < -2:
            raise ValueError("Rate percentage cannot have more than 2 decimal places")
        return v

    class Config:
        from_attributes = True


# Schema for creating a new tax rate
class TaxRateCreate(TaxRateBase):
    """Schema for creating a new tax rate"""
    tenant_id: str = Field(..., description="Tenant ID")
    company_id: str = Field(..., description="Company ID")
    created_by: str = Field(..., description="User ID who created the tax rate")


# Schema for updating a tax rate
class TaxRateUpdate(BaseModel):
    """Schema for updating a tax rate"""
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    rate_percentage: Optional[Decimal] = None
    tax_type: Optional[str] = None
    tax_authority: Optional[str] = None
    tax_jurisdiction: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    is_compound: Optional[bool] = None
    tax_account_id: Optional[str] = None
    applies_to_sales: Optional[bool] = None
    applies_to_purchases: Optional[bool] = None
    country_code: Optional[str] = None
    state_code: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    extra_data: Optional[str] = None
    updated_by: str = Field(..., description="User ID who updated the tax rate")

    class Config:
        from_attributes = True


# Schema for tax rate response
class TaxRateResponse(TaxRateBase):
    """Schema for tax rate response"""
    id: str
    tenant_id: str
    company_id: str
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # Computed fields
    full_name: str
    is_valid: bool

    class Config:
        from_attributes = True


# Schema for tax rate list response
class TaxRateListResponse(BaseModel):
    """Schema for paginated tax rate list"""
    tax_rates: List[TaxRateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Schema for tax calculation
class TaxCalculationRequest(BaseModel):
    """Schema for tax calculation request"""
    amount: Decimal = Field(..., gt=0, description="Amount to calculate tax on")
    tax_rate_id: str = Field(..., description="Tax rate ID to use")

    class Config:
        from_attributes = True


class TaxCalculationResponse(BaseModel):
    """Schema for tax calculation response"""
    amount: Decimal
    tax_rate_id: str
    tax_rate_code: str
    tax_rate_name: str
    tax_percentage: Decimal
    tax_amount: Decimal
    total_amount: Decimal

    class Config:
        from_attributes = True
