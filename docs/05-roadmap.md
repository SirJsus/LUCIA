# 05 · Roadmap

> Las fases 0 a 4 son el camino hacia **v1.0.0**: cubren todo el alcance
> congelado en [docs/02-requerimientos.md](02-requerimientos.md). Cuando se
> marquen todas sus casillas, `versionador` propone el corte de 1.0.0. Fases
> agregadas después de eso van bajo [Post 1.0](#post-10-futuro), al final.

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
      |---|---|---|
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
- [ ] Extractores de patrones: errores por tipo, *time trouble*, momentos
      críticos (RF-2.8, con MultiPV real en la clasificación) y "eval al salir
      de la apertura" (lo que falta de RF-3.2).
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

- [ ] Puzzles desde mis errores con repetición espaciada.
- [ ] Sparring contra Stockfish limitado / Lc0 con Maia.
- [ ] Drill de aperturas; "re-juega desde el error".
- [ ] Plan semanal de entrenamiento.

## Fase 4 · Pulido y distribución

- [ ] Ocupación del tablero, extras (RF-7.8 y 7.9): recordar sub-modo y filtros entre sesiones; "casillas críticas según motor" superponiendo las casillas más frecuentes en las mejores líneas de Stockfish.
- [ ] Explicaciones en lenguaje natural de errores.
- [ ] Empaquetado (Docker, posiblemente Tauri).
- [ ] macOS / Windows.

## Post 1.0 (futuro)

Ideas y fases que surjan después de publicada v1.0.0, o que se decida sacar
del alcance original antes de esa fecha. Se numeran como Fase 5 en adelante.

*(vacío por ahora)*
