"""
Seed data modules for database initialization.

Available seed scripts:
- seed_complete_org: Seed complete organizational structure (tenants, companies, users)
- seed_entity_metadata: Seed entity metadata for dynamic forms
- seed_financial_rbac: Seed financial module RBAC (roles, permissions, groups)
- seed_module_management_rbac: Seed module management RBAC
- seed_menu_items: Seed menu items from frontend/config/menu.json
- seed_menu_management_rbac: Seed menu management RBAC (new!)

Usage:
    python -m app.seeds.seed_menu_items
    python -m app.seeds.seed_menu_management_rbac [TENANT_CODE]
    python -m app.seeds.seed_module_management_rbac [TENANT_CODE]
"""

from .seed_complete_org import *
from .seed_entity_metadata import *
from .seed_financial_rbac import *
from .seed_module_management_rbac import *
from .seed_menu_items import *
from .seed_menu_management_rbac import *
