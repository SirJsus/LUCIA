# L.U.C.I.A. — Logic & Ultimate Chess Insight Algorithm

Plataforma personal de entrenamiento de ajedrez. Usa **Stockfish** y **Lc0 (Leela Chess Zero)** como "cerebro", importa tu perfil e historial de **chess.com**, y construye encima análisis, estadísticas y entrenamiento que en las plataformas comerciales están detrás de un muro de pago.

> Estado: fases 0 a 3 del roadmap cerradas — importación, análisis con motor,
> estadísticas, tablero de análisis, ocupación del tablero y **RF-4 entero**:
> puzzles desde los errores propios con repetición espaciada (RF-4.1), drill de
> aperturas (RF-4.2), sparring contra el motor con fuerza calibrada (RF-4.3),
> re-jugar desde el error (RF-4.4) y el plan de entrenamiento semanal (RF-4.5).
> Queda el empaquetado (fase 4) para la v1.0.0. Ver
> [docs/05-roadmap.md](docs/05-roadmap.md) y [CHANGELOG.md](CHANGELOG.md).

## Estructura del monorepo

``` text
LUCIA/
├── apps/
│   ├── api/            # Backend FastAPI (Python): orquesta motores, expone análisis
│   └── web/            # Frontend React + Vite + TypeScript: tablero, gráficas, entrenamiento
├── packages/
│   ├── core/           # Python: puente UCI con Stockfish/Lc0, clasificación de jugadas, métricas,
│   │                   #   patrones de juego, repetición espaciada de los puzzles,
│   │                   #   reglas de una partida de sparring, del drill de aperturas
│   │                   #   y del plan de entrenamiento semanal
│   │                   #   y tabla ECO de aperturas (datos incluidos)
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

La web tiene seis pantallas: **Partidas** (lista con filtros, sincronización
desde chess.com e importación de un archivo PGN de otra fuente —OTB, lichess—),
**Visor** (tablero, jugadas clasificadas, gráfico de
evaluación, análisis con progreso en vivo, exportación de la partida a PGN
anotado —con comentarios y variantes, para abrirla en lichess o ChessBase— y
"Abrir como tablero", que la lleva al tablero de análisis como copia
desacoplada), **Tableros** (análisis libre desde la posición inicial, un FEN,
un PGN pegado o el editor de posición pieza a pieza, con árbol de
variantes, motor en vivo, deshacer / rehacer que sobrevive a recargar y
análisis completo de la línea principal en background; el PGN entra y sale
con sus variantes y comentarios, y un tablero que sea una partida tuya —una
OTB, una de club— se marca como "partida propia" y pasa a contar en Partidas y
en Estadísticas como cualquier otra), **Estadísticas** (marcador,
ratings, aperturas con su código ECO, en qué fase se pierde más ventaja, de qué
tipo son los errores, qué pasa cuando baja el reloj, si mejoras mes a mes y
dónde te sales de la teoría de maestros), **Entrenamiento** (te recibe el **plan de
la semana**: qué te está costando puntos —en qué fase pierdes ventaja, de qué
tipo son tus errores, qué apertura te sale cara, si juegas con el reloj encima,
si tu precisión está cayendo— y los deberes que salen de ahí, cada uno diciendo
qué debilidad lo pide y cuánto llevas hecho. No hay nada que marcar: el avance
sale de lo que ya entrenaste, y cada deber te lleva a su pestaña. Las cuatro
pestañas a las que manda son: puzzles sacados de tus propios errores —la posición justo antes del blunder—,
con repetición espaciada, donde los que aciertas vuelven cada vez más tarde y
vale cualquier jugada tan buena como la del motor, no solo la suya; el **drill
de aperturas**, que toma las líneas donde más puntos pierdes —los puntos donde
abandonas la teoría y las aperturas que peor se te dan— y te las hace repetir
jugando desde la primera jugada, con la aplicación respondiendo por el rival,
hasta la jugada que los maestros hacen ahí en lugar de la tuya;
**sparring**, partidas contra Stockfish con el Elo que le pongas o contra Lc0
con una red Maia, que en vez de contenerse juega como una persona de ~1500; y
**re-jugar desde el error**, que te lista tus errores más caros y te deja
volver a jugar la partida desde justo antes de cada uno, contra el motor y con
el bando que quieras —o, desde el visor, desde cualquier posición de cualquier
partida tuya, con "Jugar desde aquí"—. Una partida contra el motor, la empieces
donde la empieces, no cuenta en tus estadísticas —sería medirte contra un
motor al que le has bajado la fuerza—, pero se abre como tablero para
analizarla) y **Motores** (profundidad, MultiPV, hilos y hash, editables).

Sobre cualquier tablero —el del visor, el de análisis y los tres de
entrenamiento: puzzle, drill de apertura y partida de sparring— se enciende con
la tecla `O` la **capa de ocupación** (RF-7): quién controla cada casilla, qué
piezas están colgadas o clavadas y qué rayos X hay detrás. Se calcula en el
navegador, sin motor y sin red. Entrenando, las tres marcas —colgadas, clavadas
y rayos X— arrancan apagadas: rodear una pieza colgada es media solución del
puzzle. Se encienden desde el panel cuando quieras la ayuda.

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
