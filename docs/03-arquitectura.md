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
- **`analysis/`** (implementado) — `evaluate_positions()` recorre una partida y evalúa cada posición una sola vez (N+1 evaluaciones para N jugadas, no 2N); `analyze_game()` combina eso con `classification` y `accuracy` para producir `AnalyzedGame`/`AnalyzedMove`. Cada `PositionEval` guarda el MultiPV entero en `lines` (`EngineLine`: puntuación + continuación) y deriva de la primera su mejor jugada; de ahí sale `AnalyzedMove.alternatives` (RF-10.1), que son las líneas de la posición **anterior** a la jugada: lo que el motor proponía cuando todavía se podía elegir. La caché por FEN (RF-2.7) no vive aquí sino en `apps/api` (`CachedEngineBridge`), para que este paquete no dependa de ninguna base de datos.
- **`classification/`** (implementado) — `classify_move()`: convierte la caída de *win probability* en categorías (best / excellent / good / inaccuracy / mistake / blunder / missed_win). Umbrales en `ClassificationThresholds`, ajustables, testeados. `missed_win` detecta perder un mate forzado aunque la posición siga siendo ganadora en centipawns. `book` es la única categoría que no sale de un umbral: la decide `openings/` mirando si la posición sigue en la tabla ECO y quien llama la pasa en `in_opening_book` — pero **no tapa un error**, porque la tabla nombra también celadas (`1. f3 e5 2. g4` es el mate del loco y tiene nombre), así que una jugada de libro que hunde la posición se clasifica por lo que hizo.
- **`accuracy/`** (implementado) — `win_percent()` usa el modelo estadístico `lichess` que ya trae `python-chess` (`Score.wdl(model="lichess")`), sin reimplementarlo. `move_accuracy()` es la fórmula pública de Lichess (cp/mate → win% → precisión). `game_accuracy()` es una aproximación documentada del agregado por partida (media ponderada por volatilidad + media armónica), no una reimplementación exacta.
- **`phases/`** (implementado) — `detect_phase()` clasifica una posición (final por material restante; apertura por desarrollo y tope de jugadas) y `phases_by_ply()` la fuerza a avanzar en un solo sentido a lo largo de una partida. Umbrales como constantes con nombre, ajustables.
- **`insights/`** (implementado) — Extractores de patrones sobre partidas **ya analizadas**: `critical_moments()` (RF-2.8: jugada única, vuelco de la partida, ocasión perdida), `mistake_type()`/`mistakes_by_type()` (RF-3.4: reloj, táctico, final, posicional, comprobados en ese orden, de la causa más específica a la más general), `time_pressure()` (RF-3.5: calidad de juego por tramo de reloj restante) y `opening_exit_win_percent()` (lo que faltaba de RF-3.2). No se consulta al motor: todo sale de lo que el análisis guardó —clasificación, probabilidad de victoria antes/después, alternativas de RF-10.1 y relojes de RF-1.2—, así que las partidas analizadas antes también entran. Lee `MoveContext`, un tipo propio y no `analysis.AnalyzedMove`, porque el material llega de la base y trae además el reloj y las alternativas ya traducidas a probabilidad de victoria; todos sus porcentajes van desde el punto de vista de quien mueve, no de las blancas, porque un patrón es de quien lo comete. Umbrales explícitos y ajustables en `InsightThresholds` (10 puntos de win% entre la mejor línea y la segunda para "jugada única", 15 y cruzar el 50 % para un vuelco, 20 segundos para apuros de tiempo), por la misma razón que en `phases/` y `classification/`.
  Lo que aquí no está: los mates perdidos ya los marca `classification/` (`missed_win`) y las heurísticas de pieza colgada son RF-2.9, que necesita mirar el tablero y no solo la evaluación.
- **`openings/`** (implementado) — Clasificación ECO de aperturas sin red: `identify_opening()` recorre las jugadas de una partida y devuelve su apertura y hasta qué jugada llegó la teoría (`book_plies`), y `opening_of_pgn()` hace lo mismo desde el PGN, que es lo que necesita quien tiene la partida en texto (el importador de chess.com y la migración `9c2d51ab7e04`). La tabla es chess-openings de Lichess (CC0, dominio público) y **se versiona ya procesada** en `data/openings.tsv` —3.810 posiciones con su ECO y su nombre—, no se descarga al instalar: RNF-1 dice que la aplicación funciona sin red, y nombrar una apertura no puede ser la excepción ([ADR-0009](adr/0009-tabla-de-aperturas-versionada.md)). La genera `scripts/build-openings-table.py`, único punto que toca la red y solo para actualizarla.
  Dos decisiones que explican el resto: **la clave es la posición (EPD), no la secuencia de jugadas**, y por eso las transposiciones se reconocen solas —llegar a la Najdorf por otro orden da el mismo nombre—; y **la tabla tiene huecos** —solo nombra las posiciones donde termina alguna línea con nombre—, así que la búsqueda los tolera (hasta `MAX_UNKNOWN_PLIES_IN_A_ROW`) y se queda con la posición conocida más profunda, la del nombre más específico. Lo que corta la teoría es una racha de posiciones desconocidas, no el primer hueco. Pendiente de aquí: la comparación con el Lichess Opening Explorer (RF-3.6), que sí necesita red y es otra fuente.

### `packages/chesscom` (Python)

Cliente `httpx` asíncrono para la API pública de chess.com (`https://api.chess.com/pub/...`). Sin autenticación. Endpoints: `player/{u}`, `player/{u}/stats`, `player/{u}/games/archives`, `player/{u}/games/{Y}/{M}`. Parsea PGN con `python-chess`, extrae relojes `%clk`. Respeta `User-Agent` y rate limit (peticiones secuenciales, backoff en 429).

### `apps/api` (FastAPI)

- **Routers** (implementado): `sync` (RF-1), `games` (RF-5.3), `analysis` (RF-2: crear, consultar —con los momentos críticos de la partida, RF-2.8, deducidos al servir—, WebSocket de progreso, y `POST /analysis/position` para el análisis en vivo de una posición suelta), `engines` (RF-5.4: lee y edita parámetros; la ruta del binario es de solo lectura a propósito), `stats` (RF-3.1 a 3.5), `boards` (RF-6: CRUD de tableros de análisis).
- **`services/`**: la lógica que no es HTTP ni motor. `chesscom_sync.py` (RF-1); `analysis.py` (RF-2: `run_analysis` orquesta `lucia_core`, `analyze_position` para el análisis en vivo, `CachedEngineBridge` envuelve el motor con caché por FEN sin que `lucia_core` sepa de bases de datos); `engines.py` (config efectiva = lo editado en BD, o `.env` si nunca se tocó; también decide en qué unidad se le pide esfuerzo a cada motor: profundidad en Stockfish, nodos en Lc0); `comparison.py` (RF-2.6: dónde discrepan dos análisis de la misma partida); la caché de posiciones se indexa por motor **y red neuronal**, porque el mismo Lc0 con otra red evalúa distinto, y guarda sus líneas en el mismo formato que las alternativas de una jugada (`_serialize_line`), lo que permite a `alternatives_from_cache` servir las alternativas de un análisis anterior a RF-10 leyéndolas de `position_cache` en vez de re-analizar la partida; `insights.py` (RF-2.8/RF-3.4/RF-3.5: el puente entre la base y `lucia_core.insights` — carga las jugadas analizadas con su fase, su reloj y sus alternativas, y las convierte en `MoveContext`; las reglas de qué es un patrón viven en el núcleo, no aquí. Rescata de `position_cache` las alternativas de los análisis anteriores a RF-10, igual que hace el visor, y gira a la perspectiva de quien mueve las líneas guardadas, que se persisten desde la de las blancas); `stats.py` (agregaciones SQL para el dashboard; las comparaciones de nombre de usuario van en minúsculas porque chess.com canoniza el perfil pero el PGN conserva el casing original). **En estadísticas cada partida cuenta una sola vez**: una analizada con Stockfish y con Lc0 (RF-2.6) tiene dos filas en `analyses`, y sumarlas contaba dos veces la misma partida en precisión media, partidas analizadas y reparto por fases; se toma el análisis terminado más reciente de cada partida (`latest_analysis_ids`, `max(id)` y no `max(created_at)` porque el id no empata), que es además el que la interfaz enseña por defecto.
- **`worker/`** (implementado): `AnalysisWorker`, una cola en proceso (`asyncio.Queue`, un consumidor) — no Redis/arq todavía, se extrae si hace falta escalar (ver roadmap). Vive en `app.state`, un pub/sub simple en memoria reparte el progreso a quien esté conectado por WebSocket para ese `analysis_id`.
- Persistencia con SQLAlchemy 2 (async) + Alembic sobre SQLite (siete migraciones: `players`/`games`/`sync_state`, columnas de perfil, `analyses`/`analyzed_moves`/`position_cache`, `engine_settings`, `phase` en `analyzed_moves`, `boards` y `alternatives_json` en `analyzed_moves`).
- `GameSummary` —y por herencia `GameDetail`— lleva un campo derivado, `starts_from_custom_position`, que no es columna: sale de mirar la cabecera `[FEN ...]` del PGN (`Game.starts_from_custom_position`). Con él la interfaz avisa de las partidas que no empiezan en la posición estándar —odds chess, Chess960, partidas desde posición— en vez de enseñar un tablero con piezas de menos sin explicación.
- Genera `openapi.json` → `packages/shared-types` (tipos TS con `openapi-typescript`) vía `make types`. `scripts/export-openapi.py` lo vuelca **sin arrancar el servidor**, y el CI falla si el contrato quedó desincronizado.

### `apps/web` (React) — implementado

- Vite + React 19 + TypeScript. Rutas con **TanStack Router** en modo código (pocas rutas, sin plugin ni árbol generado): `/` (partidas), `/games/$gameId` (visor), `/boards` y `/boards/$boardId` (tableros de análisis), `/stats` (estadísticas) y `/engines` (motores). `Layout` marca en la navegación la sección a la que pertenece cada ruta, detalle incluido: sin eso, estando en el visor de una partida no se iluminaba nada.
- **`lib/api.ts`**: cliente tipado con los tipos generados desde el OpenAPI real (`make types`), así un cambio de endpoint rompe la compilación en vez de fallar en producción.
- **`lib/` (el resto)**: lo que tiene que dar el mismo resultado en todas las pantallas. `format.ts` (fechas, porcentajes, nombres de motor, controles de tiempo), `score.ts` (evaluación y probabilidad de victoria, ADR-0006), `classification.ts` (cómo se ve cada categoría de jugada), `insights.ts` (cómo se nombra y se explica cada tipo de error y cada motivo de momento crítico: los identificadores llegan de la API en inglés y se traducen una sola vez, con la regla con la que el núcleo decidió, para el visor y el dashboard), `moves.ts` (numeración: del ply interno al número que se lee en un tablero, partiendo de la posición real de la partida) y `chartTheme.ts` (la paleta que Recharts necesita como valores concretos, que Tailwind no le puede dar).
- **`features/games/`**: lista con filtros (jugador, color, control, puntuadas), paginación y disparo de sincronización.
- **`components/`**: lo que comparten varias pantallas. `board/` tiene las piezas de ajedrez reutilizables: `Chessboard` (envoltorio de **chessground**, API imperativa manejada con `useRef`), `boardConfig` (configuración de chessground y traducción de líneas del motor a flechas: la mejor destacada, hasta tres, cada una etiquetada con su evaluación — RF-5.2), `EvalBar` (barra de evaluación en probabilidad de victoria, orientada como el tablero), `BoardWithEvalBar` (las dos juntas, que es como aparecen en las dos pantallas) `MoveNavigator` (⏮ ◀ ▶ ⏭) con `useMoveNavigationKeys` (los mismos saltos por teclado, ignorando las pulsaciones que son de un campo), `MoveButton` (el botón que lleva a una posición: el control más repetido de la aplicación) y `EngineLineList` (la lista de líneas del motor: evaluación y continuación, con previsualización sobre el tablero al señalar una jugada; la comparten el panel del motor en vivo y las alternativas del visor — RF-10.2 —, y lo único que cambia entre las dos es si pulsar una jugada puede llevar el tablero hasta ahí). Fuera de `board/`: `Button`, `Panel`, `DataTable` (las tres tablas de la aplicación), `EngineSelect` (con qué motor analizar, en las dos pantallas que lo eligen), `Badge` y sus dos usos con significado —`ClassificationBadge` (la clasificación de una jugada, con su nombre siempre a mano y no solo el símbolo) y `CustomPositionBadge` (aviso de que la partida o el tablero no arranca en la posición estándar)—, `Feedback` (carga, error, éxito, aviso, progreso y vacío), `styles.ts` con las recetas de clases y las medidas compartidas para lo que no puede ser un componente, `Layout` y `ThemeToggle`. Que estas piezas vivan aquí y no dentro de una feature es lo que sostiene RNF-11: la misma lectura en las dos pantallas, sin copiar y pegar.
- **`features/viewer/`**: el visor de partidas: `MoveList` (jugadas clasificadas), `EvalChart` (**Recharts**, eje Y en probabilidad de victoria, no centipawns, con cada punto del color de su clasificación), `EngineComparison` (RF-2.6) y `useAnalysisProgress` (WebSocket con respaldo HTTP; el callback de fin va en una ref para no reabrir el socket en cada render). Desde RF-10.2 dibuja las mismas flechas múltiples que el tablero de análisis (`arrowsFromEngineLines`) y enseña en el lateral las alternativas de la posición en pantalla con `EngineLineList`; cuando la jugada que se hizo desde ahí salió mal, el panel se titula "Podías haber jugado, en vez de X" y marca en la lista cuál fue. Ojo al lado del que se cuentan: las alternativas viajan con la jugada **siguiente** a la posición que se ve, porque están tomadas desde la posición anterior a ella. Navegación con teclado y con los controles en pantalla, que son los mismos del tablero de análisis. La posición de partida sale del PGN y de ella sale también la numeración (`lib/moves.ts`), porque no toda partida empieza en la jugada 1.
- **`features/engines/`**: configuración editable de los motores (RF-5.4).
- **`features/dashboard/`**: estadísticas (RF-3.1 a 3.5): marcador y rating por control, partidas por mes, rendimiento por apertura —con su código ECO y la evaluación al salir de ella—, pérdida de ventaja por fase, reparto de errores por tipo y calidad de juego según el reloj restante.
- **`features/board/`**: tablero de análisis (RF-6). `tree.ts` tiene el árbol de variantes (añadir, promover, borrar, exportar a PGN) y es donde vive la validación de jugadas con chess.js; el servidor guarda ese árbol como JSON opaco. `EngineLines` enseña el MultiPV en vivo y se queda solo con los estados del motor (apagado, buscando, con error, sin líneas, con líneas), porque las líneas en sí las pinta `EngineLineList`, compartido con el visor: al señalar una jugada previsualiza esa continuación sobre el tablero y al pulsarla lo lleva hasta ahí (RF-6.2). El tablero, la barra de evaluación, las flechas y los controles de navegación se reutilizan de `components/board/`, y la pantalla ofrece los mismos atajos y el mismo orden de acciones que el visor.
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
            opening_eco, opening_name,
            clocks_json, played_at, year, month)
           -- platform_id = uuid de chess.com: upsert idempotente por partida.
           -- eco: la URL de apertura que reporta chess.com, dato de origen.
           -- opening_eco/opening_name: la apertura deducida de las jugadas con
           -- la tabla propia (lucia_core.openings, RF-3.2). Se guardan al
           -- importar porque agrupar por apertura en SQL lo necesita; NULL en
           -- las partidas que no empiezan en la posición estándar, que no
           -- tienen apertura ECO que nombrar. Es por lo que agrupan las
           -- estadísticas, no por eco.
           -- clocks_json: reloj tras cada jugada (lucia_chesscom.parse_move_clocks).
           -- starts_from_custom_position NO es columna: se deriva del pgn en
           -- Game (property) y solo la API la expone. Ver más arriba.
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
                win_percent_after, best_move_uci, alternatives_json)
               -- phase: RF-3.3, de lucia_core.phases.
               -- tal como los produce lucia_core.analysis.AnalyzedMove.
               -- alternatives_json: RF-10.1, las N mejores líneas de la
               -- posición ANTERIOR a esta jugada (la de fen_before), de mejor
               -- a peor, en el mismo formato que position_cache.lines_json.
               -- La SAN no se guarda: se deriva de fen_before al servir.
               -- Nullable: los análisis previos a RF-10 no la tienen, y para
               -- esos GET /analysis/{id} la busca en position_cache.
position_cache (fen, engine, depth, multipv, lines_json, created_at)
               -- RF-2.7: caché por FEN+config del motor. lines_json = una
               -- entrada por línea de MultiPV (score y pv serializados).
               -- Mismo formato que alternatives_json a propósito: así una
               -- posición cacheada sirve tal cual como alternativas.
```

Pendiente (fases posteriores, no migrado todavía):

``` database
puzzles (id, source_move_id, fen, solution_uci, theme, srs_due_at, srs_ease)
```

## Flujos principales

1. **Sync** (implementado): `POST /sync` → `lucia_chesscom.ChessComClient` trae perfil, stats y archivos → `months_to_sync` decide qué meses faltan (RF-1.3) → por cada mes, secuencial, descarga partidas y hace upsert por `uuid` en `games` (idempotente), deduciendo de paso la apertura de cada PGN con `lucia_core.openings` (`opening_eco`/`opening_name`, RF-3.2: se resuelve al guardar y no al consultar, porque las estadísticas agrupan por ella en SQL) → actualiza `sync_state` → responde un resumen (meses sincronizados, partidas insertadas/actualizadas). Ver `lucia_api/services/chesscom_sync.py`.
2. **Análisis** (implementado): `POST /analysis {game_ids, engine, depth, multipv}` → crea una fila `Analysis` por partida (estado `queued`) → `AnalysisWorker.enqueue` (una cola `asyncio.Queue` en proceso, un consumidor) → el worker llama a `run_analysis`, que replica las jugadas **desde la posición de partida del PGN** (`pgn_game.board()`: las partidas con `[SetUp "1"]` + `[FEN ...]` —odds chess, Chess960, "partidas desde posición"— no empiezan en la posición estándar, y de ahí sale también el flag `chess960` que `python-chess` traduce a `UCI_Chess960` para el motor) y las pasa a `lucia_core.analyze_game` con un `CachedEngineBridge` (consulta `position_cache` antes de preguntarle al motor real) → guarda `analyzed_moves` —con las alternativas de cada jugada en `alternatives_json`, que son las líneas de la posición previa (RF-10.1)— y las precisiones → publica progreso a quien esté conectado por `WS /ws/analysis/{id}` → al terminar, deja el estado en `done` o `error`. `GET /analysis/{id}` es el respaldo si no hubo WebSocket o se perdió algún evento; también es donde se rellenan las alternativas de los análisis anteriores a RF-10, leyéndolas de `position_cache` (`alternatives_from_cache`, solo si la clave coincide exactamente: posición, motor y red, límite y MultiPV), y donde la SAN de cada línea se deriva del `fen_before` de la jugada. Ver `lucia_api/worker/` y `lucia_api/services/analysis.py`.
3. **Análisis en vivo de una posición** (implementado, RF-5.2 / RF-6.2): el tablero de análisis manda `POST /analysis/position {fen, engine, multipv}` (con espera de ~400 ms para no disparar una petición por jugada de una secuencia rápida) → `analyze_position` responde las N mejores líneas **en centipawns o mate**, sin derivados → el cliente las dibuja como flechas y traduce la evaluación a probabilidad de victoria para la barra, replicando el modelo de Lichess del backend ([ADR-0006](adr/0006-probabilidad-de-victoria-en-el-cliente.md)). Mientras esa espera no vence, lo que hay en pantalla es la evaluación de la posición anterior, y el panel y la barra lo dicen en vez de dejar que la barra contradiga al tablero. A diferencia del flujo 2, no hay fila `Analysis` ni worker: la petición es síncrona y se apoya en `position_cache`.
4. **Insight** (implementado, RF-3): `GET /stats/{username}` agrega sobre `analyzed_moves` + `games`. El rendimiento por apertura (RF-3.2) agrupa por `games.opening_name`, la clasificación propia, y no por la URL que reporta chess.com: sale en más partidas, trae el código ECO —que chess.com no da— y reconoce transposiciones. Dos caminos que conviven: lo que se puede contar en SQL (marcador, rating, partidas por mes, precisión y reparto por fases) se agrega en la base, y lo que necesita leer jugada a jugada (tipo de error, tramos de reloj, evaluación al salir de la apertura) pasa por `services/insights.py` → `lucia_core.insights`. Las jugadas del jugador se cargan **una sola vez** por petición y los tres extractores miran ese mismo material; las del rival no entran, porque hablan de cómo juega el otro. Los momentos críticos (RF-2.8) no viven aquí sino en `GET /analysis/{id}`, que es donde se miran: son de una partida concreta y de los dos bandos.
5. **Puzzles**: job periódico toma blunders con solución única (MultiPV: 1ª línea ≫ 2ª) → crea `puzzles`.

## Decisiones clave

Ver [ADRs](adr/): monorepo, motores como sub-módulos compilados, Python orquesta / C++ solo en motores, GPL-3.0, SQLite local-first, probabilidad de victoria calculada también en el cliente, las alternativas por jugada como JSON en la fila de la jugada con respaldo en la caché de posiciones ([ADR-0007](adr/0007-alternativas-por-jugada-json-y-cache.md)), los patrones de juego deducidos al leer, sin persistirlos ni volver a llamar al motor ([ADR-0008](adr/0008-patrones-deducidos-al-leer.md)), y la tabla de aperturas versionada ya procesada en vez de descargada al instalar ([ADR-0009](adr/0009-tabla-de-aperturas-versionada.md)).

## Ver también

[06-mapa-del-proyecto.md](06-mapa-del-proyecto.md) tiene la versión en diagramas Mermaid de este documento (flujo general, módulos y secuencias) más una tabla de qué requerimiento vive en qué archivo. Se mantiene con el agente `mapeador`; si este documento cambia de forma estructural, el mapa debe actualizarse también.
