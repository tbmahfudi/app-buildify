"""
Automation System Service

Business logic for the Automation System feature.
Handles trigger detection and action execution.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.automation import (
    AutomationRule,
    AutomationExecution,
    ActionTemplate,
    WebhookConfig,
)
from app.schemas.automation import (
    AutomationRuleCreate,
    AutomationRuleUpdate,
    WebhookConfigCreate,
    WebhookConfigUpdate,
    AutomationTestRequest,
)


class AutomationService:
    """Service for managing automation rules and executions"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self.tenant_id = current_user.tenant_id

    # ==================== Automation Rule Methods ====================

    async def create_rule(self, rule_data: AutomationRuleCreate):
        """Create a new automation rule"""
        # Check if rule name already exists
        existing = self.db.query(AutomationRule).filter(
            AutomationRule.tenant_id == self.tenant_id,
            AutomationRule.name == rule_data.name,
            AutomationRule.is_deleted == False
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Automation rule with name '{rule_data.name}' already exists"
            )

        rule = AutomationRule(
            **rule_data.model_dump(),
            tenant_id=self.tenant_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        return rule

    async def list_rules(
        self,
        entity_id: Optional[UUID] = None,
        trigger_type: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_platform: bool = True
    ):
        """List all automation rules (tenant-specific and optionally platform-level)"""
        from sqlalchemy import or_

        # Build tenant filter: include current tenant and optionally platform-level (tenant_id=NULL)
        if include_platform:
            tenant_filter = or_(
                AutomationRule.tenant_id == self.tenant_id,
                AutomationRule.tenant_id == None  # Platform-level rules
            )
        else:
            tenant_filter = AutomationRule.tenant_id == self.tenant_id

        query = self.db.query(AutomationRule).filter(
            tenant_filter,
            AutomationRule.is_deleted == False
        )

        if entity_id:
            query = query.filter(AutomationRule.entity_id == entity_id)
        if trigger_type:
            query = query.filter(AutomationRule.trigger_type == trigger_type)
        if category:
            query = query.filter(AutomationRule.category == category)
        if is_active is not None:
            query = query.filter(AutomationRule.is_active == is_active)

        return query.all()

    async def get_rule(self, rule_id: UUID, include_platform: bool = True):
        """Get automation rule by ID (checks tenant-specific and optionally platform-level)"""
        from sqlalchemy import or_

        # Build tenant filter
        if include_platform:
            tenant_filter = or_(
                AutomationRule.tenant_id == self.tenant_id,
                AutomationRule.tenant_id == None  # Platform-level rules
            )
        else:
            tenant_filter = AutomationRule.tenant_id == self.tenant_id

        rule = self.db.query(AutomationRule).filter(
            AutomationRule.id == rule_id,
            tenant_filter,
            AutomationRule.is_deleted == False
        ).first()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Automation rule not found"
            )

        return rule

    async def update_rule(self, rule_id: UUID, rule_data: AutomationRuleUpdate):
        """Update automation rule"""
        rule = await self.get_rule(rule_id)

        update_data = rule_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rule, key, value)

        rule.updated_by = self.current_user.id

        self.db.commit()
        self.db.refresh(rule)

        return rule

    async def delete_rule(self, rule_id: UUID):
        """Delete automation rule (soft delete)"""
        rule = await self.get_rule(rule_id)

        rule.is_deleted = True
        rule.updated_by = self.current_user.id

        self.db.commit()

        return {"message": "Automation rule deleted successfully"}

    async def toggle_rule(self, rule_id: UUID):
        """Toggle automation rule active status"""
        rule = await self.get_rule(rule_id)

        rule.is_active = not rule.is_active
        rule.updated_by = self.current_user.id

        self.db.commit()
        self.db.refresh(rule)

        return rule

    async def test_rule(self, rule_id: UUID, test_request: AutomationTestRequest):
        """Test an automation rule"""
        rule = await self.get_rule(rule_id)

        # Evaluate conditions
        conditions_met = await self._evaluate_conditions(
            rule.conditions,
            test_request.test_data
        )

        # Preview actions
        actions_preview = []
        for action in rule.actions:
            actions_preview.append({
                "type": action.get("type"),
                "config": action.get("config"),
                "will_execute": conditions_met
            })

        return {
            "success": True,
            "conditions_met": conditions_met,
            "condition_evaluation": {"test": "evaluation"},
            "actions_preview": actions_preview,
            "estimated_duration_ms": 100,
            "warnings": [],
            "errors": []
        }

    # ==================== Automation Execution Methods ====================

    async def list_executions(
        self,
        rule_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 50
    ):
        """List automation executions"""
        query = self.db.query(AutomationExecution).filter(
            AutomationExecution.tenant_id == self.tenant_id
        )

        if rule_id:
            query = query.filter(AutomationExecution.rule_id == rule_id)
        if status:
            query = query.filter(AutomationExecution.status == status)

        return query.order_by(AutomationExecution.triggered_at.desc()).limit(limit).all()

    async def get_execution(self, execution_id: UUID):
        """Get automation execution by ID"""
        execution = self.db.query(AutomationExecution).filter(
            AutomationExecution.id == execution_id,
            AutomationExecution.tenant_id == self.tenant_id
        ).first()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Automation execution not found"
            )

        return execution

    async def execute_rule(self, rule_id: UUID, context_data: dict):
        """Execute an automation rule manually"""
        rule = await self.get_rule(rule_id)

        if not rule.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot execute inactive rule"
            )

        # Create execution record
        execution = AutomationExecution(
            rule_id=rule_id,
            tenant_id=self.tenant_id,
            trigger_type="manual",
            triggered_by_user_id=self.current_user.id,
            context_data=context_data,
            total_actions=len(rule.actions)
        )

        self.db.add(execution)
        self.db.flush()

        # Execute in test mode if configured
        if rule.is_test_mode:
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            return execution

        # Evaluate conditions
        conditions_met = await self._evaluate_conditions(
            rule.conditions,
            context_data
        )

        execution.conditions_met = conditions_met
        execution.status = "running"
        execution.started_at = datetime.utcnow()

        if not conditions_met:
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            return execution

        # Execute actions
        action_results = []
        for action in rule.actions:
            try:
                result = await self._execute_action(action, context_data)
                action_results.append(result)
                execution.completed_actions += 1
            except Exception as e:
                action_results.append({
                    "success": False,
                    "error": str(e)
                })
                execution.failed_actions += 1

        execution.action_results = action_results
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()

        if execution.started_at:
            duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.execution_time_ms = int(duration * 1000)

        self.db.commit()
        self.db.refresh(execution)

        return execution

    # ==================== Action Template Methods ====================

    async def list_action_templates(self):
        """List all available action templates"""
        return self.db.query(ActionTemplate).filter(
            (ActionTemplate.tenant_id == self.tenant_id) |
            (ActionTemplate.is_system == True),
            ActionTemplate.is_deleted == False,
            ActionTemplate.is_active == True
        ).all()

    # ==================== Webhook Config Methods ====================

    async def create_webhook(self, webhook_data: WebhookConfigCreate):
        """Create a new webhook configuration"""
        webhook = WebhookConfig(
            **webhook_data.model_dump(),
            tenant_id=self.tenant_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id
        )

        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)

        return webhook

    async def list_webhooks(self, webhook_type: Optional[str] = None):
        """List webhook configurations"""
        query = self.db.query(WebhookConfig).filter(
            WebhookConfig.tenant_id == self.tenant_id,
            WebhookConfig.is_deleted == False
        )

        if webhook_type:
            query = query.filter(WebhookConfig.webhook_type == webhook_type)

        return query.all()

    async def get_webhook(self, webhook_id: UUID):
        """Get webhook configuration by ID"""
        webhook = self.db.query(WebhookConfig).filter(
            WebhookConfig.id == webhook_id,
            WebhookConfig.tenant_id == self.tenant_id,
            WebhookConfig.is_deleted == False
        ).first()

        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook configuration not found"
            )

        return webhook

    async def update_webhook(self, webhook_id: UUID, webhook_data: WebhookConfigUpdate):
        """Update webhook configuration"""
        webhook = await self.get_webhook(webhook_id)

        update_data = webhook_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(webhook, key, value)

        webhook.updated_by = self.current_user.id

        self.db.commit()
        self.db.refresh(webhook)

        return webhook

    async def delete_webhook(self, webhook_id: UUID):
        """Delete webhook configuration"""
        webhook = await self.get_webhook(webhook_id)

        webhook.is_deleted = True
        webhook.updated_by = self.current_user.id

        self.db.commit()

        return {"message": "Webhook configuration deleted successfully"}

    # ==================== Helper Methods ====================

    async def _evaluate_conditions(self, conditions: dict, context_data: dict) -> bool:
        """Evaluate automation conditions (simplified)"""
        if not conditions:
            return True

        # Simplified condition evaluation
        # In production, implement full condition tree evaluation
        return True

    async def _execute_action(self, action: dict, context_data: dict):
        """Execute a single action (simplified)"""
        action_type = action.get("type")

        # Simplified action execution
        # In production, implement:
        # - send_email
        # - webhook
        # - update_record
        # - create_record
        # - etc.

        return {
            "success": True,
            "action_type": action_type,
            "message": f"Action {action_type} executed"
        }
