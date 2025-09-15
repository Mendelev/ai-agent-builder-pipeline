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

# Testes Unitários

cd backend && source venv/bin/activate && pytest tests/unit_tests -q

# Executar todos os testes
make test

# Verificar linting
make lint

----------------

# Aplicar nova migration
make db-migrate

# Iniciar Celery Beat para tarefas agendadas
celery -A app.workers.celery_app beat --loglevel=info

# Iniciar workers com fila de manutenção
celery -A app.workers.celery_app worker --loglevel=info -Q default,maintenance

# Executar testes de orquestração
python -m pytest tests/test_orchestration_api.py tests/test_state_machine.py tests/test_orchestration_service.py -v

# Verificar métricas Prometheus
curl http://localhost:8000/metrics

# Testar state machine
python -m pytest tests/test_state_machine.py::test_validate_transition_valid -v

# Executar todos os testes
make test