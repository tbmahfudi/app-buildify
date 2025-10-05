# Setup Guide - Option B (Metadata-Driven System)

## Prerequisites

Option B builds on Option A, so you must have:
- ✅ Option A fully implemented and working
- ✅ Database with Option A migrations applied
- ✅ Auth system functional
- ✅ Org CRUD endpoints working

## 🚀 Quick Setup

### 1. Run New Migrations

**PostgreSQL:**
```bash
cd backend
alembic upgrade pg_b2c3d4e5f6a7
```

**MySQL:**
```bash
cd backend
alembic upgrade mysql_a7f6e5d4c3b2
```

**SQLite (Development):**
```bash
cd backend
alembic upgrade head
```

### 2. Seed Metadata

```bash
cd backend
python -m app.seeds.seed_metadata
```

This creates metadata definitions for companies, branches, and departments.

### 3. Restart API Server

```bash
cd backend
uvicorn app.main:app --reload
```

### 4. Test Option B Features

```bash
cd backend
chmod +x test_api_option_b.sh
./test_api_option_b.sh
```

## 📊 What Gets Created

### New Database Tables

1. **entity_metadata** - Stores entity configurations
2. **audit_logs** - Complete audit trail
3. **user_settings** - User preferences
4. **tenant_settings** - Tenant branding and config

### New API Endpoints

**Metadata Service:**
- GET `/api/metadata/entities`
- GET `/api/metadata/entities/{entity}`
- POST `/api/metadata/entities` (admin)
- PUT `/api/metadata/entities/{entity}` (admin)
- DELETE `/api/metadata/entities/{entity}` (admin)

**Generic CRUD:**
- POST `/api/data/{entity}/list`
- GET `/api/data/{entity}/{id}`
- POST `/api/data/{entity}`
- PUT `/api/data/{entity}/{id}`
- DELETE `/api/data/{entity}/{id}`
- POST `/api/data/{entity}/bulk`

**Audit:**
- POST `/api/audit/list`
- GET `/api/audit/{log_id}`
- GET `/api/audit/stats/summary` (admin)

**Settings:**
- GET `/api/settings/user`
- PUT `/api/settings/user`
- GET `/api/settings/tenant`
- PUT `/api/settings/tenant` (admin)

## 🧪 Testing Each Feature

### Test Metadata Service

```bash
TOKEN="your_access_token"

# List all entities
curl http://localhost:8000/api/metadata/entities \
  -H "Authorization: Bearer $TOKEN"

# Get company metadata
curl http://localhost:8000/api/metadata/entities/companies \
  -H "Authorization: Bearer $TOKEN"
```

Expected response includes:
- Entity configuration
- Table columns
- Form fields
- RBAC permissions

### Test Generic CRUD

```bash
# List companies via generic endpoint
curl -X POST http://localhost:8000/api/data/companies/list \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "companies",
    "page": 1,
    "page_size": 10
  }'

# Create via generic endpoint
curl -X POST http://localhost:8000/api/data/companies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "companies",
    "data": {
      "code": "TEST",
      "name": "Test Company"
    }
  }'

# Search with filters
curl -X POST http://localhost:8000/api/data/companies/list \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "companies",
    "filters": [
      {"field": "code", "operator": "like", "value": "TEST"}
    ],
    "sort": [["name", "asc"]],
    "page": 1,
    "page_size": 10
  }'
```

### Test Audit Logs

```bash
# List recent audit logs
curl -X POST http://localhost:8000/api/audit/list \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "companies",
    "page": 1,
    "page_size": 20
  }'

# Get audit statistics (admin only)
curl http://localhost:8000/api/audit/stats/summary \
  -H "Authorization: Bearer $TOKEN"
```

### Test Settings

```bash
# Get user settings
curl http://localhost:8000/api/settings/user \
  -H "Authorization: Bearer $TOKEN"

# Update user settings
curl -X PUT http://localhost:8000/api/settings/user \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "dark",
    "language": "en",
    "density": "compact"
  }'

# Get tenant settings
curl http://localhost:8000/api/settings/tenant \
  -H "Authorization: Bearer $TOKEN"

# Update tenant settings (admin only)
curl -X PUT http://localhost:8000/api/settings/tenant \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "My Company",
    "primary_color": "#0066cc",
    "logo_url": "https://example.com/logo.png"
  }'
```

## 🎯 Adding New Entities

### Example: Adding a Products Entity

**1. Create the Model:**

```python
# backend/app/models/product.py
from sqlalchemy import Column, String, Float, Integer, DateTime, func
from .base import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(50), unique=True, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

**2. Add to Entity Registry:**

```python
# backend/app/routers/data.py
from app.models.product import Product

ENTITY_REGISTRY = {
    "companies": Company,
    "branches": Branch,
    "departments": Department,
    "users": User,
    "products": Product  # Add this line
}
```

**3. Create Migration:**

```bash
alembic revision --autogenerate -m "Add products table"
alembic upgrade head
```

**4. Create Metadata:**

```python
# Add to backend/app/seeds/seed_metadata.py
PRODUCT_METADATA = {
    "entity_name": "products",
    "display_name": "Products",
    "description": "Manage product catalog",
    "icon": "package",
    "table_config": json.dumps({
        "columns": [
            {"field": "sku", "title": "SKU", "sortable": True, "width": 120},
            {"field": "name", "title": "Product Name", "sortable": True, "filterable": True},
            {"field": "price", "title": "Price", "sortable": True, "format": "currency"},
            {"field": "stock", "title": "In Stock", "sortable": True},
            {"field": "created_at", "title": "Created", "sortable": True, "format": "date"}
        ],
        "default_sort": [["name", "asc"]],
        "page_size": 25,
        "actions": ["view", "edit", "delete"]
    }),
    "form_config": json.dumps({
        "fields": [
            {
                "field": "sku",
                "title": "SKU",
                "type": "text",
                "required": True,
                "validators": {"maxLength": 50}
            },
            {
                "field": "name",
                "title": "Product Name",
                "type": "text",
                "required": True,
                "validators": {"maxLength": 255}
            },
            {
                "field": "price",
                "title": "Price",
                "type": "number",
                "required": True,
                "validators": {"min": 0}
            },
            {
                "field": "stock",
                "title": "Stock Quantity",
                "type": "number",
                "default": 0,
                "validators": {"min": 0}
            }
        ],
        "layout": "vertical"
    }),
    "permissions": json.dumps({
        "admin": ["create", "read", "update", "delete"],
        "user": ["read", "update"],
        "viewer": ["read"]
    })
}

# Add insert statement in run() function
conn.execute(text("""
    INSERT INTO entity_metadata (
        id, entity_name, display_name, description, icon,
        table_config, form_config, permissions,
        version, is_active, is_system
    ) VALUES (
        :id, :entity_name, :display_name, :description, :icon,
        :table_config, :form_config, :permissions,
        :version, :is_active, :is_system
    )
"""), dict(
    id=str(uuid.uuid4()),
    version=1,
    is_active=True,
    is_system=False,
    **PRODUCT_METADATA
))
```

**5. Seed and Test:**

```bash
python -m app.seeds.seed_metadata

# Test the new entity
curl -X POST http://localhost:8000/api/data/products/list \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "products",
    "page": 1,
    "page_size": 10
  }'
```

That's it! Your new entity is fully integrated with:
- ✅ Generic CRUD operations
- ✅ Automatic audit logging
- ✅ RBAC enforcement
- ✅ Metadata-driven UI

## 🔧 Configuration

### Filter Operators

The generic list endpoint supports these operators:

- `eq` - Equal
- `ne` - Not equal
- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than
- `lte` - Less than or equal
- `like` - SQL LIKE pattern match
- `in` - Value in list

**Example:**
```json
{
  "filters": [
    {"field": "price", "operator": "gte", "value": 100},
    {"field": "name", "operator": "like", "value": "Pro"},
    {"field": "status", "operator": "in", "value": ["active", "pending"]}
  ]
}
```

### Sorting

Multiple fields can be sorted:

```json
{
  "sort": [
    ["priority", "desc"],
    ["name", "asc"]
  ]
}
```

### Pagination

Control page size and navigate pages:

```json
{
  "page": 2,
  "page_size": 50
}
```

## 📊 Audit Log Actions

The system automatically logs these actions:

**Auth Actions:**
- `LOGIN` - User login
- `LOGOUT` - User logout
- `REFRESH` - Token refresh

**Data Actions:**
- `CREATE` - Record created
- `UPDATE` - Record updated
- `DELETE` - Record deleted
- `BULK_CREATE` - Bulk create operation
- `BULK_UPDATE` - Bulk update operation
- `BULK_DELETE` - Bulk delete operation

**Metadata Actions:**
- `CREATE_METADATA` - Metadata created
- `UPDATE_METADATA` - Metadata updated
- `DELETE_METADATA` - Metadata deleted

**Settings Actions:**
- `UPDATE_USER_SETTINGS` - User settings changed
- `UPDATE_TENANT_SETTINGS` - Tenant settings changed

## 🐛 Troubleshooting

### Migration Issues

**Problem:** "Target database is not up to date"

```bash
# Check current revision
alembic current

# Should show: pg_a1b2c3d4e5f6 (Option A) or pg_b2c3d4e5f6a7 (Option B)

# If needed, stamp the database
alembic stamp head
```

### Import Errors

**Problem:** "No module named 'app.models.metadata'"

Make sure you've created all the new model files:
- `backend/app/models/metadata.py`
- `backend/app/models/audit.py`
- `backend/app/models/settings.py`

### Entity Not Found

**Problem:** "Entity 'xyz' not found"

Check the entity registry in `backend/app/routers/data.py`:

```python
ENTITY_REGISTRY = {
    "companies": Company,
    # Add your entity here
}
```

### Audit Logs Not Working

Make sure you're passing the `Request` object:

```python
from fastapi import Request

@router.post("/endpoint")
def my_endpoint(
    req: Request,  # Add this
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Audit logging will work now
    create_audit_log(db=db, user=current_user, request=req, ...)
```

### Settings Not Persisting

Check that you're committing the database session:

```python
db.add(settings)
db.commit()
db.refresh(settings)
```

## 📈 Performance Tips

### Index Usage

Audit logs are indexed on:
- `user_id`, `tenant_id`, `action`, `entity_type`, `created_at`
- Composite: `(user_id, action)`, `(entity_type, entity_id)`, `(tenant_id, created_at)`

**Query efficiently:**
```json
{
  "user_id": "123",
  "action": "CREATE",
  "start_date": "2025-01-01T00:00:00Z"
}
```

### Pagination

Always use pagination on list endpoints:
- Default: 25 records per page
- Max recommended: 100 records per page

### Caching Strategy

Consider caching:
- **Metadata:** Versioned, cache until version changes
- **User Settings:** Cache per session
- **Tenant Settings:** Cache globally, invalidate on update

## 🔒 Security Best Practices

### 1. Audit Retention

Implement a cleanup job for old audit logs:

```python
# Run periodically
from datetime import datetime, timedelta

cutoff = datetime.utcnow() - timedelta(days=90)
db.query(AuditLog).filter(AuditLog.created_at < cutoff).delete()
db.commit()
```

### 2. Tenant Isolation

Always filter by tenant for non-superusers:

```python
if not current_user.is_superuser and current_user.tenant_id:
    query = query.filter(Model.tenant_id == current_user.tenant_id)
```

### 3. Sensitive Data

Redact sensitive fields in audit logs:

```python
SENSITIVE_FIELDS = ["password", "ssn", "credit_card"]

def redact_sensitive(data: dict) -> dict:
    return {
        k: "***REDACTED***" if k in SENSITIVE_FIELDS else v
        for k, v in data.items()
    }
```

## 📚 API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

All new endpoints are automatically documented!

## ✅ Verification Checklist

After setup, verify:

- [ ] Migrations applied successfully
- [ ] Metadata seeded (3 entities: companies, branches, departments)
- [ ] Can list entities via `/api/metadata/entities`
- [ ] Can get metadata via `/api/metadata/entities/companies`
- [ ] Can list data via `/api/data/companies/list`
- [ ] Can create via `/api/data/companies`
- [ ] Can update via `/api/data/companies/{id}`
- [ ] Can delete via `/api/data/companies/{id}`
- [ ] Audit logs are being created
- [ ] Can list audit logs via `/api/audit/list`
- [ ] Can get/update user settings
- [ ] Can get/update tenant settings (admin)
- [ ] All automated tests pass

## 🚀 Docker Setup

Update your docker-compose to run Option B:

```bash
# Start services
make docker-up

# The Makefile will automatically:
# 1. Run migrations (including Option B tables)
# 2. Seed org data
# 3. Seed users
# 4. Seed metadata (NEW in Option B)
```

Or manually:

```bash
docker-compose -f docker-compose.dev.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed data
docker-compose exec backend python -m app.seeds.seed_org
docker-compose exec backend python -m app.seeds.seed_users
docker-compose exec backend python -m app.seeds.seed_metadata

# Test
docker-compose exec backend ./test_api_option_b.sh
```

## 🎉 You're Ready!

Your NoCode platform now has:

- ✅ **Metadata Service** - Define entities without code
- ✅ **Generic CRUD** - Universal data operations
- ✅ **Complete Audit** - Track every change
- ✅ **User Settings** - Personalization
- ✅ **Tenant Settings** - Branding & features

Start building your entities and let the metadata drive your UI! 🚀

## 🔜 Next Steps

Explore these advanced topics:
- Frontend integration with metadata-driven forms
- Dynamic table rendering from metadata
- Real-time audit trail widgets
- Theme customization from tenant settings
- Custom field widgets and validators

See `OPTION_B_SUMMARY.md` for more details!