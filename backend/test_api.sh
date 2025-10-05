#!/bin/bash

# API Test Script for Option A MVP
BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "================================"
echo "Testing NoCode App API - Option A MVP"
echo "================================"
echo ""

# 1. Health Check
echo "1. Testing health endpoint..."
HEALTH=$(curl -s ${BASE_URL}/api/healthz)
if echo $HEALTH | grep -q "ok"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi
echo ""

# 2. Login as Admin
echo "2. Testing login (admin)..."
LOGIN_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}')

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    echo "   Access token: ${ACCESS_TOKEN:0:20}..."
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "   Response: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

# 3. Get Current User
echo "3. Testing /api/auth/me..."
ME_RESPONSE=$(curl -s ${BASE_URL}/api/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo $ME_RESPONSE | grep -q "admin@example.com"; then
    echo -e "${GREEN}✓ Get current user passed${NC}"
    echo "   User: $(echo $ME_RESPONSE | grep -o '"email":"[^"]*' | cut -d'"' -f4)"
else
    echo -e "${RED}✗ Get current user failed${NC}"
    exit 1
fi
echo ""

# 4. List Companies
echo "4. Testing GET /api/org/companies..."
COMPANIES=$(curl -s ${BASE_URL}/api/org/companies \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo $COMPANIES | grep -q "items"; then
    echo -e "${GREEN}✓ List companies passed${NC}"
    COUNT=$(echo $COMPANIES | grep -o '"total":[0-9]*' | cut -d':' -f2)
    echo "   Total companies: $COUNT"
else
    echo -e "${RED}✗ List companies failed${NC}"
    exit 1
fi
echo ""

# 5. Create Company
echo "5. Testing POST /api/org/companies..."
NEW_COMPANY=$(curl -s -X POST ${BASE_URL}/api/org/companies \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"TEST","name":"Test Company"}')

COMPANY_ID=$(echo $NEW_COMPANY | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -n "$COMPANY_ID" ]; then
    echo -e "${GREEN}✓ Create company passed${NC}"
    echo "   Company ID: $COMPANY_ID"
else
    echo -e "${RED}✗ Create company failed${NC}"
    echo "   Response: $NEW_COMPANY"
    exit 1
fi
echo ""

# 6. Get Company
echo "6. Testing GET /api/org/companies/{id}..."
COMPANY=$(curl -s ${BASE_URL}/api/org/companies/${COMPANY_ID} \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo $COMPANY | grep -q "TEST"; then
    echo -e "${GREEN}✓ Get company passed${NC}"
else
    echo -e "${RED}✗ Get company failed${NC}"
    exit 1
fi
echo ""

# 7. Update Company
echo "7. Testing PUT /api/org/companies/{id}..."
UPDATED=$(curl -s -X PUT ${BASE_URL}/api/org/companies/${COMPANY_ID} \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated Test Company"}')

if echo $UPDATED | grep -q "Updated"; then
    echo -e "${GREEN}✓ Update company passed${NC}"
else
    echo -e "${RED}✗ Update company failed${NC}"
    exit 1
fi
echo ""

# 8. Create Branch
echo "8. Testing POST /api/org/branches..."
NEW_BRANCH=$(curl -s -X POST ${BASE_URL}/api/org/branches \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"company_id\":\"${COMPANY_ID}\",\"code\":\"BR1\",\"name\":\"Branch 1\"}")

BRANCH_ID=$(echo $NEW_BRANCH | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -n "$BRANCH_ID" ]; then
    echo -e "${GREEN}✓ Create branch passed${NC}"
    echo "   Branch ID: $BRANCH_ID"
else
    echo -e "${RED}✗ Create branch failed${NC}"
    echo "   Response: $NEW_BRANCH"
    exit 1
fi
echo ""

# 9. Create Department
echo "9. Testing POST /api/org/departments..."
NEW_DEPT=$(curl -s -X POST ${BASE_URL}/api/org/departments \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"company_id\":\"${COMPANY_ID}\",\"branch_id\":\"${BRANCH_ID}\",\"code\":\"DEPT1\",\"name\":\"Department 1\"}")

DEPT_ID=$(echo $NEW_DEPT | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -n "$DEPT_ID" ]; then
    echo -e "${GREEN}✓ Create department passed${NC}"
    echo "   Department ID: $DEPT_ID"
else
    echo -e "${RED}✗ Create department failed${NC}"
    exit 1
fi
echo ""

# 10. Test Token Refresh
echo "10. Testing POST /api/auth/refresh..."
REFRESH_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"${REFRESH_TOKEN}\"}")

NEW_ACCESS_TOKEN=$(echo $REFRESH_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$NEW_ACCESS_TOKEN" ]; then
    echo -e "${GREEN}✓ Token refresh passed${NC}"
    echo "   New token: ${NEW_ACCESS_TOKEN:0:20}..."
else
    echo -e "${RED}✗ Token refresh failed${NC}"
    exit 1
fi
echo ""

# 11. Test RBAC - Login as viewer
echo "11. Testing RBAC (viewer cannot create)..."
VIEWER_LOGIN=$(curl -s -X POST ${BASE_URL}/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"viewer@example.com","password":"viewer123"}')

VIEWER_TOKEN=$(echo $VIEWER_LOGIN | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

VIEWER_CREATE=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/api/org/companies \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"FAIL","name":"Should Fail"}')

HTTP_CODE=$(echo "$VIEWER_CREATE" | tail -n1)

if [ "$HTTP_CODE" = "403" ]; then
    echo -e "${GREEN}✓ RBAC enforcement passed (403 Forbidden)${NC}"
else
    echo -e "${RED}✗ RBAC enforcement failed (expected 403, got $HTTP_CODE)${NC}"
    exit 1
fi
echo ""

# Cleanup
echo "12. Cleanup - Deleting test data..."
curl -s -X DELETE ${BASE_URL}/api/org/companies/${COMPANY_ID} \
  -H "Authorization: Bearer $ACCESS_TOKEN" > /dev/null
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

echo "================================"
echo -e "${GREEN}All tests passed! ✓${NC}"
echo "================================"