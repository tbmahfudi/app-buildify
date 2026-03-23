# Technical Specification
## App-Buildify Platform

**Version:** 1.0
**Last Updated:** 2025-11-12
**Status:** Active

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Backend Architecture](#backend-architecture)
5. [Frontend Architecture](#frontend-architecture)
6. [Database Design](#database-design)
7. [Security Architecture](#security-architecture)
8. [Module System Architecture](#module-system-architecture)
9. [API Design](#api-design)
10. [Infrastructure & Deployment](#infrastructure--deployment)
11. [Performance & Scalability](#performance--scalability)
12. [Monitoring & Logging](#monitoring--logging)
13. [Development Guidelines](#development-guidelines)

---

## 1. Overview

App-Buildify is a multi-tenant NoCode/LowCode platform designed to enable rapid application development with enterprise-grade security, modularity, and scalability. The platform provides a comprehensive foundation for building SaaS applications with pluggable modules, role-based access control, reporting, and analytics capabilities.

### 1.1 Key Technical Characteristics

- **Multi-Tenant Architecture**: Complete tenant isolation with hierarchical organization structure
- **Modular Design**: Plugin-based architecture for feature extensibility
- **API-First**: RESTful API with comprehensive OpenAPI documentation
- **Modern Stack**: FastAPI backend with vanilla JavaScript frontend
- **Database Agnostic**: Support for PostgreSQL and MySQL
- **Containerized**: Docker-based deployment with orchestration support
- **Scalable**: Horizontal scaling support with stateless design

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Browser    │  │  Mobile App  │  │  API Client  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Load Balancer / Nginx                      │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌──────────────────────┐    ┌──────────────────────┐
│  Frontend (Nginx)    │    │  Backend (FastAPI)   │
│  - Static Assets     │    │  - API Endpoints     │
│  - SPA Routing       │    │  - Business Logic    │
│  - GZIP Compression  │    │  - Module System     │
└──────────────────────┘    └──────────────────────┘
                                        │
                ┌───────────────────────┼───────────────────────┐
                ▼                       ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │    PostgreSQL    │    │      Redis       │    │   File Storage   │
    │    / MySQL       │    │   (Optional)     │    │    (S3/Local)    │
    │  - Primary DB    │    │  - Sessions      │    │  - Uploads       │
    │  - Multi-Tenant  │    │  - Cache         │    │  - Reports       │
    └──────────────────┘    │  - Token Blacklist│   └──────────────────┘
                            └──────────────────┘
```

### 2.2 Component Overview

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend Server | Nginx | Static file serving, reverse proxy |
| Frontend Application | Vanilla JavaScript | SPA with custom component library |
| Backend API | FastAPI | RESTful API, business logic |
| Database | PostgreSQL/MySQL | Primary data store |
| Cache | Redis | Session management, caching, token blacklist |
| Task Scheduler | APScheduler | Background job execution |
| File Storage | Local/S3 | Document and report storage |

### 2.3 Architecture Patterns

- **Three-Tier Architecture**: Presentation, Business Logic, Data Access
- **Microservices-Ready**: Modular design allows service extraction
- **Event-Driven**: Component communication via event emitters
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic separation
- **Dependency Injection**: FastAPI's Depends() system

---

## 3. Technology Stack

### 3.1 Backend Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Framework | FastAPI | Latest | High-performance API framework |
| Runtime | Python | 3.10+ | Programming language |
| ORM | SQLAlchemy | 2.0+ | Database abstraction |
| Migrations | Alembic | Latest | Database versioning |
| Authentication | PyJWT | Latest | JWT token handling |
| Password Hashing | Passlib + Bcrypt | Latest | Secure password storage |
| Validation | Pydantic | 2.0+ | Request/response validation |
| Caching | Redis | 7.0+ | Session and data caching |
| Task Scheduling | APScheduler | Latest | Background job execution |
| Logging | Structlog | Latest | Structured logging |
| Rate Limiting | SlowAPI | Latest | API rate limiting |
| Monitoring | Sentry (optional) | Latest | Error tracking |
| Metrics | Prometheus (optional) | Latest | Metrics collection |

### 3.2 Frontend Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Language | JavaScript | ES6+ | Programming language |
| UI Framework | Tailwind CSS | Latest | Utility-first CSS |
| Icons | Phosphor Icons | Latest | Icon library |
| Components | Custom Flex Library | 1.0 | Component framework |
| Module System | ES6 Modules | Native | Code organization |
| Build Tool | None | - | Zero-build approach |

### 3.3 Infrastructure Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| Containerization | Docker | Application packaging |
| Orchestration | Docker Compose | Development environment |
| Web Server | Nginx | Reverse proxy, static files |
| Database | PostgreSQL/MySQL | Primary data store |
| Cache | Redis | Session and data caching |

---

## 4. Backend Architecture

### 4.1 Project Structure

```
backend/
├── app/
│   ├── alembic/                    # Database migrations
│   │   ├── versions/
│   │   │   ├── postgresql/         # PostgreSQL-specific migrations
│   │   │   └── mysql/              # MySQL-specific migrations
│   │   └── env.py
│   ├── core/                       # Core framework components
│   │   ├── config.py              # Configuration management
│   │   ├── database.py            # Database connection
│   │   ├── security.py            # Security utilities
│   │   └── logging.py             # Logging configuration
│   ├── models/                     # SQLAlchemy models
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── rbac.py
│   │   ├── security.py
│   │   ├── module.py
│   │   ├── report.py
│   │   ├── dashboard.py
│   │   └── scheduler.py
│   ├── schemas/                    # Pydantic schemas
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── tenant.py
│   │   └── ...
│   ├── routers/                    # API endpoints
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── org.py
│   │   ├── rbac.py
│   │   ├── modules.py
│   │   ├── reports.py
│   │   ├── dashboards.py
│   │   ├── scheduler.py
│   │   └── admin/
│   │       └── security.py
│   ├── services/                   # Business logic
│   │   ├── auth_service.py
│   │   ├── security/
│   │   │   ├── password_validator.py
│   │   │   ├── lockout_manager.py
│   │   │   └── session_manager.py
│   │   ├── module_service.py
│   │   ├── report_service.py
│   │   └── scheduler_service.py
│   ├── middleware/                 # Request/response middleware
│   │   ├── tenant_middleware.py
│   │   ├── security_middleware.py
│   │   └── logging_middleware.py
│   ├── modules/                    # Plugin modules
│   │   └── financial/
│   │       ├── manifest.json
│   │       ├── module.py
│   │       ├── models/
│   │       ├── routers/
│   │       └── schemas/
│   └── main.py                     # Application entry point
├── requirements.txt
├── Makefile
└── Dockerfile
```

### 4.2 Core Components

#### 4.2.1 Database Connection

**Location**: `app/core/database.py`

- **Connection Pooling**: SQLAlchemy connection pool with overflow
- **Session Management**: Scoped sessions with request lifecycle
- **Health Checks**: Database connectivity verification
- **Multi-Database Support**: PostgreSQL and MySQL support

```python
# Key configuration
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

#### 4.2.2 Configuration Management

**Location**: `app/core/config.py`

- **Environment Variables**: 12-factor app configuration
- **Type Safety**: Pydantic-based settings
- **Validation**: Automatic validation on startup
- **Secrets Management**: Secure handling of sensitive data

#### 4.2.3 Security Core

**Location**: `app/core/security.py`

- **JWT Token Generation**: HS256 algorithm
- **Password Hashing**: Bcrypt with configurable rounds
- **Token Verification**: Signature and expiration validation
- **Token Blacklist**: Redis-based revocation

### 4.3 Service Layer Architecture

All business logic is encapsulated in service classes:

```python
class BaseService:
    """Base service with common functionality"""
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, model, id: UUID) -> Optional[Model]:
        return self.db.query(model).filter(model.id == id).first()
```

Services implement:
- Transaction management
- Error handling
- Logging
- Caching
- Permission checks

### 4.4 Middleware Stack

Middleware executes in the following order:

1. **CORS Middleware**: Cross-origin request handling
2. **Logging Middleware**: Request/response logging
3. **Tenant Middleware**: Tenant context resolution
4. **Security Middleware**: Session timeout, password expiry enforcement
5. **Rate Limiting Middleware**: Request throttling
6. **Exception Middleware**: Error handling and formatting

---

## 5. Frontend Architecture

### 5.1 Project Structure

```
frontend/
├── assets/
│   ├── css/
│   │   └── app.css                 # Tailwind CSS
│   ├── js/
│   │   ├── core/
│   │   │   ├── base-component.js   # Component base class
│   │   │   ├── flex-responsive.js  # Responsive utilities
│   │   │   └── module-system/      # Dynamic module loading
│   │   ├── components/             # UI components
│   │   │   ├── flex-stack.js
│   │   │   ├── flex-grid.js
│   │   │   ├── flex-card.js
│   │   │   └── ...
│   │   ├── layout/                 # Layout components
│   │   │   ├── flex-container.js
│   │   │   ├── flex-section.js
│   │   │   ├── flex-sidebar.js
│   │   │   └── ...
│   │   ├── services/               # API services
│   │   │   ├── base-service.js
│   │   │   ├── user-service.js
│   │   │   └── ...
│   │   ├── utilities/              # Helper functions
│   │   ├── api.js                  # API client
│   │   ├── router.js               # Client-side routing
│   │   ├── auth-service.js         # Authentication
│   │   └── app-entry.js            # Entry point
│   └── templates/                  # HTML page templates
│       ├── dashboard.html
│       ├── users.html
│       └── ...
├── components/                     # Module-specific components
└── index.html                      # SPA shell
```

### 5.2 Component Architecture

#### 5.2.1 BaseComponent

All components extend `BaseComponent` which provides:

- **Lifecycle Methods**: `init()`, `mount()`, `unmount()`, `update()`
- **Event System**: `emit()`, `on()`, `off()`
- **State Management**: `setState()`, `getState()`
- **DOM Utilities**: `render()`, `querySelector()`
- **Cleanup**: Automatic event listener cleanup

```javascript
class MyComponent extends BaseComponent {
    init() {
        this.state = { count: 0 };
    }

    mount() {
        this.attachEvents();
    }

    unmount() {
        this.cleanup();
    }
}
```

#### 5.2.2 Flex Component Library

The Flex component library provides:

**Foundation Components**:
- `FlexStack`: Vertical/horizontal stacking
- `FlexGrid`: Responsive grid layouts
- `FlexCard`: Content cards
- `FlexModal`: Modal dialogs
- `FlexTabs`: Tab navigation

**Layout Components**:
- `FlexContainer`: Max-width containers
- `FlexSection`: Full-width sections
- `FlexSidebar`: Collapsible sidebar
- `FlexToolbar`: Header/footer toolbars
- `FlexMasonry`: Masonry grids
- `FlexSplitPane`: Split layouts
- `FlexCluster`: Horizontal grouping

**Features**:
- Zero dependencies
- Event-driven communication
- Responsive design
- Accessibility support
- Custom styling via props

### 5.3 API Integration

#### 5.3.1 API Client

**Location**: `assets/js/api.js`

```javascript
async function apiFetch(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`/api/v1${endpoint}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        }
    });

    if (response.status === 401) {
        // Token refresh logic
        await refreshToken();
        // Retry request
    }

    return response.json();
}
```

#### 5.3.2 Service Pattern

All API interactions use singleton services:

```javascript
class BaseService {
    constructor() {
        if (this.constructor.instance) {
            return this.constructor.instance;
        }
        this.constructor.instance = this;
    }

    async get(endpoint) {
        return apiFetch(endpoint);
    }

    async post(endpoint, data) {
        return apiFetch(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}
```

### 5.4 Routing System

**Location**: `assets/js/router.js`

- **Client-Side Routing**: Hash-based or history API routing
- **Route Matching**: Pattern-based route matching
- **Guards**: Authentication and permission guards
- **Lazy Loading**: On-demand template loading
- **State Management**: Route state preservation

```javascript
router.addRoute('/dashboard', async () => {
    const template = await loadTemplate('dashboard.html');
    renderTemplate(template);
});
```

---

## 6. Database Design

### 6.1 Multi-Tenancy Strategy

**Approach**: Shared database, shared schema with tenant_id filtering

**Rationale**:
- Cost-effective for large number of tenants
- Simplified maintenance and upgrades
- Efficient resource utilization
- Row-level security enforcement

**Implementation**:
- All tenant-scoped tables include `tenant_id` column
- Foreign key constraints enforce tenant isolation
- Database queries automatically filter by tenant
- Tenant context injected via middleware

### 6.2 Core Tables

#### 6.2.1 Tenancy Tables

**tenants**
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    subscription_tier VARCHAR(50),
    max_users INTEGER,
    max_companies INTEGER,
    max_storage_mb INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**companies**
```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(tenant_id, code)
);
```

**branches**
```sql
CREATE TABLE branches (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 6.2.2 User Tables

**users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    password_expires_at TIMESTAMP,
    grace_logins_remaining INTEGER,
    must_change_password BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
);
```

**user_company_access**
```sql
CREATE TABLE user_company_access (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    company_id UUID REFERENCES companies(id),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    UNIQUE(user_id, company_id)
);
```

#### 6.2.3 RBAC Tables

**roles**
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    role_type VARCHAR(50), -- system, default, custom
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(tenant_id, name)
);
```

**permissions**
```sql
CREATE TABLE permissions (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL, -- format: resource:action:scope
    description TEXT,
    resource VARCHAR(100),
    action VARCHAR(50),
    scope VARCHAR(50), -- all, tenant, company, branch, department, own
    created_at TIMESTAMP
);
```

**role_permissions**
```sql
CREATE TABLE role_permissions (
    id UUID PRIMARY KEY,
    role_id UUID REFERENCES roles(id),
    permission_id UUID REFERENCES permissions(id),
    created_at TIMESTAMP,
    UNIQUE(role_id, permission_id)
);
```

#### 6.2.4 Security Tables

**security_policies**
```sql
CREATE TABLE security_policies (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) NULL,
    -- Password Policy
    password_min_length INTEGER DEFAULT 8,
    password_require_uppercase BOOLEAN DEFAULT TRUE,
    password_require_lowercase BOOLEAN DEFAULT TRUE,
    password_require_numbers BOOLEAN DEFAULT TRUE,
    password_require_special BOOLEAN DEFAULT TRUE,
    password_expiry_days INTEGER DEFAULT 90,
    password_history_count INTEGER DEFAULT 5,
    password_grace_logins INTEGER DEFAULT 3,
    -- Lockout Policy
    lockout_enabled BOOLEAN DEFAULT TRUE,
    lockout_threshold INTEGER DEFAULT 5,
    lockout_duration_minutes INTEGER DEFAULT 30,
    lockout_observation_window_minutes INTEGER DEFAULT 15,
    lockout_type VARCHAR(20) DEFAULT 'progressive',
    -- Session Policy
    session_timeout_minutes INTEGER DEFAULT 30,
    session_absolute_timeout_minutes INTEGER DEFAULT 480,
    max_concurrent_sessions INTEGER DEFAULT 3,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**password_history**
```sql
CREATE TABLE password_history (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP
);
```

**token_blacklist**
```sql
-- Stored in Redis for performance
-- Key: token_jti
-- Value: expiration timestamp
-- TTL: token expiration time
```

#### 6.2.5 Module System Tables

**module_registry**
```sql
CREATE TABLE module_registry (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    version VARCHAR(50),
    author VARCHAR(255),
    category VARCHAR(100),
    status VARCHAR(50), -- available, installed, deprecated
    icon VARCHAR(255),
    required_subscription_tier VARCHAR(50),
    dependencies JSONB,
    permissions JSONB,
    default_roles JSONB,
    configuration_schema JSONB,
    installed_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**tenant_modules**
```sql
CREATE TABLE tenant_modules (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    module_id UUID REFERENCES module_registry(id),
    is_enabled BOOLEAN DEFAULT FALSE,
    configuration JSONB,
    enabled_at TIMESTAMP,
    disabled_at TIMESTAMP,
    UNIQUE(tenant_id, module_id)
);
```

### 6.3 Migration Strategy

#### 6.3.1 Dual-Database Support

Alembic migrations are organized by database type:

```
alembic/versions/
├── postgresql/
│   ├── pg_001_initial_tables.py
│   ├── pg_002_add_security_policies.py
│   └── ...
└── mysql/
    ├── mysql_001_initial_tables.py
    ├── mysql_002_add_security_policies.py
    └── ...
```

#### 6.3.2 Migration Naming Convention

- **Prefix**: `pg_` or `mysql_`
- **Number**: Sequential 3-digit number
- **Description**: Snake_case description
- **Example**: `pg_003_add_report_caching.py`

#### 6.3.3 Migration Best Practices

- **Reversible**: All migrations include downgrade logic
- **Data Safety**: Use transactions and backups
- **Testing**: Test on copy of production data
- **Documentation**: Clear comments in migration files
- **Zero-Downtime**: Use online DDL techniques where possible

---

## 7. Security Architecture

### 7.1 Authentication Flow

```
┌──────────┐                                    ┌──────────┐
│  Client  │                                    │  Server  │
└─────┬────┘                                    └─────┬────┘
      │                                               │
      │  1. POST /auth/login                          │
      │  { username, password }                       │
      ├──────────────────────────────────────────────►│
      │                                               │
      │                         2. Validate credentials│
      │                         3. Check account status│
      │                         4. Check security policy│
      │                                               │
      │  5. Return tokens                             │
      │  { access_token, refresh_token, user }        │
      │◄──────────────────────────────────────────────┤
      │                                               │
      │  6. Store tokens in localStorage              │
      │                                               │
      │  7. API Request with Bearer token             │
      │  Authorization: Bearer {access_token}         │
      ├──────────────────────────────────────────────►│
      │                                               │
      │                         8. Validate JWT        │
      │                         9. Check blacklist     │
      │                         10. Check session      │
      │                         11. Process request    │
      │                                               │
      │  12. Return response                          │
      │◄──────────────────────────────────────────────┤
      │                                               │
```

### 7.2 JWT Token Structure

**Access Token**:
```json
{
  "sub": "user-uuid",
  "username": "john.doe",
  "tenant_id": "tenant-uuid",
  "email": "john@example.com",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "token-unique-id",
  "type": "access"
}
```

**Refresh Token**:
```json
{
  "sub": "user-uuid",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "token-unique-id",
  "type": "refresh"
}
```

**Token Expiration**:
- Access Token: 30 minutes (configurable)
- Refresh Token: 7 days (configurable)

### 7.3 Password Security

#### 7.3.1 Hashing

- **Algorithm**: Bcrypt
- **Rounds**: 12 (configurable)
- **Salt**: Automatic per-password salt

#### 7.3.2 Password Policy Enforcement

Configurable per tenant:
- Minimum length (default: 8)
- Complexity requirements (uppercase, lowercase, numbers, special chars)
- Password history (prevent reuse of last N passwords)
- Password expiration (force change after N days)
- Grace logins (allow N logins before forcing change)

#### 7.3.3 Password Validation Flow

```python
def validate_password(password: str, user: User, policy: SecurityPolicy):
    # 1. Check length
    if len(password) < policy.password_min_length:
        raise ValidationError("Password too short")

    # 2. Check complexity
    if policy.password_require_uppercase and not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain uppercase letter")

    # 3. Check history
    history = get_password_history(user.id, policy.password_history_count)
    for old_hash in history:
        if verify_password(password, old_hash):
            raise ValidationError("Password was used recently")

    # 4. Check common passwords
    if password in COMMON_PASSWORDS:
        raise ValidationError("Password is too common")

    return True
```

### 7.4 Account Lockout

#### 7.4.1 Lockout Strategies

**Progressive Lockout**:
- 1st lockout: 5 minutes
- 2nd lockout: 15 minutes
- 3rd lockout: 30 minutes
- 4th+ lockout: 60 minutes

**Fixed Duration Lockout**:
- All lockouts: Configured duration (default: 30 minutes)

#### 7.4.2 Lockout Flow

```python
def check_and_update_lockout(user: User, policy: SecurityPolicy):
    attempts = get_recent_attempts(user.id, policy.lockout_observation_window_minutes)

    if len(attempts) >= policy.lockout_threshold:
        lockout_count = get_lockout_count(user.id)

        if policy.lockout_type == 'progressive':
            duration = calculate_progressive_duration(lockout_count)
        else:
            duration = policy.lockout_duration_minutes

        lock_account(user.id, duration)
        create_lockout_record(user.id, duration)

        raise AccountLockedError(f"Account locked for {duration} minutes")
```

### 7.5 Session Management

#### 7.5.1 Session Tracking

Sessions tracked in `user_sessions` table:
- Session ID (UUID)
- User ID
- Token JTI
- IP Address
- User Agent
- Created At
- Last Activity
- Expires At

#### 7.5.2 Session Timeout

**Idle Timeout**:
- Automatically logs out user after N minutes of inactivity
- Configurable per tenant (default: 30 minutes)

**Absolute Timeout**:
- Maximum session duration regardless of activity
- Configurable per tenant (default: 8 hours)

**Concurrent Sessions**:
- Limit number of active sessions per user
- Oldest sessions terminated when limit exceeded

### 7.6 Permission System

#### 7.6.1 Permission Format

Permissions follow the format: `resource:action:scope`

Examples:
- `users:create:company` - Create users in own company
- `financial:invoices:read:all` - Read all invoices across all companies
- `reports:execute:own` - Execute own reports only

#### 7.6.2 Scopes

- `all` - Access across all tenants (superuser only)
- `tenant` - Access within own tenant
- `company` - Access within assigned companies
- `branch` - Access within assigned branch
- `department` - Access within assigned department
- `own` - Access to own resources only

#### 7.6.3 Permission Checking

```python
def check_permission(user: User, permission: str, resource_id: UUID = None):
    # 1. Get user's permissions (from roles and groups)
    user_permissions = get_user_permissions(user.id)

    # 2. Parse permission
    resource, action, scope = parse_permission(permission)

    # 3. Check if user has matching permission
    for perm in user_permissions:
        if perm.resource == resource and perm.action == action:
            # 4. Check scope
            if perm.scope == 'all':
                return True
            elif perm.scope == 'tenant' and resource_tenant_id == user.tenant_id:
                return True
            elif perm.scope == 'company' and resource_company_id in user.company_ids:
                return True
            elif perm.scope == 'own' and resource_owner_id == user.id:
                return True

    raise PermissionDeniedError()
```

### 7.7 Audit Logging

All security-relevant events are logged:

**Authentication Events**:
- Login (success/failure)
- Logout
- Token refresh
- Password change
- Password reset

**Authorization Events**:
- Permission denied
- Role/permission changes
- Account lockout

**Data Access Events**:
- Create, read, update, delete operations
- Bulk operations
- Export operations

**Audit Log Structure**:
```json
{
  "id": "uuid",
  "timestamp": "2025-11-12T10:30:00Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "action": "users:update",
  "entity_type": "User",
  "entity_id": "uuid",
  "changes": {
    "before": {"email": "old@example.com"},
    "after": {"email": "new@example.com"}
  },
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "status": "success"
}
```

---

## 8. Module System Architecture

### 8.1 Module Lifecycle

```
┌──────────────┐
│  Discovered  │ Module found in filesystem
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Registered  │ Added to module_registry
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Installed   │ Platform-wide installation
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Enabled    │ Per-tenant activation
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Configured  │ Tenant-specific configuration
└──────────────┘
```

### 8.2 Module Structure

```
modules/
└── {module_name}/
    ├── manifest.json          # Module metadata
    ├── module.py              # Module class
    ├── permissions.py         # Permission definitions
    ├── models/                # SQLAlchemy models
    │   └── __init__.py
    ├── routers/               # API endpoints
    │   └── __init__.py
    ├── schemas/               # Pydantic schemas
    │   └── __init__.py
    ├── services/              # Business logic
    │   └── __init__.py
    ├── alembic/               # Module migrations
    │   └── versions/
    ├── templates/             # Frontend templates (optional)
    └── README.md
```

### 8.3 Manifest Schema

```json
{
  "name": "financial",
  "display_name": "Financial Management",
  "version": "1.0.0",
  "description": "Comprehensive financial management module",
  "author": "App-Buildify Team",
  "category": "finance",
  "icon": "currency-dollar",
  "required_subscription_tier": "premium",
  "dependencies": [],
  "permissions": [
    {
      "name": "financial:accounts:read:company",
      "description": "View chart of accounts",
      "resource": "financial_accounts",
      "action": "read",
      "scope": "company"
    }
  ],
  "default_roles": [
    {
      "name": "Financial Manager",
      "permissions": ["financial:*:*:company"]
    }
  ],
  "configuration_schema": {
    "type": "object",
    "properties": {
      "default_currency": {"type": "string", "default": "USD"},
      "fiscal_year_start": {"type": "integer", "default": 1}
    }
  },
  "routes": [
    {
      "path": "/api/v1/financial",
      "router": "routers.financial"
    }
  ]
}
```

### 8.4 Module Base Class

```python
class BaseModule:
    """Abstract base class for all modules"""

    def __init__(self, manifest: dict):
        self.manifest = manifest
        self.name = manifest['name']

    # Lifecycle hooks
    async def pre_install(self):
        """Called before module installation"""
        pass

    async def post_install(self):
        """Called after module installation"""
        pass

    async def pre_enable(self, tenant_id: UUID):
        """Called before module enablement for tenant"""
        pass

    async def post_enable(self, tenant_id: UUID):
        """Called after module enablement for tenant"""
        pass

    async def pre_disable(self, tenant_id: UUID):
        """Called before module disablement"""
        pass

    async def post_disable(self, tenant_id: UUID):
        """Called after module disablement"""
        pass

    async def configure(self, tenant_id: UUID, config: dict):
        """Configure module for tenant"""
        pass

    async def healthcheck(self) -> bool:
        """Check module health"""
        return True
```

### 8.5 Module Discovery & Loading

```python
class ModuleLoader:
    def __init__(self, modules_dir: str = "app/modules"):
        self.modules_dir = modules_dir
        self.modules = {}

    def discover_modules(self) -> List[dict]:
        """Discover all modules in modules directory"""
        modules = []
        for module_dir in os.listdir(self.modules_dir):
            manifest_path = os.path.join(self.modules_dir, module_dir, "manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path) as f:
                    manifest = json.load(f)
                    manifest['path'] = module_dir
                    modules.append(manifest)
        return modules

    def load_module(self, module_name: str) -> BaseModule:
        """Load module class"""
        module_path = f"app.modules.{module_name}.module"
        module = importlib.import_module(module_path)
        return module.Module()

    def register_routes(self, app: FastAPI, module_name: str):
        """Register module routes"""
        manifest = self.get_manifest(module_name)
        for route in manifest.get('routes', []):
            router_path = f"app.modules.{module_name}.{route['router']}"
            router_module = importlib.import_module(router_path)
            app.include_router(
                router_module.router,
                prefix=route['path'],
                tags=[module_name]
            )
```

---

## 9. API Design

### 9.1 API Versioning

**Strategy**: URL path versioning

- Current version: `/api/v1/`
- Legacy endpoints: Root-level (backward compatibility)
- Future versions: `/api/v2/`, `/api/v3/`, etc.

### 9.2 RESTful Conventions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users` | List all users |
| GET | `/api/v1/users/{id}` | Get specific user |
| POST | `/api/v1/users` | Create new user |
| PUT | `/api/v1/users/{id}` | Update user (full) |
| PATCH | `/api/v1/users/{id}` | Update user (partial) |
| DELETE | `/api/v1/users/{id}` | Delete user |

### 9.3 Request/Response Format

#### 9.3.1 Standard Response

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "timestamp": "2025-11-12T10:30:00Z"
}
```

#### 9.3.2 Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "timestamp": "2025-11-12T10:30:00Z"
}
```

#### 9.3.3 Pagination

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_pages": 5,
    "total_items": 100,
    "has_next": true,
    "has_previous": false
  }
}
```

### 9.4 API Documentation

- **Swagger UI**: `/api/docs`
- **ReDoc**: `/api/redoc`
- **OpenAPI Spec**: `/api/openapi.json`

### 9.5 Rate Limiting

**Strategy**: Token bucket algorithm

**Limits**:
- Default: 100 requests per minute
- Authentication: 10 requests per minute
- Bulk operations: 20 requests per minute

**Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
```

---

## 10. Infrastructure & Deployment

### 10.1 Docker Configuration

#### 10.1.1 Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 10.1.2 Frontend Dockerfile

```dockerfile
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy frontend files
COPY frontend/ /usr/share/nginx/html/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

EXPOSE 80
```

### 10.2 Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: app_buildify
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/app_buildify
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

### 10.3 Environment Configuration

**.env file**:
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
DEBUG=false
CORS_ORIGINS=http://localhost:3000,https://app.example.com

# Sentry (optional)
SENTRY_DSN=https://...

# Email (optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user
SMTP_PASSWORD=pass
```

### 10.4 Nginx Configuration

```nginx
server {
    listen 80;
    server_name app.example.com;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN";
        add_header X-Content-Type-Options "nosniff";
        add_header X-XSS-Protection "1; mode=block";
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # GZIP compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    gzip_min_length 1000;
}
```

---

## 11. Performance & Scalability

### 11.1 Database Optimization

**Indexes**:
- Primary keys on all ID columns
- Foreign key indexes
- Tenant ID indexes on all tenant-scoped tables
- Composite indexes for common queries

**Query Optimization**:
- Use of `select_related` and `prefetch_related` (SQLAlchemy 2.0)
- Query result caching
- Connection pooling
- Prepared statements

**Database Pooling**:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 11.2 Caching Strategy

**Redis Caching**:
- Session data
- Token blacklist
- Frequently accessed configuration
- Report results
- Dashboard widget data

**Cache Invalidation**:
- Time-based expiration
- Event-based invalidation
- Manual cache clearing

### 11.3 API Performance

**Response Time Targets**:
- Authentication: < 200ms
- Read operations: < 100ms
- Write operations: < 300ms
- Reports: < 5 seconds

**Optimization Techniques**:
- Database query optimization
- Response compression
- Pagination
- Field filtering
- Async operations

### 11.4 Horizontal Scaling

**Stateless Design**:
- No server-side session storage (JWT tokens)
- Redis for shared state
- Stateless API servers

**Load Balancing**:
- Round-robin load balancing
- Health check endpoints
- Session affinity not required

**Database Scaling**:
- Read replicas for read-heavy workloads
- Connection pooling
- Partitioning by tenant_id (future)

---

## 12. Monitoring & Logging

### 12.1 Application Logging

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "user_login",
    user_id=user.id,
    tenant_id=user.tenant_id,
    ip_address=request.client.host
)
```

**Log Levels**:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

**Log Rotation**:
- Daily rotation
- 30-day retention
- Compressed archives

### 12.2 Health Checks

**Endpoints**:
- `/health`: Basic health check
- `/health/db`: Database connectivity
- `/health/redis`: Redis connectivity
- `/health/modules`: Module status

**Health Check Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T10:30:00Z",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "modules": "ok"
  },
  "version": "1.0.0"
}
```

### 12.3 Error Tracking

**Sentry Integration** (optional):
- Automatic error capture
- Error grouping
- Release tracking
- Performance monitoring

### 12.4 Metrics

**Prometheus Metrics** (optional):
- Request count
- Response time
- Error rate
- Active users
- Database connection pool

---

## 13. Development Guidelines

### 13.1 Code Style

**Backend (Python)**:
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use Black for formatting
- Use isort for import sorting

**Frontend (JavaScript)**:
- Follow Airbnb JavaScript Style Guide
- Use ES6+ features
- Use Prettier for formatting
- Use ESLint for linting

### 13.2 Testing

**Backend Testing**:
- Unit tests: pytest
- Integration tests: pytest with test database
- Coverage target: > 80%

**Frontend Testing**:
- Unit tests: Jest
- E2E tests: Playwright
- Coverage target: > 70%

### 13.3 Git Workflow

**Branch Strategy**:
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches
- `release/*`: Release branches

**Commit Messages**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

### 13.4 Code Review

**Requirements**:
- At least one approval
- All tests passing
- No merge conflicts
- Documentation updated

---

## Appendix

### A. Glossary

- **Tenant**: Top-level organization entity with data isolation
- **Company**: Business unit within a tenant
- **Branch**: Physical location within a company
- **Module**: Pluggable feature package
- **RBAC**: Role-Based Access Control
- **JWT**: JSON Web Token

### B. References

- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Tailwind CSS Documentation: https://tailwindcss.com/docs
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Redis Documentation: https://redis.io/documentation

### C. Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-12 | System | Initial technical specification |

---

**Document Status**: Active
**Next Review Date**: 2026-02-12
