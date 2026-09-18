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

/** Lo que se enseña donde debería haber un dato y no lo hay. Es uno solo para
 * que un hueco se reconozca como tal en cualquier pantalla (criterio C-5). */
const MISSING_VALUE = "—";

/** Ritmo con el que se guarda una partida cuyo PGN no dice a qué se jugó
 * (RF-1.5); la API lo escribe así en `games.time_class`. */
const UNKNOWN_TIME_CLASS = "unknown";

/** Control de tiempo con el que se guarda esa misma partida. */
const UNKNOWN_TIME_CONTROL = "-";

export function formatAccuracy(accuracy: number | null | undefined): string {
  return accuracy == null ? MISSING_VALUE : formatPercent(accuracy, 1);
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

/** Diferencia entre dos probabilidades de victoria: "12 pts de prob. de
 * victoria".
 *
 * No es un porcentaje —es la distancia entre dos—, y sin unidad se leía como
 * puntos de material, que es justo lo contrario de lo que mide: 12 puntos de
 * material es una dama y una torre (criterio C-6 de docs/07-coherencia-ui.md).
 */
export function formatWinPercentPoints(points: number): string {
  return `${points.toFixed(0)} pts de prob. de victoria`;
}

/** Los motores que LUCIA sabe usar, en el orden en que se ofrecen.
 *
 * El desplegable de las dos pantallas que eligen motor sale de esta lista: los
 * tenían escritos a mano cada una, así que añadir un tercero pedía acordarse
 * de dos sitios y sus nombres se saltaban `formatEngineName` (criterio C-5 de
 * docs/07-coherencia-ui.md). */
export const ENGINE_IDS = ["stockfish", "lc0"] as const;

export type EngineId = (typeof ENGINE_IDS)[number];

/** Nombre del motor tal como se enseña: "Stockfish", "Lc0".
 *
 * En la base y en la API viaja en minúscula (`stockfish`), y se estaba
 * mostrando de tres formas distintas: cruda, capitalizada por CSS y escrita a
 * mano en un desplegable. */
const ENGINE_DISPLAY_NAMES: Record<EngineId, string> = {
  stockfish: "Stockfish",
  lc0: "Lc0",
};

export function formatEngineName(engine: string): string {
  return ENGINE_DISPLAY_NAMES[engine as EngineId] ?? capitalize(engine);
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
  // Un PGN importado a mano (RF-1.5) no dice a qué ritmo se jugó y la columna
  // se guarda como "unknown": es el hueco de la columna, y se enseña como el
  // resto de huecos de la aplicación —"—", igual que el rating y la
  // precisión— en vez de un "Unknown" en inglés entre "Blitz" y "Rapid".
  if (timeClass === UNKNOWN_TIME_CLASS) return MISSING_VALUE;
  return capitalize(timeClass);
}

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Mes de una serie temporal: "2026-09".
 *
 * No pasa por `formatDate` a propósito: "sept 2026" no cabe en un eje con una
 * marca por mes, y ahí interesa que se ordene a simple vista. Vive aquí igual
 * porque una fecha compuesta a mano dentro de una pantalla es justo lo que el
 * criterio C-5 evita.
 */
export function formatYearMonth(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, "0")}`;
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

/** El rating de un bando: "1832", o "—" cuando no se sabe.
 *
 * Las partidas importadas de un PGN manual (RF-1.5) rara vez traen `WhiteElo`
 * y se guardan con 0, que es el hueco de la columna. Enseñar "(0)" haría
 * pasar el hueco por un dato, y por uno malísimo. */
export function formatRating(rating: number): string {
  return rating > 0 ? String(rating) : MISSING_VALUE;
}

/** Resultados que significan tablas para AMBOS jugadores: los de chess.com,
 * que dicen además cómo se llegó a ellas, más el "draw" a secas del PGN
 * importado a mano (RF-1.5), donde el archivo solo dice "1/2-1/2".
 * Cualquier otro valor distinto de "win" significa que ese bando perdió. */
const DRAW_RESULTS = new Set([
  "draw",
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
  if (timeControl === UNKNOWN_TIME_CONTROL) return MISSING_VALUE;
  const [base, increment] = timeControl.split("+");
  const baseSeconds = Number(base);
  if (Number.isNaN(baseSeconds)) return timeControl;
  const minutes = baseSeconds / 60;
  const shown = Number.isInteger(minutes) ? String(minutes) : minutes.toFixed(1);
  return increment ? `${shown}+${increment}` : `${shown}+0`;
}
