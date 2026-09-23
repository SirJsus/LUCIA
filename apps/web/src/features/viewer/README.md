# `features/viewer` — visor de partidas

La pantalla del visor (RF-5.1): revivir una partida ya analizada jugada a
jugada, con su clasificación, su gráfico de evaluación, los momentos en que se
decidió (RF-2.8), el disparo del análisis con progreso en vivo (RF-2.4) y la
descarga de la partida como PGN anotado (RF-5.5).

Las piezas de tablero que comparte con el tablero de análisis (`Chessboard`,
`EvalBar`, `BoardWithEvalBar`, `MoveNavigator`, `MoveButton`, `EngineLineList`,
`boardConfig`, la capa de ocupación de RF-7 y los atajos de
`useMoveNavigationKeys`) ya no viven aquí, sino en
`components/board/`; fuera de tablero comparte con él `EngineSelect` y
`ClassificationBadge`, y desde RF-6.9 también el seguimiento del análisis en
background (`lib/useTrackedAnalysis.ts`, con `useElapsedSeconds`), que estaba
aquí como `useAnalysisProgress` hasta que el tablero de análisis pasó a pedir
el mismo análisis: la regla es que el visor y el tablero de
análisis enseñen lo mismo de la misma forma (RNF-11 y criterio C-5 de
[`docs/07-coherencia-ui.md`](../../../../../docs/07-coherencia-ui.md)); si una
de las dos se desviara, el problema es la desviación, no el compartir.

| Archivo                | Qué es                                                                                                                                    | Quién lo usa          |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `GameViewerPage.tsx`   | La pantalla del visor: tablero, navegación, análisis y comparación de motores                                                             | ruta `/games/$gameId` |
| `EvalChart.tsx`        | Gráfico de evaluación de la partida (**Recharts**), eje Y en win%, con cada punto del color de su clasificación y los errores más grandes | visor                 |
| `MoveList.tsx`         | Jugadas emparejadas por turno con su clasificación                                                                                        | visor                 |
| `CriticalMoments.tsx`  | Las jugadas donde se decidió la partida y por qué (RF-2.8)                                                                                | visor                 |
| `EngineComparison.tsx` | Dónde discrepan dos motores sobre la misma partida (RF-2.6)                                                                               | visor                 |

## De dónde salen los números

- El visor **no calcula** evaluaciones: pinta lo que guardó el análisis
  (`GET /analysis/{id}`), incluido el `win_percent_after` de cada jugada.
- El tablero de análisis sí, porque `POST /analysis/position` solo devuelve
  centipawns o mate: convierte esa evaluación a probabilidad de victoria en el
  cliente (`lib/score.ts`, decisión registrada en
  [ADR-0006](../../../../../docs/adr/0006-probabilidad-de-victoria-en-el-cliente.md)).
- El análisis guardado trae, desde RF-10.1, las N mejores líneas de cada
  posición (`alternatives`), así que el visor dibuja las mismas flechas
  múltiples que el tablero de análisis y puede enseñar "lo que podías haber
  jugado" al pararse en una jugada. Un análisis anterior a RF-10 cuyas
  posiciones ya no estén en `position_cache` se queda con una sola flecha, que
  es lo único que se guardó de él.

## De qué posición son las alternativas

De la que está en el tablero, siempre: las flechas y la lista del lateral
hablan de lo mismo. Lo que despista es dónde viajan guardadas — con la jugada
**siguiente**, no con la que llevó hasta aquí, porque son las líneas que el
motor daba en la posición anterior a esa jugada (RF-10.1). De ahí el
`analysis.moves[currentPly + 1]` de `GameViewerPage`, que es también la jugada
que se hizo desde esta posición: por eso el panel puede titularse "Podías haber
jugado, en vez de X" cuando salió mal, y marcar en la lista cuál fue.

## Qué número de jugada se enseña

El `ply` que manejan la API y esta pantalla cuenta desde la primera jugada de
la partida, que no tiene por qué ser la del turno 1: una partida con ventaja o
una empezada desde una posición dada arranca donde diga su PGN. El número que
se lee sale de sumarle el ply de esa posición de partida (`lib/moves.ts`), y lo
hacen igual la lista de jugadas, el gráfico y la comparación de motores. La
cabecera avisa además de esas partidas, con el campo
`starts_from_custom_position` que trae la API.

## Qué explican las tres acciones de la cabecera

"Exportar PGN anotado" (RF-5.5), "Abrir como tablero" (RF-6.6) y "Jugar desde
aquí" (RF-4.4) son las tres formas de sacar la partida de esta pantalla, y las
tres dicen qué hacen en **una línea bajo la fila de botones**, no en un `title`:
con teclado un `title` no aparece nunca, y en un botón deshabilitado —que es
como está "Exportar PGN anotado" mientras no hay análisis— tampoco. Es la misma
forma con la que Puzzles y Aperturas explican su botón de generar (fila 103 del
inventario de [`docs/07-coherencia-ui.md`](../../../../../docs/07-coherencia-ui.md),
criterios C-6 y C-7). El texto cambia con el estado del análisis, que es lo que
antes distinguía los dos `title` de cada botón.

## Exportar el PGN anotado

"Exportar PGN anotado" (RF-5.5) es un **botón**, no un `<a download>` a
`GET /analysis/{id}/pgn`. Con el enlace la descarga la hacía el navegador, y un
409 o un 404 se guardaban como si fueran el archivo sin que la pantalla dijera
nada (fila 70 del inventario). Ahora `api.getAnalysisPgn()` pide la respuesta,
la comprueba y solo entonces `lib/download.ts::saveTextAsFile` la guarda, así
que el error sale en su `ErrorBox` como el de cualquier otra acción. El nombre
del archivo, que con el enlace ponía el servidor en `Content-Disposition`, se
lee de esa misma cabecera y se le pasa al `download` del enlace temporal;
`analysisPgnUrl()` sigue en `lib/api.ts` porque es de ahí de donde sale esa URL.

El botón está **siempre**, también sin análisis: deshabilitado y diciendo qué
falta para que sirva. Antes no existía hasta haber un análisis terminado, así
que quien abría una partida sin analizar no podía saber que la exportación
existe (fila 68, criterio C-3).

El archivo lo compone el servidor entero (`services/pgn_export.py`): el visor
no arma nada. Eso obliga a que las etiquetas de clasificación estén escritas
también allí, duplicadas a propósito de las de `lib/classification.ts`; si
cambian aquí, hay que cambiarlas allá (criterio C-5 de
[`docs/07-coherencia-ui.md`](../../../../../docs/07-coherencia-ui.md)).

Solo se habilita con el análisis en `done`, que es lo único que la API exporta:
un análisis a medias daría una partida comentada hasta la jugada 20 y muda a
partir de ahí. Qué lleva exactamente el archivo está en la nota de
RF-5.5 de
[`docs/02-requerimientos.md`](../../../../../docs/02-requerimientos.md).

## Abrir como tablero

"Abrir como tablero" (RF-6.6) crea un tablero de análisis **nuevo** con las
jugadas de esta partida: pide el PGN anotado (`GET /analysis/{id}/pgn`) si hay
análisis terminado y usa el crudo de `games.pgn` si no, lo pasa por
`features/board/tree.ts::fromPgn` y lo manda a `POST /boards`. Desde ahí las
dos cosas van por su cuenta: explorar variantes en la copia no toca el análisis
original, que es justo lo que pide RF-5.2.

La copia **nunca nace marcada como "partida propia"** (RF-6.5): esa marca
publica el tablero en el historial, y esta partida ya está en él, así que
marcarla la contaría dos veces en el dashboard.

## Ocupación del tablero

La capa de RF-7 (quién controla cada casilla, piezas colgadas, clavadas y rayos
X) se enciende con la tecla `O` o desde su panel, bajo el tablero. Esta pantalla
no calcula nada: le pasa a `useOccupancy` el FEN de la jugada en la que está
parada y le da ese controlador a `Chessboard` por su propiedad
`occupancyController`, que es quien dibuja `OccupancyLayer` encima y quien monta
la rejilla enfocable con la que se inspecciona una casilla sin ratón (RF-7.3);
esa rejilla vivía dentro de la capa hasta que hubo que compartirla con mover una
pieza por teclado, y dos rejillas superpuestas eran dos juegos de paradas de
foco. Todo lo
demás vive en `components/board/`, compartido con las otras cuatro pantallas
con tablero, y no pasa por la API ni por el motor. Cambiar de jugada suelta la
casilla inspeccionada: era de la posición anterior.

Aquí las tres marcas —colgadas, clavadas y rayos X— **arrancan encendidas**,
que es el ajuste por omisión de `useOccupancy`: son lo que la capa aporta sobre
mirar el tablero a secas y apagadas de entrada nadie las descubriría. En las
tres pantallas de entrenamiento arrancan apagadas, y por qué está en
`features/training/README.md`.

## Momentos críticos

No son "las jugadas malas" (para eso está la clasificación de cada jugada, que
ya se ve en la lista y en el gráfico): son las posiciones donde la partida se
decidía, con el motivo de cada una —solo valía una jugada, la partida cambió de
manos, había una ganada y se escapó—. La jugada única **encontrada** también
sale, porque saber que se encontró es la mitad de lo que se viene a aprender.

Los criterios no se calculan aquí: llegan resueltos en `GET /analysis/{id}`,
que los pide a `lucia_core.insights` sobre lo que ya guardó el análisis, sin
volver a preguntar al motor. Un análisis anterior a RF-10 cuyas alternativas no
se puedan rescatar de `position_cache` sale con menos momentos —los de "solo
valía una jugada" necesitan el MultiPV—, no con momentos inventados.

Entran las jugadas de **los dos** bandos, al revés que las estadísticas del
dashboard, que solo miran las propias: recorriendo una partida entera, una
posición donde el rival tenía una sola jugada es tan interesante como una
propia. Por eso cada momento trae su `color`: la API da la probabilidad de
victoria desde el punto de vista de quien movió y la pantalla la gira a la de
las blancas, que es como la enseñan la barra y el gráfico.

El nombre y la explicación de cada motivo salen de `lib/insights.ts`, el mismo
sitio del que los saca el dashboard para los tipos de error.
