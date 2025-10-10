# 🔄 R3 - Requirements Refinement Tests

Testes e documentação do módulo R3 (Requirements Refinement).

## 📁 Arquivos Disponíveis

### Scripts de Teste

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `test_r3_curl.sh` | Shell | Testes com curl (versão completa) |
| `test_r3_curl_correct.sh` | Shell | Testes com curl (versão corrigida) |
| `test_r3_simplified.sh` | Shell | Testes simplificados |
| `test_r3_example.py` | Python | Exemplos de uso em Python |
| `test_r3_direct.py` | Python | Testes diretos via API |
| `test_r3_e2e.py` | Python | Testes end-to-end |

### Documentação

| Arquivo | Descrição |
|---------|-----------|
| `SWAGGER_R3_TEST_GUIDE.md` | Guia completo de testes via Swagger UI |

## 🚀 Como Usar

### Opção 1: Testes Shell (Rápido)

```bash
# Testes simplificados
./test_r3_simplified.sh

# Testes completos com curl
./test_r3_curl_correct.sh
```

### Opção 2: Testes Python

```bash
# Exemplo de uso
python3 test_r3_example.py

# Testes end-to-end
python3 test_r3_e2e.py

# Testes diretos
python3 test_r3_direct.py
```

### Opção 3: Testes via Swagger

1. Acesse: http://localhost:8000/docs
2. Siga o guia: `SWAGGER_R3_TEST_GUIDE.md`

## 📋 Pré-requisitos

- Backend rodando: `cd .. && uvicorn main:app --reload`
- Banco de dados migrado: `cd .. && alembic upgrade head`
- Python 3.8+ (para testes Python)
- curl e jq (para testes shell)

## 🎯 O Que é o R3?

O **Requirements Refinement (R3)** é o módulo responsável por:

- ✅ Analisar requisitos para ambiguidades
- ✅ Gerar perguntas de clarificação
- ✅ Processar respostas e refinar requisitos
- ✅ Incrementar versões de requisitos
- ✅ Detectar problemas de testabilidade

### Fluxo do R3

```
1. Criar Projeto
   ↓
2. Adicionar Requisitos
   ↓
3. POST /refine (sem respostas)
   → Gera perguntas
   ↓
4. POST /refine (com respostas)
   → Refina requisitos
   → Incrementa versões
   ↓
5. Repetir até qualidade OK
```

## 📊 Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/qa-sessions/refine` | POST | Refinar requisitos (com/sem respostas) |
| `/api/v1/projects/{id}` | GET | Obter projeto |
| `/api/v1/projects/{id}/requirements` | GET | Listar requisitos |

## 🧪 Exemplo de Teste Rápido

```bash
# 1. Voltar para o diretório backend
cd ..

# 2. Criar projeto
PROJECT_ID=$(curl -s -X POST "http://localhost:8000/api/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test R3"}' | jq -r '.id')

# 3. Adicionar requisito
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [{
      "code": "REQ-001",
      "descricao": "Sistema deve ser rápido",
      "criterios_aceitacao": ["Deve ser rápido"],
      "prioridade": "must"
    }]
  }'

# 4. Refinar
curl -X POST "http://localhost:8000/api/v1/qa-sessions/refine" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\":\"$PROJECT_ID\"}" | jq '.'
```

## 📚 Documentação Completa

Veja `SWAGGER_R3_TEST_GUIDE.md` para:
- Exemplos detalhados de cada endpoint
- Cenários de teste passo-a-passo
- Tratamento de erros
- Boas práticas

## 🔗 Links Relacionados

- **R4 Tests:** `../r4_tests/` - Gateway de decisão após refinamento
- **API Routes:** `../app/api/routes/qa_sessions.py`
- **Service:** `../app/services/analyst_service.py`

---

**Versão:** 1.0  
**Última atualização:** Outubro 2024
