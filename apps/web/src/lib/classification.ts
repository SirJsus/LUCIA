/** Cómo se muestra cada categoría de jugada (RF-2.2) en la interfaz.
 *
 * Los identificadores vienen de `lucia_core.classification` en inglés; las
 * etiquetas visibles van en español, que es el idioma de la interfaz.
 */
import type { MoveClassification } from "@lucia/shared-types";

export interface ClassificationStyle {
  label: string;
  /** Símbolo corto para la lista de jugadas, al estilo de la notación de ajedrez. */
  symbol: string;
  /** Clases de Tailwind para la insignia. */
  className: string;
  /** Color plano, para pintar puntos en el gráfico de evaluación. */
  color: string;
}

const FALLBACK: ClassificationStyle = {
  label: "Sin clasificar",
  symbol: "·",
  className: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
  color: "#94a3b8",
};

const STYLES: Record<MoveClassification, ClassificationStyle> = {
  best: {
    label: "Mejor jugada",
    symbol: "★",
    className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200",
    color: "#10b981",
  },
  excellent: {
    label: "Excelente",
    symbol: "!",
    className: "bg-teal-100 text-teal-800 dark:bg-teal-900/60 dark:text-teal-200",
    color: "#14b8a6",
  },
  good: {
    label: "Buena",
    symbol: "✓",
    className: "bg-sky-100 text-sky-800 dark:bg-sky-900/60 dark:text-sky-200",
    color: "#0ea5e9",
  },
  book: {
    label: "Teoría",
    symbol: "📖",
    className: "bg-stone-200 text-stone-700 dark:bg-stone-700 dark:text-stone-200",
    color: "#a8a29e",
  },
  inaccuracy: {
    label: "Imprecisión",
    symbol: "?!",
    className: "bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200",
    color: "#f59e0b",
  },
  mistake: {
    label: "Error",
    symbol: "?",
    className: "bg-orange-100 text-orange-800 dark:bg-orange-900/60 dark:text-orange-200",
    color: "#f97316",
  },
  blunder: {
    label: "Blunder",
    symbol: "??",
    className: "bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-200",
    color: "#ef4444",
  },
  missed_win: {
    label: "Perdió el mate",
    symbol: "✗",
    className: "bg-fuchsia-100 text-fuchsia-800 dark:bg-fuchsia-900/60 dark:text-fuchsia-200",
    color: "#d946ef",
  },
};

export function classificationStyle(classification: string): ClassificationStyle {
  return STYLES[classification as MoveClassification] ?? FALLBACK;
}

/** Categorías que cuentan como "algo salió mal", para resúmenes y filtros.
 *
 * El tipo es `string[]` y no `MoveClassification[]` porque se compara contra
 * la clasificación que llega de la API, que es una cadena cualquiera; el
 * `satisfies` mantiene la comprobación de que los cuatro valores existen. */
export const MISTAKE_CLASSIFICATIONS: string[] = [
  "inaccuracy",
  "mistake",
  "blunder",
  "missed_win",
] satisfies MoveClassification[];
