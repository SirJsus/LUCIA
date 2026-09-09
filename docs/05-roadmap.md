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

## Fase 1 · MVP "Game Review propio" (P0)

- [x] `lucia-chesscom`: descargar perfil (RF-1.1) + archivos mensuales (RF-1.2),
      parsear PGN y relojes, guardar en SQLite vía Alembic (`players`, `games`,
      `sync_state`). Sync incremental (RF-1.3) e idempotente (upsert por
      `uuid`), con backoff en 429 (RF-1.4). Probado con `respx` y en vivo
      contra la API real de chess.com. Endpoint `POST /sync` expuesto.
      Pendiente de este bloque: RF-1.5 (importar PGN manual, P1).
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
      tests con distinto event loop. Pendiente: filtros de `/games` por
      apertura, rango de fechas y rival específico.
- [x] Web: lista de partidas con filtros y paginación, visor con tablero
      (chessground), jugadas clasificadas, gráfico de evaluación (en
      probabilidad de victoria) y navegación con teclado; análisis en vivo con
      barra de progreso por WebSocket. Pantalla de motores con la
      configuración **editable** (RF-5.4: hilos, hash, profundidad, MultiPV;
      la ruta del binario queda en solo lectura a propósito — aceptarla por
      HTTP sería ejecución arbitraria de comandos). Tema claro/oscuro.
      Tipos TS generados desde el OpenAPI real (`make types`), con
      verificación en CI de que no se desincronizan. 10 tests de front.
      Pendiente: reordenar/explorar variantes desde el visor (RF-5.2),
      exportar PGN anotado (RF-5.5).
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
      propia. 17 tests del árbol de variantes. Pendiente: editor de posición
      pieza a pieza (RF-6.1 permite FEN, que cubre el caso), deshacer/rehacer
      explícito (RF-6.8).

## Fase 2 · Insight (P1)

- [x] Lc0 integrado como segundo motor (RF-2.6); vista de discrepancias
      Stockfish vs Lc0. Nunca había llegado a funcionar: `EngineBridge` le
      mandaba la opción `Hash`, que Lc0 no soporta, y abortaba la conexión —
      ahora las opciones genéricas se filtran contra las que declara cada
      motor (esto además cumple RNF-9: enchufar otro motor UCI no necesita
      tocar código). El límite se mide en nodos para Lc0 y en profundidad
      para Stockfish, porque en MCTS la profundidad es un promedio del árbol
      y pedir una concreta cuesta un número imprevisible de evaluaciones.
      Endpoint `GET /analysis/compare` y panel en el visor con las jugadas
      donde los motores no coinciden.
      **Sobre el rendimiento de Lc0** (medido en un portátil con i7 y GTX
      1060). El backend y la red deciden si sirve o no:

    | Red | Backend | Velocidad |
    | --- | --- | --- |
    | grande (transformer, 313 MB) | CPU/BLAS | 2,5 nodos/s |
    | grande (transformer) | OpenCL | **no soportada** |
    | T74 convolucional (6 MB) | OpenCL | ~4.000 nodos/s |
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
        2026-09-08, en esta misma fase. Sigue pendiente "explorar variantes del
        motor desde cualquier posición" en el visor, que es el ítem de RF-6.6
        (abrir una partida importada como copia desacoplada). Hasta que ese se
        marque, RF-5.2 no está entregado del todo.
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
      [docs/07-coherencia-ui.md](07-coherencia-ui.md), cuyo inventario de
      incumplimientos quedó **vacío** el 2026-09-08). El tablero de análisis se
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
- [ ] Extractores de patrones: errores por tipo, *time trouble*, momentos
      críticos (RF-2.8, con MultiPV real en la clasificación) y "eval al salir
      de la apertura" (lo que falta de RF-3.2).

      Va junto con el ítem de RF-10 de más arriba: las varias líneas por
      posición que RF-2.8 necesita para distinguir "jugada única" de "tres
      alternativas igual de buenas" son el mismo material que RF-10.1 tiene que
      persistir. Hacerlos por separado significa recorrer dos veces el flujo de
      análisis.
- [ ] `lucia_core.openings`: tabla ECO (chess-openings de Lichess, CC0) para
      clasificar aperturas sin depender de lo que reporte chess.com, y con
      ella la categoría "book" de `classify_move` (lo que falta de RF-2.2).
- [ ] Comparación de repertorio con Lichess Explorer (RF-3.6).
- [ ] Importar PGN manual de otras fuentes —OTB, lichess— al historial (RF-1.5).
- [ ] Filtros de `/games` por apertura, rango de fechas y rival (lo que falta
      de RF-5.3; con cientos de partidas ya se nota).
- [ ] Tendencias temporales (RF-3.7).
- [ ] Tablero de análisis, extras (RF-6.6 a 6.9): abrir partida importada como
      copia desacoplada (esto también cubre "explorar variantes desde el
      visor", RF-5.2), importar / exportar PGN con variantes y comentarios,
      auto-guardado con deshacer / rehacer, análisis completo en background
      bajo demanda, y editor de posición pieza a pieza (lo que falta de
      RF-6.1; hoy se puede partir de un FEN, que cubre el caso).
- [ ] Capa de ocupación del tablero (RF-7.1 a 7.7): sub-modo mapa de calor, sub-modo cobertura directa del turno, inspección por casilla, piezas colgadas, rayos X aparte y clavadas marcadas, reglas de conteo (rey, peones en diagonal, al paso). Cálculo en cliente con chess.js, activable en visor, tablero de análisis y entrenamiento.
- [ ] Exportar PGN anotado.

## Fase 3 · Entrenamiento (P1/P2)

- [ ] Puzzles desde mis errores con repetición espaciada, aceptando como buena
      cualquier jugada equivalente y no solo la única del motor (RF-4.1 con
      RF-10.3, que necesita las líneas persistidas en la fase 2).
- [ ] Sparring contra Stockfish limitado / Lc0 con Maia.
- [ ] Drill de aperturas; "re-juega desde el error".
- [ ] Plan semanal de entrenamiento.

## Fase 4 · Pulido y distribución

- [ ] Ocupación del tablero, extras (RF-7.8 y 7.9): recordar sub-modo y filtros entre sesiones; "casillas críticas según motor" superponiendo las casillas más frecuentes en las mejores líneas de Stockfish.
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
cuenta para el progreso hacia 1.0.0. Depende de dos cosas que sí son alcance de
1.0 y hay que tener antes: el editor de posición pieza a pieza (RF-6.1, fase 2)
y el sparring contra motor con fuerza calibrada (RF-4.3, fase 3).

- [ ] Jugar contra el motor desde una posición inicial personalizada, eligiendo
      color y bando con ventaja (RF-11.1).
- [ ] Dificultad en dos perillas: fuerza del motor y ventaja material, cada una
      con su control y su explicación (RF-11.2).
- [ ] Guardar la partida jugada con su PGN (`SetUp`/`FEN`), analizable con RF-2
      y visible en el visor, pero fuera de estadísticas (RF-11.3).
