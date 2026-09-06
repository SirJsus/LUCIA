# 06 · Mapa del proyecto

Este documento es el mapa vivo de LUCIA: dónde vive cada cosa, cómo se conecta y
qué requerimiento o decisión la justifica. Sirve para dos lectores distintos:

- **Personas**, para orientarse rápido sin leer todo el repo antes de tocar algo.
- **IA (agentes de Claude Code)**, como referencia de consulta antes de un cambio:
  qué módulo toca, con qué otros habla, y qué doc detallada corresponde.

Lo mantiene actualizado el agente **`mapeador`**, y es un **cruce** del trabajo de
los otros tres agentes de calidad del proyecto: toma los nombres que fija
`bautizador`, la estructura que deja `minimalista` tras simplificar, y los
RF/RNF/ADR que registra `documentador`, y los refleja aquí. No repite la
narrativa de [03-arquitectura.md](03-arquitectura.md) ni de
[02-requerimientos.md](02-requerimientos.md); apunta a ellas.

> Si un diagrama de aquí contradice el código actual, el código manda: es señal
> de que el mapeador necesita pasar. Ver [CLAUDE.md](../CLAUDE.md).

## 1 · Flujo general

```mermaid
flowchart TB
    subgraph Cliente
        WEB["apps/web<br/>React + Vite"]
    end

    subgraph Servidor["apps/api (FastAPI)"]
        ROUTERS["routers/<br/>sync · games · analysis · stats · engines · boards"]
        WORKER["worker/<br/>cola de análisis en background"]
    end

    subgraph Nucleo["packages/core"]
        BRIDGE["engine/EngineBridge<br/>puente UCI"]
        ANALYSIS["analysis/GameAnalyzer"]
        CLASS["classification/MoveClassifier"]
        ACC["accuracy/"]
        INSIGHTS["insights/"]
    end

    CHESSCOM["packages/chesscom<br/>ChessComClient"]
    DB[("SQLite<br/>data/lucia.db")]
    ENGINES["engines/bin<br/>stockfish · lc0"]
    API_CHESSCOM["api.chess.com<br/>(externo)"]

    WEB -- "REST /api" --> ROUTERS
    WEB -- "WebSocket /ws" --> ROUTERS
    ROUTERS --> WORKER
    ROUTERS --> DB
    WORKER --> BRIDGE
    WORKER --> ANALYSIS
    ANALYSIS --> CLASS
    ANALYSIS --> ACC
    ANALYSIS --> INSIGHTS
    BRIDGE -- "UCI (stdin/stdout)" --> ENGINES
    ROUTERS --> CHESSCOM
    CHESSCOM -- "HTTPS" --> API_CHESSCOM
    ANALYSIS --> DB
```

Detalle narrativo y modelo de datos completo: [03-arquitectura.md](03-arquitectura.md).

## 2 · Módulos y dependencias

```mermaid
graph LR
    subgraph JS["Workspace pnpm"]
        web["@lucia/web"]
        types["@lucia/shared-types"]
    end

    subgraph PY["Workspace uv"]
        api["lucia_api"]
        core["lucia_core"]
        chesscom["lucia_chesscom"]
    end

    web --> types
    api --> core
    api --> chesscom
    types -. "make types:<br/>export-openapi.py + openapi-typescript" .-> api
```

Regla: `lucia_core` y `lucia_chesscom` no dependen de `lucia_api` (evita ciclos);
`lucia_api` orquesta a ambos. Si un cambio rompe esta dirección, es una señal
para el agente `minimalista`.

## 3 · Flujos principales

### Sincronizar con chess.com (RF-1, implementado)

```mermaid
sequenceDiagram
    participant U as Usuario (web)
    participant A as apps/api (routers/sync.py)
    participant S as services/chesscom_sync.py
    participant C as lucia_chesscom
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
        S->>DB: upsert games (por uuid, idempotente)
    end
    S->>DB: upsert sync_state (último mes)
    S-->>A: SyncSummary
    A-->>U: resumen de sincronización
```

### Analizar una partida (RF-2, implementado)

```mermaid
sequenceDiagram
    participant U as Usuario (web)
    participant A as apps/api (routers/analysis.py)
    participant WK as AnalysisWorker
    participant S as services/analysis.py
    participant E as EngineBridge (Stockfish/Lc0)
    participant DB as SQLite

    U->>A: POST /analysis {game_ids, engine, depth, multipv}
    A->>DB: crear Analysis (status=queued) por partida
    A->>WK: enqueue(analysis_id)
    A-->>U: 200: resumen con status=queued

    U->>A: WS /ws/analysis/{id}
    WK->>WK: consumidor toma el siguiente de la cola
    WK->>S: run_analysis(analysis, game, on_progress)
    S->>DB: status=running
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
    S->>DB: guardar analyzed_moves + white/black_accuracy
    S->>DB: status=done (o error, con el motivo)
    WK-->>U: WS: {status: done | error}
```

`GET /analysis/{id}` es el respaldo si no hubo WebSocket conectado o se
perdió algún evento (hay una ventana de carrera pequeña y documentada entre
suscribirse y el estado real, ver docstring de `analysis_progress`).

## 4 · Ubicación por requerimiento

Tabla de cruce: requerimiento → dónde vive → qué doc lo explica en detalle. Se
amplía a medida que se implementa cada RF (ver [05-roadmap.md](05-roadmap.md)).

| Requerimiento | Módulo / archivo | Doc detallada |
| --- | --- | --- |
| RF-1 · Importación chess.com | `packages/chesscom/lucia_chesscom/` (cliente, PGN, sync incremental), `apps/api/lucia_api/services/chesscom_sync.py`, `db/models.py`, `routers/sync.py` | [03-arquitectura.md § chesscom](03-arquitectura.md) |
| RF-2 · Análisis con motores | `packages/core/lucia_core/` (engine, analysis, classification, accuracy), `apps/api/lucia_api/services/analysis.py`, `worker/`, `routers/analysis.py` | [03-arquitectura.md § core / api](03-arquitectura.md) |
| RF-3.1-3.3 · Dashboard | `apps/api/lucia_api/services/stats.py` + `routers/stats.py`, `packages/core/lucia_core/phases/`, `apps/web/src/features/dashboard/` | [03-arquitectura.md](03-arquitectura.md) |
| RF-3.4+ · Insight avanzado | `packages/core/lucia_core/insights/` (pendiente, fase 2) | [05-roadmap.md](05-roadmap.md) |
| RF-4 · Entrenamiento | pendiente (fase 3) | [05-roadmap.md](05-roadmap.md) |
| RF-5.1 · Visor de partida | `apps/web/src/features/viewer/` (Chessboard, MoveList, EvalChart, useAnalysisProgress) | [03-arquitectura.md § web](03-arquitectura.md) |
| RF-5.3 · Listado de partidas | `apps/api/lucia_api/routers/games.py`, `apps/web/src/features/games/` | [03-arquitectura.md](03-arquitectura.md) |
| RF-5.4 · Config. de motores | `apps/api/lucia_api/routers/engines.py` + `services/engines.py`, `apps/web/src/features/engines/` | [03-arquitectura.md](03-arquitectura.md) |
| RF-5.6 · Tema claro/oscuro | `apps/web/src/components/ThemeToggle.tsx` | [02-requerimientos.md § RF-5](02-requerimientos.md) |
| Contrato API ↔ front | `scripts/export-openapi.py`, `openapi.json`, `packages/shared-types/` | [03-arquitectura.md § api](03-arquitectura.md) |
| RF-6 · Tablero de análisis | `apps/api/lucia_api/routers/boards.py`, `apps/web/src/features/board/` (`tree.ts` = árbol de variantes) | [03-arquitectura.md § web](03-arquitectura.md) |
| RF-7 · Ocupación del tablero | pendiente (fase 2/4) | [02-requerimientos.md § RF-7](02-requerimientos.md) |
| Motores UCI | `engines/`, `scripts/setup-engines.sh` | [ADR-0002](adr/0002-motores-como-submodulos.md) |
| Persistencia | `apps/api/lucia_api/db/` | [ADR-0005](adr/0005-sqlite-local-first.md) |
| Orquestación nativa (`make up`) | `scripts/dev.sh`, `scripts/doctor.sh` | [README.md § arranque rápido](../README.md) |

*Filas "pendiente" se completan cuando el módulo exista de verdad; el
`mapeador` no inventa rutas de código que no están escritas.*
