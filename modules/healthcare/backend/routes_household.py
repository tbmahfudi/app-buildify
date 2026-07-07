"""
Healthcare — Household & Dependent Patients (Proxy Access).

ADR-HC-009 v2 / epic-18 Feature 18.10. One platform account holder links to many
patients (self + managed dependents) via hc_patient_relationships.

Endpoints:
  Patient (account holder) session:
    GET  /api/v1/patients/me/household            — list authorized patients
    POST /api/v1/patients/auth/switch             — re-mint token scoped to another patient
    POST /api/v1/patients/me/household/link        — request to link an existing patient (Q3: staff-approved)
  Clinic staff (branch-scoped, HCRole clinic_owner|branch_manager):
    GET  /api/v1/patients/branches/{branch_id}/household/link-requests
    POST /api/v1/patients/branches/{branch_id}/household/link-requests/{rel_id}/approve
    POST /api/v1/patients/branches/{branch_id}/household/link-requests/{rel_id}/reject
    POST /api/v1/patients/branches/{branch_id}/household/{patient_id}/detach   — Q4 majority detach
"""
from __future__ import annotations
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import get_current_user
from modules.healthcare.models import HCPatient, HCPatientConsent
from modules.healthcare.sdk.patient_auth import (
    PatientTokenData,
    get_current_patient,
    get_patient_db,
)
from modules.healthcare.sdk.patient_tokens import (
    create_patient_access_token,
    create_patient_refresh_token,
)
from modules.healthcare.sdk.hc_permissions import HCRole, get_caller_hc_role
from modules.healthcare.sdk.phi_audit import write_phi_read_audit, write_event_audit
from modules.healthcare.routes_patient_auth import _resolve_active_patient

router = APIRouter()

_STAFF_APPROVER_ROLES = {HCRole.clinic_owner, HCRole.branch_manager}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SwitchRequest(BaseModel):
    patient_id: str


class LinkRequest(BaseModel):
    patient_id: str
    branch_id: str  # the clinic whose staff will approve (routes Q3)
    relationship: str = Field(default="other")  # spouse|child|parent|other
    basis: str = Field(default="delegated_adult")  # parental_guardian|delegated_adult|spousal


class RegisterDependentRequest(BaseModel):
    full_name: str
    date_of_birth: str            # ISO date string (encrypted at rest)
    phone: str
    gender: str = Field(default="other")  # male|female|other
    nik: Optional[str] = None
    relationship: str             # spouse|child|parent|other
    basis: str                    # parental_guardian|delegated_adult|spousal
    branch_id: Optional[str] = None  # clinic the dependent is registered at
    consent_version: str = Field(default="v1")
    consent_accepted: bool = False


_REL_KINDS = {"spouse", "child", "parent", "other"}
_PROXY_BASES = {"parental_guardian", "delegated_adult", "spousal"}


def _account_holder_id(patient: PatientTokenData, db: Session) -> Optional[str]:
    """Resolve the account holder (platform users.id) from the token, or the active
    patient's owner relationship as a fallback for legacy tokens without `acct`."""
    if patient.account_user_id:
        return patient.account_user_id
    row = db.execute(
        text(
            "SELECT account_user_id FROM hc_patient_relationships "
            "WHERE patient_id = :pid AND role = 'owner' AND status = 'active' LIMIT 1"
        ),
        {"pid": patient.patient_id},
    ).fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# GET /me/household — the authorized patient set (18.10.1 / 18.10.4)
# ---------------------------------------------------------------------------

@router.get("/api/v1/patients/me/clinic", summary="Resolve the active patient's own clinic (slug + name)")
async def get_my_clinic(
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(get_patient_db),
):
    """Return the clinic (Company) slug/name for the active patient so the portal
    can scope clinic-facing views (e.g. booking) to the patient's own clinic.

    ADR-HC-010 D6 / schema-hc-04 §C: under the shared SaaS tenant the clinic slug is
    the Company code (companies.code), not the tenant code — all patients share one
    tenant now, so resolving by tenant would return the SaaS umbrella, not the clinic."""
    company_id = patient.require_company()
    row = db.execute(
        text("SELECT code, name FROM companies WHERE id = :cid"),
        {"cid": company_id},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found for this patient.")
    return {"slug": row[0], "clinic_name": row[1]}


@router.get("/api/v1/patients/me/household", summary="List patients this account may act for")
async def get_household(
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(get_patient_db),
):
    tenant_id = patient.require_tenant()
    acct = _account_holder_id(patient, db)
    if not acct:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No household account resolved.")

    rels = db.execute(
        text(
            "SELECT patient_id, relationship, role FROM hc_patient_relationships "
            "WHERE account_user_id = :uid AND status = 'active' "
            "ORDER BY (relationship = 'self') DESC, granted_at ASC"
        ),
        {"uid": acct},
    ).fetchall()

    ids = [str(r[0]) for r in rels]
    pats = {}
    if ids:
        pats = {
            str(p.id): p
            for p in db.query(HCPatient)
            .filter(HCPatient.id.in_(ids), HCPatient.deleted_at.is_(None))
            .all()
        }

    members = []
    for r in rels:
        pid = str(r[0])
        p = pats.get(pid)
        if p is None:
            continue
        members.append(
            {
                "patient_id": pid,
                "relationship": r[1],
                "role": r[2],
                "full_name": p.full_name,  # decrypted via ORM PHI type
                "is_active": pid == patient.patient_id,
            }
        )

    # PHI read audit — names were returned.
    try:
        write_phi_read_audit(
            db=db, actor_id=acct, actor_type="patient", entity_type="household",
            entity_id=acct, tenant_id=tenant_id,
            ip=request.client.host if request.client else None,
            ua=request.headers.get("user-agent"),
            metadata={"count": len(members)},
        )
        db.commit()
    except Exception:
        db.rollback()

    return {"active_patient_id": patient.patient_id, "account_user_id": acct, "members": members}


# ---------------------------------------------------------------------------
# POST /auth/switch — re-mint token scoped to another household patient (18.10.4)
# ---------------------------------------------------------------------------

@router.post("/api/v1/patients/auth/switch", summary="Switch the active household patient")
async def switch_active_patient(
    body: SwitchRequest,
    response: Response,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(get_patient_db),
):
    acct = _account_holder_id(patient, db)
    if not acct:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No household account resolved.")

    target, is_self = _resolve_active_patient(db, acct, requested_patient_id=body.patient_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to act for this patient.",
        )

    active_patient_id = str(target.id)
    tenant_id = str(target.tenant_id) if target.tenant_id else None
    company_id = str(target.company_id) if target.company_id else None  # ADR-HC-010 D5
    access_token = create_patient_access_token(
        patient_id=active_patient_id, phone=target.phone, tenant_id=tenant_id, company_id=company_id,
        account_user_id=acct, on_behalf_of=not is_self,
    )
    refresh_token = create_patient_refresh_token(
        patient_id=active_patient_id, tenant_id=tenant_id, company_id=company_id)
    response.set_cookie(
        key="patient_refresh_token", value=refresh_token, httponly=True, secure=True,
        samesite="strict", max_age=7 * 24 * 3600, path="/api/v1/patients/auth",
    )
    return {"access_token": access_token, "patient_id": active_patient_id, "on_behalf_of": not is_self}


# ---------------------------------------------------------------------------
# POST /me/household/link — account holder requests to link an existing patient (18.10.3, Q3)
# ---------------------------------------------------------------------------

@router.post("/api/v1/patients/me/household/link", status_code=status.HTTP_202_ACCEPTED,
             summary="Request to link an existing patient (clinic-staff approval required)")
async def request_link(
    body: LinkRequest,
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(get_patient_db),
):
    caller_company = patient.require_company()
    acct = _account_holder_id(patient, db)
    if not acct:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No household account resolved.")
    if body.relationship not in ("spouse", "child", "parent", "other"):
        raise HTTPException(status_code=422, detail="Invalid relationship.")
    if body.basis not in ("parental_guardian", "delegated_adult", "spousal"):
        raise HTTPException(status_code=422, detail="Invalid basis.")

    generic = {"message": "If the patient exists, your link request has been submitted for clinic approval."}

    target = (
        db.query(HCPatient)
        .filter(HCPatient.id == body.patient_id, HCPatient.deleted_at.is_(None))
        .first()
    )
    # Anti-enumeration: never reveal whether the patient exists.
    if target is None:
        return generic
    # Same-Company (ADR-HC-009 AM3-3 / ADR-HC-010): under the shared SaaS tenant, the isolation
    # key is the Company — a target in another Company is rejected (stay generic to avoid
    # enumeration). Tenant is no longer a meaningful fence (all clinics share the SaaS tenant).
    if str(target.company_id) != caller_company:
        return generic

    db.execute(
        text(
            "INSERT INTO hc_patient_relationships "
            "(id, tenant_id, branch_id, account_user_id, patient_id, relationship, role, status, basis, granted_by, granted_at) "
            "VALUES (gen_random_uuid(), :tid, :bid, :acct, :pid, :rel, 'proxy', 'pending', :basis, :acct, NOW()) "
            # Re-request after a revoke reactivates the row to 'pending'. Active/pending
            # rows are left untouched (WHERE fails → no-op, no duplicate).
            "ON CONFLICT (account_user_id, patient_id) DO UPDATE SET "
            "status = 'pending', relationship = EXCLUDED.relationship, basis = EXCLUDED.basis, "
            "branch_id = EXCLUDED.branch_id, revoked_at = NULL, granted_at = NOW(), updated_at = NOW() "
            "WHERE hc_patient_relationships.status = 'revoked'"
        ),
        {"tid": str(target.tenant_id), "bid": body.branch_id, "acct": acct,
         "pid": str(target.id), "rel": body.relationship, "basis": body.basis},
    )
    try:
        write_event_audit(
            db=db, actor_id=acct, actor_type="patient", event_type="patient.link_requested",
            entity_type="patient", entity_id=str(target.id), tenant_id=str(target.tenant_id),
            branch_id=body.branch_id,
            ip=request.client.host if request.client else None,
            ua=request.headers.get("user-agent"),
        )
        db.commit()
    except Exception:
        db.rollback()
    return generic


# ---------------------------------------------------------------------------
# POST /me/household/dependents — register a NEW dependent patient (18.10.2, proxy consent 18.10.6)
# ---------------------------------------------------------------------------

@router.post("/api/v1/patients/me/household/dependents", status_code=status.HTTP_201_CREATED,
             summary="Register a new dependent patient under this account")
async def register_dependent(
    body: RegisterDependentRequest,
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(get_patient_db),
):
    tenant_id = patient.require_tenant()
    # A dependent belongs to the SAME Company as the account holder (ADR-HC-009 AM3-3;
    # household is within one Company). Inherit the caller's Company (NOT NULL isolation key).
    company_id = patient.require_company()
    acct = _account_holder_id(patient, db)
    if not acct:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No household account resolved.")
    if body.relationship not in _REL_KINDS:
        raise HTTPException(status_code=422, detail="Invalid relationship.")
    if body.basis not in _PROXY_BASES:
        raise HTTPException(status_code=422, detail="Invalid consent basis for a dependent.")
    if body.gender not in ("male", "female", "other"):
        raise HTTPException(status_code=422, detail="Invalid gender.")
    if not body.consent_accepted:
        raise HTTPException(status_code=422, detail="Consent must be accepted to register a dependent.")

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    now = datetime.utcnow()

    # New dependent PHI record — no own login (user_id NULL); phone_hash left NULL
    # so a dependent's contact number never blocks a real patient's phone-login.
    dep = HCPatient(
        tenant_id=tenant_id,
        company_id=company_id,
        full_name=body.full_name,
        date_of_birth=body.date_of_birth,
        phone=body.phone,
        nik=body.nik,
        gender=body.gender,
        consent_version=body.consent_version,
        consent_accepted_at=now,
        consent_ip=ip,
        consent_user_agent=ua,
        status="active",
    )
    dep.user_id = None
    db.add(dep)
    db.flush()
    dep_id = str(dep.id)

    # Owner relationship (the account holder owns the record they created).
    db.execute(
        text(
            "INSERT INTO hc_patient_relationships "
            "(id, tenant_id, branch_id, account_user_id, patient_id, relationship, role, status, basis, granted_by, granted_at) "
            "VALUES (gen_random_uuid(), :tid, :bid, :acct, :pid, :rel, 'owner', 'active', :basis, :acct, NOW())"
        ),
        {"tid": tenant_id, "bid": body.branch_id, "acct": acct,
         "pid": dep_id, "rel": body.relationship, "basis": body.basis},
    )

    # Proxy consent — records who consented, for whom, and on what basis (Q1 / 18.10.6).
    db.add(HCPatientConsent(
        tenant_id=tenant_id,
        company_id=company_id,
        patient_id=dep_id,
        consent_type="data_processing",
        consent_version=body.consent_version,
        status="active",
        accepted_at=now,
        ip=ip,
        user_agent=ua,
        purpose_description="Proxy-registered dependent — consent by account holder",
        basis=body.basis,
        consented_by_user_id=acct,
    ))

    try:
        write_event_audit(
            db=db, actor_id=acct, actor_type="patient", event_type="patient.dependent_registered",
            entity_type="patient", entity_id=dep_id, tenant_id=tenant_id, branch_id=body.branch_id,
            ip=ip, ua=ua, metadata={"on_behalf_of": dep_id, "relationship": body.relationship, "basis": body.basis},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"patient_id": dep_id, "relationship": body.relationship, "role": "owner", "basis": body.basis}


# ---------------------------------------------------------------------------
# Staff (branch-scoped) — link approval queue + majority detach
# ---------------------------------------------------------------------------

def _require_clinic_staff(branch_id: str, db: Session, current_user) -> HCRole:
    """Assert the caller is active clinic_owner/branch_manager for this branch (adr-hc-001)."""
    user_roles = getattr(current_user, "roles", []) or []
    if user_roles == ["patient"]:
        raise HTTPException(status_code=401, detail="Staff credentials required.")
    role = get_caller_hc_role(
        db=db, user_id=str(current_user.id), tenant_id=hc_shared_tenant_id(), branch_id=branch_id,
    )
    if role is None or role not in _STAFF_APPROVER_ROLES:
        raise HTTPException(status_code=403, detail="Requires clinic owner or branch manager.")
    return role


@router.get("/api/v1/patients/branches/{branch_id}/household/link-requests",
            summary="List pending patient-link requests for a branch (staff)")
async def list_link_requests(
    branch_id: str,
    db: Session = Depends(get_patient_db),
    current_user=Depends(get_current_user),
):
    _require_clinic_staff(branch_id, db, current_user)
    rows = db.execute(
        text(
            "SELECT id, account_user_id, patient_id, relationship, basis, granted_at "
            "FROM hc_patient_relationships "
            "WHERE tenant_id = :tid AND branch_id = :bid AND status = 'pending' "
            "ORDER BY granted_at ASC"
        ),
        {"tid": hc_shared_tenant_id(), "bid": branch_id},
    ).fetchall()
    return {
        "link_requests": [
            {"id": str(r[0]), "account_user_id": r[1], "patient_id": str(r[2]),
             "relationship": r[3], "basis": r[4], "requested_at": r[5].isoformat() if r[5] else None}
            for r in rows
        ],
        "total": len(rows),
    }


def _decide_link_request(branch_id: str, rel_id: str, approve: bool, db: Session, current_user) -> dict:
    _require_clinic_staff(branch_id, db, current_user)
    row = db.execute(
        text(
            "SELECT id, patient_id FROM hc_patient_relationships "
            "WHERE id = :rid AND tenant_id = :tid AND branch_id = :bid AND status = 'pending'"
        ),
        {"rid": rel_id, "tid": hc_shared_tenant_id(), "bid": branch_id},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Pending link request not found for this branch.")

    new_status = "active" if approve else "revoked"
    db.execute(
        text(
            "UPDATE hc_patient_relationships SET status = :st, "
            "approved_by_staff_id = :sid, approved_at = NOW(), "
            "revoked_at = CASE WHEN :st = 'revoked' THEN NOW() ELSE NULL END, updated_at = NOW() "
            "WHERE id = :rid"
        ),
        {"st": new_status, "sid": str(current_user.id), "rid": rel_id},
    )
    try:
        write_event_audit(
            db=db, actor_id=str(current_user.id), actor_type="staff",
            event_type="patient.link_approved" if approve else "patient.link_rejected",
            entity_type="patient", entity_id=str(row[1]),
            tenant_id=hc_shared_tenant_id(), branch_id=branch_id,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"id": rel_id, "status": new_status}


@router.post("/api/v1/patients/branches/{branch_id}/household/link-requests/{rel_id}/approve",
             summary="Approve a patient-link request (staff)")
async def approve_link_request(branch_id: str, rel_id: str,
                               db: Session = Depends(get_patient_db),
                               current_user=Depends(get_current_user)):
    return _decide_link_request(branch_id, rel_id, True, db, current_user)


@router.post("/api/v1/patients/branches/{branch_id}/household/link-requests/{rel_id}/reject",
             summary="Reject a patient-link request (staff)")
async def reject_link_request(branch_id: str, rel_id: str,
                              db: Session = Depends(get_patient_db),
                              current_user=Depends(get_current_user)):
    return _decide_link_request(branch_id, rel_id, False, db, current_user)


@router.post("/api/v1/patients/branches/{branch_id}/household/{patient_id}/detach",
             summary="Clinic-mediated majority detach: revoke all proxy access to a patient (staff, Q4)")
async def detach_patient(branch_id: str, patient_id: str,
                         db: Session = Depends(get_patient_db),
                         current_user=Depends(get_current_user)):
    _require_clinic_staff(branch_id, db, current_user)
    result = db.execute(
        text(
            "UPDATE hc_patient_relationships SET status = 'revoked', revoked_at = NOW(), updated_at = NOW() "
            "WHERE patient_id = :pid AND tenant_id = :tid AND status IN ('active','pending') "
            "AND relationship <> 'self'"
        ),
        {"pid": patient_id, "tid": hc_shared_tenant_id()},
    )
    try:
        write_event_audit(
            db=db, actor_id=str(current_user.id), actor_type="staff",
            event_type="patient.proxy_detached", entity_type="patient", entity_id=patient_id,
            tenant_id=hc_shared_tenant_id(), branch_id=branch_id,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"patient_id": patient_id, "revoked_grants": result.rowcount}


__all__ = ["router"]
