/** Evaluaciones del motor: cómo se escriben y cómo se traducen a
 * probabilidad de victoria. Siempre desde el punto de vista de las blancas,
 * como es costumbre en ajedrez. */
import type { AnalyzedMoveOut, EngineLine } from "@lucia/shared-types";

/** Lo que hace falta de una línea del motor para escribir su evaluación o
 * traducirla a probabilidad: las dos formas en que un motor puntúa una
 * posición. */
export type EngineScore = Pick<EngineLine, "score_cp" | "score_mate">;

export function formatScore(score: EngineScore): string {
  if (score.score_mate !== null && score.score_mate !== undefined) {
    // "M3+" = mate en 3 a favor de las blancas; "M3−" = a favor de las negras.
    return `M${Math.abs(score.score_mate)}${score.score_mate < 0 ? "\u2212" : "+"}`;
  }
  if (score.score_cp === null || score.score_cp === undefined) return "\u2014";
  const pawns = score.score_cp / 100;
  return `${pawns >= 0 ? "+" : "\u2212"}${Math.abs(pawns).toFixed(2)}`;
}

/** Constantes del modelo de probabilidad de victoria de Lichess, replicado
 * aquí a propósito (ver ADR-0006): `POST /analysis/position` devuelve la
 * evaluación del motor en centipawns o mate y nada más, así que la barra del
 * tablero de análisis no tiene de dónde sacar el win% si no lo calcula el
 * cliente.
 *
 * Es el mismo modelo que usa el backend: `lucia_core.accuracy.win_percent`
 * pide `wdl(model="lichess")` a `python-chess`, que por dentro calcula
 * `1000 / (1 + exp(-0.00368208 * cp))` sobre los centipawns acotados a ±1000.
 * Con evaluaciones en centipawns ambos lados dan el mismo número; con mate
 * anunciado no, y es deliberado (ver abajo). */
const LICHESS_WIN_MODEL_FACTOR = 0.00368208;
const MAX_MODELLED_CENTIPAWNS = 1000;

/** Probabilidad de victoria de las blancas (0-100) para una evaluación del
 * motor, o `null` si esa evaluación no existe todavía.
 *
 * Es lo que hace legible una evaluación sin saber leerla: `+0.35` no dice
 * nada por sí solo, "55 % para las blancas" sí. */
export function whiteWinPercentFromScore(score: EngineScore): number | null {
  // Un mate anunciado no se modela: o se gana o se pierde. `M0` significa
  // que a quien mueve ya lo han dado mate, de ahí que el cero cuente como
  // derrota de las blancas.
  //
  // Aquí es donde el cliente se separa del backend a propósito: el modelo de
  // Lichess trata el mate como una ventaja enorme en centipawns y se queda en
  // ~99,9 %, así que el visor (que enseña el `win_percent_after` guardado)
  // puede mostrar 99,9 % donde el tablero de análisis muestra 100 %. La
  // diferencia es de décimas y solo con mate a la vista; llenar la barra del
  // todo dice lo que pasa mejor que dejar una rendija. Anotado en ADR-0006.
  if (score.score_mate !== null && score.score_mate !== undefined) {
    return score.score_mate > 0 ? 100 : 0;
  }
  if (score.score_cp === null || score.score_cp === undefined) return null;
  const centipawns = Math.max(
    -MAX_MODELLED_CENTIPAWNS,
    Math.min(score.score_cp, MAX_MODELLED_CENTIPAWNS),
  );
  return Math.round(1000 / (1 + Math.exp(-LICHESS_WIN_MODEL_FACTOR * centipawns))) / 10;
}

/** Lleva a la perspectiva de las blancas el `win_percent_after` de una jugada
 * analizada, que la API devuelve desde el punto de vista de quien movió. */
export function whiteWinPercentAfterMove(
  move: Pick<AnalyzedMoveOut, "color" | "win_percent_after">,
): number {
  return move.color === "white" ? move.win_percent_after : 100 - move.win_percent_after;
}
