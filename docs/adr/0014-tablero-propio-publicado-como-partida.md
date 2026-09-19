# ADR-0014 · Un tablero marcado como "partida propia" se publica en el historial

**Estado:** aceptado · **Fecha:** 2026-09-18

## Contexto

RF-6.5 promete dos cosas: que un tablero de análisis **no** cuente en las
estadísticas ni en la detección de patrones (RF-3), y que sí cuente cuando el
usuario lo marque como "partida propia" —una OTB, una de otro club, una de un
torneo—. Hasta ahora solo estaba hecha la primera: la marca existía
(`boards.is_own_game`) y únicamente servía para distinguir esos tableros en el
listado.

Lo que faltaba no era quitar un filtro. Todas las agregaciones de RF-3 se
apoyan en columnas de `games` que un tablero no tiene: de qué color jugó el
usuario, cómo acabó, con qué rating, a qué ritmo, qué día y con qué apertura
([ADR-0013](0013-analisis-de-partida-o-de-tablero.md), Consecuencias). Un
tablero no sabe nada de eso: es una posición y un árbol de variantes.

Había que decidir dos cosas: **qué datos se le piden** a un tablero marcado, y
**por dónde entran** en RF-3.

Las opciones para lo segundo eran dos:

1. **Enseñar a RF-3 a leer tableros.** Añadir a `boards` las columnas que
   faltan y reescribir cada consulta de `services/stats.py` y
   `services/insights.py` para que lea la unión de `games` y los tableros
   marcados.
2. **Publicar el tablero como partida.** Al marcarlo, guardar además una fila
   de `games` con las jugadas del tablero, igual que ya hace la importación de
   PGN manual (RF-1.5) con una partida de torneo.

## Decisión

**La opción 2, con el mínimo de datos de RF-1.5.**

- Al marcar el tablero se piden **cuatro datos**: de qué color jugó el
  usuario, contra quién, cómo acabó (desde su punto de vista) y qué día. Con
  eso responden todas las preguntas de RF-3.
- **Rating, control de tiempo y "de competición" se quedan en hueco** —0,
  `"unknown"`, `False`—, los mismos que deja RF-1.5. La apertura se deduce de
  las jugadas con la tabla ECO propia, como en cualquier partida.
- **Las jugadas las manda el front en PGN** (`tree.ts::toPgn`), igual que al
  pedir el análisis: recorrer el árbol es cosa de chess.js.
- **La marca es el enlace**: `boards.own_game_id` apunta a la partida
  publicada y `is_own_game` se deduce de él. El booleano anterior desaparece.
- **El análisis del tablero cuenta como el de esa partida**: cuando el tablero
  está publicado, su `Analysis` lleva `game_id` **además** de `board_id`, y
  entra en el dashboard por `latest_analysis_ids` sin tocar esa consulta. Deja
  de contar en cuanto `analyzed_pgn` no coincide con lo que hay en el tablero.
- **Retirar la marca borra la partida publicada**, y borrar el tablero
  también.

Endpoints: `PUT /boards/{id}/own-game` (marcar, corregir datos y poner al día
las jugadas) y `DELETE /boards/{id}/own-game`. `PUT /boards/{id}` acepta un
`pgn` opcional, obligatorio cuando el tablero está publicado y cambia el
árbol.

## Razones

- **Ninguna consulta de RF-3 se entera.** Con la opción 1 habría que tocar el
  marcador, la tabla por control de tiempo, las partidas por mes, las
  aperturas, la precisión media, el reparto por fases, los tipos de error, los
  tramos de reloj y las tendencias —y acordarse de los tableros en cada
  consulta que se escriba a partir de ahora—. Con la opción 2 no cambió una
  sola línea de `services/stats.py` ni de `services/insights.py`.
- **No es un `Game` oculto.** ADR-0013 rechazó crear una partida por cada
  tablero analizado, porque metería filas que el dashboard cuenta, los filtros
  listan y el sincronizador podría pisar. Aquí es justo lo contrario: el
  usuario ha dicho que esa partida la jugó él, así que **quiere** que el
  dashboard la cuente y que el filtro por rival la encuentre. La fila no
  miente: dice lo mismo que diría el PGN de esa partida importado a mano. Y no
  la pisa nadie: `platform` es `"board"` y `platform_id` es el id del tablero.
- **Es la misma puerta que RF-1.5.** Una partida OTB entra hoy en LUCIA por
  `import_pgn`, con rating 0 y ritmo "unknown". Un tablero marcado como propio
  es la misma partida contada desde otro sitio, y darle otra forma haría que
  la misma partida se viera distinta según por dónde entró.
- **Cuatro datos y no más.** Pedir rating y ritmo dejaría dos campos que casi
  nadie rellena y que, mal rellenados, ensucian la línea de rating de las
  tendencias. Se deja el mismo hueco que RF-1.5 y se dice en pantalla antes de
  pulsar.
- **El resultado se pregunta desde el punto de vista del usuario** ("Gané",
  "Tablas", "Perdí") y no como "1-0": junto con el color, no hay forma de
  equivocarse de bando. Y su nombre no se escribe: se guarda su `username` de
  LUCIA, que es por donde casan las estadísticas.
- **Una sola marca.** Un booleano junto al enlace podría contradecirlo, y
  entonces el listado diría que el tablero cuenta y el dashboard no lo
  contaría. `is_own_game` se deduce del enlace y la API sigue exponiendo el
  mismo campo de siempre.
- **El análisis caduca en vez de mentir.** Un tablero se sigue editando
  después de analizarlo. Atribuir la clasificación de la jugada 12 analizada a
  otra jugada 12 sería meter un dato falso en el dashboard con toda la
  apariencia de bueno. Es la misma regla que ya avisa en pantalla
  (`matchAnalyzedLine`), aplicada a lo que se cuenta.
- **El PGN lo compone el cliente porque el árbol es suyo**, como en RF-6.7 y
  RF-6.9: la API guarda `tree_json` sin interpretarlo, y recorrerlo en el
  servidor daría dos sitios donde equivocarse.

## Consecuencias

- **`analyses.game_id` y `analyses.board_id` ya no son excluyentes.** La regla
  de ADR-0013 ("uno de los dos, nunca los dos") pasa a ser "al menos uno":
  `board_id` dice de dónde salieron las jugadas, `game_id` a qué partida se le
  atribuyen. El worker no cambia —`_load_pgn_to_analyze` sigue prefiriendo
  `analyzed_pgn`— y la exportación a PGN anotado (RF-5.5) empieza a funcionar
  también para estos tableros, porque ya encuentra su partida.
- **Guardar un tablero publicado exige mandar su PGN.** `PUT /boards/{id}`
  responde 422 si cambian las jugadas y no viene `pgn`. Es el precio de que la
  API no recorra el árbol; a cambio, la partida del historial nunca se queda
  atrasada en silencio.
- **Deshacer y rehacer arrastran la partida con ellos**, en la misma
  petición: cada fila de `board_versions` guarda además su PGN
  (`board_versions.pgn`, migración `d4b7e0c25a19`), que es el que mandó la
  pantalla al guardar esa versión. Sin esa columna el servidor no sabría cómo
  quedó el árbol —no lo recorre— y haría falta un segundo viaje desde el
  front. Las versiones anteriores a la columna no tienen PGN: volver a una
  desenlaza el análisis hasta el siguiente guardado.
- **La migración `a71c40f5d3e8` pierde las marcas existentes.** Un tablero
  marcado con el esquema anterior no trae rival, resultado ni fecha, y
  publicarlo obligaría a inventarlos. Hay que volver a marcarlo desde la
  pantalla, que ya los pide.
- **Las partidas publicadas salen bajo el control de tiempo "sin
  determinar"**, mezcladas con las importadas de un PGN. No entran en la línea
  de rating de las tendencias, que solo mira el ritmo más jugado
  (`_most_played_time_class` descarta `"unknown"`).
- **Encendió las claves foráneas de sqlite.** Publicar y retirar la marca
  mueve filas entre tres tablas, y al escribir la prueba de que borrar un
  tablero se lleva lo suyo se vio que `PRAGMA foreign_keys` estaba apagado en
  toda la aplicación: ningún `ON DELETE` del esquema se ejecutaba, ni el de
  esta decisión ni los de ADR-0012 y ADR-0013. Lo enciende
  `db/base.py::create_db_engine`, y con él salió a la luz que
  `analyzed_moves.analysis_id` no tenía cascada (migración `c8f3a2b91e47`):
  borrar un tablero analizado fallaba. Las migraciones siguen corriendo con el
  pragma apagado, porque alembic recrea tablas enteras para cambiarlas en
  sqlite.
- **Qué NO fija.** Ni que los datos tengan que ser siempre cuatro —añadir
  rating y ritmo opcionales no toca nada más que el formulario y la fila—, ni
  que el PGN deba venir del cliente si algún día el servidor aprende a
  recorrer el árbol.

## Ver también

- RF-6.5 en [02-requerimientos.md](../02-requerimientos.md), con la nota de
  cómo se cumplió.
- [ADR-0013](0013-analisis-de-partida-o-de-tablero.md), cuya consecuencia
  pendiente cierra esta decisión.
- `apps/api/lucia_api/services/own_games.py` (publicar, retirar y enlazar),
  `apps/api/lucia_api/routers/boards.py` (los dos endpoints),
  `apps/api/lucia_api/services/pgn_import.py` (la misma puerta de RF-1.5) y
  `apps/web/src/features/board/OwnGamePanel.tsx` (el formulario).
- Migración `a71c40f5d3e8`.
