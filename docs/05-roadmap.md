# 05 · Roadmap

## Fase 0 · Cimientos (esta)

- [x] Esqueleto del monorepo, documentación, requerimientos, stack.
- [ ] Añadir sub-módulos Stockfish y Lc0; `scripts/setup-engines.sh` funcionando en Fedora.
- [ ] `uv sync` + `pnpm install` limpios; CI verde con tests vacíos.

## Fase 1 · MVP "Game Review propio" (P0)

- [ ] `lucia-chesscom`: descargar perfil + archivos mensuales, parsear PGN y relojes, guardar en SQLite. Sync incremental.
- [ ] `lucia-core`: `EngineBridge` con Stockfish; `GameAnalyzer` ply a ply con MultiPV; caché por FEN.
- [ ] `MoveClassifier` + `Accuracy` con tests contra partidas de referencia.
- [ ] API: `/sync`, `/games`, `/analysis` (+ WebSocket de progreso), `/engines/config`.
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
