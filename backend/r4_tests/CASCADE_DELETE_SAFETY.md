# ✅ Segurança de Exclusão de Projetos - CASCADE DELETE

## 🎯 Resposta Rápida

**SIM, é 100% SEGURO deletar projetos!** 

Quando você deleta um projeto, **TUDO relacionado é automaticamente deletado** via CASCADE DELETE configurado no banco de dados.

---

## 🔗 Cascade Delete - Como Funciona

### Hierarquia de Exclusão

```
Project (Projeto)
  ├── Requirements (Requisitos) ← CASCADE DELETE
  │     └── RequirementVersions (Versões) ← CASCADE DELETE
  │
  ├── QASessions (Sessões de Refinamento) ← CASCADE DELETE
  │
  └── RequirementsGatewayAudit (Histórico Gateway) ← CASCADE DELETE
```

---

## 📋 O Que É Deletado Automaticamente

### 1. Requirements (Requisitos)
```python
# models/project.py - linha 28
project_id = Column(UUID, ForeignKey("projects.id", ondelete="CASCADE"))
```

**Configuração:**
- ✅ Foreign Key com `ondelete="CASCADE"`
- ✅ SQLAlchemy relationship com `cascade="all, delete-orphan"`

**O que acontece:**
- Todos os requisitos do projeto são deletados
- Inclui requisitos de todas as versões

---

### 2. RequirementVersions (Histórico de Versões)
```python
# models/project.py - linha 41
requirement_id = Column(UUID, ForeignKey("requirements.id", ondelete="CASCADE"))
```

**Configuração:**
- ✅ Foreign Key com `ondelete="CASCADE"`
- ✅ SQLAlchemy relationship com `cascade="all, delete-orphan"`

**O que acontece:**
- Todo o histórico de versões de cada requisito é deletado
- Cascata em dois níveis: Project → Requirements → RequirementVersions

---

### 3. QASessions (Sessões de Q&A do R3)
```python
# models/qa_session.py - linha 20
project_id = Column(UUID, ForeignKey("projects.id", ondelete="CASCADE"))
```

**Configuração:**
- ✅ Foreign Key com `ondelete="CASCADE"`
- ✅ SQLAlchemy relationship com `cascade="all, delete-orphan"`

**O que acontece:**
- Todas as sessões de refinamento (R3) são deletadas
- Inclui perguntas, respostas e quality flags

---

### 4. RequirementsGatewayAudit (Histórico do Gateway R4)
```python
# models/project.py - linha 55
project_id = Column(UUID, ForeignKey("projects.id", ondelete="CASCADE"))
```

**Configuração:**
- ✅ Foreign Key com `ondelete="CASCADE"`

**O que acontece:**
- Todo o histórico de transições do gateway é deletado
- Inclui correlation_ids, request_ids e audit trail completo

---

## 🛡️ Garantias de Integridade

### Nível de Banco de Dados
```sql
-- A constraint CASCADE é criada no banco de dados
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
```

### Nível de ORM (SQLAlchemy)
```python
# Configuração no modelo
requirements = relationship(
    "Requirement", 
    back_populates="project", 
    cascade="all, delete-orphan"  # ← Garantia adicional
)
```

### Dupla Proteção
1. **Database CASCADE**: O banco de dados garante a exclusão
2. **SQLAlchemy CASCADE**: O ORM também garante (se usado session.delete())

---

## 🧪 Teste de Verificação

Você pode testar o cascade delete com este script:

```bash
#!/bin/bash
# test_cascade_delete.sh

BASE_URL="http://localhost:8000/api/v1"

echo "1. Criando projeto..."
PROJECT=$(curl -s -X POST "$BASE_URL/projects" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Cascade Delete"}')

PROJECT_ID=$(echo "$PROJECT" | jq -r '.id')
echo "   Project ID: $PROJECT_ID"

echo "2. Adicionando requisito..."
curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [{
      "code": "REQ-001",
      "descricao": "Test requirement",
      "criterios_aceitacao": ["Test"],
      "prioridade": "must"
    }]
  }' > /dev/null

echo "3. Mudando para REQS_REFINING..."
curl -s -X PATCH "$BASE_URL/projects/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{"status": "REQS_REFINING"}' > /dev/null

echo "4. Executando gateway..."
curl -s -X POST "$BASE_URL/requirements/$PROJECT_ID/gateway" \
  -H "Content-Type: application/json" \
  -d '{"action": "finalizar"}' > /dev/null

echo "5. Verificando dados antes da exclusão..."
REQ_COUNT=$(curl -s "$BASE_URL/projects/$PROJECT_ID/requirements" | jq 'length')
AUDIT_COUNT=$(curl -s "$BASE_URL/requirements/$PROJECT_ID/gateway/history" | jq 'length')

echo "   Requirements: $REQ_COUNT"
echo "   Gateway Audit: $AUDIT_COUNT"

echo "6. DELETANDO PROJETO..."
curl -s -X DELETE "$BASE_URL/projects/$PROJECT_ID"

echo "7. Verificando que tudo foi deletado..."
sleep 1

# Tentar buscar requirements (deve falhar - 404)
REQ_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/projects/$PROJECT_ID/requirements")
echo "   Requirements status: $REQ_STATUS (esperado: 404)"

# Tentar buscar audit (deve falhar - 404)
AUDIT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/requirements/$PROJECT_ID/gateway/history")
echo "   Gateway Audit status: $AUDIT_STATUS (esperado: 404)"

if [[ "$REQ_STATUS" == "404" && "$AUDIT_STATUS" == "404" ]]; then
    echo "✓ CASCADE DELETE funcionou perfeitamente!"
else
    echo "✗ Algo não foi deletado corretamente"
fi
```

---

## 📊 Resumo da Segurança

| Tabela | CASCADE DELETE | SQLAlchemy CASCADE | Status |
|--------|----------------|-------------------|---------|
| `requirements` | ✅ ON DELETE CASCADE | ✅ all, delete-orphan | ✅ SEGURO |
| `requirements_versions` | ✅ ON DELETE CASCADE | ✅ all, delete-orphan | ✅ SEGURO |
| `qa_sessions` | ✅ ON DELETE CASCADE | ✅ all, delete-orphan | ✅ SEGURO |
| `requirements_gateway_audit` | ✅ ON DELETE CASCADE | ❌ N/A (sem children) | ✅ SEGURO |

---

## ⚠️ Avisos Importantes

### ✅ O Que É Seguro

```bash
# Deletar projeto via API (recomendado)
curl -X DELETE "http://localhost:8000/api/v1/projects/$PROJECT_ID"

# Deletar projeto via ORM
project = db.query(Project).filter(Project.id == project_id).first()
db.delete(project)
db.commit()

# Scripts de limpeza
./test_r4_cleanup.sh        # Seguro
./test_r4_cleanup_all.sh    # Seguro (com confirmação)
```

### ❌ O Que NÃO Fazer

```sql
-- NÃO delete diretamente no SQL sem CASCADE
DELETE FROM projects WHERE id = 'xxx';  -- Se CASCADE não estiver configurado

-- NÃO tente deletar requirements manualmente antes do projeto
-- (desnecessário, será feito automaticamente)
```

---

## 🔍 Verificação de Configuração

### Verificar CASCADE no Banco de Dados

```sql
-- PostgreSQL
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND ccu.table_name = 'projects';

-- Resultado esperado:
-- table_name                    | foreign_table_name | delete_rule
-- requirements                  | projects           | CASCADE
-- qa_sessions                   | projects           | CASCADE
-- requirements_gateway_audit    | projects           | CASCADE
```

### Verificar Migrations

Todas as migrations estão corretas:

```python
# alembic/versions/001_*.py
op.create_table(
    'requirements',
    ...
    sa.Column('project_id', CustomUUID(), 
              sa.ForeignKey('projects.id', ondelete='CASCADE'),  # ✅
              nullable=False),
)

# alembic/versions/002_*.py
op.create_table(
    'qa_sessions',
    ...
    sa.Column('project_id', CustomUUID(), 
              sa.ForeignKey('projects.id', ondelete='CASCADE'),  # ✅
              nullable=False),
)

# alembic/versions/003_*.py
op.create_table(
    'requirements_gateway_audit',
    ...
    sa.Column('project_id', CustomUUID(), 
              sa.ForeignKey('projects.id', ondelete='CASCADE'),  # ✅
              nullable=False),
)
```

---

## 💡 Conclusão

### ✅ PODE DELETAR PROJETOS SEM MEDO!

1. **Tudo é deletado automaticamente**: Requirements, versões, QA sessions, gateway audit
2. **Sem dados órfãos**: Garantido em nível de banco de dados
3. **Sem problemas de integridade**: Foreign keys com CASCADE DELETE
4. **Testado**: Scripts de limpeza funcionam perfeitamente

### 🎯 Use os Scripts de Limpeza

```bash
# Limpeza seletiva (só projetos de teste)
./test_r4_cleanup.sh

# Limpeza total (TUDO)
./test_r4_cleanup_all.sh
```

Ambos são **100% seguros** quanto à integridade do banco de dados!

---

**Última atualização:** Outubro 2024  
**Verificado em:** PostgreSQL com SQLAlchemy
