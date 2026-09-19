# ADR-0013 · Un análisis cuelga de una partida o de un tablero, en la misma tabla

**Estado:** aceptado · **Fecha:** 2026-09-18

## Contexto

RF-6.9 pide analizar el tablero de análisis completo en background, "con
clasificación de jugadas y precisión como en RF-2". Eso es exactamente lo que
ya hace el análisis de una partida: recorrer una secuencia de jugadas,
evaluar cada posición con el motor, clasificar y guardar `analyzed_moves` y
las precisiones ([03-arquitectura.md § flujo 2](../03-arquitectura.md)).

Lo único distinto es de dónde salen las jugadas. Una partida las tiene en
`games.pgn` y no cambia nunca; un tablero las tiene en un árbol de variantes
que vive como JSON opaco, que solo el front sabe recorrer (chess.js), y que
**se sigue editando después de analizarlo**.

Las opciones eran tres:

1. **Tabla aparte** (`board_analyses` + `board_analyzed_moves`) para los
   análisis de tablero.
2. **Misma tabla**, con `analyses.game_id` o `analyses.board_id` según de qué
   cuelgue.
3. **Crear un `Game` oculto** por cada tablero analizado y reutilizar todo
   tal cual.

## Decisión

**La opción 2.** `analyses.game_id` y `analyses.board_id` son las dos
opcionales y se llena **exactamente una**: partida (RF-2) o tablero (RF-6.9).
El worker, `run_analysis`, `analyzed_moves`, el WebSocket de progreso y la
caché de posiciones son los mismos para las dos.

Va con ella:

- **`run_analysis` recibe el PGN**, no un `Game`. Quién lo saca es el worker
  (`_load_pgn_to_analyze`): `analyzed_pgn` si es de tablero, `games.pgn` si
  es de partida.
- **El PGN de un tablero lo manda el front** (`POST /boards/{id}/analysis`
  con lo que devuelve `toPgn`) y se guarda en `analyses.analyzed_pgn`.
- **Se analiza la línea principal**, no el árbol entero.
- **Los análisis de tablero no entran en las estadísticas**:
  `latest_analysis_ids` filtra por `game_id` no nulo.

## Razones

- **Es el mismo trabajo, con el mismo resultado.** Con la opción 1 habría dos
  copias de `analyzed_moves` y, con ellas, dos versiones de todo lo que lee
  de esa tabla: el detalle del análisis, el rescate de alternativas desde
  `position_cache`, la exportación a PGN anotado, los momentos críticos. Cada
  arreglo futuro habría que hacerlo dos veces y una de las dos se olvidaría.
- **Un `Game` oculto mentiría en todas partes.** La opción 3 mete filas en la
  tabla que el dashboard cuenta, los filtros listan y el sincronizador podría
  pisar. Habría que excluirlas de cada consulta, que es más trabajo que
  excluir los análisis en el único sitio por donde pasan todos.
- **Una columna opcional más es un coste local.** El precio de la opción 2 es
  la regla "uno de los dos, nunca los dos", que se declara en el modelo, en
  el esquema de respuesta y en la migración. A cambio, nada más en la
  aplicación se entera.
- **`analyzed_pgn` solo en los tableros, porque solo ellos cambian.** Una
  partida tiene su PGN en `games.pgn` y guardarlo otra vez sería duplicar. Un
  tablero, en cambio, se edita después de analizarlo: sin registrar qué se
  analizó, la pantalla pegaría la clasificación de la jugada 12 sobre otra
  jugada 12 distinta, con la misma apariencia de dato bueno. Con él,
  `matchAnalyzedLine` empareja mientras coincida y avisa en cuanto deja de
  coincidir.
- **El PGN lo compone el cliente porque el árbol es suyo.** La API guarda
  `tree_json` sin interpretarlo, y duplicar en el servidor las reglas de
  ajedrez para recorrerlo daría dos sitios donde equivocarse — es la misma
  razón por la que `fromPgn` vive en `tree.ts` (flujo 8).
- **La línea principal y no todo el árbol**: las variantes son tanteos, y
  analizarlas multiplicaría el tiempo de motor por algo que el usuario no
  está mirando. Para una variante concreta ya está el motor en vivo de
  RF-6.2.

## Consecuencias

- **Pendiente conocido —resuelto el mismo día por
  [ADR-0014](0014-tablero-propio-publicado-como-partida.md), que publica el
  tablero marcado como una fila de `games` y relaja a "al menos una" la regla
  de las dos columnas—: un tablero marcado como "partida propia" seguía sin
  contar en las estadísticas**, que es lo que RF-6.5 promete. Excluirlos hoy
  es lo correcto —lo contrario metería posiciones inventadas en el
  dashboard—, pero incluirlos mañana no es quitar el filtro de
  `latest_analysis_ids`: todas las agregaciones de RF-3 se apoyan en columnas
  de `games` que un tablero no tiene (color del usuario, resultado, rating,
  control de tiempo, fecha, apertura). Hacerlo de verdad exige decidir antes
  qué significa un tablero propio para cada una de esas preguntas. Queda
  anotado en RF-6.9 en
  [02-requerimientos.md](../02-requerimientos.md).
- **`analyses.game_id` es nullable**, así que cualquier consulta nueva sobre
  la tabla tiene que decir de qué lado está. Las que ya existían pasan por
  `latest_analysis_ids` o por un `game_id` concreto, y por eso no cambiaron.
- **La migración `5ce9943fe2dc` recrea la tabla** (`batch_alter_table`):
  SQLite no sabe cambiar la nulabilidad de una columna ni añadir una clave
  foránea después. Las filas existentes son todas de partidas y quedan con
  `board_id` y `analyzed_pgn` en nulo.
- **Borrar un tablero borra sus análisis** (`ondelete="CASCADE"`). Es lo
  esperado: sin el tablero, esas clasificaciones no describen nada. *(Esa
  cascada no llegó a ejecutarse hasta
  [ADR-0014](0014-tablero-propio-publicado-como-partida.md), que encendió
  `PRAGMA foreign_keys` en sqlite —`db/base.py::create_db_engine`— y añadió la
  que le faltaba a `analyzed_moves.analysis_id`, migración `c8f3a2b91e47`.)*
- **Exportar a PGN anotado (RF-5.5) sigue siendo solo de partidas**, porque
  relee el PGN original de `games`. Extenderlo a tableros es trabajo aparte:
  el material ya está, la fuente del texto sería `analyzed_pgn`.
- **Qué NO fija.** Ni que el análisis de tablero tenga que ser de la línea
  principal para siempre, ni que el PGN deba venir del cliente si algún día
  el servidor aprende a recorrer el árbol. Cambiar cualquiera de las dos
  cosas no toca el esquema.

## Ver también

- RF-6.9 en [02-requerimientos.md](../02-requerimientos.md), con la nota de
  cómo se cumplió y el pendiente de RF-6.5.
- [03-arquitectura.md](../03-arquitectura.md): flujo 2 y el modelo de datos.
- `apps/api/lucia_api/routers/boards.py` (`POST /boards/{id}/analysis`),
  `apps/api/lucia_api/worker/__init__.py` (`_load_pgn_to_analyze`),
  `apps/api/lucia_api/services/analysis.py` (`run_analysis`),
  `apps/api/lucia_api/services/insights.py` (`latest_analysis_ids`) y
  `apps/web/src/features/board/tree.ts` (`matchAnalyzedLine`).
- Migración `5ce9943fe2dc`.
