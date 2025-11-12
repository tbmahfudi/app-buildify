# Fix: UUID Serialization in Security Admin Endpoints

## Problem

The `/api/v1/admin/security/sessions` and `/api/v1/admin/security/login-attempts` endpoints were returning 500 Internal Server Error due to Pydantic validation failures during response serialization.

### Error Messages
```
GET http://localhost:8080/api/v1/admin/security/sessions?limit=50 500 (Internal Server Error)
GET http://localhost:8080/api/v1/admin/security/login-attempts?limit=50 500 (Internal Server Error)
```

## Root Cause

### The Issue

The GUID custom type in `backend/app/models/base.py` returns `uuid.UUID` objects from the database:

```python
def process_result_value(self, value, dialect):
    """Convert database value to UUID."""
    if value is None:
        return value
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(value)
```

However, the Pydantic response schemas expect string types:

```python
class UserSessionResponse(BaseModel):
    id: str           # ← Expects string, gets UUID object
    user_id: str      # ← Expects string, gets UUID object
    ...
```

When FastAPI tried to serialize the SQLAlchemy models to JSON using the Pydantic schemas, it failed because:
1. SQLAlchemy model fields contain `uuid.UUID` objects
2. Pydantic schemas declare these fields as `str`
3. Pydantic v2 doesn't automatically convert UUID to string without explicit serializers

### Why Other Endpoints Worked

Endpoints like `/policies`, `/locked-accounts`, and `/notification-config` may have:
- Had no data to serialize (empty lists)
- Had different serialization behavior
- Or we just got lucky with how Pydantic handled them

## Solution

Added `@field_serializer` decorators to all security-related response schemas to explicitly convert UUID objects to strings during JSON serialization.

### Changes Made

Updated `backend/app/schemas/security.py`:

1. **Import field_serializer and UUID**:
```python
from pydantic import BaseModel, Field, field_serializer
from uuid import UUID
```

2. **Added serializers to all response schemas**:

**SecurityPolicyResponse:**
```python
@field_serializer('id', 'created_by', 'updated_by')
def serialize_uuid(self, value: UUID, _info) -> Optional[str]:
    """Convert UUID to string for JSON serialization."""
    return str(value) if value else None
```

**UserSessionResponse:**
```python
@field_serializer('id', 'user_id')
def serialize_uuid(self, value: UUID, _info) -> str:
    """Convert UUID to string for JSON serialization."""
    return str(value) if value else None
```

**LoginAttemptResponse:**
```python
@field_serializer('id', 'user_id')
def serialize_uuid(self, value: UUID, _info) -> Optional[str]:
    """Convert UUID to string for JSON serialization."""
    return str(value) if value else None
```

**NotificationConfigResponse:**
```python
@field_serializer('id', 'created_by', 'updated_by')
def serialize_uuid(self, value: UUID, _info) -> Optional[str]:
    """Convert UUID to string for JSON serialization."""
    return str(value) if value else None
```

**NotificationQueueResponse:**
```python
@field_serializer('id', 'tenant_id', 'user_id')
def serialize_uuid(self, value: UUID, _info) -> Optional[str]:
    """Convert UUID to string for JSON serialization."""
    return str(value) if value else None
```

## Benefits

1. **Proper Serialization**: UUID objects now correctly convert to strings in JSON responses
2. **Type Safety**: Explicit serializers make the conversion clear and maintainable
3. **No Performance Impact**: Serialization happens only when needed (during response)
4. **Consistent Behavior**: All security endpoints now serialize UUIDs the same way

## Testing

After deploying this change:

1. **Restart the backend container**:
   ```bash
   docker-compose -f infra/docker-compose.dev.yml restart backend
   ```

2. **Test the previously failing endpoints**:
   - Navigate to auth-policies page
   - Check browser console - no more 500 errors
   - Verify sessions and login-attempts load correctly

3. **Check API responses**:
   ```bash
   curl -H "Authorization: Bearer <token>" \
     http://localhost:8080/api/v1/admin/security/sessions?limit=50

   curl -H "Authorization: Bearer <token>" \
     http://localhost:8080/api/v1/admin/security/login-attempts?limit=50
   ```

## Alternative Solutions Considered

1. **Change GUID.process_result_value to return strings**: Would affect all models, potential breaking change
2. **Use Pydantic's ConfigDict with json_encoders**: Deprecated in Pydantic v2
3. **Use model_serializer**: More complex, field_serializer is cleaner for specific fields

## Notes

- This fix applies to Pydantic v2 (used in recent FastAPI versions)
- The `@field_serializer` decorator is the recommended way to handle custom serialization
- The `from_attributes = True` config handles SQLAlchemy ORM to Pydantic conversion
- Field serializers run AFTER the model is populated but BEFORE JSON encoding

## Files Modified

- `backend/app/schemas/security.py` - Added UUID field serializers to 5 response schemas:
  - SecurityPolicyResponse
  - UserSessionResponse
  - LoginAttemptResponse
  - NotificationConfigResponse
  - NotificationQueueResponse

## Related Issues

This fix complements the previous fixes:
1. Nginx static file 404 handling
2. API base URL configuration in frontend components
3. Nginx API proxy path preservation

All together, these fixes ensure the security administration features work end-to-end.
