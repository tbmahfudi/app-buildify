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

---

## Public Portal & Patient-Facing Pages

### When to use a public portal

Create a public portal for any page that must be accessible without a login:

- Clinic or service discovery directories
- Patient self-registration forms
- Appointment booking widgets embedded in external sites
- Any landing page reachable from a public URL or QR code

If a page is for staff or authenticated tenants only, it belongs in the existing
staff SPA (`#/{module}/...`) — not in the public portal.

### Declaring the portal in manifest.json

Add the `public_portal` field to your module's `manifest.json`:

```json
{
  "name": "healthcare",
  "public_portal": {
    "enabled": true,
    "entry_point": "frontend/public/index.html",
    "title": "Find a Clinic"
  },
  "...":  "..."
}
```

- `enabled` — set to `true` to activate the portal; `false` disables it without
  removing the field.
- `entry_point` — relative path to the SPA entry point inside the module package.
- `title` — displayed in browser tabs and any platform-level portal directory.

### Where to put files

Place all public portal assets in:

```
modules/{name}/frontend/public/
└── index.html          ← SPA shell (required)
└── assets/             ← JS/CSS bundles, images
```

The `index.html` must be a self-contained SPA shell. Use **hash fragments** for
client-side routing (`#search`, `#clinic/medcare`, `#register`) so that the
nginx SPA fallback always serves `index.html` regardless of the route.

### URL your portal will be served at

```
/portal/{module_slug}/
```

Example: the healthcare module's portal is at `/portal/healthcare/`.

The platform nginx config serves your `frontend/public/` assets at this path
automatically once `public_portal.enabled` is `true` in your manifest. You do
not need to add any nginx configuration yourself.

### Using the platform OTP service

**Modules must never implement their own OTP logic.** The platform provides a
shared OTP service for all phone-number verification flows (patient registration,
2FA, booking confirmation, etc.).

To verify a phone number in your public portal:

**Step 1 — Send the code**

Your portal's frontend (or a thin backend proxy) calls:

```
POST /api/v1/otp/send
{
  "phone":       "+628123456789",
  "purpose":     "patient_registration",
  "tenant_code": "clinic_medcare"
}
```

Choose a `purpose` string that is unique to your workflow (e.g.
`patient_registration`, `booking_confirm`). The response includes
`resend_after: 60` — honour this in your UI to prevent spam.

**Step 2 — User enters the code; verify it**

```
POST /api/v1/otp/verify
{
  "phone":       "+628123456789",
  "purpose":     "patient_registration",
  "tenant_code": "clinic_medcare",
  "code":        "482910"
}
```

On success you receive:
```json
{ "verified": true, "otp_token": "<uuid>" }
```

**Step 3 — Pass `otp_token` to your registration endpoint**

The `otp_token` is single-use and expires after 5 minutes. Pass it as a field
in your module's own registration request:

```
POST /api/v1/modules/healthcare/patients/register
{
  "otp_token":  "<uuid>",
  "name":       "Budi Santoso",
  "phone":      "+628123456789",
  "tenant_code": "clinic_medcare"
}
```

Your registration endpoint must call the platform's
`consume_otp_token(token, phone, tenant_code, purpose)` helper **before**
creating the patient record. A consumed, expired, or mismatched token returns
`403 Forbidden` — the registration is rejected.

### Patient / user identity

If your module creates its own user type (e.g. `hc_patients`), that identity is
**not** in the platform `users` table. Issue your own JWT with a distinct
`roles` claim (e.g. `"roles": ["hc_patient"]`) so that platform staff
endpoints automatically reject it. Never reuse platform user IDs or tokens for
module-specific patient identities.

### Sub-modules and the public portal

Sub-modules do not get their own `/portal/{sub_module_slug}/` path. Any
public-facing pages for a sub-module must be surfaced through the parent
module's portal (`/portal/{parent_slug}/`). This maintains a single public
URL per clinic service and prevents URL proliferation (see ADR-008 and ADR-010).
