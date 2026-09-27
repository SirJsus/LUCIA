/** Caja con borde: la unidad de agrupación visual de la aplicación.
 *
 * Su receta de clases estaba repetida once veces (criterio C-2 de
 * docs/07-coherencia-ui.md). Con `title` dibuja además una cabecera separada
 * por una línea, que es la otra forma que ya se usaba; `aside` es lo que va a
 * la derecha de esa cabecera, normalmente un estado ("analizando…").
 */
import type { ReactNode } from "react";
import { PANEL_CLASSES } from "./styles";

export interface PanelProps {
  title?: ReactNode;
  aside?: ReactNode;
  children: ReactNode;
  /** Clases del cuerpo. Por defecto lleva relleno; pásalo vacío cuando el
   * contenido gestione el suyo (una lista con separadores, por ejemplo). */
  bodyClassName?: string;
  className?: string;
}

export function Panel({
  title,
  aside,
  children,
  bodyClassName = "p-3",
  className = "",
}: PanelProps) {
  return (
    <div
      className={`${PANEL_CLASSES} ${className}`}
    >
      {title !== undefined && (
        <div className="flex items-center justify-between gap-2 border-b border-slate-200 px-3 py-2 text-sm font-medium dark:border-slate-800">
          <span>{title}</span>
          {aside}
        </div>
      )}
      <div className={bodyClassName}>{children}</div>
    </div>
  );
}
