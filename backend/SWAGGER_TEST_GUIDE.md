# 🧪 Guia de Testes - Swagger API

**Acesso**: http://localhost:8000/docs  
**Data**: 8 de outubro de 2025  
**Versão da API**: 1.0.0

---

## 📋 Índice

1. [Como Usar o Swagger](#como-usar-o-swagger)
2. [Testes de Projetos](#testes-de-projetos)
3. [Testes de Requirements](#testes-de-requirements)
4. [Testes de Validação](#testes-de-validação)
5. [Testes de Versionamento](#testes-de-versionamento)
6. [Testes de Dependências](#testes-de-dependências)
7. [Cenários de Erro](#cenários-de-erro)
8. [Fluxo Completo](#fluxo-completo-passo-a-passo)

---

## 🚀 Como Usar o Swagger

1. **Iniciar o servidor**:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Acessar Swagger UI**: http://localhost:8000/docs

3. **Testar endpoints**:
   - Clique no endpoint desejado
   - Clique em "Try it out"
   - Cole o JSON de exemplo
   - Clique em "Execute"
   - Veja a resposta abaixo

---

## 📦 1. Testes de Projetos

### 1.1. Criar Projeto Simples

**Endpoint**: `POST /api/v1/projects`

**Request Body**:
```json
{
  "name": "Sistema de Gestão de Tarefas"
}
```

**Resposta Esperada**: `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Sistema de Gestão de Tarefas",
  "status": "DRAFT",
  "created_by": null,
  "created_at": "2025-10-08T12:00:00",
  "updated_at": "2025-10-08T12:00:00"
}
```

**💡 Dica**: Salve o `id` retornado para usar nos próximos testes!

---

### 1.2. Criar Projeto com Usuário

**Endpoint**: `POST /api/v1/projects`

**Request Body**:
```json
{
  "name": "E-commerce Marketplace",
  "created_by": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

### 1.3. Listar Todos os Projetos

**Endpoint**: `GET /api/v1/projects`

**Sem parâmetros necessários**

**Resposta Esperada**: `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Sistema de Gestão de Tarefas",
    "status": "DRAFT",
    ...
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "E-commerce Marketplace",
    "status": "DRAFT",
    ...
  }
]
```

---

### 1.4. Obter Projeto por ID

**Endpoint**: `GET /api/v1/projects/{project_id}`

**Path Parameter**: Use o ID do projeto criado

**Resposta Esperada**: `200 OK`

---

### 1.5. Atualizar Status do Projeto

**Endpoint**: `PATCH /api/v1/projects/{project_id}`

**Request Body**:
```json
{
  "status": "REQS_REFINING"
}
```

**Status válidos**:
- `DRAFT`
- `REQS_REFINING`
- `REQS_READY`
- `CODE_VALIDATION_REQUESTED`
- `CODE_VALIDATED`
- `PLAN_READY`
- `PROMPTS_READY`
- `DONE`
- `BLOCKED`

---

### 1.6. Atualizar Nome e Status

**Endpoint**: `PATCH /api/v1/projects/{project_id}`

**Request Body**:
```json
{
  "name": "Sistema de Gestão de Tarefas v2",
  "status": "REQS_READY"
}
```

---

## 📝 2. Testes de Requirements

### 2.1. Criar Requirements Básicos (Bulk Insert)

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Request Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-001",
      "descricao": "Sistema deve permitir login de usuários",
      "criterios_aceitacao": [
        "Usuário pode fazer login com email e senha",
        "Sistema valida credenciais no banco de dados",
        "Token JWT é gerado após login bem-sucedido"
      ],
      "prioridade": "must",
      "dependencias": []
    },
    {
      "code": "REQ-002",
      "descricao": "Dashboard deve exibir métricas em tempo real",
      "criterios_aceitacao": [
        "Gráficos atualizam a cada 5 segundos",
        "Suporta 1000+ usuários simultâneos",
        "Dados vêm de API websocket"
      ],
      "prioridade": "should",
      "dependencias": ["REQ-001"]
    }
  ]
}
```

**Resposta Esperada**: `200 OK`
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "REQ-001",
    "version": 1,
    "data": {
      "code": "REQ-001",
      "descricao": "Sistema deve permitir login de usuários",
      "criterios_aceitacao": ["..."],
      "prioridade": "must",
      "dependencias": [],
      "testabilidade": null,
      "waiver_reason": null
    },
    "created_at": "...",
    "updated_at": "..."
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "REQ-002",
    "version": 1,
    ...
  }
]
```

**💡 Dica**: Salve os IDs dos requirements para testes de atualização!

---

### 2.2. Criar Requirement com Testabilidade

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Request Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-003",
      "descricao": "API deve responder em menos de 200ms",
      "criterios_aceitacao": [
        "95% das requisições < 200ms",
        "Testado com carga de 100 req/s"
      ],
      "prioridade": "should",
      "dependencias": [],
      "testabilidade": "Usar JMeter com script de carga. Métricas via New Relic."
    }
  ]
}
```

---

### 2.3. Criar Requirement com Prioridade Baixa

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Request Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-004",
      "descricao": "Tema escuro para interface",
      "criterios_aceitacao": [
        "Usuário pode alternar entre claro/escuro",
        "Preferência salva no localStorage"
      ],
      "prioridade": "could",
      "dependencias": []
    }
  ]
}
```

---

### 2.4. Criar Requirement "Won't Have"

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Request Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-005",
      "descricao": "Integração com redes sociais (descartado)",
      "criterios_aceitacao": [
        "Login via Facebook/Google descartado por questões de privacidade"
      ],
      "prioridade": "wont",
      "dependencias": []
    }
  ]
}
```

---

### 2.5. Listar Requirements do Projeto

**Endpoint**: `GET /api/v1/projects/{project_id}/requirements`

**Sem parâmetros** - Retorna versão atual de todos os requirements

**Resposta Esperada**: `200 OK` - Array com todos os requirements

---

### 2.6. Listar Requirements em Versão Específica

**Endpoint**: `GET /api/v1/projects/{project_id}/requirements`

**Query Parameters**:
- `version`: 1

**Exemplo**: `/api/v1/projects/{project_id}/requirements?version=1`

**Use case**: Ver como estava o projeto em uma versão anterior

---

## 🔄 3. Testes de Versionamento

### 3.1. Atualizar Requirement (Cria Nova Versão)

**Endpoint**: `PUT /api/v1/projects/requirements/{requirement_id}`

**Request Body**:
```json
{
  "code": "REQ-001",
  "descricao": "Sistema deve permitir login de usuários via OAuth2",
  "criterios_aceitacao": [
    "Usuário pode fazer login com email e senha",
    "Suporte a Google OAuth2",
    "Suporte a Microsoft OAuth2",
    "Token JWT é gerado após login bem-sucedido"
  ],
  "prioridade": "must",
  "dependencias": []
}
```

**Resposta Esperada**: `200 OK`
```json
{
  "requirement": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "version": 2,
    "data": {
      "code": "REQ-001",
      "descricao": "Sistema deve permitir login de usuários via OAuth2",
      ...
    }
  },
  "validation": {
    "valid": true,
    "errors": [],
    "validation_warnings": [
      "No testability information provided"
    ]
  }
}
```

**📝 Nota**: 
- Versão incrementa de 1 → 2
- Versão 1 é arquivada em `requirements_versions`
- Campo `validation` mostra warnings (não bloqueantes)

---

### 3.2. Obter Histórico de Versões

**Endpoint**: `GET /api/v1/projects/requirements/{requirement_id}/versions`

**Resposta Esperada**: `200 OK`
```json
[
  {
    "id": "990e8400-e29b-41d4-a716-446655440004",
    "requirement_id": "770e8400-e29b-41d4-a716-446655440002",
    "version": 1,
    "data": {
      "code": "REQ-001",
      "descricao": "Sistema deve permitir login de usuários",
      ...
    },
    "created_at": "2025-10-08T12:00:00"
  }
]
```

**💡 Use case**: Ver o que mudou entre versões

---

### 3.3. Obter Versão Específica Arquivada

**Endpoint**: `GET /api/v1/projects/requirements/{requirement_id}/versions/{version}`

**Path Parameters**:
- `requirement_id`: ID do requirement
- `version`: 1

**Resposta Esperada**: `200 OK` - Dados exatos da versão 1

---

## ✅ 4. Testes de Validação

### 4.1. ❌ Critérios de Aceitação Vazios (Erro)

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Request Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-BAD-01",
      "descricao": "Requirement sem critérios",
      "criterios_aceitacao": [],
      "prioridade": "must",
      "dependencias": []
    }
  ]
}
```

**Resposta Esperada**: `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "requirements", 0, "criterios_aceitacao"],
      "msg": "At least one acceptance criterion is required",
      "input": []
    }
  ]
}
```

---

### 4.2. ❌ Prioridade Inválida (Erro)

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Request Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-BAD-02",
      "descricao": "Prioridade errada",
      "criterios_aceitacao": ["Critério 1"],
      "prioridade": "HIGH",
      "dependencias": []
    }
  ]
}
```

**Resposta Esperada**: `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "requirements", 0, "prioridade"],
      "msg": "Input should be 'must', 'should', 'could' or 'wont'",
      "input": "HIGH"
    }
  ]
}
```

**✅ Prioridades válidas**: `must`, `should`, `could`, `wont`

---

### 4.3. ✅ Todas as Prioridades Válidas

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Request Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-MUST",
      "descricao": "Prioridade MUST (crítico)",
      "criterios_aceitacao": ["Essencial para o projeto"],
      "prioridade": "must",
      "dependencias": []
    },
    {
      "code": "REQ-SHOULD",
      "descricao": "Prioridade SHOULD (importante)",
      "criterios_aceitacao": ["Importante mas não crítico"],
      "prioridade": "should",
      "dependencias": []
    },
    {
      "code": "REQ-COULD",
      "descricao": "Prioridade COULD (desejável)",
      "criterios_aceitacao": ["Se houver tempo"],
      "prioridade": "could",
      "dependencias": []
    },
    {
      "code": "REQ-WONT",
      "descricao": "Prioridade WONT (não será implementado)",
      "criterios_aceitacao": ["Descartado nesta versão"],
      "prioridade": "wont",
      "dependencias": []
    }
  ]
}
```

**Resposta Esperada**: `200 OK` - Todos criados com sucesso

---

### 4.4. ⚠️ Requirement com Waiver (Warning)

**Endpoint**: `PUT /api/v1/projects/requirements/{requirement_id}`

**Request Body**:
```json
{
  "code": "REQ-001",
  "descricao": "Requirement com waiver",
  "criterios_aceitacao": ["Critério mínimo"],
  "prioridade": "could",
  "dependencias": [],
  "waiver_reason": "Decisão de negócio: prioridade rebaixada para próxima sprint"
}
```

**Resposta Esperada**: `200 OK`
```json
{
  "requirement": {...},
  "validation": {
    "valid": true,
    "errors": [],
    "validation_warnings": [
      "Only one acceptance criterion provided - consider adding more"
    ]
  }
}
```

**📝 Nota**: 
- `waiver_reason` é aceito e salvo
- Pode gerar warning (não bloqueia)
- Fica auditado no banco de dados

---

## 🔗 5. Testes de Dependências

### 5.1. ✅ Dependência Válida

**Passo 1**: Criar REQ-001 (sem dependências)
```json
{
  "requirements": [
    {
      "code": "REQ-001",
      "descricao": "Autenticação de usuários",
      "criterios_aceitacao": ["Login funcional"],
      "prioridade": "must",
      "dependencias": []
    }
  ]
}
```

**Passo 2**: Criar REQ-002 que depende de REQ-001
```json
{
  "requirements": [
    {
      "code": "REQ-002",
      "descricao": "Dashboard personalizado",
      "criterios_aceitacao": ["Exibe dados do usuário logado"],
      "prioridade": "should",
      "dependencias": ["REQ-001"]
    }
  ]
}
```

**Resposta Esperada**: `200 OK` ✅

---

### 5.2. ❌ Dependência Inexistente (Erro)

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Request Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-002",
      "descricao": "Requirement com dependência que não existe",
      "criterios_aceitacao": ["Critério 1"],
      "prioridade": "should",
      "dependencias": ["REQ-999"]
    }
  ]
}
```

**Resposta Esperada**: `422 Unprocessable Entity`
```json
{
  "detail": {
    "message": "Validation failed for one or more requirements",
    "validation_errors": [
      {
        "index": 0,
        "code": "REQ-002",
        "errors": ["Dependencies not found: REQ-999"]
      }
    ]
  }
}
```

---

### 5.3. ❌ Auto-Dependência (Erro)

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Request Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-001",
      "descricao": "Requirement que depende de si mesmo",
      "criterios_aceitacao": ["Critério 1"],
      "prioridade": "must",
      "dependencias": ["REQ-001"]
    }
  ]
}
```

**Resposta Esperada**: `422 Unprocessable Entity`
```json
{
  "detail": {
    "message": "Validation failed for one or more requirements",
    "validation_errors": [
      {
        "index": 0,
        "code": "REQ-001",
        "errors": ["Requirement cannot depend on itself: REQ-001"]
      }
    ]
  }
}
```

---

### 5.4. ✅ Dependências em Batch (Mesmo Request)

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Request Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-A",
      "descricao": "Base requirement",
      "criterios_aceitacao": ["Critério A"],
      "prioridade": "must",
      "dependencias": []
    },
    {
      "code": "REQ-B",
      "descricao": "Depende de REQ-A (mesmo batch)",
      "criterios_aceitacao": ["Critério B"],
      "prioridade": "must",
      "dependencias": ["REQ-A"]
    },
    {
      "code": "REQ-C",
      "descricao": "Depende de REQ-B (mesmo batch)",
      "criterios_aceitacao": ["Critério C"],
      "prioridade": "should",
      "dependencias": ["REQ-B"]
    }
  ]
}
```

**Resposta Esperada**: `200 OK` ✅

**📝 Nota**: Validação considera requirements do mesmo batch como disponíveis!

---

### 5.5. ✅ Múltiplas Dependências

**Endpoint**: `POST /api/v1/projects/{project_id}/requirements`

**Pré-requisito**: REQ-001 e REQ-002 já existem

**Request Body**:
```json
{
  "requirements": [
    {
      "code": "REQ-003",
      "descricao": "Requirement que depende de 2 outros",
      "criterios_aceitacao": [
        "Integra funcionalidades de REQ-001 e REQ-002",
        "Testa compatibilidade entre ambos"
      ],
      "prioridade": "must",
      "dependencias": ["REQ-001", "REQ-002"]
    }
  ]
}
```

**Resposta Esperada**: `200 OK` ✅

---

## ⚠️ 6. Cenários de Erro

### 6.1. ❌ Projeto Não Encontrado

**Endpoint**: `GET /api/v1/projects/{project_id}`

**Path Parameter**: `00000000-0000-0000-0000-000000000000`

**Resposta Esperada**: `404 Not Found`
```json
{
  "detail": "Project not found"
}
```

---

### 6.2. ❌ Requirement Não Encontrado

**Endpoint**: `GET /api/v1/projects/requirements/{requirement_id}/versions`

**Path Parameter**: `00000000-0000-0000-0000-000000000000`

**Resposta Esperada**: `404 Not Found`
```json
{
  "detail": "Requirement not found"
}
```

---

### 6.3. ❌ Bulk Insert em Projeto Inexistente

**Endpoint**: `POST /api/v1/projects/00000000-0000-0000-0000-000000000000/requirements`

**Request Body**: (qualquer requirement válido)

**Resposta Esperada**: `404 Not Found`
```json
{
  "detail": "Project not found"
}
```

---

### 6.4. ❌ Status de Projeto Inválido

**Endpoint**: `PATCH /api/v1/projects/{project_id}`

**Request Body**:
```json
{
  "status": "INVALID_STATUS"
}
```

**Resposta Esperada**: `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "status"],
      "msg": "Invalid status. Must be one of: ['DRAFT', 'REQS_REFINING', ...]"
    }
  ]
}
```

---

## 🎯 7. Fluxo Completo (Passo a Passo)

### Cenário: Criar projeto completo do zero

#### **Passo 1**: Criar Projeto
```json
POST /api/v1/projects
{
  "name": "Sistema de E-commerce"
}
```
**Salve o `project_id`**

---

#### **Passo 2**: Criar Requirements Iniciais
```json
POST /api/v1/projects/{project_id}/requirements
{
  "requirements": [
    {
      "code": "REQ-AUTH-01",
      "descricao": "Sistema de autenticação",
      "criterios_aceitacao": [
        "Login com email/senha",
        "Logout funcional",
        "Sessão expira em 24h"
      ],
      "prioridade": "must",
      "dependencias": [],
      "testabilidade": "Testes unitários + integração com mock de banco"
    },
    {
      "code": "REQ-CART-01",
      "descricao": "Carrinho de compras",
      "criterios_aceitacao": [
        "Adicionar produtos ao carrinho",
        "Remover produtos do carrinho",
        "Calcular total com impostos"
      ],
      "prioridade": "must",
      "dependencias": ["REQ-AUTH-01"],
      "testabilidade": "Testes E2E com Cypress"
    },
    {
      "code": "REQ-PAY-01",
      "descricao": "Processamento de pagamentos",
      "criterios_aceitacao": [
        "Integração com Stripe",
        "Suporte a cartão de crédito",
        "Confirmação de pagamento via email"
      ],
      "prioridade": "must",
      "dependencias": ["REQ-CART-01"],
      "testabilidade": "Mock de Stripe API em staging"
    },
    {
      "code": "REQ-NOTIF-01",
      "descricao": "Sistema de notificações",
      "criterios_aceitacao": [
        "Email de confirmação de pedido",
        "Notificação de envio"
      ],
      "prioridade": "should",
      "dependencias": ["REQ-PAY-01"]
    }
  ]
}
```
**Salve os IDs dos requirements**

---

#### **Passo 3**: Listar Requirements Criados
```
GET /api/v1/projects/{project_id}/requirements
```
**Verificar**: 4 requirements, todos com version=1

---

#### **Passo 4**: Atualizar Requirement (Refinar Critérios)
```json
PUT /api/v1/projects/requirements/{req_auth_id}
{
  "code": "REQ-AUTH-01",
  "descricao": "Sistema de autenticação com OAuth2",
  "criterios_aceitacao": [
    "Login com email/senha",
    "Login com Google OAuth2",
    "Login com Microsoft OAuth2",
    "Logout funcional",
    "Sessão expira em 24h",
    "Refresh token automático"
  ],
  "prioridade": "must",
  "dependencias": [],
  "testabilidade": "Testes unitários + integração com mock de banco + OAuth2 sandbox"
}
```
**Verificar**: version=2, validation_warnings presente

---

#### **Passo 5**: Ver Histórico de Versões
```
GET /api/v1/projects/requirements/{req_auth_id}/versions
```
**Verificar**: Versão 1 arquivada com dados originais

---

#### **Passo 6**: Adicionar Novo Requirement com Dependências
```json
POST /api/v1/projects/{project_id}/requirements
{
  "requirements": [
    {
      "code": "REQ-ADMIN-01",
      "descricao": "Painel administrativo",
      "criterios_aceitacao": [
        "Dashboard com métricas de vendas",
        "Gerenciamento de produtos",
        "Relatórios exportáveis em PDF"
      ],
      "prioridade": "should",
      "dependencias": ["REQ-AUTH-01", "REQ-PAY-01"]
    }
  ]
}
```

---

#### **Passo 7**: Adicionar Requirement de Baixa Prioridade
```json
POST /api/v1/projects/{project_id}/requirements
{
  "requirements": [
    {
      "code": "REQ-WISH-01",
      "descricao": "Lista de desejos",
      "criterios_aceitacao": [
        "Usuário pode salvar produtos favoritos",
        "Notificação quando produto entra em promoção"
      ],
      "prioridade": "could",
      "dependencias": ["REQ-AUTH-01"]
    }
  ]
}
```

---

#### **Passo 8**: Atualizar Status do Projeto
```json
PATCH /api/v1/projects/{project_id}
{
  "status": "REQS_READY"
}
```

---

#### **Passo 9**: Listar Todos os Requirements
```
GET /api/v1/projects/{project_id}/requirements
```
**Verificar**: 
- 6 requirements no total
- REQ-AUTH-01 em version=2
- Demais em version=1
- Dependências corretas

---

#### **Passo 10**: Rebaixar Prioridade com Waiver
```json
PUT /api/v1/projects/requirements/{req_wish_id}
{
  "code": "REQ-WISH-01",
  "descricao": "Lista de desejos",
  "criterios_aceitacao": [
    "Usuário pode salvar produtos favoritos"
  ],
  "prioridade": "wont",
  "dependencias": ["REQ-AUTH-01"],
  "waiver_reason": "Funcionalidade adiada para v2.0 por priorização de negócio"
}
```
**Verificar**: validation_warnings sobre waiver

---

## 📊 Resumo de Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/projects` | Criar projeto |
| GET | `/api/v1/projects` | Listar projetos |
| GET | `/api/v1/projects/{id}` | Obter projeto |
| PATCH | `/api/v1/projects/{id}` | Atualizar projeto |
| POST | `/api/v1/projects/{id}/requirements` | Bulk upsert requirements |
| GET | `/api/v1/projects/{id}/requirements` | Listar requirements |
| GET | `/api/v1/projects/{id}/requirements?version={n}` | Listar requirements em versão |
| PUT | `/api/v1/projects/requirements/{id}` | Atualizar requirement |
| GET | `/api/v1/projects/requirements/{id}/versions` | Histórico de versões |
| GET | `/api/v1/projects/requirements/{id}/versions/{n}` | Versão específica |

---

## 🎨 Dicas para Testar no Swagger

### 1. **Ordem Recomendada**:
   1. ✅ Criar projeto
   2. ✅ Criar requirements básicos
   3. ✅ Testar validações (erros 422)
   4. ✅ Atualizar requirement
   5. ✅ Ver histórico
   6. ✅ Testar dependências

### 2. **Copiar IDs**:
   - Sempre copie os IDs retornados
   - Use um bloco de notas para organizar
   - Exemplo:
     ```
     project_id: 550e8400-e29b-41d4-a716-446655440000
     req_auth_id: 770e8400-e29b-41d4-a716-446655440002
     req_cart_id: 880e8400-e29b-41d4-a716-446655440003
     ```

### 3. **Testar Erros Propositais**:
   - Use os exemplos de erro para ver as validações
   - Veja as mensagens retornadas
   - Confirme que retornam 422/404

### 4. **Explorar Swagger UI**:
   - **Schemas**: Veja modelos de dados completos
   - **Try it out**: Teste direto na interface
   - **Response**: Copie os exemplos retornados

### 5. **Alternar entre Abas**:
   - Abra múltiplas abas do Swagger
   - Uma para criar, outra para listar
   - Facilita comparar resultados

---

## 🔍 Validações Importantes

### ✅ **Sempre Válido**:
- `prioridade`: `must`, `should`, `could`, `wont`
- `criterios_aceitacao`: Array com >= 1 item
- `dependencias`: Array vazio ou com códigos existentes
- `code`: Único por projeto

### ❌ **Sempre Inválido**:
- `prioridade`: `HIGH`, `LOW`, `MEDIUM` (formato antigo)
- `criterios_aceitacao`: `[]` (vazio)
- `dependencias`: Códigos inexistentes
- `dependencias`: Auto-referência (ex: REQ-001 depende de REQ-001)

### ⚠️ **Gera Warning (Não Bloqueia)**:
- `testabilidade`: Ausente
- `waiver_reason`: Presente
- `criterios_aceitacao`: Apenas 1 item (sugere adicionar mais)
- `prioridade`: `wont`

---

## 📝 Checklist de Testes

Marque conforme for testando:

**Projetos**:
- [ ] Criar projeto simples
- [ ] Listar projetos
- [ ] Obter projeto por ID
- [ ] Atualizar status
- [ ] Projeto não encontrado (404)

**Requirements**:
- [ ] Bulk insert (2+ requirements)
- [ ] Requirement com testabilidade
- [ ] Requirement com todas as prioridades
- [ ] Listar requirements
- [ ] Dependências válidas
- [ ] Dependências em batch

**Versionamento**:
- [ ] Atualizar requirement (version bump)
- [ ] Ver histórico de versões
- [ ] Obter versão específica
- [ ] Listar por query parameter ?version=1

**Validações**:
- [ ] Critérios vazios → 422
- [ ] Prioridade inválida → 422
- [ ] Dependência inexistente → 422
- [ ] Auto-dependência → 422
- [ ] Waiver reason (aceito com warning)

**Fluxo Completo**:
- [ ] Criar projeto do zero
- [ ] Adicionar 4+ requirements
- [ ] Atualizar 1 requirement
- [ ] Verificar versionamento
- [ ] Adicionar dependências complexas
- [ ] Atualizar status do projeto

---

## 🚀 Pronto para Testar!

Acesse: **http://localhost:8000/docs**

Bons testes! 🎉
