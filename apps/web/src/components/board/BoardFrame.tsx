/** El marco del tablero: a qué medida se dibuja y dónde queda dentro de su
 * columna.
 *
 * Existe porque el mismo tablero salía de dos tamaños. El visor y el tablero
 * de análisis lo montan con `BoardWithEvalBar`, que llevaba el ancho máximo
 * dentro; las tres pantallas de entrenamiento ponen el `Chessboard` pelado, así
 * que ocupaba la columna entera y las piezas cambiaban de tamaño al pasar de
 * una pestaña a otra (fila 107 del inventario de docs/07-coherencia-ui.md,
 * criterio C-2).
 *
 * La medida vive aquí y no en `Chessboard` a propósito: el editor de posición
 * (RF-6.1) monta su tablero sin ella y no tiene por qué heredarla. Envuelve
 * **solo el tablero**; lo que va debajo —la frase de atajos, el panel de
 * ocupación, el navegador de jugadas— ocupa la columna entera, que es como
 * estaba.
 */
import type { ReactNode } from "react";

export function BoardFrame({ children }: { children: ReactNode }) {
  return <div className="mx-auto w-full max-w-[36rem]">{children}</div>;
}
