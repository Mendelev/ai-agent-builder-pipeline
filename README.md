# 🤖 AI Agent Builder Pipeline

Sistema completo para construção e gerenciamento de agentes de IA com pipeline automatizado.

## 📋 Stack Tecnológica

- **Backend**: FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis (opcional)
- **Containerização**: Docker + Docker Compose
- **Admin**: pgAdmin (opcional)

## 🚀 Quick Start

### Opção 1: Docker (Recomendado)

```bash
# Configurar ambiente
make setup

# Iniciar todos os serviços
make start-all

# Acessar API
open http://localhost:8000/docs
```

### Opção 2: Desenvolvimento Local

```bash
cd backend

# Setup automático
./setup.sh

# Ou manual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar banco
cp .env.example .env
# Editar .env com credenciais do PostgreSQL

# Rodar migrações
alembic upgrade head

# Iniciar servidor
python main.py
```

## 📂 Estrutura do Projeto

```
ai-agent-builder-pipeline/
├── backend/                    # API FastAPI
│   ├── alembic/               # Migrações de banco
│   ├── app/
│   │   ├── api/routes/       # Endpoints
│   │   ├── core/             # Config e database
│   │   ├── models/           # Models SQLAlchemy
│   │   ├── schemas/          # Schemas Pydantic
│   │   └── services/         # Lógica de negócio
│   ├── tests/                # Testes
│   ├── Dockerfile            # Container do backend
│   ├── requirements.txt      # Dependências Python
│   └── main.py              # Entry point
├── init-db/                  # Scripts SQL inicialização
├── docker-compose.yml        # Orquestração de containers
├── docker.sh                # Script gerenciador Docker
├── Makefile                 # Comandos simplificados
├── .env.docker.example      # Template de variáveis
└── README.md               # Este arquivo
```

## 🐳 Docker

### Comandos Principais (Make)

```bash
make help           # Ver todos os comandos
make setup          # Configurar .env
make start          # Iniciar serviços básicos
make start-all      # Iniciar com pgAdmin e Redis
make stop           # Parar serviços
make logs           # Ver logs
make status         # Status dos containers
make shell          # Acessar shell do backend
make psql           # Acessar PostgreSQL
make migrate        # Rodar migrações
make backup         # Backup do banco
make test           # Rodar testes
```

### Comandos Principais (Script)

```bash
./docker.sh start          # Iniciar
./docker.sh stop           # Parar
./docker.sh logs backend   # Logs
./docker.sh shell          # Shell
./docker.sh backup         # Backup
```

### Docker Compose Direto

```bash
docker-compose up -d              # Iniciar
docker-compose ps                 # Status
docker-compose logs -f backend    # Logs
docker-compose down               # Parar
```

## 🌐 URLs de Acesso

| Serviço | URL | Descrição |
|---------|-----|-----------|
| API Backend | http://localhost:8000 | API principal |
| Swagger Docs | http://localhost:8000/docs | Documentação interativa |
| ReDoc | http://localhost:8000/redoc | Documentação alternativa |
| Health Check | http://localhost:8000/health | Status da API |
| pgAdmin* | http://localhost:5050 | Admin PostgreSQL |
| PostgreSQL | localhost:5432 | Banco de dados |
| Redis* | localhost:6379 | Cache/Queue |

\* Requer iniciar com `make start-all` ou `--profile tools`

## 🗄️ Banco de Dados

### Migrações com Alembic

```bash
# Aplicar migrações
alembic upgrade head

# Criar nova migração
alembic revision --autogenerate -m "descrição"

# Reverter última migração
alembic downgrade -1

# Ver histórico
alembic history

# Via Docker
make migrate
./docker.sh migration "nova tabela"
```

### Acesso Direto ao PostgreSQL

```bash
# Local
psql -U user -d ai_agent_builder

# Docker
make psql
# ou
./docker.sh psql
```

## 📝 API Endpoints

### Projects

- `POST /api/v1/projects` - Criar projeto
- `GET /api/v1/projects` - Listar projetos
- `GET /api/v1/projects/{id}` - Obter projeto
- `PUT /api/v1/projects/{id}` - Atualizar projeto
- `DELETE /api/v1/projects/{id}` - Deletar projeto

### Requirements

- `POST /api/v1/projects/{id}/requirements/bulk` - Upsert em lote
- `GET /api/v1/projects/{id}/requirements` - Listar requisitos
- `GET /api/v1/projects/{id}/requirements/{code}/versions` - Histórico

## 🧪 Testes

```bash
# Local
pytest
pytest --cov=app tests/

# Docker
make test
make test-cov
docker-compose exec backend pytest
```

## 🔄 Atualização de Dependências

```bash
cd backend

# Ver atualizações disponíveis
python update_requirements.py --dry-run

# Aplicar atualizações
python update_requirements.py

# Script interativo
./quick_update.sh

# Via Docker
make update-deps
```

## 📚 Documentação Adicional

- [Backend README](backend/README.md) - Setup e uso do backend
- [Docker Guide](DOCKER_GUIDE.md) - Guia completo Docker
- [Dependency Update Guide](backend/DEPENDENCY_UPDATE_GUIDE.md) - Atualização de libs

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_agent_builder

# Application
APP_NAME="AI Agent Builder Pipeline"
DEBUG=True
HOST=0.0.0.0
PORT=8000

# CORS
ALLOWED_ORIGINS=*
```

### Docker (.env para docker-compose)

```bash
# PostgreSQL
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=ai_agent_builder

# Ports
POSTGRES_PORT=5432
BACKEND_PORT=8000
PGADMIN_PORT=5050
```

## 🔧 Desenvolvimento

### Setup Inicial

```bash
# Clone o repositório
git clone <repo-url>
cd ai-agent-builder-pipeline

# Docker (recomendado)
make dev

# Ou local
cd backend
./setup.sh
```

### Workflow Diário

```bash
# Iniciar
make start

# Ver logs
make logs

# Fazer alterações no código (hot reload automático)

# Testar
make test

# Parar
make stop
```

### Criar Nova Feature

```bash
# 1. Branch
git checkout -b feature/nova-feature

# 2. Modificar models em backend/app/models/

# 3. Criar migração
make shell
alembic revision --autogenerate -m "adicionar campo xyz"

# 4. Aplicar
alembic upgrade head

# 5. Testar
pytest

# 6. Commit
git add .
git commit -m "feat: adicionar nova feature"
```

## 🔍 Troubleshooting

### Porta já em uso

```bash
# Mudar porta no .env
BACKEND_PORT=8001
POSTGRES_PORT=5433
```

### Backend não inicia

```bash
make logs-backend
# ou
./docker.sh logs backend
```

### Erro de migração

```bash
make psql
\dt  # Verificar tabelas
```

### Limpar tudo e recomeçar

```bash
make clean
make start
```

## 🚀 Deploy

### Build para Produção

```bash
# Build
docker-compose -f docker-compose.yml build

# Deploy
docker-compose -f docker-compose.yml up -d
```

### Checklist de Segurança

- [ ] Mudar senhas padrão em produção
- [ ] Configurar HTTPS/SSL
- [ ] Ajustar CORS origins
- [ ] Configurar rate limiting
- [ ] Backup automatizado
- [ ] Monitoramento de logs

## 📊 Monitoramento

```bash
# Status dos containers
make stats
docker stats

# Logs estruturados
make logs > logs.txt

# Health check
curl http://localhost:8000/health
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob licença MIT.

## 🆘 Suporte

- **Documentação**: Ver arquivos `*_GUIDE.md`
- **Issues**: Abrir issue no GitHub
- **Comandos**: `make help` ou `./docker.sh help`

---

**Desenvolvido com ❤️ usando FastAPI e Docker**
