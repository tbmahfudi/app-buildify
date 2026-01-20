# Cross-Module Service Access Examples

This directory contains example implementations demonstrating how modules can safely access data and services from other modules using the Module Service Registry.

## Overview

The **Module Service Registry** enables secure, audited cross-module communication in the no-code platform. It provides:

- **Service Discovery**: Modules register services that others can discover and use
- **Permission Checking**: Automatic permission validation on every service call
- **Audit Logging**: Complete audit trail of all cross-module access
- **Error Handling**: Graceful handling of missing dependencies
- **Performance Monitoring**: Execution time tracking for optimization

## Architecture

```
┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│ Payroll Module  │────────▶│  Service Registry    │◀────────│   HR Module     │
│                 │         │  (Singleton)         │         │                 │
│ PayrollService  │         │                      │         │ EmployeeService │
│                 │         │ • Discovery          │         │                 │
│ calculate()     │         │ • Permission Check   │         │ get_employee()  │
│   │             │         │ • Audit Logging      │         │ list_employees()│
│   └─────────────┼────────▶│ • Error Handling     │         └─────────────────┘
│                 │         │                      │
└─────────────────┘         └──────────────────────┘
                                      │
                                      │ Logs to
                                      ▼
                            ┌──────────────────────┐
                            │ module_service_      │
                            │   access_log         │
                            │                      │
                            │ • Calling module     │
                            │ • Method name        │
                            │ • User ID            │
                            │ • Success/Error      │
                            │ • Execution time     │
                            └──────────────────────┘
```

## Example 1: Creating a Service (HR Module)

### Step 1: Create Service Class

```python
# File: modules/hr/services/employee_service.py

from typing import Optional, List
from sqlalchemy.orm import Session

class EmployeeService:
    """Service for employee operations"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

    def get_employee(self, employee_id: str) -> Optional[dict]:
        """PUBLIC METHOD - Can be called by other modules"""

        # 1. Check permission
        if not self._has_permission('hr:employee:read'):
            raise PermissionError("No permission to read employee data")

        # 2. Query with tenant isolation
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.tenant_id == self.current_user.tenant_id
        ).first()

        if not employee:
            return None

        # 3. Return sanitized data
        return {
            "id": str(employee.id),
            "name": employee.name,
            "email": employee.email,
            "department_id": str(employee.department_id)
        }

    def list_employees(
        self,
        department_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """PUBLIC METHOD - List employees with filters"""

        if not self._has_permission('hr:employee:read'):
            raise PermissionError("No permission to read employee data")

        # Query logic...
        return employees
```

### Step 2: Register Service

```python
# File: modules/hr/init.py

from app.services.module_service_registry import ModuleServiceRegistry
from .services.employee_service import EmployeeService

def init_hr_module(db: Session):
    """Called when HR module is loaded"""

    registry = ModuleServiceRegistry()

    registry.register_service(
        module_name='hr',
        service_name='EmployeeService',
        service_class=EmployeeService,
        methods=[
            {
                'name': 'get_employee',
                'params': [{'name': 'employee_id', 'type': 'str'}],
                'returns': 'Optional[dict]',
                'description': 'Get employee by ID'
            },
            {
                'name': 'list_employees',
                'params': [
                    {'name': 'department_id', 'type': 'str', 'optional': True},
                    {'name': 'status', 'type': 'str', 'optional': True},
                    {'name': 'limit', 'type': 'int', 'default': 100}
                ],
                'returns': 'List[dict]',
                'description': 'List employees with filters'
            }
        ],
        version='1.0.0'
    )
```

## Example 2: Using a Service (Payroll Module)

```python
# File: modules/payroll/services/payroll_service.py

from app.services.module_service_registry import ModuleServiceRegistry

class PayrollService:
    """Payroll service - depends on HR module"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

        # Get HR module's EmployeeService
        registry = ModuleServiceRegistry()
        self.employee_service = registry.get_service(
            'hr',
            'EmployeeService',
            db,
            current_user
        )

    def calculate_payroll(self, employee_id: str, month: str) -> dict:
        """Calculate payroll for employee"""

        # 1. Get employee data from HR module (cross-module call)
        # This automatically:
        # - Checks HR module permissions
        # - Logs the access to audit trail
        # - Measures execution time
        employee = self.employee_service.get_employee(employee_id)

        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        # 2. Get payroll profile from own module
        profile = self._get_payroll_profile(employee_id)

        # 3. Calculate payroll
        gross_salary = profile.monthly_salary
        deductions = self._calculate_deductions(gross_salary, profile)
        net_salary = gross_salary - deductions

        return {
            'employee': employee,
            'month': month,
            'gross_salary': gross_salary,
            'deductions': deductions,
            'net_salary': net_salary
        }
```

## Features Demonstrated

### 1. Permission Checking

Every service call automatically checks permissions:

```python
# In EmployeeService.get_employee()
if not self._has_permission('hr:employee:read'):
    raise PermissionError("No permission to read employee data")

# ServiceProxy intercepts this and logs the permission denial
```

### 2. Audit Logging

All service access is logged to `module_service_access_log`:

```sql
SELECT
    svc.service_name,
    log.method_name,
    usr.email as user_email,
    log.success,
    log.execution_time_ms,
    log.accessed_at
FROM module_service_access_log log
JOIN module_services svc ON log.service_id = svc.id
JOIN users usr ON log.user_id = usr.id
WHERE log.accessed_at >= NOW() - INTERVAL '1 day'
ORDER BY log.accessed_at DESC;
```

### 3. Error Handling

Services handle missing dependencies gracefully:

```python
try:
    self.employee_service = registry.get_service('hr', 'EmployeeService', db, user)
except ServiceNotFoundError:
    # HR module not available
    self.employee_service = None
    # Handle gracefully or show error to user
```

### 4. Performance Monitoring

Execution time is tracked for every call:

```python
# ServiceProxy measures and logs execution time
execution_time_ms = int((time.time() - start_time) * 1000)
```

Query slow services:

```sql
SELECT
    svc.service_name,
    log.method_name,
    AVG(log.execution_time_ms) as avg_time_ms,
    COUNT(*) as call_count
FROM module_service_access_log log
JOIN module_services svc ON log.service_id = svc.id
WHERE log.success = true
AND log.accessed_at >= NOW() - INTERVAL '1 day'
GROUP BY svc.service_name, log.method_name
HAVING AVG(log.execution_time_ms) > 1000
ORDER BY avg_time_ms DESC;
```

## Best Practices

### 1. Service Design

✅ **DO:**
- Keep services focused on a single responsibility
- Use clear, descriptive method names
- Check permissions in every public method
- Use tenant isolation in all queries
- Return sanitized data (no sensitive fields)
- Document public methods clearly

❌ **DON'T:**
- Expose internal implementation details
- Return ORM objects (convert to dicts)
- Allow cross-tenant data access
- Include passwords or tokens in responses

### 2. Service Registration

✅ **DO:**
- Register services during module initialization
- Document all method parameters and return types
- Version your services (semantic versioning)
- Update version when breaking changes occur

❌ **DON'T:**
- Register services with duplicate names
- Change method signatures without versioning
- Register services with generic names

### 3. Using Services

✅ **DO:**
- Handle ServiceNotFoundError gracefully
- Check if service is available before using
- Catch and handle PermissionError appropriately
- Use appropriate error messages for users

❌ **DON'T:**
- Assume dependent modules are always available
- Ignore permission errors
- Make excessive service calls in loops
- Expose service errors directly to users

### 4. Performance

✅ **DO:**
- Batch service calls when possible
- Cache frequently accessed data
- Monitor execution times
- Optimize slow service methods

❌ **DON'T:**
- Call services in tight loops
- Fetch large datasets without pagination
- Ignore performance warnings in logs

## Frontend Integration

Frontend can access cross-module data via APIs:

```javascript
// Option 1: Call module's own API (which uses services internally)
const payroll = await fetch('/api/v1/payroll/calculate', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        employee_id: employeeId,
        month: 'January',
        year: 2026
    })
});

// Option 2: Call dynamic data API directly (for simple data access)
const employee = await fetch(`/api/v1/dynamic-data/Employee/records/${employeeId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
});
```

## Security Considerations

1. **Permission Inheritance**: Service calls inherit the calling user's permissions
2. **Tenant Isolation**: All queries must filter by `tenant_id`
3. **Data Sanitization**: Remove sensitive fields from responses
4. **Audit Trail**: All access is logged for security review
5. **Rate Limiting**: Consider adding rate limits for service calls

## Testing

### Unit Testing Services

```python
def test_employee_service_get_employee():
    # Setup
    db = get_test_db()
    user = create_test_user(permissions=['hr:employee:read'])
    service = EmployeeService(db, user)

    # Execute
    employee = service.get_employee(test_employee_id)

    # Assert
    assert employee is not None
    assert employee['name'] == 'John Doe'

def test_employee_service_permission_denied():
    # Setup - user without permission
    user = create_test_user(permissions=[])
    service = EmployeeService(db, user)

    # Execute & Assert
    with pytest.raises(PermissionError):
        service.get_employee(test_employee_id)
```

### Integration Testing Cross-Module Calls

```python
def test_payroll_uses_hr_service():
    # Setup both modules
    register_hr_services(db)
    register_payroll_services(db)

    # Create test data
    employee = create_test_employee()
    profile = create_test_payroll_profile(employee.id)

    # Execute
    payroll_service = PayrollService(db, test_user)
    result = payroll_service.calculate_payroll(
        employee.id,
        'January',
        2026
    )

    # Assert
    assert result['employee']['id'] == str(employee.id)
    assert result['amounts']['net_salary'] > 0

    # Verify audit log
    logs = db.query(ModuleServiceAccessLog).all()
    assert len(logs) > 0
    assert logs[0].method_name == 'get_employee'
```

## Troubleshooting

### Service Not Found

**Error:** `ServiceNotFoundError: Service 'EmployeeService' not found in module 'hr'`

**Solutions:**
1. Ensure HR module is installed and active
2. Check if service registration happened during module init
3. Verify service name matches exactly (case-sensitive)

### Permission Denied

**Error:** `PermissionError: No permission to read employee data`

**Solutions:**
1. Check user's role has required permission
2. Verify permission string matches exactly
3. Check RBAC configuration

### Slow Performance

**Symptoms:** Service calls taking >1000ms

**Solutions:**
1. Check audit logs for execution times
2. Add database indexes on frequently queried fields
3. Implement caching for frequently accessed data
4. Batch calls instead of individual calls in loops

## Related Documentation

- [Phase 4 Design Document](../../../NO-CODE-PHASE4.md)
- [Module System Architecture](../../../NO-CODE-PLATFORM-DESIGN.md)
- [RBAC System](../../core/rbac/README.md)
- [Audit Logging](../../models/audit.py)
