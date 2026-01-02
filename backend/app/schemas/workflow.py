"""
Workflow Designer - Pydantic Schemas

Request/Response schemas for the Workflow Designer API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ==================== Workflow State Schemas ====================

class WorkflowStateBase(BaseModel):
    """Base schema for workflow states"""
    name: str = Field(..., max_length=100)
    label: str = Field(..., max_length=200)
    description: Optional[str] = None
    state_type: str = Field(..., description="start, intermediate, end, approval, condition")
    color: Optional[str] = None
    icon: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    is_final: bool = False
    requires_approval: bool = False
    approval_config: Optional[Dict[str, Any]] = None
    sla_hours: Optional[int] = None
    escalation_rules: Optional[Dict[str, Any]] = None
    on_entry_actions: List[Dict[str, Any]] = Field(default_factory=list)
    on_exit_actions: List[Dict[str, Any]] = Field(default_factory=list)
    required_fields: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStateCreate(WorkflowStateBase):
    """Schema for creating a workflow state"""
    pass


class WorkflowStateUpdate(BaseModel):
    """Schema for updating a workflow state"""
    label: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    requires_approval: Optional[bool] = None
    approval_config: Optional[Dict[str, Any]] = None
    sla_hours: Optional[int] = None
    escalation_rules: Optional[Dict[str, Any]] = None
    on_entry_actions: Optional[List[Dict[str, Any]]] = None
    on_exit_actions: Optional[List[Dict[str, Any]]] = None
    required_fields: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkflowStateResponse(WorkflowStateBase):
    """Schema for workflow state response"""
    id: UUID
    workflow_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True


# ==================== Workflow Transition Schemas ====================

class WorkflowTransitionBase(BaseModel):
    """Base schema for workflow transitions"""
    name: str = Field(..., max_length=100)
    label: str = Field(..., max_length=200)
    description: Optional[str] = None
    from_state_id: UUID
    to_state_id: UUID
    condition_type: str = "always"
    conditions: Optional[Dict[str, Any]] = None
    allowed_roles: List[UUID] = Field(default_factory=list)
    allowed_users: List[UUID] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    button_label: Optional[str] = None
    button_style: Optional[str] = None
    icon: Optional[str] = None
    display_order: int = 0
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowTransitionCreate(WorkflowTransitionBase):
    """Schema for creating a workflow transition"""
    pass


class WorkflowTransitionUpdate(BaseModel):
    """Schema for updating a workflow transition"""
    label: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    allowed_roles: Optional[List[UUID]] = None
    allowed_users: Optional[List[UUID]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    button_label: Optional[str] = None
    button_style: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = None
    validation_rules: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkflowTransitionResponse(WorkflowTransitionBase):
    """Schema for workflow transition response"""
    id: UUID
    workflow_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True


# ==================== Workflow Definition Schemas ====================

class WorkflowDefinitionBase(BaseModel):
    """Base schema for workflow definitions"""
    name: str = Field(..., max_length=100)
    label: str = Field(..., max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    entity_id: Optional[UUID] = None
    trigger_type: str = "manual"
    trigger_conditions: Optional[Dict[str, Any]] = None
    canvas_data: Dict[str, Any] = Field(..., description="Workflow diagram data")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinitionCreate(WorkflowDefinitionBase):
    """Schema for creating a workflow definition"""
    states: Optional[List[WorkflowStateCreate]] = Field(default_factory=list)
    transitions: Optional[List[WorkflowTransitionCreate]] = Field(default_factory=list)


class WorkflowDefinitionUpdate(BaseModel):
    """Schema for updating a workflow definition"""
    label: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    canvas_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkflowDefinitionResponse(WorkflowDefinitionBase):
    """Schema for workflow definition response"""
    id: UUID
    tenant_id: UUID
    version: int
    is_published: bool
    published_at: Optional[datetime]
    parent_version_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    is_deleted: bool
    states: List[WorkflowStateResponse] = Field(default_factory=list)
    transitions: List[WorkflowTransitionResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ==================== Workflow Instance Schemas ====================

class WorkflowInstanceBase(BaseModel):
    """Base schema for workflow instances"""
    workflow_id: UUID
    entity_id: UUID
    record_id: UUID
    context_data: Dict[str, Any] = Field(default_factory=dict)


class WorkflowInstanceCreate(WorkflowInstanceBase):
    """Schema for creating a workflow instance"""
    pass


class WorkflowInstanceResponse(WorkflowInstanceBase):
    """Schema for workflow instance response"""
    id: UUID
    tenant_id: UUID
    current_state_id: Optional[UUID]
    current_state_entered_at: Optional[datetime]
    status: str
    sla_deadline: Optional[datetime]
    is_sla_breached: bool
    started_at: datetime
    completed_at: Optional[datetime]
    started_by: Optional[UUID]
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class WorkflowTransitionExecuteRequest(BaseModel):
    """Schema for executing a workflow transition"""
    transition_id: UUID
    comment: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


# ==================== Workflow History Schemas ====================

class WorkflowHistoryResponse(BaseModel):
    """Schema for workflow history response"""
    id: UUID
    instance_id: UUID
    tenant_id: UUID
    from_state_id: Optional[UUID]
    to_state_id: Optional[UUID]
    transition_id: Optional[UUID]
    performed_by: Optional[UUID]
    performed_at: datetime
    action_type: Optional[str]
    action_data: Optional[Dict[str, Any]]
    comment: Optional[str]
    duration_minutes: Optional[int]
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True
