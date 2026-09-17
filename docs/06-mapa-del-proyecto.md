# 06 · Mapa del proyecto

Este documento es el mapa vivo de LUCIA: dónde vive cada cosa, cómo se conecta y
qué requerimiento o decisión la justifica. Sirve para dos lectores distintos:

- **Personas**, para orientarse rápido sin leer todo el repo antes de tocar algo.
- **IA (agentes de Claude Code)**, como referencia de consulta antes de un cambio:
  qué módulo toca, con qué otros habla, y qué doc detallada corresponde.

Lo mantiene actualizado el agente **`mapeador`**, y es un **cruce** del trabajo de
los demás agentes de calidad del proyecto: toma los nombres que fija
`bautizador`, la estructura que deja `minimalista` tras simplificar, y los
RF/RNF/ADR que registra `documentador`, y los refleja aquí. No repite la
narrativa de [03-arquitectura.md](03-arquitectura.md), de
[02-requerimientos.md](02-requerimientos.md) ni de
[07-coherencia-ui.md](07-coherencia-ui.md) (criterios de interfaz, del agente
`coherencia-ui`); apunta a ellas.

> Si un diagrama de aquí contradice el código actual, el código manda: es señal
> de que el mapeador necesita pasar. Ver [CLAUDE.md](../CLAUDE.md).

## 1 · Flujo general

```mermaid
flowchart TB
    subgraph Cliente
        WEB["apps/web<br/>React + Vite"]
    end

    subgraph Servidor["apps/api (FastAPI)"]
        ROUTERS["routers/<br/>sync · games · analysis · stats<br/>engines · boards · repertoire"]
        WORKER["worker/<br/>cola de análisis en background"]
        SVC_INSIGHTS["services/insights.py<br/>lee el análisis guardado"]
        SVC_SYNC["services/chesscom_sync.py<br/>importa partidas y les pone apertura"]
        SVC_GAMES["services/games.py<br/>de qué color jugó el usuario<br/>y qué le pasó (expresiones SQL)"]
        SVC_REP["services/repertoire.py<br/>compara con la caché ·<br/>refresh_repertoire (la red)"]
    end

    subgraph Nucleo["packages/core"]
        BRIDGE["engine/EngineBridge<br/>puente UCI"]
        ANALYSIS["analysis/GameAnalyzer"]
        CLASS["classification/MoveClassifier"]
        ACC["accuracy/"]
        INSIGHTS["insights/<br/>momentos críticos · tipos de error<br/>presión de reloj · salida de apertura"]
        OPENINGS["openings/<br/>tabla ECO versionada (ADR-0009)<br/>identify_opening · opening_of_pgn"]
    end

    CHESSCOM["packages/chesscom<br/>ChessComClient"]
    LICHESS["packages/lichess<br/>LichessExplorerClient"]
    DB[("SQLite<br/>data/lucia.db<br/>+ explorer_positions (caché EPD)")]
    ENGINES["engines/bin<br/>stockfish · lc0"]
    API_CHESSCOM["api.chess.com<br/>(externo)"]
    API_LICHESS["explorer.lichess.org<br/>(externo, con token)"]

    WEB -- "REST /api" --> ROUTERS
    WEB -- "WebSocket /ws" --> ROUTERS
    ROUTERS --> WORKER
    ROUTERS --> DB
    ROUTERS -- "GET /games (filtros RF-5.3)<br/>+ GET /stats" --> SVC_GAMES
    ROUTERS -- "GET /stats · GET /analysis/{id}" --> SVC_INSIGHTS
    SVC_INSIGHTS --> DB
    SVC_INSIGHTS -- "sin motor (ADR-0008)" --> INSIGHTS
    ROUTERS -- "POST /analysis/position<br/>(síncrono, sin cola)" --> BRIDGE
    WORKER --> BRIDGE
    WORKER --> ANALYSIS
    ANALYSIS --> CLASS
    ANALYSIS --> ACC
    ANALYSIS -- "hasta dónde llega la teoría<br/>(clasificación book, RF-2.2)" --> OPENINGS
    BRIDGE -- "UCI (stdin/stdout)" --> ENGINES
    ROUTERS --> SVC_SYNC
    SVC_SYNC --> CHESSCOM
    SVC_SYNC -- "opening_of_pgn → games.opening_eco/name" --> OPENINGS
    SVC_SYNC --> DB
    CHESSCOM -- "HTTPS" --> API_CHESSCOM
    ROUTERS -- "GET /repertoire (sin red)<br/>POST /repertoire/refresh (con red)" --> SVC_REP
    SVC_REP -- "lee partidas y caché;<br/>GET /repertoire se queda aquí" --> DB
    SVC_REP -- "solo refresh_repertoire<br/>(tope por llamada, ADR-0010)" --> LICHESS
    LICHESS -- "HTTPS masters(fen)" --> API_LICHESS
    ANALYSIS --> DB
```

Detalle narrativo y modelo de datos completo: [03-arquitectura.md](03-arquitectura.md).

## 2 · Módulos y dependencias

```mermaid
graph LR
    subgraph JS["Workspace pnpm"]
        subgraph WEB["@lucia/web"]
            board["features/board<br/>tablero de análisis"]
            viewer["features/viewer<br/>visor de partidas<br/>+ CriticalMoments"]
            screens["features/dashboard (+ RepertoireSection)<br/>games · engines · otras pantallas"]
            boardui["components/board<br/>Chessboard · EvalBar · boardConfig<br/>BoardWithEvalBar · MoveNavigator<br/>MoveButton · EngineLineList<br/>useMoveNavigationKeys"]
            ui["components/<br/>Button · Panel · Feedback · DataTable<br/>Badge (Classification · CustomPosition)<br/>EngineSelect · FilterBar · FieldLabel<br/>RecordBadges · Layout · styles"]
            lib["lib/<br/>api · score · format · moves<br/>classification · chartTheme · insights"]
        end
        types["@lucia/shared-types"]
    end

    subgraph PY["Workspace uv"]
        subgraph API["lucia_api"]
            api_sync["services/chesscom_sync.py"]
            api_analysis["services/analysis.py"]
            api_stats["services/stats.py"]
            api_games["services/games.py<br/>color y resultado del jugador"]
            api_insights["services/insights.py"]
            api_repertoire["services/repertoire.py<br/>comparación + refresh"]
            api_deps["dependencies.py<br/>resolved_username · clientes"]
        end
        subgraph CORE["lucia_core"]
            core_analysis["analysis · classification<br/>accuracy · engine · phases"]
            core_insights["insights"]
            core_openings["openings<br/>+ data/openings.tsv"]
        end
        chesscom["lucia_chesscom"]
        lichess["lucia_lichess<br/>Opening Explorer"]
    end

    board --> boardui
    viewer --> boardui
    board --> ui
    viewer --> ui
    boardui --> ui
    screens --> ui
    board --> lib
    viewer --> lib
    boardui --> lib
    ui --> lib
    screens --> lib
    lib --> types
    api_sync --> chesscom
    api_sync --> core_openings
    api_analysis --> core_analysis
    core_analysis --> core_openings
    api_stats --> api_games
    api_stats --> api_insights
    api_stats --> core_insights
    api_insights --> core_insights
    api_repertoire --> api_games
    api_repertoire --> lichess
    types -. "make types:<br/>export-openapi.py + openapi-typescript" .-> API
```

Regla: `lucia_core`, `lucia_chesscom` y `lucia_lichess` no dependen de
`lucia_api` (evita ciclos); `lucia_api` orquesta a los tres. Si un cambio rompe esta dirección, es una señal
para el agente `minimalista`. Se comprobó tras los extractores de patrones:
`lucia_core.insights` solo recibe `MoveContext` ya construidos, no conoce ni la
base de datos ni la API. Se volvió a comprobar con `lucia_core.openings`: la
tabla ECO es un dato del propio núcleo (`openings/data/openings.tsv`,
[ADR-0009](adr/0009-tabla-de-aperturas-versionada.md)) y tanto
`services/chesscom_sync.py` como `analysis/` la usan hacia abajo, sin vuelta.
`routers/stats.py` y `routers/analysis.py` entran por
`services/`, que es quien lee SQLite y traduce a los tipos del núcleo
([ADR-0008](adr/0008-patrones-deducidos-al-leer.md)). Con los filtros de
`GET /games` (RF-5.3) apareció una dependencia más dentro de `lucia_api`:
`routers/games.py` y `services/stats.py` importan las mismas expresiones SQL de
`services/games.py` (`is_white`, `is_black`, `is_player`, `player_side`,
`player_color`, `outcome_of`, `DRAW_RESULTS`) —de qué color jugó el usuario y
qué le pasó—, en vez de repetirlas cada uno. `services/games.py` no depende de
nadie más que del modelo `Game`, así que sigue siendo una sola vía.

Con el repertorio (RF-3.6) entró el segundo cliente externo del workspace,
`packages/lichess` (`lucia_lichess`), hermano de `packages/chesscom`: mismo
sitio en el grafo —lo importa `lucia_api`, no al revés— y misma regla de una
sola vía. La diferencia está dentro de `lucia_api`: solo
`services/repertoire.py::refresh_repertoire` lo usa, mientras
`compare_repertoire` se queda en SQLite ([ADR-0010](adr/0010-repertorio-con-red-y-cacheado.md)).
`services/repertoire.py` reutiliza `is_white` de `services/games.py`, la misma
pieza que ya comparten `routers/games.py` y `services/stats.py`. Y la
resolución del jugador por defecto, que estaba repetida en `routers/stats.py` y
`routers/repertoire.py`, vive ahora en `lucia_api/dependencies.py`
(`resolved_username`).

Dentro de `@lucia/web` la dirección también es de una sola vía: las pantallas
(`features/*`) importan de `components/` —lo compartido entre dos o más de
ellas—, nunca al revés. Las piezas de tablero que usan el visor y el tablero de
análisis viven en `components/board/` —desde RF-10, también `EngineLineList`, la
lista de líneas del motor que comparten los dos—; el resto de lo común (botón,
panel, estados, recetas de clases), en `components/`. Si un componente de
`components/` empieza a importar de un `features/`, es que no era compartido y
su sitio es esa pantalla. La barra de filtros de `GamesPage` y `DashboardPage`
está en `components/FilterBar.tsx` por eso mismo (con la espera de 400 ms al
teclear dentro de `FilterText`, ya no en cada pantalla), y la etiqueta de campo
que comparten esa barra, Sincronizar, `BoardsPage` y `EnginesPage`, en
`components/FieldLabel.tsx`. Sí puede apoyarse en `lib/` —funciones puras y hooks
sin pantalla: `EngineSelect` usa `format.ts`, `ClassificationBadge` usa
`classification.ts`—, que es la capa de abajo de todos. Inventario:
[apps/web/src/components/README.md](../apps/web/src/components/README.md).

## 3 · Flujos principales

### Sincronizar con chess.com (RF-1, implementado)

```mermaid
sequenceDiagram
    participant U as Usuario (web)
    participant A as apps/api (routers/sync.py)
    participant S as services/chesscom_sync.py
    participant C as lucia_chesscom
    participant O as lucia_core.openings
    participant CC as api.chess.com
    participant DB as SQLite

    U->>A: POST /sync {username?}
    A->>S: sync_player(session, client, username)
    S->>C: get_player + get_stats
    C->>CC: GET /player/{u}, /player/{u}/stats
    CC-->>C: perfil, ratings
    S->>DB: upsert players (country, joined_at, ratings_json)
    S->>C: get_archives(username)
    C->>CC: GET /player/{u}/games/archives
    CC-->>C: lista de meses
    S->>S: months_to_sync(archivos, sync_state) [RF-1.3]
    loop por cada mes pendiente, secuencial
        S->>C: get_month_games(year, month)
        C->>CC: GET /player/{u}/games/{Y}/{M}
        CC-->>C: partidas (PGN + relojes)
        S->>O: opening_of_pgn(pgn) [RF-3.2]
        O-->>S: Opening(eco, name) o nada
        S->>DB: upsert games (por uuid, idempotente)<br/>incluidos opening_eco y opening_name
    end
    S->>DB: upsert sync_state (último mes)
    S-->>A: SyncSummary
    A-->>U: resumen de sincronización
```

### Listar partidas con filtros (RF-5.3, implementado)

Nueve filtros sobre lo que la sincronización ya guardó, sin llamar al motor.
Las reglas (qué filtro necesita jugador, cómo se leen las fechas) están en
[02-requerimientos.md § RF-5](02-requerimientos.md); aquí solo el recorrido.

```mermaid
sequenceDiagram
    participant U as Usuario
    participant P as GamesPage (features/games)
    participant F as components/FilterBar<br/>FilterText · FilterSelect · FieldLabel
    participant AP as lib/api.ts (listGames)
    participant R as apps/api (routers/games.py)
    participant SG as services/games.py
    participant DB as SQLite

    U->>F: escribir o elegir en un campo
    F->>F: al teclear, esperar 400 ms (TYPING_DELAY_MS)
    F->>P: onChange(valor) → updateFilter
    P->>AP: listGames({username, color, result, opponent,<br/>opening, since, until, time_class, rated, limit, offset})
    AP->>R: GET /games?...
    R->>R: _filter_conditions(...) [las comparten página y conteo]
    Note over R,SG: result · opponent · color necesitan username:<br/>sin él se ignoran (la web los deshabilita)
    R->>SG: is_white · is_black · is_player · outcome_of
    SG-->>R: expresiones SQL del lado del jugador
    R->>DB: SELECT games WHERE ... LIMIT/OFFSET
    R->>DB: SELECT count(*) WHERE ... [mismas condiciones]
    R-->>AP: 200: GameSummary[] + cabecera X-Total-Count
    AP-->>P: GamePage {games, total}
    P-->>U: DataTable + "N de TOTAL partidas"
```

### Analizar una partida (RF-2, implementado)

```mermaid
sequenceDiagram
    participant U as Usuario (web)
    participant A as apps/api (routers/analysis.py)
    participant WK as AnalysisWorker
    participant S as services/analysis.py
    participant E as EngineBridge (Stockfish/Lc0)
    participant O as lucia_core.openings
    participant DB as SQLite

    U->>A: POST /analysis {game_ids, engine, depth, multipv}
    A->>DB: crear Analysis (status=queued) por partida
    A->>WK: enqueue(analysis_id)
    A-->>U: 200: resumen con status=queued

    U->>A: WS /ws/analysis/{id}
    WK->>WK: consumidor toma el siguiente de la cola
    WK->>S: run_analysis(analysis, game, on_progress)
    S->>S: pgn_starting_board = pgn_game.board()<br/>(la posición del PGN, no chess.Board(): SetUp/FEN → odds, Chess960)
    Note over S,E: de ese tablero sale el flag chess960, que python-chess<br/>traduce a UCI_Chess960 al hablar con el motor
    S->>DB: status=running
    S->>O: identify_opening(board, moves) → book_plies
    Note over S,O: hasta ese ply, classify_move recibe in_opening_book=True<br/>y devuelve la categoría "book" (RF-2.2)
    loop cada posición de la partida
        S->>DB: ¿FEN+engine+depth+multipv en position_cache?
        alt no está en caché
            S->>E: analyse(board)
            E-->>S: eval, mejores líneas (MultiPV)
            S->>DB: guardar en position_cache
        end
        S->>WK: on_progress(ply, total)
        WK-->>U: WS: {status: running, ply, total}
    end
    S->>DB: guardar analyzed_moves + white/black_accuracy<br/>(cada jugada con alternatives_json:<br/>las líneas de la posición previa, RF-10.1)
    S->>DB: status=done (o error, con el motivo)
    WK-->>U: WS: {status: done | error}
```

`GET /analysis/{id}` es el respaldo si no hubo WebSocket conectado o se
perdió algún evento (hay una ventana de carrera pequeña y documentada entre
suscribirse y el estado real, ver docstring de `analysis_progress`), y es
también donde se rellenan las alternativas de los análisis anteriores a RF-10,
leyéndolas de `position_cache` con `alternatives_from_cache`
([ADR-0007](adr/0007-alternativas-por-jugada-json-y-cache.md)).

### Analizar una posición en vivo (RF-5.2 / RF-6.2, implementado)

Flujo 3 de [03-arquitectura.md § Flujos principales](03-arquitectura.md): no
hay fila `Analysis` ni cola, la petición es síncrona y el cliente es quien
traduce la evaluación a probabilidad de victoria ([ADR-0006](adr/0006-probabilidad-de-victoria-en-el-cliente.md)).

```mermaid
sequenceDiagram
    participant U as Usuario
    participant B as BoardPage (features/board)
    participant V as components/board<br/>BoardWithEvalBar · Chessboard<br/>boardConfig · EngineLineList
    participant A as apps/api (routers/analysis.py)
    participant S as services/analysis.py
    participant E as CachedEngineBridge → EngineBridge
    participant DB as SQLite (position_cache)

    U->>B: elegir motor (components/EngineSelect)
    U->>B: jugar / navegar (tablero, teclado, árbol)
    B->>B: esperar ANALYSIS_DELAY_MS antes de pedir
    Note over U,B: mientras se espera, lo que se ve es de la posición<br/>anterior: isEvaluationStale lo dice (barra sin valor,<br/>panel del motor en "analizando")
    B->>A: POST /analysis/position {fen, engine, depth, multipv}
    A->>S: analyze_position(session, fen, ...)
    S->>DB: ¿FEN+engine+depth+multipv en position_cache?
    alt no está en caché
        S->>E: analyse(board)
        E-->>S: líneas MultiPV (cp o mate)
        S->>DB: guardar en position_cache
    end
    S-->>A: EngineLine[] (rank, score_cp/score_mate, pv_uci, pv_san)
    A-->>B: 200: líneas del motor
    B->>V: arrowsFromEngineLines(lines) → engineArrows
    B->>B: whiteWinPercentFromScore(línea 1) [lib/score.ts]
    B->>V: BoardWithEvalBar(whiteWinPercent, engineArrows, orientation)
    V-->>U: flechas sobre el tablero + barra de evaluación

    opt señalar una jugada en EngineLineList (previsualización)
        U->>B: hover/foco sobre una jugada de una línea
        B->>V: arrowsFromPreviewLine(pv recortado) → engineArrows
        V-->>U: la continuación previsualizada sustituye a las flechas del motor
    end

    opt pulsar esa jugada (jugar la línea)
        U->>B: clic en la jugada n de una línea
        B->>B: playLine(SAN 1..n) → addMove en features/board/tree.ts
        B->>V: nueva posición actual (y vuelve a empezar el ciclo)
    end
```

### Ver las alternativas de una jugada guardada (RF-10, implementado)

En el visor la fuente es distinta: no llama al motor, pinta el análisis ya
guardado. Desde RF-10 ese análisis trae todas las líneas de cada posición, así
que el visor dibuja las mismas flechas y la misma lista que el tablero de
análisis sin pedir nada más.

```mermaid
sequenceDiagram
    participant U as Usuario
    participant G as GameViewerPage (features/viewer)
    participant L as components/board<br/>EngineLineList · boardConfig<br/>BoardWithEvalBar
    participant A as apps/api (routers/analysis.py)
    participant S as services/analysis.py
    participant DB as SQLite

    U->>G: abrir la partida
    G->>A: GET /analysis/{id}
    A->>DB: analyses + analyzed_moves
    alt la jugada guardó alternatives_json (RF-10.1)
        A->>S: engine_lines_from_serialized(alternatives_json, fen_before)
    else análisis anterior a RF-10 (alternatives_json = NULL)
        A->>S: alternatives_from_cache(analysis, moves)
        S->>DB: position_cache por FEN + motor + límite + multipv
        Note over S,DB: solo si la clave coincide exacta,<br/>lo que no coincide se sirve vacío (ADR-0007)
    end
    A-->>G: AnalyzedMoveOut.alternatives: EngineLineOut[]<br/>(el mismo tipo del análisis en vivo)

    U->>G: navegar a una jugada (lista, gráfico, teclado)
    Note over G: las alternativas de la posición en pantalla son las<br/>de la jugada siguiente: se tomaron antes de jugarla
    G->>L: arrowsFromEngineLines(alternatives) → engineArrows
    L-->>U: flechas múltiples + panel de alternativas, con la<br/>jugada real marcada (playedUci) y, si fue un error,<br/>el título "podías haber jugado, en vez de esta"

    opt señalar una jugada de una alternativa
        U->>G: hover/foco sobre una jugada de una línea
        G->>L: arrowsFromPreviewLine(pv recortado)
        L-->>U: la continuación previsualizada sustituye a las flechas
    end

    opt ni alternativas guardadas ni caché que coincida
        G->>L: una sola flecha, la de best_move_uci
        L-->>U: el panel dice que ese análisis no las guardó
    end
```

A diferencia del tablero de análisis, aquí pulsar una jugada de una línea solo
la dibuja: no hay `onPlayLine`, porque una partida terminada no se continúa.

### Comparar el repertorio con la teoría de maestros (RF-3.6, implementado)

Dos recorridos separados a propósito ([ADR-0010](adr/0010-repertorio-con-red-y-cacheado.md)):
`GET /repertoire` responde con lo que ya está en `explorer_positions` y no sale
a internet nunca; `POST /repertoire/refresh` es lo único que pregunta a
Lichess, con tope por llamada para no dejar la petición HTTP colgada. Los
umbrales (hasta qué jugada se compara, cuántas partidas de maestros hacen
teoría) están en [02-requerimientos.md § RF-3](02-requerimientos.md).

```mermaid
sequenceDiagram
    participant U as Usuario
    participant D as RepertoireSection<br/>(features/dashboard)
    participant R as apps/api (routers/repertoire.py)
    participant SR as services/repertoire.py
    participant LI as lucia_lichess
    participant EX as explorer.lichess.org
    participant DB as SQLite

    Note over U,DB: Ver el repertorio: sin red
    U->>D: abrir Estadísticas
    D->>R: GET /repertoire?username
    R->>SR: compare_repertoire(session, resolved_username)
    SR->>DB: games del jugador + explorer_positions (por EPD)
    SR->>SR: primera jugada propia fuera del libro,<br/>y se para ahí (MAX_REPERTOIRE_PLIES)
    SR-->>R: departures + games_compared<br/>+ positions_known / positions_missing
    R-->>D: RepertoireOut (+ positions_per_refresh,<br/>seconds_between_positions)
    D-->>U: tabla de salidas con RecordBadges y, si falta<br/>teoría, lo dice en vez de darla por buena

    Note over U,DB: Rellenar la caché: la única llamada externa
    U->>D: "Consultar a Lichess"
    D->>R: POST /repertoire/refresh (username, budget)
    R->>SR: refresh_repertoire(session, client, username, budget)
    loop hasta agotar el tope
        SR->>DB: posiciones que faltan ahora (se recalculan cada ronda)
        SR->>LI: masters(fen)
        LI->>EX: GET /masters?fen (espaciado, con reintento)
        EX-->>LI: jugadas de maestros
        SR->>DB: insert explorer_positions (epd, masters_json)
    end
    alt el explorador falla o limita
        SR->>DB: commit de lo conseguido hasta ahí
        R-->>D: 502 con el motivo (LichessExplorerError)
    else
        SR-->>R: (fetched, remaining)
        R-->>D: RefreshResultOut
    end
    D-->>U: cuántas se trajeron y si hay que volver a pulsar
```

### Deducir patrones del análisis guardado (RF-2.8 · RF-3.2 · RF-3.4 · RF-3.5, implementado)

Los patrones no se persisten ni vuelven a llamar al motor: se deducen al leer,
sobre lo que el análisis ya guardó ([ADR-0008](adr/0008-patrones-deducidos-al-leer.md)).
El núcleo (`lucia_core.insights`) solo ve `MoveContext`; quien lee SQLite y los
construye es `services/insights.py`. Las reglas y umbrales concretos están en
[02-requerimientos.md § RF-2 y RF-3](02-requerimientos.md).

```mermaid
sequenceDiagram
    participant U as Usuario (web)
    participant D as DashboardPage / GameViewerPage
    participant R as routers/stats.py · routers/analysis.py
    participant ST as services/stats.py
    participant IN as services/insights.py
    participant CI as lucia_core.insights
    participant DB as SQLite

    Note over U,DB: Dashboard: patrones agregados del jugador
    U->>D: abrir dashboard
    D->>R: GET /stats
    R->>ST: get_player_stats(session, username)
    ST->>IN: player_move_contexts(session, username)
    IN->>DB: analyzed_moves + analyses + games<br/>filtrando con latest_analysis_ids()<br/>(una partida cuenta una vez)
    IN->>IN: alternatives_from_cache si el análisis<br/>es anterior a RF-10 (ADR-0007)
    IN-->>ST: [(game_id, MoveContext)]
    ST->>CI: mistakes_by_type(moves) [RF-3.4]
    ST->>CI: time_pressure(moves) + is_time_trouble [RF-3.5]
    ST->>CI: opening_exit_win_percent(moves) [RF-3.2]
    CI-->>ST: recuentos por tipo, tramos de reloj, win% al salir
    ST-->>R: PlayerStats → PlayerStatsOut
    R-->>D: by_mistake_type · by_time_left · time_trouble<br/>+ columna "Al salir" por apertura
    D-->>U: MistakeTypeSection · TimePressureSection<br/>(etiquetas y colores de lib/insights.ts)

    Note over U,DB: Visor: momentos críticos de una partida
    U->>D: abrir la partida
    D->>R: GET /analysis/{id}
    R->>DB: analyses + analyzed_moves (+ alternativas)
    R->>IN: analysis_critical_moments(moves, cached_alternatives)
    IN->>CI: critical_moments(contexts, thresholds)
    CI-->>IN: jugada única · vuelco · ocasión perdida
    IN-->>R: CriticalMoment[]
    R-->>D: AnalysisDetail.critical_moments
    D-->>U: panel CriticalMoments (features/viewer)
```

## 4 · Ubicación por requerimiento

Tabla de cruce: requerimiento → dónde vive → qué doc lo explica en detalle. Se
amplía a medida que se implementa cada RF (ver [05-roadmap.md](05-roadmap.md)).

| Requerimiento | Módulo / archivo | Doc detallada |
| --- | --- | --- |
| RF-1 · Importación chess.com | `packages/chesscom/lucia_chesscom/` (cliente, PGN, sync incremental), `apps/api/lucia_api/services/chesscom_sync.py` (que además fija `opening_eco`/`opening_name` con `lucia_core.openings.opening_of_pgn`), `db/models.py`, `routers/sync.py` | [03-arquitectura.md § chesscom](03-arquitectura.md) |
| RF-2 · Análisis con motores | `packages/core/lucia_core/` (engine, `analysis/` con `EngineLine` y el MultiPV completo en `PositionEval.lines`, classification, accuracy), `apps/api/lucia_api/services/analysis.py`, `worker/`, `routers/analysis.py` | [03-arquitectura.md § core / api](03-arquitectura.md) |
| RF-2.2 · Categoría "Libro" | `packages/core/lucia_core/openings/__init__.py` (`Opening`, `default_book`, `GameOpening`, `identify_opening`, `opening_of_pgn`) con la tabla `openings/data/openings.tsv` generada por `scripts/build-openings-table.py`, `packages/core/lucia_core/classification/__init__.py` (`classify_move(..., in_opening_book=...)` → `"book"`), `packages/core/lucia_core/analysis/__init__.py` (`book_plies`), `apps/web/src/lib/classification.ts` (etiqueta "Teoría" y su `description`, que usa el resumen de jugadas del visor) | [ADR-0009](adr/0009-tabla-de-aperturas-versionada.md), [02-requerimientos.md § RF-2](02-requerimientos.md) |
| RF-2.6 · Lc0 y discrepancias | `apps/api/lucia_api/services/comparison.py`, `apps/web/src/features/viewer/EngineComparison.tsx` | [05-roadmap.md § fase 2](05-roadmap.md) |
| RF-2.8 · Momentos críticos | `packages/core/lucia_core/insights/__init__.py` (`MoveContext`, `InsightThresholds`, `CriticalMoment`, `critical_moments`), `apps/api/lucia_api/services/insights.py` (`analysis_critical_moments`, sobre el análisis ya guardado), `routers/analysis.py` (`AnalysisDetail.critical_moments`), `apps/web/src/features/viewer/CriticalMoments.tsx` + `apps/web/src/lib/insights.ts` (`criticalMomentStyle`) | [ADR-0008](adr/0008-patrones-deducidos-al-leer.md), [02-requerimientos.md § RF-2](02-requerimientos.md) |
| RF-3.1-3.3 · Dashboard | `apps/api/lucia_api/services/stats.py` + `routers/stats.py` (cada partida cuenta una vez, con `latest_analysis_ids` de `services/insights.py`), `packages/core/lucia_core/phases/`, `apps/web/src/features/dashboard/` (tablas con `components/DataTable.tsx`, gráficos con la paleta de `lib/chartTheme.ts`); la tabla de aperturas es RF-3.2 y agrupa por `Game.opening_eco` / `Game.opening_name` —la apertura propia de `lucia_core.openings`, ya no la URL de chess.com—, con columna ECO en `apps/web/src/features/dashboard/DashboardPage.tsx` y `OpeningStatsOut.eco` en `routers/stats.py`; la columna "Al salir" sale de `lucia_core.insights.opening_exit_win_percent` y `services/stats.py::_opening_exit_by_opening` | [03-arquitectura.md](03-arquitectura.md), [02-requerimientos.md § RF-3](02-requerimientos.md) |
| RF-3.4 · Distribución de errores por tipo | `packages/core/lucia_core/insights/__init__.py` (`mistake_type`, `mistakes_by_type`), `apps/api/lucia_api/services/stats.py` (`by_mistake_type`) + `routers/stats.py`, `apps/web/src/features/dashboard/DashboardPage.tsx` (`MistakeTypeSection`) con las etiquetas de `apps/web/src/lib/insights.ts` (`mistakeTypeStyle`) | [ADR-0008](adr/0008-patrones-deducidos-al-leer.md), [02-requerimientos.md § RF-3](02-requerimientos.md) |
| RF-3.5 · Gestión del tiempo y *time trouble* | `packages/core/lucia_core/insights/__init__.py` (`time_pressure`, `is_time_trouble`, `TimeBucketStats`), `apps/api/lucia_api/services/stats.py` (`by_time_left`, `time_trouble`, con los relojes de `Game.clocks_json`) + `routers/stats.py`, `apps/web/src/features/dashboard/DashboardPage.tsx` (`TimePressureSection`, tramos con `formatTimeLeftBucket` de `lib/insights.ts`) | [ADR-0008](adr/0008-patrones-deducidos-al-leer.md), [02-requerimientos.md § RF-3](02-requerimientos.md) |
| RF-3.6 · Repertorio contra la teoría de maestros | `packages/lichess/lucia_lichess/` (`LichessExplorerClient.masters`, `ExplorerPosition`), `apps/api/lucia_api/services/repertoire.py` (`compare_repertoire` sin red, `refresh_repertoire` con tope por llamada), `routers/repertoire.py` (`GET /repertoire`, `POST /repertoire/refresh`), `apps/api/lucia_api/db/models.py` (`ExplorerPositionCache`, tabla `explorer_positions`, migración `apps/api/migrations/versions/b4e8c17f0a92_agrega_cache_del_opening_explorer.py`), `apps/web/src/features/dashboard/RepertoireSection.tsx` (con `components/RecordBadges.tsx`) | [ADR-0010](adr/0010-repertorio-con-red-y-cacheado.md), [02-requerimientos.md § RF-3](02-requerimientos.md) |
| RF-3.7-3.8 · Insight avanzado restante | pendiente (fase 2): tendencias temporales (RF-3.7), rivales recurrentes (RF-3.8) | [05-roadmap.md § fase 2](05-roadmap.md) |
| Lectura de patrones sin persistirlos | `apps/api/lucia_api/services/insights.py` (`latest_analysis_ids`, `player_move_contexts`, `analysis_critical_moments`): traduce filas de `analyzed_moves` a `MoveContext` para que `lucia_core.insights` no sepa de SQLite ni vuelva a llamar al motor | [ADR-0008](adr/0008-patrones-deducidos-al-leer.md) |
| RF-4 · Entrenamiento | pendiente (fase 3) | [05-roadmap.md](05-roadmap.md) |
| RF-5.1 · Visor de partida | `apps/web/src/features/viewer/` (`GameViewerPage`, con `parsePgn` sacando de ahí la posición inicial de la partida; `MoveList`, `EvalChart`, `useAnalysisProgress`); la numeración de las jugadas sale de `apps/web/src/lib/moves.ts` y los colores del gráfico de `lib/chartTheme.ts`; tablero, barra, botón de jugada (`MoveButton`), lista de líneas del motor (`EngineLineList`) y navegación —con `useMoveNavigationKeys`— se importan de `apps/web/src/components/board/` | [03-arquitectura.md § web](03-arquitectura.md) |
| RF-5.2 · Análisis en vivo y flechas del motor | entregado en el tablero de análisis y, desde RF-10.2, con flechas múltiples y previsualización también en el visor (sobre el análisis guardado, sin llamar al motor); queda RF-6.6 (fase 2). `apps/api/lucia_api/routers/analysis.py` (`POST /analysis/position`) + `services/analysis.py::analyze_position`; `apps/web/src/components/board/` (`boardConfig.ts` con `arrowsFromEngineLines` y `arrowsFromPreviewLine`, `EvalBar.tsx`, `Chessboard.tsx` con la prop `engineArrows`, `BoardWithEvalBar.tsx`); con qué motor se pide lo elige `apps/web/src/components/EngineSelect.tsx` en las dos pantallas | [03-arquitectura.md § flujo 3](03-arquitectura.md) |
| RF-5.3 · Listado de partidas con filtros | `apps/api/lucia_api/routers/games.py` (nueve filtros: `username`, `color`, `result`, `opponent`, `opening`, `since`, `until`, `time_class`, `rated`, con `_filter_conditions` compartido entre la página y el conteo, y la cabecera `X-Total-Count`), `apps/api/lucia_api/services/games.py` (el lado del jugador en SQL, compartido con `services/stats.py`), `apps/web/src/features/games/GamesPage.tsx` (tabla con `components/DataTable.tsx`, campos con `components/FilterBar.tsx` y `components/FieldLabel.tsx`, total en `lib/api.ts::GamePage`) | [02-requerimientos.md § RF-5](02-requerimientos.md) (reglas de los filtros), [03-arquitectura.md](03-arquitectura.md) |
| RF-5.4 · Config. de motores | `apps/api/lucia_api/routers/engines.py` + `services/engines.py`, `apps/web/src/features/engines/` | [03-arquitectura.md](03-arquitectura.md) |
| RF-5.6 · Tema claro/oscuro | `apps/web/src/components/ThemeToggle.tsx` | [02-requerimientos.md § RF-5](02-requerimientos.md) |
| Contrato API ↔ front | `scripts/export-openapi.py`, `openapi.json`, `packages/shared-types/` | [03-arquitectura.md § api](03-arquitectura.md) |
| RF-6 · Tablero de análisis | `apps/api/lucia_api/routers/boards.py`, `apps/web/src/features/board/` (`tree.ts` = árbol de variantes, numerado desde la raíz real del tablero con `plyFromFen` de `apps/web/src/lib/moves.ts`, RF-6.3; `EngineLines.tsx` = los estados del motor en vivo, con las líneas de `components/board/EngineLineList.tsx`, previsualización de línea y `playLine` de `BoardPage.tsx` para jugarla hasta la jugada pulsada, RF-6.2); tablero, barra, flechas, botón de jugada y navegación se importan de `apps/web/src/components/board/` | [03-arquitectura.md § web](03-arquitectura.md) |
| RF-7 · Ocupación del tablero | pendiente (fase 2/4) | [02-requerimientos.md § RF-7](02-requerimientos.md) |
| RF-10.1-10.2 · Alternativas por jugada en el análisis guardado | `packages/core/lucia_core/analysis/__init__.py` (`EngineLine`, `PositionEval.lines`, `AnalyzedMove.alternatives`), `apps/api/lucia_api/db/models.py` (`AnalyzedMove.alternatives_json`, migración `apps/api/migrations/versions/7a1c4e9d2b30_agrega_alternatives_json_a_analyzed_moves.py`), `services/analysis.py` (`_engine_lines`, `engine_lines_from_serialized`, `alternatives_from_cache`), `routers/analysis.py` (`AnalyzedMoveOut.alternatives`), `apps/web/src/features/viewer/GameViewerPage.tsx` + `apps/web/src/components/board/EngineLineList.tsx`. RF-10.3 (usarlas en los puzzles) sigue pendiente con RF-4.1 | [ADR-0007](adr/0007-alternativas-por-jugada-json-y-cache.md), [02-requerimientos.md § RF-10](02-requerimientos.md) |
| RF-8 · Personalización de interfaz | pendiente (Post 1.0, fase 5) | [02-requerimientos.md § RF-8](02-requerimientos.md) |
| RF-9 · Comparación entre motores (tabla y flechas) | pendiente (Post 1.0); amplía lo que hoy hace `services/comparison.py` + `EngineComparison.tsx` | [02-requerimientos.md § RF-9](02-requerimientos.md) |
| RF-11 · Partidas con ventaja (odds) contra el motor | pendiente (Post 1.0, fase 6); analizar una partida con ventaja ya funciona, porque `services/analysis.py::run_analysis` parte de la posición del PGN — falta jugarla | [02-requerimientos.md § RF-11](02-requerimientos.md), [05-roadmap.md § fase 6](05-roadmap.md) |
| Posición de partida no estándar (odds, Chess960, posición dada) | `apps/api/lucia_api/db/models.py` (`Game.starts_from_custom_position`, derivado del PGN: sin columna ni migración) expuesto por `routers/games.py` en `GameSummary`/`GameDetail`; lo avisa `apps/web/src/components/CustomPositionBadge.tsx` en listado, visor y tableros; al analizar lo respeta `apps/api/lucia_api/services/analysis.py::run_analysis` | [03-arquitectura.md § api y flujo 2](03-arquitectura.md) |
| RNF-11 · Coherencia de interfaz | transversal a `apps/web/`: lo compartido vive en `apps/web/src/components/` (`Button.tsx`, `Panel.tsx`, `Feedback.tsx`, `DataTable.tsx`, `EngineSelect.tsx`, `FilterBar.tsx` (barra de filtros de listado y dashboard, con la espera al teclear), `FieldLabel.tsx` (la etiqueta de campo de la barra, Sincronizar, `BoardsPage` y `EnginesPage`) y `RecordBadges.tsx` (el marcador V/T/D de las tablas de control de tiempo, apertura y salidas de la teoría), `Badge.tsx` con sus dos usos con significado `ClassificationBadge.tsx` y `CustomPositionBadge.tsx`, `styles.ts` con las recetas de clases y las medidas comunes, y las piezas de tablero en `components/board/`, incluidos `MoveButton.tsx`, `EngineLineList.tsx` y `useMoveNavigationKeys.ts`) y en `apps/web/src/lib/` lo que debe dar el mismo resultado en todas las pantallas (`format.ts`, `score.ts`, `classification.ts`, `moves.ts`, `chartTheme.ts`, `insights.ts` con las etiquetas y colores de tipos de error y momentos críticos, que comparten dashboard y visor); inventariado en su [README](../apps/web/src/components/README.md); criterios C-1 a C-7, inventario de incumplimientos vacío: las 63 filas que llegó a tener están cerradas | [07-coherencia-ui.md](07-coherencia-ui.md) |
| Destinos externos y su ritmo | `packages/chesscom/lucia_chesscom/` (importación, fuera de la sesión de uso) y `packages/lichess/lucia_lichess/` (Opening Explorer, el único que se consulta mientras se usa la aplicación: espaciado entre consultas, reintento y tope por llamada desde `routers/repertoire.py`) | [ADR-0010](adr/0010-repertorio-con-red-y-cacheado.md), [04-stack-tecnologico.md](04-stack-tecnologico.md) |
| Motores UCI | `engines/`, `scripts/setup-engines.sh` | [ADR-0002](adr/0002-motores-como-submodulos.md) |
| Tabla de aperturas versionada | `packages/core/lucia_core/openings/data/openings.tsv` (3.810 posiciones, generadas desde chess-openings de Lichess, CC0) + `scripts/build-openings-table.py`; la carga cacheada es `default_book()`; la columna en BD la añade `apps/api/migrations/versions/9c2d51ab7e04_agrega_apertura_propia_a_games.py`, que rellena también las partidas ya importadas | [ADR-0009](adr/0009-tabla-de-aperturas-versionada.md) |
| Persistencia | `apps/api/lucia_api/db/` | [ADR-0005](adr/0005-sqlite-local-first.md) |
| Probabilidad de victoria (win%) | `packages/core/lucia_core/accuracy/__init__.py` (backend) y `apps/web/src/lib/score.ts` (`whiteWinPercentFromScore`, cliente) | [ADR-0006](adr/0006-probabilidad-de-victoria-en-el-cliente.md) |
| Orquestación nativa (`make up`) | `scripts/dev.sh`, `scripts/doctor.sh` | [README.md § arranque rápido](../README.md) |

*Filas "pendiente" se completan cuando el módulo exista de verdad; el
`mapeador` no inventa rutas de código que no están escritas.*
