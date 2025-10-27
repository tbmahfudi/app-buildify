# App Buildify - Multi-Tenant NoCode Platform

A production-ready, multi-tenant NoCode application platform with comprehensive RBAC, security, and organizational management.

## 🚀 Quick Start

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and set SECRET_KEY (generate with: openssl rand -hex 32)

# Run migrations
alembic upgrade head  # SQLite for development
# OR for PostgreSQL (recommended for production)
export SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://user:pass@localhost/db
alembic upgrade pg_g1h2i3j4k5l6

# Seed multi-tenant data (creates 5 sample organizations)
python -m app.seeds.seed_complete_org

# Run API
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
python -m http.server 8080
# Or use any static file server
```

### Access

- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/api/docs
- **Frontend**: http://localhost:8080

## 📖 Documentation

### **📚 [Backend Documentation](./backend/README.md)** - **Start Here for Backend**
Complete backend API documentation, setup guides, and architecture details.

### **📖 [Documentation Index](./backend/DOCS.md)**
Navigate all backend documentation by topic and use case.

### Key Documentation Files

- **[Backend README](./backend/README.md)** - API setup and usage
- **[Seed Data Guide](./backend/SEED_DATA.md)** - Sample organizations and test data
- **[Architecture Guide](./backend/MODELS_UPDATE_SUMMARY.md)** - Multi-tenant architecture
- **[Security Guide](./backend/SECURITY.md)** - Security and compliance
- **[Token Management](./backend/TOKEN_REVOCATION.md)** - JWT token revocation

## 🎯 Features

### ✅ Multi-Tenant Architecture
- Complete tenant isolation
- Per-tenant companies, branches, departments
- Subscription management
- Usage tracking and limits

### ✅ Authentication & Authorization
- JWT access tokens (30 min expiry) with automatic refresh
- JWT refresh tokens (7 day expiry)
- Database-backed token revocation (no Redis required)
- Role-Based Access Control (RBAC)
- Permission system (resource:action:scope)
- Superuser support

### ✅ Organization Management
- Multi-level hierarchy: Tenant → Company → Branch → Department
- User assignments to organizations
- Multi-company access per user
- Flexible group and role system

### ✅ Security
- bcrypt password hashing
- Input validation and XSS prevention
- SQL injection protection
- Audit logging
- CORS configuration
- Multi-tenant data isolation
- Compliance ready (GDPR, SOC 2, HIPAA)

### ✅ Database Support
- **PostgreSQL** (recommended for production) - UUID primary keys
- **MySQL** - String(36) primary keys
- **SQLite** - Development/testing only
- Complete migrations for all databases
- Connection pooling with pre-ping

## 🔐 Test Credentials

### Superuser (Cross-Tenant Access)
- Email: `superadmin@system.com`
- Password: `SuperAdmin123!`

### Tenant Users (Password: `password123` for all)
- `ceo@techstart.com` - Tech Startup
- `ceo@fashionhub.com` - Retail Chain
- `ceo@medcare.com` - Healthcare Network
- `ceo@cloudwork.com` - Remote-First Tech
- `ceo@fintech.com` - Financial Services

**⚠️ WARNING:** These are development credentials only. Never use in production!

See [SEED_DATA.md](./backend/SEED_DATA.md) for complete test user list.

## 🏗️ Project Structure

```
app-buildify/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── models/      # SQLAlchemy models (16 models)
│   │   ├── routers/     # API endpoints
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── core/        # Auth, config, dependencies
│   │   ├── seeds/       # Seed data scripts
│   │   └── alembic/     # Database migrations
│   ├── README.md        # Backend documentation
│   ├── DOCS.md          # Documentation index
│   ├── SEED_DATA.md     # Seed data guide
│   ├── SECURITY.md      # Security guide
│   └── requirements.txt
├── frontend/            # Static frontend
│   ├── index.html
│   ├── js/
│   └── css/
└── README.md            # This file
```

## 📊 Database Models

The platform includes 16 comprehensive database models:

### Core Multi-Tenant Models
- **Tenant** - Top-level tenant with subscription management
- **Company** - Business entities within tenants
- **Branch** - Physical/virtual locations
- **Department** - Organizational units
- **User** - User accounts with multi-tenant support
- **UserCompanyAccess** - Multi-company user access

### RBAC System
- **Permission** - Granular permissions (resource:action:scope)
- **Role** - Permission collections
- **Group** - User groups
- **RolePermission** - Role ↔ Permission mapping
- **UserRole** - User ↔ Role assignment
- **UserGroup** - User ↔ Group membership
- **GroupRole** - Group ↔ Role assignment

### Supporting Models
- **TokenBlacklist** - Revoked JWT tokens
- **UserSettings** - User preferences
- **TenantSettings** - Tenant branding and configuration

See [MODELS_UPDATE_SUMMARY.md](./backend/MODELS_UPDATE_SUMMARY.md) for detailed schema documentation.

## 🔌 API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /login` - Login (returns tokens with expiration)
- `POST /refresh` - Refresh access token
- `POST /logout` - Logout (revoke token)
- `GET /me` - Get current user profile

### Organizations (`/api/org/`)
- Companies, Branches, Departments
- Full CRUD operations
- Tenant-scoped queries
- Permission-based access control

### System (`/api/`)
- `GET /health` - Comprehensive health check
- `GET /healthz` - Simple health check
- `GET /system/info` - System information

Full API documentation available at `/api/docs` when running.

## 🚢 Deployment

### Production Checklist

1. **Database Setup**
   - Use PostgreSQL (recommended)
   - Run migrations: `alembic upgrade pg_g1h2i3j4k5l6`
   - Configure backups

2. **Security Configuration**
   - Generate strong `SECRET_KEY`: `openssl rand -hex 32`
   - Set `REFRESH_TOKEN_EXPIRE_DAYS=7`
   - Configure CORS `ALLOWED_ORIGINS`
   - Enable HTTPS only
   - Review [SECURITY.md](./backend/SECURITY.md)

3. **Environment Variables**
   ```bash
   SECRET_KEY=<strong-secret-key>
   SQLALCHEMY_DATABASE_URL=postgresql://user:pass@host/db
   ALLOWED_ORIGINS=https://yourdomain.com
   ACCESS_TOKEN_EXPIRE_MIN=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ```

4. **Application Server**
   - Use Gunicorn with Uvicorn workers
   - Configure worker count
   - Set up process manager (systemd/supervisor)
   - Enable logging

5. **Token Cleanup**
   - Schedule cleanup job (see [TOKEN_REVOCATION.md](./backend/TOKEN_REVOCATION.md))
   - Recommended: hourly cleanup

See [SECURITY.md](./backend/SECURITY.md) for complete production deployment checklist.

## 🧪 Development

### Running Tests

```bash
cd backend
pytest
```

### Adding New Features

1. **New Model**: Create in `app/models/`, add to `alembic/env.py`
2. **Migration**: `alembic revision --autogenerate -m "description"`
3. **Schema**: Create Pydantic models in `app/schemas/`
4. **Router**: Create endpoints in `app/routers/`
5. **Dependencies**: Use `get_current_user`, `has_permission` for auth

### Code Structure

```python
# Example endpoint with authentication
from app.core.dependencies import get_current_user, has_permission

@router.get("/items")
def list_items(
    current_user: User = Depends(get_current_user),
    _: User = Depends(has_permission("items:read:all")),
    db: Session = Depends(get_db)
):
    return db.query(Item).filter(Item.tenant_id == current_user.tenant_id).all()
```

## 🤝 Contributing

When contributing:

1. Follow existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure migrations work on all databases
5. Test multi-tenant isolation

## 📋 Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Auth**: PyJWT, passlib
- **Validation**: Pydantic
- **Database**: PostgreSQL/MySQL/SQLite

### Frontend
- **Vanilla JavaScript** (ES6+)
- **CSS3** with custom properties
- **HTML5**
- **No framework dependencies**

## 📈 Version History

- **v0.3.0** (Current) - Multi-tenant architecture with RBAC
  - Complete RBAC system implementation
  - Database-backed token revocation
  - Enhanced security features
  - 5 seed data scenarios

- **v0.2.0** - Basic multi-tenancy
  - Tenant isolation
  - JWT authentication
  - Audit logging

- **v0.1.0** - Initial release
  - Basic CRUD operations
  - Simple authentication

## 📞 Support

- **Documentation**: [./backend/DOCS.md](./backend/DOCS.md)
- **API Docs**: http://localhost:8000/api/docs (when running)
- **Issues**: Use GitHub issues

## ⚖️ License

[Specify your license here]

---

**Built with FastAPI, SQLAlchemy, and modern web standards.**

For detailed backend documentation, see [backend/README.md](./backend/README.md).
