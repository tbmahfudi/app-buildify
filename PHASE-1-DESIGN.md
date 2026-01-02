# Phase 1 Design: Data Model & Workflow Designers

**Date:** 2026-01-02
**Project:** App-Buildify
**Phase:** 1 - Core Foundation
**Priorities:** 1 & 2
**Status:** Design Phase

---

## Table of Contents

1. [Overview](#overview)
2. [Priority 1: Data Model Designer](#priority-1-data-model-designer)
3. [Priority 2: Workflow/Business Process Designer](#priority-2-workflowbusiness-process-designer)
4. [Integration Points](#integration-points)
5. [Security & RBAC](#security--rbac)
6. [Implementation Roadmap](#implementation-roadmap)
7. [Testing Strategy](#testing-strategy)

---

## Overview

### Scope

This document provides detailed technical design for Phase 1 priorities:

- **Priority 1:** Data Model Designer (Entity/Table Creator)
- **Priority 2:** Workflow/Business Process Designer

These two features form the **Core Foundation** for the no-code platform, enabling users to:
1. Create database entities without backend code
2. Define business processes and workflows visually

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

**Week 1: Backend Foundation**
- [ ] Create database models (entity_definitions, field_definitions, etc.)
- [ ] Implement basic CRUD endpoints
- [ ] Create validation logic

**Week 2: Migration Generator**
- [ ] Build SQL migration generator
- [ ] Implement schema preview
- [ ] Add migration execution engine
- [ ] Implement rollback capability

**Week 3: Frontend UI**
- [ ] Build entity list view
- [ ] Create multi-step wizard
- [ ] Implement field designer form
- [ ] Add relationship configuration UI

**Week 4: Integration & Testing**
- [ ] Integrate with metadata system
- [ ] Sync with RBAC
- [ ] End-to-end testing
- [ ] Documentation

### Phase 1.2: Workflow Designer (Weeks 5-8)

**Week 5: Backend Foundation**
- [ ] Create workflow models
- [ ] Implement CRUD endpoints
- [ ] Build workflow execution engine

**Week 6: State & Transition Logic**
- [ ] Implement state machine logic
- [ ] Build transition validation
- [ ] Add approval routing
- [ ] Create SLA tracking

**Week 7: Frontend Canvas**
- [ ] Setup canvas library
- [ ] Build visual designer
- [ ] Implement drag-and-drop
- [ ] Create properties panel

**Week 8: Testing & Integration**
- [ ] Workflow simulation
- [ ] Integration testing
- [ ] Performance optimization
- [ ] Documentation

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

