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
      dependencias nuevas. Pendiente de este bloque: caché por FEN (RF-2.7,
      necesita `position_cache` en BD), Lc0 como segundo motor (RF-2.6),
      categoría "book" (necesita `openings/`), MultiPV real en la
      clasificación (RF-2.8, momentos críticos).
- [ ] API: `/games`, `/analysis` (+ worker, WebSocket de progreso, `position_cache`, usando `lucia-core` como librería), `/engines/config` (`/sync` ya está, ver arriba).
- [ ] Web: lista de partidas, visor con tablero + clasificaciones + gráfico de eval, análisis en vivo.
- [ ] Dashboard básico: ratings, W/D/L, rendimiento por apertura y por fase.
- [ ] Tablero de análisis, núcleo (RF-6.1 a 6.5): crear desde inicial / FEN / PGN / editor de posición, análisis en vivo, árbol de variantes (ramas, promover, borrar), guardar / listar / eliminar tableros, independientes del historial y de las estadísticas.

## Fase 2 · Insight (P1)

- [ ] Lc0 integrado como segundo motor; vista de discrepancias Stockfish vs Lc0.
- [ ] Extractores de patrones: errores por tipo, *time trouble*, momentos críticos.
- [ ] Comparación de repertorio con Lichess Explorer.
- [ ] Tendencias temporales.
- [ ] Tablero de análisis, extras (RF-6.6 a 6.9): abrir partida importada como copia desacoplada, importar / exportar PGN con variantes y comentarios, auto-guardado con deshacer / rehacer, análisis completo en background bajo demanda.
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
