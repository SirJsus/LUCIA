/** Formateo de evaluaciones del motor, siempre desde el punto de vista de las
 * blancas, como es costumbre en ajedrez. */
import type { EngineLine } from "@lucia/shared-types";

export function formatScore(line: Pick<EngineLine, "score_cp" | "score_mate">): string {
  if (line.score_mate !== null && line.score_mate !== undefined) {
    // "M3+" = mate en 3 a favor de las blancas; "M3−" = a favor de las negras.
    return `M${Math.abs(line.score_mate)}${line.score_mate < 0 ? "\u2212" : "+"}`;
  }
  if (line.score_cp === null || line.score_cp === undefined) return "\u2014";
  const peones = line.score_cp / 100;
  return `${peones >= 0 ? "+" : "\u2212"}${Math.abs(peones).toFixed(2)}`;
}
