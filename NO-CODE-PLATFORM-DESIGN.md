# No-Code Platform - High-Level Design

**Date:** 2026-01-02
**Last Updated:** 2026-01-11
**Project:** App-Buildify
**Purpose:** High-level design and architecture of the No-Code Platform

---

## Executive Summary

App-Buildify is a comprehensive no-code/low-code platform that enables sysadmin and developer roles to configure entire modules from the frontend without code deployment. This document provides a high-level overview of the platform architecture, capabilities, and implementation roadmap.

**Vision:** Configure everything from the platform - if developing a new module with all needed functionality, only platform configuration is required. Backend processes are handled separately in their own modules/business services.

**Current Status (2026-01-11):**
- ✅ **Phase 1 Core Foundation:** 100% Complete
- 🚀 **Phase 2 Runtime Layer:** Ready to Start
- 📋 **Phase 3+:** Planned

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
│  RUNTIME LAYER (Phase 2 - ⏸️ PENDING)                       │
│  - Dynamic Data API (CRUD on nocode entities)              │
│  - Query Engine (Generate SQL from metadata)               │
│  - Relationship Traversal                                   │
│  - Validation Engine                                        │
│  - Workflow Execution Engine                                │
│  - Automation Execution Engine                              │
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

### Phase 2: Runtime Data Layer (Planned)

#### Dynamic Data API
**Purpose:** Enable CRUD operations on nocode entities at runtime

**Requirements:**
- `/api/v1/dynamic-data/{entity_name}/records`
- Runtime query engine
- Relationship traversal
- Field validation
- Audit trail integration
- RBAC enforcement

**Status:** ⏸️ Pending (See [NO-CODE-PHASE1.md](NO-CODE-PHASE1.md) for details)

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

#### New APIs (Properly Versioned)
```
/api/v1/data-model      - Data Model Designer
/api/v1/workflows       - Workflow Designer
/api/v1/automations     - Automation System
/api/v1/lookups         - Lookup Configuration
/api/v1/templates       - Template Management
```

#### Legacy APIs (No Versioning)
```
/org                    - Organization (Companies, Branches, Departments, Tenants)
/data                   - Generic Data CRUD
/dashboards             - Dashboard Builder
/reports                - Report Builder
/menu                   - Menu Configuration
/metadata               - Entity Metadata
/rbac                   - RBAC Management
/audit                  - Audit Logs
/auth                   - Authentication
```

**Decision:** Keep legacy APIs for now, plan migration to `/api/v1/*` in Phase 2
- **Reason:** Too risky to break during Phase 1
- **Strategy:** Add aliases, deprecate gradually
- See [BACKEND-API-REVIEW.md](BACKEND-API-REVIEW.md) for migration plan

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

### ✅ Phase 1: Core Foundation (95% Complete)

**Goal:** Enable design of entities, workflows, automations, lookups

**Priorities:**
1. Data Model Designer - ✅ Complete
2. Workflow Designer - ✅ Complete
3. Automation System - ✅ Complete
4. Lookup Configuration - ✅ Complete

**Remaining:**
- Minor UX enhancements
- Documentation
- Testing

**Detail:** See [NO-CODE-PHASE1.md](NO-CODE-PHASE1.md)

---

### ⏸️ Phase 2: Runtime Data Layer (Planned - 3-4 weeks)

**Goal:** Enable CRUD operations on nocode entities at runtime

**Critical Missing Feature:**
- Dynamic Data API (`/api/v1/dynamic-data/{entity_name}/records`)
- Runtime query engine
- Auto-generated UI for nocode entities
- Menu auto-registration
- Report/Dashboard integration

**Blockers:**
- Cannot create/read/update/delete records in nocode entities
- Cannot generate CRUD UI
- Cannot create reports on nocode entity data

**Detail:** See "Phase 2 Requirements" in [NO-CODE-PHASE1.md](NO-CODE-PHASE1.md)

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
4. ⏸️ **Runtime Data** - CRUD operations on nocode entities (Phase 2 - Pending)
5. ⏸️ **Integrations** - External API connections configurable (Phase 3 - Pending)
6. ✅ **Automation** - Event triggers configurable from UI (Phase 1 - Done)
7. ✅ **Reporting** - Reports and dashboards buildable from UI (Existing - Done)
8. ✅ **Security** - Permissions configurable from UI (Existing - Done)
9. 📋 **Customization** - Branding, themes, localization from UI (Phase 5 - Planned)

**Final Goal:** Develop a complete new module with full functionality using ONLY the platform's configuration UI, with backend processes handled by separate business service modules.

---

## Related Documentation

- [NO-CODE-PHASE1.md](NO-CODE-PHASE1.md) - Detailed Phase 1 design and status
- [BACKEND-API-REVIEW.md](BACKEND-API-REVIEW.md) - API consistency review and EntityMetadata analysis
- [API-OVERLAP-ANALYSIS.md](API-OVERLAP-ANALYSIS.md) - API overlap analysis and Phase 2 strategy

---

**Document Version:** 2.0
**Last Updated:** 2026-01-11
**Next Review:** After Phase 2 Planning
