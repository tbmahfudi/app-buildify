"""Pydantic v2 schemas for patient auth (T-HC-020, T-HC-021)."""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


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


class PatientTokenResponse(BaseModel):
    """Patient portal session response. Minted by the platform-login → from-platform
    bridge and by /auth/refresh (S6b removed the phone+OTP /auth/token path)."""

    model_config = ConfigDict(from_attributes=True)
    access_token: str
    patient_id: str
    message: str
    # Vestigial claim signal (ADR-HC-009 D7). The OTP /auth/token response used to set this
    # so the portal could route a backfilled patient to claim-account; both are gone with
    # S6b. Kept (defaults False) so the response shape is unchanged for existing callers.
    must_set_password: bool = False


class StaffLinkRequest(BaseModel):
    """Staff-mediated recovery: put a real email on a backfilled account (ADR-HC-009 V-D10).

    Recovery exists because a backfilled patient who never claimed has an unusable password
    AND a synthetic, non-deliverable ``@patients.invalid`` address — so no self-service route
    back in. Staff verify identity the way clinics always have (at the desk, against ID);
    this endpoint only records the outcome.

    It deliberately does NOT set a password or create an account. Once the real email is on
    the account, the platform's ordinary password-reset flow takes over and clears
    ``must_set_password`` (``app/routers/auth.py``) — so recovery needs no OTP and no new
    credential path.
    """

    model_config = ConfigDict(from_attributes=True)
    patient_id: str
    email: str
    # confirm: email the person a link; the address is only written when they click it, which
    #          proves they control the mailbox.
    # force:   write it now and notify. For when the person cannot receive the confirmation
    #          (wrong address on file, no access) — which is the case recovery exists for.
    mode: Literal["confirm", "force"] = "confirm"
    # Required for BOTH modes, not just force. This grants access to someone's medical
    # records on staff say-so; the reason is what makes the audit trail answer "why".
    reason: str = Field(min_length=5, max_length=500)


class StaffLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    mode: str
    pending_confirmation: bool
    message: str


class StaffLinkConfirmRequest(BaseModel):
    """Consume the emailed staff-link token (public — the token IS the proof)."""

    model_config = ConfigDict(from_attributes=True)
    token: str


class StaffLinkConfirmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    confirmed: bool
    message: str
