/** Cómo se lee un drill de aperturas en pantalla (RF-4.2): por qué está en la
 * baraja y cómo va la línea.
 *
 * Vive aparte de las pantallas porque es lógica pura y se prueba sola
 * (`__tests__/drills.test.ts`). Lo que traduce es el motivo: la API manda
 * `source`, `games_played` y `score_percent`, que son el dato, y aquí se
 * convierten en la frase que explica qué se está entrenando y por qué — un
 * porcentaje suelto no lo dice (criterio C-6 de docs/07-coherencia-ui.md).
 */
import type { Drill, DrillSource } from "@lucia/shared-types";
import { formatPercent } from "../../lib/format";

const SOURCE_LABELS: Record<DrillSource, string> = {
  departure: "Te sales de la teoría",
  opening: "Apertura floja",
};

/** La etiqueta corta de la baraja de la que salió, que encabeza el motivo en
 * el panel de la línea. Fue una insignia hasta que la fila 98 del inventario
 * de docs/07-coherencia-ui.md dejó la insignia del panel para el estado del
 * ejercicio, igual en las tres pantallas de entrenamiento. */
export function drillSourceLabel(source: string): string {
  return SOURCE_LABELS[source as DrillSource] ?? source;
}

/** Por qué este drill está en la baraja, en una frase. */
export function drillSourceSentence(drill: Drill): string {
  const games = `${drill.games_played} ${drill.games_played === 1 ? "partida" : "partidas"}`;
  // La misma puntuación sale con un decimal en el panel de estadísticas, que
  // es donde se ve el otro lado de este mismo dato (criterio C-5).
  const score = formatPercent(drill.score_percent, 1);
  return drill.source === "departure"
    ? `Abandonas la teoría aquí en ${games} y sacas un ${score}.`
    : `Con esta apertura sacas un ${score} en ${games}.`;
}

/** Cuántas jugadas propias tiene la línea: las que hay que acertar. Es la
 * unidad en la que se cuenta el progreso, porque las del rival las juega la
 * aplicación y no cuestan nada.
 *
 * `first_player_ply` es 0 con blancas y 1 con negras, así que las jugadas
 * propias son las que quedan desde ahí contando de dos en dos. */
export function playerMoveCount(drill: Drill): number {
  return Math.ceil((drill.line_length_plies - drill.first_player_ply) / 2);
}
