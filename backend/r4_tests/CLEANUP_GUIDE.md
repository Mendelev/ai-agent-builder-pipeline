# 🧹 Scripts de Limpeza - R4 Test Cleanup

Scripts para limpar projetos de teste criados durante os testes do R4 Requirements Gateway.

---

## 📋 Scripts Disponíveis

| Script | Tipo | Segurança | Uso |
|--------|------|-----------|-----|
| `test_r4_cleanup.sh` | Seletivo | ✅ Seguro | Dia a dia |
| `test_r4_cleanup_all.sh` | Total | ⚠️ Perigoso | Reset completo |

---

## 1️⃣ test_r4_cleanup.sh - Limpeza Seletiva

### Descrição
Remove **apenas** projetos de teste identificados por padrões específicos no nome.

### Características
- ✅ **Seguro para produção** - Não afeta projetos reais
- ✅ Identificação inteligente por nome
- ✅ Resumo detalhado (deletados vs preservados)
- ✅ Opção de visualizar projetos restantes
- ✅ Sem confirmação necessária (é seguro)

### Uso
```bash
cd backend
./test_r4_cleanup.sh
```

### Padrões Reconhecidos como Teste

O script identifica e remove projetos com nomes contendo:
- `Test R4`
- `E-commerce Platform`
- `Mobile App MVP`
- `Legacy System Refactoring`
- `Idempotency Test Project`
- `Test E2E`
- `Test E-commerce`
- `Teste R4`

### Exemplo de Saída

```
╔════════════════════════════════════════════════════╗
║   R4 Requirements Gateway - Cleanup Script         ║
║   Remove all test projects from database          ║
╔════════════════════════════════════════════════════╗

Fetching all projects...
Found 10 total project(s)

Looking for test projects to delete...

Deleting test project:
  Name: Test R4 - Finalizar
  ID: 550e8400-e29b-41d4-a716-446655440000
  Status: REQS_READY
✓ Deleted successfully

Deleting test project:
  Name: E-commerce Platform
  ID: 660e8400-e29b-41d4-a716-446655440001
  Status: REQS_READY
✓ Deleted successfully

═══════════════════════════════════════════════════
Cleanup Summary
═══════════════════════════════════════════════════
Deleted: 7 test project(s)
Skipped: 3 non-test project(s)
Total: 10 project(s) processed

✓ Cleanup completed successfully

Show remaining projects? [y/N]: y

Remaining projects:
  - Sistema de Produção (DONE)
  - API Gateway Real (REQS_READY)
  - App Mobile Cliente (PLAN_READY)

Done!
```

---

## 2️⃣ test_r4_cleanup_all.sh - Limpeza Total

### Descrição
Remove **TODOS** os projetos do banco de dados, sem exceções.

### ⚠️ AVISOS IMPORTANTES
- ❌ **NÃO é seletivo** - deleta tudo
- ❌ **Ação irreversível** - não há backup automático
- ⚠️ Requer confirmação explícita (digite "yes")
- ⚠️ **Use apenas em desenvolvimento**

### Uso
```bash
cd backend
./test_r4_cleanup_all.sh
```

### Quando Usar
✅ **Casos adequados:**
- Reset completo do ambiente de desenvolvimento
- Preparar banco limpo para nova bateria de testes
- Demonstrações que requerem banco vazio
- Ambiente local/desenvolvimento

❌ **NÃO use:**
- Em produção
- Com dados reais/importantes
- Sem backup prévio

### Exemplo de Saída

```
╔════════════════════════════════════════════════════╗
║   ⚠️  WARNING: FULL DATABASE CLEANUP  ⚠️           ║
║   This will DELETE ALL projects!                  ║
╔════════════════════════════════════════════════════╗

Fetching all projects...
Found 10 project(s) to delete:

  • Test R4 - Finalizar (REQS_READY) - ID: abc-123
  • Sistema de Produção (DONE) - ID: def-456
  • E-commerce Platform (REQS_REFINING) - ID: ghi-789
  • API Gateway Real (REQS_READY) - ID: jkl-012
  ...

⚠️  This action cannot be undone! ⚠️

Are you ABSOLUTELY sure you want to delete ALL 10 projects? [yes/NO]: yes

Proceeding with deletion...

Deleting: Test R4 - Finalizar... ✓
Deleting: Sistema de Produção... ✓
Deleting: E-commerce Platform... ✓
...

═══════════════════════════════════════════════════
Cleanup Summary
═══════════════════════════════════════════════════
Successfully deleted: 10 project(s)
Total processed: 10 project(s)

✓ Database is now empty

Cleanup completed!
```

---

## 🔄 Workflow Recomendado

### Cenário 1: Limpeza Regular (Pós-Testes)

```bash
# 1. Executar testes
./test_r4_basic.sh
# ou
./test_r4_e2e.sh

# 2. Limpar apenas projetos de teste
./test_r4_cleanup.sh
```

### Cenário 2: Reset Completo do Ambiente

```bash
# 1. Backup (se necessário)
# ... faça backup do banco de dados ...

# 2. Limpar tudo
./test_r4_cleanup_all.sh
# Digite: yes

# 3. Verificar banco vazio
curl http://localhost:8000/api/v1/projects | jq 'length'
# Deve retornar: 0
```

### Cenário 3: Limpeza Automatizada em CI/CD

```bash
#!/bin/bash
# Script de CI para testes

# Limpar ambiente antes dos testes
./test_r4_cleanup_all.sh <<< "yes"

# Executar testes
./test_r4_e2e.sh

# Status do teste
if [ $? -eq 0 ]; then
    echo "✓ Testes passaram"
    # Limpar novamente após testes
    ./test_r4_cleanup_all.sh <<< "yes"
else
    echo "✗ Testes falharam"
    exit 1
fi
```

---

## 🛡️ Proteções de Segurança

### test_r4_cleanup.sh
- ✅ Lista branca de padrões de nome
- ✅ Não deleta projetos desconhecidos
- ✅ Resumo de ações antes de confirmar
- ✅ Sem confirmação (é seguro por design)

### test_r4_cleanup_all.sh
- ⚠️ Mostra lista completa antes de deletar
- ⚠️ Requer confirmação explícita "yes"
- ⚠️ "y" ou "Y" **NÃO funcionam** (deve ser "yes")
- ⚠️ Cancela se não digitar exatamente "yes"

---

## 🔧 Troubleshooting

### Erro: "Connection refused"
**Problema:** Backend não está rodando

**Solução:**
```bash
cd backend
uvicorn main:app --reload
```

### Erro: "Failed to fetch projects"
**Problema:** Backend não responde ou URL incorreta

**Solução:**
```bash
# Verificar se backend está rodando
curl http://localhost:8000/api/v1/projects

# Se necessário, ajustar BASE_URL no script
# Edite o script e mude a linha:
BASE_URL="http://localhost:8000/api/v1"
```

### Script não deleta nada
**Problema:** Nenhum projeto corresponde aos padrões

**Solução:**
```bash
# Verificar projetos existentes
curl http://localhost:8000/api/v1/projects | jq -r '.[] | .name'

# Se quiser deletar tudo, use:
./test_r4_cleanup_all.sh
```

### Permissão negada
**Problema:** Script não é executável

**Solução:**
```bash
chmod +x test_r4_cleanup.sh
chmod +x test_r4_cleanup_all.sh
```

---

## 📊 Comparação dos Scripts

| Aspecto | test_r4_cleanup.sh | test_r4_cleanup_all.sh |
|---------|-------------------|------------------------|
| **Segurança** | ✅ Alta | ⚠️ Baixa |
| **Seletividade** | ✅ Sim (por padrão) | ❌ Não (tudo) |
| **Confirmação** | Não requer | Requer "yes" |
| **Uso em produção** | ✅ Seguro | ❌ Perigoso |
| **Velocidade** | Média | Rápida |
| **Resumo** | Detalhado | Completo |
| **Visualização** | Opcional | Mostra antes |

---

## 💡 Dicas

### 1. Sempre prefira test_r4_cleanup.sh
```bash
# Seguro e eficiente
./test_r4_cleanup.sh
```

### 2. Verifique antes de deletar tudo
```bash
# Ver o que será deletado
curl http://localhost:8000/api/v1/projects | jq -r '.[] | .name'

# Só então delete
./test_r4_cleanup_all.sh
```

### 3. Adicione seus padrões de teste
Edite `test_r4_cleanup.sh` e adicione na seção:
```bash
TEST_PROJECT_PATTERNS=(
    "Test R4"
    "Seu Padrão Aqui"  # ← Adicione aqui
    "Outro Padrão"      # ← E aqui
)
```

### 4. Integre com seus testes
```bash
# No final do seu script de teste
./test_r4_cleanup.sh > /dev/null 2>&1
```

---

## 📝 Notas

- Scripts funcionam via API REST (não manipulam banco diretamente)
- Requerem `jq` instalado para parsing JSON
- Requerem `curl` para requisições HTTP
- Backend deve estar rodando em `http://localhost:8000`
- Deletar projetos também deleta requirements e audit records (CASCADE)

---

**Criado para:** R4 Requirements Gateway Testing  
**Versão:** 1.0  
**Última atualização:** Outubro 2024
