# Changes Required to Existing Code

This document lists all modifications needed to existing files to implement the open module development architecture.

---

## BACKEND CHANGES

### 1. **backend/app/main.py**

**Current**: Loads modules directly from filesystem
**Change**: Add Core API Gateway router

```python
# ADD THIS IMPORT
from app.routers import core_api

# ADD THIS ROUTER (after existing routers around line 179)
app.include_router(core_api.router, prefix="/api/v1")
```

**Location**: After line 179 (after admin_security router)

**Why**: Expose Core API endpoints for modules to call

---

### 2. **backend/requirements.txt**

**Current**: Has basic FastAPI dependencies
**Change**: Add httpx for SDK

```txt
# ADD THESE LINES
httpx  # For SDK to make HTTP requests to Core API
```

**Location**: After line 44 (after faker)

**Why**: SDK needs httpx to call Core API

---

### 3. **backend/app/core/module_system/registry.py**

**Current**: Loads modules from local filesystem
**Change**: Add support for remote modules (optional - Phase 2)

**Option A - No changes needed**: Keep current behavior for now
**Option B - Future enhancement**: Add method to register remote modules

```python
# ADD THIS METHOD to ModuleRegistryService class (around line 300)

def register_remote_module(
    self,
    module_name: str,
    backend_url: str,
    api_key: str
) -> None:
    """
    Register a remote module that runs on separate server.

    Args:
        module_name: Module identifier
        backend_url: URL of module's backend API
        api_key: API key for module authentication
    """
    # Store remote module info in database
    # Module calls will be proxied to backend_url
    pass
```

**Status**: OPTIONAL - Can defer to Phase 7 (Deployment)

---

### 4. **backend/app/models/** (New Model)

**Current**: No API key model
**Action**: CREATE NEW FILE

**File**: `backend/app/models/api_key.py`

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .base import BaseModel

class APIKey(BaseModel):
    """API keys for module authentication"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    module_name = Column(String(100))
    environment = Column(String(20))  # dev, staging, prod
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    created_by = Column(Integer)  # user_id who created it
```

**Why**: Store API keys for module authentication

---

### 5. **backend/app/core/auth.py**

**Current**: Has JWT token functions
**Change**: Add API key verification function

```python
# ADD THIS FUNCTION (around line 100, after existing functions)

def verify_api_key(api_key: str, db: Session) -> Optional[dict]:
    """
    Verify API key and return associated module info.

    Args:
        api_key: The API key to verify
        db: Database session

    Returns:
        Dict with module_name and permissions, or None if invalid
    """
    from app.models.api_key import APIKey
    from datetime import datetime

    key_record = db.query(APIKey).filter(
        APIKey.key == api_key,
        APIKey.is_active == True
    ).first()

    if not key_record:
        return None

    # Check expiration
    if key_record.expires_at and key_record.expires_at < datetime.utcnow():
        return None

    # Update last used
    key_record.last_used_at = datetime.utcnow()
    db.commit()

    return {
        "module_name": key_record.module_name,
        "environment": key_record.environment,
        "key_id": key_record.id
    }
```

**Location**: Add to `backend/app/core/auth.py`
**Why**: Verify API keys from modules

---

### 6. **backend/app/models/__init__.py**

**Current**: Imports all models
**Change**: Add API key model import

```python
# ADD THIS LINE (after other imports)
from .api_key import APIKey
```

**Location**: Around line 20, with other model imports

---

### 7. **backend/app/core/dependencies.py**

**Current**: Has get_current_user dependency
**Change**: Add get_current_module dependency (optional)

```python
# ADD THIS FUNCTION (after get_current_user)

async def get_current_module(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to verify module API key.
    Use in Core API endpoints.
    """
    from app.core.auth import verify_api_key

    module_info = verify_api_key(x_api_key, db)
    if not module_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key"
        )

    return module_info
```

**Why**: Reusable dependency for Core API endpoints

---

## FRONTEND CHANGES

### 8. **frontend/assets/js/app.js**

**Current**: Initializes app
**Change**: Initialize global Buildify API

```javascript
// ADD THIS NEAR THE TOP (after imports, around line 10)
import './buildify-global-api.js';

// MODIFY initApp() function to initialize global API
async function initApp() {
    // ... existing code ...

    // ADD THIS BEFORE RETURN
    // Initialize Buildify Global API
    if (window.buildify) {
        console.log('Buildify Global API initialized:', window.buildify.version);
    }

    // ... rest of existing code ...
}
```

**Location**: In `initApp()` function
**Why**: Make global API available to all modules

---

### 9. **frontend/assets/js/app-entry.js**

**Current**: Imports various modules
**Change**: Import global API

```javascript
// ADD THIS IMPORT (after resource-loader import, around line 3)
import './buildify-global-api.js';

// Rest of file stays the same
```

**Location**: After line 2
**Why**: Load global API early in app lifecycle

---

### 10. **frontend/index.html**

**Current**: Loads app-entry.js
**Change**: No changes needed (already using ES6 modules)

**Status**: ✅ NO CHANGES NEEDED

---

### 11. **frontend/assets/js/api.js** or **data-service.js**

**Current**: Has API client implementation
**Change**: Expose as part of global API (in buildify-global-api.js)

**Status**: NO CHANGES to existing file - we'll reference it from global API

---

### 12. **frontend/assets/js/router.js**

**Current**: Has SPA router
**Change**: Expose router via global API

**Status**: NO CHANGES to existing file - we'll reference it from global API

---

### 13. **frontend/assets/js/auth-service.js**

**Current**: Has auth functions
**Change**: Expose via global API

**Status**: NO CHANGES to existing file - we'll reference it from global API

---

## CONFIGURATION CHANGES

### 14. **backend/.env.example**

**Current**: Has core environment variables
**Change**: Add Core API configuration

```bash
# ADD THESE LINES

# Core API Settings (for modules to connect)
CORE_API_URL=http://localhost:8000
CORE_API_KEY=dev_key_123

# API Key Management
API_KEY_SECRET=your-secret-key-for-generating-api-keys
```

**Location**: At the end of file
**Why**: Document new environment variables

---

### 15. **docker-compose.yml**

**Current**: Has core services
**Change**: Add environment variables for Core API

```yaml
# MODIFY backend service
  backend:
    # ... existing config ...
    environment:
      # ... existing vars ...
      # ADD THESE
      - CORE_API_URL=http://backend:8000
      - API_KEY_SECRET=${API_KEY_SECRET:-dev-secret}
```

**Location**: In backend service section
**Why**: Configure Core API URL for development

---

### 16. **backend/alembic/versions/** (New Migration)

**Action**: CREATE NEW MIGRATION

**Command to run**:
```bash
cd backend
alembic revision -m "add_api_keys_table"
```

**Migration content**:
```python
# In the generated migration file

def upgrade():
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('module_name', sa.String(length=100)),
        sa.Column('environment', sa.String(length=20)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_keys_key', 'api_keys', ['key'], unique=True)

def downgrade():
    op.drop_index('ix_api_keys_key', table_name='api_keys')
    op.drop_table('api_keys')
```

**Why**: Database table for API keys

---

## NEW FILES TO CREATE

### Backend - Core Files

1. ✅ **backend/app/routers/core_api.py** - NEW
   Core API Gateway with auth, RBAC, tenant endpoints

2. ✅ **backend/app/models/api_key.py** - NEW
   API key model for module authentication

3. ✅ **backend/app/services/rbac_service.py** - NEW (if doesn't exist)
   RBAC service for permission checking
   - **Check first**: May already exist in routers/rbac.py

### Backend - SDK Files (Separate Package)

4. ✅ **backend/sdk/** - NEW DIRECTORY
   Entire SDK package structure:
   ```
   backend/sdk/
   ├── setup.py
   ├── README.md
   ├── buildify_sdk/
   │   ├── __init__.py
   │   ├── client.py
   │   ├── dependencies.py
   │   ├── exceptions.py
   │   ├── schemas.py
   │   └── testing/
   │       ├── __init__.py
   │       ├── mock_core.py
   │       └── fixtures.py
   ```

### Frontend - New Files

5. ✅ **frontend/assets/js/buildify-global-api.js** - NEW
   Global API exposed to modules (`window.buildify`)

### Module Development Kit

6. ✅ **module-dev-kit/** - NEW DIRECTORY
   Complete developer kit:
   ```
   module-dev-kit/
   ├── template/
   ├── mock-core/
   ├── docs/
   └── examples/
   ```

### Documentation

7. ✅ **docs/** - NEW DIRECTORY
   Developer documentation site

---

## SUMMARY OF CHANGES

### 📝 Modify Existing Files (11 files)

**Backend (7 files):**
- ✏️ `backend/app/main.py` - Add core_api router
- ✏️ `backend/requirements.txt` - Add httpx
- ✏️ `backend/app/core/auth.py` - Add verify_api_key()
- ✏️ `backend/app/core/dependencies.py` - Add get_current_module()
- ✏️ `backend/app/models/__init__.py` - Import APIKey
- ✏️ `backend/.env.example` - Add Core API vars
- ✏️ `docker-compose.yml` - Add environment vars

**Frontend (2 files):**
- ✏️ `frontend/assets/js/app.js` - Initialize global API
- ✏️ `frontend/assets/js/app-entry.js` - Import global API

**Config (2 files):**
- ✏️ `.env.example` - Document new vars
- ✏️ `docker-compose.yml` - Configure services

---

### ✨ Create New Files (30+ files)

**Backend Core (3 files):**
- 📄 `backend/app/routers/core_api.py`
- 📄 `backend/app/models/api_key.py`
- 📄 `backend/alembic/versions/xxx_add_api_keys.py` (migration)

**Backend SDK (10+ files):**
- 📁 `backend/sdk/` (entire package)

**Frontend (1 file):**
- 📄 `frontend/assets/js/buildify-global-api.js`

**Module Dev Kit (15+ files):**
- 📁 `module-dev-kit/` (complete kit)

**Documentation (20+ files):**
- 📁 `docs/` (complete docs site)

---

## MIGRATION PATH

### Phase 1: Core API Setup (Essential)
1. Create `backend/app/routers/core_api.py`
2. Create `backend/app/models/api_key.py`
3. Modify `backend/app/main.py` (add router)
4. Modify `backend/app/core/auth.py` (add verify_api_key)
5. Modify `backend/app/models/__init__.py` (import APIKey)
6. Create migration for api_keys table
7. Run migration

### Phase 2: Frontend Global API (Essential)
1. Create `frontend/assets/js/buildify-global-api.js`
2. Modify `frontend/assets/js/app-entry.js` (import)
3. Modify `frontend/assets/js/app.js` (initialize)

### Phase 3: SDK Package (Essential for module devs)
1. Create `backend/sdk/` structure
2. Implement CoreAPIClient
3. Implement dependencies
4. Create mock core API

### Phase 4: Dev Kit (Nice to have)
1. Create module template
2. Create docker-compose for testing
3. Create documentation

---

## TESTING CHANGES

After implementing changes, test:

1. **Core API endpoints work**:
   ```bash
   curl -H "X-API-Key: dev_key_123" \
        http://localhost:8000/api/v1/core/auth/verify \
        -d '{"token":"your-jwt-token"}'
   ```

2. **Global API available in browser**:
   ```javascript
   console.log(window.buildify);  // Should show API object
   ```

3. **Existing functionality still works**:
   - Login/logout
   - RBAC
   - Module loading
   - All existing routes

---

## BACKWARD COMPATIBILITY

✅ **All changes are backward compatible:**

- Existing routes unchanged
- Existing models unchanged
- Existing frontend code works as before
- New Core API is additive only
- Existing modules continue to work

**Breaking changes**: NONE

---

## ROLLBACK PLAN

If needed, rollback is simple:

1. Remove `core_api` router from main.py
2. Remove new files (core_api.py, api_key.py, etc.)
3. Rollback database migration
4. Remove global API from frontend

All existing code continues to work.

---

## NEXT STEPS

**Minimal viable implementation** (to start testing):

1. ✅ Create `backend/app/routers/core_api.py` (200 lines)
2. ✅ Create `backend/app/models/api_key.py` (20 lines)
3. ✅ Modify `backend/app/main.py` (1 line)
4. ✅ Create migration (30 lines)
5. ✅ Create `frontend/assets/js/buildify-global-api.js` (200 lines)
6. ✅ Modify frontend entry files (2 lines each)

**Total**: ~450 lines of new code + 5 lines changed in existing files

**Time estimate**: 4-6 hours for minimal implementation

Would you like me to start implementing these changes?
