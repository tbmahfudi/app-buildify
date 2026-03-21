# Platform Overview

## What is App-Buildify?

App-Buildify is a **multi-tenant NoCode/LowCode platform** that enables organizations to build, deploy, and manage business applications without writing custom code. It provides a complete foundation for enterprise application development with built-in authentication, authorization, data modeling, workflow automation, and reporting.

---

## Core Capabilities

| Capability | Description |
|-----------|-------------|
| **Multi-Tenancy** | Isolated data per tenant with shared infrastructure |
| **RBAC** | Fine-grained role-based access control |
| **NoCode Data Model** | Design database entities visually |
| **Workflow Engine** | Build process automations visually |
| **Automation Rules** | Trigger-action business rules |
| **Dashboard Builder** | Configure KPI dashboards with widgets |
| **Report Designer** | Build and schedule reports |
| **Module System** | Extend the platform with pluggable modules |
| **Multi-Language** | i18n support (EN, DE, ES, FR, ID) |
| **Audit Logging** | Full activity trail across all operations |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         API Gateway (Nginx)                        │
│                  Routes: /api → Core | /api/v1/financial → Module │
└───────────────────────┬──────────────────────┬───────────────────┘
                        │                      │
           ┌────────────▼──────────┐  ┌────────▼───────────┐
           │   Core Platform API   │  │  Financial Module  │
           │  FastAPI :8000        │  │  FastAPI :9001     │
           └────────────┬──────────┘  └────────┬───────────┘
                        │                      │
           ┌────────────▼──────────────────────▼───────────┐
           │              PostgreSQL (Primary DB)           │
           └───────────────────────────────────────────────┘
           ┌───────────────────────────────────────────────┐
           │              Redis (Cache / Sessions)          │
           └───────────────────────────────────────────────┘
           ┌───────────────────────────────────────────────┐
           │           Frontend (Vanilla JS / Nginx)        │
           └───────────────────────────────────────────────┘
```

---

## Multi-Tenancy Model

```
Platform
  └── Tenant (1 per organization group)
        ├── Company A
        │     ├── Branch 1
        │     │     └── Department X
        │     └── Branch 2
        └── Company B
```

- A **User** belongs to exactly one **Tenant**
- A User can access one or more **Companies** within that Tenant
- **Data** is scoped to: Platform | Tenant | Company | Branch | Department
- All DB queries are automatically filtered by `tenant_id` and `company_id`

---

## RBAC Permission Model

Permissions follow the pattern: `resource:action:scope`

| Example | Meaning |
|---------|---------|
| `users:create:tenant` | Create users across the tenant |
| `financial:invoices:read:company` | Read invoices within a company |
| `data:*:branch` | Full access to data at branch level |

**Assignment chain**: User → Roles → Permissions (also via Groups → Roles)

---

## Module System

The platform supports pluggable modules that integrate seamlessly:

1. Module registers itself via `/api/v1/modules/register`
2. Tenant enables the module via the admin UI
3. Module menus, routes, and permissions are dynamically injected
4. Each module ships with its own FastAPI service, DB migrations, and frontend pages

**Current modules**: Financial

---

## Technology Summary

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI (Python 3.11) |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2.0 |
| Cache | Redis 7 |
| Migrations | Alembic |
| Frontend | Vanilla JavaScript (ES6+) |
| UI Components | Flex Component Library (zero dependencies) |
| CSS | Tailwind CSS (CDN) |
| Icons | Phosphor Icons |
| i18n | i18next |
| Container | Docker + Docker Compose |
| API Gateway | Nginx |

---

## Related Documents

- [Getting Started](./GETTING_STARTED.md)
- [Backend Architecture](../backend/README.md)
- [Frontend Architecture](../frontend/README.md)
- [Deployment Guide](../deployment/README.md)
- [Module Development Guide](../MODULE_DEVELOPMENT_GUIDE.md)
