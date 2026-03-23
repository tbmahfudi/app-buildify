# Backend API Review & Standardization

**Date:** 2026-01-11
**Purpose:** Review all backend APIs for consistency, identify deprecated patterns, and assess EntityMetadata/EntityDefinition merge

---

## API Path Consistency Analysis

### Current State

#### ✅ **NEW APIs** (Phase 1 - Properly Versioned)
```
/api/v1/automations      - Automation System (Phase 1 Priority 3)
/api/v1/data-model       - Data Model Designer (Phase 1 Priority 1)
/api/v1/lookups          - Lookup Configuration (Phase 1 Priority 4)
/api/v1/workflows        - Workflow Designer (Phase 1 Priority 2)
/api/v1/templates        - Template Management
```

#### ⚠️ **LEGACY APIs** (No Versioning - INCONSISTENT)
```
/org                     - Organization (Companies, Branches, Departments, Tenants, Users)
/data                    - Generic Data CRUD
/dashboards              - Dashboard Builder
/reports                 - Report Builder
/menu                    - Menu Configuration
/metadata                - Entity Metadata (UI Config)
/modules                 - Module Management
/rbac                    - RBAC Management
/settings                - Settings Management
/audit                   - Audit Logs
/auth                    - Authentication
/scheduler               - Scheduler
/admin/security          - Security Admin (has prefix but not versioned)
```

#### ❌ **NO PREFIX** (Router registered without prefix)
```
(builder_pages)          - Needs verification of registration path
```

### Recommended Standardization

#### Strategy: **Gradual Migration with Backward Compatibility**

```
Phase 1 (Current): Keep both old and new
├── /api/v1/*           (New APIs - preferred)
└── Legacy paths        (Old APIs - maintain for now)

Phase 2 (Future): Add versioned aliases
├── /api/v1/*           (All new development)
├── /api/v1/org         (Alias to legacy /org)
├── /api/v1/dashboards  (Alias to legacy /dashboards)
└── Legacy paths        (Deprecated but still working)

Phase 3 (Long-term): Deprecate old paths
├── /api/v1/*           (All APIs)
└── Legacy paths        (Return 410 Gone with migration guide)
```

#### Prioritized Migration List

| Priority | Current Path | New Path | Frontend Impact | Status |
|----------|--------------|----------|-----------------|--------|
| 🔴 High | `/org` | `/api/v1/org` | Used in 5+ files | ⚠️ Active |
| 🔴 High | `/data` | `/api/v1/data` | Used by EntityManager | ⚠️ Active |
| 🟡 Medium | `/dashboards` | `/api/v1/dashboards` | Dashboard designer | ⚠️ Active |
| 🟡 Medium | `/reports` | `/api/v1/reports` | Report designer | ⚠️ Active |
| 🟡 Medium | `/menu` | `/api/v1/menu` | Menu management | ⚠️ Active |
| 🟡 Medium | `/metadata` | `/api/v1/metadata` | EntityManager | ⚠️ Active |
| 🟢 Low | `/rbac` | `/api/v1/rbac` | RBAC management | ⚠️ Active |
| 🟢 Low | `/settings` | `/api/v1/settings` | Settings UI | ⚠️ Active |
| 🟢 Low | `/audit` | `/api/v1/audit` | Audit viewer | ⚠️ Active |
| 🟢 Low | `/auth` | `/api/v1/auth` | Auth flows | ⚠️ Active |
| 🟢 Low | `/modules` | `/api/v1/modules` | Module manager | ⚠️ Active |
| 🟢 Low | `/scheduler` | `/api/v1/scheduler` | Background jobs | ⚠️ Active |
| 🟢 Low | `/admin/security` | `/api/v1/admin/security` | Security admin | ⚠️ Active |

---

## Deprecated API Patterns

### ❌ **Pattern 1: Unversioned Endpoints**

**Problem:** All legacy APIs lack version prefix, making breaking changes difficult.

**Examples:**
```
/org/companies              → Should be /api/v1/org/companies
/data/{entity}/list         → Should be /api/v1/data/{entity}/records
/dashboards                 → Should be /api/v1/dashboards
```

**Impact:**
- Cannot introduce breaking changes without breaking frontend
- No clear deprecation path
- Difficult to maintain multiple API versions

**Recommendation:**
1. ✅ **DO NOT BREAK** existing paths (too risky)
2. ✅ Add `/api/v1/*` aliases for ALL legacy endpoints
3. ✅ Update frontend gradually to use new paths
4. ✅ Add deprecation warnings to old endpoints (HTTP header: `Warning: 299 - "Deprecated, use /api/v1/..."`)

---

### ❌ **Pattern 2: Inconsistent Response Formats**

**Problem:** Different endpoints use different response structures.

**Examples:**

**Pattern A** (Old - Wrapped):
```json
// /org/companies
{
  "items": [...],
  "total": 100
}
```

**Pattern B** (New - Direct):
```json
// /api/v1/data-model/entities
[
  {...},
  {...}
]
```

**Pattern C** (Mixed):
```json
// Some endpoints return { "data": {...} }
// Some return direct objects
```

**Recommendation:**
1. ✅ Standardize on **Pattern A** for lists (items + total + pagination)
2. ✅ Standardize on direct object for single resources
3. ✅ Document response formats in OpenAPI/Swagger
4. ✅ Add response model validation with Pydantic

---

### ❌ **Pattern 3: Mixed Naming Conventions**

**Problem:** Inconsistent naming for similar operations.

**Examples:**
```
POST /data/{entity}/list          ← Uses POST for GET operation
GET  /api/v1/data-model/entities  ← Correct RESTful pattern

POST /org/companies               ← Correct
POST /data/{entity}               ← Correct
```

**Issue:** `/data/{entity}/list` uses POST when it should use GET with query params.

**Recommendation:**
1. ❌ **DO NOT FIX** `/data/{entity}/list` (breaking change)
2. ✅ Add GET alternative: `GET /data/{entity}` with query params
3. ✅ Document both, prefer GET in new code
4. ✅ Mark POST version as deprecated

---

## EntityMetadata vs EntityDefinition Analysis

### Can They Be Merged? **NO - Should NOT Merge**

#### EntityDefinition (Schema Layer)
**Purpose:** Database schema definition
**File:** `/backend/app/models/data_model.py`

```python
class EntityDefinition:
    # Identity
    id, tenant_id, name, label, plural_label

    # Schema details
    table_name, schema_name
    fields → FieldDefinition[]
    relationships → RelationshipDefinition[]
    indexes → IndexDefinition[]

    # Migration
    migrations → EntityMigration[]
    status (draft/published/archived)

    # Database properties
    primary_field, default_sort_field
    is_audited, is_versioned
    supports_soft_delete, supports_attachments
```

#### EntityMetadata (UI Layer)
**Purpose:** UI/UX configuration
**File:** `/backend/app/models/metadata.py`

```python
class EntityMetadata:
    # Identity
    id, entity_name, display_name

    # UI Configuration (JSON)
    table_config  # DynamicTable settings
    form_config   # DynamicForm settings

    # RBAC (JSON)
    permissions   # {role: [actions]}

    # System
    version, is_active, is_system
```

### Comparison Matrix

| Aspect | EntityDefinition | EntityMetadata |
|--------|------------------|----------------|
| **Layer** | Data/Schema | Presentation |
| **Purpose** | Define database structure | Define UI behavior |
| **Changes Require** | Migration (DDL) | Config update (instant) |
| **Used By** | Migration generator, SQL builder | DynamicTable, DynamicForm |
| **Lifecycle** | Long (schema stability) | Short (UI iterations) |
| **Permissions** | DBA, Schema Designer | UI Configurator, Admin |
| **Complexity** | High (relationships, constraints) | Low (simple JSON config) |
| **Versioning** | Migration-based | Version number |
| **Tenant Scope** | Platform + Tenant | Global (no tenant_id) |

### Merge Analysis

#### ❌ **Arguments AGAINST Merging:**

1. **Separation of Concerns**
   - Schema changes ≠ UI changes
   - Different stakeholders (DBA vs UI designer)
   - Different risk levels (migration vs config)

2. **Different Lifecycles**
   - EntityDefinition: Stable, requires migration
   - EntityMetadata: Fluid, instant updates

3. **Different Permissions**
   - Schema design: Restricted (data-model:create:tenant)
   - UI config: More permissive (metadata:update:tenant)

4. **System vs Tenant Scope**
   - EntityDefinition: Has tenant_id (multi-tenant entities)
   - EntityMetadata: No tenant_id (global UI config)

5. **Complexity Management**
   - EntityDefinition: Complex (fields, relationships, indexes)
   - EntityMetadata: Simple (JSON config)

#### ✅ **Arguments FOR Keeping Separate:**

1. **Single Responsibility Principle**
   - EntityDefinition: "What exists in database"
   - EntityMetadata: "How to show it to users"

2. **Independent Evolution**
   - Can change UI without schema migration
   - Can change schema without breaking UI

3. **Clear Mental Model**
   - Developers understand: Schema = EntityDefinition
   - Designers understand: UI = EntityMetadata

### Recommendation: **KEEP SEPARATE, BUT LINK**

Instead of merging, **improve integration**:

#### 1. Auto-Generate EntityMetadata from EntityDefinition

When a new EntityDefinition is published:
```python
def auto_create_metadata(entity_def: EntityDefinition):
    """Auto-generate EntityMetadata with sensible defaults"""

    # Auto table config from fields
    table_config = {
        "columns": [
            {
                "field": field.name,
                "label": field.label,
                "type": field.field_type,
                "sortable": True,
                "filterable": True
            }
            for field in entity_def.fields
            if not field.is_system
        ],
        "default_sort": entity_def.default_sort_field or "created_at",
        "default_page_size": 25
    }

    # Auto form config from fields
    form_config = {
        "fields": [
            {
                "name": field.name,
                "label": field.label,
                "type": field.field_type,
                "required": field.is_required,
                "help_text": field.help_text,
                "validation": field.validation_rules
            }
            for field in entity_def.fields
            if not field.is_system
        ],
        "layout": "single_column"
    }

    # Create metadata
    metadata = EntityMetadata(
        entity_name=entity_def.name,
        display_name=entity_def.label,
        description=entity_def.description,
        icon=entity_def.icon,
        table_config=json.dumps(table_config),
        form_config=json.dumps(form_config),
        permissions={},  # Inherit from entity RBAC
        is_system=False,
        is_active=True
    )

    return metadata
```

#### 2. Add Reference Link

```python
class EntityMetadata:
    # Add new field
    entity_definition_id = Column(GUID, ForeignKey('entity_definitions.id'))
    entity_definition = relationship('EntityDefinition')
```

#### 3. Sync Service

```python
class MetadataSync:
    def sync_from_definition(self, entity_def_id: UUID):
        """Update EntityMetadata when EntityDefinition changes"""
        entity_def = get_entity_definition(entity_def_id)
        metadata = get_or_create_metadata(entity_def.name)

        # Update fields in table_config if they exist in entity_def
        # Add new fields, mark removed fields as hidden
        # Keep user customizations (column order, labels, etc.)
```

#### 4. API Enhancement

```
GET /api/v1/entities/{name}/full
Response:
{
  "definition": { /* EntityDefinition */ },
  "metadata": { /* EntityMetadata */ },
  "stats": { /* Record counts, last modified, etc. */ }
}
```

---

## Frontend API Usage Audit

### Active Legacy API Usage

#### `/org` API - **HEAVILY USED**

**Files:**
- `/frontend/assets/js/companies.js` (5 calls)
- `/frontend/assets/js/tenants.js` (7 calls)
- `/frontend/assets/js/organization-hierarchy.js` (11 calls)

**Endpoints:**
```javascript
GET    /org/companies
GET    /org/companies/{id}
POST   /org/companies
PUT    /org/companies/{id}
DELETE /org/companies/{id}
GET    /org/branches
GET    /org/departments
GET    /org/tenants
POST   /org/tenants
PUT    /org/tenants/{id}
DELETE /org/tenants/{id}
GET    /org/users
```

**Migration Effort:** 🔴 High (23+ call sites)

#### `/data` API - **USED BY ENTITY MANAGER**

**Files:**
- `/frontend/assets/js/data-service.js`
- `/frontend/assets/js/entity-manager.js`

**Endpoints:**
```javascript
POST   /data/{entity}/list
GET    /data/{entity}/{id}
POST   /data/{entity}
PUT    /data/{entity}/{id}
DELETE /data/{entity}/{id}
POST   /data/{entity}/bulk
```

**Migration Effort:** 🟡 Medium (centralized in data-service)

#### `/metadata` API - **USED BY DYNAMIC COMPONENTS**

**Files:**
- `/frontend/assets/js/metadata-service.js`
- `/frontend/assets/js/entity-manager.js`
- `/frontend/assets/js/dynamic-table.js`
- `/frontend/assets/js/dynamic-form.js`

**Endpoints:**
```javascript
GET    /metadata/entities
GET    /metadata/entities/{name}
POST   /metadata/entities
PUT    /metadata/entities/{name}
DELETE /metadata/entities/{name}
```

**Migration Effort:** 🟡 Medium (centralized in metadata-service)

---

## Recommendations

### Immediate Actions (Phase 1 Focus)

1. ✅ **KEEP EntityMetadata and EntityDefinition separate**
   - They serve different purposes
   - Merging would violate SRP
   - Integration > Merge

2. ✅ **DO NOT break legacy APIs**
   - Too risky during Phase 1
   - Focus on Phase 1 features first
   - Plan migration for Phase 2

3. ✅ **Add auto-generation for EntityMetadata**
   - When EntityDefinition is published, auto-create EntityMetadata
   - Improves UX for Phase 1

4. ✅ **Document current state**
   - API patterns
   - Response formats
   - Migration path

### Phase 2 Actions (After Phase 1 Complete)

1. 🔄 **Add versioned aliases**
   ```python
   # In main.py
   app.include_router(org_router, prefix="/api/v1/org")  # New
   app.include_router(org_router, prefix="/org")          # Legacy
   ```

2. 🔄 **Add deprecation warnings**
   ```python
   @router.get("/companies")  # Legacy path
   async def list_companies(response: Response, ...):
       response.headers["Warning"] = '299 - "Deprecated, use /api/v1/org/companies"'
       # ... existing code
   ```

3. 🔄 **Update frontend gradually**
   - Update service files first (data-service.js, metadata-service.js)
   - Test thoroughly
   - Update component files
   - Remove old imports

4. 🔄 **Create migration guide**
   - Document all changes
   - Provide examples
   - Test backward compatibility

### Long-term (Phase 3+)

1. 📅 **Deprecate old paths** (after 6+ months)
2. 📅 **Remove old paths** (after 12+ months)
3. 📅 **Consolidate documentation**

---

## Decision Matrix

| Decision | Status | Rationale |
|----------|--------|-----------|
| Keep EntityDefinition & EntityMetadata separate | ✅ APPROVED | Different concerns, lifecycles, permissions |
| Add auto-generation of EntityMetadata | ✅ RECOMMENDED | Improves Phase 1 UX |
| Migrate legacy APIs to /api/v1/* | ⏸️ DEFERRED | Focus on Phase 1 first |
| Add deprecation warnings | ⏸️ DEFERRED | After Phase 1 complete |
| Break existing API contracts | ❌ REJECTED | Too risky, no business value |

---

## Summary

**EntityMetadata ≠ EntityDefinition**
- **Keep separate** - They serve different layers
- **Add integration** - Auto-generate, link, sync

**API Versioning**
- **Current:** Mixed (v1 for new, unversioned for old)
- **Short-term:** Keep both patterns
- **Long-term:** Migrate to /api/v1/* for all

**Legacy API Migration**
- **Status:** Deferred to Phase 2
- **Reason:** Phase 1 features are priority
- **Strategy:** Alias, warn, migrate, deprecate, remove

**No Deprecated APIs to Remove Yet**
- All "legacy" APIs are **actively used** by frontend
- **DO NOT** remove or break them
- Plan gradual migration instead

---

**Next Steps:**
1. ✅ Implement auto-generation of EntityMetadata in Phase 1
2. ✅ Document current API patterns
3. ✅ Complete Phase 1 features
4. ⏸️ Plan API migration for Phase 2
