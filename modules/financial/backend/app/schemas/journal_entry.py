"""
Journal Entry Pydantic Schemas

Request/response schemas for Journal Entry operations.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator


# Journal entry line schemas
class JournalEntryLineBase(BaseModel):
    """Base journal entry line schema"""
    line_number: int = Field(..., ge=1, description="Line number")
    account_id: str = Field(..., description="Account ID")
    description: Optional[str] = None
    debit_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    credit_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    department_id: Optional[str] = None
    project_id: Optional[str] = None
    extra_data: Optional[str] = None

    @validator('credit_amount')
    def validate_amounts(cls, v, values):
        """Ensure either debit OR credit, not both or neither"""
        debit = values.get('debit_amount', Decimal('0.00'))
        if (debit > 0 and v > 0) or (debit == 0 and v == 0):
            raise ValueError("Each line must have either debit OR credit amount (not both or neither)")
        return v

    class Config:
        from_attributes = True


class JournalEntryLineCreate(JournalEntryLineBase):
    """Schema for creating journal entry line"""
    pass


class JournalEntryLineUpdate(BaseModel):
    """Schema for updating journal entry line"""
    line_number: Optional[int] = None
    account_id: Optional[str] = None
    description: Optional[str] = None
    debit_amount: Optional[Decimal] = None
    credit_amount: Optional[Decimal] = None
    department_id: Optional[str] = None
    project_id: Optional[str] = None
    extra_data: Optional[str] = None

    class Config:
        from_attributes = True


class JournalEntryLineResponse(JournalEntryLineBase):
    """Schema for journal entry line response"""
    id: str
    journal_entry_id: str
    is_debit: bool
    is_credit: bool
    amount: Decimal

    class Config:
        from_attributes = True


# Journal entry schemas
class JournalEntryBase(BaseModel):
    """Base journal entry schema with common fields"""
    entry_number: str = Field(..., min_length=1, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    entry_date: date = Field(..., description="Entry date")
    posting_date: Optional[date] = None
    description: str = Field(..., min_length=1, description="Entry description")
    memo: Optional[str] = None
    source_type: Optional[str] = Field(None, description="manual, invoice, payment, adjustment")
    source_id: Optional[str] = None
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    tags: Optional[str] = None
    extra_data: Optional[str] = None

    @validator('source_type')
    def validate_source_type(cls, v):
        """Validate source type"""
        if v is not None:
            allowed_types = ['manual', 'invoice', 'payment', 'adjustment']
            if v not in allowed_types:
                raise ValueError(f"Source type must be one of {allowed_types}")
        return v

    class Config:
        from_attributes = True


class JournalEntryCreate(JournalEntryBase):
    """Schema for creating a new journal entry"""
    tenant_id: str = Field(..., description="Tenant ID")
    company_id: str = Field(..., description="Company ID")
    created_by: str = Field(..., description="User ID who created the entry")
    lines: List[JournalEntryLineCreate] = Field(..., min_items=2, description="Journal entry lines")

    @validator('lines')
    def validate_balanced(cls, v):
        """Ensure debits equal credits"""
        total_debit = sum(line.debit_amount for line in v)
        total_credit = sum(line.credit_amount for line in v)
        if total_debit != total_credit:
            raise ValueError(f"Journal entry must be balanced. Debits: {total_debit}, Credits: {total_credit}")
        return v


class JournalEntryUpdate(BaseModel):
    """Schema for updating a journal entry"""
    entry_number: Optional[str] = None
    reference_number: Optional[str] = None
    entry_date: Optional[date] = None
    posting_date: Optional[date] = None
    description: Optional[str] = None
    memo: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    currency_code: Optional[str] = None
    tags: Optional[str] = None
    extra_data: Optional[str] = None
    updated_by: str = Field(..., description="User ID who updated the entry")

    class Config:
        from_attributes = True


class JournalEntryResponse(JournalEntryBase):
    """Schema for journal entry response"""
    id: str
    tenant_id: str
    company_id: str
    status: str
    is_posted: bool
    posted_at: Optional[datetime]
    posted_by: Optional[str]
    is_reversal: bool
    reversed_entry_id: Optional[str]
    reversed_at: Optional[datetime]
    reversed_by: Optional[str]
    total_debit: Decimal
    total_credit: Decimal
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # Computed properties
    is_balanced: bool
    can_post: bool
    can_edit: bool

    # Lines
    lines: List[JournalEntryLineResponse] = []

    class Config:
        from_attributes = True


class JournalEntryListResponse(BaseModel):
    """Schema for paginated journal entry list"""
    entries: List[JournalEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JournalEntrySummary(BaseModel):
    """Schema for journal entry summary"""
    id: str
    entry_number: str
    entry_date: date
    description: str
    status: str
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool

    class Config:
        from_attributes = True


class JournalEntryPostRequest(BaseModel):
    """Schema for posting a journal entry"""
    posting_date: Optional[date] = Field(None, description="Posting date (defaults to today)")
    posted_by: str = Field(..., description="User ID who posted the entry")


class JournalEntryReverseRequest(BaseModel):
    """Schema for reversing a journal entry"""
    reversal_date: date = Field(..., description="Reversal date")
    description: str = Field(..., description="Reversal description")
    reversed_by: str = Field(..., description="User ID who reversed the entry")
