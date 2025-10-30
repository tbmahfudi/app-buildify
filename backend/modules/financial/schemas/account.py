"""
Account Schemas for Financial Module
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AccountBase(BaseModel):
    """Base account schema"""
    code: str = Field(..., description="Account code")
    name: str = Field(..., description="Account name")
    description: Optional[str] = None
    account_type: str = Field(..., description="Account type: asset, liability, equity, revenue, expense")
    account_subtype: Optional[str] = None
    parent_account_id: Optional[str] = None
    is_active: bool = True
    is_header: bool = False
    allow_manual_entry: bool = True
    currency: str = "USD"


class AccountCreate(AccountBase):
    """Schema for creating an account"""
    company_id: str


class AccountUpdate(BaseModel):
    """Schema for updating an account"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    allow_manual_entry: Optional[bool] = None


class AccountResponse(AccountBase):
    """Account response schema"""
    id: str
    tenant_id: str
    company_id: str
    current_balance: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
