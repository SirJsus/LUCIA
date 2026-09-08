# `features/viewer` — visor de partidas

La pantalla del visor (RF-5.1): revivir una partida ya analizada jugada a
jugada, con su clasificación, su gráfico de evaluación y el disparo del
análisis con progreso en vivo (RF-2.4).

Las piezas de tablero que comparte con el tablero de análisis (`Chessboard`,
`EvalBar`, `BoardWithEvalBar`, `MoveNavigator`, `boardConfig`) ya no viven
aquí, sino en `components/board/`: la regla es que el visor y el tablero de
análisis enseñen lo mismo de la misma forma (RNF-11 y criterio C-5 de
[`docs/07-coherencia-ui.md`](../../../../../docs/07-coherencia-ui.md)); si una
de las dos se desviara, el problema es la desviación, no el compartir.

| Archivo | Qué es | Quién lo usa |
| --- | --- | --- |
| `GameViewerPage.tsx` | La pantalla del visor: tablero, navegación, análisis y comparación de motores | ruta `/games/$gameId` |
| `EvalChart.tsx` | Gráfico de evaluación de la partida (**Recharts**), eje Y en win% | visor |
| `MoveList.tsx` | Jugadas emparejadas por turno con su clasificación | visor |
| `EngineComparison.tsx` | Dónde discrepan dos motores sobre la misma partida (RF-2.6) | visor |
| `useAnalysisProgress.ts` | Progreso del análisis por WebSocket, con respaldo HTTP (RF-2.4) | visor |

## De dónde salen los números

- El visor **no calcula** evaluaciones: pinta lo que guardó el análisis
  (`GET /analysis/{id}`), incluido el `win_percent_after` de cada jugada.
- El tablero de análisis sí, porque `POST /analysis/position` solo devuelve
  centipawns o mate: convierte esa evaluación a probabilidad de victoria en el
  cliente (`lib/score.ts`, decisión registrada en
  [ADR-0006](../../../../../docs/adr/0006-probabilidad-de-victoria-en-el-cliente.md)).
- El análisis guardado solo tiene la mejor jugada de cada posición, así que en
  el visor la flecha es una sola; las flechas múltiples son cosa del tablero de
  análisis hasta que RF-10 persista las alternativas.
