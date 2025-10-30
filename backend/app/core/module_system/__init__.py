"""
Module System for Pluggable Architecture

This package provides the infrastructure for discovering, loading,
installing, and managing pluggable modules in the platform.
"""

from .base_module import BaseModule
from .loader import ModuleLoader
from .registry import ModuleRegistryService

__all__ = [
    "BaseModule",
    "ModuleLoader",
    "ModuleRegistryService",
]
