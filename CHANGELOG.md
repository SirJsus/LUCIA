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
De la **fase 2** quedan tres ítems: tendencias (RF-3.7), extras del tablero
de análisis (RF-6.6 a 6.9) y capa de ocupación (RF-7.1 a 7.7). Cerrarlos
cierra la fase y toca subir el minor a `0.3.0`. Después, las fases 3 y 4.

Fuera de ese camino, en Post 1.0: **RF-8 · Personalización de interfaz**
(Fase 5), **RF-11 · Partidas con ventaja (odds) contra el motor** (Fase 6,
planteado el 2026-09-07: necesita antes el editor de posición de RF-6.1 y el
sparring calibrado de RF-4.3, ambos alcance de 1.0), **RF-9 · Comparación de
evaluaciones entre motores** (ampliación de RF-2.6, sin fase propia) y
**RNF-11 · Coherencia de interfaz**, criterio permanente cuyos incumplimientos
concretos se arreglan dentro de 1.0: de las 70 filas que su inventario en
[docs/07-coherencia-ui.md](docs/07-coherencia-ui.md) lleva abiertas, 65 están
cerradas y quedan **cinco** —la 65 y la 67, de la importación de PGN (RF-1.5),
y las 68 a 70, del enlace de exportación (RF-5.5)—, pendientes para el próximo
corte.

## [0.2.2] - 2026-09-17

El historial deja de depender de chess.com: se puede **subir un PGN** de un
torneo presencial o de otro sitio y esas partidas se ven, se analizan y cuentan
igual que las sincronizadas (RF-1.5); y lo analizado **sale de LUCIA** como PGN
anotado, legible en lichess, ChessBase o SCID (RF-5.5). Acompañan el trabajo
acumulado desde `0.2.1`: repertorio contra la teoría de maestros, tabla de
aperturas propia, extractores de patrones, filtros de partidas y coherencia de
interfaz.

No cierra la fase 2, que sigue abierta con tres ítems, así que sube el
patch y no el minor — mismo criterio que en `0.2.1`.

### Añadido

- **Importar un PGN de otra fuente al historial** (RF-1.5), con `POST
  /import/pgn` (multipart, tope de 5 MB) y el formulario "Importar PGN" junto
  al de sincronizar, en Partidas. Cierra el último ítem que arrastraba la
  fase 1.
  - **Las partidas manuales son filas normales de `games`**, con
    `platform="manual"`, para que el visor, el análisis y las estadísticas no
    tengan que saber de dónde vino cada una
    ([ADR-0011](docs/adr/0011-pgn-manual-en-la-misma-tabla.md)). Lo que un PGN
    no trae y las columnas exigen —rating, ritmo, si era puntuada— se guarda
    como hueco y se enseña como "—", en vez de inventarlo: deducir el ritmo de
    un "40/7200:1800" de torneo sería adivinar.
  - **Identidad por el SHA-256 del PGN de cada partida**: no hay `uuid` que
    usar, así que reimportar el mismo archivo reescribe las filas en vez de
    duplicarlas, igual de idempotente que el sync (RF-1.3).
  - **Hay que decir cómo apareces en el archivo** (`player_name_in_pgn`). Un
    PGN de torneo nombra al jugador "Durán, Jesús" y no con su usuario, y las
    estadísticas y tres de los filtros de RF-5.3 casan por nombre: ese bando se
    guarda con el `username` de LUCIA y el nombre original no se pierde, porque
    el PGN se guarda entero. La respuesta dice en cuántas se reconoció y la
    pantalla avisa cuando no fue en ninguna —guardadas, pero sin contar en
    ningún marcador.
  - **Lo que no entra**: partidas sin terminar ("\*") y sin jugadas. La
    respuesta las enumera con el motivo, para que un recuento que no cuadra con
    el archivo no se lea como un fallo.
  - Dependencia nueva: `python-multipart` (BSD-3, compatible con GPL-3.0).

- **Exportar una partida analizada a PGN anotado** (RF-5.5), con `GET
  /analysis/{id}/pgn` y el enlace "Exportar PGN anotado" en el visor. El
  archivo se abre como cualquier PGN comentado.
  - **Se comentan todas las jugadas**, no solo las falladas: cada una lleva su
    clasificación (RF-2.2) y la probabilidad de victoria en que dejó la
    partida, siempre desde el punto de vista de las blancas para que el número
    no cambie de signo a mitad del archivo. El NAG (`?!`, `?`, `??`) sí es solo
    para lo fallado: poner `!` donde se coincidió con el motor sería un mérito
    que el análisis no mide.
  - **La línea del motor cuelga del padre de la jugada** —la posición desde la
    que se eligió, que es donde una variante tiene sentido— y solo cuando lo
    jugado no era lo que el motor prefería, recortada a 6 medias jugadas.
  - **No se vuelve a llamar al motor**: todo sale de lo que el análisis ya
    guardó (RF-2.2, RF-10.1), así que exportar es inmediato y no gasta CPU.
  - **Solo se exportan análisis terminados** (409 si no): uno a medias daría
    una partida comentada hasta la jugada 20 y muda después.
  - **El PGN conserva las cabeceras del archivo original**, no las columnas
    normalizadas de `games`, que en una partida importada por RF-1.5 pueden
    estar vacías.
  - Sin dependencias nuevas: lo escribe `python-chess`, que ya estaba en el
    stack.

- **Comparación de repertorio con la teoría de maestros** (RF-3.6), en
  Estadísticas: dónde te sales de la línea principal, qué juegan los maestros
  en su lugar y qué puntuación sacas cuando lo haces. Las salidas se agrupan,
  porque lo que dice algo es el patrón, no la partida suelta.
  - **Es lo único de LUCIA que necesita red mientras se usa**, así que va con
    su decisión escrita ([ADR-0010](docs/adr/0010-repertorio-con-red-y-cacheado.md)):
    `GET /repertoire` nunca sale a internet y dice cuántas posiciones le faltan
    por saber; `POST /repertoire/refresh` es lo único que consulta, y solo
    cuando se pulsa. Todo lo consultado se guarda en `explorer_positions`
    (migración `b4e8c17f0a92`).
  - Cliente propio en `packages/lichess`, con las mismas reglas de cortesía que
    el de chess.com: `User-Agent` con contacto, una consulta por segundo,
    backoff ante `429` y tope por llamada.
  - **Necesita un token de Lichess** (`LICHESS_TOKEN`), gratuito y sin
    permisos: el Opening Explorer dejó de admitir peticiones anónimas. La
    pantalla lo dice antes de que se pulse nada, con el enlace donde se saca, y
    sin él sigue enseñando lo que ya se consultó.

- **Filtros de partidas por apertura, fechas, rival y resultado** (lo que
  faltaba de RF-5.3). `GET /games` acepta `opening` (subcadena del nombre, así
  que "sicilian" trae todas las sicilianas), `since` y `until` (fechas
  inclusivas por los dos lados), `opponent` y `result`. Los tres que dependen
  de quién sea el jugador —color, resultado y rival— se ignoran sin `username`
  y en la pantalla salen deshabilitados diciendo por qué: la misma partida es
  victoria para uno y derrota para el otro.

- **Tabla de aperturas propia** (`lucia_core.openings`), con la clasificación
  ECO de [chess-openings de Lichess](https://github.com/lichess-org/chess-openings)
  (CC0, dominio público). Se versiona ya procesada —3.810 posiciones con su
  código y su nombre— porque la aplicación no puede depender de tener red para
  nombrar una apertura (RNF-1); la regenera `scripts/build-openings-table.py`.
  - **Se busca por posición, no por secuencia de jugadas**, así que reconoce
    transposiciones: llegar a la Najdorf por otro orden da el mismo nombre.
  - **Categoría "Teoría" en la clasificación de jugadas** (RF-2.2, que estaba
    definida pero no se producía nunca): mientras la partida siga en el libro,
    la jugada no se puntúa como acierto de quien la juega. Con una excepción
    aprendida probándolo: la tabla nombra también celadas —el mate del loco
    tiene nombre—, así que una jugada de libro que hunde la posición se
    clasifica por lo que hizo. La teoría no tapa un error.
  - **La apertura se guarda al importar la partida** (`games.opening_eco` y
    `opening_name`, migración `9c2d51ab7e04`, que rellena también las ya
    importadas). Sale en 262 de las 324 partidas del autor, frente a las 260
    que traía chess.com, y ahora con código ECO. Las 62 restantes son las que
    no empiezan en la posición estándar, donde no hay apertura que nombrar.
  - **Estadísticas por apertura** (RF-3.2) pasan a usar esta clasificación en
    vez de la URL que reporta chess.com, con el código ECO a la vista.

- **Extractores de patrones** (RF-2.8, RF-3.4, RF-3.5 y lo que faltaba de
  RF-3.2), en `lucia_core.insights`. Ninguno vuelve a llamar al motor: leen lo
  que el análisis ya guardó, así que las partidas analizadas antes también
  entran.
  - **Momentos críticos** en el visor: las jugadas donde se decidió la partida,
    con el motivo de cada una —solo valía una jugada, la partida cambió de
    manos, o había una ganada y se escapó— y un clic para ir a esa posición.
    Llegan en `GET /analysis/{id}`.
  - **Por qué fallas**, en Estadísticas: los errores repartidos por tipo (con
    el reloj encima, táctico, de final, posicional), cada uno con la regla con
    la que se decidió, porque "posicional" no significa nada sin ella.
  - **Con el reloj en la mano**, en Estadísticas: precisión y errores por tramo
    de reloj restante, y en cuántas partidas se llegó a jugar con menos de
    veinte segundos.
  - **Al salir de la apertura**: columna nueva en la tabla de aperturas con la
    probabilidad de victoria media al terminar la fase de apertura.

- **Alternativas por jugada en el análisis guardado** (RF-10.1 y RF-10.2). El
  análisis persiste ahora las N mejores líneas de cada posición, no solo
  `best_move_uci`, y el visor las usa: las mismas flechas múltiples que el
  tablero de análisis, y un panel "podías haber jugado, en vez de …" al pararse
  en una jugada, con su evaluación y su continuación. Señalar o pulsar una
  jugada de una línea la dibuja sobre el tablero.
  - En la base: columna `analyzed_moves.alternatives_json` (migración
    `7a1c4e9d2b30`), con el mismo formato serializado que
    `position_cache.lines_json`. La notación SAN no se guarda: se deriva de
    `fen_before` al servir.
  - En la API: `AnalyzedMoveOut.alternatives`, con la misma forma
    (`EngineLineOut`) que devuelve el análisis en vivo de una posición.
  - **Los análisis que ya existían no hay que repetirlos**, que era el motivo
    de meter RF-10 en el alcance de 1.0: sus posiciones siguen en
    `position_cache` con todas sus líneas (RF-2.7), y `GET /analysis/{id}` las
    recupera de ahí cuando la clave coincide exactamente (misma posición,
    motor, red, límite y MultiPV). Comprobado sobre la base del autor: un
    análisis de 56 jugadas recuperó las tres alternativas de todas ellas sin
    gastar motor.

### Corregido

- Una partida analizada con **los dos motores** (RF-2.6) contaba dos veces en
  las estadísticas: en la precisión media, en el número de partidas analizadas
  y en el reparto por fases. Ahora cada partida cuenta una vez, con su análisis
  más reciente, que es el que la interfaz enseña.

### Cambiado

- **La interfaz es coherente entre pantallas** (RF-5.1, RF-5.2, RF-6.2,
  RNF-6/RNF-11): el inventario de
  [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md) quedó **vacío** ese día,
  con las 51 filas que llevaba cerradas: las 38 que lo motivaron, las nueve que
  destapó después el barrido de comprobación de las seis pantallas contra los
  siete criterios, y las cuatro de revisar las alternativas por jugada del
  visor. Cierra el ítem de coherencia de la fase 2. Lo más visible:
  - El **tablero de análisis** tiene controles de navegación en pantalla y los
    mismos cuatro atajos que el visor (`Home` y `End` incluidos), dice qué
    motor firma la evaluación y con cuál analizar, y distingue los cinco
    estados del motor —apagado, buscando, con error, sin líneas y con líneas—
    en vez de un "analizando…" en letra pequeña. Pulsar cualquier jugada de una
    línea del motor lleva el tablero hasta ahí; antes solo la primera hacía
    algo, con el mismo aspecto que las demás. Y mientras el motor todavía no ha
    contestado a la posición nueva, el panel y la barra dicen que lo que se ve
    es de la anterior, en vez de contradecir al tablero en silencio.
  - **La numeración de jugadas sale de la partida**, no del índice interno
    (`lib/moves.ts`): una partida que empieza en la jugada 12 se numera desde
    12 en la lista, en el gráfico y en la comparación de motores. El gráfico de
    evaluación dejaba de contar medias jugadas llamándolas "Jugada 41".
  - **Nada se transmite ya solo con color** (C-7): la clasificación de jugada
    viaja con su nombre, victorias/tablas/derrotas llevan su letra, la fase que
    más ventaja cuesta se dice con palabras, y la barra de evaluación gira sus
    colores con el tablero — con el tablero de negras afirmaba lo contrario que
    el motor. Los tres gráficos tienen paleta propia en tema oscuro
    (`lib/chartTheme.ts`), donde el tooltip conservaba su fondo blanco.
  - **Se avisa de las partidas que no empiezan en la posición estándar**, en el
    visor y en el listado. `GET /games` y `GET /games/{id}` traen para ello un
    campo nuevo, `starts_from_custom_position`, que la API deduce del PGN sin
    columna nueva ni migración.
  - **Las dos pantallas de listado se abren igual**: un enlace con aspecto de
    botón al final de la fila —"Ver partida", "Ver tablero"—, separado de
    eliminar. En Tableros era el título entero, que no se veía pulsable. Y la
    navegación superior marca la sección también en las pantallas de detalle:
    en el visor de una partida no se iluminaba nada.
  - Piezas que dejan de estar copiadas y pasan a `components/`: la insignia
    (`Badge` y sus dos usos con significado), la tabla de datos (`DataTable`),
    el selector de motor (`EngineSelect`), el botón de jugada (`MoveButton`) y
    los atajos de navegación (`useMoveNavigationKeys`).
  - Detalles que se arrastraban: guardar o borrar un tablero dice qué está
    pasando, "Copiar PGN" y "Partida propia" dicen si salieron bien, eliminar
    pregunta antes y se llama igual en los dos sitios, filtrar por jugador se
    aplica al teclear y está en el mismo sitio en las dos pantallas que lo
    tienen, y el enlace del listado de partidas dice "Ver partida", que es lo
    que hace.

- Cimientos compartidos de la interfaz, primera parte del ítem de coherencia
  entre pantallas de la fase 2 (RNF-11, inventario en
  [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md)): componentes `Button`,
  `Panel`, `BoardWithEvalBar` y `MoveNavigator`; `Feedback` gana `SuccessBox`,
  `WarningBox` y `ProgressBox`; `styles.ts` recoge las recetas de clases que no
  pueden ser un componente; y `lib/format.ts` gana `formatPercent`,
  `formatEngineName` y `formatTimeClass`. Las piezas de tablero (`Chessboard`,
  `EvalBar`, `boardConfig`) se mudan de `features/viewer/` a
  `components/board/`, que es donde deben estar si las comparten dos pantallas.
  Cerró once filas del inventario.

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
