"""
Backward-compatibility shim.

The ModuleRegistry and TenantModule classes have been merged into the unified
Module and ModuleActivation models in nocode_module.py.

This file re-exports the aliases so that existing imports continue to work:
    from app.models.module_registry import ModuleRegistry, TenantModule
"""

from .nocode_module import Module as ModuleRegistry, ModuleActivation as TenantModule

__all__ = ["ModuleRegistry", "TenantModule"]
