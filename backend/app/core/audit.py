import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request
from app.models.audit import AuditLog
from app.models.user import User

def create_audit_log(
    db: Session,
    action: str,
    user: Optional[User] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    status: str = "success",
    error_message: Optional[str] = None
):
    """Create an audit log entry"""
    
    # Extract request info
    ip_address = None
    user_agent = None
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
    
    # Create log entry
    audit_log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=str(user.id) if user else None,
        user_email=user.email if user else None,
        tenant_id=user.tenant_id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=json.dumps(changes) if changes else None,
        metadata=json.dumps(metadata) if metadata else None,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=str(uuid.uuid4()),
        status=status,
        error_message=error_message
    )
    
    db.add(audit_log)
    db.commit()
    
    return audit_log

def compute_diff(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    """Compute differences between two dictionaries"""
    changes = {}
    
    # Check for modified and new fields
    for key, new_value in after.items():
        old_value = before.get(key)
        if old_value != new_value:
            changes[key] = {
                "before": old_value,
                "after": new_value
            }
    
    # Check for removed fields
    for key in before:
        if key not in after:
            changes[key] = {
                "before": before[key],
                "after": None
            }
    
    return changes

def audit_action(action: str, entity_type: Optional[str] = None):
    """Decorator to automatically audit an action"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            request = kwargs.get('request')
            
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # Log success
                if db and current_user:
                    create_audit_log(
                        db=db,
                        action=action,
                        user=current_user,
                        entity_type=entity_type,
                        request=request,
                        status="success"
                    )
                
                return result
            except Exception as e:
                # Log failure
                if db and current_user:
                    create_audit_log(
                        db=db,
                        action=action,
                        user=current_user,
                        entity_type=entity_type,
                        request=request,
                        status="failure",
                        error_message=str(e)
                    )
                raise
        
        return wrapper
    return decorator