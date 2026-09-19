# `features/viewer` — visor de partidas

La pantalla del visor (RF-5.1): revivir una partida ya analizada jugada a
jugada, con su clasificación, su gráfico de evaluación, los momentos en que se
decidió (RF-2.8), el disparo del análisis con progreso en vivo (RF-2.4) y la
descarga de la partida como PGN anotado (RF-5.5).

Las piezas de tablero que comparte con el tablero de análisis (`Chessboard`,
`EvalBar`, `BoardWithEvalBar`, `MoveNavigator`, `MoveButton`, `EngineLineList`,
`boardConfig` y los atajos de `useMoveNavigationKeys`) ya no viven aquí, sino en
`components/board/`; fuera de tablero comparte con él `EngineSelect` y
`ClassificationBadge`, y desde RF-6.9 también el seguimiento del análisis en
background (`lib/useTrackedAnalysis.ts`, con `useElapsedSeconds`), que estaba
aquí como `useAnalysisProgress` hasta que el tablero de análisis pasó a pedir
el mismo análisis: la regla es que el visor y el tablero de
análisis enseñen lo mismo de la misma forma (RNF-11 y criterio C-5 de
[`docs/07-coherencia-ui.md`](../../../../../docs/07-coherencia-ui.md)); si una
de las dos se desviara, el problema es la desviación, no el compartir.

| Archivo | Qué es | Quién lo usa |
| --- | --- | --- |
| `GameViewerPage.tsx` | La pantalla del visor: tablero, navegación, análisis y comparación de motores | ruta `/games/$gameId` |
| `EvalChart.tsx` | Gráfico de evaluación de la partida (**Recharts**), eje Y en win%, con cada punto del color de su clasificación y los errores más grandes | visor |
| `MoveList.tsx` | Jugadas emparejadas por turno con su clasificación | visor |
| `CriticalMoments.tsx` | Las jugadas donde se decidió la partida y por qué (RF-2.8) | visor |
| `EngineComparison.tsx` | Dónde discrepan dos motores sobre la misma partida (RF-2.6) | visor |

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

## Exportar el PGN anotado

"Exportar PGN anotado" (RF-5.5) es un `<a download>` a
`GET /analysis/{id}/pgn` y no una llamada por `fetch`: así el navegador
descarga el archivo con el nombre que manda el servidor en
`Content-Disposition`, que es justo lo que se perdería al pasar el contenido
por JavaScript. Por eso `lib/api.ts` expone `analysisPgnUrl()` —una URL— y no
un método más del cliente.

El archivo lo compone el servidor entero (`services/pgn_export.py`): el visor
no arma nada. Eso obliga a que las etiquetas de clasificación estén escritas
también allí, duplicadas a propósito de las de `lib/classification.ts`; si
cambian aquí, hay que cambiarlas allá (criterio C-5 de
[`docs/07-coherencia-ui.md`](../../../../../docs/07-coherencia-ui.md)).

El enlace solo aparece con el análisis en `done`, que es lo único que la API
exporta: un análisis a medias daría una partida comentada hasta la jugada 20 y
muda a partir de ahí. Qué lleva exactamente el archivo está en la nota de
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
