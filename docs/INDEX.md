# Documentation Index

Welcome to the App-Buildify documentation. Use this index to navigate all available docs.

---

## Platform

| Document | Description |
|----------|-------------|
| [Overview](./platform/OVERVIEW.md) | What the platform is, architecture diagram, multi-tenancy model, tech summary |
| [Getting Started](./platform/GETTING_STARTED.md) | Prerequisites, quick start with Docker, local dev setup, Make commands |

---

## Backend

| Document | Description |
|----------|-------------|
| [Architecture](./backend/README.md) | Directory structure, layers, models, routers, services, configuration |
| [API Reference](./backend/API_REFERENCE.md) | All REST endpoints, request/response formats, status codes, pagination |
| [Authentication & Security](./backend/AUTH_SECURITY.md) | JWT flow, password policy, account lockout, session management, audit logging |
| [RBAC System](./backend/RBAC.md) | Permission format, data model, default roles, enforcement, API endpoints |

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
| [Module Development Guide](./MODULE_DEVELOPMENT_GUIDE.md) | How to build a custom module |
| [Module Registration](./MODULE_REGISTRATION.md) | Module manifest format and registration API |
| [Modular Architecture Design](./MODULAR_ARCHITECTURE_DESIGN.md) | Design decisions and patterns |
| [Financial Module](./FINANCIAL_MODULE_DESIGN.md) | Financial module feature design |

---

## Additional References

| Document | Description |
|----------|-------------|
| [Architecture (Legacy)](./ARCHITECTURE.md) | Original architecture overview |
| [Technical Specification](./TECHNICAL_SPECIFICATION.md) | Detailed technical requirements |
| [Functional Specification](./FUNCTIONAL_SPECIFICATION.md) | Feature requirements |
| [Database Migrations](./DATABASE_MIGRATIONS.md) | Migration guide and patterns |
| [Changelog](./CHANGELOG.md) | Version history |

---

## Quick Links

- **Backend API Docs** (Swagger): `http://localhost:8000/docs`
- **Backend API Docs** (Redoc): `http://localhost:8000/redoc`
- **Frontend**: `http://localhost`
- **Default Admin**: `admin@example.com` / `Admin@123`
