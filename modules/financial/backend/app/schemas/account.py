"""
Account Pydantic Schemas

Request/response schemas for Account operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator


# Base schema with common fields
class AccountBase(BaseModel):
    """Base account schema with common fields"""
    code: str = Field(..., min_length=1, max_length=50, description="Account code")
    name: str = Field(..., min_length=1, max_length=255, description="Account name")
    description: Optional[str] = Field(None, description="Account description")
    type: str = Field(..., description="Account type: asset, liability, equity, revenue, expense")
    category: Optional[str] = Field(None, max_length=100, description="Account category")
    sub_category: Optional[str] = Field(None, max_length=100, description="Account sub-category")
    is_active: bool = Field(default=True, description="Whether account is active")
    is_header: bool = Field(default=False, description="Whether account is a header account")
    parent_account_id: Optional[str] = Field(None, description="Parent account ID for hierarchical structure")
    currency_code: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")
    tax_category: Optional[str] = Field(None, description="Tax category: taxable, non_taxable, tax_exempt")
    requires_department: bool = Field(default=False, description="Whether department is required")
    requires_project: bool = Field(default=False, description="Whether project is required")
    extra_data: Optional[str] = Field(None, description="Additional data as JSON string")

    @validator('type')
    def validate_type(cls, v):
        """Validate account type"""
        allowed_types = ['asset', 'liability', 'equity', 'revenue', 'expense']
        if v not in allowed_types:
            raise ValueError(f"Account type must be one of {allowed_types}")
        return v

    @validator('tax_category')
    def validate_tax_category(cls, v):
        """Validate tax category"""
        if v is not None:
            allowed_categories = ['taxable', 'non_taxable', 'tax_exempt']
            if v not in allowed_categories:
                raise ValueError(f"Tax category must be one of {allowed_categories}")
        return v

    class Config:
        from_attributes = True


# Schema for creating a new account
class AccountCreate(AccountBase):
    """Schema for creating a new account"""
    tenant_id: str = Field(..., description="Tenant ID")
    company_id: str = Field(..., description="Company ID")
    created_by: str = Field(..., description="User ID who created the account")


# Schema for updating an account
class AccountUpdate(BaseModel):
    """Schema for updating an account"""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    is_active: Optional[bool] = None
    is_header: Optional[bool] = None
    parent_account_id: Optional[str] = None
    currency_code: Optional[str] = None
    tax_category: Optional[str] = None
    requires_department: Optional[bool] = None
    requires_project: Optional[bool] = None
    extra_data: Optional[str] = None
    updated_by: str = Field(..., description="User ID who updated the account")

    @validator('type')
    def validate_type(cls, v):
        """Validate account type"""
        if v is not None:
            allowed_types = ['asset', 'liability', 'equity', 'revenue', 'expense']
            if v not in allowed_types:
                raise ValueError(f"Account type must be one of {allowed_types}")
        return v

    class Config:
        from_attributes = True


# Schema for account response
class AccountResponse(AccountBase):
    """Schema for account response"""
    id: str
    tenant_id: str
    company_id: str
    current_balance: Decimal
    debit_balance: Decimal
    credit_balance: Decimal
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # Computed fields
    full_name: str
    is_debit_account: bool
    is_credit_account: bool

    class Config:
        from_attributes = True


# Schema for account list response
class AccountListResponse(BaseModel):
    """Schema for paginated account list"""
    accounts: List[AccountResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Schema for account balance
class AccountBalance(BaseModel):
    """Schema for account balance"""
    account_id: str
    account_code: str
    account_name: str
    current_balance: Decimal
    debit_balance: Decimal
    credit_balance: Decimal
    currency_code: str

    class Config:
        from_attributes = True


# Schema for updating account balance
class AccountBalanceUpdate(BaseModel):
    """Schema for updating account balance"""
    debit_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    credit_amount: Decimal = Field(default=Decimal('0.00'), ge=0)

    @validator('debit_amount', 'credit_amount')
    def validate_amounts(cls, v):
        """Ensure amounts have max 2 decimal places"""
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v


# Schema for chart of accounts tree structure
class AccountTreeNode(BaseModel):
    """Schema for account in tree structure"""
    id: str
    code: str
    name: str
    full_name: str
    type: str
    is_header: bool
    current_balance: Decimal
    children: List['AccountTreeNode'] = []

    class Config:
        from_attributes = True


# Enable forward references for recursive model
AccountTreeNode.model_rebuild()
