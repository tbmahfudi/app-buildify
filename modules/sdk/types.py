from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class ModuleStatus(str, Enum):
    DRAFT = "draft"
    AVAILABLE = "available"
    STABLE = "stable"
    DEPRECATED = "deprecated"

@dataclass
class ModuleDependency:
    module_id: str
    min_version: Optional[str] = None
    max_version: Optional[str] = None

@dataclass
class ModulePermission:
    key: str
    label: str
    description: str
    category: str = "general"

@dataclass
class ModuleMenuItem:
    label: str
    route: str
    icon: Optional[str] = None
    parent: Optional[str] = None
    roles: List[str] = field(default_factory=list)

@dataclass
class ModuleManifest:
    name: str
    version: str
    display_name: str
    description: str
    author: str
    permissions: List[ModulePermission] = field(default_factory=list)
    menu_items: List[ModuleMenuItem] = field(default_factory=list)
    dependencies: List[ModuleDependency] = field(default_factory=list)
    tenant_scoped: bool = True

@dataclass
class HookResult:
    success: bool
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

class ModuleEvent(str, Enum):
    INSTALLED = "module.installed"
    ENABLED = "module.enabled"
    DISABLED = "module.disabled"
    UNINSTALLED = "module.uninstalled"
