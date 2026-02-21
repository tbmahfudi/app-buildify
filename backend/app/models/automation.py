"""
Automation System - Database Models

Models for the no-code platform's automation and trigger system.
Enables event-based automation without writing code.
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


class AutomationRule(Base):
    """
    Automation Rule Model

    Stores automation rules with triggers, conditions, and actions.
    """
    __tablename__ = "automation_rules"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    # tenant_id: NULL = platform-level (shared across tenants), specific ID = tenant-specific
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True, index=True)
    # module_id: Associates automation with a specific module (optional)
    module_id = Column(GUID, ForeignKey("modules.id"), nullable=True, index=True)

    # Basic Info
    name = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))

    # Trigger Configuration
    trigger_type = Column(String(50), nullable=False)  # 'database_event', 'scheduled', 'user_action', 'webhook', 'manual'
    trigger_config = Column(JSONB, nullable=False)  # Trigger-specific configuration

    # Entity Association (for database events)
    entity_id = Column(GUID, ForeignKey("entity_definitions.id"))

    # Database Event Triggers
    event_type = Column(String(50))  # 'create', 'update', 'delete', 'any'
    trigger_timing = Column(String(20))  # 'before', 'after'

    # Schedule Configuration (for scheduled triggers)
    schedule_type = Column(String(50))  # 'cron', 'interval', 'one_time'
    cron_expression = Column(String(100))  # For cron schedules
    schedule_interval = Column(Integer)  # Minutes for interval schedules
    schedule_timezone = Column(String(50), default="UTC")
    next_run_at = Column(DateTime)
    last_run_at = Column(DateTime)

    # Conditions (if-then-else logic)
    has_conditions = Column(Boolean, default=False)
    conditions = Column(JSONB, default=dict)  # Condition tree structure

    # Actions
    actions = Column(JSONB, nullable=False, default=list)  # Array of actions to execute

    # Execution Settings
    execution_order = Column(Integer, default=0)  # Order when multiple rules match
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    timeout_seconds = Column(Integer, default=300)

    # Concurrency Control
    allow_concurrent = Column(Boolean, default=True)
    max_concurrent_instances = Column(Integer)

    # Error Handling
    on_error_action = Column(String(50), default="stop")  # 'stop', 'continue', 'retry'
    error_notification_emails = Column(JSONB, default=list)

    # Status & Control
    is_active = Column(Boolean, default=True)
    is_async = Column(Boolean, default=True)  # Execute asynchronously?

    # Testing
    is_test_mode = Column(Boolean, default=False)  # Don't execute actions in test mode

    # Statistics
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    average_execution_time_ms = Column(Integer)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Version Control
    version = Column(Integer, default=1)
    is_published = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))
    updated_by = Column(GUID, ForeignKey("users.id"))
    deleted_at = Column(DateTime)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    executions = relationship("AutomationExecution", back_populates="rule")

    # Table constraints
    __table_args__ = (
        Index("idx_automation_rules_tenant", "tenant_id", postgresql_where=text("is_deleted = false")),
        Index("idx_automation_rules_entity", "entity_id", postgresql_where=text("is_active = true")),
        Index("idx_automation_rules_trigger_type", "trigger_type", postgresql_where=text("is_active = true")),
        Index("idx_automation_rules_next_run", "next_run_at", postgresql_where=text("is_active = true AND schedule_type IS NOT NULL")),
        Index("idx_automation_rules_event", "entity_id", "event_type", postgresql_where=text("is_active = true")),
    )


class AutomationExecution(Base):
    """
    Automation Execution Model

    Tracks individual executions of automation rules.
    """
    __tablename__ = "automation_executions"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    rule_id = Column(GUID, ForeignKey("automation_rules.id"), nullable=False, index=True)
    # tenant_id: NULL = platform-level execution, specific ID = tenant-specific execution
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True)

    # Trigger Context
    trigger_type = Column(String(50), nullable=False)
    triggered_by_user_id = Column(GUID, ForeignKey("users.id"))
    triggered_at = Column(DateTime, default=datetime.utcnow)

    # Entity Context (for database events)
    entity_id = Column(GUID, ForeignKey("entity_definitions.id"))
    record_id = Column(GUID)  # ID of the record that triggered the rule
    record_data_before = Column(JSONB)  # Snapshot before change (for updates)
    record_data_after = Column(JSONB)  # Snapshot after change

    # Execution Status
    status = Column(String(50), default="pending")  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time_ms = Column(Integer)

    # Condition Evaluation
    conditions_met = Column(Boolean)
    condition_evaluation_result = Column(JSONB)  # Details of condition evaluation

    # Actions Execution
    total_actions = Column(Integer, default=0)
    completed_actions = Column(Integer, default=0)
    failed_actions = Column(Integer, default=0)
    action_results = Column(JSONB, default=list)  # Results of each action

    # Error Handling
    error_message = Column(Text)
    error_stack_trace = Column(Text)
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime)

    # Context Data
    context_data = Column(JSONB, default=dict)  # Additional context for the execution

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Relationships
    rule = relationship("AutomationRule", back_populates="executions")

    # Table constraints
    __table_args__ = (
        Index("idx_automation_executions_rule", "rule_id"),
        Index("idx_automation_executions_status", "status"),
        Index("idx_automation_executions_record", "entity_id", "record_id"),
        Index("idx_automation_executions_triggered_at", "triggered_at"),
        Index("idx_automation_executions_retry", "next_retry_at", postgresql_where=text("status = 'failed'")),
    )


class ActionTemplate(Base):
    """
    Action Template Model

    Stores reusable action templates for automations.
    """
    __tablename__ = "action_templates"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True)  # NULL for system templates

    # Basic Info
    name = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))

    # Action Type
    action_type = Column(String(50), nullable=False)  # 'send_email', 'webhook', 'update_record', 'create_record', etc.

    # Template Configuration
    config_schema = Column(JSONB, nullable=False)  # JSON schema for action configuration
    default_config = Column(JSONB, default=dict)

    # Display
    icon = Column(String(50))
    color = Column(String(50))

    # System vs Custom
    is_system = Column(Boolean, default=False)  # System templates can't be modified

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)

    # Table constraints
    __table_args__ = (
        Index("idx_action_templates_tenant", "tenant_id"),
        Index("idx_action_templates_type", "action_type", postgresql_where=text("is_active = true")),
    )


class WebhookConfig(Base):
    """
    Webhook Configuration Model

    Stores webhook configurations for inbound and outbound webhooks.
    """
    __tablename__ = "webhook_configs"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    # tenant_id: NULL = platform-level webhook, specific ID = tenant-specific webhook
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True)

    # module_id: Associates webhook with a specific module (optional)
    module_id = Column(GUID, ForeignKey("modules.id"), nullable=True, index=True)

    # Basic Info
    name = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text)

    # Webhook Type
    webhook_type = Column(String(50), nullable=False)  # 'inbound', 'outbound'

    # Inbound Webhook Config
    endpoint_path = Column(String(200))  # Unique path: /webhooks/{endpoint_path}
    secret_token = Column(String(255))  # For validating incoming requests
    allowed_ips = Column(JSONB, default=list)  # IP whitelist

    # Outbound Webhook Config
    target_url = Column(String(500))  # External URL to call
    http_method = Column(String(10), default="POST")  # GET, POST, PUT, DELETE
    headers = Column(JSONB, default=dict)  # HTTP headers
    authentication_type = Column(String(50))  # 'none', 'basic', 'bearer', 'api_key', 'oauth2'
    authentication_config = Column(JSONB, default=dict)

    # Payload Configuration
    payload_template = Column(Text)  # Template for outbound payload
    payload_mapping = Column(JSONB, default=dict)  # Field mapping

    # Retry Configuration
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    timeout_seconds = Column(Integer, default=30)

    # Status
    is_active = Column(Boolean, default=True)

    # Statistics
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    last_called_at = Column(DateTime)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))
    updated_by = Column(GUID, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)

    # Table constraints
    __table_args__ = (
        Index("idx_webhook_configs_tenant", "tenant_id", postgresql_where=text("is_deleted = false")),
        Index("idx_webhook_configs_endpoint", "endpoint_path", postgresql_where=text("webhook_type = 'inbound'")),
    )
