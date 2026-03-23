# No-Code Platform - Phase 4: Module System Foundation

**Date:** 2026-01-19
**Status:** In Progress
**Phase:** 4 of 7
**Duration:** 3-4 weeks
**Purpose:** Build infrastructure for modular no-code development with cross-module capabilities

---

## Executive Summary

Phase 4 establishes the foundation for a modular no-code platform where business domains are organized into self-contained modules with semantic versioning, cross-module dependencies, and extension capabilities. This enables developers to build complex applications by composing reusable modules while maintaining clear boundaries and versioned contracts.

**Key Achievements:**
- Module registry with semantic versioning
- Cross-module service layer for safe data access
- Extension framework (entity, screen, menu extensions)
- Dependency resolution system

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Priority 1: Module Definition & Registry](#priority-1-module-definition--registry)
3. [Priority 2: Cross-Module Access](#priority-2-cross-module-access)
4. [Priority 3: Extension Framework](#priority-3-extension-framework)
5. [Implementation Plan](#implementation-plan)
6. [Testing Strategy](#testing-strategy)
7. [Migration Guide](#migration-guide)

---

## Architecture Overview

### Module System Layers

```
┌─────────────────────────────────────────────────────────┐
│  MODULE DEFINITION LAYER                                │
│  - Module metadata (name, version, description)        │
│  - Dependency declarations (required, optional)        │
│  - Component grouping (entities, workflows, etc.)      │
│  - Table naming: {prefix}_{entity} (max 10 char)       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  SERVICE LAYER                                          │
│  - Service registration & discovery                    │
│  - Cross-module API contracts                          │
│  - Permission delegation                                │
│  - Version compatibility checking                       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  EXTENSION LAYER                                        │
│  - Entity extensions (add fields)                       │
│  - Screen extensions (add tabs/sections)                │
│  - Menu extensions (add items)                          │
│  - Dynamic composition at runtime                       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  DATA LAYER                                             │
│  - Module tables: {prefix}_{entity}                     │
│  - Extension tables: {prefix}_{targetprefix}_{entity}_ext │
│  - Organization hierarchy (tenant → company → branch)   │
└─────────────────────────────────────────────────────────┘
```

### Module Composition Example

```
Core Platform
  └── Base entities (User, Tenant, Company, Branch)

HR Module (v1.5.0)
  ├── Entities: hr_employees, hr_departments
  ├── Exports: EmployeeService
  └── Dependencies: core >= 1.0.0

Payroll Module (v2.1.0)
  ├── Entities: payroll_payslips, payroll_runs
  ├── Extensions: payroll_hr_employees_ext (adds fields to hr_employees)
  ├── Imports: EmployeeService from HR Module
  └── Dependencies: hr >= 1.5.0, < 2.0.0

Benefits Module (v1.0.0)
  ├── Entities: benefits_plans, benefits_enrollments
  ├── Extensions: benefits_hr_employees_ext (adds fields to hr_employees)
  ├── Imports: EmployeeService from HR Module
  └── Dependencies: hr >= 1.5.0
```

---

## Priority 1: Module Definition & Registry

**Duration:** Week 1-2
**Goal:** Core module infrastructure with semantic versioning and dependency management

### 1.1 Database Schema

#### Table: nocode_modules

```sql
CREATE TABLE nocode_modules (
  -- Identity
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL UNIQUE,
  display_name VARCHAR(200) NOT NULL,
  description TEXT,

  -- Versioning (Semantic Versioning: MAJOR.MINOR.PATCH)
  version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
  major_version INT NOT NULL DEFAULT 1,
  minor_version INT NOT NULL DEFAULT 0,
  patch_version INT NOT NULL DEFAULT 0,

  -- Table naming
  table_prefix VARCHAR(10) NOT NULL UNIQUE,  -- No underscore in prefix, max 10 chars

  -- Metadata
  category VARCHAR(50),  -- hr, finance, sales, crm, etc.
  tags JSONB DEFAULT '[]',
  icon VARCHAR(50),  -- Phosphor icon name
  color VARCHAR(7),  -- Hex color for UI

  -- Status
  status VARCHAR(20) NOT NULL DEFAULT 'draft',  -- draft, active, deprecated, archived
  is_core BOOLEAN DEFAULT FALSE,  -- Core platform module (cannot be deleted)
  is_template BOOLEAN DEFAULT FALSE,  -- Available as template

  -- Organization
  tenant_id UUID REFERENCES tenants(id),  -- NULL = platform-level template

  -- Permissions
  permissions JSONB DEFAULT '[]',  -- Custom permissions this module defines

  -- Configuration
  config JSONB DEFAULT '{}',  -- Module-specific configuration

  -- Audit
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_by UUID REFERENCES users(id),
  updated_at TIMESTAMP DEFAULT NOW(),
  published_at TIMESTAMP,
  published_by UUID REFERENCES users(id),

  -- Constraints
  CONSTRAINT valid_version CHECK (version ~ '^[0-9]+\.[0-9]+\.[0-9]+$'),
  CONSTRAINT valid_prefix CHECK (table_prefix ~ '^[a-z0-9]{1,10}$'),  -- lowercase alphanumeric only
  CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'deprecated', 'archived'))
);

-- Indexes
CREATE INDEX idx_nocode_modules_tenant ON nocode_modules(tenant_id);
CREATE INDEX idx_nocode_modules_status ON nocode_modules(status);
CREATE INDEX idx_nocode_modules_prefix ON nocode_modules(table_prefix);
CREATE INDEX idx_nocode_modules_category ON nocode_modules(category);
```

#### Table: module_dependencies

```sql
CREATE TABLE module_dependencies (
  -- Identity
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Relationship
  module_id UUID NOT NULL REFERENCES nocode_modules(id) ON DELETE CASCADE,
  depends_on_module_id UUID NOT NULL REFERENCES nocode_modules(id) ON DELETE RESTRICT,

  -- Dependency type
  dependency_type VARCHAR(20) NOT NULL DEFAULT 'required',  -- required, optional, conflicts

  -- Version constraints (Semantic Versioning)
  min_version VARCHAR(20),  -- Minimum version (inclusive)
  max_version VARCHAR(20),  -- Maximum version (exclusive)
  version_constraint VARCHAR(100),  -- e.g., ">=1.5.0, <2.0.0"

  -- Metadata
  reason TEXT,  -- Why this dependency exists

  -- Audit
  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID REFERENCES users(id),

  -- Constraints
  CONSTRAINT valid_dependency_type CHECK (dependency_type IN ('required', 'optional', 'conflicts')),
  CONSTRAINT no_self_dependency CHECK (module_id != depends_on_module_id),
  CONSTRAINT unique_module_dependency UNIQUE (module_id, depends_on_module_id)
);

-- Indexes
CREATE INDEX idx_module_dependencies_module ON module_dependencies(module_id);
CREATE INDEX idx_module_dependencies_depends_on ON module_dependencies(depends_on_module_id);
```

#### Table: module_versions

```sql
CREATE TABLE module_versions (
  -- Identity
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Module reference
  module_id UUID NOT NULL REFERENCES nocode_modules(id) ON DELETE CASCADE,

  -- Version info
  version VARCHAR(20) NOT NULL,
  version_number INT NOT NULL,  -- Auto-increment per module
  major_version INT NOT NULL,
  minor_version INT NOT NULL,
  patch_version INT NOT NULL,

  -- Change tracking
  change_type VARCHAR(20) NOT NULL,  -- major, minor, patch, hotfix
  change_summary TEXT NOT NULL,
  changelog TEXT,
  breaking_changes TEXT,

  -- Snapshot (full module state at this version)
  snapshot JSONB NOT NULL,  -- Complete module definition

  -- Status
  is_current BOOLEAN DEFAULT FALSE,

  -- Audit
  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID REFERENCES users(id),

  -- Constraints
  CONSTRAINT valid_change_type CHECK (change_type IN ('major', 'minor', 'patch', 'hotfix')),
  CONSTRAINT unique_module_version UNIQUE (module_id, version)
);

-- Indexes
CREATE INDEX idx_module_versions_module ON module_versions(module_id);
CREATE INDEX idx_module_versions_current ON module_versions(module_id, is_current) WHERE is_current = TRUE;
CREATE INDEX idx_module_versions_number ON module_versions(module_id, version_number);
```

#### Add module_id to existing no-code tables

```sql
-- Add module_id to all no-code component tables
ALTER TABLE entity_definitions ADD COLUMN module_id UUID REFERENCES nocode_modules(id) ON DELETE SET NULL;
ALTER TABLE workflow_definitions ADD COLUMN module_id UUID REFERENCES nocode_modules(id) ON DELETE SET NULL;
ALTER TABLE automation_rules ADD COLUMN module_id UUID REFERENCES nocode_modules(id) ON DELETE SET NULL;
ALTER TABLE lookup_configurations ADD COLUMN module_id UUID REFERENCES nocode_modules(id) ON DELETE SET NULL;
ALTER TABLE report_definitions ADD COLUMN module_id UUID REFERENCES nocode_modules(id) ON DELETE SET NULL;
ALTER TABLE dashboard_definitions ADD COLUMN module_id UUID REFERENCES nocode_modules(id) ON DELETE SET NULL;

-- Add indexes
CREATE INDEX idx_entity_definitions_module ON entity_definitions(module_id);
CREATE INDEX idx_workflow_definitions_module ON workflow_definitions(module_id);
CREATE INDEX idx_automation_rules_module ON automation_rules(module_id);
CREATE INDEX idx_lookup_configurations_module ON lookup_configurations(module_id);
CREATE INDEX idx_report_definitions_module ON report_definitions(module_id);
CREATE INDEX idx_dashboard_definitions_module ON dashboard_definitions(module_id);
```

### 1.2 Semantic Versioning

**Format:** `MAJOR.MINOR.PATCH`

**Rules:**
- **MAJOR**: Incompatible API changes, breaking changes
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, backward-compatible

**Examples:**
```
1.0.0 → 1.0.1  (Patch: bug fix)
1.0.1 → 1.1.0  (Minor: new feature)
1.1.0 → 2.0.0  (Major: breaking change)
```

**Version Constraints:**
```python
# Dependency declarations
"hr_module >= 1.5.0"           # Minimum version
"hr_module >= 1.5.0, < 2.0.0"  # Range (minor versions of 1.x)
"hr_module >= 2.1.0"           # Latest 2.x
```

### 1.3 API Endpoints

```
# Module CRUD
POST   /api/v1/nocode-modules                    # Create module
GET    /api/v1/nocode-modules                    # List modules
GET    /api/v1/nocode-modules/{id}               # Get module
PUT    /api/v1/nocode-modules/{id}               # Update module
DELETE /api/v1/nocode-modules/{id}               # Delete module (only if no dependencies)
POST   /api/v1/nocode-modules/{id}/publish       # Publish module (draft → active)

# Module versions
GET    /api/v1/nocode-modules/{id}/versions      # List versions
POST   /api/v1/nocode-modules/{id}/versions      # Create version snapshot
GET    /api/v1/nocode-modules/{id}/versions/{vid}  # Get specific version
POST   /api/v1/nocode-modules/{id}/rollback      # Rollback to version

# Dependencies
GET    /api/v1/nocode-modules/{id}/dependencies  # List dependencies
POST   /api/v1/nocode-modules/{id}/dependencies  # Add dependency
DELETE /api/v1/nocode-modules/{id}/dependencies/{did}  # Remove dependency
GET    /api/v1/nocode-modules/{id}/dependents    # List modules that depend on this

# Validation
POST   /api/v1/nocode-modules/validate-prefix    # Validate table prefix
POST   /api/v1/nocode-modules/validate-name      # Validate module name
POST   /api/v1/nocode-modules/{id}/validate-dependencies  # Check dependency conflicts

# Components
GET    /api/v1/nocode-modules/{id}/components    # List all components (entities, workflows, etc.)
POST   /api/v1/nocode-modules/{id}/components/{type}  # Add component to module
DELETE /api/v1/nocode-modules/{id}/components/{type}/{cid}  # Remove component
```

### 1.4 Module Registry Service

```python
# File: backend/app/services/nocode_module_service.py

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from packaging import version as pkg_version
import re

class NocodeModuleService:
    """Service for managing no-code modules"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

    def create_module(
        self,
        name: str,
        display_name: str,
        description: str,
        table_prefix: str,
        category: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None
    ) -> Tuple[bool, str, Optional[dict]]:
        """Create a new module"""

        # Validate table prefix (max 10 chars, lowercase alphanumeric, no underscore)
        if not re.match(r'^[a-z0-9]{1,10}$', table_prefix):
            return False, "Table prefix must be 1-10 lowercase alphanumeric characters (no underscore)", None

        # Check if prefix already exists
        existing = self.db.query(NocodeModule).filter(
            NocodeModule.table_prefix == table_prefix
        ).first()
        if existing:
            return False, f"Table prefix '{table_prefix}' already in use by module '{existing.name}'", None

        # Check if name already exists
        existing_name = self.db.query(NocodeModule).filter(
            NocodeModule.name == name
        ).first()
        if existing_name:
            return False, f"Module name '{name}' already exists", None

        # Create module
        module = NocodeModule(
            name=name,
            display_name=display_name,
            description=description,
            table_prefix=table_prefix,
            category=category,
            icon=icon or 'cube',
            color=color or '#3b82f6',
            version='1.0.0',
            major_version=1,
            minor_version=0,
            patch_version=0,
            status='draft',
            tenant_id=self.current_user.tenant_id,
            created_by=self.current_user.id
        )

        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)

        return True, "Module created successfully", {
            "id": str(module.id),
            "name": module.name,
            "version": module.version,
            "table_prefix": module.table_prefix
        }

    def add_dependency(
        self,
        module_id: str,
        depends_on_module_id: str,
        dependency_type: str = 'required',
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Add a dependency between modules"""

        # Get modules
        module = self.db.query(NocodeModule).get(module_id)
        depends_on = self.db.query(NocodeModule).get(depends_on_module_id)

        if not module or not depends_on:
            return False, "Module not found"

        # Check for circular dependencies
        if self._has_circular_dependency(module_id, depends_on_module_id):
            return False, f"Circular dependency detected: {module.name} → {depends_on.name} → {module.name}"

        # Validate version constraints
        if min_version and not self._is_valid_version(min_version):
            return False, f"Invalid min_version: {min_version}"
        if max_version and not self._is_valid_version(max_version):
            return False, f"Invalid max_version: {max_version}"

        # Build version constraint string
        version_constraint = None
        if min_version and max_version:
            version_constraint = f">={min_version}, <{max_version}"
        elif min_version:
            version_constraint = f">={min_version}"
        elif max_version:
            version_constraint = f"<{max_version}"

        # Create dependency
        dependency = ModuleDependency(
            module_id=module_id,
            depends_on_module_id=depends_on_module_id,
            dependency_type=dependency_type,
            min_version=min_version,
            max_version=max_version,
            version_constraint=version_constraint,
            reason=reason,
            created_by=self.current_user.id
        )

        self.db.add(dependency)
        self.db.commit()

        return True, f"Dependency added: {module.name} → {depends_on.name}"

    def check_dependency_compatibility(
        self,
        module_id: str
    ) -> Tuple[bool, List[str]]:
        """Check if all dependencies are satisfied"""

        issues = []

        # Get module and its dependencies
        module = self.db.query(NocodeModule).get(module_id)
        if not module:
            return False, ["Module not found"]

        dependencies = self.db.query(ModuleDependency).filter(
            ModuleDependency.module_id == module_id
        ).all()

        for dep in dependencies:
            depends_on = dep.depends_on_module

            # Check if dependency is active
            if depends_on.status != 'active':
                issues.append(
                    f"Dependency '{depends_on.name}' is not active (status: {depends_on.status})"
                )
                continue

            # Check version compatibility
            if dep.min_version:
                if not self._version_satisfies(depends_on.version, f">={dep.min_version}"):
                    issues.append(
                        f"Dependency '{depends_on.name}' version {depends_on.version} "
                        f"does not satisfy minimum version {dep.min_version}"
                    )

            if dep.max_version:
                if not self._version_satisfies(depends_on.version, f"<{dep.max_version}"):
                    issues.append(
                        f"Dependency '{depends_on.name}' version {depends_on.version} "
                        f"exceeds maximum version {dep.max_version}"
                    )

        return len(issues) == 0, issues

    def increment_version(
        self,
        module_id: str,
        change_type: str,  # major, minor, patch
        change_summary: str,
        changelog: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """Increment module version and create snapshot"""

        module = self.db.query(NocodeModule).get(module_id)
        if not module:
            return False, "Module not found", None

        # Calculate new version
        if change_type == 'major':
            new_major = module.major_version + 1
            new_minor = 0
            new_patch = 0
        elif change_type == 'minor':
            new_major = module.major_version
            new_minor = module.minor_version + 1
            new_patch = 0
        else:  # patch
            new_major = module.major_version
            new_minor = module.minor_version
            new_patch = module.patch_version + 1

        new_version = f"{new_major}.{new_minor}.{new_patch}"

        # Create version snapshot
        snapshot = self._create_module_snapshot(module)

        # Get next version number
        max_version_num = self.db.query(func.max(ModuleVersion.version_number)).filter(
            ModuleVersion.module_id == module_id
        ).scalar() or 0

        version_record = ModuleVersion(
            module_id=module_id,
            version=new_version,
            version_number=max_version_num + 1,
            major_version=new_major,
            minor_version=new_minor,
            patch_version=new_patch,
            change_type=change_type,
            change_summary=change_summary,
            changelog=changelog,
            snapshot=snapshot,
            is_current=True,
            created_by=self.current_user.id
        )

        # Mark previous versions as not current
        self.db.query(ModuleVersion).filter(
            ModuleVersion.module_id == module_id,
            ModuleVersion.is_current == True
        ).update({"is_current": False})

        # Update module version
        module.version = new_version
        module.major_version = new_major
        module.minor_version = new_minor
        module.patch_version = new_patch
        module.updated_by = self.current_user.id
        module.updated_at = datetime.utcnow()

        self.db.add(version_record)
        self.db.commit()

        return True, f"Version updated to {new_version}", new_version

    # Helper methods

    def _is_valid_version(self, version_str: str) -> bool:
        """Validate semantic version format"""
        return bool(re.match(r'^\d+\.\d+\.\d+$', version_str))

    def _version_satisfies(self, version_str: str, constraint: str) -> bool:
        """Check if version satisfies constraint"""
        try:
            v = pkg_version.parse(version_str)

            if constraint.startswith('>='):
                min_v = pkg_version.parse(constraint[2:])
                return v >= min_v
            elif constraint.startswith('<'):
                max_v = pkg_version.parse(constraint[1:])
                return v < max_v
            elif constraint.startswith('=='):
                exact_v = pkg_version.parse(constraint[2:])
                return v == exact_v

            return False
        except:
            return False

    def _has_circular_dependency(self, module_id: str, depends_on_id: str) -> bool:
        """Check for circular dependencies using DFS"""
        visited = set()

        def dfs(current_id: str) -> bool:
            if current_id == module_id:
                return True
            if current_id in visited:
                return False

            visited.add(current_id)

            # Get dependencies of current module
            deps = self.db.query(ModuleDependency).filter(
                ModuleDependency.module_id == current_id
            ).all()

            for dep in deps:
                if dfs(str(dep.depends_on_module_id)):
                    return True

            return False

        return dfs(depends_on_id)

    def _create_module_snapshot(self, module: NocodeModule) -> dict:
        """Create complete snapshot of module state"""
        # This will be implemented to capture all module components
        # For now, return basic module data
        return {
            "module": {
                "name": module.name,
                "version": module.version,
                "table_prefix": module.table_prefix,
                # ... other fields
            },
            "entities": [],  # Will fetch from entity_definitions
            "workflows": [],  # Will fetch from workflow_definitions
            "automations": [],  # Will fetch from automation_rules
            # ... other components
        }
```

### 1.5 Module Creation Wizard UI

**Navigation:** No-Code Platform > Platform Configuration > Module Management > Create Module

**Step 1: Basic Information**
```
Module Name: [text input]
  - Example: "Human Resources Management"
  - Auto-suggest table prefix

Display Name: [text input]
  - Example: "HR Management"

Description: [textarea]
  - What this module does

Category: [dropdown]
  - HR, Finance, Sales, CRM, Operations, etc.

Icon: [icon picker]
  - Phosphor icons

Color: [color picker]
  - Module theme color
```

**Step 2: Table Naming**
```
Table Prefix: [text input] (max 10 chars, lowercase alphanumeric)
  - Example: "hr" or "hrm" or "humanres"
  - Validation: Real-time check for uniqueness
  - Preview: Shows example table names
    ✓ hr_employees
    ✓ hr_departments
    ✓ hr_leave_requests

Rules:
  ✓ Must be 1-10 characters
  ✓ Lowercase alphanumeric only (a-z, 0-9)
  ✓ No underscores within prefix
  ✓ Must be unique across all modules
```

**Step 3: Dependencies (Optional)**
```
Add Dependencies:
  [+ Add Dependency Button]

Dependency List:
  ┌─────────────────────────────────────┐
  │ Module: hr_management               │
  │ Type: Required                      │
  │ Version: >= 1.5.0, < 2.0.0          │
  │ Reason: Access employee data        │
  │ [Edit] [Remove]                     │
  └─────────────────────────────────────┘
```

**Step 4: Review & Create**
```
Summary:
  Name: hr_management
  Version: 1.0.0
  Prefix: hr
  Status: Draft

  Dependencies:
    - core_platform >= 1.0.0 (required)

[Create Module] [Cancel]
```

---

## Priority 2: Cross-Module Access

**Duration:** Week 2-3
**Goal:** Enable modules to safely access data and services from other modules

### 2.1 Service Layer Architecture

#### Service Registry Table

```sql
CREATE TABLE module_services (
  -- Identity
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Module reference
  module_id UUID NOT NULL REFERENCES nocode_modules(id) ON DELETE CASCADE,

  -- Service definition
  service_name VARCHAR(100) NOT NULL,  -- e.g., "EmployeeService"
  service_class VARCHAR(200) NOT NULL,  -- Full Python class path
  service_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',

  -- API contract
  methods JSONB NOT NULL,  -- List of public methods with signatures

  -- Documentation
  description TEXT,

  -- Status
  is_active BOOLEAN DEFAULT TRUE,

  -- Audit
  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID REFERENCES users(id),

  -- Constraints
  CONSTRAINT unique_module_service UNIQUE (module_id, service_name, service_version)
);

CREATE INDEX idx_module_services_module ON module_services(module_id);
CREATE INDEX idx_module_services_name ON module_services(service_name);
```

#### Service Access Log

```sql
CREATE TABLE module_service_access_log (
  -- Identity
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Access details
  calling_module_id UUID REFERENCES nocode_modules(id),
  service_id UUID NOT NULL REFERENCES module_services(id),
  method_name VARCHAR(100) NOT NULL,

  -- Request
  user_id UUID REFERENCES users(id),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  parameters JSONB,

  -- Response
  success BOOLEAN,
  error_message TEXT,
  execution_time_ms INT,

  -- Audit
  accessed_at TIMESTAMP DEFAULT NOW(),

  -- Permissions
  permission_checked VARCHAR(200)
);

CREATE INDEX idx_service_access_calling_module ON module_service_access_log(calling_module_id);
CREATE INDEX idx_service_access_service ON module_service_access_log(service_id);
CREATE INDEX idx_service_access_time ON module_service_access_log(accessed_at);
```

### 2.2 Service Registration

```python
# File: backend/app/services/module_service_registry.py

class ModuleServiceRegistry:
    """Registry for cross-module services"""

    _instance = None
    _services = {}  # Cache: {module_name: {service_name: service_class}}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register_service(
        self,
        module_name: str,
        service_name: str,
        service_class: type,
        methods: List[dict],
        version: str = '1.0.0'
    ):
        """Register a service for cross-module use"""

        if module_name not in self._services:
            self._services[module_name] = {}

        self._services[module_name][service_name] = {
            'class': service_class,
            'methods': methods,
            'version': version
        }

        logger.info(f"Registered service: {module_name}.{service_name} v{version}")

    def get_service(
        self,
        module_name: str,
        service_name: str,
        db: Session,
        current_user
    ) -> Optional[object]:
        """Get service instance with permission checking"""

        if module_name not in self._services:
            raise ServiceNotFoundError(f"Module '{module_name}' not found")

        if service_name not in self._services[module_name]:
            raise ServiceNotFoundError(
                f"Service '{service_name}' not found in module '{module_name}'"
            )

        service_info = self._services[module_name][service_name]
        service_class = service_info['class']

        # Instantiate service with user context
        service_instance = service_class(db, current_user)

        # Wrap service to add permission checking and logging
        wrapped_service = ServiceProxy(
            service_instance,
            module_name,
            service_name,
            current_user
        )

        return wrapped_service

    def list_services(self, module_name: Optional[str] = None) -> dict:
        """List all registered services"""
        if module_name:
            return self._services.get(module_name, {})
        return self._services


class ServiceProxy:
    """Proxy to add permission checking and logging to service calls"""

    def __init__(self, service_instance, module_name, service_name, current_user):
        self._service = service_instance
        self._module_name = module_name
        self._service_name = service_name
        self._user = current_user

    def __getattr__(self, method_name):
        """Intercept method calls"""

        if not hasattr(self._service, method_name):
            raise AttributeError(
                f"Service '{self._service_name}' has no method '{method_name}'"
            )

        original_method = getattr(self._service, method_name)

        def wrapped_method(*args, **kwargs):
            # Log access
            start_time = time.time()

            try:
                # Call original method
                result = original_method(*args, **kwargs)

                # Log success
                execution_time = int((time.time() - start_time) * 1000)
                self._log_access(method_name, True, None, execution_time)

                return result

            except PermissionError as e:
                # Log permission error
                self._log_access(method_name, False, str(e), 0)
                raise

            except Exception as e:
                # Log other errors
                execution_time = int((time.time() - start_time) * 1000)
                self._log_access(method_name, False, str(e), execution_time)
                raise

        return wrapped_method

    def _log_access(self, method_name, success, error_message, execution_time_ms):
        """Log service access to database"""
        # Implementation to log to module_service_access_log table
        pass
```

### 2.3 Example: HR Module Service

```python
# File: modules/hr/services/employee_service.py

from app.services.module_service_registry import ModuleServiceRegistry

class EmployeeService:
    """Service for employee operations - exported for other modules"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

    def get_employee(self, employee_id: str) -> Optional[dict]:
        """Get employee by ID - PUBLIC METHOD"""

        # Check permission
        if not self.current_user.has_permission('hr:employee:read'):
            raise PermissionError("No permission to read employee data")

        # Query with tenant isolation
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.tenant_id == self.current_user.tenant_id
        ).first()

        if not employee:
            return None

        return {
            "id": str(employee.id),
            "name": employee.name,
            "email": employee.email,
            "department_id": str(employee.department_id),
            "hire_date": employee.hire_date.isoformat(),
            "status": employee.status
        }

    def list_employees(
        self,
        department_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """List employees - PUBLIC METHOD"""

        # Check permission
        if not self.current_user.has_permission('hr:employee:read'):
            raise PermissionError("No permission to read employee data")

        # Build query
        query = self.db.query(Employee).filter(
            Employee.tenant_id == self.current_user.tenant_id
        )

        if department_id:
            query = query.filter(Employee.department_id == department_id)
        if status:
            query = query.filter(Employee.status == status)

        employees = query.limit(limit).all()

        return [
            {
                "id": str(e.id),
                "name": e.name,
                "email": e.email,
                "department_id": str(e.department_id),
                "status": e.status
            }
            for e in employees
        ]

# Register service on module initialization
def init_hr_module(db: Session):
    """Called when HR module is loaded"""

    registry = ModuleServiceRegistry()

    registry.register_service(
        module_name='hr',
        service_name='EmployeeService',
        service_class=EmployeeService,
        methods=[
            {
                "name": "get_employee",
                "params": [{"name": "employee_id", "type": "str"}],
                "returns": "dict",
                "description": "Get employee by ID"
            },
            {
                "name": "list_employees",
                "params": [
                    {"name": "department_id", "type": "str", "optional": True},
                    {"name": "status", "type": "str", "optional": True},
                    {"name": "limit", "type": "int", "default": 100}
                ],
                "returns": "List[dict]",
                "description": "List employees with filters"
            }
        ],
        version='1.0.0'
    )
```

### 2.4 Example: Payroll Module Using HR Service

```python
# File: modules/payroll/services/payroll_service.py

from app.services.module_service_registry import ModuleServiceRegistry

class PayrollService:
    """Payroll service - depends on HR module"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

        # Get HR module's EmployeeService
        registry = ModuleServiceRegistry()
        self.employee_service = registry.get_service(
            'hr',
            'EmployeeService',
            db,
            current_user
        )

    def calculate_payroll(self, employee_id: str, month: str) -> dict:
        """Calculate payroll for employee"""

        # Get employee data from HR module (cross-module call)
        employee = self.employee_service.get_employee(employee_id)

        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        # Get payroll profile (from payroll module's own tables)
        profile = self.db.query(PayrollProfile).filter(
            PayrollProfile.employee_id == employee_id,
            PayrollProfile.tenant_id == self.current_user.tenant_id
        ).first()

        if not profile:
            raise ValueError(f"No payroll profile for employee {employee_id}")

        # Calculate payroll
        gross_salary = profile.monthly_salary
        deductions = self._calculate_deductions(gross_salary, profile)
        net_salary = gross_salary - deductions

        return {
            "employee": employee,
            "month": month,
            "gross_salary": gross_salary,
            "deductions": deductions,
            "net_salary": net_salary
        }

    def _calculate_deductions(self, gross, profile):
        # Payroll calculation logic
        tax = gross * 0.20
        insurance = profile.insurance_amount or 0
        return tax + insurance
```

### 2.5 Frontend Cross-Module Access

**Frontend can access other modules' data via API:**

```javascript
// File: frontend/modules/payroll/pages/payroll-calculator-page.js

class PayrollCalculatorPage {
    async calculatePayroll(employeeId, month) {
        // Option 1: Call Payroll module API (which internally calls HR service)
        const payrollData = await apiFetch('/payroll/calculate', {
            method: 'POST',
            body: JSON.stringify({
                employee_id: employeeId,
                month: month
            })
        });

        // Option 2: Call HR module API directly (for simple data display)
        const employee = await apiFetch(`/dynamic-data/Employee/records/${employeeId}`);

        this.displayPayroll(payrollData);
    }

    async loadEmployeeDropdown() {
        // Load employees from HR module for dropdown
        const employees = await apiFetch('/dynamic-data/Employee/records?status=active');

        this.renderDropdown(employees);
    }
}
```

---

## Priority 3: Extension Framework

**Duration:** Week 3-4
**Goal:** Allow modules to extend other modules' entities, screens, and menus

### 3.1 Entity Extensions

#### Extension Registry Table

```sql
CREATE TABLE module_entity_extensions (
  -- Identity
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Extension source
  extending_module_id UUID NOT NULL REFERENCES nocode_modules(id) ON DELETE CASCADE,

  -- Extension target
  target_module_id UUID NOT NULL REFERENCES nocode_modules(id) ON DELETE CASCADE,
  target_entity_id UUID NOT NULL REFERENCES entity_definitions(id) ON DELETE CASCADE,

  -- Extension details
  extension_table VARCHAR(100) NOT NULL,  -- e.g., "payroll_hr_employees_ext"
  extension_fields JSONB NOT NULL,  -- Field definitions

  -- Status
  is_active BOOLEAN DEFAULT TRUE,

  -- Audit
  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID REFERENCES users(id),

  -- Constraints
  CONSTRAINT unique_module_extension UNIQUE (extending_module_id, target_entity_id)
);

CREATE INDEX idx_entity_extensions_extending ON module_entity_extensions(extending_module_id);
CREATE INDEX idx_entity_extensions_target ON module_entity_extensions(target_entity_id);
```

#### Example: Payroll Extends HR Employee

```sql
-- Base entity (HR module)
CREATE TABLE hr_employees (
  id UUID PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100),
  hire_date DATE,

  -- Organization hierarchy (always include)
  tenant_id UUID NOT NULL,
  company_id UUID NOT NULL,
  branch_id UUID NOT NULL,
  department_id UUID,

  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID
);

-- Extension table (Payroll module extends HR employee)
CREATE TABLE payroll_hr_employees_ext (
  employee_id UUID PRIMARY KEY REFERENCES hr_employees(id) ON DELETE CASCADE,

  -- Payroll-specific fields
  bank_account VARCHAR(50),
  tax_id VARCHAR(20),
  payment_method VARCHAR(20),  -- bank_transfer, check, cash
  pay_frequency VARCHAR(20),   -- monthly, biweekly, weekly
  monthly_salary DECIMAL(12,2),

  -- Organization (must match base entity)
  tenant_id UUID NOT NULL,

  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMP DEFAULT NOW(),
  updated_by UUID
);

-- Another extension (Benefits module also extends HR employee)
CREATE TABLE benefits_hr_employees_ext (
  employee_id UUID PRIMARY KEY REFERENCES hr_employees(id) ON DELETE CASCADE,

  -- Benefits-specific fields
  health_insurance_plan VARCHAR(50),
  retirement_contribution_pct DECIMAL(5,2),
  life_insurance_amount DECIMAL(12,2),

  -- Organization
  tenant_id UUID NOT NULL,

  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID
);
```

#### Dynamic Query with Extensions

```python
# File: backend/app/services/dynamic_entity_service_extended.py

class DynamicEntityServiceExtended(DynamicEntityService):
    """Enhanced service that auto-joins entity extensions"""

    def get_record_with_extensions(
        self,
        entity_name: str,
        record_id: str,
        tenant_id: str
    ) -> dict:
        """Get record with all enabled module extensions"""

        # Get base entity data
        base_data = self.get_record(entity_name, record_id)

        # Find all extensions for this entity
        extensions = self._get_entity_extensions(entity_name, tenant_id)

        # Join extension data
        for ext in extensions:
            ext_data = self._get_extension_data(ext, record_id, tenant_id)
            if ext_data:
                base_data[f"{ext.extending_module.table_prefix}_ext"] = ext_data

        return base_data

    def _get_entity_extensions(self, entity_name: str, tenant_id: str) -> List:
        """Get all active extensions for entity"""

        # Find entity
        entity = self.db.query(EntityDefinition).filter(
            EntityDefinition.name == entity_name
        ).first()

        if not entity:
            return []

        # Get extensions from modules enabled for this tenant
        extensions = self.db.query(ModuleEntityExtension).join(
            NocodeModule,
            ModuleEntityExtension.extending_module_id == NocodeModule.id
        ).filter(
            ModuleEntityExtension.target_entity_id == entity.id,
            ModuleEntityExtension.is_active == True,
            NocodeModule.status == 'active'
        ).all()

        return extensions

    def _get_extension_data(self, extension, record_id: str, tenant_id: str) -> Optional[dict]:
        """Get data from extension table"""

        table_name = extension.extension_table

        # Build query
        query = f"""
            SELECT * FROM {table_name}
            WHERE employee_id = :record_id
            AND tenant_id = :tenant_id
        """

        result = self.db.execute(
            text(query),
            {"record_id": record_id, "tenant_id": tenant_id}
        ).first()

        if not result:
            return None

        return dict(result)
```

**Example Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "John Doe",
  "email": "john@company.com",
  "hire_date": "2020-01-15",
  "tenant_id": "...",
  "company_id": "...",
  "branch_id": "...",

  // Payroll extension (if payroll module enabled)
  "payroll_ext": {
    "bank_account": "1234567890",
    "tax_id": "987-65-4321",
    "payment_method": "bank_transfer",
    "monthly_salary": 5000.00
  },

  // Benefits extension (if benefits module enabled)
  "benefits_ext": {
    "health_insurance_plan": "Premium PPO",
    "retirement_contribution_pct": 5.0,
    "life_insurance_amount": 100000.00
  }
}
```

### 3.2 Screen Extensions

#### Screen Extension Registry

```sql
CREATE TABLE module_screen_extensions (
  -- Identity
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Extension source
  extending_module_id UUID NOT NULL REFERENCES nocode_modules(id) ON DELETE CASCADE,

  -- Extension target
  target_module_id UUID NOT NULL REFERENCES nocode_modules(id) ON DELETE CASCADE,
  target_screen VARCHAR(100) NOT NULL,  -- e.g., "employee_detail"

  -- Extension details
  extension_type VARCHAR(50) NOT NULL,  -- tab, section, widget, action
  extension_config JSONB NOT NULL,
  position INT DEFAULT 999,

  -- Status
  is_active BOOLEAN DEFAULT TRUE,

  -- Permissions
  required_permission VARCHAR(200),

  -- Audit
  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_screen_extensions_target ON module_screen_extensions(target_module_id, target_screen);
```

#### Example: Payroll Adds Tab to Employee Screen

```javascript
// Frontend: Platform loads and renders extensions

class EmployeeDetailPage {
    async loadEmployee(employeeId) {
        // Load base employee data
        const employee = await apiFetch(`/dynamic-data/Employee/records/${employeeId}`);

        // Get screen extensions for this entity
        const extensions = await apiFetch(
            `/nocode-modules/screen-extensions?screen=employee_detail`
        );

        // Render base UI
        this.renderEmployeeDetails(employee);

        // Render extension tabs
        extensions.forEach(ext => {
            if (ext.extension_type === 'tab') {
                this.addTab(ext);
            }
        });
    }

    addTab(extension) {
        const tabConfig = extension.extension_config;

        // Add tab to UI
        const tab = {
            id: extension.id,
            label: tabConfig.label,
            icon: tabConfig.icon,
            component: tabConfig.component_path,
            permission: extension.required_permission
        };

        this.tabContainer.addTab(tab);
    }
}

// Payroll module's extension component
// File: frontend/modules/payroll/components/employee-payroll-tab.js

class EmployeePayrollTab {
    async render(employeeId) {
        // Load payroll data for this employee
        const payrollData = await apiFetch(`/payroll/employees/${employeeId}/profile`);

        return `
            <div class="payroll-info">
                <h3>Payroll Information</h3>

                <div class="form-group">
                    <label>Bank Account</label>
                    <input value="${payrollData.bank_account}" />
                </div>

                <div class="form-group">
                    <label>Monthly Salary</label>
                    <input type="number" value="${payrollData.monthly_salary}" />
                </div>

                <div class="form-group">
                    <label>Payment Method</label>
                    <select value="${payrollData.payment_method}">
                        <option value="bank_transfer">Bank Transfer</option>
                        <option value="check">Check</option>
                        <option value="cash">Cash</option>
                    </select>
                </div>
            </div>
        `;
    }
}
```

### 3.3 Menu Extensions

#### Menu Extension Registry

```sql
CREATE TABLE module_menu_extensions (
  -- Identity
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Extension source
  extending_module_id UUID NOT NULL REFERENCES nocode_modules(id) ON DELETE CASCADE,

  -- Extension target
  target_module_id UUID REFERENCES nocode_modules(id) ON DELETE CASCADE,  -- NULL = add to root
  target_menu_item VARCHAR(100),  -- Parent menu item

  -- Menu item details
  menu_config JSONB NOT NULL,
  position INT DEFAULT 999,

  -- Status
  is_active BOOLEAN DEFAULT TRUE,

  -- Permissions
  required_permission VARCHAR(200),

  -- Audit
  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_menu_extensions_target ON module_menu_extensions(target_module_id);
```

#### Example: Payroll Adds Items to HR Menu

```json
{
  "extending_module": "payroll",
  "target_module": "hr",
  "target_menu_item": "hr_management",
  "menu_config": {
    "type": "submenu",
    "label": "Payroll",
    "icon": "money",
    "items": [
      {
        "label": "Payroll Runs",
        "route": "payroll/runs",
        "icon": "calendar",
        "permission": "payroll:runs:read"
      },
      {
        "label": "Payslips",
        "route": "payroll/payslips",
        "icon": "receipt",
        "permission": "payroll:payslips:read"
      },
      {
        "label": "Tax Configuration",
        "route": "payroll/tax-config",
        "icon": "calculator",
        "permission": "payroll:config:manage"
      }
    ]
  },
  "position": 10
}
```

**Resulting Menu Structure:**
```
HR Management
  ├── Employees
  ├── Departments
  ├── Leave Requests
  ├── Payroll (extension from payroll module)
  │   ├── Payroll Runs
  │   ├── Payslips
  │   └── Tax Configuration
  └── Benefits (extension from benefits module)
      ├── Insurance Plans
      └── Enrollments
```

---

## Implementation Plan

### Week 1: Module Definition & Registry Foundation

**Days 1-2: Database Schema**
- [ ] Create migration for nocode_modules table
- [ ] Create migration for module_dependencies table
- [ ] Create migration for module_versions table
- [ ] Add module_id to all no-code component tables
- [ ] Run migrations and verify

**Days 3-4: Backend Services**
- [ ] Implement NocodeModuleService
- [ ] Implement dependency resolver
- [ ] Implement version management
- [ ] Add API endpoints
- [ ] Unit tests

**Day 5: Module Creation Wizard UI**
- [ ] Create module list page
- [ ] Create module creation wizard (4 steps)
- [ ] Add table prefix validation
- [ ] Add dependency management UI
- [ ] Integration tests

### Week 2: Cross-Module Service Layer

**Days 1-2: Service Registry**
- [ ] Create module_services table
- [ ] Create module_service_access_log table
- [ ] Implement ModuleServiceRegistry
- [ ] Implement ServiceProxy for permission checking
- [ ] Unit tests

**Days 3-4: Example Implementations**
- [ ] Create HR EmployeeService example
- [ ] Create Payroll service using HR service
- [ ] Add service documentation generator
- [ ] Add service discovery UI
- [ ] Integration tests

**Day 5: Frontend Integration**
- [ ] Update apiFetch to support cross-module calls
- [ ] Add service call examples in docs
- [ ] Performance testing

### Week 3: Extension Framework - Entity

**Days 1-2: Entity Extensions**
- [ ] Create module_entity_extensions table
- [ ] Update DynamicEntityService to auto-join extensions
- [ ] Add extension creation API
- [ ] Add extension management UI

**Days 3-5: Testing & Examples**
- [ ] Create Payroll → HR employee extension example
- [ ] Create Benefits → HR employee extension example
- [ ] Test multiple extensions on same entity
- [ ] Performance testing with multiple extensions

### Week 4: Extension Framework - Screen & Menu

**Days 1-2: Screen Extensions**
- [ ] Create module_screen_extensions table
- [ ] Implement screen extension loader
- [ ] Add tab extension support
- [ ] Add section extension support
- [ ] Create Payroll tab example

**Days 3-4: Menu Extensions**
- [ ] Create module_menu_extensions table
- [ ] Update menu system to load extensions
- [ ] Add menu extension UI
- [ ] Create Payroll menu extension example

**Day 5: Documentation & Testing**
- [ ] Complete Phase 4 documentation
- [ ] End-to-end testing
- [ ] Performance benchmarks
- [ ] Update NO-CODE-MODULE-CREATION-GUIDE.md

---

## Testing Strategy

### Unit Tests

```python
# Test: Semantic versioning
def test_version_increment():
    assert increment_version("1.0.0", "patch") == "1.0.1"
    assert increment_version("1.0.1", "minor") == "1.1.0"
    assert increment_version("1.1.0", "major") == "2.0.0"

# Test: Version constraints
def test_version_satisfies():
    assert version_satisfies("1.5.2", ">=1.5.0")
    assert version_satisfies("1.9.9", "<2.0.0")
    assert not version_satisfies("2.0.0", "<2.0.0")

# Test: Circular dependency detection
def test_circular_dependency():
    # A depends on B, B depends on C, C depends on A → circular
    assert has_circular_dependency("A", "B") == True
```

### Integration Tests

```python
# Test: Cross-module service call
def test_cross_module_service_call():
    # Payroll calls HR EmployeeService
    payroll_service = PayrollService(db, user)
    result = payroll_service.calculate_payroll(employee_id, "2026-01")

    assert result["employee"]["name"] == "John Doe"
    assert result["gross_salary"] > 0

# Test: Entity extension
def test_entity_extension():
    # Load employee with payroll extension
    employee = entity_service.get_record_with_extensions("Employee", emp_id)

    assert "payroll_ext" in employee
    assert employee["payroll_ext"]["bank_account"] is not None
```

### Performance Tests

```python
# Test: Extension overhead
def test_extension_performance():
    # Measure query time with 0, 1, 3, 5 extensions
    times = []
    for num_extensions in [0, 1, 3, 5]:
        start = time.time()
        employee = load_with_n_extensions(emp_id, num_extensions)
        times.append(time.time() - start)

    # Overhead should be < 50ms per extension
    assert all(t < 0.05 for t in times[1:])
```

---

## Migration Guide

### For Existing No-Code Entities

**Option 1: Leave as Non-Module Entities (Recommended for Now)**
- Existing entities continue without module_id
- No changes required
- Migration tool provided in Phase 6

**Option 2: Assign to Default Module**
```sql
-- Create "Legacy Entities" module
INSERT INTO nocode_modules (name, display_name, table_prefix, status)
VALUES ('legacy', 'Legacy Entities', 'nc', 'active');

-- Assign existing entities to legacy module
UPDATE entity_definitions
SET module_id = (SELECT id FROM nocode_modules WHERE name = 'legacy')
WHERE module_id IS NULL;
```

### For New Entities

**All new entities MUST have module_id:**
- Select module during entity creation
- Table name automatically prefixed: `{module.table_prefix}_{entity.name}`
- Platform enforces module assignment

---

## Success Metrics

**Phase 4 is successful when:**

1. ✅ Modules can be created with semantic versioning
2. ✅ Dependencies are resolved correctly
3. ✅ Services can be registered and discovered
4. ✅ Cross-module service calls work with permission checking
5. ✅ Entity extensions auto-join on queries
6. ✅ Screen extensions render correctly
7. ✅ Menu extensions appear in target module menus
8. ✅ Performance overhead < 10% for extensions
9. ✅ Documentation is complete
10. ✅ All tests passing

---

## Related Documentation

- [NO-CODE-PLATFORM-DESIGN.md](NO-CODE-PLATFORM-DESIGN.md) - Overall platform architecture
- [NO-CODE-PHASE1.md](NO-CODE-PHASE1.md) - Data Model Designer foundation
- [NO-CODE-MODULE-CREATION-GUIDE.md](NO-CODE-MODULE-CREATION-GUIDE.md) - User guide (to be updated after Phase 4)

---

**Document Version:** 1.0
**Last Updated:** 2026-01-19
**Status:** In Progress
**Next Steps:** Begin Week 1 implementation (Module Definition & Registry)
