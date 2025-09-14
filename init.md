# Setup inicial
cd backend
poetry install  # ou pip install -r requirements.txt

# Iniciar serviços
make dev-up

# Aplicar migrations
make db-migrate

# Executar testes
make test

# Verificar linting
make lint

# Iniciar API
make run-api

# Iniciar workers (em outro terminal)
make run-workers