# ============================================================
# CAMIULA Backend — Developer Commands
# ============================================================
# Usage: make <target>
#
# Run `make help` to see all available targets.
# ============================================================

.PHONY: help dev test lint migrate seed new-module postman validate docs

# Default
help: ## Show this help message
	@echo "CAMIULA Backend — Available Commands"
	@echo "===================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────────────

dev: ## Start dev server with hot reload
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-debug: ## Start dev server with SQL logging
	DEBUG=True uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

install: ## Install dependencies
	pip install -r requirements.txt

# ── Testing ──────────────────────────────────────────────

test: ## Run all tests
	python -m pytest tests/ -v --tb=short

test-integration: ## Run integration tests only
	python -m pytest tests/integration/ -v --tb=short

test-stress: ## Run stress/performance tests
	python -m pytest tests/stress/ -v --tb=short -s

test-module: ## Run tests for a specific module (usage: make test-module MODULE=patients)
	python -m pytest tests/integration/$(MODULE)/ -v --tb=short

# ── Database ─────────────────────────────────────────────

migrate: ## Create a new migration (usage: make migrate MSG="add_xyz_table")
	alembic revision --autogenerate -m "$(MSG)"

migrate-up: ## Apply all pending migrations
	alembic upgrade head

migrate-down: ## Rollback last migration
	alembic downgrade -1

migrate-status: ## Show current migration status
	alembic current

# ── Code Quality ─────────────────────────────────────────

validate: ## Run architecture validator (Clean Architecture rules)
	python scripts/validate_architecture.py

validate-module: ## Validate a single module (usage: make validate-module MODULE=patients)
	python scripts/validate_architecture.py --module $(MODULE)

validate-db: ## Run database standards validator
	python scripts/validate_db_standards.py

lint: ## Run all validators
	python scripts/validate_architecture.py
	@echo ""
	python scripts/validate_db_standards.py

# ── Scaffolding ──────────────────────────────────────────

new-module: ## Generate a new module (usage: make new-module NAME=billing)
	python scripts/new_module.py $(NAME)

new-module-entities: ## Generate module with entities (usage: make new-module-entities NAME=lab ENTITIES=order,result)
	python scripts/new_module.py $(NAME) --entities $(ENTITIES)

# ── Documentation ────────────────────────────────────────

postman: ## Export Postman collection from OpenAPI spec
	PYTHONPATH=. python scripts/export_postman.py

docs-serve: ## Open ReDoc in browser
	@echo "Starting server..."
	@echo "ReDoc:   http://localhost:8000/redoc"
	@echo "Swagger: http://localhost:8000/docs"
	@echo "OpenAPI: http://localhost:8000/openapi.json"
	uvicorn app.main:app --host 0.0.0.0 --port 8000

# ── Seeding ──────────────────────────────────────────────

seed: ## Run all seeders
	PYTHONPATH=. python scripts/seed_form_schemas.py
	PYTHONPATH=. python scripts/seed_movements.py

seed-schemas: ## Seed form schemas only
	PYTHONPATH=. python scripts/seed_form_schemas.py

seed-movements: ## Seed inventory movements only
	PYTHONPATH=. python scripts/seed_movements.py
