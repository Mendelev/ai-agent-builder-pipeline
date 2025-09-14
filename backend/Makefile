# backend/Makefile
.PHONY: help dev-up dev-down db-migrate db-rollback test lint run-api run-workers clean format

help:
	@echo "Available targets:"
	@echo "  dev-up       - Start development environment (Docker services)"
	@echo "  dev-down     - Stop development environment"
	@echo "  db-migrate   - Run database migrations"
	@echo "  db-rollback  - Rollback last migration"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run linters (ruff, mypy)"
	@echo "  format       - Format code with black"
	@echo "  run-api      - Run FastAPI server"
	@echo "  run-workers  - Run Celery workers"
	@echo "  clean        - Clean cache files"

dev-up:
	docker-compose up -d postgres redis rabbitmq

dev-down:
	docker-compose down

db-migrate:
	poetry run alembic upgrade head

db-rollback:
	poetry run alembic downgrade -1

test:
	poetry run python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

lint:
	poetry run ruff check app/ tests/
	poetry run mypy app/ --ignore-missing-imports

format:
	poetry run black app/ tests/ --line-length 120
	poetry run ruff check app/ tests/ --fix

run-api:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-config logging.json

run-workers:
	poetry run celery -A app.workers.celery_app worker --loglevel=info --pool=prefork --concurrency=4 -Q default

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov/