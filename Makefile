# Puerto de la API. Cambiable para convivir con otros proyectos en la misma
# máquina: `make up API_PORT=8001`. El proxy del front lee la misma variable.
API_PORT ?= 8000

.PHONY: help doctor up setup engines types api web test lint

help:
	@echo "make doctor   - diagnostica el entorno (que falta y como instalarlo)"
	@echo "make up       - levanta api + web en nativo con logs unificados (make up S=api para uno solo)"
	@echo "make setup    - instala dependencias Python (uv) y JS (pnpm)"
	@echo "make engines  - clona y compila Stockfish y Lc0, descarga red por defecto"
	@echo "make api      - levanta la API FastAPI en :$(API_PORT) (API_PORT=8001 para cambiarlo)"
	@echo "make web      - levanta el frontend en :5173"
	@echo "make types    - regenera los tipos TS del front desde el OpenAPI de la API"
	@echo "make test     - corre las pruebas: pytest (Python) + vitest (web)"
	@echo "make lint     - ruff + eslint + tsc (comprobacion de tipos del front)"

doctor:
	./scripts/doctor.sh

up:
	API_PORT=$(API_PORT) ./scripts/dev.sh $(S)

setup:
	uv sync --all-packages --all-extras
	pnpm install

engines:
	./scripts/setup-engines.sh

api:
	uv run --package lucia-api uvicorn lucia_api.main:app --reload --port $(API_PORT)

web:
	pnpm dev:web

types:
	uv run python3 scripts/export-openapi.py
	pnpm --filter @lucia/shared-types generate

# Las dos mitades del monorepo, en un solo comando: hasta ahora `make test`
# solo corría Python y las pruebas de `apps/web` había que acordarse de
# lanzarlas aparte. Python primero porque es donde está el grueso.
test:
	uv run pytest
	pnpm test

# `tsc --noEmit` va aquí y no en `make test` porque no es una prueba: es la
# misma comprobación estática que ruff y eslint, y hasta ahora no la corría
# ningún comando, así que un error de tipos solo salía al construir el front.
lint:
	uv run ruff check .
	pnpm lint
	pnpm typecheck
