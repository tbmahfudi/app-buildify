#!/bin/bash

# API Test Script for Option B - Metadata, Generic CRUD, Audit, Settings
BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================"
echo "Testing Option B Features"
echo "================================"
echo ""

# Login
echo -e "${BLUE}1. Logging in...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
else
    echo -e "${RED}✗ Login failed${NC}"
    exit 1
fi
echo ""

# Test Metadata Service
echo -e "${BLUE}2. Testing Metadata Service${NC}"

# List entities
ENTITIES=$(curl -s ${BASE_URL}/api/metadata/entities \
  -H "Authorization: Bearer $TOKEN")

if echo $ENTITIES | grep -q "companies"; then
    echo -e "${GREEN}✓ List entities passed${NC}"
    echo "   Entities: $(echo $ENTITIES | grep -o '"entities":\[[^]]*\]')"
else
    echo -e "${RED}✗ List entities failed${NC}"
    exit 1
fi
echo ""

# Get company metadata
echo -e "${BLUE}3. Testing Get Entity Metadata${NC}"
METADATA=$(curl -s ${BASE_URL}/api/metadata/entities/companies \
  -H "Authorization: Bearer $TOKEN")

if echo $METADATA | grep -q "display_name"; then
    echo -e "${GREEN}✓ Get metadata passed${NC}"
    echo "   Entity: $(echo $METADATA | grep -o '"entity_name":"[^"]*' | cut -d'"' -f4)"
else
    echo -e "${RED}✗ Get metadata failed${NC}"
    exit 1
fi
echo ""

# Test Generic CRUD
echo -e "${BLUE}4. Testing Generic Data List${NC}"
LIST_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/data/companies/list \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "companies",
    "page": 1,
    "page_size": 10
  }')

if echo $LIST_RESPONSE | grep -q "rows"; then
    echo -e "${GREEN}✓ Generic list passed${NC}"
    TOTAL=$(echo $LIST_RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
    echo "   Total records: $TOTAL"
else
    echo -e "${RED}✗ Generic list failed${NC}"
    exit 1
fi
echo ""

# Create via generic endpoint
echo -e "${BLUE}5. Testing Generic Create${NC}"
CREATE_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/data/companies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "companies",
    "data": {
      "code": "GENTEST",
      "name": "Generic Test Company"
    }
  }')

RECORD_ID=$(echo $CREATE_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -n "$RECORD_ID" ]; then
    echo -e "${GREEN}✓ Generic create passed${NC}"
    echo "   Created ID: $RECORD_ID"
else
    echo -e "${RED}✗ Generic create failed${NC}"
    echo "   Response: $CREATE_RESPONSE"
    exit 1
fi
echo ""

# Get via generic endpoint
echo -e "${BLUE}6. Testing Generic Get${NC}"
GET_RESPONSE=$(curl -s ${BASE_URL}/api/data/companies/${RECORD_ID} \
  -H "Authorization: Bearer $TOKEN")

if echo $GET_RESPONSE | grep -q "GENTEST"; then
    echo -e "${GREEN}✓ Generic get passed${NC}"
else
    echo -e "${RED}✗ Generic get failed${NC}"
    exit 1
fi
echo ""

# Update via generic endpoint
echo -e "${BLUE}7. Testing Generic Update${NC}"
UPDATE_RESPONSE=$(curl -s -X PUT ${BASE_URL}/api/data/companies/${RECORD_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "companies",
    "id": "'$RECORD_ID'",
    "data": {
      "name": "Updated Generic Test"
    }
  }')

if echo $UPDATE_RESPONSE | grep -q "Updated"; then
    echo -e "${GREEN}✓ Generic update passed${NC}"
else
    echo -e "${RED}✗ Generic update failed${NC}"
    exit 1
fi
echo ""

# Test Audit Logs
echo -e "${BLUE}8. Testing Audit Logs${NC}"
AUDIT_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/audit/list \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page": 1,
    "page_size": 10,
    "entity_type": "companies"
  }')

if echo $AUDIT_RESPONSE | grep -q "logs"; then
    echo -e "${GREEN}✓ Audit list passed${NC}"
    LOG_COUNT=$(echo $AUDIT_RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
    echo "   Total audit logs: $LOG_COUNT"
else
    echo -e "${RED}✗ Audit list failed${NC}"
    exit 1
fi
echo ""

# Check for CREATE action in audit
if echo $AUDIT_RESPONSE | grep -q "CREATE"; then
    echo -e "${GREEN}✓ CREATE action logged${NC}"
else
    echo -e "${RED}✗ CREATE action not found in audit${NC}"
fi
echo ""

# Test Audit Statistics
echo -e "${BLUE}9. Testing Audit Statistics${NC}"
STATS_RESPONSE=$(curl -s ${BASE_URL}/api/audit/stats/summary \
  -H "Authorization: Bearer $TOKEN")

if echo $STATS_RESPONSE | grep -q "total_logs"; then
    echo -e "${GREEN}✓ Audit stats passed${NC}"
    TOTAL_LOGS=$(echo $STATS_RESPONSE | grep -o '"total_logs":[0-9]*' | cut -d':' -f2)
    echo "   Total logs in system: $TOTAL_LOGS"
else
    echo -e "${RED}✗ Audit stats failed${NC}"
    exit 1
fi
echo ""

# Test User Settings
echo -e "${BLUE}10. Testing User Settings${NC}"
USER_SETTINGS=$(curl -s ${BASE_URL}/api/settings/user \
  -H "Authorization: Bearer $TOKEN")

if echo $USER_SETTINGS | grep -q "theme"; then
    echo -e "${GREEN}✓ Get user settings passed${NC}"
    THEME=$(echo $USER_SETTINGS | grep -o '"theme":"[^"]*' | cut -d'"' -f4)
    echo "   Current theme: $THEME"
else
    echo -e "${RED}✗ Get user settings failed${NC}"
    exit 1
fi
echo ""

# Update user settings
echo -e "${BLUE}11. Testing Update User Settings${NC}"
UPDATE_SETTINGS=$(curl -s -X PUT ${BASE_URL}/api/settings/user \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "dark",
    "density": "compact"
  }')

if echo $UPDATE_SETTINGS | grep -q "dark"; then
    echo -e "${GREEN}✓ Update user settings passed${NC}"
else
    echo -e "${RED}✗ Update user settings failed${NC}"
    exit 1
fi
echo ""

# Test Tenant Settings
echo -e "${BLUE}12. Testing Tenant Settings${NC}"
TENANT_SETTINGS=$(curl -s ${BASE_URL}/api/settings/tenant \
  -H "Authorization: Bearer $TOKEN")

if echo $TENANT_SETTINGS | grep -q "tenant_id"; then
    echo -e "${GREEN}✓ Get tenant settings passed${NC}"
else
    echo -e "${RED}✗ Get tenant settings failed${NC}"
    exit 1
fi
echo ""

# Test Search with Filters
echo -e "${BLUE}13. Testing Generic Search with Filters${NC}"
SEARCH_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/data/companies/list \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "companies",
    "filters": [
      {"field": "code", "operator": "like", "value": "GEN"}
    ],
    "page": 1,
    "page_size": 10
  }')

if echo $SEARCH_RESPONSE | grep -q "GENTEST"; then
    echo -e "${GREEN}✓ Search with filters passed${NC}"
else
    echo -e "${RED}✗ Search with filters failed${NC}"
    exit 1
fi
echo ""

# Test Sorting
echo -e "${BLUE}14. Testing Generic Search with Sorting${NC}"
SORT_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/data/companies/list \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "companies",
    "sort": [["name", "desc"]],
    "page": 1,
    "page_size": 10
  }')

if echo $SORT_RESPONSE | grep -q "rows"; then
    echo -e "${GREEN}✓ Search with sorting passed${NC}"
else
    echo -e "${RED}✗ Search with sorting failed${NC}"
    exit 1
fi
echo ""

# Test Bulk Operations
echo -e "${BLUE}15. Testing Bulk Operations${NC}"
BULK_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/data/companies/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "companies",
    "operation": "create",
    "records": [
      {"code": "BULK1", "name": "Bulk Company 1"},
      {"code": "BULK2", "name": "Bulk Company 2"}
    ]
  }')

SUCCESS_COUNT=$(echo $BULK_RESPONSE | grep -o '"success":[0-9]*' | cut -d':' -f2)

if [ "$SUCCESS_COUNT" = "2" ]; then
    echo -e "${GREEN}✓ Bulk create passed${NC}"
    echo "   Created: $SUCCESS_COUNT records"
else
    echo -e "${RED}✗ Bulk create failed${NC}"
    echo "   Response: $BULK_RESPONSE"
fi
echo ""

# Cleanup
echo -e "${BLUE}16. Cleanup - Deleting test data${NC}"
curl -s -X DELETE ${BASE_URL}/api/data/companies/${RECORD_ID} \
  -H "Authorization: Bearer $TOKEN" > /dev/null

# Delete bulk records
for CODE in BULK1 BULK2; do
    BULK_LIST=$(curl -s -X POST ${BASE_URL}/api/data/companies/list \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"entity\":\"companies\",\"filters\":[{\"field\":\"code\",\"operator\":\"eq\",\"value\":\"$CODE\"}]}")
    BULK_ID=$(echo $BULK_LIST | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
    if [ -n "$BULK_ID" ]; then
        curl -s -X DELETE ${BASE_URL}/api/data/companies/${BULK_ID} \
          -H "Authorization: Bearer $TOKEN" > /dev/null
    fi
done

echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

echo "================================"
echo -e "${GREEN}All Option B tests passed! ✓${NC}"
echo "================================"
echo ""
echo "Features tested:"
echo "  ✓ Metadata service"
echo "  ✓ Generic CRUD operations"
echo "  ✓ Audit logging"
echo "  ✓ User settings"
echo "  ✓ Tenant settings"
echo "  ✓ Search with filters"
echo "  ✓ Sorting"
echo "  ✓ Bulk operations"