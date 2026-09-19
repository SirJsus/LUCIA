# ADR-0008 · Los patrones de juego se deducen al leer, no se persisten ni se vuelve a llamar al motor

**Estado:** aceptado · **Fecha:** 2026-09-09

## Contexto

RF-2.8 (momentos críticos), RF-3.4 (tipo de error), RF-3.5 (gestión de tiempo)
y la mitad que faltaba de RF-3.2 (evaluación al salir de la apertura) son
lecturas sobre partidas **ya analizadas**: qué posiciones decidieron la partida,
por qué se falló, con cuánto reloj, con qué evaluación se salió del repertorio.

Todo lo que necesitan estaba ya en la base cuando se plantearon:

- la clasificación de cada jugada y su probabilidad de victoria antes y después
  (RF-2.2, RF-2.3),
- la fase de cada jugada (RF-3.3),
- las alternativas del motor en la posición previa (RF-10.1, con respaldo en
  `position_cache` para los análisis anteriores — [ADR-0007](0007-alternativas-por-jugada-json-y-cache.md)),
- y los relojes por jugada que trae chess.com (RF-1.2, `games.clocks_json`).

Las opciones eran tres: (1) calcular los patrones durante el análisis y
persistirlos en tablas propias (`critical_moments`, `mistake_types`); (2)
calcularlos al servir, sobre lo guardado; (3) volver a preguntar al motor con
MultiPV alto para decidirlos con más información que la que quedó guardada.

## Decisión

**Se calculan al servir, en memoria, sobre lo que el análisis ya guardó.** No
hay tabla nueva, ni migración, ni columna nueva, ni una segunda pasada del
motor.

Las reglas viven en `packages/core/lucia_core/insights/` —son reglas de ajedrez
y de lectura de partidas, no consultas a una base—, y `apps/api` solo pone el
material: `services/insights.py` carga las jugadas con su fase, su reloj y sus
alternativas y las convierte en `MoveContext`, el tipo que el núcleo sabe leer.

Los momentos críticos salen en `GET /analysis/{id}`, que es donde se miran —una
partida concreta, los dos bandos—, y los patrones agregados en
`GET /stats?username=…`, que solo mira las jugadas del jugador.

## Razones

- **Las partidas ya analizadas entran igual.** Con la opción (1) los patrones
  solo existirían para lo analizado a partir de hoy, o habría que re-analizar
  —horas de motor— o escribir un backfill. Aquí el historial completo tiene
  momentos críticos desde el primer despliegue.
- **Las reglas van a cambiar.** Son umbrales sobre gustos ajedrecísticos, no
  hechos: "10 puntos de diferencia entre la primera y la segunda línea" es una
  decisión revisable, como los umbrales de `classification` y de `phases`. Un
  patrón persistido es un patrón fosilizado: cambiar el umbral obligaría a
  recalcular toda la base. Deducido al leer, cambiar el número basta.
- **Es barato.** El trabajo es recorrer las jugadas de una partida (decenas)
  o las del jugador en sus partidas analizadas (miles), sin E/S más allá de la
  consulta que ya se hacía. Nada que ver con el coste de una llamada al motor,
  que es lo que la opción (3) pagaría por cada visita a una pantalla.
- **Un dato derivado que se guarda es un dato que puede contradecir a su
  origen.** Si mañana se re-analiza una partida con otro motor, un
  `critical_moments` persistido seguiría hablando del análisis viejo.
- **La opción (3) además daría respuestas distintas cada vez**, contra RNF-3
  (reproducibilidad): el mismo momento crítico dependería de con qué esfuerzo
  se preguntó al motor esta vez, no del análisis que el usuario está mirando.

## Consecuencias

- **El coste crece con el historial.** `GET /stats?username=…` carga las jugadas
  del jugador en todas sus partidas analizadas para pasárselas a los tres
  extractores; se cargan **una sola vez** por petición precisamente por eso. Si
  con un historial grande la petición se vuelve lenta, la salida es cachear el
  resultado por usuario (invalidando al terminar un análisis) y, solo si eso no
  basta, materializarlo — y eso sería un ADR nuevo que reemplace a este.
- **No se puede filtrar ni ordenar por patrón en SQL.** "Enséñame las partidas
  con un vuelco" no es un `WHERE`: hoy no hace falta, pero RF-4.1 (puzzles desde
  errores propios) sí querrá seleccionar posiciones por criterio. Un job que
  cree `puzzles` puede aplicar las mismas funciones del núcleo al generarlos, que
  es lo que ya prevé el flujo 5 de [03-arquitectura.md](../03-arquitectura.md):
  lo que se persistiría entonces es el puzzle, no el patrón.
- **Lo que no quedó guardado, no se afirma.** Un análisis anterior a RF-10 cuyas
  alternativas no se puedan rescatar de `position_cache` sale con menos momentos
  críticos —los de "solo valía una jugada" necesitan el MultiPV—, y una partida
  sin relojes no aparece en las estadísticas de tiempo. Se prefiere el hueco
  explicado al número inventado.
- **`lucia_core` sigue sin saber de bases de datos.** Por eso existe
  `MoveContext` y no se reutiliza `analysis.AnalyzedMove`: el material llega de
  la base con cosas que el motor nunca vio (el reloj) y con las alternativas ya
  traducidas a probabilidad de victoria desde el punto de vista de quien mueve.
- **Qué NO fija este ADR.** Los umbrales y el orden en que se comprueban los
  tipos de error (reloj → táctico → final → posicional) son reglas de un módulo,
  revisables sin tocar nada más: viven en `InsightThresholds` y en los docstrings
  de `lucia_core.insights`, y están anotadas en la nota de reglas de RF-3 en
  [02-requerimientos.md](../02-requerimientos.md). Cambiarlas no necesita un ADR;
  cambiar *dónde y cuándo se calculan*, sí.

## Ver también

- RF-2.8, RF-3.2, RF-3.4 y RF-3.5 en [02-requerimientos.md](../02-requerimientos.md),
  con las reglas concretas que se eligieron.
- [ADR-0007](0007-alternativas-por-jugada-json-y-cache.md): de dónde salen las
  alternativas que "solo valía una jugada" necesita.
- `packages/core/lucia_core/insights/__init__.py` (las reglas),
  `apps/api/lucia_api/services/insights.py` (el puente con la base) y
  `apps/api/lucia_api/services/stats.py` (los agregados).

## Corrección de hecho (2026-09-19)

Este ADR nombraba el endpoint de estadísticas como `GET /stats/{username}`, en
la decisión y en la primera consecuencia. **Ese endpoint no existió nunca**: es
`GET /stats?username=…`, con el nombre en la cadena de consulta y opcional —sin
él se resuelve al de `CHESSCOM_USERNAME`—, y así está en `routers/stats.py`
desde el primer día (comprobado en el historial de git al auditar el cierre de
la fase 2). Las dos menciones quedan corregidas arriba.

Se corrige **en el propio archivo**, y no con un ADR nuevo, porque no se está
cambiando ninguna decisión: lo que este documento decide —que los patrones se
deducen al leer, sin tabla propia ni segunda pasada del motor— es exactamente
lo mismo antes y después. La norma del proyecto de no editar un ADR publicado
protege el registro de las **decisiones**, no obliga a conservar un dato de
hecho equivocado que desinforma a quien lo lea. Queda esta nota para que la
corrección no sea silenciosa, que es lo que esa norma sí busca evitar.
