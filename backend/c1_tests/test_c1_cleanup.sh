#!/bin/bash

# Test C1 Cleanup Script
# Safely removes test projects created by C1 test scripts

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost:8000/api/v1"

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   C1 Test Cleanup - Remove Test Projects          ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo ""

# Fetch all projects
echo -e "${YELLOW}Fetching all projects...${NC}"
PROJECTS=$(curl -s -X GET "${BASE_URL}/projects")

if [ -z "$PROJECTS" ] || [ "$PROJECTS" == "null" ]; then
  echo -e "${YELLOW}No projects found or API error.${NC}"
  exit 0
fi

# Define test project patterns
TEST_PATTERNS=(
  "Test C1"
  "E2E Test"
  "Test E2E"
)

# Find test projects
echo -e "\n${YELLOW}Identifying test projects...${NC}"
TEST_PROJECT_IDS=()

while IFS= read -r project; do
  if [ -n "$project" ] && [ "$project" != "null" ]; then
    PROJECT_ID=$(echo "$project" | jq -r '.id')
    PROJECT_NAME=$(echo "$project" | jq -r '.name')
    
    # Check if project name matches any test pattern
    for pattern in "${TEST_PATTERNS[@]}"; do
      if [[ "$PROJECT_NAME" == *"$pattern"* ]]; then
        TEST_PROJECT_IDS+=("$PROJECT_ID")
        echo -e "  ${CYAN}Found: $PROJECT_NAME ($PROJECT_ID)${NC}"
        break
      fi
    done
  fi
done < <(echo "$PROJECTS" | jq -c '.[]')

# Count test projects
TEST_COUNT=${#TEST_PROJECT_IDS[@]}

if [ $TEST_COUNT -eq 0 ]; then
  echo -e "\n${GREEN}No test projects found. Nothing to clean up!${NC}"
  exit 0
fi

echo -e "\n${YELLOW}Found $TEST_COUNT test project(s) to delete.${NC}"

# Confirm deletion
echo -e "\n${YELLOW}Do you want to delete these test projects? (y/N)${NC}"
read -r CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
  echo -e "${BLUE}Cleanup cancelled.${NC}"
  exit 0
fi

# Delete projects
echo -e "\n${YELLOW}Deleting test projects...${NC}"
DELETED_COUNT=0
FAILED_COUNT=0

for PROJECT_ID in "${TEST_PROJECT_IDS[@]}"; do
  # Get project name for logging (with error handling)
  PROJECT_INFO=$(curl -s -X GET "${BASE_URL}/projects/${PROJECT_ID}" 2>/dev/null || echo "{}")
  PROJECT_NAME=$(echo "$PROJECT_INFO" | jq -r '.name // "Unknown"' 2>/dev/null || echo "Unknown")
  
  # Delete project
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${BASE_URL}/projects/${PROJECT_ID}" 2>/dev/null || echo "000")
  
  if [ "$HTTP_CODE" == "204" ] || [ "$HTTP_CODE" == "200" ]; then
    echo -e "  ${GREEN}✓ Deleted: $PROJECT_NAME ($PROJECT_ID)${NC}"
    ((DELETED_COUNT++)) || true
  elif [ "$HTTP_CODE" == "404" ]; then
    echo -e "  ${YELLOW}⚠ Already deleted: $PROJECT_ID${NC}"
    ((DELETED_COUNT++)) || true
  else
    echo -e "  ${RED}✗ Failed to delete: $PROJECT_NAME ($PROJECT_ID) [HTTP $HTTP_CODE]${NC}"
    ((FAILED_COUNT++)) || true
  fi
done

# Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 CLEANUP SUMMARY                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Deleted: $DELETED_COUNT project(s)${NC}"
if [ $FAILED_COUNT -gt 0 ]; then
  echo -e "${RED}Failed: $FAILED_COUNT project(s)${NC}"
fi
echo ""

# Note about CASCADE delete
echo -e "${YELLOW}Note: CASCADE DELETE automatically removed:${NC}"
echo -e "  - All code repositories associated with deleted projects"
echo -e "  - All encrypted tokens"
echo -e "  - All sandbox workspace data"
echo ""

# Verify cleanup
echo -e "${YELLOW}Remaining test projects:${NC}"
REMAINING=$(curl -s -X GET "${BASE_URL}/projects")
REMAINING_TEST_COUNT=0

while IFS= read -r project; do
  if [ -n "$project" ] && [ "$project" != "null" ]; then
    PROJECT_NAME=$(echo "$project" | jq -r '.name')
    
    for pattern in "${TEST_PATTERNS[@]}"; do
      if [[ "$PROJECT_NAME" == *"$pattern"* ]]; then
        echo -e "  ${CYAN}- $PROJECT_NAME${NC}"
        ((REMAINING_TEST_COUNT++))
        break
      fi
    done
  fi
done < <(echo "$REMAINING" | jq -c '.[]')

if [ $REMAINING_TEST_COUNT -eq 0 ]; then
  echo -e "${GREEN}  None - All test projects cleaned up!${NC}"
else
  echo -e "${YELLOW}  $REMAINING_TEST_COUNT test project(s) still remain${NC}"
fi

echo ""
echo -e "${GREEN}Cleanup completed!${NC}"
