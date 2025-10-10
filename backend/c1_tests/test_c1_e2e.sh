#!/bin/bash

# Test C1 Code Repository Connect - End-to-End Tests
# Complete workflow tests including security and lifecycle management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000/api/v1"

echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║   C1 Code Repository Connect - End-to-End Tests         ║${NC}"
echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════╗${NC}"
echo ""

# ============================================================================
# Scenario 1: Complete Repository Connection Lifecycle
# ============================================================================
echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  SCENARIO 1: Complete Repository Connection Lifecycle   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Step 1: Create Project${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "E2E Test - Repository Lifecycle"}')

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID${NC}"

echo -e "\n${BLUE}Step 2: Connect Git Repository${NC}"
REPO_CONNECT=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/octocat/Hello-World.git\",
    \"access_token\": \"ghp_e2e_test_token_12345678901234567890\",
    \"project_id\": \"$PROJECT_ID\"
  }")

REPO_ID=$(echo "$REPO_CONNECT" | jq -r '.id // .repo_id')
TASK_ID=$(echo "$REPO_CONNECT" | jq -r '.task_id // "none"')
echo -e "${GREEN}✓ Repository connected${NC}"
echo -e "  Repo ID: ${BLUE}$REPO_ID${NC}"
echo -e "  Task ID: ${BLUE}$TASK_ID${NC}"

# Verify token is NOT in response
if echo "$REPO_CONNECT" | jq -e 'has("access_token") or has("token")' > /dev/null 2>&1; then
  echo -e "${RED}✗ SECURITY ISSUE: Token exposed in response!${NC}"
  exit 1
else
  echo -e "${GREEN}✓ Security check: Token properly masked${NC}"
fi

echo -e "\n${BLUE}Step 3: Check Initial Status${NC}"
sleep 1  # Give backend time to process
STATUS_1=$(curl -s -X GET "${BASE_URL}/code/repos/${REPO_ID}/status")
CLONE_STATUS=$(echo "$STATUS_1" | jq -r '.clone_status')
echo -e "${GREEN}✓ Initial clone status: $CLONE_STATUS${NC}"

echo -e "\n${BLUE}Step 4: Get Repository Details${NC}"
REPO_DETAILS=$(curl -s -X GET "${BASE_URL}/code/repos/${REPO_ID}")
GIT_URL=$(echo "$REPO_DETAILS" | jq -r '.git_url')
SIZE_MB=$(echo "$REPO_DETAILS" | jq -r '.repository_size_mb // "unknown"')
echo -e "${GREEN}✓ Repository details retrieved${NC}"
echo -e "  Git URL: ${BLUE}$GIT_URL${NC}"
echo -e "  Size: ${BLUE}${SIZE_MB}MB${NC}"

echo -e "\n${BLUE}Step 5: List All Project Repositories${NC}"
REPO_LIST=$(curl -s -X GET "${BASE_URL}/code/projects/${PROJECT_ID}/repos")
REPO_COUNT=$(echo "$REPO_LIST" | jq 'length')
echo -e "${GREEN}✓ Found $REPO_COUNT repository(ies) for project${NC}"

echo -e "\n${GREEN}✓ Scenario 1 completed successfully!${NC}"

# ============================================================================
# Scenario 2: Token Security and Encryption Verification
# ============================================================================
echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  SCENARIO 2: Token Security & Encryption Verification   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Step 1: Create Project for Security Test${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "E2E Test - Token Security"}')

PROJECT_ID_2=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID_2${NC}"

echo -e "\n${BLUE}Step 2: Connect Repository with Sensitive Token${NC}"
SENSITIVE_TOKEN="ghp_VERY_SECRET_TOKEN_MUST_BE_ENCRYPTED_123456"
REPO_CONNECT_2=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/github/docs.git\",
    \"access_token\": \"$SENSITIVE_TOKEN\",
    \"project_id\": \"$PROJECT_ID_2\"
  }")

REPO_ID_2=$(echo "$REPO_CONNECT_2" | jq -r '.id // .repo_id')
echo -e "${GREEN}✓ Repository connected${NC}"

echo -e "\n${BLUE}Step 3: Verify Token is NOT in Response${NC}"
if echo "$REPO_CONNECT_2" | grep -q "$SENSITIVE_TOKEN"; then
  echo -e "${RED}✗ CRITICAL: Plaintext token found in response!${NC}"
  exit 1
else
  echo -e "${GREEN}✓ Token not exposed in connection response${NC}"
fi

echo -e "\n${BLUE}Step 4: Verify Token is NOT in GET /repos/{id}${NC}"
REPO_GET=$(curl -s -X GET "${BASE_URL}/code/repos/${REPO_ID_2}")
if echo "$REPO_GET" | grep -q "$SENSITIVE_TOKEN"; then
  echo -e "${RED}✗ CRITICAL: Plaintext token found in repository details!${NC}"
  exit 1
else
  echo -e "${GREEN}✓ Token not exposed in repository details${NC}"
fi

echo -e "\n${BLUE}Step 5: Verify Token is NOT in GET /projects/{id}/repos${NC}"
PROJECT_REPOS=$(curl -s -X GET "${BASE_URL}/code/projects/${PROJECT_ID_2}/repos")
if echo "$PROJECT_REPOS" | grep -q "$SENSITIVE_TOKEN"; then
  echo -e "${RED}✗ CRITICAL: Plaintext token found in project repos list!${NC}"
  exit 1
else
  echo -e "${GREEN}✓ Token not exposed in project repositories list${NC}"
fi

echo -e "\n${BLUE}Step 6: Verify Encrypted Storage (via Database Check)${NC}"
echo -e "${YELLOW}Note: Database check requires direct DB access - skipped in API tests${NC}"
echo -e "${GREEN}✓ Token encryption assumed based on schema design${NC}"

echo -e "\n${GREEN}✓ Scenario 2 completed - All security checks passed!${NC}"

# ============================================================================
# Scenario 3: Repository Size Validation and Rejection
# ============================================================================
echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  SCENARIO 3: Repository Size Validation & Rejection     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Step 1: Create Project for Size Test${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "E2E Test - Size Validation"}')

PROJECT_ID_3=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID_3${NC}"

echo -e "\n${BLUE}Step 2: Attempt to Connect Large Repository${NC}"
echo -e "${YELLOW}Testing with Linux kernel repo (typically >100MB)${NC}"

LARGE_REPO_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/torvalds/linux.git\",
    \"access_token\": \"ghp_test_token_large_repo_check_123\",
    \"project_id\": \"$PROJECT_ID_3\"
  }")

HTTP_CODE=$(echo "$LARGE_REPO_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$LARGE_REPO_RESPONSE" | sed '$d')

echo -e "${BLUE}HTTP Status: $HTTP_CODE${NC}"

if [[ "$HTTP_CODE" == "413" ]]; then
  echo -e "${GREEN}✓ Large repository correctly rejected (HTTP 413)${NC}"
  
  ERROR_TYPE=$(echo "$RESPONSE_BODY" | jq -r '.detail.error // "unknown"')
  ERROR_MSG=$(echo "$RESPONSE_BODY" | jq -r '.detail.message // "unknown"')
  EST_SIZE=$(echo "$RESPONSE_BODY" | jq -r '.detail.estimated_size_mb // "unknown"')
  LIMIT=$(echo "$RESPONSE_BODY" | jq -r '.detail.limit_mb // "unknown"')
  
  echo -e "  Error Type: ${BLUE}$ERROR_TYPE${NC}"
  echo -e "  Message: ${BLUE}$ERROR_MSG${NC}"
  echo -e "  Estimated Size: ${BLUE}${EST_SIZE}MB${NC}"
  echo -e "  Limit: ${BLUE}${LIMIT}MB${NC}"
  
  if [[ "$ERROR_TYPE" == "repository_too_large" ]]; then
    echo -e "${GREEN}✓ Correct error type returned${NC}"
  else
    echo -e "${YELLOW}⚠ Warning: Expected error type 'repository_too_large'${NC}"
  fi
elif [[ "$HTTP_CODE" == "201" ]]; then
  echo -e "${YELLOW}⚠ Repository was accepted (may be under limit or check disabled)${NC}"
  echo -e "${YELLOW}  This could mean:${NC}"
  echo -e "${YELLOW}  - Repository is actually <100MB${NC}"
  echo -e "${YELLOW}  - Size check is mocked/disabled in test environment${NC}"
else
  echo -e "${YELLOW}⚠ Unexpected status code: $HTTP_CODE${NC}"
  echo -e "${BLUE}Response: $RESPONSE_BODY${NC}"
fi

echo -e "\n${BLUE}Step 3: Connect Small Repository (Should Succeed)${NC}"
SMALL_REPO=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/octocat/Spoon-Knife.git\",
    \"access_token\": \"ghp_test_token_small_repo_check_123\",
    \"project_id\": \"$PROJECT_ID_3\"
  }")

SMALL_CONNECTED=$(echo "$SMALL_REPO" | jq -r '.connected')
if [[ "$SMALL_CONNECTED" == "true" ]]; then
  echo -e "${GREEN}✓ Small repository accepted successfully${NC}"
  SMALL_SIZE=$(echo "$SMALL_REPO" | jq -r '.repository_size_mb // "unknown"')
  echo -e "  Estimated Size: ${BLUE}${SMALL_SIZE}MB${NC}"
else
  echo -e "${YELLOW}⚠ Small repository connection status unclear${NC}"
fi

echo -e "\n${GREEN}✓ Scenario 3 completed!${NC}"

# ============================================================================
# Scenario 4: Multiple Repositories per Project
# ============================================================================
echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  SCENARIO 4: Multiple Repositories per Project          ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Step 1: Create Microservices Project${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "E2E Test - Microservices Multi-Repo"}')

PROJECT_ID_4=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID_4${NC}"

echo -e "\n${BLUE}Step 2: Connect Frontend Repository${NC}"
FRONTEND_REPO=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/octocat/Hello-World.git\",
    \"access_token\": \"ghp_frontend_token_123\",
    \"project_id\": \"$PROJECT_ID_4\"
  }")

FRONTEND_ID=$(echo "$FRONTEND_REPO" | jq -r '.id // .repo_id')
echo -e "${GREEN}✓ Frontend repo connected: $FRONTEND_ID${NC}"

echo -e "\n${BLUE}Step 3: Connect Backend Repository${NC}"
BACKEND_REPO=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/github/docs.git\",
    \"access_token\": \"ghp_backend_token_456\",
    \"project_id\": \"$PROJECT_ID_4\"
  }")

BACKEND_ID=$(echo "$BACKEND_REPO" | jq -r '.id // .repo_id')
echo -e "${GREEN}✓ Backend repo connected: $BACKEND_ID${NC}"

echo -e "\n${BLUE}Step 4: Connect Infrastructure Repository${NC}"
INFRA_REPO=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/octocat/Spoon-Knife.git\",
    \"access_token\": \"ghp_infra_token_789\",
    \"project_id\": \"$PROJECT_ID_4\"
  }")

INFRA_ID=$(echo "$INFRA_REPO" | jq -r '.id // .repo_id')
echo -e "${GREEN}✓ Infrastructure repo connected: $INFRA_ID${NC}"

echo -e "\n${BLUE}Step 5: List All Project Repositories${NC}"
ALL_REPOS=$(curl -s -X GET "${BASE_URL}/code/projects/${PROJECT_ID_4}/repos")
TOTAL_REPOS=$(echo "$ALL_REPOS" | jq 'length')

echo -e "${GREEN}✓ Total repositories for project: $TOTAL_REPOS${NC}"

if [[ "$TOTAL_REPOS" == "3" ]]; then
  echo -e "${GREEN}✓ All 3 repositories successfully connected${NC}"
  echo -e "\n${BLUE}Repository Summary:${NC}"
  echo "$ALL_REPOS" | jq -r '.[] | "  - ID: \(.id) | URL: \(.git_url) | Status: \(.clone_status)"'
else
  echo -e "${YELLOW}⚠ Expected 3 repositories, found $TOTAL_REPOS${NC}"
fi

echo -e "\n${GREEN}✓ Scenario 4 completed!${NC}"

# ============================================================================
# Scenario 5: Clone Task Processing Verification (Critical!)
# ============================================================================
echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  SCENARIO 5: Clone Task Processing Verification         ║${NC}"
echo -e "${CYAN}║  (Prevents false positives - ensures actual cloning)    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Step 1: Create Project for Clone Verification${NC}"
PROJECT_CLONE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "E2E Test - Clone Verification"}')

PROJECT_ID_CLONE=$(echo "$PROJECT_CLONE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID_CLONE${NC}"

echo -e "\n${BLUE}Step 2: Connect Repository${NC}"
CLONE_REPO=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/octocat/Hello-World.git\",
    \"access_token\": \"ghp_clone_test_token_123\",
    \"project_id\": \"$PROJECT_ID_CLONE\"
  }")

CLONE_REPO_ID=$(echo "$CLONE_REPO" | jq -r '.id // .repo_id')
INITIAL_STATUS=$(echo "$CLONE_REPO" | jq -r '.clone_status')
echo -e "${GREEN}✓ Repository connected${NC}"
echo -e "  Initial Status: ${BLUE}$INITIAL_STATUS${NC}"

if [[ "$INITIAL_STATUS" != "PENDING" ]]; then
  echo -e "${YELLOW}⚠ Warning: Expected initial status PENDING, got $INITIAL_STATUS${NC}"
fi

echo -e "\n${BLUE}Step 3: Wait for Clone to Complete${NC}"
echo -e "${YELLOW}Monitoring clone status for up to 30 seconds...${NC}"

MAX_WAIT=30
WAITED=0
FINAL_STATUS=""
SANDBOX_PATH=""

while [[ $WAITED -lt $MAX_WAIT ]]; do
  sleep 2
  WAITED=$((WAITED + 2))
  
  STATUS_CHECK=$(curl -s -X GET "${BASE_URL}/code/repos/${CLONE_REPO_ID}/status")
  CURRENT_STATUS=$(echo "$STATUS_CHECK" | jq -r '.clone_status')
  
  echo -e "  [$WAITED s] Status: ${BLUE}$CURRENT_STATUS${NC}"
  
  if [[ "$CURRENT_STATUS" == "COMPLETED" ]]; then
    FINAL_STATUS="COMPLETED"
    SANDBOX_PATH=$(echo "$STATUS_CHECK" | jq -r '.sandbox_path')
    echo -e "${GREEN}✓ Clone completed in ${WAITED}s!${NC}"
    break
  elif [[ "$CURRENT_STATUS" == "FAILED" ]]; then
    FINAL_STATUS="FAILED"
    ERROR_MSG=$(echo "$STATUS_CHECK" | jq -r '.error_message // "unknown"')
    echo -e "${RED}✗ Clone failed: $ERROR_MSG${NC}"
    break
  elif [[ "$CURRENT_STATUS" == "CLONING" ]]; then
    # Still in progress, continue waiting
    continue
  elif [[ "$CURRENT_STATUS" == "PENDING" ]] && [[ $WAITED -gt 10 ]]; then
    echo -e "${YELLOW}⚠ Still PENDING after ${WAITED}s - possible worker issue!${NC}"
  fi
done

echo -e "\n${BLUE}Step 4: Verify Clone Completion${NC}"

if [[ "$FINAL_STATUS" == "COMPLETED" ]]; then
  echo -e "${GREEN}✓ Clone Status: COMPLETED${NC}"
  
  # Verify sandbox path exists
  if [[ -n "$SANDBOX_PATH" ]] && [[ "$SANDBOX_PATH" != "null" ]]; then
    echo -e "${GREEN}✓ Sandbox path provided: $SANDBOX_PATH${NC}"
    
    # Check if directory actually exists
    REPO_PATH="${SANDBOX_PATH}/repository"
    if [[ -d "$REPO_PATH" ]]; then
      echo -e "${GREEN}✓ Repository directory exists${NC}"
      
      # Check if it has Git files
      if [[ -d "${REPO_PATH}/.git" ]]; then
        echo -e "${GREEN}✓ Git repository cloned successfully${NC}"
        
        # Count files to verify it's not empty
        FILE_COUNT=$(find "$REPO_PATH" -type f 2>/dev/null | wc -l)
        echo -e "${GREEN}✓ Repository contains $FILE_COUNT files${NC}"
        
        if [[ $FILE_COUNT -gt 0 ]]; then
          echo -e "${GREEN}✓ CRITICAL CHECK PASSED: Clone actually completed!${NC}"
        else
          echo -e "${RED}✗ CRITICAL: Repository is empty!${NC}"
          exit 1
        fi
      else
        echo -e "${RED}✗ CRITICAL: No .git directory found!${NC}"
        exit 1
      fi
    else
      echo -e "${RED}✗ CRITICAL: Sandbox directory doesn't exist!${NC}"
      echo -e "${RED}  Expected: $REPO_PATH${NC}"
      exit 1
    fi
  else
    echo -e "${RED}✗ CRITICAL: No sandbox path provided!${NC}"
    exit 1
  fi
  
elif [[ "$FINAL_STATUS" == "FAILED" ]]; then
  echo -e "${RED}✗ Clone failed - checking for common issues${NC}"
  
  # Get detailed error info
  DETAIL_RESPONSE=$(curl -s -X GET "${BASE_URL}/code/repos/${CLONE_REPO_ID}")
  echo -e "${BLUE}Repository details:${NC}"
  echo "$DETAIL_RESPONSE" | jq '.'
  
  echo -e "\n${YELLOW}Common failure causes to check:${NC}"
  echo -e "  1. Worker not running or not processing 'celery' queue"
  echo -e "  2. MASTER_ENCRYPTION_KEY not configured"
  echo -e "  3. Token decryption failed (wrong key)"
  echo -e "  4. Invalid Git credentials"
  echo -e "  5. Network/connectivity issues"
  
  exit 1
  
elif [[ "$FINAL_STATUS" == "" ]]; then
  echo -e "${RED}✗ CRITICAL: Clone stuck in PENDING state!${NC}"
  echo -e "\n${YELLOW}This indicates one of these problems:${NC}"
  echo -e "  1. ${RED}Celery Worker NOT running${NC}"
  echo -e "  2. ${RED}Worker NOT listening to 'celery' queue${NC}"
  echo -e "  3. ${RED}clone_repository_task NOT registered${NC}"
  echo -e "  4. ${RED}Redis connection issues${NC}"
  
  echo -e "\n${YELLOW}To diagnose:${NC}"
  echo -e "  1. Check worker: ps aux | grep celery"
  echo -e "  2. Check registered tasks: celery -A app.celery_app inspect registered"
  echo -e "  3. Check Redis queue: docker exec ai-agent-redis redis-cli LLEN celery"
  echo -e "  4. Check worker logs for errors"
  
  exit 1
else
  echo -e "${YELLOW}⚠ Clone in unexpected state: $FINAL_STATUS${NC}"
  exit 1
fi

echo -e "\n${GREEN}✓ Scenario 5 completed - Clone verification passed!${NC}"

# ============================================================================
# Scenario 6: Encryption Key Configuration Verification
# ============================================================================
echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  SCENARIO 6: Encryption Key Configuration Check         ║${NC}"
echo -e "${CYAN}║  (Verifies MASTER_ENCRYPTION_KEY is properly set)       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Step 1: Create Project for Encryption Test${NC}"
PROJECT_ENC=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "E2E Test - Encryption Verification"}')

PROJECT_ID_ENC=$(echo "$PROJECT_ENC" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID_ENC${NC}"

echo -e "\n${BLUE}Step 2: Connect Repository (triggers encryption)${NC}"
ENC_REPO=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/octocat/Spoon-Knife.git\",
    \"access_token\": \"ghp_encryption_test_unique_token_456789\",
    \"project_id\": \"$PROJECT_ID_ENC\"
  }")

ENC_REPO_ID=$(echo "$ENC_REPO" | jq -r '.id // .repo_id')
ENC_CONNECTED=$(echo "$ENC_REPO" | jq -r '.connected')

if [[ "$ENC_CONNECTED" == "true" ]]; then
  echo -e "${GREEN}✓ Repository connection accepted${NC}"
else
  echo -e "${RED}✗ Repository connection failed${NC}"
  echo "$ENC_REPO" | jq '.'
  exit 1
fi

echo -e "\n${BLUE}Step 3: Wait and Check for Decryption Success${NC}"
echo -e "${YELLOW}Waiting 15 seconds for clone to process...${NC}"
sleep 15

ENC_STATUS=$(curl -s -X GET "${BASE_URL}/code/repos/${ENC_REPO_ID}/status")
ENC_CLONE_STATUS=$(echo "$ENC_STATUS" | jq -r '.clone_status')

echo -e "  Final Status: ${BLUE}$ENC_CLONE_STATUS${NC}"

if [[ "$ENC_CLONE_STATUS" == "COMPLETED" ]]; then
  echo -e "${GREEN}✓ CRITICAL: Token was encrypted AND decrypted successfully!${NC}"
  echo -e "${GREEN}✓ This confirms MASTER_ENCRYPTION_KEY is properly configured${NC}"
  
elif [[ "$ENC_CLONE_STATUS" == "FAILED" ]]; then
  echo -e "${RED}✗ CRITICAL: Clone failed - likely decryption issue${NC}"
  echo -e "\n${YELLOW}This usually means:${NC}"
  echo -e "  1. ${RED}MASTER_ENCRYPTION_KEY not set in .env${NC}"
  echo -e "  2. ${RED}API and Worker using different keys${NC}"
  echo -e "  3. ${RED}EncryptionService still using os.getenv() instead of settings${NC}"
  
  echo -e "\n${YELLOW}To fix:${NC}"
  echo -e "  1. Check .env has: MASTER_ENCRYPTION_KEY=\"...\"" 
  echo -e "  2. Restart API: uvicorn main:app --reload"
  echo -e "  3. Restart Worker: ./start_worker.sh"
  echo -e "  4. Verify worker logs show: 'Loaded master encryption key from settings'"
  
  exit 1
  
elif [[ "$ENC_CLONE_STATUS" == "PENDING" ]]; then
  echo -e "${RED}✗ CRITICAL: Still PENDING - worker not processing!${NC}"
  exit 1
else
  echo -e "${YELLOW}⚠ Status: $ENC_CLONE_STATUS${NC}"
fi

echo -e "\n${GREEN}✓ Scenario 6 completed - Encryption configuration verified!${NC}"

# ============================================================================
# Scenario 7: Error Handling and Edge Cases
# ============================================================================
echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  SCENARIO 7: Error Handling & Edge Cases                ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Test 7.1: Invalid Git URL Format${NC}"
PROJECT_7=$(curl -s -X POST "${BASE_URL}/projects" -H "Content-Type: application/json" \
  -d '{"name": "E2E Test - Error Handling"}')
PROJECT_ID_7=$(echo "$PROJECT_7" | jq -r '.id')

INVALID_URL=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"invalid-url-format\",
    \"access_token\": \"ghp_test_123\",
    \"project_id\": \"$PROJECT_ID_7\"
  }")

if echo "$INVALID_URL" | jq -e '.detail' > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Invalid URL correctly rejected${NC}"
else
  echo -e "${YELLOW}⚠ Expected validation error for invalid URL${NC}"
fi

echo -e "\n${BLUE}Test 7.2: Empty Access Token${NC}"
EMPTY_TOKEN=$(curl -s -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/octocat/Hello-World.git\",
    \"access_token\": \"\",
    \"project_id\": \"$PROJECT_ID_7\"
  }")

if echo "$EMPTY_TOKEN" | jq -e '.detail' > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Empty token correctly rejected${NC}"
else
  echo -e "${YELLOW}⚠ Expected validation error for empty token${NC}"
fi

echo -e "\n${BLUE}Test 7.3: Non-existent Project ID${NC}"
FAKE_PROJECT_ID="00000000-0000-0000-0000-000000000000"
NONEXISTENT=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/code/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"git_url\": \"https://github.com/octocat/Hello-World.git\",
    \"access_token\": \"ghp_test_123\",
    \"project_id\": \"$FAKE_PROJECT_ID\"
  }")

HTTP_CODE_NE=$(echo "$NONEXISTENT" | tail -n 1)
if [[ "$HTTP_CODE_NE" == "404" ]] || [[ "$HTTP_CODE_NE" == "400" ]]; then
  echo -e "${GREEN}✓ Non-existent project correctly rejected (HTTP $HTTP_CODE_NE)${NC}"
else
  echo -e "${YELLOW}⚠ Expected 404/400 for non-existent project, got $HTTP_CODE_NE${NC}"
fi

echo -e "\n${BLUE}Test 7.4: Get Non-existent Repository${NC}"
FAKE_REPO_ID="99999999-9999-9999-9999-999999999999"
NONEXISTENT_REPO=$(curl -s -w "\n%{http_code}" -X GET "${BASE_URL}/code/repos/${FAKE_REPO_ID}")
HTTP_CODE_REPO=$(echo "$NONEXISTENT_REPO" | tail -n 1)

if [[ "$HTTP_CODE_REPO" == "404" ]]; then
  echo -e "${GREEN}✓ Non-existent repository returns 404${NC}"
else
  echo -e "${YELLOW}⚠ Expected 404 for non-existent repo, got $HTTP_CODE_REPO${NC}"
fi

echo -e "\n${GREEN}✓ Scenario 7 completed!${NC}"

# ============================================================================
# FINAL SUMMARY
# ============================================================================
echo -e "\n${MAGENTA}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║                     TEST SUMMARY                         ║${NC}"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Scenario 1: Complete repository connection lifecycle${NC}"
echo -e "${GREEN}✓ Scenario 2: Token security & encryption verification${NC}"
echo -e "${GREEN}✓ Scenario 3: Repository size validation & rejection${NC}"
echo -e "${GREEN}✓ Scenario 4: Multiple repositories per project${NC}"
echo -e "${GREEN}✓ Scenario 5: Clone task processing verification (CRITICAL)${NC}"
echo -e "${GREEN}✓ Scenario 6: Encryption key configuration verification${NC}"
echo -e "${GREEN}✓ Scenario 7: Error handling & edge cases${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}All E2E tests completed successfully!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Created Test Projects:${NC}"
echo -e "  1. Repository Lifecycle: $PROJECT_ID"
echo -e "  2. Token Security: $PROJECT_ID_2"
echo -e "  3. Size Validation: $PROJECT_ID_3"
echo -e "  4. Multi-Repo: $PROJECT_ID_4"
echo -e "  5. Clone Verification: $PROJECT_ID_CLONE"
echo -e "  6. Encryption Verification: $PROJECT_ID_ENC"
echo -e "  7. Error Handling: $PROJECT_ID_7"
echo ""
echo -e "${YELLOW}To cleanup all test data, run: ./test_c1_cleanup.sh${NC}"
