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

---

## Sub-modules

### What is a sub-module?

A **sub-module** is a module that runs *inside* an existing parent service rather than as its
own deployment unit. Sub-modules are used for closely-related features within a single product
domain that share a DB namespace, auth context, and process with their parent.

A **top-level module** gets its own deployment unit (container / process). It may optionally
declare dependencies on other modules, but it is deployed independently.

### When to use each

| Situation | Use |
|-----------|-----|
| Feature is tightly coupled to a parent domain (same DB tables, same auth context) | Sub-module |
| Feature is activated/deactivated alongside the parent, per-tenant | Sub-module |
| Feature could logically stand alone and has no shared DB namespace with a parent | Top-level module |
| Feature needs its own scaling profile or independent deploy cadence | Top-level module |
| You are unsure | Start as a sub-module; graduate later if needed |

### Declaring a sub-module in manifest.json

Add two fields to your `manifest.json`:

```json
{
  "name": "healthcare-lab",
  "parent_module": "healthcare",
  "deployment": { "mode": "inherit" },
  "display_name": "Healthcare — Lab",
  "...": "..."
}
```

- `parent_module` — the `name` value of the already-installed parent module. The install
  pipeline validates that the parent exists before accepting the sub-module.
- `deployment.mode` — must be `"inherit"` for sub-modules. This tells the installer to skip
  container provisioning and reuse the parent's runtime environment.

### Install behaviour

| Module type | Install result |
|-------------|----------------|
| Top-level (`parent_module: null`) | Standard pipeline: new container / embedded service, own Alembic chain |
| Sub-module (`parent_module: "<name>"`) | Files injected into parent service directory; parent reloads routes; no new container |

The install pipeline branch (pseudocode):

```
if manifest.parent_module:
    -> validate parent module is installed
    -> inject sub-module files into parent service directory
    -> signal parent service to reload routes
else:
    -> standard install (embedded or standalone)
```

### Graduation path — promoting a sub-module to top-level

Promotion is an **explicit architectural migration**, not a runtime toggle.

Steps:

1. Remove `parent_module` from the manifest.
2. Declare the former parent as a `dependencies.required` entry so the install pipeline still
   validates the parent is present.
3. Change `deployment.mode` from `"inherit"` to `"embedded"` or `"standalone"`.
4. Write an Alembic migration to move any DB tables you own into your own namespace (rename
   `hc_lab_*` to `lab_*`, for example).
5. Bump the module version and publish the new tarball.

Downstream effects: the install pipeline will now provision a new deployment unit for the
module. Inform the platform team (file a `platform-requests/open/REQ-NNN.md`) so infrastructure
is updated.

### Worked example — Healthcare

The healthcare domain deploys as **one standalone service** (`app_buildify_healthcare`) with
five modules inside it:

```
app_buildify_healthcare  (one standalone service)
├── core              <- always active; owns the hc_* DB namespace
├── healthcare-lab        <- per-tenant; runs inside healthcare service
├── healthcare-billing    <- per-tenant; runs inside healthcare service
├── healthcare-pharmacy   <- per-tenant; runs inside healthcare service
└── healthcare-scheduling <- per-tenant; runs inside healthcare service
```

`manifest.json` for `healthcare-lab`:

```json
{
  "name": "healthcare-lab",
  "display_name": "Healthcare — Lab",
  "version": "1.0.0",
  "parent_module": "healthcare",
  "deployment": { "mode": "inherit" },
  "subscription_tier": "enterprise",
  "dependencies": {
    "required": ["healthcare"]
  }
}
```

All `healthcare-*` sub-modules prefix DB tables with `hc_` to share the parent's namespace
without conflicts. The parent module (`healthcare/core`) owns that namespace; sub-modules lease
from it and must not create tables outside it.
