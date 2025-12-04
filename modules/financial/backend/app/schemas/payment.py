"""
Payment Pydantic Schemas

Request/response schemas for Payment operations.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator


# Payment allocation schemas
class PaymentAllocationBase(BaseModel):
    """Base payment allocation schema"""
    invoice_id: str = Field(..., description="Invoice ID to allocate payment to")
    allocation_amount: Decimal = Field(..., gt=0, description="Amount to allocate")
    allocation_date: date = Field(..., description="Allocation date")
    description: Optional[str] = None
    extra_data: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentAllocationCreate(PaymentAllocationBase):
    """Schema for creating payment allocation"""
    created_by: str = Field(..., description="User ID who created the allocation")


class PaymentAllocationResponse(PaymentAllocationBase):
    """Schema for payment allocation response"""
    id: str
    payment_id: str
    is_voided: bool
    voided_at: Optional[datetime]
    voided_by: Optional[str]
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# Payment schemas
class PaymentBase(BaseModel):
    """Base payment schema with common fields"""
    payment_number: str = Field(..., min_length=1, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    customer_id: str = Field(..., description="Customer ID")
    payment_date: date = Field(..., description="Payment date")
    payment_method: str = Field(..., description="Payment method")
    payment_amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency_code: str = Field(default="USD", min_length=3, max_length=3)

    # Payment method specific fields
    check_number: Optional[str] = Field(None, max_length=50)
    card_last_four: Optional[str] = Field(None, max_length=4)
    transaction_id: Optional[str] = Field(None, max_length=100)
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account: Optional[str] = Field(None, max_length=50)

    # Deposit account
    deposit_account_id: str = Field(..., description="Account to deposit payment into")

    # Description
    description: Optional[str] = None
    memo: Optional[str] = None
    extra_data: Optional[str] = None

    @validator('payment_method')
    def validate_payment_method(cls, v):
        """Validate payment method"""
        allowed_methods = ['cash', 'check', 'credit_card', 'bank_transfer', 'paypal', 'stripe', 'other']
        if v not in allowed_methods:
            raise ValueError(f"Payment method must be one of {allowed_methods}")
        return v

    class Config:
        from_attributes = True


class PaymentCreate(PaymentBase):
    """Schema for creating a new payment"""
    tenant_id: str = Field(..., description="Tenant ID")
    company_id: str = Field(..., description="Company ID")
    created_by: str = Field(..., description="User ID who created the payment")
    allocations: Optional[List[PaymentAllocationCreate]] = Field(
        default=[],
        description="Optional payment allocations"
    )


class PaymentUpdate(BaseModel):
    """Schema for updating a payment"""
    payment_number: Optional[str] = None
    reference_number: Optional[str] = None
    customer_id: Optional[str] = None
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    currency_code: Optional[str] = None
    check_number: Optional[str] = None
    card_last_four: Optional[str] = None
    transaction_id: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    deposit_account_id: Optional[str] = None
    description: Optional[str] = None
    memo: Optional[str] = None
    extra_data: Optional[str] = None
    updated_by: str = Field(..., description="User ID who updated the payment")

    class Config:
        from_attributes = True


class PaymentResponse(PaymentBase):
    """Schema for payment response"""
    id: str
    tenant_id: str
    company_id: str
    status: str
    allocated_amount: Decimal
    unallocated_amount: Decimal
    is_cleared: bool
    cleared_date: Optional[date]
    journal_entry_id: Optional[str]
    is_voided: bool
    voided_at: Optional[datetime]
    voided_by: Optional[str]
    void_reason: Optional[str]
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # Computed properties
    is_fully_allocated: bool
    can_allocate: bool
    can_void: bool

    # Allocations
    allocations: List[PaymentAllocationResponse] = []

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """Schema for paginated payment list"""
    payments: List[PaymentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaymentSummary(BaseModel):
    """Schema for payment summary"""
    id: str
    payment_number: str
    customer_id: str
    customer_name: str
    payment_date: date
    payment_method: str
    payment_amount: Decimal
    allocated_amount: Decimal
    unallocated_amount: Decimal
    status: str

    class Config:
        from_attributes = True


class PaymentAllocationRequest(BaseModel):
    """Schema for allocating payment to invoices"""
    allocations: List[PaymentAllocationCreate] = Field(
        ...,
        min_items=1,
        description="Payment allocations to create"
    )

    @validator('allocations')
    def validate_allocations(cls, v):
        """Ensure no duplicate invoice IDs"""
        invoice_ids = [alloc.invoice_id for alloc in v]
        if len(invoice_ids) != len(set(invoice_ids)):
            raise ValueError("Cannot allocate to the same invoice multiple times")
        return v


class PaymentClearRequest(BaseModel):
    """Schema for clearing a payment"""
    cleared_date: date = Field(..., description="Date payment cleared")
    updated_by: str = Field(..., description="User ID who cleared the payment")


class PaymentVoidRequest(BaseModel):
    """Schema for voiding a payment"""
    void_reason: str = Field(..., min_length=1, description="Reason for voiding")
    voided_by: str = Field(..., description="User ID who voided the payment")
