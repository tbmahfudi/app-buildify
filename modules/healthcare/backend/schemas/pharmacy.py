"""
Healthcare Pharmacy — Pydantic v2 schemas.

Sprint 7 — T-HC-PHR-001
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Medication
# ---------------------------------------------------------------------------

class MedicationCreate(BaseModel):
    name: str = Field(..., max_length=255)
    generic_name: Optional[str] = Field(None, max_length=255)
    brand_name: Optional[str] = Field(None, max_length=255)
    category: str = Field(
        "other",
        pattern="^(antibiotic|analgesic|antihypertensive|vitamin|other)$",
    )
    form: str = Field(
        "tablet",
        pattern="^(tablet|capsule|syrup|injection|topical|other)$",
    )
    strength: Optional[str] = Field(None, max_length=50)
    unit: str = Field("tablet", max_length=20)
    stock_quantity: int = Field(0, ge=0)
    minimum_stock: int = Field(10, ge=0)
    unit_price: float = Field(..., ge=0)
    currency: str = Field("IDR", max_length=3)
    is_active: bool = True


class MedicationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    generic_name: Optional[str] = Field(None, max_length=255)
    brand_name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(
        None,
        pattern="^(antibiotic|analgesic|antihypertensive|vitamin|other)$",
    )
    form: Optional[str] = Field(
        None,
        pattern="^(tablet|capsule|syrup|injection|topical|other)$",
    )
    strength: Optional[str] = Field(None, max_length=50)
    unit: Optional[str] = Field(None, max_length=20)
    minimum_stock: Optional[int] = Field(None, ge=0)
    unit_price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    is_active: Optional[bool] = None


class MedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    category: str
    form: str
    strength: Optional[str] = None
    unit: str
    stock_quantity: int
    minimum_stock: int
    unit_price: float
    currency: str
    is_active: bool
    is_low_stock: bool = False
    created_at: datetime
    updated_at: datetime


class MedicationListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[MedicationResponse]
    total: int
    page: int
    page_size: int


class StockAdjustRequest(BaseModel):
    adjustment: int = Field(
        ...,
        description="Positive = restock, negative = write-off",
    )
    reason: str = Field(..., min_length=1, max_length=500)


# ---------------------------------------------------------------------------
# Drug Interactions
# ---------------------------------------------------------------------------

class DrugInteractionCheckRequest(BaseModel):
    medication_ids: List[str] = Field(
        ...,
        min_length=2,
        description="List of medication UUIDs to check for interactions",
    )


class DrugInteractionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    medication_a_id: str
    medication_a_name: str
    medication_b_id: str
    medication_b_name: str
    severity: str  # mild/moderate/severe
    description: Optional[str] = None
    source: Optional[str] = None


class DrugInteractionCheckResponse(BaseModel):
    interactions: List[DrugInteractionItem]
    has_severe: bool
    medication_ids_checked: List[str]


class DrugInteractionCreate(BaseModel):
    medication_a_id: str
    medication_b_id: str
    severity: str = Field(..., pattern="^(mild|moderate|severe)$")
    description: Optional[str] = None
    source: Optional[str] = Field(None, max_length=100)


class DrugInteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    medication_a_id: str
    medication_b_id: str
    severity: str
    description: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Prescription
# ---------------------------------------------------------------------------

class PrescriptionLineCreate(BaseModel):
    medication_id: str
    quantity: int = Field(..., gt=0)
    dosage_instructions: Optional[str] = Field(None, max_length=255)
    days_supply: Optional[int] = Field(None, gt=0)


class PrescriptionLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    medication_id: str
    medication_name: Optional[str] = None
    medication_form: Optional[str] = None
    medication_strength: Optional[str] = None
    quantity: int
    dosage_instructions: Optional[str] = None
    days_supply: Optional[int] = None
    dispensed_quantity: int
    status: str


class PrescriptionCreate(BaseModel):
    encounter_id: str
    lines: List[PrescriptionLineCreate] = Field(..., min_length=1)


class PrescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    encounter_id: str
    patient_id: str
    provider_id: str
    status: str
    notes: Optional[str] = None
    lines: List[PrescriptionLineResponse] = []
    interaction_warnings: List[DrugInteractionItem] = []
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Dispense
# ---------------------------------------------------------------------------

class DispenseLineRequest(BaseModel):
    prescription_line_id: str
    quantity_dispensed: int = Field(..., gt=0)
    batch_number: Optional[str] = Field(None, max_length=50)
    expiry_date: Optional[date] = None


class DispenseRequest(BaseModel):
    lines: List[DispenseLineRequest] = Field(..., min_length=1)


class DispenseResponse(BaseModel):
    prescription_id: str
    prescription_status: str
    lines_dispensed: int
    records_created: List[str]  # list of dispensing record IDs


# ---------------------------------------------------------------------------
# Patient-facing
# ---------------------------------------------------------------------------

class PatientPrescriptionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prescription_id: str
    encounter_date: Optional[datetime] = None
    clinic_name: Optional[str] = None
    status: str
    medication_names: List[str] = []


class PatientPrescriptionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prescription_id: str
    encounter_date: Optional[datetime] = None
    clinic_name: Optional[str] = None
    status: str
    lines: List[PrescriptionLineResponse] = []
