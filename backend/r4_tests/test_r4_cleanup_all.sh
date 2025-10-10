#!/bin/bash

# Test R4 Requirements Gateway - Full Database Cleanup
# WARNING: This deletes ALL projects from the database

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000/api/v1"

echo -e "${RED}${BOLD}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}${BOLD}║   ⚠️  WARNING: FULL DATABASE CLEANUP  ⚠️           ║${NC}"
echo -e "${RED}${BOLD}║   This will DELETE ALL projects!                  ║${NC}"
echo -e "${RED}${BOLD}╔════════════════════════════════════════════════════╗${NC}"
echo ""

# Get all projects
echo -e "${BLUE}Fetching all projects...${NC}"
PROJECTS_RESPONSE=$(curl -s -X GET "${BASE_URL}/projects")

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to fetch projects${NC}"
    exit 1
fi

TOTAL_COUNT=$(echo "$PROJECTS_RESPONSE" | jq 'length')

if [ "$TOTAL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ Database is already empty${NC}"
    exit 0
fi

echo -e "${YELLOW}Found $TOTAL_COUNT project(s) to delete:${NC}"
echo ""

# List all projects
echo "$PROJECTS_RESPONSE" | jq -r '.[] | "  • \(.name) (\(.status)) - ID: \(.id)"'

echo ""
echo -e "${RED}${BOLD}⚠️  This action cannot be undone! ⚠️${NC}"
echo ""
read -p "$(echo -e ${RED}${BOLD}Are you ABSOLUTELY sure you want to delete ALL $TOTAL_COUNT projects? \[yes/NO\]: ${NC})" -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Cleanup cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${RED}Proceeding with deletion...${NC}"
echo ""

DELETED_COUNT=0
FAILED_COUNT=0

# Delete each project
while IFS= read -r project; do
    PROJECT_ID=$(echo "$project" | jq -r '.id')
    PROJECT_NAME=$(echo "$project" | jq -r '.name')
    
    echo -ne "${YELLOW}Deleting: $PROJECT_NAME...${NC} "
    
    DELETE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${BASE_URL}/projects/${PROJECT_ID}")
    
    if [ "$DELETE_RESPONSE" -eq 200 ] || [ "$DELETE_RESPONSE" -eq 204 ]; then
        echo -e "${GREEN}✓${NC}"
        ((DELETED_COUNT++))
    else
        echo -e "${RED}✗ (HTTP $DELETE_RESPONSE)${NC}"
        ((FAILED_COUNT++))
    fi
done < <(echo "$PROJECTS_RESPONSE" | jq -c '.[]')

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Cleanup Summary${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Successfully deleted:${NC} $DELETED_COUNT project(s)"

if [ "$FAILED_COUNT" -gt 0 ]; then
    echo -e "${RED}Failed to delete:${NC} $FAILED_COUNT project(s)"
fi

echo -e "${CYAN}Total processed:${NC} $TOTAL_COUNT project(s)"
echo ""

# Verify cleanup
REMAINING=$(curl -s -X GET "${BASE_URL}/projects" | jq 'length')
if [ "$REMAINING" -eq 0 ]; then
    echo -e "${GREEN}✓ Database is now empty${NC}"
else
    echo -e "${YELLOW}⚠ Warning: $REMAINING project(s) still remain${NC}"
fi

echo ""
echo -e "${GREEN}Cleanup completed!${NC}"
