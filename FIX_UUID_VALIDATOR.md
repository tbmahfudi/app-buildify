# Fix: UUID Validation with field_validator

## Problem

After implementing `BaseResponse` with `field_serializer`, the backend was still throwing validation errors:

```
500 Internal Server Error
"18 validation errors:
  {'type': 'string_type', 'loc': ('response', 0, 'id'), 'msg': 'Input should be a valid string', 'input': UUID('8332eb73-0005-41b3-bd69-0459751fe30d')}
  {'type': 'string_type', 'loc': ('response', 0, 'user_id'), 'msg': 'Input should be a valid string', 'input': UUID('efa8a684-8b28-47e0-aec9-bda421409fb4')}"
```

## Root Cause

### The Issue with field_serializer

`@field_serializer` only runs during **serialization** (when converting the model to JSON for output). However, Pydantic validates field types **before** serialization when creating the model from ORM objects.

**Flow:**
1. ORM returns `UUID` objects
2. Pydantic tries to create model with `id: str` field
3. **Validation fails** ❌ (UUID is not str)
4. field_serializer never runs (validation failed first)

### Why It Appeared to Work Initially

During initial testing, the endpoints may have had no data to return (empty lists), so validation didn't occur.

## Solution

Changed from `@field_serializer` to `@field_validator` with `mode='before'`:

```python
@field_validator('id', 'user_id', 'tenant_id', 'created_by', 'updated_by', mode='before', check_fields=False)
@classmethod
def convert_uuid_to_str(cls, value: Any) -> Optional[str]:
    """Convert UUID fields to strings before validation."""
    return serialize_uuid_field(value)
```

**New Flow:**
1. ORM returns `UUID` objects
2. field_validator runs **before** type checking
3. UUID → string conversion happens
4. Pydantic validates with string value ✅
5. Model created successfully

## Key Differences

| Aspect | field_serializer | field_validator (mode='before') |
|--------|------------------|----------------------------------|
| **When it runs** | During serialization (output) | Before validation (input) |
| **Purpose** | Convert for JSON output | Convert before type checking |
| **Our use case** | ❌ Too late | ✅ Perfect |

## Changes Made

### 1. Updated `backend/app/schemas/base.py`

**Before:**
```python
@field_serializer('id', 'user_id', 'tenant_id', 'created_by', 'updated_by', check_fields=False)
def serialize_common_uuid_fields(self, value: Any, _info) -> Optional[str]:
    return serialize_uuid_field(value)
```

**After:**
```python
@field_validator('id', 'user_id', 'tenant_id', 'created_by', 'updated_by', mode='before', check_fields=False)
@classmethod
def convert_uuid_to_str(cls, value: Any) -> Optional[str]:
    return serialize_uuid_field(value)
```

### 2. Updated `backend/app/schemas/audit.py`

Changed `entity_id` from field_serializer to field_validator:

```python
@field_validator('entity_id', mode='before')
@classmethod
def convert_entity_id_to_str(cls, value):
    from .base import serialize_uuid_field
    return serialize_uuid_field(value)
```

## Benefits

1. **Validation Success**: UUID objects converted before type checking
2. **No 500 Errors**: All endpoints work correctly with UUID data
3. **Correct Approach**: Using the right Pydantic tool for the job
4. **Maintained DRY**: Still centralized in BaseResponse
5. **Performance**: Validation happens once, at the right time

## Testing

After this fix:

```bash
# Restart backend
docker-compose -f infra/docker-compose.dev.yml restart backend

# Test previously failing endpoints
curl -H "Authorization: Bearer <token>" \
  http://localhost:8080/api/v1/admin/security/sessions?limit=50

curl -H "Authorization: Bearer <token>" \
  http://localhost:8080/api/v1/admin/security/login-attempts?limit=50
```

**Expected:** 200 OK with proper JSON data containing string UUIDs

## Understanding mode='before'

Pydantic validators have different modes:

- **`mode='before'`**: Runs before Pydantic parses/validates the value
  - Use for: Type conversion, data cleaning
  - Our case: Convert UUID → str

- **`mode='after'`**: Runs after validation succeeds
  - Use for: Additional validation, business logic

- **`mode='wrap'`**: Wraps the validation
  - Use for: Complex validation patterns

For UUID conversion, `mode='before'` is the correct choice.

## Pydantic v2 Migration Note

This is a common pattern when migrating from Pydantic v1 to v2:

**Pydantic v1:**
- Used `validator` (now deprecated)
- Had `pre=True` for before-validation

**Pydantic v2:**
- Uses `field_validator`
- Has `mode='before'` for before-validation
- More explicit and type-safe

Our implementation follows Pydantic v2 best practices.

## Related Issues

This fix builds on:
1. **FIX_UUID_SERIALIZATION.md** - Initial UUID serialization attempt (incorrect approach)
2. **REFACTOR_UUID_SERIALIZATION.md** - Centralized with BaseResponse (still used serializer)
3. **FIX_UUID_VALIDATOR.md** - This fix (correct approach with validator)

## Files Modified

- `backend/app/schemas/base.py` - Changed UUIDMixin to use field_validator
- `backend/app/schemas/audit.py` - Updated entity_id validator
- `FIX_UUID_VALIDATOR.md` - This documentation

## Summary

The key insight: In Pydantic v2, use `field_validator(mode='before')` for type conversion that needs to happen before validation, not `field_serializer` which only affects output serialization.
