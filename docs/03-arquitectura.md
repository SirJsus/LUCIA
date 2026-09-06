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

- **`engine/`** (implementado) — `EngineBridge`: abstracción sobre cualquier motor UCI usando `python-chess` (`chess.engine.popen_uci`). Config tipada (`EngineConfig`: hilos, hash, MultiPV, límite por profundidad/nodos/tiempo). Un motor por instancia; el pool de procesos para análisis en lote llega con el worker (fase 1, pendiente).
- **`analysis/`** (implementado) — `evaluate_positions()` recorre una partida y evalúa cada posición una sola vez (N+1 evaluaciones para N jugadas, no 2N); `analyze_game()` combina eso con `classification` y `accuracy` para producir `AnalyzedGame`/`AnalyzedMove`. Caché por FEN entre partidas (RF-2.7): pendiente, hoy cada partida se evalúa desde cero.
- **`classification/`** (implementado) — `classify_move()`: convierte la caída de *win probability* en categorías (best / excellent / good / inaccuracy / mistake / blunder / missed_win). Umbrales en `ClassificationThresholds`, ajustables, testeados. `missed_win` detecta perder un mate forzado aunque la posición siga siendo ganadora en centipawns. `book` queda sin implementar hasta integrar `openings/`.
- **`accuracy/`** (implementado) — `win_percent()` usa el modelo estadístico `lichess` que ya trae `python-chess` (`Score.wdl(model="lichess")`), sin reimplementarlo. `move_accuracy()` es la fórmula pública de Lichess (cp/mate → win% → precisión). `game_accuracy()` es una aproximación documentada del agregado por partida (media ponderada por volatilidad + media armónica), no una reimplementación exacta.
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

## Modelo de datos

Implementado (RF-1, `apps/api/lucia_api/db/models.py`, migrado con Alembic):

``` database
players    (id, platform, username, country, joined_at, ratings_json, fetched_at)
           -- country/joined_at: RF-1.1. ratings_json: JSON crudo de /stats (RF-1.6).
games      (id, player_id, platform, platform_id, pgn,
            white_username, white_rating, white_result,
            black_username, black_rating, black_result,
            time_control, time_class, rules, rated, eco,
            clocks_json, played_at, year, month)
           -- platform_id = uuid de chess.com: upsert idempotente por partida.
           -- clocks_json: reloj tras cada jugada (lucia_chesscom.parse_move_clocks).
sync_state (player_id, last_synced_year, last_synced_month, last_synced_at)
           -- RF-1.3: qué mes sincronizar de nuevo (lucia_chesscom.months_to_sync).
```

Pendiente (fases posteriores, no migrado todavía):

``` database
analyses       (id, game_id, engine, engine_version, depth, multipv, created_at,
                white_accuracy, black_accuracy, status)
analyzed_moves (id, analysis_id, ply, san, uci, fen_before, eval_cp, eval_mate,
                best_move, best_eval_cp, delta_winprob, classification, phase,
                clock_seconds, pv_json)
position_cache (fen, engine, depth, eval_cp, eval_mate, best_move, pv_json)
puzzles        (id, source_move_id, fen, solution_uci, theme, srs_due_at, srs_ease)
boards         (id, title, tags_json, root_fen, tree_json, is_own_game, created_at, updated_at)
               -- tableros de análisis (RF-6); tree_json = árbol de variantes con comentarios
```

## Flujos principales

1. **Sync** (implementado): `POST /sync` → `lucia_chesscom.ChessComClient` trae perfil, stats y archivos → `months_to_sync` decide qué meses faltan (RF-1.3) → por cada mes, secuencial, descarga partidas y hace upsert por `uuid` en `games` (idempotente) → actualiza `sync_state` → responde un resumen (meses sincronizados, partidas insertadas/actualizadas). Ver `lucia_api/services/chesscom_sync.py`.
2. **Análisis**: UI → `POST /analysis` (game_ids, config) → encola → worker toma un motor del pool → analiza ply a ply (consulta `position_cache` primero) → guarda `analyzed_moves` → emite progreso por WebSocket → calcula precisión y clasificaciones.
3. **Insight**: `GET /stats/...` agrega sobre `analyzed_moves` + `games` (consultas SQL, cacheadas).
4. **Puzzles**: job periódico toma blunders con solución única (MultiPV: 1ª línea ≫ 2ª) → crea `puzzles`.

## Decisiones clave

Ver [ADRs](adr/): monorepo, motores como sub-módulos compilados, Python orquesta / C++ solo en motores, GPL-3.0, SQLite local-first.

## Ver también

[06-mapa-del-proyecto.md](06-mapa-del-proyecto.md) tiene la versión en diagramas Mermaid de este documento (flujo general, módulos y secuencias) más una tabla de qué requerimiento vive en qué archivo. Se mantiene con el agente `mapeador`; si este documento cambia de forma estructural, el mapa debe actualizarse también.
