# Phase 1 Design: Core Foundation Features

**Date:** 2026-01-02
**Last Updated:** 2026-01-11
**Project:** App-Buildify
**Phase:** 1 - Core Foundation
**Priorities:** 1, 2, 3 & 4
**Status:** ✅ **COMPLETED (95%)** - All Priority Features Implemented

---

## Table of Contents

1. [Implementation Status Summary](#implementation-status-summary)
2. [Overview](#overview)
3. [Priority 1: Data Model Designer](#priority-1-data-model-designer)
4. [Priority 2: Workflow/Business Process Designer](#priority-2-workflowbusiness-process-designer)
5. [Priority 3: Automation & Trigger System](#priority-3-automation--trigger-system)
6. [Priority 4: Lookup/Reference Configuration](#priority-4-lookupreference-configuration)
7. [Integration Points](#integration-points)
8. [Security & RBAC](#security--rbac)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Testing Strategy](#testing-strategy)

---

## Implementation Status Summary

**Last Updated:** 2026-01-11

### 🎉 **PHASE 1 COMPLETE!**

All four priority features have been successfully implemented with full visual designers, monitoring dashboards, and management tools.

### Quick Status Overview

| Priority | Feature | Backend | Frontend | Status |
|----------|---------|---------|----------|--------|
| 1 | Data Model Designer | ✅ Complete | ✅ Complete | ✅ 95% |
| 2 | Workflow Designer | ✅ Complete | ✅ Complete | ✅ 95% |
| 3 | Automation System | ✅ Complete | ✅ Complete | ✅ 95% |
| 4 | Lookup Configuration | ✅ Complete | ✅ Complete | ✅ 95% |

### **Phase 1 Achievement Summary**

✅ **All Critical Features Completed:**
1. Data Model Designer with migration management
2. Visual Workflow Designer with approval routing
3. Automation System with visual condition/action builders
4. Lookup Configuration with cascading support

✅ **All Visual Builders Implemented:**
- SVG-based workflow canvas with drag-and-drop
- Visual condition builder with AND/OR groups
- Visual action builder with sequential steps
- Cron expression builder for scheduling

✅ **All Monitoring Dashboards Implemented:**
- Workflow instance monitoring with real-time stats
- Automation execution monitoring with success rates
- Migration history with rollback capability

✅ **Production-Ready Features:**
- RBAC integration across all features
- Multi-tenant support with platform-level templates
- Comprehensive error handling and validation
- Full CRUD operations for all configurations

### Detailed Implementation Status

#### Priority 1: Data Model Designer
**Backend (✅ Complete)**
- ✅ Database models (EntityDefinition, FieldDefinition, RelationshipDefinition, IndexDefinition, EntityMigration)
- ✅ CRUD APIs for entities (`/api/v1/data-model/entities`)
- ✅ CRUD APIs for fields (`/api/v1/data-model/entities/{id}/fields`)
- ✅ CRUD APIs for relationships (`/api/v1/data-model/relationships`)
- ✅ Data model service with validation
- ✅ RBAC integration
- ✅ Schema introspection service (auto-import from database objects)
- ✅ Migration generator service (SQL generation for CREATE/ALTER/DROP)
- ✅ Migration preview, publish, history, and rollback APIs

**Frontend (✅ Complete - 95%)**
- ✅ Entity list and creation (`/frontend/assets/js/nocode-data-model.js`)
- ✅ Entity editor (edit entity properties)
- ✅ Field manager (CRUD operations for fields)
- ✅ Field type selection with 13+ types
- ✅ Auto-suggest database types
- ✅ Relationship designer (create/delete relationships)
- ✅ Visual indicators for field types and relationships
- ✅ Database import (import from existing tables/views/materialized views)
- ✅ **Migration preview UI** (preview SQL with risk assessment before publishing)
- ✅ **Schema diff viewer** (shows added/removed/modified columns)
- ✅ **Migration history viewer** (complete migration log with status tracking)
- ✅ **Rollback migration UI** (revert completed migrations)
- ✅ **Index management** (indexes auto-created with entities, displayed in preview)
- ⚠️ **Minor: Multi-step wizard for entity creation** (could be added for enhanced UX)

#### Priority 2: Workflow Designer
**Backend (✅ Complete)**
- ✅ Database models (WorkflowDefinition, WorkflowState, WorkflowTransition, WorkflowInstance, WorkflowHistory)
- ✅ CRUD APIs for workflows (`/api/v1/workflows`)
- ✅ CRUD APIs for states (`/api/v1/workflows/{id}/states`)
- ✅ CRUD APIs for transitions (`/api/v1/workflows/{id}/transitions`)
- ✅ Workflow instance management
- ✅ RBAC integration

**Frontend (✅ Complete - 95%)**
- ✅ Workflow list and creation (`/frontend/assets/js/nocode-workflows.js`)
- ✅ Workflow editor (edit workflow properties)
- ✅ State manager (CRUD operations with 5 state types)
- ✅ Transition designer (create/delete transitions)
- ✅ Color-coded state indicators
- ✅ Instance detail viewer
- ✅ SLA configuration support
- ✅ **Visual canvas editor** (SVG-based drag-and-drop workflow designer)
- ✅ **Visual transition arrows/connectors** (automatic arrow drawing between states)
- ✅ **Workflow simulation/testing** (test workflows with sample data before production)
- ✅ **Approval routing UI** (configure approval types, roles, and auto-approval)
- ✅ **Workflow versioning UI** (view version history and track changes)
- ✅ **Instance monitoring dashboard** (real-time monitoring with stats and activity feed)

#### Priority 3: Automation & Trigger System
**Backend (✅ Complete)**
- ✅ Database models (AutomationRule, AutomationExecution, ActionTemplate, WebhookConfig)
- ✅ CRUD APIs for automation rules (`/api/v1/automations/rules`)
- ✅ Webhook configuration APIs
- ✅ Execution history tracking
- ✅ RBAC integration

**Frontend (✅ Complete - 95%)**
- ✅ Automation rule list and creation (`/frontend/assets/js/nocode-automations.js`)
- ✅ Rule editor (edit rule properties)
- ✅ JSON-based condition builder
- ✅ JSON-based action configuration
- ✅ Webhook management (create webhooks)
- ✅ Execution detail viewer with error display
- ✅ Trigger type selection
- ✅ **Visual condition builder** (drag-and-drop if-then-else with AND/OR groups)
- ✅ **Visual action builder** (step-by-step wizard with sequential actions)
- ✅ **Action template library UI** (predefined templates for common patterns)
- ✅ **Automation testing/debugging UI** (integrated with visual builders)
- ✅ **Schedule configuration UI** (cron expression builder with simple/advanced modes)
- ✅ **Execution monitoring dashboard** (stats cards, success rates, recent executions)

#### Priority 4: Lookup/Reference Configuration
**Backend (✅ Complete)**
- ✅ Database models (LookupConfiguration, LookupCache, CascadingLookupRule)
- ✅ CRUD APIs for lookup configurations (`/api/v1/lookups`)
- ✅ Cascading lookup rules
- ✅ Lookup data fetching with caching
- ✅ RBAC integration

**Frontend (✅ Complete - 95%)**
- ✅ Lookup configuration list and creation (`/frontend/assets/js/nocode-lookups.js`)
- ✅ All source types (entity, custom query, static list, API)
- ✅ Search and filter configuration
- ✅ Cascading dropdown rules
- ✅ Display template configuration
- ⚠️ **Minor:** Advanced API source configuration could be enhanced

### Critical Missing Features

All critical features for Phase 1 have been implemented! ✅

1. ~~**Visual Workflow Canvas** - Drag-and-drop workflow designer with state nodes and transition arrows~~ ✅ **COMPLETED**
2. ~~**Visual Condition/Action Builder** - Drag-and-drop interface for automation rules~~ ✅ **COMPLETED**
3. ~~**Workflow Simulation** - Test workflows before deployment~~ ✅ **COMPLETED**
4. ~~**Automation Testing** - Debug and test automation rules~~ ✅ **COMPLETED**
5. ~~**Monitoring Dashboards** - Real-time monitoring for workflows and automations~~ ✅ **COMPLETED**

---

## 🚀 What's Next: Phase 2 Requirements

### **CRITICAL: Runtime Data Access Layer**

**Problem Statement:**
Phase 1 allows designing entities, workflows, automations, and lookups, but there's NO way to perform CRUD operations on the actual data in those entities at runtime. This is the **single most critical missing piece** for creating functional app modules.

**Current Gap:**
- ✅ Can design a "Customer" entity with fields
- ❌ **Cannot** create, read, update, or delete customer records
- ❌ **Cannot** generate UI for customer management
- ❌ **Cannot** create reports on customer data
- ❌ **Cannot** trigger automations on customer record changes

**Required Implementation:**

#### 1. **Dynamic Data API** (`/api/v1/dynamic-data`)
```
POST   /api/v1/dynamic-data/{entity_name}/records           - Create record
GET    /api/v1/dynamic-data/{entity_name}/records           - List records
GET    /api/v1/dynamic-data/{entity_name}/records/{id}      - Get record
PUT    /api/v1/dynamic-data/{entity_name}/records/{id}      - Update record
DELETE /api/v1/dynamic-data/{entity_name}/records/{id}      - Delete record
GET    /api/v1/dynamic-data/{entity_name}/records/{id}/{rel} - Get related records
POST   /api/v1/dynamic-data/{entity_name}/records/bulk      - Bulk operations
```

#### 2. **Runtime Query Engine**
- Read entity definitions from `EntityDefinition` table
- Generate SQL queries dynamically based on entity metadata
- Apply filters, sorting, pagination at runtime
- Follow relationships through foreign keys
- Enforce field-level RBAC
- Execute validation rules
- Track audit trail

#### 3. **Auto-Generated UI**
- Dynamic route registration for each published entity
- Auto-generate CRUD pages using `EntityManager`
- Automatic menu item creation for published entities
- Routes: `#/dynamic/{entity}/list`, `#/dynamic/{entity}/create`, etc.

#### 4. **Integration Points**
- **Reports:** Allow selecting nocode entities as data sources
- **Dashboards:** Display widgets with nocode entity data
- **Automations:** Trigger rules on nocode entity events
- **Workflows:** Assign workflows to nocode entity records

**Impact:** **WITHOUT THIS, Phase 1 features are design-time only with NO runtime functionality.**

**Estimated Effort:** 2-3 weeks

**Priority:** **HIGHEST** - Blocking feature for functional app modules

### Recent Completions (2026-01-09)

**✅ Priority 1: Migration Preview & Management System** - COMPLETE
- Migration preview UI with SQL display and risk assessment
- Schema diff viewer showing column changes
- Migration history tracking with execution details
- Rollback capability for completed migrations
- Database introspection for auto-importing entities

**✅ Priority 2: Workflow Designer Visual Features** - COMPLETE
- SVG-based visual canvas with drag-and-drop state positioning
- Automatic transition arrows with labels between states
- Workflow simulation with step-by-step execution preview
- Comprehensive approval routing configuration (types, roles, auto-approval)
- Version history UI with timeline view
- Real-time monitoring dashboard with stats and activity feed

**✅ Priority 3: Automation System Visual Features** - COMPLETE
- Visual condition builder with drag-and-drop AND/OR groups
- Visual action builder with sequential step management
- Action template library with predefined common patterns
- Schedule configuration UI with cron expression builder (simple/advanced modes)
- Execution monitoring dashboard with success rate visualization
- Integration of all visual builders into rule detail view

### Implementation Priority Recommendations

**High Priority (Core Functionality)**
1. ~~Migration preview UI for data model~~ ✅ **COMPLETED**
2. ~~Visual workflow canvas - Core feature for workflow designer~~ ✅ **COMPLETED**
3. ~~Visual condition builder for automations - Improves usability significantly~~ ✅ **COMPLETED**

**Medium Priority (Enhanced UX)**
4. ~~Workflow simulation/testing~~ ✅ **COMPLETED**
5. ~~Automation testing tools~~ ✅ **COMPLETED**
6. ~~Migration history and rollback UI~~ ✅ **COMPLETED**

**Low Priority (Nice to Have)**
7. ~~Monitoring dashboards~~ ✅ **COMPLETED**
8. Advanced visualizations
9. Performance optimization tools

---

## Overview

### Scope

This document provides detailed technical design for Phase 1 priorities:

- **Priority 1:** Data Model Designer (Entity/Table Creator)
- **Priority 2:** Workflow/Business Process Designer
- **Priority 3:** Automation & Trigger System
- **Priority 4:** Lookup/Reference Configuration

These four features form the **Core Foundation** for the no-code platform, enabling users to:
1. Create database entities without backend code
2. Define business processes and workflows visually
3. Configure event-driven automation without code
4. Establish data relationships and lookup configurations

### Design Principles

1. **Metadata-Driven:** All configurations stored as metadata in the database
2. **RBAC-Aware:** Granular permission controls at every level
3. **Tenant-Isolated:** Complete multi-tenancy support
4. **Version-Controlled:** Track all changes with audit trail
5. **Extensible:** Designed to integrate with existing platform features
6. **User-Friendly:** Intuitive visual interfaces for non-developers

### Dependencies

**Existing Features Leveraged:**
- Entity Metadata System (`/backend/app/models/metadata.py`)
- RBAC Management (`/backend/app/routers/rbac.py`)
- Audit System (`/backend/app/routers/audit.py`)
- Dynamic Form System (`/frontend/assets/js/dynamic-form.js`)

---

## Priority 1: Data Model Designer

### 1.1 Overview

**Purpose:** Enable sysadmins and developers to create, modify, and manage database entities (tables) and their relationships through a visual interface without writing backend code.

**Key Capabilities:**
- Visual entity/table creation
- Field definition with data types and constraints
- Relationship management (one-to-many, many-to-many, one-to-one)
- Index and constraint management
- Schema versioning and migration
- Data migration tools

---

### 1.2 Database Schema

#### 1.2.1 Entity Definition Model

```sql
-- Table: entity_definitions
CREATE TABLE entity_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Basic Info
    name VARCHAR(100) NOT NULL,  -- Technical name (snake_case)
    label VARCHAR(200) NOT NULL,  -- Display name
    plural_label VARCHAR(200),
    description TEXT,
    icon VARCHAR(50),  -- Phosphor icon name

    -- Type & Category
    entity_type VARCHAR(50) DEFAULT 'custom',  -- 'system', 'custom', 'virtual'
    category VARCHAR(100),  -- Grouping for UI

    -- Table Info
    table_name VARCHAR(100) NOT NULL,  -- Actual database table name
    schema_name VARCHAR(100) DEFAULT 'public',

    -- Configuration
    is_audited BOOLEAN DEFAULT true,
    is_versioned BOOLEAN DEFAULT false,
    supports_soft_delete BOOLEAN DEFAULT true,
    supports_attachments BOOLEAN DEFAULT true,
    supports_comments BOOLEAN DEFAULT true,

    -- Layout & Display
    primary_field VARCHAR(100),  -- Field to use as record title
    default_sort_field VARCHAR(100),
    default_sort_order VARCHAR(10) DEFAULT 'ASC',
    records_per_page INTEGER DEFAULT 25,

    -- Status
    status VARCHAR(50) DEFAULT 'draft',  -- 'draft', 'published', 'migrating', 'archived'
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    metadata JSONB DEFAULT '{}',  -- Extended configuration

    -- Versioning
    version INTEGER DEFAULT 1,
    parent_version_id UUID REFERENCES entity_definitions(id),

    -- Audit fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT false,

    UNIQUE(tenant_id, name),
    UNIQUE(tenant_id, table_name)
);

CREATE INDEX idx_entity_definitions_tenant ON entity_definitions(tenant_id) WHERE is_deleted = false;
CREATE INDEX idx_entity_definitions_status ON entity_definitions(status);
CREATE INDEX idx_entity_definitions_type ON entity_definitions(entity_type);
```

#### 1.2.2 Field Definition Model

```sql
-- Table: field_definitions
CREATE TABLE field_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entity_definitions(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Basic Info
    name VARCHAR(100) NOT NULL,  -- Technical name (snake_case)
    label VARCHAR(200) NOT NULL,  -- Display name
    description TEXT,
    help_text TEXT,

    -- Field Type
    field_type VARCHAR(50) NOT NULL,  -- 'string', 'integer', 'decimal', 'date', etc.
    data_type VARCHAR(50) NOT NULL,  -- Database type: 'VARCHAR', 'INTEGER', 'TIMESTAMP', etc.

    -- Constraints
    is_required BOOLEAN DEFAULT false,
    is_unique BOOLEAN DEFAULT false,
    is_indexed BOOLEAN DEFAULT false,
    is_nullable BOOLEAN DEFAULT true,

    -- String Constraints
    max_length INTEGER,
    min_length INTEGER,

    -- Numeric Constraints
    max_value NUMERIC,
    min_value NUMERIC,
    decimal_places INTEGER,

    -- Default Value
    default_value TEXT,
    default_expression TEXT,  -- SQL expression for dynamic defaults

    -- Validation
    validation_rules JSONB DEFAULT '[]',  -- Custom validation rules
    allowed_values JSONB,  -- For enum-like fields

    -- Display & Behavior
    display_order INTEGER DEFAULT 0,
    is_readonly BOOLEAN DEFAULT false,
    is_system BOOLEAN DEFAULT false,  -- System fields can't be deleted
    is_calculated BOOLEAN DEFAULT false,
    calculation_formula TEXT,  -- Formula for calculated fields

    -- UI Configuration
    input_type VARCHAR(50),  -- 'text', 'textarea', 'select', 'date-picker', etc.
    placeholder TEXT,
    prefix TEXT,  -- e.g., '$' for currency
    suffix TEXT,  -- e.g., 'kg' for weight

    -- Relationship Fields (for lookup/reference fields)
    reference_entity_id UUID REFERENCES entity_definitions(id),
    reference_field VARCHAR(100),  -- Field in referenced entity to display
    relationship_type VARCHAR(50),  -- 'many-to-one', 'one-to-one'

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    is_deleted BOOLEAN DEFAULT false,

    UNIQUE(entity_id, name)
);

CREATE INDEX idx_field_definitions_entity ON field_definitions(entity_id) WHERE is_deleted = false;
CREATE INDEX idx_field_definitions_type ON field_definitions(field_type);
```

#### 1.2.3 Relationship Definition Model

```sql
-- Table: relationship_definitions
CREATE TABLE relationship_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Basic Info
    name VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    description TEXT,

    -- Relationship Type
    relationship_type VARCHAR(50) NOT NULL,  -- 'one-to-many', 'many-to-many', 'one-to-one'

    -- Source Entity
    source_entity_id UUID NOT NULL REFERENCES entity_definitions(id),
    source_field_name VARCHAR(100),  -- Field name to create on source

    -- Target Entity
    target_entity_id UUID NOT NULL REFERENCES entity_definitions(id),
    target_field_name VARCHAR(100),  -- Field name to create on target

    -- Junction Table (for many-to-many)
    junction_table_name VARCHAR(100),
    junction_source_field VARCHAR(100),
    junction_target_field VARCHAR(100),

    -- Cascade Behavior
    on_delete VARCHAR(50) DEFAULT 'NO ACTION',  -- 'CASCADE', 'SET NULL', 'RESTRICT', 'NO ACTION'
    on_update VARCHAR(50) DEFAULT 'NO ACTION',

    -- Display Configuration
    is_active BOOLEAN DEFAULT true,
    display_in_source BOOLEAN DEFAULT true,
    display_in_target BOOLEAN DEFAULT true,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    is_deleted BOOLEAN DEFAULT false,

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_relationship_definitions_source ON relationship_definitions(source_entity_id);
CREATE INDEX idx_relationship_definitions_target ON relationship_definitions(target_entity_id);
```

#### 1.2.4 Index Definition Model

```sql
-- Table: index_definitions
CREATE TABLE index_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entity_definitions(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Basic Info
    name VARCHAR(100) NOT NULL,
    index_type VARCHAR(50) DEFAULT 'btree',  -- 'btree', 'hash', 'gin', 'gist'

    -- Fields (ordered)
    field_names JSONB NOT NULL,  -- Array of field names

    -- Configuration
    is_unique BOOLEAN DEFAULT false,
    is_partial BOOLEAN DEFAULT false,
    where_clause TEXT,  -- For partial indexes

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    is_deleted BOOLEAN DEFAULT false,

    UNIQUE(entity_id, name)
);

CREATE INDEX idx_index_definitions_entity ON index_definitions(entity_id);
```

#### 1.2.5 Migration History Model

```sql
-- Table: entity_migrations
CREATE TABLE entity_migrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entity_definitions(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Migration Info
    migration_name VARCHAR(200) NOT NULL,
    migration_type VARCHAR(50) NOT NULL,  -- 'create', 'alter', 'drop'

    -- Version Info
    from_version INTEGER,
    to_version INTEGER NOT NULL,

    -- SQL Scripts
    up_script TEXT NOT NULL,  -- SQL to apply migration
    down_script TEXT,  -- SQL to rollback migration

    -- Execution
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed', 'rolled_back'
    executed_at TIMESTAMP,
    execution_time_ms INTEGER,
    error_message TEXT,

    -- Metadata
    changes JSONB,  -- Detailed change log

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_entity_migrations_entity ON entity_migrations(entity_id);
CREATE INDEX idx_entity_migrations_status ON entity_migrations(status);
```

---

### 1.3 Backend API

#### 1.3.1 Router: `/backend/app/routers/data_model.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.rbac import has_permission
from app.schemas.data_model import (
    EntityDefinitionCreate,
    EntityDefinitionUpdate,
    EntityDefinitionResponse,
    FieldDefinitionCreate,
    FieldDefinitionUpdate,
    FieldDefinitionResponse,
    RelationshipDefinitionCreate,
    RelationshipDefinitionResponse,
    MigrationResponse,
    SchemaPreviewResponse
)
from app.services.data_model_service import DataModelService

router = APIRouter(prefix="/api/v1/data-model", tags=["Data Model"])

# ==================== Entity Endpoints ====================

@router.post("/entities", response_model=EntityDefinitionResponse)
@has_permission("data_model:create:tenant")
async def create_entity(
    entity: EntityDefinitionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new entity definition"""
    service = DataModelService(db, current_user)
    return await service.create_entity(entity)


@router.get("/entities", response_model=List[EntityDefinitionResponse])
@has_permission("data_model:read:tenant")
async def list_entities(
    category: Optional[str] = None,
    entity_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all entity definitions"""
    service = DataModelService(db, current_user)
    return await service.list_entities(category, entity_type, status)


@router.get("/entities/{entity_id}", response_model=EntityDefinitionResponse)
@has_permission("data_model:read:tenant")
async def get_entity(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get entity definition by ID"""
    service = DataModelService(db, current_user)
    return await service.get_entity(entity_id)


@router.put("/entities/{entity_id}", response_model=EntityDefinitionResponse)
@has_permission("data_model:update:tenant")
async def update_entity(
    entity_id: UUID,
    entity: EntityDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update entity definition"""
    service = DataModelService(db, current_user)
    return await service.update_entity(entity_id, entity)


@router.delete("/entities/{entity_id}")
@has_permission("data_model:delete:tenant")
async def delete_entity(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete entity definition (soft delete)"""
    service = DataModelService(db, current_user)
    return await service.delete_entity(entity_id)


# ==================== Field Endpoints ====================

@router.post("/entities/{entity_id}/fields", response_model=FieldDefinitionResponse)
@has_permission("data_model:create:tenant")
async def create_field(
    entity_id: UUID,
    field: FieldDefinitionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add a field to an entity"""
    service = DataModelService(db, current_user)
    return await service.create_field(entity_id, field)


@router.get("/entities/{entity_id}/fields", response_model=List[FieldDefinitionResponse])
@has_permission("data_model:read:tenant")
async def list_fields(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all fields for an entity"""
    service = DataModelService(db, current_user)
    return await service.list_fields(entity_id)


@router.put("/entities/{entity_id}/fields/{field_id}", response_model=FieldDefinitionResponse)
@has_permission("data_model:update:tenant")
async def update_field(
    entity_id: UUID,
    field_id: UUID,
    field: FieldDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a field definition"""
    service = DataModelService(db, current_user)
    return await service.update_field(entity_id, field_id, field)


@router.delete("/entities/{entity_id}/fields/{field_id}")
@has_permission("data_model:delete:tenant")
async def delete_field(
    entity_id: UUID,
    field_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a field definition"""
    service = DataModelService(db, current_user)
    return await service.delete_field(entity_id, field_id)


# ==================== Relationship Endpoints ====================

@router.post("/relationships", response_model=RelationshipDefinitionResponse)
@has_permission("data_model:create:tenant")
async def create_relationship(
    relationship: RelationshipDefinitionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a relationship between entities"""
    service = DataModelService(db, current_user)
    return await service.create_relationship(relationship)


@router.get("/relationships", response_model=List[RelationshipDefinitionResponse])
@has_permission("data_model:read:tenant")
async def list_relationships(
    entity_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all relationships (optionally filtered by entity)"""
    service = DataModelService(db, current_user)
    return await service.list_relationships(entity_id)


@router.delete("/relationships/{relationship_id}")
@has_permission("data_model:delete:tenant")
async def delete_relationship(
    relationship_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a relationship"""
    service = DataModelService(db, current_user)
    return await service.delete_relationship(relationship_id)


# ==================== Migration Endpoints ====================

@router.post("/entities/{entity_id}/preview-migration", response_model=SchemaPreviewResponse)
@has_permission("data_model:read:tenant")
async def preview_migration(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Preview schema changes before applying"""
    service = DataModelService(db, current_user)
    return await service.preview_migration(entity_id)


@router.post("/entities/{entity_id}/publish", response_model=MigrationResponse)
@has_permission("data_model:execute:tenant")
async def publish_entity(
    entity_id: UUID,
    commit_message: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Publish entity (generate and execute migration)"""
    service = DataModelService(db, current_user)
    return await service.publish_entity(entity_id, commit_message)


@router.get("/entities/{entity_id}/migrations", response_model=List[MigrationResponse])
@has_permission("data_model:read:tenant")
async def list_migrations(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List migration history for an entity"""
    service = DataModelService(db, current_user)
    return await service.list_migrations(entity_id)


@router.post("/migrations/{migration_id}/rollback")
@has_permission("data_model:execute:tenant")
async def rollback_migration(
    migration_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Rollback a migration"""
    service = DataModelService(db, current_user)
    return await service.rollback_migration(migration_id)


# ==================== Validation Endpoints ====================

@router.post("/entities/validate-name")
@has_permission("data_model:read:tenant")
async def validate_entity_name(
    name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Validate entity name availability and format"""
    service = DataModelService(db, current_user)
    return await service.validate_entity_name(name)


@router.post("/entities/{entity_id}/fields/validate-name")
@has_permission("data_model:read:tenant")
async def validate_field_name(
    entity_id: UUID,
    name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Validate field name availability and format"""
    service = DataModelService(db, current_user)
    return await service.validate_field_name(entity_id, name)
```

#### 1.3.2 Service: `/backend/app/services/data_model_service.py`

```python
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from uuid import UUID
import re

from app.models.data_model import (
    EntityDefinition,
    FieldDefinition,
    RelationshipDefinition,
    EntityMigration
)
from app.schemas.data_model import *
from app.core.exceptions import ValidationError, NotFoundError
from app.services.migration_generator import MigrationGenerator
from app.services.audit_service import AuditService


class DataModelService:
    """Service for managing data model definitions"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self.tenant_id = current_user.tenant_id
        self.audit = AuditService(db)
        self.migration_gen = MigrationGenerator(db)

    # ==================== Entity Methods ====================

    async def create_entity(self, entity_data: EntityDefinitionCreate) -> EntityDefinition:
        """Create a new entity definition"""
        # Validate name format
        if not self._is_valid_identifier(entity_data.name):
            raise ValidationError("Entity name must be valid identifier (snake_case)")

        # Check uniqueness
        exists = self.db.query(EntityDefinition).filter(
            EntityDefinition.tenant_id == self.tenant_id,
            EntityDefinition.name == entity_data.name,
            EntityDefinition.is_deleted == False
        ).first()

        if exists:
            raise ValidationError(f"Entity '{entity_data.name}' already exists")

        # Generate table name if not provided
        table_name = entity_data.table_name or f"custom_{entity_data.name}"

        # Create entity
        entity = EntityDefinition(
            tenant_id=self.tenant_id,
            table_name=table_name,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
            **entity_data.dict(exclude={"table_name"})
        )

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        # Audit log
        await self.audit.log_action(
            action="create",
            entity_type="entity_definition",
            entity_id=entity.id,
            changes=entity_data.dict()
        )

        return entity

    async def update_entity(self, entity_id: UUID, entity_data: EntityDefinitionUpdate) -> EntityDefinition:
        """Update entity definition"""
        entity = self._get_entity(entity_id)

        if entity.status == 'published':
            # Create new version for published entities
            entity = self._create_version(entity)

        # Update fields
        update_data = entity_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(entity, key, value)

        entity.updated_by = self.current_user.id

        self.db.commit()
        self.db.refresh(entity)

        await self.audit.log_action("update", "entity_definition", entity_id, update_data)

        return entity

    async def delete_entity(self, entity_id: UUID):
        """Soft delete entity"""
        entity = self._get_entity(entity_id)

        if entity.status == 'published':
            raise ValidationError("Cannot delete published entity. Archive it first.")

        entity.is_deleted = True
        entity.deleted_at = func.now()

        self.db.commit()

        await self.audit.log_action("delete", "entity_definition", entity_id)

        return {"message": "Entity deleted successfully"}

    # ==================== Field Methods ====================

    async def create_field(self, entity_id: UUID, field_data: FieldDefinitionCreate) -> FieldDefinition:
        """Add field to entity"""
        entity = self._get_entity(entity_id)

        # Validate field name
        if not self._is_valid_identifier(field_data.name):
            raise ValidationError("Field name must be valid identifier")

        # Check uniqueness within entity
        exists = self.db.query(FieldDefinition).filter(
            FieldDefinition.entity_id == entity_id,
            FieldDefinition.name == field_data.name,
            FieldDefinition.is_deleted == False
        ).first()

        if exists:
            raise ValidationError(f"Field '{field_data.name}' already exists")

        # Map field type to data type
        data_type = self._map_field_type_to_db_type(field_data.field_type, field_data)

        field = FieldDefinition(
            entity_id=entity_id,
            tenant_id=self.tenant_id,
            data_type=data_type,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
            **field_data.dict()
        )

        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)

        await self.audit.log_action("create", "field_definition", field.id, field_data.dict())

        return field

    # ==================== Relationship Methods ====================

    async def create_relationship(self, rel_data: RelationshipDefinitionCreate) -> RelationshipDefinition:
        """Create relationship between entities"""
        # Validate source and target entities exist
        source = self._get_entity(rel_data.source_entity_id)
        target = self._get_entity(rel_data.target_entity_id)

        relationship = RelationshipDefinition(
            tenant_id=self.tenant_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
            **rel_data.dict()
        )

        self.db.add(relationship)

        # Create corresponding fields based on relationship type
        if rel_data.relationship_type == 'one-to-many':
            # Add foreign key field to target entity
            await self._create_foreign_key_field(
                target.id,
                rel_data.target_field_name or f"{source.name}_id",
                source.id
            )
        elif rel_data.relationship_type == 'many-to-many':
            # Create junction table
            await self._create_junction_table(relationship)

        self.db.commit()
        self.db.refresh(relationship)

        await self.audit.log_action("create", "relationship_definition", relationship.id, rel_data.dict())

        return relationship

    # ==================== Migration Methods ====================

    async def preview_migration(self, entity_id: UUID) -> SchemaPreviewResponse:
        """Preview SQL changes for entity"""
        entity = self._get_entity(entity_id)

        # Generate migration SQL
        up_sql, down_sql = await self.migration_gen.generate_migration(entity)

        return SchemaPreviewResponse(
            entity_id=entity_id,
            entity_name=entity.name,
            up_script=up_sql,
            down_script=down_sql,
            estimated_impact=self._estimate_impact(entity)
        )

    async def publish_entity(self, entity_id: UUID, commit_message: str) -> MigrationResponse:
        """Publish entity and execute migration"""
        entity = self._get_entity(entity_id)

        if entity.status == 'published':
            raise ValidationError("Entity already published")

        # Generate migration
        up_sql, down_sql = await self.migration_gen.generate_migration(entity)

        # Create migration record
        migration = EntityMigration(
            entity_id=entity_id,
            tenant_id=self.tenant_id,
            migration_name=f"{entity.name}_v{entity.version}",
            migration_type='create' if entity.version == 1 else 'alter',
            from_version=entity.version - 1 if entity.version > 1 else None,
            to_version=entity.version,
            up_script=up_sql,
            down_script=down_sql,
            status='pending',
            created_by=self.current_user.id
        )

        self.db.add(migration)
        self.db.commit()

        # Execute migration
        try:
            migration.status = 'running'
            self.db.commit()

            start_time = time.time()

            # Execute in transaction
            self.db.execute(text(up_sql))

            execution_time = int((time.time() - start_time) * 1000)

            migration.status = 'completed'
            migration.executed_at = func.now()
            migration.execution_time_ms = execution_time

            # Update entity status
            entity.status = 'published'

            self.db.commit()

            await self.audit.log_action("publish", "entity_definition", entity_id, {
                "migration_id": migration.id,
                "commit_message": commit_message
            })

            return migration

        except Exception as e:
            migration.status = 'failed'
            migration.error_message = str(e)
            self.db.commit()

            raise ValidationError(f"Migration failed: {str(e)}")

    # ==================== Helper Methods ====================

    def _get_entity(self, entity_id: UUID) -> EntityDefinition:
        """Get entity or raise 404"""
        entity = self.db.query(EntityDefinition).filter(
            EntityDefinition.id == entity_id,
            EntityDefinition.tenant_id == self.tenant_id,
            EntityDefinition.is_deleted == False
        ).first()

        if not entity:
            raise NotFoundError(f"Entity {entity_id} not found")

        return entity

    def _is_valid_identifier(self, name: str) -> bool:
        """Validate identifier format (snake_case)"""
        return bool(re.match(r'^[a-z][a-z0-9_]*$', name))

    def _map_field_type_to_db_type(self, field_type: str, field_data) -> str:
        """Map abstract field type to database type"""
        type_mapping = {
            'string': f"VARCHAR({field_data.max_length or 255})",
            'text': 'TEXT',
            'integer': 'INTEGER',
            'biginteger': 'BIGINT',
            'decimal': f"NUMERIC({field_data.decimal_places or 10}, 2)",
            'boolean': 'BOOLEAN',
            'date': 'DATE',
            'datetime': 'TIMESTAMP',
            'time': 'TIME',
            'json': 'JSONB',
            'uuid': 'UUID',
            'email': 'VARCHAR(255)',
            'url': 'VARCHAR(500)',
            'phone': 'VARCHAR(20)',
        }

        return type_mapping.get(field_type, 'TEXT')
```

---

### 1.4 Frontend Components

#### 1.4.1 Main Component: `/frontend/components/data-model-designer.js`

```javascript
/**
 * Data Model Designer
 * Visual entity and field designer for creating database tables
 */

class DataModelDesigner {
    constructor() {
        this.currentEntity = null;
        this.entities = [];
        this.fields = [];
        this.relationships = [];
        this.currentStep = 1;

        this.service = new DataModelService();
        this.init();
    }

    init() {
        this.renderLayout();
        this.attachEventListeners();
        this.loadEntities();
    }

    renderLayout() {
        const container = document.getElementById('app-container');
        container.innerHTML = `
            <div class="data-model-designer">
                <!-- Header -->
                <div class="designer-header">
                    <div class="header-left">
                        <h1><i class="ph-database"></i> Data Model Designer</h1>
                        <p class="subtitle">Create and manage database entities</p>
                    </div>
                    <div class="header-right">
                        <button class="btn btn-secondary" id="btn-refresh">
                            <i class="ph-arrows-clockwise"></i> Refresh
                        </button>
                        <button class="btn btn-primary" id="btn-new-entity">
                            <i class="ph-plus"></i> New Entity
                        </button>
                    </div>
                </div>

                <!-- Main Content -->
                <div class="designer-content">
                    <!-- Sidebar: Entity List -->
                    <div class="entity-sidebar">
                        <div class="sidebar-header">
                            <h3>Entities</h3>
                            <input type="text" id="entity-search" placeholder="Search entities..." class="form-control-sm">
                        </div>
                        <div class="entity-list" id="entity-list">
                            <!-- Entity list items -->
                        </div>
                    </div>

                    <!-- Main Panel: Entity Designer -->
                    <div class="entity-designer" id="entity-designer">
                        <!-- Empty state or entity details -->
                    </div>

                    <!-- Right Panel: Properties & Preview -->
                    <div class="properties-panel" id="properties-panel">
                        <!-- Properties and schema preview -->
                    </div>
                </div>
            </div>

            <!-- Entity Designer Modal -->
            <div class="modal fade" id="entity-modal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Entity Designer</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Multi-step wizard -->
                            <div class="wizard-steps">
                                <div class="step active" data-step="1">
                                    <span class="step-number">1</span>
                                    <span class="step-label">Basic Info</span>
                                </div>
                                <div class="step" data-step="2">
                                    <span class="step-number">2</span>
                                    <span class="step-label">Fields</span>
                                </div>
                                <div class="step" data-step="3">
                                    <span class="step-number">3</span>
                                    <span class="step-label">Relationships</span>
                                </div>
                                <div class="step" data-step="4">
                                    <span class="step-number">4</span>
                                    <span class="step-label">Indexes</span>
                                </div>
                                <div class="step" data-step="5">
                                    <span class="step-number">5</span>
                                    <span class="step-label">Preview</span>
                                </div>
                            </div>

                            <div class="wizard-content" id="wizard-content">
                                <!-- Step content -->
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" id="btn-prev-step">
                                <i class="ph-caret-left"></i> Previous
                            </button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="btn-next-step">
                                Next <i class="ph-caret-right"></i>
                            </button>
                            <button type="button" class="btn btn-success" id="btn-save-entity" style="display:none;">
                                <i class="ph-check"></i> Save Draft
                            </button>
                            <button type="button" class="btn btn-primary" id="btn-publish-entity" style="display:none;">
                                <i class="ph-rocket-launch"></i> Publish
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Field Designer Modal -->
            <div class="modal fade" id="field-modal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Field Designer</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="field-modal-body">
                            <!-- Field configuration form -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="btn-save-field">
                                <i class="ph-check"></i> Save Field
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // ==================== Step Rendering ====================

    renderStep1_BasicInfo() {
        return `
            <div class="step-content">
                <h4>Basic Information</h4>
                <p class="text-muted">Define the entity's basic properties</p>

                <div class="row g-3 mt-3">
                    <div class="col-md-6">
                        <label class="form-label required">Entity Name</label>
                        <input type="text" class="form-control" id="entity-name"
                               placeholder="e.g., customer, product, order"
                               pattern="[a-z][a-z0-9_]*">
                        <small class="form-text text-muted">Technical name (snake_case, lowercase)</small>
                    </div>

                    <div class="col-md-6">
                        <label class="form-label required">Display Label</label>
                        <input type="text" class="form-control" id="entity-label"
                               placeholder="e.g., Customer, Product, Order">
                        <small class="form-text text-muted">Human-readable name</small>
                    </div>

                    <div class="col-md-6">
                        <label class="form-label">Plural Label</label>
                        <input type="text" class="form-control" id="entity-plural"
                               placeholder="e.g., Customers, Products, Orders">
                    </div>

                    <div class="col-md-6">
                        <label class="form-label">Icon</label>
                        <select class="form-select" id="entity-icon">
                            <option value="">Select icon...</option>
                            <option value="users">👥 Users</option>
                            <option value="package">📦 Package</option>
                            <option value="shopping-cart">🛒 Shopping Cart</option>
                            <option value="file-text">📄 Document</option>
                            <option value="briefcase">💼 Briefcase</option>
                        </select>
                    </div>

                    <div class="col-md-6">
                        <label class="form-label">Category</label>
                        <select class="form-select" id="entity-category">
                            <option value="">Select category...</option>
                            <option value="core">Core</option>
                            <option value="business">Business</option>
                            <option value="support">Support</option>
                            <option value="configuration">Configuration</option>
                        </select>
                    </div>

                    <div class="col-12">
                        <label class="form-label">Description</label>
                        <textarea class="form-control" id="entity-description" rows="3"
                                  placeholder="Describe the purpose of this entity..."></textarea>
                    </div>

                    <div class="col-12">
                        <h5 class="mt-3">Entity Features</h5>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="feature-audit" checked>
                            <label class="form-check-label" for="feature-audit">
                                Enable audit trail (track all changes)
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="feature-soft-delete" checked>
                            <label class="form-check-label" for="feature-soft-delete">
                                Enable soft delete (mark as deleted instead of removing)
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="feature-versioning">
                            <label class="form-check-label" for="feature-versioning">
                                Enable versioning (keep historical versions)
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="feature-attachments" checked>
                            <label class="form-check-label" for="feature-attachments">
                                Support file attachments
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="feature-comments" checked>
                            <label class="form-check-label" for="feature-comments">
                                Support comments/notes
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderStep2_Fields() {
        return `
            <div class="step-content">
                <h4>Field Definitions</h4>
                <p class="text-muted">Define the fields for this entity</p>

                <div class="d-flex justify-content-between align-items-center mt-3 mb-3">
                    <div>
                        <span class="badge bg-info" id="field-count">0 fields defined</span>
                    </div>
                    <button class="btn btn-sm btn-primary" id="btn-add-field">
                        <i class="ph-plus"></i> Add Field
                    </button>
                </div>

                <div class="field-list" id="field-list">
                    <!-- System fields (read-only) -->
                    <div class="field-group">
                        <h6 class="text-muted">System Fields (Automatic)</h6>
                        <div class="system-fields">
                            <div class="field-item system">
                                <i class="ph-key"></i>
                                <span class="field-name">id</span>
                                <span class="field-type badge bg-secondary">UUID</span>
                                <span class="field-desc">Primary key (auto-generated)</span>
                            </div>
                            <div class="field-item system">
                                <i class="ph-clock"></i>
                                <span class="field-name">created_at</span>
                                <span class="field-type badge bg-secondary">TIMESTAMP</span>
                                <span class="field-desc">Creation timestamp</span>
                            </div>
                            <div class="field-item system">
                                <i class="ph-clock"></i>
                                <span class="field-name">updated_at</span>
                                <span class="field-type badge bg-secondary">TIMESTAMP</span>
                                <span class="field-desc">Last update timestamp</span>
                            </div>
                            <div class="field-item system">
                                <i class="ph-user"></i>
                                <span class="field-name">created_by</span>
                                <span class="field-type badge bg-secondary">UUID</span>
                                <span class="field-desc">User who created record</span>
                            </div>
                            <div class="field-item system">
                                <i class="ph-user"></i>
                                <span class="field-name">updated_by</span>
                                <span class="field-type badge bg-secondary">UUID</span>
                                <span class="field-desc">User who last updated</span>
                            </div>
                        </div>
                    </div>

                    <!-- Custom fields -->
                    <div class="field-group mt-4">
                        <h6>Custom Fields</h6>
                        <div class="custom-fields" id="custom-fields">
                            <!-- Dynamically added fields -->
                            <div class="empty-state text-center py-4" id="fields-empty-state">
                                <i class="ph-plus-circle" style="font-size: 48px; opacity: 0.3;"></i>
                                <p class="text-muted">No custom fields defined yet</p>
                                <button class="btn btn-sm btn-outline-primary" onclick="designerInstance.openFieldDesigner()">
                                    Add First Field
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderFieldDesignerForm(field = null) {
        const isEdit = field !== null;

        return `
            <form id="field-form">
                <div class="row g-3">
                    <!-- Basic Info -->
                    <div class="col-md-6">
                        <label class="form-label required">Field Name</label>
                        <input type="text" class="form-control" id="field-name"
                               value="${field?.name || ''}"
                               placeholder="e.g., first_name, email, price"
                               pattern="[a-z][a-z0-9_]*" required>
                        <small class="form-text text-muted">Technical name (snake_case)</small>
                    </div>

                    <div class="col-md-6">
                        <label class="form-label required">Display Label</label>
                        <input type="text" class="form-control" id="field-label"
                               value="${field?.label || ''}"
                               placeholder="e.g., First Name, Email, Price" required>
                    </div>

                    <div class="col-md-6">
                        <label class="form-label required">Field Type</label>
                        <select class="form-select" id="field-type" required>
                            <option value="">Select type...</option>
                            <optgroup label="Text">
                                <option value="string">String (short text)</option>
                                <option value="text">Text (long text)</option>
                                <option value="email">Email</option>
                                <option value="url">URL</option>
                                <option value="phone">Phone Number</option>
                            </optgroup>
                            <optgroup label="Numbers">
                                <option value="integer">Integer</option>
                                <option value="decimal">Decimal</option>
                                <option value="currency">Currency</option>
                                <option value="percentage">Percentage</option>
                            </optgroup>
                            <optgroup label="Date & Time">
                                <option value="date">Date</option>
                                <option value="datetime">Date & Time</option>
                                <option value="time">Time</option>
                            </optgroup>
                            <optgroup label="Other">
                                <option value="boolean">Boolean (Yes/No)</option>
                                <option value="json">JSON Data</option>
                                <option value="uuid">UUID</option>
                                <option value="lookup">Lookup (Reference)</option>
                            </optgroup>
                        </select>
                    </div>

                    <div class="col-md-6">
                        <label class="form-label">Input Type</label>
                        <select class="form-select" id="field-input-type">
                            <option value="text">Text Input</option>
                            <option value="textarea">Text Area</option>
                            <option value="select">Dropdown</option>
                            <option value="radio">Radio Buttons</option>
                            <option value="checkbox">Checkbox</option>
                            <option value="date-picker">Date Picker</option>
                            <option value="number">Number Input</option>
                        </select>
                    </div>

                    <div class="col-12">
                        <label class="form-label">Description</label>
                        <textarea class="form-control" id="field-description" rows="2"
                                  placeholder="Describe the purpose of this field...">${field?.description || ''}</textarea>
                    </div>

                    <div class="col-12">
                        <label class="form-label">Help Text</label>
                        <input type="text" class="form-control" id="field-help-text"
                               value="${field?.help_text || ''}"
                               placeholder="e.g., Enter your email address">
                        <small class="form-text text-muted">Shown to users when filling the field</small>
                    </div>

                    <!-- Constraints -->
                    <div class="col-12">
                        <h6 class="mt-3">Constraints</h6>
                    </div>

                    <div class="col-md-6">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="field-required">
                            <label class="form-check-label" for="field-required">
                                Required (cannot be empty)
                            </label>
                        </div>
                    </div>

                    <div class="col-md-6">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="field-unique">
                            <label class="form-check-label" for="field-unique">
                                Unique (no duplicates allowed)
                            </label>
                        </div>
                    </div>

                    <div class="col-md-6">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="field-indexed">
                            <label class="form-check-label" for="field-indexed">
                                Indexed (faster searching)
                            </label>
                        </div>
                    </div>

                    <div class="col-md-6">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="field-readonly">
                            <label class="form-check-label" for="field-readonly">
                                Read-only (cannot be edited)
                            </label>
                        </div>
                    </div>

                    <!-- Type-specific options -->
                    <div class="col-12" id="field-type-options">
                        <!-- Dynamically populated based on field type -->
                    </div>

                    <div class="col-md-6">
                        <label class="form-label">Default Value</label>
                        <input type="text" class="form-control" id="field-default-value"
                               placeholder="Optional default value">
                    </div>

                    <div class="col-md-6">
                        <label class="form-label">Placeholder</label>
                        <input type="text" class="form-control" id="field-placeholder"
                               placeholder="e.g., Enter value...">
                    </div>
                </div>
            </form>
        `;
    }

    // Additional methods for handling field types, relationships, etc.
    // ... (continued in next part)
}

// Initialize
let designerInstance;
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.hash.startsWith('#data-model')) {
        designerInstance = new DataModelDesigner();
    }
});
```

---

### 1.5 User Workflows

#### Workflow 1: Create New Entity

1. **Access Designer**
   - Navigate to `#data-model`
   - Click "New Entity" button

2. **Step 1: Basic Information**
   - Enter entity name (e.g., "customer")
   - Enter display label (e.g., "Customer")
   - Select icon and category
   - Configure features (audit, soft delete, etc.)

3. **Step 2: Define Fields**
   - Add custom fields (name, email, phone, etc.)
   - Configure field types and constraints
   - Set validation rules

4. **Step 3: Define Relationships**
   - Add relationships to other entities
   - Configure relationship type (one-to-many, etc.)
   - Set cascade behaviors

5. **Step 4: Configure Indexes**
   - Add indexes for performance
   - Configure unique constraints

5. **Step 5: Preview & Publish**
   - Review generated SQL schema
   - Preview migration impact
   - Save as draft OR publish immediately
   - Execute migration to create actual table

---

## Priority 2: Workflow/Business Process Designer

### 2.1 Overview

**Purpose:** Enable visual design of business workflows, approval processes, and state machines without writing code.

**Key Capabilities:**
- Visual workflow canvas (drag-and-drop)
- State and transition management
- Approval routing logic
- Escalation rules (SLA-based)
- Workflow versioning
- Instance tracking and monitoring

---

### 2.2 Database Schema

#### 2.2.1 Workflow Definition Model

```sql
-- Table: workflow_definitions
CREATE TABLE workflow_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Basic Info
    name VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    -- Associated Entity
    entity_id UUID REFERENCES entity_definitions(id),  -- Entity this workflow applies to

    -- Configuration
    trigger_type VARCHAR(50) DEFAULT 'manual',  -- 'manual', 'automatic', 'scheduled'
    trigger_conditions JSONB,  -- Conditions for automatic triggers

    -- Canvas Data
    canvas_data JSONB NOT NULL,  -- Workflow diagram (nodes, edges, positions)

    -- Version Control
    version INTEGER DEFAULT 1,
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMP,
    parent_version_id UUID REFERENCES workflow_definitions(id),

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    is_deleted BOOLEAN DEFAULT false,

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_workflow_definitions_tenant ON workflow_definitions(tenant_id) WHERE is_deleted = false;
CREATE INDEX idx_workflow_definitions_entity ON workflow_definitions(entity_id);
```

#### 2.2.2 Workflow State Model

```sql
-- Table: workflow_states
CREATE TABLE workflow_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflow_definitions(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Basic Info
    name VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    description TEXT,

    -- State Type
    state_type VARCHAR(50) NOT NULL,  -- 'start', 'intermediate', 'end', 'approval', 'condition'

    -- Display
    color VARCHAR(50),
    icon VARCHAR(50),
    position_x INTEGER,  -- Canvas position
    position_y INTEGER,

    -- Behavior
    is_final BOOLEAN DEFAULT false,  -- End state?
    requires_approval BOOLEAN DEFAULT false,
    approval_config JSONB,  -- Approval routing rules

    -- SLA & Escalation
    sla_hours INTEGER,  -- Time limit for this state
    escalation_rules JSONB,  -- What happens on SLA breach

    -- Actions on Entry/Exit
    on_entry_actions JSONB DEFAULT '[]',  -- Actions when entering state
    on_exit_actions JSONB DEFAULT '[]',  -- Actions when exiting state

    -- Field Requirements
    required_fields JSONB DEFAULT '[]',  -- Fields that must be filled

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,

    UNIQUE(workflow_id, name)
);

CREATE INDEX idx_workflow_states_workflow ON workflow_states(workflow_id);
```

#### 2.2.3 Workflow Transition Model

```sql
-- Table: workflow_transitions
CREATE TABLE workflow_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflow_definitions(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Basic Info
    name VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    description TEXT,

    -- Source & Target
    from_state_id UUID NOT NULL REFERENCES workflow_states(id),
    to_state_id UUID NOT NULL REFERENCES workflow_states(id),

    -- Conditions
    condition_type VARCHAR(50) DEFAULT 'always',  -- 'always', 'conditional', 'approval'
    conditions JSONB,  -- Conditional logic

    -- Permissions
    allowed_roles JSONB DEFAULT '[]',  -- Roles allowed to execute transition
    allowed_users JSONB DEFAULT '[]',  -- Specific users allowed

    -- Actions
    actions JSONB DEFAULT '[]',  -- Actions to perform on transition

    -- Display
    button_label VARCHAR(100),  -- Label for transition button
    button_style VARCHAR(50),  -- 'primary', 'success', 'danger', etc.
    icon VARCHAR(50),
    display_order INTEGER DEFAULT 0,

    -- Validation
    validation_rules JSONB DEFAULT '[]',

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false
);

CREATE INDEX idx_workflow_transitions_workflow ON workflow_transitions(workflow_id);
CREATE INDEX idx_workflow_transitions_from_state ON workflow_transitions(from_state_id);
CREATE INDEX idx_workflow_transitions_to_state ON workflow_transitions(to_state_id);
```

#### 2.2.4 Workflow Instance Model

```sql
-- Table: workflow_instances
CREATE TABLE workflow_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflow_definitions(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Associated Record
    entity_id UUID NOT NULL REFERENCES entity_definitions(id),
    record_id UUID NOT NULL,  -- ID of the record being processed

    -- Current State
    current_state_id UUID REFERENCES workflow_states(id),
    current_state_entered_at TIMESTAMP,

    -- Status
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'completed', 'cancelled', 'error'

    -- SLA Tracking
    sla_deadline TIMESTAMP,
    is_sla_breached BOOLEAN DEFAULT false,

    -- Context Data
    context_data JSONB DEFAULT '{}',  -- Workflow-specific data

    -- Audit
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    started_by UUID REFERENCES users(id),

    -- Error Handling
    error_message TEXT,
    error_details JSONB
);

CREATE INDEX idx_workflow_instances_workflow ON workflow_instances(workflow_id);
CREATE INDEX idx_workflow_instances_record ON workflow_instances(entity_id, record_id);
CREATE INDEX idx_workflow_instances_status ON workflow_instances(status);
CREATE INDEX idx_workflow_instances_sla ON workflow_instances(sla_deadline) WHERE is_sla_breached = false;
```

#### 2.2.5 Workflow History Model

```sql
-- Table: workflow_history
CREATE TABLE workflow_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES workflow_instances(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Transition Info
    from_state_id UUID REFERENCES workflow_states(id),
    to_state_id UUID REFERENCES workflow_states(id),
    transition_id UUID REFERENCES workflow_transitions(id),

    -- Actor
    performed_by UUID REFERENCES users(id),
    performed_at TIMESTAMP DEFAULT NOW(),

    -- Action Details
    action_type VARCHAR(50),  -- 'transition', 'escalation', 'comment', 'assignment'
    action_data JSONB,

    -- Comments
    comment TEXT,

    -- Duration
    duration_minutes INTEGER,  -- Time spent in previous state

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_workflow_history_instance ON workflow_history(instance_id);
CREATE INDEX idx_workflow_history_performed_by ON workflow_history(performed_by);
```

---

### 2.3 Backend API

#### 2.3.1 Router: `/backend/app/routers/workflows.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.rbac import has_permission
from app.schemas.workflow import *
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])

# ==================== Workflow Definition Endpoints ====================

@router.post("/", response_model=WorkflowDefinitionResponse)
@has_permission("workflows:create:tenant")
async def create_workflow(
    workflow: WorkflowDefinitionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new workflow definition"""
    service = WorkflowService(db, current_user)
    return await service.create_workflow(workflow)


@router.get("/", response_model=List[WorkflowDefinitionResponse])
@has_permission("workflows:read:tenant")
async def list_workflows(
    entity_id: Optional[UUID] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all workflow definitions"""
    service = WorkflowService(db, current_user)
    return await service.list_workflows(entity_id, category)


@router.get("/{workflow_id}", response_model=WorkflowDefinitionResponse)
@has_permission("workflows:read:tenant")
async def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get workflow definition"""
    service = WorkflowService(db, current_user)
    return await service.get_workflow(workflow_id)


@router.put("/{workflow_id}", response_model=WorkflowDefinitionResponse)
@has_permission("workflows:update:tenant")
async def update_workflow(
    workflow_id: UUID,
    workflow: WorkflowDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update workflow definition"""
    service = WorkflowService(db, current_user)
    return await service.update_workflow(workflow_id, workflow)


@router.post("/{workflow_id}/publish")
@has_permission("workflows:execute:tenant")
async def publish_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Publish workflow (make it active)"""
    service = WorkflowService(db, current_user)
    return await service.publish_workflow(workflow_id)


# ==================== State Endpoints ====================

@router.post("/{workflow_id}/states", response_model=WorkflowStateResponse)
@has_permission("workflows:create:tenant")
async def create_state(
    workflow_id: UUID,
    state: WorkflowStateCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add a state to workflow"""
    service = WorkflowService(db, current_user)
    return await service.create_state(workflow_id, state)


@router.put("/{workflow_id}/states/{state_id}", response_model=WorkflowStateResponse)
@has_permission("workflows:update:tenant")
async def update_state(
    workflow_id: UUID,
    state_id: UUID,
    state: WorkflowStateUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a state"""
    service = WorkflowService(db, current_user)
    return await service.update_state(workflow_id, state_id, state)


# ==================== Transition Endpoints ====================

@router.post("/{workflow_id}/transitions", response_model=WorkflowTransitionResponse)
@has_permission("workflows:create:tenant")
async def create_transition(
    workflow_id: UUID,
    transition: WorkflowTransitionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add a transition between states"""
    service = WorkflowService(db, current_user)
    return await service.create_transition(workflow_id, transition)


# ==================== Instance Endpoints ====================

@router.post("/instances/start", response_model=WorkflowInstanceResponse)
@has_permission("workflows:execute:tenant")
async def start_workflow_instance(
    instance: WorkflowInstanceStart,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Start a workflow instance for a record"""
    service = WorkflowService(db, current_user)
    return await service.start_instance(instance)


@router.post("/instances/{instance_id}/transition")
@has_permission("workflows:execute:tenant")
async def execute_transition(
    instance_id: UUID,
    transition: WorkflowTransitionExecute,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Execute a workflow transition"""
    service = WorkflowService(db, current_user)
    return await service.execute_transition(instance_id, transition)


@router.get("/instances/{instance_id}/history", response_model=List[WorkflowHistoryResponse])
@has_permission("workflows:read:tenant")
async def get_workflow_history(
    instance_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get workflow history for an instance"""
    service = WorkflowService(db, current_user)
    return await service.get_history(instance_id)


@router.get("/instances/record/{entity_id}/{record_id}")
@has_permission("workflows:read:tenant")
async def get_record_workflow(
    entity_id: UUID,
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get workflow instance for a specific record"""
    service = WorkflowService(db, current_user)
    return await service.get_record_workflow(entity_id, record_id)


# ==================== Testing & Simulation ====================

@router.post("/{workflow_id}/simulate")
@has_permission("workflows:read:tenant")
async def simulate_workflow(
    workflow_id: UUID,
    simulation: WorkflowSimulation,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Simulate workflow execution (dry run)"""
    service = WorkflowService(db, current_user)
    return await service.simulate_workflow(workflow_id, simulation)
```

---

### 2.4 Frontend Components

#### 2.4.1 Main Component: `/frontend/components/workflow-designer.js`

```javascript
/**
 * Workflow Designer
 * Visual workflow builder using canvas-based drag-and-drop
 * Library: ReactFlow or similar canvas library
 */

class WorkflowDesigner {
    constructor() {
        this.currentWorkflow = null;
        this.states = [];
        this.transitions = [];
        this.canvas = null;

        this.service = new WorkflowService();
        this.init();
    }

    init() {
        this.renderLayout();
        this.initializeCanvas();
        this.attachEventListeners();
    }

    renderLayout() {
        const container = document.getElementById('app-container');
        container.innerHTML = `
            <div class="workflow-designer">
                <!-- Toolbar -->
                <div class="workflow-toolbar">
                    <div class="toolbar-left">
                        <h2><i class="ph-flow-arrow"></i> Workflow Designer</h2>
                        <span class="workflow-name" id="workflow-name-display">Untitled Workflow</span>
                    </div>
                    <div class="toolbar-right">
                        <button class="btn btn-sm btn-secondary" id="btn-save">
                            <i class="ph-floppy-disk"></i> Save
                        </button>
                        <button class="btn btn-sm btn-primary" id="btn-test">
                            <i class="ph-play"></i> Test
                        </button>
                        <button class="btn btn-sm btn-success" id="btn-publish">
                            <i class="ph-rocket-launch"></i> Publish
                        </button>
                    </div>
                </div>

                <!-- Main Content -->
                <div class="workflow-content">
                    <!-- Left Panel: Node Palette -->
                    <div class="node-palette">
                        <h4>Components</h4>
                        <div class="palette-section">
                            <h6>States</h6>
                            <div class="palette-item" draggable="true" data-type="start">
                                <i class="ph-play-circle"></i> Start
                            </div>
                            <div class="palette-item" draggable="true" data-type="task">
                                <i class="ph-note"></i> Task
                            </div>
                            <div class="palette-item" draggable="true" data-type="approval">
                                <i class="ph-check-circle"></i> Approval
                            </div>
                            <div class="palette-item" draggable="true" data-type="condition">
                                <i class="ph-git-branch"></i> Condition
                            </div>
                            <div class="palette-item" draggable="true" data-type="end">
                                <i class="ph-check-square"></i> End
                            </div>
                        </div>

                        <div class="palette-section mt-3">
                            <h6>Actions</h6>
                            <div class="palette-item" draggable="true" data-type="email">
                                <i class="ph-envelope"></i> Send Email
                            </div>
                            <div class="palette-item" draggable="true" data-type="notification">
                                <i class="ph-bell"></i> Notification
                            </div>
                            <div class="palette-item" draggable="true" data-type="update">
                                <i class="ph-pencil"></i> Update Field
                            </div>
                            <div class="palette-item" draggable="true" data-type="webhook">
                                <i class="ph-link"></i> Call Webhook
                            </div>
                        </div>
                    </div>

                    <!-- Center: Canvas -->
                    <div class="workflow-canvas" id="workflow-canvas">
                        <!-- React Flow or similar canvas library -->
                    </div>

                    <!-- Right Panel: Properties -->
                    <div class="properties-panel">
                        <h4>Properties</h4>
                        <div id="properties-content">
                            <div class="empty-state">
                                <i class="ph-cursor-click"></i>
                                <p>Select a node to edit properties</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    initializeCanvas() {
        // Initialize canvas library (ReactFlow, etc.)
        // Setup drag-and-drop for nodes
        // Setup edge connections
    }

    // Methods for state management, transition creation, etc.
    // ... (implementation details)
}
```

---

## Priority 3: Automation & Trigger System

### 3.1 Overview

**Purpose:** Enable event-based automation and trigger configuration without writing code, allowing users to create automated workflows based on database events, schedules, user actions, and external events.

**Key Capabilities:**
- Event trigger configuration (onCreate, onUpdate, onDelete)
- Scheduled triggers (cron-based)
- User action triggers
- External webhook triggers
- Visual condition builder (if-then-else logic)
- Action configuration (email, API calls, record updates, etc.)
- Multi-step automation chains
- Testing and debugging tools
- Execution history and monitoring

---

### 3.2 Database Schema

#### 3.2.1 Automation Rule Model

```sql
-- Table: automation_rules
CREATE TABLE automation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Basic Info
    name VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    -- Trigger Configuration
    trigger_type VARCHAR(50) NOT NULL,  -- 'database_event', 'scheduled', 'user_action', 'webhook', 'manual'
    trigger_config JSONB NOT NULL,  -- Trigger-specific configuration

    -- Entity Association (for database events)
    entity_id UUID REFERENCES entity_definitions(id),

    -- Database Event Triggers
    event_type VARCHAR(50),  -- 'create', 'update', 'delete', 'any'
    trigger_timing VARCHAR(20),  -- 'before', 'after'

    -- Schedule Configuration (for scheduled triggers)
    schedule_type VARCHAR(50),  -- 'cron', 'interval', 'one_time'
    cron_expression VARCHAR(100),  -- For cron schedules
    schedule_interval INTEGER,  -- Minutes for interval schedules
    schedule_timezone VARCHAR(50) DEFAULT 'UTC',
    next_run_at TIMESTAMP,
    last_run_at TIMESTAMP,

    -- Conditions (if-then-else logic)
    has_conditions BOOLEAN DEFAULT false,
    conditions JSONB DEFAULT '{}',  -- Condition tree structure

    -- Actions
    actions JSONB NOT NULL DEFAULT '[]',  -- Array of actions to execute

    -- Execution Settings
    execution_order INTEGER DEFAULT 0,  -- Order when multiple rules match
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    timeout_seconds INTEGER DEFAULT 300,

    -- Concurrency Control
    allow_concurrent BOOLEAN DEFAULT true,
    max_concurrent_instances INTEGER,

    -- Error Handling
    on_error_action VARCHAR(50) DEFAULT 'stop',  -- 'stop', 'continue', 'retry'
    error_notification_emails JSONB DEFAULT '[]',

    -- Status & Control
    is_active BOOLEAN DEFAULT true,
    is_async BOOLEAN DEFAULT true,  -- Execute asynchronously?

    -- Testing
    is_test_mode BOOLEAN DEFAULT false,  -- Don't execute actions in test mode

    -- Statistics
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    average_execution_time_ms INTEGER,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Version Control
    version INTEGER DEFAULT 1,
    is_published BOOLEAN DEFAULT false,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT false,

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_automation_rules_tenant ON automation_rules(tenant_id) WHERE is_deleted = false;
CREATE INDEX idx_automation_rules_entity ON automation_rules(entity_id) WHERE is_active = true;
CREATE INDEX idx_automation_rules_trigger_type ON automation_rules(trigger_type) WHERE is_active = true;
CREATE INDEX idx_automation_rules_next_run ON automation_rules(next_run_at) WHERE is_active = true AND schedule_type IS NOT NULL;
CREATE INDEX idx_automation_rules_event ON automation_rules(entity_id, event_type) WHERE is_active = true;
```

#### 3.2.2 Automation Execution Model

```sql
-- Table: automation_executions
CREATE TABLE automation_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES automation_rules(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Trigger Context
    trigger_type VARCHAR(50) NOT NULL,
    triggered_by_user_id UUID REFERENCES users(id),
    triggered_at TIMESTAMP DEFAULT NOW(),

    -- Entity Context (for database events)
    entity_id UUID REFERENCES entity_definitions(id),
    record_id UUID,  -- ID of the record that triggered the rule
    record_data_before JSONB,  -- Snapshot before change (for updates)
    record_data_after JSONB,  -- Snapshot after change

    -- Execution Status
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_ms INTEGER,

    -- Condition Evaluation
    conditions_met BOOLEAN,
    condition_evaluation_result JSONB,  -- Details of condition evaluation

    -- Actions Execution
    total_actions INTEGER DEFAULT 0,
    completed_actions INTEGER DEFAULT 0,
    failed_actions INTEGER DEFAULT 0,
    action_results JSONB DEFAULT '[]',  -- Results of each action

    -- Error Handling
    error_message TEXT,
    error_stack_trace TEXT,
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP,

    -- Context Data
    context_data JSONB DEFAULT '{}',  -- Additional context for the execution

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_automation_executions_rule ON automation_executions(rule_id);
CREATE INDEX idx_automation_executions_status ON automation_executions(status);
CREATE INDEX idx_automation_executions_record ON automation_executions(entity_id, record_id);
CREATE INDEX idx_automation_executions_triggered_at ON automation_executions(triggered_at);
CREATE INDEX idx_automation_executions_retry ON automation_executions(next_retry_at) WHERE status = 'failed';
```

#### 3.2.3 Action Template Model

```sql
-- Table: action_templates
CREATE TABLE action_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),  -- NULL for system templates

    -- Basic Info
    name VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    -- Action Type
    action_type VARCHAR(50) NOT NULL,  -- 'send_email', 'webhook', 'update_record', 'create_record', etc.

    -- Template Configuration
    config_schema JSONB NOT NULL,  -- JSON schema for action configuration
    default_config JSONB DEFAULT '{}',

    -- Display
    icon VARCHAR(50),
    color VARCHAR(50),

    -- System vs Custom
    is_system BOOLEAN DEFAULT false,  -- System templates can't be modified

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    is_deleted BOOLEAN DEFAULT false,

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_action_templates_tenant ON action_templates(tenant_id);
CREATE INDEX idx_action_templates_type ON action_templates(action_type) WHERE is_active = true;
```

#### 3.2.4 Webhook Configuration Model

```sql
-- Table: webhook_configs
CREATE TABLE webhook_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Basic Info
    name VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    description TEXT,

    -- Webhook Type
    webhook_type VARCHAR(50) NOT NULL,  -- 'inbound', 'outbound'

    -- Inbound Webhook Config
    endpoint_path VARCHAR(200),  -- Unique path: /webhooks/{endpoint_path}
    secret_token VARCHAR(255),  -- For validating incoming requests
    allowed_ips JSONB DEFAULT '[]',  -- IP whitelist

    -- Outbound Webhook Config
    target_url VARCHAR(500),  -- External URL to call
    http_method VARCHAR(10) DEFAULT 'POST',  -- GET, POST, PUT, DELETE
    headers JSONB DEFAULT '{}',  -- HTTP headers
    authentication_type VARCHAR(50),  -- 'none', 'basic', 'bearer', 'api_key', 'oauth2'
    authentication_config JSONB DEFAULT '{}',

    -- Payload Configuration
    payload_template TEXT,  -- Template for outbound payload
    payload_mapping JSONB DEFAULT '{}',  -- Field mapping

    -- Retry Configuration
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    timeout_seconds INTEGER DEFAULT 30,

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Statistics
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    last_called_at TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    is_deleted BOOLEAN DEFAULT false,

    UNIQUE(tenant_id, name),
    UNIQUE(endpoint_path) WHERE webhook_type = 'inbound'
);

CREATE INDEX idx_webhook_configs_tenant ON webhook_configs(tenant_id) WHERE is_deleted = false;
CREATE INDEX idx_webhook_configs_endpoint ON webhook_configs(endpoint_path) WHERE webhook_type = 'inbound';
```

---

### 3.3 Backend API

#### 3.3.1 Router: `/backend/app/routers/automations.py`

```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.rbac import has_permission
from app.schemas.automation import (
    AutomationRuleCreate,
    AutomationRuleUpdate,
    AutomationRuleResponse,
    AutomationExecutionResponse,
    ActionTemplateResponse,
    WebhookConfigCreate,
    WebhookConfigResponse,
    AutomationTestRequest,
    AutomationTestResponse
)
from app.services.automation_service import AutomationService

router = APIRouter(prefix="/api/v1/automations", tags=["Automations"])

# ==================== Automation Rule Endpoints ====================

@router.post("/rules", response_model=AutomationRuleResponse)
@has_permission("automations:create:tenant")
async def create_automation_rule(
    rule: AutomationRuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new automation rule"""
    service = AutomationService(db, current_user)
    return await service.create_rule(rule)


@router.get("/rules", response_model=List[AutomationRuleResponse])
@has_permission("automations:read:tenant")
async def list_automation_rules(
    entity_id: Optional[UUID] = None,
    trigger_type: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all automation rules"""
    service = AutomationService(db, current_user)
    return await service.list_rules(entity_id, trigger_type, category, is_active)


@router.get("/rules/{rule_id}", response_model=AutomationRuleResponse)
@has_permission("automations:read:tenant")
async def get_automation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get automation rule details"""
    service = AutomationService(db, current_user)
    return await service.get_rule(rule_id)


@router.put("/rules/{rule_id}", response_model=AutomationRuleResponse)
@has_permission("automations:update:tenant")
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
@has_permission("automations:delete:tenant")
async def delete_automation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete automation rule"""
    service = AutomationService(db, current_user)
    return await service.delete_rule(rule_id)


@router.post("/rules/{rule_id}/activate")
@has_permission("automations:execute:tenant")
async def activate_automation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Activate automation rule"""
    service = AutomationService(db, current_user)
    return await service.activate_rule(rule_id)


@router.post("/rules/{rule_id}/deactivate")
@has_permission("automations:execute:tenant")
async def deactivate_automation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Deactivate automation rule"""
    service = AutomationService(db, current_user)
    return await service.deactivate_rule(rule_id)


# ==================== Execution Endpoints ====================

@router.post("/rules/{rule_id}/execute")
@has_permission("automations:execute:tenant")
async def execute_automation_rule(
    rule_id: UUID,
    context_data: dict = {},
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Manually execute an automation rule"""
    service = AutomationService(db, current_user)
    return await service.execute_rule(rule_id, context_data, background_tasks)


@router.get("/executions", response_model=List[AutomationExecutionResponse])
@has_permission("automations:read:tenant")
async def list_executions(
    rule_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List automation execution history"""
    service = AutomationService(db, current_user)
    return await service.list_executions(rule_id, status, limit, offset)


@router.get("/executions/{execution_id}", response_model=AutomationExecutionResponse)
@has_permission("automations:read:tenant")
async def get_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get execution details"""
    service = AutomationService(db, current_user)
    return await service.get_execution(execution_id)


@router.post("/executions/{execution_id}/retry")
@has_permission("automations:execute:tenant")
async def retry_execution(
    execution_id: UUID,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Retry a failed execution"""
    service = AutomationService(db, current_user)
    return await service.retry_execution(execution_id, background_tasks)


# ==================== Testing Endpoints ====================

@router.post("/rules/{rule_id}/test", response_model=AutomationTestResponse)
@has_permission("automations:read:tenant")
async def test_automation_rule(
    rule_id: UUID,
    test_request: AutomationTestRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Test automation rule with sample data (dry run)"""
    service = AutomationService(db, current_user)
    return await service.test_rule(rule_id, test_request)


# ==================== Action Template Endpoints ====================

@router.get("/action-templates", response_model=List[ActionTemplateResponse])
@has_permission("automations:read:tenant")
async def list_action_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List available action templates"""
    service = AutomationService(db, current_user)
    return await service.list_action_templates(category)


@router.get("/action-templates/{template_id}", response_model=ActionTemplateResponse)
@has_permission("automations:read:tenant")
async def get_action_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get action template details"""
    service = AutomationService(db, current_user)
    return await service.get_action_template(template_id)


# ==================== Webhook Endpoints ====================

@router.post("/webhooks", response_model=WebhookConfigResponse)
@has_permission("automations:create:tenant")
async def create_webhook(
    webhook: WebhookConfigCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create webhook configuration"""
    service = AutomationService(db, current_user)
    return await service.create_webhook(webhook)


@router.get("/webhooks", response_model=List[WebhookConfigResponse])
@has_permission("automations:read:tenant")
async def list_webhooks(
    webhook_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List webhook configurations"""
    service = AutomationService(db, current_user)
    return await service.list_webhooks(webhook_type)


@router.get("/webhooks/{webhook_id}", response_model=WebhookConfigResponse)
@has_permission("automations:read:tenant")
async def get_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get webhook configuration"""
    service = AutomationService(db, current_user)
    return await service.get_webhook(webhook_id)


@router.post("/webhooks/{webhook_id}/test")
@has_permission("automations:execute:tenant")
async def test_webhook(
    webhook_id: UUID,
    test_payload: dict = {},
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Test webhook configuration"""
    service = AutomationService(db, current_user)
    return await service.test_webhook(webhook_id, test_payload)


# ==================== Statistics Endpoints ====================

@router.get("/stats/summary")
@has_permission("automations:read:tenant")
async def get_automation_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get automation statistics summary"""
    service = AutomationService(db, current_user)
    return await service.get_stats_summary()


@router.get("/stats/rules/{rule_id}")
@has_permission("automations:read:tenant")
async def get_rule_stats(
    rule_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get statistics for specific rule"""
    service = AutomationService(db, current_user)
    return await service.get_rule_stats(rule_id, days)
```

---

### 3.4 Frontend Components

#### 3.4.1 Main Component: `/frontend/components/automation-designer.js`

```javascript
/**
 * Automation Designer
 * Visual automation rule builder with condition and action configuration
 */

class AutomationDesigner {
    constructor() {
        this.currentRule = null;
        this.actionTemplates = [];
        this.availableEntities = [];

        this.service = new AutomationService();
        this.init();
    }

    init() {
        this.renderLayout();
        this.loadActionTemplates();
        this.loadEntities();
        this.attachEventListeners();
    }

    renderLayout() {
        const container = document.getElementById('app-container');
        container.innerHTML = `
            <div class="automation-designer">
                <!-- Header -->
                <div class="designer-header">
                    <div class="header-left">
                        <h1><i class="ph-lightning"></i> Automation Designer</h1>
                        <p class="subtitle">Create event-driven automation rules</p>
                    </div>
                    <div class="header-right">
                        <button class="btn btn-secondary" id="btn-view-executions">
                            <i class="ph-clock-counter-clockwise"></i> History
                        </button>
                        <button class="btn btn-primary" id="btn-new-automation">
                            <i class="ph-plus"></i> New Automation
                        </button>
                    </div>
                </div>

                <!-- Main Content -->
                <div class="designer-content">
                    <!-- Sidebar: Automation List -->
                    <div class="automation-sidebar">
                        <div class="sidebar-header">
                            <h3>Automation Rules</h3>
                            <div class="filter-group">
                                <select class="form-select form-select-sm" id="filter-trigger-type">
                                    <option value="">All Triggers</option>
                                    <option value="database_event">Database Events</option>
                                    <option value="scheduled">Scheduled</option>
                                    <option value="webhook">Webhooks</option>
                                    <option value="user_action">User Actions</option>
                                </select>
                                <select class="form-select form-select-sm mt-2" id="filter-status">
                                    <option value="">All Status</option>
                                    <option value="active">Active</option>
                                    <option value="inactive">Inactive</option>
                                </select>
                            </div>
                        </div>
                        <div class="automation-list" id="automation-list">
                            <!-- List items -->
                        </div>
                    </div>

                    <!-- Main Panel: Rule Designer -->
                    <div class="automation-designer-panel" id="designer-panel">
                        <!-- Empty state or rule details -->
                        <div class="empty-state">
                            <i class="ph-lightning" style="font-size: 64px; opacity: 0.3;"></i>
                            <h3>No Automation Selected</h3>
                            <p>Select an automation from the list or create a new one</p>
                            <button class="btn btn-primary" id="btn-create-first">
                                <i class="ph-plus"></i> Create First Automation
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Automation Designer Modal -->
            <div class="modal fade" id="automation-modal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Automation Rule Designer</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Multi-step wizard -->
                            <div class="wizard-steps">
                                <div class="step active" data-step="1">
                                    <span class="step-number">1</span>
                                    <span class="step-label">Trigger</span>
                                </div>
                                <div class="step" data-step="2">
                                    <span class="step-number">2</span>
                                    <span class="step-label">Conditions</span>
                                </div>
                                <div class="step" data-step="3">
                                    <span class="step-number">3</span>
                                    <span class="step-label">Actions</span>
                                </div>
                                <div class="step" data-step="4">
                                    <span class="step-number">4</span>
                                    <span class="step-label">Settings</span>
                                </div>
                                <div class="step" data-step="5">
                                    <span class="step-number">5</span>
                                    <span class="step-label">Test & Publish</span>
                                </div>
                            </div>

                            <div class="wizard-content" id="wizard-content">
                                <!-- Step content -->
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" id="btn-prev-step">
                                <i class="ph-caret-left"></i> Previous
                            </button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="btn-next-step">
                                Next <i class="ph-caret-right"></i>
                            </button>
                            <button type="button" class="btn btn-warning" id="btn-test-automation" style="display:none;">
                                <i class="ph-play"></i> Test
                            </button>
                            <button type="button" class="btn btn-success" id="btn-save-automation" style="display:none;">
                                <i class="ph-check"></i> Save & Activate
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Condition Builder Modal -->
            <div class="modal fade" id="condition-modal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Condition Builder</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="condition-builder">
                            <!-- Visual condition builder -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="btn-save-condition">
                                <i class="ph-check"></i> Save Condition
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Action Designer Modal -->
            <div class="modal fade" id="action-modal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Action Designer</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="action-designer">
                            <!-- Action configuration -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="btn-save-action">
                                <i class="ph-check"></i> Save Action
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // ==================== Step Rendering ====================

    renderStep1_Trigger() {
        return `
            <div class="step-content">
                <h4>Configure Trigger</h4>
                <p class="text-muted">When should this automation run?</p>

                <div class="row g-3 mt-3">
                    <div class="col-12">
                        <label class="form-label required">Rule Name</label>
                        <input type="text" class="form-control" id="rule-name"
                               placeholder="e.g., Send welcome email on new customer">
                    </div>

                    <div class="col-12">
                        <label class="form-label">Description</label>
                        <textarea class="form-control" id="rule-description" rows="2"
                                  placeholder="Describe what this automation does..."></textarea>
                    </div>

                    <div class="col-md-6">
                        <label class="form-label">Category</label>
                        <select class="form-select" id="rule-category">
                            <option value="">Select category...</option>
                            <option value="notifications">Notifications</option>
                            <option value="data_sync">Data Synchronization</option>
                            <option value="workflows">Workflows</option>
                            <option value="integrations">Integrations</option>
                            <option value="maintenance">Maintenance</option>
                        </select>
                    </div>

                    <div class="col-12 mt-4">
                        <label class="form-label required">Trigger Type</label>
                        <div class="trigger-types">
                            <div class="trigger-card" data-type="database_event">
                                <i class="ph-database"></i>
                                <h6>Database Event</h6>
                                <p>When a record is created, updated, or deleted</p>
                            </div>
                            <div class="trigger-card" data-type="scheduled">
                                <i class="ph-clock"></i>
                                <h6>Scheduled</h6>
                                <p>Run on a schedule (cron or interval)</p>
                            </div>
                            <div class="trigger-card" data-type="webhook">
                                <i class="ph-globe"></i>
                                <h6>Webhook</h6>
                                <p>Triggered by external system via webhook</p>
                            </div>
                            <div class="trigger-card" data-type="user_action">
                                <i class="ph-user"></i>
                                <h6>User Action</h6>
                                <p>When user performs a specific action</p>
                            </div>
                            <div class="trigger-card" data-type="manual">
                                <i class="ph-hand-pointing"></i>
                                <h6>Manual</h6>
                                <p>Triggered manually by user or API</p>
                            </div>
                        </div>
                    </div>

                    <!-- Database Event Configuration -->
                    <div class="col-12 trigger-config" id="config-database-event" style="display:none;">
                        <div class="card">
                            <div class="card-body">
                                <h6>Database Event Configuration</h6>

                                <div class="row g-3 mt-2">
                                    <div class="col-md-6">
                                        <label class="form-label required">Entity</label>
                                        <select class="form-select" id="trigger-entity">
                                            <option value="">Select entity...</option>
                                            <!-- Populated dynamically -->
                                        </select>
                                    </div>

                                    <div class="col-md-6">
                                        <label class="form-label required">Event Type</label>
                                        <select class="form-select" id="trigger-event-type">
                                            <option value="create">Create (Insert)</option>
                                            <option value="update">Update</option>
                                            <option value="delete">Delete</option>
                                            <option value="any">Any Change</option>
                                        </select>
                                    </div>

                                    <div class="col-md-6">
                                        <label class="form-label required">Timing</label>
                                        <select class="form-select" id="trigger-timing">
                                            <option value="after">After Event</option>
                                            <option value="before">Before Event</option>
                                        </select>
                                        <small class="form-text text-muted">
                                            Before: Can prevent the operation. After: Can't prevent but safer.
                                        </small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Scheduled Configuration -->
                    <div class="col-12 trigger-config" id="config-scheduled" style="display:none;">
                        <div class="card">
                            <div class="card-body">
                                <h6>Schedule Configuration</h6>

                                <div class="row g-3 mt-2">
                                    <div class="col-md-6">
                                        <label class="form-label required">Schedule Type</label>
                                        <select class="form-select" id="schedule-type">
                                            <option value="interval">Interval (Every X minutes)</option>
                                            <option value="cron">Cron Expression</option>
                                            <option value="one_time">One Time</option>
                                        </select>
                                    </div>

                                    <div class="col-md-6 schedule-option" id="option-interval">
                                        <label class="form-label">Interval (minutes)</label>
                                        <input type="number" class="form-control" id="schedule-interval"
                                               min="1" placeholder="e.g., 60 for hourly">
                                    </div>

                                    <div class="col-md-6 schedule-option" id="option-cron" style="display:none;">
                                        <label class="form-label">Cron Expression</label>
                                        <input type="text" class="form-control" id="schedule-cron"
                                               placeholder="e.g., 0 9 * * * (daily at 9 AM)">
                                        <small class="form-text text-muted">
                                            <a href="#" id="cron-helper">Cron expression helper</a>
                                        </small>
                                    </div>

                                    <div class="col-md-6">
                                        <label class="form-label">Timezone</label>
                                        <select class="form-select" id="schedule-timezone">
                                            <option value="UTC">UTC</option>
                                            <option value="America/New_York">Eastern Time</option>
                                            <option value="America/Chicago">Central Time</option>
                                            <option value="America/Denver">Mountain Time</option>
                                            <option value="America/Los_Angeles">Pacific Time</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Webhook Configuration -->
                    <div class="col-12 trigger-config" id="config-webhook" style="display:none;">
                        <div class="card">
                            <div class="card-body">
                                <h6>Webhook Configuration</h6>

                                <div class="row g-3 mt-2">
                                    <div class="col-12">
                                        <label class="form-label">Webhook URL</label>
                                        <div class="input-group">
                                            <span class="input-group-text">POST</span>
                                            <input type="text" class="form-control" id="webhook-url" readonly
                                                   value="https://app.buildify.com/webhooks/[auto-generated]">
                                            <button class="btn btn-outline-secondary" id="btn-copy-webhook">
                                                <i class="ph-copy"></i>
                                            </button>
                                        </div>
                                        <small class="form-text text-muted">
                                            External systems will call this URL to trigger the automation
                                        </small>
                                    </div>

                                    <div class="col-12">
                                        <label class="form-label">Secret Token</label>
                                        <div class="input-group">
                                            <input type="password" class="form-control" id="webhook-secret" readonly>
                                            <button class="btn btn-outline-secondary" id="btn-regenerate-secret">
                                                <i class="ph-arrows-clockwise"></i> Regenerate
                                            </button>
                                        </div>
                                        <small class="form-text text-muted">
                                            Include this in X-Webhook-Secret header for authentication
                                        </small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderStep2_Conditions() {
        return `
            <div class="step-content">
                <h4>Add Conditions (Optional)</h4>
                <p class="text-muted">Define when the actions should execute</p>

                <div class="mt-3">
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="enable-conditions">
                        <label class="form-check-label" for="enable-conditions">
                            Enable conditions (if unchecked, actions always execute)
                        </label>
                    </div>
                </div>

                <div id="conditions-panel" style="display:none;">
                    <div class="card mt-3">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">Condition Logic</h6>
                            <button class="btn btn-sm btn-primary" id="btn-add-condition-group">
                                <i class="ph-plus"></i> Add Condition
                            </button>
                        </div>
                        <div class="card-body">
                            <div id="condition-builder-visual">
                                <!-- Visual condition builder -->
                                <div class="condition-group">
                                    <div class="condition-operator">
                                        <select class="form-select form-select-sm">
                                            <option value="AND">Match ALL conditions (AND)</option>
                                            <option value="OR">Match ANY condition (OR)</option>
                                        </select>
                                    </div>
                                    <div class="condition-list" id="condition-list">
                                        <div class="empty-state-sm">
                                            <p class="text-muted mb-2">No conditions defined</p>
                                            <button class="btn btn-sm btn-outline-primary" id="btn-add-first-condition">
                                                Add First Condition
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Example condition items (hidden by default) -->
                            <template id="condition-item-template">
                                <div class="condition-item">
                                    <div class="row g-2 align-items-center">
                                        <div class="col-md-3">
                                            <select class="form-select form-select-sm condition-field">
                                                <option value="">Select field...</option>
                                                <!-- Populated based on entity -->
                                            </select>
                                        </div>
                                        <div class="col-md-3">
                                            <select class="form-select form-select-sm condition-operator">
                                                <option value="equals">Equals</option>
                                                <option value="not_equals">Not Equals</option>
                                                <option value="greater_than">Greater Than</option>
                                                <option value="less_than">Less Than</option>
                                                <option value="contains">Contains</option>
                                                <option value="starts_with">Starts With</option>
                                                <option value="ends_with">Ends With</option>
                                                <option value="is_empty">Is Empty</option>
                                                <option value="is_not_empty">Is Not Empty</option>
                                                <option value="in">In List</option>
                                            </select>
                                        </div>
                                        <div class="col-md-5">
                                            <input type="text" class="form-control form-control-sm condition-value"
                                                   placeholder="Value">
                                        </div>
                                        <div class="col-md-1">
                                            <button class="btn btn-sm btn-danger btn-remove-condition">
                                                <i class="ph-trash"></i>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>

                    <!-- Advanced: Field Change Detection (for update events) -->
                    <div class="card mt-3" id="field-change-detection" style="display:none;">
                        <div class="card-header">
                            <h6 class="mb-0">Field Change Detection</h6>
                        </div>
                        <div class="card-body">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="check-field-changes">
                                <label class="form-check-label" for="check-field-changes">
                                    Only trigger when specific fields change
                                </label>
                            </div>
                            <div id="changed-fields-selector" class="mt-3" style="display:none;">
                                <label class="form-label">Fields to Monitor</label>
                                <div id="field-checkboxes">
                                    <!-- Populated dynamically -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderStep3_Actions() {
        return `
            <div class="step-content">
                <h4>Configure Actions</h4>
                <p class="text-muted">What should happen when conditions are met?</p>

                <div class="d-flex justify-content-between align-items-center mt-3 mb-3">
                    <div>
                        <span class="badge bg-info" id="action-count">0 actions configured</span>
                    </div>
                    <button class="btn btn-sm btn-primary" id="btn-add-action">
                        <i class="ph-plus"></i> Add Action
                    </button>
                </div>

                <div class="action-list" id="action-list">
                    <div class="empty-state text-center py-4">
                        <i class="ph-lightning" style="font-size: 48px; opacity: 0.3;"></i>
                        <p class="text-muted">No actions configured yet</p>
                        <button class="btn btn-outline-primary" id="btn-add-first-action">
                            Add First Action
                        </button>
                    </div>
                </div>

                <!-- Action Templates Panel (shown when adding action) -->
                <div class="action-templates-panel" id="action-templates" style="display:none;">
                    <h6>Select Action Type</h6>
                    <div class="row g-3 mt-2">
                        <div class="col-md-4">
                            <div class="action-template-card" data-type="send_email">
                                <i class="ph-envelope"></i>
                                <h6>Send Email</h6>
                                <p>Send email notification</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="action-template-card" data-type="send_notification">
                                <i class="ph-bell"></i>
                                <h6>Send Notification</h6>
                                <p>In-app notification</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="action-template-card" data-type="update_record">
                                <i class="ph-pencil-simple"></i>
                                <h6>Update Record</h6>
                                <p>Update field values</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="action-template-card" data-type="create_record">
                                <i class="ph-plus-circle"></i>
                                <h6>Create Record</h6>
                                <p>Create new record</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="action-template-card" data-type="webhook">
                                <i class="ph-globe"></i>
                                <h6>Call Webhook</h6>
                                <p>HTTP API call</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="action-template-card" data-type="start_workflow">
                                <i class="ph-flow-arrow"></i>
                                <h6>Start Workflow</h6>
                                <p>Initiate workflow</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="action-template-card" data-type="run_script">
                                <i class="ph-code"></i>
                                <h6>Run Script</h6>
                                <p>Execute custom code</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="action-template-card" data-type="send_sms">
                                <i class="ph-chat-dots"></i>
                                <h6>Send SMS</h6>
                                <p>Text message notification</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="action-template-card" data-type="delay">
                                <i class="ph-clock"></i>
                                <h6>Delay</h6>
                                <p>Wait before next action</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Additional methods for condition builder, action designer, etc.
    // ... (implementation details)
}

// Initialize
let automationDesignerInstance;
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.hash.startsWith('#automations')) {
        automationDesignerInstance = new AutomationDesigner();
    }
});
```

---

### 3.5 Key Features

#### 3.5.1 Condition Builder

**Visual Condition Builder:**
- Drag-and-drop interface
- Support for complex boolean logic (AND/OR groups)
- Field value comparisons
- Date/time conditions
- User/role conditions
- Custom expressions

**Condition Types:**
- Field value conditions (equals, contains, greater than, etc.)
- Field change detection (for update events)
- Date/time conditions (before, after, between)
- User conditions (current user, role, department)
- Related record conditions (lookup fields)

#### 3.5.2 Action Types

**Built-in Actions:**

1. **Send Email**
   - Template selection
   - Dynamic recipient list
   - Merge fields from record data
   - Attachments support

2. **Send Notification**
   - In-app notifications
   - Push notifications
   - User/role targeting

3. **Update Record**
   - Update current record
   - Update related records
   - Bulk update

4. **Create Record**
   - Create in same or different entity
   - Copy field values
   - Set default values

5. **Call Webhook**
   - HTTP methods (GET, POST, PUT, DELETE)
   - Custom headers
   - Request body templates
   - Authentication

6. **Start Workflow**
   - Initiate workflow instance
   - Pass context data

7. **Run Script**
   - Python/JavaScript execution
   - Sandbox environment
   - Access to record data

---

### 3.6 Integration with Other Systems

#### 3.6.1 Integration with Data Model Designer

When entities are created:
- Automatically available for automation triggers
- Fields available in condition builder
- Actions can create/update records

#### 3.6.2 Integration with Workflow Designer

- Automations can start workflow instances
- Workflow state changes can trigger automations
- Shared action library

#### 3.6.3 Integration with Email Template Designer

- Email actions use email templates
- Merge fields from record data
- Template variables

---

## Priority 4: Lookup/Reference Configuration

### 4.1 Overview

**Purpose:** Provide comprehensive configuration for dropdown fields, reference fields, and data relationships, enabling users to define how lookup data is sourced, filtered, and displayed.

**Key Capabilities:**
- Lookup data source configuration
- Cascading dropdown rules
- Dynamic filtering based on context
- Custom lookup queries
- Search and autocomplete settings
- Lookup caching strategies

---

### 4.2 Database Schema

#### 4.2.1 Lookup Configuration Model

```sql
-- Table: lookup_configurations
CREATE TABLE lookup_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Basic Info
    name VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    description TEXT,

    -- Source Configuration
    source_type VARCHAR(50) NOT NULL,  -- 'entity', 'custom_query', 'static_list', 'api'

    -- Entity Source
    source_entity_id UUID REFERENCES entity_definitions(id),
    display_field VARCHAR(100),  -- Field to show in dropdown
    value_field VARCHAR(100) DEFAULT 'id',  -- Field to use as value
    additional_display_fields JSONB DEFAULT '[]',  -- Additional fields to show

    -- Query Configuration
    custom_query TEXT,  -- Custom SQL query for advanced scenarios
    query_parameters JSONB DEFAULT '{}',

    -- Static List Source
    static_options JSONB DEFAULT '[]',  -- [{value, label, metadata}]

    -- API Source
    api_endpoint VARCHAR(500),
    api_method VARCHAR(10) DEFAULT 'GET',
    api_headers JSONB DEFAULT '{}',
    api_response_mapping JSONB DEFAULT '{}',  -- How to map API response

    -- Filtering
    default_filter JSONB DEFAULT '{}',  -- Default WHERE conditions
    allow_user_filter BOOLEAN DEFAULT true,
    filter_fields JSONB DEFAULT '[]',  -- Fields available for filtering

    -- Sorting
    default_sort_field VARCHAR(100),
    default_sort_order VARCHAR(10) DEFAULT 'ASC',
    allow_user_sort BOOLEAN DEFAULT true,

    -- Display Configuration
    display_template VARCHAR(500),  -- Template for displaying items
    placeholder_text VARCHAR(200),
    empty_message VARCHAR(200) DEFAULT 'No options available',

    -- Search Configuration
    enable_search BOOLEAN DEFAULT true,
    search_fields JSONB DEFAULT '[]',  -- Fields to search in
    min_search_length INTEGER DEFAULT 3,
    search_debounce_ms INTEGER DEFAULT 300,

    -- Autocomplete Configuration
    enable_autocomplete BOOLEAN DEFAULT false,
    autocomplete_min_chars INTEGER DEFAULT 2,
    autocomplete_max_results INTEGER DEFAULT 10,

    -- Performance
    enable_caching BOOLEAN DEFAULT true,
    cache_ttl_seconds INTEGER DEFAULT 3600,
    lazy_load BOOLEAN DEFAULT false,  -- Load on demand vs preload
    page_size INTEGER DEFAULT 50,

    -- Dependency Configuration
    is_dependent BOOLEAN DEFAULT false,
    parent_lookup_id UUID REFERENCES lookup_configurations(id),
    dependency_mapping JSONB DEFAULT '{}',  -- How parent value affects this lookup

    -- Advanced Features
    allow_create_new BOOLEAN DEFAULT false,  -- Allow creating new options inline
    create_entity_id UUID REFERENCES entity_definitions(id),  -- Entity to create in

    allow_multiple BOOLEAN DEFAULT false,  -- Multi-select
    max_selections INTEGER,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    is_deleted BOOLEAN DEFAULT false,

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_lookup_configurations_tenant ON lookup_configurations(tenant_id) WHERE is_deleted = false;
CREATE INDEX idx_lookup_configurations_source_entity ON lookup_configurations(source_entity_id);
CREATE INDEX idx_lookup_configurations_parent ON lookup_configurations(parent_lookup_id) WHERE is_dependent = true;
```

#### 4.2.2 Lookup Cache Model

```sql
-- Table: lookup_cache
CREATE TABLE lookup_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lookup_id UUID NOT NULL REFERENCES lookup_configurations(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Cache Key
    cache_key VARCHAR(255) NOT NULL,  -- Hash of query parameters

    -- Cached Data
    cached_data JSONB NOT NULL,  -- The actual lookup data
    record_count INTEGER,

    -- Cache Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(lookup_id, cache_key)
);

CREATE INDEX idx_lookup_cache_lookup ON lookup_cache(lookup_id);
CREATE INDEX idx_lookup_cache_expires ON lookup_cache(expires_at);
CREATE INDEX idx_lookup_cache_key ON lookup_cache(cache_key);
```

#### 4.2.3 Cascading Lookup Rule Model

```sql
-- Table: cascading_lookup_rules
CREATE TABLE cascading_lookup_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Basic Info
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Parent-Child Relationship
    parent_lookup_id UUID NOT NULL REFERENCES lookup_configurations(id),
    child_lookup_id UUID NOT NULL REFERENCES lookup_configurations(id),

    -- Filtering Rule
    filter_type VARCHAR(50) DEFAULT 'field_match',  -- 'field_match', 'custom_query', 'function'
    parent_field VARCHAR(100),  -- Field in parent that drives filtering
    child_filter_field VARCHAR(100),  -- Field in child to filter on

    -- Custom Filter
    custom_filter_expression TEXT,  -- Advanced filtering logic

    -- Behavior
    clear_on_parent_change BOOLEAN DEFAULT true,
    auto_select_if_single BOOLEAN DEFAULT false,  -- Auto-select if only one option

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    UNIQUE(parent_lookup_id, child_lookup_id)
);

CREATE INDEX idx_cascading_lookup_rules_parent ON cascading_lookup_rules(parent_lookup_id);
CREATE INDEX idx_cascading_lookup_rules_child ON cascading_lookup_rules(child_lookup_id);
```

---

### 4.3 Backend API

#### 4.3.1 Router: `/backend/app/routers/lookups.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.rbac import has_permission
from app.schemas.lookup import (
    LookupConfigurationCreate,
    LookupConfigurationUpdate,
    LookupConfigurationResponse,
    LookupDataResponse,
    CascadingLookupRuleCreate,
    CascadingLookupRuleResponse
)
from app.services.lookup_service import LookupService

router = APIRouter(prefix="/api/v1/lookups", tags=["Lookups"])

# ==================== Lookup Configuration Endpoints ====================

@router.post("/configurations", response_model=LookupConfigurationResponse)
@has_permission("lookups:create:tenant")
async def create_lookup_configuration(
    config: LookupConfigurationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new lookup configuration"""
    service = LookupService(db, current_user)
    return await service.create_configuration(config)


@router.get("/configurations", response_model=List[LookupConfigurationResponse])
@has_permission("lookups:read:tenant")
async def list_lookup_configurations(
    source_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all lookup configurations"""
    service = LookupService(db, current_user)
    return await service.list_configurations(source_type, entity_id)


@router.get("/configurations/{config_id}", response_model=LookupConfigurationResponse)
@has_permission("lookups:read:tenant")
async def get_lookup_configuration(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get lookup configuration"""
    service = LookupService(db, current_user)
    return await service.get_configuration(config_id)


@router.put("/configurations/{config_id}", response_model=LookupConfigurationResponse)
@has_permission("lookups:update:tenant")
async def update_lookup_configuration(
    config_id: UUID,
    config: LookupConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update lookup configuration"""
    service = LookupService(db, current_user)
    return await service.update_configuration(config_id, config)


@router.delete("/configurations/{config_id}")
@has_permission("lookups:delete:tenant")
async def delete_lookup_configuration(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete lookup configuration"""
    service = LookupService(db, current_user)
    return await service.delete_configuration(config_id)


# ==================== Lookup Data Endpoints ====================

@router.get("/configurations/{config_id}/data", response_model=LookupDataResponse)
@has_permission("lookups:read:tenant")
async def get_lookup_data(
    config_id: UUID,
    search: Optional[str] = Query(None),
    filters: Optional[str] = Query(None),  # JSON string
    parent_value: Optional[str] = Query(None),  # For cascading lookups
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get lookup data (dropdown options)"""
    service = LookupService(db, current_user)
    return await service.get_lookup_data(
        config_id,
        search=search,
        filters=filters,
        parent_value=parent_value,
        page=page,
        page_size=page_size
    )


@router.get("/configurations/{config_id}/search", response_model=LookupDataResponse)
@has_permission("lookups:read:tenant")
async def search_lookup(
    config_id: UUID,
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Search lookup data (autocomplete)"""
    service = LookupService(db, current_user)
    return await service.search_lookup(config_id, q, limit)


@router.post("/configurations/{config_id}/refresh-cache")
@has_permission("lookups:execute:tenant")
async def refresh_lookup_cache(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Manually refresh lookup cache"""
    service = LookupService(db, current_user)
    return await service.refresh_cache(config_id)


# ==================== Cascading Lookup Endpoints ====================

@router.post("/cascading-rules", response_model=CascadingLookupRuleResponse)
@has_permission("lookups:create:tenant")
async def create_cascading_rule(
    rule: CascadingLookupRuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create cascading lookup rule"""
    service = LookupService(db, current_user)
    return await service.create_cascading_rule(rule)


@router.get("/cascading-rules", response_model=List[CascadingLookupRuleResponse])
@has_permission("lookups:read:tenant")
async def list_cascading_rules(
    parent_lookup_id: Optional[UUID] = None,
    child_lookup_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List cascading lookup rules"""
    service = LookupService(db, current_user)
    return await service.list_cascading_rules(parent_lookup_id, child_lookup_id)


@router.delete("/cascading-rules/{rule_id}")
@has_permission("lookups:delete:tenant")
async def delete_cascading_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete cascading lookup rule"""
    service = LookupService(db, current_user)
    return await service.delete_cascading_rule(rule_id)


# ==================== Utility Endpoints ====================

@router.get("/entities/{entity_id}/fields")
@has_permission("lookups:read:tenant")
async def get_entity_fields_for_lookup(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get fields from entity (for lookup configuration)"""
    service = LookupService(db, current_user)
    return await service.get_entity_fields(entity_id)


@router.post("/test-query")
@has_permission("lookups:read:tenant")
async def test_lookup_query(
    query: str,
    parameters: dict = {},
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Test custom lookup query"""
    service = LookupService(db, current_user)
    return await service.test_query(query, parameters)
```

---

### 4.4 Frontend Components

#### 4.4.1 Main Component: `/frontend/components/lookup-designer.js`

```javascript
/**
 * Lookup Designer
 * Configure dropdown and reference field data sources
 */

class LookupDesigner {
    constructor() {
        this.currentLookup = null;
        this.availableEntities = [];
        this.service = new LookupService();
        this.init();
    }

    init() {
        this.renderLayout();
        this.loadEntities();
        this.attachEventListeners();
    }

    renderLayout() {
        const container = document.getElementById('app-container');
        container.innerHTML = `
            <div class="lookup-designer">
                <!-- Header -->
                <div class="designer-header">
                    <div class="header-left">
                        <h1><i class="ph-list"></i> Lookup Designer</h1>
                        <p class="subtitle">Configure dropdown and reference fields</p>
                    </div>
                    <div class="header-right">
                        <button class="btn btn-secondary" id="btn-refresh">
                            <i class="ph-arrows-clockwise"></i> Refresh
                        </button>
                        <button class="btn btn-primary" id="btn-new-lookup">
                            <i class="ph-plus"></i> New Lookup
                        </button>
                    </div>
                </div>

                <!-- Main Content -->
                <div class="designer-content">
                    <!-- Sidebar: Lookup List -->
                    <div class="lookup-sidebar">
                        <div class="sidebar-header">
                            <h3>Lookup Configurations</h3>
                            <select class="form-select form-select-sm mt-2" id="filter-source-type">
                                <option value="">All Sources</option>
                                <option value="entity">Entity</option>
                                <option value="custom_query">Custom Query</option>
                                <option value="static_list">Static List</option>
                                <option value="api">API</option>
                            </select>
                        </div>
                        <div class="lookup-list" id="lookup-list">
                            <!-- List items -->
                        </div>
                    </div>

                    <!-- Main Panel: Lookup Designer -->
                    <div class="lookup-designer-panel" id="designer-panel">
                        <!-- Empty state or lookup details -->
                    </div>
                </div>
            </div>

            <!-- Lookup Designer Modal -->
            <div class="modal fade" id="lookup-modal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Lookup Configuration</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Configuration form -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="btn-save-lookup">
                                <i class="ph-check"></i> Save Configuration
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Additional methods for lookup configuration
    // ... (implementation details)
}
```

---

### 4.5 Use Cases

#### Use Case 1: Simple Entity Lookup

**Scenario:** Country dropdown for address form

**Configuration:**
- Source Type: Entity
- Source Entity: countries
- Display Field: name
- Value Field: id
- Sort: name ASC
- Enable Search: Yes

#### Use Case 2: Cascading Lookups

**Scenario:** Country → State → City dropdowns

**Configuration:**
1. **Country Lookup:**
   - Source Entity: countries
   - Display Field: name

2. **State Lookup:**
   - Source Entity: states
   - Display Field: name
   - Is Dependent: Yes
   - Parent Lookup: Country
   - Filter: states.country_id = [selected country]

3. **City Lookup:**
   - Source Entity: cities
   - Display Field: name
   - Is Dependent: Yes
   - Parent Lookup: State
   - Filter: cities.state_id = [selected state]

#### Use Case 3: Custom Query Lookup

**Scenario:** Active users from specific department

**Configuration:**
- Source Type: Custom Query
- Custom Query:
  ```sql
  SELECT id, CONCAT(first_name, ' ', last_name) as display_name
  FROM users
  WHERE is_active = true
    AND department_id = :department_id
  ORDER BY first_name, last_name
  ```
- Query Parameters: {department_id: context.department_id}

#### Use Case 4: API-Based Lookup

**Scenario:** External product catalog

**Configuration:**
- Source Type: API
- API Endpoint: https://api.example.com/products
- API Method: GET
- Response Mapping:
  - value: $.data[*].id
  - label: $.data[*].name
  - metadata: $.data[*]
- Enable Caching: Yes
- Cache TTL: 3600 seconds

---

## Integration Points

### 3.1 Data Model ↔ Entity Metadata System

The Data Model Designer integrates with the existing Entity Metadata System:

**Integration Flow:**
1. When entity is published, create/update `EntityMetadata` record
2. Sync field definitions to metadata for dynamic form/table generation
3. Update RBAC permissions for new entity

**Code Example:**
```python
async def sync_to_metadata(self, entity_id: UUID):
    """Sync entity definition to metadata system"""
    entity = self._get_entity(entity_id)
    fields = self.db.query(FieldDefinition).filter(
        FieldDefinition.entity_id == entity_id
    ).all()

    # Create/update EntityMetadata
    metadata = {
        "entity": entity.name,
        "label": entity.label,
        "fields": [self._field_to_metadata(f) for f in fields],
        "permissions": self._generate_permissions(entity)
    }

    # Sync to metadata system
    metadata_service = EntityMetadataService(self.db)
    await metadata_service.upsert_metadata(entity.name, metadata)
```

### 3.2 Workflow ↔ Automation System (Phase 1, Priority 3)

Workflows can trigger automations and vice versa:

**Integration Points:**
- Workflow state changes trigger automation rules
- Automation actions can initiate workflows
- Shared action library (send email, update record, etc.)

### 3.3 Workflow ↔ RBAC System

Workflows respect RBAC permissions:

**Integration:**
- Transitions check user roles/permissions
- State-based field visibility
- Approval routing based on roles

---

## Security & RBAC

### 4.1 Permissions

New permissions required:

```python
# Data Model permissions
"data_model:create:tenant"    # Create entities
"data_model:read:tenant"      # View entities
"data_model:update:tenant"    # Edit entities
"data_model:delete:tenant"    # Delete entities
"data_model:execute:tenant"   # Publish/migrate entities

# Workflow permissions
"workflows:create:tenant"     # Create workflows
"workflows:read:tenant"       # View workflows
"workflows:update:tenant"     # Edit workflows
"workflows:delete:tenant"     # Delete workflows
"workflows:execute:tenant"    # Execute transitions
```

### 4.2 Tenant Isolation

All data strictly isolated by `tenant_id`:

- All queries filtered by tenant
- Cross-tenant references forbidden
- Migrations scoped to tenant schema

### 4.3 Audit Trail

All operations logged:

```python
# Example audit log entry
{
    "action": "publish_entity",
    "entity_type": "entity_definition",
    "entity_id": "uuid",
    "changes": {
        "status": "draft -> published",
        "migration_id": "uuid"
    },
    "user_id": "uuid",
    "timestamp": "2026-01-02T10:00:00Z"
}
```

---

## Implementation Roadmap

### Phase 1.1: Data Model Designer (Weeks 1-4)

**Week 1: Backend Foundation** ✅ COMPLETE
- ✅ Create database models (entity_definitions, field_definitions, etc.)
- ✅ Implement basic CRUD endpoints
- ✅ Create validation logic

**Week 2: Migration Generator** ⚠️ PARTIAL
- ✅ Build SQL migration generator (backend service exists)
- ❌ Implement schema preview (API exists, UI missing)
- ✅ Add migration execution engine (backend complete)
- ❌ Implement rollback capability (API exists, UI missing)

**Week 3: Frontend UI** ⚠️ PARTIAL (70% Complete)
- ✅ Build entity list view
- ❌ Create multi-step wizard
- ✅ Implement field designer form
- ✅ Add relationship configuration UI

**Week 4: Integration & Testing** ⚠️ PARTIAL
- ✅ Integrate with metadata system
- ✅ Sync with RBAC
- ⚠️ End-to-end testing (needs completion)
- ❌ Documentation (needs update)

### Phase 1.2: Workflow Designer (Weeks 5-8)

**Week 5: Backend Foundation** ✅ COMPLETE
- ✅ Create workflow models
- ✅ Implement CRUD endpoints
- ✅ Build workflow execution engine

**Week 6: State & Transition Logic** ✅ COMPLETE
- ✅ Implement state machine logic
- ✅ Build transition validation
- ✅ Add approval routing (backend)
- ✅ Create SLA tracking

**Week 7: Frontend Canvas** ❌ NOT IMPLEMENTED
- ❌ Setup canvas library
- ❌ Build visual designer
- ❌ Implement drag-and-drop
- ⚠️ Create properties panel (basic forms exist, visual canvas missing)

**Week 8: Testing & Integration** ⚠️ PARTIAL
- ❌ Workflow simulation
- ⚠️ Integration testing (partial)
- ⚠️ Performance optimization (needs work)
- ❌ Documentation (needs completion)

### Phase 1.3: Automation System (Weeks 9-11)

**Week 9: Backend Foundation** ✅ COMPLETE
- ✅ Create automation rule models
- ✅ Implement CRUD endpoints
- ✅ Build trigger system
- ✅ Create action execution engine

**Week 10: Frontend UI** ⚠️ PARTIAL (70% Complete)
- ✅ Build rule list and editor
- ❌ Visual condition builder (JSON editor exists instead)
- ❌ Visual action builder (JSON editor exists instead)
- ✅ Webhook configuration UI
- ✅ Execution history viewer

**Week 11: Testing & Integration** ⚠️ PARTIAL
- ❌ Automation testing UI
- ⚠️ Integration testing (partial)
- ✅ RBAC integration
- ❌ Documentation (needs completion)

### Phase 1.4: Lookup Configuration (Weeks 12-13)

**Week 12: Backend & Frontend** ✅ COMPLETE
- ✅ Create lookup models
- ✅ Implement CRUD endpoints
- ✅ Build lookup UI
- ✅ Add cascading dropdown rules

**Week 13: Testing & Integration** ✅ COMPLETE
- ✅ Integration testing
- ✅ RBAC integration
- ✅ Performance optimization
- ⚠️ Documentation (needs minor updates)

### Overall Progress Summary

| Phase | Status | Completion |
|-------|--------|-----------|
| Phase 1.1: Data Model Designer | ⚠️ Partial | 70% |
| Phase 1.2: Workflow Designer | ⚠️ Partial | 65% |
| Phase 1.3: Automation System | ⚠️ Partial | 70% |
| Phase 1.4: Lookup Configuration | ✅ Complete | 95% |
| **Overall Phase 1** | ⚠️ Partial | **75%** |

### Next Steps (Priority Order)

1. **High Priority - Core Features**
   - [ ] Implement migration preview UI with SQL display
   - [ ] Add visual workflow canvas with drag-and-drop
   - [ ] Build visual condition builder for automations
   - [ ] Add migration history viewer with rollback option

2. **Medium Priority - Enhanced UX**
   - [ ] Create workflow simulation/testing interface
   - [ ] Build automation rule testing/debugging UI
   - [ ] Add multi-step wizard for entity creation
   - [ ] Implement workflow versioning UI

3. **Low Priority - Nice to Have**
   - [ ] Build monitoring dashboards
   - [ ] Add advanced visualizations
   - [ ] Implement performance analytics
   - [ ] Create comprehensive documentation

---

## Testing Strategy

### 7.1 Unit Testing

**Backend:**
- Test all service methods
- Validate SQL generation
- Test migration execution
- Test workflow state transitions

**Frontend:**
- Test component rendering
- Test form validation
- Test canvas interactions

### 7.2 Integration Testing

**End-to-End Scenarios:**
1. Create entity → Add fields → Publish → Verify table created
2. Create workflow → Add states → Publish → Execute instance
3. Entity with workflow → Transition record → Verify state change

### 7.3 Performance Testing

**Benchmarks:**
- Entity list load time < 500ms
- Migration execution < 2s (simple entity)
- Workflow execution < 100ms per transition
- Canvas rendering < 1s for 50 nodes

---

## Appendix: Field Type Reference

| Field Type | Database Type | Input Type | Validation |
|------------|---------------|------------|------------|
| string | VARCHAR | text | max_length |
| text | TEXT | textarea | - |
| integer | INTEGER | number | min/max |
| decimal | NUMERIC | number | precision |
| boolean | BOOLEAN | checkbox | - |
| date | DATE | date-picker | format |
| datetime | TIMESTAMP | datetime-picker | format |
| email | VARCHAR | email | regex |
| url | VARCHAR | url | regex |
| phone | VARCHAR | tel | pattern |
| json | JSONB | textarea | json |
| uuid | UUID | text | uuid |
| lookup | UUID | select | fk |

---

**Document Version:** 1.0
**Last Updated:** 2026-01-02
**Status:** Design Complete - Ready for Implementation

