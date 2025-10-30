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
]
