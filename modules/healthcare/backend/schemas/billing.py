"""
Healthcare Billing -- Pydantic v2 schemas.

T-HC-052 / T-HC-053 / T-HC-054
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Service Items
# ---------------------------------------------------------------------------

class ServiceItemCreate(BaseModel):
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    unit_price: Decimal = Field(..., ge=0)
    currency: str = Field(default="IDR", max_length=3)
    category: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class ServiceItemUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    category: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    # NOTE: code intentionally excluded -- cannot change if used in invoice lines


class ServiceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    name: str
    code: str
    unit_price: Decimal
    currency: str
    category: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ServiceItemListResponse(BaseModel):
    items: List[ServiceItemResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Invoice Lines
# ---------------------------------------------------------------------------

class InvoiceLineCreate(BaseModel):
    service_item_id: str
    quantity: int = Field(default=1, ge=1)


class InvoiceLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    service_item_id: Optional[str]
    item_name: str
    item_code: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------

class InvoiceCreate(BaseModel):
    patient_id: str
    encounter_id: Optional[str] = None
    insurance_profile_id: Optional[str] = None
    lines: List[InvoiceLineCreate] = Field(..., min_length=1)
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    patient_id: str
    patient_display: Optional[str] = None  # masked name e.g. "J*** D***"
    encounter_id: Optional[str]
    invoice_number: str
    status: str
    total_amount: Decimal
    currency: str
    insurance_profile_id: Optional[str]
    notes: Optional[str]
    finalized_at: Optional[datetime]
    voided_at: Optional[datetime]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []


class InvoiceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_number: str
    patient_id: str
    status: str
    total_amount: Decimal
    currency: str
    created_at: datetime
    finalized_at: Optional[datetime]


class InvoiceListResponse(BaseModel):
    items: List[InvoiceListItem]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., pattern="^(cash|transfer|bpjs|insurance|other)$")
    payment_date: datetime
    reference_number: Optional[str] = Field(None, max_length=100)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: str
    amount: Decimal
    currency: str
    payment_method: str
    payment_date: datetime
    reference_number: Optional[str]
    recorded_by: Optional[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# Insurance Profiles
# ---------------------------------------------------------------------------

class InsuranceProfileCreate(BaseModel):
    insurance_type: str = Field(..., pattern="^(bpjs|private|none)$")
    insurance_number: Optional[str] = Field(None, max_length=100)
    provider_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class InsuranceProfileUpdate(BaseModel):
    insurance_type: Optional[str] = Field(None, pattern="^(bpjs|private|none)$")
    insurance_number: Optional[str] = Field(None, max_length=100)
    provider_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class InsuranceProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    patient_id: str
    insurance_type: str
    insurance_number: Optional[str]  # decrypted for display
    provider_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Patient-facing invoice (T-HC-053)
# ---------------------------------------------------------------------------

class PatientInvoiceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_number: str
    total_amount: Decimal
    currency: str
    status: str
    encounter_date: Optional[datetime]
    clinic_name: Optional[str]
    created_at: datetime


class PatientInvoiceListResponse(BaseModel):
    items: List[PatientInvoiceListItem]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# BPJS Export (T-HC-054)
# ---------------------------------------------------------------------------

class BPJSExportCreate(BaseModel):
    export_period: str = Field(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class BPJSExportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    export_period: str
    status: str
    record_count: Optional[int]
    total_amount: Optional[Decimal]
    generated_at: Optional[datetime]
    download_url: str
    created_at: datetime
