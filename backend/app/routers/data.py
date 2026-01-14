import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.orm import Session

from app.core.audit import compute_diff, create_audit_log
from app.core.dependencies import get_current_user, get_db
from app.models.branch import Branch
from app.models.company import Company
from app.models.department import Department
from app.models.user import User
from app.schemas.data import (
    BulkOperationRequest,
    BulkOperationResponse,
    DataCreateRequest,
    DataResponse,
    DataSearchRequest,
    DataSearchResponse,
    DataUpdateRequest,
)

router = APIRouter(prefix="/api/v1/data", tags=["data"])
logger = logging.getLogger(__name__)

# Entity registry - maps entity names to SQLAlchemy models
ENTITY_REGISTRY = {
    "companies": Company,
    "branches": Branch,
    "departments": Department,
    "users": User
}

def get_model_class(entity: str):
    """Get model class for entity name"""
    model = ENTITY_REGISTRY.get(entity)
    if not model:
        raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found")
    return model

def model_to_dict(obj) -> Dict[str, Any]:
    """Convert SQLAlchemy model to dict"""
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        # Convert to string for UUID, datetime, etc.
        if value is not None:
            result[column.name] = str(value) if not isinstance(value, (str, int, float, bool)) else value
        else:
            result[column.name] = None
    return result

def apply_filters(query, model, filters):
    """Apply filters to query"""
    for f in filters:
        field = f.get("field")
        operator = f.get("operator", "eq")
        value = f.get("value")
        
        if not hasattr(model, field):
            continue
        
        column = getattr(model, field)
        
        if operator == "eq":
            query = query.filter(column == value)
        elif operator == "ne":
            query = query.filter(column != value)
        elif operator == "gt":
            query = query.filter(column > value)
        elif operator == "gte":
            query = query.filter(column >= value)
        elif operator == "lt":
            query = query.filter(column < value)
        elif operator == "lte":
            query = query.filter(column <= value)
        elif operator == "like":
            query = query.filter(column.like(f"%{value}%"))
        elif operator == "in":
            query = query.filter(column.in_(value))
    
    return query

def apply_sort(query, model, sort):
    """Apply sorting to query"""
    for s in sort:
        field, direction = s[0], s[1] if len(s) > 1 else "asc"
        if hasattr(model, field):
            column = getattr(model, field)
            query = query.order_by(desc(column) if direction == "desc" else asc(column))
    return query

@router.post("/{entity}/list", response_model=DataSearchResponse)
def search_data(
    entity: str,
    request: DataSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generic data search/list endpoint"""
    model = get_model_class(entity)
    
    # Base query
    query = db.query(model)
    
    # Apply scope filters (if entity supports tenant isolation)
    if request.scope and hasattr(model, "company_id"):
        if "company_id" in request.scope:
            query = query.filter(model.company_id == request.scope["company_id"])
    
    # Apply filters
    if request.filters:
        query = apply_filters(query, model, request.filters)
    
    # Global search (if provided)
    if request.search:
        # Search across common text fields
        search_fields = []
        for col in ["name", "code", "email", "description"]:
            if hasattr(model, col):
                search_fields.append(getattr(model, col).like(f"%{request.search}%"))
        if search_fields:
            query = query.filter(or_(*search_fields))
    
    # Get total before pagination
    total = query.count()
    
    # Apply sorting
    if request.sort:
        query = apply_sort(query, model, request.sort)
    
    # Apply pagination
    offset = (request.page - 1) * request.page_size
    query = query.offset(offset).limit(request.page_size)
    
    # Execute query
    results = query.all()
    rows = [model_to_dict(r) for r in results]
    
    return DataSearchResponse(
        rows=rows,
        total=total,
        filtered=len(rows),
        page=request.page,
        page_size=request.page_size
    )

@router.get("/{entity}/{id}", response_model=DataResponse)
def get_record(
    entity: str,
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single record by ID"""
    model = get_model_class(entity)
    
    record = db.query(model).filter(model.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Record not found")
    
    return DataResponse(
        id=str(record.id),
        data=model_to_dict(record)
    )

@router.post("/{entity}", response_model=DataResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    entity: str,
    request: DataCreateRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new record"""
    model = get_model_class(entity)
    
    # Add ID if not provided
    data = request.data.copy()
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    
    # Create instance
    try:
        record = model(**data)
        db.add(record)
        db.commit()
        db.refresh(record)
        
        # Audit
        create_audit_log(
            db=db,
            action="CREATE",
            user=current_user,
            entity_type=entity,
            entity_id=str(record.id),
            changes={"created": data},
            request=req,
            status="success"
        )
        
        return DataResponse(
            id=str(record.id),
            data=model_to_dict(record)
        )
    except Exception as e:
        db.rollback()
        create_audit_log(
            db=db,
            action="CREATE",
            user=current_user,
            entity_type=entity,
            request=req,
            status="failure",
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{entity}/{id}", response_model=DataResponse)
def update_record(
    entity: str,
    id: str,
    request: DataUpdateRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a record"""
    model = get_model_class(entity)
    
    record = db.query(model).filter(model.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Capture before state
    before = model_to_dict(record)
    
    # Update fields
    try:
        for key, value in request.data.items():
            if hasattr(record, key) and key != "id":
                setattr(record, key, value)
        
        db.commit()
        db.refresh(record)
        
        # Capture after state and compute diff
        after = model_to_dict(record)
        changes = compute_diff(before, after)
        
        # Audit
        create_audit_log(
            db=db,
            action="UPDATE",
            user=current_user,
            entity_type=entity,
            entity_id=id,
            changes=changes,
            request=req,
            status="success"
        )
        
        return DataResponse(
            id=str(record.id),
            data=model_to_dict(record)
        )
    except Exception as e:
        db.rollback()
        create_audit_log(
            db=db,
            action="UPDATE",
            user=current_user,
            entity_type=entity,
            entity_id=id,
            request=req,
            status="failure",
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{entity}/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    entity: str,
    id: str,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a record"""
    model = get_model_class(entity)
    
    record = db.query(model).filter(model.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Capture state before deletion
    before = model_to_dict(record)
    
    try:
        db.delete(record)
        db.commit()
        
        # Audit
        create_audit_log(
            db=db,
            action="DELETE",
            user=current_user,
            entity_type=entity,
            entity_id=id,
            changes={"deleted": before},
            request=req,
            status="success"
        )
        
        return None
    except Exception as e:
        db.rollback()
        create_audit_log(
            db=db,
            action="DELETE",
            user=current_user,
            entity_type=entity,
            entity_id=id,
            request=req,
            status="failure",
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{entity}/bulk", response_model=BulkOperationResponse)
def bulk_operation(
    entity: str,
    request: BulkOperationRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk operations on records"""
    model = get_model_class(entity)
    
    success = 0
    failed = 0
    errors = []
    
    for idx, record_data in enumerate(request.records):
        try:
            if request.operation == "create":
                if "id" not in record_data:
                    record_data["id"] = str(uuid.uuid4())
                record = model(**record_data)
                db.add(record)
                
            elif request.operation == "update":
                record_id = record_data.get("id")
                if not record_id:
                    raise ValueError("ID required for update")
                record = db.query(model).filter(model.id == record_id).first()
                if not record:
                    raise ValueError(f"Record {record_id} not found")
                for key, value in record_data.items():
                    if hasattr(record, key) and key != "id":
                        setattr(record, key, value)
            
            elif request.operation == "delete":
                record_id = record_data.get("id")
                if not record_id:
                    raise ValueError("ID required for delete")
                record = db.query(model).filter(model.id == record_id).first()
                if not record:
                    raise ValueError(f"Record {record_id} not found")
                db.delete(record)
            
            success += 1
            
        except Exception as e:
            failed += 1
            errors.append({
                "index": idx,
                "record": record_data,
                "error": str(e)
            })
    
    # Commit all successful operations
    try:
        db.commit()
        
        # Audit
        create_audit_log(
            db=db,
            action=f"BULK_{request.operation.upper()}",
            user=current_user,
            entity_type=entity,
            context_info={
                "total": len(request.records),
                "success": success,
                "failed": failed
            },
            request=req,
            status="success" if failed == 0 else "partial"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Bulk operation failed: {str(e)}")
    
    return BulkOperationResponse(
        success=success,
        failed=failed,
        errors=errors
    )