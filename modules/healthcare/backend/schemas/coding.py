"""Pydantic schemas for EMR Clinical Coding & Notes (epic-10 / ADR-HC-007)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

_NOTE_TYPE = "^(progress|nursing|observation|follow_up)$"


# --- catalogs --------------------------------------------------------------

class ICD10CodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    description: str
    description_id: Optional[str] = None
    chapter: Optional[str] = None
    category: Optional[str] = None
    is_billable: bool = True


class ICD9CMCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    description: str
    description_id: Optional[str] = None
    category: Optional[str] = None


# --- diagnoses -------------------------------------------------------------

class DiagnosisCreate(BaseModel):
    icd10_code: str = Field(..., max_length=10)
    is_primary: bool = False
    sequence: int = Field(1, ge=1)


class DiagnosisUpdate(BaseModel):
    is_primary: Optional[bool] = None
    sequence: Optional[int] = Field(None, ge=1)


class DiagnosisReorder(BaseModel):
    order: List[str]  # diagnosis ids in the desired sequence


class DiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    encounter_id: str
    icd10_code: str
    description: Optional[str] = None
    is_primary: bool
    sequence: int
    created_at: datetime


# --- procedures ------------------------------------------------------------

class ProcedureCreate(BaseModel):
    icd9cm_code: str = Field(..., max_length=10)
    note: Optional[str] = Field(None, max_length=255)


class ProcedureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    encounter_id: str
    icd9cm_code: str
    description: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime


# --- clinical notes --------------------------------------------------------

class NoteCreate(BaseModel):
    note_type: str = Field(..., pattern=_NOTE_TYPE)
    body: str = Field(..., min_length=1)


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    encounter_id: str
    note_type: str
    body: str
    author_id: str
    created_at: datetime


class NoteSummary(BaseModel):
    id: str
    note_type: str
    author_id: str
    created_at: datetime


class EncounterListItem(BaseModel):
    id: str
    patient_name: str
    provider_name: Optional[str] = None
    status: str
    started_at: datetime


class CodingSummaryResponse(BaseModel):
    encounter_id: str
    primary_diagnosis: Optional[str] = None
    diagnoses: List[DiagnosisResponse]
    procedures: List[ProcedureResponse]
    notes: List[NoteSummary]
