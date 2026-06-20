"""Re-export BaseModule for module developers. Do not import internals directly."""
from backend.app.core.module_system.base_module import BaseModule

__all__ = ['BaseModule']
