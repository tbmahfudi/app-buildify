"""
Healthcare — Clinic signup and DPA status API.

T-HC-018  POST /api/v1/clinics/register  (PUBLIC)
T-HC-019  GET  /api/v1/modules/healthcare/dpa/status  (Clinic Owner)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from app.core.dependencies import get_db as _platform_get_db
from modules.healthcare.models import HCBranch, HCBranchStaff, HCPatientConsent
from modules.healthcare.schemas.clinic_signup import (
    ClinicRegisterRequest,
    ClinicRegisterResponse,
    CompanyOnboardRequest,
    CompanyOnboardResponse,
    DPAStatusResponse,
)
from modules.healthcare.sdk.captcha import require_captcha
from modules.healthcare.sdk.dpa_gate import require_dpa
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.hc_tenant import resolve_shared_tenant_id
from modules.healthcare.sdk.locale import t
from modules.healthcare.sdk.phi_audit import write_event_audit

router = APIRouter(tags=["healthcare-clinic-signup"])


def _get_public_db():
    """Unauthenticated plain DB session for public (no-auth) signup endpoints."""
    yield from _platform_get_db()


@router.post(
    "/api/v1/clinics/register",
    response_model=ClinicRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new clinic (public)",
)
async def clinic_register(
    payload: ClinicRegisterRequest,
    request: Request,
    _captcha=Depends(require_captcha),
    db: Session = Depends(tenant_scoped_session),
) -> ClinicRegisterResponse:
    """
    Public endpoint — creates a new tenant + branch + clinic_owner user,
    records the DPA consent, and emits an audit event.

    Steps:
      1. Validate hCaptcha (dependency)
      2. Reject if dpa_accepted != True
      3. Create tenant row (via platform bridge / raw SQL stub)
      4. Create branch row
      5. Create platform user for owner
      6. Create hc_branch_staff row (role=clinic_owner, branch_id=NULL)
      7. Record DPA in hc_patient_consents (consent_type='clinic_dpa')
      8. Emit audit
      9. Return ClinicRegisterResponse
    """
    locale = payload.locale

    # Step 2 — DPA gate
    if not payload.dpa_accepted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=t(locale, "error.dpa_required"),
        )

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    # Step 3 — Create tenant (platform responsibility; we generate tenant_id here
    #           and pass it to the platform bridge in a full implementation).
    #           For module-level isolation we use a stub that inserts into
    #           the platform tenants table via raw SQL.
    tenant_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO tenants (id, name, status, created_at, updated_at) "
            "VALUES (:id, :name, 'active', NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {"id": tenant_id, "name": payload.clinic_name},
    )

    # Step 4 — Create branch
    branch_id = str(uuid.uuid4())
    slug = payload.clinic_name.lower().replace(" ", "-")[:100]
    branch = HCBranch(
        id=branch_id,
        tenant_id=tenant_id,
        branch_name=payload.clinic_name,
        slug=slug,
        address_street="",
        address_city=payload.city,
        address_province="",
        contact_phone=payload.owner_phone,
        default_locale=locale,
        status="active",
    )
    db.add(branch)
    db.flush()

    # Step 5 — Create platform user for owner
    owner_user_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, name, status, created_at, updated_at) "
            "VALUES (:id, :tid, :email, :name, 'active', NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {
            "id": owner_user_id,
            "tid": tenant_id,
            "email": payload.owner_email,
            "name": payload.owner_name,
        },
    )

    # Step 6 — Create hc_branch_staff (clinic_owner, branch_id=NULL sentinel)
    staff = HCBranchStaff(
        tenant_id=tenant_id,
        branch_id=None,  # NULL = clinic owner sentinel
        user_id=owner_user_id,
        role=HCRole.clinic_owner,
        status="active",
        is_active=True,
    )
    db.add(staff)
    db.flush()

    # Step 7 — Record DPA consent
    #   For clinic DPA we store entity_id in patient_id column with a sentinel UUID
    #   that matches the tenant_id so require_dpa() can locate it.
    dpa_record = HCPatientConsent(
        tenant_id=tenant_id,
        patient_id=tenant_id,  # DPA sentinel: patient_id == tenant_id
        consent_type="clinic_dpa",
        consent_version=payload.dpa_version,
        status="active",
        accepted_at=datetime.utcnow(),
        ip=ip,
        user_agent=ua,
        purpose_description="Clinic Data Processing Agreement acceptance",
    )
    db.add(dpa_record)
    db.flush()

    # Step 8 — Emit audit
    write_event_audit(
        db=db,
        actor_id=owner_user_id,
        actor_type="staff",
        event_type="clinic.registered",
        entity_type="tenant",
        entity_id=tenant_id,
        tenant_id=tenant_id,
        ip=ip,
        ua=ua,
    )

    db.commit()

    return ClinicRegisterResponse(
        tenant_id=tenant_id,
        branch_id=branch_id,
        message=t(locale, "clinic.registered"),
    )


# ---------------------------------------------------------------------------
# Feature 20.1 — Owner Signup & Company Creation (shared-tenant SaaS model)
#   Replaces the tenant-per-clinic clinic_register above. No new platform tenant:
#   the Company is created under the shared SAAS tenant; the owner is Company-anchored.
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/modules/healthcare/onboarding/company",
    response_model=CompanyOnboardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard a clinic business (Company) on the shared SaaS tenant (public)",
)
async def onboard_company(
    payload: CompanyOnboardRequest,
    request: Request,
    _captcha=Depends(require_captcha),
    db: Session = Depends(_get_public_db),
) -> CompanyOnboardResponse:
    """Create a clinic business (Company) under the shared SaaS tenant.

    Provisions, atomically (NO new platform tenant is created):
      1. a ``companies`` row (``code`` = slug, ``public_listing`` default false);
      2. the owner platform ``User`` (bcrypt password, ``default_company_id`` = Company);
      3. the ``clinic_owner`` platform Role (idempotent, shared-tenant scoped) + a
         Company-scoped Group + group_role + user_group — so the owner's "all branches"
         bypass resolves via ``User.get_roles()`` while the ``app.company_id`` GUC still
         fences reads to this Company (ADR-HC-010);
      4. an ``hc_branch_staff`` owner sentinel (``branch_id`` NULL, ``company_id`` set) —
         Company-anchored so the owner is never a SaaS-wide super-owner;
      5. the clinic DPA consent (Company-scoped) and a ``company.created`` audit event.

    Idempotent on the slug within the shared tenant → 409; owner email is globally
    unique → 409 on collision. All roles are enumerated within the Company.
    """
    from app.core.auth import hash_password

    locale = payload.locale

    # DPA gate (mirror clinic_register)
    if not payload.dpa_accepted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=t(locale, "error.dpa_required"),
        )

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    # Shared SaaS tenant — the single home for all clinics (ADR-HC-010 / migration Phase 0).
    saas_tenant_id = resolve_shared_tenant_id(db)

    # Idempotency: companies unique on (tenant_id, code) → duplicate slug is a 409.
    if db.execute(
        text("SELECT 1 FROM companies WHERE tenant_id = :tid AND code = :code"),
        {"tid": saas_tenant_id, "code": payload.slug},
    ).fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="clinic slug already taken",
        )

    # users.email is globally unique.
    if db.execute(
        text("SELECT 1 FROM users WHERE lower(email) = lower(:email)"),
        {"email": payload.owner_email},
    ).fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already registered",
        )

    company_id = str(uuid.uuid4())
    owner_user_id = str(uuid.uuid4())
    group_id = str(uuid.uuid4())

    # 1 — Company under the shared SAAS tenant (public_listing opt-in, default off).
    db.execute(
        text(
            "INSERT INTO companies "
            "(id, tenant_id, code, name, email, phone, city, is_active, public_listing, created_at, updated_at) "
            "VALUES (:id, :tid, :code, :name, :email, :phone, :city, true, :pub, NOW(), NOW())"
        ),
        {
            "id": company_id, "tid": saas_tenant_id, "code": payload.slug,
            "name": payload.company_name, "email": payload.owner_email,
            "phone": payload.owner_phone, "city": payload.city,
            "pub": payload.public_listing,
        },
    )

    # 2 — Owner platform user (staff), bound to the shared tenant + Company.
    db.execute(
        text(
            "INSERT INTO users "
            "(id, tenant_id, email, full_name, hashed_password, is_active, is_superuser, "
            " is_verified, default_company_id, roles, created_at, updated_at) "
            "VALUES (:id, :tid, :email, :name, :pw, true, false, true, :cid, 'clinic_owner', NOW(), NOW())"
        ),
        {
            "id": owner_user_id, "tid": saas_tenant_id, "email": payload.owner_email,
            "name": payload.owner_name, "pw": hash_password(payload.owner_password),
            "cid": company_id,
        },
    )

    # 3 — clinic_owner Role (idempotent, shared-tenant scoped) + Company-scoped Group chain.
    db.execute(
        text(
            "INSERT INTO roles (id, tenant_id, code, name, role_type, is_active, is_system, created_at) "
            "VALUES (:id, :tid, 'clinic_owner', 'Clinic Owner', 'system', true, true, NOW()) "
            "ON CONFLICT (tenant_id, code) DO NOTHING"
        ),
        {"id": str(uuid.uuid4()), "tid": saas_tenant_id},
    )
    role_id = str(
        db.execute(
            text("SELECT id FROM roles WHERE tenant_id = :tid AND code = 'clinic_owner'"),
            {"tid": saas_tenant_id},
        ).fetchone()[0]
    )
    db.execute(
        text(
            "INSERT INTO groups (id, tenant_id, company_id, code, name, group_type, is_active, created_at) "
            "VALUES (:id, :tid, :cid, 'clinic_owners', :name, 'team', true, NOW())"
        ),
        {"id": group_id, "tid": saas_tenant_id, "cid": company_id,
         "name": f"{payload.company_name} Owners"[:255]},
    )
    db.execute(
        text("INSERT INTO group_roles (id, group_id, role_id, created_at) VALUES (:id, :gid, :rid, NOW())"),
        {"id": str(uuid.uuid4()), "gid": group_id, "rid": role_id},
    )
    db.execute(
        text("INSERT INTO user_groups (id, user_id, group_id, created_at) VALUES (:id, :uid, :gid, NOW())"),
        {"id": str(uuid.uuid4()), "uid": owner_user_id, "gid": group_id},
    )

    # 4 — hc_branch_staff owner sentinel (Company-anchored; branch_id NULL).
    db.execute(
        text(
            "INSERT INTO hc_branch_staff "
            "(id, tenant_id, branch_id, user_id, role, status, is_active, company_id, created_at, updated_at) "
            "VALUES (:id, :tid, NULL, :uid, 'clinic_owner', 'active', true, :cid, NOW(), NOW())"
        ),
        {"id": str(uuid.uuid4()), "tid": saas_tenant_id, "uid": owner_user_id, "cid": company_id},
    )

    # 5 — Emit company.created audit. The clinic DPA acceptance is gated above and its
    #     version recorded here (non-PHI). hc_patient_consents is *patient*-scoped
    #     (patient_id FKs hc_patients), so the clinic-level DPA is not written there.
    write_event_audit(
        db=db,
        actor_id=owner_user_id,
        actor_type="staff",
        event_type="company.created",
        entity_type="company",
        entity_id=company_id,
        tenant_id=saas_tenant_id,
        ip=ip,
        ua=ua,
        metadata={
            "slug": payload.slug,
            "public_listing": payload.public_listing,
            "dpa_accepted": payload.dpa_accepted,
            "dpa_version": payload.dpa_version,
        },
    )

    db.commit()

    return CompanyOnboardResponse(
        company_id=company_id,
        slug=payload.slug,
        owner_user_id=owner_user_id,
        message=t(locale, "clinic.registered"),
    )


# ---------------------------------------------------------------------------
# T-HC-019 — DPA status endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/modules/healthcare/dpa/status",
    response_model=DPAStatusResponse,
    summary="DPA acceptance status for this tenant (Clinic Owner)",
)
async def dpa_status(
    _role=Depends(has_hc_permission([HCRole.clinic_owner])),
    current_user=Depends(get_current_user),
    db: Session = Depends(tenant_scoped_session),
) -> DPAStatusResponse:
    """Return DPA acceptance status for the authenticated clinic owner's tenant."""
    tenant_id = str(current_user.tenant_id)

    row = db.execute(
        text(
            "SELECT consent_version, accepted_at "
            "FROM hc_patient_consents "
            "WHERE tenant_id = :tid "
            "AND consent_type = 'clinic_dpa' "
            "AND status = 'active' "
            "ORDER BY accepted_at DESC "
            "LIMIT 1"
        ),
        {"tid": tenant_id},
    ).fetchone()

    if row is None:
        return DPAStatusResponse(dpa_accepted=False, dpa_version=None, accepted_at=None)

    return DPAStatusResponse(
        dpa_accepted=True,
        dpa_version=row[0],
        accepted_at=row[1].isoformat() if row[1] else None,
    )
