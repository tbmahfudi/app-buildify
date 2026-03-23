# App-Buildify — Documentation Index

**App-Buildify** is a multi-tenant NoCode/LowCode platform for building business applications without custom code. It ships with authentication, RBAC, a visual data model designer, workflow engine, dashboards, reporting, and a pluggable module system.

---

## Quick Start

```bash
cp backend/.env.example backend/.env   # configure environment
docker-compose -f infra/docker-compose.dev.yml up -d
make migrate-pg                        # run database migrations
make seed                              # seed default admin + roles
```

| URL | Service |
|-----|---------|
| http://localhost:8080 | Frontend application |
| http://localhost:8000/api/v1 | REST API |
| http://localhost:8000/docs | Swagger UI |

Default admin: `admin@example.com` / `Admin@123`

---

## Documentation

### Platform

| Document | Description |
|----------|-------------|
| [Platform Overview](docs/platform/OVERVIEW.md) | Architecture, multi-tenancy model, tech summary |
| [Getting Started](docs/platform/GETTING_STARTED.md) | Docker quick start, local dev setup, Make commands |
| [Roadmap](docs/platform/ROADMAP.md) | Component roadmap, release history, planned features |

### Backend

| Document | Description |
|----------|-------------|
| [Architecture](docs/backend/README.md) | Directory structure, layers, models, services, config |
| [API Reference](docs/backend/API_REFERENCE.md) | All REST endpoints, formats, pagination |
| [Authentication & Security](docs/backend/AUTH_SECURITY.md) | JWT, password policy, lockout, sessions, audit |
| [RBAC System](docs/backend/RBAC.md) | Permission format, roles, enforcement |

### Frontend

| Document | Description |
|----------|-------------|
| [Architecture](docs/frontend/README.md) | Bootstrap flow, routing, state, API client |
| [Component Library](docs/frontend/COMPONENT_LIBRARY.md) | All Flex components with usage examples |
| [Internationalization](docs/frontend/I18N.md) | i18next setup, translation files, language switching |

### Deployment

| Document | Description |
|----------|-------------|
| [Deployment Guide](docs/deployment/README.md) | Docker Compose, Nginx, migrations, logging, scaling |
| [Production Checklist](docs/deployment/PRODUCTION.md) | Security, DB, infra, and deployment checklists |
| [Environment Variables](docs/deployment/ENVIRONMENT.md) | Full env var reference for all services |

### Modules

| Document | Description |
|----------|-------------|
| [Financial Module](docs/modules/FINANCIAL_MODULE.md) | Financial management module — full API and feature reference |
| [Module Development Guide](docs/archive/MODULE_DEVELOPMENT_GUIDE.md) | Build a custom module |
| [Module Registration](docs/archive/MODULE_REGISTRATION.md) | Manifest format and registration API |
| [Modular Architecture Design](docs/archive/MODULAR_ARCHITECTURE_DESIGN.md) | Design decisions and patterns |

### Reference

| Document | Description |
|----------|-------------|
| [Known Gaps](docs/GAPS.md) | Features documented but not yet implemented |
| [Functional Specification](docs/archive/FUNCTIONAL_SPECIFICATION.md) | Feature requirements and business rules |
| [Technical Specification](docs/archive/TECHNICAL_SPECIFICATION.md) | Technical design and architecture details |
| [Database Migrations](docs/archive/DATABASE_MIGRATIONS.md) | Alembic usage and patterns |
| [Changelog](docs/archive/CHANGELOG.md) | Version history |

---

## Project Structure

```
app-buildify/
├── backend/           FastAPI core platform (Python 3.11)
├── frontend/          Vanilla JS + Flex Component Library
├── modules/
│   └── financial/     Financial management module
├── infra/
│   └── nginx/         API gateway configuration
├── docs/              Active documentation
│   ├── archive/       Original/legacy documentation
│   ├── backend/
│   ├── deployment/
│   ├── frontend/
│   ├── modules/
│   └── platform/
├── tests/             Frontend unit tests
├── scripts/           Utility scripts
└── Makefile           Build commands
```
