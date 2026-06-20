"""
App-Buildify Module SDK — Public API

Module developers import from here. Do NOT import from backend.app directly.
"""
from .base_module import BaseModule
from .types import (
    ModuleManifest, ModulePermission, ModuleMenuItem,
    ModuleDependency, HookResult, ModuleEvent
)
from .platform_bridge import PlatformBridge

__all__ = [
    'BaseModule', 'ModuleManifest', 'ModulePermission',
    'ModuleMenuItem', 'ModuleDependency', 'HookResult',
    'ModuleEvent', 'PlatformBridge',
]
