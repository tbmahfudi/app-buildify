"""
Automation System API Router

API endpoints for the Automation System feature.
Stub implementation - to be expanded in future iterations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.automation import AutomationRuleResponse


router = APIRouter(prefix="/api/v1/automations", tags=["Automation System"])


@router.get("/rules", response_model=List[AutomationRuleResponse])
async def list_automation_rules(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all automation rules - Stub implementation"""
    return []


@router.get("/rules/{rule_id}", response_model=AutomationRuleResponse)
async def get_automation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get automation rule - Stub implementation"""
    from fastapi import HTTPException
    raise HTTPException(status_code=501, detail="Not yet implemented")
