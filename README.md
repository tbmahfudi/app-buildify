# Backend Package (Org + Auth + Alembic + Seeds)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and set SECRET_KEY (use: openssl rand -hex 32)

# Run migrations (choose your database)
alembic upgrade head  # SQLite
# OR
export SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://user:pass@localhost/db
alembic upgrade pg_a1b2c3d4e5f6

# Seed data
python -m app.seeds.seed_org
python -m app.seeds.seed_users

# Run API
uvicorn app.main:app --reload
```

## Database Configuration

### PostgreSQL
```bash
export SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://user:pass@localhost/appdb
alembic upgrade pg_a1b2c3d4e5f6
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
# Seed organizations (companies, branches, departments)
python -m app.seeds.seed_org

# Seed users with test credentials
python -m app.seeds.seed_users
```

**Test Users:**
- `admin@example.com` / `admin123` (superuser, all roles)
- `user@example.com` / `user123` (regular user with tenant)
- `viewer@example.com` / `viewer123` (view-only)

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user profile

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

### System
- `GET /api/healthz` - Health check

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Features Implemented

### ✅ Authentication & Authorization
- JWT access tokens (30 min expiry)
- JWT refresh tokens (7 day expiry)
- Automatic token refresh
- Role-based access control (RBAC)
- Multi-tenant support via X-Tenant-Id header
- Superuser bypass
- Password hashing with bcrypt

### ✅ Organization Management
- Complete CRUD for companies, branches, departments
- Unique constraints (code per company)
- Cascading deletes
- Hierarchical relationships
- Foreign key validation

### ✅ Database Support
- PostgreSQL with UUID primary keys
- MySQL with String(36) primary keys
- SQLite for development
- Proper migrations for each database
- Connection pooling with pre-ping

### ✅ Security
- CORS configuration
- Password hashing (bcrypt)
- JWT token validation
- Role enforcement
- Tenant isolation
- SQL injection prevention (ORM)

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

```bash
APP_NAME="NoCode App"
SECRET_KEY="your-secret-key-here"  # Generate with: openssl rand -hex 32
ACCESS_TOKEN_EXPIRE_MIN=30
REFRESH_TOKEN_EXPIRE_DAYS=7
SQLALCHEMY_DATABASE_URL="sqlite:///./app.db"
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8080"
```

## Troubleshooting

### Migration Issues
```bash
# Check current revision
alembic current

# Stamp database to specific revision
alembic stamp head
```

### Token Issues
- Ensure SECRET_KEY is set in .env
- Check token expiry times
- Verify clock sync between client/server

### Database Connection
- Check database is running
- Verify connection string format
- Test with: `alembic current`