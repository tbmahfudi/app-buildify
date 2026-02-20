"""
Workflow Designer Service

Business logic for the Workflow Designer feature.
Implements state machine logic and workflow execution.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.models.workflow import (
    WorkflowDefinition,
    WorkflowState,
    WorkflowTransition,
    WorkflowInstance,
    WorkflowHistory,
)
from app.schemas.workflow import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowStateCreate,
    WorkflowStateUpdate,
    WorkflowTransitionCreate,
    WorkflowTransitionUpdate,
    WorkflowInstanceCreate,
    WorkflowTransitionExecuteRequest,
)


class WorkflowService:
    """Service for managing workflows and workflow execution"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self.tenant_id = current_user.tenant_id

    # ==================== Workflow Definition Methods ====================

    async def create_workflow(self, workflow_data: WorkflowDefinitionCreate):
        """Create a new workflow definition"""
        # Check if workflow name already exists
        existing = self.db.query(WorkflowDefinition).filter(
            WorkflowDefinition.tenant_id == self.tenant_id,
            WorkflowDefinition.name == workflow_data.name,
            WorkflowDefinition.is_deleted == False
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workflow with name '{workflow_data.name}' already exists"
            )

        # Create workflow
        workflow = WorkflowDefinition(
            **workflow_data.model_dump(exclude={'states', 'transitions'}),
            tenant_id=self.tenant_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id
        )

        self.db.add(workflow)
        self.db.flush()

        # Create states if provided
        if workflow_data.states:
            for state_data in workflow_data.states:
                state = WorkflowState(
                    **state_data.model_dump(),
                    workflow_id=workflow.id,
                    tenant_id=self.tenant_id
                )
                self.db.add(state)

        # Create transitions if provided
        if workflow_data.transitions:
            for transition_data in workflow_data.transitions:
                transition = WorkflowTransition(
                    **transition_data.model_dump(),
                    workflow_id=workflow.id,
                    tenant_id=self.tenant_id
                )
                self.db.add(transition)

        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    async def list_workflows(
        self,
        entity_id: Optional[UUID] = None,
        category: Optional[str] = None,
        include_platform: bool = True
    ):
        """List all workflow definitions (tenant-specific and optionally platform-level)"""
        # Build tenant filter: include current tenant and optionally platform-level (tenant_id=NULL)
        if include_platform:
            tenant_filter = or_(
                WorkflowDefinition.tenant_id == self.tenant_id,
                WorkflowDefinition.tenant_id == None  # Platform-level workflows
            )
        else:
            tenant_filter = WorkflowDefinition.tenant_id == self.tenant_id

        query = self.db.query(WorkflowDefinition).filter(
            tenant_filter,
            WorkflowDefinition.is_deleted == False
        )

        if entity_id:
            query = query.filter(WorkflowDefinition.entity_id == entity_id)
        if category:
            query = query.filter(WorkflowDefinition.category == category)

        return query.all()

    async def get_workflow(self, workflow_id: UUID, include_platform: bool = True):
        """Get workflow definition by ID (checks tenant-specific and optionally platform-level)"""
        # Build tenant filter
        if include_platform:
            tenant_filter = or_(
                WorkflowDefinition.tenant_id == self.tenant_id,
                WorkflowDefinition.tenant_id == None  # Platform-level workflows
            )
        else:
            tenant_filter = WorkflowDefinition.tenant_id == self.tenant_id

        workflow = self.db.query(WorkflowDefinition).filter(
            WorkflowDefinition.id == workflow_id,
            tenant_filter,
            WorkflowDefinition.is_deleted == False
        ).first()

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )

        return workflow

    async def update_workflow(self, workflow_id: UUID, workflow_data: WorkflowDefinitionUpdate):
        """Update workflow definition"""
        workflow = await self.get_workflow(workflow_id)

        update_data = workflow_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(workflow, key, value)

        workflow.updated_by = self.current_user.id

        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    async def delete_workflow(self, workflow_id: UUID):
        """Delete workflow definition (soft delete)"""
        workflow = await self.get_workflow(workflow_id)

        workflow.is_deleted = True
        workflow.updated_by = self.current_user.id

        self.db.commit()

        return {"message": "Workflow deleted successfully"}

    async def publish_workflow(self, workflow_id: UUID):
        """Publish a workflow to make it active"""
        workflow = await self.get_workflow(workflow_id)

        if workflow.is_published:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow is already published"
            )

        # Validate workflow has at least one start state and one end state
        states = self.db.query(WorkflowState).filter(
            WorkflowState.workflow_id == workflow_id,
            WorkflowState.is_deleted == False
        ).all()

        start_states = [s for s in states if s.state_type == 'start']
        end_states = [s for s in states if s.is_final]

        if not start_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow must have at least one start state"
            )

        if not end_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow must have at least one end state"
            )

        workflow.is_published = True
        workflow.published_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    async def unpublish_workflow(self, workflow_id: UUID):
        """Unpublish a workflow to revert it to draft"""
        workflow = await self.get_workflow(workflow_id)

        if not workflow.is_published:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow is not published"
            )

        workflow.is_published = False
        workflow.published_at = None

        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    async def simulate_workflow(self, workflow_id: UUID, simulation_data):
        """Simulate a workflow execution for testing purposes"""
        workflow = await self.get_workflow(workflow_id)

        # Get all states and transitions
        states = self.db.query(WorkflowState).filter(
            WorkflowState.workflow_id == workflow_id,
            WorkflowState.is_deleted == False
        ).all()

        transitions = self.db.query(WorkflowTransition).filter(
            WorkflowTransition.workflow_id == workflow_id,
            WorkflowTransition.is_deleted == False
        ).all()

        if not states:
            return {
                "success": False,
                "steps": [],
                "message": "Workflow has no states defined"
            }

        # Find start state or use provided initial state
        start_state = None
        if simulation_data.initial_state_id:
            start_state = next((s for s in states if str(s.id) == str(simulation_data.initial_state_id)), None)

        if not start_state:
            start_state = next((s for s in states if s.state_type == 'start'), None)

        if not start_state:
            return {
                "success": False,
                "steps": [],
                "message": "No start state found in workflow"
            }

        # Simulate workflow execution
        simulation_steps = []
        current_state = start_state
        visited_states = set()
        max_iterations = 20  # Prevent infinite loops

        while current_state and len(simulation_steps) < max_iterations:
            if current_state.id in visited_states and current_state.state_type != 'start':
                break  # Prevent cycles

            visited_states.add(current_state.id)

            # Record step
            action = "Started" if current_state.state_type == 'start' else (
                "Completed" if current_state.is_final else "Transitioned"
            )
            simulation_steps.append({
                "state": current_state.label,
                "timestamp": datetime.utcnow(),
                "action": action
            })

            # If final state, stop
            if current_state.is_final or current_state.state_type == 'end':
                break

            # Find next transition
            available_transitions = [t for t in transitions if str(t.from_state_id) == str(current_state.id)]

            if not available_transitions:
                break

            # Take first available transition (in real simulation, this would be based on conditions)
            next_transition = available_transitions[0]
            next_state = next((s for s in states if str(s.id) == str(next_transition.to_state_id)), None)

            current_state = next_state

        return {
            "success": True,
            "steps": simulation_steps,
            "message": f"Simulation completed successfully with {len(simulation_steps)} steps"
        }

    # ==================== Workflow State Methods ====================

    async def create_state(self, workflow_id: UUID, state_data: WorkflowStateCreate):
        """Add a state to a workflow"""
        workflow = await self.get_workflow(workflow_id)

        # Check if state name already exists
        existing = self.db.query(WorkflowState).filter(
            WorkflowState.workflow_id == workflow_id,
            WorkflowState.name == state_data.name,
            WorkflowState.is_deleted == False
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"State with name '{state_data.name}' already exists"
            )

        state = WorkflowState(
            **state_data.model_dump(),
            workflow_id=workflow_id,
            tenant_id=self.tenant_id
        )

        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)

        return state

    async def list_states(self, workflow_id: UUID):
        """List all states for a workflow"""
        await self.get_workflow(workflow_id)  # Verify workflow exists

        return self.db.query(WorkflowState).filter(
            WorkflowState.workflow_id == workflow_id,
            WorkflowState.is_deleted == False
        ).all()

    async def update_state(self, workflow_id: UUID, state_id: UUID, state_data: WorkflowStateUpdate):
        """Update a workflow state"""
        state = self.db.query(WorkflowState).filter(
            WorkflowState.id == state_id,
            WorkflowState.workflow_id == workflow_id,
            WorkflowState.is_deleted == False
        ).first()

        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="State not found"
            )

        update_data = state_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(state, key, value)

        self.db.commit()
        self.db.refresh(state)

        return state

    # ==================== Workflow Transition Methods ====================

    async def create_transition(self, workflow_id: UUID, transition_data: WorkflowTransitionCreate):
        """Add a transition to a workflow"""
        workflow = await self.get_workflow(workflow_id)

        transition = WorkflowTransition(
            **transition_data.model_dump(),
            workflow_id=workflow_id,
            tenant_id=self.tenant_id
        )

        self.db.add(transition)
        self.db.commit()
        self.db.refresh(transition)

        return transition

    async def list_transitions(self, workflow_id: UUID):
        """List all transitions for a workflow"""
        await self.get_workflow(workflow_id)  # Verify workflow exists

        return self.db.query(WorkflowTransition).filter(
            WorkflowTransition.workflow_id == workflow_id,
            WorkflowTransition.is_deleted == False
        ).all()

    async def delete_transition(self, workflow_id: UUID, transition_id: UUID):
        """Delete a workflow transition (soft delete)"""
        await self.get_workflow(workflow_id)  # Verify workflow exists

        transition = self.db.query(WorkflowTransition).filter(
            WorkflowTransition.id == transition_id,
            WorkflowTransition.workflow_id == workflow_id,
            WorkflowTransition.is_deleted == False
        ).first()

        if not transition:
            raise HTTPException(status_code=404, detail="Transition not found")

        transition.is_deleted = True
        self.db.commit()

        return {"message": "Transition deleted successfully"}

    # ==================== Workflow Instance Methods ====================

    async def create_instance(self, instance_data: WorkflowInstanceCreate):
        """Start a new workflow instance"""
        workflow = await self.get_workflow(instance_data.workflow_id)

        if not workflow.is_published:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start instance of unpublished workflow"
            )

        # Find start state
        start_state = self.db.query(WorkflowState).filter(
            WorkflowState.workflow_id == instance_data.workflow_id,
            WorkflowState.state_type == 'start',
            WorkflowState.is_deleted == False
        ).first()

        if not start_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow has no start state"
            )

        # Create instance
        instance = WorkflowInstance(
            **instance_data.model_dump(),
            tenant_id=self.tenant_id,
            current_state_id=start_state.id,
            current_state_entered_at=datetime.utcnow(),
            started_by=self.current_user.id
        )

        self.db.add(instance)
        self.db.flush()

        # Create history entry
        history = WorkflowHistory(
            instance_id=instance.id,
            tenant_id=self.tenant_id,
            to_state_id=start_state.id,
            performed_by=self.current_user.id,
            action_type='start',
            comment='Workflow instance started'
        )
        self.db.add(history)

        # Execute on_entry actions for start state
        if start_state.on_entry_actions:
            await self._execute_actions(instance, start_state.on_entry_actions)

        self.db.commit()
        self.db.refresh(instance)

        return instance

    async def get_instance(self, instance_id: UUID):
        """Get workflow instance by ID"""
        instance = self.db.query(WorkflowInstance).filter(
            WorkflowInstance.id == instance_id,
            WorkflowInstance.tenant_id == self.tenant_id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow instance not found"
            )

        return instance

    async def list_instances(
        self,
        workflow_id: UUID = None,
        status: str = None,
        entity_id: UUID = None
    ):
        """List workflow instances with optional filters"""
        query = self.db.query(WorkflowInstance).filter(
            WorkflowInstance.tenant_id == self.tenant_id
        )

        if workflow_id:
            query = query.filter(WorkflowInstance.workflow_id == workflow_id)

        if status:
            query = query.filter(WorkflowInstance.status == status)

        if entity_id:
            query = query.filter(WorkflowInstance.entity_id == entity_id)

        instances = query.order_by(WorkflowInstance.started_at.desc()).all()
        return instances

    async def execute_transition(
        self,
        instance_id: UUID,
        transition_request: WorkflowTransitionExecuteRequest
    ):
        """Execute a workflow transition"""
        instance = await self.get_instance(instance_id)

        if instance.status != 'active':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot execute transition on non-active instance"
            )

        # Get transition
        transition = self.db.query(WorkflowTransition).filter(
            WorkflowTransition.id == transition_request.transition_id,
            WorkflowTransition.from_state_id == instance.current_state_id,
            WorkflowTransition.is_deleted == False
        ).first()

        if not transition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid transition from current state"
            )

        # Check permissions (simplified)
        # In production, check allowed_roles and allowed_users

        # Get from and to states
        from_state = self.db.query(WorkflowState).get(transition.from_state_id)
        to_state = self.db.query(WorkflowState).get(transition.to_state_id)

        # Calculate duration in previous state
        duration_minutes = None
        if instance.current_state_entered_at:
            delta = datetime.utcnow() - instance.current_state_entered_at
            duration_minutes = int(delta.total_seconds() / 60)

        # Execute on_exit actions for current state
        if from_state.on_exit_actions:
            await self._execute_actions(instance, from_state.on_exit_actions)

        # Execute transition actions
        if transition.actions:
            await self._execute_actions(instance, transition.actions)

        # Update instance
        instance.current_state_id = to_state.id
        instance.current_state_entered_at = datetime.utcnow()

        # Check if workflow is complete
        if to_state.is_final:
            instance.status = 'completed'
            instance.completed_at = datetime.utcnow()

        # Create history entry
        history = WorkflowHistory(
            instance_id=instance.id,
            tenant_id=self.tenant_id,
            from_state_id=from_state.id,
            to_state_id=to_state.id,
            transition_id=transition.id,
            performed_by=self.current_user.id,
            action_type='transition',
            comment=transition_request.comment,
            duration_minutes=duration_minutes
        )
        self.db.add(history)

        # Execute on_entry actions for new state
        if to_state.on_entry_actions:
            await self._execute_actions(instance, to_state.on_entry_actions)

        self.db.commit()
        self.db.refresh(instance)

        return instance

    async def get_instance_history(self, instance_id: UUID):
        """Get history for a workflow instance"""
        await self.get_instance(instance_id)  # Verify instance exists

        return self.db.query(WorkflowHistory).filter(
            WorkflowHistory.instance_id == instance_id
        ).order_by(WorkflowHistory.performed_at).all()

    async def get_available_transitions(self, instance_id: UUID):
        """Get available transitions from current state"""
        instance = await self.get_instance(instance_id)

        if instance.status != 'active':
            return []

        transitions = self.db.query(WorkflowTransition).filter(
            WorkflowTransition.from_state_id == instance.current_state_id,
            WorkflowTransition.is_deleted == False
        ).all()

        return transitions

    async def _execute_actions(self, instance: WorkflowInstance, actions: list):
        """Execute workflow actions (simplified implementation)"""
        # This is a simplified implementation
        # In production, this would execute various action types:
        # - Send email
        # - Update record
        # - Call webhook
        # - etc.
        for action in actions:
            action_type = action.get('type')
            # Log action execution
            print(f"Executing action: {action_type} for instance {instance.id}")
            # Action execution logic would go here
