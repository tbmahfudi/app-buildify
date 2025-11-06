#!/usr/bin/env python3
"""
Verification script for module system setup
Run this after backend restart to verify everything is configured correctly
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file(path: str, description: str) -> bool:
    """Check if a file exists"""
    if os.path.exists(path):
        print(f"{GREEN}✓{RESET} {description}")
        return True
    else:
        print(f"{RED}✗{RESET} {description}")
        return False

def check_content(path: str, search_string: str, description: str) -> bool:
    """Check if a file contains a specific string"""
    try:
        with open(path, 'r') as f:
            content = f.read()
            if search_string in content:
                print(f"{GREEN}✓{RESET} {description}")
                return True
            else:
                print(f"{RED}✗{RESET} {description}")
                return False
    except Exception as e:
        print(f"{RED}✗{RESET} {description} (Error: {e})")
        return False

def main():
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Module System Setup Verification{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    checks_passed = 0
    checks_failed = 0

    # Backend files
    print(f"\n{YELLOW}Backend Files:{RESET}")

    checks = [
        ("backend/app/core/module_system/registry.py",
         "Module registry exists"),
        ("backend/modules/financial/module.py",
         "Financial module exists"),
        ("backend/modules/financial/manifest.json",
         "Financial manifest exists"),
        ("backend/app/seeds/seed_module_management_rbac.py",
         "RBAC seed file exists"),
    ]

    for path, desc in checks:
        if check_file(path, desc):
            checks_passed += 1
        else:
            checks_failed += 1

    # Frontend files
    print(f"\n{YELLOW}Frontend Files:{RESET}")

    checks = [
        ("frontend/assets/js/module-manager-enhanced.js",
         "Module manager UI exists"),
        ("frontend/assets/js/modules.js",
         "Module route handler exists"),
        ("frontend/assets/templates/modules.html",
         "Module template exists"),
        ("frontend/config/menu.json",
         "Menu configuration exists"),
    ]

    for path, desc in checks:
        if check_file(path, desc):
            checks_passed += 1
        else:
            checks_failed += 1

    # Content checks
    print(f"\n{YELLOW}Code Verifications:{RESET}")

    content_checks = [
        ("backend/app/core/module_system/registry.py",
         "self.db.flush()",
         "UUID fix (db.flush) present"),
        ("backend/app/core/module_system/registry.py",
         'code_parts = perm_data["code"].split(":")',
         "Permission parsing present"),
        ("backend/modules/financial/module.py",
         "from sqlalchemy import text",
         "SQLAlchemy text() import present"),
        ("frontend/assets/js/module-manager-enhanced.js",
         "'Content-Type': 'application/json'",
         "Content-Type header present"),
        ("frontend/assets/js/app-entry.js",
         "import './modules.js'",
         "Modules.js imported in app-entry"),
        ("frontend/config/menu.json",
         '"route": "modules"',
         "Module Management in menu"),
    ]

    for path, search, desc in content_checks:
        if check_content(path, search, desc):
            checks_passed += 1
        else:
            checks_failed += 1

    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"\n{GREEN}Passed: {checks_passed}{RESET}")
    print(f"{RED}Failed: {checks_failed}{RESET}")

    if checks_failed == 0:
        print(f"\n{GREEN}✓ All checks passed! Ready to test module installation.{RESET}")
        print(f"\n{YELLOW}Next steps:{RESET}")
        print("1. Restart your backend server")
        print("2. Navigate to http://localhost:8000/app#modules")
        print("3. Click 'Install' on the Financial module")
        print("4. Click 'Enable' to activate it for your tenant")
        print(f"\n{BLUE}See TEST_MODULE_INSTALLATION.md for detailed steps{RESET}\n")
        return 0
    else:
        print(f"\n{RED}✗ Some checks failed. Please review the errors above.{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
