# AI Agent Builder Pipeline

API backend construída com FastAPI para gerenciamento de projetos e requisitos com versionamento.

## 📋 Tecnologias

- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para Python
- **Alembic** - Ferramenta de migração de banco de dados
- **PostgreSQL** - Banco de dados relacional
- **Pydantic** - Validação de dados e configuração
- **Uvicorn** - Servidor ASGI

## 🚀 Setup Rápido

### Opção 1: Script Automatizado (Recomendado)

```bash
cd backend
chmod +x setup.sh
./setup.sh
```

### Opção 2: Setup Manual

#### 1. Criar Ambiente Virtual

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # No Linux/Mac
# ou
venv\Scripts\activate  # No Windows
```

#### 2. Instalar Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

## 🗄️ Configuração do Banco de Dados

### 1. Instalar PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

### 2. Criar Banco de Dados

```bash
# Conectar ao PostgreSQL
sudo -u postgres psql

# Criar usuário e banco
CREATE USER user WITH PASSWORD 'password';
CREATE DATABASE ai_agent_builder OWNER user;
GRANT ALL PRIVILEGES ON DATABASE ai_agent_builder TO user;
\q
```

### 3. Atualizar .env

Edite o arquivo `.env` com suas credenciais:

```env
DATABASE_URL="postgresql://user:password@localhost:5432/ai_agent_builder"
```

## 🔄 Executar Migrações

```bash
# Aplicar todas as migrações
alembic upgrade head

# Criar nova migração (se necessário)
alembic revision --autogenerate -m "descrição da mudança"

# Reverter última migração
alembic downgrade -1
```

## ▶️ Executar a Aplicação

### Modo Desenvolvimento (com reload automático)

```bash
python main.py
# ou
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Modo Produção

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 Documentação da API

Após iniciar o servidor, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🏗️ Estrutura do Projeto

```
backend/
├── alembic/                 # Migrações do banco de dados
│   ├── versions/           # Scripts de migração
│   └── env.py             # Configuração do Alembic
├── app/
│   ├── api/
│   │   └── routes/        # Endpoints da API
│   │       └── projects.py
│   ├── core/              # Configurações centrais
│   │   ├── config.py      # Variáveis de ambiente
│   │   ├── database.py    # Conexão com banco
│   │   └── logging_config.py
│   ├── models/            # Modelos SQLAlchemy
│   │   └── project.py
│   ├── schemas/           # Schemas Pydantic
│   │   └── project.py
│   └── services/          # Lógica de negócio
│       └── requirement_service.py
├── tests/                 # Testes
│   └── test_projects.py
├── .env.example           # Template de variáveis de ambiente
├── .env                   # Suas configurações (não commitado)
├── alembic.ini           # Configuração do Alembic
├── main.py               # Ponto de entrada da aplicação
├── requirements.txt      # Dependências Python
└── setup.sh             # Script de setup automatizado
```

## 🔧 Endpoints Principais

### Projects

- `POST /api/v1/projects` - Criar projeto
- `GET /api/v1/projects` - Listar projetos
- `GET /api/v1/projects/{id}` - Obter projeto
- `PUT /api/v1/projects/{id}` - Atualizar projeto
- `DELETE /api/v1/projects/{id}` - Deletar projeto

### Requirements

- `POST /api/v1/projects/{id}/requirements/bulk` - Upsert em lote de requisitos
- `GET /api/v1/projects/{id}/requirements` - Listar requisitos
- `GET /api/v1/projects/{id}/requirements/{code}/versions` - Histórico de versões

## 🧪 Executar Testes

```bash
pytest
# ou com coverage
pytest --cov=app tests/
```

## � Atualizar Dependências

Existem duas opções para atualizar as versões das bibliotecas no `requirements.txt`:

### Opção 1: Script Python (Recomendado)

```bash
# Ver o que seria atualizado (dry-run)
python update_requirements.py --dry-run

# Atualizar o arquivo
python update_requirements.py

# Especificar arquivo diferente
python update_requirements.py -f requirements-dev.txt
```

### Opção 2: Script Bash com pip-tools

```bash
./update_requirements_simple.sh
```

Após atualizar o `requirements.txt`, instale as novas versões:

```bash
pip install -r requirements.txt --upgrade
```

## �🔍 Troubleshooting

### Erro de conexão com PostgreSQL

1. Verifique se o PostgreSQL está rodando:
```bash
sudo systemctl status postgresql
```

2. Teste a conexão:
```bash
psql -U user -d ai_agent_builder -h localhost
```

### Erro de importação de módulos

Certifique-se de estar com o ambiente virtual ativado:
```bash
source venv/bin/activate
```

### Alembic não encontra modelos

Verifique se o arquivo `alembic/env.py` está importando os modelos corretamente.

## 📝 Variáveis de Ambiente Disponíveis

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `APP_NAME` | Nome da aplicação | "AI Agent Builder Pipeline" |
| `APP_VERSION` | Versão da API | "1.0.0" |
| `DEBUG` | Modo debug | False |
| `DATABASE_URL` | URL de conexão PostgreSQL | - |
| `HOST` | Host do servidor | "0.0.0.0" |
| `PORT` | Porta do servidor | 8000 |
| `ALLOWED_ORIGINS` | CORS origins permitidos | "*" |

## 🤝 Contribuindo

1. Clone o repositório
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Envie um pull request

## 📄 Licença

Este projeto está sob licença MIT.
