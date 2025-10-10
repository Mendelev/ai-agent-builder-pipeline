# 🔄 Guia de Testes - Módulo R4 (Requirements Gateway)

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Conceitos Fundamentais](#conceitos-fundamentais)
3. [Endpoints Disponíveis](#endpoints-disponíveis)
4. [Cenários de Teste](#cenários-de-teste)
5. [Testes via Swagger](#testes-via-swagger)
6. [Checklist de Validação](#checklist-de-validação)

---

## 🎯 Visão Geral

O **Requirements Gateway (R4)** é o ponto de decisão após o refinamento de requisitos (R3). Ele controla as transições de estado do projeto, permitindo que o usuário escolha o próximo passo:

- **Finalizar**: Marca requisitos como prontos (sem processamento adicional)
- **Planejar**: Avança para a fase de planejamento
- **Validar Código**: Solicita validação de código existente contra requisitos

### 🔄 Fluxo do Processo

```
DRAFT → REQS_REFINING → [GATEWAY] → REQS_READY ou CODE_VALIDATION_REQUESTED
                            ↓
                      (finalizar / planejar / validar_codigo)
```

---

## 📚 Conceitos Fundamentais

### Estados do Projeto

| Estado | Descrição |
|--------|-----------|
| `DRAFT` | Projeto criado, ainda não iniciou refinamento |
| `REQS_REFINING` | Requisitos sendo refinados (fase R3) |
| `REQS_READY` | Requisitos finalizados e prontos |
| `CODE_VALIDATION_REQUESTED` | Validação de código solicitada |

### Ações do Gateway

| Ação | Estado Destino | Descrição |
|------|----------------|-----------|
| `finalizar` | `REQS_READY` | Finaliza requisitos sem processamento adicional |
| `planejar` | `REQS_READY` | Indica intenção de avançar para planejamento |
| `validar_codigo` | `CODE_VALIDATION_REQUESTED` | Solicita validação de código existente |

### Campos de Rastreamento

- **correlation_id**: Agrupa operações relacionadas entre serviços
- **request_id**: Chave de idempotência (evita duplicação)
- **audit_ref**: Referência completa da auditoria

---

## 🔌 Endpoints Disponíveis

### 1. POST /api/v1/requirements/{project_id}/gateway

Executa transição de estado via gateway.

**Pré-requisitos:**
- Projeto deve estar em estado `REQS_REFINING`
- Projeto deve ter pelo menos 1 requisito

**Request Schema:**
```json
{
  "action": "finalizar | planejar | validar_codigo",
  "correlation_id": "uuid (opcional)",
  "request_id": "uuid (opcional, auto-gerado se omitido)"
}
```

**Response Schema:**
```json
{
  "from": "REQS_REFINING",
  "to": "REQS_READY",
  "reason": "User chose to finalize requirements",
  "audit_ref": {
    "correlation_id": "uuid",
    "request_id": "uuid",
    "project_id": "uuid",
    "timestamp": "2024-01-15T10:30:45.123Z",
    "action": "finalizar",
    "user_id": null
  }
}
```

### 2. GET /api/v1/requirements/{project_id}/gateway/history

Retorna histórico de transições do gateway para um projeto.

**Response Schema:**
```json
[
  {
    "id": "uuid",
    "project_id": "uuid",
    "correlation_id": "uuid",
    "request_id": "uuid",
    "action": "finalizar",
    "from_state": "REQS_REFINING",
    "to_state": "REQS_READY",
    "user_id": null,
    "created_at": "2024-01-15T10:30:45.123Z"
  }
]
```

---

## 🧪 Cenários de Teste

### Cenário 1: Transição com FINALIZAR

**Objetivo**: Marcar requisitos como finalizados

**Passos:**

1. **Criar Projeto**
```json
POST /api/v1/projects
{
  "name": "Sistema de E-commerce"
}
```

2. **Adicionar Requisitos**
```json
POST /api/v1/projects/{project_id}/requirements
{
  "requirements": [
    {
      "code": "REQ-AUTH-001",
      "descricao": "Sistema de autenticação de usuários",
      "criterios_aceitacao": [
        "Login com email e senha",
        "Logout funcional",
        "Recuperação de senha"
      ],
      "prioridade": "must",
      "dependencias": []
    }
  ]
}
```

3. **Atualizar Estado para REQS_REFINING**
```json
PATCH /api/v1/projects/{project_id}
{
  "status": "REQS_REFINING"
}
```

4. **Executar Gateway - FINALIZAR**
```json
POST /api/v1/requirements/{project_id}/gateway
{
  "action": "finalizar"
}
```

**Resposta Esperada:**
```json
{
  "from": "REQS_REFINING",
  "to": "REQS_READY",
  "reason": "User chose to finalize requirements",
  "audit_ref": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "request_id": "550e8400-e29b-41d4-a716-446655440001",
    "project_id": "550e8400-e29b-41d4-a716-446655440002",
    "timestamp": "2024-01-15T10:30:45.123Z",
    "action": "finalizar",
    "user_id": null
  }
}
```

5. **Verificar Estado do Projeto**
```json
GET /api/v1/projects/{project_id}

Response:
{
  "id": "uuid",
  "name": "Sistema de E-commerce",
  "status": "REQS_READY",  ✓
  ...
}
```

---

### Cenário 2: Transição com PLANEJAR

**Objetivo**: Indicar que requisitos estão prontos para planejamento

**Request:**
```json
POST /api/v1/requirements/{project_id}/gateway
{
  "action": "planejar",
  "correlation_id": "custom-correlation-id-123"
}
```

**Resposta Esperada:**
```json
{
  "from": "REQS_REFINING",
  "to": "REQS_READY",
  "reason": "User chose to proceed to planning",
  "audit_ref": {
    "correlation_id": "custom-correlation-id-123",
    ...
  }
}
```

**Diferença de `finalizar`**: 
- Ambos transitam para `REQS_READY`
- `planejar` indica **intenção** de avançar para fase de planejamento
- `finalizar` indica apenas que requisitos estão completos

---

### Cenário 3: Transição com VALIDAR_CODIGO

**Objetivo**: Solicitar validação de código existente contra requisitos

**Request:**
```json
POST /api/v1/requirements/{project_id}/gateway
{
  "action": "validar_codigo"
}
```

**Resposta Esperada:**
```json
{
  "from": "REQS_REFINING",
  "to": "CODE_VALIDATION_REQUESTED",  ✓
  "reason": "User requested code validation",
  "audit_ref": {
    ...
  }
}
```

**Diferença**: Estado final é `CODE_VALIDATION_REQUESTED` (não `REQS_READY`)

---

### Cenário 4: Idempotência com request_id

**Objetivo**: Garantir que requisições duplicadas não criem múltiplas transições

**Primeira Requisição:**
```json
POST /api/v1/requirements/{project_id}/gateway
{
  "action": "finalizar",
  "request_id": "550e8400-e29b-41d4-a716-446655440099"
}

Response:
{
  "from": "REQS_REFINING",
  "to": "REQS_READY",
  "audit_ref": {
    "correlation_id": "abc-123",
    "request_id": "550e8400-e29b-41d4-a716-446655440099",
    ...
  }
}
```

**Segunda Requisição (MESMO request_id):**
```json
POST /api/v1/requirements/{project_id}/gateway
{
  "action": "finalizar",
  "request_id": "550e8400-e29b-41d4-a716-446655440099"
}

Response:
{
  "from": "REQS_REFINING",
  "to": "REQS_READY",
  "audit_ref": {
    "correlation_id": "abc-123",  ✓ MESMO correlation_id
    "request_id": "550e8400-e29b-41d4-a716-446655440099",
    ...
  }
}
```

**Verificação**: Ambas as respostas devem ter o **mesmo** `correlation_id`, comprovando idempotência.

---

### Cenário 5: Histórico de Transições

**Objetivo**: Consultar todas as transições de gateway de um projeto

**Setup**: Executar múltiplas transições em projetos diferentes

**Request:**
```json
GET /api/v1/requirements/{project_id}/gateway/history
```

**Resposta Esperada:**
```json
[
  {
    "id": "audit-1",
    "project_id": "project-123",
    "correlation_id": "corr-1",
    "request_id": "req-1",
    "action": "finalizar",
    "from_state": "REQS_REFINING",
    "to_state": "REQS_READY",
    "user_id": null,
    "created_at": "2024-01-15T10:30:45.123Z"
  }
]
```

**Ordenação**: Histórico retorna em ordem **decrescente** por `created_at` (mais recente primeiro)

---

## ❌ Cenários de Erro

### Erro 1: Estado Inválido (DRAFT)

**Request:**
```json
POST /api/v1/requirements/{project_id}/gateway
{
  "action": "finalizar"
}
```

**Projeto em estado**: `DRAFT`

**Resposta**: `400 Bad Request`
```json
{
  "detail": {
    "detail": "Invalid state transition: project in DRAFT state cannot transition via gateway",
    "error_code": "INVALID_STATE_TRANSITION",
    "current_state": "DRAFT",
    "requested_action": "finalizar"
  }
}
```

---

### Erro 2: Projeto Sem Requisitos

**Request:**
```json
POST /api/v1/requirements/{project_id}/gateway
{
  "action": "finalizar"
}
```

**Projeto**: Estado `REQS_REFINING` mas **sem requisitos**

**Resposta**: `400 Bad Request`
```json
{
  "detail": {
    "detail": "Project must have at least one requirement to proceed through gateway",
    "error_code": "NO_REQUIREMENTS",
    "current_state": "REQS_REFINING"
  }
}
```

---

### Erro 3: Ação Inválida

**Request:**
```json
POST /api/v1/requirements/{project_id}/gateway
{
  "action": "acao_invalida"
}
```

**Resposta**: `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "action"],
      "msg": "Input should be 'finalizar', 'planejar' or 'validar_codigo'",
      "input": "acao_invalida",
      "ctx": {
        "expected": "'finalizar', 'planejar' or 'validar_codigo'"
      }
    }
  ]
}
```

---

### Erro 4: Projeto Não Encontrado

**Request:**
```json
POST /api/v1/requirements/00000000-0000-0000-0000-000000000000/gateway
{
  "action": "finalizar"
}
```

**Resposta**: `404 Not Found`
```json
{
  "detail": "Project not found"
}
```

---

## 🧪 Testes via Swagger

### Acesso ao Swagger

1. Inicie o backend: `cd backend && uvicorn main:app --reload`
2. Acesse: http://localhost:8000/docs

### Workflow Completo via Swagger

#### Passo 1: Criar Projeto

**Endpoint**: `POST /api/v1/projects`

**Body**:
```json
{
  "name": "Teste R4 via Swagger"
}
```

**Copie o `id` retornado**: Ex: `550e8400-e29b-41d4-a716-446655440000`

---

#### Passo 2: Adicionar Requisitos

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-SWAGGER-001",
      "descricao": "Requisito de teste via Swagger",
      "criterios_aceitacao": [
        "Critério 1: Teste funcional",
        "Critério 2: Documentado"
      ],
      "prioridade": "must",
      "dependencias": []
    }
  ]
}
```

---

#### Passo 3: Atualizar Estado

**Endpoint**: `PATCH /api/v1/projects/{project_id}`

**Body**:
```json
{
  "status": "REQS_REFINING"
}
```

---

#### Passo 4: Executar Gateway

**Endpoint**: `POST /api/v1/requirements/{project_id}/gateway`

**Testar as 3 ações:**

**Ação A: Finalizar**
```json
{
  "action": "finalizar"
}
```

**Ação B: Planejar** (criar novo projeto para testar)
```json
{
  "action": "planejar"
}
```

**Ação C: Validar Código** (criar novo projeto para testar)
```json
{
  "action": "validar_codigo"
}
```

---

#### Passo 5: Consultar Histórico

**Endpoint**: `GET /api/v1/requirements/{project_id}/gateway/history`

**Sem body** - Apenas informe o `project_id`

**Resposta**: Lista de transições do projeto

---

## 🎯 Matriz de Transições Válidas

| Estado Atual | Ação | Estado Final | Status |
|-------------|------|--------------|--------|
| `REQS_REFINING` | `finalizar` | `REQS_READY` | ✅ Válido |
| `REQS_REFINING` | `planejar` | `REQS_READY` | ✅ Válido |
| `REQS_REFINING` | `validar_codigo` | `CODE_VALIDATION_REQUESTED` | ✅ Válido |
| `DRAFT` | qualquer | - | ❌ Erro 400 |
| `REQS_READY` | qualquer | - | ❌ Erro 400 |
| `CODE_VALIDATION_REQUESTED` | qualquer | - | ❌ Erro 400 |

---

## ✅ Checklist de Validação

Marque conforme for testando:

### Funcionalidades Básicas
- [ ] Criar projeto e adicionar requisitos
- [ ] Atualizar projeto para estado `REQS_REFINING`
- [ ] Executar gateway com ação `finalizar`
- [ ] Executar gateway com ação `planejar`
- [ ] Executar gateway com ação `validar_codigo`
- [ ] Verificar estado final do projeto após cada ação

### Rastreamento e Auditoria
- [ ] Verificar `audit_ref` contém todos os campos
- [ ] Testar com `correlation_id` customizado
- [ ] Verificar auto-geração de `request_id` se não fornecido
- [ ] Consultar histórico de transições
- [ ] Verificar ordenação do histórico (mais recente primeiro)

### Idempotência
- [ ] Executar gateway com `request_id` específico
- [ ] Repetir requisição com mesmo `request_id`
- [ ] Verificar que `correlation_id` permanece o mesmo
- [ ] Confirmar que estado do projeto não muda na segunda requisição

### Validações e Erros
- [ ] Tentar gateway em projeto no estado `DRAFT` → 400
- [ ] Tentar gateway em projeto sem requisitos → 400
- [ ] Tentar gateway com ação inválida → 422
- [ ] Tentar gateway com project_id inexistente → 404
- [ ] Verificar mensagens de erro são claras e informativas

### Integração com R3
- [ ] Criar projeto → Adicionar requisitos → R3 Refine → Gateway
- [ ] Verificar transição completa: `DRAFT` → `REQS_REFINING` → `REQS_READY`

---

## 🚀 Scripts de Teste Automatizados

O projeto inclui scripts prontos para teste:

### 1. test_r4_basic.sh
Testes básicos com curl de todas as ações do gateway.

```bash
cd backend
chmod +x test_r4_basic.sh
./test_r4_basic.sh
```

### 2. test_r4_e2e.sh
Workflow completo end-to-end com múltiplos cenários.

```bash
cd backend
chmod +x test_r4_e2e.sh
./test_r4_e2e.sh
```

### 3. test_r4_direct.py
Testes automatizados em Python com casos de teste detalhados.

```bash
cd backend
python3 test_r4_direct.py
```

---

## 📊 Tabela de Estados e Significados

| Estado | Significado | Próximo Passo Esperado |
|--------|-------------|------------------------|
| `DRAFT` | Projeto criado, configuração inicial | Adicionar requisitos |
| `REQS_REFINING` | Requisitos em refinamento (R3 ativo) | Gateway de decisão |
| `REQS_READY` | Requisitos finalizados | Planejamento ou execução |
| `CODE_VALIDATION_REQUESTED` | Validação de código solicitada | Workflow de validação |
| `CODE_VALIDATED` | Código validado contra requisitos | Avançar para planejamento |
| `PLAN_READY` | Plano de execução pronto | Gerar prompts |
| `PROMPTS_READY` | Prompts de IA gerados | Execução |
| `DONE` | Projeto completo | - |
| `BLOCKED` | Projeto bloqueado por algum motivo | Resolução de bloqueio |

---

## 🔍 Troubleshooting

### Problema: Gateway retorna 400 mesmo com projeto em REQS_REFINING

**Solução**: Verifique se o projeto tem pelo menos 1 requisito:
```bash
GET /api/v1/projects/{project_id}/requirements
```

### Problema: request_id não está funcionando como esperado

**Solução**: `request_id` deve ser UUID válido. Use geradores online ou:
```bash
uuidgen  # Linux/Mac
```

### Problema: Histórico retorna vazio

**Solução**: Verifique se está consultando o `project_id` correto e se alguma transição foi executada.

---

## 📝 Notas de Implementação

- **User ID**: Atualmente `null`, será implementado quando autenticação estiver ativa
- **Rollback**: Não há rollback automático; transições são finais
- **Concurrent Access**: Gateway suporta acesso concorrente via locks de banco
- **Performance**: Indexes otimizados em `project_id`, `correlation_id`, `request_id`

---

## ✨ Próximos Passos

Após testar R4, você pode:

1. **Integrar com R3**: Workflow completo de refinamento → gateway
2. **Implementar Planning Phase**: Avançar projetos `REQS_READY` para planejamento
3. **Code Validation**: Implementar workflow de validação de código
4. **Analytics**: Usar histórico de gateway para métricas e dashboards

---

**Documentação gerada para o módulo R4 - Requirements Gateway**  
**Versão**: 1.0  
**Data**: 2024
