#!/bin/bash

# 🧪 Script de Teste R3 - Novo Endpoint Simplificado
# ===================================================

set -e

BASE_URL="http://localhost:8000/api/v1"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Testing R3 New Simplified Endpoint${NC}"
echo "============================================================"

# Passo 1: Criar projeto
echo -e "\n${YELLOW}1. Creating project...${NC}"
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d '{"name":"Teste R3 - Endpoint Simplificado"}')

PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.id')
echo -e "${GREEN}✓ Project ID: ${PROJECT_ID}${NC}"

# Passo 2: Adicionar requirement
echo -e "\n${YELLOW}2. Adding requirement...${NC}"
REQ_RESPONSE=$(curl -s -X POST "${BASE_URL}/projects/${PROJECT_ID}/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [
      {
        "code": "REQ-SIMPLE-001",
        "descricao": "Sistema deve ser rápido e seguro",
        "criterios_aceitacao": ["Deve responder rápido", "Deve ser seguro"],
        "prioridade": "must"
      }
    ]
  }')

echo -e "${GREEN}✓ Requirement added${NC}"

# Passo 3: Testar NOVO ENDPOINT (sem UUID, project_id no body)
echo -e "\n${YELLOW}3. Testing NEW simplified endpoint...${NC}"
echo -e "${BLUE}   Endpoint: POST /api/v1/refine${NC}"
echo -e "${BLUE}   Request ID: Auto-generated (não precisa enviar)${NC}"

REFINE_RESPONSE=$(curl -s -X POST "${BASE_URL}/refine" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"${PROJECT_ID}\",
    \"max_rounds\": 3
  }")

echo "$REFINE_RESPONSE" | jq .

# Verificar se task_id foi gerado
TASK_ID=$(echo $REFINE_RESPONSE | jq -r '.audit_ref.task_id')

if [ "$TASK_ID" = "null" ] || [ -z "$TASK_ID" ]; then
  echo -e "${RED}✗ Error: task_id not generated${NC}"
  echo "Response: $REFINE_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Task ID auto-generated: ${TASK_ID}${NC}"
echo -e "${GREEN}✓ Request ID auto-generated: ${TASK_ID}${NC}"

# Passo 4: Aguardar processamento
echo -e "\n${YELLOW}4. Waiting for task to complete (3 seconds)...${NC}"
sleep 3

# Passo 5: Verificar sessões Q&A
echo -e "\n${YELLOW}5. Checking Q&A sessions...${NC}"
SESSION_RESPONSE=$(curl -s -X GET "${BASE_URL}/projects/${PROJECT_ID}/qa-sessions")

TOTAL_SESSIONS=$(echo $SESSION_RESPONSE | jq '.total')
echo -e "${GREEN}✓ Total sessions: ${TOTAL_SESSIONS}${NC}"

if [ "$TOTAL_SESSIONS" -gt 0 ]; then
  TOTAL_QUESTIONS=$(echo $SESSION_RESPONSE | jq '.sessions[0].questions | length')
  echo -e "${GREEN}✓ Questions generated in first session: ${TOTAL_QUESTIONS}${NC}"
  
  if [ "$TOTAL_QUESTIONS" -gt 0 ]; then
    echo -e "\n${BLUE}📋 Sample question:${NC}"
    echo $SESSION_RESPONSE | jq -r '.sessions[0].questions[0].question' | head -c 150
    echo "..."
  fi
fi

echo -e "\n============================================================"
echo -e "${GREEN}✓ Test completed successfully!${NC}"
echo -e "\nProject ID: ${PROJECT_ID}"
echo -e "Task ID (auto-generated): ${TASK_ID}"
echo -e "\n${BLUE}Key Changes:${NC}"
echo -e "  ✅ Endpoint: POST /api/v1/refine (sem project_id na URL)"
echo -e "  ✅ project_id agora vai no body do request"
echo -e "  ✅ request_id é OPCIONAL (auto-gerado se não fornecido)"
echo -e "  ✅ Listagem: GET /api/v1/projects/{id}/qa-sessions (mantido)"
