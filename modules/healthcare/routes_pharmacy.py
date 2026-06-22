"""
Healthcare Pharmacy routes — Sprint 7.

Endpoints
---------
Staff (branch-scoped via healthcare_branch_session):
  Medication catalog  — CRUD + stock adjustment
  Drug interactions   — check + add
  Prescriptions       — create, list, get, dispense, cancel

Patient-facing (patient JWT):
  GET /api/v1/patients/me/prescriptions
  GET /api/v1/patients/me/prescriptions/{prescription_id}

Sandbox rules:
  - Only imports from modules.sdk.* or modules.healthcare.sdk.*
  - No backend.app imports (patient_auth.py already wraps decode_token)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.healthcare.sdk.branch_scope import healthcare_branch_session
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.patient_auth import get_current_patient
from modules.healthcare.sdk.phi_audit import write_phi_read_audit, write_event_audit
from modules.healthcare.schemas.pharmacy import (
    DispenseRequest,
    DispenseResponse,
    DrugInteractionCheckRequest,
    DrugInteractionCheckResponse,
    DrugInteractionCreate,
    DrugInteractionItem,
    DrugInteractionResponse,
    MedicationCreate,
    MedicationListResponse,
    MedicationResponse,
    MedicationUpdate,
    PatientPrescriptionDetail,
    PatientPrescriptionSummary,
    PrescriptionCreate,
    PrescriptionLineResponse,
    PrescriptionResponse,
    StockAdjustRequest,
)

router = APIRouter(tags=["pharmacy"])

_PREFIX = "/api/v1/modules/healthcare_pharmacy"


# ===========================================================================
# Internal helpers
# ===========================================================================

def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


def _tenant_id(current_user) -> str:
    return str(current_user.tenant_id) if hasattr(current_user, "tenant_id") else ""


def _get_medication_or_404(
    db: Session, med_id: str, tenant_id: str, branch_id: str
):
    row = db.execute(
        text(
            "SELECT id, tenant_id, branch_id, name, generic_name, brand_name, "
            "category, form, strength, unit, stock_quantity, minimum_stock, "
            "unit_price, currency, is_active, created_at, updated_at "
            "FROM hcp_medications "
            "WHERE id = :mid AND tenant_id = :tid AND branch_id = :bid"
        ),
        {"mid": med_id, "tid": tenant_id, "bid": branch_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Medication not found")
    return row


def _row_to_med(row) -> MedicationResponse:
    return MedicationResponse(
        id=row[0],
        tenant_id=row[1],
        branch_id=row[2],
        name=row[3],
        generic_name=row[4],
        brand_name=row[5],
        category=row[6],
        form=row[7],
        strength=row[8],
        unit=row[9],
        stock_quantity=row[10],
        minimum_stock=row[11],
        unit_price=float(row[12]),
        currency=row[13],
        is_active=row[14],
        is_low_stock=row[10] <= row[11],
        created_at=row[15],
        updated_at=row[16],
    )


def _get_prescription_or_404(
    db: Session, prescription_id: str, tenant_id: str, branch_id: str
):
    row = db.execute(
        text(
            "SELECT id, tenant_id, branch_id, encounter_id, patient_id, provider_id, "
            "status, notes, created_at, updated_at "
            "FROM hcp_prescriptions "
            "WHERE id = :pid AND tenant_id = :tid AND branch_id = :bid"
        ),
        {"pid": prescription_id, "tid": tenant_id, "bid": branch_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return row


def _get_prescription_lines(db: Session, prescription_id: str) -> list:
    return db.execute(
        text(
            "SELECT pl.id, pl.medication_id, m.name, m.form, m.strength, "
            "pl.quantity, pl.dosage_instructions, pl.days_supply, "
            "pl.dispensed_quantity, pl.status "
            "FROM hcp_prescription_lines pl "
            "JOIN hcp_medications m ON m.id = pl.medication_id "
            "WHERE pl.prescription_id = :pid"
        ),
        {"pid": prescription_id},
    ).fetchall()


def _row_to_prescription(
    row, lines: list, interactions: Optional[list] = None
) -> PrescriptionResponse:
    line_responses = [
        PrescriptionLineResponse(
            id=ln[0],
            medication_id=ln[1],
            medication_name=ln[2],
            medication_form=ln[3],
            medication_strength=ln[4],
            quantity=ln[5],
            dosage_instructions=ln[6],
            days_supply=ln[7],
            dispensed_quantity=ln[8],
            status=ln[9],
        )
        for ln in lines
    ]
    return PrescriptionResponse(
        id=row[0],
        tenant_id=row[1],
        branch_id=row[2],
        encounter_id=row[3],
        patient_id=row[4],
        provider_id=row[5],
        status=row[6],
        notes=row[7],
        created_at=row[8],
        updated_at=row[9],
        lines=line_responses,
        interaction_warnings=[DrugInteractionItem(**i) for i in (interactions or [])],
    )


def _check_interactions(
    db: Session, medication_ids: List[str], tenant_id: str
) -> List[dict]:
    """Return all known interactions between any pair in medication_ids."""
    if len(medication_ids) < 2:
        return []

    placeholders = ", ".join(f":mid_{i}" for i in range(len(medication_ids)))
    params: dict = {"tid": tenant_id}
    for i, mid in enumerate(medication_ids):
        params[f"mid_{i}"] = mid

    rows = db.execute(
        text(
            f"SELECT di.id, di.medication_a_id, ma.name, "
            f"di.medication_b_id, mb.name, "
            f"di.severity, di.description, di.source "
            f"FROM hcp_drug_interactions di "
            f"JOIN hcp_medications ma ON ma.id = di.medication_a_id "
            f"JOIN hcp_medications mb ON mb.id = di.medication_b_id "
            f"WHERE di.tenant_id = :tid "
            f"AND ("
            f"  (di.medication_a_id IN ({placeholders}) AND di.medication_b_id IN ({placeholders}))"
            f")"
        ),
        params,
    ).fetchall()

    return [
        {
            "id": r[0],
            "medication_a_id": r[1],
            "medication_a_name": r[2],
            "medication_b_id": r[3],
            "medication_b_name": r[4],
            "severity": r[5],
            "description": r[6],
            "source": r[7],
        }
        for r in rows
    ]


# ===========================================================================
# Medication catalog
# ===========================================================================

@router.post(
    _PREFIX + "/branches/{branch_id}/medications",
    response_model=MedicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_medication(
    branch_id: str,
    payload: MedicationCreate,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(
        has_hc_permission([HCRole.pharmacist, HCRole.branch_manager, HCRole.clinic_owner])
    ),
):
    tid = _tenant_id(current_user)
    med_id = _new_id()
    now = _now()

    db.execute(
        text(
            "INSERT INTO hcp_medications "
            "(id, tenant_id, branch_id, name, generic_name, brand_name, category, form, "
            "strength, unit, stock_quantity, minimum_stock, unit_price, currency, is_active, "
            "created_at, updated_at) "
            "VALUES (:id, :tid, :bid, :name, :gname, :bname, :cat, :form, "
            ":strength, :unit, :stock, :min_stock, :price, :currency, :active, :now, :now)"
        ),
        {
            "id": med_id, "tid": tid, "bid": branch_id,
            "name": payload.name, "gname": payload.generic_name,
            "bname": payload.brand_name, "cat": payload.category,
            "form": payload.form, "strength": payload.strength,
            "unit": payload.unit, "stock": payload.stock_quantity,
            "min_stock": payload.minimum_stock, "price": payload.unit_price,
            "currency": payload.currency, "active": payload.is_active,
            "now": now,
        },
    )
    write_event_audit(
        db=db, actor_id=str(current_user.id), actor_type="staff",
        event_type="medication.created", entity_type="medication",
        entity_id=med_id, tenant_id=tid, branch_id=branch_id,
        source_module="healthcare_pharmacy",
    )
    db.commit()

    return _row_to_med(_get_medication_or_404(db, med_id, tid, branch_id))


@router.get(
    _PREFIX + "/branches/{branch_id}/medications",
    response_model=MedicationListResponse,
)
def list_medications(
    branch_id: str,
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    low_stock: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(
        has_hc_permission([HCRole.pharmacist, HCRole.doctor, HCRole.branch_manager, HCRole.clinic_owner])
    ),
):
    tid = _tenant_id(current_user)
    where = ["tenant_id = :tid", "branch_id = :bid"]
    params: dict = {"tid": tid, "bid": branch_id}

    if category is not None:
        where.append("category = :cat")
        params["cat"] = category
    if is_active is not None:
        where.append("is_active = :active")
        params["active"] = is_active
    if low_stock:
        where.append("stock_quantity <= minimum_stock")

    w = " AND ".join(where)
    total = db.execute(text(f"SELECT COUNT(*) FROM hcp_medications WHERE {w}"), params).scalar()

    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size
    rows = db.execute(
        text(
            f"SELECT id, tenant_id, branch_id, name, generic_name, brand_name, "
            f"category, form, strength, unit, stock_quantity, minimum_stock, "
            f"unit_price, currency, is_active, created_at, updated_at "
            f"FROM hcp_medications WHERE {w} ORDER BY name ASC LIMIT :limit OFFSET :offset"
        ),
        params,
    ).fetchall()

    return MedicationListResponse(
        items=[_row_to_med(r) for r in rows],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.put(
    _PREFIX + "/branches/{branch_id}/medications/{med_id}",
    response_model=MedicationResponse,
)
def update_medication(
    branch_id: str,
    med_id: str,
    payload: MedicationUpdate,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(
        has_hc_permission([HCRole.pharmacist, HCRole.branch_manager, HCRole.clinic_owner])
    ),
):
    tid = _tenant_id(current_user)
    _get_medication_or_404(db, med_id, tid, branch_id)  # 404 guard

    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_parts = [f"{k} = :{k}" for k in fields] + ["updated_at = :now"]
    params: dict = {**fields, "now": _now(), "mid": med_id, "tid": tid, "bid": branch_id}

    db.execute(
        text(
            f"UPDATE hcp_medications SET {', '.join(set_parts)} "
            f"WHERE id = :mid AND tenant_id = :tid AND branch_id = :bid"
        ),
        params,
    )
    write_event_audit(
        db=db, actor_id=str(current_user.id), actor_type="staff",
        event_type="medication.updated", entity_type="medication",
        entity_id=med_id, tenant_id=tid, branch_id=branch_id,
        source_module="healthcare_pharmacy",
        metadata={"fields_updated": list(fields.keys())},
    )
    db.commit()

    return _row_to_med(_get_medication_or_404(db, med_id, tid, branch_id))


@router.post(
    _PREFIX + "/branches/{branch_id}/medications/{med_id}/stock-adjust",
    response_model=MedicationResponse,
)
def adjust_stock(
    branch_id: str,
    med_id: str,
    payload: StockAdjustRequest,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(
        has_hc_permission([HCRole.pharmacist, HCRole.branch_manager, HCRole.clinic_owner])
    ),
):
    tid = _tenant_id(current_user)

    # CR-002 fix: use SELECT FOR UPDATE to check stock, then atomic DB arithmetic UPDATE
    # to prevent race condition between concurrent stock adjustments.
    med_row = db.execute(
        text(
            "SELECT id, stock_quantity FROM hcp_medications "
            "WHERE id = :mid AND tenant_id = :tid AND branch_id = :bid FOR UPDATE"
        ),
        {"mid": med_id, "tid": tid, "bid": branch_id},
    ).fetchone()
    if not med_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    if med_row[1] + payload.adjustment < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Stock cannot go below zero (current: {med_row[1]}, adjustment: {payload.adjustment})",
        )

    db.execute(
        text(
            "UPDATE hcp_medications "
            "SET stock_quantity = stock_quantity + :adj, updated_at = :now "
            "WHERE id = :mid AND tenant_id = :tid AND branch_id = :bid"
        ),
        {"adj": payload.adjustment, "now": _now(), "mid": med_id, "tid": tid, "bid": branch_id},
    )
    new_stock = med_row[1] + payload.adjustment
    write_event_audit(
        db=db, actor_id=str(current_user.id), actor_type="staff",
        event_type="medication.stock_adjusted", entity_type="medication",
        entity_id=med_id, tenant_id=tid, branch_id=branch_id,
        source_module="healthcare_pharmacy",
        metadata={"adjustment": payload.adjustment, "reason": payload.reason, "new_stock": new_stock},
    )
    db.commit()

    return _row_to_med(_get_medication_or_404(db, med_id, tid, branch_id))


# ===========================================================================
# Drug interactions
# ===========================================================================

@router.post(
    _PREFIX + "/branches/{branch_id}/interactions/check",
    response_model=DrugInteractionCheckResponse,
)
def check_interactions(
    branch_id: str,
    payload: DrugInteractionCheckRequest,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(
        has_hc_permission([HCRole.doctor, HCRole.pharmacist, HCRole.clinic_owner])
    ),
):
    tid = _tenant_id(current_user)
    interactions = _check_interactions(db, payload.medication_ids, tid)
    return DrugInteractionCheckResponse(
        interactions=[DrugInteractionItem(**i) for i in interactions],
        has_severe=any(i["severity"] == "severe" for i in interactions),
        medication_ids_checked=payload.medication_ids,
    )


@router.post(
    _PREFIX + "/branches/{branch_id}/interactions",
    response_model=DrugInteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_interaction(
    branch_id: str,
    payload: DrugInteractionCreate,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(
        has_hc_permission([HCRole.pharmacist, HCRole.branch_manager, HCRole.clinic_owner])
    ),
):
    tid = _tenant_id(current_user)
    # Canonical ordering to prevent duplicates
    a_id, b_id = sorted([payload.medication_a_id, payload.medication_b_id])
    interaction_id = _new_id()
    now = _now()

    try:
        db.execute(
            text(
                "INSERT INTO hcp_drug_interactions "
                "(id, tenant_id, medication_a_id, medication_b_id, severity, "
                "description, source, created_at) "
                "VALUES (:id, :tid, :a_id, :b_id, :severity, :desc, :source, :now)"
            ),
            {
                "id": interaction_id, "tid": tid, "a_id": a_id, "b_id": b_id,
                "severity": payload.severity, "desc": payload.description,
                "source": payload.source, "now": now,
            },
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        if "uq_hcp_drug_interactions_pair" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Interaction between these medications already exists",
            )
        raise

    return DrugInteractionResponse(
        id=interaction_id, tenant_id=tid,
        medication_a_id=a_id, medication_b_id=b_id,
        severity=payload.severity, description=payload.description,
        source=payload.source, created_at=now,
    )


# ===========================================================================
# Prescriptions
# ===========================================================================

@router.post(
    _PREFIX + "/branches/{branch_id}/prescriptions",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_prescription(
    branch_id: str,
    payload: PrescriptionCreate,
    force: bool = Query(False, description="Override severe interaction block"),
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(has_hc_permission([HCRole.doctor, HCRole.clinic_owner])),
):
    tid = _tenant_id(current_user)

    # Resolve encounter → patient_id, provider_id
    encounter = db.execute(
        text(
            "SELECT id, patient_id, provider_id FROM hc_encounters "
            "WHERE id = :eid AND tenant_id = :tid AND branch_id = :bid"
        ),
        {"eid": payload.encounter_id, "tid": tid, "bid": branch_id},
    ).fetchone()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found in this branch")

    patient_id = str(encounter[1])
    provider_id = str(encounter[2])

    # Drug interaction check
    med_ids = [ln.medication_id for ln in payload.lines]
    interactions = _check_interactions(db, med_ids, tid)
    severe = [i for i in interactions if i["severity"] == "severe"]

    if severe and not force:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": (
                    "Severe drug interactions detected. "
                    "Add ?force=true to override and acknowledge."
                ),
                "severe_interactions": severe,
            },
        )

    notes = None
    if severe and force:
        names = [f"{i['medication_a_name']} + {i['medication_b_name']}" for i in severe]
        notes = f"[OVERRIDE] Severe interactions acknowledged by prescriber: {'; '.join(names)}"

    rx_id = _new_id()
    now = _now()

    db.execute(
        text(
            "INSERT INTO hcp_prescriptions "
            "(id, tenant_id, branch_id, encounter_id, patient_id, provider_id, "
            "status, notes, created_at, updated_at) "
            "VALUES (:id, :tid, :bid, :eid, :pat, :prov, 'pending', :notes, :now, :now)"
        ),
        {
            "id": rx_id, "tid": tid, "bid": branch_id,
            "eid": payload.encounter_id, "pat": patient_id,
            "prov": provider_id, "notes": notes, "now": now,
        },
    )

    for ln in payload.lines:
        db.execute(
            text(
                "INSERT INTO hcp_prescription_lines "
                "(id, tenant_id, prescription_id, medication_id, quantity, "
                "dosage_instructions, days_supply, dispensed_quantity, status) "
                "VALUES (:id, :tid, :rxid, :mid, :qty, :dosage, :days, 0, 'pending')"
            ),
            {
                "id": _new_id(), "tid": tid, "rxid": rx_id,
                "mid": ln.medication_id, "qty": ln.quantity,
                "dosage": ln.dosage_instructions, "days": ln.days_supply,
            },
        )

    write_event_audit(
        db=db, actor_id=str(current_user.id), actor_type="staff",
        event_type="prescription.created", entity_type="prescription",
        entity_id=rx_id, tenant_id=tid, branch_id=branch_id,
        source_module="healthcare_pharmacy",
        metadata={
            "encounter_id": payload.encounter_id,
            "medication_count": len(payload.lines),
            "interaction_override": force and bool(severe),
        },
    )
    db.commit()

    row = _get_prescription_or_404(db, rx_id, tid, branch_id)
    lines = _get_prescription_lines(db, rx_id)
    return _row_to_prescription(row, lines, interactions)


@router.get(
    _PREFIX + "/branches/{branch_id}/prescriptions",
    response_model=dict,
)
def list_prescriptions(
    branch_id: str,
    prescription_status: Optional[str] = Query(None, alias="status"),
    encounter_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(
        has_hc_permission([HCRole.pharmacist, HCRole.doctor, HCRole.branch_manager, HCRole.clinic_owner])
    ),
):
    tid = _tenant_id(current_user)
    where = ["tenant_id = :tid", "branch_id = :bid"]
    params: dict = {"tid": tid, "bid": branch_id}

    if prescription_status:
        where.append("status = :status")
        params["status"] = prescription_status
    if encounter_id:
        where.append("encounter_id = :eid")
        params["eid"] = encounter_id
    if date_from:
        where.append("created_at >= :date_from")
        params["date_from"] = date_from
    if date_to:
        where.append("created_at <= :date_to")
        params["date_to"] = date_to

    w = " AND ".join(where)
    total = db.execute(text(f"SELECT COUNT(*) FROM hcp_prescriptions WHERE {w}"), params).scalar()

    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size
    rows = db.execute(
        text(
            f"SELECT id, tenant_id, branch_id, encounter_id, patient_id, provider_id, "
            f"status, notes, created_at, updated_at "
            f"FROM hcp_prescriptions WHERE {w} "
            f"ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        ),
        params,
    ).fetchall()

    items = [_row_to_prescription(r, _get_prescription_lines(db, r[0])) for r in rows]
    return {
        "items": [i.model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    _PREFIX + "/branches/{branch_id}/prescriptions/{prescription_id}",
    response_model=PrescriptionResponse,
)
def get_prescription(
    branch_id: str,
    prescription_id: str,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(
        has_hc_permission([HCRole.pharmacist, HCRole.doctor, HCRole.clinic_owner])
    ),
):
    tid = _tenant_id(current_user)
    row = _get_prescription_or_404(db, prescription_id, tid, branch_id)

    write_phi_read_audit(
        db=db, actor_id=str(current_user.id), actor_type="staff",
        entity_type="prescription", entity_id=prescription_id,
        tenant_id=tid, branch_id=branch_id, source_module="healthcare_pharmacy",
    )
    db.commit()

    lines = _get_prescription_lines(db, prescription_id)
    return _row_to_prescription(row, lines)


@router.post(
    _PREFIX + "/branches/{branch_id}/prescriptions/{prescription_id}/dispense",
    response_model=DispenseResponse,
)
def dispense_prescription(
    branch_id: str,
    prescription_id: str,
    payload: DispenseRequest,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(has_hc_permission([HCRole.pharmacist, HCRole.clinic_owner])),
):
    tid = _tenant_id(current_user)
    prow = _get_prescription_or_404(db, prescription_id, tid, branch_id)

    if prow[6] == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot dispense a cancelled prescription",
        )

    dispensing_ids: List[str] = []
    now = _now()

    for line_req in payload.lines:
        # SELECT FOR UPDATE on prescription line
        line = db.execute(
            text(
                "SELECT id, medication_id, quantity, dispensed_quantity, status "
                "FROM hcp_prescription_lines "
                "WHERE id = :lid AND prescription_id = :rxid FOR UPDATE"
            ),
            {"lid": line_req.prescription_line_id, "rxid": prescription_id},
        ).fetchone()

        if not line:
            raise HTTPException(
                status_code=404,
                detail=f"Prescription line {line_req.prescription_line_id} not found",
            )

        remaining = line[2] - line[3]
        if line_req.quantity_dispensed > remaining:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Cannot dispense {line_req.quantity_dispensed} — "
                    f"only {remaining} remaining on line {line_req.prescription_line_id}"
                ),
            )

        # SELECT FOR UPDATE on medication stock
        med = db.execute(
            text(
                "SELECT id, stock_quantity FROM hcp_medications "
                "WHERE id = :mid AND tenant_id = :tid FOR UPDATE"
            ),
            {"mid": line[1], "tid": tid},
        ).fetchone()

        if not med:
            raise HTTPException(status_code=404, detail=f"Medication {line[1]} not found")

        new_stock = med[1] - line_req.quantity_dispensed
        if new_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Insufficient stock for medication {line[1]}: "
                    f"have {med[1]}, need {line_req.quantity_dispensed}"
                ),
            )

        # Decrement stock
        db.execute(
            text(
                "UPDATE hcp_medications SET stock_quantity = :ns, updated_at = :now "
                "WHERE id = :mid AND tenant_id = :tid"
            ),
            {"ns": new_stock, "now": now, "mid": line[1], "tid": tid},
        )

        # Update line
        new_dispensed = line[3] + line_req.quantity_dispensed
        line_status = "dispensed" if new_dispensed >= line[2] else "pending"
        db.execute(
            text(
                "UPDATE hcp_prescription_lines "
                "SET dispensed_quantity = :nd, status = :ls "
                "WHERE id = :lid"
            ),
            {"nd": new_dispensed, "ls": line_status, "lid": line_req.prescription_line_id},
        )

        # Dispensing record
        disp_id = _new_id()
        db.execute(
            text(
                "INSERT INTO hcp_dispensing_records "
                "(id, tenant_id, branch_id, prescription_id, prescription_line_id, "
                "medication_id, quantity_dispensed, dispensed_by, dispensed_at, "
                "batch_number, expiry_date, created_at) "
                "VALUES (:id, :tid, :bid, :rxid, :lid, :mid, :qty, :by, :at, "
                ":batch, :expiry, :now)"
            ),
            {
                "id": disp_id, "tid": tid, "bid": branch_id,
                "rxid": prescription_id, "lid": line_req.prescription_line_id,
                "mid": line[1], "qty": line_req.quantity_dispensed,
                "by": str(current_user.id), "at": now,
                "batch": line_req.batch_number, "expiry": line_req.expiry_date,
                "now": now,
            },
        )
        dispensing_ids.append(disp_id)

    # Recompute prescription status
    all_lines = db.execute(
        text("SELECT dispensed_quantity, quantity FROM hcp_prescription_lines WHERE prescription_id = :rxid"),
        {"rxid": prescription_id},
    ).fetchall()

    all_fully_dispensed = all(ln[0] >= ln[1] for ln in all_lines)
    any_partially = any(ln[0] > 0 for ln in all_lines)

    if all_fully_dispensed:
        new_rx_status = "dispensed"
    elif any_partially:
        new_rx_status = "partially_dispensed"
    else:
        new_rx_status = "pending"

    db.execute(
        text(
            "UPDATE hcp_prescriptions SET status = :s, updated_at = :now "
            "WHERE id = :rxid AND tenant_id = :tid"
        ),
        {"s": new_rx_status, "now": now, "rxid": prescription_id, "tid": tid},
    )
    write_event_audit(
        db=db, actor_id=str(current_user.id), actor_type="staff",
        event_type="prescription.dispensed", entity_type="prescription",
        entity_id=prescription_id, tenant_id=tid, branch_id=branch_id,
        source_module="healthcare_pharmacy",
        metadata={
            "lines_dispensed": len(dispensing_ids),
            "dispensing_record_ids": dispensing_ids,
            "new_status": new_rx_status,
        },
    )
    db.commit()

    return DispenseResponse(
        prescription_id=prescription_id,
        prescription_status=new_rx_status,
        lines_dispensed=len(dispensing_ids),
        records_created=dispensing_ids,
    )


@router.delete(
    _PREFIX + "/branches/{branch_id}/prescriptions/{prescription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cancel_prescription(
    branch_id: str,
    prescription_id: str,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(
        has_hc_permission([HCRole.doctor, HCRole.branch_manager, HCRole.clinic_owner])
    ),
):
    tid = _tenant_id(current_user)
    caller_id = str(current_user.id)
    row = _get_prescription_or_404(db, prescription_id, tid, branch_id)

    if row[6] != "pending":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Only pending prescriptions can be cancelled (current: {row[6]})",
        )

    # Doctors may only cancel their own prescriptions (provider_id is row[5])
    from modules.healthcare.sdk.hc_permissions import get_caller_hc_role
    from modules.sdk.dependencies import tenant_scoped_session
    caller_role = get_caller_hc_role(db=db, user_id=caller_id, tenant_id=tid, branch_id=branch_id)
    if caller_role == HCRole.doctor and str(row[5]) != caller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctors can only cancel their own prescriptions",
        )

    now = _now()
    db.execute(
        text(
            "UPDATE hcp_prescriptions SET status = 'cancelled', updated_at = :now "
            "WHERE id = :rxid AND tenant_id = :tid"
        ),
        {"now": now, "rxid": prescription_id, "tid": tid},
    )
    db.execute(
        text(
            "UPDATE hcp_prescription_lines SET status = 'cancelled' "
            "WHERE prescription_id = :rxid AND status = 'pending'"
        ),
        {"rxid": prescription_id},
    )
    write_event_audit(
        db=db, actor_id=caller_id, actor_type="staff",
        event_type="prescription.cancelled", entity_type="prescription",
        entity_id=prescription_id, tenant_id=tid, branch_id=branch_id,
        source_module="healthcare_pharmacy",
    )
    db.commit()


# ===========================================================================
# Patient-facing endpoints
# ===========================================================================

# CR-007 fix: removed _patient_db() helper that returned Depends(...)
# Endpoints now use Depends(tenant_scoped_session) directly.


@router.get(
    "/api/v1/patients/me/prescriptions",
)
def patient_list_prescriptions(
    db: Session = Depends(tenant_scoped_session),
    patient=Depends(get_current_patient),
):
    patient_id = str(patient.patient_id)
    # Patient JWT has no tenant_id claim in v1; phi audit uses empty string
    tenant_id = getattr(patient, "tenant_id", "") or ""

    rows = db.execute(
        text(
            "SELECT p.id, p.status, e.created_at AS encounter_date, b.name AS clinic_name "
            "FROM hcp_prescriptions p "
            "JOIN hc_encounters e ON e.id = p.encounter_id "
            "JOIN hc_branches b ON b.id = p.branch_id "
            "WHERE p.patient_id = :pat AND p.status != 'cancelled' "
            "ORDER BY p.created_at DESC"
        ),
        {"pat": patient_id},
    ).fetchall()

    result = []
    for row in rows:
        med_names = db.execute(
            text(
                "SELECT m.name FROM hcp_prescription_lines pl "
                "JOIN hcp_medications m ON m.id = pl.medication_id "
                "WHERE pl.prescription_id = :pid"
            ),
            {"pid": row[0]},
        ).fetchall()
        result.append(
            PatientPrescriptionSummary(
                prescription_id=row[0],
                status=row[1],
                encounter_date=row[2],
                clinic_name=row[3],
                medication_names=[r[0] for r in med_names],
            )
        )

    write_phi_read_audit(
        db=db, actor_id=patient_id, actor_type="patient",
        entity_type="prescription_list", entity_id=patient_id,
        tenant_id=tenant_id, source_module="healthcare_pharmacy",
    )
    db.commit()

    return [r.model_dump() for r in result]


@router.get(
    "/api/v1/patients/me/prescriptions/{prescription_id}",
)
def patient_get_prescription(
    prescription_id: str,
    db: Session = Depends(tenant_scoped_session),
    patient=Depends(get_current_patient),
):
    patient_id = str(patient.patient_id)
    tenant_id = getattr(patient, "tenant_id", "") or ""

    row = db.execute(
        text(
            "SELECT p.id, p.status, e.created_at AS encounter_date, b.name AS clinic_name "
            "FROM hcp_prescriptions p "
            "JOIN hc_encounters e ON e.id = p.encounter_id "
            "JOIN hc_branches b ON b.id = p.branch_id "
            "WHERE p.id = :pid AND p.patient_id = :pat AND p.status != 'cancelled'"
        ),
        {"pid": prescription_id, "pat": patient_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Prescription not found")

    lines_raw = db.execute(
        text(
            "SELECT pl.id, pl.medication_id, m.name, m.form, m.strength, "
            "pl.quantity, pl.dosage_instructions, pl.days_supply, "
            "pl.dispensed_quantity, pl.status "
            "FROM hcp_prescription_lines pl "
            "JOIN hcp_medications m ON m.id = pl.medication_id "
            "WHERE pl.prescription_id = :pid"
        ),
        {"pid": prescription_id},
    ).fetchall()

    write_phi_read_audit(
        db=db, actor_id=patient_id, actor_type="patient",
        entity_type="prescription", entity_id=prescription_id,
        tenant_id=tenant_id, source_module="healthcare_pharmacy",
    )
    db.commit()

    return PatientPrescriptionDetail(
        prescription_id=row[0],
        status=row[1],
        encounter_date=row[2],
        clinic_name=row[3],
        lines=[
            PrescriptionLineResponse(
                id=ln[0], medication_id=ln[1],
                medication_name=ln[2], medication_form=ln[3], medication_strength=ln[4],
                quantity=ln[5], dosage_instructions=ln[6], days_supply=ln[7],
                dispensed_quantity=ln[8], status=ln[9],
            )
            for ln in lines_raw
        ],
    )
