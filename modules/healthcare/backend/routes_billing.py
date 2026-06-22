"""
Healthcare Billing API.

T-HC-052 -- Invoice & service-item management (staff)
T-HC-053 -- Patient invoice access
T-HC-054 -- BPJS file export

All branch-scoped staff endpoints use healthcare_branch_session.
All patient-PHI endpoints call write_phi_read_audit().
Finalized invoices are IMMUTABLE -- any edit attempt returns HTTP 422.
BPJS export uses HMAC hash for patient names -- no raw PHI in export file.
PLACEHOLDER: BPJS export needs legal review before production use.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session
from modules.healthcare.sdk.branch_scope import healthcare_branch_session
from modules.healthcare.sdk.dpa_gate import require_dpa
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.patient_auth import PatientTokenData, get_current_patient
from modules.healthcare.sdk.phi_audit import write_event_audit, write_phi_read_audit
from modules.healthcare.sdk.phi_crypto import decrypt_phi, encrypt_phi
from modules.healthcare.schemas.billing import (
    BPJSExportCreate,
    BPJSExportResponse,
    InsuranceProfileCreate,
    InsuranceProfileResponse,
    InsuranceProfileUpdate,
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceListItem,
    InvoiceResponse,
    InvoiceLineResponse,
    PatientInvoiceListItem,
    PatientInvoiceListResponse,
    PaymentCreate,
    PaymentResponse,
    ServiceItemCreate,
    ServiceItemListResponse,
    ServiceItemResponse,
    ServiceItemUpdate,
)

router = APIRouter(tags=["healthcare-billing"])

# Fail-fast: BPJS HMAC key must be set at startup
_BPJS_HMAC_KEY = os.environ.get("BPJS_EXPORT_HMAC_KEY")
if not _BPJS_HMAC_KEY:
    raise RuntimeError("BPJS_EXPORT_HMAC_KEY environment variable is required")
_BPJS_HMAC_KEY = _BPJS_HMAC_KEY.encode()

_BILLING_STAFF_ROLES = [HCRole.billing_staff, HCRole.branch_manager, HCRole.clinic_owner]
_MANAGER_ROLES = [HCRole.branch_manager, HCRole.clinic_owner]
_BILLING_WRITE_ROLES = [HCRole.billing_staff, HCRole.branch_manager]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _get_ua(request: Request) -> str:
    return request.headers.get("user-agent", "")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


def _mask_name(name: str) -> str:
    """Mask all but first character of each word: 'John Doe' -> 'J*** D***'."""
    if not name:
        return "***"
    parts = name.split()
    return " ".join((p[0] + "***") if len(p) > 1 else "***" for p in parts)


def _invoice_number(tenant_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = str(uuid.uuid4()).replace("-", "")[:6].upper()
    return f"INV-{ts}-{suffix}"


def _resolve_tenant(request: Request) -> str:
    """Extract tenant_id from request state (set by platform middleware)."""
    state = getattr(request.state, "tenant_id", None)
    if state:
        return str(state)
    user = getattr(request.state, "user", None)
    if user:
        return str(getattr(user, "tenant_id", ""))
    return ""


def _resolve_actor_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user:
        return str(getattr(user, "id", ""))
    return ""


def _fetch_invoice(db: Session, invoice_id: str, branch_id: str, tenant_id: str) -> dict:
    row = db.execute(
        text(
            "SELECT id, tenant_id, branch_id, patient_id, encounter_id, invoice_number, "
            "status, total_amount, currency, insurance_profile_id, notes, "
            "finalized_at, voided_at, created_by, created_at, updated_at "
            "FROM hcb_invoices "
            "WHERE id = :iid AND branch_id = :bid AND tenant_id = :tid"
        ),
        {"iid": invoice_id, "bid": branch_id, "tid": tenant_id},
    ).mappings().fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return dict(row)


def _fetch_invoice_lines(db: Session, invoice_id: str) -> List[dict]:
    rows = db.execute(
        text(
            "SELECT id, service_item_id, item_name, item_code, quantity, unit_price, subtotal "
            "FROM hcb_invoice_lines WHERE invoice_id = :iid ORDER BY created_at"
        ),
        {"iid": invoice_id},
    ).mappings().fetchall()
    return [dict(r) for r in rows]


def _build_invoice_response(inv: dict, lines: list) -> InvoiceResponse:
    return InvoiceResponse(
        id=inv["id"], tenant_id=inv["tenant_id"], branch_id=inv["branch_id"],
        patient_id=inv["patient_id"], patient_display=None,
        encounter_id=inv.get("encounter_id"),
        invoice_number=inv["invoice_number"], status=inv["status"],
        total_amount=inv["total_amount"], currency=inv["currency"],
        insurance_profile_id=inv.get("insurance_profile_id"),
        notes=inv.get("notes"),
        finalized_at=inv.get("finalized_at"), voided_at=inv.get("voided_at"),
        created_by=inv.get("created_by"),
        created_at=inv["created_at"], updated_at=inv["updated_at"],
        lines=[InvoiceLineResponse(**line) for line in lines],
    )


# ---------------------------------------------------------------------------
# T-HC-052  Service Items
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/modules/healthcare_billing/branches/{branch_id}/service-items",
    response_model=ServiceItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_item(
    branch_id: str,
    payload: ServiceItemCreate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    _role=Depends(has_hc_permission(_MANAGER_ROLES)),
    _dpa=Depends(require_dpa),
):
    """Create a billing service item. Auth: branch_manager, clinic_owner."""
    tenant_id = _resolve_tenant(request)

    existing = db.execute(
        text("SELECT id FROM hcb_service_items WHERE tenant_id = :tid AND code = :code LIMIT 1"),
        {"tid": tenant_id, "code": payload.code},
    ).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service item code '{payload.code}' already exists for this tenant",
        )

    item_id = _new_id()
    now = _now()
    db.execute(
        text(
            "INSERT INTO hcb_service_items "
            "(id, tenant_id, branch_id, name, code, unit_price, currency, category, is_active, created_at, updated_at) "
            "VALUES (:id, :tid, :bid, :name, :code, :price, :currency, :cat, :active, :now, :now)"
        ),
        {
            "id": item_id, "tid": tenant_id, "bid": branch_id,
            "name": payload.name, "code": payload.code,
            "price": float(payload.unit_price), "currency": payload.currency,
            "cat": payload.category, "active": payload.is_active, "now": now,
        },
    )
    db.commit()

    row = db.execute(
        text("SELECT * FROM hcb_service_items WHERE id = :id"), {"id": item_id}
    ).mappings().fetchone()
    return ServiceItemResponse(**dict(row))


@router.get(
    "/api/v1/modules/healthcare_billing/branches/{branch_id}/service-items",
    response_model=ServiceItemListResponse,
)
async def list_service_items(
    branch_id: str,
    request: Request,
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(healthcare_branch_session),
    _role=Depends(has_hc_permission(_BILLING_STAFF_ROLES)),
):
    """List service items. Auth: billing_staff, branch_manager, clinic_owner."""
    tenant_id = _resolve_tenant(request)
    filters = "WHERE tenant_id = :tid AND branch_id = :bid"
    params: dict = {"tid": tenant_id, "bid": branch_id}
    if category is not None:
        filters += " AND category = :cat"
        params["cat"] = category
    if is_active is not None:
        filters += " AND is_active = :active"
        params["active"] = is_active

    total = db.execute(text(f"SELECT COUNT(*) FROM hcb_service_items {filters}"), params).scalar()
    offset = (page - 1) * page_size
    rows = db.execute(
        text(f"SELECT * FROM hcb_service_items {filters} ORDER BY name LIMIT :lim OFFSET :off"),
        {**params, "lim": page_size, "off": offset},
    ).mappings().fetchall()

    return ServiceItemListResponse(
        items=[ServiceItemResponse(**dict(r)) for r in rows],
        total=total or 0, page=page, page_size=page_size,
    )


@router.put(
    "/api/v1/modules/healthcare_billing/branches/{branch_id}/service-items/{item_id}",
    response_model=ServiceItemResponse,
)
async def update_service_item(
    branch_id: str,
    item_id: str,
    payload: ServiceItemUpdate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    _role=Depends(has_hc_permission(_MANAGER_ROLES)),
):
    """Update a service item. Code cannot be changed if used in invoice lines."""
    tenant_id = _resolve_tenant(request)
    row = db.execute(
        text("SELECT * FROM hcb_service_items WHERE id = :id AND branch_id = :bid AND tenant_id = :tid"),
        {"id": item_id, "bid": branch_id, "tid": tenant_id},
    ).mappings().fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service item not found")

    updates: dict = {"id": item_id, "now": _now()}
    set_clauses = ["updated_at = :now"]
    if payload.name is not None:
        set_clauses.append("name = :name"); updates["name"] = payload.name
    if payload.unit_price is not None:
        set_clauses.append("unit_price = :price"); updates["price"] = float(payload.unit_price)
    if payload.currency is not None:
        set_clauses.append("currency = :currency"); updates["currency"] = payload.currency
    if payload.category is not None:
        set_clauses.append("category = :cat"); updates["cat"] = payload.category
    if payload.is_active is not None:
        set_clauses.append("is_active = :active"); updates["active"] = payload.is_active

    db.execute(
        text(f"UPDATE hcb_service_items SET {', '.join(set_clauses)} WHERE id = :id"),
        updates,
    )
    db.commit()

    updated = db.execute(
        text("SELECT * FROM hcb_service_items WHERE id = :id"), {"id": item_id}
    ).mappings().fetchone()
    return ServiceItemResponse(**dict(updated))


# ---------------------------------------------------------------------------
# T-HC-052  Invoices
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/modules/healthcare_billing/branches/{branch_id}/invoices",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invoice(
    branch_id: str,
    payload: InvoiceCreate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    _role=Depends(has_hc_permission(_BILLING_WRITE_ROLES)),
    _dpa=Depends(require_dpa),
):
    """Create a draft invoice with auto-calculated subtotals. Auth: billing_staff, branch_manager."""
    tenant_id = _resolve_tenant(request)
    actor_id = _resolve_actor_id(request)

    lines_data = []
    total = Decimal("0")
    for line in payload.lines:
        item = db.execute(
            text("SELECT * FROM hcb_service_items WHERE id = :id AND tenant_id = :tid"),
            {"id": line.service_item_id, "tid": tenant_id},
        ).mappings().fetchone()
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Service item {line.service_item_id} not found",
            )
        unit_price = Decimal(str(item["unit_price"]))
        subtotal = unit_price * line.quantity
        total += subtotal
        lines_data.append({
            "service_item_id": line.service_item_id,
            "item_name": item["name"],
            "item_code": item["code"],
            "quantity": line.quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

    invoice_id = _new_id()
    inv_number = _invoice_number(tenant_id)
    now = _now()

    db.execute(
        text(
            "INSERT INTO hcb_invoices "
            "(id, tenant_id, branch_id, patient_id, encounter_id, invoice_number, status, "
            "total_amount, currency, insurance_profile_id, notes, created_by, created_at, updated_at) "
            "VALUES (:id, :tid, :bid, :pid, :eid, :inv_num, 'draft', "
            ":total, 'IDR', :ins_id, :notes, :created_by, :now, :now)"
        ),
        {
            "id": invoice_id, "tid": tenant_id, "bid": branch_id,
            "pid": payload.patient_id, "eid": payload.encounter_id,
            "inv_num": inv_number, "total": float(total),
            "ins_id": payload.insurance_profile_id,
            "notes": payload.notes, "created_by": actor_id, "now": now,
        },
    )

    for line in lines_data:
        db.execute(
            text(
                "INSERT INTO hcb_invoice_lines "
                "(id, tenant_id, invoice_id, service_item_id, item_name, item_code, "
                "quantity, unit_price, subtotal, created_at) "
                "VALUES (:id, :tid, :inv_id, :sid, :iname, :icode, :qty, :uprice, :sub, :now)"
            ),
            {
                "id": _new_id(), "tid": tenant_id, "inv_id": invoice_id,
                "sid": line["service_item_id"], "iname": line["item_name"],
                "icode": line["item_code"], "qty": line["quantity"],
                "uprice": float(line["unit_price"]), "sub": float(line["subtotal"]),
                "now": now,
            },
        )

    write_event_audit(
        db=db, actor_id=actor_id, actor_type="staff",
        event_type="invoice.created", entity_type="invoice",
        entity_id=invoice_id, tenant_id=tenant_id, branch_id=branch_id,
        metadata={"invoice_number": inv_number},
    )
    db.commit()

    inv = _fetch_invoice(db, invoice_id, branch_id, tenant_id)
    return _build_invoice_response(inv, _fetch_invoice_lines(db, invoice_id))


@router.get(
    "/api/v1/modules/healthcare_billing/branches/{branch_id}/invoices",
    response_model=InvoiceListResponse,
)
async def list_invoices(
    branch_id: str,
    request: Request,
    invoice_status: Optional[str] = Query(None, alias="status"),
    patient_id: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(healthcare_branch_session),
    _role=Depends(has_hc_permission(_BILLING_STAFF_ROLES)),
):
    """List invoices with optional filters. Auth: billing_staff, branch_manager, clinic_owner."""
    tenant_id = _resolve_tenant(request)
    filters = "WHERE tenant_id = :tid AND branch_id = :bid"
    params: dict = {"tid": tenant_id, "bid": branch_id}
    if invoice_status:
        filters += " AND status = :status"; params["status"] = invoice_status
    if patient_id:
        filters += " AND patient_id = :pid"; params["pid"] = patient_id
    if date_from:
        filters += " AND created_at >= :dfrom"; params["dfrom"] = date_from
    if date_to:
        filters += " AND created_at <= :dto"; params["dto"] = date_to

    total = db.execute(text(f"SELECT COUNT(*) FROM hcb_invoices {filters}"), params).scalar()
    offset = (page - 1) * page_size
    rows = db.execute(
        text(
            f"SELECT id, invoice_number, patient_id, status, total_amount, currency, "
            f"created_at, finalized_at FROM hcb_invoices {filters} "
            f"ORDER BY created_at DESC LIMIT :lim OFFSET :off"
        ),
        {**params, "lim": page_size, "off": offset},
    ).mappings().fetchall()

    return InvoiceListResponse(
        items=[InvoiceListItem(**dict(r)) for r in rows],
        total=total or 0, page=page, page_size=page_size,
    )


@router.get(
    "/api/v1/modules/healthcare_billing/branches/{branch_id}/invoices/{invoice_id}",
    response_model=InvoiceResponse,
)
async def get_invoice(
    branch_id: str,
    invoice_id: str,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    _role=Depends(has_hc_permission(_BILLING_WRITE_ROLES)),
):
    """Get full invoice with lines. Calls write_phi_read_audit (patient data included)."""
    tenant_id = _resolve_tenant(request)
    actor_id = _resolve_actor_id(request)

    inv = _fetch_invoice(db, invoice_id, branch_id, tenant_id)
    inv_lines = _fetch_invoice_lines(db, invoice_id)

    write_phi_read_audit(
        db=db, actor_id=actor_id, actor_type="staff",
        entity_type="invoice", entity_id=invoice_id,
        tenant_id=tenant_id, branch_id=branch_id,
        ip=_get_ip(request), ua=_get_ua(request),
        metadata={"invoice_number": inv["invoice_number"]},
    )

    return _build_invoice_response(inv, inv_lines)


@router.post(
    "/api/v1/modules/healthcare_billing/branches/{branch_id}/invoices/{invoice_id}/finalize",
    response_model=InvoiceResponse,
)
async def finalize_invoice(
    branch_id: str,
    invoice_id: str,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    _role=Depends(has_hc_permission(_BILLING_WRITE_ROLES)),
):
    """Finalize invoice -- makes it IMMUTABLE. Auth: billing_staff, branch_manager."""
    tenant_id = _resolve_tenant(request)
    actor_id = _resolve_actor_id(request)

    inv = _fetch_invoice(db, invoice_id, branch_id, tenant_id)
    if inv["status"] != "draft":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Only draft invoices can be finalized (current status: {inv['status']})",
        )

    now = _now()
    db.execute(
        text(
            "UPDATE hcb_invoices SET status = 'finalized', finalized_at = :now, updated_at = :now "
            "WHERE id = :id AND tenant_id = :tid AND branch_id = :bid"
        ),
        {"now": now, "id": invoice_id, "tid": tenant_id, "bid": branch_id},
    )
    write_event_audit(
        db=db, actor_id=actor_id, actor_type="staff",
        event_type="invoice.finalized", entity_type="invoice",
        entity_id=invoice_id, tenant_id=tenant_id, branch_id=branch_id,
    )
    db.commit()

    inv = _fetch_invoice(db, invoice_id, branch_id, tenant_id)
    return _build_invoice_response(inv, _fetch_invoice_lines(db, invoice_id))


@router.post(
    "/api/v1/modules/healthcare_billing/branches/{branch_id}/invoices/{invoice_id}/void",
    response_model=InvoiceResponse,
)
async def void_invoice(
    branch_id: str,
    invoice_id: str,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    _role=Depends(has_hc_permission(_MANAGER_ROLES)),
):
    """Void a finalized invoice. Auth: branch_manager, clinic_owner only."""
    tenant_id = _resolve_tenant(request)
    actor_id = _resolve_actor_id(request)

    inv = _fetch_invoice(db, invoice_id, branch_id, tenant_id)
    if inv["status"] != "finalized":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only finalized invoices can be voided",
        )

    now = _now()
    db.execute(
        text(
            "UPDATE hcb_invoices SET status = 'void', voided_at = :now, updated_at = :now "
            "WHERE id = :id AND tenant_id = :tid AND branch_id = :bid"
        ),
        {"now": now, "id": invoice_id, "tid": tenant_id, "bid": branch_id},
    )
    write_event_audit(
        db=db, actor_id=actor_id, actor_type="staff",
        event_type="invoice.voided", entity_type="invoice",
        entity_id=invoice_id, tenant_id=tenant_id, branch_id=branch_id,
    )
    db.commit()

    inv = _fetch_invoice(db, invoice_id, branch_id, tenant_id)
    return _build_invoice_response(inv, _fetch_invoice_lines(db, invoice_id))


@router.post(
    "/api/v1/modules/healthcare_billing/branches/{branch_id}/invoices/{invoice_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_payment(
    branch_id: str,
    invoice_id: str,
    payload: PaymentCreate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    _role=Depends(has_hc_permission(_BILLING_WRITE_ROLES)),
):
    """Record a payment against an invoice. Auth: billing_staff, branch_manager."""
    tenant_id = _resolve_tenant(request)
    actor_id = _resolve_actor_id(request)

    inv = _fetch_invoice(db, invoice_id, branch_id, tenant_id)
    if inv["status"] == "void":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot record payment on a voided invoice",
        )

    pay_id = _new_id()
    now = _now()
    db.execute(
        text(
            "INSERT INTO hcb_payments "
            "(id, tenant_id, invoice_id, amount, currency, payment_method, payment_date, "
            "reference_number, recorded_by, created_at) "
            "VALUES (:id, :tid, :iid, :amt, :curr, :method, :pdate, :ref, :by, :now)"
        ),
        {
            "id": pay_id, "tid": tenant_id, "iid": invoice_id,
            "amt": float(payload.amount), "curr": inv["currency"],
            "method": payload.payment_method, "pdate": payload.payment_date,
            "ref": payload.reference_number, "by": actor_id, "now": now,
        },
    )
    write_event_audit(
        db=db, actor_id=actor_id, actor_type="staff",
        event_type="payment.recorded", entity_type="payment",
        entity_id=pay_id, tenant_id=tenant_id, branch_id=branch_id,
        metadata={"invoice_id": invoice_id, "amount": str(payload.amount)},
    )
    db.commit()

    row = db.execute(
        text("SELECT * FROM hcb_payments WHERE id = :id"), {"id": pay_id}
    ).mappings().fetchone()
    return PaymentResponse(**dict(row))


# ---------------------------------------------------------------------------
# T-HC-053  Patient Invoice Access
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/patients/me/invoices",
    response_model=PatientInvoiceListResponse,
)
async def patient_list_invoices(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(tenant_scoped_session),
):
    """Patient: list own finalized invoices. Calls write_phi_read_audit."""
    tenant_id = patient.tenant_id

    total = db.execute(
        text(
            "SELECT COUNT(*) FROM hcb_invoices "
            "WHERE patient_id = :pid AND tenant_id = :tid AND status = 'finalized'"
        ),
        {"pid": patient.patient_id, "tid": tenant_id},
    ).scalar()

    offset = (page - 1) * page_size
    rows = db.execute(
        text(
            "SELECT i.id, i.invoice_number, i.total_amount, i.currency, i.status, "
            "i.created_at, i.finalized_at, "
            "e.created_at AS encounter_date, b.branch_name AS clinic_name "
            "FROM hcb_invoices i "
            "LEFT JOIN hc_encounters e ON e.id = i.encounter_id "
            "LEFT JOIN hc_branches b ON b.id = i.branch_id "
            "WHERE i.patient_id = :pid AND i.tenant_id = :tid AND i.status = 'finalized' "
            "ORDER BY i.created_at DESC LIMIT :lim OFFSET :off"
        ),
        {"pid": patient.patient_id, "tid": tenant_id, "lim": page_size, "off": offset},
    ).mappings().fetchall()

    write_phi_read_audit(
        db=db, actor_id=patient.patient_id, actor_type="patient",
        entity_type="invoice_list", entity_id=patient.patient_id,
        tenant_id=tenant_id, ip=_get_ip(request), ua=_get_ua(request),
    )

    items = []
    for r in rows:
        items.append(PatientInvoiceListItem(
            id=r["id"], invoice_number=r["invoice_number"],
            total_amount=r["total_amount"], currency=r["currency"],
            status=r["status"], encounter_date=r.get("encounter_date"),
            clinic_name=r.get("clinic_name"), created_at=r["created_at"],
        ))

    return PatientInvoiceListResponse(
        items=items, total=total or 0, page=page, page_size=page_size,
    )


@router.get(
    "/api/v1/patients/me/invoices/{invoice_id}",
    response_model=InvoiceResponse,
)
async def patient_get_invoice(
    invoice_id: str,
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(tenant_scoped_session),
):
    """Patient: get own invoice detail. Calls write_phi_read_audit."""
    tenant_id = patient.tenant_id
    row = db.execute(
        text(
            "SELECT id, tenant_id, branch_id, patient_id, encounter_id, invoice_number, "
            "status, total_amount, currency, insurance_profile_id, notes, "
            "finalized_at, voided_at, created_by, created_at, updated_at "
            "FROM hcb_invoices "
            "WHERE id = :iid AND patient_id = :pid AND tenant_id = :tid"
        ),
        {"iid": invoice_id, "pid": patient.patient_id, "tid": tenant_id},
    ).mappings().fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    write_phi_read_audit(
        db=db, actor_id=patient.patient_id, actor_type="patient",
        entity_type="invoice", entity_id=invoice_id,
        tenant_id=tenant_id, ip=_get_ip(request), ua=_get_ua(request),
    )

    inv_lines = _fetch_invoice_lines(db, invoice_id)
    return _build_invoice_response(dict(row), inv_lines)


@router.get(
    "/api/v1/patients/me/invoices/{invoice_id}/pdf",
)
async def patient_invoice_pdf(
    invoice_id: str,
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(tenant_scoped_session),
):
    """
    Patient: invoice PDF-ready data (application/json).

    NOTE: Actual PDF generation is a future phase. Returns structured JSON
    with format='invoice_v1' for frontend PDF rendering.
    """
    tenant_id = patient.tenant_id
    row = db.execute(
        text(
            "SELECT id, tenant_id, branch_id, patient_id, encounter_id, invoice_number, "
            "status, total_amount, currency, insurance_profile_id, notes, "
            "finalized_at, voided_at, created_by, created_at, updated_at "
            "FROM hcb_invoices "
            "WHERE id = :iid AND patient_id = :pid AND tenant_id = :tid"
        ),
        {"iid": invoice_id, "pid": patient.patient_id, "tid": tenant_id},
    ).mappings().fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    write_phi_read_audit(
        db=db, actor_id=patient.patient_id, actor_type="patient",
        entity_type="invoice", entity_id=invoice_id,
        tenant_id=tenant_id, ip=_get_ip(request), ua=_get_ua(request),
        metadata={"action": "pdf_view"},
    )

    inv_lines = _fetch_invoice_lines(db, invoice_id)

    return {
        "format": "invoice_v1",
        "_note": "PDF download is coming in a future phase. Use this JSON for frontend PDF rendering.",
        "invoice_number": row["invoice_number"],
        "status": row["status"],
        "total_amount": str(row["total_amount"]),
        "currency": row["currency"],
        "notes": row["notes"],
        "finalized_at": row["finalized_at"].isoformat() if row["finalized_at"] else None,
        "created_at": row["created_at"].isoformat(),
        "lines": [
            {
                "item_name": line["item_name"],
                "item_code": line["item_code"],
                "quantity": line["quantity"],
                "unit_price": str(line["unit_price"]),
                "subtotal": str(line["subtotal"]),
            }
            for line in inv_lines
        ],
    }


# ---------------------------------------------------------------------------
# Patient insurance profiles
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/patients/me/insurance",
    response_model=InsuranceProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def patient_create_insurance(
    payload: InsuranceProfileCreate,
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(tenant_scoped_session),
):
    """Patient: create own insurance profile. insurance_number encrypted at rest."""
    tenant_id = patient.tenant_id
    profile_id = _new_id()
    now = _now()

    encrypted_number = encrypt_phi(payload.insurance_number) if payload.insurance_number else None

    db.execute(
        text(
            "INSERT INTO hcb_insurance_profiles "
            "(id, tenant_id, patient_id, insurance_type, insurance_number, "
            "provider_name, is_active, created_at, updated_at) "
            "VALUES (:id, :tid, :pid, :itype, :inum, :pname, :active, :now, :now)"
        ),
        {
            "id": profile_id, "tid": tenant_id, "pid": patient.patient_id,
            "itype": payload.insurance_type, "inum": encrypted_number,
            "pname": payload.provider_name, "active": payload.is_active, "now": now,
        },
    )
    write_event_audit(
        db=db, actor_id=patient.patient_id, actor_type="patient",
        event_type="insurance_profile.created", entity_type="insurance_profile",
        entity_id=profile_id, tenant_id=tenant_id,
        ip=_get_ip(request), ua=_get_ua(request),
    )
    db.commit()

    return InsuranceProfileResponse(
        id=profile_id, tenant_id=tenant_id, patient_id=patient.patient_id,
        insurance_type=payload.insurance_type,
        insurance_number=payload.insurance_number,  # return plaintext to caller
        provider_name=payload.provider_name,
        is_active=payload.is_active, created_at=now, updated_at=now,
    )


@router.get(
    "/api/v1/patients/me/insurance",
    response_model=List[InsuranceProfileResponse],
)
async def patient_list_insurance(
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(tenant_scoped_session),
):
    """Patient: list own insurance profiles. Decrypts insurance_number. Calls write_phi_read_audit."""
    tenant_id = patient.tenant_id
    rows = db.execute(
        text(
            "SELECT id, tenant_id, patient_id, insurance_type, insurance_number, "
            "provider_name, is_active, created_at, updated_at "
            "FROM hcb_insurance_profiles "
            "WHERE patient_id = :pid AND tenant_id = :tid ORDER BY created_at"
        ),
        {"pid": patient.patient_id, "tid": tenant_id},
    ).mappings().fetchall()

    write_phi_read_audit(
        db=db, actor_id=patient.patient_id, actor_type="patient",
        entity_type="insurance_profile", entity_id=patient.patient_id,
        tenant_id=tenant_id, ip=_get_ip(request), ua=_get_ua(request),
    )

    result = []
    for r in rows:
        decrypted = None
        if r["insurance_number"]:
            try:
                decrypted = decrypt_phi(r["insurance_number"])
            except Exception:
                decrypted = None
        result.append(InsuranceProfileResponse(
            id=r["id"], tenant_id=r["tenant_id"], patient_id=r["patient_id"],
            insurance_type=r["insurance_type"], insurance_number=decrypted,
            provider_name=r["provider_name"], is_active=r["is_active"],
            created_at=r["created_at"], updated_at=r["updated_at"],
        ))
    return result


@router.put(
    "/api/v1/patients/me/insurance/{profile_id}",
    response_model=InsuranceProfileResponse,
)
async def patient_update_insurance(
    profile_id: str,
    payload: InsuranceProfileUpdate,
    request: Request,
    patient: PatientTokenData = Depends(get_current_patient),
    db: Session = Depends(tenant_scoped_session),
):
    """Patient: update own insurance profile."""
    tenant_id = patient.tenant_id
    row = db.execute(
        text(
            "SELECT * FROM hcb_insurance_profiles "
            "WHERE id = :id AND patient_id = :pid AND tenant_id = :tid"
        ),
        {"id": profile_id, "pid": patient.patient_id, "tid": tenant_id},
    ).mappings().fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance profile not found")

    updates: dict = {"id": profile_id, "now": _now()}
    set_clauses = ["updated_at = :now"]
    if payload.insurance_type is not None:
        set_clauses.append("insurance_type = :itype"); updates["itype"] = payload.insurance_type
    if payload.insurance_number is not None:
        set_clauses.append("insurance_number = :inum")
        updates["inum"] = encrypt_phi(payload.insurance_number)
    if payload.provider_name is not None:
        set_clauses.append("provider_name = :pname"); updates["pname"] = payload.provider_name
    if payload.is_active is not None:
        set_clauses.append("is_active = :active"); updates["active"] = payload.is_active

    db.execute(
        text(f"UPDATE hcb_insurance_profiles SET {', '.join(set_clauses)} WHERE id = :id"),
        updates,
    )
    db.commit()

    updated = db.execute(
        text("SELECT * FROM hcb_insurance_profiles WHERE id = :id"), {"id": profile_id}
    ).mappings().fetchone()

    decrypted_num = None
    if updated["insurance_number"]:
        try:
            decrypted_num = decrypt_phi(updated["insurance_number"])
        except Exception:
            pass

    return InsuranceProfileResponse(
        id=updated["id"], tenant_id=updated["tenant_id"], patient_id=updated["patient_id"],
        insurance_type=updated["insurance_type"], insurance_number=decrypted_num,
        provider_name=updated["provider_name"], is_active=updated["is_active"],
        created_at=updated["created_at"], updated_at=updated["updated_at"],
    )


# ---------------------------------------------------------------------------
# T-HC-054  BPJS Export
# ---------------------------------------------------------------------------

def _hmac_name(name: str) -> str:
    """
    HMAC-SHA256 hash of patient name for BPJS export.

    PLACEHOLDER: Real BPJS submissions require patient names. This HMAC hash
    is used for demo/internal purposes only and must undergo legal review
    before production use.
    """
    return hmac.new(_BPJS_HMAC_KEY, name.encode("utf-8"), hashlib.sha256).hexdigest()


@router.post(
    "/api/v1/modules/healthcare_billing/branches/{branch_id}/bpjs-exports",
    response_model=BPJSExportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_bpjs_export(
    branch_id: str,
    payload: BPJSExportCreate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    _role=Depends(has_hc_permission(_BILLING_WRITE_ROLES)),
):
    """
    Generate BPJS claim export for a period. Auth: billing_staff, branch_manager.

    Patient names are HMAC-hashed -- no raw PHI in the export file.
    PLACEHOLDER: Needs legal review before production use.
    """
    tenant_id = _resolve_tenant(request)
    actor_id = _resolve_actor_id(request)
    year_month = payload.export_period

    rows = db.execute(
        text(
            "SELECT i.id AS invoice_id, i.invoice_number, i.total_amount, "
            "i.finalized_at, i.encounter_id, "
            "p.full_name AS patient_name, p.id AS patient_id "
            "FROM hcb_invoices i "
            "JOIN hc_patients p ON p.id = i.patient_id "
            "LEFT JOIN hcb_insurance_profiles ip ON ip.id = i.insurance_profile_id "
            "WHERE i.tenant_id = :tid AND i.branch_id = :bid "
            "AND i.status = 'finalized' "
            "AND (ip.insurance_type = 'bpjs' OR i.insurance_profile_id IS NULL) "
            "AND TO_CHAR(i.finalized_at, 'YYYY-MM') = :period "
            "ORDER BY i.finalized_at"
        ),
        {"tid": tenant_id, "bid": branch_id, "period": year_month},
    ).mappings().fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "no_sep", "nama_peserta_hash", "tgl_pelayanan",
        "kode_diagnosa", "kode_prosedur", "biaya_tagihan", "status_klaim",
    ])
    total_amount = Decimal("0")
    for i, r in enumerate(rows, start=1):
        name_hash = _hmac_name(r["patient_name"] or "unknown")
        tgl = r["finalized_at"].strftime("%Y-%m-%d") if r["finalized_at"] else ""
        writer.writerow([
            f"SEP-{year_month}-{i:05d}",
            name_hash,
            tgl,
            "",  # kode_diagnosa: from encounter in production
            "",  # kode_prosedur: from encounter in production
            str(r["total_amount"]),
            "pending",
        ])
        total_amount += Decimal(str(r["total_amount"]))

    csv_content = output.getvalue()
    file_reference = base64.b64encode(csv_content.encode("utf-8")).decode("ascii")

    export_id = _new_id()
    now = _now()
    db.execute(
        text(
            "INSERT INTO hcb_bpjs_exports "
            "(id, tenant_id, branch_id, export_period, status, file_reference, "
            "record_count, total_amount, generated_at, created_by, created_at) "
            "VALUES (:id, :tid, :bid, :period, 'generated', :fref, "
            ":count, :total, :gen_at, :by, :now)"
        ),
        {
            "id": export_id, "tid": tenant_id, "bid": branch_id,
            "period": year_month, "fref": file_reference,
            "count": len(rows), "total": float(total_amount),
            "gen_at": now, "by": actor_id, "now": now,
        },
    )
    write_event_audit(
        db=db, actor_id=actor_id, actor_type="staff",
        event_type="bpjs_export.generated", entity_type="bpjs_export",
        entity_id=export_id, tenant_id=tenant_id, branch_id=branch_id,
        metadata={"export_period": year_month, "record_count": len(rows)},
    )
    db.commit()

    download_url = (
        f"/api/v1/modules/healthcare_billing/branches/{branch_id}"
        f"/bpjs-exports/{export_id}/download"
    )
    return BPJSExportResponse(
        id=export_id, tenant_id=tenant_id, branch_id=branch_id,
        export_period=year_month, status="generated",
        record_count=len(rows), total_amount=total_amount,
        generated_at=now, download_url=download_url, created_at=now,
    )


@router.get(
    "/api/v1/modules/healthcare_billing/branches/{branch_id}/bpjs-exports/{export_id}/download",
)
async def download_bpjs_export(
    branch_id: str,
    export_id: str,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    _role=Depends(has_hc_permission(_BILLING_WRITE_ROLES)),
):
    """Download BPJS export as CSV. Auth: billing_staff, branch_manager."""
    tenant_id = _resolve_tenant(request)
    row = db.execute(
        text(
            "SELECT export_period, file_reference FROM hcb_bpjs_exports "
            "WHERE id = :id AND branch_id = :bid AND tenant_id = :tid"
        ),
        {"id": export_id, "bid": branch_id, "tid": tenant_id},
    ).mappings().fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    if not row["file_reference"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not available")

    csv_bytes = base64.b64decode(row["file_reference"])
    filename = f"bpjs_export_{branch_id}_{row['export_period']}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
