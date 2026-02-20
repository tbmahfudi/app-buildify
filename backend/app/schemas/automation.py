"""
Automation System - Pydantic Schemas

Request/Response schemas for the Automation System API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ==================== Automation Rule Schemas ====================

class AutomationRuleBase(BaseModel):
    """Base schema for automation rules"""
    name: str = Field(..., max_length=100)
    label: str = Field(..., max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    trigger_type: str = Field(..., description="database_event, scheduled, user_action, webhook, manual")
    trigger_config: Dict[str, Any] = Field(default_factory=dict, description="Trigger-specific configuration")
    entity_id: Optional[UUID] = None
    event_type: Optional[str] = None
    trigger_timing: Optional[str] = None
    schedule_type: Optional[str] = None
    cron_expression: Optional[str] = None
    schedule_interval: Optional[int] = None
    schedule_timezone: str = "UTC"
    has_conditions: bool = False
    conditions: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Array of actions to execute")
    execution_order: int = 0
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 300
    allow_concurrent: bool = True
    max_concurrent_instances: Optional[int] = None
    on_error_action: str = "stop"
    error_notification_emails: List[str] = Field(default_factory=list)
    is_async: bool = True
    is_test_mode: bool = False
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class AutomationRuleCreate(AutomationRuleBase):
    """Schema for creating an automation rule"""
    is_active: bool = False  # Default to inactive, user can enable from list


class AutomationRuleUpdate(BaseModel):
    """Schema for updating an automation rule"""
    label: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    event_type: Optional[str] = None
    trigger_timing: Optional[str] = None
    schedule_type: Optional[str] = None
    cron_expression: Optional[str] = None
    schedule_interval: Optional[int] = None
    has_conditions: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    execution_order: Optional[int] = None
    max_retries: Optional[int] = None
    is_active: Optional[bool] = None
    is_test_mode: Optional[bool] = None
    meta_data: Optional[Dict[str, Any]] = None


class AutomationRuleResponse(AutomationRuleBase):
    """Schema for automation rule response"""
    id: UUID
    tenant_id: Optional[UUID]  # NULL for platform-level automation rules
    module_id: Optional[UUID] = None
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    is_active: bool
    version: int
    is_published: bool
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time_ms: Optional[int]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    deleted_at: Optional[datetime]
    is_deleted: bool

    @field_validator('actions', mode='before')
    @classmethod
    def set_actions_default(cls, v):
        return v if v is not None else []

    @field_validator('conditions', mode='before')
    @classmethod
    def set_conditions_default(cls, v):
        return v if v is not None else {}

    @field_validator('trigger_config', mode='before')
    @classmethod
    def set_trigger_config_default(cls, v):
        return v if v is not None else {}

    class Config:
        from_attributes = True


# ==================== Automation Execution Schemas ====================

class AutomationExecutionResponse(BaseModel):
    """Schema for automation execution response"""
    id: UUID
    rule_id: UUID
    tenant_id: Optional[UUID]  # NULL for platform-level automation executions
    trigger_type: str
    triggered_by_user_id: Optional[UUID]
    triggered_at: datetime
    entity_id: Optional[UUID]
    record_id: Optional[UUID]
    record_data_before: Optional[Dict[str, Any]]
    record_data_after: Optional[Dict[str, Any]]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time_ms: Optional[int]
    conditions_met: Optional[bool]
    condition_evaluation_result: Optional[Dict[str, Any]]
    total_actions: int
    completed_actions: int
    failed_actions: int
    action_results: List[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int
    next_retry_at: Optional[datetime]
    context_data: Dict[str, Any]
    meta_data: Dict[str, Any]

    class Config:
        from_attributes = True


class AutomationTestRequest(BaseModel):
    """Schema for testing an automation rule"""
    test_data: Dict[str, Any] = Field(..., description="Test data for the automation")
    dry_run: bool = Field(True, description="Don't execute actual actions")


class AutomationTestResponse(BaseModel):
    """Schema for automation test response"""
    success: bool
    conditions_met: bool
    condition_evaluation: Dict[str, Any]
    actions_preview: List[Dict[str, Any]]
    estimated_duration_ms: int
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


# ==================== Action Template Schemas ====================

class ActionTemplateResponse(BaseModel):
    """Schema for action template response"""
    id: UUID
    tenant_id: Optional[UUID]
    name: str
    label: str
    description: Optional[str]
    category: Optional[str]
    action_type: str
    config_schema: Dict[str, Any]
    default_config: Dict[str, Any]
    icon: Optional[str]
    color: Optional[str]
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Webhook Config Schemas ====================

class WebhookConfigBase(BaseModel):
    """Base schema for webhook configs"""
    name: str = Field(..., max_length=100)
    label: str = Field(..., max_length=200)
    description: Optional[str] = None
    webhook_type: str = Field(..., description="inbound or outbound")
    endpoint_path: Optional[str] = None
    secret_token: Optional[str] = None
    allowed_ips: List[str] = Field(default_factory=list)
    target_url: Optional[str] = None
    http_method: str = "POST"
    headers: Dict[str, str] = Field(default_factory=dict)
    authentication_type: Optional[str] = None
    authentication_config: Dict[str, Any] = Field(default_factory=dict)
    payload_template: Optional[str] = None
    payload_mapping: Dict[str, Any] = Field(default_factory=dict)
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 30
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class WebhookConfigCreate(WebhookConfigBase):
    """Schema for creating a webhook config"""
    pass


class WebhookConfigUpdate(BaseModel):
    """Schema for updating a webhook config"""
    label: Optional[str] = None
    description: Optional[str] = None
    secret_token: Optional[str] = None
    allowed_ips: Optional[List[str]] = None
    target_url: Optional[str] = None
    http_method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    authentication_config: Optional[Dict[str, Any]] = None
    payload_template: Optional[str] = None
    payload_mapping: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    meta_data: Optional[Dict[str, Any]] = None


class WebhookConfigResponse(WebhookConfigBase):
    """Schema for webhook config response"""
    id: UUID
    tenant_id: Optional[UUID]  # NULL for platform-level webhook configs
    is_active: bool
    total_calls: int
    successful_calls: int
    failed_calls: int
    last_called_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    is_deleted: bool

    class Config:
        from_attributes = True
