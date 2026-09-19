# 05 · Roadmap

> Las fases 0 a 4 son el camino hacia **v1.0.0**: cubren todo el alcance
> congelado en [docs/02-requerimientos.md](02-requerimientos.md). Cuando se
> marquen todas sus casillas, `versionador` propone el corte de 1.0.0. Lo que
> se plantee fuera de ese alcance congelado va bajo
> [Post 1.0](#post-10-futuro), al final, y no cuenta para ese conteo.

## Fase 0 · Cimientos ✅

- [x] Esqueleto del monorepo, documentación, requerimientos, stack.
- [x] Sub-módulos Stockfish y Lc0 añadidos; `scripts/setup-engines.sh` compila
      ambos en Fedora (Lc0 solo el target `lc0`, sin sus tests empaquetados,
      que traen un `googletest` 1.10.0 incompatible con GCC recientes).
- [x] `uv sync --all-packages --all-extras` + `pnpm install` limpios; ruff,
      pytest, tsc, eslint y `vite build` pasan en local igual que en CI.

## Fase 1 · MVP "Game Review propio" (P0) ✅

- [x] `lucia-chesscom`: descargar perfil (RF-1.1) + archivos mensuales (RF-1.2),
      parsear PGN y relojes, guardar en SQLite vía Alembic (`players`, `games`,
      `sync_state`). Sync incremental (RF-1.3) e idempotente (upsert por
      `uuid`), con backoff en 429 (RF-1.4). Probado con `respx` y en vivo
      contra la API real de chess.com. Endpoint `POST /sync` expuesto.
      RF-1.5 (importar PGN manual, P1) se cerró después, en la fase 2.
- [x] `lucia-core`: `EngineBridge` con Stockfish vía UCI (RF-2.1), MultiPV
      configurable; `evaluate_positions`/`analyze_game` recorren la partida
      ply a ply con una evaluación por posición. `classify_move` (RF-2.2:
      best/excellent/good/inaccuracy/mistake/blunder/missed_win, umbrales
      ajustables) y `accuracy` (RF-2.3: `win_percent` sobre el modelo
      `lichess` de `python-chess`, `move_accuracy`/`game_accuracy` con la
      fórmula pública de Lichess). 45 tests, varios contra Stockfish real
      (detección de mate en 1, blunder de la trampa del tonto). Sin
      dependencias nuevas. Pendiente de este bloque: Lc0 como segundo motor
      (RF-2.6), categoría "book" (necesita `openings/`), MultiPV real en la
      clasificación (RF-2.8, momentos críticos).
- [x] API: `/games` (RF-5.3: listar y filtrar por username/color/time_class/
      rated, con paginación), `/analysis` + `AnalysisWorker` (RF-2.4: cola en
      proceso con `asyncio.Queue`, un consumidor) + `WS /ws/analysis/{id}`
      (progreso en vivo, con `GET /analysis/{id}` como respaldo) +
      `position_cache` (RF-2.7: caché por FEN+motor+profundidad+MultiPV, solo
      con límite por profundidad) usando `lucia-core` como librería pura,
      `/engines/config` (RF-5.4, lectura y escritura). 19 tests nuevos,
      incluido el flujo completo POST → WebSocket → GET contra Stockfish
      real. Encontrado y corregido en el camino: un bug de aislamiento entre
      tests por compartir el `AnalysisWorker` (y su cola de asyncio) entre
      tests con distinto event loop. Los filtros por apertura, rango de fechas,
      rival y resultado llegaron el 2026-09-09 (ver su ítem en la fase 2).
- [x] Web: lista de partidas con filtros y paginación, visor con tablero
      (chessground), jugadas clasificadas, gráfico de evaluación (en
      probabilidad de victoria) y navegación con teclado; análisis en vivo con
      barra de progreso por WebSocket. Pantalla de motores con la
      configuración **editable** (RF-5.4: hilos, hash, profundidad, MultiPV;
      la ruta del binario queda en solo lectura a propósito — aceptarla por
      HTTP sería ejecución arbitraria de comandos). Tema claro/oscuro.
      Tipos TS generados desde el OpenAPI real (`make types`), con
      verificación en CI de que no se desincronizan. 10 tests de front.
      Lo que quedaba aquí de RF-5.2 —explorar variantes del motor desde el
      visor— se cerró el 2026-09-18 con "Abrir como tablero" (RF-6.6), y
      exportar PGN anotado (RF-5.5) llegó el 2026-09-17; los dos tienen su
      ítem en la fase 2.
- [x] Dashboard (RF-3.1 a 3.3): marcador y rating por control de tiempo,
      partidas por mes, rendimiento por apertura separando blancas de negras,
      y pérdida de ventaja por fase, resaltando la peor. Necesitó implementar
      `lucia_core.phases` (fase por material y desarrollo, monotónica a lo
      largo de la partida) y añadir la columna `phase` a `analyzed_moves`.
      Verificado contra 324 partidas reales. Pendiente: "eval promedio al
      salir de la apertura" (RF-3.2), que se hará con los extractores de
      patrones de fase 2.
- [x] Tablero de análisis, núcleo (RF-6.1 a 6.5): crear desde posición
      inicial, FEN o PGN pegado; mover piezas arrastrando; árbol de variantes
      con ramas, promover y borrar; guardar, listar y eliminar; autoguardado;
      análisis en vivo del motor sobre la posición actual
      (`POST /analysis/position`, con tope de profundidad porque es síncrono);
      exportación a PGN con variantes. Independiente del historial: los
      tableros no cuentan en estadísticas salvo que se marquen como partida
      propia. 17 tests del árbol de variantes. El deshacer/rehacer explícito
      que quedaba pendiente aquí llegó con RF-6.8, y el editor de posición
      pieza a pieza —la cuarta forma de arrancar que pide RF-6.1— con el ítem
      de los extras del tablero, los dos en la fase 2.

## Fase 2 · Insight (P1) ✅

> Cerrada el **2026-09-19** con la capa de ocupación del tablero, su último
> ítem pendiente. Es el corte de la versión `0.3.0` (ver
> [CHANGELOG.md](../CHANGELOG.md)); su apéndice, auditado y cerrado ese mismo
> día, es el de `0.4.0`. Quedan las fases 3 y 4 para llegar a 1.0.0.

- [x] Lc0 integrado como segundo motor (RF-2.6); vista de discrepancias
      Stockfish vs Lc0. Nunca había llegado a funcionar: `EngineBridge` le
      mandaba la opción `Hash`, que Lc0 no soporta, y abortaba la conexión —
      ahora las opciones genéricas se filtran contra las que declara cada
      motor (esto es lo que cumple RNF-9 en el núcleo: `EngineBridge` habla
      con cualquier motor UCI sin saber cuál es. Añadir un tercer motor sigue
      pidiendo dos cosas fuera del núcleo: su ruta en `.env` y su nombre en
      `ENGINE_NAMES` de `services/engines.py`). El límite se mide en nodos
      para Lc0 y en profundidad para Stockfish, porque en MCTS la profundidad
      es un promedio del árbol y pedir una concreta cuesta un número
      imprevisible de evaluaciones.
      Endpoint `GET /analysis/compare` y panel en el visor con las jugadas
      donde los motores no coinciden. **Lo que no se entregó del texto del
      RF**: la "probabilidad W/D/L" que Lc0 sabe dar. Los dos motores se
      comparan en la misma unidad —la probabilidad de victoria derivada de la
      puntuación con el modelo de Lichess, la misma de RF-2.3—, porque una
      W/D/L solo del motor que la reporta no se podría poner al lado de la de
      Stockfish. Anotado en la nota de RF-2.6 de
      [02-requerimientos.md](02-requerimientos.md); que cada motor se
      configure en sus propios términos —opciones filtradas, esfuerzo en su
      unidad y la red dentro de su identidad en la caché— quedó registrado en
      [ADR-0015](adr/0015-cada-motor-con-su-unidad-de-esfuerzo-y-sus-opciones.md).
      **Sobre el rendimiento de Lc0** (medido en un portátil con i7 y GTX
      1060). El backend y la red deciden si sirve o no:

    | Red | Backend | Velocidad |
    | --- | --- | --- |
    | grande (transformer, 313 MB) | CPU/BLAS | 2,5 nodos/s |
    | grande (transformer) | OpenCL | **no soportada** |
    | T74 convolucional (6 MB) | OpenCL | ~4.000 nodos/s |
    | T74 convolucional (6 MB) | CPU/BLAS | ~200 nodos/s |
    | T74 convolucional (6 MB) | sin especificar (Lc0 elige) | ~2.400 nodos/s |
    | Maia (1 MB) | OpenCL | ~12.500 nodos/s |

      El instalador descargaba solo la red grande, que es transformer: OpenCL
      no acepta esa arquitectura y en CPU tarda 80 s por cada 200 nodos, así
      que Lc0 era inservible. Ahora descarga también una red convolucional
      T74, que es la recomendada por defecto, y detecta el soporte de GPU al
      compilar (CUDA si hay `nvcc`, si no OpenCL, si no CPU). Con eso,
      analizar una partida de 14 jugadas a 1.600 nodos por posición baja a
      8 segundos.

      Con dos motores fuertes de verdad coinciden en la mejor jugada el 86 %
      de las veces y no hay discrepancias de valoración relevantes; el 64 %
      y las 3 discrepancias que salían antes eran un artefacto de usar la red
      Maia, que imita a un humano de ~1500 en vez de buscar la mejor jugada.

      Tres bugs encontrados solo al analizar partidas reales:
      1. El rango de validación del esfuerzo era el mismo para ambos motores
         (1.600 nodos es normal en Lc0 e imposible como profundidad).
      2. La caché de posiciones no incluía la red neuronal en su clave, así
         que al cambiar de red devolvía las evaluaciones de la anterior.
      3. **`evaluate_positions` le pedía al motor que buscara también en la
         posición final.** Si la partida acaba en jaque mate o ahogado, no
         hay jugada que devolver: Stockfish responde igual, pero Lc0 se queda
         colgado para siempre. Cualquier partida terminada en mate dejaba el
         análisis tieso. Ahora las posiciones terminales no se consultan: su
         evaluación se deduce (mate o tablas). La misma partida pasó de no
         terminar nunca a analizarse en 6 s.
- [x] Legibilidad del análisis del motor sobre el tablero (RF-6.2 completo,
      RF-5.2 en su mitad del tablero de análisis).
      La predicción del motor ya existía entera en el backend, pero llegaba a
      la pantalla casi solo como texto SAN, que exige saber leer evaluaciones
      para sacarle algo. Ahora:
      1. **Flechas de las mejores líneas** en el tablero de análisis: hasta
         tres (`MAX_ENGINE_ARROWS`), la mejor en verde sólido y las siguientes
         atenuadas, cada una etiquetada con su evaluación sobre la propia
         flecha. `Chessboard` pasó de recibir `bestMoveUci` a recibir
         `engineArrows`, y la decisión de qué pincel y qué etiqueta lleva cada
         una vive en `boardConfig.ts`, con tests.
      2. **Barra de evaluación** (`EvalBar`) en el visor y en el tablero, en
         probabilidad de victoria y no en peones, orientada como el tablero y
         con la mitad marcada. Replica el modelo de Lichess con la misma
         constante y el mismo redondeo que `lucia_core.accuracy.win_percent`,
         para que la barra en vivo y el análisis guardado no den números
         distintos de la misma posición.
      3. **Previsualización de la línea**: señalar la jugada n de una línea,
         con ratón o con el tabulador, dibuja sus n primeras jugadas en azul,
         numeradas. Obligó a quitar el `disabled` de las jugadas 2 en adelante,
         porque un botón deshabilitado no recibe ni ratón ni foco.

      **Qué cierra y qué no**, porque la casilla no cierra los dos RF enteros:

      - **RF-6.2 queda cubierto.** Pide análisis en vivo al mover a mano "con
        las mismas capacidades visuales que RF-5.2: MultiPV, flechas, barra de
        evaluación y previsualización", y las cuatro están en el tablero de
        análisis.
      - **De RF-5.2 quedaba la mitad del visor**, y no por decisión de
        interfaz: el análisis guardado solo tenía `best_move_uci` por jugada,
        así que solo se podía dibujar una flecha. Lo resolvió RF-10 el
        2026-09-08, en esta misma fase. Lo último que le faltaba —"explorar
        variantes del motor desde cualquier posición" en el visor— lo cerró
        RF-6.6 el 2026-09-18 con "Abrir como tablero", que saca la partida al
        tablero de análisis como copia desacoplada: **con eso RF-5.2 queda
        entregado entero**.
- [x] Alternativas por jugada en el análisis guardado (RF-10.1 y RF-10.2).
      Persistir las N mejores líneas de cada posición analizada, no solo
      `best_move_uci`, y usarlas en el visor. Movido al alcance de v1.0 el
      2026-09-06 porque es cambio de esquema y de flujo de análisis; hecho el
      2026-09-08. Cómo quedó:
      1. **El núcleo guarda el MultiPV entero.** `PositionEval.lines` conserva
         todas las líneas que devuelve el motor (`lucia_core.analysis`), y
         `best_move`/`pv` pasan a derivarse de la primera, que es lo que eran.
         Cada `AnalyzedMove` se lleva las de la posición **anterior** a la
         jugada: eso es "lo que podías haber jugado en su lugar".
      2. **Se persisten en `analyzed_moves.alternatives_json`** (migración
         `7a1c4e9d2b30`), con el mismo formato serializado que
         `position_cache.lines_json`. La notación SAN no se guarda: depende de
         la posición y se deriva de `fen_before` al servir.
      3. **Los análisis anteriores no hay que repetirlos**, que era el motivo
         de meter esto en 1.0: sus posiciones siguen en `position_cache` con
         todas sus líneas (RF-2.7), así que `GET /analysis/{id}` las recupera
         de ahí cuando la clave coincide exactamente —misma posición, motor,
         red, límite y MultiPV—. Comprobado sobre la base del autor: un
         análisis de 56 jugadas recuperó las tres alternativas de todas ellas
         sin gastar motor.
      4. **El visor las usa** (RF-10.2): flechas múltiples por jugada, las
         mismas que el tablero de análisis (`arrowsFromEngineLines`), y un
         panel "podías haber jugado" al pararse en una jugada, con la lista de
         líneas compartida (`components/board/EngineLineList.tsx`). Señalar o
         pulsar una jugada de una línea la dibuja sobre el tablero.

      Queda fuera RF-10.3 (usar las alternativas en los puzzles de RF-4.1),
      que es P2 y vive en la fase 3 con el resto de entrenamiento.
- [x] Coherencia de la interfaz entre pantallas (RF-5.1 y RNF-6; criterios en
      [docs/07-coherencia-ui.md](07-coherencia-ui.md)). Esta casilla es el
      trabajo de coherencia que arrancó el inventario y cerró sus 51 primeras
      filas; el inventario **no se cierra con la fase**, porque RNF-11 es un
      criterio permanente y cada cambio de `apps/web` puede abrir filas
      nuevas: al cerrar la fase 2 llevaba 90 filas, 86 cerradas y **cuatro
      abiertas** (65 y 67, de la importación de PGN; 68 y 70, de la
      exportación a PGN anotado). Quien las cuenta y las cierra es el agente
      `coherencia-ui`, no este roadmap. El tablero de análisis se
      navegaba solo con el teclado y su pantalla era siempre la misma, mientras
      que el visor tenía controles visibles y cambiaba según lo que hace el
      motor: quien no sabe ya de análisis leía el tablero como una herramienta
      tosca. Entró: controles de navegación en pantalla y los mismos atajos que
      el visor (`Home`/`End` incluidos), estados del motor visibles (en cola /
      analizando con progreso / listo / vacío / error), etiquetas y selector de
      motor iguales en ambas pantallas. Se hizo en cuatro pasadas: legibilidad
      del análisis (2026-09-06), cimientos compartidos (2026-09-07), el resto
      (2026-09-08), que adoptó los componentes en el tablero de análisis y
      cerró las 38 filas del inventario, y el barrido de comprobación de las
      seis pantallas contra los siete criterios, que destapó y cerró nueve
      más. Revisar después las alternativas por jugada del visor (RF-10.2)
      añadió cuatro, cerradas igualmente: 51 en total. Entraron además seis piezas compartidas nuevas —la
      insignia (`components/Badge.tsx`) y sus dos usos con significado
      (`ClassificationBadge`, `CustomPositionBadge`), la tabla de datos
      (`DataTable`), el selector de motor (`EngineSelect`) y el botón de jugada
      (`components/board/MoveButton.tsx`) con sus atajos
      (`useMoveNavigationKeys`)— y dos módulos de `lib/`: la numeración de
      jugadas (`moves.ts`) y la paleta de los gráficos (`chartTheme.ts`).
      La API ganó para esto un solo campo, `starts_from_custom_position`,
      derivado del PGN y sin migración. Cuenta para 1.0.0 porque son
      incumplimientos de RF-5.1 y RNF-6 (progreso y errores del motor
      visibles), ya congelados; lo visual de RF-6.2 ("las mismas capacidades
      visuales que RF-5.2") lo cerró el ítem de legibilidad de más arriba y ya
      no entra aquí. La excepción son los controles en pantalla y `Home`/`End`
      del tablero de análisis, que ningún RF congelado pedía y se aceptan
      dentro de 1.0 por ser cuatro botones sobre lógica de navegación ya
      escrita.
- [x] Extractores de patrones: errores por tipo (RF-3.4), *time trouble*
      (RF-3.5), momentos críticos (RF-2.8) y "eval al salir de la apertura"
      (lo que faltaba de RF-3.2). Hecho el 2026-09-09, apoyado en el MultiPV
      que RF-10 acababa de persistir: distinguir "jugada única" de "tres
      alternativas igual de buenas" necesita exactamente ese material, y por
      eso los dos ítems iban juntos.

      Todo vive en `lucia_core.insights`, que era el módulo vacío con un TODO:
      son reglas de lectura de partidas, no consultas a una base. **No se
      vuelve a llamar al motor y nada se persiste**: los cuatro extractores
      leen lo que el análisis ya guardó, así que las partidas analizadas antes
      también entran ([ADR-0008](adr/0008-patrones-deducidos-al-leer.md)).

      1. **Momentos críticos** (RF-2.8): una posición es crítica si solo valía
         una jugada (la mejor línea le saca 10 puntos de probabilidad de
         victoria a la segunda), si la jugada cruzó el 50 % moviendo la
         evaluación al menos 15 puntos, o si había una ganada y se escapó. No
         son "las jugadas malas": la jugada única encontrada también cuenta, y
         saberlo es la mitad de lo que se viene a aprender. Salen con
         `GET /analysis/{id}` y el visor las lista con el motivo de cada una.
      2. **Tipo de error** (RF-3.4): cada error recibe un solo tipo, en este
         orden —reloj, táctico, final, posicional—, de la causa más específica
         a la más general. Que la partida esté en un final es contexto; haber
         tenido delante una captura ganadora es una causa.
      3. **Apuros de tiempo** (RF-3.5): la calidad de juego repartida por
         tramos de reloj restante, y en cuántas partidas se llegó a jugar con
         menos de veinte segundos. Solo cuentan las jugadas con reloj conocido.
      4. **Evaluación al salir de la apertura** (RF-3.2): la de la última
         jugada de fase `opening` de cada partida, promediada por apertura.

      De paso se corrigió un fallo de conteo que venía de antes: una partida
      analizada con los dos motores (RF-2.6) contaba **dos veces** en precisión
      media, en partidas analizadas y en el reparto por fases. Ahora, en
      estadísticas, cada partida cuenta una vez, con su análisis más reciente.
- [x] `lucia_core.openings`: tabla ECO (chess-openings de Lichess, CC0) para
      clasificar aperturas sin depender de lo que reporte chess.com, y con
      ella la categoría "book" de `classify_move` (lo que faltaba de RF-2.2).
      Hecho el 2026-09-09.

      1. **La tabla se versiona ya procesada** en
         `packages/core/lucia_core/openings/data/openings.tsv`: 3.810
         posiciones con su código ECO y su nombre. Lo que se guarda es la
         posición (EPD), no la secuencia de jugadas, y eso es lo que hace que
         las **transposiciones** funcionen: llegar a la Najdorf por otro orden
         de jugadas da el mismo nombre. La genera
         `scripts/build-openings-table.py` desde el repositorio de Lichess; se
         versiona porque la aplicación no puede depender de tener red para
         nombrar una apertura (RNF-1).
      2. **La tabla tiene huecos y hay que contar con ellos**: solo nombra las
         posiciones donde termina alguna línea con nombre, así que en mitad de
         una Najdorf hay jugadas sin nombre. La búsqueda los tolera —hasta
         cuatro seguidas— y se queda con la posición conocida más profunda, que
         es la que da el nombre más específico. Pararse en el primer hueco
         dejaba la partida en "Siciliana" a secas.
      3. **La categoría "book"** (RF-2.2) marca las jugadas que siguen en
         teoría, en vez de puntuarlas como aciertos de quien las juega. Con una
         excepción que se vio al probarlo: la tabla nombra también celadas —`1.
         f3 e5 2. g4` es el mate del loco y tiene nombre—, así que una jugada
         de libro que además hunde la posición se clasifica por lo que hizo. La
         teoría no tapa un error.
      4. **La apertura de cada partida se guarda al importarla**
         (`games.opening_eco` / `opening_name`, migración `9c2d51ab7e04`, con
         relleno de las ya importadas): sale en 262 de las 324 partidas del
         autor —chess.com daba 260, y sin código ECO—, y las 62 que faltan son
         exactamente las que no empiezan en la posición estándar, donde no hay
         apertura que nombrar. Las estadísticas por apertura (RF-3.2) usan ya
         esta clasificación, con su código ECO a la vista.
- [x] Comparación de repertorio con Lichess Explorer (RF-3.6). Hecho el
      2026-09-10.

      Responde a "dónde me salgo de la línea principal y con qué resultado":
      recorre cada partida desde el principio y, en cada posición en la que le
      toca mover al jugador, mira qué juegan los maestros en esa misma
      posición. La primera jugada propia que no está en ese repertorio es la
      salida de la teoría; a partir de ahí esa partida ya no dice nada del
      repertorio y se deja de mirar. Las salidas se agrupan: lo que interesa es
      "esto lo hago ocho veces y saco un 25 %", no ocho partidas sueltas.

      - **Es la primera vez que LUCIA necesita red mientras se usa**, y eso
        choca con RNF-1 (local-first). Decisión en
        [ADR-0010](adr/0010-repertorio-con-red-y-cacheado.md): `GET /repertoire`
        no sale a internet nunca —compara con lo que hay en la caché y dice
        cuánto le falta por saber—, y `POST /repertoire/refresh` es lo único
        que consulta, solo cuando el usuario lo pide. Todo lo consultado se
        guarda en `explorer_positions` (migración `b4e8c17f0a92`), indexado por
        posición, así que sirve para todas las partidas que pasen por ahí.
      - **Cliente propio en `packages/lichess`**, con las mismas reglas de
        cortesía que el de chess.com (RNF-10): `User-Agent` con contacto,
        peticiones espaciadas una por segundo, backoff ante `429` y un tope por
        llamada para no dejar la petición HTTP colgada minutos.
      - **Se pregunta lo mínimo**: solo las posiciones donde decide el jugador,
        solo hasta la jugada 8 de cada bando y solo hasta salirse del libro.
        Medido sobre las 324 partidas del autor: el tope teórico serían 1.058
        posiciones, pero como se para al salir de la teoría, la frontera real
        es mucho menor y se reaprovecha entre partidas.
      - **Hace falta un token de Lichess**, y no es opcional: el explorador
        dejó de admitir peticiones anónimas y responde `401` a todo, incluido
        el ejemplo de su propia documentación (comprobado el 2026-09-10; su
        especificación declara `security: OAuth2`). Es gratuito y sin permisos,
        se saca en <https://lichess.org/account/oauth/token> y va en
        `LICHESS_TOKEN`. La pantalla lo dice antes de que se pulse nada, y sin
        él sigue enseñando lo que ya esté consultado.
      - Lo que **no** se pudo probar: una consulta real con token válido, por
        no tener uno. El cliente está probado con la respuesta simulada
        (`respx`) y con la forma documentada de la API, y el servicio con un
        explorador falso; los dos caminos de error —sin token y sin red— sí se
        comprobaron de verdad contra el servicio real.
- [x] Importar PGN manual de otras fuentes —OTB, lichess— al historial (RF-1.5).
      Hecho el 2026-09-17: `POST /import/pgn` (multipart, tope de 5 MB) y el
      formulario "Importar PGN" junto al de sincronizar, en Partidas.

      - **Las partidas manuales son filas normales de `games`**, con
        `platform="manual"`, para que el visor, el análisis y las estadísticas
        no tengan que saber de dónde vino cada una. Lo que un PGN no dice
        —rating, ritmo, si era puntuada— se guarda como hueco y se enseña como
        "—", en vez de inventarlo o hacer las columnas opcionales
        ([ADR-0011](adr/0011-pgn-manual-en-la-misma-tabla.md)).
      - **Identidad por el SHA-256 del PGN**: no hay `uuid` que usar, así que
        reimportar el mismo archivo reescribe las filas en vez de duplicarlas,
        igual de idempotente que el sync.
      - **Hay que decir cómo apareces en el archivo.** Un PGN de torneo nombra
        al jugador "Durán, Jesús" y no con su usuario, y las estadísticas y
        tres de los filtros casan por nombre. La respuesta dice en cuántas
        partidas se reconoció al usuario y la pantalla avisa cuando fue en
        ninguna: guardadas, pero sin contar en ningún marcador.
      - **Lo que no entra**: partidas sin terminar ("\*") y sin jugadas; la
        respuesta las enumera con el motivo, para que un recuento que no cuadra
        con el archivo no se lea como un fallo.
      - Dependencia nueva: `python-multipart` (BSD-3, compatible con GPL-3.0).
- [x] Filtros de `/games` por apertura, rango de fechas, rival y resultado (lo
      que faltaba de RF-5.3). Hecho el 2026-09-09; con 324 partidas ya se
      notaba.

      - **Resultado, color y rival dependen de quién sea el jugador** y sin
        `username` se ignoran: la misma partida es victoria para uno y derrota
        para el otro, así que aplicarlos a medias daría un resultado plausible
        y equivocado. En la pantalla salen deshabilitados con el motivo, en vez
        de fingir que filtran.
      - **Apertura por subcadena**: "sicilian" trae todas las sicilianas. Usa
        el nombre de la tabla ECO propia, así que las partidas que no empiezan
        en la posición estándar no salen con ningún filtro de apertura: no
        tienen apertura que nombrar.
      - **Fechas inclusivas por los dos lados**: `until` cubre el día entero.
      - De paso, las cuatro expresiones SQL de "de qué color jugó y qué le
        pasó" dejaron de estar duplicadas entre el listado y las estadísticas y
        viven en `services/games.py`. Comprobado contra las 324 partidas
        reales: los filtros por resultado dan 193/14/117, exactamente el
        marcador que enseña el dashboard.
- [x] Tendencias temporales (RF-3.7). Hecho el 2026-09-18: sección "Cómo
      evolucionas" en el dashboard, con la precisión y el rating mes a mes y
      los errores por tipo apilados.

      - **Mes natural como tramo**, el mismo eje que "Partidas por mes"
        (RF-3.1), para que las dos series se lean juntas.
      - **Errores por cada cien jugadas y no en recuento**: con 324 partidas
        repartidas muy desigualmente por mes, el recuento crudo dibujaba la
        cantidad de ajedrez jugado y no su calidad.
      - **Solo los meses con partidas analizadas.** Uno jugado pero sin
        analizar entraría como precisión cero, que se lee como un desastre.
      - **Frase de tendencia** comparando el último mes con hasta tres
        anteriores, ponderada por jugadas, y diciendo el sentido con palabras:
        en precisión subir es mejorar y en errores es empeorar.
      - **Línea de rating al lado**, que es un extra sobre el texto del RF: es
        la del control de tiempo más jugado y la pantalla dice cuál, porque
        promediar bullet con rapid inventaría caídas de rating.
- [x] Tablero de análisis, extras (RF-6.6 a 6.9) y el editor de posición que
      faltaba de RF-6.1. **Hechos el 2026-09-18**
      RF-6.6 y RF-6.7: "Abrir como tablero" en el visor crea una copia
      desacoplada de la partida (esto también cubre "explorar variantes desde
      el visor", RF-5.2), y el tablero de análisis importa un PGN pegado con
      variantes y comentarios, `fromPgn` en `features/board/tree.ts` —lector
      propio, porque `loadPgn` de chess.js descarta las variantes—, con
      `root_fen` nuevo en `PUT /boards/{id}` para los PGN que arrancan de una
      posición dada. Exportar ya estaba desde el núcleo de la fase 1, y el
      lector nuevo sustituye también al `loadPgn` con que la pantalla de
      Tableros creaba un tablero desde un PGN pegado: descartaba las
      variantes, así que el mismo archivo daba un tablero distinto según se
      pegara al crear o después.

      - **Al abrir desde el visor se prefiere el PGN anotado** (RF-5.5) si hay
        análisis terminado, y el crudo si no: el tablero nace con lo que ya se
        sabía de la partida. La copia nunca se marca como partida propia
        (RF-6.5), que contaría dos veces la misma partida.
      - **Importar sustituye el árbol y renombra el tablero** desde las
        cabeceras del PGN: un tablero no se puede renombrar a mano desde
        ninguna pantalla.
      - **Una jugada ilegal corta su rama y se cuenta**, en vez de tumbar la
        importación entera; la pantalla dice cuántas ramas se perdieron.

      **Hechos también el 2026-09-18** RF-6.8 y RF-6.9: deshacer / rehacer
      sobre el árbol (el autoguardado ya estaba desde la fase 1) y análisis
      completo del tablero en background bajo demanda.

      - **El historial se guarda en la base**, no en la pantalla: tabla
        `board_versions` y `boards.current_version_id` como cursor, de modo
        que deshacer sobrevive a recargar. Es lineal —editar después de
        deshacer descarta lo de delante— y se poda a 50 versiones por
        tablero ([ADR-0012](adr/0012-historial-de-tablero-lineal-y-persistido.md)).
        `POST /boards/{id}/undo` y `/redo`, botones y atajos (Ctrl+Z, Ctrl+Y
        o Ctrl+Mayús+Z) en `useUndoRedoKeys`. Solo lo que cambia el árbol
        hace historial: renombrar, no.
      - **El análisis del tablero lo hace el mismo worker que las partidas**:
        `Analysis` cuelga de `game_id` o de `board_id`
        ([ADR-0013](adr/0013-analisis-de-partida-o-de-tablero.md)), el PGN de
        la línea principal lo manda el front (`toPgn`) y se guarda en
        `analyses.analyzed_pgn`, así que la pantalla avisa cuando el tablero
        cambió desde el análisis (`matchAnalyzedLine`). Un tablero a secas no
        cuenta en las estadísticas (RF-6.5); que uno marcado como propio sí
        cuente quedó pendiente aquí unas horas y lo cerró el ítem siguiente
        el mismo 2026-09-18, publicándolo como partida —las agregaciones de
        RF-3 se apoyan en columnas de `games` que un tablero no tiene (ver la
        nota de RF-6.8 / RF-6.9 en
        [02-requerimientos.md](02-requerimientos.md))—.

      **Y el mismo 2026-09-18** lo último que quedaba de RF-6.1: el editor de
      posición pieza a pieza, `features/board/PositionEditor.tsx` con la
      posición y su FEN en `features/board/position.ts` (13 tests). Con esto
      el ítem queda cerrado.

      - **El editor rellena el campo "FEN o PGN" de la pantalla de Tableros**,
        que sigue siendo la única forma de crear: es un ayudante de ese campo
        y no una segunda puerta que mantener en paralelo.
      - **La posición que se edita no es un `Chess` de chess.js**: a medio
        montar es ilegal casi siempre y chess.js no la carga, así que el
        modelo es propio y chess.js entra solo al final, para decir si sirve
        —más una comprobación que él no hace: que el bando que no mueve no
        esté dando jaque—, con los motivos traducidos y a la vista antes de
        pulsar. Es una decisión local del componente, sin ADR (razonada en la
        nota de RF-6.1 en [02-requerimientos.md](02-requerimientos.md)).
      - **Tres formas de colocar**: elegir en la paleta y pulsar casillas,
        arrastrar desde la paleta, y el teclado. Esto último pidió una rejilla
        de 64 botones superpuesta al tablero con `pointer-events-none`, porque
        chessground no hace enfocable ninguna casilla y el ratón tiene que
        seguir llegándole intacto (criterio C-1).
- [x] Tableros marcados como "partida propia" contando en estadísticas y
      patrones (lo que faltaba de **RF-6.5**). Hecho el 2026-09-18: marcar el
      tablero lo **publica en el historial como una partida**, y desde ahí
      cuenta sin que ninguna consulta de RF-3 cambie
      ([ADR-0014](adr/0014-tablero-propio-publicado-como-partida.md)).

      - **Se piden cuatro datos y ninguno más** —color, rival, resultado y
        fecha—, los que las agregaciones de RF-3 necesitan para contarlo sin
        inventar nada. Rating y control de tiempo se quedan en el mismo hueco
        que deja la importación de PGN manual (RF-1.5), porque un tablero
        tampoco los sabe, y la pantalla lo dice antes de pulsar.
      - **La marca es el enlace a esa partida** (`boards.own_game_id`), no un
        booleano aparte: un booleano podría contradecir a la fila publicada y
        entonces el listado diría una cosa y el dashboard otra. La migración
        `a71c40f5d3e8` pierde las marcas anteriores, que no traían esos datos.
      - **El análisis del tablero cuenta mientras siga siendo el de estas
        jugadas**: lleva `game_id` además de `board_id`, y se desenlaza en
        cuanto el tablero se edita. La regla de ADR-0013 ("uno de los dos,
        nunca los dos") pasa a ser "al menos uno".
      - **Deshacer y rehacer arrastran la partida publicada** en la misma
        petición: cada versión del historial guarda su PGN
        (`board_versions.pgn`, migración `d4b7e0c25a19`), así que la pantalla
        ya no tiene que volver a publicar el tablero después.
      - **De paso se encendieron las claves foráneas de sqlite**
        (`PRAGMA foreign_keys=ON` en `db/base.py::create_db_engine`): venían
        apagadas por conexión, así que ningún `ON DELETE` del esquema se
        ejecutaba y borrar un tablero dejaba huérfanas sus versiones y sus
        análisis. Con ellas encendidas salió a la luz que
        `analyzed_moves.analysis_id` no tenía cascada (migración
        `c8f3a2b91e47`). Las migraciones siguen corriendo con el pragma
        apagado, porque alembic recrea tablas enteras para cambiarlas.
- [x] Capa de ocupación del tablero (RF-7.1 a 7.7): sub-modo mapa de calor,
      sub-modo cobertura directa del turno, inspección por casilla, piezas
      colgadas, rayos X aparte y clavadas marcadas, reglas de conteo (rey,
      peones en diagonal, al paso). Hecho el 2026-09-19: se enciende con la
      tecla O o desde su panel, en el visor (RF-5) y en el tablero de análisis
      (RF-6); en el entrenamiento (RF-4) se enchufará cuando esa pantalla
      exista, en la fase 3.

      - **Cálculo propio de los alcances, no `attackers()` de chess.js.** El
        atajo de la librería devuelve solo las casillas de origen, y aquí hacen
        falta tres cosas más: qué pieza ataca desde cada una (para ordenar la
        inspección por valor, RF-7.3), el rayo X separado del ataque directo
        (RF-7.5) y si la pieza que ataca está clavada, **de los dos bandos**
        —chess.js solo calcula las jugadas legales del que tiene el turno, así
        que la clavada se resuelve por geometría (RF-7.6)—. Recorrer las líneas
        una vez las saca las tres, y de paso las reglas de conteo de RF-7.7
        salen solas: el rey alcanza sus ocho casillas como cualquier otra
        pieza, el peón sus dos diagonales y no la de delante, y la casilla de
        captura al paso la alcanza el peón que podría capturar ahí sin tratarla
        como caso especial. A chess.js se le pide solo leer el FEN.
      - **La casilla bajo el puntero se calcula por geometría**, midiendo sobre
        el rectángulo del tablero, y no se le pregunta a chessground: sus
        eventos de selección solo existen cuando el tablero es manipulable —el
        visor lo tiene en modo lectura— y no tiene evento alguno de "el ratón
        pasa por encima", que es justo lo que RF-7.2 necesita para filtrar la
        cobertura al señalar una pieza. Con la medida, las dos pantallas
        responden igual y chessground sigue recibiendo el ratón intacto.
      - **Los conectores son de la pieza señalada o fijada**, y solo una trama
        muy atenuada para el bando entero en cobertura: dibujar las sesenta
        líneas de un bando a plena intensidad no informa de nada, y en mapa de
        calor no se dibuja ninguna porque ahí el color ya lo cuenta.
      - **Nada de esto toca la API ni el motor**: es una capa de lectura sobre
        la posición que ya está en pantalla, como pedía el propio RF-7. Sin
        endpoint nuevo, sin esquema nuevo y sin persistencia, así que no hay
        decisión de arquitectura que registrar en un ADR.
      - **Quedan fuera RF-7.8 y RF-7.9**, los dos P2 y en la fase 4: recordar
        el sub-modo y los filtros entre sesiones —que espera al almacén único
        de preferencias de RF-8— y las casillas críticas según motor, el único
        punto de RF-7 que necesitaría llamar a Stockfish.
- [x] Exportar PGN anotado (RF-5.5). Hecho el 2026-09-17:
      `GET /analysis/{id}/pgn` y el enlace "Exportar PGN anotado" en la
      cabecera del visor. El archivo se abre en lichess, ChessBase o SCID como
      cualquier otro PGN comentado.

      - **Se comentan todas las jugadas**, no solo las falladas como hace
        lichess: cada una lleva su clasificación y la probabilidad de victoria
        en que dejó la partida, desde el punto de vista de las blancas. El
        símbolo (`?!`, `?`, `??`) sí es solo para lo fallado; poner `!` donde
        se coincidió con el motor sería un mérito que el análisis no mide.
      - **La línea del motor cuelga del padre de la jugada** —la posición desde
        la que se eligió— y solo cuando lo jugado no era lo que el motor
        prefería, recortada a 6 medias jugadas.
      - **No se vuelve a llamar al motor**: todo sale de `analyzed_moves`
        (RF-2.2, RF-10.1), con el mismo rescate desde `position_cache` que usa
        el detalle para los análisis anteriores a RF-10, que si no se puede
        hacer deja el PGN comentado pero sin variantes.
      - **Solo se exportan análisis terminados** (409 si no): uno a medias
        daría una partida comentada hasta la jugada 20 y muda después.
      - **Se conservan las cabeceras del PGN original** y no las columnas
        normalizadas de `games`, que en una partida importada por RF-1.5 pueden
        no coincidir.
      - De paso, el bloque que carga análisis + jugadas + alternativas de caché
        dejó de estar duplicado entre el detalle y la exportación
        (`_load_analysis_with_moves`).

## Apéndice de la fase 2 · lo que destapó la auditoría (2026-09-19) ✅

> Sus siete puntos están cerrados. Es el corte de la versión `0.4.0` (ver
> [CHANGELOG.md](../CHANGELOG.md)).

Cerrada la fase, se auditaron por separado el mapa del proyecto, la
documentación y el código de los catorce ítems. Lo que salió de ahí y no cabía
dentro de ninguno de ellos queda recogido aquí, en vez de reabrir casillas ya
cerradas o de quedarse en un informe que nadie vuelve a leer. **No es alcance
nuevo**: ninguno de estos puntos añade un RF, son cabos sueltos de lo ya
entregado. Lo que sí es alcance —RF-3.8— se dice expresamente.

- [x] **RF-2.6 entregó la mitad de su texto**, y ya está completo. Hecho el
      2026-09-19. El requerimiento pide "probabilidad W/D/L, contraste con
      Stockfish en posiciones donde discrepan": el contraste estaba, la W/D/L
      no. Lo que se guardaba era la probabilidad de victoria derivada del
      centipeón con el modelo de Lichess
      (`Score.wdl(model="lichess").expectation()` en `lucia_core.accuracy`),
      que es una fórmula común a los dos motores y no lo que el motor opina.

      - **La W/D/L se le pide al motor con `UCI_ShowWDL`**, por la misma vía
        filtrada que `Threads` y `Hash` (`EngineBridge._options_to_apply`): la
        declaran Stockfish y Lc0, pero no tiene por qué declararla un motor
        UCI cualquiera, y pedírsela a quien no la conoce abortaría la
        conexión. Un motor que no la informe deja `EngineLine.wdl` en `None` y
        la interfaz se dibuja sin la columna, que es lo que debe pasar
        (RNF-9 sigue en pie).
      - **No hizo falta ninguna migración.** La W/D/L viaja en el mismo JSON
        que la puntuación (`position_cache.lines_json` y
        `analyzed_moves.alternatives_json`), en una clave que puede faltar:
        toda la caché y todos los análisis escritos antes de esto se leen sin
        ella y siguen valiendo. Y como las líneas de una jugada son las de la
        posición **anterior** a ella (RF-10.1), la W/D/L de la posición que
        deja la jugada `ply` ya está guardada en la fila `ply + 1`: la
        comparación la lee de ahí (`comparison._wdl_after`) en vez de
        duplicarla en una columna nueva. La última jugada de la partida no
        tiene posición siguiente y se queda sin reparto, dicho y no inventado.
      - **Se enseña en los dos sitios donde se lee una opinión del motor**, con
        el mismo componente (`components/WdlBar.tsx`, criterio C-5): la lista
        de líneas —tablero de análisis y alternativas del visor— y la
        comparación entre motores, donde cada uno trae el suyo. La barra usa
        los blancos y negros de la barra de evaluación para que los bandos se
        reconozcan entre las dos, con el gris de las tablas en medio.
      - **Por qué era la mitad que faltaba, medido**: desde la posición
        inicial, Stockfish da 159/837/4 y Lc0 330/429/241. La probabilidad de
        victoria de los dos ronda el 50 % y no distingue nada; el reparto dice
        que uno ve tablas casi seguras y el otro una partida abierta. Ese es el
        desacuerdo que el requerimiento quería ver.
- [x] **RF-3.8 no estaba en ninguna fase**, y ahora está en la **fase 4**.
      Resuelto el 2026-09-19. "Análisis de rivales: patrones contra rivales
      recurrentes" (P2) entró en el alcance congelado de v1.0 el 2026-09-05 y
      nunca llegó a tener ítem: el mapa lo daba por "pendiente (fase 2)" y la
      fase 2 se cerró sin él. Se queda dentro del alcance de 1.0 —no se manda a
      Post 1.0— y baja a la fase 4 con los demás P2 congelados, que es donde
      encaja: lo que necesita para montarse (las agregaciones de
      `services/stats.py` y los extractores de `lucia_core.insights`) ya está
      entregado, así que no bloquea la fase 3.
- [x] **Cuatro incoherencias de interfaz seguían abiertas**, y ya no queda
      ninguna. Hecho el 2026-09-19. Eran las filas 65, 67, 68 y 70 de
      [07-coherencia-ui.md](07-coherencia-ui.md), dos de la pantalla de
      Partidas y dos del control de exportar del visor, heredadas de RF-1.5 y
      RF-5.5 (2026-09-17). **Es la primera vez que el inventario queda vacío.**

      - **65 (C-2)**: la cabecera de Partidas repartía con `justify-between` el
        título y **dos** formularios; al envolverse, el título se quedaba solo
        arriba y las dos formas de traer partidas a distinta altura. Ahora el
        título va en su línea y los dos formularios en la de abajo.
      - **67 (C-6)**: el listado no decía de dónde venía una partida, así que
        una importada de un PGN enseñaba cuatro columnas vacías sin explicar por
        qué. `GameSummary` expone ya `platform` y `GameSourceBadge` marca lo que
        se sale de la norma —"PGN importado", "tablero propio"—, en el listado y
        en la cabecera del visor. Las de chess.com no llevan insignia: son la
        mayoría y marcarlas todas sería ruido.
      - **68 y 70 (C-3) se arreglaron juntas porque son el mismo control.**
        "Exportar PGN anotado" está ahora **siempre**, deshabilitado y diciendo
        qué falta cuando no hay análisis; y dejó de ser un `<a download>`, con
        lo que un 409 o un 404 ya no se guardan como si fueran el archivo.
        Pasa por `api.getAnalysisPgn`, que comprueba la respuesta y solo
        entonces guarda (`lib/download.ts`), respetando el nombre que propone el
        servidor. Convertir el enlace en botón es lo que permitió las dos cosas:
        un enlace no se puede deshabilitar con un motivo ni sabe que falló.
- [x] **Dos dependencias declaradas y nunca importadas**, y ya no están.
      Hecho el 2026-09-19. Eran `polars>=1.5` en
      `packages/core/pyproject.toml` —las agregaciones de RF-3 acabaron siendo
      SQL puro— y `zustand` en `apps/web/package.json`, que
      [03-arquitectura.md](03-arquitectura.md) ya decía expresamente que no
      hizo falta. Se retiran de los manifiestos y de los dos lockfiles; si
      alguna vez hacen falta, volver a añadirlas es una línea.

      - **Quitar polars invirtió una decisión escrita**, así que llevó ADR
        propio: [ADR-0016](adr/0016-agregaciones-en-sql-sin-polars.md). La
        consecuencia de ADR-0005 decía "agregaciones pesadas se hacen en polars
        sobre extractos, no con SQL complejo" y nunca se cumplió; ADR-0005 no se
        edita, se supera. ADR-0003 sigue válido en lo que decide y solo pierde
        uno de los ejemplos de su razonamiento.
      - **Zustand no necesitaba ADR**: no era una decisión de arquitectura
        registrada, solo una fila en el stack. El estado de servidor lo lleva
        TanStack Query y el local de cada pantalla es `useState`.
      - **Quedan dos menciones del mismo tipo en
        [04-stack-tecnologico.md](04-stack-tecnologico.md)**, que no se han
        tocado porque no son dependencias declaradas en ningún manifiesto —solo
        texto—: **shadcn/ui**, que la interfaz no usa (los componentes de
        `apps/web/src/components/` son propios), y **Playwright**, que no tiene
        ni configuración ni una sola prueba E2E.
- [x] **Los valores por defecto de Lc0 eran la peor combinación posible**, y
      ya no. Hecho el 2026-09-19. `Settings` traía `default.pb.gz` + `blas`
      mientras que `.env.example` recomendaba otra cosa: quien clonara el repo
      y no copiara el `.env` arrancaba Lc0 con la red transformer, que OpenCL
      rechaza y en CPU da 2,5 nodos/s.

      - **La red por defecto pasa a ser la T74 convolucional**
        (`744706-conv.pb.gz`), que es la que el propio repo llamaba "la
        recomendada" en tres documentos mientras el código cargaba otra.
      - **El backend por defecto pasa a ser vacío**, no `opencl`. Vacío no deja
        a Lc0 sin backend: hace que elija entre los que `setup-engines.sh` le
        compiló en esa máquina, y elige bien. Copiar el `opencl` del
        `.env.example` al código habría sido peor que el problema original,
        porque un backend que no se compiló aborta el arranque —se comprobó
        pidiendo `cuda` en esta máquina, que se compiló con OpenCL: `invalid
        value for combo option 'Backend'`—.
      - **La advertencia que traía el código era falsa.** Decía que "sin
        especificarlo, Lc0 elige por su cuenta y puede ser ~20x más lento",
        medido en 74 s contra 4 s. Medido ahora con la red T74, 3.000 nodos
        desde la posición inicial en la misma GTX 1060: **vacío 1,23 s,
        `opencl` 1,12 s, `blas` 14,88 s**. Dejar elegir a Lc0 está al nivel del
        mejor backend, y el defecto anterior era doce veces más lento; aquellos
        74 segundos los costaba la **red** transformer, no la elección
        automática de backend. La tabla de medidas de más arriba, en el ítem de
        Lc0, sigue siendo correcta: cruza red con backend y no incluía la fila
        de "sin especificar".
- [x] **`analyzed_moves` arrastraba una clave foránea duplicada**, y ya no.
      Hecho el 2026-09-19 con la migración `3208b0d0f467`. La `c8f3a2b91e47`
      había añadido la de `ON DELETE CASCADE` dentro de un `batch_alter_table`
      sin quitar la original sin nombre, así que la tabla tenía dos sobre
      `analysis_id`, una `NO ACTION` y otra `CASCADE`.

      - **No era un fallo vivo**, y conviene que conste: se comprobó sobre una
        copia de la base que el borrado en cascada funcionaba —sqlite aplica la
        cascada y la `NO ACTION` ya no encuentra huérfanas que objetar—. Lo que
        dejaba era un esquema que decía dos cosas contradictorias sobre la
        misma columna, un `SAWarning` en cada `alembic check` y una trampa para
        la siguiente migración que tocara la tabla.
      - **Por qué la anterior no la quitó, que es lo que hay que recordar**:
        dentro de un `batch_alter_table`, alembic reconstruye la tabla a partir
        de lo que **refleja** de la base, así que reflejó la original, la
        recreó y le puso la nueva al lado. La de ahora lleva `copy_from` con la
        definición escrita entera en el propio archivo, y `recreate="always"`
        para forzar la reconstrucción sin pedirle ningún cambio de columna. La
        definición no se importa de `db/models.py` a propósito: una migración
        describe la tabla tal como era en ese punto de la historia.
      - **Comprobado sobre una copia de la base real** antes de tocar nada: 728
        jugadas antes y después, con la misma huella SHA-256 fila a fila; una
        sola clave foránea, la del cascade; el borrado en cascada sigue
        funcionando y `PRAGMA foreign_key_check` no encuentra violaciones;
        `alembic check` ya no avisa; bajar y volver a subir deja el esquema
        donde estaba; y una base creada desde cero nace con una sola.
- [x] **ADR-0008 citaba dos veces un `GET /stats/{username}` que nunca
      existió** (el endpoint es `GET /stats?username=…`). Corregido el
      2026-09-19, en el propio archivo y con una nota fechada al final que dice
      qué se cambió y por qué.

      - **Sí es excepción a la norma, y conviene dejar sentado por qué.** No
        editar un ADR publicado protege el registro de las **decisiones**: lo
        que ADR-0008 decide —que los patrones se deducen al leer, sin tabla
        propia ni segunda pasada del motor— es idéntico antes y después. Un
        dato de hecho equivocado en la prosa de apoyo no es una decisión, y
        conservarlo solo sirve para desinformar a quien lo lea. Lo que la norma
        sí busca evitar —que la historia se reescriba en silencio— lo cubre la
        nota de corrección, no el dejarlo mal.
      - **El barrido fue a los dieciséis ADR, no solo a este**: se cruzaron los
        endpoints que citan contra `openapi.json`, sus rutas de archivo contra
        el disco y sus identificadores entre comillas invertidas contra el
        código. Las dos menciones de ADR-0008 eran **el único** error de hecho;
        los identificadores que no aparecen en el código son nombres de
        alternativas descartadas que los propios ADR discuten
        (`analyzed_move_lines`, `mistake_types`, `board_analyses`), que es como
        deben estar.

## Fase 3 · Entrenamiento (P1/P2)

- [ ] Puzzles desde mis errores con repetición espaciada, aceptando como buena
      cualquier jugada equivalente y no solo la única del motor (RF-4.1 con
      RF-10.3, que necesita las líneas persistidas en la fase 2).
- [ ] Sparring contra Stockfish limitado / Lc0 con Maia.
- [ ] Drill de aperturas; "re-juega desde el error".
- [ ] Plan semanal de entrenamiento.

## Fase 4 · Pulido y distribución

- [ ] Ocupación del tablero, extras (RF-7.8 y 7.9): recordar sub-modo y filtros entre sesiones; "casillas críticas según motor" superponiendo las casillas más frecuentes en las mejores líneas de Stockfish.
- [ ] Análisis de rivales recurrentes (**RF-3.8**): contra quién se juega más y
      qué pasa en esas partidas —marcador, precisión, aperturas que salen y
      dónde se pierde la ventaja—, frente a la media propia. Colocado aquí el
      **2026-09-19**: es alcance congelado de v1.0 desde el corte del
      2026-09-05, pero se quedó sin ítem en ninguna fase y el mapa lo daba por
      "pendiente (fase 2)" mientras la fase 2 se cerraba sin él (ver el
      apéndice de la fase 2). Cae en esta fase y no antes porque es el único
      P2 de RF-3 y las agregaciones sobre las que se monta —`services/stats.py`
      y los extractores de `lucia_core.insights`— ya están entregadas: no
      bloquea nada de la fase 3.
- [ ] Explicaciones en lenguaje natural de errores.
- [ ] Empaquetado (Docker, posiblemente Tauri).
- [ ] macOS / Windows.

## Post 1.0 (futuro)

Todo lo que queda fuera del alcance congelado de v1.0: lo que se plantee
después del corte del **2026-09-05** aunque sea antes de publicar 1.0.0, lo
que se decida sacar del alcance original, y lo que surja ya con v1.0.0
publicada. Nada de esta sección cuenta para el progreso hacia 1.0.0. Se numera
como Fase 5 en adelante.

**RNF-11 (coherencia de interfaz)** vive aquí como criterio permanente, pero no
tiene fase propia: el trabajo que se deriva de él son incumplimientos de RF ya
congelados, y está en la fase 2.

**RF-9 (comparación de evaluaciones entre motores)** tampoco tiene fase propia:
es una ampliación menor de RF-2.6, planteada el 2026-09-06 al comprobar que el
panel de discrepancias existente solo enseña las jugadas donde los motores se
separan. Cuando se retome, cabe junto al resto del trabajo del visor.

**RF-10 estuvo aquí y ya no.** Se planteó el 2026-09-06 y se movió al alcance de
v1.0 ese mismo día: persistir las líneas del motor es cambio de esquema, y
hacerlo después obligaría a migrar o re-analizar. Vive en la fase 2.

### Fase 5 · Personalización de interfaz (RF-8)

Bloque planteado el **2026-09-06**, después del corte de alcance, así que no
cuenta para el progreso hacia 1.0.0. Recoge lo que se quiera ajustar de la
UI/UX según se vaya usando la aplicación: hoy la paleta, el tablero `brown`,
las piezas `cburnett`, los colores de clasificación y los atajos están fijados
en el código.

- [ ] Aspecto del tablero y las piezas: sets seleccionables, color del tablero,
      coordenadas, estilo de resaltados (RF-8.1).
- [ ] Paletas de la aplicación, incluidas una de alto contraste y una apta para
      daltonismo (RF-8.2), y colores semánticos configurables aparte:
      clasificaciones, mapa de calor de ocupación y flechas del motor (RF-8.3).
- [ ] Layout, densidad y tipografía: paneles reordenables y plegables, tamaño
      del tablero, modo compacto, tamaño de fuente (RF-8.4, RF-8.5).
- [ ] Comportamiento y accesibilidad: sonidos, animaciones respetando
      `prefers-reduced-motion`, atajos de teclado reconfigurables
      (RF-8.6 a RF-8.8).
- [ ] Presets exportables e importables (RF-8.9).
- [ ] Almacén único de preferencias del usuario, que absorba el tema
      claro/oscuro (hoy suelto en `localStorage`) y la persistencia del
      sub-modo de ocupación (RF-7.8).

### Fase 6 · Partidas con ventaja (RF-11)

Bloque planteado el **2026-09-07**, después del corte de alcance, así que no
cuenta para el progreso hacia 1.0.0. Dependía de dos cosas que sí son alcance
de 1.0: el editor de posición pieza a pieza (RF-6.1), que llegó el 2026-09-18
con los extras del tablero, y el sparring contra motor con fuerza calibrada
(RF-4.3, fase 3), que sigue por hacer.

- [ ] Jugar contra el motor desde una posición inicial personalizada, eligiendo
      color y bando con ventaja (RF-11.1).
- [ ] Dificultad en dos perillas: fuerza del motor y ventaja material, cada una
      con su control y su explicación (RF-11.2).
- [ ] Guardar la partida jugada con su PGN (`SetUp`/`FEN`), analizable con RF-2
      y visible en el visor, pero fuera de estadísticas (RF-11.3).
