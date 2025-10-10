#!/bin/bash

# Test R4 Requirements Gateway - Cleanup Script
# Removes all test projects created by R4 test scripts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000/api/v1"

echo -e "${MAGENTA}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║   R4 Requirements Gateway - Cleanup Script         ║${NC}"
echo -e "${MAGENTA}║   Remove all test projects from database          ║${NC}"
echo -e "${MAGENTA}╔════════════════════════════════════════════════════╗${NC}"
echo ""

# Get all projects
echo -e "${BLUE}Fetching all projects...${NC}"
PROJECTS_RESPONSE=$(curl -s -X GET "${BASE_URL}/projects")

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to fetch projects${NC}"
    exit 1
fi

# Count total projects
TOTAL_COUNT=$(echo "$PROJECTS_RESPONSE" | jq 'length')
echo -e "${CYAN}Found $TOTAL_COUNT total project(s)${NC}"

if [ "$TOTAL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ No projects to clean up${NC}"
    exit 0
fi

# Filter test projects (created by R4 test scripts)
TEST_PROJECT_PATTERNS=(
    "Test R4"
    "E-commerce Platform"
    "Mobile App MVP"
    "Legacy System Refactoring"
    "Idempotency Test Project"
    "Test E2E"
    "Test E-commerce"
    "Teste R4"
)

echo ""
echo -e "${YELLOW}Looking for test projects to delete...${NC}"
echo ""

DELETED_COUNT=0
SKIPPED_COUNT=0

# Process each project
while IFS= read -r project; do
    PROJECT_ID=$(echo "$project" | jq -r '.id')
    PROJECT_NAME=$(echo "$project" | jq -r '.name')
    PROJECT_STATUS=$(echo "$project" | jq -r '.status')
    
    # Check if project name matches any test pattern
    IS_TEST_PROJECT=false
    for pattern in "${TEST_PROJECT_PATTERNS[@]}"; do
        if [[ "$PROJECT_NAME" == *"$pattern"* ]]; then
            IS_TEST_PROJECT=true
            break
        fi
    done
    
    if [ "$IS_TEST_PROJECT" = true ]; then
        echo -e "${YELLOW}Deleting test project:${NC}"
        echo -e "  Name: ${CYAN}$PROJECT_NAME${NC}"
        echo -e "  ID: ${BLUE}$PROJECT_ID${NC}"
        echo -e "  Status: ${MAGENTA}$PROJECT_STATUS${NC}"
        
        # Delete the project
        DELETE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${BASE_URL}/projects/${PROJECT_ID}")
        
        if [ "$DELETE_RESPONSE" -eq 200 ] || [ "$DELETE_RESPONSE" -eq 204 ]; then
            echo -e "${GREEN}✓ Deleted successfully${NC}"
            ((DELETED_COUNT++))
        else
            echo -e "${RED}✗ Failed to delete (HTTP $DELETE_RESPONSE)${NC}"
        fi
        echo ""
    else
        ((SKIPPED_COUNT++))
    fi
done < <(echo "$PROJECTS_RESPONSE" | jq -c '.[]')

# Summary
echo -e "${MAGENTA}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Cleanup Summary${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Deleted:${NC} $DELETED_COUNT test project(s)"
echo -e "${BLUE}Skipped:${NC} $SKIPPED_COUNT non-test project(s)"
echo -e "${CYAN}Total:${NC} $TOTAL_COUNT project(s) processed"
echo ""

if [ "$DELETED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Cleanup completed successfully${NC}"
else
    echo -e "${YELLOW}ℹ No test projects found to delete${NC}"
fi

# Optional: Show remaining projects
echo ""
read -p "$(echo -e ${CYAN}Show remaining projects? \[y/N\]: ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Remaining projects:${NC}"
    REMAINING=$(curl -s -X GET "${BASE_URL}/projects")
    REMAINING_COUNT=$(echo "$REMAINING" | jq 'length')
    
    if [ "$REMAINING_COUNT" -eq 0 ]; then
        echo -e "${CYAN}  (no projects)${NC}"
    else
        echo "$REMAINING" | jq -r '.[] | "  - \(.name) (\(.status))"'
    fi
    echo ""
fi

echo -e "${GREEN}Done!${NC}"
