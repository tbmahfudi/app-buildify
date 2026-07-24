"""Document approval endpoints — mounted at {API_PREFIX}/approvals (E4).

Thin, access-controlled proxy over the platform workflow engine. DMS enforces
document access (RBAC + row-level ACLs) and audits; the engine owns the approval
state machine, SLA/escalation and history. The caller's JWT is forwarded.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.platform_workflow import PlatformWorkflow, WorkflowError
from ..core.security import Principal, require_permission, tenant_session
from ..services.acl_service import AclService
from ..services.audit_service import AuditService
from ..services.document_service import DocumentService

router = APIRouter()

_DOC_ADMIN = "dms:document:delete:company"


async def _require_doc(db, principal: Principal, document_id: str, need: str):
    doc = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    group_ids = await AclService.user_group_ids(db, principal.user_id)
    ok = await AclService.authorize_document(
        db, tenant_id=principal.tenant_id, user_id=principal.user_id, group_ids=group_ids,
        is_admin=principal.has_permission(_DOC_ADMIN), document=doc, need=need,
    )
    if not ok:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this document")
    return doc


class StartApprovalRequest(BaseModel):
    workflow_id: str


class ExecuteRequest(BaseModel):
    transition_id: str
    comment: Optional[str] = None


@router.get("/workflows")
async def list_approval_workflows(
    principal: Principal = Depends(require_permission("dms:document:read:company")),
):
    """Published workflow definitions the caller can start on a document."""
    try:
        wfs = await PlatformWorkflow.list_published(principal.token)
    except WorkflowError as e:
        raise HTTPException(e.status_code, str(e))
    return [
        {"id": w["id"], "name": w.get("label") or w.get("name"), "category": w.get("category")}
        for w in wfs
    ]


@router.post("/documents/{document_id}/start", status_code=status.HTTP_201_CREATED)
async def start_approval(
    document_id: str,
    body: StartApprovalRequest,
    principal: Principal = Depends(require_permission("dms:document:write:company")),
    db: AsyncSession = Depends(tenant_session),
):
    doc = await _require_doc(db, principal, document_id, "edit")
    try:
        instance = await PlatformWorkflow.start(
            principal.token, workflow_id=body.workflow_id, record_id=document_id,
            context={"filename": doc.filename, "tenant_id": str(principal.tenant_id)},
        )
    except WorkflowError as e:
        raise HTTPException(e.status_code, str(e))
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="approval.start", entity_type="document", entity_id=str(document_id),
        detail={"workflow_id": body.workflow_id, "instance_id": instance.get("id")},
    )
    return instance


@router.get("/documents/{document_id}")
async def list_document_approvals(
    document_id: str,
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    await _require_doc(db, principal, document_id, "view")
    try:
        return await PlatformWorkflow.list_for_record(principal.token, document_id)
    except WorkflowError as e:
        raise HTTPException(e.status_code, str(e))


@router.get("/instances/{instance_id}/transitions")
async def available_transitions(
    instance_id: str,
    principal: Principal = Depends(require_permission("dms:document:read:company")),
):
    try:
        return await PlatformWorkflow.available_transitions(principal.token, instance_id)
    except WorkflowError as e:
        raise HTTPException(e.status_code, str(e))


@router.post("/instances/{instance_id}/execute")
async def execute_transition(
    instance_id: str,
    body: ExecuteRequest,
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    try:
        instance = await PlatformWorkflow.execute(
            principal.token, instance_id, transition_id=body.transition_id, comment=body.comment,
        )
    except WorkflowError as e:
        raise HTTPException(e.status_code, str(e))
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="approval.action", entity_type="document",
        entity_id=str(instance.get("record_id") or ""),
        detail={"instance_id": instance_id, "transition_id": body.transition_id,
                "comment": body.comment, "status": instance.get("status")},
    )
    return instance


@router.get("/instances/{instance_id}/history")
async def instance_history(
    instance_id: str,
    principal: Principal = Depends(require_permission("dms:document:read:company")),
):
    try:
        return await PlatformWorkflow.history(principal.token, instance_id)
    except WorkflowError as e:
        raise HTTPException(e.status_code, str(e))
