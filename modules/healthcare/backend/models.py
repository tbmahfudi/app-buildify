"""Healthcare base module — SQLAlchemy ORM models (Wave 1 tables)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

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

    id = Column(String(36), primary_key=True, default=generate_uuid)
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
    # Platform-org linkage (ADR-HC-005) — read-only FKs to the platform org
    # hierarchy (companies/branches/departments, native uuid PKs). A clinic/branch
    # IS a platform branch; nullable until linked. FK constraints live in the DB;
    # not declared here since the platform tables are outside the healthcare Base.
    platform_company_id = Column(UUID(as_uuid=False), nullable=True)
    platform_branch_id = Column(UUID(as_uuid=False), nullable=True)
    platform_department_id = Column(UUID(as_uuid=False), nullable=True)
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

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=True)
    # Company anchor (ADR-HC-010): set on clinic_owner sentinel rows (branch_id NULL) so an
    # owner's "all branches" bypass is fenced to their Company, not the whole SaaS. Nullable
    # on non-owner rows (the Branch already fences to a Company). uuid to FK platform
    # companies.id (shared-DB), mirroring HCBranch.platform_company_id (migration Phase 4).
    company_id = Column(UUID(as_uuid=False), nullable=True, index=True)
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
# hc_departments  (ADR-HC-005)
# ---------------------------------------------------------------------------

class HCDepartment(Base):
    """Clinical department within a branch — drives queue routing, coding scope,
    and reporting. Not PHI."""

    __tablename__ = "hc_departments"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    # id is a str (not generate_uuid's UUID object) — the column is varchar and
    # psycopg2's uuid adapter would otherwise make db.refresh emit `varchar = uuid`.
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    kind = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "branch_id", "code", name="uq_hc_departments_code"),
        CheckConstraint(
            "kind IN ('medical','pharmacy','laboratory','radiology','administration','finance')",
            name="ck_hc_departments_kind",
        ),
    )

    def __repr__(self) -> str:
        return f"<HCDepartment id={self.id} branch={self.branch_id} kind={self.kind}>"


# ---------------------------------------------------------------------------
# hc_provider_departments  (ADR-HC-005)
# ---------------------------------------------------------------------------

class HCProviderDepartment(Base):
    """Provider ↔ department assignment (many-to-many). One primary/home
    department per provider per branch (partial unique index in DB)."""

    __tablename__ = "hc_provider_departments"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    provider_id = Column(String(36), ForeignKey("hc_providers.id"), nullable=False)
    department_id = Column(String(36), ForeignKey("hc_departments.id"), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "branch_id", "provider_id", "department_id",
            name="uq_hc_provider_departments",
        ),
    )

    def __repr__(self) -> str:
        return f"<HCProviderDepartment provider={self.provider_id} dept={self.department_id}>"


# ---------------------------------------------------------------------------
# hcr_visits  (ADR-HC-006) — check-in / registration
# ---------------------------------------------------------------------------

class HCVisit(Base):
    """A patient visit/registration (from an appointment or walk-in). PHI-by-
    association only (patient_id/encounter_id); RLS-protected, no encrypted col."""

    __tablename__ = "hcr_visits"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    patient_id = Column(String(36), ForeignKey("hc_patients.id"), nullable=False)
    # No ORM ForeignKey: hcs_appointments / hcb_insurance_profiles have no ORM
    # model in the healthcare metadata (raw-SQL tables) — the DB FK still exists.
    appointment_id = Column(String(36), nullable=True)
    visit_type = Column(String(20), nullable=False)
    payment_category = Column(String(30), nullable=False)
    insurance_profile_id = Column(String(36), nullable=True)
    referral_source = Column(String(50), nullable=False, default="self")
    department_id = Column(String(36), ForeignKey("hc_departments.id"), nullable=False)
    status = Column(String(20), nullable=False, default="registered")
    checked_in_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    encounter_id = Column(String(36), ForeignKey("hc_encounters.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("visit_type IN ('appointment','walk_in')", name="ck_hcr_visits_visit_type"),
        CheckConstraint(
            "payment_category IN ('self_pay','bpjs','private_insurance','corporate')",
            name="ck_hcr_visits_payment_category",
        ),
        CheckConstraint(
            "status IN ('registered','waiting','in_service','completed','cancelled')",
            name="ck_hcr_visits_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<HCVisit id={self.id} patient={self.patient_id} status={self.status}>"


# ---------------------------------------------------------------------------
# hcr_queue_tickets  (ADR-HC-006) — queue lifecycle
# ---------------------------------------------------------------------------

class HCQueueTicket(Base):
    """A queue ticket for a visit at a department. Not PHI (numbers/status/times).
    Transfer closes the ticket and links a new one via transferred_to_id."""

    __tablename__ = "hcr_queue_tickets"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    visit_id = Column(String(36), ForeignKey("hcr_visits.id"), nullable=False)
    department_id = Column(String(36), ForeignKey("hc_departments.id"), nullable=False)
    ticket_number = Column(String(20), nullable=False)
    station = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="waiting")
    service_day = Column(Date, nullable=False)
    transferred_to_id = Column(String(36), ForeignKey("hcr_queue_tickets.id"), nullable=True)
    called_at = Column(DateTime, nullable=True)
    served_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("branch_id", "department_id", "service_day", "ticket_number",
                         name="uq_hcr_queue_tickets_number"),
        CheckConstraint(
            "status IN ('waiting','called','skipped','recalled','transferred','served')",
            name="ck_hcr_queue_tickets_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<HCQueueTicket id={self.id} num={self.ticket_number} status={self.status}>"


# ---------------------------------------------------------------------------
# Clinical coding catalogs + encounter coding  (ADR-HC-007)
# ---------------------------------------------------------------------------

class HCICD10Code(Base):
    """ICD-10 diagnosis catalog (tenant-scoped, adapter-loaded). Not PHI."""

    __tablename__ = "hc_icd10_codes"
    __tenant_scoped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    # Company isolation key (ADR-HC-010 shared-tenant SaaS): a per-clinic coding
    # catalog. Under the shared SAAS tenant, code uniqueness + enumeration are keyed
    # on the Company, not the tenant (migration Phase 3 catalog re-scope).
    company_id = Column(String(36), nullable=True, index=True)
    code = Column(String(10), nullable=False)
    description = Column(String(500), nullable=False)
    description_id = Column(String(500), nullable=True)
    chapter = Column(String(10), nullable=True)
    category = Column(String(10), nullable=True)
    is_billable = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    edition = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_hc_icd10_codes"),)


class HCICD9CMCode(Base):
    """ICD-9-CM procedure catalog (tenant-scoped, adapter-loaded). Not PHI."""

    __tablename__ = "hc_icd9cm_codes"
    __tenant_scoped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    # Company isolation key (ADR-HC-010) — see HCICD10Code.company_id.
    company_id = Column(String(36), nullable=True, index=True)
    code = Column(String(10), nullable=False)
    description = Column(String(500), nullable=False)
    description_id = Column(String(500), nullable=True)
    category = Column(String(10), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    edition = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_hc_icd9cm_codes"),)


class HCDiagnosis(Base):
    """Encounter diagnosis (ICD-10). Immutable. PHI-by-association (codes only)."""

    __tablename__ = "hc_diagnoses"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    encounter_id = Column(String(36), ForeignKey("hc_encounters.id"), nullable=False)
    icd10_code = Column(String(10), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)
    sequence = Column(SmallInteger, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class HCProcedure(Base):
    """Encounter procedure (ICD-9-CM). `note` is a short qualifier, not PHI."""

    __tablename__ = "hc_procedures"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    encounter_id = Column(String(36), ForeignKey("hc_encounters.id"), nullable=False)
    icd9cm_code = Column(String(10), nullable=False)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class HCClinicalNote(Base):
    """Typed clinical note. `body` is PHI (encrypted at rest)."""

    __tablename__ = "hc_clinical_notes"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    encounter_id = Column(String(36), ForeignKey("hc_encounters.id"), nullable=False)
    note_type = Column(String(20), nullable=False)
    body = Column(EncryptedPHIType, nullable=False)
    author_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "note_type IN ('progress','nursing','observation','follow_up')",
            name="ck_hc_clinical_notes_type",
        ),
    )


# ---------------------------------------------------------------------------
# hc_patients  [PHI]
# ---------------------------------------------------------------------------

class HCPatient(Base):
    """Tenant-wide patient profile — PHI columns encrypted via EncryptedPHIType."""

    __tablename__ = "hc_patients"
    __tenant_scoped__ = True
    # branch_scoped intentionally False — patients belong to tenant, not branch

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)

    # Optional link to a platform User (app `users.id`). When set, a logged-in
    # platform patient-user can mint a patient portal session via
    # POST /api/v1/patients/auth/from-platform (no phone/OTP needed). Phone+OTP
    # patients leave this NULL. Added out-of-band by seed/migration (ALTER) since
    # create_all never alters an existing table.
    user_id = Column(String(36), nullable=True, index=True)

    # Company isolation key (ADR-HC-010 — SaaS shared-tenant model). NOT NULL + FK to
    # platform companies.id + Company RLS key after backfill (migration Phase 4). uuid to
    # match companies.id (shared-DB FK), mirroring HCBranch.platform_company_id.
    company_id = Column(UUID(as_uuid=False), nullable=False, index=True)

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

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("hc_patients.id"), nullable=False, index=True)
    consent_type = Column(String(50), nullable=False)
    consent_version = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    accepted_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    ip = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=False)
    purpose_description = Column(Text, nullable=True)
    # Proxy-consent attribution (ADR-HC-009 v2 / schema-hc-03 M.3). basis='self' +
    # consented_by_user_id NULL for self-consent (unchanged behaviour).
    basis = Column(String(20), nullable=False, default="self")
    consented_by_user_id = Column(String(36), nullable=True)
    # Company re-key (ADR-HC-010; user-confirmed). Nullable during phased migration.
    company_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "consent_type IN ('dpa_acceptance','data_processing','marketing')",
            name="ck_hc_patient_consents_type",
        ),
        CheckConstraint("status IN ('active','revoked')", name="ck_hc_patient_consents_status"),
        CheckConstraint(
            "basis IN ('self','parental_guardian','delegated_adult','spousal')",
            name="ck_hc_patient_consents_basis",
        ),
    )


# ---------------------------------------------------------------------------
# hc_patient_relationships — household / proxy authority (ADR-HC-009 v2, schema-hc-03 M.2)
# ---------------------------------------------------------------------------

class HCPatientRelationship(Base):
    """
    Authority for "who may act for this patient." One account holder (platform
    users.id) links to many patients: exactly one relationship='self' (their own
    patient) plus zero-or-more managed dependents. RLS-scoped like hc_patients.
    Holds an FK to a platform user but no credentials/PHI.
    """

    __tablename__ = "hc_patient_relationships"
    __tenant_scoped__ = True

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), nullable=True)  # patient's clinic — routes Q3 approval + audit
    account_user_id = Column(String(36), nullable=False, index=True)  # platform users.id (app-enforced FK)
    patient_id = Column(String(36), ForeignKey("hc_patients.id"), nullable=False, index=True)
    relationship = Column(String(20), nullable=False)  # self|spouse|child|parent|other
    role = Column(String(10), nullable=False)          # owner|proxy
    status = Column(String(10), nullable=False, default="active")  # active|pending|revoked
    basis = Column(String(20), nullable=False)         # self|parental_guardian|delegated_adult|spousal
    granted_by = Column(String(36), nullable=False)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    approved_by_staff_id = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "relationship IN ('self','spouse','child','parent','other')",
            name="ck_hcpr_relationship",
        ),
        CheckConstraint("role IN ('owner','proxy')", name="ck_hcpr_role"),
        CheckConstraint("status IN ('active','pending','revoked')", name="ck_hcpr_status"),
        CheckConstraint(
            "basis IN ('self','parental_guardian','delegated_adult','spousal')",
            name="ck_hcpr_basis",
        ),
        CheckConstraint(
            "relationship <> 'self' OR (role = 'owner' AND basis = 'self')",
            name="ck_hcpr_self_coherent",
        ),
        UniqueConstraint("account_user_id", "patient_id", name="uq_hcpr_account_patient"),
    )

    def __repr__(self) -> str:
        return (
            f"<HCPatientRelationship acct={self.account_user_id} patient={self.patient_id} "
            f"rel={self.relationship} role={self.role} status={self.status}>"
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

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    # nullable (epic-11): a provider may be a clinical record without a login account
    user_id = Column(String(36), nullable=True)
    provider_type = Column(String(30), nullable=False)
    specialty = Column(String(100), nullable=True)
    license_number = Column(String(50), nullable=True)
    display_name = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    # HR / doctor-profile / license (epic-11)
    str_number = Column(String(50), nullable=True)
    sip_number = Column(String(50), nullable=True)
    str_expiry = Column(Date, nullable=True)
    sip_expiry = Column(Date, nullable=True)
    sub_specialty = Column(String(100), nullable=True)
    consultation_fee = Column(BigInteger, nullable=True)   # branch currency minor units
    room_id = Column(String(36), ForeignKey("hc_rooms.id"), nullable=True)
    employment_status = Column(String(20), nullable=False, default="active")
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
# hc_rooms  (epic-11)
# ---------------------------------------------------------------------------

class HCRoom(Base):
    """Consultation / procedure rooms per branch. Not PHI."""

    __tablename__ = "hc_rooms"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    room_type = Column(String(30), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "branch_id", "code", name="uq_hc_rooms_code"),
    )

    def __repr__(self) -> str:
        return f"<HCRoom id={self.id} code={self.code}>"


# ---------------------------------------------------------------------------
# hc_encounters  [PHI]
# ---------------------------------------------------------------------------

class HCEncounter(Base):
    """Clinical encounters per branch — PHI SOAP fields encrypted."""

    __tablename__ = "hc_encounters"
    __tenant_scoped__ = True
    __branch_scoped__ = True

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    patient_id = Column(String(36), ForeignKey("hc_patients.id"), nullable=False)
    provider_id = Column(String(36), ForeignKey("hc_providers.id"), nullable=False)
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
    amendment_of_id = Column(String(36), ForeignKey("hc_encounters.id"), nullable=True)
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

    id = Column(String(36), primary_key=True, default=generate_uuid)
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

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("hc_branches.id"), nullable=False)
    patient_id = Column(String(36), ForeignKey("hc_patients.id"), nullable=False)
    encounter_id = Column(String(36), ForeignKey("hc_encounters.id"), nullable=False)
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

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    # Company isolation key (ADR-HC-010) — i18n overrides are per-clinic; keyed on
    # Company under the shared SAAS tenant (migration Phase 3 catalog re-scope).
    company_id = Column(String(36), nullable=True, index=True)
    locale = Column(String(10), nullable=False)
    translation_key = Column(String(255), nullable=False)
    translation_value = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("company_id", "locale", "translation_key", name="uq_hc_i18n_overrides"),
        CheckConstraint("locale IN ('id-ID','en-US')", name="ck_hc_i18n_overrides_locale"),
    )

    def __repr__(self) -> str:
        return f"<HCI18nOverride id={self.id} locale={self.locale} key={self.translation_key!r}>"
