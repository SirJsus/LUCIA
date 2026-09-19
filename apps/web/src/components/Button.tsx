/** Botón de la aplicación, con las tres variantes que ya existían repartidas a
 * mano por las pantallas (criterio C-2 de docs/07-coherencia-ui.md).
 *
 * Antes de esto la receta de clases estaba copiada quince veces: la coherencia
 * se sostenía con copiar y pegar, y el primer cambio de estilo la habría roto.
 * Las clases viven en `components/styles.ts`, porque también las necesita algo
 * que no puede ser un `button` (un `<Link>` del router).
 *
 * `primary` es la acción principal de la pantalla y hay como mucho una;
 * `secondary` es todo lo demás; `danger` es la que destruye algo.
 */
import type { ButtonHTMLAttributes } from "react";
import { buttonClasses, type ButtonSize, type ButtonVariant } from "./styles";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function Button({
  variant = "secondary",
  size = "md",
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      // `type` por defecto "button": dentro de un formulario, el defecto del
      // navegador es "submit" y un botón cualquiera acabaría enviándolo.
      type={type}
      className={`${buttonClasses(variant, size)} ${className}`}
      {...props}
    />
  );
}
