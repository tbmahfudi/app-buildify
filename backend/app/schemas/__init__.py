"""
Pydantic schemas for request/response validation

This module exports all Pydantic schemas used throughout the application
for request validation and response serialization.
"""

from .auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserCreate,
    UserUpdate,
    UserResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)

from .org import (
    CompanyBase,
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
    BranchBase,
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    BranchListResponse,
    DepartmentBase,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
)

from .settings import (
    UserSettingsResponse,
    UserSettingsUpdate,
    TenantSettingsResponse,
    TenantSettingsUpdate,
)

from .metadata import (
    FieldMetadata,
    ColumnMetadata,
    TableConfig,
    FormConfig,
    EntityMetadataResponse,
    EntityMetadataCreate,
    EntityMetadataUpdate,
    EntityListResponse,
    EntityMetadataDetailResponse,
)

from .data import (
    FilterCondition,
    DataSearchRequest,
    DataSearchResponse,
    DataCreateRequest,
    DataUpdateRequest,
    DataDeleteRequest,
    DataResponse,
    BulkOperationRequest,
    BulkOperationError,
    BulkOperationResponse,
    DataExportRequest,
    DataImportRequest,
)

from .audit import (
    AuditLogResponse,
    AuditLogCreate,
    AuditLogListRequest,
    AuditLogListResponse,
    AuditLogStatsResponse,
    AuditLogExportRequest,
)

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    # Organization
    "CompanyBase",
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    "CompanyListResponse",
    "BranchBase",
    "BranchCreate",
    "BranchUpdate",
    "BranchResponse",
    "BranchListResponse",
    "DepartmentBase",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "DepartmentListResponse",
    # Settings
    "UserSettingsResponse",
    "UserSettingsUpdate",
    "TenantSettingsResponse",
    "TenantSettingsUpdate",
    # Metadata
    "FieldMetadata",
    "ColumnMetadata",
    "TableConfig",
    "FormConfig",
    "EntityMetadataResponse",
    "EntityMetadataCreate",
    "EntityMetadataUpdate",
    "EntityListResponse",
    "EntityMetadataDetailResponse",
    # Data
    "FilterCondition",
    "DataSearchRequest",
    "DataSearchResponse",
    "DataCreateRequest",
    "DataUpdateRequest",
    "DataDeleteRequest",
    "DataResponse",
    "BulkOperationRequest",
    "BulkOperationError",
    "BulkOperationResponse",
    "DataExportRequest",
    "DataImportRequest",
    # Audit
    "AuditLogResponse",
    "AuditLogCreate",
    "AuditLogListRequest",
    "AuditLogListResponse",
    "AuditLogStatsResponse",
    "AuditLogExportRequest",
]
