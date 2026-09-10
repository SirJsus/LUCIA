# `features/viewer` — visor de partidas

La pantalla del visor (RF-5.1): revivir una partida ya analizada jugada a
jugada, con su clasificación, su gráfico de evaluación, los momentos en que se
decidió (RF-2.8) y el disparo del análisis con progreso en vivo (RF-2.4).

Las piezas de tablero que comparte con el tablero de análisis (`Chessboard`,
`EvalBar`, `BoardWithEvalBar`, `MoveNavigator`, `MoveButton`, `EngineLineList`,
`boardConfig` y los atajos de `useMoveNavigationKeys`) ya no viven aquí, sino en
`components/board/`; fuera de tablero comparte con él `EngineSelect` y
`ClassificationBadge`: la regla es que el visor y el tablero de
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
| `useAnalysisProgress.ts` | Progreso del análisis por WebSocket, con respaldo HTTP (RF-2.4) | visor |

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
