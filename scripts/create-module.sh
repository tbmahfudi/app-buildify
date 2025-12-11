#!/bin/bash

# Module Creation Script
# Creates a new pluggable module with complete backend and frontend structure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get module name from command line
if [ -z "$1" ]; then
    echo -e "${RED}Error: Module name is required${NC}"
    echo "Usage: ./create-module.sh <module-name>"
    echo "Example: ./create-module.sh warehousing"
    exit 1
fi

MODULE_NAME=$1
MODULE_CLASS=$(echo "$MODULE_NAME" | sed -r 's/(^|_)([a-z])/\U\2/g')  # Convert to PascalCase
MODULE_DISPLAY=$(echo "$MODULE_NAME" | sed 's/_/ /g; s/\b\(.\)/\u\1/g')  # Convert to Title Case

echo -e "${GREEN}Creating module: ${MODULE_NAME}${NC}"
echo -e "Class name: ${MODULE_CLASS}Module"
echo -e "Display name: ${MODULE_DISPLAY}"
echo ""

# Define paths
MODULE_BASE="modules/${MODULE_NAME}"
BACKEND_BASE="${MODULE_BASE}/backend"
FRONTEND_BASE="${MODULE_BASE}/frontend"

# Create backend directory structure
echo -e "${YELLOW}Creating backend structure...${NC}"
mkdir -p "${BACKEND_BASE}"/{models,schemas,routers,services,migrations,seeds,tests}

# Create __init__.py files
touch "${BACKEND_BASE}/models/__init__.py"
touch "${BACKEND_BASE}/schemas/__init__.py"
touch "${BACKEND_BASE}/routers/__init__.py"
touch "${BACKEND_BASE}/services/__init__.py"
touch "${BACKEND_BASE}/tests/__init__.py"

# Create permissions.py
cat > "${BACKEND_BASE}/permissions.py" <<EOF
"""
${MODULE_DISPLAY} Module Permissions

Permission definitions for the ${MODULE_NAME} module.
"""

from enum import Enum


class ${MODULE_CLASS}Permissions(str, Enum):
    """${MODULE_DISPLAY} module permission codes"""

    # Read
    READ = "${MODULE_NAME}:read:company"

    # Create
    CREATE = "${MODULE_NAME}:create:company"

    # Update
    UPDATE = "${MODULE_NAME}:update:company"

    # Delete
    DELETE = "${MODULE_NAME}:delete:company"
EOF

# Create module.py
cat > "${BACKEND_BASE}/module.py" <<EOF
"""
${MODULE_DISPLAY} Module

Main module definition for the ${MODULE_DISPLAY} module.
"""

from fastapi import APIRouter
from pathlib import Path
from typing import List, Dict, Any
import logging

from core.module_system.base_module import BaseModule

logger = logging.getLogger(__name__)


class ${MODULE_CLASS}Module(BaseModule):
    """
    ${MODULE_DISPLAY} Module

    Provides ${MODULE_NAME} management capabilities.
    """

    def get_router(self) -> APIRouter:
        """
        Return the main router for the ${MODULE_NAME} module.
        """
        router = APIRouter(
            prefix="/api/v1/${MODULE_NAME}",
            tags=["${MODULE_NAME}"]
        )

        # TODO: Include sub-routers here
        # from .routers import items_router
        # router.include_router(items_router)

        # Health check endpoint
        @router.get("/health")
        async def health_check():
            return {
                "module": self.name,
                "version": self.version,
                "status": "healthy"
            }

        return router

    def get_permissions(self) -> List[Dict[str, Any]]:
        """Return permissions defined in manifest."""
        return self.manifest.get("permissions", [])

    def get_models(self) -> List[Any]:
        """Return SQLAlchemy models for migration discovery."""
        return [
            # TODO: Add your models here
        ]

    def post_install(self, db_session: Any) -> None:
        """Post-installation tasks."""
        logger.info(f"Running post-install tasks for ${MODULE_DISPLAY} module")
        # TODO: Add installation tasks (e.g., create default data)
        pass

    def post_enable(self, db_session: Any, tenant_id: str) -> None:
        """Post-enable tasks for a tenant."""
        logger.info(f"Setting up ${MODULE_DISPLAY} module for tenant {tenant_id}")
        # TODO: Add tenant-specific setup
        pass
EOF

# Create backend manifest.json
cat > "${BACKEND_BASE}/manifest.json" <<EOF
{
  "name": "${MODULE_NAME}",
  "display_name": "${MODULE_DISPLAY}",
  "version": "1.0.0",
  "description": "${MODULE_DISPLAY} management system",
  "author": "Your Company",
  "license": "Proprietary",

  "compatibility": {
    "platform_version": ">=1.0.0",
    "python_version": ">=3.8"
  },

  "category": "business",
  "tags": ["${MODULE_NAME}"],

  "dependencies": {
    "required": [],
    "optional": []
  },

  "permissions": [
    {
      "code": "${MODULE_NAME}:read:company",
      "name": "View ${MODULE_DISPLAY}",
      "description": "View ${MODULE_NAME} data",
      "category": "${MODULE_NAME}",
      "scope": "company"
    },
    {
      "code": "${MODULE_NAME}:create:company",
      "name": "Create ${MODULE_DISPLAY}",
      "description": "Create new ${MODULE_NAME} records",
      "category": "${MODULE_NAME}",
      "scope": "company"
    },
    {
      "code": "${MODULE_NAME}:update:company",
      "name": "Update ${MODULE_DISPLAY}",
      "description": "Update ${MODULE_NAME} records",
      "category": "${MODULE_NAME}",
      "scope": "company"
    },
    {
      "code": "${MODULE_NAME}:delete:company",
      "name": "Delete ${MODULE_DISPLAY}",
      "description": "Delete ${MODULE_NAME} records",
      "category": "${MODULE_NAME}",
      "scope": "company"
    }
  ],

  "default_roles": {
    "${MODULE_DISPLAY} Admin": [
      "${MODULE_NAME}:*:company"
    ],
    "${MODULE_DISPLAY} User": [
      "${MODULE_NAME}:read:company",
      "${MODULE_NAME}:create:company",
      "${MODULE_NAME}:update:company"
    ]
  },

  "database": {
    "has_migrations": false,
    "tables": []
  },

  "api": {
    "prefix": "/api/v1/${MODULE_NAME}",
    "routes": []
  },

  "configuration": {
    "settings": []
  },

  "subscription_tier": "basic",
  "pricing": {
    "model": "per_company",
    "free_tier": true,
    "basic_tier": true,
    "premium_tier": true,
    "enterprise_tier": true
  },

  "installation": {
    "pre_install_checks": false,
    "post_install_tasks": []
  },

  "status": "beta",
  "homepage": "",
  "repository": "",
  "support_email": ""
}
EOF

# Create frontend directory structure
echo -e "${YELLOW}Creating frontend structure...${NC}"
mkdir -p "${FRONTEND_BASE}"/{components,pages,services,templates}

# Create frontend module.js
cat > "${FRONTEND_BASE}/module.js" <<EOF
/**
 * ${MODULE_DISPLAY} Module
 *
 * Frontend module for ${MODULE_NAME} management.
 */

import { BaseModule } from '../../assets/js/core/module-system/base-module.js';

export default class ${MODULE_CLASS}Module extends BaseModule {
  constructor(manifest) {
    super(manifest);
  }

  async init() {
    await super.init();
    console.log('${MODULE_DISPLAY} module initialized');

    // TODO: Add module-specific initialization
  }
}
EOF

# Create frontend manifest.json
cat > "${FRONTEND_BASE}/manifest.json" <<EOF
{
  "name": "${MODULE_NAME}",
  "display_name": "${MODULE_DISPLAY}",
  "version": "1.0.0",
  "description": "${MODULE_DISPLAY} management user interface",

  "entry_point": "module.js",

  "routes": [
    {
      "path": "#/${MODULE_NAME}/dashboard",
      "name": "${MODULE_DISPLAY} Dashboard",
      "component": "pages/dashboard-page.js",
      "permission": "${MODULE_NAME}:read:company",
      "menu": {
        "label": "${MODULE_DISPLAY}",
        "icon": "📦",
        "order": 20,
        "parent": null
      }
    }
  ],

  "navigation": {
    "primary_menu": true,
    "dashboard_widgets": []
  },

  "dependencies": {
    "core_version": ">=1.0.0",
    "required_modules": [],
    "optional_modules": []
  },

  "assets": {
    "css": [],
    "icons": []
  }
}
EOF

# Create sample dashboard page
cat > "${FRONTEND_BASE}/pages/dashboard-page.js" <<EOF
/**
 * ${MODULE_DISPLAY} Dashboard Page
 */

export default class ${MODULE_CLASS}DashboardPage {
  async render() {
    const container = document.getElementById('app-content');
    if (!container) return;

    container.innerHTML = \`
      <div class="${MODULE_NAME}-dashboard">
        <h1 class="text-2xl font-bold mb-6">${MODULE_DISPLAY} Dashboard</h1>

        <div class="card">
          <div class="card-body text-center py-12">
            <p class="text-gray-500 text-lg">Welcome to ${MODULE_DISPLAY} module!</p>
            <p class="text-sm text-gray-400 mt-2">
              Start building your ${MODULE_NAME} functionality here.
            </p>
          </div>
        </div>
      </div>
    \`;
  }
}
EOF

# Create README
cat > "${BACKEND_BASE}/README.md" <<EOF
# ${MODULE_DISPLAY} Module

${MODULE_DISPLAY} management module for the platform.

## Features

- TODO: List module features

## Installation

1. Module will be auto-discovered on server startup
2. Install via API: \`POST /api/v1/modules/install\`
3. Enable for tenant: \`POST /api/v1/modules/enable\`

## API Endpoints

- \`GET /api/v1/${MODULE_NAME}/health\` - Health check

## Configuration

See \`manifest.json\` for configuration options.

## Development

### Backend Structure
- \`models/\` - SQLAlchemy models
- \`schemas/\` - Pydantic validation schemas
- \`routers/\` - FastAPI routers
- \`services/\` - Business logic
- \`permissions.py\` - Permission definitions
- \`module.py\` - Module class definition

### Frontend Structure
- \`pages/\` - Page components
- \`components/\` - Reusable components
- \`services/\` - API services
- \`module.js\` - Module class definition

## License

Proprietary
EOF

echo ""
echo -e "${GREEN}✓ Module created successfully!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit ${BACKEND_BASE}/module.py to add your backend logic"
echo "2. Edit ${FRONTEND_BASE}/module.js to add your frontend logic"
echo "3. Add models in ${BACKEND_BASE}/models/"
echo "4. Add routers in ${BACKEND_BASE}/routers/"
echo "5. Add pages in ${FRONTEND_BASE}/pages/"
echo "6. Update manifest.json files with your module details"
echo ""
echo -e "${YELLOW}To install the module:${NC}"
echo "1. Restart the backend server to discover the module"
echo "2. Call POST /api/v1/modules/install with module_name='${MODULE_NAME}'"
echo "3. Call POST /api/v1/modules/enable with module_name='${MODULE_NAME}'"
echo ""
echo -e "${GREEN}Happy coding!${NC}"
