# Instalação
cd backend
poetry install  # ou pip install -r requirements.txt

# Configuração
cp .env.example .env
# Editar .env com suas configurações

# Iniciar serviços
make dev-up

# Aplicar migrations
make db-migrate

# Executar testes
make test

# Verificar linting
make lint

# Formatar código
make format

# Iniciar API (terminal 1)
make run-api

# Iniciar workers (terminal 2)
make run-workers

# Parar serviços
make dev-down

# Limpar cache
make clean