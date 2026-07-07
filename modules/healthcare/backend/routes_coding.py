"""
Healthcare — EMR Clinical Coding & Notes API.

Epic-10 / ADR-HC-007. ICD-10/ICD-9-CM catalog search (tenant-scoped) + encounter
diagnoses / procedures / typed clinical notes (branch-scoped). Codes validated
against the tenant catalog at write time (no hard FK). Note `body` is PHI.

    GET  /icd10/search?q=&page=
    GET  /icd9cm/search?q=&page=
    POST /branches/{b}/encounters/{e}/diagnoses
    PUT  /branches/{b}/encounters/{e}/diagnoses/reorder
    PUT  /branches/{b}/encounters/{e}/diagnoses/{id}
    POST /branches/{b}/encounters/{e}/procedures
    DELETE /branches/{b}/encounters/{e}/procedures/{id}
    POST /branches/{b}/encounters/{e}/notes
    GET  /branches/{b}/encounters/{e}/notes
    GET  /branches/{b}/encounters/{e}/coding-summary
"""
from __future__ import annotations
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from modules.sdk.dependencies import get_current_user, tenant_scoped_session
from modules.healthcare.models import (
    HCClinicalNote,
    HCDiagnosis,
    HCEncounter,
    HCICD9CMCode,
    HCICD10Code,
    HCPatient,
    HCProcedure,
    HCProvider,
)
from modules.healthcare.schemas.coding import (
    CodingSummaryResponse,
    EncounterListItem,
    DiagnosisCreate,
    DiagnosisReorder,
    DiagnosisResponse,
    DiagnosisUpdate,
    ICD9CMCodeResponse,
    ICD10CodeResponse,
    NoteCreate,
    NoteResponse,
    NoteSummary,
    ProcedureCreate,
    ProcedureResponse,
)
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.branch_scope import healthcare_branch_session
from modules.healthcare.sdk.phi_audit import write_event_audit, write_phi_read_audit

router = APIRouter(prefix="/api/v1/modules/healthcare", tags=["healthcare-emr-coding"])

_CLINICAL = [HCRole.clinic_owner, HCRole.branch_manager, HCRole.doctor, HCRole.nurse]


def _ip_ua(request):
    return (request.client.host if request.client else None, request.headers.get("user-agent"))


def _audit(db, request, user, branch_id, event, etype, eid):
    ip, ua = _ip_ua(request)
    write_event_audit(db=db, actor_id=str(user.id), actor_type="staff", event_type=event,
                      entity_type=etype, entity_id=str(eid), tenant_id=hc_shared_tenant_id(),
                      branch_id=str(branch_id), ip=ip, ua=ua)


def _get_encounter(db, tid, branch_id, encounter_id) -> HCEncounter:
    enc = (
        db.query(HCEncounter)
        .filter(HCEncounter.id == str(encounter_id), HCEncounter.tenant_id == tid,
                HCEncounter.branch_id == str(branch_id))
        .first()
    )
    if not enc:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return enc


def _icd10_desc(db, tid, code):
    row = db.query(HCICD10Code.description).filter(
        HCICD10Code.tenant_id == tid, HCICD10Code.code == code).first()
    return row[0] if row else None


def _icd9_desc(db, tid, code):
    row = db.query(HCICD9CMCode.description).filter(
        HCICD9CMCode.tenant_id == tid, HCICD9CMCode.code == code).first()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# Catalog search (tenant-scoped)
# ---------------------------------------------------------------------------

@router.get("/icd10/search", response_model=List[ICD10CodeResponse],
            summary="Search the tenant's ICD-10 diagnosis catalog")
async def icd10_search(q: str = Query("", max_length=100), page: int = Query(1, ge=1),
                       page_size: int = Query(20, ge=1, le=50),
                       db: Session = Depends(tenant_scoped_session),
                       current_user=Depends(get_current_user),
                       _=Depends(has_hc_permission(_CLINICAL))):
    tid = hc_shared_tenant_id()
    query = db.query(HCICD10Code).filter(HCICD10Code.tenant_id == tid, HCICD10Code.is_active == True)
    if q:
        like = f"%{q}%"
        query = query.filter(HCICD10Code.code.ilike(f"{q}%") | HCICD10Code.description.ilike(like))
    return query.order_by(HCICD10Code.code).offset((page - 1) * page_size).limit(page_size).all()


@router.get("/icd9cm/search", response_model=List[ICD9CMCodeResponse],
            summary="Search the tenant's ICD-9-CM procedure catalog")
async def icd9cm_search(q: str = Query("", max_length=100), page: int = Query(1, ge=1),
                        page_size: int = Query(20, ge=1, le=50),
                        db: Session = Depends(tenant_scoped_session),
                        current_user=Depends(get_current_user),
                        _=Depends(has_hc_permission(_CLINICAL))):
    tid = hc_shared_tenant_id()
    query = db.query(HCICD9CMCode).filter(HCICD9CMCode.tenant_id == tid, HCICD9CMCode.is_active == True)
    if q:
        like = f"%{q}%"
        query = query.filter(HCICD9CMCode.code.ilike(f"{q}%") | HCICD9CMCode.description.ilike(like))
    return query.order_by(HCICD9CMCode.code).offset((page - 1) * page_size).limit(page_size).all()


# ---------------------------------------------------------------------------
# Encounter picker (for the coding workspace)
# ---------------------------------------------------------------------------

@router.get("/branches/{branch_id}/encounters", response_model=List[EncounterListItem],
            summary="List recent encounters to code")
async def list_encounters(branch_id: uuid.UUID, request: Request,
                          status_filter: Optional[str] = Query(None, alias="status"),
                          db: Session = Depends(healthcare_branch_session),
                          current_user=Depends(get_current_user),
                          _=Depends(has_hc_permission(_CLINICAL))):
    tid = hc_shared_tenant_id()
    q = db.query(HCEncounter).filter(HCEncounter.tenant_id == tid, HCEncounter.branch_id == str(branch_id))
    if status_filter:
        q = q.filter(HCEncounter.status == status_filter)
    encounters = q.order_by(HCEncounter.started_at.desc()).limit(50).all()
    items = []
    for e in encounters:
        pat = db.query(HCPatient).filter(HCPatient.id == e.patient_id).first()
        prov = db.query(HCProvider).filter(HCProvider.id == e.provider_id).first()
        name = (pat.full_name if pat else "") or "Unknown"
        parts = name.split()
        masked = f"{parts[0]} {parts[-1][0]}." if len(parts) > 1 else name  # first + last initial
        items.append(EncounterListItem(id=e.id, patient_name=masked,
                                       provider_name=prov.display_name if prov else None,
                                       status=e.status, started_at=e.started_at))
    if encounters:  # PHI read audit — patient names accessed (ADR-HC-002)
        ip, ua = _ip_ua(request)
        write_phi_read_audit(db=db, actor_id=str(current_user.id), actor_type="staff",
                             entity_type="encounter_list", entity_id=str(branch_id), tenant_id=tid, ip=ip, ua=ua)
        db.commit()
    return items


# ---------------------------------------------------------------------------
# Diagnoses (ICD-10)
# ---------------------------------------------------------------------------

def _diag_resp(db, tid, d: HCDiagnosis) -> DiagnosisResponse:
    return DiagnosisResponse(id=d.id, encounter_id=d.encounter_id, icd10_code=d.icd10_code,
                             description=_icd10_desc(db, tid, d.icd10_code),
                             is_primary=d.is_primary, sequence=d.sequence, created_at=d.created_at)


@router.post("/branches/{branch_id}/encounters/{encounter_id}/diagnoses",
             response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED,
             summary="Attach an ICD-10 diagnosis to an encounter")
async def add_diagnosis(branch_id: uuid.UUID, encounter_id: uuid.UUID, payload: DiagnosisCreate,
                        request: Request, db: Session = Depends(healthcare_branch_session),
                        current_user=Depends(get_current_user),
                        _=Depends(has_hc_permission(_CLINICAL))):
    tid = hc_shared_tenant_id()
    _get_encounter(db, tid, branch_id, encounter_id)
    if not _icd10_desc(db, tid, payload.icd10_code):
        raise HTTPException(status_code=422, detail="ICD-10 code not in the tenant catalog")
    if db.query(HCDiagnosis).filter(HCDiagnosis.encounter_id == str(encounter_id),
                                    HCDiagnosis.icd10_code == payload.icd10_code).first():
        raise HTTPException(status_code=409, detail="Diagnosis already attached to this encounter")
    if payload.is_primary:
        db.query(HCDiagnosis).filter(HCDiagnosis.encounter_id == str(encounter_id),
                                     HCDiagnosis.is_primary == True).update({"is_primary": False})
    d = HCDiagnosis(tenant_id=tid, branch_id=str(branch_id), encounter_id=str(encounter_id),
                    icd10_code=payload.icd10_code, is_primary=payload.is_primary, sequence=payload.sequence)
    db.add(d); db.flush()
    _audit(db, request, current_user, branch_id, "encounter.diagnosis_added", "diagnosis", d.id)
    db.commit(); db.refresh(d)
    return _diag_resp(db, tid, d)


@router.put("/branches/{branch_id}/encounters/{encounter_id}/diagnoses/reorder",
            response_model=List[DiagnosisResponse], summary="Rewrite diagnosis sequence order")
async def reorder_diagnoses(branch_id: uuid.UUID, encounter_id: uuid.UUID, payload: DiagnosisReorder,
                            request: Request, db: Session = Depends(healthcare_branch_session),
                            current_user=Depends(get_current_user),
                            _=Depends(has_hc_permission(_CLINICAL))):
    tid = hc_shared_tenant_id()
    _get_encounter(db, tid, branch_id, encounter_id)
    existing = {d.id: d for d in db.query(HCDiagnosis).filter(
        HCDiagnosis.encounter_id == str(encounter_id), HCDiagnosis.tenant_id == tid).all()}
    if set(payload.order) != set(existing.keys()):
        raise HTTPException(status_code=422, detail="Order must list exactly the encounter's diagnoses")
    for i, did in enumerate(payload.order, start=1):
        existing[did].sequence = i
    _audit(db, request, current_user, branch_id, "encounter.diagnoses_reordered", "encounter", encounter_id)
    db.commit()
    rows = db.query(HCDiagnosis).filter(HCDiagnosis.encounter_id == str(encounter_id)).order_by(HCDiagnosis.sequence).all()
    return [_diag_resp(db, tid, d) for d in rows]


@router.put("/branches/{branch_id}/encounters/{encounter_id}/diagnoses/{diagnosis_id}",
            response_model=DiagnosisResponse, summary="Update a diagnosis (primary / sequence)")
async def update_diagnosis(branch_id: uuid.UUID, encounter_id: uuid.UUID, diagnosis_id: uuid.UUID,
                           payload: DiagnosisUpdate, request: Request,
                           db: Session = Depends(healthcare_branch_session),
                           current_user=Depends(get_current_user),
                           _=Depends(has_hc_permission(_CLINICAL))):
    tid = hc_shared_tenant_id()
    d = db.query(HCDiagnosis).filter(HCDiagnosis.id == str(diagnosis_id), HCDiagnosis.tenant_id == tid,
                                     HCDiagnosis.encounter_id == str(encounter_id)).first()
    if not d:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    if payload.is_primary is True:
        db.query(HCDiagnosis).filter(HCDiagnosis.encounter_id == str(encounter_id),
                                     HCDiagnosis.is_primary == True,
                                     HCDiagnosis.id != d.id).update({"is_primary": False})
        d.is_primary = True
    elif payload.is_primary is False:
        d.is_primary = False
    if payload.sequence is not None:
        d.sequence = payload.sequence
    _audit(db, request, current_user, branch_id, "encounter.diagnosis_updated", "diagnosis", d.id)
    db.commit(); db.refresh(d)
    return _diag_resp(db, tid, d)


# ---------------------------------------------------------------------------
# Procedures (ICD-9-CM)
# ---------------------------------------------------------------------------

@router.post("/branches/{branch_id}/encounters/{encounter_id}/procedures",
             response_model=ProcedureResponse, status_code=status.HTTP_201_CREATED,
             summary="Attach an ICD-9-CM procedure to an encounter")
async def add_procedure(branch_id: uuid.UUID, encounter_id: uuid.UUID, payload: ProcedureCreate,
                        request: Request, db: Session = Depends(healthcare_branch_session),
                        current_user=Depends(get_current_user),
                        _=Depends(has_hc_permission(_CLINICAL))):
    tid = hc_shared_tenant_id()
    _get_encounter(db, tid, branch_id, encounter_id)
    if not _icd9_desc(db, tid, payload.icd9cm_code):
        raise HTTPException(status_code=422, detail="ICD-9-CM code not in the tenant catalog")
    p = HCProcedure(tenant_id=tid, branch_id=str(branch_id), encounter_id=str(encounter_id),
                    icd9cm_code=payload.icd9cm_code, note=payload.note)
    db.add(p); db.flush()
    _audit(db, request, current_user, branch_id, "encounter.procedure_added", "procedure", p.id)
    db.commit(); db.refresh(p)
    return ProcedureResponse(id=p.id, encounter_id=p.encounter_id, icd9cm_code=p.icd9cm_code,
                             description=_icd9_desc(db, tid, p.icd9cm_code), note=p.note,
                             created_at=p.created_at)


@router.delete("/branches/{branch_id}/encounters/{encounter_id}/procedures/{procedure_id}",
               status_code=status.HTTP_204_NO_CONTENT, summary="Remove a procedure (open encounter only)")
async def delete_procedure(branch_id: uuid.UUID, encounter_id: uuid.UUID, procedure_id: uuid.UUID,
                           request: Request, db: Session = Depends(healthcare_branch_session),
                           current_user=Depends(get_current_user),
                           _=Depends(has_hc_permission(_CLINICAL))):
    tid = hc_shared_tenant_id()
    enc = _get_encounter(db, tid, branch_id, encounter_id)
    if enc.status not in ("open", "in_progress"):
        raise HTTPException(status_code=409, detail="Encounter is not open")
    p = db.query(HCProcedure).filter(HCProcedure.id == str(procedure_id), HCProcedure.tenant_id == tid,
                                     HCProcedure.encounter_id == str(encounter_id)).first()
    if not p:
        raise HTTPException(status_code=404, detail="Procedure not found")
    db.delete(p)
    _audit(db, request, current_user, branch_id, "encounter.procedure_removed", "procedure", procedure_id)
    db.commit()


# ---------------------------------------------------------------------------
# Clinical notes (PHI)
# ---------------------------------------------------------------------------

@router.post("/branches/{branch_id}/encounters/{encounter_id}/notes",
             response_model=NoteResponse, status_code=status.HTTP_201_CREATED,
             summary="Add a typed clinical note (PHI)")
async def add_note(branch_id: uuid.UUID, encounter_id: uuid.UUID, payload: NoteCreate,
                   request: Request, db: Session = Depends(healthcare_branch_session),
                   current_user=Depends(get_current_user),
                   _=Depends(has_hc_permission(_CLINICAL))):
    tid = hc_shared_tenant_id()
    _get_encounter(db, tid, branch_id, encounter_id)
    n = HCClinicalNote(tenant_id=tid, branch_id=str(branch_id), encounter_id=str(encounter_id),
                       note_type=payload.note_type, body=payload.body, author_id=str(current_user.id))
    db.add(n); db.flush()
    _audit(db, request, current_user, branch_id, "encounter.note_added", "clinical_note", n.id)
    db.commit(); db.refresh(n)
    return NoteResponse(id=n.id, encounter_id=n.encounter_id, note_type=n.note_type,
                        body=n.body, author_id=n.author_id, created_at=n.created_at)


@router.get("/branches/{branch_id}/encounters/{encounter_id}/notes",
            response_model=List[NoteResponse], summary="List clinical notes (PHI — audited read)")
async def list_notes(branch_id: uuid.UUID, encounter_id: uuid.UUID, request: Request,
                     note_type: Optional[str] = Query(None),
                     db: Session = Depends(healthcare_branch_session),
                     current_user=Depends(get_current_user),
                     _=Depends(has_hc_permission(_CLINICAL))):
    tid = hc_shared_tenant_id()
    _get_encounter(db, tid, branch_id, encounter_id)
    q = db.query(HCClinicalNote).filter(HCClinicalNote.tenant_id == tid,
                                        HCClinicalNote.encounter_id == str(encounter_id))
    if note_type:
        q = q.filter(HCClinicalNote.note_type == note_type)
    notes = q.order_by(HCClinicalNote.created_at).all()
    ip, ua = _ip_ua(request)
    for n in notes:  # PHI read audit before returning bodies (ADR-HC-002)
        write_phi_read_audit(db=db, actor_id=str(current_user.id), actor_type="staff",
                             entity_type="clinical_note", entity_id=str(n.id), tenant_id=tid, ip=ip, ua=ua)
    db.commit()
    return [NoteResponse(id=n.id, encounter_id=n.encounter_id, note_type=n.note_type,
                         body=n.body, author_id=n.author_id, created_at=n.created_at) for n in notes]


# ---------------------------------------------------------------------------
# Coding summary
# ---------------------------------------------------------------------------

@router.get("/branches/{branch_id}/encounters/{encounter_id}/coding-summary",
            response_model=CodingSummaryResponse, summary="Consolidated coding summary for an encounter")
async def coding_summary(branch_id: uuid.UUID, encounter_id: uuid.UUID,
                         db: Session = Depends(healthcare_branch_session),
                         current_user=Depends(get_current_user),
                         _=Depends(has_hc_permission(list(HCRole)))):
    tid = hc_shared_tenant_id()
    _get_encounter(db, tid, branch_id, encounter_id)
    diags = db.query(HCDiagnosis).filter(HCDiagnosis.encounter_id == str(encounter_id)).order_by(HCDiagnosis.sequence).all()
    procs = db.query(HCProcedure).filter(HCProcedure.encounter_id == str(encounter_id)).order_by(HCProcedure.created_at).all()
    notes = db.query(HCClinicalNote).filter(HCClinicalNote.encounter_id == str(encounter_id)).order_by(HCClinicalNote.created_at).all()
    primary = next((d.icd10_code for d in diags if d.is_primary), None)
    return CodingSummaryResponse(
        encounter_id=str(encounter_id),
        primary_diagnosis=primary,
        diagnoses=[_diag_resp(db, tid, d) for d in diags],
        procedures=[ProcedureResponse(id=p.id, encounter_id=p.encounter_id, icd9cm_code=p.icd9cm_code,
                                      description=_icd9_desc(db, tid, p.icd9cm_code), note=p.note,
                                      created_at=p.created_at) for p in procs],
        notes=[NoteSummary(id=n.id, note_type=n.note_type, author_id=n.author_id, created_at=n.created_at) for n in notes],
    )
