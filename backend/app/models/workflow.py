"""
Workflow Designer - Database Models

Models for the no-code platform's workflow/business process designer feature.
Enables visual design of workflows, approval processes, and state machines.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import GUID, Base, generate_uuid


class WorkflowDefinition(Base):
    """
    Workflow Definition Model

    Stores metadata for workflow definitions.
    Each workflow represents a business process or approval flow.
    """
    __tablename__ = "workflow_definitions"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False, index=True)

    # Basic Info
    name = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))

    # Associated Entity
    entity_id = Column(GUID, ForeignKey("entity_definitions.id"))  # Entity this workflow applies to

    # Configuration
    trigger_type = Column(String(50), default="manual")  # 'manual', 'automatic', 'scheduled'
    trigger_conditions = Column(JSONB)  # Conditions for automatic triggers

    # Canvas Data
    canvas_data = Column(JSONB, nullable=False)  # Workflow diagram (nodes, edges, positions)

    # Version Control
    version = Column(Integer, default=1)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    parent_version_id = Column(GUID, ForeignKey("workflow_definitions.id"))

    # Status
    is_active = Column(Boolean, default=True)

    # Metadata
    metadata = Column(JSONB, default=dict)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))
    updated_by = Column(GUID, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)

    # Relationships
    states = relationship("WorkflowState", back_populates="workflow", cascade="all, delete-orphan")
    transitions = relationship("WorkflowTransition", back_populates="workflow", cascade="all, delete-orphan")
    instances = relationship("WorkflowInstance", back_populates="workflow")

    # Table constraints
    __table_args__ = (
        Index("idx_workflow_definitions_tenant", "tenant_id", postgresql_where=text("is_deleted = false")),
        Index("idx_workflow_definitions_entity", "entity_id"),
        {"schema": "public"},
    )


class WorkflowState(Base):
    """
    Workflow State Model

    Represents individual states in a workflow.
    """
    __tablename__ = "workflow_states"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    workflow_id = Column(GUID, ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)

    # Basic Info
    name = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text)

    # State Type
    state_type = Column(String(50), nullable=False)  # 'start', 'intermediate', 'end', 'approval', 'condition'

    # Display
    color = Column(String(50))
    icon = Column(String(50))
    position_x = Column(Integer)  # Canvas position
    position_y = Column(Integer)

    # Behavior
    is_final = Column(Boolean, default=False)  # End state?
    requires_approval = Column(Boolean, default=False)
    approval_config = Column(JSONB)  # Approval routing rules

    # SLA & Escalation
    sla_hours = Column(Integer)  # Time limit for this state
    escalation_rules = Column(JSONB)  # What happens on SLA breach

    # Actions on Entry/Exit
    on_entry_actions = Column(JSONB, default=list)  # Actions when entering state
    on_exit_actions = Column(JSONB, default=list)  # Actions when exiting state

    # Field Requirements
    required_fields = Column(JSONB, default=list)  # Fields that must be filled

    # Metadata
    metadata = Column(JSONB, default=dict)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    workflow = relationship("WorkflowDefinition", back_populates="states")
    transitions_from = relationship("WorkflowTransition", foreign_keys="WorkflowTransition.from_state_id", back_populates="from_state")
    transitions_to = relationship("WorkflowTransition", foreign_keys="WorkflowTransition.to_state_id", back_populates="to_state")

    # Table constraints
    __table_args__ = (
        Index("idx_workflow_states_workflow", "workflow_id"),
        {"schema": "public"},
    )


class WorkflowTransition(Base):
    """
    Workflow Transition Model

    Represents transitions between workflow states.
    """
    __tablename__ = "workflow_transitions"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    workflow_id = Column(GUID, ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)

    # Basic Info
    name = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text)

    # Source & Target
    from_state_id = Column(GUID, ForeignKey("workflow_states.id"), nullable=False, index=True)
    to_state_id = Column(GUID, ForeignKey("workflow_states.id"), nullable=False, index=True)

    # Conditions
    condition_type = Column(String(50), default="always")  # 'always', 'conditional', 'approval'
    conditions = Column(JSONB)  # Conditional logic

    # Permissions
    allowed_roles = Column(JSONB, default=list)  # Roles allowed to execute transition
    allowed_users = Column(JSONB, default=list)  # Specific users allowed

    # Actions
    actions = Column(JSONB, default=list)  # Actions to perform on transition

    # Display
    button_label = Column(String(100))  # Label for transition button
    button_style = Column(String(50))  # 'primary', 'success', 'danger', etc.
    icon = Column(String(50))
    display_order = Column(Integer, default=0)

    # Validation
    validation_rules = Column(JSONB, default=list)

    # Metadata
    metadata = Column(JSONB, default=dict)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    workflow = relationship("WorkflowDefinition", back_populates="transitions")
    from_state = relationship("WorkflowState", foreign_keys=[from_state_id], back_populates="transitions_from")
    to_state = relationship("WorkflowState", foreign_keys=[to_state_id], back_populates="transitions_to")

    # Table constraints
    __table_args__ = (
        Index("idx_workflow_transitions_workflow", "workflow_id"),
        Index("idx_workflow_transitions_from_state", "from_state_id"),
        Index("idx_workflow_transitions_to_state", "to_state_id"),
        {"schema": "public"},
    )


class WorkflowInstance(Base):
    """
    Workflow Instance Model

    Represents a running instance of a workflow for a specific record.
    """
    __tablename__ = "workflow_instances"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    workflow_id = Column(GUID, ForeignKey("workflow_definitions.id"), nullable=False, index=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)

    # Associated Record
    entity_id = Column(GUID, ForeignKey("entity_definitions.id"), nullable=False)
    record_id = Column(GUID, nullable=False)  # ID of the record being processed

    # Current State
    current_state_id = Column(GUID, ForeignKey("workflow_states.id"))
    current_state_entered_at = Column(DateTime)

    # Status
    status = Column(String(50), default="active")  # 'active', 'completed', 'cancelled', 'error'

    # SLA Tracking
    sla_deadline = Column(DateTime)
    is_sla_breached = Column(Boolean, default=False)

    # Context Data
    context_data = Column(JSONB, default=dict)  # Workflow-specific data

    # Audit
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    started_by = Column(GUID, ForeignKey("users.id"))

    # Error Handling
    error_message = Column(Text)
    error_details = Column(JSONB)

    # Relationships
    workflow = relationship("WorkflowDefinition", back_populates="instances")
    history = relationship("WorkflowHistory", back_populates="instance", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        Index("idx_workflow_instances_workflow", "workflow_id"),
        Index("idx_workflow_instances_record", "entity_id", "record_id"),
        Index("idx_workflow_instances_status", "status"),
        Index("idx_workflow_instances_sla", "sla_deadline", postgresql_where=text("is_sla_breached = false")),
        {"schema": "public"},
    )


class WorkflowHistory(Base):
    """
    Workflow History Model

    Tracks all transitions and actions in a workflow instance.
    """
    __tablename__ = "workflow_history"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    instance_id = Column(GUID, ForeignKey("workflow_instances.id"), nullable=False, index=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)

    # Transition Info
    from_state_id = Column(GUID, ForeignKey("workflow_states.id"))
    to_state_id = Column(GUID, ForeignKey("workflow_states.id"))
    transition_id = Column(GUID, ForeignKey("workflow_transitions.id"))

    # Actor
    performed_by = Column(GUID, ForeignKey("users.id"), index=True)
    performed_at = Column(DateTime, default=datetime.utcnow)

    # Action Details
    action_type = Column(String(50))  # 'transition', 'escalation', 'comment', 'assignment'
    action_data = Column(JSONB)

    # Comments
    comment = Column(Text)

    # Duration
    duration_minutes = Column(Integer)  # Time spent in previous state

    # Metadata
    metadata = Column(JSONB, default=dict)

    # Relationships
    instance = relationship("WorkflowInstance", back_populates="history")

    # Table constraints
    __table_args__ = (
        Index("idx_workflow_history_instance", "instance_id"),
        Index("idx_workflow_history_performed_by", "performed_by"),
        {"schema": "public"},
    )
