#!/bin/bash
#
# Enable Financial Module via API
#
# This script enables the financial module for the current user's tenant.
# Run this script after logging in to the application.
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000/api/v1}"

echo ""
echo "========================================"
echo "  Financial Module Enablement Script"
echo "========================================"
echo ""

# Check if AUTH_TOKEN is provided
if [ -z "$AUTH_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  AUTH_TOKEN environment variable not set${NC}"
    echo ""
    echo "Please provide your authentication token:"
    echo "1. Log in to the application in your browser"
    echo "2. Open Browser DevTools (F12)"
    echo "3. Go to Console tab"
    echo "4. Run: localStorage.getItem('tokens')"
    echo "5. Copy the access_token value"
    echo ""
    read -p "Enter your access token: " AUTH_TOKEN
    echo ""
fi

if [ -z "$AUTH_TOKEN" ]; then
    echo -e "${RED}❌ No token provided. Exiting.${NC}"
    exit 1
fi

# Step 1: Check current module status
echo -e "${BLUE}1️⃣  Checking module status...${NC}"
echo "---"

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    "$API_BASE_URL/modules/enabled/names")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ Successfully fetched enabled modules${NC}"
    echo "Enabled modules: $BODY"

    if echo "$BODY" | grep -q '"financial"'; then
        echo -e "${GREEN}✅ Financial module is ALREADY ENABLED${NC}"
        echo ""
        echo "If the menu is still not showing, try:"
        echo "  1. Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)"
        echo "  2. Clear browser cache"
        echo "  3. Check browser console for JavaScript errors"
        echo "  4. Open: http://localhost:PORT/debug-financial-module.html"
        exit 0
    else
        echo -e "${YELLOW}⚠️  Financial module is NOT enabled${NC}"
    fi
else
    echo -e "${RED}❌ Failed to check module status (HTTP $HTTP_CODE)${NC}"
    echo "Response: $BODY"
    exit 1
fi

echo ""

# Step 2: Check if module is installed
echo -e "${BLUE}2️⃣  Checking if module is installed...${NC}"
echo "---"

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    "$API_BASE_URL/modules/financial")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ Module information retrieved${NC}"

    IS_INSTALLED=$(echo "$BODY" | grep -o '"is_installed":[^,}]*' | cut -d':' -f2 | tr -d ' ')

    if [ "$IS_INSTALLED" = "true" ]; then
        echo -e "${GREEN}✅ Financial module is installed${NC}"
    else
        echo -e "${YELLOW}⚠️  Financial module is NOT installed${NC}"
        echo ""
        echo "Installing module..."

        INSTALL_RESPONSE=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"module_name": "financial"}' \
            "$API_BASE_URL/modules/install")

        INSTALL_HTTP_CODE=$(echo "$INSTALL_RESPONSE" | tail -n 1)
        INSTALL_BODY=$(echo "$INSTALL_RESPONSE" | sed '$d')

        if [ "$INSTALL_HTTP_CODE" -eq 200 ]; then
            echo -e "${GREEN}✅ Module installed successfully${NC}"
        else
            echo -e "${RED}❌ Failed to install module (HTTP $INSTALL_HTTP_CODE)${NC}"
            echo "Response: $INSTALL_BODY"
            echo ""
            echo "Note: You might need superuser permissions to install modules"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Could not get module info (HTTP $HTTP_CODE)${NC}"
    echo "Continuing anyway..."
fi

echo ""

# Step 3: Enable module for tenant
echo -e "${BLUE}3️⃣  Enabling financial module for your tenant...${NC}"
echo "---"

ENABLE_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "module_name": "financial",
        "configuration": {
            "default_currency": "USD",
            "fiscal_year_start": "01-01",
            "enable_multi_currency": false,
            "tax_rate": 0,
            "invoice_prefix": "INV"
        }
    }' \
    "$API_BASE_URL/modules/enable")

ENABLE_HTTP_CODE=$(echo "$ENABLE_RESPONSE" | tail -n 1)
ENABLE_BODY=$(echo "$ENABLE_RESPONSE" | sed '$d')

if [ "$ENABLE_HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ Financial module enabled successfully!${NC}"
    echo "Response: $ENABLE_BODY"
else
    echo -e "${RED}❌ Failed to enable module (HTTP $ENABLE_HTTP_CODE)${NC}"
    echo "Response: $ENABLE_BODY"

    if echo "$ENABLE_BODY" | grep -q "already enabled"; then
        echo -e "${YELLOW}Note: Module might already be enabled${NC}"
    elif echo "$ENABLE_BODY" | grep -q "permission"; then
        echo -e "${YELLOW}Note: You might need tenant admin permissions${NC}"
    fi

    exit 1
fi

echo ""
echo "========================================"
echo -e "${GREEN}✅ SUCCESS!${NC}"
echo "========================================"
echo ""
echo "The financial module has been enabled."
echo ""
echo "Next steps:"
echo "  1. Refresh your browser (or hard refresh: Ctrl+Shift+R)"
echo "  2. The Financial menu should now appear in the sidebar"
echo "  3. If not visible, check user permissions:"
echo "     - User must be in a group with financial permissions"
echo "     - Run: python -m backend.app.seeds.seed_financial_rbac.py"
echo ""
echo "Troubleshooting:"
echo "  • Open browser diagnostic: http://localhost:PORT/debug-financial-module.html"
echo "  • Check browser console for errors (F12 > Console)"
echo "  • Verify permissions: GET $API_BASE_URL/auth/me"
echo ""
