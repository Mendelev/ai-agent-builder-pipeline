#!/bin/bash

# 🧪 Script de Teste R3 - cURL (Formato Correto)
# ================================================

set -e

BASE_URL="http://localhost:8000/api/v1"

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔍 Testing R3 with cURL (Correct Format)"
echo "============================================================"

# Passo 1: Criar projeto
echo -e "\n${YELLOW}1. Creating project...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name":"Teste R3 - cURL Correto"}')

PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.id')
echo -e "${GREEN}✓ Project ID: ${PROJECT_ID}${NC}"

# Passo 2: Adicionar requirement
echo -e "\n${YELLOW}2. Adding requirement...${NC}"
REQ_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects/${PROJECT_ID}/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [
      {
        "code": "REQ-CURL-001",
        "descricao": "Sistema deve ser rápido",
        "criterios_aceitacao": ["Deve responder rápido"],
        "prioridade": "must"
      }
    ]
  }')

echo -e "${GREEN}✓ Requirement added${NC}"

# Passo 3: Gerar UUID válido para request_id
echo -e "\n${YELLOW}3. Generating valid UUID for request_id...${NC}"
REQUEST_UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
echo -e "${GREEN}✓ Request UUID: ${REQUEST_UUID}${NC}"

# Passo 4: Iniciar refinamento (FORMATO CORRETO)
echo -e "\n${YELLOW}4. Starting refinement with correct format...${NC}"
REFINE_RESPONSE=$(curl -s -X POST "${BASE_URL}/qa-sessions/refine" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"${PROJECT_ID}\",
    \"request_id\": \"${REQUEST_UUID}\"
  }")

SESSION_ID=$(echo $REFINE_RESPONSE | jq -r '.session_id')

if [ "$SESSION_ID" = "null" ]; then
  echo -e "${RED}✗ Error: ${REFINE_RESPONSE}${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Session ID: ${SESSION_ID}${NC}"
echo -e "${GREEN}✓ Request ID: ${REQUEST_UUID}${NC}"

# Passo 5: Aguardar processamento
echo -e "\n${YELLOW}5. Waiting for task to complete (3 seconds)...${NC}"
sleep 3

# Passo 6: Verificar sessão Q&A
echo -e "\n${YELLOW}6. Checking Q&A session...${NC}"
SESSION_RESPONSE=$(curl -s -X GET "${BASE_URL}/qa-sessions/${SESSION_ID}")

TOTAL_QUESTIONS=$(echo $SESSION_RESPONSE | jq '.questions | length')
echo -e "${GREEN}✓ Total questions generated: ${TOTAL_QUESTIONS}${NC}"

if [ "$TOTAL_QUESTIONS" -gt 0 ]; then
  echo -e "\n${GREEN}📋 Sample question:${NC}"
  echo $SESSION_RESPONSE | jq -r '.questions[0].question' | head -c 100
  echo "..."
fi

echo -e "\n============================================================"
echo -e "${GREEN}✓ Test completed successfully!${NC}"
echo -e "\nProject ID: ${PROJECT_ID}"
echo -e "Session ID: ${SESSION_ID}"
echo -e "Request ID: ${REQUEST_UUID}"
echo -e "\nView session: ${BASE_URL}/qa-sessions/${SESSION_ID}"

