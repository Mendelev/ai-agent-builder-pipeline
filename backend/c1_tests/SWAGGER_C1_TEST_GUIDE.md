# 🔐 Guia de Testes - Módulo C1 (Code Repository Connect)

**Versão:** 1.0  
**Data:** Outubro 2024  
**Módulo:** CODE.C1 - Conectar Git com Token Cifrado

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Acesso ao Swagger](#acesso-ao-swagger)
3. [Pré-requisitos](#pré-requisitos)
4. [Endpoints Disponíveis](#endpoints-disponíveis)
5. [Cenários de Teste](#cenários-de-teste)
6. [Segurança e Criptografia](#segurança-e-criptografia)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O módulo **C1 (Code Repository Connect)** permite conectar repositórios Git ao sistema com:

- ✅ **Token Encryption**: AES-GCM envelope encryption
- ✅ **Size Validation**: Rejeita repos >100MB
- ✅ **Security**: Tokens nunca expostos em logs ou respostas
- ✅ **Sandbox Clone**: Clone isolado por projeto
- ✅ **Status Tracking**: Acompanhamento de clone em tempo real

---

## 🌐 Acesso ao Swagger

### 1. Iniciar Backend

```bash
cd backend
uvicorn main:app --reload
```

### 2. Acessar Swagger UI

Abra no navegador: **http://localhost:8000/docs**

Você verá os endpoints organizados por tags:
- **projects**: Gerenciamento de projetos
- **code-repositories**: Conexão e gestão de repositórios

---

## 📋 Pré-requisitos

### 1. Criar Projeto

Antes de conectar um repositório, você precisa de um projeto existente.

**Endpoint**: `POST /api/v1/projects`

**Request Body**:
```json
{
  "name": "Meu Projeto de Teste"
}
```

**Resposta Esperada**: `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Meu Projeto de Teste",
  "status": "DRAFT",
  "created_at": "2024-10-23T10:30:00"
}
```

**⚠️ Importante**: Guarde o `id` do projeto para os próximos passos.

---

## 📍 Endpoints Disponíveis

### 1. POST /api/v1/code/connect
**Conectar Repositório Git**

### 2. GET /api/v1/code/repos/{repo_id}
**Obter Detalhes do Repositório**

### 3. GET /api/v1/code/repos/{repo_id}/status
**Verificar Status de Clone**

### 4. GET /api/v1/code/projects/{project_id}/repos
**Listar Todos os Repositórios do Projeto**

---

## 🧪 Cenários de Teste

### Cenário 1: Conectar Repositório Pequeno (Happy Path)

#### Passo 1: Criar Projeto

```json
POST /api/v1/projects
{
  "name": "Test C1 - Small Repo"
}
```

Guarde o `project_id` retornado.

#### Passo 2: Conectar Repositório

```json
POST /api/v1/code/connect
{
  "git_url": "https://github.com/octocat/Hello-World.git",
  "access_token": "ghp_your_github_token_here",
  "project_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Resposta Esperada**: `201 Created`
```json
{
  "id": "660e9500-f30c-52e5-b827-557766551111",
  "git_url": "https://github.com/octocat/Hello-World.git",
  "connected": true,
  "task_id": "770ea600-g41d-63f6-c938-668877662222",
  "repository_size_mb": 0.5,
  "clone_status": "PENDING",
  "created_at": "2024-10-23T10:35:00"
}
```

**✅ Verificações**:
- `connected: true`
- `clone_status: "PENDING"` ou `"CLONING"`
- **Token NÃO aparece na resposta** (segurança!)

#### Passo 3: Verificar Status do Clone

```json
GET /api/v1/code/repos/{repo_id}/status
```

**Resposta**:
```json
{
  "repo_id": "660e9500-f30c-52e5-b827-557766551111",
  "clone_status": "COMPLETED",
  "repository_size_mb": 0.48,
  "sandbox_path": "/tmp/repos/project-550e8400/repo-660e9500",
  "progress_message": "Repository successfully cloned",
  "error_message": null
}
```

**Status Possíveis**:
- `PENDING`: Aguardando início
- `CLONING`: Clone em andamento
- `COMPLETED`: Clone concluído
- `FAILED`: Erro no clone
- `CLEANING`: Limpeza em andamento
- `CLEANED`: Removido

#### Passo 4: Obter Detalhes do Repositório

```json
GET /api/v1/code/repos/{repo_id}
```

**Resposta**:
```json
{
  "id": "660e9500-f30c-52e5-b827-557766551111",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "git_url": "https://github.com/octocat/Hello-World.git",
  "repository_size_mb": 0.48,
  "clone_status": "COMPLETED",
  "sandbox_path": "/tmp/repos/project-550e8400/repo-660e9500",
  "created_at": "2024-10-23T10:35:00",
  "updated_at": "2024-10-23T10:35:30"
}
```

**🔒 Segurança**:
- ✅ `access_token` NÃO está na resposta
- ✅ `token_ciphertext` NÃO está na resposta
- ✅ Apenas informações públicas são retornadas

---

### Cenário 2: Repositório Muito Grande (Rejeitado)

#### Objetivo
Testar validação de tamanho (limite: 100MB)

#### Passo 1: Criar Projeto

```json
POST /api/v1/projects
{
  "name": "Test C1 - Large Repo"
}
```

#### Passo 2: Tentar Conectar Repositório Grande

```json
POST /api/v1/code/connect
{
  "git_url": "https://github.com/torvalds/linux.git",
  "access_token": "ghp_your_token",
  "project_id": "{project_id}"
}
```

**Resposta Esperada**: `413 Payload Too Large`
```json
{
  "detail": {
    "error": "repository_too_large",
    "message": "Repository size 3500.0MB exceeds limit of 100MB",
    "estimated_size_mb": 3500.0,
    "limit_mb": 100
  }
}
```

**✅ Validações**:
- HTTP 413 (Payload Too Large)
- `error: "repository_too_large"`
- Tamanho estimado fornecido
- Limite claramente indicado

**🧹 Cleanup**:
O sistema automaticamente limpa workspaces temporários se o repo for rejeitado.

---

### Cenário 3: URL de Git Inválida

#### Objetivo
Testar validação de formato de URL

#### Passo 1: Tentar URL Inválida

```json
POST /api/v1/code/connect
{
  "git_url": "not-a-valid-url",
  "access_token": "ghp_your_token",
  "project_id": "{project_id}"
}
```

**Resposta Esperada**: `422 Validation Error`
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "git_url"],
      "msg": "Invalid Git repository URL format",
      "input": "not-a-valid-url"
    }
  ]
}
```

**URLs Válidas**:
- ✅ `https://github.com/user/repo.git`
- ✅ `https://gitlab.com/user/repo.git`
- ✅ `https://bitbucket.org/user/repo.git`
- ❌ `http://github.com/...` (HTTPS obrigatório)
- ❌ `github.com/user/repo` (protocolo obrigatório)

---

### Cenário 4: Múltiplos Repositórios por Projeto

#### Objetivo
Testar arquitetura multi-repo (microservices)

#### Passo 1: Criar Projeto Microservices

```json
POST /api/v1/projects
{
  "name": "Microservices Project"
}
```

#### Passo 2: Conectar Frontend

```json
POST /api/v1/code/connect
{
  "git_url": "https://github.com/myorg/frontend.git",
  "access_token": "ghp_token_1",
  "project_id": "{project_id}"
}
```

#### Passo 3: Conectar Backend

```json
POST /api/v1/code/connect
{
  "git_url": "https://github.com/myorg/backend.git",
  "access_token": "ghp_token_2",
  "project_id": "{project_id}"
}
```

#### Passo 4: Conectar Infrastructure

```json
POST /api/v1/code/connect
{
  "git_url": "https://github.com/myorg/infra.git",
  "access_token": "ghp_token_3",
  "project_id": "{project_id}"
}
```

#### Passo 5: Listar Todos os Repositórios

```json
GET /api/v1/code/projects/{project_id}/repos
```

**Resposta**:
```json
[
  {
    "id": "repo-id-1",
    "git_url": "https://github.com/myorg/frontend.git",
    "clone_status": "COMPLETED",
    ...
  },
  {
    "id": "repo-id-2",
    "git_url": "https://github.com/myorg/backend.git",
    "clone_status": "COMPLETED",
    ...
  },
  {
    "id": "repo-id-3",
    "git_url": "https://github.com/myorg/infra.git",
    "clone_status": "PENDING",
    ...
  }
]
```

**✅ Verificações**:
- Múltiplos repos para mesmo projeto
- Cada repo tem seu próprio `id` e `task_id`
- Tokens são criptografados independentemente
- Sandboxes separados por repositório

---

## 🔒 Segurança e Criptografia

### 🔐 Envelope Encryption (AES-GCM)

#### Como Funciona

```
1. User envia:          access_token (plaintext)
                             ↓
2. Backend gera:        Data Encryption Key (DEK) aleatória
                             ↓
3. Criptografa token:   AES-GCM(DEK, plaintext_token) = ciphertext
                             ↓
4. Criptografa DEK:     Master Key (KMS) + DEK = encrypted_DEK
                             ↓
5. Salva no DB:         token_ciphertext = nonce + ciphertext + encrypted_DEK
                        token_kid = key-{uuid}
```

#### O Que é Armazenado

**Tabela `code_repos`**:
```sql
| Column            | Valor Exemplo                          |
|-------------------|----------------------------------------|
| id                | 660e9500-f30c-52e5-b827-557766551111  |
| project_id        | 550e8400-e29b-41d4-a716-446655440000  |
| git_url           | https://github.com/user/repo.git      |
| token_ciphertext  | 0x89AB...CD (bytes cifrados)          |
| token_kid         | key-a1b2c3d4e5f6                      |
| repository_size_mb| 2.5                                    |
| clone_status      | COMPLETED                              |
```

**🔒 Garantias de Segurança**:
- ✅ Token NUNCA armazenado em plaintext
- ✅ Token NUNCA retornado em APIs
- ✅ Token NUNCA aparece em logs
- ✅ DEK única por token (não reutilização)
- ✅ Nonce único por criptografia (replay protection)

### 🛡️ Security Checklist

Ao testar, verifique:

```bash
# 1. Token não está na resposta de conexão
curl -X POST .../connect -d {...} | grep "ghp_" 
# Deve retornar vazio

# 2. Token não está em GET repository
curl -X GET .../repos/{id} | grep "ghp_"
# Deve retornar vazio

# 3. Token não está em logs (verificar backend logs)
tail -f backend.log | grep "ghp_"
# Deve mostrar apenas versões mascaradas: "ghp_***...***"
```

---

## 🐛 Troubleshooting

### Erro: "Repository not found" após conexão

**Causa**: Clone ainda em andamento (assíncrono)

**Solução**:
```json
// Verificar status do clone
GET /api/v1/code/repos/{repo_id}/status

// Se CLONING, aguardar alguns segundos
// Se FAILED, verificar logs do backend
```

---

### Erro: "Invalid Git credentials" (401)

**Causa**: Token inválido ou sem permissões

**Solução**:
1. Verificar se token tem escopo `repo` no GitHub
2. Testar token manualmente:
```bash
curl -H "Authorization: token ghp_your_token" \
  https://api.github.com/user
```

---

### Erro: "Repository size check timeout"

**Causa**: `git ls-remote` muito lento

**Solução**:
- Aumentar `GIT_CLONE_TIMEOUT` no `.env`
- Usar repo com melhor conectividade

---

### Erro: HTTP 500 "Encryption failed"

**Causa**: `MASTER_ENCRYPTION_KEY` não configurada

**Solução**:
```bash
# Gerar chave mestra (base64)
python3 -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"

# Adicionar ao .env
MASTER_ENCRYPTION_KEY=<chave_gerada>

# Reiniciar backend
```

---

## 📊 Resumo de Códigos HTTP

| Código | Significado | Quando Ocorre |
|--------|-------------|---------------|
| 201 | Created | Repositório conectado com sucesso |
| 200 | OK | GET bem-sucedido |
| 400 | Bad Request | Projeto não existe ou dados inválidos |
| 401 | Unauthorized | Credenciais Git inválidas |
| 404 | Not Found | Repositório não encontrado |
| 413 | Payload Too Large | Repositório excede 100MB |
| 422 | Validation Error | URL inválida, token vazio, etc |
| 500 | Internal Error | Erro de criptografia ou banco |

---

## 🎓 Boas Práticas

### ✅ DO's

- ✅ Sempre use HTTPS para git_url
- ✅ Use tokens com permissões mínimas (read-only se possível)
- ✅ Teste size validation antes de repos grandes
- ✅ Monitore clone_status para repos grandes
- ✅ Use correlation_id para rastreamento de logs

### ❌ DON'Ts

- ❌ Não commitar tokens em código
- ❌ Não logar tokens em plaintext
- ❌ Não reutilizar tokens entre ambientes
- ❌ Não ignorar erros 413 (size limit)
- ❌ Não expor token_ciphertext em APIs customizadas

---

## 📚 Documentação Adicional

- **Encryption Security**: Ver `ENCRYPTION_SECURITY.md`
- **Size Validation**: Ver `SIZE_VALIDATION.md`
- **Sandbox Cleanup**: Ver `SANDBOX_CLEANUP.md`
- **Testes Automatizados**: Ver `README.md`

---

**✨ Fim do Guia de Testes C1 ✨**
