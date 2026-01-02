"""
Workflow Designer API Router

API endpoints for the Workflow Designer feature.
Stub implementation - to be expanded in future iterations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.workflow import WorkflowDefinitionResponse


router = APIRouter(prefix="/api/v1/workflows", tags=["Workflow Designer"])


@router.get("/", response_model=List[WorkflowDefinitionResponse])
async def list_workflows(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all workflow definitions - Stub implementation"""
    return []


@router.get("/{workflow_id}", response_model=WorkflowDefinitionResponse)
async def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get workflow definition - Stub implementation"""
    from fastapi import HTTPException
    raise HTTPException(status_code=501, detail="Not yet implemented")
