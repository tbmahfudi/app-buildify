# Refactor: Centralized UUID Serialization

## Summary

Created a reusable `BaseResponse` class and helper functions for UUID serialization to eliminate code duplication across all response schemas.

## Problem

After fixing UUID serialization in security schemas, we had duplicated `@field_serializer` decorators across multiple response classes:

```python
# Duplicated in every response schema
@field_serializer('id', 'user_id', 'created_by', 'updated_by')
def serialize_uuid(self, value: UUID, _info) -> Optional[str]:
    """Convert UUID to string for JSON serialization."""
    return str(value) if value else None

class Config:
    from_attributes = True
```

This violates DRY (Don't Repeat Yourself) principle and makes maintenance harder.

## Solution

### 1. Created Base Schema Module

**File**: `backend/app/schemas/base.py`

```python
def serialize_uuid_field(value: Any) -> Optional[str]:
    """
    Helper function to serialize UUID objects to strings.
    """
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, str):
        return value
    return str(value)


class UUIDMixin:
    """
    Mixin to add UUID serialization for common ID fields.

    Automatically serializes 'id', 'user_id', 'tenant_id',
    'created_by', 'updated_by' to strings.
    """
    @field_serializer('id', 'user_id', 'tenant_id', 'created_by', 'updated_by', check_fields=False)
    def serialize_common_uuid_fields(self, value: Any, _info) -> Optional[str]:
        return serialize_uuid_field(value)


class BaseResponse(UUIDMixin, BaseModel):
    """
    Base response schema with:
    - Automatic UUID serialization for common fields
    - from_attributes = True for ORM compatibility
    """
    class Config:
        from_attributes = True
```

### 2. Updated All Response Schemas

**Before:**
```python
class UserSessionResponse(BaseModel):
    id: str
    user_id: str
    ...

    @field_serializer('id', 'user_id')
    def serialize_uuid(self, value: UUID, _info) -> str:
        return str(value) if value else None

    class Config:
        from_attributes = True
```

**After:**
```python
class UserSessionResponse(BaseResponse):
    id: str
    user_id: str
    ...
    # UUID serialization and from_attributes inherited from BaseResponse
```

## Files Modified

### Created
- **`backend/app/schemas/base.py`** - New base schema module with:
  - `serialize_uuid_field()` - Helper function
  - `UUIDMixin` - Mixin class for UUID serialization
  - `BaseResponse` - Base class for all response schemas

### Updated Response Schemas

1. **`backend/app/schemas/security.py`**:
   - SecurityPolicyResponse
   - UserSessionResponse
   - LoginAttemptResponse
   - NotificationConfigResponse
   - NotificationQueueResponse

2. **`backend/app/schemas/org.py`**:
   - CompanyResponse
   - BranchResponse
   - DepartmentResponse

3. **`backend/app/schemas/audit.py`**:
   - AuditLogResponse (with additional entity_id serializer)

## Benefits

### 1. DRY Principle
- Single source of truth for UUID serialization
- No code duplication across schemas

### 2. Consistency
- All response schemas serialize UUIDs the same way
- Common fields automatically handled

### 3. Maintainability
- Easy to update serialization logic in one place
- Simpler to add new response schemas

### 4. Type Safety
- Helper function handles multiple input types safely
- Proper Optional[str] return type

### 5. Extensibility
- Easy to add more common fields to UUIDMixin
- Can create specialized mixins for other patterns

## Usage

### For Standard Response Schemas
```python
from .base import BaseResponse

class MyResponse(BaseResponse):
    id: str
    user_id: str
    # Common UUID fields automatically serialized
```

### For Schemas with Additional UUID Fields
```python
from .base import BaseResponse, serialize_uuid_field

class MyResponse(BaseResponse):
    id: str
    custom_uuid_field: str

    @field_serializer('custom_uuid_field')
    def serialize_custom(self, value, _info):
        return serialize_uuid_field(value)
```

### For Base Schemas (Non-Response)
```python
from pydantic import BaseModel

class MyBase(BaseModel):
    # Use BaseModel directly for non-response schemas
    field: str
```

## Testing

After this refactoring:

1. **All existing API endpoints should work without changes**
   - BaseResponse provides same serialization behavior
   - Same from_attributes configuration

2. **Test key endpoints**:
   ```bash
   # Sessions
   curl -H "Authorization: Bearer <token>" \
     http://localhost:8080/api/v1/admin/security/sessions

   # Companies
   curl -H "Authorization: Bearer <token>" \
     http://localhost:8080/api/v1/org/companies

   # Audit logs
   curl -H "Authorization: Bearer <token>" \
     http://localhost:8080/api/v1/audit/logs
   ```

3. **Verify UUID fields serialize correctly**:
   - Check that id, user_id, tenant_id are strings in JSON
   - No validation errors
   - No type conversion issues

## Future Improvements

### 1. Apply to All Schemas
Current PR updates security, org, and audit schemas. Future work:
- metadata.py
- settings.py
- auth.py
- dashboard.py
- report.py
- scheduler.py
- module.py

### 2. Additional Mixins
Could create specialized mixins for common patterns:
```python
class TimestampMixin:
    """Mixin for created_at/updated_at fields"""
    created_at: datetime
    updated_at: Optional[datetime]

class SoftDeleteMixin:
    """Mixin for soft-deletable resources"""
    deleted_at: Optional[datetime]
    is_deleted: bool
```

### 3. Request Schema Bases
Could create base classes for request schemas:
```python
class BaseCreate(BaseModel):
    """Base for create requests"""
    pass

class BaseUpdate(BaseModel):
    """Base for update requests"""
    pass
```

## Migration Guide

### For New Response Schemas
```python
# Instead of
class NewResponse(BaseModel):
    id: str
    class Config:
        from_attributes = True

# Use
class NewResponse(BaseResponse):
    id: str
```

### For Existing Schemas
1. Import BaseResponse: `from .base import BaseResponse`
2. Change `BaseModel` to `BaseResponse` in class definition
3. Remove `@field_serializer` decorators for common fields (id, user_id, etc.)
4. Remove `class Config: from_attributes = True` if no other config needed
5. Keep custom field_serializers for non-standard UUID fields

## Notes

- `check_fields=False` in UUIDMixin allows it to work even if a schema doesn't have all listed fields
- BaseResponse inherits from UUIDMixin and BaseModel, providing both serialization and Pydantic features
- The helper function handles None, UUID objects, and strings safely
- This refactoring is backward compatible - no API changes needed

## Related Issues

This refactoring builds on:
- FIX_UUID_SERIALIZATION.md - Original UUID serialization fix
- FIX_API_BASE_URL.md - API base URL configuration
- FIX_NGINX_STATIC_FILES.md - Nginx configuration fixes

Together, these changes ensure security admin features work end-to-end with clean, maintainable code.
