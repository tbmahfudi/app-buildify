# No-Code Platform - High-Level Design

**Date:** 2026-01-02
**Last Updated:** 2026-01-14
**Project:** App-Buildify
**Purpose:** High-level design and architecture of the No-Code Platform

---

## Executive Summary

App-Buildify is a comprehensive no-code/low-code platform that enables sysadmin and developer roles to configure entire modules from the frontend without code deployment. This document provides a high-level overview of the platform architecture, capabilities, and implementation roadmap.

**Vision:** Configure everything from the platform - if developing a new module with all needed functionality, only platform configuration is required. Backend processes are handled separately in their own modules/business services.

**Current Status (2026-01-14):**
- ✅ **Phase 1 Core Foundation:** 100% Complete
- ✅ **Phase 2 Runtime Layer:** 100% Complete
- 📋 **Phase 3+ Advanced Features:** Ready to Start

---

## Platform Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                         │
│  - Visual Designers (Data Model, Workflow, Automation)      │
│  - Page Builder (GrapeJS)                                   │
│  - Report/Dashboard Builders                                │
│  - Dynamic Forms & Tables                                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  CONFIGURATION LAYER (Phase 1 - ✅ COMPLETE)                │
│  - EntityDefinition (Schema Design)                         │
│  - WorkflowDefinition (Business Processes)                  │
│  - AutomationRule (Event Triggers)                          │
│  - LookupConfiguration (Data Sources)                       │
│  - EntityMetadata (UI Config)                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  RUNTIME LAYER (Phase 2 - ✅ COMPLETE)                      │
│  - Dynamic Data API (CRUD on nocode entities) ✅            │
│  - Query Engine (Generate SQL from metadata) ✅             │
│  - Dynamic Model Generation (Runtime SQLAlchemy) ✅         │
│  - Validation Engine ✅                                      │
│  - Auto-Generated UI (CRUD forms & tables) ✅               │
│  - Report Integration (NoCode data sources) ✅              │
│  - Automation Triggers (onCreate/onUpdate/onDelete) ✅      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  DATA LAYER                                                 │
│  - PostgreSQL (Multi-tenant with tenant_id isolation)      │
│  - Dynamic Tables (Created via migrations)                  │
│  - System Tables (Users, Roles, Permissions, Audit)        │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Metadata-Driven**: All configurations stored in database as metadata
2. **Multi-Tenant**: Complete tenant isolation with platform-level templates
3. **RBAC-Integrated**: Granular permissions across all features
4. **Event-Driven**: Automation triggers on database events
5. **API-First**: RESTful APIs for all operations
6. **Separation of Concerns**: Schema (EntityDefinition) ≠ UI (EntityMetadata)

---

## Core Capabilities

### Phase 1: Core Foundation (100% Complete)

#### 1. Data Model Designer
**Purpose:** Design database entities without backend code

**Key Features:**
- Visual entity/table creator
- 13+ field types
- Relationship designer (1:M, M:M, 1:1)
- Migration generator with preview
- Database introspection (import existing tables)
- Migration history and rollback

**Status:** ✅ Complete

#### 2. Workflow Designer
**Purpose:** Visual workflow builder for approval processes

**Key Features:**
- SVG-based visual canvas (drag-and-drop)
- State machines with 5 state types
- Approval routing (sequential, parallel, dynamic)
- Workflow simulation and testing
- Instance monitoring dashboard

**Status:** ✅ Complete

#### 3. Automation System
**Purpose:** Event-based automation without code

**Key Features:**
- 4 trigger types (database, scheduled, manual, webhook)
- Visual condition builder (AND/OR groups)
- Visual action builder (sequential steps)
- Cron expression builder
- Execution monitoring dashboard

**Status:** ✅ Complete

#### 4. Lookup Configuration
**Purpose:** Configure dropdown and reference field data sources

**Key Features:**
- 4 source types (entity, static, query, API)
- Cascading dropdowns
- Caching with TTL
- Search and autocomplete

**Status:** ✅ Complete

### Phase 2: Runtime Data Layer (100% Complete)

**Goal:** Enable runtime operations on nocode entities + system integration

#### Priority 1: Runtime Data Access Layer ✅
**Purpose:** Enable CRUD operations on nocode entities at runtime

**Implemented:**
- ✅ Dynamic SQLAlchemy model generation at runtime
- ✅ Field type mapper (20+ field types supported)
- ✅ Model cache with TTL and hash-based invalidation
- ✅ Dynamic query builder (filters, sort, search, pagination)
- ✅ Complete CRUD service (DynamicEntityService)
- ✅ REST API endpoints: `/api/v1/dynamic-data/{entity}/records`
- ✅ Tenant isolation and RBAC enforcement
- ✅ Audit logging for all operations
- ✅ Bulk operations support

**Key Components:**
- RuntimeModelGenerator - Generates SQLAlchemy models from EntityDefinition
- FieldTypeMapper - Maps field types to SQLAlchemy columns
- DynamicQueryBuilder - 12 operators, complex filters (AND/OR)
- DynamicEntityService - Complete CRUD with validation

#### Priority 2: Backend API Standardization ✅
**Purpose:** Standardize all APIs under /api/v1/* prefix

**Implemented:**
- ✅ All 13 routers updated with /api/v1 prefix
- ✅ Deprecated endpoints removed
- ✅ Frontend code migrated (100% using apiFetch)
- ✅ Migration guide created (FRONTEND-API-MIGRATION-GUIDE.md)
- ✅ Consistent API response formats

**Routers Standardized:**
auth, org, metadata, data, audit, settings, modules, rbac, reports, dashboards, scheduler, menu, admin/security

#### Priority 3: Auto-Generated UI ✅
**Purpose:** Auto-generate CRUD UI for published entities

**Implemented:**
- ✅ DynamicRouteRegistry service (680+ lines)
- ✅ Route pattern: `dynamic/{entity}/{action}` (list/create/edit/detail)
- ✅ EntityManager enhanced (nocode entity support)
- ✅ Menu auto-registration on entity publish
- ✅ "No-Code Entities" parent menu auto-created
- ✅ Router integration with app.js
- ✅ Auto-loads published entities on app init

**UI Components:**
- Uses existing DynamicTable and DynamicForm
- Seamless integration with standard entities
- Automatic metadata conversion

#### Priority 4: Integration Layer ✅
**Purpose:** Integrate nocode entities with existing systems

**Implemented:**
- ✅ Report Designer: NoCode entities in data source dropdown
- ✅ Automation Triggers: onCreate, onUpdate, onDelete events
- ✅ Dashboard support (via reports)
- ✅ Dynamic entity loading (standard + nocode)
- ✅ Graceful error handling

**Status:** ✅ Complete (See [NO-CODE-PHASE2.md](NO-CODE-PHASE2.md) for detailed documentation)

### Existing Supporting Features

#### Report & Dashboard System (Complete)
- 5-step report wizard
- Multiple export formats (PDF, Excel, CSV, JSON, HTML)
- Dashboard builder with 9 chart types
- Scheduling and caching
- Multi-page dashboards

#### Infrastructure
- RBAC System (459 permissions)
- Multi-tenancy (platform + tenant levels)
- Menu System (hierarchical with RBAC)
- Visual Page Builder (GrapeJS)
- Dynamic Forms & Tables
- Security & Audit System

---

## Data Model Architecture

### EntityDefinition (Schema Layer)
**Purpose:** Define database structure

```
EntityDefinition
├── Fields (FieldDefinition[])
│   ├── Field type, constraints, validation
│   └── Indexed, unique, required flags
├── Relationships (RelationshipDefinition[])
│   ├── One-to-Many, Many-to-Many, One-to-One
│   └── Foreign key constraints
├── Indexes (IndexDefinition[])
├── Migrations (EntityMigration[])
│   ├── Up/Down SQL scripts
│   └── Execution history
└── Status (draft, published, archived)
```

### EntityMetadata (UI Layer)
**Purpose:** Define UI behavior

```
EntityMetadata
├── table_config (JSON)
│   ├── Column visibility, order, formatting
│   └── Default filters and sort
├── form_config (JSON)
│   ├── Field layout and grouping
│   └── Validation rules and help text
└── permissions (JSON)
    └── Role-based access control
```

**Design Decision:** EntityDefinition and EntityMetadata are **intentionally separate**
- Different concerns (schema vs UI)
- Different lifecycles (migration vs instant update)
- Different permissions (DBA vs UI configurator)
- See [BACKEND-API-REVIEW.md](BACKEND-API-REVIEW.md) for detailed analysis

---

## API Architecture

### Current State

#### Standardized APIs (All under /api/v1/*)
```
/api/v1/data-model      - Data Model Designer
/api/v1/workflows       - Workflow Designer
/api/v1/automations     - Automation System
/api/v1/lookups         - Lookup Configuration
/api/v1/templates       - Template Management
/api/v1/dynamic-data    - Runtime CRUD on NoCode Entities ✅ NEW
/api/v1/org             - Organization Management ✅ MIGRATED
/api/v1/data            - Generic Data CRUD ✅ MIGRATED
/api/v1/dashboards      - Dashboard Builder ✅ MIGRATED
/api/v1/reports         - Report Builder ✅ MIGRATED
/api/v1/menu            - Menu Configuration ✅ MIGRATED
/api/v1/metadata        - Entity Metadata ✅ MIGRATED
/api/v1/rbac            - RBAC Management ✅ MIGRATED
/api/v1/audit           - Audit Logs ✅ MIGRATED
/api/v1/auth            - Authentication ✅ MIGRATED
/api/v1/settings        - Settings Management ✅ MIGRATED
/api/v1/modules         - Module System ✅ MIGRATED
/api/v1/scheduler       - Scheduler Configuration ✅ MIGRATED
```

**Status:** ✅ All APIs standardized under /api/v1/* (Phase 2 Priority 2)
- **Completed:** 13 routers updated + 1 new dynamic-data router
- **Frontend:** 100% migrated to use apiFetch() with short paths
- **Deprecated:** All legacy endpoints removed
- See [FRONTEND-API-MIGRATION-GUIDE.md](FRONTEND-API-MIGRATION-GUIDE.md) for migration details

---

## Multi-Tenancy Model

### Platform-Level Templates (tenant_id = NULL)
- **Purpose:** Shared across all tenants
- **Examples:** Generic entities (Task, Contact, Document)
- **Usage:** Tenants clone and customize

### Tenant-Level Customizations
- **Purpose:** Tenant-specific configurations
- **Isolation:** Filtered by `tenant_id` in all queries
- **Inheritance:** Can use platform templates as starting points

### Tenant Isolation Strategy
```sql
-- All queries automatically filter by tenant
SELECT * FROM entity_definitions WHERE tenant_id = :current_tenant_id;

-- Platform templates accessible to all
SELECT * FROM entity_definitions WHERE tenant_id IS NULL;
```

---

## Security Model

### RBAC System
- **Total Permissions:** 459
- **Permission Format:** `entity:action:scope`
- **Scopes:** all, tenant, company, department, own
- **Enforcement:** Router-level decorators + service-level checks

### Permission Examples
```
data-model:create:tenant    - Create entity in tenant
workflows:execute:tenant    - Execute workflows in tenant
reports:export:tenant       - Export reports in tenant
automations:read:all        - Read all automation rules
```

### Field-Level Security
- Defined in EntityMetadata.permissions
- Enforced at runtime
- Role-based visibility and editability

---

## Implementation Roadmap

### ✅ Phase 1: Core Foundation (100% Complete)

**Goal:** Enable design of entities, workflows, automations, lookups

**Priorities:**
1. Data Model Designer - ✅ Complete
2. Workflow Designer - ✅ Complete
3. Automation System - ✅ Complete
4. Lookup Configuration - ✅ Complete

**Detail:** See [NO-CODE-PHASE1.md](NO-CODE-PHASE1.md)

---

### ✅ Phase 2: Runtime Data Layer & API Standardization (100% Complete)

**Goal:** Enable runtime operations on nocode entities + system integration

**Priorities:**
1. **Runtime Data Access Layer** - ✅ Complete
   - Dynamic SQLAlchemy model generation
   - Field type mapper (20+ types)
   - Model cache with invalidation
   - Query builder (12 operators, filters, sort, search)
   - REST API: `/api/v1/dynamic-data/{entity}/records`
   - Complete CRUD service with validation
   - Tenant isolation + RBAC + audit logging

2. **Backend API Standardization** - ✅ Complete
   - All 13 routers migrated to `/api/v1/*`
   - Frontend 100% migrated (apiFetch with short paths)
   - Deprecated endpoints removed
   - Migration guide created

3. **Auto-Generated UI** - ✅ Complete
   - DynamicRouteRegistry service (680+ lines)
   - Route pattern: `dynamic/{entity}/{action}`
   - EntityManager enhanced (nocode support)
   - Menu auto-registration on publish
   - Auto-loads published entities

4. **Integration Layer** - ✅ Complete
   - Report Designer: NoCode entities support
   - Automation Triggers: onCreate/onUpdate/onDelete
   - Dashboard support (via reports)

**Achievements:**
- ✅ Can create/read/update/delete records in nocode entities
- ✅ Auto-generated CRUD UI for published entities
- ✅ Reports on nocode entity data
- ✅ Automation triggers on nocode events
- ✅ Standardized API architecture

**Implementation Stats:**
- 8 new files created (~3,500 backend lines)
- 18+ files modified (~1,500 frontend lines)
- 11 commits total
- 100% test coverage pending

**Detail:** See [NO-CODE-PHASE2.md](NO-CODE-PHASE2.md)

---

### 📋 Phase 3: Integration & Communication (Future)

**Goal:** Connect with external systems

**Features:**
- API & Integration Designer
- Email Template Designer
- Notification Configuration
- Document Template Designer

---

### 📋 Phase 4: Advanced Features (Future)

**Goal:** Power user capabilities

**Features:**
- Calculated Fields & Formula Builder
- Custom Validation Rules Designer
- Data Import/Export Templates
- Query Builder (Advanced)
- Scheduled Jobs/Batch Processes

---

### 📋 Phase 5: Administration & Customization (Future)

**Goal:** Enterprise features

**Features:**
- Record-Level Security
- Theme & Branding Designer
- Localization/Translation Management
- Audit Configuration
- Mobile App Configuration

---

## Technical Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Migrations:** Alembic (for system) + Custom (for nocode entities)
- **Auth:** JWT with RBAC
- **Validation:** Pydantic schemas

### Frontend
- **Core:** Vanilla JavaScript (ES6+)
- **UI Components:** Custom component library
- **Page Builder:** GrapeJS
- **Workflow Canvas:** Custom SVG-based
- **Charts:** Chart.js
- **Icons:** Phosphor Icons

### Infrastructure
- **Multi-tenancy:** Database-level isolation
- **Caching:** Redis (for lookups, reports)
- **Background Jobs:** Celery (for scheduled automations)
- **Storage:** S3-compatible (for attachments)

---

## Success Criteria

The platform achieves complete no-code capability when:

1. ✅ **Entity Creation** - Sysadmin can create new entities from UI (Phase 1 - Done)
2. ✅ **Business Logic** - Workflows and processes configurable from UI (Phase 1 - Done)
3. ✅ **UI Design** - Pages, forms, lists designable from UI (Existing - Done)
4. ✅ **Runtime Data** - CRUD operations on nocode entities (Phase 2 - Done)
5. ✅ **Integrations** - Report/Dashboard integration with nocode data (Phase 2 - Done)
6. ✅ **Automation** - Event triggers on nocode entities (Phase 1+2 - Done)
7. ✅ **Reporting** - Reports and dashboards buildable from UI (Existing - Done)
8. ✅ **Security** - Permissions configurable from UI (Existing - Done)
9. 📋 **Customization** - Branding, themes, localization from UI (Phase 3+ - Planned)

**Final Goal:** Develop a complete new module with full functionality using ONLY the platform's configuration UI, with backend processes handled by separate business service modules.

---

## Related Documentation

- [NO-CODE-PHASE1.md](NO-CODE-PHASE1.md) - Detailed Phase 1 design and status
- [NO-CODE-PHASE2.md](NO-CODE-PHASE2.md) - Detailed Phase 2 implementation and status ✅
- [FRONTEND-API-MIGRATION-GUIDE.md](FRONTEND-API-MIGRATION-GUIDE.md) - API migration reference for frontend
- [BACKEND-API-REVIEW.md](BACKEND-API-REVIEW.md) - API consistency review and EntityMetadata analysis
- [API-OVERLAP-ANALYSIS.md](API-OVERLAP-ANALYSIS.md) - API overlap analysis

---

**Document Version:** 3.0
**Last Updated:** 2026-01-14
**Next Review:** Phase 3 Planning (Advanced Features)
