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

- **`engine/`** (implementado) — `EngineBridge`: abstracción sobre cualquier motor UCI usando `python-chess` (`chess.engine.popen_uci`). Config tipada (`EngineConfig`: hilos, hash, MultiPV, límite por profundidad/nodos/tiempo). Las opciones genéricas (`Threads`, `Hash`) se aplican solo si el motor las declara — Lc0 no tiene `Hash` y mandársela aborta la conexión —, mientras que las `extra_options` van sin filtrar porque alguien las pidió a propósito. Un motor por instancia; el worker procesa un análisis a la vez, un pool de procesos para análisis en lote queda pendiente.
- **`analysis/`** (implementado) — `evaluate_positions()` recorre una partida y evalúa cada posición una sola vez (N+1 evaluaciones para N jugadas, no 2N); `analyze_game()` combina eso con `classification` y `accuracy` para producir `AnalyzedGame`/`AnalyzedMove`. La caché por FEN (RF-2.7) no vive aquí sino en `apps/api` (`CachedEngineBridge`), para que este paquete no dependa de ninguna base de datos.
- **`classification/`** (implementado) — `classify_move()`: convierte la caída de *win probability* en categorías (best / excellent / good / inaccuracy / mistake / blunder / missed_win). Umbrales en `ClassificationThresholds`, ajustables, testeados. `missed_win` detecta perder un mate forzado aunque la posición siga siendo ganadora en centipawns. `book` queda sin implementar hasta integrar `openings/`.
- **`accuracy/`** (implementado) — `win_percent()` usa el modelo estadístico `lichess` que ya trae `python-chess` (`Score.wdl(model="lichess")`), sin reimplementarlo. `move_accuracy()` es la fórmula pública de Lichess (cp/mate → win% → precisión). `game_accuracy()` es una aproximación documentada del agregado por partida (media ponderada por volatilidad + media armónica), no una reimplementación exacta.
- **`phases/`** (implementado) — `detect_phase()` clasifica una posición (final por material restante; apertura por desarrollo y tope de jugadas) y `phases_by_ply()` la fuerza a avanzar en un solo sentido a lo largo de una partida. Umbrales como constantes con nombre, ajustables.
- **`insights/`** — Extractores de patrones: errores por fase, por apertura, *time trouble*, piezas colgadas, mates perdidos.
- **`openings/`** — Clasificación ECO (base de datos de aperturas de Lichess, CC0) y comparación con explorer.

### `packages/chesscom` (Python)

Cliente `httpx` asíncrono para la API pública de chess.com (`https://api.chess.com/pub/...`). Sin autenticación. Endpoints: `player/{u}`, `player/{u}/stats`, `player/{u}/games/archives`, `player/{u}/games/{Y}/{M}`. Parsea PGN con `python-chess`, extrae relojes `%clk`. Respeta `User-Agent` y rate limit (peticiones secuenciales, backoff en 429).

### `apps/api` (FastAPI)

- **Routers** (implementado): `sync` (RF-1), `games` (RF-5.3), `analysis` (RF-2: crear, consultar, WebSocket de progreso, y `POST /analysis/position` para el análisis en vivo de una posición suelta), `engines` (RF-5.4: lee y edita parámetros; la ruta del binario es de solo lectura a propósito), `stats` (RF-3.1 a 3.3), `boards` (RF-6: CRUD de tableros de análisis).
- **`services/`**: la lógica que no es HTTP ni motor. `chesscom_sync.py` (RF-1); `analysis.py` (RF-2: `run_analysis` orquesta `lucia_core`, `analyse_position` para el análisis en vivo, `CachedEngineBridge` envuelve el motor con caché por FEN sin que `lucia_core` sepa de bases de datos); `engines.py` (config efectiva = lo editado en BD, o `.env` si nunca se tocó; también decide en qué unidad se le pide esfuerzo a cada motor: profundidad en Stockfish, nodos en Lc0); `comparison.py` (RF-2.6: dónde discrepan dos análisis de la misma partida); la caché de posiciones se indexa por motor **y red neuronal**, porque el mismo Lc0 con otra red evalúa distinto; `stats.py` (agregaciones SQL para el dashboard; las comparaciones de nombre de usuario van en minúsculas porque chess.com canoniza el perfil pero el PGN conserva el casing original).
- **`worker/`** (implementado): `AnalysisWorker`, una cola en proceso (`asyncio.Queue`, un consumidor) — no Redis/arq todavía, se extrae si hace falta escalar (ver roadmap). Vive en `app.state`, un pub/sub simple en memoria reparte el progreso a quien esté conectado por WebSocket para ese `analysis_id`.
- Persistencia con SQLAlchemy 2 (async) + Alembic sobre SQLite (cuatro migraciones: `players`/`games`/`sync_state`, columnas de perfil, `analyses`/`analyzed_moves`/`position_cache`, y `engine_settings`).
- Genera `openapi.json` → `packages/shared-types` (tipos TS con `openapi-typescript`) vía `make types`. `scripts/export-openapi.py` lo vuelca **sin arrancar el servidor**, y el CI falla si el contrato quedó desincronizado.

### `apps/web` (React) — implementado

- Vite + React 19 + TypeScript. Rutas con **TanStack Router** en modo código (pocas rutas, sin plugin ni árbol generado): `/` (partidas), `/games/$gameId` (visor), `/engines` (motores).
- **`lib/api.ts`**: cliente tipado con los tipos generados desde el OpenAPI real (`make types`), así un cambio de endpoint rompe la compilación en vez de fallar en producción.
- **`features/games/`**: lista con filtros (jugador, color, control, puntuadas), paginación y disparo de sincronización.
- **`features/viewer/`**: `Chessboard` (envoltorio de **chessground**, API imperativa manejada con `useRef`), `MoveList` (jugadas clasificadas), `EvalChart` (**Recharts**, eje Y en probabilidad de victoria, no centipawns), `useAnalysisProgress` (WebSocket con respaldo HTTP). Navegación con teclado.
- **`features/engines/`**: configuración editable de los motores (RF-5.4).
- **`features/dashboard/`**: estadísticas (RF-3.1 a 3.3): marcador y rating por control, partidas por mes, rendimiento por apertura y pérdida de ventaja por fase.
- **`features/board/`**: tablero de análisis (RF-6). `tree.ts` tiene el árbol de variantes (añadir, promover, borrar, exportar a PGN) y es donde vive la validación de jugadas con chess.js; el servidor guarda ese árbol como JSON opaco.
- Estado de servidor con **TanStack Query**; el estado local del visor es `useState` — Zustand no hizo falta todavía.
- Tailwind CSS con tema claro/oscuro (preferencia del sistema + conmutador recordado en `localStorage`).

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
boards (id, title, tags_json, root_fen, tree_json, is_own_game, created_at, updated_at)
        -- RF-6. tree_json es un documento opaco para la API: quien valida
        -- jugadas es chess.js en el front, y duplicar esas reglas en el
        -- servidor solo daría dos sitios donde equivocarse.
engine_settings (name, threads, hash_mb, depth, multipv, updated_at)
               -- RF-5.4: parámetros editables por motor. NO guarda la ruta
               -- del binario a propósito (sería ejecución arbitraria por HTTP).
sync_state (player_id, last_synced_year, last_synced_month, last_synced_at)
           -- RF-1.3: qué mes sincronizar de nuevo (lucia_chesscom.months_to_sync).
analyses       (id, game_id, engine, depth, multipv, status, error,
                white_accuracy, black_accuracy, created_at, finished_at)
               -- status: queued | running | done | error. Varias por partida
               -- (distinto motor/profundidad), por eso es tabla propia.
analyzed_moves (id, analysis_id, ply, color, san, uci, fen_before,
                classification, phase, move_accuracy, win_percent_before,
                win_percent_after, best_move_uci)
               -- phase: RF-3.3, de lucia_core.phases.
               -- tal como los produce lucia_core.analysis.AnalyzedMove.
position_cache (fen, engine, depth, multipv, lines_json, created_at)
               -- RF-2.7: caché por FEN+config del motor. lines_json = una
               -- entrada por línea de MultiPV (score y pv serializados).
```

Pendiente (fases posteriores, no migrado todavía):

``` database
puzzles (id, source_move_id, fen, solution_uci, theme, srs_due_at, srs_ease)
```

## Flujos principales

1. **Sync** (implementado): `POST /sync` → `lucia_chesscom.ChessComClient` trae perfil, stats y archivos → `months_to_sync` decide qué meses faltan (RF-1.3) → por cada mes, secuencial, descarga partidas y hace upsert por `uuid` en `games` (idempotente) → actualiza `sync_state` → responde un resumen (meses sincronizados, partidas insertadas/actualizadas). Ver `lucia_api/services/chesscom_sync.py`.
2. **Análisis** (implementado): `POST /analysis {game_ids, engine, depth, multipv}` → crea una fila `Analysis` por partida (estado `queued`) → `AnalysisWorker.enqueue` (una cola `asyncio.Queue` en proceso, un consumidor) → el worker llama a `run_analysis`, que usa `lucia_core.analyze_game` con un `CachedEngineBridge` (consulta `position_cache` antes de preguntarle al motor real) → guarda `analyzed_moves` y las precisiones → publica progreso a quien esté conectado por `WS /ws/analysis/{id}` → al terminar, deja el estado en `done` o `error`. `GET /analysis/{id}` es el respaldo si no hubo WebSocket o se perdió algún evento. Ver `lucia_api/worker/` y `lucia_api/services/analysis.py`.
3. **Insight**: `GET /stats/...` agrega sobre `analyzed_moves` + `games` (consultas SQL, cacheadas).
4. **Puzzles**: job periódico toma blunders con solución única (MultiPV: 1ª línea ≫ 2ª) → crea `puzzles`.

## Decisiones clave

Ver [ADRs](adr/): monorepo, motores como sub-módulos compilados, Python orquesta / C++ solo en motores, GPL-3.0, SQLite local-first.

## Ver también

[06-mapa-del-proyecto.md](06-mapa-del-proyecto.md) tiene la versión en diagramas Mermaid de este documento (flujo general, módulos y secuencias) más una tabla de qué requerimiento vive en qué archivo. Se mantiene con el agente `mapeador`; si este documento cambia de forma estructural, el mapa debe actualizarse también.
