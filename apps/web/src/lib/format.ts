/** Formateo de datos para mostrar: fechas, resultados, control de tiempo,
 * porcentajes y nombres de motor. Todo lo que se enseña con un formato pasa
 * por aquí (criterio C-5 de docs/07-coherencia-ui.md). */
import type { GameSummary } from "@lucia/shared-types";

export function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("es", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatAccuracy(accuracy: number | null | undefined): string {
  return accuracy == null ? "—" : formatPercent(accuracy, 1);
}

/** Porcentaje con la unidad puesta: "54.3 %".
 *
 * La precisión se mostraba como número pelado ("87.3") al lado de porcentajes
 * que sí llevaban el signo, y la misma magnitud aparecía con cero o con un
 * decimal según la pantalla. Ambas cosas son porcentajes y ahora se ven igual.
 */
export function formatPercent(value: number, decimals = 0): string {
  // Espacio antes del signo, como pide la ortografía española.
  return `${value.toFixed(decimals)} %`;
}

/** Nombre del motor tal como se enseña: "Stockfish", "Lc0".
 *
 * En la base y en la API viaja en minúscula (`stockfish`), y se estaba
 * mostrando de tres formas distintas: cruda, capitalizada por CSS y escrita a
 * mano en un desplegable. */
const ENGINE_DISPLAY_NAMES: Record<string, string> = {
  stockfish: "Stockfish",
  lc0: "Lc0",
};

export function formatEngineName(engine: string): string {
  return ENGINE_DISPLAY_NAMES[engine] ?? capitalize(engine);
}

/** Control de tiempo de chess.com tal como se enseña: "Blitz", "Rapid"…
 *
 * Llegan en minúscula desde la API y se veían crudas en dos pantallas y
 * capitalizadas por CSS en una tercera. Se dejan **en inglés**: "blitz" y
 * "bullet" son préstamos de uso corriente en el ajedrez en español, y
 * traducir unos sí y otros no dejaba cuatro formas gramaticales distintas en
 * la misma columna. Además son los términos que el usuario ya ve en
 * chess.com, que es de donde vienen los datos.
 */
export function formatTimeClass(timeClass: string): string {
  return capitalize(timeClass);
}

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
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
