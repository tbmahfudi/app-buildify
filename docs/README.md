# Documentation Index

Welcome to the App-Buildify documentation. Use this index to navigate all available docs.

---

## Platform

| Document | Description |
|----------|-------------|
| [Overview](./platform/OVERVIEW.md) | What the platform is, architecture diagram, multi-tenancy model, tech summary |
| [Getting Started](./platform/GETTING_STARTED.md) | Prerequisites, quick start with Docker, local dev setup, Make commands |
| [Roadmap](./platform/ROADMAP.md) | Component and platform roadmap, release history |

---

## Backend

| Document | Description |
|----------|-------------|
| [Architecture](./backend/README.md) | Directory structure, layers, models, routers, services, configuration |
| [API Reference](./backend/API_REFERENCE.md) | All REST endpoints, request/response formats, status codes, pagination |
| [Authentication & Security](./backend/AUTH_SECURITY.md) | JWT flow, password policy, account lockout, session management, audit logging |
| [RBAC System](./backend/RBAC.md) | Permission format, data model, default roles, enforcement, API endpoints |
| [Dynamic Entity System](./backend/DYNAMIC_ENTITIES.md) | NoCode entity designer, field types, data scope, runtime CRUD API, bulk ops, filters |

---

## Frontend

| Document | Description |
|----------|-------------|
| [Architecture](./frontend/README.md) | Directory structure, bootstrap flow, routing, state, API client, testing |
| [Component Library](./frontend/COMPONENT_LIBRARY.md) | All Flex layout and UI components with usage examples |
| [Internationalization](./frontend/I18N.md) | i18next setup, file structure, adding translations, language switching |

---

## Deployment

| Document | Description |
|----------|-------------|
| [Deployment Guide](./deployment/README.md) | Docker Compose services, Nginx config, environments, migrations, logging |
| [Production Checklist](./deployment/PRODUCTION.md) | Security, DB, infra, networking, and deployment checklists |
| [Environment Variables](./deployment/ENVIRONMENT.md) | Complete reference for all env vars across core and modules |

---

## Modules & Extensions

| Document | Description |
|----------|-------------|
| [Financial Module](./modules/FINANCIAL_MODULE.md) | Financial module — full API, setup, and feature reference |
| [Module Development Guide](./archive/MODULE_DEVELOPMENT_GUIDE.md) | How to build a custom module |
| [Module Registration](./archive/MODULE_REGISTRATION.md) | Module manifest format and registration API |
| [Modular Architecture Design](./archive/MODULAR_ARCHITECTURE_DESIGN.md) | Design decisions and patterns |

---

## Reference

| Document | Description |
|----------|-------------|
| [Known Gaps](./GAPS.md) | Features in documentation not yet implemented in code |
| [Technical Specification](./archive/TECHNICAL_SPECIFICATION.md) | Detailed technical requirements |
| [Functional Specification](./archive/FUNCTIONAL_SPECIFICATION.md) | Feature requirements and business rules |
| [Database Migrations](./archive/DATABASE_MIGRATIONS.md) | Migration guide and patterns |
| [Changelog](./archive/CHANGELOG.md) | Version history |

---

## Archive (Original Documents)

Legacy and source documents preserved for reference.

| Document | Description |
|----------|-------------|
| [Architecture (Original)](./archive/ARCHITECTURE.md) | Original architecture overview |
| [Financial Module Design](./archive/FINANCIAL_MODULE_DESIGN.md) | Original financial module design specification |
| [Financial Module Complete](./archive/FINANCIAL_MODULE_COMPLETE.md) | Financial module implementation summary |
| [Financial Module Status](./archive/FINANCIAL_MODULE_STATUS.md) | Implementation status report |
| [Financial Module Implementation](./archive/FINANCIAL_MODULE_IMPLEMENTATION_SUMMARY.md) | Phase 1 implementation details |
| [Modular System Implementation](./archive/MODULAR_SYSTEM_IMPLEMENTATION.md) | Modular architecture implementation guide |
| [Module Sync Options](./archive/MODULE_SYNC_OPTIONS.md) | Module synchronization architectural approaches |
| [Phase 4 Plan](./archive/PHASE4_PLAN.md) | Phase 4 implementation plan |
| [PostgreSQL Event Bus Design](./archive/POSTGRES_EVENT_BUS_DESIGN.md) | Event bus design using LISTEN/NOTIFY |
| [Table Components & Lookup Fields](./archive/TABLE_COMPONENTS_AND_LOOKUP_FIELDS.md) | Table and lookup field implementation guide |
| [Displaying Lookup Fields](./archive/DISPLAYING_LOOKUP_FIELDS_PRACTICAL_GUIDE.md) | Practical guide for lookup field display |
| [Migration Guide](./archive/MIGRATION.md) | Migration guides from other UI frameworks |
| [Flex Component Library README](./archive/README.md) | Original Flex component library overview |
| [Phase 3 Components](./archive/components/phase3/) | FlexCluster, FlexToolbar, FlexMasonry, FlexSplitPane docs |

---

## Quick Links

- **Frontend**: `http://localhost:8080`
- **Backend API**: `http://localhost:8000/api/v1`
- **Swagger UI**: `http://localhost:8000/docs`
- **Redoc**: `http://localhost:8000/redoc`
- **Financial Module**: `http://localhost:9001`
- **Default Admin**: `admin@example.com` / `Admin@123`
