"""Healthcare base module — SQLAlchemy ORM models (Wave 1 tables)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

# SDK-only imports — never from backend.app directly
from modules.sdk.db import Base, GUID, generate_uuid
from modules.healthcare.sdk.phi_crypto import EncryptedPHIType


# ---------------------------------------------------------------------------
# hc_branches
# ---------------------------------------------------------------------------

class HCBranch(Base):
    """Branch registry per tenant."""

    __tablename__ = "hc_branches"
    __tenant_scoped__ = True  # Required by TenantScopeListener

    id = Column(GUID(), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    address_street = Column(String(500), nullable=False)
    address_city = Column(String(100), nullable=False)
    address_province = Column(String(100), nullable=False)
    address_postal_code = Column(String(10), nullable=True)
    timezone = Column(String(50), nullable=False, default="Asia/Jakarta")
    contact_phone = Column(String(30), nullable=False)
    operating_hours = Column(JSONB, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="active")
    online_booking = Column(Boolean, nullable=False, default=True)
    default_locale = Column(String(10), nullable=False, default="id-ID")
    appointment_types = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_hc_branches_tenant_slug"),
        CheckConstraint("status IN ('active','inactive','suspended')", name="ck_hc_branches_status"),
        CheckConstraint("default_locale IN ('id-ID','en-US')", name="ck_hc_branches_locale"),
    )

    def __repr__(self) -> str:
        return f"<HCBranch id={self.id} tenant={self.tenant_id} name={self.branch_name!r}>"


# ---------------------------------------------------------------------------
# hc_branch_staff
# ---------------------------------------------------------------------------

class HCBranchStaff(Base):
    """Staff ↔ branch assignments with role."""

    __tablename__ = "hc_branch_staff"
    __tenant_scoped__ = True
    __branch_scoped__ = True  # branch_id NOT NULL for non-owner rows

    id = Column(GUID(), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=True)
    user_id = Column(String(36), nullable=False)
    role = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    invitation_token = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    invited_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "branch_id", "user_id", "role", name="uq_hc_branch_staff"),
        CheckConstraint(
            "role IN ('clinic_owner','branch_manager','doctor','nurse','pharmacist','lab_tech','billing_staff')",
            name="ck_hc_branch_staff_role",
        ),
        CheckConstraint("status IN ('pending','active','revoked')", name="ck_hc_branch_staff_status"),
    )

    def __repr__(self) -> str:
        return f"<HCBranchStaff id={self.id} user={self.user_id} role={self.role}>"


# ---------------------------------------------------------------------------
# hc_patients  [PHI]
# ---------------------------------------------------------------------------

class HCPatient(Base):
    """Tenant-wide patient profile — PHI columns encrypted via EncryptedPHIType."""

    __tablename__ = "hc_patients"
    __tenant_scoped__ = True
    # branch_scoped intentionally False — patients belong to tenant, not branch

    id = Column(GUID(), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)

    # PHI columns — encrypted at rest by EncryptedPHIType
    full_name = Column(EncryptedPHIType, nullable=False)
    date_of_birth = Column(EncryptedPHIType, nullable=False)
    phone = Column(EncryptedPHIType, nullable=False)
    email = Column(EncryptedPHIType, nullable=True)
    nik = Column(EncryptedPHIType, nullable=True)
    address = Column(EncryptedPHIType, nullable=True)

    gender = Column(String(10), nullable=False)
    locale = Column(String(10), nullable=False, default="id-ID")
    consent_version = Column(String(20), nullable=False)
    consent_accepted_at = Column(DateTime, nullable=False)
    consent_ip = Column(String(45), nullable=False)
    consent_user_agent = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("gender IN ('male','female','other')", name="ck_hc_patients_gender"),
        CheckConstraint("status IN ('active','suspended','deleted')", name="ck_hc_patients_status"),
    )

    def __repr__(self) -> str:
        return f"<HCPatient id={self.id} tenant={self.tenant_id}>"


# ---------------------------------------------------------------------------
# hc_patient_consents
# ---------------------------------------------------------------------------

class HCPatientConsent(Base):
    """DPA / consent records per patient — immutable after creation."""

    __tablename__ = "hc_patient_consents"
    __tenant_scoped__ = True

    id = Column(GUID(), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    patient_id = Column(GUID(), ForeignKey("hc_patients.id"), nullable=False, index=True)
    consent_type = Column(String(50), nullable=False)
    consent_version = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    accepted_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    ip = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=False)
    purpose_description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "consent_type IN ('dpa_acceptance','data_processing','marketing')",
            name="ck_hc_patient_consents_type",
        ),
        CheckConstraint("status IN ('active','revoked')", name="ck_hc_patient_consents_status"),
    )

    def __repr__(self) -> str:
        return f"<HCPatientConsent id={self.id} patient={self.patient_id} type={self.consent_type}>"


# ---------------------------------------------------------------------------
# hc_providers
# ---------------------------------------------------------------------------

class HCProvider(Base):
    """Doctors, nurses, etc. per branch."""

    __tablename__ = "hc_providers"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    id = Column(GUID(), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    user_id = Column(String(36), nullable=False)
    provider_type = Column(String(30), nullable=False)
    specialty = Column(String(100), nullable=True)
    license_number = Column(String(50), nullable=True)
    display_name = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "branch_id", "user_id", name="uq_hc_providers_tenant_branch_user"),
        CheckConstraint(
            "provider_type IN ('doctor','nurse','pharmacist','lab_tech','billing_staff')",
            name="ck_hc_providers_type",
        ),
    )

    def __repr__(self) -> str:
        return f"<HCProvider id={self.id} branch={self.branch_id} type={self.provider_type}>"


# ---------------------------------------------------------------------------
# hc_encounters  [PHI]
# ---------------------------------------------------------------------------

class HCEncounter(Base):
    """Clinical encounters per branch — PHI SOAP fields encrypted."""

    __tablename__ = "hc_encounters"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    id = Column(GUID(), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    patient_id = Column(GUID(), ForeignKey("hc_patients.id"), nullable=False)
    provider_id = Column(GUID(), ForeignKey("hc_providers.id"), nullable=False)
    appointment_id = Column(String(36), nullable=True)  # deferred FK → hcs_appointments.id added in hcs001
    status = Column(String(20), nullable=False, default="open")
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # PHI columns — encrypted at rest
    soap_subjective = Column(EncryptedPHIType, nullable=True)
    soap_objective = Column(EncryptedPHIType, nullable=True)
    soap_assessment = Column(EncryptedPHIType, nullable=True)
    soap_plan = Column(EncryptedPHIType, nullable=True)
    soap_notes = Column(EncryptedPHIType, nullable=True)

    patient_summary = Column(Text, nullable=True)
    summary_released = Column(Boolean, nullable=False, default=False)
    summary_released_at = Column(DateTime, nullable=True)
    amendment_of_id = Column(GUID(), ForeignKey("hc_encounters.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "status IN ('open','in_progress','completed','cancelled')",
            name="ck_hc_encounters_status",
        ),
        Index("idx_hc_encounters_tenant_branch", "tenant_id", "branch_id"),
        Index("idx_hc_encounters_patient_id", "tenant_id", "patient_id"),
    )

    def __repr__(self) -> str:
        return f"<HCEncounter id={self.id} branch={self.branch_id} status={self.status}>"


# ---------------------------------------------------------------------------
# hc_audit_log
# ---------------------------------------------------------------------------

class HCAuditLog(Base):
    """Append-only PHI access audit log — no UPDATE/DELETE permitted."""

    __tablename__ = "hc_audit_log"
    __tenant_scoped__ = True

    id = Column(GUID(), primary_key=True, default=generate_uuid)
    event_type = Column(String(100), nullable=False)
    actor_id = Column(String(36), nullable=False)
    actor_type = Column(String(20), nullable=False)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), nullable=True)  # NULL for tenant-wide events
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=False)
    source_module = Column(String(50), nullable=False)
    phi_accessed = Column(Boolean, nullable=False, default=False)
    ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("actor_type IN ('staff','patient','system')", name="ck_hc_audit_log_actor_type"),
    )

    def __repr__(self) -> str:
        return f"<HCAuditLog id={self.id} event={self.event_type} actor={self.actor_id}>"


# ---------------------------------------------------------------------------
# hc_clinic_reviews
# ---------------------------------------------------------------------------

class HCClinicReview(Base):
    """Patient reviews and ratings per branch."""

    __tablename__ = "hc_clinic_reviews"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    id = Column(GUID(), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    patient_id = Column(GUID(), ForeignKey("hc_patients.id"), nullable=False)
    encounter_id = Column(GUID(), ForeignKey("hc_encounters.id"), nullable=False)
    rating = Column(SmallInteger, nullable=False)
    review_text = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending_moderation")
    moderated_at = Column(DateTime, nullable=True)
    moderated_by = Column(String(36), nullable=True)
    staff_response = Column(Text, nullable=True)
    staff_response_at = Column(DateTime, nullable=True)
    staff_response_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("encounter_id", name="uq_hc_clinic_reviews_encounter"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_hc_clinic_reviews_rating"),
        CheckConstraint(
            "status IN ('pending_moderation','approved','removed')",
            name="ck_hc_clinic_reviews_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<HCClinicReview id={self.id} rating={self.rating}>"


# ---------------------------------------------------------------------------
# hc_i18n_overrides
# ---------------------------------------------------------------------------

class HCI18nOverride(Base):
    """Per-tenant translation key overrides."""

    __tablename__ = "hc_i18n_overrides"
    __tenant_scoped__ = True

    id = Column(GUID(), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    locale = Column(String(10), nullable=False)
    translation_key = Column(String(255), nullable=False)
    translation_value = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "locale", "translation_key", name="uq_hc_i18n_overrides"),
        CheckConstraint("locale IN ('id-ID','en-US')", name="ck_hc_i18n_overrides_locale"),
    )

    def __repr__(self) -> str:
        return f"<HCI18nOverride id={self.id} locale={self.locale} key={self.translation_key!r}>"
