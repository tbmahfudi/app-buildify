#!/bin/bash

# Script to add Module Management menu item via API
# Make sure your backend is running and you have a valid token

# Configuration
API_URL="http://localhost:8000"  # Change to your backend URL
TOKEN="your_token_here"           # Get this from localStorage in browser

echo "Adding Module Management menu item..."

# First, get the No-Code Platform parent menu ID
PARENT_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/menu/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

# Extract parent menu ID (using jq if available, otherwise manual)
if command -v jq &> /dev/null; then
    PARENT_ID=$(echo "$PARENT_RESPONSE" | jq -r '.[] | select(.name=="No-Code Platform") | .id' | head -1)
    echo "Found No-Code Platform menu ID: $PARENT_ID"
else
    echo "Note: Install 'jq' for automatic parsing, or manually extract parent_id from:"
    echo "$PARENT_RESPONSE"
    read -p "Enter No-Code Platform menu ID: " PARENT_ID
fi

if [ -z "$PARENT_ID" ] || [ "$PARENT_ID" = "null" ]; then
    echo "Error: No-Code Platform menu not found!"
    echo "Please create it first or check if it exists with a different name."
    exit 1
fi

# Create Module Management menu item
echo "Creating Module Management menu item..."

curl -X POST "$API_URL/api/v1/menu/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"parent_id\": \"$PARENT_ID\",
    \"name\": \"Module Management\",
    \"path\": \"/nocode-modules.html\",
    \"icon\": \"package\",
    \"position\": 5,
    \"is_active\": true,
    \"description\": \"Create and manage business domain modules\",
    \"required_permission\": \"modules:read:tenant\"
  }"

echo ""
echo "Done! Refresh your browser to see the new menu item."
echo ""
echo "If you see an error, make sure:"
echo "1. Your backend is running"
echo "2. Your token is valid (check localStorage.getItem('token') in browser)"
echo "3. You have permission to create menu items"
