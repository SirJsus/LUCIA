# ADR-0007 · Las alternativas de una jugada se guardan como JSON en su fila, y las de los análisis viejos salen de la caché

**Estado:** aceptado · **Fecha:** 2026-09-08

## Contexto

RF-10.1 pide persistir las N mejores líneas de cada posición analizada, no solo
la mejor, para que el visor pueda enseñar las alternativas de cada jugada
(RF-10.2) y para que los puzzles de RF-4.1 puedan aceptar respuestas
equivalentes (RF-10.3). Hasta ahora `analyzed_moves` guardaba una sola
`best_move_uci` por jugada aunque el análisis se hubiera corrido con MultiPV: el
resto del MultiPV se calculaba, se usaba para clasificar y se tiraba.

Dos preguntas, con alternativas reales cada una:

1. **Dónde ponerlas.** Una tabla normalizada (`analyzed_move_lines`, una fila
   por línea, con `rank`, `score_cp`, `score_mate`, `pv_uci`) o una columna JSON
   en la fila de la jugada. Con MultiPV 3 y partidas de 80 plies, la tabla
   normalizada multiplica por tres el número de filas de la parte que más crece
   de la base.
2. **Qué hacer con los análisis ya hechos.** Una migración de datos que los
   rellene, dejarlos sin alternativas para siempre, o reconstruirlas al vuelo.
   Lo relevante es que el dato **no se había perdido**: `position_cache`
   (RF-2.7) guarda todas las líneas del MultiPV indexadas por FEN, motor, red,
   límite y MultiPV, precisamente las que produjeron esas clasificaciones.

## Decisión

**Una columna JSON, `analyzed_moves.alternatives_json`**, con la lista de líneas
de la posición **anterior** a la jugada, de mejor a peor, en el **mismo formato
serializado** que `position_cache.lines_json` (`score_cp`, `score_mate`, `pv`
en UCI, puntuación desde el punto de vista de las blancas). Un único
`_serialize_line` escribe los dos sitios.

La notación **SAN no se persiste**: depende de la posición, y la posición ya
está en `fen_before`. Se deriva al servir (`engine_lines_from_serialized`).

**Los análisis anteriores a RF-10 no se migran.** La columna es *nullable*, y
`NULL` significa "este análisis es de antes", distinto de `[]` ("el motor no
propuso nada"). `GET /analysis/{id}` intenta rellenarlos leyendo
`position_cache` (`alternatives_from_cache`), y solo cuando la clave coincide
**exactamente**. Lo que no coincide se sirve vacío, y el visor lo dice.

## Razones

- Las líneas de una jugada no se consultan nunca sueltas: se leen enteras, con
  la jugada, o no se leen. Una tabla normalizada añade filas y un `JOIN` a la
  consulta más caliente de la aplicación para dar exactamente el mismo objeto.
- El formato compartido con `position_cache` es lo que hace posible el segundo
  punto sin código de traducción: una posición cacheada **es** ya una lista de
  alternativas. Si los dos formatos divergieran, esto dejaría de funcionar.
- No guardar la SAN evita tener la misma jugada escrita dos veces y, con ello,
  la posibilidad de que una contradiga a la otra. Derivarla cuesta un
  `chess.Board(fen)` por jugada al servir un análisis, no por petición de
  usuario en un bucle.
- Migrar los datos viejos habría sido escribir un backfill que hace exactamente
  la misma consulta que hace el router, una sola vez y con el riesgo de
  equivocarse en silencio sobre miles de filas. Leerlo al servir es reversible:
  si mañana se decide rellenar, la consulta ya está escrita y probada.
- El coste de no encontrarlo en la caché es bajo y honesto: la pantalla vuelve a
  lo que ese análisis sí guardó —una flecha— y explica por qué.

## Consecuencias

- **Buscar dentro de las líneas es SQL sobre JSON.** Cuando RF-2.8 (momentos
  críticos con MultiPV real) o RF-10.3 (puzzles con respuestas equivalentes)
  quieran preguntar "en qué posiciones había tres jugadas igual de buenas",
  tendrán que hacerlo con `json_extract` o en Python, no con un `WHERE` sobre
  columnas. Si esa consulta se vuelve frecuente o lenta, la salida es
  normalizar, y eso sería un ADR nuevo que reemplace a este.
- **La respuesta para un análisis viejo puede cambiar con el tiempo.** Si se
  purga `position_cache`, o si cambia la configuración efectiva del motor con el
  que se corrió (otra red de Lc0, otra profundidad), sus alternativas dejan de
  aparecer. No es un fallo: es que el dato solo estaba prestado. Los análisis
  hechos desde RF-10 no dependen de la caché.
- **Los dos formatos quedan atados.** Tocar `_serialize_line` cambia a la vez lo
  que se escribe en `position_cache` y en `alternatives_json`, y romper esa
  simetría rompe `alternatives_from_cache`. Está dicho en el docstring de la
  función y en el de la columna.
- La API sirve las alternativas con el mismo `EngineLineOut` que
  `POST /analysis/position`, así que el visor y el tablero de análisis dibujan
  las mismas flechas y la misma lista de líneas sin adaptadores de por medio
  (RNF-11).

## Ver también

- RF-10 en [02-requerimientos.md](../02-requerimientos.md), RF-2.7 (caché de
  posiciones) y RF-2.8 (momentos críticos).
- El modelo de datos y el flujo de análisis en
  [03-arquitectura.md](../03-arquitectura.md).
- `apps/api/lucia_api/services/analysis.py` (`_serialize_line`,
  `alternatives_from_cache`, `engine_lines_from_serialized`),
  `apps/api/lucia_api/db/models.py` (`AnalyzedMove.alternatives_json`) y la
  migración `7a1c4e9d2b30`.
