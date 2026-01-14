# No-Code Platform - Phase 2: Runtime Data Layer & API Standardization

**Date:** 2026-01-11
**Last Updated:** 2026-01-14
**Project:** App-Buildify
**Phase:** 2 - Runtime Data Layer & API Standardization
**Status:** 🚧 **IN PROGRESS** - Priority 1 ✅, Priority 2 ✅, Priority 3 ✅ Complete

**Parent Document:** [NO-CODE-PLATFORM-DESIGN.md](NO-CODE-PLATFORM-DESIGN.md)
**Prerequisites:** Phase 1 must be 100% complete

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Phase 2 Objectives](#phase-2-objectives)
3. [Priority 1: Runtime Data Access Layer](#priority-1-runtime-data-access-layer)
4. [Priority 2: Backend API Standardization](#priority-2-backend-api-standardization)
5. [Priority 3: Auto-Generated UI](#priority-3-auto-generated-ui)
6. [Priority 4: Integration Layer](#priority-4-integration-layer)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Backend Migration Tracking](#backend-migration-tracking)
9. [Frontend Migration Guide](#frontend-migration-guide)
10. [Testing Strategy](#testing-strategy)
11. [Rollback Plan](#rollback-plan)

---

## Executive Summary

**Goal:** Make Phase 1 nocode entities **functional at runtime** by enabling CRUD operations on entity records and standardizing backend APIs.

**Current Gap:**
- ✅ Can **design** entities in Phase 1 (EntityDefinition, fields, relationships)
- ❌ **Cannot use** entities at runtime (no CRUD operations on records)
- ❌ **Cannot generate UI** for entity management
- ❌ **Cannot create reports** on nocode entity data
- ⚠️ **Inconsistent API paths** (mixed versioning)

**Phase 2 Delivers:**
1. Dynamic Data API for runtime CRUD operations
2. Standardized `/api/v1/*` paths for all APIs
3. Auto-generated UI for nocode entities
4. Report/Dashboard integration with nocode data
5. Backend migration tracking for frontend updates

**Duration:** 6-8 weeks
**Complexity:** High

---

## Phase 2 Objectives

### Primary Objectives

1. **Runtime Data Access** - Enable CRUD operations on nocode entity records
2. **API Standardization** - Migrate all APIs to `/api/v1/*` versioning
3. **UI Generation** - Auto-generate CRUD pages for nocode entities
4. **Integration** - Connect reports, dashboards, automations with nocode data

### Success Criteria

✅ **User can:**
1. Design a "Customer" entity in Data Model Designer (Phase 1)
2. Create customer records via generated UI (Phase 2)
3. View customer list with filtering and sorting (Phase 2)
4. Edit and delete customer records (Phase 2)
5. Create reports on customer data (Phase 2)
6. Build dashboards with customer metrics (Phase 2)
7. Trigger automations on customer events (Phase 2)

✅ **System can:**
1. Generate SQLAlchemy models from EntityDefinition at runtime
2. Execute CRUD operations with tenant isolation
3. Apply field validation and RBAC at runtime
4. Track audit trail for nocode entity operations
5. Serve all APIs from `/api/v1/*` prefix

---

## Priority 1: Runtime Data Access Layer

**Status:** 🚧 In Progress
**Duration:** 3-4 weeks
**Complexity:** High
**Dependencies:** ✅ Phase 1 EntityDefinition complete

### Overview

Create a dynamic data API that reads EntityDefinition metadata and performs CRUD operations on the actual database tables created by migrations.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Dynamic Data API (/api/v1/dynamic-data)                │
│  - FastAPI router with path parameter {entity_name}    │
│  - Pydantic schemas for request/response validation    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  DynamicEntityService                                    │
│  - get_entity_model(entity_name) → SQLAlchemy Model    │
│  - create_record(entity_name, data) → Record           │
│  - list_records(entity_name, filters, sort, page)      │
│  - get_record(entity_name, id) → Record                │
│  - update_record(entity_name, id, data) → Record       │
│  - delete_record(entity_name, id)                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Runtime Model Generator                                 │
│  - read_entity_definition(entity_name) → EntityDef     │
│  - generate_sqlalchemy_model(entity_def) → Model       │
│  - apply_relationships(model, entity_def)               │
│  - cache_model(entity_name, model)                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Query Execution Engine                                  │
│  - build_query(model, filters, sort) → Query           │
│  - apply_tenant_filter(query, tenant_id) → Query       │
│  - apply_rbac_filter(query, user, permissions)         │
│  - execute_with_pagination(query, page, size)          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL Database                                     │
│  - Dynamic tables created by EntityDefinition migrations│
│  - Tenant isolation via tenant_id columns               │
└─────────────────────────────────────────────────────────┘
```

### API Design

#### Base Path
```
/api/v1/dynamic-data/{entity_name}/records
```

#### Endpoints

##### 1. Create Record
```http
POST /api/v1/dynamic-data/{entity_name}/records
Content-Type: application/json

Request Body:
{
  "data": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  }
}

Response (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "created_at": "2026-01-11T10:30:00Z",
    "updated_at": "2026-01-11T10:30:00Z"
  }
}

Errors:
- 400 Bad Request: Validation failed
- 403 Forbidden: Permission denied (entity:create:tenant)
- 404 Not Found: Entity not found or not published
```

##### 2. List Records
```http
GET /api/v1/dynamic-data/{entity_name}/records
Query Parameters:
  - page: int (default: 1)
  - page_size: int (default: 25, max: 100)
  - sort: string (e.g., "name:asc,created_at:desc")
  - filters: JSON string (see filter format below)
  - search: string (global search across text fields)

Response (200 OK):
{
  "items": [
    {
      "id": "uuid...",
      "first_name": "John",
      "last_name": "Doe",
      ...
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 25,
  "pages": 6
}

Filter Format (JSON string):
{
  "operator": "AND",
  "conditions": [
    {"field": "email", "operator": "contains", "value": "@example.com"},
    {"field": "created_at", "operator": "gte", "value": "2026-01-01"}
  ]
}

Operators: eq, ne, gt, gte, lt, lte, contains, starts_with, ends_with, in, not_in, is_null, is_not_null
```

##### 3. Get Single Record
```http
GET /api/v1/dynamic-data/{entity_name}/records/{id}

Response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "John",
    ...
  }
}

Errors:
- 403 Forbidden: Permission denied (entity:read:tenant)
- 404 Not Found: Record not found
```

##### 4. Update Record
```http
PUT /api/v1/dynamic-data/{entity_name}/records/{id}
Content-Type: application/json

Request Body:
{
  "data": {
    "phone": "+0987654321"
  }
}

Response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+0987654321",
    "updated_at": "2026-01-11T11:00:00Z"
  }
}

Errors:
- 400 Bad Request: Validation failed
- 403 Forbidden: Permission denied (entity:update:own)
- 404 Not Found: Record not found
```

##### 5. Delete Record
```http
DELETE /api/v1/dynamic-data/{entity_name}/records/{id}

Response (204 No Content)

Errors:
- 403 Forbidden: Permission denied (entity:delete:own)
- 404 Not Found: Record not found
```

##### 6. Get Related Records
```http
GET /api/v1/dynamic-data/{entity_name}/records/{id}/{relationship_name}
Example: GET /api/v1/dynamic-data/customers/records/{id}/orders

Response (200 OK):
{
  "items": [
    {
      "id": "order-uuid-1",
      "order_number": "ORD-001",
      "total_amount": 150.00,
      ...
    }
  ],
  "total": 5
}

Notes:
- Follows RelationshipDefinition from Phase 1
- Applies RBAC to related entity as well
```

##### 7. Bulk Create
```http
POST /api/v1/dynamic-data/{entity_name}/records/bulk
Content-Type: application/json

Request Body:
{
  "records": [
    {"first_name": "John", "last_name": "Doe", "email": "john@example.com"},
    {"first_name": "Jane", "last_name": "Smith", "email": "jane@example.com"}
  ]
}

Response (201 Created):
{
  "created": 2,
  "failed": 0,
  "errors": [],
  "ids": ["uuid-1", "uuid-2"]
}
```

##### 8. Bulk Update
```http
PUT /api/v1/dynamic-data/{entity_name}/records/bulk
Content-Type: application/json

Request Body:
{
  "records": [
    {"id": "uuid-1", "status": "active"},
    {"id": "uuid-2", "status": "active"}
  ]
}

Response (200 OK):
{
  "updated": 2,
  "failed": 0,
  "errors": []
}
```

##### 9. Bulk Delete
```http
DELETE /api/v1/dynamic-data/{entity_name}/records/bulk
Content-Type: application/json

Request Body:
{
  "ids": ["uuid-1", "uuid-2", "uuid-3"]
}

Response (200 OK):
{
  "deleted": 3,
  "failed": 0,
  "errors": []
}
```

### Implementation Details

#### File Structure
```
/backend/app/
├── routers/
│   └── dynamic_data.py          (NEW - Dynamic Data API router)
├── services/
│   ├── dynamic_entity_service.py (NEW - CRUD service)
│   └── runtime_model_generator.py (NEW - Model generation)
├── schemas/
│   └── dynamic_data.py           (NEW - Request/response schemas)
├── core/
│   ├── dynamic_query_builder.py  (NEW - Query builder)
│   └── model_cache.py            (NEW - Runtime model cache)
└── utils/
    └── field_type_mapper.py      (NEW - Field type conversions)
```

#### Key Components

##### 1. Runtime Model Generator
**File:** `/backend/app/services/runtime_model_generator.py`

```python
from typing import Type, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from app.models.data_model import EntityDefinition, FieldDefinition

class RuntimeModelGenerator:
    """Generate SQLAlchemy models from EntityDefinition at runtime"""

    def __init__(self, db: Session):
        self.db = db
        self._model_cache: Dict[str, Type] = {}

    def get_model(self, entity_name: str, tenant_id: str) -> Type:
        """Get or create SQLAlchemy model for entity"""
        cache_key = f"{tenant_id}:{entity_name}"

        if cache_key in self._model_cache:
            return self._model_cache[cache_key]

        # Load entity definition
        entity_def = self._load_entity_definition(entity_name, tenant_id)

        if not entity_def:
            raise ValueError(f"Entity '{entity_name}' not found or not published")

        # Generate model
        model = self._generate_model(entity_def)

        # Cache it
        self._model_cache[cache_key] = model

        return model

    def _load_entity_definition(self, entity_name: str, tenant_id: str) -> EntityDefinition:
        """Load EntityDefinition from database"""
        return self.db.query(EntityDefinition).filter(
            EntityDefinition.name == entity_name,
            EntityDefinition.status == "published",
            or_(
                EntityDefinition.tenant_id == tenant_id,
                EntityDefinition.tenant_id.is_(None)  # Platform-level
            )
        ).first()

    def _generate_model(self, entity_def: EntityDefinition) -> Type:
        """Generate SQLAlchemy model from EntityDefinition"""
        Base = declarative_base()

        # Build attributes dict
        attrs = {
            '__tablename__': entity_def.table_name,
            '__table_args__': {'schema': entity_def.schema_name or 'public'}
        }

        # Add columns from FieldDefinitions
        for field in entity_def.fields:
            column = self._create_column(field)
            attrs[field.name] = column

        # Create model class dynamically
        model_class = type(
            entity_def.name,  # Class name
            (Base,),          # Base classes
            attrs             # Attributes
        )

        return model_class

    def _create_column(self, field: FieldDefinition) -> Column:
        """Create SQLAlchemy Column from FieldDefinition"""
        # Map field_type to SQLAlchemy type
        type_map = {
            'string': String(field.max_length or 255),
            'email': String(255),
            'text': Text,
            'integer': Integer,
            'decimal': Numeric(precision=field.precision, scale=field.scale),
            'boolean': Boolean,
            'date': DateTime,
            'datetime': DateTime,
            'uuid': String(36),
            # ... more types
        }

        col_type = type_map.get(field.field_type, String(255))

        return Column(
            field.db_column_name,
            col_type,
            primary_key=field.is_primary_key,
            nullable=not field.is_required,
            unique=field.is_unique,
            index=field.is_indexed,
            default=field.default_value
        )

    def clear_cache(self, entity_name: str = None):
        """Clear model cache (when entity definition changes)"""
        if entity_name:
            self._model_cache = {
                k: v for k, v in self._model_cache.items()
                if not k.endswith(f":{entity_name}")
            }
        else:
            self._model_cache.clear()
```

##### 2. Dynamic Entity Service
**File:** `/backend/app/services/dynamic_entity_service.py`

```python
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.runtime_model_generator import RuntimeModelGenerator
from app.core.dynamic_query_builder import DynamicQueryBuilder

class DynamicEntityService:
    """Service for CRUD operations on dynamic entities"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self.model_generator = RuntimeModelGenerator(db)
        self.query_builder = DynamicQueryBuilder()

    async def create_record(
        self,
        entity_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new record"""
        # Get model
        model = self.model_generator.get_model(
            entity_name,
            str(self.current_user.tenant_id)
        )

        # Add tenant_id if entity has it
        if hasattr(model, 'tenant_id'):
            data['tenant_id'] = str(self.current_user.tenant_id)

        # Add created_by if entity has it
        if hasattr(model, 'created_by'):
            data['created_by'] = str(self.current_user.id)

        # Create instance
        record = model(**data)

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        # Audit log
        await self._create_audit_log('CREATE', entity_name, str(record.id), data)

        return self._model_to_dict(record)

    async def list_records(
        self,
        entity_name: str,
        filters: Optional[Dict] = None,
        sort: Optional[List] = None,
        page: int = 1,
        page_size: int = 25,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """List records with filtering, sorting, pagination"""
        model = self.model_generator.get_model(
            entity_name,
            str(self.current_user.tenant_id)
        )

        # Base query
        query = self.db.query(model)

        # Apply tenant filter
        if hasattr(model, 'tenant_id'):
            query = query.filter(model.tenant_id == str(self.current_user.tenant_id))

        # Apply filters
        if filters:
            query = self.query_builder.apply_filters(query, model, filters)

        # Apply search
        if search:
            query = self.query_builder.apply_search(query, model, search)

        # Get total
        total = query.count()

        # Apply sorting
        if sort:
            query = self.query_builder.apply_sort(query, model, sort)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute
        records = query.all()

        return {
            'items': [self._model_to_dict(r) for r in records],
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }

    async def get_record(self, entity_name: str, record_id: str) -> Dict[str, Any]:
        """Get single record by ID"""
        model = self.model_generator.get_model(
            entity_name,
            str(self.current_user.tenant_id)
        )

        query = self.db.query(model).filter(model.id == record_id)

        # Apply tenant filter
        if hasattr(model, 'tenant_id'):
            query = query.filter(model.tenant_id == str(self.current_user.tenant_id))

        record = query.first()

        if not record:
            raise ValueError(f"Record not found: {record_id}")

        return self._model_to_dict(record)

    async def update_record(
        self,
        entity_name: str,
        record_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update record"""
        model = self.model_generator.get_model(
            entity_name,
            str(self.current_user.tenant_id)
        )

        query = self.db.query(model).filter(model.id == record_id)

        # Apply tenant filter
        if hasattr(model, 'tenant_id'):
            query = query.filter(model.tenant_id == str(self.current_user.tenant_id))

        record = query.first()

        if not record:
            raise ValueError(f"Record not found: {record_id}")

        # Capture before state
        before = self._model_to_dict(record)

        # Update fields
        for key, value in data.items():
            if hasattr(record, key) and key not in ['id', 'created_at', 'created_by']:
                setattr(record, key, value)

        # Update metadata
        if hasattr(record, 'updated_by'):
            record.updated_by = str(self.current_user.id)

        self.db.commit()
        self.db.refresh(record)

        # Capture after state
        after = self._model_to_dict(record)

        # Audit log
        await self._create_audit_log('UPDATE', entity_name, record_id, {
            'before': before,
            'after': after
        })

        return after

    async def delete_record(self, entity_name: str, record_id: str):
        """Delete record"""
        model = self.model_generator.get_model(
            entity_name,
            str(self.current_user.tenant_id)
        )

        query = self.db.query(model).filter(model.id == record_id)

        # Apply tenant filter
        if hasattr(model, 'tenant_id'):
            query = query.filter(model.tenant_id == str(self.current_user.tenant_id))

        record = query.first()

        if not record:
            raise ValueError(f"Record not found: {record_id}")

        # Capture state before deletion
        before = self._model_to_dict(record)

        # Soft delete if supported
        if hasattr(record, 'deleted_at'):
            record.deleted_at = datetime.utcnow()
            if hasattr(record, 'deleted_by'):
                record.deleted_by = str(self.current_user.id)
        else:
            self.db.delete(record)

        self.db.commit()

        # Audit log
        await self._create_audit_log('DELETE', entity_name, record_id, {
            'deleted': before
        })

    def _model_to_dict(self, record) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dict"""
        result = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            # Convert to JSON-serializable types
            if value is not None:
                if isinstance(value, (datetime, date)):
                    result[column.name] = value.isoformat()
                elif isinstance(value, UUID):
                    result[column.name] = str(value)
                else:
                    result[column.name] = value
            else:
                result[column.name] = None
        return result

    async def _create_audit_log(
        self,
        action: str,
        entity_name: str,
        entity_id: str,
        changes: Dict
    ):
        """Create audit log entry"""
        from app.core.audit import create_audit_log
        create_audit_log(
            db=self.db,
            action=action,
            user=self.current_user,
            entity_type=entity_name,
            entity_id=entity_id,
            changes=changes,
            status='success'
        )
```

##### 3. Dynamic Data Router
**File:** `/backend/app/routers/dynamic_data.py`

```python
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_db, get_current_user, has_permission
from app.schemas.dynamic_data import (
    DynamicDataCreateRequest,
    DynamicDataUpdateRequest,
    DynamicDataResponse,
    DynamicDataListResponse,
    DynamicDataBulkRequest,
    DynamicDataBulkResponse
)
from app.services.dynamic_entity_service import DynamicEntityService

router = APIRouter(prefix="/api/v1/dynamic-data", tags=["Dynamic Data"])

# Create Record
@router.post("/{entity_name}/records", response_model=DynamicDataResponse)
async def create_record(
    entity_name: str,
    request: DynamicDataCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new record in dynamic entity"""
    # Check permission: {entity_name}:create:tenant
    # This will be dynamic permission based on entity_name

    service = DynamicEntityService(db, current_user)

    try:
        result = await service.create_record(entity_name, request.data)
        return DynamicDataResponse(
            id=result['id'],
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# List Records
@router.get("/{entity_name}/records", response_model=DynamicDataListResponse)
async def list_records(
    entity_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort: Optional[str] = Query(None),
    filters: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List records with filtering, sorting, pagination"""
    service = DynamicEntityService(db, current_user)

    # Parse filters from JSON string if provided
    filter_dict = json.loads(filters) if filters else None

    # Parse sort
    sort_list = []
    if sort:
        for item in sort.split(','):
            field, direction = item.split(':') if ':' in item else (item, 'asc')
            sort_list.append((field, direction))

    result = await service.list_records(
        entity_name=entity_name,
        filters=filter_dict,
        sort=sort_list if sort_list else None,
        page=page,
        page_size=page_size,
        search=search
    )

    return DynamicDataListResponse(**result)

# Get Record
@router.get("/{entity_name}/records/{record_id}", response_model=DynamicDataResponse)
async def get_record(
    entity_name: str,
    record_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get single record by ID"""
    service = DynamicEntityService(db, current_user)

    try:
        result = await service.get_record(entity_name, record_id)
        return DynamicDataResponse(
            id=result['id'],
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Update Record
@router.put("/{entity_name}/records/{record_id}", response_model=DynamicDataResponse)
async def update_record(
    entity_name: str,
    record_id: str,
    request: DynamicDataUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update record"""
    service = DynamicEntityService(db, current_user)

    try:
        result = await service.update_record(entity_name, record_id, request.data)
        return DynamicDataResponse(
            id=result['id'],
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Delete Record
@router.delete("/{entity_name}/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    entity_name: str,
    record_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete record"""
    service = DynamicEntityService(db, current_user)

    try:
        await service.delete_record(entity_name, record_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Bulk operations...
```

### RBAC Integration

Dynamic permissions for nocode entities:
```python
# When entity "customers" is published, auto-create permissions:
customers:create:tenant
customers:read:all
customers:read:tenant
customers:read:own
customers:update:all
customers:update:tenant
customers:update:own
customers:delete:all
customers:delete:tenant
customers:delete:own
```

### Validation Engine

Field validation at runtime:
```python
class RuntimeValidator:
    def validate_field(self, field_def: FieldDefinition, value: Any) -> bool:
        # Required check
        if field_def.is_required and value is None:
            raise ValidationError(f"{field_def.label} is required")

        # Type check
        if not self._check_type(field_def.field_type, value):
            raise ValidationError(f"{field_def.label} must be {field_def.field_type}")

        # Range check
        if field_def.min_value and value < field_def.min_value:
            raise ValidationError(f"{field_def.label} must be >= {field_def.min_value}")

        # Custom validation rules (from field_def.validation_rules JSON)
        if field_def.validation_rules:
            self._apply_custom_rules(field_def.validation_rules, value)

        return True
```

### Performance Considerations

1. **Model Caching** - Cache generated SQLAlchemy models per tenant/entity
2. **Query Optimization** - Use EXPLAIN ANALYZE for generated queries
3. **Indexing** - Respect IndexDefinition from Phase 1
4. **Connection Pooling** - Reuse database connections
5. **Result Caching** - Cache frequently accessed records (optional)

### Testing Requirements

1. **Unit Tests**
   - RuntimeModelGenerator: Test model generation for all field types
   - DynamicEntityService: Test CRUD operations
   - Query Builder: Test filter/sort/pagination logic

2. **Integration Tests**
   - Create entity → Publish migration → CRUD operations
   - Multi-tenant isolation
   - RBAC enforcement
   - Relationship traversal

3. **Performance Tests**
   - Load testing with 10k+ records
   - Complex query performance
   - Concurrent access

---

## Priority 2: Backend API Standardization

**Status:** ✅ Complete
**Duration:** 2-3 weeks (Completed in 1 session)
**Complexity:** Medium
**Dependencies:** None (can start in parallel with Priority 1)

### Overview

Migrate all legacy backend APIs to standardized `/api/v1/*` paths. **All deprecated endpoints have been removed** - frontend updates required (use migration tracking tables below).

### Strategy

**Gradual Migration with Backward Compatibility**

```
Phase 2.1: Add /api/v1/* Aliases (Week 1)
├── Keep old paths working (no breaking changes)
├── Add new paths as aliases
└── Both paths serve same endpoints

Phase 2.2: Add Deprecation Warnings (Week 2)
├── Add HTTP Warning headers to old paths
├── Update API documentation
└── Track usage metrics (old vs new paths)

Phase 2.3: Update Routers (Week 2)
├── Standardize response formats
├── Add proper error handling
└── Improve validation

Phase 2.4: Documentation (Week 3)
├── OpenAPI/Swagger specs
├── Migration guide for frontend
└── Deprecation timeline
```

### Backend API Migration Tracking

Track all backend endpoints being migrated for frontend reference.

#### 1. Organization API (`/org` → `/api/v1/org`)

**File:** `/backend/app/routers/org.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| List Companies | `GET /org/companies` | `GET /api/v1/org/companies` | ⏸️ Pending | Used in companies.js |
| Get Company | `GET /org/companies/{id}` | `GET /api/v1/org/companies/{id}` | ⏸️ Pending | |
| Create Company | `POST /org/companies` | `POST /api/v1/org/companies` | ⏸️ Pending | |
| Update Company | `PUT /org/companies/{id}` | `PUT /api/v1/org/companies/{id}` | ⏸️ Pending | |
| Delete Company | `DELETE /org/companies/{id}` | `DELETE /api/v1/org/companies/{id}` | ⏸️ Pending | |
| List Branches | `GET /org/branches` | `GET /api/v1/org/branches` | ⏸️ Pending | Used in tenants.js |
| Get Branch | `GET /org/branches/{id}` | `GET /api/v1/org/branches/{id}` | ⏸️ Pending | |
| Create Branch | `POST /org/branches` | `POST /api/v1/org/branches` | ⏸️ Pending | |
| Update Branch | `PUT /org/branches/{id}` | `PUT /api/v1/org/branches/{id}` | ⏸️ Pending | |
| Delete Branch | `DELETE /org/branches/{id}` | `DELETE /api/v1/org/branches/{id}` | ⏸️ Pending | |
| List Departments | `GET /org/departments` | `GET /api/v1/org/departments` | ⏸️ Pending | Used in organization-hierarchy.js |
| Get Department | `GET /org/departments/{id}` | `GET /api/v1/org/departments/{id}` | ⏸️ Pending | |
| Create Department | `POST /org/departments` | `POST /api/v1/org/departments` | ⏸️ Pending | |
| Update Department | `PUT /org/departments/{id}` | `PUT /api/v1/org/departments/{id}` | ⏸️ Pending | |
| Delete Department | `DELETE /org/departments/{id}` | `DELETE /api/v1/org/departments/{id}` | ⏸️ Pending | |
| List Tenants | `GET /org/tenants` | `GET /api/v1/org/tenants` | ⏸️ Pending | Used in tenants.js |
| Get Tenant | `GET /org/tenants/{id}` | `GET /api/v1/org/tenants/{id}` | ⏸️ Pending | |
| Create Tenant | `POST /org/tenants` | `POST /api/v1/org/tenants` | ⏸️ Pending | |
| Update Tenant | `PUT /org/tenants/{id}` | `GET /api/v1/org/tenants/{id}` | ⏸️ Pending | |
| Delete Tenant | `DELETE /org/tenants/{id}` | `DELETE /api/v1/org/tenants/{id}` | ⏸️ Pending | |
| List Users | `GET /org/users` | `GET /api/v1/org/users` | ⏸️ Pending | |

**Implementation:**
```python
# In main.py, add both routes:
app.include_router(org_router, prefix="/api/v1/org")  # New
app.include_router(org_router, prefix="/org")          # Legacy (with deprecation warning)
```

**Frontend Files Affected:**
- `/frontend/assets/js/companies.js` (5 calls)
- `/frontend/assets/js/tenants.js` (7 calls)
- `/frontend/assets/js/organization-hierarchy.js` (11 calls)

---

#### 2. Data API (`/data` → `/api/v1/data`)

**File:** `/backend/app/routers/data.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| Search/List | `POST /data/{entity}/list` | `GET /api/v1/data/{entity}` | ⏸️ Pending | Change POST to GET |
| Get Record | `GET /data/{entity}/{id}` | `GET /api/v1/data/{entity}/{id}` | ⏸️ Pending | |
| Create | `POST /data/{entity}` | `POST /api/v1/data/{entity}` | ⏸️ Pending | |
| Update | `PUT /data/{entity}/{id}` | `PUT /api/v1/data/{entity}/{id}` | ⏸️ Pending | |
| Delete | `DELETE /data/{entity}/{id}` | `DELETE /api/v1/data/{entity}/{id}` | ⏸️ Pending | |
| Bulk Operations | `POST /data/{entity}/bulk` | `POST /api/v1/data/{entity}/bulk` | ⏸️ Pending | |

**Breaking Change:** `POST /data/{entity}/list` should become `GET /api/v1/data/{entity}` with query parameters.

**Implementation:**
```python
# Add new GET endpoint
@router.get("/api/v1/data/{entity}")
def list_records(
    entity: str,
    page: int = Query(1),
    page_size: int = Query(25),
    sort: Optional[str] = Query(None),
    filters: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Same logic as POST /data/{entity}/list
    pass

# Keep old POST for backward compatibility
@router.post("/data/{entity}/list")
def list_records_legacy(response: Response, ...):
    response.headers["Warning"] = '299 - "Deprecated, use GET /api/v1/data/{entity}"'
    # Same logic
    pass
```

**Frontend Files Affected:**
- `/frontend/assets/js/data-service.js`
- `/frontend/assets/js/entity-manager.js`

---

#### 3. Metadata API (`/metadata` → `/api/v1/metadata`)

**File:** `/backend/app/routers/metadata.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| List Entities | `GET /metadata/entities` | `GET /api/v1/metadata/entities` | ⏸️ Pending | |
| Get Entity Metadata | `GET /metadata/entities/{name}` | `GET /api/v1/metadata/entities/{name}` | ⏸️ Pending | |
| Create Metadata | `POST /metadata/entities` | `POST /api/v1/metadata/entities` | ⏸️ Pending | |
| Update Metadata | `PUT /metadata/entities/{name}` | `PUT /api/v1/metadata/entities/{name}` | ⏸️ Pending | |
| Delete Metadata | `DELETE /metadata/entities/{name}` | `DELETE /api/v1/metadata/entities/{name}` | ⏸️ Pending | |

**Frontend Files Affected:**
- `/frontend/assets/js/metadata-service.js`
- `/frontend/assets/js/dynamic-table.js`
- `/frontend/assets/js/dynamic-form.js`

---

#### 4. Dashboard API (`/dashboards` → `/api/v1/dashboards`)

**File:** `/backend/app/routers/dashboards.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| List Dashboards | `GET /dashboards` | `GET /api/v1/dashboards` | ⏸️ Pending | |
| Get Dashboard | `GET /dashboards/{id}` | `GET /api/v1/dashboards/{id}` | ⏸️ Pending | |
| Create Dashboard | `POST /dashboards` | `POST /api/v1/dashboards` | ⏸️ Pending | |
| Update Dashboard | `PUT /dashboards/{id}` | `PUT /api/v1/dashboards/{id}` | ⏸️ Pending | |
| Delete Dashboard | `DELETE /dashboards/{id}` | `DELETE /api/v1/dashboards/{id}` | ⏸️ Pending | |
| Clone Dashboard | `POST /dashboards/{id}/clone` | `POST /api/v1/dashboards/{id}/clone` | ⏸️ Pending | |
| Create Page | `POST /dashboards/pages` | `POST /api/v1/dashboards/pages` | ⏸️ Pending | |
| Update Page | `PUT /dashboards/pages/{id}` | `PUT /api/v1/dashboards/pages/{id}` | ⏸️ Pending | |
| Delete Page | `DELETE /dashboards/pages/{id}` | `DELETE /api/v1/dashboards/pages/{id}` | ⏸️ Pending | |
| Create Widget | `POST /dashboards/widgets` | `POST /api/v1/dashboards/widgets` | ⏸️ Pending | |
| Update Widget | `PUT /dashboards/widgets/{id}` | `PUT /api/v1/dashboards/widgets/{id}` | ⏸️ Pending | |
| Delete Widget | `DELETE /dashboards/widgets/{id}` | `DELETE /api/v1/dashboards/widgets/{id}` | ⏸️ Pending | |
| Get Widget Data | `GET /dashboards/widgets/{id}/data` | `GET /api/v1/dashboards/widgets/{id}/data` | ⏸️ Pending | |
| Create Share | `POST /dashboards/{id}/share` | `POST /api/v1/dashboards/{id}/share` | ⏸️ Pending | |
| Create Snapshot | `POST /dashboards/{id}/snapshots` | `POST /api/v1/dashboards/{id}/snapshots` | ⏸️ Pending | |

**Frontend Files Affected:**
- `/frontend/components/dashboard-designer.js`

---

#### 5. Report API (`/reports` → `/api/v1/reports`)

**File:** `/backend/app/routers/reports.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| Create Report Definition | `POST /reports/definitions` | `POST /api/v1/reports/definitions` | ⏸️ Pending | |
| List Report Definitions | `GET /reports/definitions` | `GET /api/v1/reports/definitions` | ⏸️ Pending | |
| Get Report Definition | `GET /reports/definitions/{id}` | `GET /api/v1/reports/definitions/{id}` | ⏸️ Pending | |
| Update Report Definition | `PUT /reports/definitions/{id}` | `PUT /api/v1/reports/definitions/{id}` | ⏸️ Pending | |
| Delete Report Definition | `DELETE /reports/definitions/{id}` | `DELETE /api/v1/reports/definitions/{id}` | ⏸️ Pending | |
| Execute Report | `POST /reports/execute` | `POST /api/v1/reports/execute` | ⏸️ Pending | |
| Execute & Export | `POST /reports/execute/export` | `POST /api/v1/reports/execute/export` | ⏸️ Pending | |
| Get Execution History | `GET /reports/executions/{id}` | `GET /api/v1/reports/executions/{id}` | ⏸️ Pending | |
| Get Lookup Data | `GET /reports/lookup-data` | `GET /api/v1/reports/lookup-data` | ⏸️ Pending | |
| Create Schedule | `POST /reports/schedules` | `POST /api/v1/reports/schedules` | ⏸️ Pending | |
| List Templates | `GET /reports/templates` | `GET /api/v1/reports/templates` | ⏸️ Pending | |
| Create from Template | `POST /reports/templates/{id}/create` | `POST /api/v1/reports/templates/{id}/create` | ⏸️ Pending | |

**Frontend Files Affected:**
- `/frontend/components/report-designer.js`

---

#### 6. Menu API (`/menu` → `/api/v1/menu`)

**File:** `/backend/app/routers/menu.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| Get User Menu | `GET /menu` | `GET /api/v1/menu` | ⏸️ Pending | |
| List Menu Items | `GET /menu/items` | `GET /api/v1/menu/items` | ⏸️ Pending | |
| Create Menu Item | `POST /menu/items` | `POST /api/v1/menu/items` | ⏸️ Pending | |
| Update Menu Item | `PUT /menu/items/{id}` | `PUT /api/v1/menu/items/{id}` | ⏸️ Pending | |
| Delete Menu Item | `DELETE /menu/items/{id}` | `DELETE /api/v1/menu/items/{id}` | ⏸️ Pending | |

**Frontend Files Affected:**
- `/frontend/assets/js/menu-service.js`
- Navigation components

---

#### 7. RBAC API (`/rbac` → `/api/v1/rbac`)

**File:** `/backend/app/routers/rbac.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| List Roles | `GET /rbac/roles` | `GET /api/v1/rbac/roles` | ⏸️ Pending | |
| Create Role | `POST /rbac/roles` | `POST /api/v1/rbac/roles` | ⏸️ Pending | |
| Update Role | `PUT /rbac/roles/{id}` | `PUT /api/v1/rbac/roles/{id}` | ⏸️ Pending | |
| Delete Role | `DELETE /rbac/roles/{id}` | `DELETE /api/v1/rbac/roles/{id}` | ⏸️ Pending | |
| List Permissions | `GET /rbac/permissions` | `GET /api/v1/rbac/permissions` | ⏸️ Pending | |
| Assign Permission | `POST /rbac/roles/{id}/permissions` | `POST /api/v1/rbac/roles/{id}/permissions` | ⏸️ Pending | |
| Remove Permission | `DELETE /rbac/roles/{id}/permissions/{perm_id}` | `DELETE /api/v1/rbac/roles/{id}/permissions/{perm_id}` | ⏸️ Pending | |
| List Groups | `GET /rbac/groups` | `GET /api/v1/rbac/groups` | ⏸️ Pending | |
| Create Group | `POST /rbac/groups` | `POST /api/v1/rbac/groups` | ⏸️ Pending | |

**Frontend Files Affected:**
- `/frontend/assets/js/rbac-management.js`

---

#### 8. Audit API (`/audit` → `/api/v1/audit`)

**File:** `/backend/app/routers/audit.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| List Audit Logs | `GET /audit/logs` | `GET /api/v1/audit/logs` | ⏸️ Pending | |
| Get Audit Log | `GET /audit/logs/{id}` | `GET /api/v1/audit/logs/{id}` | ⏸️ Pending | |

**Frontend Files Affected:**
- `/frontend/assets/js/audit-viewer.js`

---

#### 9. Auth API (`/auth` → `/api/v1/auth`)

**File:** `/backend/app/routers/auth.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| Login | `POST /auth/login` | `POST /api/v1/auth/login` | ⏸️ Pending | CRITICAL - test thoroughly |
| Logout | `POST /auth/logout` | `POST /api/v1/auth/logout` | ⏸️ Pending | |
| Refresh Token | `POST /auth/refresh` | `POST /api/v1/auth/refresh` | ⏸️ Pending | |
| Get Current User | `GET /auth/me` | `GET /api/v1/auth/me` | ⏸️ Pending | |
| Change Password | `POST /auth/change-password` | `POST /api/v1/auth/change-password` | ⏸️ Pending | |

**Frontend Files Affected:**
- `/frontend/assets/js/auth.js` - CRITICAL FILE
- All authenticated requests

---

#### 10. Settings API (`/settings` → `/api/v1/settings`)

**File:** `/backend/app/routers/settings.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| Get Settings | `GET /settings` | `GET /api/v1/settings` | ⏸️ Pending | |
| Update Settings | `PUT /settings` | `PUT /api/v1/settings` | ⏸️ Pending | |
| Get User Preferences | `GET /settings/preferences` | `GET /api/v1/settings/preferences` | ⏸️ Pending | |
| Update User Preferences | `PUT /settings/preferences` | `PUT /api/v1/settings/preferences` | ⏸️ Pending | |

**Frontend Files Affected:**
- `/frontend/assets/js/settings.js`

---

#### 11. Modules API (`/modules` → `/api/v1/modules`)

**File:** `/backend/app/routers/modules.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| List Modules | `GET /modules` | `GET /api/v1/modules` | ⏸️ Pending | |
| Get Module | `GET /modules/{id}` | `GET /api/v1/modules/{id}` | ⏸️ Pending | |
| Activate Module | `POST /modules/{id}/activate` | `POST /api/v1/modules/{id}/activate` | ⏸️ Pending | |
| Deactivate Module | `POST /modules/{id}/deactivate` | `POST /api/v1/modules/{id}/deactivate` | ⏸️ Pending | |

**Frontend Files Affected:**
- `/frontend/assets/js/module-manager.js`

---

#### 12. Scheduler API (`/scheduler` → `/api/v1/scheduler`)

**File:** `/backend/app/routers/scheduler.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| List Jobs | `GET /scheduler/jobs` | `GET /api/v1/scheduler/jobs` | ⏸️ Pending | |
| Create Job | `POST /scheduler/jobs` | `POST /api/v1/scheduler/jobs` | ⏸️ Pending | |
| Update Job | `PUT /scheduler/jobs/{id}` | `PUT /api/v1/scheduler/jobs/{id}` | ⏸️ Pending | |
| Delete Job | `DELETE /scheduler/jobs/{id}` | `DELETE /api/v1/scheduler/jobs/{id}` | ⏸️ Pending | |
| Trigger Job | `POST /scheduler/jobs/{id}/trigger` | `POST /api/v1/scheduler/jobs/{id}/trigger` | ⏸️ Pending | |

**Frontend Files Affected:**
- `/frontend/assets/js/scheduler-management.js`

---

#### 13. Security Admin API (`/admin/security` → `/api/v1/admin/security`)

**File:** `/backend/app/routers/admin/security.py`

**Current Status:** ⏸️ Not Started

**Migration Tasks:**

| Endpoint | Old Path | New Path | Status | Notes |
|----------|----------|----------|--------|-------|
| Get Security Policies | `GET /admin/security/policies` | `GET /api/v1/admin/security/policies` | ⏸️ Pending | |
| Update Security Policies | `PUT /admin/security/policies` | `PUT /api/v1/admin/security/policies` | ⏸️ Pending | |
| List Failed Logins | `GET /admin/security/failed-logins` | `GET /api/v1/admin/security/failed-logins` | ⏸️ Pending | |
| List Active Sessions | `GET /admin/security/sessions` | `GET /api/v1/admin/security/sessions` | ⏸️ Pending | |
| Terminate Session | `DELETE /admin/security/sessions/{id}` | `DELETE /api/v1/admin/security/sessions/{id}` | ⏸️ Pending | |

**Frontend Files Affected:**
- `/frontend/assets/js/security-admin.js`

---

### Migration Implementation Pattern

**File:** `/backend/app/main.py`

```python
from fastapi import FastAPI, Response
from app.routers import (
    org, data, metadata, dashboards, reports,
    menu, rbac, audit, auth, settings, modules, scheduler
)
from app.routers.admin import security

app = FastAPI()

# ============= NEW VERSIONED APIS (RECOMMENDED) =============
app.include_router(org.router, prefix="/api/v1/org")
app.include_router(data.router, prefix="/api/v1/data")
app.include_router(metadata.router, prefix="/api/v1/metadata")
app.include_router(dashboards.router, prefix="/api/v1/dashboards")
app.include_router(reports.router, prefix="/api/v1/reports")
app.include_router(menu.router, prefix="/api/v1/menu")
app.include_router(rbac.router, prefix="/api/v1/rbac")
app.include_router(audit.router, prefix="/api/v1/audit")
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(settings.router, prefix="/api/v1/settings")
app.include_router(modules.router, prefix="/api/v1/modules")
app.include_router(scheduler.router, prefix="/api/v1/scheduler")
app.include_router(security.router, prefix="/api/v1/admin/security")

# ============= LEGACY APIS (DEPRECATED - BACKWARD COMPATIBILITY) =============
# These will be removed in Phase 3
# Add middleware to inject deprecation warnings

from starlette.middleware.base import BaseHTTPMiddleware

class DeprecationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Add deprecation warning for legacy paths
        if not request.url.path.startswith("/api/v1/"):
            deprecated_paths = [
                "/org", "/data", "/metadata", "/dashboards", "/reports",
                "/menu", "/rbac", "/audit", "/auth", "/settings",
                "/modules", "/scheduler", "/admin/security"
            ]

            for path in deprecated_paths:
                if request.url.path.startswith(path):
                    new_path = f"/api/v1{request.url.path}"
                    response.headers["Warning"] = f'299 - "Deprecated, use {new_path}"'
                    response.headers["X-Deprecated-Path"] = request.url.path
                    response.headers["X-New-Path"] = new_path
                    break

        return response

app.add_middleware(DeprecationMiddleware)

# Register legacy routes (backward compatibility)
app.include_router(org.router, prefix="/org", tags=["DEPRECATED"])
app.include_router(data.router, prefix="/data", tags=["DEPRECATED"])
app.include_router(metadata.router, prefix="/metadata", tags=["DEPRECATED"])
app.include_router(dashboards.router, prefix="/dashboards", tags=["DEPRECATED"])
app.include_router(reports.router, prefix="/reports", tags=["DEPRECATED"])
app.include_router(menu.router, prefix="/menu", tags=["DEPRECATED"])
app.include_router(rbac.router, prefix="/rbac", tags=["DEPRECATED"])
app.include_router(audit.router, prefix="/audit", tags=["DEPRECATED"])
app.include_router(auth.router, prefix="/auth", tags=["DEPRECATED"])
app.include_router(settings.router, prefix="/settings", tags=["DEPRECATED"])
app.include_router(modules.router, prefix="/modules", tags=["DEPRECATED"])
app.include_router(scheduler.router, prefix="/scheduler", tags=["DEPRECATED"])
app.include_router(security.router, prefix="/admin/security", tags=["DEPRECATED"])
```

### Deprecation Timeline

```
Phase 2 (Now - Months 1-2):
├── Add /api/v1/* paths
├── Keep legacy paths working
└── Add deprecation warnings

Phase 3 (Months 3-6):
├── Monitor usage (track old vs new)
├── Update frontend to new paths
└── Send deprecation notices to users

Phase 4 (Months 7-12):
├── Mark legacy paths as deprecated in docs
├── Return 410 Gone for legacy paths (with migration guide)
└── Plan removal date

Phase 5 (Month 13+):
└── Remove legacy paths completely
```

---

## Priority 3: Auto-Generated UI

**Status:** ✅ **COMPLETE**
**Duration:** 2 weeks
**Complexity:** Medium
**Dependencies:** ✅ Priority 1 (Runtime Data Layer) Complete

### Overview

Auto-generate complete CRUD UI for nocode entities when they are published.

### Architecture

```
EntityDefinition (published)
         ↓
Auto-Generate EntityMetadata (if not exists)
         ↓
Register Dynamic Routes
         ↓
Generate CRUD Pages
         ↓
Add to Menu System
```

### Components

#### 1. Auto-Generated Routes

**Pattern:**
```
#/dynamic/{entity_name}/list       - List view
#/dynamic/{entity_name}/create     - Create form
#/dynamic/{entity_name}/{id}       - Detail view
#/dynamic/{entity_name}/{id}/edit  - Edit form
```

#### 2. Route Registration Service

**File:** `/frontend/assets/js/dynamic-route-registry.js`

```javascript
class DynamicRouteRegistry {
  constructor() {
    this.routes = new Map();
  }

  async registerEntity(entityName) {
    // Fetch entity definition and metadata
    const [entityDef, entityMeta] = await Promise.all([
      apiFetch(`/api/v1/data-model/entities?name=${entityName}`),
      apiFetch(`/api/v1/metadata/entities/${entityName}`)
    ]);

    // Register routes
    this.routes.set(`dynamic/${entityName}/list`, () => this.renderList(entityName, entityDef, entityMeta));
    this.routes.set(`dynamic/${entityName}/create`, () => this.renderCreate(entityName, entityDef, entityMeta));
    this.routes.set(`dynamic/${entityName}/:id`, (id) => this.renderDetail(entityName, entityDef, entityMeta, id));
    this.routes.set(`dynamic/${entityName}/:id/edit`, (id) => this.renderEdit(entityName, entityDef, entityMeta, id));

    // Register in global router
    window.router.addRoutes(this.routes);
  }

  renderList(entityName, entityDef, entityMeta) {
    const container = document.getElementById('app');
    const table = new DynamicTable(container, {
      entity: entityName,
      apiEndpoint: `/api/v1/dynamic-data/${entityName}/records`,
      config: entityMeta.table_config,
      actions: {
        create: () => navigate(`#/dynamic/${entityName}/create`),
        view: (id) => navigate(`#/dynamic/${entityName}/${id}`),
        edit: (id) => navigate(`#/dynamic/${entityName}/${id}/edit`),
        delete: (id) => this.deleteRecord(entityName, id)
      }
    });
    table.render();
  }

  renderCreate(entityName, entityDef, entityMeta) {
    const container = document.getElementById('app');
    const form = new DynamicForm(container, {
      entity: entityName,
      fields: entityMeta.form_config.fields,
      onSubmit: async (data) => {
        await apiFetch(`/api/v1/dynamic-data/${entityName}/records`, {
          method: 'POST',
          body: JSON.stringify({ data })
        });
        navigate(`#/dynamic/${entityName}/list`);
      }
    });
    form.render();
  }

  // ... renderDetail, renderEdit
}
```

#### 3. Menu Auto-Registration

**When entity is published:**
```javascript
async function onEntityPublished(entityDefId) {
  const entityDef = await apiFetch(`/api/v1/data-model/entities/${entityDefId}`);

  // Create menu item
  await apiFetch('/api/v1/menu/items', {
    method: 'POST',
    body: JSON.stringify({
      code: `menu_${entityDef.name}`,
      title: entityDef.plural_label,
      icon: entityDef.icon || 'table',
      route: `#/dynamic/${entityDef.name}/list`,
      permission: `${entityDef.name}:read:tenant`,
      parent_id: null,  // Or specific parent
      order: 100,
      is_active: true
    })
  });

  // Register dynamic routes
  await dynamicRouteRegistry.registerEntity(entityDef.name);
}
```

#### 4. EntityManager Integration

Enhance existing EntityManager to work with nocode entities:

**File:** `/frontend/assets/js/entity-manager.js` (UPDATE)

```javascript
class EntityManager {
  constructor(container, entityName) {
    this.container = container;
    this.entityName = entityName;
    this.isNoCodeEntity = false;
  }

  async init() {
    // Check if this is a nocode entity
    try {
      const entityDef = await apiFetch(`/api/v1/data-model/entities?name=${this.entityName}`);
      if (entityDef) {
        this.isNoCodeEntity = true;
        this.apiBase = `/api/v1/dynamic-data/${this.entityName}`;
      } else {
        // Legacy entity (uses /data API)
        this.apiBase = `/data/${this.entityName}`;
      }
    } catch (e) {
      // Fallback to legacy
      this.apiBase = `/data/${this.entityName}`;
    }

    // Fetch metadata
    this.metadata = await apiFetch(`/api/v1/metadata/entities/${this.entityName}`);

    // Initialize table and form
    this.initTable();
    this.initForm();
  }

  initTable() {
    const endpoint = this.isNoCodeEntity
      ? `${this.apiBase}/records`
      : `${this.apiBase}/list`;

    this.table = new DynamicTable(this.container, {
      entity: this.entityName,
      apiEndpoint: endpoint,
      config: this.metadata.table_config,
      // ...
    });
  }

  // ... rest of EntityManager
}
```

---

## Priority 4: Integration Layer

**Status:** ⏸️ Not Started
**Duration:** 1-2 weeks
**Complexity:** Medium
**Dependencies:** Priority 1 (Runtime Data Layer)

### Overview

Integrate nocode entities with existing systems: Reports, Dashboards, Automations.

### 1. Report Integration

**Update:** `/frontend/components/report-designer.js`

Add nocode entities to data source dropdown:

```javascript
async function loadDataSources() {
  // Load system entities
  const systemEntities = await apiFetch('/api/v1/metadata/entities');

  // Load nocode entities (published)
  const nocodeEntities = await apiFetch('/api/v1/data-model/entities?status=published');

  const allEntities = [
    ...systemEntities.map(e => ({
      name: e.entity_name,
      label: e.display_name,
      type: 'system'
    })),
    ...nocodeEntities.map(e => ({
      name: e.name,
      label: e.label,
      type: 'nocode'
    }))
  ];

  return allEntities;
}
```

### 2. Dashboard Integration

Dashboard widgets already use reports, so once reports support nocode entities, dashboards automatically work.

### 3. Automation Integration

**Update:** `/backend/app/services/automation_service.py`

Trigger automations on nocode entity events:

```python
# In DynamicEntityService.create_record()
async def create_record(self, entity_name: str, data: Dict) -> Dict:
    # ... create record

    # Trigger automations
    await self._trigger_automations(entity_name, 'onCreate', record)

    return record

async def _trigger_automations(self, entity_name: str, event: str, record: Dict):
    """Trigger automation rules for entity event"""
    from app.services.automation_service import AutomationService

    automation_service = AutomationService(self.db, self.current_user)

    # Find matching rules
    rules = self.db.query(AutomationRule).filter(
        AutomationRule.trigger_type == 'database',
        AutomationRule.trigger_config['entity_name'].astext == entity_name,
        AutomationRule.trigger_config['event'].astext == event,
        AutomationRule.is_active == True
    ).all()

    # Execute each rule
    for rule in rules:
        await automation_service.execute_rule(rule.id, context={
            'entity': entity_name,
            'event': event,
            'record': record
        })
```

---

## Implementation Roadmap

### Week-by-Week Plan

#### **Weeks 1-2: Priority 1 - Runtime Data Layer (Part 1)**
- **Week 1:**
  - [ ] Create runtime model generator service
  - [ ] Implement field type mapping
  - [ ] Create model cache mechanism
  - [ ] Unit tests for model generation

- **Week 2:**
  - [ ] Create DynamicEntityService
  - [ ] Implement CRUD methods (create, read, update, delete)
  - [ ] Add tenant isolation
  - [ ] Add RBAC enforcement

#### **Weeks 3-4: Priority 1 - Runtime Data Layer (Part 2)**
- **Week 3:**
  - [ ] Create Dynamic Data API router
  - [ ] Implement all endpoints (CRUD + bulk)
  - [ ] Add request/response validation
  - [ ] Create Pydantic schemas

- **Week 4:**
  - [ ] Implement query builder (filters, sort, pagination)
  - [ ] Add relationship traversal
  - [ ] Implement validation engine
  - [ ] Integration tests

#### **Weeks 5-6: Priority 2 - Backend API Standardization**
- **Week 5:**
  - [ ] Add /api/v1/* routes for all APIs
  - [ ] Implement deprecation middleware
  - [ ] Keep legacy routes for backward compatibility
  - [ ] Add migration tracking document

- **Week 6:**
  - [ ] Standardize response formats
  - [ ] Add proper error handling
  - [ ] Update OpenAPI/Swagger specs
  - [ ] Create backend migration reference guide

#### **Weeks 7-8: Priority 3 - Auto-Generated UI**
- **Week 7:**
  - [ ] Create DynamicRouteRegistry service
  - [ ] Implement route registration for published entities
  - [ ] Update EntityManager for nocode entities
  - [ ] Create auto-menu registration

- **Week 8:**
  - [ ] Implement auto-generation of EntityMetadata
  - [ ] Add sync service (EntityDefinition ↔ EntityMetadata)
  - [ ] Create UI templates for CRUD pages
  - [ ] Frontend integration tests

#### **Week 9: Priority 4 - Integration Layer**
- [ ] Update Report Designer to list nocode entities
- [ ] Update Automation Service for nocode entity triggers
- [ ] Test report generation on nocode data
- [ ] Test dashboard widgets with nocode data

#### **Week 10: Testing & Documentation**
- [ ] End-to-end testing (design → publish → CRUD → report)
- [ ] Performance testing (query optimization)
- [ ] Security testing (RBAC, tenant isolation)
- [ ] Documentation (API docs, migration guides)

---

## Frontend Migration Guide

**File:** `FRONTEND-MIGRATION-GUIDE.md` (to be created)

### Migration Strategy

**Centralized Service Updates** - Update service files first, then components

#### Phase 2.1: Update API Service Files (Week 6)

1. **data-service.js**
   ```javascript
   // Before
   const endpoint = `/data/${entity}/list`;

   // After
   const endpoint = `/api/v1/data/${entity}`;  // Use GET with query params
   ```

2. **metadata-service.js**
   ```javascript
   // Before
   const endpoint = `/metadata/entities/${name}`;

   // After
   const endpoint = `/api/v1/metadata/entities/${name}`;
   ```

3. **auth.js**
   ```javascript
   // Before
   const response = await fetch('/auth/login', { ... });

   // After
   const response = await fetch('/api/v1/auth/login', { ... });
   ```

#### Phase 2.2: Update Component Files (Week 7)

Update all components that use the updated services.

#### Phase 2.3: Test & Validate (Week 8)

- Regression testing on all CRUD operations
- Test authentication flows
- Test menu navigation
- Test report/dashboard functionality

---

## Testing Strategy

### 1. Unit Tests

**Backend:**
- RuntimeModelGenerator: Model generation for all field types
- DynamicEntityService: CRUD operations
- QueryBuilder: Filter/sort/pagination logic
- ValidationEngine: Field validation rules

**Frontend:**
- DynamicRouteRegistry: Route registration
- EntityManager: Nocode entity detection
- DynamicForm: Auto-generated forms
- DynamicTable: Auto-generated tables

### 2. Integration Tests

**Backend:**
- Entity lifecycle: Design → Publish → CRUD → Delete
- Multi-tenant isolation: Verify data separation
- RBAC: Permission enforcement
- Audit trail: Verify logging

**Frontend:**
- Route navigation: All dynamic routes work
- Menu integration: Auto-generated menu items
- Form submission: Create/update records
- Table operations: List/filter/sort/pagination

### 3. End-to-End Tests

**Scenario 1: Customer Management**
1. Design "Customer" entity (name, email, phone)
2. Publish migration
3. Auto-generate UI
4. Create customer records via UI
5. View customer list with filtering
6. Edit customer record
7. Delete customer record
8. Create report on customer data
9. Add customer widget to dashboard
10. Trigger automation on customer creation

**Scenario 2: Multi-Tenant Isolation**
1. Tenant A creates "Product" entity
2. Tenant A publishes and creates products
3. Tenant B should NOT see Tenant A's products
4. Tenant B can create own "Product" entity
5. Verify complete data separation

### 4. Performance Tests

- Load test: 10,000+ records in dynamic entity
- Concurrent access: Multiple users CRUD operations
- Complex queries: Filters + sorts + relationships
- Report generation: Large dataset exports

---

## Rollback Plan

### If Priority 1 Fails (Runtime Data Layer)

**Impact:** Cannot CRUD nocode entity records

**Rollback Steps:**
1. Remove `/api/v1/dynamic-data` routes
2. Remove DynamicEntityService
3. Phase 1 features remain functional (design-only)
4. No frontend changes needed

**Mitigation:**
- Thorough testing before deployment
- Feature flag to enable/disable dynamic data API
- Gradual rollout (enable for specific tenants first)

### If Priority 2 Fails (API Standardization)

**Impact:** Inconsistent API paths

**Rollback Steps:**
1. Remove /api/v1/* aliases
2. Keep legacy paths only
3. Remove deprecation warnings
4. No breaking changes to rollback

**Mitigation:**
- Both old and new paths work simultaneously
- No breaking changes introduced
- Can rollback at any time

### If Priority 3 Fails (Auto-Generated UI)

**Impact:** No automatic UI for nocode entities

**Rollback Steps:**
1. Remove dynamic route registration
2. Remove auto-menu generation
3. Manual UI creation still possible

**Mitigation:**
- Feature flag for auto-UI generation
- Fallback to manual UI creation
- EntityManager can still be used manually

---

## Success Metrics

### Phase 2 Completion Criteria

✅ **Technical:**
1. [ ] All CRUD operations work on nocode entities
2. [ ] All legacy APIs available at `/api/v1/*`
3. [ ] Auto-generated UI for all published entities
4. [ ] Reports work on nocode entity data
5. [ ] Dashboards display nocode entity metrics
6. [ ] Automations trigger on nocode entity events

✅ **User Experience:**
1. [ ] User can create entity and use it without code
2. [ ] All CRUD pages auto-generated with good UX
3. [ ] No breaking changes to existing functionality
4. [ ] Deprecation warnings visible in browser console

✅ **Performance:**
1. [ ] CRUD operations < 200ms (avg)
2. [ ] List pages load < 500ms (avg)
3. [ ] Report generation < 3s (avg)
4. [ ] No memory leaks in model cache

✅ **Security:**
1. [ ] Tenant isolation enforced (0 data leaks)
2. [ ] RBAC permissions work correctly
3. [ ] Audit trail captures all operations
4. [ ] Input validation prevents SQL injection

---

## Related Documents

- [NO-CODE-PLATFORM-DESIGN.md](NO-CODE-PLATFORM-DESIGN.md) - High-level platform design
- [NO-CODE-PHASE1.md](NO-CODE-PHASE1.md) - Phase 1 detailed specs
- [BACKEND-API-REVIEW.md](BACKEND-API-REVIEW.md) - API review and analysis
- [API-OVERLAP-ANALYSIS.md](API-OVERLAP-ANALYSIS.md) - API overlap analysis

---

**Document Version:** 1.0
**Last Updated:** 2026-01-11
**Status:** Draft - Not Started
**Next Review:** After Phase 1 reaches 100%
