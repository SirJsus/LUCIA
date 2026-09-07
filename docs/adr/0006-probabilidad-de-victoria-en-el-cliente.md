# ADR-0006 · La probabilidad de victoria se calcula también en el cliente

**Estado:** aceptado · **Fecha:** 2026-09-06

## Contexto

RF-5.2 y RF-6.2 piden una barra de evaluación en **probabilidad de victoria**
(no en centipawns) tanto en el visor de partidas como en el tablero de
análisis. Los dos sitios sacan el número de fuentes distintas:

- El **visor** lee un análisis ya guardado: `analyzed_moves.win_percent_after`
  lo calculó el backend con `lucia_core.accuracy.win_percent`, que delega en
  `Score.wdl(model="lichess")` de `python-chess` (ver ADR-0003: no
  reimplementamos lo que la librería ya trae).
- El **tablero de análisis** consulta `POST /analysis/position`, que devuelve
  las líneas del motor tal cual las da el motor: `score_cp` o `score_mate`, sin
  ningún derivado. No hay win% que mostrar.

Las opciones eran añadir `win_percent` a `EngineLineOut` (una sola
implementación, en el backend) o calcularlo en el cliente a partir de los
centipawns que ya llegan.

## Decisión

Calcularlo en el **cliente**: `whiteWinPercentFromScore` en
`apps/web/src/lib/score.ts` replica el modelo de Lichess
(`1000 / (1 + exp(-0.00368208 · cp))` con los centipawns acotados a ±1000) con
el mismo redondeo que `python-chess`, y `EvalBar` recibe siempre un porcentaje
ya resuelto, venga del análisis guardado o del motor en vivo.

Con una excepción deliberada: un **mate anunciado** satura a 100 % / 0 % en el
cliente, mientras que el modelo de Lichess lo trata como una ventaja grande en
centipawns y se queda en ~99,9 % / 0,1 %.

## Razones

- El contrato de la API no cambia: `/analysis/position` sigue devolviendo lo
  que dice el motor, sin interpretaciones. Un derivado en la respuesta obliga a
  versionarlo y a regenerar tipos cada vez que se toque el modelo.
- La réplica es una fórmula de una línea y dos constantes, sin estado. El
  modelo de Lichess **ignora el ply**, así que el cliente no necesita saber en
  qué jugada está para dar el mismo número.
- La paridad con el backend queda fijada por tests
  (`apps/web/src/lib/__tests__/score.test.ts`), no por buena fe.
- Llenar la barra del todo cuando hay mate dice mejor lo que pasa que dejar una
  rendija: la barra es una lectura de un vistazo, no un dato estadístico.

## Consecuencias

- El mismo modelo vive en dos sitios (`lucia_core/accuracy/__init__.py` y
  `apps/web/src/lib/score.ts`). Si se cambia de modelo —o se hace configurable—
  hay que cambiarlo en ambos; cada lado tiene un comentario que apunta al otro.
- Divergencia conocida y acotada: con mate a la vista, el visor puede mostrar
  99,9 % donde el tablero de análisis muestra 100 %. Con evaluación en
  centipawns los dos coinciden exactamente.
- Si aparece un tercer consumidor del win% (por ejemplo, RF-10 llevando las
  alternativas del motor al visor y a los puzles) o el modelo deja de ser una
  constante, la salida es mover el cálculo a la API añadiendo el campo a
  `EngineLineOut`: eso sería un ADR nuevo que reemplace a este.
