/** Cómo se muestra cada categoría de jugada (RF-2.2) en la interfaz.
 *
 * Los identificadores vienen de `lucia_core.classification` en inglés; las
 * etiquetas visibles van en español, que es el idioma de la interfaz.
 */
import type { MoveClassification } from "@lucia/shared-types";

export interface ClassificationStyle {
  label: string;
  /** La regla por la que se aplica, en una frase. El nombre solo no basta:
   * "Teoría" no dice que las jugadas de libro no se puntúan como acierto de
   * quien las juega (criterio C-6 de docs/07-coherencia-ui.md). */
  description: string;
  /** Símbolo corto para la lista de jugadas, al estilo de la notación de
   * ajedrez. Monocromo a propósito: un emoji se pinta con su propia paleta,
   * ignora el color de la insignia y cambia de dibujo según el sistema. */
  symbol: string;
  /** Clases de Tailwind para la insignia. */
  className: string;
  /** Color plano, para pintar puntos en el gráfico de evaluación. */
  color: string;
}

const FALLBACK: ClassificationStyle = {
  label: "Sin clasificar",
  description: "El análisis no dice de qué tipo es esta jugada.",
  symbol: "·",
  className: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
  color: "#94a3b8",
};

const STYLES: Record<MoveClassification, ClassificationStyle> = {
  best: {
    label: "Mejor jugada",
    description: "Es la que recomendaba el motor.",
    symbol: "★",
    className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200",
    color: "#10b981",
  },
  excellent: {
    label: "Excelente",
    description: "No era la del motor, pero pierde tan poco que da igual.",
    symbol: "!",
    className: "bg-teal-100 text-teal-800 dark:bg-teal-900/60 dark:text-teal-200",
    color: "#14b8a6",
  },
  good: {
    label: "Buena",
    description: "Mantiene la posición: cede algo, pero poco.",
    symbol: "✓",
    className: "bg-sky-100 text-sky-800 dark:bg-sky-900/60 dark:text-sky-200",
    color: "#0ea5e9",
  },
  book: {
    label: "Teoría",
    description:
      "La partida seguía en el libro de aperturas, así que no se puntúa como acierto de quien la juega. Una jugada de libro que hunde la posición sí se clasifica por lo que hizo.",
    symbol: "▤",
    className: "bg-stone-200 text-stone-700 dark:bg-stone-700 dark:text-stone-200",
    color: "#a8a29e",
  },
  inaccuracy: {
    label: "Imprecisión",
    description: "Cede ventaja sin llegar a estropear la posición.",
    symbol: "?!",
    className: "bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200",
    color: "#f59e0b",
  },
  mistake: {
    label: "Error",
    description: "Cambia la posición a peor de forma clara.",
    symbol: "?",
    className: "bg-orange-100 text-orange-800 dark:bg-orange-900/60 dark:text-orange-200",
    color: "#f97316",
  },
  blunder: {
    label: "Blunder",
    description: "Tira media partida de una jugada.",
    symbol: "??",
    className: "bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-200",
    color: "#ef4444",
  },
  missed_win: {
    label: "Perdió el mate",
    description: "Había mate forzado y la jugada lo dejó escapar.",
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
