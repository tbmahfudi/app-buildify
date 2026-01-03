"""Phase 1 No-Code Platform - All features

Revision ID: pg_phase1_nocode
Revises: pg_001_initial_builder
Create Date: 2026-01-02 00:00:00.000000

Creates tables for:
- Priority 1: Data Model Designer
- Priority 2: Workflow Designer
- Priority 3: Automation System
- Priority 4: Lookup Configuration
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision = 'pg_phase1_nocode'
down_revision = 'pg_001_initial_builder'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== Priority 1: Data Model Designer ====================

    # Create entity_definitions table
    op.create_table(
        'entity_definitions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False, index=True),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('plural_label', sa.String(200)),
        sa.Column('description', sa.Text),
        sa.Column('icon', sa.String(50)),

        # Type & Category
        sa.Column('entity_type', sa.String(50), default='custom'),
        sa.Column('category', sa.String(100)),

        # Table Info
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('schema_name', sa.String(100), default='public'),

        # Configuration
        sa.Column('is_audited', sa.Boolean, default=True),
        sa.Column('is_versioned', sa.Boolean, default=False),
        sa.Column('supports_soft_delete', sa.Boolean, default=True),
        sa.Column('supports_attachments', sa.Boolean, default=True),
        sa.Column('supports_comments', sa.Boolean, default=True),

        # Layout & Display
        sa.Column('primary_field', sa.String(100)),
        sa.Column('default_sort_field', sa.String(100)),
        sa.Column('default_sort_order', sa.String(10), default='ASC'),
        sa.Column('records_per_page', sa.Integer, default=25),

        # Status
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('is_active', sa.Boolean, default=True),

        # Metadata
        sa.Column('metadata', JSONB, default='{}'),

        # Versioning
        sa.Column('version', sa.Integer, default=1),
        sa.Column('parent_version_id', sa.String(36), sa.ForeignKey('entity_definitions.id')),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('updated_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('deleted_at', sa.DateTime),
        sa.Column('is_deleted', sa.Boolean, default=False),

        sa.UniqueConstraint('tenant_id', 'name', name='uq_entity_def_name'),
        sa.UniqueConstraint('tenant_id', 'table_name', name='uq_entity_def_table'),
    )

    op.create_index('idx_entity_definitions_tenant', 'entity_definitions', ['tenant_id'],
                    postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_entity_definitions_status', 'entity_definitions', ['status'])
    op.create_index('idx_entity_definitions_type', 'entity_definitions', ['entity_type'])

    # Create field_definitions table
    op.create_table(
        'field_definitions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('help_text', sa.Text),

        # Field Type
        sa.Column('field_type', sa.String(50), nullable=False),
        sa.Column('data_type', sa.String(50), nullable=False),

        # Constraints
        sa.Column('is_required', sa.Boolean, default=False),
        sa.Column('is_unique', sa.Boolean, default=False),
        sa.Column('is_indexed', sa.Boolean, default=False),
        sa.Column('is_nullable', sa.Boolean, default=True),

        # String Constraints
        sa.Column('max_length', sa.Integer),
        sa.Column('min_length', sa.Integer),

        # Numeric Constraints
        sa.Column('max_value', sa.Numeric),
        sa.Column('min_value', sa.Numeric),
        sa.Column('decimal_places', sa.Integer),

        # Default Value
        sa.Column('default_value', sa.Text),
        sa.Column('default_expression', sa.Text),

        # Validation
        sa.Column('validation_rules', JSONB, default='[]'),
        sa.Column('allowed_values', JSONB),

        # Display & Behavior
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('is_readonly', sa.Boolean, default=False),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('is_calculated', sa.Boolean, default=False),
        sa.Column('calculation_formula', sa.Text),

        # UI Configuration
        sa.Column('input_type', sa.String(50)),
        sa.Column('placeholder', sa.Text),
        sa.Column('prefix', sa.Text),
        sa.Column('suffix', sa.Text),

        # Relationship Fields
        sa.Column('reference_entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id')),
        sa.Column('reference_field', sa.String(100)),
        sa.Column('relationship_type', sa.String(50)),

        # Metadata
        sa.Column('metadata', JSONB, default='{}'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('updated_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('is_deleted', sa.Boolean, default=False),

        sa.UniqueConstraint('entity_id', 'name', name='uq_field_def_name'),
    )

    op.create_index('idx_field_definitions_entity', 'field_definitions', ['entity_id'],
                    postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_field_definitions_type', 'field_definitions', ['field_type'])

    # Create relationship_definitions table
    op.create_table(
        'relationship_definitions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),

        # Relationship Type
        sa.Column('relationship_type', sa.String(50), nullable=False),

        # Source Entity
        sa.Column('source_entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id'), nullable=False, index=True),
        sa.Column('source_field_name', sa.String(100)),

        # Target Entity
        sa.Column('target_entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id'), nullable=False, index=True),
        sa.Column('target_field_name', sa.String(100)),

        # Junction Table (for many-to-many)
        sa.Column('junction_table_name', sa.String(100)),
        sa.Column('junction_source_field', sa.String(100)),
        sa.Column('junction_target_field', sa.String(100)),

        # Cascade Behavior
        sa.Column('on_delete', sa.String(50), default='NO ACTION'),
        sa.Column('on_update', sa.String(50), default='NO ACTION'),

        # Display Configuration
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('display_in_source', sa.Boolean, default=True),
        sa.Column('display_in_target', sa.Boolean, default=True),

        # Metadata
        sa.Column('metadata', JSONB, default='{}'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('updated_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('is_deleted', sa.Boolean, default=False),

        sa.UniqueConstraint('tenant_id', 'name', name='uq_relationship_def_name'),
    )

    op.create_index('idx_relationship_definitions_source', 'relationship_definitions', ['source_entity_id'])
    op.create_index('idx_relationship_definitions_target', 'relationship_definitions', ['target_entity_id'])

    # Create index_definitions table
    op.create_table(
        'index_definitions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('index_type', sa.String(50), default='btree'),

        # Fields (ordered)
        sa.Column('field_names', JSONB, nullable=False),

        # Configuration
        sa.Column('is_unique', sa.Boolean, default=False),
        sa.Column('is_partial', sa.Boolean, default=False),
        sa.Column('where_clause', sa.Text),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('is_deleted', sa.Boolean, default=False),

        sa.UniqueConstraint('entity_id', 'name', name='uq_index_def_name'),
    )

    op.create_index('idx_index_definitions_entity', 'index_definitions', ['entity_id'])

    # Create entity_migrations table
    op.create_table(
        'entity_migrations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id'), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Migration Info
        sa.Column('migration_name', sa.String(200), nullable=False),
        sa.Column('migration_type', sa.String(50), nullable=False),

        # Version Info
        sa.Column('from_version', sa.Integer),
        sa.Column('to_version', sa.Integer, nullable=False),

        # SQL Scripts
        sa.Column('up_script', sa.Text, nullable=False),
        sa.Column('down_script', sa.Text),

        # Execution
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('executed_at', sa.DateTime),
        sa.Column('execution_time_ms', sa.Integer),
        sa.Column('error_message', sa.Text),

        # Metadata
        sa.Column('changes', JSONB),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
    )

    op.create_index('idx_entity_migrations_entity', 'entity_migrations', ['entity_id'])
    op.create_index('idx_entity_migrations_status', 'entity_migrations', ['status'])

    # ==================== Priority 2: Workflow Designer ====================

    # Create workflow_definitions table
    op.create_table(
        'workflow_definitions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False, index=True),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(100)),

        # Associated Entity
        sa.Column('entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id')),

        # Configuration
        sa.Column('trigger_type', sa.String(50), default='manual'),
        sa.Column('trigger_conditions', JSONB),

        # Canvas Data
        sa.Column('canvas_data', JSONB, nullable=False),

        # Version Control
        sa.Column('version', sa.Integer, default=1),
        sa.Column('is_published', sa.Boolean, default=False),
        sa.Column('published_at', sa.DateTime),
        sa.Column('parent_version_id', sa.String(36), sa.ForeignKey('workflow_definitions.id')),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),

        # Metadata
        sa.Column('metadata', JSONB, default='{}'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('updated_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('is_deleted', sa.Boolean, default=False),

        sa.UniqueConstraint('tenant_id', 'name', name='uq_workflow_def_name'),
    )

    op.create_index('idx_workflow_definitions_tenant', 'workflow_definitions', ['tenant_id'],
                    postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_workflow_definitions_entity', 'workflow_definitions', ['entity_id'])

    # Create workflow_states table
    op.create_table(
        'workflow_states',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workflow_id', sa.String(36), sa.ForeignKey('workflow_definitions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),

        # State Type
        sa.Column('state_type', sa.String(50), nullable=False),

        # Display
        sa.Column('color', sa.String(50)),
        sa.Column('icon', sa.String(50)),
        sa.Column('position_x', sa.Integer),
        sa.Column('position_y', sa.Integer),

        # Behavior
        sa.Column('is_final', sa.Boolean, default=False),
        sa.Column('requires_approval', sa.Boolean, default=False),
        sa.Column('approval_config', JSONB),

        # SLA & Escalation
        sa.Column('sla_hours', sa.Integer),
        sa.Column('escalation_rules', JSONB),

        # Actions
        sa.Column('on_entry_actions', JSONB, default='[]'),
        sa.Column('on_exit_actions', JSONB, default='[]'),

        # Field Requirements
        sa.Column('required_fields', JSONB, default='[]'),

        # Metadata
        sa.Column('metadata', JSONB, default='{}'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean, default=False),

        sa.UniqueConstraint('workflow_id', 'name', name='uq_workflow_state_name'),
    )

    op.create_index('idx_workflow_states_workflow', 'workflow_states', ['workflow_id'])

    # Create workflow_transitions table
    op.create_table(
        'workflow_transitions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workflow_id', sa.String(36), sa.ForeignKey('workflow_definitions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),

        # Source & Target
        sa.Column('from_state_id', sa.String(36), sa.ForeignKey('workflow_states.id'), nullable=False, index=True),
        sa.Column('to_state_id', sa.String(36), sa.ForeignKey('workflow_states.id'), nullable=False, index=True),

        # Conditions
        sa.Column('condition_type', sa.String(50), default='always'),
        sa.Column('conditions', JSONB),

        # Permissions
        sa.Column('allowed_roles', JSONB, default='[]'),
        sa.Column('allowed_users', JSONB, default='[]'),

        # Actions
        sa.Column('actions', JSONB, default='[]'),

        # Display
        sa.Column('button_label', sa.String(100)),
        sa.Column('button_style', sa.String(50)),
        sa.Column('icon', sa.String(50)),
        sa.Column('display_order', sa.Integer, default=0),

        # Validation
        sa.Column('validation_rules', JSONB, default='[]'),

        # Metadata
        sa.Column('metadata', JSONB, default='{}'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean, default=False),
    )

    op.create_index('idx_workflow_transitions_workflow', 'workflow_transitions', ['workflow_id'])
    op.create_index('idx_workflow_transitions_from_state', 'workflow_transitions', ['from_state_id'])
    op.create_index('idx_workflow_transitions_to_state', 'workflow_transitions', ['to_state_id'])

    # Create workflow_instances table
    op.create_table(
        'workflow_instances',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workflow_id', sa.String(36), sa.ForeignKey('workflow_definitions.id'), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Associated Record
        sa.Column('entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id'), nullable=False),
        sa.Column('record_id', sa.String(36), nullable=False),

        # Current State
        sa.Column('current_state_id', sa.String(36), sa.ForeignKey('workflow_states.id')),
        sa.Column('current_state_entered_at', sa.DateTime),

        # Status
        sa.Column('status', sa.String(50), default='active'),

        # SLA Tracking
        sa.Column('sla_deadline', sa.DateTime),
        sa.Column('is_sla_breached', sa.Boolean, default=False),

        # Context Data
        sa.Column('context_data', JSONB, default='{}'),

        # Audit
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('started_by', sa.String(36), sa.ForeignKey('users.id')),

        # Error Handling
        sa.Column('error_message', sa.Text),
        sa.Column('error_details', JSONB),
    )

    op.create_index('idx_workflow_instances_workflow', 'workflow_instances', ['workflow_id'])
    op.create_index('idx_workflow_instances_record', 'workflow_instances', ['entity_id', 'record_id'])
    op.create_index('idx_workflow_instances_status', 'workflow_instances', ['status'])
    op.create_index('idx_workflow_instances_sla', 'workflow_instances', ['sla_deadline'],
                    postgresql_where=sa.text('is_sla_breached = false'))

    # Create workflow_history table
    op.create_table(
        'workflow_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('instance_id', sa.String(36), sa.ForeignKey('workflow_instances.id'), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Transition Info
        sa.Column('from_state_id', sa.String(36), sa.ForeignKey('workflow_states.id')),
        sa.Column('to_state_id', sa.String(36), sa.ForeignKey('workflow_states.id')),
        sa.Column('transition_id', sa.String(36), sa.ForeignKey('workflow_transitions.id')),

        # Actor
        sa.Column('performed_by', sa.String(36), sa.ForeignKey('users.id'), index=True),
        sa.Column('performed_at', sa.DateTime, server_default=sa.func.now()),

        # Action Details
        sa.Column('action_type', sa.String(50)),
        sa.Column('action_data', JSONB),

        # Comments
        sa.Column('comment', sa.Text),

        # Duration
        sa.Column('duration_minutes', sa.Integer),

        # Metadata
        sa.Column('metadata', JSONB, default='{}'),
    )

    op.create_index('idx_workflow_history_instance', 'workflow_history', ['instance_id'])
    op.create_index('idx_workflow_history_performed_by', 'workflow_history', ['performed_by'])

    # ==================== Priority 3: Automation System ====================

    # Create automation_rules table
    op.create_table(
        'automation_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False, index=True),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(100)),

        # Trigger Configuration
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('trigger_config', JSONB, nullable=False),

        # Entity Association
        sa.Column('entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id')),

        # Database Event Triggers
        sa.Column('event_type', sa.String(50)),
        sa.Column('trigger_timing', sa.String(20)),

        # Schedule Configuration
        sa.Column('schedule_type', sa.String(50)),
        sa.Column('cron_expression', sa.String(100)),
        sa.Column('schedule_interval', sa.Integer),
        sa.Column('schedule_timezone', sa.String(50), default='UTC'),
        sa.Column('next_run_at', sa.DateTime),
        sa.Column('last_run_at', sa.DateTime),

        # Conditions
        sa.Column('has_conditions', sa.Boolean, default=False),
        sa.Column('conditions', JSONB, default='{}'),

        # Actions
        sa.Column('actions', JSONB, nullable=False, default='[]'),

        # Execution Settings
        sa.Column('execution_order', sa.Integer, default=0),
        sa.Column('max_retries', sa.Integer, default=3),
        sa.Column('retry_delay_seconds', sa.Integer, default=60),
        sa.Column('timeout_seconds', sa.Integer, default=300),

        # Concurrency Control
        sa.Column('allow_concurrent', sa.Boolean, default=True),
        sa.Column('max_concurrent_instances', sa.Integer),

        # Error Handling
        sa.Column('on_error_action', sa.String(50), default='stop'),
        sa.Column('error_notification_emails', JSONB, default='[]'),

        # Status & Control
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_async', sa.Boolean, default=True),

        # Testing
        sa.Column('is_test_mode', sa.Boolean, default=False),

        # Statistics
        sa.Column('total_executions', sa.Integer, default=0),
        sa.Column('successful_executions', sa.Integer, default=0),
        sa.Column('failed_executions', sa.Integer, default=0),
        sa.Column('average_execution_time_ms', sa.Integer),

        # Metadata
        sa.Column('metadata', JSONB, default='{}'),

        # Version Control
        sa.Column('version', sa.Integer, default=1),
        sa.Column('is_published', sa.Boolean, default=False),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('updated_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('deleted_at', sa.DateTime),
        sa.Column('is_deleted', sa.Boolean, default=False),

        sa.UniqueConstraint('tenant_id', 'name', name='uq_automation_rule_name'),
    )

    op.create_index('idx_automation_rules_tenant', 'automation_rules', ['tenant_id'],
                    postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_automation_rules_entity', 'automation_rules', ['entity_id'],
                    postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_automation_rules_trigger_type', 'automation_rules', ['trigger_type'],
                    postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_automation_rules_next_run', 'automation_rules', ['next_run_at'],
                    postgresql_where=sa.text('is_active = true AND schedule_type IS NOT NULL'))
    op.create_index('idx_automation_rules_event', 'automation_rules', ['entity_id', 'event_type'],
                    postgresql_where=sa.text('is_active = true'))

    # Create automation_executions table
    op.create_table(
        'automation_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('rule_id', sa.String(36), sa.ForeignKey('automation_rules.id'), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Trigger Context
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('triggered_by_user_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('triggered_at', sa.DateTime, server_default=sa.func.now()),

        # Entity Context
        sa.Column('entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id')),
        sa.Column('record_id', sa.String(36)),
        sa.Column('record_data_before', JSONB),
        sa.Column('record_data_after', JSONB),

        # Execution Status
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('execution_time_ms', sa.Integer),

        # Condition Evaluation
        sa.Column('conditions_met', sa.Boolean),
        sa.Column('condition_evaluation_result', JSONB),

        # Actions Execution
        sa.Column('total_actions', sa.Integer, default=0),
        sa.Column('completed_actions', sa.Integer, default=0),
        sa.Column('failed_actions', sa.Integer, default=0),
        sa.Column('action_results', JSONB, default='[]'),

        # Error Handling
        sa.Column('error_message', sa.Text),
        sa.Column('error_stack_trace', sa.Text),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('next_retry_at', sa.DateTime),

        # Context Data
        sa.Column('context_data', JSONB, default='{}'),

        # Metadata
        sa.Column('metadata', JSONB, default='{}'),
    )

    op.create_index('idx_automation_executions_rule', 'automation_executions', ['rule_id'])
    op.create_index('idx_automation_executions_status', 'automation_executions', ['status'])
    op.create_index('idx_automation_executions_record', 'automation_executions', ['entity_id', 'record_id'])
    op.create_index('idx_automation_executions_triggered_at', 'automation_executions', ['triggered_at'])
    op.create_index('idx_automation_executions_retry', 'automation_executions', ['next_retry_at'],
                    postgresql_where=sa.text("status = 'failed'"))

    # Create action_templates table
    op.create_table(
        'action_templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id')),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(100)),

        # Action Type
        sa.Column('action_type', sa.String(50), nullable=False),

        # Template Configuration
        sa.Column('config_schema', JSONB, nullable=False),
        sa.Column('default_config', JSONB, default='{}'),

        # Display
        sa.Column('icon', sa.String(50)),
        sa.Column('color', sa.String(50)),

        # System vs Custom
        sa.Column('is_system', sa.Boolean, default=False),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('is_deleted', sa.Boolean, default=False),

        sa.UniqueConstraint('tenant_id', 'name', name='uq_action_template_name'),
    )

    op.create_index('idx_action_templates_tenant', 'action_templates', ['tenant_id'])
    op.create_index('idx_action_templates_type', 'action_templates', ['action_type'],
                    postgresql_where=sa.text('is_active = true'))

    # Create webhook_configs table
    op.create_table(
        'webhook_configs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),

        # Webhook Type
        sa.Column('webhook_type', sa.String(50), nullable=False),

        # Inbound Webhook Config
        sa.Column('endpoint_path', sa.String(200)),
        sa.Column('secret_token', sa.String(255)),
        sa.Column('allowed_ips', JSONB, default='[]'),

        # Outbound Webhook Config
        sa.Column('target_url', sa.String(500)),
        sa.Column('http_method', sa.String(10), default='POST'),
        sa.Column('headers', JSONB, default='{}'),
        sa.Column('authentication_type', sa.String(50)),
        sa.Column('authentication_config', JSONB, default='{}'),

        # Payload Configuration
        sa.Column('payload_template', sa.Text),
        sa.Column('payload_mapping', JSONB, default='{}'),

        # Retry Configuration
        sa.Column('max_retries', sa.Integer, default=3),
        sa.Column('retry_delay_seconds', sa.Integer, default=60),
        sa.Column('timeout_seconds', sa.Integer, default=30),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),

        # Statistics
        sa.Column('total_calls', sa.Integer, default=0),
        sa.Column('successful_calls', sa.Integer, default=0),
        sa.Column('failed_calls', sa.Integer, default=0),
        sa.Column('last_called_at', sa.DateTime),

        # Metadata
        sa.Column('metadata', JSONB, default='{}'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('updated_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('is_deleted', sa.Boolean, default=False),

        sa.UniqueConstraint('tenant_id', 'name', name='uq_webhook_config_name'),
    )

    op.create_index('idx_webhook_configs_tenant', 'webhook_configs', ['tenant_id'],
                    postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_webhook_configs_endpoint', 'webhook_configs', ['endpoint_path'],
                    postgresql_where=sa.text("webhook_type = 'inbound'"))

    # ==================== Priority 4: Lookup Configuration ====================

    # Create lookup_configurations table
    op.create_table(
        'lookup_configurations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),

        # Source Configuration
        sa.Column('source_type', sa.String(50), nullable=False),

        # Entity Source
        sa.Column('source_entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id')),
        sa.Column('display_field', sa.String(100)),
        sa.Column('value_field', sa.String(100), default='id'),
        sa.Column('additional_display_fields', JSONB, default='[]'),

        # Query Configuration
        sa.Column('custom_query', sa.Text),
        sa.Column('query_parameters', JSONB, default='{}'),

        # Static List Source
        sa.Column('static_options', JSONB, default='[]'),

        # API Source
        sa.Column('api_endpoint', sa.String(500)),
        sa.Column('api_method', sa.String(10), default='GET'),
        sa.Column('api_headers', JSONB, default='{}'),
        sa.Column('api_response_mapping', JSONB, default='{}'),

        # Filtering
        sa.Column('default_filter', JSONB, default='{}'),
        sa.Column('allow_user_filter', sa.Boolean, default=True),
        sa.Column('filter_fields', JSONB, default='[]'),

        # Sorting
        sa.Column('default_sort_field', sa.String(100)),
        sa.Column('default_sort_order', sa.String(10), default='ASC'),
        sa.Column('allow_user_sort', sa.Boolean, default=True),

        # Display Configuration
        sa.Column('display_template', sa.String(500)),
        sa.Column('placeholder_text', sa.String(200)),
        sa.Column('empty_message', sa.String(200), default='No options available'),

        # Search Configuration
        sa.Column('enable_search', sa.Boolean, default=True),
        sa.Column('search_fields', JSONB, default='[]'),
        sa.Column('min_search_length', sa.Integer, default=3),
        sa.Column('search_debounce_ms', sa.Integer, default=300),

        # Autocomplete Configuration
        sa.Column('enable_autocomplete', sa.Boolean, default=False),
        sa.Column('autocomplete_min_chars', sa.Integer, default=2),
        sa.Column('autocomplete_max_results', sa.Integer, default=10),

        # Performance
        sa.Column('enable_caching', sa.Boolean, default=True),
        sa.Column('cache_ttl_seconds', sa.Integer, default=3600),
        sa.Column('lazy_load', sa.Boolean, default=False),
        sa.Column('page_size', sa.Integer, default=50),

        # Dependency Configuration
        sa.Column('is_dependent', sa.Boolean, default=False),
        sa.Column('parent_lookup_id', sa.String(36), sa.ForeignKey('lookup_configurations.id')),
        sa.Column('dependency_mapping', JSONB, default='{}'),

        # Advanced Features
        sa.Column('allow_create_new', sa.Boolean, default=False),
        sa.Column('create_entity_id', sa.String(36), sa.ForeignKey('entity_definitions.id')),

        sa.Column('allow_multiple', sa.Boolean, default=False),
        sa.Column('max_selections', sa.Integer),

        # Metadata
        sa.Column('metadata', JSONB, default='{}'),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('updated_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('is_deleted', sa.Boolean, default=False),

        sa.UniqueConstraint('tenant_id', 'name', name='uq_lookup_config_name'),
    )

    op.create_index('idx_lookup_configurations_tenant', 'lookup_configurations', ['tenant_id'],
                    postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_lookup_configurations_source_entity', 'lookup_configurations', ['source_entity_id'])
    op.create_index('idx_lookup_configurations_parent', 'lookup_configurations', ['parent_lookup_id'],
                    postgresql_where=sa.text('is_dependent = true'))

    # Create lookup_cache table
    op.create_table(
        'lookup_cache',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('lookup_id', sa.String(36), sa.ForeignKey('lookup_configurations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Cache Key
        sa.Column('cache_key', sa.String(255), nullable=False),

        # Cached Data
        sa.Column('cached_data', JSONB, nullable=False),
        sa.Column('record_count', sa.Integer),

        # Cache Metadata
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('hit_count', sa.Integer, default=0),
        sa.Column('last_accessed_at', sa.DateTime, server_default=sa.func.now()),

        sa.UniqueConstraint('lookup_id', 'cache_key', name='uq_lookup_cache_key'),
    )

    op.create_index('idx_lookup_cache_lookup', 'lookup_cache', ['lookup_id'])
    op.create_index('idx_lookup_cache_expires', 'lookup_cache', ['expires_at'])
    op.create_index('idx_lookup_cache_key', 'lookup_cache', ['cache_key'])

    # Create cascading_lookup_rules table
    op.create_table(
        'cascading_lookup_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),

        # Basic Info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),

        # Parent-Child Relationship
        sa.Column('parent_lookup_id', sa.String(36), sa.ForeignKey('lookup_configurations.id'), nullable=False, index=True),
        sa.Column('child_lookup_id', sa.String(36), sa.ForeignKey('lookup_configurations.id'), nullable=False, index=True),

        # Filtering Rule
        sa.Column('filter_type', sa.String(50), default='field_match'),
        sa.Column('parent_field', sa.String(100)),
        sa.Column('child_filter_field', sa.String(100)),

        # Custom Filter
        sa.Column('custom_filter_expression', sa.Text),

        # Behavior
        sa.Column('clear_on_parent_change', sa.Boolean, default=True),
        sa.Column('auto_select_if_single', sa.Boolean, default=False),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),

        sa.UniqueConstraint('parent_lookup_id', 'child_lookup_id', name='uq_cascading_lookup'),
    )

    op.create_index('idx_cascading_lookup_rules_parent', 'cascading_lookup_rules', ['parent_lookup_id'])
    op.create_index('idx_cascading_lookup_rules_child', 'cascading_lookup_rules', ['child_lookup_id'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key dependencies)

    # Priority 4: Lookup Configuration
    op.drop_table('cascading_lookup_rules')
    op.drop_table('lookup_cache')
    op.drop_table('lookup_configurations')

    # Priority 3: Automation System
    op.drop_table('webhook_configs')
    op.drop_table('action_templates')
    op.drop_table('automation_executions')
    op.drop_table('automation_rules')

    # Priority 2: Workflow Designer
    op.drop_table('workflow_history')
    op.drop_table('workflow_instances')
    op.drop_table('workflow_transitions')
    op.drop_table('workflow_states')
    op.drop_table('workflow_definitions')

    # Priority 1: Data Model Designer
    op.drop_table('entity_migrations')
    op.drop_table('index_definitions')
    op.drop_table('relationship_definitions')
    op.drop_table('field_definitions')
    op.drop_table('entity_definitions')
