# 🧪 Scripts de Teste R4 - Requirements Gateway

## ✅ Verificação da Implementação

A implementação do **R4 Requirements Gateway** está **100% completa** e conforme o design document:

### Componentes Implementados

| Componente | Status | Localização |
|------------|--------|-------------|
| API Endpoint | ✅ | `app/api/routes/gateway.py` |
| Service Layer | ✅ | `app/services/gateway_service.py` |
| Schemas | ✅ | `app/schemas/gateway.py` |
| Models | ✅ | `app/models/project.py` |
| Migration | ✅ | `alembic/versions/003_create_requirements_gateway_audit.py` |
| Unit Tests | ✅ | `tests/test_requirements_gateway.py` |
| E2E Tests | ✅ | `tests/test_requirements_gateway_e2e.py` |

### Funcionalidades

- ✅ POST `/requirements/{project_id}/gateway` - Transições de estado
- ✅ GET `/requirements/{project_id}/gateway/history` - Histórico de auditoria
- ✅ Três ações: `finalizar`, `planejar`, `validar_codigo`
- ✅ Validação de estados e guards
- ✅ Idempotência com `request_id`
- ✅ Rastreamento com `correlation_id`
- ✅ Audit trail completo

---

## 🚀 Scripts de Teste Criados

### 1. test_r4_basic.sh
**Testes rápidos das funcionalidades básicas**

```bash
cd backend
./test_r4_basic.sh
```

**O que testa:**
- ✅ Ação `finalizar` (REQS_REFINING → REQS_READY)
- ✅ Ação `planejar` (REQS_REFINING → REQS_READY)
- ✅ Ação `validar_codigo` (REQS_REFINING → CODE_VALIDATION_REQUESTED)
- ✅ Histórico de transições
- ✅ Casos de erro (estado inválido, sem requisitos, ação inválida)

**Duração:** ~10-15 segundos

---

### 2. test_r4_e2e.sh
**Workflow completo end-to-end com múltiplos cenários**

```bash
cd backend
./test_r4_e2e.sh
```

**O que testa:**
- ✅ Cenário 1: Workflow completo → Finalizar
- ✅ Cenário 2: Workflow completo → Planejar
- ✅ Cenário 3: Workflow completo → Validar Código
- ✅ Cenário 4: Idempotência com mesmo request_id
- ✅ Cenário 5: Consulta de histórico

**Duração:** ~20-30 segundos

---

### 3. test_r4_direct.py
**Testes automatizados em Python com validações detalhadas**

```bash
cd backend
python3 test_r4_direct.py
```

**O que testa:**
- ✅ Test 1: Gateway Transition - FINALIZAR
- ✅ Test 2: Gateway Transition - PLANEJAR
- ✅ Test 3: Gateway Transition - VALIDAR_CODIGO
- ✅ Test 4: Idempotência
- ✅ Test 5: Estado inválido
- ✅ Test 6: Projeto sem requisitos
- ✅ Test 7: Histórico de gateway
- ✅ Test 8: Rastreamento com correlation_id

**Duração:** ~15-20 segundos

---

## 📚 Documentação

### SWAGGER_R4_TEST_GUIDE.md
**Guia completo em português para testes via Swagger UI**

Localização: `backend/SWAGGER_R4_TEST_GUIDE.md`

**Conteúdo:**
- 📋 Visão geral do R4
- 🔄 Fluxo do processo
- 🔌 Documentação de endpoints
- 🧪 Cenários de teste passo-a-passo
- ❌ Tratamento de erros
- ✅ Checklist de validação
- 🚀 Scripts automatizados

---

## 🎯 Como Usar

### Pré-requisitos

1. Backend rodando:
```bash
cd backend
uvicorn main:app --reload
```

2. Banco de dados migrado:
```bash
cd backend
alembic upgrade head
```

### Opção 1: Teste Rápido (Automatizado)

```bash
# Teste básico (mais rápido)
./test_r4_basic.sh

# Ou teste completo (mais abrangente)
./test_r4_e2e.sh

# Ou teste em Python (com métricas)
python3 test_r4_direct.py
```

### Opção 2: Teste Manual via Swagger

1. Acesse: http://localhost:8000/docs
2. Siga o guia: `SWAGGER_R4_TEST_GUIDE.md`

### Opção 3: Teste via Curl

```bash
# 1. Criar projeto
PROJECT_ID=$(curl -s -X POST "http://localhost:8000/api/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Project"}' | jq -r '.id')

# 2. Adicionar requisito
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [{
      "code": "REQ-001",
      "descricao": "Test requirement",
      "criterios_aceitacao": ["Criterion 1", "Criterion 2"],
      "prioridade": "must"
    }]
  }'

# 3. Atualizar estado
curl -X PATCH "http://localhost:8000/api/v1/projects/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{"status": "REQS_REFINING"}'

# 4. Executar gateway
curl -X POST "http://localhost:8000/api/v1/requirements/$PROJECT_ID/gateway" \
  -H "Content-Type: application/json" \
  -d '{"action": "finalizar"}' | jq '.'

# 5. Ver histórico
curl -X GET "http://localhost:8000/api/v1/requirements/$PROJECT_ID/gateway/history" | jq '.'
```

---

## 🧹 Limpeza de Projetos de Teste

### Script 1: test_r4_cleanup.sh (Recomendado)
**Remove apenas projetos de teste** criados pelos scripts R4.

```bash
cd backend
./test_r4_cleanup.sh
```

**Características:**
- ✅ **Seguro**: Deleta apenas projetos com nomes de teste
- ✅ Preserva projetos reais/produção
- ✅ Mostra resumo detalhado
- ✅ Opção de ver projetos restantes

**Padrões identificados como teste:**
- "Test R4"
- "E-commerce Platform"
- "Mobile App MVP"
- "Legacy System Refactoring"
- "Idempotency Test Project"
- "Test E2E"
- "Teste R4"

**Exemplo de saída:**
```
╔════════════════════════════════════════════════════╗
║   R4 Requirements Gateway - Cleanup Script         ║
║   Remove all test projects from database          ║
╔════════════════════════════════════════════════════╗

Fetching all projects...
Found 8 total project(s)

Looking for test projects to delete...

Deleting test project:
  Name: Test R4 - Finalizar
  ID: 550e8400-e29b-41d4-a716-446655440000
  Status: REQS_READY
✓ Deleted successfully

═══════════════════════════════════════════════════
Cleanup Summary
═══════════════════════════════════════════════════
Deleted: 5 test project(s)
Skipped: 3 non-test project(s)
Total: 8 project(s) processed

✓ Cleanup completed successfully
```

---

### Script 2: test_r4_cleanup_all.sh (⚠️ Use com cuidado)
**Remove TODOS os projetos do banco de dados.**

```bash
cd backend
./test_r4_cleanup_all.sh
```

**⚠️ ATENÇÃO:**
- ❌ Deleta **TODOS** os projetos (teste + produção)
- ⚠️ Requer confirmação explícita (digite "yes")
- ⚠️ **Ação irreversível**

**Quando usar:**
- Reset completo do ambiente de desenvolvimento
- Limpar banco antes de nova bateria de testes
- Preparar ambiente limpo

**Exemplo de saída:**
```
╔════════════════════════════════════════════════════╗
║   ⚠️  WARNING: FULL DATABASE CLEANUP  ⚠️           ║
║   This will DELETE ALL projects!                  ║
╔════════════════════════════════════════════════════╗

Fetching all projects...
Found 8 project(s) to delete:

  • Test R4 - Finalizar (REQS_READY) - ID: abc-123
  • My Production App (DONE) - ID: def-456
  ...

⚠️  This action cannot be undone! ⚠️

Are you ABSOLUTELY sure you want to delete ALL 8 projects? [yes/NO]: yes

Proceeding with deletion...

Deleting: Test R4 - Finalizar... ✓
Deleting: My Production App... ✓
...

═══════════════════════════════════════════════════
Cleanup Summary
═══════════════════════════════════════════════════
Successfully deleted: 8 project(s)
Total processed: 8 project(s)

✓ Database is now empty
```

---

## 🔄 Workflow Completo de Testes

### 1. Executar testes
```bash
./test_r4_basic.sh      # Testes rápidos
# ou
./test_r4_e2e.sh        # Testes completos
# ou
python3 test_r4_direct.py  # Testes Python
```

### 2. Limpar projetos de teste
```bash
./test_r4_cleanup.sh    # Remove apenas projetos de teste
```

### 3. (Opcional) Reset completo
```bash
./test_r4_cleanup_all.sh  # Remove TODOS os projetos (cuidado!)
```

---

## 🔍 Validação da Implementação

### Checklist de Conformidade com Design Document

| Item | Status |
|------|--------|
| Endpoint POST /requirements/{id}/gateway | ✅ |
| Endpoint GET /requirements/{id}/gateway/history | ✅ |
| Três ações (finalizar, planejar, validar_codigo) | ✅ |
| Validação de estado (REQS_REFINING obrigatório) | ✅ |
| Validação de requisitos (mínimo 1) | ✅ |
| Transições corretas de estado | ✅ |
| Idempotência com request_id | ✅ |
| Correlation ID tracking | ✅ |
| Audit trail completo | ✅ |
| Tabela requirements_gateway_audit | ✅ |
| Indexes otimizados | ✅ |
| Tratamento de erros 400/404/422 | ✅ |
| Testes unitários | ✅ |
| Testes E2E | ✅ |

**Resultado:** ✅ **100% Implementado**

---

## 📊 Matriz de Transições

| Estado Inicial | Ação | Estado Final | Válido |
|---------------|------|--------------|--------|
| REQS_REFINING | finalizar | REQS_READY | ✅ |
| REQS_REFINING | planejar | REQS_READY | ✅ |
| REQS_REFINING | validar_codigo | CODE_VALIDATION_REQUESTED | ✅ |
| DRAFT | qualquer | - | ❌ HTTP 400 |
| REQS_READY | qualquer | - | ❌ HTTP 400 |

---

## 🎉 Exemplos de Saída dos Scripts

### test_r4_basic.sh
```
╔════════════════════════════════════════════════════╗
║   R4 Requirements Gateway - Basic Tests            ║
╔════════════════════════════════════════════════════╗

═══════════════════════════════════════════════════
Test 1: Gateway Action - FINALIZAR
═══════════════════════════════════════════════════

1.1. Creating project...
✓ Project created: 550e8400-e29b-41d4-a716-446655440000

1.2. Adding requirement...
✓ Requirement added

1.3. Setting project to REQS_REFINING state...
✓ Project status updated

1.4. Executing gateway action: FINALIZAR...
✓ Gateway action executed
Response:
{
  "from": "REQS_REFINING",
  "to": "REQS_READY",
  "reason": "User chose to finalize requirements"
}

✓ State transition successful: REQS_REFINING → REQS_READY
```

### test_r4_direct.py
```
════════════════════════════════════════════════════
     R4 REQUIREMENTS GATEWAY - AUTOMATED TESTS
════════════════════════════════════════════════════

▶ TEST 1: Gateway Transition - FINALIZAR
✓ Project created: Test R4 - Finalizar
✓ Added 1 requirement(s)
✓ Project status updated to: REQS_REFINING
✓ Gateway action executed
✓ HTTP status code: 200 == 200
✓ From state: REQS_REFINING == REQS_REFINING
✓ To state: REQS_READY == REQS_READY

════════════════════════════════════════════════════
TEST SUMMARY
════════════════════════════════════════════════════
Passed: 24
Failed: 0
Total:  24

🎉 ALL TESTS PASSED! 🎉
```

---

## 🐛 Troubleshooting

### Erro: "Connection refused"
**Solução:** Backend não está rodando. Execute:
```bash
cd backend
uvicorn main:app --reload
```

### Erro: "Project not found"
**Solução:** Use um `project_id` válido. Os scripts criam projetos automaticamente.

### Erro: "Invalid state transition"
**Solução:** Projeto deve estar em `REQS_REFINING`. Atualize o status:
```bash
curl -X PATCH "http://localhost:8000/api/v1/projects/$PROJECT_ID" \
  -d '{"status": "REQS_REFINING"}'
```

### Erro: "No requirements"
**Solução:** Adicione pelo menos um requisito ao projeto antes do gateway.

---

## 📞 Suporte

- **Documentação completa:** `SWAGGER_R4_TEST_GUIDE.md`
- **Design document:** `.qoder/quests/unnamed-task.md`
- **Código fonte:** `app/api/routes/gateway.py` e `app/services/gateway_service.py`

---

**Criado em:** 2024  
**Versão:** 1.0  
**Status:** ✅ Pronto para uso
