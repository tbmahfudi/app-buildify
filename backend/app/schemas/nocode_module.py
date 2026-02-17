"""
No-Code Module Schemas

Pydantic schemas for Module System Foundation (Phase 4 Priority 1).
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from app.schemas.base import UUIDMixin


# ==================== Module Schemas ====================

class NocodeModuleCreate(BaseModel):
    """Schema for creating a new module"""
    name: str = Field(..., min_length=1, max_length=100, description="Module internal name")
    display_name: str = Field(..., min_length=1, max_length=200, description="User-facing display name")
    description: Optional[str] = Field(None, description="Module description")
    table_prefix: str = Field(..., min_length=1, max_length=10, description="Database table prefix (lowercase alphanumeric, no underscore)")
    category: Optional[str] = Field(None, max_length=50, description="Module category (hr, finance, sales, etc.)")
    icon: Optional[str] = Field('cube', max_length=50, description="Phosphor icon name")
    color: Optional[str] = Field('#3b82f6', max_length=7, description="Hex color code")
    is_platform_level: bool = Field(False, description="Create as platform-level template (superuser only)")

    @field_validator('table_prefix')
    @classmethod
    def validate_table_prefix(cls, v):
        import re
        if not re.match(r'^[a-z0-9]{1,10}$', v):
            raise ValueError('Table prefix must be 1-10 lowercase alphanumeric characters (no underscore)')
        return v

    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        if v and not v.startswith('#'):
            raise ValueError('Color must be a hex code starting with #')
        return v


class NocodeModuleUpdate(BaseModel):
    """Schema for updating a module"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=7)
    config: Optional[Dict] = None


class NocodeModuleResponse(UUIDMixin, BaseModel):
    """Schema for module response"""
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    table_prefix: Optional[str] = None
    category: Optional[str] = None
    tags: List = Field(default_factory=list)
    icon: Optional[str] = None
    color: Optional[str] = None
    status: str = "draft"
    is_core: bool = False
    is_template: bool = False
    tenant_id: Optional[str] = None
    permissions: List = Field(default_factory=list)
    config: Dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    @field_validator('tags', 'permissions', mode='before')
    @classmethod
    def coerce_none_to_list(cls, v):
        return v if v is not None else []

    @field_validator('config', mode='before')
    @classmethod
    def coerce_none_to_dict(cls, v):
        return v if v is not None else {}

    @field_validator('is_core', 'is_template', mode='before')
    @classmethod
    def coerce_none_to_false(cls, v):
        return v if v is not None else False

    @field_validator('version', mode='before')
    @classmethod
    def coerce_none_version(cls, v):
        return v if v is not None else "1.0.0"

    @field_validator('status', mode='before')
    @classmethod
    def coerce_none_status(cls, v):
        return v if v is not None else "draft"

    class Config:
        from_attributes = True


class NocodeModuleListResponse(BaseModel):
    """Schema for list of modules"""
    modules: List[NocodeModuleResponse]
    total: int


# ==================== Dependency Schemas ====================

class ModuleDependencyCreate(BaseModel):
    """Schema for creating a module dependency"""
    depends_on_module_id: str = Field(..., description="ID of the module to depend on")
    dependency_type: str = Field('required', description="Type: required, optional, conflicts")
    min_version: Optional[str] = Field(None, description="Minimum version (inclusive)")
    max_version: Optional[str] = Field(None, description="Maximum version (exclusive)")
    reason: Optional[str] = Field(None, description="Why this dependency exists")

    @field_validator('dependency_type')
    @classmethod
    def validate_dependency_type(cls, v):
        if v not in ['required', 'optional', 'conflicts']:
            raise ValueError("dependency_type must be 'required', 'optional', or 'conflicts'")
        return v

    @field_validator('min_version', 'max_version')
    @classmethod
    def validate_version_format(cls, v):
        if v:
            import re
            if not re.match(r'^\d+\.\d+\.\d+$', v):
                raise ValueError('Version must be in format MAJOR.MINOR.PATCH (e.g., 1.0.0)')
        return v


class ModuleDependencyResponse(UUIDMixin, BaseModel):
    """Schema for dependency response"""
    id: str
    depends_on_module: Dict  # {id, name, display_name, version}
    dependency_type: str
    min_version: Optional[str]
    max_version: Optional[str]
    version_constraint: Optional[str]
    reason: Optional[str]


class ModuleDependentResponse(UUIDMixin, BaseModel):
    """Schema for dependent module response (who depends on this module)"""
    id: str
    module: Dict  # {id, name, display_name, version}
    dependency_type: str
    version_constraint: Optional[str]


class DependencyCompatibilityCheck(BaseModel):
    """Schema for dependency compatibility check result"""
    is_compatible: bool
    issues: List[str] = Field(default_factory=list)


# ==================== Version Schemas ====================

class ModuleVersionCreate(BaseModel):
    """Schema for creating a new version"""
    change_type: str = Field(..., description="Type: major, minor, patch, hotfix")
    change_summary: str = Field(..., min_length=1, description="Summary of changes")
    changelog: Optional[str] = Field(None, description="Detailed changelog")
    breaking_changes: Optional[str] = Field(None, description="Breaking changes description")

    @field_validator('change_type')
    @classmethod
    def validate_change_type(cls, v):
        if v not in ['major', 'minor', 'patch', 'hotfix']:
            raise ValueError("change_type must be 'major', 'minor', 'patch', or 'hotfix'")
        return v


class ModuleVersionResponse(UUIDMixin, BaseModel):
    """Schema for version response"""
    id: str
    version: str
    version_number: int
    change_type: str
    change_summary: str
    changelog: Optional[str]
    breaking_changes: Optional[str]
    is_current: bool
    created_at: Optional[datetime]
    created_by: Optional[str]


class ModuleVersionListResponse(BaseModel):
    """Schema for list of versions"""
    versions: List[ModuleVersionResponse]
    total: int


# ==================== Operation Response Schemas ====================

class ModuleOperationResponse(BaseModel):
    """Generic operation response"""
    success: bool
    message: str
    data: Optional[Dict] = None


class ValidationResponse(BaseModel):
    """Schema for validation responses"""
    is_valid: bool
    message: str


# ==================== Component Association Schemas ====================

class ModuleComponentsResponse(BaseModel):
    """Schema for listing all components in a module"""
    module_id: str
    module_name: str
    components: Dict = Field(default_factory=dict)  # {entities: [], workflows: [], etc.}
    component_counts: Dict = Field(default_factory=dict)  # {entities: 5, workflows: 2, etc.}


# ==================== Query Schemas ====================

class ModuleListQuery(BaseModel):
    """Query parameters for listing modules"""
    status: Optional[str] = Field(None, description="Filter by status")
    category: Optional[str] = Field(None, description="Filter by category")
    include_platform: bool = Field(True, description="Include platform-level templates")


class ModulePublishRequest(BaseModel):
    """Request to publish a module"""
    pass  # No additional fields needed


class ModuleDeleteRequest(BaseModel):
    """Request to delete a module"""
    confirm: bool = Field(..., description="Must be true to confirm deletion")

    @field_validator('confirm')
    @classmethod
    def validate_confirm(cls, v):
        if not v:
            raise ValueError("Must confirm deletion")
        return v
