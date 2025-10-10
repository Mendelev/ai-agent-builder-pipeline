# 🎯 R4 - Requirements Gateway Tests

Testes, scripts de limpeza e documentação do módulo R4 (Requirements Gateway).

## 📁 Arquivos Disponíveis

### Scripts de Teste

| Arquivo | Tipo | Descrição | Tempo |
|---------|------|-----------|-------|
| `test_r4_basic.sh` | Shell | Testes básicos de validação | ~30s |
| `test_r4_e2e.sh` | Shell | Testes end-to-end completos | ~1min |
| `test_r4_direct.py` | Python | Testes automatizados com assertions | ~45s |

### Scripts de Limpeza

| Arquivo | Descrição | Segurança |
|---------|-----------|-----------|
| `test_r4_cleanup.sh` | Remove APENAS projetos de teste | ✅ Seguro |
| `test_r4_cleanup_all.sh` | Remove TODOS os projetos | ⚠️ Requer confirmação |

### Documentação

| Arquivo | Conteúdo |
|---------|----------|
| `SWAGGER_R4_TEST_GUIDE.md` | Guia completo de testes via Swagger UI (15KB) |
| `TEST_R4_README.md` | Guia de início rápido |
| `CLEANUP_GUIDE.md` | Documentação dos scripts de limpeza |
| `CASCADE_DELETE_SAFETY.md` | Explicação sobre CASCADE DELETE |
| `DELETE_ENDPOINT_FIX.md` | Documentação do fix do endpoint DELETE |

## 🚀 Início Rápido

### 1️⃣ Testes Básicos (30 segundos)

```bash
./test_r4_basic.sh
```

**Testa:**
- ✅ Gateway "finalizar" (REQS_REFINING → REQS_READY)
- ✅ Gateway "planejar" (REQS_REFINING → REQS_READY)
- ✅ Gateway "validar_codigo" (REQS_REFINING → CODE_VALIDATION_REQUESTED)
- ✅ Histórico de transições
- ✅ Validações de erro

### 2️⃣ Testes End-to-End (1 minuto)

```bash
./test_r4_e2e.sh
```

**Cenários:**
1. ✅ Finalizar requisitos (happy path)
2. ✅ Planejar projeto
3. ✅ Validar código
4. ✅ Rejeitar estado inválido
5. ✅ Idempotência (request_id)

### 3️⃣ Testes Python Automatizados

```bash
python3 test_r4_direct.py
```

**8 casos de teste:**
- ✅ Transitions básicas
- ✅ Validações de estado
- ✅ Request ID (idempotência)
- ✅ Correlation ID
- ✅ Histórico
- ✅ Error handling

## 🧹 Limpeza de Projetos

### Opção 1: Limpar Apenas Projetos de Teste (Seguro)

```bash
./test_r4_cleanup.sh
```

Remove apenas projetos com nomes conhecidos:
- "Test R4 *"
- "E-commerce Platform"
- "Mobile Banking"
- "Sistema de Reservas"
- etc.

**Seguro:** Não afeta projetos reais.

### Opção 2: Limpar TODOS os Projetos (Cuidado!)

```bash
./test_r4_cleanup_all.sh
```

**⚠️ ATENÇÃO:**
- Remove TODOS os projetos do banco
- Requer confirmação manual
- Use apenas em ambiente de desenvolvimento

### Verificar Limpeza

```bash
# Listar projetos restantes
curl -s http://localhost:8000/api/v1/projects | jq '.[] | {id, name, status}'
```

## 🎯 O Que é o R4?

O **Requirements Gateway (R4)** é o módulo que controla transições de estado do projeto após o refinamento de requisitos.

### Ações Disponíveis

| Ação | Estado Inicial | Estado Final | Uso |
|------|----------------|--------------|-----|
| `finalizar` | REQS_REFINING | REQS_READY | Finalizar refinamento |
| `planejar` | REQS_REFINING | REQS_READY | Iniciar planejamento |
| `validar_codigo` | REQS_REFINING | CODE_VALIDATION_REQUESTED | Solicitar validação |

### Fluxo do R4

```
1. Criar Projeto
   ↓
2. Adicionar Requisitos
   ↓
3. Refinar Requisitos (R3)
   → Status: REQS_REFINING
   ↓
4. POST /requirements/{id}/gateway
   → Ação: finalizar/planejar/validar_codigo
   ↓
5. Status muda para:
   - REQS_READY (finalizar/planejar)
   - CODE_VALIDATION_REQUESTED (validar_codigo)
```

## 📊 Endpoints do R4

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/requirements/{id}/gateway` | POST | Executar transição de gateway |
| `/api/v1/requirements/{id}/gateway/history` | GET | Obter histórico de transições |

## 🧪 Exemplo de Teste Manual

```bash
# 1. Criar projeto
PROJECT_ID=$(curl -s -X POST "http://localhost:8000/api/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Gateway"}' | jq -r '.id')

# 2. Adicionar requisito
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [{
      "code": "REQ-001",
      "descricao": "Sistema deve processar pagamentos",
      "criterios_aceitacao": ["Processar em até 3 segundos"],
      "prioridade": "must"
    }]
  }'

# 3. Executar gateway "finalizar"
curl -X POST "http://localhost:8000/api/v1/requirements/$PROJECT_ID/gateway" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "finalizar",
    "request_id": "req-001",
    "observations": "Requisitos prontos para desenvolvimento"
  }' | jq '.'

# 4. Verificar histórico
curl -s "http://localhost:8000/api/v1/requirements/$PROJECT_ID/gateway/history" | jq '.'

# 5. Limpar
curl -X DELETE "http://localhost:8000/api/v1/projects/$PROJECT_ID"
```

## 📋 Pré-requisitos

- ✅ Backend rodando: `cd .. && uvicorn main:app --reload`
- ✅ Banco de dados migrado: `cd .. && alembic upgrade head`
- ✅ Python 3.8+ (para test_r4_direct.py)
- ✅ curl e jq (para scripts shell)

## 🔒 Segurança do CASCADE DELETE

Quando você deleta um projeto via DELETE endpoint:

```
DELETE /api/v1/projects/{id}
```

**O que acontece automaticamente:**

1. ✅ RequirementsGatewayAudit deletados (CASCADE)
2. ✅ Requirements deletados (CASCADE)
3. ✅ QASessions deletados (CASCADE)
4. ✅ Todas as relações limpas

**Por quê é seguro:**
- Configurado no SQLAlchemy: `ondelete="CASCADE"`
- Configurado no PostgreSQL: `ON DELETE CASCADE`
- Verificado em testes: `CASCADE_DELETE_SAFETY.md`

## 📚 Documentação Detalhada

| Arquivo | O Que Você Encontra |
|---------|---------------------|
| `SWAGGER_R4_TEST_GUIDE.md` | Tutorial passo-a-passo com Swagger UI |
| `TEST_R4_README.md` | Guia completo de todos os scripts |
| `CLEANUP_GUIDE.md` | Como usar scripts de limpeza |
| `CASCADE_DELETE_SAFETY.md` | Explicação técnica do CASCADE |
| `DELETE_ENDPOINT_FIX.md` | Fix do bug HTTP 405 |

## 🐛 Troubleshooting

### Erro: "Backend não está rodando"

```bash
cd ..
uvicorn main:app --reload
```

### Erro: "Project not in REQS_REFINING state"

```bash
# Projeto precisa estar em REQS_REFINING
# Certifique-se de que o projeto tem requisitos
curl -s "http://localhost:8000/api/v1/projects/$PROJECT_ID" | jq '.status'
```

### Erro: "jq: command not found"

```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq
```

## 🔗 Links Relacionados

- **R3 Tests:** `../r3_tests/` - Refinamento de requisitos (passo anterior)
- **API Routes:** `../app/api/routes/gateway.py`
- **Service:** `../app/services/gateway_service.py`
- **Models:** `../app/models/project.py`

## 📈 Estatísticas

- **Scripts de teste:** 3 arquivos (47KB total)
- **Scripts de limpeza:** 2 arquivos (7.7KB total)
- **Documentação:** 5 arquivos (60KB total)
- **Total:** 10 arquivos (124KB total)

---

**Versão:** 1.0  
**Última atualização:** Outubro 2024  
**Status:** ✅ Todos os testes passando
