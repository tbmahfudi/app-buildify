"""
SQLAlchemy Models for Multi-Tenant Architecture

This module exports all database models for the application.
All models use GUID (UUID) for primary keys, with support for:
- PostgreSQL: Native UUID type
- MySQL: String(36)
- SQLite: String(36)
"""

from .base import Base, GUID, generate_uuid

# Core entities
from .tenant import Tenant
from .company import Company
from .branch import Branch
from .department import Department
from .user import User

# Multi-company access
from .user_company_access import UserCompanyAccess

# RBAC entities
from .permission import Permission
from .role import Role
from .group import Group

# RBAC junction tables
from .rbac_junctions import (
    RolePermission,
    UserRole,
    UserGroup,
    GroupRole,
)

# Audit and settings
from .audit import AuditLog
from .settings import UserSettings, TenantSettings
from .metadata import EntityMetadata

# Token revocation
from .token_blacklist import TokenBlacklist

# Module system
from .module_registry import ModuleRegistry, TenantModule

# Report system
from .report import (
    ReportDefinition,
    ReportExecution,
    ReportSchedule,
    ReportTemplate,
    ReportCache
)

# Dashboard system
from .dashboard import (
    Dashboard,
    DashboardPage,
    DashboardWidget,
    DashboardShare,
    DashboardSnapshot,
    WidgetDataCache
)

# Security system
from .password_history import PasswordHistory
from .login_attempt import LoginAttempt
from .account_lockout import AccountLockout
from .user_session import UserSession
from .security_policy import SecurityPolicy
from .notification_queue import NotificationQueue
from .notification_config import NotificationConfig
from .password_reset_token import PasswordResetToken

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
]
