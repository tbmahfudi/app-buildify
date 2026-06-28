"""
Healthcare Laboratory routes — Sprint 8.

Endpoints
---------
Staff (branch-scoped via healthcare_branch_session):
  Test panel catalog  — create, list, update
  Lab orders          — create, list, get, status update
  Specimen collection — record specimen for an order
  Results             — batch enter, release, get

Patient-facing (patient JWT):
  GET /api/v1/patients/me/lab-orders
  GET /api/v1/patients/me/lab-orders/{order_id}/results

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
from modules.sdk.dependencies import tenant_scoped_session
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.patient_auth import get_current_patient, get_patient_db
from modules.healthcare.sdk.phi_audit import write_phi_read_audit, write_event_audit
from modules.healthcare.sdk.notification_service import NotificationService
from modules.healthcare.schemas.lab import (
    LabOrderCreate,
    LabOrderListItem,
    LabOrderListResponse,
    LabOrderResponse,
    LabOrderStatusUpdate,
    OrderLineResponse,
    PatientLabOrderSummary,
    PatientLabResultItem,
    PatientLabResultsResponse,
    ResultResponse,
    ResultsBatchCreate,
    SpecimenCreate,
    SpecimenResponse,
    TestPanelCreate,
    TestPanelListResponse,
    TestPanelResponse,
    TestPanelUpdate,
)

router = APIRouter(tags=["laboratory"])

_PREFIX = "/api/v1/modules/healthcare_lab"
_PATIENT_PREFIX = "/api/v1/patients/me"

# ---------------------------------------------------------------------------
# Valid order status transitions
# ---------------------------------------------------------------------------
_VALID_TRANSITIONS: dict[str, set] = {
    "ordered": {"specimen_collected", "cancelled"},
    "specimen_collected": {"processing"},
    "processing": {"resulted"},
    "resulted": set(),
    "cancelled": set(),
}


# ===========================================================================
# Internal helpers
# ===========================================================================

def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


def _short_uuid() -> str:
    """Generate a short barcode-friendly ID (first 8 chars of a UUID)."""
    return str(uuid.uuid4()).replace("-", "")[:12].upper()


def _tenant_branch(db: Session):
    """Extract tenant_id and branch_id from session PG vars."""
    row = db.execute(
        text(
            "SELECT current_setting('app.tenant_id', true) AS tid, "
            "current_setting('app.branch_id', true) AS bid"
        )
    ).fetchone()
    return (row[0] if row else ""), (row[1] if row else "")


def _get_panel_or_404(db: Session, panel_id: str, tenant_id: str) -> dict:
    row = db.execute(
        text(
            "SELECT id, tenant_id, branch_id, code, name, category, "
            "turnaround_hours, unit_price, currency, sample_type, "
            "requires_fasting, is_active, created_at, updated_at "
            "FROM hcl_test_panels WHERE id = :id AND tenant_id = :tid LIMIT 1"
        ),
        {"id": panel_id, "tid": tenant_id},
    ).mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Test panel not found")
    return dict(row)


def _get_order_or_404(
    db: Session, order_id: str, tenant_id: str, branch_id: str
) -> dict:
    row = db.execute(
        text(
            "SELECT id, tenant_id, branch_id, encounter_id, patient_id, "
            "provider_id, status, priority, clinical_notes, created_at, updated_at "
            "FROM hcl_lab_orders "
            "WHERE id = :id AND tenant_id = :tid AND branch_id = :bid LIMIT 1"
        ),
        {"id": order_id, "tid": tenant_id, "bid": branch_id},
    ).mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Lab order not found")
    return dict(row)


def _get_order_lines(db: Session, order_id: str, tenant_id: str) -> list:
    rows = db.execute(
        text(
            "SELECT ol.id, ol.order_id, ol.test_panel_id, ol.status, "
            "tp.name AS test_panel_name "
            "FROM hcl_order_lines ol "
            "LEFT JOIN hcl_test_panels tp ON tp.id = ol.test_panel_id "
            "WHERE ol.order_id = :oid AND ol.tenant_id = :tid"
        ),
        {"oid": order_id, "tid": tenant_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def _get_specimen(db: Session, order_id: str) -> Optional[dict]:
    row = db.execute(
        text(
            "SELECT id, order_id, sample_type, collection_datetime, "
            "collected_by, barcode, notes, created_at "
            "FROM hcl_specimens WHERE order_id = :oid LIMIT 1"
        ),
        {"oid": order_id},
    ).mappings().one_or_none()
    return dict(row) if row else None


def _get_results(db: Session, order_id: str, tenant_id: str) -> list:
    rows = db.execute(
        text(
            "SELECT r.id, r.order_id, r.order_line_id, r.test_panel_id, "
            "tp.name AS test_panel_name, r.result_value, r.result_unit, "
            "r.reference_range, r.is_abnormal, r.is_critical, r.resulted_by, "
            "r.resulted_at, r.shared_with_patient, r.released_at, r.notes, r.created_at "
            "FROM hcl_results r "
            "LEFT JOIN hcl_test_panels tp ON tp.id = r.test_panel_id "
            "WHERE r.order_id = :oid AND r.tenant_id = :tid"
        ),
        {"oid": order_id, "tid": tenant_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def _build_order_response(db: Session, order: dict, tenant_id: str) -> dict:
    lines = _get_order_lines(db, order["id"], tenant_id)
    specimen = _get_specimen(db, order["id"])
    return {**order, "lines": lines, "specimen": specimen}


def _mask_patient_id(patient_id: str) -> str:
    """Return masked display: first 4 chars + *** — no PHI exposed in list views."""
    return f"{patient_id[:4]}***" if patient_id else "***"


def _get_provider_contact(db: Session, provider_id: str) -> Optional[dict]:
    """Fetch provider user_id for notification dispatch."""
    row = db.execute(
        text("SELECT user_id, tenant_id, branch_id FROM hc_providers WHERE id = :id LIMIT 1"),
        {"id": provider_id},
    ).mappings().one_or_none()
    return dict(row) if row else None


# ===========================================================================
# Test Panel Catalog
# ===========================================================================

@router.post(
    _PREFIX + "/branches/{branch_id}/test-panels",
    response_model=TestPanelResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_test_panel(
    branch_id: str,
    payload: TestPanelCreate,
    db: Session = Depends(healthcare_branch_session),
    _auth=Depends(
        has_hc_permission(
            [HCRole.lab_tech, HCRole.branch_manager, HCRole.clinic_owner]
        )
    ),
):
    """Create a new test panel in the branch catalog."""
    tenant_id, effective_branch_id = _tenant_branch(db)
    # Scope to the URL branch unless clinic owner
    use_branch = branch_id if effective_branch_id != "ALL" else branch_id

    # Check code uniqueness within tenant
    existing = db.execute(
        text(
            "SELECT id FROM hcl_test_panels "
            "WHERE tenant_id = :tid AND code = :code LIMIT 1"
        ),
        {"tid": tenant_id, "code": payload.code},
    ).fetchone()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Test panel code '{payload.code}' already exists for this tenant",
        )

    panel_id = _new_id()
    now = _now()
    db.execute(
        text(
            "INSERT INTO hcl_test_panels "
            "(id, tenant_id, branch_id, code, name, category, turnaround_hours, "
            "unit_price, currency, sample_type, requires_fasting, is_active, "
            "created_at, updated_at) "
            "VALUES (:id, :tid, :bid, :code, :name, :cat, :tah, :price, :cur, "
            ":stype, :fasting, :active, :ca, :ua)"
        ),
        dict(
            id=panel_id,
            tid=tenant_id,
            bid=use_branch,
            code=payload.code,
            name=payload.name,
            cat=payload.category,
            tah=payload.turnaround_hours,
            price=payload.unit_price,
            cur=payload.currency,
            stype=payload.sample_type,
            fasting=payload.requires_fasting,
            active=payload.is_active,
            ca=now,
            ua=now,
        ),
    )
    db.commit()
    return _get_panel_or_404(db, panel_id, tenant_id)


@router.get(
    _PREFIX + "/branches/{branch_id}/test-panels",
    response_model=TestPanelListResponse,
)
def list_test_panels(
    branch_id: str,
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    sample_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(healthcare_branch_session),
    _auth=Depends(
        has_hc_permission(
            [HCRole.lab_tech, HCRole.doctor, HCRole.branch_manager, HCRole.clinic_owner]
        )
    ),
):
    """List test panels with optional filters."""
    tenant_id, _ = _tenant_branch(db)

    where_clauses = ["tenant_id = :tid", "branch_id = :bid"]
    params: dict = {"tid": tenant_id, "bid": branch_id}

    if category is not None:
        where_clauses.append("category = :category")
        params["category"] = category
    if is_active is not None:
        where_clauses.append("is_active = :is_active")
        params["is_active"] = is_active
    if sample_type is not None:
        where_clauses.append("sample_type = :sample_type")
        params["sample_type"] = sample_type

    where_sql = " AND ".join(where_clauses)
    count_row = db.execute(
        text(f"SELECT COUNT(*) FROM hcl_test_panels WHERE {where_sql}"), params
    ).scalar()

    offset = (page - 1) * page_size
    rows = db.execute(
        text(
            f"SELECT id, tenant_id, branch_id, code, name, category, turnaround_hours, "
            f"unit_price, currency, sample_type, requires_fasting, is_active, "
            f"created_at, updated_at "
            f"FROM hcl_test_panels WHERE {where_sql} "
            f"ORDER BY name ASC LIMIT :limit OFFSET :offset"
        ),
        {**params, "limit": page_size, "offset": offset},
    ).mappings().all()

    return TestPanelListResponse(
        items=[TestPanelResponse(**dict(r)) for r in rows],
        total=count_row or 0,
        page=page,
        page_size=page_size,
    )


@router.put(
    _PREFIX + "/branches/{branch_id}/test-panels/{panel_id}",
    response_model=TestPanelResponse,
)
def update_test_panel(
    branch_id: str,
    panel_id: str,
    payload: TestPanelUpdate,
    db: Session = Depends(healthcare_branch_session),
    _auth=Depends(
        has_hc_permission([HCRole.lab_tech, HCRole.branch_manager, HCRole.clinic_owner])
    ),
):
    """Update a test panel."""
    tenant_id, _ = _tenant_branch(db)
    existing = _get_panel_or_404(db, panel_id, tenant_id)

    update_fields = payload.model_dump(exclude_none=True)
    if not update_fields:
        return TestPanelResponse(**existing)

    set_clauses = ", ".join(f"{k} = :{k}" for k in update_fields)
    update_fields["updated_at"] = _now()
    set_clauses += ", updated_at = :updated_at"
    update_fields["id"] = panel_id
    update_fields["tid"] = tenant_id

    db.execute(
        text(
            f"UPDATE hcl_test_panels SET {set_clauses} "
            f"WHERE id = :id AND tenant_id = :tid"
        ),
        update_fields,
    )
    db.commit()
    return _get_panel_or_404(db, panel_id, tenant_id)


# ===========================================================================
# Lab Orders
# ===========================================================================

@router.post(
    _PREFIX + "/branches/{branch_id}/orders",
    response_model=LabOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lab_order(
    branch_id: str,
    payload: LabOrderCreate,
    db: Session = Depends(healthcare_branch_session),
    _auth=Depends(has_hc_permission([HCRole.doctor, HCRole.clinic_owner])),
):
    """Doctor creates a lab order for an encounter."""
    tenant_id, effective_branch_id = _tenant_branch(db)
    use_branch = branch_id if effective_branch_id != "ALL" else branch_id

    # Validate encounter belongs to this branch
    encounter = db.execute(
        text(
            "SELECT id, patient_id, provider_id FROM hc_encounters "
            "WHERE id = :eid AND tenant_id = :tid AND branch_id = :bid LIMIT 1"
        ),
        {"eid": payload.encounter_id, "tid": tenant_id, "bid": use_branch},
    ).mappings().one_or_none()
    if not encounter:
        raise HTTPException(
            status_code=404,
            detail="Encounter not found in this branch",
        )

    # Validate all test panels exist
    for panel_id in payload.test_panel_ids:
        panel_row = db.execute(
            text(
                "SELECT id FROM hcl_test_panels "
                "WHERE id = :pid AND tenant_id = :tid AND is_active = true LIMIT 1"
            ),
            {"pid": panel_id, "tid": tenant_id},
        ).fetchone()
        if not panel_row:
            raise HTTPException(
                status_code=400,
                detail=f"Test panel {panel_id} not found or inactive",
            )

    order_id = _new_id()
    now = _now()

    db.execute(
        text(
            "INSERT INTO hcl_lab_orders "
            "(id, tenant_id, branch_id, encounter_id, patient_id, provider_id, "
            "status, priority, clinical_notes, created_at, updated_at) "
            "VALUES (:id, :tid, :bid, :eid, :pid, :provid, :status, :priority, "
            ":notes, :ca, :ua)"
        ),
        dict(
            id=order_id,
            tid=tenant_id,
            bid=use_branch,
            eid=payload.encounter_id,
            pid=str(encounter["patient_id"]),
            provid=str(encounter["provider_id"]),
            status="ordered",
            priority=payload.priority,
            notes=payload.clinical_notes,
            ca=now,
            ua=now,
        ),
    )

    # Create order lines
    for panel_id in payload.test_panel_ids:
        db.execute(
            text(
                "INSERT INTO hcl_order_lines (id, tenant_id, order_id, test_panel_id, status) "
                "VALUES (:id, :tid, :oid, :panel, :status)"
            ),
            dict(
                id=_new_id(),
                tid=tenant_id,
                oid=order_id,
                panel=panel_id,
                status="pending",
            ),
        )

    # Audit
    write_event_audit(
        db=db,
        actor_id=str(encounter["provider_id"]),
        actor_type="staff",
        event_type="lab_order.created",
        entity_type="lab_order",
        entity_id=order_id,
        tenant_id=tenant_id,
        branch_id=use_branch,
        source_module="healthcare_lab",
        metadata={"priority": payload.priority, "panel_count": len(payload.test_panel_ids)},
    )

    db.commit()
    order = _get_order_or_404(db, order_id, tenant_id, use_branch)
    return LabOrderResponse(**_build_order_response(db, order, tenant_id))


@router.get(
    _PREFIX + "/branches/{branch_id}/orders",
    response_model=LabOrderListResponse,
)
def list_lab_orders(
    branch_id: str,
    order_status: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(healthcare_branch_session),
    _auth=Depends(
        has_hc_permission(
            [HCRole.lab_tech, HCRole.doctor, HCRole.branch_manager, HCRole.clinic_owner]
        )
    ),
):
    """List lab orders with filters. Patient display is masked."""
    tenant_id, _ = _tenant_branch(db)

    where_clauses = ["o.tenant_id = :tid", "o.branch_id = :bid"]
    params: dict = {"tid": tenant_id, "bid": branch_id}

    if order_status:
        where_clauses.append("o.status = :status")
        params["status"] = order_status
    if priority:
        where_clauses.append("o.priority = :priority")
        params["priority"] = priority
    if date_from:
        where_clauses.append("o.created_at >= :date_from")
        params["date_from"] = date_from
    if date_to:
        where_clauses.append("o.created_at <= :date_to")
        params["date_to"] = date_to

    where_sql = " AND ".join(where_clauses)
    count_val = db.execute(
        text(f"SELECT COUNT(*) FROM hcl_lab_orders o WHERE {where_sql}"), params
    ).scalar()

    offset = (page - 1) * page_size
    rows = db.execute(
        text(
            f"SELECT o.id, o.encounter_id, o.patient_id, o.provider_id, "
            f"o.status, o.priority, o.created_at, o.updated_at, "
            f"(SELECT COUNT(*) FROM hcl_order_lines ol WHERE ol.order_id = o.id) AS panel_count "
            f"FROM hcl_lab_orders o WHERE {where_sql} "
            f"ORDER BY o.created_at DESC LIMIT :limit OFFSET :offset"
        ),
        {**params, "limit": page_size, "offset": offset},
    ).mappings().all()

    items = [
        LabOrderListItem(
            id=r["id"],
            encounter_id=r["encounter_id"],
            patient_id=r["patient_id"],
            patient_display=_mask_patient_id(r["patient_id"]),
            provider_id=r["provider_id"],
            status=r["status"],
            priority=r["priority"],
            panel_count=r["panel_count"] or 0,
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]

    return LabOrderListResponse(
        items=items,
        total=count_val or 0,
        page=page,
        page_size=page_size,
    )


@router.get(
    _PREFIX + "/branches/{branch_id}/orders/{order_id}",
    response_model=LabOrderResponse,
)
def get_lab_order(
    branch_id: str,
    order_id: str,
    db: Session = Depends(healthcare_branch_session),
    _auth=Depends(
        has_hc_permission([HCRole.lab_tech, HCRole.doctor, HCRole.clinic_owner])
    ),
):
    """Get full lab order with lines and specimen info. PHI audit logged."""
    tenant_id, _ = _tenant_branch(db)
    order = _get_order_or_404(db, order_id, tenant_id, branch_id)

    write_phi_read_audit(
        db=db,
        actor_id=str(_auth.id),
        actor_type="staff",
        entity_type="lab_order",
        entity_id=order_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        source_module="healthcare_lab",
    )

    return LabOrderResponse(**_build_order_response(db, order, tenant_id))


@router.put(
    _PREFIX + "/branches/{branch_id}/orders/{order_id}/status",
    response_model=LabOrderResponse,
)
def update_order_status(
    branch_id: str,
    order_id: str,
    payload: LabOrderStatusUpdate,
    db: Session = Depends(healthcare_branch_session),
    _auth=Depends(has_hc_permission([HCRole.lab_tech, HCRole.clinic_owner])),
):
    """Transition lab order status. Lab tech only."""
    tenant_id, _ = _tenant_branch(db)
    order = _get_order_or_404(db, order_id, tenant_id, branch_id)

    current_status = order["status"]
    new_status = payload.status

    allowed_next = _VALID_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_next:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot transition from '{current_status}' to '{new_status}'. "
                f"Allowed transitions: {sorted(allowed_next) or 'none'}"
            ),
        )

    db.execute(
        text(
            "UPDATE hcl_lab_orders SET status = :status, updated_at = :ua "
            "WHERE id = :id AND tenant_id = :tid"
        ),
        {"status": new_status, "ua": _now(), "id": order_id, "tid": tenant_id},
    )

    write_event_audit(
        db=db,
        actor_id=str(_auth.id),
        actor_type="staff",
        event_type="lab_order.status_changed",
        entity_type="lab_order",
        entity_id=order_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        source_module="healthcare_lab",
        metadata={"from_status": current_status, "to_status": new_status},
    )

    db.commit()
    order = _get_order_or_404(db, order_id, tenant_id, branch_id)
    return LabOrderResponse(**_build_order_response(db, order, tenant_id))


# ===========================================================================
# Specimen Collection
# ===========================================================================

@router.post(
    _PREFIX + "/branches/{branch_id}/orders/{order_id}/specimens",
    response_model=SpecimenResponse,
    status_code=status.HTTP_201_CREATED,
)
def collect_specimen(
    branch_id: str,
    order_id: str,
    payload: SpecimenCreate,
    db: Session = Depends(healthcare_branch_session),
    _auth=Depends(
        has_hc_permission([HCRole.lab_tech, HCRole.nurse, HCRole.clinic_owner])
    ),
):
    """Record specimen collection for an order."""
    tenant_id, _ = _tenant_branch(db)
    order = _get_order_or_404(db, order_id, tenant_id, branch_id)

    if order["status"] not in ("ordered",):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot collect specimen for order in status '{order['status']}'",
        )

    # Check if specimen already exists
    existing_specimen = _get_specimen(db, order_id)
    if existing_specimen:
        raise HTTPException(status_code=400, detail="Specimen already collected for this order")

    # Auto-generate barcode if not provided
    barcode = payload.barcode or _short_uuid()
    collection_dt = payload.collection_datetime or _now()

    specimen_id = _new_id()
    db.execute(
        text(
            "INSERT INTO hcl_specimens "
            "(id, tenant_id, branch_id, order_id, sample_type, collection_datetime, "
            "collected_by, barcode, notes, created_at) "
            "VALUES (:id, :tid, :bid, :oid, :stype, :cdt, :cby, :bc, :notes, :ca)"
        ),
        dict(
            id=specimen_id,
            tid=tenant_id,
            bid=branch_id,
            oid=order_id,
            stype=payload.sample_type,
            cdt=collection_dt,
            cby=None,  # lab_tech user_id not directly available here
            bc=barcode,
            notes=payload.notes,
            ca=_now(),
        ),
    )

    # Transition order to specimen_collected
    db.execute(
        text(
            "UPDATE hcl_lab_orders SET status = 'specimen_collected', updated_at = :ua "
            "WHERE id = :id AND tenant_id = :tid"
        ),
        {"ua": _now(), "id": order_id, "tid": tenant_id},
    )

    write_event_audit(
        db=db,
        actor_id=str(_auth.id),
        actor_type="staff",
        event_type="specimen.collected",
        entity_type="specimen",
        entity_id=specimen_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        source_module="healthcare_lab",
        metadata={"order_id": order_id, "barcode": barcode, "sample_type": payload.sample_type},
    )

    db.commit()
    specimen = _get_specimen(db, order_id)
    return SpecimenResponse(**specimen)


# ===========================================================================
# Results
# ===========================================================================

@router.post(
    _PREFIX + "/branches/{branch_id}/orders/{order_id}/results",
    response_model=list,
    status_code=status.HTTP_201_CREATED,
)
def enter_results(
    branch_id: str,
    order_id: str,
    payload: ResultsBatchCreate,
    db: Session = Depends(healthcare_branch_session),
    _auth=Depends(has_hc_permission([HCRole.lab_tech, HCRole.clinic_owner])),
):
    """Lab tech enters results for one or more order lines."""
    tenant_id, _ = _tenant_branch(db)
    order = _get_order_or_404(db, order_id, tenant_id, branch_id)

    # Validate order lines belong to this order
    lines = _get_order_lines(db, order_id, tenant_id)
    line_ids = {ln["id"] for ln in lines}
    panel_by_line = {ln["id"]: ln["test_panel_id"] for ln in lines}

    for entry in payload.results:
        if entry.order_line_id not in line_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Order line {entry.order_line_id} does not belong to this order",
            )

    now = _now()
    result_ids = []
    has_critical = False

    for entry in payload.results:
        test_panel_id = panel_by_line[entry.order_line_id]
        result_id = _new_id()
        result_ids.append(result_id)

        db.execute(
            text(
                "INSERT INTO hcl_results "
                "(id, tenant_id, order_id, order_line_id, test_panel_id, "
                "result_value, result_unit, reference_range, is_abnormal, is_critical, "
                "resulted_by, resulted_at, shared_with_patient, notes, created_at) "
                "VALUES (:id, :tid, :oid, :olid, :tpid, :rv, :ru, :rr, :abn, :crit, "
                ":rby, :rat, false, :notes, :ca)"
            ),
            dict(
                id=result_id,
                tid=tenant_id,
                oid=order_id,
                olid=entry.order_line_id,
                tpid=test_panel_id,
                rv=entry.result_value,
                ru=entry.result_unit,
                rr=entry.reference_range,
                abn=entry.is_abnormal,
                crit=entry.is_critical,
                rby=None,
                rat=now,
                notes=entry.notes,
                ca=now,
            ),
        )

        # Update order line status to resulted
        db.execute(
            text(
                "UPDATE hcl_order_lines SET status = 'resulted' "
                "WHERE id = :lid AND tenant_id = :tid"
            ),
            {"lid": entry.order_line_id, "tid": tenant_id},
        )

        if entry.is_critical:
            has_critical = True

    # Transition order status based on completeness
    total_lines_row = db.execute(
        text("SELECT COUNT(*) FROM hcl_order_lines WHERE order_id = :oid AND tenant_id = :tid"),
        {"oid": order_id, "tid": tenant_id},
    ).fetchone()
    resulted_lines_row = db.execute(
        text("SELECT COUNT(*) FROM hcl_order_lines WHERE order_id = :oid AND tenant_id = :tid AND status = 'resulted'"),
        {"oid": order_id, "tid": tenant_id},
    ).fetchone()
    total_lines = total_lines_row[0] if total_lines_row else 0
    resulted_lines = resulted_lines_row[0] if resulted_lines_row else 0
    new_order_status = "resulted" if resulted_lines >= total_lines and total_lines > 0 else "processing"
    db.execute(
        text(
            "UPDATE hcl_lab_orders SET status = :status, updated_at = :ua "
            "WHERE id = :id AND tenant_id = :tid"
        ),
        {"status": new_order_status, "ua": now, "id": order_id, "tid": tenant_id},
    )

    write_event_audit(
        db=db,
        actor_id=str(_auth.id),
        actor_type="staff",
        event_type="lab_results.entered",
        entity_type="lab_order",
        entity_id=order_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        source_module="healthcare_lab",
        metadata={"result_count": len(payload.results), "has_critical": has_critical},
    )

    db.commit()

    # Critical alert: dispatch PHI-safe notification to ordering provider
    if has_critical:
        _dispatch_critical_alert(db, order, tenant_id, branch_id)

    results = _get_results(db, order_id, tenant_id)
    return [ResultResponse(**r) for r in results]


def _dispatch_critical_alert(
    db: Session, order: dict, tenant_id: str, branch_id: str
) -> None:
    """
    Dispatch PHI-safe critical alert to the ordering provider.
    Template: lab_critical_alert — no patient name, no result values.
    """
    try:
        provider = _get_provider_contact(db, str(order["provider_id"]))
        if not provider:
            return

        svc = NotificationService(
            db=db,
            tenant_id=tenant_id,
            branch_id=branch_id,
        )
        # CR-006 fix: dispatch critical alert to the ORDERING PROVIDER, not the patient.
        # Use dispatch_to_provider() which looks up the provider's phone from hc_providers.
        svc.dispatch_to_provider(
            provider_id=str(order["provider_id"]),
            template_name="lab_critical_alert",
            context={},
        )
    except Exception:
        # Never let notification failure block the result entry
        import logging
        logging.getLogger(__name__).warning(
            "Critical alert dispatch failed for order %s", order["id"], exc_info=True
        )


def _dispatch_results_ready(
    db: Session, order: dict, tenant_id: str, branch_id: str
) -> None:
    """Dispatch PHI-safe notification to patient that results are ready."""
    try:
        svc = NotificationService(
            db=db,
            tenant_id=tenant_id,
            branch_id=branch_id,
        )
        svc._dispatch(
            patient_id=str(order["patient_id"]),
            template_name="lab_results_ready",
            context={},
            appointment_id=None,
            waitlist_id=None,
        )
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            "Results ready notification failed for order %s", order["id"], exc_info=True
        )


@router.post(
    _PREFIX + "/branches/{branch_id}/orders/{order_id}/results/release",
    response_model=list,
)
def release_results(
    branch_id: str,
    order_id: str,
    db: Session = Depends(healthcare_branch_session),
    _auth=Depends(
        has_hc_permission([HCRole.lab_tech, HCRole.branch_manager, HCRole.clinic_owner])
    ),
):
    """Release all results for an order to the patient."""
    tenant_id, _ = _tenant_branch(db)
    order = _get_order_or_404(db, order_id, tenant_id, branch_id)

    if order["status"] != "resulted":
        raise HTTPException(
            status_code=400,
            detail="Results can only be released when order status is 'resulted'",
        )

    now = _now()
    db.execute(
        text(
            "UPDATE hcl_results SET shared_with_patient = true, released_at = :now "
            "WHERE order_id = :oid AND tenant_id = :tid"
        ),
        {"now": now, "oid": order_id, "tid": tenant_id},
    )

    write_event_audit(
        db=db,
        actor_id=str(_auth.id),
        actor_type="staff",
        event_type="lab_results.released",
        entity_type="lab_order",
        entity_id=order_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        source_module="healthcare_lab",
    )

    db.commit()

    # Notify patient — PHI-safe template
    _dispatch_results_ready(db, order, tenant_id, branch_id)

    results = _get_results(db, order_id, tenant_id)
    return [ResultResponse(**r) for r in results]


@router.get(
    _PREFIX + "/branches/{branch_id}/orders/{order_id}/results",
    response_model=list,
)
def get_results(
    branch_id: str,
    order_id: str,
    db: Session = Depends(healthcare_branch_session),
    _auth=Depends(
        has_hc_permission([HCRole.lab_tech, HCRole.doctor, HCRole.clinic_owner])
    ),
):
    """Get all results for an order. PHI audit logged."""
    tenant_id, _ = _tenant_branch(db)
    _get_order_or_404(db, order_id, tenant_id, branch_id)

    write_phi_read_audit(
        db=db,
        actor_id=str(_auth.id),
        actor_type="staff",
        entity_type="lab_results",
        entity_id=order_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        source_module="healthcare_lab",
    )

    results = _get_results(db, order_id, tenant_id)
    return [ResultResponse(**r) for r in results]


# ===========================================================================
# Patient-facing endpoints
# ===========================================================================

@router.get(
    _PATIENT_PREFIX + "/lab-orders",
    response_model=list,
)
def patient_list_lab_orders(
    db: Session = Depends(get_patient_db),
    current_patient=Depends(get_current_patient),
):
    """Patient: list own lab orders where any result has been shared."""
    patient_id = current_patient.patient_id
    tenant_id = current_patient.require_tenant()

    rows = db.execute(
        text(
            "SELECT DISTINCT o.id AS order_id, e.created_at AS encounter_date, "
            "b.branch_name AS clinic_name, o.status AS order_status, "
            "MAX(r.resulted_at) AS resulted_at "
            "FROM hcl_lab_orders o "
            "JOIN hc_encounters e ON e.id = o.encounter_id "
            "JOIN hc_branches b ON b.id = o.branch_id "
            "JOIN hcl_results r ON r.order_id = o.id "
            "WHERE o.patient_id = :pid AND o.tenant_id = :tid AND r.shared_with_patient = true "
            "GROUP BY o.id, e.created_at, b.branch_name, o.status "
            "ORDER BY e.created_at DESC"
        ),
        {"pid": patient_id, "tid": tenant_id},
    ).mappings().all()

    result_list = []
    for row in rows:
        # Get panel names for this order
        panel_rows = db.execute(
            text(
                "SELECT DISTINCT tp.name FROM hcl_order_lines ol "
                "JOIN hcl_test_panels tp ON tp.id = ol.test_panel_id "
                "WHERE ol.order_id = :oid"
            ),
            {"oid": row["order_id"]},
        ).fetchall()
        panel_names = [p[0] for p in panel_rows]

        result_list.append(
            PatientLabOrderSummary(
                order_id=row["order_id"],
                encounter_date=row["encounter_date"],
                clinic_name=row["clinic_name"],
                test_panel_names=panel_names,
                order_status=row["order_status"],
                resulted_at=row["resulted_at"],
            )
        )

    write_phi_read_audit(
        db=db,
        actor_id=patient_id,
        actor_type="patient",
        entity_type="patient_lab_orders",
        entity_id=patient_id,
        tenant_id=tenant_id,
        source_module="healthcare_lab",
    )

    return result_list


@router.get(
    _PATIENT_PREFIX + "/lab-orders/{order_id}/results",
    response_model=PatientLabResultsResponse,
)
def patient_get_lab_results(
    order_id: str,
    db: Session = Depends(get_patient_db),
    current_patient=Depends(get_current_patient),
):
    """Patient: get released results for own order. No clinical notes exposed."""
    patient_id = current_patient.patient_id
    tenant_id = current_patient.require_tenant()

    # Verify order belongs to this patient AND tenant
    order = db.execute(
        text(
            "SELECT id FROM hcl_lab_orders WHERE id = :oid AND patient_id = :pid AND tenant_id = :tid LIMIT 1"
        ),
        {"oid": order_id, "pid": patient_id, "tid": tenant_id},
    ).fetchone()
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Lab order not found",
        )

    # Only return shared results — no clinical_notes, no internal notes
    rows = db.execute(
        text(
            "SELECT tp.name AS test_panel_name, r.result_value, r.result_unit, "
            "r.reference_range, r.is_abnormal, r.is_critical "
            "FROM hcl_results r "
            "JOIN hcl_test_panels tp ON tp.id = r.test_panel_id "
            "WHERE r.order_id = :oid AND r.shared_with_patient = true "
            "ORDER BY tp.name ASC"
        ),
        {"oid": order_id},
    ).mappings().all()

    write_phi_read_audit(
        db=db,
        actor_id=patient_id,
        actor_type="patient",
        entity_type="lab_results",
        entity_id=order_id,
        tenant_id=tenant_id,
        source_module="healthcare_lab",
    )

    items = [PatientLabResultItem(**dict(r)) for r in rows]
    return PatientLabResultsResponse(order_id=order_id, results=items)


# ---------------------------------------------------------------------------
# Deferred import helper for patient DB session
# ---------------------------------------------------------------------------

# CR-013 fix: removed _get_patient_db() helper that returned Depends(...)
# Endpoints now use Depends(tenant_scoped_session) directly.
