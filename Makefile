PYTHON ?= python3
API_DIR := apps/api

.PHONY: setup up down migrate seed test lint typecheck e2e format api-docs

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e "$(API_DIR)[dev]"
	npm install

up:
	docker compose up --build

down:
	docker compose down --remove-orphans

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m oldpages_api.scripts.seed_foundation

test:
	cd $(API_DIR) && ../../.venv/bin/python -m pytest
	npm run test

lint:
	cd $(API_DIR) && ../../.venv/bin/ruff format --check .
	cd $(API_DIR) && ../../.venv/bin/ruff check .
	npm run lint

typecheck:
	cd $(API_DIR) && ../../.venv/bin/mypy src tests
	npm run typecheck

e2e:
	cd $(API_DIR) && ../../.venv/bin/python -m pytest tests/e2e
	npm run e2e

format:
	cd $(API_DIR) && ../../.venv/bin/ruff format .
	npm run format

api-docs:
	cd $(API_DIR) && ../../.venv/bin/python -m oldpages_api.scripts.export_openapi > ../../docs/api/openapi.json
