"""
Backward-compatibility shim.

The CompanyModule class has been merged into the unified ModuleActivation model
in nocode_module.py. Company-level activation is now handled by setting
company_id on a ModuleActivation row.

This file re-exports the alias so that existing imports continue to work:
    from app.models.company_module import CompanyModule
"""

from .nocode_module import ModuleActivation as CompanyModule

__all__ = ["CompanyModule"]
