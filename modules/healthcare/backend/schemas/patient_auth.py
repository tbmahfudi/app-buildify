"""Pydantic v2 schemas for patient auth (T-HC-020, T-HC-021)."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict


class PatientRegisterRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Primary credential (ADR-011): patients register with email + password.
    email: str
    password: str
    username: Optional[str] = None
    phone: str
    full_name: str
    date_of_birth: str
    gender: str
    nik: Optional[str] = None
    consent_accepted: bool
    consent_version: str


class PatientRegisterResponse(BaseModel):
    """Legacy OTP-flow response (access_token). Retained for the OTP path."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    patient_id: str
    message: str


class RegisterAcceptedResponse(BaseModel):
    """Enumeration-safe 202 for the verify-email flow (ADR-011, sec-review-011 R1).

    Identical for a brand-new email and an already-registered one — reveals nothing.
    """

    model_config = ConfigDict(from_attributes=True)

    message: str


class ActivateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    token: str


class ActivateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    activated: bool
    message: str


class OTPSendRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    phone: str


class OTPSendResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message: str
    resend_after: int = 60


class OTPVerifyRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    phone: str
    code: str


class OTPVerifyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    verified: bool


class PatientTokenRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    phone: str
    code: str


class PatientTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token: str
    patient_id: str
    message: str
