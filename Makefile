.PHONY: install test lint api frontend-install frontend-dev frontend-build

install:
	python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check backend tests

api:
	uvicorn gridup.api:app --app-dir backend --reload --host 0.0.0.0 --port 8000

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

