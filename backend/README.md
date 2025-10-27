# Backend Package - Multi-Tenant NoCode Application API

## Version 0.3.0 - Production-Ready with Enhanced Security

A secure, multi-tenant FastAPI backend with comprehensive authentication, authorization, audit logging, and monitoring capabilities.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# IMPORTANT: Set a strong SECRET_KEY
# Generate with: openssl rand -hex 32

# (Optional) Start Redis for token revocation
docker run -d -p 6379:6379 redis:alpine

# Run migrations (choose your database)
alembic upgrade head  # SQLite
# OR for PostgreSQL (recommended for production)
export SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://user:pass@localhost/db
alembic upgrade pg_g1h2i3j4k5l6  # Latest multi-tenant migration

# Seed data (development only - creates 5 sample organizations)
python -m app.seeds.seed_complete_org

# Run API
uvicorn app.main:app --reload
```

## Database Configuration

### PostgreSQL (Recommended for Production)
```bash
export SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://user:pass@localhost/appdb
alembic upgrade pg_g1h2i3j4k5l6  # Multi-tenant architecture
```

### MySQL
```bash
export SQLALCHEMY_DATABASE_URL=mysql+pymysql://user:pass@localhost/appdb
alembic upgrade mysql_f6e5d4c3b2a1
```

### SQLite (Development)
```bash
# Already configured in alembic.ini
alembic upgrade head
```

## Seeding

```bash
# Seed complete multi-tenant organizations
python -m app.seeds.seed_complete_org
```

This creates **5 realistic organizational scenarios**:
- Tech Startup (25 employees)
- Retail Chain (200 employees, 15 stores)
- Healthcare Network (1000+ employees, 3 hospitals)
- Remote-First Tech (150 remote employees)
- Financial Services (500 employees)

**Test Credentials (Development Only):**

**Superuser (Cross-tenant access):**
- Email: `superadmin@system.com`
- Password: `SuperAdmin123!`

**Tenant Users (Password: `password123` for all):**
- `ceo@techstart.com` - Tech Startup
- `ceo@fashionhub.com` - Retail Chain
- `ceo@medcare.com` - Healthcare
- `ceo@cloudwork.com` - Remote Tech
- `ceo@fintech.com` - Financial Services

📖 **See [SEED_DATA.md](./SEED_DATA.md) for complete documentation**

**⚠️ SECURITY WARNING:** Never use these credentials in production! Generate strong, unique passwords.

## API Versioning

All API endpoints are now available under `/api/v1/` for versioned access:
- **New (v1):** `/api/v1/auth/login`
- **Legacy (deprecated):** `/api/auth/login`

The legacy endpoints are maintained for backward compatibility but will be removed in future versions.

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /login` - Login with email/password, returns JWT tokens with expiration
- `POST /refresh` - Refresh access token using refresh token
- `POST /logout` - Revoke current access token (database-backed blacklist)
- `GET /me` - Get current user profile and permissions

### Organizations
- `GET /api/org/companies` - List companies
- `POST /api/org/companies` - Create company (admin)
- `GET /api/org/companies/{id}` - Get company
- `PUT /api/org/companies/{id}` - Update company (admin)
- `DELETE /api/org/companies/{id}` - Delete company (admin)

- `GET /api/org/branches` - List branches
- `POST /api/org/branches` - Create branch (admin)
- `GET /api/org/branches/{id}` - Get branch
- `PUT /api/org/branches/{id}` - Update branch (admin)
- `DELETE /api/org/branches/{id}` - Delete branch (admin)

- `GET /api/org/departments` - List departments
- `POST /api/org/departments` - Create department (admin)
- `GET /api/org/departments/{id}` - Get department
- `PUT /api/org/departments/{id}` - Update department (admin)
- `DELETE /api/org/departments/{id}` - Delete department (admin)

### System & Health
- `GET /` - API information and version
- `GET /api/health` - Comprehensive health check with component status
- `GET /api/healthz` - Simple health check (backward compatibility)
- `GET /api/system/info` - System information and feature list

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## Features Implemented

### ✅ Authentication & Authorization (ENHANCED)
- **JWT Tokens** with JTI (JWT ID) for revocation support
  - Access tokens: 30-minute expiry (configurable)
  - Refresh tokens: 7-day expiry (configurable)
  - Token rotation on refresh
- **Token Revocation** via Redis (graceful fallback if unavailable)
- **Secure Tenant Isolation** - Tenant ID extracted from JWT payload only
  - **SECURITY FIX:** Removed client-controlled X-Tenant-Id header
  - Prevents unauthorized cross-tenant data access
- **Role-Based Access Control (RBAC)**
  - User, Admin, Viewer roles
  - Superuser bypass for cross-tenant operations
- **Password Security** - bcrypt hashing with salt
- **Logout Endpoint** for token revocation

### ✅ Rate Limiting
- **Request throttling** using SlowAPI
- Default: 60 requests/minute per user/IP
- Configurable via environment variables
- User-based rate limiting for authenticated requests
- IP-based fallback for anonymous requests

### ✅ Error Handling & Logging
- **Centralized exception handlers**
  - Validation errors (422)
  - Database integrity errors (409/400)
  - Application-specific errors
  - Unhandled exceptions with traceback logging
- **Structured logging** with structlog
  - JSON logs in production
  - Human-readable logs in development
  - Request context tracking (request_id, user_id, tenant_id)
- **Sentry integration** (optional) for error tracking

### ✅ API Versioning
- **Version 1 (v1)** endpoints: `/api/v1/*`
- **Backward compatibility** with legacy `/api/*` endpoints (deprecated)
- Future-proof architecture for API evolution

### ✅ Monitoring & Observability
- **Comprehensive health checks** with component status
  - Database connectivity
  - Redis availability
  - Rate limiting status
- **Prometheus metrics** (optional, configurable)
- **Request tracking** with unique request IDs

### ✅ Configuration Management
- **Pydantic Settings** for type-safe configuration
- **Environment-based** configuration (.env support)
- **Validation** of all configuration values
- **Multiple environments** (development, staging, production)

### ✅ Input Validation
- **Enhanced Pydantic validators**
  - String length limits
  - Pattern matching (codes, UUIDs)
  - Injection attack prevention
  - JSON sanitization
- **Automatic OpenAPI documentation** of validation rules

### ✅ Testing Infrastructure
- **pytest** test suite
- **Unit tests** for business logic
- **Integration tests** for API endpoints
- **Test fixtures** for database and authentication
- **Faker** for test data generation

### ✅ Organization Management
- Complete CRUD for companies, branches, departments
- Unique constraints (code per company)
- Cascading deletes
- Hierarchical relationships
- Foreign key validation
- Audit logging for all operations

### ✅ Database Support
- PostgreSQL with UUID primary keys
- MySQL with String(36) primary keys
- SQLite for development
- Proper migrations for each database
- Connection pooling with pre-ping
- Session management with dependency injection

### ✅ Audit Logging
- **Comprehensive audit trail** for all operations
- Tracks: user, tenant, action, entity, changes (before/after)
- IP address and user agent logging
- Request ID correlation
- Searchable and filterable
- Tenant-isolated audit logs

## Development

### Adding New Models
1. Create model in `app/models/`
2. Import in `app/alembic/env.py`
3. Generate migration: `alembic revision --autogenerate -m "description"`
4. Review and edit migration files
5. Run: `alembic upgrade head`

### Adding New Endpoints
1. Create schemas in `app/schemas/`
2. Create router in `app/routers/`
3. Use dependencies for auth: `Depends(get_current_user)`
4. Use role checks: `Depends(has_role("admin"))`
5. Include router in `app/main.py`

### Database Sessions
Always use dependency injection:
```python
from app.core.dependencies import get_db

@router.get("/items")
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).all()
```

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```bash
# Application
APP_NAME="NoCode App"
DEBUG=false
ENVIRONMENT="production"  # development, staging, production

# Security (REQUIRED)
SECRET_KEY="your-secret-key-here"  # Generate with: openssl rand -hex 32
ACCESS_TOKEN_EXPIRE_MIN=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
SQLALCHEMY_DATABASE_URL="postgresql+psycopg2://user:pass@localhost/appdb"

# CORS
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8080"

# Redis (Optional - for token revocation)
REDIS_URL="redis://localhost:6379/0"
# OR configure components separately:
# REDIS_HOST="localhost"
# REDIS_PORT=6379
# REDIS_DB=0
# REDIS_PASSWORD="your-redis-password"

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE="app.log"

# Sentry (Optional - for error tracking)
SENTRY_DSN="https://your-sentry-dsn"

# Monitoring (Optional)
ENABLE_METRICS=false
```

### Required Environment Variables

The following environment variables are **required** for production:
- `SECRET_KEY` - Strong random key for JWT signing
- `SQLALCHEMY_DATABASE_URL` - Database connection string
- `ENVIRONMENT` - Set to "production"

### Recommended for Production

- `REDIS_URL` - For token revocation support
- `SENTRY_DSN` - For error tracking and monitoring
- `ALLOWED_ORIGINS` - Restrict to your frontend domains only
- `RATE_LIMIT_ENABLED=true` - Enable request throttling

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/integration/test_auth.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

Test structure:
```
tests/
├── conftest.py          # Test fixtures and configuration
├── unit/                # Unit tests for business logic
└── integration/         # Integration tests for API endpoints
    └── test_auth.py     # Authentication endpoint tests
```

## Troubleshooting

### Migration Issues
```bash
# Check current revision
alembic current

# Stamp database to specific revision
alembic stamp head

# Generate new migration
alembic revision --autogenerate -m "description"
```

### Token Issues
- Ensure `SECRET_KEY` is set in .env and is strong (32+ characters)
- Check token expiry times in environment variables
- Verify clock sync between client/server
- Check Redis connection if using token revocation
- Review logs for token validation errors

### Database Connection
- Check database is running
- Verify connection string format
- Test with: `alembic current`
- Check network connectivity and firewall rules
- Verify database credentials

### Redis Connection (Token Revocation)
```bash
# Test Redis connection
redis-cli ping

# Check if Redis is accessible
docker ps  # if using Docker

# Application will work without Redis but token revocation will be disabled
```

### Rate Limiting Issues
- Check if rate limit is enabled: `RATE_LIMIT_ENABLED=true`
- Verify rate limit settings: `RATE_LIMIT_PER_MINUTE=60`
- Clear rate limit for testing: Restart Redis or wait for TTL expiry
- Authenticated users are rate-limited by user ID, anonymous by IP

### Performance Issues
- Enable database connection pooling
- Configure appropriate `ACCESS_TOKEN_EXPIRE_MIN`
- Use Redis for caching (if enabled)
- Monitor with `/api/health` endpoint
- Check database query performance with logging
- Review structured logs for slow queries

## Security Best Practices

### Production Deployment Checklist

1. **Environment Variables**
   - [ ] Set strong `SECRET_KEY` (use `openssl rand -hex 32`)
   - [ ] Set `ENVIRONMENT=production`
   - [ ] Configure `ALLOWED_ORIGINS` to specific domains
   - [ ] Use PostgreSQL or MySQL (not SQLite)
   - [ ] Enable `RATE_LIMIT_ENABLED=true`

2. **Database**
   - [ ] Use strong database credentials
   - [ ] Enable SSL/TLS for database connections
   - [ ] Regular backups configured
   - [ ] Connection pooling enabled

3. **Redis (Recommended)**
   - [ ] Configure Redis with password authentication
   - [ ] Use Redis for token revocation
   - [ ] Enable Redis persistence if needed

4. **Monitoring**
   - [ ] Configure Sentry for error tracking
   - [ ] Enable structured logging
   - [ ] Set up health check monitoring
   - [ ] Configure log rotation

5. **Network Security**
   - [ ] Use HTTPS in production
   - [ ] Configure firewall rules
   - [ ] Restrict database access to application servers only
   - [ ] Use reverse proxy (nginx/Caddy)

6. **Application Security**
   - [ ] Never use seed data credentials
   - [ ] Implement password complexity requirements
   - [ ] Regular security updates
   - [ ] Review audit logs regularly

## Migration from Previous Versions

### Breaking Changes in v0.3.0

**Tenant Isolation Security Fix:**
- The `X-Tenant-Id` header is **no longer used** for tenant validation
- Tenant ID is now **exclusively extracted from JWT token payload**
- This prevents users from accessing other tenants' data by manipulating headers

**Migration Steps:**
1. Update your frontend to **remove** `X-Tenant-Id` header from requests
2. Tenant context is automatically determined from the JWT token
3. No code changes needed in authentication flow
4. Existing JWT tokens will continue to work

**API Versioning:**
- All endpoints now available under `/api/v1/` prefix
- Legacy `/api/` endpoints maintained for backward compatibility (will be deprecated)
- Update clients to use versioned endpoints: `/api/v1/auth/login`

## Contributing

When adding new features:
1. Add type hints to all functions
2. Write tests for new functionality
3. Update OpenAPI documentation
4. Add audit logging where applicable
5. Follow security best practices
6. Update this README