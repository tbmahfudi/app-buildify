# Creating a Module — Step-by-Step Guide

---

## 1. Scaffold from the template

```bash
manage.sh module new my_module
```

This copies `modules/template/` to `modules/my_module/` and replaces all
`TEMPLATE` placeholders with `my_module`.

Alternatively, copy manually:
```bash
cp -r modules/template/ modules/my_module/
find modules/my_module -type f | xargs sed -i 's/TEMPLATE/my_module/g'
```

---

## 2. Fill in `manifest.json`

Edit `modules/my_module/manifest.json`:

- Set `name`, `display_name`, `description`, `author`
- Define `routes` — one entry per page, with `permission` and `menu` keys
- List `permissions` your module introduces
- Set `subscription_tier` (`free` / `basic` / `premium` / `enterprise`)

---

## 3. Implement `module.py`

Rename `MyModuleModule` class. Implement:

```python
def get_router(self) -> APIRouter:
    from .routes import router
    return router

def get_permissions(self) -> List[Dict]:
    return self.manifest.get("permissions", [])

def get_models(self):
    from .models import MyModel
    return [MyModel]
```

Add business logic to `post_install` / `post_enable` hooks as needed.

---

## 4. Write routes in `routes.py`

All routes must use the prefix `/api/v1/modules/my_module/`:

```python
router = APIRouter(prefix="/api/v1/modules/my_module", tags=["my_module"])

@router.get("/items")
async def list_items(db: Session = Depends(get_db), user=Depends(current_user)):
    ...
```

---

## 5. Write models in `models.py`

```python
class MyItem(Base):
    __tablename__ = "my_module_items"
    __tenant_scoped__ = True          # required

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(36), nullable=False, index=True)  # required
    ...
```

---

## 6. Write migrations

Add an Alembic migration in `modules/my_module/migrations/`:

```bash
cd backend
alembic revision -m "001_initial_my_module_tables"
# edit the generated file, then:
alembic upgrade head
```

See `migrations/README.md` inside your module for details.

---

## 7. Build the module

```bash
manage.sh module pack my_module
```

This produces `my_module_v1.0.0.tar.gz` in the current directory (or `--out <dir>`).

---

## 8. Install the module

```bash
manage.sh module install my_module_v1.0.0.tar.gz
```

The 8-step pipeline:
1. Validates the tarball and manifest
2. Extracts to a staging directory
3. Registers in the module registry
4. Runs Alembic migrations
5. Copies backend files to `backend/modules/my_module/`
6. Copies frontend files to `frontend/assets/modules/my_module/`
7. Registers routes with the platform router
8. Marks the module as installed and available

---

## 9. Enable for a tenant

Via the admin UI: **Settings → Modules → my_module → Enable**

Or via the API:
```
POST /api/v1/admin/modules/my_module/activate
{ "tenant_id": "your-tenant-id" }
```

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Import error on startup | Ensure you only import from `modules.sdk`, not `backend.app` |
| 403 on API calls | Verify the permission code in manifest matches what the route checks |
| Data leaking between tenants | Check every model has `__tenant_scoped__ = True` and `tenant_id` column |
| Migration fails | Run `alembic history` to check for conflicts |
