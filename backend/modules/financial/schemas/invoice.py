"""
Invoice Schemas for Financial Module
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class InvoiceLineItemBase(BaseModel):
    """Base invoice line item schema"""
    description: str
    quantity: float
    unit_price: float
    tax_rate: float = 0


class InvoiceLineItemCreate(InvoiceLineItemBase):
    """Schema for creating invoice line item"""
    pass


class InvoiceLineItemResponse(InvoiceLineItemBase):
    """Invoice line item response"""
    id: str
    line_number: int
    amount: float
    tax_amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    """Base invoice schema"""
    invoice_number: str
    invoice_date: datetime
    due_date: datetime
    customer_name: str
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    currency: str = "USD"


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice"""
    company_id: str
    line_items: List[InvoiceLineItemCreate]


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice"""
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    status: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema"""
    id: str
    tenant_id: str
    company_id: str
    subtotal: float
    tax_amount: float
    total_amount: float
    paid_amount: float
    status: str
    sent_at: Optional[datetime] = None
    line_items: List[InvoiceLineItemResponse]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
