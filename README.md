# L.U.C.I.A. — Logic & Ultimate Chess Insight Algorithm

Plataforma personal de entrenamiento de ajedrez. Usa **Stockfish** y **Lc0 (Leela Chess Zero)** como "cerebro", importa tu perfil e historial de **chess.com**, y construye encima análisis, estadísticas y entrenamiento que en las plataformas comerciales están detrás de un muro de pago.

> Estado: esqueleto inicial. Ver [docs/05-roadmap.md](docs/05-roadmap.md).

## Estructura del monorepo

```
LUCIA/
├── apps/
│   ├── api/            # Backend FastAPI (Python): orquesta motores, expone análisis
│   └── web/            # Frontend React + Vite + TypeScript: tablero, gráficas, entrenamiento
├── packages/
│   ├── core/           # Python: puente UCI con Stockfish/Lc0, clasificación de jugadas, métricas
│   ├── chesscom/       # Python: cliente de la API pública de chess.com (perfil, archivos PGN)
│   └── shared-types/   # TypeScript: tipos compartidos API <-> web (generados desde OpenAPI)
├── engines/            # Submódulos git: stockfish/ y lc0/ (fuente C++, compilado a engines/bin/)
├── infra/docker/       # docker-compose y Dockerfiles
├── scripts/            # setup-engines.sh, utilidades
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
| [docs/adr/](docs/adr/) | Decisiones de arquitectura (ADR) |
| [CHANGELOG.md](CHANGELOG.md) | Historial de versiones (Keep a Changelog + SemVer), a partir del alcance v1.0 congelado en requerimientos |

## Arranque rápido (nativo)

El flujo de desarrollo es nativo, sin Docker, pero con la comodidad de `docker compose up`: un solo comando levanta todo y muestra los logs de cada servicio con su prefijo en la misma consola.

```bash
make doctor    # qué tienes, qué falta y cómo instalarlo
make engines   # clona submódulos, compila Stockfish y Lc0, descarga red (una sola vez)
make up        # crea .env si falta, instala dependencias si faltan, levanta api + web
make up S=api  # solo un servicio (api | web)
```

Ctrl+C apaga todos los servicios. Los logs también quedan en `data/logs/<servicio>.log`.

- API: <http://localhost:8000/docs>
- Web: <http://localhost:5173>

Docker (`infra/docker/`) queda como vía de portabilidad y reproducibilidad, no como entorno principal. Ver [docs/04-stack-tecnologico.md](docs/04-stack-tecnologico.md).

## Licencia

GPL-3.0. Stockfish y Lc0 son GPL-3.0; al integrarlos y distribuirlos, LUCIA adopta la misma licencia. Ver [ADR-0004](docs/adr/0004-licencia-gpl3.md).
