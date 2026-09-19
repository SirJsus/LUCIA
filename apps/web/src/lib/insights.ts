/** Cómo se nombran en la interfaz los patrones que extrae
 * `lucia_core.insights` (RF-2.8, RF-3.4, RF-3.5) y cómo se cuenta en palabras
 * su evolución (RF-3.7, `formatTrendSentence`).
 *
 * Lo usan el visor (momentos críticos) y el dashboard (tipos de error, tramos
 * de reloj y la frase de tendencia), que son las dos pantallas donde el mismo
 * patrón tiene que llamarse igual.
 *
 * Los identificadores llegan de la API en inglés (`time`, `only_move`…);
 * aquí se traducen una sola vez, con su explicación, para que "táctico" o
 * "solo valía una jugada" signifiquen lo mismo en todas las pantallas
 * (criterios C-5 y C-6 de docs/07-coherencia-ui.md).
 *
 * Las descripciones no son adorno: son la regla con la que el núcleo decidió.
 * Sin ellas, "posicional" es una palabra que el usuario tiene que adivinar.
 */
import type { CriticalMomentKind, MistakeType, TrendChange } from "@lucia/shared-types";
import type { BadgeTone } from "../components/Badge";
import { formatPerHundredMoves } from "./format";

export interface PatternStyle {
  label: string;
  description: string;
  tone: BadgeTone;
}

const MISTAKE_TYPE_STYLES: Record<MistakeType, PatternStyle> = {
  time: {
    label: "Con el reloj encima",
    description: "Se jugó con menos de veinte segundos: la causa fue el tiempo, no la posición.",
    tone: "warning",
  },
  tactical: {
    label: "Táctico",
    description: "El motor proponía una captura o un jaque: había algo concreto que ver.",
    tone: "danger",
  },
  endgame: {
    label: "De final",
    description: "Ya era un final y no había una jugada concreta que encontrar: es técnica.",
    tone: "info",
  },
  positional: {
    label: "Posicional",
    description: "No había táctica ni apuro de tiempo: se eligió mal el plan.",
    tone: "neutral",
  },
};

const FALLBACK_STYLE: PatternStyle = {
  label: "Sin clasificar",
  description: "",
  tone: "neutral",
};

export function mistakeTypeStyle(mistakeType: string): PatternStyle {
  return MISTAKE_TYPE_STYLES[mistakeType as MistakeType] ?? FALLBACK_STYLE;
}

const CRITICAL_MOMENT_STYLES: Record<CriticalMomentKind, PatternStyle> = {
  only_move: {
    label: "Solo valía una jugada",
    description:
      "El motor veía una única forma de sostener la posición: la segunda mejor perdía mucho.",
    tone: "info",
  },
  swing: {
    label: "Cambió de manos",
    description: "La jugada cruzó el 50 % de probabilidad de victoria: la partida se dio la vuelta.",
    tone: "danger",
  },
  missed_chance: {
    label: "Ocasión perdida",
    description: "Había una posición ganada y se escapó.",
    tone: "warning",
  },
};

export function criticalMomentStyle(kind: string): PatternStyle {
  return CRITICAL_MOMENT_STYLES[kind as CriticalMomentKind] ?? FALLBACK_STYLE;
}

/** El tramo de reloj de `TimeBucketStats`, en palabras: el techo llega como
 * segundos, o `null` para el tramo holgado. */
export function formatTimeLeftBucket(maxSecondsLeft: number | null): string {
  if (maxSecondsLeft === null) return "más de 1 min";
  if (maxSecondsLeft >= 60) return `menos de ${Math.round(maxSecondsLeft / 60)} min`;
  return `menos de ${maxSecondsLeft} s`;
}

/** Por debajo de esta diferencia se considera que nada se ha movido: con un
 * decimal, "sube 0.0 puntos" es una frase que no dice nada. */
const TREND_NOISE_THRESHOLD = 0.05;

/** La comparación del último mes con los anteriores, en una frase (RF-3.7).
 *
 * El número solo no se interpreta: en precisión subir es mejorar y en errores
 * subir es empeorar, así que la frase lo dice con palabras en vez de dejar al
 * usuario deducirlo del signo (criterio C-6 de docs/07-coherencia-ui.md).
 */
export function formatTrendSentence(change: TrendChange): string {
  // "Respecto a el mes anterior" no es castellano: la contracción obliga a
  // llevarse la preposición dentro de la referencia.
  const referencePhrase =
    change.baseline_months === 1
      ? "al mes anterior"
      : `a los ${change.baseline_months} meses anteriores`;
  const accuracyPhrase = isNegligibleChange(change.accuracy_change)
    ? "tu precisión se mantiene"
    : `tu precisión ${change.accuracy_change > 0 ? "sube" : "baja"} ${formatAccuracyPoints(change.accuracy_change)} puntos`;
  const formattedMistakeRate = formatPerHundredMoves(Math.abs(change.mistake_rate_change));
  const mistakesPhrase = isNegligibleChange(change.mistake_rate_change)
    ? "los errores siguen igual"
    : `los errores ${change.mistake_rate_change > 0 ? "suben" : "bajan"} ${formattedMistakeRate} por cada cien jugadas`;
  return `Respecto ${referencePhrase}, ${accuracyPhrase} y ${mistakesPhrase}.`;
}

function isNegligibleChange(change: number): boolean {
  return Math.abs(change) < TREND_NOISE_THRESHOLD;
}

/** Los puntos de precisión ganados o perdidos, sin el signo: de "sube" o
 * "baja" ya se encarga el verbo. Un decimal, el mismo que enseña la columna
 * "Precisión" de la tabla de tendencias. */
function formatAccuracyPoints(change: number): string {
  return Math.abs(change).toFixed(1);
}
