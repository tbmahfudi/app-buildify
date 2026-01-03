"""
Automation System API Router

API endpoints for the Automation System feature.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.automation import (
    AutomationRuleCreate,
    AutomationRuleUpdate,
    AutomationRuleResponse,
    AutomationExecutionResponse,
    ActionTemplateResponse,
    WebhookConfigCreate,
    WebhookConfigUpdate,
    WebhookConfigResponse,
    AutomationTestRequest,
    AutomationTestResponse,
)
from app.services.automation_service import AutomationService


router = APIRouter(prefix="/api/v1/automations", tags=["Automation System"])


# ==================== Automation Rule Endpoints ====================

@router.post("/rules", response_model=AutomationRuleResponse)
async def create_automation_rule(
    rule: AutomationRuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new automation rule"""
    service = AutomationService(db, current_user)
    return await service.create_rule(rule)


@router.get("/rules", response_model=List[AutomationRuleResponse])
async def list_automation_rules(
    entity_id: Optional[UUID] = Query(None),
    trigger_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all automation rules"""
    service = AutomationService(db, current_user)
    return await service.list_rules(entity_id, trigger_type, category, is_active)


@router.get("/rules/{rule_id}", response_model=AutomationRuleResponse)
async def get_automation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get automation rule details"""
    service = AutomationService(db, current_user)
    return await service.get_rule(rule_id)


@router.put("/rules/{rule_id}", response_model=AutomationRuleResponse)
async def update_automation_rule(
    rule_id: UUID,
    rule: AutomationRuleUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update automation rule"""
    service = AutomationService(db, current_user)
    return await service.update_rule(rule_id, rule)


@router.delete("/rules/{rule_id}")
async def delete_automation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete automation rule"""
    service = AutomationService(db, current_user)
    return await service.delete_rule(rule_id)


@router.post("/rules/{rule_id}/toggle", response_model=AutomationRuleResponse)
async def toggle_automation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Toggle automation rule active status"""
    service = AutomationService(db, current_user)
    return await service.toggle_rule(rule_id)


@router.post("/rules/{rule_id}/test", response_model=AutomationTestResponse)
async def test_automation_rule(
    rule_id: UUID,
    test_request: AutomationTestRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Test an automation rule"""
    service = AutomationService(db, current_user)
    return await service.test_rule(rule_id, test_request)


@router.post("/rules/{rule_id}/execute")
async def execute_automation_rule(
    rule_id: UUID,
    context_data: dict = {},
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Execute an automation rule manually"""
    service = AutomationService(db, current_user)
    return await service.execute_rule(rule_id, context_data)


# ==================== Automation Execution Endpoints ====================

@router.get("/executions", response_model=List[AutomationExecutionResponse])
async def list_automation_executions(
    rule_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List automation executions"""
    service = AutomationService(db, current_user)
    return await service.list_executions(rule_id, status, limit)


@router.get("/executions/{execution_id}", response_model=AutomationExecutionResponse)
async def get_automation_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get automation execution details"""
    service = AutomationService(db, current_user)
    return await service.get_execution(execution_id)


# ==================== Action Template Endpoints ====================

@router.get("/action-templates", response_model=List[ActionTemplateResponse])
async def list_action_templates(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all available action templates"""
    service = AutomationService(db, current_user)
    return await service.list_action_templates()


# ==================== Webhook Config Endpoints ====================

@router.post("/webhooks", response_model=WebhookConfigResponse)
async def create_webhook_config(
    webhook: WebhookConfigCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new webhook configuration"""
    service = AutomationService(db, current_user)
    return await service.create_webhook(webhook)


@router.get("/webhooks", response_model=List[WebhookConfigResponse])
async def list_webhook_configs(
    webhook_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List webhook configurations"""
    service = AutomationService(db, current_user)
    return await service.list_webhooks(webhook_type)


@router.get("/webhooks/{webhook_id}", response_model=WebhookConfigResponse)
async def get_webhook_config(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get webhook configuration"""
    service = AutomationService(db, current_user)
    return await service.get_webhook(webhook_id)


@router.put("/webhooks/{webhook_id}", response_model=WebhookConfigResponse)
async def update_webhook_config(
    webhook_id: UUID,
    webhook: WebhookConfigUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update webhook configuration"""
    service = AutomationService(db, current_user)
    return await service.update_webhook(webhook_id, webhook)


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook_config(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete webhook configuration"""
    service = AutomationService(db, current_user)
    return await service.delete_webhook(webhook_id)
