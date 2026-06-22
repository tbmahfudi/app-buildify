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

__all__ = ['BaseModule', 'ModuleManifest', 'ModulePermission', 'ModuleMenuItem', 'ModuleDependency', 'HookResult', 'ModuleEvent', 'PlatformBridge', 'Base', 'GUID', 'generate_uuid', 'tenant_scoped_session', 'get_current_user', 'has_permission']

from modules.sdk.db import Base, GUID, generate_uuid
from modules.sdk.dependencies import tenant_scoped_session, get_current_user, has_permission
