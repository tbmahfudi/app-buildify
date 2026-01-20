"""
SQLAlchemy Models for Multi-Tenant Architecture

This module exports all database models for the application.
All models use GUID (UUID) for primary keys, with support for:
- PostgreSQL: Native UUID type
- MySQL: String(36)
- SQLite: String(36)
"""

from .account_lockout import AccountLockout

# Audit and settings
from .audit import AuditLog
from .base import GUID, Base, generate_uuid
from .branch import Branch
from .company import Company

# Dashboard system
from .dashboard import (
    Dashboard,
    DashboardPage,
    DashboardShare,
    DashboardSnapshot,
    DashboardWidget,
    WidgetDataCache,
)
from .department import Department
from .group import Group
from .login_attempt import LoginAttempt
from .menu_item import MenuItem
from .metadata import EntityMetadata

# Module system
from .module_registry import ModuleRegistry, TenantModule
from .company_module import CompanyModule

# Event bus
from .event_bus import Event, EventSubscription, EventHandler, EventArchive
from .notification_config import NotificationConfig
from .notification_queue import NotificationQueue

# Builder system
from .builder_page import BuilderPage, BuilderPageVersion

# No-Code Platform - Data Model Designer
from .data_model import (
    EntityDefinition,
    FieldDefinition,
    RelationshipDefinition,
    IndexDefinition,
    EntityMigration,
)

# No-Code Platform - Workflow Designer
from .workflow import (
    WorkflowDefinition,
    WorkflowState,
    WorkflowTransition,
    WorkflowInstance,
    WorkflowHistory,
)

# No-Code Platform - Automation System
from .automation import (
    AutomationRule,
    AutomationExecution,
    ActionTemplate,
    WebhookConfig,
)

# No-Code Platform - Lookup Configuration
from .lookup import (
    LookupConfiguration,
    LookupCache,
    CascadingLookupRule,
)

# No-Code Platform - Module System Foundation (Phase 4)
from .nocode_module import (
    NocodeModule,
    ModuleDependency,
    ModuleVersion,
)

# No-Code Platform - Module Service Registry (Phase 4 Priority 2)
from .module_service import (
    ModuleService,
    ModuleServiceAccessLog,
)

# Security system
from .password_history import PasswordHistory
from .password_reset_token import PasswordResetToken

# RBAC entities
from .permission import Permission

# RBAC junction tables
from .rbac_junctions import (
    GroupRole,
    RolePermission,
    UserGroup,
    UserRole,
)

# Report system
from .report import (
    ReportCache,
    ReportDefinition,
    ReportExecution,
    ReportSchedule,
    ReportTemplate,
)
from .role import Role

# Scheduler system
from .scheduler import (
    SchedulerConfig,
    SchedulerJob,
    SchedulerJobExecution,
    SchedulerJobLog,
)
from .security_policy import SecurityPolicy
from .settings import TenantSettings, UserSettings

# Core entities
from .tenant import Tenant

# Token revocation
from .token_blacklist import TokenBlacklist
from .user import User

# Multi-company access
from .user_company_access import UserCompanyAccess
from .user_session import UserSession

# Export all models
__all__ = [
    # Base
    "Base",
    "GUID",
    "generate_uuid",

    # Core entities
    "Tenant",
    "Company",
    "Branch",
    "Department",
    "User",

    # Multi-company access
    "UserCompanyAccess",

    # RBAC
    "Permission",
    "Role",
    "Group",

    # RBAC junctions
    "RolePermission",
    "UserRole",
    "UserGroup",
    "GroupRole",

    # Audit and settings
    "AuditLog",
    "UserSettings",
    "TenantSettings",
    "EntityMetadata",

    # Token revocation
    "TokenBlacklist",

    # Module system
    "ModuleRegistry",
    "TenantModule",
    "CompanyModule",

    # Event bus
    "Event",
    "EventSubscription",
    "EventHandler",
    "EventArchive",

    # Menu system
    "MenuItem",

    # Report system
    "ReportDefinition",
    "ReportExecution",
    "ReportSchedule",
    "ReportTemplate",
    "ReportCache",

    # Dashboard system
    "Dashboard",
    "DashboardPage",
    "DashboardWidget",
    "DashboardShare",
    "DashboardSnapshot",
    "WidgetDataCache",

    # Security system
    "PasswordHistory",
    "LoginAttempt",
    "AccountLockout",
    "UserSession",
    "SecurityPolicy",
    "NotificationQueue",
    "NotificationConfig",
    "PasswordResetToken",

    # Scheduler system
    "SchedulerConfig",
    "SchedulerJob",
    "SchedulerJobExecution",
    "SchedulerJobLog",

    # Builder system
    "BuilderPage",
    "BuilderPageVersion",

    # No-Code Platform - Data Model Designer
    "EntityDefinition",
    "FieldDefinition",
    "RelationshipDefinition",
    "IndexDefinition",
    "EntityMigration",

    # No-Code Platform - Workflow Designer
    "WorkflowDefinition",
    "WorkflowState",
    "WorkflowTransition",
    "WorkflowInstance",
    "WorkflowHistory",

    # No-Code Platform - Automation System
    "AutomationRule",
    "AutomationExecution",
    "ActionTemplate",
    "WebhookConfig",

    # No-Code Platform - Lookup Configuration
    "LookupConfiguration",
    "LookupCache",
    "CascadingLookupRule",

    # No-Code Platform - Module System Foundation (Phase 4)
    "NocodeModule",
    "ModuleDependency",
    "ModuleVersion",

    # No-Code Platform - Module Service Registry (Phase 4 Priority 2)
    "ModuleService",
    "ModuleServiceAccessLog",
]
