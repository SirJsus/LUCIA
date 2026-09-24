/** Formateo de datos para mostrar: fechas, resultados, control de tiempo,
 * porcentajes y nombres de motor. Todo lo que se enseña con un formato pasa
 * por aquí (criterio C-5 de docs/07-coherencia-ui.md). */
import type { GamePhase, GameSummary } from "@lucia/shared-types";

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

/** Una partida que nadie ha mandado analizar todavía, en la columna «Análisis»
 * de la lista (RF-2.5). **No es `MISSING_VALUE`**: ahí no falta ningún dato
 * —se sabe que no hay ningún análisis—, y un "—" en esa columna se leería como
 * el hueco del rating o del control de tiempo, que son datos que no llegaron.
 * Es además el nombre que ese estado ya tiene en el visor y en el tablero de
 * análisis, en su `EmptyState` (criterios C-5 y C-6). */
const NOT_ANALYZED = "Sin analizar";

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

/** Puntos de precisión ganados o perdidos, sin signo: "3.2".
 *
 * Un decimal, el mismo que enseña la columna "Precisión" de la tabla de
 * tendencias. De si suben o bajan se encarga el verbo de la frase que lo
 * rodea. Vive aquí porque lo dicen dos pantallas —la frase de tendencia del
 * panel de estadísticas (RF-3.7) y la debilidad de precisión del plan semanal
 * (RF-4.5)—, y dos sitios decidiendo por su cuenta cuántos decimales es justo
 * lo que evita el criterio C-5. */
export function formatAccuracyPoints(points: number): string {
  return Math.abs(points).toFixed(1);
}

/** Puntos de partida perdidos frente a empatarlas todas: "2.5 puntos de
 * marcador" (`lucia_core.drills.points_lost`, RF-4.2 y RF-4.5).
 *
 * No son los puntos de probabilidad de victoria de `formatWinPercentPoints` ni
 * los de precisión de `formatAccuracyPoints`: son victorias y tablas, la
 * moneda del marcador. Los tres decían "puntos" a secas y los tres salían
 * seguidos en la misma lista del plan semanal, así que la palabra nombraba tres
 * magnitudes distintas (fila 104 del inventario de docs/07-coherencia-ui.md).
 * Cada uno dice ya de qué son los suyos, que es lo que hizo
 * `formatWinPercentPoints` cuando "pts" a secas se leía como puntos de
 * material. */
export function formatScorePoints(points: number): string {
  return `${points.toFixed(1)} puntos de marcador`;
}

/** Lo que costó un error propio, en una frase: "Tu probabilidad de victoria
 * pasó de 72.0 % a 31.0 %: 41 pts de prob. de victoria menos."
 *
 * Es la misma frase en las dos pantallas que dicen lo que costó un error del
 * usuario —el puzzle ya resuelto (RF-4.1) y la lista de errores desde los que
 * re-jugar (RF-4.4)—, y estaba escrita dos veces con su resta incluida, que es
 * la forma de que dos sitios acaben diciendo lo mismo de dos maneras (criterio
 * C-5).
 *
 * **Cuenta desde quien jugó y no desde las blancas**, que es la excepción
 * escrita de C-5 (fila 92 del inventario, decidida el 2026-09-22): la misma
 * jugada de las negras sale aquí como 31 % y como 69 % en el visor al que
 * lleva "Ver partida", y se acepta porque la frase nombra el bando —"Tu
 * probabilidad"— y porque girarla rompería el "menos" que hace legible la
 * pérdida. Lo que C-5 sigue prohibiendo es el número suelto, sin frase que
 * diga desde dónde se cuenta. Razonado, con lo que se descartó y dónde queda
 * la frontera, en
 * [ADR-0022](../../../../docs/adr/0022-la-probabilidad-de-victoria-se-cuenta-desde-quien-entrena.md).
 */
export function formatOwnWinPercentLossSentence(before: number, after: number): string {
  return `Tu probabilidad de victoria pasó de ${formatPercent(before, 1)} a ${formatPercent(
    after,
    1,
  )}: ${formatWinPercentPoints(before - after)} menos.`;
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

/** Cómo se llama el rival de una partida de sparring (RF-4.3): "Stockfish
 * (1500)", "Lc0 · Maia".
 *
 * El nombre se componía en dos sitios y desde dos lados —el desplegable de
 * "Nueva partida" lo armaba en el front y la partida lo recibía ya armado del
 * servidor—, así que coincidían carácter a carácter sin que nada lo
 * garantizara (fila 96 del inventario de docs/07-coherencia-ui.md, criterio
 * C-5). Se compone aquí, que es donde vive el formateo, a partir de `engine` y
 * `engine_elo`, que es todo lo que hace falta y lo que la API ya manda.
 *
 * Sin `engineElo` da el nombre a secas, que es lo que necesita el desplegable:
 * ahí la fuerza se elige en su propio campo.
 */
export function formatOpponentName(engine: string, engineElo: number | null = null): string {
  // Lc0 juega con una red Maia y no con un Elo pedido, así que lo que lo
  // identifica es la red; Stockfish, la fuerza a la que se le pidió jugar.
  const name = engine === "lc0" ? `${formatEngineName(engine)} · Maia` : formatEngineName(engine);
  return engineElo === null ? name : `${name} (${engineElo})`;
}

/** Fase de la partida tal como se enseña: "Apertura", "Medio juego", "Final"
 * (RF-3.3).
 *
 * Vivía dentro del panel de estadísticas y subió aquí en cuanto la necesitó la
 * segunda pantalla —el plan semanal de RF-4.5—, que es la regla de `lib/`: en
 * cuanto algo lo usa un segundo sitio, sube en vez de copiarse. */
const PHASE_DISPLAY_NAMES: Record<GamePhase, string> = {
  opening: "Apertura",
  middlegame: "Medio juego",
  endgame: "Final",
};

export function formatPhase(phase: string): string {
  return PHASE_DISPLAY_NAMES[phase as GamePhase] ?? phase;
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
 * pasar el hueco por un dato, y por uno malísimo. El hueco también llega como
 * `null` —un mes sin partidas del control de tiempo de la serie (RF-3.7), o
 * un control del que chess.com no da rating actual—, y las dos formas de no
 * tener rating se enseñan igual (criterio C-5). */
export function formatRating(rating: number | null | undefined): string {
  return rating != null && rating > 0 ? String(rating) : MISSING_VALUE;
}

/** Una tasa por cada cien jugadas: "1.4" (RF-3.7).
 *
 * Un decimal, que es lo que distingue dos meses sin fingir una precisión que
 * no hay. Vive aquí y no en la pantalla porque la misma magnitud se enseña en
 * la tabla de tendencias, en el tooltip de su gráfico y en la frase de
 * `lib/insights.ts`: tres sitios decidiendo por su cuenta cuántos decimales
 * es justo lo que evita el criterio C-5. La unidad no va en el número —"1.4
 * por cada cien jugadas" no cabe en una celda—: la ponen el encabezado de la
 * columna y el pie del gráfico. */
export function formatPerHundredMoves(value: number): string {
  return value.toFixed(1);
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

/** Cómo se nombra una partida cuando hay que darle un título: "Ana - Beto,
 * 12 sept 2026" (RF-6.6).
 *
 * Lo usa el tablero de análisis que se crea a partir de una partida, que
 * necesita un título y no tiene ninguno propio. Vive aquí porque compone
 * nombres y fecha con el mismo `formatDate` que el resto de la aplicación
 * (criterio C-5). */
export function formatBoardTitleFromGame(
  game: Pick<GameSummary, "white_username" | "black_username" | "played_at">,
): string {
  return `${game.white_username} - ${game.black_username}, ${formatDate(game.played_at)}`;
}

/** El mismo título, compuesto desde las cabeceras de un PGN pegado (RF-6.7).
 *
 * `null` si el archivo no nombra a los dos jugadores: sin ellos no hay título
 * que valga más que el que el tablero ya tiene. La fecha del PGN
 * ("2026.09.12", con puntos y a veces con interrogantes) se pasa a ISO para
 * que salga por `formatDate` como la de cualquier otra partida. */
export function formatBoardTitleFromPgnHeaders(headers: Record<string, string>): string | null {
  const { White, Black, Date: playedOn } = headers;
  if (!White || !Black) return null;
  const isoDate = playedOn?.replaceAll(".", "-");
  const day = isoDate && !isoDate.includes("?") ? `, ${formatDate(isoDate)}` : "";
  return `${White} - ${Black}${day}`;
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

/** Con qué motores está analizada una partida, para la columna «Análisis» de
 * la lista (RF-2.5).
 *
 * Los dos datos vienen separados de `GameSummary` —los motores que terminaron
 * y si queda alguno en marcha— porque significan cosas distintas, y aquí se
 * juntan en la frase que se lee: sin decir que hay uno corriendo, una partida
 * recién mandada a analizar se leería igual que una que nadie tocó, y quien
 * elige la tanda la volvería a mandar.
 */
export function formatAnalyzedByEngines(
  engines: string[],
  hasAnalysisInProgress: boolean,
): string {
  const engineNames = engines.map(formatEngineName).join(" · ");
  if (!hasAnalysisInProgress) return engineNames || NOT_ANALYZED;
  return engineNames ? `${engineNames} · analizando…` : "Analizando…";
}
