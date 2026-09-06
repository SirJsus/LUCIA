# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
versionado según [SemVer 2.0.0](https://semver.org/lang/es/). Lo mantiene el
agente `versionador`, cruzando `docs/05-roadmap.md` y
`docs/02-requerimientos.md`.

Mientras el proyecto esté por debajo de `1.0.0`, la API y el esquema de datos
pueden cambiar sin aviso entre versiones menores (convención habitual de
SemVer para la serie `0.x`).

## [Sin publicar]

Camino a v1.0.0 — ver progreso en [docs/05-roadmap.md](docs/05-roadmap.md) y
alcance congelado en [docs/02-requerimientos.md](docs/02-requerimientos.md).
Siguiente: fase 2 (insight), empezando por Lc0 como segundo motor.

## [0.2.0] - 2026-09-06

Cierre de la **fase 1**: el MVP "Game Review propio" funciona de punta a punta.

### Añadido

- **Importación de chess.com** (RF-1): perfil, historial mensual, relojes por
  jugada, sincronización incremental e idempotente, con backoff ante 429.
- **Análisis con motor** (RF-2): puente UCI con Stockfish, evaluación posición
  a posición, clasificación de jugadas con umbrales ajustables, precisión con
  la fórmula de Lichess, caché por FEN, cola en background y progreso por
  WebSocket.
- **Dashboard** (RF-3.1 a 3.3): marcador y ratings por control de tiempo,
  partidas por mes, rendimiento por apertura y pérdida de ventaja por fase,
  con detección de fase propia (`lucia_core.phases`).
- **Interfaz web** (RF-5): lista de partidas con filtros, visor con tablero,
  jugadas clasificadas y gráfico de evaluación, configuración editable de
  motores y tema claro/oscuro.
- **Tablero de análisis** (RF-6.1 a 6.5): crear desde FEN o PGN, árbol de
  variantes con promover y borrar, motor en vivo, autoguardado y exportación
  a PGN.
- Contrato API ↔ front generado desde el OpenAPI real (`make types`), con
  verificación en CI de que no se desincroniza.

### Corregido

- Rutas relativas (base de datos y binarios de motor) que apuntaban a sitios
  distintos según el directorio desde el que arrancara el proceso.
- El cliente de chess.com no seguía la redirección 301 que devuelve la API
  cuando el nombre de usuario no está en su forma canónica.
- Las búsquedas por nombre de usuario distinguían mayúsculas, así que buscar
  el propio perfil ("sirjsus") no encontraba ninguna de sus partidas, porque
  dentro del PGN el nombre va como lo escribió el jugador ("SirJsus").

## [0.1.0] - 2026-09-05

### Añadido

- Esqueleto del monorepo: `apps/api` (FastAPI), `apps/web` (React + Vite),
  `packages/core`, `packages/chesscom`, `packages/shared-types`.
- Documentación completa: visión, requerimientos RF-1 a RF-7 y RNF-1 a RNF-10,
  arquitectura, stack tecnológico, roadmap, ADR-0001 a ADR-0005.
- Motores como sub-módulos git con `scripts/setup-engines.sh`.
- Orquestación de desarrollo nativa (`make doctor`, `make up`).
- CI (GitHub Actions), Docker Compose como vía secundaria, licencia GPL-3.0.
- Agentes de calidad del proyecto: `documentador`, `minimalista`, `bautizador`,
  `mapeador`, y la skill `/revision-lucia` que los encadena.
