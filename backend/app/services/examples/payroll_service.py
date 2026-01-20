"""
Example: Payroll Module Service

Demonstrates how to use services from other modules.
This Payroll service depends on the HR module's EmployeeService
to access employee data.

Phase 4 Priority 2 - Cross-Module Access Example
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal

from app.services.module_service_registry import ModuleServiceRegistry, ServiceNotFoundError


class PayrollService:
    """
    Payroll Service - Depends on HR Module

    Calculates and manages payroll using employee data from HR module.
    Demonstrates cross-module service access pattern.
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

        # Get HR module's EmployeeService through registry
        registry = ModuleServiceRegistry()

        try:
            self.employee_service = registry.get_service(
                module_name='hr',
                service_name='EmployeeService',
                db=db,
                current_user=current_user
            )
        except ServiceNotFoundError as e:
            # HR module not available - handle gracefully
            self.employee_service = None
            # In production, might want to log this or raise module dependency error

    def calculate_payroll(self, employee_id: str, month: str, year: int) -> dict:
        """
        Calculate payroll for employee.

        Demonstrates:
        1. Using HR service to get employee data (cross-module call)
        2. Using own module's data (payroll profile)
        3. Business logic combining data from multiple modules

        Args:
            employee_id: Employee UUID
            month: Month name (e.g., 'January')
            year: Year (e.g., 2026)

        Returns:
            Payroll calculation result

        Raises:
            ValueError: If employee not found or has no payroll profile
            PermissionError: If user lacks required permissions
            ServiceNotFoundError: If HR module not available
        """
        # Check if HR service is available
        if not self.employee_service:
            raise ServiceNotFoundError(
                "HR module is required but not available. "
                "Please ensure HR module is installed and active."
            )

        # Check permission
        if not self._has_permission('payroll:calculate'):
            raise PermissionError(
                "No permission to calculate payroll. Required: payroll:calculate"
            )

        # 1. Get employee data from HR module (cross-module call)
        # This call goes through ServiceProxy which:
        # - Checks HR module permissions
        # - Logs the access
        # - Measures execution time
        employee = self.employee_service.get_employee(employee_id)

        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        # Check if employee is active
        if not self.employee_service.is_employee_active(employee_id):
            raise ValueError(f"Employee {employee['name']} is not active")

        # 2. Get payroll profile from own module's table
        profile = self._get_payroll_profile(employee_id)

        if not profile:
            raise ValueError(
                f"No payroll profile found for employee {employee['name']}. "
                "Please create payroll profile first."
            )

        # 3. Calculate payroll
        gross_salary = profile['monthly_salary']
        deductions = self._calculate_deductions(gross_salary, profile)
        net_salary = gross_salary - deductions['total']

        # 4. Get department info for reporting
        department = self.employee_service.get_employee_department(employee_id)

        return {
            'payroll_id': self._generate_payroll_id(),
            'employee': {
                'id': employee['id'],
                'name': employee['name'],
                'email': employee['email'],
                'position': employee.get('position'),
                'department': department['name'] if department else 'Unknown'
            },
            'period': {
                'month': month,
                'year': year
            },
            'amounts': {
                'gross_salary': float(gross_salary),
                'deductions': {
                    'tax': float(deductions['tax']),
                    'insurance': float(deductions['insurance']),
                    'retirement': float(deductions['retirement']),
                    'other': float(deductions['other']),
                    'total': float(deductions['total'])
                },
                'net_salary': float(net_salary)
            },
            'payment_details': {
                'bank_account': profile['bank_account'],
                'payment_method': profile['payment_method']
            }
        }

    def list_payroll_for_department(
        self,
        department_id: str,
        month: str,
        year: int
    ) -> List[dict]:
        """
        Calculate payroll for all employees in a department.

        Demonstrates batch cross-module access.

        Args:
            department_id: Department UUID
            month: Month name
            year: Year

        Returns:
            List of payroll calculations
        """
        if not self.employee_service:
            raise ServiceNotFoundError("HR module not available")

        # Get all active employees in department (cross-module call)
        employees = self.employee_service.list_employees(
            department_id=department_id,
            status='active'
        )

        payroll_results = []

        for employee in employees:
            try:
                payroll = self.calculate_payroll(
                    employee_id=employee['id'],
                    month=month,
                    year=year
                )
                payroll_results.append(payroll)
            except ValueError as e:
                # Skip employees without payroll profiles
                payroll_results.append({
                    'employee': employee,
                    'error': str(e),
                    'status': 'error'
                })

        return payroll_results

    def _get_payroll_profile(self, employee_id: str) -> Optional[dict]:
        """
        Get payroll profile from payroll module's own table.

        This data is managed by payroll module and not shared with others.
        """
        # Note: This assumes payroll_profiles table exists
        query = text("""
            SELECT
                employee_id,
                monthly_salary,
                bank_account,
                tax_id,
                payment_method,
                insurance_amount,
                retirement_contribution_pct
            FROM payroll_profiles
            WHERE employee_id = :employee_id
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

        return {
            'employee_id': str(result.employee_id),
            'monthly_salary': Decimal(str(result.monthly_salary)),
            'bank_account': result.bank_account,
            'tax_id': result.tax_id,
            'payment_method': result.payment_method,
            'insurance_amount': Decimal(str(result.insurance_amount or 0)),
            'retirement_contribution_pct': Decimal(str(result.retirement_contribution_pct or 0))
        }

    def _calculate_deductions(self, gross_salary: Decimal, profile: dict) -> dict:
        """
        Calculate payroll deductions.

        Business logic for payroll calculation.
        """
        # Tax (20%)
        tax = gross_salary * Decimal('0.20')

        # Insurance (fixed amount from profile)
        insurance = profile['insurance_amount']

        # Retirement (percentage from profile)
        retirement = gross_salary * (profile['retirement_contribution_pct'] / Decimal('100'))

        # Other deductions
        other = Decimal('0')

        # Total
        total = tax + insurance + retirement + other

        return {
            'tax': tax,
            'insurance': insurance,
            'retirement': retirement,
            'other': other,
            'total': total
        }

    def _generate_payroll_id(self) -> str:
        """Generate unique payroll ID"""
        import uuid
        return str(uuid.uuid4())

    def _has_permission(self, permission: str) -> bool:
        """Check if current user has permission"""
        # TODO: Integrate with actual RBAC system
        return True


# Service registration function
def register_payroll_services(db: Session):
    """
    Register Payroll module services with the service registry.

    This demonstrates that Payroll module can also export services
    that other modules might use (e.g., Benefits module might need
    to know salary information for benefit calculations).
    """
    registry = ModuleServiceRegistry()

    registry.register_service(
        module_name='payroll',
        service_name='PayrollService',
        service_class=PayrollService,
        methods=[
            {
                'name': 'calculate_payroll',
                'params': [
                    {'name': 'employee_id', 'type': 'str', 'required': True},
                    {'name': 'month', 'type': 'str', 'required': True},
                    {'name': 'year', 'type': 'int', 'required': True}
                ],
                'returns': 'dict',
                'description': 'Calculate payroll for employee for given month/year'
            },
            {
                'name': 'list_payroll_for_department',
                'params': [
                    {'name': 'department_id', 'type': 'str', 'required': True},
                    {'name': 'month', 'type': 'str', 'required': True},
                    {'name': 'year', 'type': 'int', 'required': True}
                ],
                'returns': 'List[dict]',
                'description': 'Calculate payroll for all employees in department'
            }
        ],
        version='1.0.0',
        description='Payroll calculation service (depends on HR module)'
    )
