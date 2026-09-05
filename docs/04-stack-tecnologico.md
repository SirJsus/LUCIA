# 04 · Stack tecnológico

Elegido con el criterio: **maduro, gratuito, compatible con GPL-3.0, y con el menor número de piezas posible**.

## Motores de ajedrez

| Tecnología | Uso | Por qué |
| ------------ | ----- | --------- |
| **Stockfish** (C++, GPL-3.0) | Motor principal de análisis | El más fuerte del mundo, NNUE corre excelente en CPU, evaluación en centipawns estable y determinista con `nodes` fijos. |
| **Lc0 – Leela Chess Zero** (C++, GPL-3.0) | Segunda opinión, análisis "posicional", sparring humano | Evaluación por probabilidad W/D/L, distinto sesgo que Stockfish. Rinde mejor con GPU (CUDA/OpenCL); en CPU usar backend `blas`/`eigen` con redes pequeñas. Existen redes tipo Maia para jugar como humano de N Elo. |
| **Protocolo UCI** | Comunicación con motores | Estándar. Cualquier motor UCI se enchufa sin tocar el núcleo (RNF-9). |

## Backend / lógica (Python)

| Tecnología | Uso | Por qué |
| ------------ | ----- | --------- |
| **Python 3.12+** | Orquestación, análisis, API | Ecosistema de ajedrez y datos inmejorable. El trabajo pesado lo hacen los motores en C++, Python solo coordina (ver ADR-0003). |
| **python-chess** | PGN, FEN, generación de jugadas, wrapper UCI (`chess.engine`) | Librería de referencia, async, madura. Nos ahorra escribir un parser UCI. |
| **FastAPI** + **uvicorn** | API REST + WebSocket | Async nativo, OpenAPI automático (del que generamos tipos TS), validación con Pydantic. |
| **Pydantic v2** | Modelos y config | Tipado fuerte, settings desde `.env`. |
| **SQLAlchemy 2 (async)** + **aiosqlite** | ORM sobre SQLite | Local-first (RNF-7). Migrar a PostgreSQL sería cambiar la URL. |
| **Alembic** | Migraciones | Estándar con SQLAlchemy. |
| **httpx** | Cliente HTTP async para chess.com | Async, HTTP/2, fácil de testear con `respx`. |
| **polars** | Agregaciones estadísticas | Más rápido y con menos memoria que pandas para cruzar miles de partidas. |
| **uv** | Gestión de paquetes y workspaces Python | Rápido, lockfile único para el monorepo. *(Pendiente instalar: `curl -LsSf https://astral.sh/uv/install.sh \| sh`)* |
| **ruff** | Lint + format | Un solo binario para todo. |
| **pytest** + **pytest-asyncio** | Tests | Estándar. |

## Frontend (TypeScript)

| Tecnología | Uso | Por qué |
| ------------ | ----- | --------- |
| **React 19** + **Vite** + **TypeScript** | SPA | La API es FastAPI; no necesitamos SSR de Next.js. Vite es más simple y rápido. |
| **chessground** (GPL-3.0) | Tablero | El tablero de lichess: flechas, drag, premoves, animaciones, accesible. Misma licencia que el proyecto. |
| **chess.js** | Validación de jugadas en cliente | Para exploración interactiva sin ir al servidor. |
| **TanStack Query** | Fetch y caché de datos | Manejo de estado servidor sin boilerplate. |
| **TanStack Router** | Navegación | Type-safe. |
| **Zustand** | Estado del visor (posición actual, variante) | Mínimo y suficiente. |
| **Recharts** | Gráfico de eval, tendencias | Declarativo, integrado con React. |
| **Tailwind CSS** + **shadcn/ui** | UI | Componentes copiables, tema oscuro/claro sin esfuerzo. |
| **openapi-typescript** | Tipos compartidos desde `openapi.json` | Un solo origen de verdad para los contratos API. |
| **pnpm workspaces** | Monorepo JS | Rápido, estricto con dependencias. |
| **Vitest** + **Playwright** | Tests unitarios y E2E | Nativos de Vite. |

## Datos externos (gratuitos)

| Fuente | Uso |
| -------- | ----- |
| **chess.com Public API** (`api.chess.com/pub`) | Perfil, stats, archivos mensuales de partidas en PGN/JSON. Sin auth. Requiere `User-Agent`. |
| **Lichess Opening Explorer API** | Teoría de aperturas (base de maestros y de jugadores por rating). Gratuito. |
| **Lichess `chess-openings`** (CC0) | Tabla ECO → nombre de apertura, para clasificar partidas offline. |
| **Redes Lc0** (lczero.org) y **Maia** | Pesos para Lc0. Maia: redes entrenadas para jugar como humanos de 1100–1900 Elo. |

## Infraestructura y tooling

| Tecnología | Uso |
| ------------ | ----- |
| **git submodules** | `engines/stockfish`, `engines/lc0` fijados a un tag. |
| **Makefile** + `scripts/` | Comandos unificados: `make doctor` (diagnóstico), `make up` (orquestador nativo con logs unificados, estilo compose), `make engines`, `make test`, `make lint`. Bash puro, sin dependencias. Si el número de servicios crece, [process-compose](https://github.com/F1bonacc1/process-compose) es el reemplazo natural. |
| **Docker Compose** | Vía secundaria de portabilidad. En nativo los motores se compilan con `profile-build` para la CPU local y rinden un 10–20 % más que la imagen genérica. Los motores viven dentro del contenedor de la API; cuando entre Lc0 con GPU o análisis en lote pesado se separará un servicio `worker` (misma imagen, otro comando). |
| **GitHub Actions** | CI: ruff, pytest, eslint, tsc, build de web. Compilar motores en CI solo en release. |
| **Meson + Ninja** | Requerido para compilar Lc0. Stockfish usa `make`. |

## Lo que NO usamos (y por qué)

- **Next.js**: no necesitamos SSR ni API routes; añade complejidad.
- **PostgreSQL desde el día 1**: un usuario, local; SQLite basta y simplifica el arranque. Queda como opción.
- **Celery/Redis desde el día 1**: cola en proceso con asyncio + pool de motores cubre el MVP. Se extrae a `arq` + Redis si hace falta.
- **Bindings C++ propios (pybind11)**: solo si un *profiler* demuestra que Python es cuello de botella. El coste del análisis está en el motor, no en el orquestador.
- **Electron/Tauri**: por ahora web local en el navegador. Tauri es candidato para empaquetar en el futuro.
