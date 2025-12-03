"""
Invoice Pydantic Schemas

Request/response schemas for Invoice operations.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator


# Invoice line item schemas
class InvoiceLineItemBase(BaseModel):
    """Base invoice line item schema"""
    line_number: int = Field(..., ge=1, description="Line number")
    description: str = Field(..., min_length=1, description="Line item description")
    item_id: Optional[str] = Field(None, description="Item ID reference")
    item_code: Optional[str] = Field(None, max_length=50, description="Item code")
    quantity: Decimal = Field(..., gt=0, description="Quantity")
    unit_price: Decimal = Field(..., ge=0, description="Unit price")
    discount_percentage: Decimal = Field(default=Decimal('0.00'), ge=0, le=100)
    tax_rate_id: Optional[str] = Field(None, description="Tax rate ID")
    tax_percentage: Decimal = Field(default=Decimal('0.00'), ge=0, le=100)
    is_taxable: bool = Field(default=True, description="Whether line is taxable")
    revenue_account_id: Optional[str] = Field(None, description="Revenue account ID")
    department_id: Optional[str] = Field(None, description="Department ID")
    project_id: Optional[str] = Field(None, description="Project ID")
    extra_data: Optional[str] = None

    @validator('quantity', 'unit_price')
    def validate_decimal_places(cls, v):
        """Ensure amounts have max 4 decimal places for quantity, 2 for price"""
        return v

    class Config:
        from_attributes = True


class InvoiceLineItemCreate(InvoiceLineItemBase):
    """Schema for creating invoice line item"""
    pass


class InvoiceLineItemUpdate(BaseModel):
    """Schema for updating invoice line item"""
    line_number: Optional[int] = None
    description: Optional[str] = None
    item_id: Optional[str] = None
    item_code: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    tax_rate_id: Optional[str] = None
    tax_percentage: Optional[Decimal] = None
    is_taxable: Optional[bool] = None
    revenue_account_id: Optional[str] = None
    department_id: Optional[str] = None
    project_id: Optional[str] = None
    extra_data: Optional[str] = None

    class Config:
        from_attributes = True


class InvoiceLineItemResponse(InvoiceLineItemBase):
    """Schema for invoice line item response"""
    id: str
    invoice_id: str
    line_total: Decimal
    discount_amount: Decimal
    tax_amount: Decimal

    class Config:
        from_attributes = True


# Invoice schemas
class InvoiceBase(BaseModel):
    """Base invoice schema with common fields"""
    invoice_number: str = Field(..., min_length=1, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    customer_id: str = Field(..., description="Customer ID")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: date = Field(..., description="Due date")
    payment_terms_days: int = Field(default=30, ge=0)
    description: Optional[str] = None
    memo: Optional[str] = None
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    discount_type: Optional[str] = Field(None, description="percentage or fixed")
    discount_value: Decimal = Field(default=Decimal('0.00'), ge=0)
    shipping_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    tags: Optional[str] = None
    extra_data: Optional[str] = None

    @validator('discount_type')
    def validate_discount_type(cls, v):
        """Validate discount type"""
        if v is not None and v not in ['percentage', 'fixed']:
            raise ValueError("Discount type must be 'percentage' or 'fixed'")
        return v

    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Ensure due date is not before invoice date"""
        if 'invoice_date' in values and v < values['invoice_date']:
            raise ValueError("Due date cannot be before invoice date")
        return v

    class Config:
        from_attributes = True


class InvoiceCreate(InvoiceBase):
    """Schema for creating a new invoice"""
    tenant_id: str = Field(..., description="Tenant ID")
    company_id: str = Field(..., description="Company ID")
    created_by: str = Field(..., description="User ID who created the invoice")
    line_items: List[InvoiceLineItemCreate] = Field(..., min_items=1, description="Invoice line items")


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice"""
    invoice_number: Optional[str] = None
    reference_number: Optional[str] = None
    customer_id: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_terms_days: Optional[int] = None
    description: Optional[str] = None
    memo: Optional[str] = None
    currency_code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[Decimal] = None
    shipping_amount: Optional[Decimal] = None
    tags: Optional[str] = None
    extra_data: Optional[str] = None
    updated_by: str = Field(..., description="User ID who updated the invoice")

    class Config:
        from_attributes = True


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response"""
    id: str
    tenant_id: str
    company_id: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    journal_entry_id: Optional[str]
    sent_at: Optional[datetime]
    sent_by: Optional[str]
    delivered_at: Optional[datetime]
    last_payment_date: Optional[date]
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # Computed properties
    is_draft: bool
    is_paid: bool
    is_overdue: bool
    can_edit: bool
    can_void: bool

    # Line items
    line_items: List[InvoiceLineItemResponse] = []

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list"""
    invoices: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class InvoiceSummary(BaseModel):
    """Schema for invoice summary"""
    id: str
    invoice_number: str
    customer_id: str
    customer_name: str
    invoice_date: date
    due_date: date
    status: str
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    is_overdue: bool

    class Config:
        from_attributes = True


class InvoiceStatusUpdate(BaseModel):
    """Schema for updating invoice status"""
    status: str = Field(..., description="New status")
    updated_by: str = Field(..., description="User ID who updated the status")

    @validator('status')
    def validate_status(cls, v):
        """Validate status"""
        allowed_statuses = ['draft', 'sent', 'partially_paid', 'paid', 'overdue', 'void', 'cancelled']
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of {allowed_statuses}")
        return v


class InvoiceSendRequest(BaseModel):
    """Schema for sending invoice to customer"""
    send_via: str = Field(..., description="Method: email, print, portal")
    recipient_email: Optional[str] = Field(None, description="Email address if sending via email")
    message: Optional[str] = Field(None, description="Message to include")
    sent_by: str = Field(..., description="User ID who sent the invoice")

    @validator('send_via')
    def validate_send_via(cls, v):
        """Validate send method"""
        if v not in ['email', 'print', 'portal']:
            raise ValueError("send_via must be 'email', 'print', or 'portal'")
        return v
