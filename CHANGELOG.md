# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
versionado según [SemVer 2.0.0](https://semver.org/lang/es/). Lo mantiene el
agente `versionador`, cruzando `docs/05-roadmap.md` y
`docs/02-requerimientos.md`.

Mientras el proyecto esté por debajo de `1.0.0`, la API y el esquema de datos
pueden cambiar sin aviso entre versiones menores (convención habitual de
SemVer para la serie `0.x`).

## [Sin publicar]

Nada entregado todavía, pero sí **un defecto encontrado y sin arreglar**; ver
abajo. Para `1.0.0` queda la **fase 4 y solo la fase 4**; el progreso en
[docs/05-roadmap.md](docs/05-roadmap.md) y el alcance congelado en
[docs/02-requerimientos.md](docs/02-requerimientos.md).

### Defecto conocido

**El árbol de un tablero deja de servirse pasados 127 plies** (**RF-6**,
encontrado el **2026-09-24** con la aplicación en marcha, diagnosticado y **no
arreglado**). `pydantic-core` serializa como mucho 127 niveles de anidamiento y
`boards.tree_json` anida uno por ply, así que un tablero de más de unas 64
jugadas falla con `Circular reference detected (depth exceeded)` — el mensaje
habla de ciclo y lo que hay es profundidad. Medido sobre la base del autor: los
tableros de 31, 49 y 56 plies se sirven; el de 142, no.

**El dato entra y no sale**: el fallo es al serializar la respuesta, después de
escribir, así que `POST`/`PUT /boards` guardan la fila y devuelven error, y el
tablero queda en la base sin poder abrirse. No es un defecto nuevo —es el
serializador contra una estructura que ya era así—, pero lo destapa el camino
que abrió la fase 3: una partida de sparring (RF-4.3) abierta como tablero
(RF-6.6) pasa de 127 plies con facilidad.

**Arreglo decidido y pendiente**: servir `tree_json` sin pasarlo por el
serializador de Pydantic (`json.dumps` lo aguanta, comprobado hasta 1000
niveles) en vez de aplanar el árbol, que sería lo correcto de raíz pero cambia
el contrato, `tree.ts` y el esquema. Está como ítem de la fase 4.

Son **cuatro requerimientos** —**RF-2.9** (explicaciones en lenguaje natural de
por qué una jugada es error), **RF-3.8** (rivales recurrentes) y **RF-7.8** y
**RF-7.9** (recordar sub-modo y filtros de ocupación entre sesiones, y casillas
críticas según motor)— más el empaquetado y macOS/Windows, que no son
requerimientos de nadie sino distribución.

**El siguiente movimiento es RF-2.9, y `1.0.0` no se puede cortar sin él**: es
el único punto de **RF-2** sin entregar, así que el corte afirmaría que RF-2
está entregado entero y eso sería falso. Hasta `0.6.0` este archivo lo daba por
hecho sin querer —contaba tres pendientes donde hay cuatro—; el roadmap dice
ahora por dónde se abre la fase.

**Eran cuatro y estuvieron a punto de ser cinco.** **RF-2.5** (análisis en
lote, **P0**) tampoco estaba en esta cuenta: entregado solo en el servidor
desde la fase 1, sin forma de pedirlo desde ninguna pantalla y **sin una sola
mención** en el roadmap ni aquí. **Se cierra en `0.6.0`**, entero, así que no
engorda esta lista — pero deja la lección: lo pendiente se contaba por los
ítems escritos en el roadmap y no por las filas de
[02-requerimientos.md](docs/02-requerimientos.md), que es la lista que manda.
Antes de cortar `1.0.0` hay que recorrer esa tabla RF a RF, no este resumen.

## [0.6.0] - 2026-09-23

Dos cosas en el mismo commit. La primera es la **auditoría de cierre de la fase
3**: volver a leer entera la sección que se acababa de construir y saldar lo
que salió — **rompe el contrato de la API en ocho campos**, trae **una
migración**, arregla **un error de verdad** y pone a decir la verdad al relato
de `0.5.0`, que en tres puntos no la decía. La segunda es la que esa forma de
mirar destapó fuera de la fase 3: el **análisis en lote desde el listado de
Partidas**, que **completa RF-2.5** (P0).

**Sí hay prestación nueva, y esta entrada decía lo contrario.** Llegó a decir
"no hay un solo RF que no estuviera ya entregado", y eso era verdad de los RF
que el proyecto se contaba a sí mismo: **RF-2.5 estaba a medias y ningún
documento lo decía** —`POST /analysis` aceptaba una lista de `game_ids` desde
la fase 1 y no había forma de pedir una tanda desde ninguna pantalla—. Con este
commit queda **entregado entero**, backend e interfaz; el detalle está abajo,
en "Añadido", y por qué nadie lo contaba, en "Corregido".

**Por qué sigue siendo `0.6.0` y no `0.7.0`.** Porque `0.6.0` **es** el número
de este commit, no uno que se le adjudique después: todo esto —auditoría y
análisis en lote— va en un solo commit, y una versión por commit es
precisamente la disciplina que esta entrada le reclama a `0.5.0`, que abarcó
dos. Y porque el número ya está donde tiene que estar: en la serie `0.x` una
prestación nueva sube el **minor**, que es exactamente lo que este ya es. Subir
a `0.7.0` inventaría una versión que ningún commit llevó y partiría en dos un
trabajo que no lo está. Los diez manifiestos, `openapi.json` y
`packages/shared-types` siguen en `0.6.0`.

**Por qué sube el minor sin cerrar fase.** La regla de casa —minor al cerrar
una fase del roadmap, patch para lo que pasa dentro de ella— dice cuándo
**basta** con un patch, no cuándo basta con nada más, y aquí se queda corta por
debajo: ocho campos renombrados en la API y una migración que renombra dos
columnas **no caben en un patch**, que es por definición el número que se sube
cuando actualizar no obliga a tocar nada. En la serie `0.x` el sitio de un
cambio incompatible es el minor —lo dice la cabecera de este archivo— y ese es
el segundo motivo por el que un minor existe, además de cerrar fase. `0.5.0`
usó el otro argumento, "es el mismo commit sin publicar", para meter dos
rupturas de contrato sin subir nada; **esta versión no lo repite**.

**La fase 3 sigue cerrada por `0.5.0` y la fase 4 sigue sin abrirse.** Esto es
la deuda de la fase 3, no su continuación: **no se ha reabierto ninguna
casilla** —los seis ítems están entregados de verdad, comprobados uno a uno— y
no se ha marcado ninguna nueva. **El análisis en lote tampoco abre una**: es la
mitad que le faltaba a un requerimiento de la **fase 1**, y está contado como
**nota al final de esa fase** —no como casilla— por lo mismo que el barrido de
RNF-11 es una nota de la fase 3: una casilla nueva en una fase cerrada diría
que esa fase lo entregó, y no lo entregó.

**No hay alcance nuevo**: no se ha añadido ningún RF ni RNF, nada baja a Post
1.0 y nada sube a 1.0. RF-2.5 es **alcance congelado de v1.0 desde el corte del
2026-09-05**, y completarlo no amplía nada — solo deja de dar por hecho lo que
estaba a medias. Lo que cambia es el **conteo**, que venía mal por dos
sitios, y el **relato**, que afirmaba cosas que no pasaron; los dos están en
"Corregido".

**Tests**: **356 de Python** (cuatro más: el de regresión del error de abajo y
tres del listado, que comprueban con qué motores sale analizada cada partida,
que un análisis en marcha no se cuenta como terminado y que el detalle de una
partida dice lo mismo que su fila) y **169 del front** (cuatro más y uno
menos: entran los cuatro de `formatAnalyzedByEngines` —los cuatro estados de la
columna, incluido el que la distingue de un hueco— y los de `turnsOf` se
mudaron de `sparring.test.ts` —que pasa de 8 a 5— a `moves.test.ts` —de 10 a
12—, donde ya vive la función, y al juntarse con los que allí había sobraba
uno).

### Añadido

- **Análisis en lote desde el listado de Partidas** (**RF-2.5**, sobre RF-2.4 y
  RF-5.3), que es **la mitad que le faltaba a un P0**: se marcan partidas con
  las casillas de la primera columna —o la página entera desde la cabecera—,
  se elige **un** motor para toda la tanda (`engineForNextBatch`) y el botón la
  manda a la cola de análisis con un solo `POST /analysis`. El endpoint ya
  aceptaba `game_ids` como lista y un `engine` desde la fase 1; lo que no
  existía era **pedirlo desde ninguna pantalla** —el único sitio del front que
  llamaba a `createAnalysis` era el visor, con un lote de una partida—, así que
  "analiza mis últimas N partidas" solo se podía hacer con `curl`. Las
  decisiones que el texto del requerimiento no fijaba están en la nota "Con qué
  reglas se cumplió RF-2.5" de
  [02-requerimientos.md](docs/02-requerimientos.md).
  - **Columna «Análisis», que es parte del requerimiento y no un adorno**: dice
    con qué motores está analizada ya cada partida, porque sin eso la tanda se
    compone a ciegas. Dice **motores y no un sí o un no** —la misma partida se
    analiza con Stockfish y con Lc0 (RF-2.6) y son análisis distintos— y una
    partida sin ninguno dice **"Sin analizar" y no "—"**: el guion es el hueco
    de un dato que no llegó, y aquí no falta nada.
  - **Dos campos nuevos en `GameSummary`, los dos aditivos**:
    `analyzed_by_engines` y `has_analysis_in_progress`, que hereda `GameDetail`.
    **No rompen contrato** —nada de lo que ya consumía la API deja de
    funcionar— y **no hay migración**, porque no salen de `games` sino de
    `analyses`: lo resuelve `services/games.py::load_analysis_state_by_game_id`
    en **una sola consulta para toda la página**, ya que el listado sirve hasta
    200 filas de una vez. "Estar analizada" no es una columna de la partida
    sino el resultado de las corridas que se le hayan lanzado. `openapi.json` y
    los tipos de `packages/shared-types` regenerados con `make types`; el
    número de versión de `info.version` no se mueve, sigue en `0.6.0`.
  - **`lib/format.ts::formatAnalyzedByEngines`**, que es quien decide cómo se
    lee esa columna: los motores terminados, "Analizando…" cuando hay uno en
    marcha y nada hecho, y "Stockfish · analizando…" cuando hay las dos cosas
    —que es el caso que se leería mal con cualquiera de los otros dos textos—.
    Con sus cuatro tests.
  - **Quedan dos filas abiertas** del inventario de
    [07-coherencia-ui.md](docs/07-coherencia-ui.md), las **110** y **111**, las
    dos de la misma raíz: la tanda se manda bien pero no cuenta lo que hace
    después. Ver abajo por qué **no impiden dar RF-2.5 por entregado**.
- **[ADR-0023](docs/adr/0023-la-ocupacion-entra-en-el-entrenamiento-y-la-barra-no.md)**,
  la decisión que `0.5.0` tomó y no escribió donde se buscan las decisiones: en
  las pantallas de entrenamiento **entra la capa de ocupación (RF-7.1 a 7.7) y
  no la barra de evaluación**, y las tres marcas **arrancan apagadas**. Estaba
  razonada —en este archivo, en la nota de RF-7 de
  [02-requerimientos.md](docs/02-requerimientos.md) y en el ítem del roadmap—,
  pero un ADR no es donde se cuenta lo que se hizo sino dónde se va a buscar
  por qué, y CLAUDE.md manda las decisiones de arquitectura a `docs/adr/`. La
  entrada de `0.5.0` llegó a decir que "la capa no trae ADR": lo que no lo
  necesitaba era la capa, no la frontera de dónde entra, que es lo que se
  decidió y lo que un día alguien querrá discutir.
- **`apps/api/lucia_api/services/review.py`**: la cola de repaso y el apunte
  del resultado, **una sola vez** para los dos ejercicios que se repasan
  —puzzles (RF-4.1) y drills de apertura (RF-4.2)—, genéricos sobre el mixin
  `SpacedRepetition` del modelo. Nace de la de-duplicación de abajo y del
  error de abajo, que es exactamente lo que pasa cuando el mismo algoritmo se
  escribe dos veces: una de las dos copias se quedó atrás.
- **Un test de regresión** del error de la cola de drills
  (`test_the_queue_announces_the_next_review_in_utc`), que es el que faltaba
  para que la copia no volviera a divergir.

### Cambiado

- **Contrato de la API: ocho campos renombrados, los ocho de forma
  incompatible**, y un esquema renombrado con ellos. Quien consumiera estos
  nombres deja de funcionar; no hay periodo de gracia ni alias, porque en la
  serie `0.x` no se debe compatibilidad y arrastrar los dos nombres es la forma
  segura de que nadie arregle nunca el primero. `openapi.json` y los tipos de
  `packages/shared-types` regenerados con `make types`.
  - **`PuzzleOut.color` → `player_color`**: "color" a secas no decía de quién,
    en una respuesta donde hay dos bandos y el que importa es el de quien
    resuelve.
  - **`PuzzleAnswerIn.attempt` → `attempt_number`**: `attempt` se leía como "el
    intento" —la jugada que se manda— cuando es su número, y esa lectura ya
    había costado un incumplimiento de coherencia (la fila que contaba un
    intento de más).
  - **`DrillOut.reason` → `source`** y **`DrillOut.games` → `games_played`**,
    con la **migración `e6c4d20b7f19`**, que renombra las dos columnas
    homónimas de `opening_drills` con `batch_alter_table` —SQLite no renombra
    columnas con un `ALTER` a secas— conservando el índice de `due_at` y la
    clave única `(player_color, line_uci)`. **Solo cambian los nombres; los
    datos se quedan donde están.** `reason` decía "motivo" en una tabla donde
    el motivo lo cuentan `games_played` y `score_percent`: lo que guarda es de
    qué baraja salió la línea, que es su procedencia. Y `games` no decía qué se
    contaba, en una tabla que no guarda partidas.
  - **`DrillMoveOut.finished` → `reviewed`**, **`DrillMoveOut.line_san` →
    `line_moves_san`** y **`length_plies` → `line_length_plies`**: `finished`
    no distinguía "la línea se acabó" de "el repaso quedó apuntado", que es lo
    que de verdad marca; los otros dos no decían de qué eran las jugadas ni de
    qué la longitud, en una respuesta que habla de una línea y de una partida.
  - **`PlanTaskOut.reasons` → `weaknesses`**: son las mismas debilidades que
    `WeeklyPlanOut.weaknesses`, filtradas a las que apuntan a esa tarea, y
    llamarlas de dos maneras en el mismo cuerpo hacía dudar de si eran otra
    cosa.
  - **El esquema `GamePositionIn` pasa a llamarse `SparringOriginIn`**: no es
    una posición de una partida, es de dónde sale una partida de sparring
    (RF-4.4), y con el nombre viejo parecía reutilizable para cualquier cosa
    que llevara `{game_id, ply}`.
- **De-duplicación: −269 líneas netas y ningún cambio de comportamiento.** Todo
  nacido de copias reales, ninguna de anticipación: `services/review.py` (la
  cola y el apunte de repaso, arriba), `features/training/TrainingBoard.tsx`
  (la columna del tablero de entrenamiento, que estaba escrita tres veces —el
  puzzle, el drill y el sparring— y es lo que permitió comparar las tres),
  `features/training/useReviewQueue.ts` (pedir la cola y refrescarla),
  `components/board/TurnList.tsx` (la lista de jugadas por turnos) y
  `tryMove`/`turnsOf` en `lib/moves.ts`, que estaban duplicadas entre el visor
  y el sparring.
- **Accesibilidad: la rejilla de casillas enfocables deja de desmontarse a
  media jugada** (criterios C-1 y C-7). `Chessboard` la montaba según
  `legalMoves`, es decir según si el tablero acepta jugadas **en ese instante**,
  y las tres pantallas de entrenamiento se quedan sin ellas mientras el
  servidor contesta: la rejilla desaparecía en cada jugada, el foco caía al
  `<body>` y la casilla enfocada volvía a e4, mientras el pie del tablero
  seguía prometiendo el teclado. Se monta ahora según `isMovableBoard` —lo que
  el tablero **es** y no lo que puede ahora mismo—, así que durante la espera
  sigue enfocable e inspeccionable pero no le devuelve la pulsación a
  chessground. Con ella, **nueve arreglos más de coherencia de interfaz** y
  **ninguna fila nueva** en esa pasada, que dejó el inventario de RNF-11
  vacío; el detalle, en la pasada del 2026-09-23 de
  [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md).
- **El inventario de RNF-11 vuelve a tener filas, y las abre el análisis en
  lote**: la **110** (la columna «Análisis» no se entera de nada una vez pedida
  la lista, así que una partida que termina mientras se mira se queda en
  "Analizando…" hasta recargar, mientras el visor sí sigue el progreso en
  vivo), la **111** (la tanda no distingue lo ya analizado con ese mismo motor,
  cuando las dos pantallas que analizan de una en una lo dicen con "Reanalizar
  con X") y la **112** (lo marcado sobrevivía al cambio de página), que **se
  cerró en el mismo commit** porque no pedía decidir nada: la regla ya estaba
  tomada para el cambio de filtro. Las otras dos quedan abiertas a propósito
  —piden decidir comportamiento: cada cuánto se refresca una lista y si una
  tanda deduplica— y con ellas **siete arreglos** más en el mismo commit.

### Corregido

- **La cola de drills anunciaba el día equivocado.** `next_due_at` —el "vuelve
  el …" que se enseña cuando no queda nada por repasar hoy— salía del
  vencimiento **más antiguo de todos**, incluidos los ya vencidos, y **sin zona
  horaria**, así que la pantalla mostraba una fecha pasada y, al interpretarla
  el navegador en local, podía además correrla de día. La cola de puzzles lo
  hacía bien: es el precio de haber escrito dos veces el mismo repaso, y por
  eso el arreglo va con la unificación en `services/review.py` y con un test de
  regresión, no suelto.
- **RF-2.5 estaba a medias desde la fase 1 y ningún documento lo decía** — y
  es **P0**. `RF-2.5 · Análisis en lote: "analiza mis últimas N partidas" o
  "todo 2025"` (alcance congelado desde el corte del **2026-09-05**) estaba
  entregado **solo en el servidor**: `POST /analysis` aceptaba `game_ids` como
  lista y un `engine`, y **ninguna pantalla lo pedía**. Como RF-2.9 y RF-3.8,
  **no se citaba en ningún sitio** —cero menciones en el roadmap y cero en este
  archivo—, así que no figuraba ni entre lo pendiente ni entre lo entregado y
  se daba por hecho. Es el **tercer caso del mismo patrón y el peor**: los
  otros dos son P2 y estaban sin empezar, este es P0 y estaba medio hecho, que
  es como se sale de un conteo sin que se note — desde el servidor parecía
  hecho y desde la pantalla parecía que no existía. **Con este commit queda
  entregado entero**, backend e interfaz (ver "Añadido"), y citado por ID en la
  **nota al final de la fase 1** del [roadmap](docs/05-roadmap.md), que es la
  fase donde se entregó su mitad servidor; va como nota y no como casilla
  nueva, por lo mismo que el barrido de RNF-11 es una nota de la fase 3. **No
  cambia lo que falta para `1.0.0`**: entró y salió de lo pendiente en el mismo
  commit, y siguen siendo RF-2.9, RF-3.8, RF-7.8 y RF-7.9.
  - **Se da por entregado con las filas 110 y 111 abiertas, y conviene decir
    por qué.** Lo que pide el requerimiento —mandar a analizar muchas partidas
    de una vez, eligiendo motor, sin ir de una en una— se puede hacer desde la
    pantalla, y la columna dice qué hay hecho para no componer la tanda a
    ciegas. Las dos filas son de **RNF-11**: una lista que no se refresca sola
    y una tanda que no avisa de que va a repetir trabajo son incoherencias con
    lo que las otras pantallas prometen, no partes del requerimiento sin
    hacer. Se arreglan **dentro de 1.0**, como los demás incumplimientos sobre
    RF ya congelados, y **no bloquean el corte**. La línea es la misma que se
    usó con las 38 primeras filas del inventario: un RF se da por entregado
    cuando hace lo que dice, y RNF-11 no se marca nunca como hecho.
- **RF-2.9 había desaparecido del conteo de lo que falta para `1.0.0`.**
  `RF-2.9 · Explicación en lenguaje natural de por qué una jugada es error`
  (P2, alcance congelado desde el corte del **2026-09-05**) existía solo en su
  fila de [02-requerimientos.md](docs/02-requerimientos.md) y **no se citaba en
  ningún otro sitio**: ni en el roadmap —donde el ítem "explicaciones en
  lenguaje natural" de la fase 4 estaba sin ID— ni en este archivo, que daba
  **RF-2** entre lo entregado y contaba **tres** requerimientos pendientes
  donde hay **cuatro** (RF-2.9, RF-3.8, RF-7.8 y RF-7.9), colocando además las
  explicaciones del lado del "pulido". Corregido en los dos documentos, con el
  ID citado en el ítem de la fase 4 como ya se hizo con RF-3.8. **Consecuencia
  que no es de redacción: `1.0.0` no se puede cortar hasta que RF-2.9 esté**,
  porque el corte afirmaría que RF-2 está entregado entero.
- **`0.5.0` no fue un commit ni un día, y decía que sí.** Su entrada y dos
  puntos del roadmap afirmaban que la capa de ocupación y el barrido de RNF-11
  viajaban "en el mismo commit" y "con la misma fecha". Son `c06cdaa`
  (2026-09-22) y `81de827` (2026-09-23), y el segundo **no toca ningún
  manifiesto**: llegó después del corte, con dos cambios incompatibles de
  contrato y un ADR, sin subir versión. Se queda dentro de `0.5.0` —que es el
  número que ese commit lleva, y nada se ha publicado ni etiquetado— pero
  diciéndolo; el razonamiento completo, en la propia entrada de `0.5.0`.
- **RNF-11 figuraba como casilla marcada de la fase 3**, contradiciendo lo que
  el propio roadmap dice de él dos secciones más abajo: que vive en Post 1.0
  como criterio permanente, sin fase propia, y que nada de esa sección cuenta
  para el progreso hacia 1.0.0. El barrido de cierre pasa a ser una **nota de
  cierre** de la fase, no un ítem: la fase 3 son **seis** casillas y la cierra
  la sexta. **No se pierde nada del relato ni del alcance** —las dieciséis
  filas eran incumplimientos de RF ya congelados y por eso se arreglaron dentro
  de 1.0—; lo que se pierde es la idea de que un criterio permanente se puede
  dar por terminado.
- **Documentación que había dejado de ser cierta** al renombrar: los nombres
  viejos que quedaban en [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md) y
  en las entradas `0.4.5` y `0.5.0` de este archivo
  (`ExerciseStatusBadge` → `TrainingStatusBadge`, `reasons` → `weaknesses`,
  `attempt` → `attemptNumber`), y la fila 102, que justificaba el total en el
  cuerpo "porque las tres pestañas hermanas lo traen así" cuando son dos: el
  listado de sparring no reparte cola y no lleva total.

## [0.5.0] - 2026-09-22

**Cierra la fase 3 del roadmap**, y por eso sube el minor y no el patch. Trae
**dos cosas grandes, en dos commits de dos días** —`c06cdaa` del 2026-09-22 y
`81de827` del 2026-09-23—, y **solo la primera es un ítem de la fase**:

1. La **capa de ocupación del tablero** (**RF-7.1 a RF-7.7**) entra en las tres
   pantallas de entrenamiento que tienen tablero —el puzzle (RF-4.1), el drill
   de apertura (RF-4.2) y la partida de sparring (RF-4.3 y RF-4.4)—, que era el
   sexto ítem de la fase y el único que le quedaba desde que `0.4.5` cerró
   **RF-4 entero** sin cerrarla. Con esto son **cinco pantallas con la misma
   capa**: el visor (RF-5), el tablero de análisis (RF-6) y esas tres. Es lo
   que la fase 2 dejó dicho que se haría cuando las pantallas de entrenamiento
   existieran.
2. El **barrido de cierre de la fase 3 para RNF-11** (coherencia de interfaz),
   que **no es un séptimo ítem** —la fase tiene seis y la cierra el de arriba—
   sino lo que a ese cierre se le preveía: las **dieciséis filas** que quedaban
   del inventario de
   [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md) cerradas de una vez
   —las quince que la sección de Entrenamiento había ido abriendo pantalla a
   pantalla (91, 92, 94 a 105 y 107) más la **109**, que nació al comprobar el
   propio barrido—, y **el inventario queda vacío**. Es lo que se decidió el
   2026-09-19 al abrir la primera de esas filas: seis de ellas pedían decidir
   en qué se parecen las pantallas de Entrenamiento, y eso no se puede decidir
   con la primera delante.

Lo que **cierra la fase es el primero**; el segundo es lo que al cierre se le
preveía, y no tiene versión propia porque **RNF-11 es un criterio permanente y
no una casilla del roadmap**: la fase se cierra con una versión, el inventario
no.

**Fechas y commits, que no son uno solo.** Esta entrada dijo hasta `0.6.0` que
las dos cosas viajaban "en el mismo commit y la misma fecha", y es falso: la
capa de ocupación es de `c06cdaa`, del **2026-09-22**, que es el commit que
subió el número a `0.5.0` en los diez manifiestos; el barrido es de `81de827`,
comiteado el **2026-09-23**, que **llegó después del corte y no volvió a
subirlo**. Su trabajo empezó el 22, pero comprobarlo —leer las cinco pantallas
con tablero estado por estado— se llevó el día siguiente, y es lo que dejó esos
cinco arreglos mecánicos más y la fila 109 dentro de ese segundo commit. El inventario está vacío **al 2026-09-23**.

**Por qué el segundo commit se queda dentro de `0.5.0` y no lleva un `0.5.1`
propio**, aun trayendo dos cambios incompatibles: porque `0.5.0` **es** su
versión, no una que se le adjudique ahora. Sus diez manifiestos dicen `0.5.0`,
y ni `0.5.0` ni ninguna otra de esta serie se ha publicado ni etiquetado, así
que no hay nadie a quien un número congelado le hubiera prometido otra cosa.
Inventar un `0.5.1` sería crear una versión que ningún commit llevó nunca —una
mentira de otro tipo, y más difícil de ver—. Lo que sí hacía falta era decirlo:
**`0.5.0` abarca dos commits y dos días**, y el trabajo de su segundo día
cambió la API sin que el número lo avisara. `0.6.0` es la primera versión que
no repite esa forma de trabajar: el número se sube con el trabajo, no después.

**Con la fase 3 cerrada quedan cerradas las fases 0 a 3**, y para `1.0.0` queda
la **fase 4**: RF-3.8 (rivales recurrentes), RF-7.8 y RF-7.9 —que son los dos
extras de esta misma capa: recordar el sub-modo entre sesiones y las casillas
críticas según motor—, las explicaciones en lenguaje natural, el empaquetado y
macOS/Windows.

**No hay alcance nuevo, tampoco con el barrido.** RF-7 es alcance congelado de
v1.0 desde el corte del **2026-09-05**. RNF-11 vive en Post 1.0 y **sigue
ahí**: trabajarlo no lo mueve de sección ni lo mete en el conteo de progreso
hacia 1.0.0, porque es una práctica de trabajo vinculante en cada commit de
`apps/web` y no una prestación que se entregue. Sus dieciséis filas, en
cambio, eran incumplimientos de requerimientos **ya congelados** —RF-4.1 a
RF-4.5, RF-5, RF-6 y RF-7—, y por eso se arreglan dentro de 1.0. No se ha
añadido ningún RF ni RNF, nada baja a Post 1.0 y nada sube a 1.0.

**Esta versión sí toca el contrato de la API**, al contrario de lo que se dijo
cuando esta entrada solo recogía la capa de ocupación: el barrido cambia tres
endpoints y **dos de esos cambios son incompatibles** —`SparringGameOut` pierde
`opponent_name` y `GET /training/replays` deja de devolver una lista—, porque
la incoherencia estaba en el dato y no en cómo se pintaba. Sigue siendo
`0.5.0`, por lo dicho arriba —ese es el número que el commit lleva y nada se ha
publicado—, y en la serie `0.x` la API puede cambiar sin aviso entre versiones
menores, como dice la cabecera de este archivo. **Sin migraciones y sin cambios
de esquema ni de datos.**

### Añadido

- **Capa de ocupación del tablero en el entrenamiento** (RF-7.1 a RF-7.7 sobre
  RF-4.1 a RF-4.4): la misma tecla `O`, el mismo panel y el mismo cálculo de
  `apps/web/src/components/board/` que ya tenían el visor y el tablero de
  análisis, sin endpoint, sin migración y sin reglas de conteo nuevas — es lo
  que hace que sean cinco pantallas y no cinco copias. **Entran las tres que
  tienen tablero y ninguna más**: el plan (RF-4.5), la lista de re-jugar y la
  antesala de sparring no lo tienen, y en el resto de la aplicación la capa no
  pinta nada que mirar.
  - **La capa entra donde la barra de evaluación no entró**, y esa es la línea
    que se decidió aquí: las pantallas de RF-4 renunciaron a la barra a
    propósito —decir a cada jugada quién va ganando convierte el ejercicio en
    un análisis asistido—, pero la ocupación es **lectura de la posición que ya
    está en pantalla y no opinión del motor**, y la cabecera de RF-7 dice desde
    el primer día que se activa sobre **cualquier** tablero, entrenamiento
    incluido.
  - **Ahí las tres marcas arrancan apagadas** (`marksOnByDefault: false`), y
    siguen arrancando encendidas en el visor y en el tablero de análisis:
    rodear las piezas colgadas (RF-7.4) es media solución de un puzzle y, en
    una partida de sparring, el aviso de blunder que un rival calibrado no debe
    dar. Se apagan las tres a la vez —colgadas, clavadas (RF-7.6) y rayos X
    (RF-7.5)— y no solo las que delatan, porque el panel las presenta como tres
    controles iguales; quien las quiera las enciende a sabiendas, y el propio
    panel dice ahí mismo que arrancan apagadas y por qué.
  - **Las marcas gobiernan también lo que el panel dice**, no solo lo que
    dibuja: con su marca apagada, la inspección calla "· colgada", "· clavada"
    y la lista de rayos X. Sin eso, apagar una marca era un gesto sin efecto
    —pulsar una casilla entregaba en palabras justo lo que se había pedido no
    ver—. **El conteo de atacantes y defensores va siempre**: es el propio
    RF-7.3 y no una marca.

  Las decisiones que el texto del requerimiento no fijaba están en la nota
  "Cómo se cumplieron los siete puntos P1" de
  [docs/02-requerimientos.md](docs/02-requerimientos.md), ampliada con esta
  fecha, y en el ítem de cierre de la fase 3 del
  [roadmap](docs/05-roadmap.md). Esta entrada dijo aquí que **"la capa no trae
  ADR"**, por lo mismo que no lo trajo en `0.3.0` cuando nació —es una capa de
  lectura sobre la posición que ya está en pantalla, sin endpoint, sin esquema
  y sin motor—. Se corrigió en `0.6.0`: lo que decide esta versión no es la
  capa, es **dónde entra y dónde no**, y eso sí es una decisión de arquitectura.
  Está en el
  [ADR-0023](docs/adr/0023-la-ocupacion-entra-en-el-entrenamiento-y-la-barra-no.md).
  El ADR-0022 de más abajo es del barrido y no de ella.

- **Mover una pieza con el teclado en los cuatro tableros donde se juega**
  (RNF-11 fila 91, criterio C-1, sobre RF-4.1, RF-4.2, RF-4.3/RF-4.4 y RF-6):
  el puzzle, el drill, la partida de sparring y el tablero de análisis solo se
  dejaban usar arrastrando. Ahora **Intro elige el origen y vuelve a pulsarse
  en el destino, y Esc suelta lo elegido**. Era la fila más vieja del
  inventario y la única que no se podía arreglar en su pantalla, porque la
  rejilla enfocable que ya existía activa **una** casilla y una jugada son dos.
  La solución no fue inventar el flujo de dos pasos sino **devolvérselo a
  chessground**: la rejilla sube de `OccupancyLayer` a `Chessboard`, que es
  quien conoce los dos trabajos de una casilla —ser origen o destino de una
  jugada e inspeccionarse (RF-7.3)— y puede darle a Intro uno solo sin
  superponer dos juegos de paradas de foco. El editor de posición (RF-6.1)
  conserva la suya por `overlay`, porque ahí activar una casilla es colocar una
  pieza.
- **Cuatro módulos compartidos del front**, todos nacidos de duplicación real y
  ninguno por anticipación: `components/PanelList.tsx` (el listado de filas
  dentro de un panel, que estaba escrito a mano en el listado de sparring y
  copiado carácter a carácter en el de re-jugar; no sustituye a `DataTable`,
  porque una fila de re-jugar se despliega para enseñar el formulario de
  dificultad), `components/board/BoardFrame.tsx` (la medida del tablero, que
  salía de dos tamaños según llevara barra de evaluación o no — fila 107; vive
  ahí y no en `Chessboard` para que el editor de posición no la herede),
  `components/board/hints.ts` (las frases del pie del tablero) y
  `features/training/TrainingStatusBadge.tsx` (la insignia del panel lateral,
  que significaba tres cosas distintas en las tres pantallas con tablero).
- **[ADR-0022](docs/adr/0022-la-probabilidad-de-victoria-se-cuenta-desde-quien-entrena.md)**,
  la única excepción escrita del barrido (fila 92): la probabilidad de victoria
  **se cuenta desde quien entrena cuando la frase nombra el bando** —"Tu
  probabilidad de victoria pasó de 62,0 % a 31,0 %"—, y es el criterio **C-5 el
  que cede**. Girarla a las blancas habría sido coherente con la fila 52, pero
  quien juega con negras leería "31 puntos más" justo debajo del titular que le
  dice que acaba de cometer un error grave. El punto de vista de las blancas
  sigue siendo obligatorio en todo número suelto —una columna, una insignia, un
  gráfico—, que es donde nadie puede preguntar desde dónde se cuenta. Va a ADR
  y no al inventario porque **un criterio con excepción es una decisión y no un
  arreglo**.
- **Nueve tests nuevos**: cinco del front para `formatMoveSequence` y dos para
  `turnsOf`, y dos de API —el `starting_ply` de una partida retomada y el total
  de la cola de re-jugar—. El total queda en **352 de Python y 166 del front**.

### Cambiado

- **`Chessboard` recibe la capa por una sola propiedad**,
  `occupancyController`, en vez del trío `overlay` + `onSelectSquare` +
  `onHoverSquare` con el que la montaban el visor y el tablero de análisis: las
  tres piezas van siempre juntas, y repetirlas a mano en cinco pantallas era
  poder equivocarse en una. **`overlay` queda para la rejilla del editor de
  posición** (RF-6.1), que es lo único que la usa aparte. La frase que anuncia
  el atajo `O` pasa a ser una constante compartida,
  `OCCUPANCY_TOGGLE_KEY_HINT`, al lado de la tecla que nombra (criterios C-1 y
  C-2).
- **Cuatro cambios de comportamiento visibles**, los cuatro del barrido y los
  cuatro con decisión detrás; van aparte para que no se lean como arreglos de
  estilo:
  - **La partida de sparring se encabeza como pantalla de detalle** (fila 94,
    C-2): llevaba la cabecera de la sección, así que se titulaba
    "Entrenamiento", volvía atrás con un botón al final del lateral y la
    pestaña "Sparring" hacía lo mismo con otro nombre. Ahora lleva "← Volver a
    sparring" sobre un título que nombra la partida, **sin sub-navegación**,
    como el visor y el tablero de análisis: una partida concreta no es una
    forma de entrenar entre cinco. Con ella suben a la cabecera sus acciones
    —"Abrir como tablero" y "Abandonar"— (fila 109).
  - **El drill deja la jugada errónea sobre el tablero al fallar** (fila 97,
    C-2 / C-3), como ya hacía el puzzle, que es el que tenía la razón escrita:
    borrarla al instante da la sensación de que la pieza rebotó y no de que la
    respuesta era otra. Hace falta pulsar "Volver a intentarlo".
  - **El plan dice de qué son los puntos de cada magnitud** (fila 104, C-5 /
    C-6): "puntos" nombraba tres cosas seguidas en la misma lista. Ahora son
    "pts de prob. de victoria", "puntos de marcador" y "puntos de precisión", y
    la de la apertura dice además frente a qué se pierden.
  - **Cada tarjeta de deberes se llama como la pestaña a la que lleva** (fila
    105, C-2): decían "Líneas de apertura", "Posiciones a re-jugar" y "Partidas
    contra el motor" y se aterrizaba en "Aperturas", "Re-jugar" y "Sparring".
    Manda el nombre del destino; lo que la tarjeta hace lo cuenta la frase de
    debajo.
- **Contrato de la API: tres endpoints cambiados, dos de ellos de forma
  incompatible**, porque en esos tres la incoherencia estaba en el dato y no en
  cómo se pintaba. `openapi.json` y los tipos de `packages/shared-types`,
  regenerados con `make types`; ver los flujos 12, 13 y 14 de
  [docs/03-arquitectura.md](docs/03-arquitectura.md).
  - **`SparringGameOut` pierde `opponent_name`** (fila 96) y **gana
    `starting_ply`** (fila 101). El nombre del rival lo componían por separado
    el front y el servidor, y coincidían carácter a carácter sin que nada lo
    garantizara: lo compone ya solo `lib/format.ts::formatOpponentName`, y el
    del servidor se queda para la cabecera del PGN, que es un documento que se
    abre en otros programas y donde `[Black "lc0"]` no diría contra quién se
    jugó. `starting_ply` sale de `starting_fen` y no de `origin_ply` —que es
    relativo al inicio de la partida de origen y da otro número si esa no
    empezaba en la salida— y con él una partida retomada (RF-4.4) se numera
    desde donde empieza.
  - **`GET /training/replays` deja de devolver una lista y devuelve
    `ReplayQueueOut`** (`positions` + `total`, fila 102), para poder decir "20
    de 312" como las otras colas. El total va en el cuerpo y no en una cabecera
    `X-Total-Count` como el listado de Partidas, porque con las tres pestañas
    hermanas es con las que se compara al cambiar de pestaña.
  - **`DrillQueueOut` gana `positions_missing`** (fila 99), de la misma
    `compare_repertoire` que ya lo contaba al generar: el repertorio se llena a
    trozos ([ADR-0010](docs/adr/0010-repertorio-con-red-y-cacheado.md)), así
    que una cola corta puede serlo porque falte teoría y no porque se juegue
    bien, y eso es una condición de la pantalla al llegar y no el resultado de
    pulsar "Generar líneas".
- **Inventario de RNF-11: de quince filas abiertas a ninguna.** La capa de
  ocupación abrió la **107** —el mismo tablero dibujado de dos tamaños, que
  venía de antes y solo se veía con las cinco columnas construidas igual—,
  cerró la **108** el mismo día y precisó la **91**; el barrido cerró después
  esas quince y la **109** que él mismo destapó. **El inventario queda vacío**,
  por segunda vez desde que existe. Ver
  [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md), donde está el detalle
  fila a fila de las dieciséis.

### Corregido

- **Un tablero que dejaba de aceptar jugadas las seguía aceptando.** Quitarle
  `legalMoves` no bastaba: `buildBoardConfig` omite `movable` cuando no las hay
  —mandarlo en `undefined` le borraría a chessground ese trozo de estado— y
  chessground **conserva entonces los destinos de la posición anterior**, así
  que las piezas se seguían arrastrando sobre el puzzle ya fallado y el tablero
  acababa enseñando una posición que no era la de nadie. `Chessboard` le manda
  ya los **destinos vacíos**. Con eso el puzzle cierra su tablero al cerrarse y
  mientras el servidor comprueba, que es la regla que el drill y el sparring ya
  tenían (`canMove`). Salió de comprobar el barrido leyendo las cinco pantallas
  con tablero estado por estado (criterio C-3).
- **Con las tres marcas apagadas, el lector de pantalla las seguía diciendo**
  (C-3). La fila 108 hizo que gobernaran la inspección del panel, pero la
  rejilla enfocable que se mudó a `Chessboard` seguía diciendo "clavada" y
  "colgada" en el `aria-label` de cada casilla: con teclado y lector de
  pantalla, apagarlas volvía a ser un gesto sin efecto **justo en las tres
  pantallas de entrenamiento, que son donde arrancan apagadas**.
  `describeSquareOccupancy` recibe ya las marcas, como `SquareInspection`.
- **El atajo del teclado se anunciaba donde el tablero no acepta jugadas**
  (C-1). `KEYBOARD_MOVE_HINT` se encadenaba siempre, así que el puzzle cerrado,
  la línea terminada y la partida acabada decían "el tablero ya no se mueve" y
  a continuación "Intro elige origen y destino", en la misma frase. Va ahora
  donde va la invitación a arrastrar y no más: las dos vías se prometen juntas,
  que es lo que pide C-1. En el tablero de análisis sigue saliendo siempre,
  porque allí el tablero siempre acepta jugadas. De paso, la frase del teclado
  del **editor de posición** pasa a usar las mismas palabras que las otras
  cinco pantallas, cambiando solo lo único que cambia: lo que hace Intro.
- **Comentarios y READMEs que habían dejado de ser ciertos**: `TrainingHeader`
  y `features/training/README.md` seguían diciendo que las **seis** pantallas
  de la sección comparten cabecera, cuando la fila 94 sacó de ahí a la partida
  de sparring; y los cuatro archivos que estrena este barrido no estaban en la
  tabla de su README, que es donde se mira antes de copiar una receta a mano.

## [0.4.5] - 2026-09-21

El entrenamiento deja de ser cuatro barajas sueltas y pasa a tener portada:
el **plan de entrenamiento semanal** (**RF-4.5**), que junta lo que RF-3 sabe
del jugador con lo que RF-4 sabe entrenar y dice **por dónde empezar esta
semana**. **Con esto queda cerrado RF-4 entero** (RF-4.1 a RF-4.5, entregados
entre el 2026-09-19 y el 2026-09-21).

**La fase 3 no se cierra con esto, y conviene no leer lo uno como lo otro.** Le
queda un ítem, y no es de RF-4: enchufar la capa de ocupación (RF-7.1 a 7.7) en
las pantallas de entrenamiento, que la fase 2 dejó pendiente de que existieran.
Ya existen las seis y **ninguna la usa** —comprobado sobre el código, no sobre
la documentación: `OccupancyLayer` y `useOccupancy` solo se importan desde el
visor y el tablero de análisis—. Por eso esto sube el **patch y no el minor**,
mismo criterio que en `0.2.1` a `0.2.5` y en `0.4.1` a `0.4.4`; el minor
`0.5.0` le toca a quien cierre esa casilla.

**No hay alcance nuevo**: RF-4.5 es alcance congelado de v1.0 desde el corte
del **2026-09-05** y es P2, que dentro de este proyecto significa "deseable
dentro de 1.0" y no "para después". No se ha añadido ningún RF ni RNF, nada
baja a Post 1.0 y nada sube a 1.0.

### Añadido

- **Plan de entrenamiento semanal** (RF-4.5): la pestaña "Plan" de
  Entrenamiento, que dice **qué falla** —con su número y de qué requerimiento
  de RF-3 sale— y debajo **los deberes que salen de ahí**, cada uno con su
  objetivo de la semana y su avance. En la API, un solo endpoint y de solo
  lectura, `GET /training/plan`
  (`apps/api/lucia_api/services/plan.py` y `routers/plan.py`); en el núcleo,
  `lucia_core.plan` con `detect_weaknesses`, `task_for_weakness` /
  `_TASK_BY_WEAKNESS`, `build_weekly_tasks` y `week_start`, sin base de datos,
  sin motor y sin red, para poder probarse solo (RNF-8). Razonado en
  [ADR-0021](docs/adr/0021-el-plan-semanal-se-deduce-y-el-orden-de-las-debilidades-es-editorial.md),
  y las reglas que el texto del requerimiento no fijaba, en la nota "Con qué
  reglas se cumplió RF-4.5" de
  [docs/02-requerimientos.md](docs/02-requerimientos.md).
  - **Sin tabla y sin migración.** El plan **no se guarda**: se recalcula en
    cada visita a partir de las estadísticas de RF-3 y de las colas de RF-4, y
    lo hecho sale de fechas que la base ya tenía —`puzzles.last_reviewed_at`,
    `opening_drills.last_reviewed_at` y `sparring_games.created_at`—, así que
    **nadie marca un deber a mano**: entrenar en las otras pestañas es lo que
    mueve la barra. Es la misma decisión que los patrones
    ([ADR-0008](docs/adr/0008-patrones-deducidos-al-leer.md)) y la lista de
    re-jugar
    ([ADR-0020](docs/adr/0020-re-jugar-desde-el-error-es-sparring-desde-otra-posicion.md)),
    y la contraria a la de los puzzles y los drills
    ([ADR-0017](docs/adr/0017-puzzle-persistido-con-su-solucion-congelada.md)).
    **RF-4.5 es el único punto de RF-4 que no toca el modelo de datos.**
  - **Cinco clases de debilidad, cada una con su umbral**, y ninguna aparece
    por debajo del suyo: la fase donde se pierde ventaja (RF-3.3,
    `MIN_PHASE_WIN_PERCENT_LOST` = 5 puntos de probabilidad de victoria por
    jugada), el tipo de error que más pesa (RF-3.4, `MIN_MISTAKE_TYPE_SHARE`
    = 33 %, cuando el reparto ciego entre cuatro tipos sería el 25 %), la
    apertura que más cuesta (RF-3.2, `MIN_OPENING_POINTS_LOST` = 1 punto de
    marcador, el mismo umbral con el que el drill de RF-4.2 decide qué línea
    merece repetirse), los apuros de reloj (RF-3.5,
    `MIN_TIME_TROUBLE_SHARE` = 30 % de las partidas) y la precisión que cae
    (RF-3.7, `MIN_ACCURACY_DROP` = 2 puntos). Un plan que enumera cinco
    debilidades siempre, las tenga o no, no ayuda a decidir por dónde empezar.
  - **El orden de las debilidades es editorial y no numérico**, que es la
    mitad de ADR-0021: cada una se mide **en su propia unidad** —puntos de
    probabilidad, porcentaje de errores, puntos de marcador, porcentaje de
    partidas, puntos de precisión— y ordenarlas por magnitud sería inventar
    una escala común en la que el 55 % de errores tácticos pesa más que perder
    8 puntos de probabilidad por jugada. El orden es fijo por clase, de lo más
    estructural a lo más circunstancial, y la primera lleva la insignia "lo
    primero": es una recomendación de la que se responde.
  - **Cada deber nace de una debilidad concreta y la lleva encima**
    (`_TASK_BY_WEAKNESS`, `weaknesses`), que es la lectura de "generado a partir
    de las debilidades detectadas": lo táctico y el medio juego van a puzzles
    (RF-4.1), lo posicional y la apertura a repetir líneas (RF-4.2), el final
    a re-jugar posiciones (RF-4.4), y los apuros de reloj y la precisión que
    cae a partidas enteras contra el motor (RF-4.3), que es lo único que
    reproduce la fatiga de una partida de verdad. Una debilidad sin
    entrenamiento posible no genera deber, y un deber sin motivo a la vista
    sería una cuota inventada.
  - **El objetivo nunca pide más de lo que hay**: `min(MAX_WEEKLY_TARGETS,
    material disponible)`, y sin material no hay tarea. Un plan que pide
    treinta puzzles cuando hay cuatro no es exigente, es falso. Puzzles y
    líneas cuentan como material **solo lo que vence esta semana**: repasar
    antes de tiempo no es entrenar, es adelantar trabajo que el SM-2 ya había
    colocado en otra fecha.
  - **La semana empieza el lunes** (`week_start`) y no "hace siete días": con
    una ventana móvil, lo entrenado el lunes dejaría de contar el martes
    siguiente y el avance bajaría solo, sin que nadie hiciera nada.
  - **Un plan vacío no es un fallo, y hay dos vacíos distintos**: sin partidas
    analizadas la pantalla manda a analizar, porque no se sabe nada todavía; y
    con partidas analizadas y nada por encima de su umbral, dice que no ha
    encontrado nada que destaque. Por eso la respuesta lleva sobre cuántas
    partidas se hizo el diagnóstico.
- **`ProgressBar`** (`apps/web/src/components/ProgressBar.tsx`): la barra de
  avance, extraída de `ProgressBox` y compartida con las tarjetas de deberes
  del plan, para que "cuánto llevas" se dibuje igual en toda la aplicación
  (criterio C-5).

### Cambiado

- **La portada de Entrenamiento ya no son los puzzles, es el plan.** Es el
  único cambio de comportamiento visible de esta versión y se dice aparte para
  que no se lea como un alta más: **`/training` deja de abrir los puzzles y
  abre el plan**, y los puzzles se mudan a **`/training/puzzles`**
  (`TrainingPage` → `PuzzlesPage`). Quien tuviera `/training` guardado o
  enlazado sigue entrando en Entrenamiento, pero cae en otra pantalla. El
  motivo es cuál de las dos responde a "¿por dónde empiezo?": el plan es la
  pantalla que lo dice y las otras cinco son adónde manda. La sección pasa a
  tener cinco pestañas —Plan, Puzzles, Aperturas, Re-jugar, Sparring—, y la
  fila de pestañas de `TrainingHeader` gana `flex-wrap` porque con la quinta ya
  no cabe en una ventana estrecha. **No es alcance nuevo**: mueve una pantalla
  que ya existía, no añade requerimiento ninguno.
- **`formatPhase` sube a `lib/format.ts`** desde donde estaba: el plan nombra
  las fases de la partida (RF-3.3) igual que el dashboard, y dos copias de la
  misma traducción acaban diciendo lo mismo de dos maneras.
- **Tres filas nuevas del inventario de RNF-11** (la 104 a la 106), abiertas
  por esta pantalla, que es la primera que enseña **cinco magnitudes distintas
  seguidas**: la 106 se cerró en el mismo commit y las otras dos quedan
  **abiertas** —cómo se nombra cada magnitud y cómo se llaman los destinos de
  las tarjetas—, para el barrido de cierre de la fase 3 junto a las doce
  anteriores. Ocho arreglos más en el mismo commit; ver
  [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md).
- Contrato de la API: ruta y esquemas **nuevos** (`/training/plan`,
  `WeeklyPlanOut`, `PlanTaskOut`, `WeaknessOut`), todos añadidos: nada de lo
  que ya consumía la API se rompe, y no hay migración porque no hay tabla.
  `openapi.json` y los tipos de `packages/shared-types` regenerados con
  `make types`.

## [0.4.4] - 2026-09-21

Una partida propia deja de terminarse donde se torció: **"re-juega desde el
error"** (**RF-4.4**), que retoma contra el motor una posición de una partida
ya jugada y la sigue desde ahí. Cierra el **cuarto ítem de la fase 3** del
roadmap, que **sigue abierta** con el plan semanal (RF-4.5) y la capa de
ocupación en las pantallas de entrenamiento, así que sube el **patch y no el
minor**, mismo criterio que en `0.2.1` a `0.2.5` y en `0.4.1` a `0.4.3`. **No
hay alcance nuevo**: RF-4.4 es alcance congelado de v1.0 desde el corte del
**2026-09-05**, no se ha añadido ningún RF ni RNF y nada baja a Post 1.0 ni
sube a 1.0.

**Lo que sí hubo que comprobar**, porque aquí había materia: poder retomar
**cualquier** posición de la partida y con cualquier bando es una lectura
generosa del texto del requerimiento, que dice "desde la posición del blunder"
en singular. Se toma como el caso que importa y no como una restricción, y
**no mete RF-11 dentro de v1.0** —verificado contra el código, no solo contra
la documentación—: las posiciones salen siempre de partidas propias ya
guardadas y por HTTP se mandan como partida + jugada, nunca como FEN, así que
no hay posición inventada (RF-11.1); no existe ninguna perilla de ventaja
material (RF-11.2); y la partida retomada vive en `sparring_games` y no se
escribe en `games` con `[SetUp "1"]` (RF-11.3), que sigue pidiendo el acto
explícito de RF-6.5. Razonado en
[ADR-0020](docs/adr/0020-re-jugar-desde-el-error-es-sparring-desde-otra-posicion.md).

### Añadido

- **Re-jugar desde el error** (RF-4.4): la pestaña "Re-jugar" de Entrenamiento
  (`/training/replays`), con los errores propios que más caros salieron y su
  formulario para retomar cada uno, y el botón **"Jugar desde aquí"** en la
  cabecera del visor, que abre la partida desde la posición que se está
  viendo. En la API, `GET /training/replays`
  (`apps/api/lucia_api/services/replays.py` y `routers/replays.py`) y un
  `origin` nuevo en `POST /sparring/games`; en el núcleo,
  `lucia_core.sparring.board_at_ply`, que saca del PGN guardado la posición
  tras N jugadas, sin base de datos ni motor (RNF-8). Las reglas que el texto
  del requerimiento no fijaba están en la nota "Con qué reglas se cumplió
  RF-4.4" de [docs/02-requerimientos.md](docs/02-requerimientos.md).
  - **Retomar es sparring desde otra posición, y no otra cosa**: misma tabla,
    mismo ciclo de endpoints, misma pantalla de juego y mismo listado —donde
    una partida retomada se distingue con una insignia y enlaza de vuelta al
    visor—. Lo que faltaba para esto, que el motor **juegue** y no solo
    analice, lo había resuelto RF-4.3 con `EngineBridge.play`, y
    `starting_fen` ya era columna precisamente para poder arrancar en otro
    sitio. Una partida retomada **tampoco cuenta** en estadísticas ni en
    patrones (RF-3), por la misma frontera que el sparring.
  - **La lista de errores no se persiste**: se deduce de los análisis que ya
    hay cada vez que se pregunta
    ([ADR-0008](docs/adr/0008-patrones-deducidos-al-leer.md)), que es la
    decisión **contraria** a la de los puzzles (RF-4.1) y los drills (RF-4.2)
    ([ADR-0017](docs/adr/0017-puzzle-persistido-con-su-solucion-congelada.md)).
    La diferencia es el estado propio: un puzzle arrastra un historial de
    repasos SM-2 que no está en ninguna otra parte, mientras que una posición
    desde la que re-jugar no se repasa, no vence y no acumula intentos, así
    que guardarla solo daría una segunda copia que envejece en cuanto se
    reanaliza la partida. Por lo mismo **no hay botón de generar**: la pestaña
    está llena en cuanto hay una partida analizada.
  - **La posición la deriva el servidor y por HTTP no viaja ningún FEN.** Se
    manda `{game_id, ply}` y el servidor saca la posición de `games.pgn`;
    `ply` cuenta jugadas ya hechas, así que retomar justo antes de un error es
    pedir el ply de ese error, que es como lo numera `AnalyzedMove`.
  - **Se puede retomar cualquier posición y con cualquier bando** desde el
    visor: una apertura que va mal se rehace desde la jugada 6 y no desde la
    24. La pestaña, en cambio, se ciñe a los errores graves —los mismos que
    dan puzzle (`PUZZLE_CLASSIFICATIONS`)— ordenados por lo que costaron: la
    libertad está en el visor y la lista curada responde a "¿por dónde
    empiezo?". **Quién abre no es "las blancas"** sino quien tenga el turno en
    la posición de partida, y el bando que se ofrece por defecto es el que se
    jugaba en la partida original.
  - **`sparring_games` gana `origin_game_id` y `origin_ply`** (migración
    `d5a81c6e3f04`), que son **procedencia y no dependencia**: sirven para
    decir en pantalla de dónde salió la partida y llevar de vuelta al visor.
    La clave foránea es `ON DELETE SET NULL` y no hay cascada, porque borrar
    la partida de origen no invalida lo jugado —la posición vive en
    `starting_fen`—, solo deja de haber adónde volver.
  - **Lo que costó el error viaja en la lista**, al revés que en un puzzle
    abierto: aquí no hay nada que adivinar —la jugada que se hizo está a la
    vista y de lo que se trata es de jugar la posición mejor de lo que se
    jugó— y saber cuánto costó es lo que dice por cuál empezar.

### Cambiado

- **El formulario de dificultad del sparring es ahora compartido**
  (`apps/web/src/features/training/SparringSetupForm.tsx`): lo usan las tres
  pantallas desde las que se abre una partida contra el motor —Sparring, la
  lista de re-jugar y el visor—, con el mismo nombre para la misma acción en
  todas. Antes vivía dentro de `SparringPage`.
- **La frase de lo que costó un error se escribe en un solo sitio**
  (`lib/format.ts::formatOwnWinPercentLossSentence`), que comparten el puzzle
  resuelto y la lista de re-jugar: estaba duplicada, con su resta incluida, en
  dos pantallas donde el mismo dato podía acabar diciéndose de dos maneras.
- **Tres filas nuevas del inventario de RNF-11** (la 101 a la 103), abiertas
  por esta pantalla y **abiertas todavía** —dos piden un campo más en la API y
  la tercera es la ayuda de la cabecera del visor—, más las filas 92 y 95
  ampliadas y ocho arreglos cerrados en el mismo commit; ver
  [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md).
- Contrato de la API: ruta y esquemas **nuevos** (`/training/replays`,
  `ReplayPosition`) y dos campos nuevos en `SparringGameOut`
  (`origin_game_id`, `origin_ply`) más un `origin` opcional en
  `SparringGameCreate`, todos añadidos: nada de lo que ya consumía la API se
  rompe. `openapi.json` y los tipos de `packages/shared-types` regenerados con
  `make types`.

## [0.4.3] - 2026-09-21

El repertorio deja de ser un informe y se puede jugar: **drill de aperturas**
(**RF-4.2**), que convierte los puntos donde se abandona la teoría y las
aperturas que peor van en líneas para repetir desde la jugada 1, con el
servidor contestando por el rival. Cierra el **tercer ítem de la fase 3** del
roadmap, que **sigue abierta** con "re-juega desde el error" (RF-4.4), el plan
semanal (RF-4.5) y la capa de ocupación en la pantalla de entrenamiento, así
que sube el **patch y no el minor**, mismo criterio que en `0.2.1` a `0.2.5`,
`0.4.1` y `0.4.2`. **No hay alcance nuevo**: RF-4.2 es alcance congelado de
v1.0 desde el corte del **2026-09-05**, no se ha añadido ningún RF ni RNF y
nada baja a Post 1.0 ni sube a 1.0.

### Añadido

- **Drill de aperturas: repetir jugando las líneas donde peor se rinde**
  (RF-4.2), en la pestaña "Aperturas" de Entrenamiento (`/training/drills`):
  un botón que genera la baraja desde lo que el repertorio ya sabe, la cola de
  lo que toca hoy y el tablero donde se repite la línea. En la API, tres
  endpoints bajo `/training/drills` —generar, la cola y jugar una jugada— con
  `apps/api/lucia_api/services/drills.py`; las reglas puras de una línea en
  `lucia_core.drills`, sin base de datos, sin motor y sin red, para poder
  probarse solas (RNF-8). De dónde sale el material y qué se entiende por
  "peor" está razonado en
  [ADR-0019](docs/adr/0019-el-drill-de-aperturas-se-construye-sobre-las-salidas-de-la-teoria.md),
  y las reglas que el texto del requerimiento no fijaba, en la nota "Con qué
  reglas se cumplió RF-4.2" de
  [docs/02-requerimientos.md](docs/02-requerimientos.md).
  - **Un drill es una línea y no una posición.** Se recorre desde la jugada 1
    jugando el bando propio y termina siempre en una jugada propia. Es la
    diferencia con los puzzles de RF-4.1: una apertura no se olvida en una
    posición, se olvida como camino —se llega a la jugada 6 por inercia y se
    hace la de siempre—, así que empezar justo antes de la salida regalaría la
    parte que no se recuerda.
  - **Dos barajas del mismo material**, y lo único que las separa es por qué
    entra cada línea: las **salidas de la teoría** (RF-3.6) y las **peores
    aperturas** (RF-3.2). Las dos se construyen igual —el camino propio de la
    partida hasta el punto donde se abandonó el libro, más la jugada que ahí
    juegan los maestros—, así que una apertura que va mal pero en la que nunca
    se abandona la teoría **no da drill**: no hay ninguna jugada que se pueda
    enseñar como la que había que hacer, y ese problema es el de los puzzles
    de RF-4.1.
  - **"Peor" se mide en puntos perdidos, no con un corte por porcentaje**:
    `partidas * (50 - %) / 100`, y la baraja se ordena por ese daño. Quince
    partidas al 40 % cuestan punto y medio y tres al 20 % cuestan nueve
    décimas: un corte absoluto deja fuera precisamente el agujero grande, que
    sangra despacio y muchas veces. Medido sobre las **326 partidas reales**
    del autor, el corte por porcentaje daba 3 líneas y ordenar por daño da 10.
    El único umbral que queda es de hábito, **3 partidas**
    (`MIN_GAMES_TO_DRILL`), la misma pregunta que ya se hace RF-3.6.
  - **Generar no sale a la red**, y por eso la baraja crece con el
    repertorio: usa solo lo que la caché del Opening Explorer ya sepa
    ([ADR-0010](docs/adr/0010-repertorio-con-red-y-cacheado.md)), así que
    mientras queden posiciones por consultar hay drills que todavía no
    existen. **La pantalla lo avisa** y manda a refrescar el repertorio (RF-3.6)
    en vez de dejar creer que no hay material. Por lo mismo, la línea termina
    en la jugada de maestros que había que hacer y no continúa por la teoría
    que sigue: limitación conocida y escrita.
  - **La línea no viaja al navegador mientras el drill está abierto**: es la
    respuesta y además diría qué va a contestar el rival. El servidor
    comprueba jugada a jugada, contesta por el otro bando y solo al cerrarlo
    manda la línea entera, la misma regla que en los puzzles de RF-4.1; y
    tampoco hay barra de evaluación, por la misma razón. Fallar no cierra el
    drill ni enseña la jugada buena; rendirse sí, como fallado.
  - **El servidor no guarda progreso**: por dónde va la línea lo lleva la
    pantalla (`ply`), como el número de intento de un puzzle. Un drill se
    repite entero o no se repite.
  - **Tabla `opening_drills`** (migración `c7b2e9f05a31`), que nace vacía y
    guarda la línea y su motivo **congelados**, sin clave foránea a la partida
    de la que salió, por lo mismo que el puzzle
    ([ADR-0017](docs/adr/0017-puzzle-persistido-con-su-solucion-congelada.md)):
    lleva encima un historial de repasos que no se puede regenerar. Su clave
    única es `(bando, línea)` y no la partida de origen —al revés que en los
    puzzles—, porque la gracia de un drill es que la misma línea se repite en
    muchas partidas; eso es además lo que hace idempotente el generar.
  - **No hay un segundo algoritmo de repaso**: un drill se reparte y vuelve
    con el mismo SM-2 de `lucia_core.training` que los puzzles y con las
    mismas tres notas —rendirse es fallar, recorrer la línea limpia es acertar
    y tropezar por el camino queda en medio—.

### Cambiado

- **El ítem del roadmap que juntaba RF-4.2 y RF-4.4 se parte en dos**, y solo
  el primero queda marcado: "re-juega desde el error" (**RF-4.4**) pasa a ser
  ítem propio de la fase 3, todavía abierto. Marcar la casilla compartida
  habría dado por cerrado algo que no lo está; es el mismo criterio con el que
  en `0.2.4` lo que faltaba de RF-6.5 se separó de los extras del tablero.
  RF-4.4 sigue siendo alcance congelado de v1.0 y sigue en esta fase: lo único
  que cambia es que ya no comparte casilla. Ver
  [docs/05-roadmap.md](docs/05-roadmap.md).
- **`lucia_core.training` deja de ser "las reglas de los puzzles" para ser
  "las reglas del repaso"**, con dos servicios que lo usan. `next_review` lo
  comparten puzzles y drills; `equivalent_solutions` sigue siendo solo de los
  puzzles, porque en una línea de apertura la respuesta es una y la dicen los
  maestros.
- **`Departure` (RF-3.6) lleva dos campos nuevos** —`master_moves_uci` y
  `preceding_moves_uci`— que la comparación de repertorio no mira: son el
  material del drill, y el camino y la jugada en UCI solo se pueden componer
  mientras se recorre la partida. Recorrerla otra vez desde el drill sería
  hacer dos veces el mismo trabajo, con el riesgo de que las dos pantallas no
  coincidieran.
- Cuatro filas nuevas del inventario de **RNF-11** (la 97 a la 100), abiertas
  por esta pantalla y **abiertas todavía**, todas de lo que la separa de la de
  puzzles, que es su gemela; ver
  [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md).
- Contrato de la API: esquemas y rutas **nuevos** (`/training/drills...`), sin
  tocar ninguno de los existentes, así que nada de lo que ya la consumía se
  rompe. `openapi.json` y los tipos de `packages/shared-types` regenerados con
  `make types`.

## [0.4.2] - 2026-09-21

El motor deja de ser solo un oráculo y se sienta enfrente: **sparring contra
motor con fuerza calibrada** (**RF-4.3**), Stockfish conteniéndose con
`UCI_LimitStrength`/`UCI_Elo` o Lc0 jugando con una red Maia. Cierra el
**segundo ítem de la fase 3** del roadmap, que **sigue abierta** con los otros
dos —drill de aperturas y "re-juega desde el error" (RF-4.2, RF-4.4) y plan
semanal (RF-4.5)— más la capa de ocupación en la pantalla de entrenamiento, así
que sube el **patch y no el minor**, mismo criterio que en `0.2.1` a `0.2.5` y
en `0.4.1`. **No hay alcance nuevo**: RF-4.3 es alcance congelado de v1.0 desde
el corte del **2026-09-05**, no se ha añadido ningún RF ni RNF y nada baja a
Post 1.0 ni sube a 1.0.

### Añadido

- **Sparring contra el motor con la fuerza calibrada** (RF-4.3): la pantalla
  `/training/sparring` para elegir rival y empezar y
  `/training/sparring/$sparringGameId` para jugar y retomar, con
  sub-navegación nueva dentro de Entrenamiento. En la API, cinco endpoints
  bajo `/sparring` —crear partida, listarlas, ver una, jugar y abandonar— con
  `apps/api/lucia_api/services/sparring.py`, y las reglas puras de una partida
  —rehacerla desde sus jugadas, saber si acabó y por qué, y escribirla en
  PGN— en `lucia_core.sparring`, sin base de datos y sin motor, para poder
  probarse solas (RNF-8).
  - **`EngineBridge.play(board)`**: le pide al motor la jugada que **haría**,
    no la que recomienda. Es la otra forma de hablar UCI y la que faltaba para
    jugar contra él: `analyze` siempre contesta lo mejor que hay, mientras que
    `play` respeta lo que se le haya pedido de fuerza, que es lo que convierte
    al motor en rival y no en oráculo. La nota técnica de **RF-11** señalaba
    esta carencia como compartida por RF-4.3, RF-4.4 y RF-11: **queda resuelta
    una vez para los tres**. Como en `evaluate_positions`, no se le pregunta
    por una posición ya terminada —no hay jugada que devolver y Lc0 se queda
    esperando para siempre—.
  - **Dos rivales que no se calibran igual, y la pantalla lo dice.** Stockfish
    busca igual de bien y se contiene: acepta un Elo entre **1320 y 3190**
    (`STOCKFISH_ELO_RANGE`, los topes de Stockfish 17) y piensa un segundo por
    jugada, porque lo que lo frena es el límite de fuerza y no el reloj. Lc0
    con una red Maia **no se contiene**: está entrenada para predecir la jugada
    de una persona de ~1500, así que sus errores son los que comete la gente y
    no los de un motor mutilado; su fuerza es la de la red cargada y no un
    número que se le pueda pedir, por eso `engine_elo` solo existe con
    Stockfish y el formulario esconde el deslizador en vez de enseñar uno
    muerto. Maia se juega a **un solo nodo**: con más, la búsqueda empieza a
    corregir a la red y se pierde justo lo que la hace humana. Medido en el
    portátil de desarrollo (i7 + GTX 1060): ~1,15 s por jugada Stockfish
    calibrado y ~0,08 s Maia, que además abre con el Giuoco Piano.
  - **Ajuste nuevo `MAIA_WEIGHTS`** (`maia-1500.pb.gz`, la que descarga
    `make engines`), separado de la red del análisis: cambiarlo por otra de la
    familia (1100 a 1900) es cambiar la fuerza del rival de Lc0. No puede ser
    la misma red que analiza, porque Maia es buena imitando y mala como fuente
    de verdad, que es lo contrario de lo que se le pide a un analizador.
  - **Tabla `sparring_games`** (migración `f3d9a1c47b58`), que nace vacía y
    guarda la partida como **posición de partida más jugadas en UCI**: la
    posición actual, el PGN y el final se derivan al servir, así que no hay dos
    versiones de la misma partida que puedan discrepar. `result` es la única
    marca de que terminó (`null` mientras se juega) y `termination` dice por
    qué —mate, ahogado, material insuficiente, cincuenta jugadas, repetición o
    abandono—, porque "0-1" no distingue un mate de un abandono y en un
    entrenamiento eso es justo lo que se quiere saber.
  - **Aquí el servidor es el rival y el árbitro**, al revés que en el tablero
    de análisis, donde quien sabe de reglas es chess.js y la API solo custodia
    el árbol ([ADR-0013](docs/adr/0013-analisis-de-partida-o-de-tablero.md)):
    para contestar hay que saber qué posición hay, así que la jugada de la
    persona se valida en el servidor y la respuesta del motor vuelve en la
    misma petición, porque son un solo turno. Y la partida **no cuenta** en
    estadísticas ni en detección de patrones (RF-3), la misma frontera que un
    tablero sin publicar (RF-6.5): para estudiarla se abre como tablero desde
    su PGN (RF-6.6) y se analiza desde ahí (RF-6.9). Razonado en
    [ADR-0018](docs/adr/0018-sparring-en-su-propia-tabla-y-el-servidor-como-arbitro.md),
    que adelanta buena parte de lo que RF-11.3 pedirá.
  - **Sin reloj y sin barra de evaluación**: una partida de entrenamiento se
    interrumpe y se retoma por su URL tal como estaba, porque el estado vive en
    la base; la barra queda fuera por lo mismo que en los puzzles de RF-4.1,
    que decir a cada jugada quién va ganando convierte la partida en un
    análisis asistido.

### Cambiado

- El **segundo ítem de la fase 3** del roadmap queda marcado y la fase se
  documenta como abierta, con lo que falta enumerado; ver
  [docs/05-roadmap.md](docs/05-roadmap.md).
- **Ese ítem citaba `RF-4.2` y no le tocaba.** El sparring es RF-4.3 y solo
  RF-4.3; RF-4.2 es el drill de aperturas, que es el ítem siguiente del propio
  roadmap y ahora lo cita junto a RF-4.4. Corregido de paso, sin mover nada de
  sitio: los dos son alcance congelado de v1.0 y siguen en la fase 3.
- **La nota de RF-11 en Post 1.0 ya no da por pendiente que el motor sepa
  jugar.** Sus dos dependencias de alcance 1.0 están entregadas —RF-6.1 el
  2026-09-18 y RF-4.3 hoy—, así que lo que le queda es solo suyo: arrancar de
  una posición con ventaja y la segunda perilla de dificultad. **Sigue fuera
  del alcance de v1.0**: que ya se pueda montar no lo mete dentro del corte del
  2026-09-05.
- Contrato de la API: esquemas y rutas **nuevos** (`/sparring/...`), sin tocar
  ninguno de los existentes, así que nada de lo que ya la consumía se rompe.
  `openapi.json` y los tipos de `packages/shared-types` regenerados con
  `make types`.

## [0.4.1] - 2026-09-19

LUCIA deja de solo contar lo que se hizo mal y pasa a preguntarlo: la pantalla
de **Entrenamiento** convierte los errores propios del análisis en puzzles y
los devuelve con repetición espaciada, aceptando cualquier jugada tan buena
como la del motor (**RF-4.1** con **RF-10.3**). Cierra el **primer ítem de la
fase 3** del roadmap, que **sigue abierta** con los otros tres —sparring
(RF-4.2, RF-4.3), drill de aperturas y "re-juega desde el error" (RF-4.4) y
plan semanal (RF-4.5)— más la capa de ocupación en esta tercera pantalla, así
que sube el **patch y no el minor**, mismo criterio que en `0.2.1` a `0.2.5`.
**No hay alcance nuevo**: RF-4.1 y RF-10.3 son alcance congelado de v1.0 desde
el corte del **2026-09-05**, no se ha añadido ningún RF ni RNF y nada baja a
Post 1.0 ni sube a 1.0.

### Añadido

- **Puzzles desde los errores propios, con repetición espaciada** (RF-4.1), en
  la pantalla de Entrenamiento (`apps/web/src/features/training/`): un botón
  que genera la baraja desde lo ya analizado, la cola de lo que toca hoy y el
  tablero donde se responde. En la API, `POST /training/puzzles` (generar),
  `GET /training/puzzles` (la cola) y `POST /training/puzzles/{id}/answer`
  (responder), con `apps/api/lucia_api/services/training.py`; las dos reglas
  puras —SM-2 y la equivalencia de jugadas— en `lucia_core.training`, sin base
  de datos y sin reloj, para poder probarse solas (RNF-8).
  - **Dan puzzle los errores propios graves** —`mistake`, `blunder` y
    `missed_win` (`PUZZLE_CLASSIFICATIONS`)— del análisis terminado más
    reciente de cada partida, el mismo criterio con el que se cuentan las
    estadísticas. Las imprecisiones no: una jugada que pierde menos de diez
    puntos de probabilidad de victoria no tiene respuesta que encontrar, y como
    puzzle solo enseñaría a adivinar la preferencia del motor. Los del rival
    tampoco: su error dice cómo juega el otro.
  - **SM-2, el algoritmo de SuperMemo que usa Anki**, con tres resultados:
    fallar (o rendirse), acertar tras más de un intento y acertar a la primera.
    Fallar reinicia los aciertos seguidos pero **no** la facilidad, que se
    arrastra, de modo que un puzzle que se falla una y otra vez acaba volviendo
    casi a diario; el próximo vencimiento se cuenta desde el repaso y no desde
    el anterior, para que repasar con retraso no encadene retrasos.
  - **Generar es un acto explícito y es idempotente**, con clave
    `(partida, jugada)`: quien entrena decide cuándo renovar su baraja, volver
    a pulsar solo añade lo nuevo y analizar una tanda de partidas no le cambia
    la cola de repaso por sorpresa.
  - **La comprobación es del servidor y un puzzle abierto no viaja con nada
    que lo resuelva**: ni la solución, ni la jugada que se hizo en la partida,
    ni la clasificación, ni las probabilidades. Saber que aquello fue un
    blunder de treinta puntos ya es media respuesta; todo eso llega al
    cerrarlo, que es cuando la pantalla lo enseña. Por lo mismo, es la única
    pantalla con tablero **sin barra de evaluación**.
  - **Tabla `puzzles`** (migración `e1a7c93d40b2`), que nace vacía y no enlaza
    a `analyzed_moves`: cada fila se basta a sí misma —posición, jugada que se
    hizo, soluciones aceptadas, coste del error y estado de SM-2— porque lleva
    encima el historial de repasos, el único dato de LUCIA que no se puede
    regenerar volviendo a pasar el motor. Reanalizar una partida no la toca:
    crea un análisis nuevo, con sus propias `analyzed_moves`, y el anterior
    deja de ser el vigente, así que un puzzle colgado de aquella fila hablaría
    de un análisis que ya no se enseña. Razonado en
    [ADR-0017](docs/adr/0017-puzzle-persistido-con-su-solucion-congelada.md),
    que es la decisión contraria a la de los patrones
    ([ADR-0008](docs/adr/0008-patrones-deducidos-al-leer.md)) y explica dónde
    está la línea.

- **Se acepta como buena cualquier jugada equivalente** (RF-10.3), y no solo
  la favorita del motor: toda la que no pierda más de **2 puntos de
  probabilidad de victoria** respecto a ella
  (`EQUIVALENT_MOVE_MAX_WIN_PERCENT_LOSS`), que es el mismo margen con el que
  RF-2.2 llama "excelente" a una jugada — lo que el análisis no considera un
  error tampoco puede serlo en un puzzle sacado de ese mismo análisis. Las
  candidatas salen de las alternativas persistidas por RF-10.1 o de lo que se
  rescate de `position_cache`; si no hay ninguna queda la `best_move_uci`
  sola, que es peor puzzle pero no uno falso, y un error del que no se pueda
  afirmar ninguna respuesta no genera puzzle. **Con esto RF-10 queda entregado
  entero.**

### Cambiado

- El primer ítem de la **fase 3** del roadmap queda marcado y la fase se
  documenta como abierta, con lo que falta enumerado; ver
  [docs/05-roadmap.md](docs/05-roadmap.md). El bloque "Estado" del `README.md`
  pasa de "fases 0 a 2 cerradas" a decir también qué hay ya de la fase 3.
- Contrato de la API: esquemas y rutas **nuevos** (`/training/...`), sin tocar
  ninguno de los existentes, así que nada de lo que ya la consumía se rompe.
  `openapi.json` y los tipos de `packages/shared-types` regenerados con
  `make types`.

## [0.4.0] - 2026-09-19

**Cierra el apéndice de la fase 2 del roadmap**, los siete puntos que destapó
auditar el mapa, la documentación y el código de la fase entera después del
corte de `0.3.0`, el mismo día. Sube el minor y no el patch por tres motivos
que no caben en un parche: entrega una prestación que faltaba (**RF-2.6**, la
probabilidad W/D/L del motor), cambia el contrato de la API —`EngineLineOut` y
`MoveComparisonOut` ganan campos, todos **opcionales**, así que nada de lo que
ya consumía la API se rompe— y cambia el esquema (migración `3208b0d0f467`) y
el comportamiento por defecto de Lc0 para quien no tenga `.env`. **No hay
alcance nuevo**: RF-2.6 era alcance congelado entregado a medias y RF-3.8 solo
cambia de fase; nada baja a Post 1.0 ni sube a 1.0.

### Añadido

- **La probabilidad W/D/L del motor (RF-2.6)**, que era la mitad del
  requerimiento que nunca se había entregado: hasta ahora la comparación entre
  motores solo usaba la probabilidad de victoria derivada del centipeón con el
  modelo de Lichess, que es una fórmula común a los dos y por tanto no dice en
  qué discrepan. Ahora se le pide a cada motor la suya con `UCI_ShowWDL` —por
  la misma vía filtrada que `Threads` y `Hash`, así que un motor que no la
  declare sigue funcionando sin ella— y se enseña con `WdlBar` en la lista de
  líneas del motor y en el panel de comparación. **Sin migración**: viaja en el
  JSON que ya guardaba las líneas, en una clave opcional, así que la caché y
  los análisis anteriores se siguen leyendo igual. Lo destapó la auditoría de
  cierre de la fase 2; ver su apéndice en
  [docs/05-roadmap.md](docs/05-roadmap.md).

### Cambiado

- **RF-3.8 (análisis de rivales recurrentes) pasa a la fase 4.** Era alcance
  congelado de v1.0 desde el corte del 2026-09-05 y se había quedado sin ítem
  en ninguna fase: el mapa lo daba por "pendiente (fase 2)" mientras esa fase
  se cerraba sin él. Sigue dentro del alcance de 1.0 —no baja a Post 1.0— y no
  bloquea la fase 3, porque lo que necesita para montarse ya está entregado.

### Corregido

- **Las cuatro incoherencias de interfaz que quedaban abiertas** (RNF-11, filas
  65, 67, 68 y 70): la cabecera de Partidas ya no reparte el título y dos
  formularios en la misma fila; el listado y el visor dicen de dónde vino cada
  partida con `GameSourceBadge`, para que los huecos de un PGN importado se
  expliquen; y "Exportar PGN anotado" está siempre —deshabilitado y con el
  motivo cuando no hay análisis— y su descarga pasa por el cliente, así que un
  409 o un 404 salen en un `ErrorBox` en vez de guardarse como si fueran el
  archivo. **El inventario de `docs/07-coherencia-ui.md` queda vacío por primera
  vez.**
- **ADR-0008 citaba un endpoint que nunca existió** (`GET /stats/{username}`;
  el real es `GET /stats?username=…`), en su decisión y en su primera
  consecuencia. Corregido en el propio archivo, con una nota fechada que
  explica el cambio: la norma de no editar un ADR publicado protege el registro
  de las decisiones, y la de ADR-0008 no cambia. Se barrieron los dieciséis
  ADR cruzando endpoints, rutas e identificadores contra el código: era el
  único error de hecho.
- **`analyzed_moves` tenía dos claves foráneas sobre `analysis_id`**, una
  `NO ACTION` y otra `CASCADE`: la migración `c8f3a2b91e47` añadió la segunda
  sin quitar la primera, porque dentro de un `batch_alter_table` alembic
  reconstruye la tabla a partir de lo que refleja de la base. No era un fallo
  vivo —el borrado en cascada funcionaba—, pero ensuciaba cada `alembic check`
  y lo habría arrastrado la siguiente migración que tocara la tabla. La nueva
  migración `3208b0d0f467` reconstruye la tabla desde una definición dada
  (`copy_from`) y la deja con una sola.
- **Los valores por defecto de Lc0 eran la peor combinación posible.** El
  código traía la red transformer (`default.pb.gz`, que OpenCL rechaza y en CPU
  da 2,5 nodos/s) y el backend `blas`, mientras que `.env.example` recomendaba
  otra cosa: quien clonara el repo sin copiar el `.env` tenía un Lc0
  inservible. Ahora la red por defecto es la T74 convolucional —la que el
  propio repo llamaba "la recomendada"— y el backend va **vacío**, para que lo
  elija Lc0 entre los que se le compilaron. Medido con la T74, 3.000 nodos: en
  vacío 1,23 s, con `opencl` 1,12 s, con `blas` 14,88 s. De paso se corrige la
  advertencia del código, que atribuía al backend ("~20x más lento sin
  especificarlo") lo que en realidad costaba la red.

### Eliminado

- **`polars` y `zustand`, declaradas como dependencia y nunca importadas.**
  polars estaba en `packages/core` desde el primer día porque
  [ADR-0005](docs/adr/0005-sqlite-local-first.md) daba por hecho que las
  agregaciones se harían con él; todo RF-3 acabó escrito en SQL. Zustand
  estaba en `apps/web` para un estado global que nunca hizo falta. Fuera de
  los manifiestos y de los dos lockfiles. Invertir lo que decía ADR-0005
  llevó ADR propio:
  [ADR-0016](docs/adr/0016-agregaciones-en-sql-sin-polars.md).

## [0.3.0] - 2026-09-19

**Cierra la fase 2 del roadmap**, y por eso sube el minor y no el patch: la
capa de ocupación del tablero era su último ítem pendiente. Con ella entregada
quedan cubiertos los siete puntos P1 de **RF-7**, congelados en el alcance de
v1.0 desde el corte del **2026-09-05**. No hay requerimientos nuevos en esta
versión ni cambio de alcance: RF-7.8 y RF-7.9 son P2 y siguen donde estaban,
en la fase 4.

### Añadido

- **Capa de ocupación del tablero (RF-7.1 a RF-7.7)**, activable con la tecla
  `O` o desde su panel, sin salir de lo que se esté haciendo, en el visor
  (RF-5) y en el tablero de análisis (RF-6); en el entrenamiento (RF-4) se
  enchufará cuando esa pantalla exista, en la fase 3. Vive entera en
  `apps/web/src/components/board/`: `occupancy.ts` (el cálculo, con pruebas
  propias en `__tests__/occupancy.test.ts`), `useOccupancy.ts` (el estado y el
  atajo), `OccupancyLayer.tsx` (lo que se pinta sobre el tablero) y
  `OccupancyPanel.tsx` (el control, la inspección y la leyenda). Cubre:
  - Sub-modo **mapa de calor** con el balance de atacantes directos por
    casilla e intensidad proporcional (RF-7.1) y sub-modo **cobertura
    directa** del bando con el turno, con conmutador al otro bando, filtrado
    al señalar una pieza y fijado al hacer clic (RF-7.2).
  - **Inspección por casilla** con atacantes y defensores de los dos bandos
    ordenados por valor de pieza (RF-7.3) y marcado de **piezas colgadas**
    (RF-7.4).
  - **Rayos X dibujados aparte** y nunca sumados al balance del mapa de calor
    (RF-7.5) y **piezas clavadas** contando como atacante pero marcadas
    distinto (RF-7.6).
  - Las **reglas de conteo** de RF-7.7: el rey cuenta como atacante, los
    peones cuentan por sus capturas en diagonal y no por su avance, y la
    casilla de captura al paso cuenta como atacada por el peón que podría
    capturar ahí.

  Las decisiones que el texto del requerimiento no fijaba están razonadas en
  la nota "Cómo se cumplieron los siete puntos P1" de
  [docs/02-requerimientos.md](docs/02-requerimientos.md) y en la entrada del
  roadmap. En resumen: los alcances se generan aquí y no con `attackers()` de
  chess.js —que solo devuelve casillas de origen y no puede dar la clavada de
  los dos bandos, porque solo calcula las jugadas legales del que tiene el
  turno—, la casilla bajo el puntero se mide por geometría sobre el rectángulo
  del tablero en vez de preguntársela a chessground, y los conectores se
  limitan a la pieza señalada o fijada. **No hay ADR nuevo**: es una capa de
  lectura sobre la posición que ya está en pantalla, sin endpoint, sin esquema
  y sin motor, así que no hay decisión de arquitectura que registrar.

### Cambiado

- Tres filas nuevas del inventario de **RNF-11** (la 88, la 89 y la 90),
  abiertas por esta pantalla y cerradas el mismo día; ver
  [docs/07-coherencia-ui.md](docs/07-coherencia-ui.md).

## [0.2.5] - 2026-09-18

Un tablero de análisis puede ser una partida que se jugó de verdad —una OTB
anotada a mano, una casual sin PGN— y ahora **marcarlo como "partida propia"
lo publica en el historial como una fila de `games`**: desde ahí cuenta en el
marcador, en las aperturas, en las fases, en los patrones y en los filtros de
Partidas sin que ninguna consulta de RF-3 cambie. Con esto queda cerrado
**RF-6** entero. Por el camino salió a la luz que **las claves foráneas de
sqlite llevaban apagadas desde el principio**, así que ningún `ON DELETE` del
esquema se estaba ejecutando: eso va aquí, en Corregido. No cierra la fase 2,
que sigue abierta con la capa de ocupación (RF-7.1 a 7.7), así que sube el
patch y no el minor — mismo criterio que en `0.2.1`, `0.2.2`, `0.2.3` y
`0.2.4`.

### Añadido

- **Tableros marcados como "partida propia" contando en estadísticas y
  patrones** (lo que faltaba de RF-6.5), con
  `apps/api/lucia_api/services/own_games.py`,
  `PUT /boards/{id}/own-game` y `DELETE /boards/{id}/own-game`, y el panel
  `apps/web/src/features/board/OwnGamePanel.tsx`. Razonado en
  [ADR-0014](docs/adr/0014-tablero-propio-publicado-como-partida.md); las
  reglas que el texto del requerimiento no fija están en la nota "Con qué
  reglas se cumplió RF-6.5" de
  [docs/02-requerimientos.md](docs/02-requerimientos.md). En resumen:
  - **Se piden cuatro datos y ninguno más** —de qué color se jugó, contra
    quién, cómo acabó ("Gané / Tablas / Perdí", no "1-0") y qué día—, que es
    lo que las agregaciones de RF-3 necesitan para contar la partida sin
    inventar nada. Rating, control de tiempo y "de competición" se quedan en
    el mismo hueco que ya deja la importación de PGN manual (RF-1.5), porque
    un tablero tampoco los sabe, y la pantalla lo dice antes de pulsar. La
    apertura se deduce de las jugadas.
  - **Publicar en `games` en vez de enseñar a cada consulta qué es un
    tablero**: las agregaciones de RF-3 leen columnas de `games` que un
    tablero no tiene, y tocarlas todas habría multiplicado por dos cada
    consulta del dashboard.
  - **El análisis del tablero cuenta mientras siga siendo el de estas
    jugadas**: estando publicado lleva `game_id` además de `board_id` y entra
    en el dashboard por `latest_analysis_ids`; en cuanto el tablero se edita
    se desenlaza, hasta que se vuelva a analizar. Es la misma regla que ya
    avisaba en pantalla (`matchAnalyzedLine`), aplicada a lo que se cuenta.
  - **Guardar un tablero publicado exige mandar su PGN**, por la misma razón
    que en RF-6.7 y RF-6.9: quien recorre el árbol es chess.js y no la API.
    Sin él la partida del historial se quedaría atrasada en silencio.
  - **Deshacer y rehacer (RF-6.8) no lo piden otra vez**: cada versión del
    historial guarda su propio PGN (columna `board_versions.pgn`, migración
    `d4b7e0c25a19`), así que el servidor pone al día la partida publicada en
    la misma petición y la pantalla no tiene que volver a publicar el tablero.
    Las versiones anteriores a la columna quedan con el PGN en nulo: deshacer
    hasta una de ellas desenlaza el análisis —deja de contar en estadísticas—
    hasta el siguiente guardado, que es lo que hacía todo el historial antes.

### Cambiado

- **La marca de "partida propia" es el enlace a la partida publicada**
  (`boards.own_game_id`) y ya no un booleano aparte (`boards.is_own_game`),
  que podría contradecir a la fila publicada y hacer que el listado dijera una
  cosa y el dashboard otra. Migración `a71c40f5d3e8`: las marcas anteriores se
  pierden, porque no traían los cuatro datos que ahora hacen falta.
- La regla de [ADR-0013](docs/adr/0013-analisis-de-partida-o-de-tablero.md)
  —un `Analysis` cuelga de `game_id` **o** de `board_id`, nunca de los dos—
  pasa a ser "al menos uno": el análisis de un tablero publicado lleva los dos.
  Recogido en [ADR-0014](docs/adr/0014-tablero-propio-publicado-como-partida.md).
- Con RF-6.5 cerrado queda cerrado **RF-6** entero (tablero de análisis,
  RF-6.1 a RF-6.9) y, con él, el ítem correspondiente del roadmap de la fase 2.
- **`make test` corre ya las dos mitades del monorepo**, pytest y vitest.
  Corría solo Python, así que las 116 pruebas de `apps/web` había que acordarse
  de lanzarlas aparte y era fácil comitear con alguna rota.
- **`make lint` comprueba además los tipos del front** (`tsc --noEmit`, por
  `pnpm typecheck`). El script existía desde el principio pero no lo lanzaba
  ningún comando: un error de tipos no salía hasta construir el front.
- **Las pruebas de la API usan `httpx2`** y no `httpx`: es el cliente que pide
  el `TestClient` de starlette desde la 1.6, y con httpx a secas avisaba en
  cada corrida. Solo es dependencia de desarrollo; los clientes de chess.com y
  de lichess siguen con httpx. BSD-3-Clause, compatible con GPL-3.0.
- **Silenciados dos avisos de obsolescencia de terceros** que Python 3.14
  levanta sobre `chess.engine` y `starlette.testclient`, los dos ya en su
  última versión publicada. Se silencian por módulo y no por categoría, para
  que un aviso propio siga viéndose (`filterwarnings` en `pyproject.toml`).

### Corregido

- **Las claves foráneas de sqlite estaban apagadas en toda la aplicación.**
  Vienen así por conexión, y nadie las encendía, de modo que **ningún
  `ON DELETE` del esquema se ejecutaba**: borrar un tablero dejaba en la base
  sus análisis (`analyses.board_id`, [ADR-0013](docs/adr/0013-analisis-de-partida-o-de-tablero.md))
  y sus versiones (`board_versions.board_id`, [ADR-0012](docs/adr/0012-historial-de-tablero-lineal-y-persistido.md))
  apuntando a una fila que ya no existe, justo lo contrario de lo que esos dos
  ADR dan por hecho. Era corrupción silenciosa: no fallaba nada, solo quedaba
  basura. Ahora toda conexión pasa por
  `apps/api/lucia_api/db/base.py::create_db_engine`, que emite
  `PRAGMA foreign_keys=ON`. Las migraciones son la excepción a propósito y
  siguen con el pragma apagado, porque alembic recrea la tabla entera para
  cambiarla en sqlite (`batch_alter_table`) y con las claves encendidas ese
  renombrado se lleva por delante lo que apunta a ella.
- **`analyzed_moves.analysis_id` no tenía `ON DELETE CASCADE`** (migración
  `c8f3a2b91e47`). La limpieza la hacía solo la relación de SQLAlchemy, que
  basta cuando el análisis se borra desde el ORM pero no cuando lo borra la
  propia base: borrar un tablero se lleva sus `analyses` por la clave foránea
  sin cargarlos. Con el pragma encendido eso pasó de dejar jugadas huérfanas a
  fallar el borrado; con la cascada, se van con su análisis.

## [0.2.4] - 2026-09-18

El tablero de análisis deja de ser una isla: una partida importada se abre
como tablero con un clic, un PGN ajeno entra con sus variantes y comentarios,
el deshacer sobrevive a recargar la pantalla porque vive en la base, y el
mismo worker que analiza partidas analiza ahora la línea principal de un
tablero (RF-6.6 a RF-6.9). Y con el **editor de posición pieza a pieza** queda
completo RF-6.1: las cuatro formas de empezar un tablero —posición inicial,
FEN, PGN pegado y editor—. Con eso se cierra el ítem del roadmap "Tablero de
análisis, extras (RF-6.6 a 6.9) y el editor de posición que faltaba de
RF-6.1", pero **no la fase 2**: siguen abiertos que un tablero marcado como
"partida propia" cuente en estadísticas (lo que falta de RF-6.5) y la capa de
ocupación (RF-7.1 a 7.7). Por eso sube el patch y no el minor, mismo criterio
que en `0.2.1`, `0.2.2` y `0.2.3`.

### Añadido

- **Abrir una partida importada como tablero de análisis** (RF-6.6), copia
  desacoplada que también cubre "explorar variantes desde el visor" de
  RF-5.2. Se prefiere el PGN anotado de RF-5.5 cuando hay análisis terminado
  y el crudo cuando no, y la copia nunca nace marcada como "partida propia"
  (RF-6.5): la original ya cuenta en estadísticas y contaría dos veces.
- **Importar el tablero como PGN con variantes y comentarios** (RF-6.7), con
  `fromPgn` en `apps/web/src/features/board/tree.ts` —lector propio, porque
  `loadPgn` de chess.js descarta las variantes— y un `root_fen` nuevo en
  `PUT /boards/{id}` para los PGN que arrancan de una posición dada.
  Exportar ya existía desde el núcleo de RF-6. Importar sustituye el árbol
  (avisando antes, y se puede deshacer) y renombra el tablero desde las
  cabeceras; una jugada ilegal corta su rama, se cuenta y se informa, en vez
  de tumbar el archivo entero.
- **Deshacer / rehacer persistido** (RF-6.8): tabla `board_versions` y
  `boards.current_version_id` como cursor, historial lineal podado a 50
  versiones por tablero, `POST /boards/{id}/undo` y `/redo`, botones y atajos
  (Ctrl+Z, Ctrl+Y o Ctrl+Mayús+Z) en `useUndoRedoKeys`. Solo lo que cambia el
  árbol hace historial; renombrar o marcar como propia, no. Razonado en
  [ADR-0012](docs/adr/0012-historial-de-tablero-lineal-y-persistido.md).
- **Análisis completo del tablero en background** (RF-6.9), por el mismo
  worker y en las mismas tablas que las partidas: `Analysis` cuelga de
  `game_id` **o** de `board_id`, el front manda el PGN de la línea principal
  (`toPgn`) y se guarda en `analyses.analyzed_pgn`, de modo que la pantalla
  avisa cuando el tablero cambió desde el análisis (`matchAnalyzedLine`). Se
  analiza la línea principal y no el árbol entero; para una variante concreta
  está el motor en vivo de RF-6.2. Razonado en
  [ADR-0013](docs/adr/0013-analisis-de-partida-o-de-tablero.md).
- **Editor de posición pieza a pieza** (lo último que faltaba de RF-6.1),
  `apps/web/src/features/board/PositionEditor.tsx` con la posición y su FEN en
  `features/board/position.ts` y el modo `editable` de
  `components/board/Chessboard.tsx`. El editor rellena el campo "FEN o PGN" de
  la pantalla de Tableros en vez de abrir una segunda forma de crear. La
  posición a medio montar no es un `Chess` de chess.js —es ilegal casi
  siempre—, así que el modelo es propio y chess.js entra solo al final para
  validar, con una comprobación extra (que el bando que no mueve no esté dando
  jaque) y los motivos a la vista antes de aceptar. Tres formas de colocar:
  paleta y clic, arrastrar, y teclado (rejilla de 64 botones con
  `pointer-events-none` sobre chessground, criterio C-1). Sin endpoint, tabla
  ni migración; las reglas están en la nota de RF-6.1 de
  [docs/02-requerimientos.md](docs/02-requerimientos.md).

### Cambiado

- `run_analysis` recibe el PGN a analizar en vez de un `Game`, y los análisis
  de tablero quedan fuera de estadísticas y patrones (`latest_analysis_ids`
  solo mira los que tienen `game_id`), que es lo que RF-6.5 pide por defecto.
- Dos migraciones de Alembic: `board_versions` (deshacer / rehacer) y
  `analyses` colgando también de un tablero.
- Alcance: lo que falta de **RF-6.5** —que un tablero marcado como "partida
  propia" cuente en estadísticas y patrones— pasa a ser **ítem propio de la
  fase 2** en [docs/05-roadmap.md](docs/05-roadmap.md). Sigue siendo alcance
  de 1.0 (RF-6.5 es P0 y está congelado); se separa para que no se dé por
  cerrado junto a RF-6.6 a RF-6.9.

## [0.2.3] - 2026-09-18

El dashboard deja de ser una foto del total y pasa a contar una historia: la
sección **"Cómo evolucionas"** enseña la precisión y los errores mes a mes, y
dice con palabras si el último mes va mejor o peor que los anteriores
(RF-3.7). No cierra la fase 2, que sigue abierta con dos ítems, así que sube
el patch y no el minor — mismo criterio que en `0.2.1` y `0.2.2`.

### Añadido

- **Tendencias temporales** (RF-3.7), con `GET /stats/trends` y la sección
  "Cómo evolucionas" en el dashboard: una serie mensual de precisión, otra de
  errores por tipo y una tabla mes a mes. Las reglas de lectura que el texto
  del requerimiento no fija están escritas en la nota "Con qué reglas se
  cumplió RF-3.7" de [docs/02-requerimientos.md](docs/02-requerimientos.md);
  en resumen:
  - **El tramo es el mes natural**, el mismo eje que usa "Partidas por mes"
    (RF-3.1), para que las dos series se lean juntas.
  - **Los errores van por cada cien jugadas**, no en recuento crudo: con 324
    partidas repartidas muy desigualmente por mes, contar dibujaba cuánto
    ajedrez se jugó y no cómo se jugó. El reparto por tipo usa las mismas
    reglas que RF-3.4, así que la suma de los meses coincide con la
    distribución global.
  - **Solo entran los meses con alguna partida analizada**: uno jugado pero
    sin analizar aparecería como precisión cero, que se lee como un desastre.
  - **Frase de tendencia**, comparando el último mes con hasta tres
    anteriores y ponderando por jugadas (`TREND_BASELINE_PERIODS` en
    `lucia_core.insights`, constante con nombre y no número suelto). Tres y no
    uno porque contra el mes pasado cualquier racha mala de dos semanas diría
    "estás empeorando"; ponderado porque un mes de dos partidas no pesa como
    uno de cuarenta. Dice el sentido con palabras: en precisión subir es
    mejorar, en errores es empeorar.
  - **Línea de rating superpuesta a la de precisión**, para ver si calidad y
    resultado suben juntos. Es la del **control de tiempo más jugado** y la
    pantalla dice cuál: promediar bullet con rapid convertiría un mes de mucho
    bullet en una caída de rating inventada.
  - Frase de tendencia y línea de rating van **más allá del texto literal de
    RF-3.7** ("evolución de precisión y tipo de errores en el tiempo") y se
    añadieron a petición explícita del usuario. No son requerimientos nuevos:
    la frase es otra lectura de los mismos datos del propio RF-3.7 y el rating
    por control de tiempo ya es alcance de RF-3.1. Por eso quedan recogidos en
    la nota de RF-3.7 y no en `Post 1.0 (futuro)`.

### Cambiado

- **"Cómo evolucionas" va detrás de "Por qué fallas"** en el panel de
  estadísticas (C-6): los cuatro tipos de error se estrenaban en el gráfico de
  áreas, dos secciones por encima de donde está escrita la regla que los
  define.
- **Un solo formateador para la tasa por cada cien jugadas y para el rating**
  (C-5, RNF-11): `formatPerHundredMoves` y un `formatRating` que acepta el
  `null` de la serie mensual, en `apps/web/src/lib/format.ts`, en vez del
  `.toFixed(1)` y el `?? "—"` sueltos que se repetían por pantalla.

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
