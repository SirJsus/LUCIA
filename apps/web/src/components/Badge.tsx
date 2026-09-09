/** Insignia: una etiqueta corta de color sobre un dato.
 *
 * Su forma —esquina redondeada, relleno pequeño, `text-xs`— estaba escrita a
 * mano en seis sitios y ya había divergido en tres rellenos distintos, y cinco
 * de los seis repetían la pareja de colores claro/oscuro
 * (`bg-X-100 text-X-800` + `dark:bg-X-900/60 dark:text-X-200`) a mano
 * (criterio C-2 de docs/07-coherencia-ui.md).
 *
 * Los tonos son los que ya usaba la aplicación; `neutral` es el gris de lo que
 * no significa nada bueno ni malo. Para la clasificación de una jugada, que
 * tiene su propia paleta en `lib/classification.ts`, se pasa `className`.
 */
import type { ReactNode } from "react";

export type BadgeTone = "neutral" | "info" | "success" | "warning" | "danger";

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
  info: "bg-sky-100 text-sky-800 dark:bg-sky-900/60 dark:text-sky-200",
  success: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200",
  warning: "bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200",
  danger: "bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-200",
};

export const BADGE_SHAPE_CLASSES = "rounded px-1.5 py-0.5 text-xs";

export function Badge({
  tone = "neutral",
  className = "",
  title,
  children,
}: {
  tone?: BadgeTone;
  /** Colores propios, para quien ya tiene paleta (la clasificación de jugada). */
  className?: string;
  title?: string;
  children: ReactNode;
}) {
  return (
    <span
      title={title}
      className={`${BADGE_SHAPE_CLASSES} ${className || TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}
