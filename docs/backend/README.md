# Backend Architecture

## Overview

The backend is built with **FastAPI** (Python 3.11) and follows a layered architecture: **Routers → Services → Models → Database**. It supports multi-tenancy, RBAC, a NoCode engine, workflow automation, and a pluggable module system.

---

## Directory Structure

```
backend/
├── app/
│   ├── main.py                      # App factory, middleware, router registration
│   ├── core/                        # Cross-cutting concerns
│   │   ├── config.py                # Settings via pydantic-settings
│   │   ├── db.py                    # SQLAlchemy session factory
│   │   ├── auth.py                  # JWT token creation/validation
│   │   ├── dependencies.py          # Dependency injection (get_db, get_current_user)
│   │   ├── security_config.py       # Security policy engine
│   │   ├── session_manager.py       # Session lifecycle
│   │   ├── lockout_manager.py       # Account lockout logic
│   │   ├── password_validator.py    # Password complexity rules
│   │   ├── password_history.py      # Password history enforcement
│   │   ├── notification_service.py  # Email/notification dispatch
│   │   ├── rate_limiter.py          # SlowAPI rate limiting
│   │   ├── security_middleware.py   # HTTP security headers
│   │   ├── exceptions.py            # Custom exception classes
│   │   ├── logging_config.py        # Structlog configuration
│   │   ├── model_cache.py           # Runtime model caching
│   │   ├── dynamic_query_builder.py # Filter / sort / search / aggregate helpers
│   │   ├── response_builders.py     # Standardised response envelope builders
│   │   ├── event_bus/               # Event publishing system
│   │   └── module_system/           # Module loader & registry
│   │       ├── base_module.py       # BaseModule interface
│   │       ├── loader.py            # Filesystem module loader
│   │       └── registry.py          # Module registry service
│   ├── models/                      # SQLAlchemy ORM models (40+ tables)
│   ├── routers/                     # FastAPI route handlers (20+ routers)
│   ├── schemas/                     # Pydantic request/response schemas
│   ├── services/                    # Business logic layer (21 services)
│   ├── alembic/                     # Database migrations
│   │   └── versions/                # Individual migration files
│   ├── seeds/                       # Database seed scripts
│   └── utils/                       # Utility helpers
├── requirements.txt
├── alembic.ini
├── .env.example
└── Dockerfile
```

---

## Layer Responsibilities

### Routers (`app/routers/`)
- Define FastAPI routes with HTTP methods, path parameters, and dependency injection
- Validate input via Pydantic schemas
- Delegate all logic to services
- Return Pydantic response schemas

### Services (`app/services/`)
- Contain all business logic
- Orchestrate multiple model operations within a single transaction
- Raise `HTTPException` for business rule violations

### Models (`app/models/`)
- SQLAlchemy ORM classes mapping to DB tables
- Include relationships, constraints, and indexes
- Extend `Base` from `app/models/base.py` (UUID primary keys, timestamps)

### Schemas (`app/schemas/`)
- Pydantic models for request validation and response serialization
- Separate `Create`, `Update`, and `Response` variants per resource

---

## Core Models

### Identity & Tenancy

| Model | Table | Purpose |
|-------|-------|---------|
| `User` | `users` | Login identity, profile, security state |
| `Tenant` | `tenants` | Tenant isolation root |
| `Company` | `companies` | Business entities within a tenant |
| `Branch` | `branches` | Office/branch within a company |
| `Department` | `departments` | Department within a branch |

### RBAC

| Model | Table | Purpose |
|-------|-------|---------|
| `Role` | `roles` | Named permission bundles |
| `Permission` | `permissions` | Atomic permission (`resource:action:scope`) |
| `Group` | `groups` | User collections for bulk role assignment |
| `UserRole` | `user_roles` | User ↔ Role junction |
| `RolePermission` | `role_permissions` | Role ↔ Permission junction |
| `UserGroup` | `user_groups` | User ↔ Group junction |
| `GroupRole` | `group_roles` | Group ↔ Role junction |

### NoCode Platform

| Model | Table | Purpose |
|-------|-------|---------|
| `EntityDefinition` | `entity_definitions` | Custom table blueprints |
| `FieldDefinition` | `field_definitions` | Column definitions per entity |
| `WorkflowDefinition` | `workflow_definitions` | Business process state machines |
| `AutomationRule` | `automation_rules` | Trigger/condition/action rules |
| `LookupConfiguration` | `lookup_configurations` | Dropdown data sources |
| `Dashboard` | `dashboards` | Dashboard configurations |
| `Widget` | `widgets` | Individual dashboard widgets |
| `Report` | `reports` | Report definitions and templates |

### System

| Model | Table | Purpose |
|-------|-------|---------|
| `AuditLog` | `audit_logs` | All user activity |
| `Event` | `events` | Published events |
| `EventSubscription` | `event_subscriptions` | Event listeners |
| `TokenBlacklist` | `token_blacklist` | Revoked JWT tokens (also Redis) |
| `UserSession` | `user_sessions` | Active session tracking |
| `LoginAttempt` | `login_attempts` | Brute-force detection |
| `PasswordHistory` | `password_history` | Prevent password reuse |
| `SecurityPolicy` | `security_policies` | Tenant-specific security rules |

---

## API Routers

All routes are prefixed with `/api/v1/`.

| Router File | Prefix | Main Operations |
|------------|--------|----------------|
| `auth.py` | `/auth` | Login, logout, refresh, password reset |
| `users.py` | `/users` | CRUD users, assign roles |
| `rbac.py` | `/rbac` | Manage roles, permissions, groups |
| `org.py` | `/org` | Manage tenants, companies, branches |
| `data.py` | `/data` | Generic entity CRUD |
| `data_model.py` | `/data-model` | Design entity definitions |
| `dynamic_data.py` | `/dynamic-data` | Runtime data for custom entities |
| `workflows.py` | `/workflows` | Define and trigger workflows |
| `automations.py` | `/automations` | Automation rule CRUD |
| `dashboards.py` | `/dashboards` | Dashboard and widget management |
| `reports.py` | `/reports` | Report design, generation, export |
| `lookups.py` | `/lookups` | Lookup source configuration |
| `scheduler.py` | `/scheduler` | Job scheduling |
| `menu.py` | `/menu` | Menu item CRUD |
| `modules.py` | `/modules` | Module registration |
| `nocode_modules.py` | `/nocode-modules` | NoCode module APIs |
| `audit.py` | `/audit` | Audit log retrieval |
| `settings.py` | `/settings` | User/system settings |
| `metadata.py` | `/metadata` | Entity metadata |
| `admin/security.py` | `/admin/security` | Security policy management |

---

## Key Services

| Service | File | Responsibility |
|---------|------|---------------|
| `DataModelService` | `data_model_service.py` | CRUD for entity/field definitions |
| `DynamicEntityService` | `dynamic_entity_service.py` | Runtime CRUD, aggregation, and expand on custom entities |
| `ProcedureService` | `procedure_service.py` | Tenant-aware caller for named PostgreSQL functions and materialized view refresh |
| `WorkflowService` | `workflow_service.py` | Workflow execution and state transitions |
| `AutomationService` | `automation_service.py` | Rule evaluation and action dispatch |
| `SchedulerService` | `scheduler_service.py` | APScheduler job management |
| `DashboardService` | `dashboard_service.py` | Widget data aggregation |
| `ReportService` | `report_service.py` | Report generation and PDF/Excel export |
| `MenuService` | `menu_service.py` | Menu CRUD and permission-based filtering |
| `LookupService` | `lookup_service.py` | Dropdown source resolution |
| `ModuleRegistryService` | `module_service_registry.py` | Dynamic module loading |
| `NocodeModuleService` | `nocode_module_service.py` | Module lifecycle management |
| `MetadataSyncService` | `metadata_sync_service.py` | Entity metadata synchronization |
| `MigrationGenerator` | `migration_generator.py` | DDL for tables, views, and generated columns from entity definitions |
| `RuntimeModelGenerator` | `runtime_model_generator.py` | Create SQLAlchemy models at runtime (tables and views) |

---

## Authentication & Security

See [AUTH_SECURITY.md](./AUTH_SECURITY.md) for full details.

**Summary**:
- JWT-based (access token + refresh token)
- Tokens passed via `Authorization: Bearer <token>` header
- Redis used for token revocation blacklist
- Configurable password policies, session timeouts, and account lockout

---

## Configuration

All settings are in `app/core/config.py` (Pydantic `BaseSettings`), loaded from `.env`:

```python
DATABASE_URL: str
REDIS_URL: str
JWT_SECRET_KEY: str
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
REFRESH_TOKEN_EXPIRE_DAYS: int = 7
DEBUG: bool = False
ENVIRONMENT: str = "production"
RATE_LIMIT: str = "100/minute"
SENTRY_DSN: Optional[str] = None
```

---

## Database Migrations

Alembic manages all schema changes.

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Check current revision
alembic current
```

Migration files live in `app/alembic/versions/`.

---

## Dependency Injection

FastAPI dependencies (`app/core/dependencies.py`):

```python
# Database session per request
def get_db() -> Generator[Session, None, None]

# Current authenticated user (raises 401 if not authenticated)
def get_current_user(token: str, db: Session) -> User

# Current user with specific permission check
def require_permission(permission: str) -> Callable
```

Usage in routers:

```python
@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ...
```

---

## Event Bus

The platform includes a PostgreSQL-backed event bus:

- **Publish**: `EventBusService.publish(event_type, payload, tenant_id)`
- **Subscribe**: Register handlers via `EventSubscription` model
- **Delivery**: APScheduler polls and dispatches events

Used for cross-module communication without tight coupling.

---

## Dynamic Data — Advanced Capabilities

The `/api/v1/dynamic-data/` layer supports more than plain CRUD:

### Virtual Entities (DB View Backing)

Set `entity_type = "virtual"` on an `EntityDefinition` to map it to an existing PostgreSQL view. The platform queries the view identically to a regular table. Write operations return `405`. Useful for cross-entity reports and pre-joined read models.

```json
{
  "entity_type": "virtual",
  "table_name": "v_invoice_summary",
  "meta_data": {
    "view_sql": "CREATE OR REPLACE VIEW v_invoice_summary AS SELECT ...",
    "view_dependencies": ["financial_invoices", "financial_customers"]
  }
}
```

### Aggregation API

`GET /api/v1/dynamic-data/{entity}/aggregate` runs server-side GROUP BY aggregations — no need to fetch all rows.

```
?group_by=status&metrics=[{"field":"amount","function":"sum"}]&date_trunc=month&date_field=created_at
```

Org-scope isolation (tenant/company/branch) is applied automatically. Virtual entities are fully supported here.

### Expand — Inline Related Records

`?expand=customer_id,region_id` on any list endpoint fetches related entities in a single IN query and inlines them as `customer_id_data: {...}`. Depth is limited to 1 level.

### Calculated Fields

Fields with `is_calculated = true` and a `calculation_formula` are emitted as PostgreSQL `GENERATED ALWAYS AS (...) STORED` columns — they are persisted on disk and are filterable/sortable in aggregation queries.

Formula syntax: `{field_name}` tokens reference sibling column names, e.g. `{unit_price} * {quantity}`.

### DB Procedures and Materialized Views

`ProcedureService` (`app/services/procedure_service.py`) provides a tenant-aware wrapper for calling named PostgreSQL functions and refreshing materialized views. Use it for logic too complex for the aggregation API — recursive CTEs, financial aging reports, amortisation schedules.

```python
service = ProcedureService(db, current_user)
rows = await service.call("fn_ar_aging", {"as_of_date": "2026-04-15"})
await service.refresh_materialized_view("mv_dashboard_kpis", concurrently=True)
```

Register new functions in the `PROCEDURE_REGISTRY` dict at the top of `procedure_service.py`.

---

## Related Documents

- [API Reference](./API_REFERENCE.md)
- [Dynamic Entity System](./DYNAMIC_ENTITIES.md)
- [Dynamic Entity Gaps & Enhancements](./DYNAMIC_ENTITIES_GAPS.md)
- [Authentication & Security](./AUTH_SECURITY.md)
- [RBAC System](./RBAC.md)
- [Platform Overview](../platform/OVERVIEW.md)
