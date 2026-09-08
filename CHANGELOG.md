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
De la **fase 2** quedan once ítems: alternativas por jugada en el análisis
guardado (RF-10), coherencia de la interfaz entre pantallas, extractores de
patrones (RF-2.8, RF-3.2), tabla ECO y categoría "book" (RF-2.2), repertorio
contra Lichess Explorer (RF-3.6), importación de PGN manual (RF-1.5), filtros
de `/games` (RF-5.3), tendencias (RF-3.7), extras del tablero de análisis
(RF-6.6 a 6.9), capa de ocupación (RF-7.1 a 7.7) y exportación de PGN anotado.
Después, las fases 3 y 4.

Fuera de ese camino, en Post 1.0: **RF-8 · Personalización de interfaz**
(Fase 5), **RF-11 · Partidas con ventaja (odds) contra el motor** (Fase 6,
planteado el 2026-09-07: necesita antes el editor de posición de RF-6.1 y el
sparring calibrado de RF-4.3, ambos alcance de 1.0), **RF-9 · Comparación de
evaluaciones entre motores** (ampliación de RF-2.6, sin fase propia) y
**RNF-11 · Coherencia de interfaz**, criterio permanente cuyos incumplimientos
concretos sí se arreglan dentro de 1.0 —inventario en
[docs/07-coherencia-ui.md](docs/07-coherencia-ui.md)—.

### Cambiado

- Cimientos compartidos de la interfaz, primera parte del ítem de coherencia
  entre pantallas de la fase 2 (RNF-11, inventario en
  [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md)): componentes `Button`,
  `Panel`, `BoardWithEvalBar` y `MoveNavigator`; `Feedback` gana `SuccessBox`,
  `WarningBox` y `ProgressBox`; `styles.ts` recoge las recetas de clases que no
  pueden ser un componente; y `lib/format.ts` gana `formatPercent`,
  `formatEngineName` y `formatTimeClass`. Las piezas de tablero (`Chessboard`,
  `EvalBar`, `boardConfig`) se mudan de `features/viewer/` a
  `components/board/`, que es donde deben estar si las comparten dos pantallas.
  Cierra once filas del inventario, que baja de 42 a 34.

- Identificadores traducidos al inglés en todo el repositorio, cumpliendo la
  regla de `CLAUDE.md` que ya lo pedía. Se midió antes de decidir: de los 3.151
  identificadores declarados (AST de Python y compilador de TypeScript, solo
  declaraciones propias), el 85,3 % estaba ya solo en inglés y el 14,7 % tenía
  alguna palabra en español, concentrada en el backend. Tras la traducción,
  99,9 %. No cambió ningún nombre público: ni endpoints, ni campos de esquema,
  ni columnas de base de datos, ni el `operationId` del OpenAPI — verificado
  comparando `openapi.json`, que solo difiere en el número de versión. Los
  comentarios, docstrings y textos de interfaz siguen en español, como manda
  la misma regla.
- Grafía de "analyze" unificada en americano en todo el repo (`analyse_position`
  → `analyze_position`, `AnalysingEngine` → `AnalyzingEngine`,
  `EngineBridge.analyse` → `analyze`, `api.analysePosition` → `analyzePosition`),
  que convivía con la americana de `analyze_game` y `AnalyzedMove`. Se mantiene
  `analyse` solo donde es de `python-chess`, que usa la grafía británica en su
  propia API, y el plural `analyses`, que es igual en las dos.
  Efecto en el contrato: para evitar que el servicio y el manejador del
  endpoint acabaran con el mismo nombre en el mismo módulo —lo que haría que el
  manejador se llamase a sí mismo—, el manejador de `POST /analysis/position`
  pasó a `position_analysis`, siguiendo el estilo de sus vecinos del router
  (`analysis_progress`). Eso cambia su `operationId` en el OpenAPI y en los
  tipos generados, ya regenerados con `make types`. La ruta, los esquemas y los
  campos no cambian, y el front no usa los `operationId`.

### Corregido

- El análisis de una partida se replicaba siempre sobre la posición inicial
  estándar (RF-2.1, RF-2.2, RF-2.3). Las partidas con `[SetUp "1"]` +
  `[FEN ...]` —odds chess, Chess960, "partidas desde posición", que chess.com
  ofrece y LUCIA ya importaba— acababan sobre tableros imposibles, con jugadas
  ilegales y evaluaciones sin sentido. `run_analysis` parte ahora de
  `pgn_game.board()`, que además marca `chess960` cuando toca. Afecta a 62 de
  las 324 partidas importadas: sus análisis anteriores son basura y hay que
  volver a lanzarlos.
- La jugada que daba mate se clasificaba como *perdió el mate* (RF-2.2). El
  mate ya dado es `#+0` (`MateGiven`) y el recibido `#-0`, ambos con
  `mate() == 0`, así que la comprobación `mate() > 0` descartaba el remate.
  Ahora se usa el orden de `Score`, que sí distingue un mate a favor de uno en
  contra.
- El visor sacaba la posición previa a la primera jugada de una constante con
  el FEN estándar en vez del PGN (RF-5.1), así que en esas mismas partidas
  enseñaba un tablero que no era el de la partida. Ahora sale del historial
  parseado.

## [0.2.1] - 2026-09-06

El análisis del motor se lee **sobre el tablero** y no solo como texto, y Lc0
funciona de verdad como segundo motor. No cierra la fase 2, que sigue abierta.

**Cambio de alcance de v1.0.** **RF-10 · Alternativas por jugada en el análisis
guardado** se planteó el 2026-09-06 después del corte de alcance del
2026-09-05 y se movió a v1.0 el mismo día, por decisión expresa: persistir las
N líneas del motor por posición es cambio de esquema y del flujo de análisis,
y dejarlo para después de 1.0 obligaría a migrar la base o a re-analizar las
partidas ya analizadas. Vive en la fase 2 del roadmap (RF-10.1 y RF-10.2) y en
la 3 (RF-10.3, dentro de los puzles de RF-4.1).

### Añadido

- **Flechas de las mejores líneas del motor sobre el tablero de análisis**
  (RF-6.2, y RF-5.2 en su mitad de análisis en vivo): hasta tres, la mejor
  destacada y las siguientes atenuadas, cada una etiquetada con su evaluación.
  `Chessboard` recibe `engineArrows` en vez de `bestMoveUci`; qué pincel y qué
  etiqueta lleva cada una se decide en `boardConfig.ts`.
- **Barra de evaluación** (`EvalBar`) en el visor y en el tablero de análisis,
  en probabilidad de victoria y no en peones, orientada como el tablero
  (RF-5.2, RF-6.2). El cliente replica el modelo de Lichess del backend con la
  misma constante y el mismo redondeo que `lucia_core.accuracy.win_percent`
  para que la barra en vivo y el análisis guardado no den números distintos de
  la misma posición ([ADR-0006](docs/adr/0006-probabilidad-de-victoria-en-el-cliente.md)).
- **Previsualización de la continuación**: señalar la jugada n de una línea del
  panel del motor, con el ratón o con el tabulador, dibuja sus n primeras
  jugadas sobre el tablero (RF-6.2).
- Lc0 como segundo motor, con detección de GPU al compilar y vista de
  discrepancias entre motores (RF-2.6).
- Contador de tiempo transcurrido junto a la barra de progreso del análisis
  (RF-2.4, RNF-6), con `formatDuration` en `apps/web/src/lib/format.ts`.
  Acompaña a la barra en vez de sustituirla porque miden cosas distintas: la
  barra avanza por posición evaluada y las posiciones no tardan lo mismo (las
  que ya están en la caché por FEN salen al instante, y Lc0 varía mucho).
  Limitación conocida: al recargar la página el contador vuelve a cero, porque
  `created_at` de la tabla `analyses` existe en la base pero no se expone en la
  API.
- Criterios de coherencia de interfaz C-1 a C-7 con su inventario de
  incumplimientos abiertos, en
  [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md) (RNF-11), y el agente
  `coherencia-ui` que los vigila.

### Cambiado

- **RF-5.2 y RF-6.2 pasan de una línea resumida a decir qué se ve sobre el
  tablero** (MultiPV, flechas etiquetadas, barra de evaluación,
  previsualización). No es alcance nuevo pendiente, pero toca dos
  requerimientos congelados y queda anotado en la nota de alcance de
  [docs/02-requerimientos.md](docs/02-requerimientos.md).
- El motor genérico ya no recibe opciones que no declara soportar, que es lo
  que impedía conectar con Lc0 (`Hash`); de paso, enchufar cualquier otro motor
  UCI deja de necesitar cambios en el núcleo (RNF-9).

### Corregido

- La barra de progreso del análisis nunca mostraba progreso real (RF-2.4,
  RNF-6). `useAnalysisProgress` tenía el callback `onFinished` como dependencia
  del efecto, y el visor lo construye a partir del resultado de `useQuery`:
  react-query devuelve un objeto nuevo (un `Proxy`) en cada render, así que el
  efecto se re-ejecutaba en cada render, cerraba el WebSocket y borraba el
  progreso recién recibido. Cada evento se anulaba a sí mismo y los publicados
  mientras el socket estaba cerrado se perdían. Ahora el callback va en una ref
  y el efecto solo depende de `analysisId`. El backend no tenía nada mal: ya
  emitía un evento por posición evaluada.
- El visor de partidas fallaba con "Cannot set properties of undefined
  (setting 'dests')". Se le pasaban a chessground claves en `undefined`
  (`movable`, `turnColor`) para las cosas que el visor no usa, y su
  `deepMerge` hace `base[clave] = nuevo[clave]` sin comprobar nada: eso
  borraba su estado interno y la siguiente actualización reventaba. Ahora las
  claves que no aplican se omiten.
- El análisis se colgaba para siempre en cualquier partida terminada en jaque
  mate: se le pedía al motor que buscara en la posición final, donde no hay
  jugada que devolver, y Lc0 se queda esperando.
- La caché de posiciones no incluía la red neuronal en su clave, así que al
  cambiar de red de Lc0 devolvía las evaluaciones de la anterior.
- El rango de validación del esfuerzo del motor era el mismo para los dos
  motores, cuando 1.600 nodos es normal en Lc0 e imposible como profundidad de
  Stockfish.

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
