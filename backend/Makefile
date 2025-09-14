# backend/Makefile
.PHONY: help dev-up dev-down db-migrate db-rollback test lint run-api run-workers clean

help:
	@echo "Available targets:"
	@echo "  dev-up       - Start development environment (Docker services)"
	@echo "  dev-down     - Stop development environment"
	@echo "  db-migrate   - Run database migrations"
	@echo "  db-rollback  - Rollback last migration"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linters (ruff, mypy)"
	@echo "  run-api      - Run FastAPI server"
	@echo "  run-workers  - Run Celery workers"
	@echo "  clean        - Clean cache files"

dev-up:
	docker-compose -f ../infra/docker-compose.yml up -d postgres redis rabbitmq

dev-down:
	docker-compose -f ../infra/docker-compose.yml down

db-migrate:
	cd backend && alembic upgrade head

db-rollback:
	cd backend && alembic downgrade -1

test:
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	cd backend && ruff check app/ tests/
	cd backend && mypy app/ --ignore-missing-imports

run-api:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-workers:
	cd backend && celery -A app.workers.celery_app worker --loglevel=info --pool=prefork --concurrency=4

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache