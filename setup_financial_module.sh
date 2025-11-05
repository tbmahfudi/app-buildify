#!/bin/bash
#
# Setup Financial Module
# This script installs and enables the financial module for a tenant
#

set -e

API_BASE="http://localhost:8000/api/v1"
TOKEN=""

echo "============================================"
echo "Financial Module Setup Script"
echo "============================================"
echo ""

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3

    if [ -z "$data" ]; then
        curl -s -X "$method" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            "${API_BASE}${endpoint}"
    else
        curl -s -X "$method" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${API_BASE}${endpoint}"
    fi
}

# Check if token is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <AUTH_TOKEN>"
    echo ""
    echo "To get your auth token:"
    echo "1. Login via: curl -X POST http://localhost:8000/api/v1/auth/login \\"
    echo "              -H 'Content-Type: application/json' \\"
    echo "              -d '{\"email\":\"your@email.com\",\"password\":\"yourpassword\"}'"
    echo "2. Copy the 'access_token' from the response"
    echo "3. Run: $0 YOUR_ACCESS_TOKEN"
    echo ""
    exit 1
fi

TOKEN=$1

echo "Step 1: Checking available modules..."
echo "--------------------------------------"
AVAILABLE=$(api_call GET "/modules/available")
echo "$AVAILABLE" | python3 -m json.tool
echo ""

echo "Step 2: Installing financial module (requires superuser)..."
echo "-----------------------------------------------------------"
INSTALL_RESULT=$(api_call POST "/modules/install" '{"module_name": "financial"}')
echo "$INSTALL_RESULT" | python3 -m json.tool
echo ""

echo "Step 3: Enabling financial module for your tenant..."
echo "----------------------------------------------------"
ENABLE_RESULT=$(api_call POST "/modules/enable" '{"module_name": "financial", "configuration": {"default_currency": "USD", "fiscal_year_start": "01-01", "enable_multi_currency": false, "tax_rate": 0, "invoice_prefix": "INV"}}')
echo "$ENABLE_RESULT" | python3 -m json.tool
echo ""

echo "Step 4: Verifying enabled modules..."
echo "-------------------------------------"
ENABLED=$(api_call GET "/modules/enabled/names")
echo "Enabled modules: $ENABLED"
echo ""

echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "The financial module should now be available at:"
echo "  - ${API_BASE}/financial/accounts"
echo "  - ${API_BASE}/financial/invoices"
echo "  - ${API_BASE}/financial/transactions"
echo "  - ${API_BASE}/financial/payments"
echo "  - ${API_BASE}/financial/reports"
echo ""
