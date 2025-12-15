# Module Self-Registration System

## Overview

This document describes the **Push-Based Self-Registration** system implemented for module synchronization between modules and the core platform.

## Architecture

```
┌─────────────────┐                    ┌─────────────────┐
│  Module Backend │                    │  Core Platform  │
│   (Financial)   │                    │    Backend      │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │ 1. Module Starts                     │
         │                                      │
         │ 2. Load manifest.json                │
         │                                      │
         │ 3. POST /api/v1/modules/register     │
         │────────────────────────────────────> │
         │                                      │
         │                                      │ 4. Validate manifest
         │                                      │
         │                                      │ 5. Store in database
         │                                      │
         │ 6. Return success response           │
         │ <────────────────────────────────────│
         │                                      │
         │ 7. Module ready to serve requests    │
         │                                      │
         │                                      │
         │ 8. (Optional) Periodic heartbeat     │
         │ POST /api/v1/modules/{name}/heartbeat│
         │────────────────────────────────────> │
         │                                      │
         │ 9. Acknowledgment                    │
         │ <────────────────────────────────────│
         │                                      │
```

## Key Components

### 1. Core Platform Registration Endpoint

**Endpoint:** `POST /api/v1/modules/register`

**Location:** `backend/app/routers/modules.py`

**Request Schema:**
```json
{
  "manifest": {
    "name": "financial",
    "display_name": "Financial Management",
    "version": "1.0.0",
    "backend_service_url": "http://financial-module:9001",
    ...
  },
  "backend_service_url": "http://financial-module:9001",
  "health_check_url": "http://financial-module:9001/health"
}
```

**Response Schema:**
```json
{
  "success": true,
  "message": "Module 'financial' registered successfully",
  "module_name": "financial",
  "registered_at": "2025-01-15T10:30:00Z",
  "should_install": false
}
```

**Behavior:**
- **No Authentication Required** - Modules can register during startup before users authenticate
- **Idempotent** - Can be called multiple times safely
- **Creates or Updates** - If module exists, updates it; otherwise creates new entry
- **Stores in Database** - Updates `module_registry` table with latest manifest

### 2. Module Registration Logic

**Location:** `modules/financial/backend/app/main.py`

**Function:** `register_with_core_platform()`

**Features:**
- ✅ Loads manifest from filesystem
- ✅ Constructs registration payload
- ✅ Implements retry logic with exponential backoff (2s, 4s, 8s, 16s, 32s)
- ✅ Maximum 5 retry attempts
- ✅ Detailed logging of registration status
- ✅ Graceful error handling

**Integration:**
- Called during FastAPI lifespan startup
- Runs asynchronously
- Non-blocking - module continues even if registration fails temporarily

### 3. Heartbeat Endpoint (Optional)

**Endpoint:** `POST /api/v1/modules/{module_name}/heartbeat`

**Purpose:** Allow modules to periodically signal they are healthy

**Request Schema:**
```json
{
  "module_name": "financial",
  "version": "1.0.0",
  "status": "healthy",
  "metadata": {}
}
```

**Response Schema:**
```json
{
  "success": true,
  "message": "Heartbeat received",
  "last_seen": "2025-01-15T10:30:00Z"
}
```

## Registration Flow

### Step 1: Module Startup

When a module backend starts (e.g., `financial-module`):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... other startup tasks ...

    # Register with core platform
    await register_with_core_platform()

    yield

    # ... shutdown tasks ...
```

### Step 2: Load Manifest

Module reads its `manifest.json` file:

```python
manifest_path = Path(__file__).parent.parent.parent / "manifest.json"
with open(manifest_path, 'r') as f:
    manifest = json.load(f)
```

### Step 3: Prepare Registration Data

Module constructs the registration payload:

```python
registration_data = {
    "manifest": manifest,
    "backend_service_url": "http://financial-module:9001",
    "health_check_url": "http://financial-module:9001/health"
}
```

### Step 4: Send Registration Request

Module sends POST request to core platform:

```python
async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.post(
        f"{CORE_PLATFORM_URL}/api/v1/modules/register",
        json=registration_data
    )
```

### Step 5: Handle Response

Core platform validates and stores the module:

```python
# Check if module exists
existing_module = db.query(ModuleRegistry).filter(
    ModuleRegistry.name == module_name
).first()

if existing_module:
    # Update existing module
    existing_module.manifest = manifest
    existing_module.version = manifest.get('version')
    # ... update other fields ...
else:
    # Create new module entry
    new_module = ModuleRegistry(...)
    db.add(new_module)

db.commit()
```

### Step 6: Retry Logic

If registration fails, module retries with exponential backoff:

```
Attempt 1: Immediate
Attempt 2: Wait 2 seconds
Attempt 3: Wait 4 seconds
Attempt 4: Wait 8 seconds
Attempt 5: Wait 16 seconds
```

## Database Schema

The `module_registry` table stores registered modules:

```sql
CREATE TABLE module_registry (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    manifest JSONB NOT NULL,
    backend_service_url VARCHAR(500),  -- Extracted from manifest
    is_installed BOOLEAN DEFAULT TRUE,
    is_enabled BOOLEAN DEFAULT TRUE,
    installed_at TIMESTAMP,
    updated_at TIMESTAMP,
    -- ... other fields ...
);
```

**Key Field:** `manifest.backend_service_url` - Used by core to fetch live manifests

## Startup Order

Docker Compose ensures correct startup order:

```yaml
financial-module:
  depends_on:
    postgres:
      condition: service_healthy
    core-platform:
      condition: service_started  # Core must start before modules
```

This guarantees:
1. ✅ Database is ready
2. ✅ Core platform is running
3. ✅ Module can register successfully

## Error Handling

### Connection Errors

If core platform is not reachable:

```
✗ Cannot connect to core platform (attempt 1/5): Connection refused
  Retrying in 2 seconds...
✗ Cannot connect to core platform (attempt 2/5): Connection refused
  Retrying in 4 seconds...
...
```

### Validation Errors

If manifest is invalid:

```
✗ Registration failed: Module manifest must contain 'name' field
```

### Registration Success

When registration succeeds:

```
Registering financial with core platform...
✓ Successfully registered with core platform: Module 'financial' registered successfully
financial started successfully on port 9001
```

## Advantages of This Approach

### ✅ Simplicity
- Straightforward HTTP POST request
- No external dependencies (no message queue, no service registry)
- Easy to understand and debug

### ✅ Immediate Registration
- Module knows instantly if registration succeeded
- No polling delay
- Fast feedback loop

### ✅ Controlled Startup
- Docker Compose `depends_on` ensures correct order
- Retry logic handles temporary unavailability
- Graceful degradation

### ✅ Idempotent
- Safe to call multiple times
- Module can re-register on restart
- Updates existing entries

### ✅ No Authentication Required
- Modules can register before any user logs in
- Suitable for startup phase
- Can add API key authentication later if needed

## Testing

### Manual Test

1. Start core platform:
   ```bash
   docker-compose up core-platform postgres redis -d
   ```

2. Watch logs for module registration:
   ```bash
   docker-compose logs -f financial-module
   ```

3. Start financial module:
   ```bash
   docker-compose up financial-module -d
   ```

4. Check logs for registration success:
   ```
   ✓ Successfully registered with core platform
   ```

5. Verify in database:
   ```sql
   SELECT name, version, is_installed, updated_at
   FROM module_registry
   WHERE name = 'financial';
   ```

### Automated Test

```python
import httpx
import pytest

@pytest.mark.asyncio
async def test_module_registration():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/modules/register",
            json={
                "manifest": {
                    "name": "test-module",
                    "display_name": "Test Module",
                    "version": "1.0.0"
                },
                "backend_service_url": "http://test-module:9999"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["module_name"] == "test-module"
```

## Future Enhancements

### Phase 2: Heartbeat Monitoring

Implement periodic heartbeats to detect unhealthy modules:

```python
async def send_heartbeat():
    while True:
        await asyncio.sleep(30)  # Every 30 seconds
        await client.post(
            f"{CORE_PLATFORM_URL}/api/v1/modules/financial/heartbeat",
            json={
                "module_name": "financial",
                "version": "1.0.0",
                "status": "healthy"
            }
        )
```

### Phase 3: Health Monitoring

Core platform background task to check module health:

```python
async def monitor_module_health():
    while True:
        await asyncio.sleep(60)  # Every minute

        modules = db.query(ModuleRegistry).filter(
            ModuleRegistry.is_installed == True
        ).all()

        for module in modules:
            if module.updated_at < now() - timedelta(minutes=5):
                # Module hasn't sent heartbeat in 5 minutes
                module.status = "unhealthy"
                db.commit()
```

### Phase 4: Deregistration

Add endpoint for modules to deregister on shutdown:

```python
@router.post("/{module_name}/deregister")
async def deregister_module(module_name: str, db: Session):
    module = db.query(ModuleRegistry).filter(
        ModuleRegistry.name == module_name
    ).first()

    if module:
        module.is_installed = False
        db.commit()

    return {"success": True}
```

## Troubleshooting

### Module fails to register

**Symptom:**
```
✗ Failed to register with core platform after 5 attempts
```

**Solutions:**
1. Check core platform is running: `docker-compose ps core-platform`
2. Check network connectivity: `docker-compose exec financial-module ping core-platform`
3. Check core platform logs: `docker-compose logs core-platform`
4. Verify DATABASE_URL is correct in core platform

### Module registers but doesn't appear in UI

**Symptom:** Registration succeeds but menus don't show

**Solutions:**
1. Check module is enabled for tenant:
   ```sql
   SELECT * FROM tenant_modules WHERE module_id = (
     SELECT id FROM module_registry WHERE name = 'financial'
   );
   ```

2. Enable module for tenant:
   ```bash
   curl -X POST http://localhost:8000/api/v1/modules/enable \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"module_name": "financial"}'
   ```

3. Check user has permissions to see menu items

### Manifest validation errors

**Symptom:**
```
✗ Registration failed: ValidationError
```

**Solutions:**
1. Validate manifest JSON syntax
2. Ensure all required fields are present:
   - `name`
   - `display_name`
   - `version`
3. Check manifest matches schema in `app/schemas/module.py`

## See Also

- [Module Sync Options](./MODULE_SYNC_OPTIONS.md) - Comparison of all sync approaches
- [Module Architecture](./MODULE_ARCHITECTURE.md) - Overall module system design
- [API Documentation](http://localhost:8000/docs) - Full API reference
