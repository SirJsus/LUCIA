# L.U.C.I.A. — Logic & Ultimate Chess Insight Algorithm

Plataforma personal de entrenamiento de ajedrez. Usa **Stockfish** y **Lc0 (Leela Chess Zero)** como "cerebro", importa tu perfil e historial de **chess.com**, y construye encima análisis, estadísticas y entrenamiento que en las plataformas comerciales están detrás de un muro de pago.

> Estado: esqueleto inicial. Ver [docs/05-roadmap.md](docs/05-roadmap.md).

## Estructura del monorepo

``` text
LUCIA/
├── apps/
│   ├── api/            # Backend FastAPI (Python): orquesta motores, expone análisis
│   └── web/            # Frontend React + Vite + TypeScript: tablero, gráficas, entrenamiento
├── packages/
│   ├── core/           # Python: puente UCI con Stockfish/Lc0, clasificación de jugadas, métricas,
│   │                   #   patrones de juego y tabla ECO de aperturas (datos incluidos)
│   ├── chesscom/       # Python: cliente de la API pública de chess.com (perfil, archivos PGN)
│   ├── lichess/        # Python: cliente del Opening Explorer de Lichess (teoría de aperturas)
│   └── shared-types/   # TypeScript: tipos compartidos API <-> web (generados desde OpenAPI)
├── engines/            # Sub-módulos git: stockfish/ y lc0/ (fuente C++, compilado a engines/bin/)
├── infra/docker/       # docker-compose y Docker-files
├── scripts/            # setup-engines.sh, build-openings-table.py, utilidades
└── docs/               # Visión, requerimientos, arquitectura, stack, roadmap, ADRs
```

## Documentación

| Doc | Contenido |
| ----- | ----------- |
| [01-vision.md](docs/01-vision.md) | Qué es LUCIA, para quién y por qué |
| [02-requerimientos.md](docs/02-requerimientos.md) | Requerimientos funcionales y no funcionales, priorizados |
| [03-arquitectura.md](docs/03-arquitectura.md) | Componentes, flujo de datos, modelo de datos |
| [04-stack-tecnologico.md](docs/04-stack-tecnologico.md) | Tecnologías elegidas y por qué |
| [05-roadmap.md](docs/05-roadmap.md) | Fases de entrega |
| [06-mapa-del-proyecto.md](docs/06-mapa-del-proyecto.md) | Mapa vivo en diagramas Mermaid: flujo general, módulos, secuencias y qué RF vive en qué archivo |
| [07-coherencia-ui.md](docs/07-coherencia-ui.md) | Criterios de coherencia de la interfaz (RNF-11), qué se arregló para cumplirlos y cómo se verifica antes de comitear en `apps/web` |
| [docs/adr/](docs/adr/) | Decisiones de arquitectura (ADR) |
| [CHANGELOG.md](CHANGELOG.md) | Historial de versiones (Keep a Changelog + SemVer), a partir del alcance v1.0 congelado en requerimientos |

## Arranque rápido (nativo)

El flujo de desarrollo es nativo, sin Docker, pero con la comodidad de `docker compose up`: un solo comando levanta todo y muestra los logs de cada servicio con su prefijo en la misma consola.

```bash
make doctor    # qué tienes, qué falta y cómo instalarlo
make engines   # clona sub-módulos, compila Stockfish y Lc0, descarga red (una sola vez)
make up        # crea .env si falta, instala dependencias si faltan, levanta api + web
make up S=api  # solo un servicio (api | web)
make types     # regenera los tipos TS del front desde el OpenAPI de la API
```

La web tiene cinco pantallas: **Partidas** (lista con filtros y sincronización
desde chess.com), **Visor** (tablero, jugadas clasificadas, gráfico de
evaluación y análisis con progreso en vivo), **Tableros** (análisis libre desde
FEN o PGN, con árbol de variantes y motor en vivo), **Estadísticas** (marcador,
ratings, aperturas con su código ECO, en qué fase se pierde más ventaja, de qué
tipo son los errores, qué pasa cuando baja el reloj y dónde te sales de la
teoría de maestros) y **Motores** (profundidad, MultiPV, hilos y hash,
editables).

Todo funciona sin conexión salvo dos cosas, y las dos las pides tú: importar
partidas de chess.com y traer teoría de aperturas nueva del Opening Explorer de
Lichess (RF-3.6). Lo ya traído se consulta offline como el resto — ver
[ADR-0010](docs/adr/0010-repertorio-con-red-y-cacheado.md).

Ctrl+C apaga todos los servicios. Los logs también quedan en `data/logs/<servicio>.log`.

- API: <http://localhost:8000/docs>
- Web: <http://localhost:5173>

Docker (`infra/docker/`) queda como vía de portabilidad y reproducibilidad, no como entorno principal. Ver [docs/04-stack-tecnologico.md](docs/04-stack-tecnologico.md).

## Licencia

GPL-3.0. Stockfish y Lc0 son GPL-3.0; al integrarlos y distribuirlos, LUCIA adopta la misma licencia. Ver [ADR-0004](docs/adr/0004-licencia-gpl3.md).

La tabla de aperturas versionada en `packages/core/lucia_core/openings/data/` deriva de [chess-openings de Lichess](https://github.com/lichess-org/chess-openings), publicada bajo **CC0 1.0** (dominio público), compatible con la GPL-3.0. La regenera `scripts/build-openings-table.py`.
