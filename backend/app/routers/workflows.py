"""
Workflow Designer API Router

API endpoints for the Workflow Designer feature.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.workflow import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowDefinitionResponse,
    WorkflowStateCreate,
    WorkflowStateUpdate,
    WorkflowStateResponse,
    WorkflowTransitionCreate,
    WorkflowTransitionUpdate,
    WorkflowTransitionResponse,
    WorkflowInstanceCreate,
    WorkflowInstanceResponse,
    WorkflowTransitionExecuteRequest,
    WorkflowHistoryResponse,
)
from app.services.workflow_service import WorkflowService


router = APIRouter(prefix="/api/v1/workflows", tags=["Workflow Designer"])


# ==================== Workflow Definition Endpoints ====================

@router.post("/", response_model=WorkflowDefinitionResponse)
async def create_workflow(
    workflow: WorkflowDefinitionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new workflow definition"""
    service = WorkflowService(db, current_user)
    return await service.create_workflow(workflow)


@router.get("/", response_model=List[WorkflowDefinitionResponse])
async def list_workflows(
    entity_id: Optional[UUID] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all workflow definitions"""
    service = WorkflowService(db, current_user)
    return await service.list_workflows(entity_id, category)


@router.get("/{workflow_id}", response_model=WorkflowDefinitionResponse)
async def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get workflow definition by ID"""
    service = WorkflowService(db, current_user)
    return await service.get_workflow(workflow_id)


@router.put("/{workflow_id}", response_model=WorkflowDefinitionResponse)
async def update_workflow(
    workflow_id: UUID,
    workflow: WorkflowDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update workflow definition"""
    service = WorkflowService(db, current_user)
    return await service.update_workflow(workflow_id, workflow)


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete workflow definition (soft delete)"""
    service = WorkflowService(db, current_user)
    return await service.delete_workflow(workflow_id)


@router.post("/{workflow_id}/publish", response_model=WorkflowDefinitionResponse)
async def publish_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Publish a workflow to make it active"""
    service = WorkflowService(db, current_user)
    return await service.publish_workflow(workflow_id)


# ==================== Workflow State Endpoints ====================

@router.post("/{workflow_id}/states", response_model=WorkflowStateResponse)
async def create_state(
    workflow_id: UUID,
    state: WorkflowStateCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add a state to a workflow"""
    service = WorkflowService(db, current_user)
    return await service.create_state(workflow_id, state)


@router.get("/{workflow_id}/states", response_model=List[WorkflowStateResponse])
async def list_states(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all states for a workflow"""
    service = WorkflowService(db, current_user)
    return await service.list_states(workflow_id)


@router.put("/{workflow_id}/states/{state_id}", response_model=WorkflowStateResponse)
async def update_state(
    workflow_id: UUID,
    state_id: UUID,
    state: WorkflowStateUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a workflow state"""
    service = WorkflowService(db, current_user)
    return await service.update_state(workflow_id, state_id, state)


# ==================== Workflow Transition Endpoints ====================

@router.post("/{workflow_id}/transitions", response_model=WorkflowTransitionResponse)
async def create_transition(
    workflow_id: UUID,
    transition: WorkflowTransitionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add a transition to a workflow"""
    service = WorkflowService(db, current_user)
    return await service.create_transition(workflow_id, transition)


@router.get("/{workflow_id}/transitions", response_model=List[WorkflowTransitionResponse])
async def list_transitions(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all transitions for a workflow"""
    service = WorkflowService(db, current_user)
    return await service.list_transitions(workflow_id)


# ==================== Workflow Instance Endpoints ====================

@router.post("/instances", response_model=WorkflowInstanceResponse)
async def create_instance(
    instance: WorkflowInstanceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Start a new workflow instance"""
    service = WorkflowService(db, current_user)
    return await service.create_instance(instance)


@router.get("/instances/{instance_id}", response_model=WorkflowInstanceResponse)
async def get_instance(
    instance_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get workflow instance by ID"""
    service = WorkflowService(db, current_user)
    return await service.get_instance(instance_id)


@router.post("/instances/{instance_id}/execute", response_model=WorkflowInstanceResponse)
async def execute_transition(
    instance_id: UUID,
    transition_request: WorkflowTransitionExecuteRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Execute a workflow transition"""
    service = WorkflowService(db, current_user)
    return await service.execute_transition(instance_id, transition_request)


@router.get("/instances/{instance_id}/history", response_model=List[WorkflowHistoryResponse])
async def get_instance_history(
    instance_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get history for a workflow instance"""
    service = WorkflowService(db, current_user)
    return await service.get_instance_history(instance_id)


@router.get("/instances/{instance_id}/available-transitions", response_model=List[WorkflowTransitionResponse])
async def get_available_transitions(
    instance_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get available transitions from current state"""
    service = WorkflowService(db, current_user)
    return await service.get_available_transitions(instance_id)
