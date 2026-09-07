/** Formateo de datos para mostrar: fechas, resultados y control de tiempo. */
import type { GameSummary } from "@lucia/shared-types";

export function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("es", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatAccuracy(accuracy: number | null | undefined): string {
  return accuracy == null ? "—" : accuracy.toFixed(1);
}

/** Segundos transcurridos como "m:ss", o "h:mm:ss" si pasa de una hora.
 * Para relojes en marcha: cuánto lleva corriendo un análisis. */
export function formatDuration(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const padTwoDigits = (value: number) => String(value).padStart(2, "0");
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor(seconds / 60);
  // La primera cifra va sin rellenar: "1:02:05", no "01:02:05".
  return hours > 0
    ? `${hours}:${padTwoDigits(minutes % 60)}:${padTwoDigits(seconds % 60)}`
    : `${minutes}:${padTwoDigits(seconds % 60)}`;
}

/** Resultados que chess.com reporta para AMBOS jugadores cuando es tablas;
 * cualquier otro valor distinto de "win" significa que ese bando perdió. */
const DRAW_RESULTS = new Set([
  "agreed",
  "repetition",
  "stalemate",
  "insufficient",
  "50move",
  "timevsinsufficient",
]);

/** El resultado en notación PGN, deducido del campo por jugador de chess.com. */
export function gameResult(game: Pick<GameSummary, "white_result">): string {
  if (game.white_result === "win") return "1-0";
  if (DRAW_RESULTS.has(game.white_result)) return "½-½";
  return "0-1";
}

/** "180" -> "3+0", "600+5" -> "10+5" (chess.com da el control en segundos). */
export function formatTimeControl(timeControl: string): string {
  const [base, increment] = timeControl.split("+");
  const baseSeconds = Number(base);
  if (Number.isNaN(baseSeconds)) return timeControl;
  const minutes = baseSeconds / 60;
  const shown = Number.isInteger(minutes) ? String(minutes) : minutes.toFixed(1);
  return increment ? `${shown}+${increment}` : `${shown}+0`;
}
