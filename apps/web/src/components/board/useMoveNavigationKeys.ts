/** Los atajos de teclado que acompañan a `MoveNavigator`: ← → recorren las
 * jugadas e Inicio/Fin saltan a los extremos.
 *
 * Va aparte del componente porque escucha en `window` —el foco no está en los
 * botones— y así las dos pantallas que recorren jugadas —el visor (RF-5) y el
 * tablero de análisis (RF-6); las tres de entrenamiento tienen tablero pero
 * nada que recorrer— responden a las mismas teclas con la misma regla, en vez
 * de tener cada una su copia del listener (criterios C-1 y C-2 de
 * docs/07-coherencia-ui.md).
 *
 * Escribiendo en un campo —o eligiendo en un desplegable— las flechas son del
 * campo, no del tablero: el selector de motor de las dos pantallas cambiaba de
 * motor y movía el tablero con la misma pulsación.
 */
import { useEffect } from "react";
import { isTypingTarget } from "../../lib/keyboard";
import type { MoveNavigatorProps } from "./MoveNavigator";

type MoveNavigationHandlers = Pick<
  MoveNavigatorProps,
  "onFirst" | "onPrevious" | "onNext" | "onLast"
>;

export function useMoveNavigationKeys({
  onFirst,
  onPrevious,
  onNext,
  onLast,
}: MoveNavigationHandlers) {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (isTypingTarget(event.target)) return;
      const actions: Record<string, () => void> = {
        ArrowLeft: onPrevious,
        ArrowRight: onNext,
        Home: onFirst,
        End: onLast,
      };
      const action = actions[event.key];
      if (action) {
        event.preventDefault();
        action();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onFirst, onPrevious, onNext, onLast]);
}
