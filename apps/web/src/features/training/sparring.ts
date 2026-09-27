/** Cómo se lee en pantalla una partida de sparring (RF-4.3): cómo acabó y
 * quién ganó, dicho desde quien juega.
 *
 * Vive aparte de las pantallas porque es lógica pura y se prueba sola
 * (`__tests__/sparring.test.ts`), y porque las dos pantallas de sparring —la
 * lista y la partida en curso— tienen que decir lo mismo con las mismas
 * palabras (criterio C-2 de docs/07-coherencia-ui.md).
 *
 * El resultado llega de la API como "1-0", "0-1" o "1/2-1/2", que es el
 * marcador de la partida y no dice nada por sí solo a quien no lo lee
 * (criterio C-6): aquí se traduce a ganaste / perdiste / tablas, que es lo
 * que se viene a saber.
 */
import type { SparringGame, SparringTermination } from "@lucia/shared-types";

export type SparringOutcome = "win" | "loss" | "draw";

/** Cómo le fue a quien juega, o `null` si la partida sigue viva. */
export function outcomeFor(game: SparringGame): SparringOutcome | null {
  if (game.result === null) return null;
  if (game.result === "1/2-1/2") return "draw";
  const playerIsWhite = game.player_color === "white";
  return game.result === (playerIsWhite ? "1-0" : "0-1") ? "win" : "loss";
}

const OUTCOME_LABELS: Record<SparringOutcome, string> = {
  win: "Ganaste",
  loss: "Perdiste",
  draw: "Tablas",
};

/** Por qué acabó, en una frase que se pega detrás del resultado. Va aparte
 * del marcador porque "0-1" no distingue un mate de un abandono, y en un
 * entrenamiento eso es justo lo que se quiere saber. */
const TERMINATION_LABELS: Record<SparringTermination, string> = {
  checkmate: "por jaque mate",
  stalemate: "por rey ahogado",
  insufficient_material: "por material insuficiente",
  fifty_moves: "por la regla de las 50 jugadas",
  repetition: "por repetición de jugadas",
  resignation: "por abandono",
};

/** El resultado entero tal como se enseña: "Ganaste por jaque mate". Si la
 * causa no se reconoce se queda en el resultado a secas. */
export function outcomeSentence(game: SparringGame): string | null {
  const outcome = outcomeFor(game);
  if (outcome === null) return null;
  const label = OUTCOME_LABELS[outcome];
  const reason = TERMINATION_LABELS[game.termination as SparringTermination];
  return reason ? `${label} ${reason}` : label;
}
