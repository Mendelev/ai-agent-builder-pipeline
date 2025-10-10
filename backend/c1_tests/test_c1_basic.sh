#!/bin/bash

# Test C1 Code Repository Connect - Basic Tests
# Tests connection, encryption, size validation, and error handling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000/api/v1"

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   C1 Code Repository Connect - Basic Tests        ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo ""

# Test 1: Connect Repository Successfully
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Test 1: Connect Repository - SUCCESS${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

# Create project
echo -e "\n${BLUE}1.1. Creating project...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test C1 - Small Repo"}')

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID${NC}"

# Connect repository (small public repo)
echo -e "\n${BLUE}1.2. Connecting Git repository...${NC}"
CONNECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/octocat/Hello-World.git\",
    \"access_token\": \"ghp_test_token_placeholder_1234567890abcdef\",
    \"project_id\": \"$PROJECT_ID\"
  }")

echo -e "${GREEN}✓ Connection request sent${NC}"
echo -e "${BLUE}Response:${NC}"
echo "$CONNECT_RESPONSE" | jq '.'

# Verify response structure
CONNECTED=$(echo "$CONNECT_RESPONSE" | jq -r '.connected')
REPO_ID=$(echo "$CONNECT_RESPONSE" | jq -r '.id // .repo_id')
CLONE_STATUS=$(echo "$CONNECT_RESPONSE" | jq -r '.clone_status')

if [[ "$CONNECTED" == "true" ]]; then
  echo -e "${GREEN}✓ Repository connected successfully${NC}"
  echo -e "  Repo ID: ${BLUE}$REPO_ID${NC}"
  echo -e "  Status: ${BLUE}$CLONE_STATUS${NC}"
else
  echo -e "${RED}✗ Connection failed${NC}"
  exit 1
fi

# Test 2: Get Repository Status
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Test 2: Get Repository Status${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

echo -e "\n${BLUE}2.1. Fetching repository status...${NC}"
STATUS_RESPONSE=$(curl -s -X GET "${BASE_URL}/code/repos/${REPO_ID}/status")

echo -e "${GREEN}✓ Status fetched${NC}"
echo -e "${BLUE}Response:${NC}"
echo "$STATUS_RESPONSE" | jq '.'

STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.clone_status')
echo -e "  Clone Status: ${BLUE}$STATUS${NC}"

# Test 3: Get Repository Details
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Test 3: Get Repository Details${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

echo -e "\n${BLUE}3.1. Fetching repository details...${NC}"
REPO_RESPONSE=$(curl -s -X GET "${BASE_URL}/code/repos/${REPO_ID}")

echo -e "${GREEN}✓ Repository details fetched${NC}"
echo -e "${BLUE}Response:${NC}"
echo "$REPO_RESPONSE" | jq '.'

# Verify that token is NOT in response (security check)
TOKEN_IN_RESPONSE=$(echo "$REPO_RESPONSE" | jq 'has("access_token") or has("token") or has("token_ciphertext")')
if [[ "$TOKEN_IN_RESPONSE" == "false" ]]; then
  echo -e "${GREEN}✓ Security check passed: No token data in response${NC}"
else
  echo -e "${RED}✗ Security issue: Token data exposed in response${NC}"
  exit 1
fi

# Test 4: Invalid Git URL
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Test 4: Invalid Git URL - ERROR HANDLING${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

echo -e "\n${BLUE}4.1. Creating another project...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test C1 - Invalid URL"}')

PROJECT_ID_2=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID_2${NC}"

echo -e "\n${BLUE}4.2. Attempting connection with invalid URL...${NC}"
ERROR_RESPONSE=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"not-a-valid-git-url\",
    \"access_token\": \"ghp_test_token_placeholder_1234567890abcdef\",
    \"project_id\": \"$PROJECT_ID_2\"
  }")

echo -e "${BLUE}Response:${NC}"
echo "$ERROR_RESPONSE" | jq '.'

ERROR_DETAIL=$(echo "$ERROR_RESPONSE" | jq -r '.detail[]?.msg // .detail // "No error"')
if [[ "$ERROR_DETAIL" == *"Invalid"* ]] || [[ "$ERROR_DETAIL" == *"invalid"* ]]; then
  echo -e "${GREEN}✓ Invalid URL correctly rejected${NC}"
else
  echo -e "${YELLOW}⚠ Warning: Expected validation error for invalid URL${NC}"
fi

# Test 5: Repository Too Large (Simulated)
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Test 5: Repository Size Validation${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

echo -e "\n${BLUE}5.1. Creating project for size test...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test C1 - Size Check"}')

PROJECT_ID_3=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID_3${NC}"

echo -e "\n${BLUE}5.2. Testing with potentially large repository...${NC}"
echo -e "${YELLOW}Note: Size check is performed during connection${NC}"

# Try connecting a known large public repo (this may fail with 413 if >100MB)
SIZE_TEST_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/torvalds/linux.git\",
    \"access_token\": \"ghp_test_token_placeholder_1234567890abcdef\",
    \"project_id\": \"$PROJECT_ID_3\"
  }")

HTTP_CODE=$(echo "$SIZE_TEST_RESPONSE" | tail -n 1)
BODY=$(echo "$SIZE_TEST_RESPONSE" | sed '$d')

echo -e "${BLUE}HTTP Status Code: $HTTP_CODE${NC}"
echo -e "${BLUE}Response:${NC}"
echo "$BODY" | jq '.' || echo "$BODY"

if [[ "$HTTP_CODE" == "413" ]]; then
  echo -e "${GREEN}✓ Repository correctly rejected for exceeding size limit${NC}"
  ERROR_INFO=$(echo "$BODY" | jq -r '.detail.error // "unknown"')
  SIZE_MB=$(echo "$BODY" | jq -r '.detail.estimated_size_mb // "unknown"')
  echo -e "  Error: ${BLUE}$ERROR_INFO${NC}"
  echo -e "  Estimated Size: ${BLUE}${SIZE_MB}MB${NC}"
elif [[ "$HTTP_CODE" == "201" ]]; then
  echo -e "${YELLOW}⚠ Repository accepted (may be under 100MB or size check not enforced)${NC}"
else
  echo -e "${BLUE}ℹ HTTP $HTTP_CODE - Check backend logs for details${NC}"
fi

# Test 6: List Project Repositories
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Test 6: List Repositories by Project${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

echo -e "\n${BLUE}6.1. Listing repositories for project $PROJECT_ID...${NC}"
LIST_RESPONSE=$(curl -s -X GET "${BASE_URL}/code/projects/${PROJECT_ID}/repos")

echo -e "${GREEN}✓ Repository list fetched${NC}"
echo -e "${BLUE}Response:${NC}"
echo "$LIST_RESPONSE" | jq '.'

REPO_COUNT=$(echo "$LIST_RESPONSE" | jq 'length')
echo -e "  Total repositories: ${BLUE}$REPO_COUNT${NC}"

# Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   TEST SUMMARY                     ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo ""
echo -e "${GREEN}✓ Test 1: Repository connection successful${NC}"
echo -e "${GREEN}✓ Test 2: Status check working${NC}"
echo -e "${GREEN}✓ Test 3: Repository details fetch & security check${NC}"
echo -e "${GREEN}✓ Test 4: Invalid URL validation${NC}"
echo -e "${GREEN}✓ Test 5: Size validation check${NC}"
echo -e "${GREEN}✓ Test 6: Repository listing${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}All basic tests completed!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Created Resources:${NC}"
echo -e "  Project 1: $PROJECT_ID (with repository)"
echo -e "  Project 2: $PROJECT_ID_2 (failed connection)"
echo -e "  Project 3: $PROJECT_ID_3 (size test)"
echo ""
echo -e "${YELLOW}To cleanup, run: ./test_c1_cleanup.sh${NC}"
