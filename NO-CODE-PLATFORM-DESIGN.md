# No-Code Platform - High-Level Design

**Date:** 2026-01-02
**Last Updated:** 2026-01-23
**Project:** App-Buildify
**Purpose:** High-level design and architecture of the No-Code Platform

---

## Executive Summary

App-Buildify is a comprehensive no-code/low-code platform that enables sysadmin and developer roles to configure entire modules from the frontend without code deployment. This document provides a high-level overview of the platform architecture, capabilities, and implementation roadmap.

**Vision:** Configure everything from the platform - if developing a new module with all needed functionality, only platform configuration is required. Backend processes are handled separately in their own modules/business services.

**Current Status (2026-01-23):**
- ✅ **Phase 1 Core Foundation:** 100% Complete
- ✅ **Phase 2 Runtime Layer:** 100% Complete
- ✅ **Phase 3 Visual Designer Enhancement:** 100% Complete
  - ✅ Priority 1: Menu Consolidation & Designer Activation
  - ✅ Priority 2: Visual Report Designer Enhancement
  - ✅ Priority 3: Visual Dashboard Designer Enhancement
  - 📋 Priority 4: Developer Tools Enhancement (Documentation Only)
- 🎯 **Phase 4 Module System Foundation:** In Progress (2026-01-19)
  - 📋 Priority 1: Module Definition & Registry
  - 📋 Priority 2: Cross-Module Access (Service Layer)
  - 📋 Priority 3: Extension Framework
- 🔥 **Phase 5 Field-Level Features (Quick Wins):** In Progress (2026-01-23)
  - ✅ Select & Reference field types with FK constraints
  - 🎯 Priority 1: Calculated Fields & Validation Rules (Week 1)
  - 📋 Priority 2: Advanced Input Types & Lookup Enhancements (Week 2)
  - 📋 Priority 3: Conditional Visibility & Field Groups (Week 3-4)
- 📋 **Phase 6-7 Advanced Features:** Future Planning

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

### 🔄 Phase 3: Visual Designer Enhancement & Menu Consolidation (Priority 3 Completed)

**Goal:** Consolidate No-Code Platform menu, enable visual designers, and enhance user experience

**Status:** Priority 3 Completed (2026-01-18)
- ✅ Priority 1: Menu Consolidation & Designer Activation
- ✅ Priority 2: Visual Report Designer Enhancement
- ✅ Priority 3: Visual Dashboard Designer Enhancement
- 📋 Priority 4: Developer Tools Enhancement (Documentation Only)

**Priorities:**

#### Priority 1: Menu Consolidation & Designer Activation (1-2 weeks)
**Goal:** Reorganize menu structure and enable existing but inaccessible designers

**Sub-Tasks:**
1. **Menu Restructuring** - Consolidate all no-code tools under unified menu
   - Move UI Builder (Page Designer, Manage Pages) to No-Code Platform
   - Move System Management tools (Menu Management, Menu Sync, Module Management) to No-Code Platform
   - Create logical groupings: Data & Schema, UI & Pages, Reports & Dashboards, Business Logic, Platform Configuration
   - Update menu.json with new hierarchical structure
   - Update i18n translations

2. **Enable Report & Dashboard Designers** - Critical: Unlock existing 1,552 lines of code
   - Register routes in app.js (report-designer, dashboard-designer)
   - Create Reports List page (reports-list.html, reports-list-page.js)
   - Create Dashboards List page (dashboards-list.html, dashboards-list-page.js)
   - Add menu items to No-Code Platform menu
   - Test existing designer functionality (843 lines report, 709 lines dashboard)

3. **Menu Sync UI Implementation** - Complete the menu management workflow
   - Replace placeholder UI with functional interface
   - Add sync configuration options (clear existing checkbox)
   - Implement sync trigger with confirmation
   - Add sync history display
   - Create JavaScript handler (settings-menu-sync-page.js)

4. **Cross-Feature Quick Actions** - Improve workflow efficiency
   - Add "Create Report on this Entity" button in Data Model Designer
   - Add "Create Page for this Entity" button in Data Model Designer
   - Add "Add to Dashboard" button in Report Designer
   - Add "Add to Menu" button in Page Designer and Dashboard Designer
   - Add "Create Automation for this Report" button in Report Designer

**Deliverables:**
- ✅ Unified No-Code Platform menu with logical groupings
- ✅ Report & Dashboard designers accessible from menu
- ✅ Functional Menu Sync UI
- ✅ Quick action buttons for improved workflows
- ✅ Updated documentation and user guides

---

#### Priority 2: Visual Report Designer Enhancement (3-4 weeks)
**Goal:** Transform text-based report configuration into fully visual experience

**Current State:**
- ✅ 5-step wizard (Data Source, Columns, Parameters, Formatting, Preview)
- ✅ NoCode entity support
- ✅ Export formats (PDF, Excel, CSV, JSON, HTML)
- ✅ Scheduling and caching
- ❌ Text-based configuration (dropdowns and forms)

**Enhancement Tasks:**

1. **Visual Data Source Builder** (Week 1)
   - Replace dropdown with entity relationship diagram
   - Show entity relationships graphically (using D3.js or Cytoscape.js)
   - Drag-and-drop to add entity joins
   - Visual filter builder (similar to Automation Rules)
   - Preview data sample (top 10 rows)

2. **Drag-and-Drop Column Designer** (Week 1)
   - Left panel: Entity schema with available fields
   - Center panel: Selected columns with drag-to-reorder
   - Right panel: Column properties (formatting, aggregation, alias)
   - Visual format preview for each column
   - Quick actions: Add all fields, Clear all, Group by entity

3. **Visual Chart Builder** (Week 2)
   - Chart type selector with thumbnails and previews
   - Drag fields to axis configuration (X-axis, Y-axis, Series, Filters)
   - Color scheme designer with preset palettes
   - Visual chart customization (titles, legends, tooltips)
   - Live chart preview with sample data
   - Support for all 9 chart types (Bar, Line, Pie, Donut, Area, Scatter, Radar, Polar, Bubble)

4. **Split-Pane Live Preview** (Week 2)
   - Left pane: Configuration wizard
   - Right pane: Live data preview
   - Toggle between table view and chart view
   - Auto-refresh on configuration changes
   - Performance metrics (query time, row count)

5. **Enhanced Parameter UI** (Week 3)
   - Visual parameter builder
   - Input type selector with previews (text, number, date, dropdown, checkbox)
   - Default value configuration
   - Dependency rules (cascading parameters)
   - Test parameter values in preview

6. **Template Library** (Week 3-4)
   - Pre-built report templates (Sales Report, Inventory Report, Customer Analytics, etc.)
   - Template preview with screenshots
   - Clone and customize templates
   - Save custom templates for reuse

**Deliverables:**
- ✅ Fully visual report designer with drag-and-drop
- ✅ Live preview with auto-refresh
- ✅ Template library with 10+ templates
- ✅ Enhanced user experience (50% faster report creation)

---

#### Priority 3: Visual Dashboard Designer Enhancement (3-4 weeks)
**Goal:** Transform form-based dashboard configuration into drag-and-drop canvas

**Status:** ✅ **COMPLETED** (2026-01-18)

**Implementation Summary:**
- ✅ Visual Dashboard Canvas with GridStack.js (~500 lines)
- ✅ Widget Library Palette with 26 widget types (~850 lines)
- ✅ Live Dashboard Preview (~500 lines)
- ✅ Enhanced Widget Configuration (~800 lines)
- ✅ Dashboard Template Library (~400 lines)
- ✅ Interactive Features (~600 lines)
- ✅ Dashboard Designer Page Template (~250 lines)
- ✅ Menu restructure with nested submenus
- **Total:** ~3,900 lines of code

**Current State:**
- ✅ 4-step wizard (Details, Pages, Widgets, Preview)
- ✅ Widget types (9 chart types + metrics)
- ✅ Theme support
- ✅ Multi-page dashboards
- ✅ Drag-and-drop visual canvas with GridStack.js
- ✅ 26 widget types across 6 categories
- ✅ Multi-device preview (Desktop, Tablet, Mobile)
- ✅ Visual widget configuration
- ✅ 5 pre-built dashboard templates
- ✅ Interactive features (drill-down, cross-filtering)
- ✅ Export functionality (PDF, PNG, HTML, Excel)

**Enhancement Tasks (All Completed):**

1. **Visual Layout Canvas (GrapeJS-style)** (Week 1-2)
   - Grid-based layout with snap-to-grid (12-column responsive grid)
   - Drag widgets from left palette to canvas
   - Visual resize handles (drag corners/edges)
   - Widget positioning with pixel-perfect placement
   - Copy/paste/duplicate widgets
   - Undo/redo support
   - Grid guidelines and alignment helpers

2. **Widget Library with Visual Previews** (Week 2)
   - Categorized palette with thumbnails:
     - 📊 **Charts:** Bar, Line, Pie, Donut, Area, Scatter, Radar, Polar, Bubble
     - 📈 **Metrics:** KPI Card, Gauge, Progress Bar, Stat Card, Number Counter
     - 📋 **Tables:** Data Grid, Summary Table, Pivot Table
     - 📝 **Text:** Header (H1-H6), Paragraph, Rich Text Editor
     - 🖼️ **Media:** Image, Video, Iframe Embed
     - 🔗 **Actions:** Button, Link, Dropdown Menu, Filter Panel
   - Live preview on hover
   - Drag to add to canvas
   - Widget search and favorites

3. **Live Dashboard Preview** (Week 2-3)
   - Multi-device preview modes:
     - 💻 Desktop (1920x1080, 1366x768)
     - 📱 Tablet (768x1024, 1024x768)
     - 📱 Mobile (375x812, 414x896)
   - Theme switcher (Light/Dark/Custom)
   - Live data toggle (Real data vs Mock data)
   - Performance metrics overlay (load time, API calls)
   - Refresh rate configuration
   - Auto-save with version history

4. **Enhanced Widget Configuration** (Week 3)
   - Visual report selector with search/filter/preview
   - Chart type visual picker with previews
   - Color scheme designer:
     - Preset palettes (Material, Tailwind, Bootstrap, Custom)
     - Color picker for custom colors
     - Gradient support
   - Visual spacing editor (padding, margin with visual preview)
   - Border and shadow designer
   - Conditional formatting rules

5. **Dashboard Templates** (Week 4)
   - Pre-built dashboard templates:
     - Executive Dashboard (KPIs, trends, top metrics)
     - Sales Dashboard (revenue, pipeline, conversion)
     - Operations Dashboard (capacity, efficiency, alerts)
     - Analytics Dashboard (user behavior, traffic, engagement)
     - Financial Dashboard (P&L, cash flow, budget vs actual)
   - Template gallery with screenshots and descriptions
   - Clone and customize templates
   - Save custom templates

6. **Interactive Features** (Week 4)
   - Widget drill-down (click chart to see details)
   - Widget filtering (click to filter other widgets)
   - Cross-widget communication
   - Real-time data refresh
   - Export dashboard (PDF, Image, Interactive HTML)

**Deliverables:**
- ✅ Fully visual drag-and-drop dashboard canvas
- ✅ Widget library with 30+ widget types
- ✅ Multi-device preview with live data
- ✅ Template library with 5+ dashboard templates
- ✅ Enhanced user experience (60% faster dashboard creation)

---

#### Priority 4: Developer Tools Enhancement (2-3 weeks)
**Goal:** Define and document features for Schema Designer, API Playground, and Code Generator

**Note:** Implementation decision pending - currently defining features only

**Feature Definitions:**

1. **Schema Designer**
   - **Purpose:** Visual database schema viewer and lightweight editor
   - **Target Users:** Developers, Database Admins, System Architects
   - **Key Features:**
     - Visual ER diagram of entire database schema
     - Interactive node-based graph (entities as nodes, relationships as edges)
     - Zoom, pan, filter by schema/table
     - Click entity to view details (columns, indexes, constraints, relationships)
     - Read-only view of system tables
     - Export schema as image (PNG, SVG) or documentation (PDF, Markdown)
     - Compare schemas across tenants or environments
     - Integration with Data Model Designer (open entity in designer)
   - **Implementation Approach:**
     - Use existing Data Model Designer metadata
     - Add read-only visualization layer
     - Leverage D3.js or Cytoscape.js for graph rendering
   - **Estimated Effort:** 2-3 weeks
   - **Dependencies:** Data Model Designer (already complete)

2. **API Playground**
   - **Purpose:** Interactive API testing and documentation tool (Swagger/Postman alternative)
   - **Target Users:** Developers, Integration Engineers, QA Testers
   - **Key Features:**
     - Auto-generated API documentation from OpenAPI spec
     - Interactive request builder (method, headers, body, query params)
     - Authentication handling (JWT token injection)
     - Request history and favorites
     - Response viewer with syntax highlighting (JSON, XML, HTML)
     - Code snippet generator (Python, JavaScript, cURL, PHP)
     - Test collection builder (save and replay API sequences)
     - Environment variables (dev, staging, production)
     - Mock server for testing frontend before backend ready
     - WebSocket support for real-time APIs
   - **Implementation Approach:**
     - Build on top of existing FastAPI OpenAPI spec
     - Integrate with authentication system
     - Use Monaco Editor for request/response editing
   - **Estimated Effort:** 3-4 weeks
   - **Dependencies:** OpenAPI spec generation, Auth system

3. **Code Generator**
   - **Purpose:** Generate boilerplate code from NoCode entity definitions
   - **Target Users:** Developers extending the platform
   - **Key Features:**
     - Generate SQLAlchemy models from EntityDefinition
     - Generate Pydantic schemas (request/response)
     - Generate FastAPI CRUD endpoints
     - Generate frontend forms and tables (HTML + JS)
     - Generate test cases (pytest, jest)
     - Generate API documentation (Markdown)
     - Template customization (modify code templates)
     - Preview generated code before download
     - Export as ZIP or Git repository
     - Support for multiple languages/frameworks:
       - Backend: Python (FastAPI), Node.js (Express), Java (Spring Boot)
       - Frontend: React, Vue.js, Vanilla JS
   - **Implementation Approach:**
     - Template engine (Jinja2) for code generation
     - Read from EntityDefinition and EntityMetadata
     - Modular generator architecture (separate generators per artifact type)
   - **Estimated Effort:** 4-6 weeks
   - **Dependencies:** Data Model Designer, Entity Metadata

**Deliverables:**
- ✅ Feature specification documents for Schema Designer
- ✅ Feature specification documents for API Playground
- ✅ Feature specification documents for Code Generator
- ✅ Architecture diagrams and technical designs
- ✅ Effort estimation and resource planning
- ⏸️ Implementation decision: To be determined by stakeholders

---

**Phase 3 Summary:**

**Duration:** 8-12 weeks (depending on priorities selected)

**Quick Wins (Priority 1):** 1-2 weeks
- Menu consolidation
- Enable existing designers
- Menu Sync UI
- Cross-feature quick actions

**Major Enhancements (Priority 2-3):** 6-8 weeks
- Visual Report Designer
- Visual Dashboard Designer

**Documentation (Priority 4):** 2-3 weeks
- Feature specifications for future tools

**Total Effort:**
- Minimum viable (Priority 1 only): 1-2 weeks
- Recommended (Priority 1-2): 4-6 weeks
- Complete (Priority 1-3): 8-10 weeks
- Full scope (Priority 1-4): 10-12 weeks

**Success Metrics:**
- ✅ All no-code tools accessible from unified menu
- ✅ Report/Dashboard designers available to all users
- ✅ 50% reduction in report creation time (with visual enhancements)
- ✅ 60% reduction in dashboard creation time (with visual enhancements)
- ✅ Positive user feedback (>4.5/5 rating)
- ✅ Increased platform adoption (>80% of users create custom reports/dashboards)

**Detail:** See [NO-CODE-PHASE3.md](NO-CODE-PHASE3.md) (to be created when phase starts)

---

### 🎯 Phase 4: Module System Foundation (In Progress - 2026-01-19)

**Goal:** Build infrastructure for modular no-code development with cross-module capabilities

**Status:** In Progress (started 2026-01-19)

**Priorities:**

#### Priority 1: Module Definition & Registry (Week 1-2)
**Purpose:** Core module infrastructure with semantic versioning and dependency management

**Features:**
1. **Module Metadata Model**
   - Module definition table with versioning
   - Semantic versioning (MAJOR.MINOR.PATCH)
   - Dependency declaration (required, optional, conflicts)
   - Table naming convention: `{prefix}_{entity}` (max 10 char prefix, no underscore in prefix)
   - Organization hierarchy support (always include branch_id)

2. **Module Registry Service**
   - Register/unregister modules
   - Dependency resolver (version compatibility checking)
   - Module lifecycle management (draft, active, deprecated)
   - Module metadata API endpoints

3. **Database Schema**
   - nocode_modules table
   - module_dependencies table
   - module_versions table (version history)
   - Add module_id FK to all no-code component tables

**Deliverables:**
- Module registry database schema
- Module API endpoints (`/api/v1/nocode-modules/*`)
- Dependency resolver service
- Module creation wizard UI

---

#### Priority 2: Cross-Module Access (Week 2-3)
**Purpose:** Enable modules to safely access data and services from other modules

**Features:**
1. **Service Layer Architecture**
   - Service registration (modules export typed services)
   - Service discovery (find available services)
   - Service versioning (API compatibility)

2. **Permission Delegation**
   - Cross-module permission checks
   - Service-level RBAC enforcement
   - Audit logging for cross-module access

3. **Data Access Patterns**
   - Backend: Service layer calls (recommended)
   - Frontend: Direct API calls to `/dynamic-data/*`
   - No direct database access across modules

**Deliverables:**
- Service registry system
- Cross-module access examples
- Permission delegation framework
- Developer documentation

---

#### Priority 3: Extension Framework (Week 3-4)
**Purpose:** Allow modules to extend other modules' entities, screens, and menus

**Features:**
1. **Entity Extensions**
   - Add custom fields to existing entities
   - Extension tables: `{extending_prefix}_{target_prefix}_{target_entity}_ext`
   - Auto-join extensions when loading entities
   - Example: `payroll_hr_employees_ext` extends `hr_employees`

2. **Screen Extensions**
   - Add tabs to existing entity screens
   - Add sections to existing forms
   - Extension point registration
   - Dynamic UI composition

3. **Menu Extensions**
   - Add menu items under other modules' menus
   - Context-aware menu items
   - Permission-based visibility

**Deliverables:**
- Entity extension system
- Screen extension framework
- Menu extension API
- Extension registry UI
- Example implementations

**Total Effort:** 3-4 weeks

**Detail:** See [NO-CODE-PHASE4.md](NO-CODE-PHASE4.md)

---

### 🔥 Phase 5: Field-Level Features & Enhancements (In Progress - 2026-01-23)

**Goal:** Advanced field-level capabilities leveraging existing backend infrastructure

**Status:** Priority 1 In Progress (2026-01-23)

**Key Discovery:** Backend models already support many advanced features - columns exist but frontend implementation missing!

**Backend Readiness Assessment:**
- ✅ `is_calculated` + `calculation_formula` columns exist (data_model.py:158-159)
- ✅ `validation_rules` JSONB column exists (data_model.py:151)
- ✅ `prefix` + `suffix` columns exist (data_model.py:164-165)
- ✅ `input_type` column exists (data_model.py:162)
- ✅ `allowed_values` JSONB column exists (data_model.py:152)
- ✅ Select & Reference field types added (2026-01-23)
- ✅ FK constraint behavior (`on_delete`, `on_update`) added (2026-01-23)

---

#### Priority 1: Quick Wins (Week 1 - 2026-01-23)
**Goal:** Unlock existing backend capabilities with minimal frontend work

**Sub-Tasks:**

1. **✅ Select & Reference Field Types** (Completed 2026-01-23)
   - Added `select` and `reference` to field type dropdown
   - Reference field configuration UI (entity selector, FK constraints)
   - Select options configuration UI (multi-line textarea)
   - Frontend: 224 lines added/modified
   - Backend: Migration for `on_delete`/`on_update` columns
   - **Status:** ✅ Complete, Committed, Pushed

2. **🎯 Calculated/Formula Fields** (Day 1-2)
   - Expression evaluator in dynamic-form.js
   - Support arithmetic: `+`, `-`, `*`, `/`, `%`
   - Support functions: `SUM()`, `AVG()`, `MIN()`, `MAX()`, `COUNT()`
   - Support conditionals: `IF(condition, true_value, false_value)`
   - Field dependency tracking
   - Auto-recalculate on dependency change
   - Read-only display for calculated fields
   - **Backend:** ✅ Ready (columns exist)
   - **Frontend:** ❌ Need implementation
   - **Effort:** 1-2 days

3. **🎯 Field Validation Rules** (Day 2-3)
   - Validation executor in dynamic-form.js
   - Support validation types:
     - `regex`: Pattern matching
     - `min_length` / `max_length`: String length
     - `min_value` / `max_value`: Numeric range
     - `custom`: JavaScript expression
     - `email`, `url`, `phone`: Format validation
   - Real-time validation on blur/change
   - Custom error messages
   - Cross-field validation support
   - **Backend:** ✅ Ready (validation_rules column exists)
   - **Frontend:** ❌ Need implementation
   - **Effort:** 1-2 days

4. **🎯 Prefix/Suffix Support** (Day 4)
   - Render prefix/suffix in FlexInput component
   - Visual styling (prepend/append to input)
   - Examples: `$` for currency, `%` for percentage, `kg` for weight
   - **Backend:** ✅ Ready (prefix/suffix columns exist)
   - **Frontend:** ❌ Need implementation
   - **Effort:** 0.5 day

**Deliverables:**
- ✅ Select & Reference field types working
- 🎯 Formula engine for calculated fields
- 🎯 Validation engine for field rules
- 🎯 Prefix/Suffix rendering in forms
- 🎯 Updated dynamic-form.js with new capabilities
- 🎯 Documentation and examples

**Total Effort:** 4-5 days

---

#### Priority 2: Advanced Input Types & Lookup Enhancements (Week 2)
**Goal:** Rich UI controls and improved reference field UX

**Features:**

1. **Advanced Input Types**
   - `color`: Color picker (native `<input type="color">`)
   - `rating`: Star rating component (1-5 stars)
   - `currency`: Number input with currency symbol
   - `percentage`: Number input with % symbol
   - `slider`: Range slider for numeric values
   - `rich-text`: WYSIWYG editor (TinyMCE/Quill)
   - `code-editor`: Syntax highlighting (Monaco/CodeMirror)
   - `tags`: Multi-tag input component
   - `autocomplete`: Search-as-you-type
   - Leverage existing `input_type` column

2. **Lookup/Reference Field Enhancements**
   - Replace dropdown with autocomplete (search-as-you-type)
   - Quick-create button (add new record inline)
   - Display template support (e.g., "{name} ({email})")
   - Filtered lookups based on other field values
   - Multi-column display in dropdown
   - Recent/favorites in lookup
   - Backend: Add `lookup_display_template`, `lookup_filter_field` columns

**Total Effort:** 3-4 days

---

#### Priority 3: Conditional Visibility & Field Groups (Week 3-4)
**Goal:** Dynamic forms with conditional logic and organization

**Features:**

1. **Conditional Field Visibility**
   - Show/hide fields based on other field values
   - Visibility rules: `{"field": "status", "operator": "equals", "value": "active"}`
   - Support operators: equals, not_equals, contains, in, greater_than, less_than
   - AND/OR rule groups
   - Real-time visibility updates
   - Backend: Add `visibility_rules` JSONB column

2. **Field Groups & Sections**
   - Organize fields into collapsible sections
   - Visual section headers with icons
   - Tab-based layouts
   - Accordion-style sections
   - Backend: New `FieldGroup` model
   - Frontend: Enhanced form renderer

3. **Field Dependencies (Cascading)**
   - Auto-populate fields based on other fields
   - Cascading dropdowns (Country → State → City)
   - Dynamic option filtering
   - Backend: Add `depends_on_field`, `filter_expression` columns

**Total Effort:** 4-6 days

---

#### Priority 4: Multi-language Support (Week 4)
**Goal:** Internationalization for global applications

**Features:**

1. **Field Label Translations**
   - Backend: Add `label_i18n`, `help_text_i18n`, `placeholder_i18n` JSONB columns
   - Store translations: `{"en": "Name", "es": "Nombre", "fr": "Nom"}`
   - Frontend: Locale selector and dynamic label rendering
   - Fallback to default language

2. **Data Translations**
   - Translatable text fields
   - Language switcher in forms
   - Multi-language data storage

**Total Effort:** 3-5 days

---

#### Future Enhancements (Phase 5B)

**Workflow Enhancements**
- Conditional branching (if/then/else)
- Loop support (foreach, while)
- Sub-workflows (call other workflows)
- Error handling and retry logic

**Automation Enhancements**
- Event chaining (trigger cascades)
- Advanced retry policies
- Complex nested conditions (already supported)
- Action templates library

**UI/UX Enhancements**
- Multi-step forms with progress indicators
- Inline editing in data tables
- Bulk edit operations
- Custom form templates

**Report/Dashboard Enhancements**
- Drill-through reports (click to detail)
- Cross-tab/pivot reports
- Scheduled email delivery
- Custom SQL query builder

---

**Phase 5 Summary:**

**Total Duration:** 3-4 weeks (Priorities 1-4)

**Week 1:** Quick Wins (Calculated, Validation, Prefix/Suffix)
**Week 2:** Advanced Input Types & Lookup Enhancements
**Week 3-4:** Conditional Visibility, Field Groups, Multi-language

**Success Metrics:**
- ✅ Backend columns fully utilized (no unused infrastructure)
- 🎯 Users can create calculated fields (e.g., `total = quantity * price`)
- 🎯 Users can add validation rules (e.g., email format, min/max)
- 🎯 Rich input controls available (color picker, rating, rich-text)
- 🎯 Reference fields have autocomplete and quick-create
- 🎯 Forms support conditional visibility and sections
- 🎯 Multi-language support for global apps

**Detail:** See [NO-CODE-PHASE5.md](NO-CODE-PHASE5.md) (to be created)

---

### 📋 Phase 6: Module Packaging & Deployment (Future)

**Goal:** Enable environment promotion and module distribution

**Features:**

1. **Module Export**
   - Bundle all module components (entities, workflows, automations, reports, etc.)
   - Include database migrations
   - Dependency validation
   - Export as ZIP package

2. **Module Import**
   - Parse module package
   - Conflict detection (naming conflicts, version conflicts)
   - Preview changes before import
   - Atomic deployment (all or nothing)

3. **Version Management**
   - Track module versions
   - Upgrade existing modules
   - Rollback capability
   - Version comparison

4. **Environment Promotion**
   - Export from dev → import to staging
   - Export from staging → import to prod
   - Configuration overrides per environment
   - Migration script generation

5. **Deployment Tools**
   - Deployment wizard UI
   - Conflict resolution interface
   - Deployment history and audit log
   - Rollback UI

**Total Effort:** 3-4 weeks

**Detail:** See [NO-CODE-PHASE6.md](NO-CODE-PHASE6.md) (to be created)

---

### 📋 Phase 7: Integration & Communication (Future)

**Goal:** Connect with external systems and communication channels

**Features:**

1. **API Integration Designer**
   - REST API connector configuration
   - GraphQL support
   - Authentication methods (API key, OAuth, JWT)
   - Request/response mapping
   - Error handling and retry

2. **Email System**
   - Email template designer (WYSIWYG)
   - Dynamic content with merge fields
   - Attachment support
   - Email scheduling
   - Delivery tracking

3. **Notification System**
   - In-app notification builder
   - SMS integration (Twilio, etc.)
   - Push notifications (mobile/web)
   - Notification preferences
   - Read/unread tracking

4. **Document Generation**
   - PDF template designer
   - Word template support
   - Merge fields and dynamic content
   - Batch document generation
   - Template library

5. **Webhook Management**
   - Outgoing webhook configuration
   - Incoming webhook handlers
   - Payload transformation
   - Webhook security (signatures)

6. **External Data Sync**
   - Bi-directional sync configuration
   - Field mapping UI
   - Conflict resolution strategies
   - Sync scheduling
   - Sync history and logs

**Total Effort:** 6-8 weeks

**Detail:** See [NO-CODE-PHASE7.md](NO-CODE-PHASE7.md) (to be created)

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
9. ✅ **Visual Designers** - Fully visual report/dashboard designers (Phase 3 - Done)
10. 🎯 **Modular Architecture** - Modules with dependencies and extensions (Phase 4 - In Progress)
11. 🔥 **Field-Level Features** - Select/Reference types, calculated fields, validation rules, prefix/suffix (Phase 5 - In Progress)
12. 📋 **Advanced Input Types** - Rich UI controls, conditional visibility, field groups (Phase 5 - Planned)
13. 📋 **Module Packaging** - Export/import modules across environments (Phase 6 - Planned)
14. 📋 **External Integration** - API, email, notifications (Phase 7 - Planned)

**Final Goal:** Develop complete, modular business applications using ONLY the platform's no-code configuration UI, with cross-module capabilities and environment promotion (dev → staging → prod).

---

## Related Documentation

### Phase Documentation
- [NO-CODE-PHASE1.md](NO-CODE-PHASE1.md) - Core Foundation (Data Model, Workflow, Automation, Lookups) ✅
- [NO-CODE-PHASE2.md](NO-CODE-PHASE2.md) - Runtime Data Layer (CRUD API, Auto-UI, Integration) ✅
- [NO-CODE-PHASE3.md](NO-CODE-PHASE3.md) - Visual Designer Enhancement (Menu, Report, Dashboard) ✅
- [NO-CODE-PHASE4.md](NO-CODE-PHASE4.md) - Module System Foundation (Registry, Cross-Module, Extensions) 🎯
- [NO-CODE-PHASE5.md](NO-CODE-PHASE5.md) - Field-Level Features & Enhancements (Calculated, Validation, Advanced Inputs) 🔥
- [NO-CODE-PHASE6.md](NO-CODE-PHASE6.md) - Module Packaging & Deployment (to be created) 📋
- [NO-CODE-PHASE7.md](NO-CODE-PHASE7.md) - Integration & Communication (to be created) 📋

### User Guides
- [NO-CODE-MODULE-CREATION-GUIDE.md](NO-CODE-MODULE-CREATION-GUIDE.md) - Step-by-step guide to create modules ✅

### Technical Documentation
- [FRONTEND-API-MIGRATION-GUIDE.md](FRONTEND-API-MIGRATION-GUIDE.md) - API migration reference for frontend
- [BACKEND-API-REVIEW.md](BACKEND-API-REVIEW.md) - API consistency review and EntityMetadata analysis
- [API-OVERLAP-ANALYSIS.md](API-OVERLAP-ANALYSIS.md) - API overlap analysis

---

**Document Version:** 7.0
**Last Updated:** 2026-01-23
**Next Review:** Phase 5 Priority 1 completion
**Changelog:**
- v7.0 (2026-01-23): Phase 5 started - Select/Reference field types implemented, detailed Quick Wins plan, backend readiness assessment
- v6.0 (2026-01-19): Reorganized phases, added Phase 4-7 structure, updated module system architecture
