/** Cómo se nombran en la interfaz los patrones que extrae
 * `lucia_core.insights` (RF-2.8, RF-3.4, RF-3.5).
 *
 * Los identificadores llegan de la API en inglés (`time`, `only_move`…);
 * aquí se traducen una sola vez, con su explicación, para que "táctico" o
 * "solo valía una jugada" signifiquen lo mismo en todas las pantallas
 * (criterios C-5 y C-6 de docs/07-coherencia-ui.md).
 *
 * Las descripciones no son adorno: son la regla con la que el núcleo decidió.
 * Sin ellas, "posicional" es una palabra que el usuario tiene que adivinar.
 */
import type { CriticalMomentKind, MistakeType } from "@lucia/shared-types";
import type { BadgeTone } from "../components/Badge";

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
