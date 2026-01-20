"""
Module Service Examples

Example implementations demonstrating cross-module service access.

These examples show:
1. How to create a service that other modules can use (EmployeeService)
2. How to use services from other modules (PayrollService)
3. Service registration and discovery
4. Permission checking and audit logging
5. Error handling for missing dependencies

Phase 4 Priority 2 - Cross-Module Access
"""

from .hr_employee_service import EmployeeService, register_hr_services
from .payroll_service import PayrollService, register_payroll_services


__all__ = [
    'EmployeeService',
    'register_hr_services',
    'PayrollService',
    'register_payroll_services',
]
