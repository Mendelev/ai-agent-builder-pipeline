#!/bin/bash

# R3 - Requirement Refinement - Exemplos de Curl
# Este script demonstra como usar a API de refinamento de requisitos

BASE_URL="http://localhost:8000/api/v1"

echo "=========================================="
echo "  R3 - Requirement Refinement Examples"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if API is running
echo -e "${BLUE}Checking API availability...${NC}"
if ! curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}✗ API is not running on http://localhost:8000${NC}"
    echo ""
    echo "Please start the API first:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  python main.py"
    exit 1
fi
echo -e "${GREEN}✓ API is running${NC}"
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}✗ jq is not installed${NC}"
    echo "Install with: sudo apt-get install jq"
    exit 1
fi

# 1. Create Project
echo -e "${BLUE}1. Creating project...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "$BASE_URL/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E-commerce Platform",
    "description": "A modern e-commerce platform with payment integration"
  }')

if ! echo "$PROJECT_RESPONSE" | jq -e . >/dev/null 2>&1; then
    echo -e "${RED}✗ Failed to create project. Response:${NC}"
    echo "$PROJECT_RESPONSE"
    exit 1
fi

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
if [[ "$PROJECT_ID" == "null" || -z "$PROJECT_ID" ]]; then
    echo -e "${RED}✗ Failed to get project ID${NC}"
    echo "$PROJECT_RESPONSE" | jq
    exit 1
fi

echo -e "${GREEN}✓ Project created: $PROJECT_ID${NC}"
echo ""

# 2. Add Requirements (with intentional issues)
echo -e "${BLUE}2. Adding requirements with ambiguities...${NC}"

# REQ-001: Testability issues
curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "REQ-001",
    "data": {
      "description": "The system should be fast and user-friendly with good performance"
    }
  }' > /dev/null
echo -e "${GREEN}✓ Added REQ-001 (testability issues)${NC}"

# REQ-002: Dependency issues
curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "REQ-002",
    "data": {
      "description": "The system depends on payment gateway and should handle many concurrent users"
    }
  }' > /dev/null
echo -e "${GREEN}✓ Added REQ-002 (dependency issues)${NC}"

# REQ-003: Ambiguity issues
curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "REQ-003",
    "data": {
      "description": "It should probably integrate with external APIs appropriately and handle some edge cases"
    }
  }' > /dev/null
echo -e "${GREEN}✓ Added REQ-003 (ambiguity issues)${NC}"
echo ""

# 3. Round 1 - Initial Refinement
echo -e "${BLUE}3. Starting refinement (Round 1)...${NC}"
REQUEST_ID_1=$(uuidgen)

REFINE_RESPONSE=$(curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/refine" \
  -H "Content-Type: application/json" \
  -d "{
    \"max_rounds\": 3,
    \"request_id\": \"$REQUEST_ID_1\"
  }")

# Check if response is valid JSON
if ! echo "$REFINE_RESPONSE" | jq -e . >/dev/null 2>&1; then
    echo -e "${RED}✗ Invalid response from refinement endpoint${NC}"
    echo "Response: $REFINE_RESPONSE"
    exit 1
fi

# Check for error in response
if echo "$REFINE_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    echo -e "${RED}✗ Error from API:${NC}"
    echo "$REFINE_RESPONSE" | jq -r '.detail'
    exit 1
fi

echo "$REFINE_RESPONSE" | jq
echo ""

# Extract questions for display
QUESTIONS_COUNT=$(echo "$REFINE_RESPONSE" | jq -r '.open_questions | length // 0')
echo -e "${YELLOW}📋 Generated $QUESTIONS_COUNT questions${NC}"

if [ "$QUESTIONS_COUNT" -gt 0 ]; then
    echo "$REFINE_RESPONSE" | jq -r '.open_questions[] | "  [\(.category | ascii_upcase)] \(.text)"'
fi
echo ""

# 4. Round 2 - With Answers
echo -e "${BLUE}4. Submitting answers (Round 2)...${NC}"
REQUEST_ID_2=$(uuidgen)

# Get first question ID (would come from previous response in real scenario)
Q1_ID=$(echo "$REFINE_RESPONSE" | jq -r '.open_questions[0].id // "q1"')
Q2_ID=$(echo "$REFINE_RESPONSE" | jq -r '.open_questions[1].id // "q2"')
Q3_ID=$(echo "$REFINE_RESPONSE" | jq -r '.open_questions[2].id // "q3"')

REFINE_WITH_ANSWERS=$(curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/refine" \
  -H "Content-Type: application/json" \
  -d "{
    \"max_rounds\": 3,
    \"request_id\": \"$REQUEST_ID_2\",
    \"answers\": [
      {
        \"question_id\": \"$Q1_ID\",
        \"text\": \"Performance: p95 response time < 200ms, p99 < 500ms. UI: System Usability Scale (SUS) score > 80. Error rate < 0.1%.\",
        \"confidence\": 5
      },
      {
        \"question_id\": \"$Q2_ID\",
        \"text\": \"Payment: Stripe API v2023-10-16. Concurrent users: 1000 simultaneous connections. Fallback to queue after 1000.\",
        \"confidence\": 4
      },
      {
        \"question_id\": \"$Q3_ID\",
        \"text\": \"External APIs: REST with OAuth 2.0. Timeout: 5s. Retry: 3 attempts with exponential backoff (1s, 2s, 4s). Circuit breaker after 5 failures.\",
        \"confidence\": 5
      }
    ]
  }")

echo "$REFINE_WITH_ANSWERS" | jq
echo ""

# Check if requirements were refined
REFINED_VERSION=$(echo "$REFINE_WITH_ANSWERS" | jq -r '.refined_requirements_version // "null"')
if [ "$REFINED_VERSION" != "null" ]; then
    echo -e "${GREEN}✓ Requirements updated to version $REFINED_VERSION${NC}"
else
    echo -e "${YELLOW}⚠ Requirements not yet refined${NC}"
fi
echo ""

# 5. Get QA Sessions
echo -e "${BLUE}5. Getting QA sessions...${NC}"
SESSIONS=$(curl -s -X GET "$BASE_URL/projects/$PROJECT_ID/qa-sessions")
echo "$SESSIONS" | jq
echo ""

SESSIONS_COUNT=$(echo "$SESSIONS" | jq '.total')
echo -e "${GREEN}✓ Total sessions: $SESSIONS_COUNT${NC}"
echo ""

# 6. Test Idempotency
echo -e "${BLUE}6. Testing idempotency (same request_id)...${NC}"
IDEMPOTENT_RESPONSE=$(curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/refine" \
  -H "Content-Type: application/json" \
  -d "{
    \"max_rounds\": 3,
    \"request_id\": \"$REQUEST_ID_1\"
  }")

echo "$IDEMPOTENT_RESPONSE" | jq
echo ""
echo -e "${GREEN}✓ Idempotency test complete${NC}"
echo ""

# Summary
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo ""
echo "Project ID: $PROJECT_ID"
echo "Request IDs:"
echo "  - Round 1: $REQUEST_ID_1"
echo "  - Round 2: $REQUEST_ID_2"
echo ""
echo "View in Swagger UI:"
echo "  http://localhost:8000/docs#/qa_sessions"
echo ""
echo "Get specific session:"
echo "  curl $BASE_URL/projects/$PROJECT_ID/qa-sessions | jq '.sessions[0]'"
echo ""
echo -e "${GREEN}✓ All tests completed successfully!${NC}"
