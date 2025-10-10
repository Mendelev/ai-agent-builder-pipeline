# 🔄 Guia de Testes - Módulo R3 (Requirement Refinement)

**Acesso**: http://localhost:8000/docs  
**Data**: 8 de outubro de 2025  
**Módulo**: R3 - Refinamento de Requisitos via Q&A Automatizado

---

## 📋 Índice

1. [Visão Geral do R3](#visão-geral-do-r3)
2. [Pré-requisitos](#pré-requisitos)
3. [Endpoints do R3](#endpoints-do-r3)
4. [Fluxo Completo de Refinamento](#fluxo-completo-de-refinamento)
5. [Testes de Q&A Sessions](#testes-de-qa-sessions)
6. [Testes de Idempotência](#testes-de-idempotência)
7. [Testes de Rounds Múltiplos](#testes-de-rounds-múltiplos)
8. [Testes de Heurísticos](#testes-de-heurísticos)
9. [Cenários de Erro](#cenários-de-erro)
10. [Monitoramento Celery](#monitoramento-celery)

---

## 🎯 Visão Geral do R3

O módulo R3 (Requirement Refinement) implementa um sistema de refinamento iterativo de requisitos através de:

- **Análise Heurística**: 5 categorias de análise automática
- **Geração de Perguntas**: Perguntas contextuais baseadas em gaps detectados
- **Q&A Iterativo**: Múltiplos rounds de perguntas e respostas
- **Processamento Assíncrono**: Celery + Redis para tasks em background
- **Idempotência**: Request ID para evitar processamento duplicado
- **Versionamento**: Atualização de requirements após cada round

### 🔍 Heurísticos Implementados:

1. **Testability** - Detecta requisitos subjetivos/não testáveis
2. **Ambiguity** - Identifica linguagem vaga
3. **Dependencies** - Encontra referências a sistemas externos
4. **Acceptance Criteria** - Valida completude dos critérios
5. **Constraints** - Detecta restrições não formalizadas

---

## ⚙️ Pré-requisitos

### 1. **Iniciar Infraestrutura**

```bash
# Terminal 1 - Redis e PostgreSQL
cd backend
docker-compose up -d

# Verificar
docker ps
# Deve mostrar: postgres e redis rodando
```

### 2. **Iniciar Worker Celery**

```bash
# Terminal 2 - Worker
cd backend
source venv/bin/activate
./start_worker.sh

# ✅ Você deve ver:
# [2025-10-08 20:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
# [2025-10-08 20:00:00,000: INFO/MainProcess] Ready to accept tasks!
```

### 3. **Iniciar API FastAPI**

```bash
# Terminal 3 - API
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# ✅ Você deve ver:
# INFO:     Application startup complete.
```

### 4. **Acessar Swagger**

Abra: **http://localhost:8000/docs**

---

### 5. **⚠️ IMPORTANTE: Formato de Dados**

#### **Request ID deve ser UUID válido**:

❌ **ERRADO** (string arbitrária):
```json
{
  "request_id": "req-001-round-1"
}
```

✅ **CORRETO** (UUID v4):
```json
{
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Como gerar UUIDs**:
- **Online**: https://www.uuidgenerator.net/
- **Terminal Linux/Mac**: `uuidgen`
- **Terminal (lowercase)**: `uuidgen | tr '[:upper:]' '[:lower:]'`
- **Python**: `python3 -c "import uuid; print(uuid.uuid4())"`
- **Node.js**: `node -e "console.log(require('crypto').randomUUID())"`

#### **Confidence Score** (quando houver campo `answers`):

❌ **ERRADO** (< 1):
```json
{
  "confidence": 0
}
```

✅ **CORRETO** (1-10):
```json
{
  "confidence": 8
}
```

**Escala**: 1 (baixa confiança) a 10 (alta confiança)

---

## 📡 Endpoints do R3

| Método | Endpoint | Descrição | Tag |
|--------|----------|-----------|-----|
| POST | `/api/v1/projects/{project_id}/refine` | Iniciar refinamento assíncrono | qa_sessions |
| GET | `/api/v1/projects/{project_id}/qa-sessions` | Listar sessões Q&A do projeto | qa_sessions |
| GET | `/api/v1/projects/{project_id}/qa-sessions/{session_id}` | Obter sessão específica | qa_sessions |

---

## 🚀 Fluxo Completo de Refinamento

### **Cenário**: Refinar requisito de login com múltiplos rounds

---

#### **Passo 1**: Criar Projeto

**Endpoint**: `POST /api/v1/projects`

```json
{
  "name": "Sistema de Autenticação Empresarial"
}
```

**Resposta**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Sistema de Autenticação Empresarial",
  "status": "DRAFT",
  "requirements_version": 0,
  ...
}
```

**💡 Salve**: `project_id = 550e8400-e29b-41d4-a716-446655440000`

---

#### **Passo 2**: Adicionar Requirement Inicial (Proposital com Gaps)

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

```json
{
  "requirements": [
    {
      "code": "REQ-AUTH-001",
      "descricao": "O sistema deve permitir que usuários façam login de forma segura",
      "criterios_aceitacao": [
        "Usuário consegue fazer login",
        "Sistema valida credenciais"
      ],
      "prioridade": "must",
      "dependencias": []
    }
  ]
}
```

**📝 Nota**: Este requirement tem **gaps propositais**:
- ❌ Descrição vaga: "forma segura" não especifica como
- ❌ Critérios genéricos: não especifica métricas
- ❌ Falta testabilidade
- ❌ Não menciona dependências externas (banco de dados)
- ❌ Não especifica constraints (timeout, tentativas)

**Resposta**:
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "code": "REQ-AUTH-001",
    "version": 1,
    ...
  }
]
```

---

#### **Passo 3**: Iniciar Refinamento (Round 1)

**Endpoint**: `POST /api/v1/projects/{project_id}/refine`

**Tag**: `qa_sessions`

**⚠️ IMPORTANTE**: `request_id` deve ser um **UUID válido** (não uma string arbitrária)

```json
{
  "max_rounds": 5,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "answers": []
}
```

**� Campos**:
- `max_rounds`: Número máximo de rounds de refinamento (default: 5)
- `request_id`: UUID único para idempotência (obrigatório)
- `answers`: Array de respostas (vazio no primeiro round)

**�💡 Dica**: Gere UUIDs únicos para cada request:
- Online: https://www.uuidgenerator.net/
- Linux/Mac: `uuidgen` no terminal
- Python: `import uuid; str(uuid.uuid4())`

**Resposta**: `202 Accepted`
```json
{
  "status": "REQS_REFINING",
  "open_questions": null,
  "refined_requirements_version": null,
  "audit_ref": {
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "enqueued_at": "UTC_NOW",
    "state": "PENDING"
  },
  "current_round": 1,
  "max_rounds": 5,
  "quality_flags": null
}
```

**📋 O que acontece nos bastidores**:
1. ✅ Projeto muda para status `REQS_REFINING`
2. ✅ Task Celery é enfileirada na queue `q_analyst` com `task_id = request_id`
3. ✅ Worker processa assincronamente
4. ✅ Heurísticos analisam o requirement
5. ✅ Sessão Q&A é criada com perguntas geradas

**⏱️ Aguarde**: 2-5 segundos para processamento

---

#### **Passo 4**: Verificar Sessão Q&A Criada

**Endpoint**: `GET /api/v1/projects/{project_id}/qa-sessions`

**Path Parameter**: Use o `project_id` do Passo 1

**Resposta**: `200 OK`
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "sessions": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "round": 1,
      "questions": [
        {
          "id": "q1",
          "heuristic": "testability",
          "question": "What specific security mechanisms should be implemented for 'forma segura' in requirement 'REQ-AUTH-001'? (e.g., encryption algorithm, password hashing method)",
          "context": {
            "requirement_code": "REQ-AUTH-001",
            "detected_issue": "Vague term 'segura' without measurable criteria"
          }
        },
        {
          "id": "q2",
          "heuristic": "acceptance_criteria",
          "question": "What are the specific acceptance criteria for requirement 'REQ-AUTH-001'? Please provide measurable conditions.",
          "context": {
            "requirement_code": "REQ-AUTH-001",
            "detected_issue": "Generic criteria without metrics"
          }
        },
        {
          "id": "q3",
          "heuristic": "dependencies",
          "question": "Which external systems does requirement 'REQ-AUTH-001' depend on? (e.g., database, LDAP, OAuth provider)",
          "context": {
            "requirement_code": "REQ-AUTH-001",
            "detected_issue": "No external dependencies specified"
          }
        },
        {
          "id": "q4",
          "heuristic": "constraints",
          "question": "What are the performance and error handling constraints for requirement 'REQ-AUTH-001'? (e.g., timeout, max login attempts, lockout policy)",
          "context": {
            "requirement_code": "REQ-AUTH-001",
            "detected_issue": "No constraints formalized"
          }
        }
      ],
      "answers": [],
      "quality_flags": {
        "clarity_score": 0.4,
        "completeness_score": 0.3,
        "testability_score": 0.2,
        "needs_clarification": true,
        "critical_gaps": [
          "No security mechanism specified",
          "Missing performance constraints",
          "External dependencies unclear"
        ]
      },
      "created_at": "2025-10-08T20:30:00",
      "updated_at": "2025-10-08T20:30:05"
    }
  ],
  "total": 1
}
```

**🔍 Análise**:
- ✅ 4 perguntas geradas pelos heurísticos
- ✅ Cada pergunta tem contexto (issue detectado)
- ✅ Quality flags mostram scores baixos
- ✅ Critical gaps identificados

---

#### **Passo 5**: Simular Respostas (Round 1)

**⚠️ ATENÇÃO**: Endpoint de resposta será implementado no módulo O1 (LangGraph State Machine)

**Por enquanto**, você pode **manualmente** atualizar o requirement com base nas perguntas:

**Endpoint**: `PUT /api/v1/projects/requirements/{requirement_id}`

```json
{
  "code": "REQ-AUTH-001",
  "descricao": "O sistema deve permitir que usuários façam login usando autenticação baseada em JWT com senha hash bcrypt",
  "criterios_aceitacao": [
    "Usuário consegue fazer login com email e senha válidos em menos de 500ms",
    "Sistema valida credenciais contra banco PostgreSQL usando bcrypt (cost factor 12)",
    "Token JWT é gerado com expiração de 24h",
    "Após 5 tentativas falhas, conta é bloqueada por 15 minutos",
    "Sistema retorna erro 401 para credenciais inválidas com mensagem genérica (segurança)"
  ],
  "prioridade": "must",
  "dependencias": [],
  "testabilidade": "Testes unitários para hash validation. Testes de integração com mock DB. Testes E2E com Postman."
}
```

**Resposta**:
```json
{
  "requirement": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "code": "REQ-AUTH-001",
    "version": 2,
    ...
  },
  "validation": {
    "valid": true,
    "errors": [],
    "validation_warnings": []
  }
}
```

**📝 Nota**: Version incrementou de 1 → 2

---

#### **Passo 6**: Iniciar Round 2 (Validar Melhorias)

**Endpoint**: `POST /api/v1/projects/{project_id}/refine`

```json
{
  "max_rounds": 5,
  "request_id": "b2c3d4e5-f6a7-8901-bcde-234567890abc",
  "answers": []
}
```

**⚠️ IMPORTANTE**: Use um **novo UUID** para o Round 2 (não reutilize o do Round 1)

**Resposta**: `202 Accepted`
```json
{
  "status": "REQS_REFINING",
  "audit_ref": {
    "task_id": "b2c3d4e5-f6a7-8901-bcde-234567890abc",
    "request_id": "b2c3d4e5-f6a7-8901-bcde-234567890abc",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "enqueued_at": "UTC_NOW",
    "state": "PENDING"
  },
  "current_round": 2,
  "max_rounds": 5
}
```

**⏱️ Aguarde**: 2-5 segundos

---

#### **Passo 7**: Verificar Sessão Round 2

**Endpoint**: `GET /api/v1/projects/{project_id}/qa-sessions`

**Resposta**: `200 OK`
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "sessions": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "round": 1,
      "questions": [...],  // 4 perguntas
      "created_at": "2025-10-08T20:30:00"
    },
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "round": 2,
      "questions": [
        {
          "id": "q1",
          "heuristic": "dependencies",
          "question": "Does the PostgreSQL database need to be running in a specific version or configuration for bcrypt integration?",
          "context": {
            "requirement_code": "REQ-AUTH-001",
            "detected_issue": "External dependency 'PostgreSQL' mentioned but version not specified"
          }
        }
      ],
      "quality_flags": {
        "clarity_score": 0.8,
        "completeness_score": 0.75,
        "testability_score": 0.9,
        "needs_clarification": true,
        "critical_gaps": []
      },
      "created_at": "2025-10-08T20:35:00"
    }
  ],
  "total": 2
}
```

**🎉 Progresso**:
- ✅ Apenas 1 pergunta (vs 4 no Round 1)
- ✅ Scores melhoraram significativamente
- ✅ `critical_gaps` está vazio
- ✅ Pergunta é mais específica (versão PostgreSQL)

---

#### **Passo 8**: Listar Todas as Sessões

**Endpoint**: `GET /api/v1/projects/{project_id}/qa-sessions`

**Path Parameter**: `project_id = 550e8400-e29b-41d4-a716-446655440000`

**Resposta**: `200 OK`
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "sessions": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "round": 1,
      "questions": [...],  // 4 perguntas
      "created_at": "2025-10-08T20:30:00"
    },
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "round": 2,
      "questions": [...],  // 1 pergunta
      "created_at": "2025-10-08T20:35:00"
    }
  ],
  "total": 2
}
```

**📊 Visualização do Progresso**:
- Round 1: 4 perguntas → Muitos gaps
- Round 2: 1 pergunta → Quase pronto

---

## 🧪 Testes de Q&A Sessions

### Teste 1: Listar Sessões do Projeto

**Endpoint**: `GET /api/v1/projects/{project_id}/qa-sessions`

**Path Parameter**: ID do projeto

**Resposta**: Lista TODAS as sessões Q&A do projeto específico

**Use case**: Histórico de refinamento do projeto

---

### Teste 2: Obter Sessão Específica

**Endpoint**: `GET /api/v1/projects/{project_id}/qa-sessions/{session_id}`

**Path Parameters**:
- `project_id`: ID do projeto
- `session_id`: ID da sessão Q&A

**Resposta**: Detalhes completos da sessão específica

**Use case**: Ver perguntas e respostas de um round específico

---

### Teste 3: Obter Sessão Inexistente

**Endpoint**: `GET /api/v1/projects/{project_id}/qa-sessions/00000000-0000-0000-0000-000000000000`

**Resposta**: `404 Not Found`
```json
{
  "detail": "QA session not found"
}
```

---

### Teste 4: Refinamento com Múltiplos Requirements

**Cenário**: Projeto com 3 requirements que todos têm termos vagos

**Endpoint**: `POST /api/v1/projects/{project_id}/refine`

**Resultado Esperado**: Perguntas agrupadas por heurístico, mas não duplicadas

**Exemplo de resposta (após task completar)**:
```json
{
  "sessions": [
    {
      "round": 1,
      "questions": [
        {
          "id": "q1",
          "heuristic": "testability",
          "question": "Multiple requirements use vague terms. Can you specify measurable criteria for: 'REQ-001: forma segura', 'REQ-002: alta performance', 'REQ-003: interface intuitiva'?"
        }
      ]
    }
  ]
}
```

---

## 🔄 Testes de Idempotência

### Teste 5: Mesmo Request ID (Idempotência)

**📌 Nota**: Use UUIDs válidos nos testes. Exemplo: `b1c2d3e4-f5a6-7890-bcde-f12345678901`

**Passo 1**: Enviar refinement
```json
POST /api/v1/projects/{project_id}/refine
{
  "max_rounds": 5,
  "request_id": "b1c2d3e4-f5a6-7890-bcde-f12345678901",
  "answers": []
}
```

**Resposta**: `202 Accepted` com `task_id` e `state: PENDING`

---

**Passo 2**: Reenviar MESMO request_id (imediatamente)

```json
POST /api/v1/projects/{project_id}/refine
{
  "max_rounds": 5,
  "request_id": "b1c2d3e4-f5a6-7890-bcde-f12345678901",
  "answers": []
}
```

**Resposta**: `202 Accepted` com **MESMO** `task_id`

**✅ Validação**:
```json
{
  "status": "REQS_REFINING",
  "audit_ref": {
    "task_id": "b1c2d3e4-f5a6-7890-bcde-f12345678901",  // ← MESMO ID
    "request_id": "b1c2d3e4-f5a6-7890-bcde-f12345678901",
    "state": "PENDING"  // ← ou "SUCCESS" se já processou
  }
}
```

**🎯 Comportamento Esperado**:
- ✅ Não cria task duplicada no Celery (reutiliza task_id)
- ✅ Celery detecta task já existente e não reexecuta
- ✅ Database pode ter 1 ou 2 registros (dependendo de timing)
- ✅ Resposta é idêntica (mesmo task_id)

---

### Teste 6: Request IDs Diferentes (Não Idempotente)

**📌 Nota**: UUIDs diferentes = Tasks diferentes

```json
// Request 1
POST /api/v1/projects/{project_id}/refine
{
  "max_rounds": 5,
  "request_id": "c1d2e3f4-a5b6-7890-cdef-123456789abc",
  "answers": []
}

// Request 2 (request_id diferente)
POST /api/v1/projects/{project_id}/refine
{
  "max_rounds": 5,
  "request_id": "d2e3f4a5-b6c7-8901-def0-23456789abcd",
  "answers": []
}
```

**Resultado**: 2 tasks criadas, 2 sessões Q&A geradas (potencialmente com rounds diferentes)

---

## 🔁 Testes de Rounds Múltiplos

### Teste 7: Limite de Rounds (MAX_ROUNDS=5)

**Cenário**: Forçar 5 rounds para atingir o limite

**Round 1**: Requirement inicial ruim
```json
POST /api/v1/qa-sessions/refine
{
  "project_id": "{project_id}",
  "request_id": "max-rounds-001"
}
```

**Round 2-4**: Melhorar requirement gradualmente (atualizar via PUT)

**Round 5**: Último round permitido
```json
POST /api/v1/qa-sessions/refine
{
  "project_id": "{project_id}",
  "request_id": "max-rounds-005"
}
```

**Round 6** (Tentativa): Deve ser bloqueado
```json
POST /api/v1/qa-sessions/refine
{
  "project_id": "{project_id}",
  "request_id": "max-rounds-006"
}
```

**Resposta Esperada**: `400 Bad Request`
```json
{
  "detail": "Maximum number of refinement rounds (5) reached for this project"
}
```

---

### Teste 8: Verificar Incremento de Round

**Passo 1**: Criar projeto e requirement

**Passo 2**: Round 1
```json
POST /api/v1/qa-sessions/refine → current_round: 1
```

**Passo 3**: Round 2
```json
POST /api/v1/qa-sessions/refine → current_round: 2
```

**Validação**:
```sql
-- Query no banco (via pgAdmin ou psql)
SELECT current_round, created_at 
FROM qa_sessions 
WHERE project_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY created_at;

-- Resultado esperado:
-- current_round | created_at
-- 1             | 2025-10-08 20:30:00
-- 2             | 2025-10-08 20:35:00
```

---

## 🔍 Testes de Heurísticos

### Teste 9: Heurístico "Testability"

**Requirement com termos subjetivos**:

```json
{
  "code": "REQ-TEST-001",
  "descricao": "Interface deve ser bonita e intuitiva",
  "criterios_aceitacao": [
    "Usuários devem achar fácil de usar",
    "Design deve ser moderno"
  ],
  "prioridade": "should"
}
```

**Após Refinement**:

**Perguntas Esperadas**:
```json
{
  "questions": [
    {
      "heuristic": "testability",
      "question": "What are the measurable criteria for 'bonita' in requirement 'REQ-TEST-001'? How will you test if the interface is 'bonita'?",
      "context": {
        "detected_terms": ["bonita", "intuitiva", "fácil", "moderno"]
      }
    }
  ]
}
```

---

### Teste 10: Heurístico "Ambiguity"

**Requirement com linguagem vaga**:

```json
{
  "code": "REQ-AMB-001",
  "descricao": "Sistema deve ser rápido e processar muitos dados",
  "criterios_aceitacao": [
    "Responder em tempo razoável",
    "Suportar bastante usuários"
  ],
  "prioridade": "must"
}
```

**Perguntas Esperadas**:
```json
{
  "questions": [
    {
      "heuristic": "ambiguity",
      "question": "Please quantify 'rápido', 'muitos dados', 'tempo razoável', and 'bastante usuários' in requirement 'REQ-AMB-001' with specific metrics.",
      "context": {
        "vague_terms": ["rápido", "muitos", "razoável", "bastante"]
      }
    }
  ]
}
```

---

### Teste 11: Heurístico "Dependencies"

**Requirement com dependências externas implícitas**:

```json
{
  "code": "REQ-DEP-001",
  "descricao": "Sistema deve enviar notificações por email usando template HTML",
  "criterios_aceitacao": [
    "Email entregue em menos de 30 segundos",
    "Template responsivo para mobile"
  ],
  "prioridade": "must"
}
```

**Perguntas Esperadas**:
```json
{
  "questions": [
    {
      "heuristic": "dependencies",
      "question": "Which email service will be used for requirement 'REQ-DEP-001'? (e.g., SendGrid, AWS SES, SMTP server)",
      "context": {
        "implicit_dependencies": ["email service", "template engine"]
      }
    }
  ]
}
```

---

### Teste 12: Heurístico "Acceptance Criteria"

**Requirement com critérios genéricos**:

```json
{
  "code": "REQ-AC-001",
  "descricao": "Dashboard deve exibir relatórios",
  "criterios_aceitacao": [
    "Relatórios são exibidos"
  ],
  "prioridade": "should"
}
```

**Perguntas Esperadas**:
```json
{
  "questions": [
    {
      "heuristic": "acceptance_criteria",
      "question": "What are the specific acceptance criteria for requirement 'REQ-AC-001'? Current criteria are too generic.",
      "context": {
        "issue": "Only one generic criterion provided"
      }
    }
  ]
}
```

---

### Teste 13: Heurístico "Constraints"

**Requirement sem constraints formalizadas**:

```json
{
  "code": "REQ-CON-001",
  "descricao": "API REST para busca de produtos",
  "criterios_aceitacao": [
    "Endpoint GET /products retorna lista de produtos",
    "Suporta filtros por categoria"
  ],
  "prioridade": "must"
}
```

**Perguntas Esperadas**:
```json
{
  "questions": [
    {
      "heuristic": "constraints",
      "question": "What are the performance and error handling constraints for requirement 'REQ-CON-001'? (e.g., response time, rate limiting, pagination, error codes)",
      "context": {
        "missing_constraints": ["performance", "pagination", "error handling"]
      }
    }
  ]
}
```

---

## ⚠️ Cenários de Erro

### Erro 1: Projeto Não Encontrado

**Endpoint**: `POST /api/v1/qa-sessions/refine`

```json
{
  "project_id": "00000000-0000-0000-0000-000000000000",
  "request_id": "test-001"
}
```

**Resposta**: `404 Not Found`
```json
{
  "detail": "Project not found"
}
```

---

### Erro 2: Projeto Sem Requirements

**Endpoint**: `POST /api/v1/qa-sessions/refine`

**Cenário**: Projeto existe mas não tem requirements

**Resposta**: `400 Bad Request`
```json
{
  "detail": "Project has no requirements to refine"
}
```

---

### Erro 3: Request ID Duplicado (Idempotência)

**NÃO é erro!** Retorna sessão existente (ver Teste 5)

---

### Erro 4: Status do Projeto Inválido

**Endpoint**: `POST /api/v1/qa-sessions/refine`

**Cenário**: Projeto está em status `DONE` ou `BLOCKED`

**Resposta**: `400 Bad Request`
```json
{
  "detail": "Project status must be DRAFT or REQS_REFINING to start refinement"
}
```

---

### Erro 5: Worker Celery Offline

**Endpoint**: `POST /api/v1/qa-sessions/refine`

**Cenário**: Worker não está rodando

**Resposta**: `200 OK` (Task enfileirada, mas não processa)

**Como Detectar**:
1. Enviar refinement request
2. Aguardar 10 segundos
3. GET session ainda mostra `status: processing`
4. Perguntas nunca são geradas

**Solução**: Iniciar worker (`./start_worker.sh`)

---

### Erro 6: Redis Offline

**Endpoint**: `POST /api/v1/qa-sessions/refine`

**Cenário**: Redis não está rodando

**Resposta**: `500 Internal Server Error`
```json
{
  "detail": "Failed to connect to task queue"
}
```

**Solução**: `docker-compose up -d`

---

## 📊 Monitoramento Celery

### Ver Tasks em Tempo Real

**Flower (Dashboard Celery)** - Opcional

```bash
# Instalar Flower
pip install flower

# Iniciar
celery -A app.celery_app flower --port=5555

# Acessar
http://localhost:5555
```

**Funcionalidades**:
- ✅ Ver tasks em execução
- ✅ Ver tasks completadas
- ✅ Ver falhas
- ✅ Ver workers ativos
- ✅ Gráficos de performance

---

### Ver Logs do Worker

**Terminal do Worker** mostra:

```
[2025-10-08 20:30:05,000: INFO/MainProcess] Task app.tasks.analyst.refine_requirements[req-001-round-1] received
[2025-10-08 20:30:05,100: INFO/ForkPoolWorker-1] Starting refinement for project 550e8400...
[2025-10-08 20:30:05,200: INFO/ForkPoolWorker-1] Analyzing 1 requirements
[2025-10-08 20:30:05,300: INFO/ForkPoolWorker-1] Heuristic 'testability' generated 1 questions
[2025-10-08 20:30:05,400: INFO/ForkPoolWorker-1] Heuristic 'dependencies' generated 1 questions
[2025-10-08 20:30:05,500: INFO/ForkPoolWorker-1] Total questions generated: 4
[2025-10-08 20:30:05,600: INFO/ForkPoolWorker-1] QA session saved: 880e8400...
[2025-10-08 20:30:05,700: INFO/ForkPoolWorker-1] Task app.tasks.analyst.refine_requirements[req-001-round-1] succeeded
```

---

### Verificar Status no Database

**Query SQL**:

```sql
-- Listar todas as sessões Q&A
SELECT 
  id,
  project_id,
  request_id,
  current_round,
  jsonb_array_length(questions) as total_questions,
  created_at
FROM qa_sessions
ORDER BY created_at DESC;

-- Ver perguntas de uma sessão
SELECT 
  request_id,
  current_round,
  jsonb_pretty(questions) as questions_detail
FROM qa_sessions
WHERE id = '880e8400-e29b-41d4-a716-446655440003';

-- Ver quality flags
SELECT 
  request_id,
  current_round,
  jsonb_pretty(quality_flags) as quality_detail
FROM qa_sessions
WHERE project_id = '550e8400-e29b-41d4-a716-446655440000';
```

---

## 📝 Checklist de Testes R3

**Setup**:
- [ ] Redis rodando (docker ps)
- [ ] PostgreSQL rodando (docker ps)
- [ ] Worker Celery ativo (./start_worker.sh)
- [ ] API rodando (uvicorn)
- [ ] Swagger acessível (http://localhost:8000/docs)

**Fluxo Básico**:
- [ ] Criar projeto
- [ ] Adicionar requirement com gaps
- [ ] Iniciar refinement (Round 1)
- [ ] Aguardar processamento (2-5s)
- [ ] Verificar sessão criada
- [ ] Ver perguntas geradas
- [ ] Verificar quality flags

**Idempotência**:
- [ ] Enviar mesmo request_id 2x → Mesma sessão
- [ ] Enviar request_ids diferentes → Sessões diferentes

**Heurísticos**:
- [ ] Testability: Termos subjetivos detectados
- [ ] Ambiguity: Linguagem vaga identificada
- [ ] Dependencies: Sistemas externos encontrados
- [ ] Acceptance Criteria: Critérios genéricos flagados
- [ ] Constraints: Constraints faltantes detectadas

**Rounds Múltiplos**:
- [ ] Round 1: Muitas perguntas
- [ ] Atualizar requirement
- [ ] Round 2: Menos perguntas
- [ ] Verificar incremento de current_round
- [ ] Testar limite MAX_ROUNDS=5

**Listagem**:
- [ ] GET /projects/{id}/qa-sessions (todas as sessões do projeto)
- [ ] GET /projects/{id}/qa-sessions/{session_id} (sessão específica)

**Erros**:
- [ ] Projeto não encontrado → 404
- [ ] Projeto sem requirements → 400
- [ ] Status inválido → 400
- [ ] Worker offline → Task não processa
- [ ] Redis offline → 500

---

## 🎯 Casos de Uso Reais

### Caso 1: Requisito de Performance Vago

**Input**:
```json
{
  "code": "PERF-001",
  "descricao": "Sistema deve ser rápido",
  "criterios_aceitacao": ["Responde rápido"]
}
```

**Perguntas Esperadas**:
- "What is the maximum acceptable response time?"
- "What is the expected number of concurrent users?"
- "Are there specific endpoints with stricter performance requirements?"

---

### Caso 2: Requisito de Segurança Incompleto

**Input**:
```json
{
  "code": "SEC-001",
  "descricao": "Dados devem ser protegidos",
  "criterios_aceitacao": ["Dados seguros"]
}
```

**Perguntas Esperadas**:
- "What encryption method should be used? (e.g., AES-256, RSA)"
- "Should data be encrypted at rest, in transit, or both?"
- "Are there compliance requirements? (e.g., GDPR, LGPD, HIPAA)"

---

### Caso 3: Requisito de Integração Sem Detalhes

**Input**:
```json
{
  "code": "INT-001",
  "descricao": "Integrar com sistema externo",
  "criterios_aceitacao": ["Integração funcional"]
}
```

**Perguntas Esperadas**:
- "Which external system will be integrated?"
- "What is the integration protocol? (REST, GraphQL, SOAP, gRPC)"
- "What is the expected SLA for the external system?"
- "How should the system handle external system downtime?"

---

## 🚀 Próximos Passos

Após validar o R3:

1. **Módulo O1 (State Machine)**:
   - Implementar máquina de estados com LangGraph
   - Endpoint para submeter respostas
   - Transições automáticas entre rounds
   - Critérios de parada (quality threshold)

2. **Módulo O2 (Code Validation)**:
   - Validação de código gerado
   - Análise de aderência aos requirements

3. **Módulo O3 (LLM Integration)**:
   - Substituir heurísticos por LLM
   - Perguntas mais contextuais
   - Análise semântica profunda

---

## 📚 Documentação Adicional

- **R3_IMPLEMENTATION.md**: Detalhes técnicos da implementação
- **R3_ARCHITECTURE.md**: Arquitetura e design patterns
- **R3_COMMANDS_REFERENCE.md**: Referência rápida de comandos
- **SWAGGER_TEST_GUIDE.md**: Testes de requirements base

---

## 🔧 Exemplo de Requisição cURL Correta

### ✅ Comando cURL Válido:

```bash
# Gerar UUID único
REQUEST_UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')

# Definir ID do projeto
PROJECT_ID="550e8400-e29b-41d4-a716-446655440000"

# Enviar requisição
curl -X 'POST' \
  "http://localhost:8000/api/v1/projects/${PROJECT_ID}/refine" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d "{
  \"max_rounds\": 5,
  \"request_id\": \"${REQUEST_UUID}\",
  \"answers\": []
}"
```

### 📋 Notas Importantes:

1. **UUID obrigatório**: `request_id` DEVE ser UUID v4
2. **Porta correta**: Por padrão é `8000` (não `8001`)
3. **Endpoint**: `/api/v1/projects/{project_id}/refine` (não `/qa-sessions/refine`)
4. **Campos obrigatórios**:
   - `request_id`: UUID único (obrigatório)
   - `max_rounds`: Número máximo de rounds (opcional, default: 5)
   - `answers`: Array de respostas (opcional, vazio no Round 1)

### ❌ Erros Comuns:

**Erro 1**: `request_id must be a valid UUID`
```bash
# ERRADO:
"request_id": "req-001-round-1"

# CORRETO:
"request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Erro 2**: `Input should be greater than or equal to 1`
```bash
# ERRADO (campo answers):
"confidence": 0

# CORRETO:
"confidence": 8  # Escala 1-10
```

**Erro 3**: Endpoint incorreto
```bash
# ERRADO:
POST /api/v1/qa-sessions/refine

# CORRETO:
POST /api/v1/projects/{project_id}/refine
```

**Erro 4**: Formato de resposta
```bash
# A resposta NÃO retorna session_id diretamente
# Ela retorna task_id dentro de audit_ref

# ✅ CORRETO:
{
  "status": "REQS_REFINING",
  "audit_ref": {
    "task_id": "uuid-do-request",
    "state": "PENDING"
  }
}

# Para ver as sessões criadas, use:
GET /api/v1/projects/{project_id}/qa-sessions
```

---

## ✅ Pronto para Testar!

Acesse: **http://localhost:8000/docs**

Procure pela tag: **`qa_sessions`**

Bons testes! 🎉
