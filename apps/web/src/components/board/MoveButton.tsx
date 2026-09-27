/** El botón que lleva a una posición al pulsarlo: una jugada.
 *
 * Es el control más repetido de la aplicación —lista de jugadas del visor,
 * lista sin analizar, árbol de variantes y líneas del motor— y su receta
 * estaba copiada cuatro veces con tres rellenos distintos y dos formas de
 * marcar "estás aquí" (criterio C-2 de docs/07-coherencia-ui.md).
 *
 * `isCurrent` es la posición en la que está el tablero ahora mismo. Se marca
 * con fondo **y** con negrita a propósito: el fondo solo no vale para quien no
 * distingue bien los colores (C-7).
 */
import type { ButtonHTMLAttributes, ReactNode } from "react";

export interface MoveButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** La posición a la que lleva es la que se está viendo. */
  isCurrent?: boolean;
  children: ReactNode;
}

export function MoveButton({
  isCurrent = false,
  className = "",
  children,
  ...props
}: MoveButtonProps) {
  return (
    <button
      type="button"
      aria-current={isCurrent ? "true" : undefined}
      className={`flex items-center gap-1.5 rounded px-1.5 py-0.5 text-left font-mono transition-colors hover:bg-slate-100 dark:hover:bg-slate-800 ${
        isCurrent ? "bg-indigo-100 font-bold dark:bg-indigo-900/60" : ""
      } ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
