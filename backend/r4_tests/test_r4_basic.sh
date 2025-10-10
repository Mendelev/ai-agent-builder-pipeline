#!/bin/bash

# Test R4 Requirements Gateway - Basic Tests
# Tests all three gateway actions: finalizar, planejar, validar_codigo

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000/api/v1"

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   R4 Requirements Gateway - Basic Tests           ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo ""

# Test 1: Finalizar Action
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Test 1: Gateway Action - FINALIZAR${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

# Create project
echo -e "\n${BLUE}1.1. Creating project...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test R4 - Finalizar"}')

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID${NC}"

# Add requirement
echo -e "\n${BLUE}1.2. Adding requirement...${NC}"
curl -s -X POST "${BASE_URL}/projects/${PROJECT_ID}/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [{
      "code": "REQ-001",
      "descricao": "Sistema de autenticação",
      "criterios_aceitacao": ["Login funcional", "Logout funcional"],
      "prioridade": "must"
    }]
  }' > /dev/null
echo -e "${GREEN}✓ Requirement added${NC}"

# Set project to REQS_REFINING
echo -e "\n${BLUE}1.3. Setting project to REQS_REFINING state...${NC}"
curl -s -X PATCH "${BASE_URL}/projects/${PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{"status": "REQS_REFINING"}' > /dev/null
echo -e "${GREEN}✓ Project status updated${NC}"

# Execute gateway action: finalizar
echo -e "\n${BLUE}1.4. Executing gateway action: FINALIZAR...${NC}"
GATEWAY_RESPONSE=$(curl -s -X POST "${BASE_URL}/requirements/${PROJECT_ID}/gateway" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "finalizar"
  }')

echo -e "${GREEN}✓ Gateway action executed${NC}"
echo -e "${BLUE}Response:${NC}"
echo "$GATEWAY_RESPONSE" | jq '.'

# Verify state transition
FROM_STATE=$(echo "$GATEWAY_RESPONSE" | jq -r '.from')
TO_STATE=$(echo "$GATEWAY_RESPONSE" | jq -r '.to')

if [[ "$FROM_STATE" == "REQS_REFINING" && "$TO_STATE" == "REQS_READY" ]]; then
  echo -e "${GREEN}✓ State transition successful: $FROM_STATE → $TO_STATE${NC}"
else
  echo -e "${RED}✗ State transition failed: expected REQS_REFINING → REQS_READY, got $FROM_STATE → $TO_STATE${NC}"
  exit 1
fi

# Test 2: Planejar Action
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Test 2: Gateway Action - PLANEJAR${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

# Create new project
echo -e "\n${BLUE}2.1. Creating project...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test R4 - Planejar"}')

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID${NC}"

# Add requirement
echo -e "\n${BLUE}2.2. Adding requirement...${NC}"
curl -s -X POST "${BASE_URL}/projects/${PROJECT_ID}/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [{
      "code": "REQ-002",
      "descricao": "Dashboard de métricas",
      "criterios_aceitacao": ["Exibir gráficos", "Atualizar em tempo real"],
      "prioridade": "should"
    }]
  }' > /dev/null
echo -e "${GREEN}✓ Requirement added${NC}"

# Set project to REQS_REFINING
echo -e "\n${BLUE}2.3. Setting project to REQS_REFINING state...${NC}"
curl -s -X PATCH "${BASE_URL}/projects/${PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{"status": "REQS_REFINING"}' > /dev/null
echo -e "${GREEN}✓ Project status updated${NC}"

# Execute gateway action: planejar
echo -e "\n${BLUE}2.4. Executing gateway action: PLANEJAR...${NC}"
GATEWAY_RESPONSE=$(curl -s -X POST "${BASE_URL}/requirements/${PROJECT_ID}/gateway" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "planejar"
  }')

echo -e "${GREEN}✓ Gateway action executed${NC}"
echo -e "${BLUE}Response:${NC}"
echo "$GATEWAY_RESPONSE" | jq '.'

# Verify state transition
FROM_STATE=$(echo "$GATEWAY_RESPONSE" | jq -r '.from')
TO_STATE=$(echo "$GATEWAY_RESPONSE" | jq -r '.to')

if [[ "$FROM_STATE" == "REQS_REFINING" && "$TO_STATE" == "REQS_READY" ]]; then
  echo -e "${GREEN}✓ State transition successful: $FROM_STATE → $TO_STATE${NC}"
else
  echo -e "${RED}✗ State transition failed${NC}"
  exit 1
fi

# Test 3: Validar Codigo Action
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Test 3: Gateway Action - VALIDAR_CODIGO${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

# Create new project
echo -e "\n${BLUE}3.1. Creating project...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test R4 - Validar Código"}')

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID${NC}"

# Add requirement
echo -e "\n${BLUE}3.2. Adding requirement...${NC}"
curl -s -X POST "${BASE_URL}/projects/${PROJECT_ID}/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [{
      "code": "REQ-003",
      "descricao": "API REST completa",
      "criterios_aceitacao": ["Endpoints documentados", "Testes unitários"],
      "prioridade": "must"
    }]
  }' > /dev/null
echo -e "${GREEN}✓ Requirement added${NC}"

# Set project to REQS_REFINING
echo -e "\n${BLUE}3.3. Setting project to REQS_REFINING state...${NC}"
curl -s -X PATCH "${BASE_URL}/projects/${PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{"status": "REQS_REFINING"}' > /dev/null
echo -e "${GREEN}✓ Project status updated${NC}"

# Execute gateway action: validar_codigo
echo -e "\n${BLUE}3.4. Executing gateway action: VALIDAR_CODIGO...${NC}"
GATEWAY_RESPONSE=$(curl -s -X POST "${BASE_URL}/requirements/${PROJECT_ID}/gateway" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "validar_codigo"
  }')

echo -e "${GREEN}✓ Gateway action executed${NC}"
echo -e "${BLUE}Response:${NC}"
echo "$GATEWAY_RESPONSE" | jq '.'

# Verify state transition
FROM_STATE=$(echo "$GATEWAY_RESPONSE" | jq -r '.from')
TO_STATE=$(echo "$GATEWAY_RESPONSE" | jq -r '.to')

if [[ "$FROM_STATE" == "REQS_REFINING" && "$TO_STATE" == "CODE_VALIDATION_REQUESTED" ]]; then
  echo -e "${GREEN}✓ State transition successful: $FROM_STATE → $TO_STATE${NC}"
else
  echo -e "${RED}✗ State transition failed${NC}"
  exit 1
fi

# Test 4: Gateway History
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Test 4: Gateway History${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

echo -e "\n${BLUE}4.1. Getting gateway history...${NC}"
HISTORY_RESPONSE=$(curl -s -X GET "${BASE_URL}/requirements/${PROJECT_ID}/gateway/history")

echo -e "${GREEN}✓ History retrieved${NC}"
echo -e "${BLUE}History:${NC}"
echo "$HISTORY_RESPONSE" | jq '.'

HISTORY_COUNT=$(echo "$HISTORY_RESPONSE" | jq 'length')
echo -e "${GREEN}✓ Found $HISTORY_COUNT transition(s) in history${NC}"

# Test 5: Error Cases
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Test 5: Error Cases${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

# Test 5.1: Invalid state (DRAFT)
echo -e "\n${BLUE}5.1. Testing invalid state (DRAFT)...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test R4 - Invalid State"}')

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')

# Try gateway on DRAFT state (should fail)
ERROR_RESPONSE=$(curl -s -X POST "${BASE_URL}/requirements/${PROJECT_ID}/gateway" \
  -H "Content-Type: application/json" \
  -d '{"action": "finalizar"}')

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/requirements/${PROJECT_ID}/gateway" \
  -H "Content-Type: application/json" \
  -d '{"action": "finalizar"}')

if [[ "$STATUS_CODE" == "400" ]]; then
  echo -e "${GREEN}✓ Correctly rejected invalid state transition (HTTP 400)${NC}"
  echo -e "${BLUE}Error response:${NC}"
  echo "$ERROR_RESPONSE" | jq '.'
else
  echo -e "${RED}✗ Expected HTTP 400, got HTTP $STATUS_CODE${NC}"
fi

# Test 5.2: Project without requirements
echo -e "\n${BLUE}5.2. Testing project without requirements...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test R4 - No Requirements"}')

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')

# Set to REQS_REFINING but don't add requirements
curl -s -X PATCH "${BASE_URL}/projects/${PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{"status": "REQS_REFINING"}' > /dev/null

# Try gateway without requirements (should fail)
ERROR_RESPONSE=$(curl -s -X POST "${BASE_URL}/requirements/${PROJECT_ID}/gateway" \
  -H "Content-Type: application/json" \
  -d '{"action": "finalizar"}')

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/requirements/${PROJECT_ID}/gateway" \
  -H "Content-Type: application/json" \
  -d '{"action": "finalizar"}')

if [[ "$STATUS_CODE" == "400" ]]; then
  echo -e "${GREEN}✓ Correctly rejected project without requirements (HTTP 400)${NC}"
  echo -e "${BLUE}Error response:${NC}"
  echo "$ERROR_RESPONSE" | jq '.'
else
  echo -e "${RED}✗ Expected HTTP 400, got HTTP $STATUS_CODE${NC}"
fi

# Test 5.3: Invalid action
echo -e "\n${BLUE}5.3. Testing invalid action...${NC}"
ERROR_RESPONSE=$(curl -s -X POST "${BASE_URL}/requirements/${PROJECT_ID}/gateway" \
  -H "Content-Type: application/json" \
  -d '{"action": "invalid_action"}')

echo -e "${BLUE}Error response:${NC}"
echo "$ERROR_RESPONSE" | jq '.'

# Summary
echo -e "\n${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ALL TESTS COMPLETED ✓                 ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo ""
