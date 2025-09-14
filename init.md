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



----------------

# Aplicar nova migration
make db-migrate

# Executar testes do plano
python -m pytest tests/test_plan_api.py tests/test_plan_service.py -v

# Testar API completa
make test

# Verificar linting
make lint

-----------------

# Aplicar nova migration
make db-migrate

# Executar testes dos prompts
python -m pytest tests/test_prompts_api.py tests/test_prompt_service.py -v

# Testar segurança (remoção de secrets)
python -m pytest tests/test_prompt_service.py::test_remove_secrets -v

# Executar todos os testes
make test

# Verificar linting
make lint

----------------