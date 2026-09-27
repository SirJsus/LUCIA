/** Un campo de formulario con su etiqueta encima y su ayuda debajo.
 *
 * La receta estaba escrita de dos formas distintas —`flex flex-col gap-1` en
 * las barras de filtros, `mb-1 block` en los formularios de sincronizar, crear
 * tablero y configurar motores— para el mismo resultado visual, y la ayuda
 * unas veces se enseñaba y otras se escondía en un `title` (criterios C-2 y
 * C-6 de docs/07-coherencia-ui.md).
 *
 * La etiqueta envuelve al control, así que no hace falta emparejarlos con
 * `for`/`id`: pulsar el texto lleva el foco al campo igual.
 */
import type { ReactNode } from "react";

export function FieldLabel({
  label,
  hint,
  children,
}: {
  label: ReactNode;
  /** Lo que hay que saber para usarlo, en una línea. Se enseña; no es un
   * `title`. */
  hint?: ReactNode;
  children: ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="opacity-70">{label}</span>
      {children}
      {hint && <span className="max-w-52 text-xs opacity-60">{hint}</span>}
    </label>
  );
}
