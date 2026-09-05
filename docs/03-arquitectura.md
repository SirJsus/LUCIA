# 03 · Arquitectura

## Vista general

``` text
┌────────────────────────────────────────────────────────────────────┐
│  apps/web  (React + Vite + TS)                                      │
│  Tablero (chessground) · Gráfico eval · Dashboard · Entrenamiento   │
└───────────────▲────────────────────────────────────▲───────────────┘
                │ REST (OpenAPI)                     │ WebSocket (progreso, análisis en vivo)
┌───────────────┴────────────────────────────────────┴───────────────┐
│  apps/api  (FastAPI)                                                │
│  routers: games · analysis · stats · training · engines · sync      │
│  worker: cola de análisis en background                             │
└───────┬───────────────────────┬───────────────────────┬────────────┘
        │                       │                       │
┌───────▼────────┐   ┌──────────▼──────────┐   ┌────────▼───────────┐
│ packages/      │   │ packages/core       │   │ SQLite             │
│ chesscom       │   │ EngineBridge (UCI)  │   │ (SQLAlchemy +      │
│ cliente API    │   │ MoveClassifier      │   │  Alembic)          │
│ pública        │   │ Accuracy / Phases   │   │                    │
└───────┬────────┘   │ Insight extractors  │   └────────────────────┘
        │            └──────────┬──────────┘
        ▼                       │ stdin/stdout UCI
  api.chess.com        ┌────────▼──────────┐  ┌────────────────────┐
                       │ engines/bin/      │  │ engines/networks/  │
                       │ stockfish · lc0   │──│ *.pb.gz (Lc0)      │
                       └───────────────────┘  └────────────────────┘
```

## Componentes

### `packages/core` (Python) — el corazón

- **`engine/`** — `EngineBridge`: abstracción sobre cualquier motor UCI usando `python-chess` (`chess.engine`). Pool de procesos de motor para análisis paralelo. Config tipada (hilos, hash, MultiPV, límites por profundidad/nodos/tiempo).
- **`analysis/`** — `GameAnalyzer`: recorre una partida, obtiene eval de cada posición (con caché por FEN), produce `AnalyzedGame` con `AnalyzedMove` por jugada.
- **`classification/`** — `MoveClassifier`: convierte deltas de *win probability* en categorías (Mejor / Buena / Imprecisión / Error / Blunder…). Umbrales en un archivo de config, testeados.
- **`accuracy/`** — Fórmula de precisión (basada en la de Lichess, documentada: `cp -> win% -> accuracy`).
- **`phases/`** — Detección de fase de partida (apertura / medio juego / final) por material y desarrollo.
- **`insights/`** — Extractores de patrones: errores por fase, por apertura, *time trouble*, piezas colgadas, mates perdidos.
- **`openings/`** — Clasificación ECO (base de datos de aperturas de Lichess, CC0) y comparación con explorer.

### `packages/chesscom` (Python)

Cliente `httpx` asíncrono para la API pública de chess.com (`https://api.chess.com/pub/...`). Sin autenticación. Endpoints: `player/{u}`, `player/{u}/stats`, `player/{u}/games/archives`, `player/{u}/games/{Y}/{M}`. Parsea PGN con `python-chess`, extrae relojes `%clk`. Respeta `User-Agent` y rate limit (peticiones secuenciales, backoff en 429).

### `apps/api` (FastAPI)

- Routers REST + WebSocket para progreso.
- **Worker de análisis**: cola en proceso (asyncio + pool de motores). Se puede extraer a Redis/arq si se necesita escalar (ver roadmap).
- Persistencia con SQLAlchemy 2 (async) + Alembic sobre SQLite.
- Genera `openapi.json` → `packages/shared-types` (tipos TS con `openapi-typescript`).

### `apps/web` (React)

- Vite + React 19 + TypeScript.
- **chessground** (tablero de lichess) + **chess.js** (validación local de jugadas y cálculo de atacantes para la capa de ocupación RF-7, sin motor).
- TanStack Query para datos, TanStack Router para navegación, Zustand para estado del visor.
- Gráficas con Recharts (eval por jugada, tendencias).
- Tailwind CSS + shadcn/ui.

### `engines/`

Sub-módulos git apuntando a los repos oficiales de Stockfish y Lc0. `scripts/setup-engines.sh` compila ambos a `engines/bin/` y descarga una red de Lc0 a `engines/networks/`. Los binarios y redes no se versionan.

## Modelo de datos (inicial)

``` database
players        (id, username, platform, ratings_json, fetched_at)
games          (id, player_id, platform_id, pgn, white, black, result, time_control,
                eco, opening_name, played_at, end_reason, clocks_json, rated)
analyses       (id, game_id, engine, engine_version, depth, multipv, created_at,
                white_accuracy, black_accuracy, status)
analyzed_moves (id, analysis_id, ply, san, uci, fen_before, eval_cp, eval_mate,
                best_move, best_eval_cp, delta_winprob, classification, phase,
                clock_seconds, pv_json)
position_cache (fen, engine, depth, eval_cp, eval_mate, best_move, pv_json)
puzzles        (id, source_move_id, fen, solution_uci, theme, srs_due_at, srs_ease)
sync_state     (player_id, last_archive_synced, last_synced_at)
boards         (id, title, tags_json, root_fen, tree_json, is_own_game, created_at, updated_at)
               -- tableros de análisis (RF-6); tree_json = árbol de variantes con comentarios
```

## Flujos principales

1. **Sync**: UI → `POST /sync` → chesscom client descarga archivos nuevos → parsea PGN → inserta `games` → responde resumen.
2. **Análisis**: UI → `POST /analysis` (game_ids, config) → encola → worker toma un motor del pool → analiza ply a ply (consulta `position_cache` primero) → guarda `analyzed_moves` → emite progreso por WebSocket → calcula precisión y clasificaciones.
3. **Insight**: `GET /stats/...` agrega sobre `analyzed_moves` + `games` (consultas SQL, cacheadas).
4. **Puzzles**: job periódico toma blunders con solución única (MultiPV: 1ª línea ≫ 2ª) → crea `puzzles`.

## Decisiones clave

Ver [ADRs](adr/): monorepo, motores como sub-módulos compilados, Python orquesta / C++ solo en motores, GPL-3.0, SQLite local-first.

## Ver también

[06-mapa-del-proyecto.md](06-mapa-del-proyecto.md) tiene la versión en diagramas Mermaid de este documento (flujo general, módulos y secuencias) más una tabla de qué requerimiento vive en qué archivo. Se mantiene con el agente `mapeador`; si este documento cambia de forma estructural, el mapa debe actualizarse también.
