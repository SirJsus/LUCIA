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

> **RF-4 está cerrado entero. La fase 3 no.** Conviene no leer lo uno como lo
> otro. Con el plan semanal (RF-4.5, 2026-09-21, versión `0.4.5`) quedan
> entregados los cinco puntos de RF-4 —puzzles (2026-09-19, versión `0.4.1`),
> sparring (2026-09-21, versión `0.4.2`), drill de aperturas (2026-09-21,
> versión `0.4.3`), "re-juega desde el error" (2026-09-21, versión `0.4.4`) y
> el plan—, y el entrenamiento de v1.0 no tiene nada pendiente.
>
> **Lo que mantiene la fase abierta es su sexto ítem, y es de RF-7, no de
> RF-4**: enchufar la capa de ocupación (RF-7.1 a 7.7) en las pantallas de
> entrenamiento, que la fase 2 dejó dicho que se haría cuando esas pantallas
> existieran. Ahora existen las seis y **ninguna la usa** —comprobado sobre el
> código el 2026-09-21: `OccupancyLayer` y `useOccupancy` solo aparecen en el
> visor (`features/viewer/`) y en el tablero de análisis (`features/board/`)—,
> así que la casilla sigue sin marcar y no se marca por simpatía con RF-4. Por
> eso `0.4.5` sube el patch y no cierra fase.
>
> Eran cuatro ítems hasta el **2026-09-21**: RF-4.2 y RF-4.4 compartían uno y
> se separaron al entregarse el primero, para no marcar como hecho lo que no lo
> estaba — el mismo criterio con el que RF-6.5 se separó de los extras del
> tablero en la fase 2, y el mismo por el que la capa de ocupación no se marca
> ahora.

- [x] Puzzles desde mis errores con repetición espaciada, aceptando como buena
      cualquier jugada equivalente y no solo la única del motor (RF-4.1 con
      RF-10.3, que necesita las líneas persistidas en la fase 2). Hecho el
      2026-09-19: pantalla de Entrenamiento con la cola del día,
      `POST /training/puzzles` (generar), `GET /training/puzzles` (lo que toca
      repasar) y `POST /training/puzzles/{id}/answer` (responder), tabla
      `puzzles` (migración `e1a7c93d40b2`) y las dos reglas puras en
      `lucia_core.training`. Las reglas que el texto del RF no fijaba están en
      la nota "Con qué reglas se cumplió RF-4.1" de
      [02-requerimientos.md](02-requerimientos.md).

      - **Dan puzzle los errores propios graves** —`mistake`, `blunder`,
        `missed_win`— del análisis terminado más reciente de cada partida, el
        mismo criterio con el que cuentan las estadísticas. Las imprecisiones
        no: una jugada que pierde menos de diez puntos de probabilidad de
        victoria no tiene respuesta que encontrar, y como puzzle solo enseñaría
        a adivinar la preferencia del motor. Los errores del rival tampoco.
      - **RF-10.3: se acepta cualquier jugada equivalente**, no solo la
        favorita del motor — toda la que no pierda más de 2 puntos de
        probabilidad de victoria respecto a ella, que es el mismo margen con el
        que RF-2.2 llama "excelente" a una jugada. Las candidatas salen de las
        alternativas persistidas en la fase 2 (RF-10.1) o de lo que se rescate
        de `position_cache`; sin ninguna queda la `best_move_uci` sola, y un
        error del que no se pueda afirmar ninguna respuesta no genera puzzle.
        **Con esto RF-10 queda entregado entero.**
      - **La repetición espaciada es SM-2** (el de Anki), con tres resultados:
        fallar, acertar tras más de un intento y acertar a la primera. Fallar
        reinicia los aciertos seguidos pero no la facilidad, que se arrastra, y
        el próximo vencimiento se cuenta desde el repaso para que repasar tarde
        no encadene retrasos. Vive en `lucia_core.training`, sin base de datos
        y sin reloj, para poder probarse solo (RNF-8).
      - **Generar es un botón y es idempotente**, con clave `(partida, jugada)`:
        quien entrena decide cuándo renovar su baraja, y analizar una tanda de
        partidas no le cambia la cola por sorpresa ni le toca el estado de
        repaso de lo que ya tenía.
      - **El puzzle abierto no viaja con nada que lo resuelva** —ni solución,
        ni la jugada que se hizo, ni clasificación, ni evaluaciones—: la
        comprobación es del servidor y todo eso se manda al cerrarlo. Por lo
        mismo, es la única pantalla con tablero sin barra de evaluación.
      - **El puzzle se guarda entero y con su solución congelada**, desacoplado
        de la jugada analizada de la que salió, porque lleva encima un
        historial de repasos que no está en ninguna otra parte
        ([ADR-0017](adr/0017-puzzle-persistido-con-su-solucion-congelada.md)):
        es la decisión contraria a la de los patrones
        ([ADR-0008](adr/0008-patrones-deducidos-al-leer.md)), y el ADR explica
        por qué.
- [x] Sparring contra Stockfish limitado / Lc0 con Maia (**RF-4.3**, y solo
      RF-4.3: este ítem citaba además RF-4.2, que es el drill de aperturas y
      vive en el ítem siguiente con RF-4.4 — corregido el 2026-09-21).
      Hecho el 2026-09-21: `/training/sparring` para elegir rival y empezar y
      `/training/sparring/$sparringGameId` para jugar y retomar, cinco
      endpoints bajo `/sparring`, tabla `sparring_games` (migración
      `f3d9a1c47b58`) y las reglas puras de una partida —rehacerla desde sus
      jugadas, saber si acabó y por qué, y escribirla en PGN— en
      `lucia_core.sparring`. Las reglas que el texto del RF no fijaba están en
      la nota "Con qué reglas se cumplió RF-4.3" de
      [02-requerimientos.md](02-requerimientos.md).

      - **El motor pasa a mover y no solo a opinar**: `EngineBridge.play(board)`
        le pide la jugada que **haría** —y entonces respeta la fuerza que se le
        haya pedido, que es lo que lo convierte en rival y no en oráculo—,
        frente a `analyze`, que siempre contesta lo mejor que hay. Era la
        carencia que la nota técnica de RF-11 señalaba como compartida por
        RF-4.3, RF-4.4 y RF-11: **queda resuelta una vez para los tres**, y los
        otros dos heredan el camino hecho.
      - **Los dos rivales no se calibran igual, y la pantalla lo dice.**
        Stockfish se contiene con `UCI_LimitStrength`/`UCI_Elo` entre 1320 y
        3190 y piensa un segundo por jugada, porque lo que lo frena es el
        límite de fuerza y no el reloj. Lc0 con `maia-1500.pb.gz`
        (`MAIA_WEIGHTS`, ajuste nuevo, distinto de la red del análisis) no se
        contiene: imita a una persona de ~1500, así que su fuerza es la de la
        red cargada y no un número que se le pueda pedir —`engine_elo` solo
        existe con Stockfish y el formulario esconde el deslizador en vez de
        enseñar uno muerto— y se juega a **un solo nodo**, porque con más la
        búsqueda empieza a corregir a la red y se pierde justo lo que la hace
        humana. Medido en el portátil de desarrollo: ~1,15 s por jugada
        Stockfish calibrado y ~0,08 s Maia, que además abre con el Giuoco
        Piano.
      - **Aquí el servidor es el rival y el árbitro**, al revés que en el
        tablero de análisis, donde quien sabe de reglas es chess.js y la API
        solo custodia el árbol
        ([ADR-0013](adr/0013-analisis-de-partida-o-de-tablero.md)): para
        contestar hay que saber qué posición hay, así que la jugada de la
        persona se valida en el servidor y la respuesta del motor vuelve en la
        misma petición, porque son un solo turno. La partida se guarda como
        posición de partida más jugadas en UCI y todo lo demás —posición
        actual, PGN, final y su motivo— se deriva al servir, para que no haya
        dos versiones de la misma partida que puedan discrepar
        ([ADR-0018](adr/0018-sparring-en-su-propia-tabla-y-el-servidor-como-arbitro.md)).
      - **No cuenta en estadísticas ni en detección de patrones** (RF-3), por
        la misma frontera que un tablero de análisis sin publicar (RF-6.5):
        una partida contra un motor al que se le ha bajado la fuerza no dice
        nada del rendimiento real. Para estudiarla se abre como tablero desde
        su PGN (RF-6.6) y se analiza desde ahí (RF-6.9), que es el camino que
        ya existía; si quien juega decide que cuente, el paso es marcarla como
        partida propia (RF-6.5), un acto explícito y no un efecto colateral de
        haber entrenado.
      - **Sin reloj y sin barra de evaluación**, y con sub-navegación nueva
        dentro de Entrenamiento para las dos pantallas. Una partida de
        entrenamiento se interrumpe y se retoma por su URL tal como estaba,
        porque el estado vive en la base; la barra queda fuera por lo mismo que
        en los puzzles de RF-4.1: decir a cada jugada quién va ganando
        convierte la partida en un análisis asistido.
      - 26 tests nuevos —14 de API, uno de ellos contra Stockfish real, y 12
        del núcleo— más 6 del front.
- [x] Drill de aperturas (**RF-4.2**, y solo RF-4.2: este ítem citaba también
      RF-4.4 —"re-juega desde el error"—, que pasa a ser el ítem siguiente para
      que no se dé por cerrado junto a esto, igual que RF-6.5 se separó de los
      extras del tablero en la fase 2). Hecho el 2026-09-21: la pestaña
      "Aperturas" dentro de Entrenamiento y la pantalla `/training/drills`, tres
      endpoints bajo `/training/drills` —generar, la cola y jugar—, tabla
      `opening_drills` (migración `c7b2e9f05a31`) y las reglas puras de una
      línea —a quién le toca cada ply, qué se espera en él, qué contesta el
      rival y la notación SAN derivada al servir— en `lucia_core.drills`. Las
      reglas que el texto del RF no fijaba están en la nota "Con qué reglas se
      cumplió RF-4.2" de [02-requerimientos.md](02-requerimientos.md), y de
      dónde sale el material y qué es "peor" en
      [ADR-0019](adr/0019-el-drill-de-aperturas-se-construye-sobre-las-salidas-de-la-teoria.md).

      - **Un drill es una línea, no una posición.** Se repite desde la jugada 1
        jugando el bando propio, con la aplicación contestando por el rival
        hasta la última jugada, que es siempre propia. Es la diferencia con los
        puzzles de RF-4.1: una apertura no se olvida en una posición, se olvida
        como camino, y plantar al usuario justo antes de la salida le regalaría
        la parte que no recuerda.
      - **Las dos barajas comparten material y solo cambia el motivo.**
        "Salidas de la teoría" (RF-3.6) y "peores aperturas" (RF-3.2) se
        construyen igual —el camino propio de una partida, corregido en el
        punto donde se abandona el libro con la jugada más jugada por los
        maestros— y se recorren en el mismo bucle; `reason` es lo único que las
        separa después. Consecuencia buscada: **una apertura que va mal pero en
        la que nunca se abandona el libro no da drill**, porque ahí no hay
        ninguna jugada que se pueda enseñar como la que había que hacer.
      - **"Peor" se mide en puntos perdidos y no en porcentaje**:
        `games * (50 - score_percent) / 100`, y la baraja se ordena por ese
        daño. Un corte absoluto deja fuera los agujeros grandes, que sangran
        despacio y muchas veces. Medido sobre las 326 partidas del autor, el
        corte por porcentaje daba 3 líneas y ordenar por daño da 10. El único
        umbral que queda es de hábito, **3 partidas**
        (`MIN_GAMES_TO_DRILL`), la misma pregunta que ya se hace RF-3.6.
      - **Generar no sale a la red** y hereda la cobertura de RF-3.6: usa lo
        que la caché del explorador ya sepa ([ADR-0010](adr/0010-repertorio-con-red-y-cacheado.md)),
        así que mientras falte teoría la baraja crece cada vez que se refresca
        el repertorio y la pantalla lo dice en vez de dejar creer que no hay
        material. Con 150 posiciones traídas salían 49 salidas de teoría —la
        mayoría en los plies 2-3—, 10 drills y 42 posiciones por consultar.
        Por lo mismo **la línea no continúa más allá de la salida**, limitación
        conocida: seguir pediría posiciones que RF-3.6 nunca consulta.
      - **El servidor es el árbitro y no guarda progreso.** La línea no viaja
        al navegador mientras el drill está abierto —es la respuesta, y además
        diría qué va a contestar el rival—: el servidor comprueba jugada a
        jugada y solo al cerrarlo manda la línea entera, la misma regla de
        RF-4.1. Por dónde va la línea lo lleva la pantalla (`ply`), porque un
        drill se repite entero o no se repite. Y, como en los puzzles, esta
        pantalla tampoco tiene barra de evaluación.
      - **El repaso es el mismo SM-2 de los puzzles** (`lucia_core.training`):
        rendirse es fallar, recorrer la línea limpia es acertar y tropezar por
        el camino queda en medio. No hay un segundo algoritmo de repaso que
        mantener; el módulo deja de ser "las reglas de los puzzles" para ser
        "las reglas del repaso", con dos servicios que lo usan. Generar es un
        botón y es idempotente, con clave `(bando, línea)` y no la partida de
        origen: la gracia es que la misma línea se repite en muchas.
      - **El drill se guarda entero, con su línea y su motivo congelados** y
        sin enlace a la partida de la que salió, por lo mismo que el puzzle
        ([ADR-0017](adr/0017-puzzle-persistido-con-su-solucion-congelada.md)):
        lleva encima un historial de repasos que no está en ninguna otra parte,
        y volver a sincronizar o a refrescar el repertorio no puede
        llevárselo por delante.
      - **`Departure` (RF-3.6) creció dos campos** —`master_moves_uci` y
        `preceding_moves_uci`— que la comparación de repertorio no mira: el
        camino y la jugada en UCI solo se pueden componer mientras se recorre
        la partida, y recorrerla otra vez desde el drill sería hacer dos veces
        el mismo trabajo con el riesgo de que las dos pantallas no coincidan.
      - 23 tests nuevos —11 de API y 12 del núcleo— más 6 del front.
- [x] "Re-juega desde el error" (**RF-4.4**). Separado del ítem anterior el
      **2026-09-21**, al entregarse RF-4.2 —los dos compartían casilla y
      marcarla habría dado por cerrado algo que no lo estaba—, y cerrado ese
      mismo día: la pestaña "Re-jugar" dentro de Entrenamiento
      (`/training/replays`) con los errores propios que más caros salieron, el
      botón "Jugar desde aquí" en el visor, `GET /training/replays` —que solo
      lista y no crea nada—, un `origin` nuevo en `POST /sparring/games`, las
      columnas `origin_game_id` y `origin_ply` de `sparring_games` (migración
      `d5a81c6e3f04`) y la regla pura que saca la posición de un PGN,
      `board_at_ply`, en `lucia_core.sparring`. Las reglas que el texto del RF
      no fijaba están en la nota "Con qué reglas se cumplió RF-4.4" de
      [02-requerimientos.md](02-requerimientos.md), y por qué esto no es una
      tabla nueva ni mete RF-11 dentro de v1.0, en
      [ADR-0020](adr/0020-re-jugar-desde-el-error-es-sparring-desde-otra-posicion.md).

      - **Retomar es sparring desde otra posición**, no otra forma de jugar:
        misma tabla, mismos endpoints, misma pantalla de juego y mismo
        listado, donde una partida retomada se distingue con una insignia. Lo
        que este ítem daba por pendiente —que el motor **juegue** y no solo
        analice— lo había resuelto RF-4.3 con `EngineBridge.play`, y
        `starting_fen` ya era columna precisamente para esto; lo que se añade
        es de dónde sale la posición y de dónde salió la partida. Una partida
        retomada **tampoco cuenta** en estadísticas ni en patrones (RF-3), por
        la misma frontera que el sparring de RF-4.3.
      - **La lista de errores no se guarda**: se deduce de los análisis cada
        vez que se pregunta ([ADR-0008](adr/0008-patrones-deducidos-al-leer.md)),
        que es la decisión **contraria** a la de los puzzles y los drills
        ([ADR-0017](adr/0017-puzzle-persistido-con-su-solucion-congelada.md)).
        La diferencia es el estado propio: una posición desde la que re-jugar
        no se repasa, no vence y no acumula intentos, así que persistirla solo
        daría una segunda copia que envejece en cuanto se reanaliza la
        partida. Por lo mismo no hay botón de generar: la pestaña está llena
        en cuanto hay una partida analizada.
      - **Por HTTP se manda de qué partida y de qué jugada, nunca un FEN.** La
        posición la deriva el servidor del PGN que ya tiene (`board_at_ply`
        sobre `games.pgn`), y eso es deliberado: es lo que mantiene la
        frontera con **RF-11.1**, que sigue congelado fuera de v1.0 (ver la
        fase 6 en Post 1.0, actualizada con esto).
      - **Se retoma cualquier posición y con cualquier bando** desde el visor,
        que es una lectura generosa de "desde la posición del blunder": una
        apertura que va mal se rehace desde la jugada 6 y no desde la 24.
        Quién abre no es "las blancas" sino quien tenga el turno en esa
        posición. La pestaña sí se ciñe a los errores graves, los mismos que
        dan puzzle (`PUZZLE_CLASSIFICATIONS`) y ordenados por lo que costaron:
        la libertad está en el visor y la lista curada responde a "¿por dónde
        empiezo?".
      - **`origin_game_id` / `origin_ply` son procedencia, no dependencia**:
        `ON DELETE SET NULL` y sin cascada, porque borrar la partida de origen
        no invalida lo jugado —la posición vive en `starting_fen`, que es lo
        que hace la partida jugable—, solo deja de haber adónde volver.
      - **El formulario de dificultad pasa a ser compartido** por las tres
        pantallas desde las que se abre una partida contra el motor
        (`features/training/SparringSetupForm.tsx`). El inventario de RNF-11
        gana tres filas (101 a 103) y se cierran ocho arreglos en el mismo
        commit; ver [07-coherencia-ui.md](07-coherencia-ui.md).
      - 13 tests nuevos: 9 de API, 3 del núcleo y 1 del front.
- [x] Plan semanal de entrenamiento (**RF-4.5**). Hecho el 2026-09-21: la
      pestaña "Plan", que pasa a ser **la portada de Entrenamiento**, un solo
      endpoint de lectura `GET /training/plan`
      (`services/plan.py` + `routers/plan.py`) y las reglas puras de qué es una
      debilidad y qué se entrena con ella en `lucia_core.plan`. **Sin tabla y
      sin migración: es el único punto de RF-4 que no toca el modelo de
      datos.** Las reglas que el texto del RF no fijaba están en la nota "Con
      qué reglas se cumplió RF-4.5" de
      [02-requerimientos.md](02-requerimientos.md), y por qué el plan no se
      persiste y por qué el orden de las debilidades es editorial, en
      [ADR-0021](adr/0021-el-plan-semanal-se-deduce-y-el-orden-de-las-debilidades-es-editorial.md).

      - **Es la primera pantalla de la sección que no entrena nada.** Dice qué
        falla, con su número, y debajo los deberes que salen de ahí con su
        avance; las otras cinco son adónde manda. Por eso es la portada:
        `/training` deja de ser los puzzles y pasa a ser el plan, y los puzzles
        se mudan a `/training/puzzles` (`TrainingPage` → `PuzzlesPage`). Es el
        único cambio de comportamiento visible del ítem y está destacado como
        tal en el [CHANGELOG](../CHANGELOG.md).
      - **Cinco debilidades, una por cada cosa que RF-3 ya sabe mirar**, y cada
        una entra solo si pasa **su** umbral (`MIN_PHASE_WIN_PERCENT_LOST`,
        `MIN_MISTAKE_TYPE_SHARE`, `MIN_OPENING_POINTS_LOST`,
        `MIN_TIME_TROUBLE_SHARE`, `MIN_ACCURACY_DROP`): la fase donde se pierde
        ventaja (RF-3.3), el tipo de error que más pesa (RF-3.4), la apertura
        que más cuesta (RF-3.2), los apuros de reloj (RF-3.5) y la precisión
        que cae (RF-3.7). Enumerar las cinco siempre, las tenga o no, no
        ayudaría a decidir por dónde empezar.
      - **El orden es fijo por clase y no sale de los números**, y esto es la
        mitad de ADR-0021: cada debilidad se mide en su propia unidad —puntos
        de probabilidad, porcentaje de errores, puntos de marcador, porcentaje
        de partidas, puntos de precisión—, así que ordenarlas por magnitud
        sería inventar una escala común. De lo más estructural a lo más
        circunstancial, y la primera lleva la insignia "lo primero".
      - **Cada deber nace de una debilidad concreta y la lleva encima**
        (`_TASK_BY_WEAKNESS`, `reasons`): eso es lo que dice "generado a partir
        de las debilidades detectadas". Una debilidad sin entrenamiento posible
        no genera deber, y un deber sin motivo a la vista sería una cuota
        inventada. El objetivo es `min(MAX_WEEKLY_TARGETS, material
        disponible)` y sin material no hay tarea: pedir treinta puzzles cuando
        hay cuatro no es exigente, es falso.
      - **El plan no se guarda y nadie marca un deber a mano.** Se deduce en
        cada visita de las estadísticas de RF-3 y de las colas de RF-4, y lo
        hecho sale de fechas que la base ya tiene —`puzzles.last_reviewed_at`,
        `opening_drills.last_reviewed_at` y `sparring_games.created_at`—, así
        que entrenar en las otras pestañas es lo que mueve la barra. Es la
        misma decisión que los patrones
        ([ADR-0008](adr/0008-patrones-deducidos-al-leer.md)) y la lista de
        re-jugar ([ADR-0020](adr/0020-re-jugar-desde-el-error-es-sparring-desde-otra-posicion.md)),
        y la contraria a la de los puzzles y los drills
        ([ADR-0017](adr/0017-puzzle-persistido-con-su-solucion-congelada.md)).
      - **La semana empieza el lunes** (`week_start`), no "hace siete días":
        con una ventana móvil, lo entrenado el lunes dejaría de contar el
        martes siguiente y el avance bajaría solo, sin que nadie hiciera nada.
      - **Un plan vacío no es un fallo, y hay dos vacíos distintos**: sin
        partidas analizadas la pantalla manda a analizar, y con partidas
        analizadas y nada por encima de su umbral dice que no ha encontrado
        nada que destaque. Por eso la respuesta lleva sobre cuántas partidas se
        hizo el diagnóstico.
      - **Con esto queda cerrado RF-4 entero** (RF-4.1 a RF-4.5). La fase no:
        ver la cabecera y el ítem siguiente.
      - 37 tests nuevos —21 del núcleo, 6 de API y 10 del front— y un primitivo
        compartido nuevo, `components/ProgressBar.tsx`, más `formatPhase` subida
        a `lib/format.ts`. El inventario de RNF-11 gana las filas 104 a 106, con
        la 106 cerrada el mismo día; ver [07-coherencia-ui.md](07-coherencia-ui.md).
- [ ] Capa de ocupación (RF-7.1 a 7.7) en la pantalla de entrenamiento, que la
      fase 2 dejó pendiente de que esa pantalla existiera. **Es el único ítem
      que queda de la fase 3** desde el 2026-09-21, y no es de RF-4: las seis
      pantallas de entrenamiento ya existen —plan, puzzles, aperturas,
      re-jugar, antesala de sparring y partida de sparring— y **ninguna usa la
      capa**. Comprobado sobre el código ese mismo día: `OccupancyLayer` y
      `useOccupancy` solo se importan desde `features/viewer/GameViewerPage.tsx`
      y `features/board/BoardPage.tsx`. Las pantallas con tablero de RF-4
      renunciaron a propósito a la barra de evaluación —decir a cada jugada
      quién va ganando convierte el ejercicio en un análisis asistido—, así que
      al cerrarlo habrá que decidir en cuáles de ellas entra la capa y con qué
      sub-modo, que es lectura de la posición y no opinión del motor. Con ese
      ítem cerrado, la fase 3 cierra y le toca `0.5.0`.

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
(RF-4.3), que llegó el 2026-09-21 en la fase 3. **Las dos están entregadas**,
así que lo que le queda a RF-11 es solo suyo: arrancar de una posición elegida
con ventaja material y la segunda perilla de dificultad. Sigue fuera del
alcance de v1.0 —se planteó después del corte y esto no lo cambia—, solo que
ahora no lo bloquea nada.

**Y jugar desde una posición que no es la inicial también quedó resuelto** el
**2026-09-21**, con RF-4.4: `sparring_games.starting_fen` ya lleva posiciones
que no son la estándar, el PGN de esas partidas ya sale con `[SetUp "1"]` y el
turno de salida ya lo decide la posición. **RF-11.1 sigue entero fuera de
v1.0**, y comprobado sobre el código lo que le falta son dos cosas que ningún
requerimiento de 1.0 adelanta: la **posición inventada** —hoy la deriva siempre
el servidor del PGN de una partida propia ya guardada y por HTTP no se acepta
un FEN, a propósito
([ADR-0020](adr/0020-re-jugar-desde-el-error-es-sparring-desde-otra-posicion.md))—
y la **ventaja material como perilla** (RF-11.2), de la que no existe nada.
RF-11.3 tampoco está adelantado: una partida de sparring, retomada o no, no se
escribe en `games`, y publicarla sigue siendo el acto explícito de RF-6.5.

- [ ] Jugar contra el motor desde una posición inicial personalizada, eligiendo
      color y bando con ventaja (RF-11.1).
- [ ] Dificultad en dos perillas: fuerza del motor y ventaja material, cada una
      con su control y su explicación (RF-11.2).
- [ ] Guardar la partida jugada con su PGN (`SetUp`/`FEN`), analizable con RF-2
      y visible en el visor, pero fuera de estadísticas (RF-11.3).
