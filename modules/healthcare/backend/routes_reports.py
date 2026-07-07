"""
Healthcare — Reporting & Executive Dashboard API.

Epic-12 / ADR-HC-008. Serves the PHI-free v_hc_* reporting views (schema-hc-02
Part D). The views filter on the app.current_tenant_id GUC; the platform enforces
tenancy via an ORM listener (not this GUC), so these endpoints set it explicitly
via set_config before querying — keeping the reporting self-contained and tenant-safe.

    GET /branches/{b}/reports/dashboard
    GET /branches/{b}/reports/datasets/{name}
"""
from __future__ import annotations
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id

import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import get_current_user
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.branch_scope import healthcare_branch_session

router = APIRouter(prefix="/api/v1/modules/healthcare", tags=["healthcare-reporting"])

# dataset name -> (view, order-by column)
_DATASETS = {
    "daily-patients": ("v_hc_daily_patients", "service_day DESC"),
    "doctor-productivity": ("v_hc_doctor_productivity", "service_day DESC"),
    "queue": ("v_hc_queue", "service_day DESC"),
    "appointments": ("v_hc_appointments", "service_day DESC"),
    "revenue": ("v_hc_revenue", "service_day DESC"),
    "disease-stats": ("v_hc_disease_stats", "diagnosis_count DESC"),
}


def _set_tenant(db, tenant_id: str):
    # The v_hc_* views scope on app.current_tenant_id; set it for this txn.
    db.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": tenant_id})


def _rows(db, sql, params):
    return [dict(r._mapping) for r in db.execute(text(sql), params).fetchall()]


@router.get("/branches/{branch_id}/reports/datasets/{name}",
            summary="Rows from a healthcare reporting view (tenant+branch scoped)")
async def dataset(branch_id: uuid.UUID, name: str,
                  date_from: Optional[date] = Query(None), date_to: Optional[date] = Query(None),
                  limit: int = Query(200, ge=1, le=1000),
                  db: Session = Depends(healthcare_branch_session),
                  current_user=Depends(get_current_user),
                  _=Depends(has_hc_permission(list(HCRole)))):
    if name not in _DATASETS:
        raise HTTPException(status_code=404, detail="Unknown dataset")
    view, order = _DATASETS[name]
    tid = hc_shared_tenant_id()
    _set_tenant(db, tid)
    where = ["branch_id = :bid"]
    params = {"bid": str(branch_id), "lim": limit}
    day_col = "period_month" if name == "disease-stats" else "service_day"
    if date_from:
        where.append(f"{day_col} >= :df"); params["df"] = date_from
    if date_to:
        where.append(f"{day_col} <= :dt"); params["dt"] = date_to
    sql = f"SELECT * FROM {view} WHERE {' AND '.join(where)} ORDER BY {order} LIMIT :lim"
    return {"dataset": name, "view": view, "rows": _rows(db, sql, params)}


@router.get("/branches/{branch_id}/reports/dashboard",
            summary="Executive dashboard KPIs (today) from the reporting views")
async def dashboard(branch_id: uuid.UUID,
                    db: Session = Depends(healthcare_branch_session),
                    current_user=Depends(get_current_user),
                    _=Depends(has_hc_permission(list(HCRole)))):
    tid = hc_shared_tenant_id()
    _set_tenant(db, tid)
    bid = str(branch_id)
    today = datetime.utcnow().date()
    p = {"bid": bid, "today": today}

    def scalar(sql, default=0):
        v = db.execute(text(sql), p).scalar()
        return v if v is not None else default

    todays_patients = scalar(
        "SELECT COALESCE(SUM(visit_count),0) FROM v_hc_daily_patients WHERE branch_id=:bid AND service_day=:today")
    walk_ins = scalar(
        "SELECT COALESCE(SUM(walk_in_count),0) FROM v_hc_daily_patients WHERE branch_id=:bid AND service_day=:today")
    encounters_today = scalar(
        "SELECT COALESCE(SUM(encounter_count),0) FROM v_hc_doctor_productivity WHERE branch_id=:bid AND service_day=:today")
    revenue_today = scalar(
        "SELECT COALESCE(SUM(invoiced_total),0) FROM v_hc_revenue WHERE branch_id=:bid AND service_day=:today")
    appts_today = scalar(
        "SELECT COALESCE(SUM(appointment_count),0) FROM v_hc_appointments WHERE branch_id=:bid AND service_day=:today")

    # live queue (not GUC-dependent — direct table, branch-scoped)
    waiting = db.execute(text(
        "SELECT COUNT(*) FROM hcr_queue_tickets WHERE tenant_id=:tid AND branch_id=:bid "
        "AND service_day=:today AND status IN ('waiting','called','recalled')"),
        {"tid": tid, "bid": bid, "today": today}).scalar() or 0
    active_doctors = db.execute(text(
        "SELECT COUNT(*) FROM hc_providers WHERE tenant_id=:tid AND branch_id=:bid "
        "AND provider_type='doctor' AND is_active AND employment_status='active'"),
        {"tid": tid, "bid": bid}).scalar() or 0

    # top diagnoses this month
    top_dx = _rows(db,
        "SELECT icd10_code, SUM(diagnosis_count) AS n FROM v_hc_disease_stats WHERE branch_id=:bid "
        "GROUP BY icd10_code ORDER BY n DESC LIMIT 5", {"bid": bid})
    revenue_by_payer = _rows(db,
        "SELECT payer, SUM(invoiced_total) AS invoiced, SUM(collected_total) AS collected "
        "FROM v_hc_revenue WHERE branch_id=:bid GROUP BY payer ORDER BY invoiced DESC", {"bid": bid})

    return {
        "service_day": str(today),
        "kpis": {
            "todays_patients": int(todays_patients),
            "walk_ins": int(walk_ins),
            "waiting_patients": int(waiting),
            "encounters_today": int(encounters_today),
            "appointments_today": int(appts_today),
            "revenue_today": int(revenue_today),
            "active_doctors": int(active_doctors),
        },
        "top_diagnoses": top_dx,
        "revenue_by_payer": revenue_by_payer,
    }
