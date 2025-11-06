from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from uuid import UUID
import json

from app.core.dependencies import get_db, get_current_user, has_role
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.audit import (
    AuditLogResponse, AuditLogListRequest, AuditLogListResponse
)

router = APIRouter(prefix="/audit", tags=["audit"])

@router.post("/list", response_model=AuditLogListResponse)
def list_audit_logs(
    request: AuditLogListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List audit logs with filters"""
    
    # Base query
    query = db.query(AuditLog)
    
    # Non-superusers can only see their own tenant's logs
    if not current_user.is_superuser and current_user.tenant_id:
        query = query.filter(AuditLog.tenant_id == current_user.tenant_id)
    
    # Apply filters
    if request.user_id:
        query = query.filter(AuditLog.user_id == request.user_id)
    
    if request.action:
        query = query.filter(AuditLog.action == request.action)
    
    if request.entity_type:
        query = query.filter(AuditLog.entity_type == request.entity_type)
    
    if request.entity_id:
        query = query.filter(AuditLog.entity_id == request.entity_id)
    
    if request.status:
        query = query.filter(AuditLog.status == request.status)
    
    if request.start_date:
        query = query.filter(AuditLog.created_at >= request.start_date)
    
    if request.end_date:
        query = query.filter(AuditLog.created_at <= request.end_date)
    
    # Get total
    total = query.count()
    
    # Order by created_at desc
    query = query.order_by(AuditLog.created_at.desc())
    
    # Pagination
    offset = (request.page - 1) * request.page_size
    query = query.offset(offset).limit(request.page_size)
    
    # Execute
    logs = query.all()
    
    # Parse JSON fields
    result_logs = []
    for log in logs:
        log_dict = {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "user_email": log.user_email,
            "tenant_id": str(log.tenant_id) if log.tenant_id else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "changes": json.loads(log.changes) if log.changes else None,
            "context_info": json.loads(log.context_info) if log.context_info else None,
            "ip_address": log.ip_address,
            "status": log.status,
            "error_message": log.error_message,
            "created_at": log.created_at
        }
        result_logs.append(AuditLogResponse(**log_dict))
    
    # Calculate pagination flags
    has_next = (request.page * request.page_size) < total
    has_prev = request.page > 1

    return AuditLogListResponse(
        logs=result_logs,
        total=total,
        filtered=total,
        page=request.page,
        page_size=request.page_size,
        has_next=has_next,
        has_prev=has_prev
    )

def _get_audit_summary_impl(db: Session, current_user: User):
    """Implementation for audit statistics summary"""
    query = db.query(AuditLog)

    # Filter by tenant for non-superusers
    if not current_user.is_superuser and current_user.tenant_id:
        query = query.filter(AuditLog.tenant_id == current_user.tenant_id)

    total = query.count()
    success = query.filter(AuditLog.status == "success").count()
    failed = query.filter(AuditLog.status == "failure").count()

    # Top actions
    from sqlalchemy import func
    top_actions = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).limit(10).all()

    return {
        "total_logs": total,
        "success_count": success,
        "failed_count": failed,
        "top_actions": [{"action": a[0], "count": a[1]} for a in top_actions]
    }

@router.get("/summary")
def get_audit_summary_short(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Get audit statistics summary (short path)"""
    return _get_audit_summary_impl(db, current_user)

@router.get("/stats/summary")
def get_audit_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Get audit statistics summary"""
    return _get_audit_summary_impl(db, current_user)

@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific audit log"""
    log = db.query(AuditLog).filter(AuditLog.id == str(log_id)).first()

    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    # Check permissions
    if not current_user.is_superuser:
        if current_user.tenant_id and log.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return AuditLogResponse(
        id=str(log.id),
        user_id=str(log.user_id) if log.user_id else None,
        user_email=log.user_email,
        tenant_id=str(log.tenant_id) if log.tenant_id else None,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=str(log.entity_id) if log.entity_id else None,
        changes=json.loads(log.changes) if log.changes else None,
        context_info=json.loads(log.context_info) if log.context_info else None,
        ip_address=log.ip_address,
        status=log.status,
        error_message=log.error_message,
        created_at=log.created_at
    )