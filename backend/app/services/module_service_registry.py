"""
Module Service Registry

Central registry for cross-module service access with permission checking
and audit logging (Phase 4 Priority 2).
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import time
from datetime import datetime

from app.core.logging_config import get_logger
from app.models.module_service import ModuleService, ModuleServiceAccessLog
from app.models.nocode_module import NocodeModule


logger = get_logger(__name__)


class ServiceNotFoundError(Exception):
    """Raised when a requested service is not found"""
    pass


class ModuleServiceRegistry:
    """
    Singleton registry for cross-module services.

    Manages service registration, discovery, and access control for
    modules to communicate with each other safely.
    """

    _instance = None
    _services: Dict[str, Dict[str, Any]] = {}  # Cache: {module_name: {service_name: service_info}}

    def __new__(cls):
        """Ensure singleton instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register_service(
        self,
        module_name: str,
        service_name: str,
        service_class: type,
        methods: List[dict],
        version: str = '1.0.0',
        description: str = None
    ):
        """
        Register a service for cross-module use.

        Args:
            module_name: Module name (e.g., 'hr', 'payroll')
            service_name: Service class name (e.g., 'EmployeeService')
            service_class: Python class reference
            methods: List of method signatures with params and return types
            version: Service version (semantic versioning)
            description: Service description

        Example:
            registry.register_service(
                module_name='hr',
                service_name='EmployeeService',
                service_class=EmployeeService,
                methods=[
                    {
                        "name": "get_employee",
                        "params": [{"name": "employee_id", "type": "str"}],
                        "returns": "dict",
                        "description": "Get employee by ID"
                    }
                ],
                version='1.0.0'
            )
        """
        if module_name not in self._services:
            self._services[module_name] = {}

        self._services[module_name][service_name] = {
            'class': service_class,
            'methods': methods,
            'version': version,
            'description': description
        }

        logger.info(
            f"Registered service: {module_name}.{service_name} v{version}",
            extra={
                'module': module_name,
                'service': service_name,
                'version': version,
                'method_count': len(methods)
            }
        )

    def get_service(
        self,
        module_name: str,
        service_name: str,
        db: Session,
        current_user
    ) -> Optional[object]:
        """
        Get service instance with permission checking.

        Returns a wrapped service proxy that:
        - Checks permissions before each method call
        - Logs all access to audit trail
        - Measures execution time
        - Handles errors gracefully

        Args:
            module_name: Module providing the service
            service_name: Service class name
            db: Database session
            current_user: Current user for permission checking

        Returns:
            ServiceProxy instance wrapping the actual service

        Raises:
            ServiceNotFoundError: If service not found
        """
        if module_name not in self._services:
            raise ServiceNotFoundError(f"Module '{module_name}' not found in registry")

        if service_name not in self._services[module_name]:
            raise ServiceNotFoundError(
                f"Service '{service_name}' not found in module '{module_name}'"
            )

        service_info = self._services[module_name][service_name]
        service_class = service_info['class']

        # Instantiate service with user context
        service_instance = service_class(db, current_user)

        # Get service ID from database for logging
        service_record = db.query(ModuleService).join(
            NocodeModule,
            ModuleService.module_id == NocodeModule.id
        ).filter(
            NocodeModule.name == module_name,
            ModuleService.service_name == service_name
        ).first()

        # Wrap service to add permission checking and logging
        wrapped_service = ServiceProxy(
            service_instance=service_instance,
            module_name=module_name,
            service_name=service_name,
            service_id=str(service_record.id) if service_record else None,
            current_user=current_user,
            db=db
        )

        return wrapped_service

    def list_services(self, module_name: Optional[str] = None) -> dict:
        """
        List all registered services.

        Args:
            module_name: Filter by module name (optional)

        Returns:
            Dictionary of services by module
        """
        if module_name:
            return self._services.get(module_name, {})
        return self._services

    def is_service_registered(self, module_name: str, service_name: str) -> bool:
        """Check if a service is registered"""
        return (
            module_name in self._services and
            service_name in self._services[module_name]
        )

    def unregister_service(self, module_name: str, service_name: str):
        """Unregister a service"""
        if module_name in self._services and service_name in self._services[module_name]:
            del self._services[module_name][service_name]
            logger.info(f"Unregistered service: {module_name}.{service_name}")

            # Clean up empty module entry
            if not self._services[module_name]:
                del self._services[module_name]


class ServiceProxy:
    """
    Proxy wrapper for service instances.

    Intercepts all method calls to:
    - Validate permissions
    - Log access to audit trail
    - Measure execution time
    - Handle errors
    """

    def __init__(
        self,
        service_instance: object,
        module_name: str,
        service_name: str,
        service_id: Optional[str],
        current_user,
        db: Session
    ):
        """
        Initialize service proxy.

        Args:
            service_instance: Actual service instance
            module_name: Module providing service
            service_name: Service class name
            service_id: Service ID from database (for logging)
            current_user: Current user context
            db: Database session for logging
        """
        self._service = service_instance
        self._module_name = module_name
        self._service_name = service_name
        self._service_id = service_id
        self._user = current_user
        self._db = db

    def __getattr__(self, method_name: str):
        """
        Intercept method calls.

        This magic method is called when accessing any attribute/method
        on the proxy that doesn't exist directly on the proxy itself.
        """
        # Check if method exists on actual service
        if not hasattr(self._service, method_name):
            raise AttributeError(
                f"Service '{self._service_name}' has no method '{method_name}'"
            )

        original_method = getattr(self._service, method_name)

        def wrapped_method(*args, **kwargs):
            """Wrapped method with logging and error handling"""
            start_time = time.time()
            success = False
            error_message = None
            permission_checked = None

            try:
                # Call original method
                result = original_method(*args, **kwargs)
                success = True

                return result

            except PermissionError as e:
                # Permission denied
                error_message = str(e)
                permission_checked = self._extract_permission_from_error(str(e))
                logger.warning(
                    f"Permission denied for {self._module_name}.{self._service_name}.{method_name}",
                    extra={
                        'user_id': str(self._user.id),
                        'permission': permission_checked
                    }
                )
                raise

            except Exception as e:
                # Other errors
                error_message = str(e)
                logger.error(
                    f"Error in {self._module_name}.{self._service_name}.{method_name}: {str(e)}",
                    extra={
                        'user_id': str(self._user.id),
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                raise

            finally:
                # Log access regardless of success/failure
                execution_time_ms = int((time.time() - start_time) * 1000)
                self._log_access(
                    method_name=method_name,
                    success=success,
                    error_message=error_message,
                    execution_time_ms=execution_time_ms,
                    permission_checked=permission_checked,
                    parameters=self._sanitize_parameters(args, kwargs)
                )

        return wrapped_method

    def _log_access(
        self,
        method_name: str,
        success: bool,
        error_message: Optional[str],
        execution_time_ms: int,
        permission_checked: Optional[str],
        parameters: Optional[dict]
    ):
        """
        Log service access to database.

        Creates audit record of service call for:
        - Security auditing
        - Performance monitoring
        - Debugging cross-module interactions
        """
        if not self._service_id:
            # Service not registered in DB, skip logging
            return

        try:
            log_entry = ModuleServiceAccessLog(
                calling_module_id=None,  # TODO: Track calling module context
                service_id=self._service_id,
                method_name=method_name,
                user_id=self._user.id,
                tenant_id=self._user.tenant_id,
                parameters=parameters,
                success=success,
                error_message=error_message,
                execution_time_ms=execution_time_ms,
                permission_checked=permission_checked,
                accessed_at=datetime.utcnow()
            )

            self._db.add(log_entry)
            self._db.commit()

        except Exception as e:
            # Don't fail the service call if logging fails
            logger.error(f"Failed to log service access: {str(e)}", exc_info=True)
            self._db.rollback()

    def _sanitize_parameters(self, args: tuple, kwargs: dict) -> dict:
        """
        Sanitize parameters for logging.

        Removes sensitive data like passwords, tokens, etc.
        """
        # Convert args to dict
        sanitized = {
            'args': [self._sanitize_value(arg) for arg in args],
            'kwargs': {k: self._sanitize_value(v) for k, v in kwargs.items()}
        }
        return sanitized

    def _sanitize_value(self, value: Any) -> Any:
        """
        Sanitize individual parameter value.

        Redacts sensitive fields and truncates large objects.
        """
        # Sensitive field names to redact
        sensitive_fields = ['password', 'token', 'secret', 'api_key', 'private_key']

        # Handle strings
        if isinstance(value, str):
            # Truncate long strings
            if len(value) > 1000:
                return f"{value[:1000]}... [truncated]"
            return value

        # Handle dictionaries
        if isinstance(value, dict):
            sanitized_dict = {}
            for k, v in value.items():
                # Redact sensitive fields
                if any(sensitive in k.lower() for sensitive in sensitive_fields):
                    sanitized_dict[k] = "[REDACTED]"
                else:
                    sanitized_dict[k] = self._sanitize_value(v)
            return sanitized_dict

        # Handle lists
        if isinstance(value, (list, tuple)):
            # Truncate long lists
            if len(value) > 100:
                return [self._sanitize_value(v) for v in value[:100]] + ["... [truncated]"]
            return [self._sanitize_value(v) for v in value]

        # Return other types as-is (int, float, bool, None, etc.)
        return value

    def _extract_permission_from_error(self, error_message: str) -> Optional[str]:
        """
        Extract permission name from error message.

        Looks for patterns like "No permission to read employee data"
        or "hr:employee:read permission required"
        """
        # Look for permission format like "hr:employee:read"
        import re
        pattern = r'([a-z_]+:[a-z_]+:[a-z_]+)'
        match = re.search(pattern, error_message)
        if match:
            return match.group(1)

        # Return generic permission indicator
        return "permission_denied"


# Singleton instance
registry = ModuleServiceRegistry()
