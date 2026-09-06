.PHONY: help doctor up setup engines types api web test lint

help:
	@echo "make doctor   - diagnostica el entorno (que falta y como instalarlo)"
	@echo "make up       - levanta api + web en nativo con logs unificados (make up S=api para uno solo)"
	@echo "make setup    - instala dependencias Python (uv) y JS (pnpm)"
	@echo "make engines  - clona y compila Stockfish y Lc0, descarga red por defecto"
	@echo "make api      - levanta la API FastAPI en :8000"
	@echo "make web      - levanta el frontend en :5173"
	@echo "make types    - regenera los tipos TS del front desde el OpenAPI de la API"
	@echo "make test     - corre pytest"
	@echo "make lint     - ruff + eslint"

doctor:
	./scripts/doctor.sh

up:
	./scripts/dev.sh $(S)

setup:
	uv sync --all-packages --all-extras
	pnpm install

engines:
	./scripts/setup-engines.sh

api:
	uv run --package lucia-api uvicorn lucia_api.main:app --reload --port 8000

web:
	pnpm dev:web

types:
	uv run python3 scripts/export-openapi.py
	pnpm --filter @lucia/shared-types generate

test:
	uv run pytest

lint:
	uv run ruff check .
	pnpm lint
