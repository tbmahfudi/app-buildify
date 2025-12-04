"""
Customer Pydantic Schemas

Request/response schemas for Customer operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator


# Base schema with common fields
class CustomerBase(BaseModel):
    """Base customer schema with common fields"""
    customer_number: str = Field(..., min_length=1, max_length=50, description="Customer number")
    name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    display_name: Optional[str] = Field(None, max_length=255, description="Display name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")

    # Billing address
    billing_address_line1: Optional[str] = Field(None, max_length=255)
    billing_address_line2: Optional[str] = Field(None, max_length=255)
    billing_city: Optional[str] = Field(None, max_length=100)
    billing_state: Optional[str] = Field(None, max_length=100)
    billing_postal_code: Optional[str] = Field(None, max_length=20)
    billing_country: Optional[str] = Field(None, max_length=100)

    # Shipping address
    shipping_address_line1: Optional[str] = Field(None, max_length=255)
    shipping_address_line2: Optional[str] = Field(None, max_length=255)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=100)
    shipping_postal_code: Optional[str] = Field(None, max_length=20)
    shipping_country: Optional[str] = Field(None, max_length=100)

    # Financial details
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    payment_terms_days: int = Field(default=30, ge=0, description="Payment terms in days")
    credit_limit: Optional[Decimal] = Field(None, ge=0, description="Credit limit")

    # Tax information
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax ID number")
    tax_exempt: bool = Field(default=False, description="Whether customer is tax exempt")

    # Accounts
    receivables_account_id: Optional[str] = Field(None, description="Receivables account ID")

    # Status
    is_active: bool = Field(default=True, description="Whether customer is active")

    # Metadata
    notes: Optional[str] = Field(None, description="Notes")
    extra_data: Optional[str] = Field(None, description="Additional data as JSON string")

    class Config:
        from_attributes = True


# Schema for creating a new customer
class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""
    tenant_id: str = Field(..., description="Tenant ID")
    company_id: str = Field(..., description="Company ID")
    created_by: str = Field(..., description="User ID who created the customer")


# Schema for updating a customer
class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""
    customer_number: Optional[str] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    billing_address_line1: Optional[str] = None
    billing_address_line2: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None

    shipping_address_line1: Optional[str] = None
    shipping_address_line2: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = None

    currency_code: Optional[str] = None
    payment_terms_days: Optional[int] = None
    credit_limit: Optional[Decimal] = None

    tax_id: Optional[str] = None
    tax_exempt: Optional[bool] = None

    receivables_account_id: Optional[str] = None
    is_active: Optional[bool] = None

    notes: Optional[str] = None
    extra_data: Optional[str] = None

    updated_by: str = Field(..., description="User ID who updated the customer")

    class Config:
        from_attributes = True


# Schema for customer response
class CustomerResponse(CustomerBase):
    """Schema for customer response"""
    id: str
    tenant_id: str
    company_id: str
    current_balance: Decimal
    overdue_balance: Decimal
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # Computed fields
    full_address: str
    has_overdue_balance: bool

    class Config:
        from_attributes = True


# Schema for customer list response
class CustomerListResponse(BaseModel):
    """Schema for paginated customer list"""
    customers: List[CustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Schema for customer balance summary
class CustomerBalanceSummary(BaseModel):
    """Schema for customer balance summary"""
    customer_id: str
    customer_number: str
    customer_name: str
    current_balance: Decimal
    overdue_balance: Decimal
    credit_limit: Optional[Decimal]
    available_credit: Optional[Decimal]

    class Config:
        from_attributes = True
