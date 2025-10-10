#!/bin/bash

# Test R4 Requirements Gateway - End-to-End Workflow
# Complete workflow: Create project → Add requirements → Refine → Gateway transition

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

BASE_URL="http://localhost:8000/api/v1"

echo -e "${MAGENTA}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║   R4 Requirements Gateway - E2E Workflow Test      ║${NC}"
echo -e "${MAGENTA}║   Complete workflow from creation to transition    ║${NC}"
echo -e "${MAGENTA}╔════════════════════════════════════════════════════╗${NC}"
echo ""

# ============================================================================
# SCENARIO 1: Complete Workflow with Finalizar
# ============================================================================
echo -e "${YELLOW}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  SCENARIO 1: Complete Workflow → Finalizar         ║${NC}"
echo -e "${YELLOW}╔════════════════════════════════════════════════════╗${NC}"

# Step 1: Create Project
echo -e "\n${BLUE}Step 1: Creating project...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E-commerce Platform"
  }')

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
STATUS=$(echo "$PROJECT_RESPONSE" | jq -r '.status')

echo -e "${GREEN}✓ Project created${NC}"
echo -e "  ID: ${BLUE}$PROJECT_ID${NC}"
echo -e "  Status: ${BLUE}$STATUS${NC}"

# Step 2: Add Requirements
echo -e "\n${BLUE}Step 2: Adding initial requirements...${NC}"
REQ_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects/${PROJECT_ID}/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [
      {
        "code": "REQ-AUTH-001",
        "descricao": "Sistema de autenticação de usuários",
        "criterios_aceitacao": [
          "Usuário pode fazer login com email e senha",
          "Sistema valida credenciais no banco de dados",
          "Token JWT é gerado após login bem-sucedido"
        ],
        "prioridade": "must",
        "dependencias": []
      },
      {
        "code": "REQ-CART-001",
        "descricao": "Carrinho de compras funcional",
        "criterios_aceitacao": [
          "Usuário pode adicionar produtos ao carrinho",
          "Usuário pode remover produtos do carrinho",
          "Carrinho persiste entre sessões"
        ],
        "prioridade": "must",
        "dependencias": ["REQ-AUTH-001"]
      },
      {
        "code": "REQ-PAY-001",
        "descricao": "Integração com gateway de pagamento",
        "criterios_aceitacao": [
          "Aceita cartões de crédito e débito",
          "Processa pagamentos via PIX"
        ],
        "prioridade": "should",
        "dependencias": ["REQ-CART-001"]
      }
    ]
  }')

REQ_COUNT=$(echo "$REQ_RESPONSE" | jq 'length')
echo -e "${GREEN}✓ Added $REQ_COUNT requirements${NC}"

# Step 3: Update to REQS_REFINING
echo -e "\n${BLUE}Step 3: Moving to requirements refinement phase...${NC}"
UPDATE_RESPONSE=$(curl -s -X PATCH "${BASE_URL}/projects/${PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{"status": "REQS_REFINING"}')

NEW_STATUS=$(echo "$UPDATE_RESPONSE" | jq -r '.status')
echo -e "${GREEN}✓ Project status updated to: $NEW_STATUS${NC}"

# Step 4: Simulate refinement process (optional - would use R3 here)
echo -e "\n${BLUE}Step 4: [Simulating refinement process...]${NC}"
echo -e "  ${MAGENTA}ℹ In real workflow, R3 would refine requirements here${NC}"
sleep 1
echo -e "${GREEN}✓ Refinement completed${NC}"

# Step 5: Execute Gateway - Finalizar
echo -e "\n${BLUE}Step 5: Executing gateway transition (FINALIZAR)...${NC}"
GATEWAY_RESPONSE=$(curl -s -X POST "${BASE_URL}/requirements/${PROJECT_ID}/gateway" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "finalizar",
    "correlation_id": "'"$(uuidgen)"'",
    "request_id": "'"$(uuidgen)"'"
  }')

echo -e "${GREEN}✓ Gateway transition executed${NC}"
echo ""
echo -e "${MAGENTA}Gateway Response:${NC}"
echo "$GATEWAY_RESPONSE" | jq '{
  from: .from,
  to: .to,
  reason: .reason,
  audit: {
    correlation_id: .audit_ref.correlation_id,
    action: .audit_ref.action,
    timestamp: .audit_ref.timestamp
  }
}'

# Step 6: Verify final state
echo -e "\n${BLUE}Step 6: Verifying final project state...${NC}"
FINAL_STATE=$(curl -s -X GET "${BASE_URL}/projects/${PROJECT_ID}" | jq -r '.status')
echo -e "${GREEN}✓ Final project status: $FINAL_STATE${NC}"

if [[ "$FINAL_STATE" == "REQS_READY" ]]; then
  echo -e "${GREEN}✓✓✓ SCENARIO 1 PASSED ✓✓✓${NC}"
else
  echo -e "${RED}✗✗✗ SCENARIO 1 FAILED ✗✗✗${NC}"
  exit 1
fi

# ============================================================================
# SCENARIO 2: Workflow with Planejar
# ============================================================================
echo -e "\n\n${YELLOW}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  SCENARIO 2: Complete Workflow → Planejar          ║${NC}"
echo -e "${YELLOW}╔════════════════════════════════════════════════════╗${NC}"

# Create second project
echo -e "\n${BLUE}Creating new project for planning workflow...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Mobile App MVP"}')

PROJECT_ID_2=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID_2${NC}"

# Add requirements
curl -s -X POST "${BASE_URL}/projects/${PROJECT_ID_2}/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [
      {
        "code": "REQ-UI-001",
        "descricao": "Interface responsiva para mobile",
        "criterios_aceitacao": [
          "Funciona em iOS e Android",
          "Adapta-se a diferentes tamanhos de tela"
        ],
        "prioridade": "must",
        "dependencias": []
      }
    ]
  }' > /dev/null

# Set to REQS_REFINING
curl -s -X PATCH "${BASE_URL}/projects/${PROJECT_ID_2}" \
  -H "Content-Type: application/json" \
  -d '{"status": "REQS_REFINING"}' > /dev/null

echo -e "${GREEN}✓ Requirements added and project set to REQS_REFINING${NC}"

# Execute Gateway - Planejar
echo -e "\n${BLUE}Executing gateway transition (PLANEJAR)...${NC}"
GATEWAY_RESPONSE=$(curl -s -X POST "${BASE_URL}/requirements/${PROJECT_ID_2}/gateway" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "planejar"
  }')

echo -e "${GREEN}✓ Gateway transition executed${NC}"
echo ""
echo -e "${MAGENTA}Gateway Response:${NC}"
echo "$GATEWAY_RESPONSE" | jq '{from: .from, to: .to, reason: .reason}'

FINAL_STATE=$(curl -s -X GET "${BASE_URL}/projects/${PROJECT_ID_2}" | jq -r '.status')
if [[ "$FINAL_STATE" == "REQS_READY" ]]; then
  echo -e "${GREEN}✓✓✓ SCENARIO 2 PASSED ✓✓✓${NC}"
else
  echo -e "${RED}✗✗✗ SCENARIO 2 FAILED ✗✗✗${NC}"
  exit 1
fi

# ============================================================================
# SCENARIO 3: Workflow with Validar Codigo
# ============================================================================
echo -e "\n\n${YELLOW}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  SCENARIO 3: Complete Workflow → Validar Código    ║${NC}"
echo -e "${YELLOW}╔════════════════════════════════════════════════════╗${NC}"

# Create third project
echo -e "\n${BLUE}Creating project for code validation workflow...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Legacy System Refactoring"}')

PROJECT_ID_3=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID_3${NC}"

# Add requirements
curl -s -X POST "${BASE_URL}/projects/${PROJECT_ID_3}/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [
      {
        "code": "REQ-REFACTOR-001",
        "descricao": "Refatorar módulo de relatórios",
        "criterios_aceitacao": [
          "Código segue padrões de clean code",
          "Cobertura de testes >= 80%",
          "Performance melhorada em 50%"
        ],
        "prioridade": "must",
        "dependencias": []
      }
    ]
  }' > /dev/null

# Set to REQS_REFINING
curl -s -X PATCH "${BASE_URL}/projects/${PROJECT_ID_3}" \
  -H "Content-Type: application/json" \
  -d '{"status": "REQS_REFINING"}' > /dev/null

echo -e "${GREEN}✓ Requirements added and project set to REQS_REFINING${NC}"

# Execute Gateway - Validar Codigo
echo -e "\n${BLUE}Executing gateway transition (VALIDAR_CODIGO)...${NC}"
GATEWAY_RESPONSE=$(curl -s -X POST "${BASE_URL}/requirements/${PROJECT_ID_3}/gateway" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "validar_codigo"
  }')

echo -e "${GREEN}✓ Gateway transition executed${NC}"
echo ""
echo -e "${MAGENTA}Gateway Response:${NC}"
echo "$GATEWAY_RESPONSE" | jq '{from: .from, to: .to, reason: .reason}'

FINAL_STATE=$(curl -s -X GET "${BASE_URL}/projects/${PROJECT_ID_3}" | jq -r '.status')
if [[ "$FINAL_STATE" == "CODE_VALIDATION_REQUESTED" ]]; then
  echo -e "${GREEN}✓✓✓ SCENARIO 3 PASSED ✓✓✓${NC}"
else
  echo -e "${RED}✗✗✗ SCENARIO 3 FAILED ✗✗✗${NC}"
  exit 1
fi

# ============================================================================
# SCENARIO 4: Idempotency Test
# ============================================================================
echo -e "\n\n${YELLOW}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  SCENARIO 4: Idempotency Test                      ║${NC}"
echo -e "${YELLOW}╔════════════════════════════════════════════════════╗${NC}"

# Create project
echo -e "\n${BLUE}Creating project for idempotency test...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Idempotency Test Project"}')

PROJECT_ID_4=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Project created: $PROJECT_ID_4${NC}"

# Add requirement and set state
curl -s -X POST "${BASE_URL}/projects/${PROJECT_ID_4}/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [{
      "code": "REQ-TEST-001",
      "descricao": "Test requirement",
      "criterios_aceitacao": ["Test criterion"],
      "prioridade": "must"
    }]
  }' > /dev/null

curl -s -X PATCH "${BASE_URL}/projects/${PROJECT_ID_4}" \
  -H "Content-Type: application/json" \
  -d '{"status": "REQS_REFINING"}' > /dev/null

# First request with specific request_id
REQUEST_ID=$(uuidgen)
echo -e "\n${BLUE}First request with request_id: $REQUEST_ID${NC}"
RESPONSE_1=$(curl -s -X POST "${BASE_URL}/requirements/${PROJECT_ID_4}/gateway" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "finalizar",
    "request_id": "'"$REQUEST_ID"'"
  }')

AUDIT_ID_1=$(echo "$RESPONSE_1" | jq -r '.audit_ref.correlation_id')
echo -e "${GREEN}✓ First request completed - Audit ID: $AUDIT_ID_1${NC}"

# Second request with SAME request_id (should be idempotent)
echo -e "\n${BLUE}Second request with SAME request_id: $REQUEST_ID${NC}"
RESPONSE_2=$(curl -s -X POST "${BASE_URL}/requirements/${PROJECT_ID_4}/gateway" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "finalizar",
    "request_id": "'"$REQUEST_ID"'"
  }')

AUDIT_ID_2=$(echo "$RESPONSE_2" | jq -r '.audit_ref.correlation_id')
echo -e "${GREEN}✓ Second request completed - Audit ID: $AUDIT_ID_2${NC}"

# Verify idempotency
if [[ "$AUDIT_ID_1" == "$AUDIT_ID_2" ]]; then
  echo -e "${GREEN}✓✓✓ SCENARIO 4 PASSED - Idempotency verified ✓✓✓${NC}"
else
  echo -e "${RED}✗✗✗ SCENARIO 4 FAILED - Different audit IDs ✗✗✗${NC}"
  exit 1
fi

# ============================================================================
# SCENARIO 5: Gateway History
# ============================================================================
echo -e "\n\n${YELLOW}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  SCENARIO 5: Gateway History                       ║${NC}"
echo -e "${YELLOW}╔════════════════════════════════════════════════════╗${NC}"

# Get history for first project (should have 1 transition)
echo -e "\n${BLUE}Getting gateway history for project 1...${NC}"
HISTORY=$(curl -s -X GET "${BASE_URL}/requirements/${PROJECT_ID}/gateway/history")

HISTORY_COUNT=$(echo "$HISTORY" | jq 'length')
echo -e "${GREEN}✓ History retrieved: $HISTORY_COUNT transition(s)${NC}"

echo -e "\n${MAGENTA}History Details:${NC}"
echo "$HISTORY" | jq '.[] | {
  action: .action,
  from_state: .from_state,
  to_state: .to_state,
  created_at: .created_at
}'

if [[ "$HISTORY_COUNT" -ge 1 ]]; then
  echo -e "${GREEN}✓✓✓ SCENARIO 5 PASSED ✓✓✓${NC}"
else
  echo -e "${RED}✗✗✗ SCENARIO 5 FAILED ✗✗✗${NC}"
  exit 1
fi

# ============================================================================
# FINAL SUMMARY
# ============================================================================
echo -e "\n\n${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                    ║${NC}"
echo -e "${GREEN}║       🎉 ALL E2E SCENARIOS PASSED! 🎉             ║${NC}"
echo -e "${GREEN}║                                                    ║${NC}"
echo -e "${GREEN}║  ✓ Scenario 1: Finalizar workflow                 ║${NC}"
echo -e "${GREEN}║  ✓ Scenario 2: Planejar workflow                  ║${NC}"
echo -e "${GREEN}║  ✓ Scenario 3: Validar Código workflow            ║${NC}"
echo -e "${GREEN}║  ✓ Scenario 4: Idempotency                        ║${NC}"
echo -e "${GREEN}║  ✓ Scenario 5: Gateway History                    ║${NC}"
echo -e "${GREEN}║                                                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
