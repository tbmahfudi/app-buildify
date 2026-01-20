"""
Example: HR Module Employee Service

Demonstrates how to create a service that can be called by other modules.
This service would be part of an HR module and exports employee data
to other modules like Payroll, Benefits, etc.

Phase 4 Priority 2 - Cross-Module Access Example
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.module_service_registry import ModuleServiceRegistry


class EmployeeService:
    """
    Employee Service - Exported by HR Module

    Provides employee data access to other modules with
    proper permission checking and tenant isolation.

    PUBLIC METHODS (can be called by other modules):
    - get_employee(employee_id)
    - list_employees(department_id, status, limit)
    - get_employee_department(employee_id)
    - is_employee_active(employee_id)
    """

    def __init__(self, db: Session, current_user):
        """
        Initialize service with database and user context.

        Args:
            db: Database session
            current_user: Current user for permission checking
        """
        self.db = db
        self.current_user = current_user

    def get_employee(self, employee_id: str) -> Optional[dict]:
        """
        Get employee by ID.

        PUBLIC METHOD - Can be called by other modules.

        Args:
            employee_id: Employee UUID

        Returns:
            Employee data dict or None if not found

        Raises:
            PermissionError: If user lacks hr:employee:read permission
        """
        # Check permission
        if not self._has_permission('hr:employee:read'):
            raise PermissionError(
                "No permission to read employee data. Required: hr:employee:read"
            )

        # Query with tenant isolation
        # Note: This assumes hr_employees table exists (would be created by HR module)
        query = text("""
            SELECT
                id,
                name,
                email,
                department_id,
                hire_date,
                status,
                position,
                phone
            FROM hr_employees
            WHERE id = :employee_id
            AND tenant_id = :tenant_id
        """)

        result = self.db.execute(
            query,
            {
                'employee_id': employee_id,
                'tenant_id': str(self.current_user.tenant_id)
            }
        ).first()

        if not result:
            return None

        # Convert to dict
        return {
            'id': str(result.id),
            'name': result.name,
            'email': result.email,
            'department_id': str(result.department_id) if result.department_id else None,
            'hire_date': result.hire_date.isoformat() if result.hire_date else None,
            'status': result.status,
            'position': result.position,
            'phone': result.phone
        }

    def list_employees(
        self,
        department_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        List employees with filters.

        PUBLIC METHOD - Can be called by other modules.

        Args:
            department_id: Filter by department (optional)
            status: Filter by status (active, inactive, etc.)
            limit: Maximum number of results (default 100, max 1000)

        Returns:
            List of employee data dicts

        Raises:
            PermissionError: If user lacks hr:employee:read permission
        """
        # Check permission
        if not self._has_permission('hr:employee:read'):
            raise PermissionError(
                "No permission to read employee data. Required: hr:employee:read"
            )

        # Enforce limit
        limit = min(limit, 1000)

        # Build query with filters
        query_parts = ["""
            SELECT
                id,
                name,
                email,
                department_id,
                status,
                position
            FROM hr_employees
            WHERE tenant_id = :tenant_id
        """]

        params = {'tenant_id': str(self.current_user.tenant_id)}

        if department_id:
            query_parts.append("AND department_id = :department_id")
            params['department_id'] = department_id

        if status:
            query_parts.append("AND status = :status")
            params['status'] = status

        query_parts.append("ORDER BY name")
        query_parts.append("LIMIT :limit")
        params['limit'] = limit

        query = text(" ".join(query_parts))

        results = self.db.execute(query, params).fetchall()

        # Convert to list of dicts
        return [
            {
                'id': str(row.id),
                'name': row.name,
                'email': row.email,
                'department_id': str(row.department_id) if row.department_id else None,
                'status': row.status,
                'position': row.position
            }
            for row in results
        ]

    def get_employee_department(self, employee_id: str) -> Optional[dict]:
        """
        Get employee's department information.

        PUBLIC METHOD - Can be called by other modules.

        Args:
            employee_id: Employee UUID

        Returns:
            Department data dict or None if not found

        Raises:
            PermissionError: If user lacks hr:employee:read permission
        """
        # Check permission
        if not self._has_permission('hr:employee:read'):
            raise PermissionError(
                "No permission to read employee data. Required: hr:employee:read"
            )

        query = text("""
            SELECT
                d.id,
                d.name,
                d.code
            FROM hr_employees e
            JOIN departments d ON e.department_id = d.id
            WHERE e.id = :employee_id
            AND e.tenant_id = :tenant_id
        """)

        result = self.db.execute(
            query,
            {
                'employee_id': employee_id,
                'tenant_id': str(self.current_user.tenant_id)
            }
        ).first()

        if not result:
            return None

        return {
            'id': str(result.id),
            'name': result.name,
            'code': result.code
        }

    def is_employee_active(self, employee_id: str) -> bool:
        """
        Check if employee is active.

        PUBLIC METHOD - Can be called by other modules.

        Args:
            employee_id: Employee UUID

        Returns:
            True if employee is active, False otherwise

        Raises:
            PermissionError: If user lacks hr:employee:read permission
        """
        # Check permission
        if not self._has_permission('hr:employee:read'):
            raise PermissionError(
                "No permission to read employee data. Required: hr:employee:read"
            )

        query = text("""
            SELECT status
            FROM hr_employees
            WHERE id = :employee_id
            AND tenant_id = :tenant_id
        """)

        result = self.db.execute(
            query,
            {
                'employee_id': employee_id,
                'tenant_id': str(self.current_user.tenant_id)
            }
        ).scalar()

        return result == 'active' if result else False

    def _has_permission(self, permission: str) -> bool:
        """
        Check if current user has permission.

        This is a placeholder - actual implementation would check
        user's roles and permissions from RBAC system.

        Args:
            permission: Permission string (e.g., 'hr:employee:read')

        Returns:
            True if user has permission
        """
        # TODO: Integrate with actual RBAC system
        # For now, return True for demonstration
        # In production, this would check:
        # return self.current_user.has_permission(permission)
        return True


# Service registration function
def register_hr_services(db: Session):
    """
    Register HR module services with the service registry.

    This function should be called during HR module initialization
    to make its services available to other modules.
    """
    registry = ModuleServiceRegistry()

    registry.register_service(
        module_name='hr',
        service_name='EmployeeService',
        service_class=EmployeeService,
        methods=[
            {
                'name': 'get_employee',
                'params': [
                    {'name': 'employee_id', 'type': 'str', 'required': True}
                ],
                'returns': 'Optional[dict]',
                'description': 'Get employee by ID with full details'
            },
            {
                'name': 'list_employees',
                'params': [
                    {'name': 'department_id', 'type': 'str', 'optional': True},
                    {'name': 'status', 'type': 'str', 'optional': True},
                    {'name': 'limit', 'type': 'int', 'default': 100}
                ],
                'returns': 'List[dict]',
                'description': 'List employees with optional filters'
            },
            {
                'name': 'get_employee_department',
                'params': [
                    {'name': 'employee_id', 'type': 'str', 'required': True}
                ],
                'returns': 'Optional[dict]',
                'description': 'Get employee\'s department information'
            },
            {
                'name': 'is_employee_active',
                'params': [
                    {'name': 'employee_id', 'type': 'str', 'required': True}
                ],
                'returns': 'bool',
                'description': 'Check if employee is active'
            }
        ],
        version='1.0.0',
        description='Employee data access service for cross-module communication'
    )
