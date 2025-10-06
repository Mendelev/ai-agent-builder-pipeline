.PHONY: help setup start stop restart clean logs status shell psql migrate backup rebuild

# Cores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m

help: ## Mostrar esta ajuda
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║   🐳 AI Agent Builder Pipeline - Makefile          ║"
	@echo "╚══════════════════════════════════════════════════════╝"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

setup: ## Configurar ambiente (criar .env)
	@./docker.sh setup

start: ## Iniciar serviços (PostgreSQL + Backend)
	@./docker.sh start

start-all: ## Iniciar todos os serviços (com pgAdmin e Redis)
	@./docker.sh start-all

stop: ## Parar todos os serviços
	@./docker.sh stop

restart: ## Reiniciar todos os serviços
	@./docker.sh restart

clean: ## Parar e limpar volumes (apaga dados!)
	@./docker.sh clean

logs: ## Mostrar logs de todos os serviços
	@./docker.sh logs

logs-backend: ## Mostrar logs do backend
	@./docker.sh logs backend

logs-db: ## Mostrar logs do PostgreSQL
	@./docker.sh logs postgres

status: ## Mostrar status dos serviços
	@./docker.sh status

shell: ## Acessar shell do backend
	@./docker.sh shell

psql: ## Acessar PostgreSQL CLI
	@./docker.sh psql

migrate: ## Executar migrações do banco
	@./docker.sh migrate

backup: ## Criar backup do banco de dados
	@./docker.sh backup

rebuild: ## Reconstruir imagens Docker
	@./docker.sh rebuild

dev: ## Setup completo para desenvolvimento
	@echo "$(GREEN)🚀 Configurando ambiente de desenvolvimento...$(NC)"
	@make setup
	@make start-all
	@sleep 5
	@make status

test: ## Executar testes
	@docker-compose exec backend pytest

test-cov: ## Executar testes com cobertura
	@docker-compose exec backend pytest --cov=app tests/

lint: ## Executar linter
	@docker-compose exec backend flake8 app/

format: ## Formatar código
	@docker-compose exec backend black app/

update-deps: ## Atualizar dependências
	@docker-compose exec backend python update_requirements.py --dry-run

install: ## Instalar dependências no container
	@docker-compose exec backend pip install -r requirements.txt

down: ## Parar serviços sem remover volumes
	@docker-compose down

up: ## Iniciar serviços em modo attached
	@docker-compose up

build: ## Build das imagens
	@docker-compose build

ps: ## Listar containers
	@docker-compose ps

top: ## Mostrar processos dos containers
	@docker-compose top

stats: ## Mostrar estatísticas de recursos
	@docker stats

prune: ## Limpar recursos Docker não utilizados
	@docker system prune -f

# Atalhos rápidos
s: start ## Atalho para start
st: stop ## Atalho para stop
l: logs ## Atalho para logs
r: restart ## Atalho para restart
