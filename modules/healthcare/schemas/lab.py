"""
Healthcare Laboratory — Pydantic v2 schemas.

Sprint 8 — T-HC-LAB-001
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Test Panel
# ---------------------------------------------------------------------------

class TestPanelCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    category: str = Field(
        "other",
        pattern="^(hematology|chemistry|immunology|microbiology|urinalysis|other)$",
    )
    turnaround_hours: int = Field(24, ge=1)
    unit_price: float = Field(..., ge=0)
    currency: str = Field("IDR", max_length=3)
    sample_type: str = Field(
        "blood",
        pattern="^(blood|urine|stool|swab|tissue|other)$",
    )
    requires_fasting: bool = False
    is_active: bool = True


class TestPanelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(
        None,
        pattern="^(hematology|chemistry|immunology|microbiology|urinalysis|other)$",
    )
    turnaround_hours: Optional[int] = Field(None, ge=1)
    unit_price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    sample_type: Optional[str] = Field(
        None,
        pattern="^(blood|urine|stool|swab|tissue|other)$",
    )
    requires_fasting: Optional[bool] = None
    is_active: Optional[bool] = None


class TestPanelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    code: str
    name: str
    category: str
    turnaround_hours: int
    unit_price: float
    currency: str
    sample_type: str
    requires_fasting: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TestPanelListResponse(BaseModel):
    items: List[TestPanelResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Lab Order
# ---------------------------------------------------------------------------

class LabOrderCreate(BaseModel):
    encounter_id: str
    test_panel_ids: List[str] = Field(..., min_length=1)
    priority: str = Field(
        "routine",
        pattern="^(routine|urgent|stat)$",
    )
    clinical_notes: Optional[str] = None


class OrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    test_panel_id: str
    test_panel_name: Optional[str] = None
    status: str


class LabOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    encounter_id: str
    patient_id: str
    provider_id: str
    status: str
    priority: str
    clinical_notes: Optional[str] = None
    lines: List[OrderLineResponse] = []
    specimen: Optional["SpecimenResponse"] = None
    created_at: datetime
    updated_at: datetime


class LabOrderListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    encounter_id: str
    patient_id: str
    patient_display: Optional[str] = None  # masked
    provider_id: str
    status: str
    priority: str
    panel_count: int = 0
    created_at: datetime
    updated_at: datetime


class LabOrderListResponse(BaseModel):
    items: List[LabOrderListItem]
    total: int
    page: int
    page_size: int


class LabOrderStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        pattern="^(specimen_collected|processing|resulted|cancelled)$",
    )


# ---------------------------------------------------------------------------
# Specimen
# ---------------------------------------------------------------------------

class SpecimenCreate(BaseModel):
    sample_type: str = Field(
        ...,
        pattern="^(blood|urine|stool|swab|tissue|other)$",
    )
    collection_datetime: Optional[datetime] = None
    barcode: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class SpecimenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    sample_type: str
    collection_datetime: Optional[datetime] = None
    collected_by: Optional[str] = None
    barcode: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

class ResultEntryItem(BaseModel):
    order_line_id: str
    result_value: Optional[str] = Field(None, max_length=255)
    result_unit: Optional[str] = Field(None, max_length=50)
    reference_range: Optional[str] = Field(None, max_length=100)
    is_abnormal: bool = False
    is_critical: bool = False
    notes: Optional[str] = None


class ResultsBatchCreate(BaseModel):
    results: List[ResultEntryItem] = Field(..., min_length=1)


class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    order_line_id: str
    test_panel_id: str
    test_panel_name: Optional[str] = None
    result_value: Optional[str] = None
    result_unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool
    is_critical: bool
    resulted_by: Optional[str] = None
    resulted_at: Optional[datetime] = None
    shared_with_patient: bool
    released_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Patient-facing
# ---------------------------------------------------------------------------

class PatientLabOrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: str
    encounter_date: Optional[datetime] = None
    clinic_name: Optional[str] = None
    test_panel_names: List[str] = []
    order_status: str
    resulted_at: Optional[datetime] = None


class PatientLabResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    test_panel_name: str
    result_value: Optional[str] = None
    result_unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool
    is_critical: bool


class PatientLabResultsResponse(BaseModel):
    order_id: str
    results: List[PatientLabResultItem]


__all__ = [
    "TestPanelCreate",
    "TestPanelUpdate",
    "TestPanelResponse",
    "TestPanelListResponse",
    "LabOrderCreate",
    "LabOrderResponse",
    "LabOrderListItem",
    "LabOrderListResponse",
    "LabOrderStatusUpdate",
    "OrderLineResponse",
    "SpecimenCreate",
    "SpecimenResponse",
    "ResultEntryItem",
    "ResultsBatchCreate",
    "ResultResponse",
    "PatientLabOrderSummary",
    "PatientLabResultItem",
    "PatientLabResultsResponse",
]
