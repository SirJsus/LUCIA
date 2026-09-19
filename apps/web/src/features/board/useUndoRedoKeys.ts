/** Los atajos de deshacer y rehacer del tablero de análisis (RF-6.8).
 *
 * Va aparte, y no dentro de `useMoveNavigationKeys`, porque estas dos teclas
 * son solo del tablero de análisis: en el visor no hay nada que deshacer, y
 * un atajo que existe en una pantalla y en otra no debe estar declarado donde
 * las dos lo leen.
 *
 * Se aceptan las dos convenciones de rehacer —`Ctrl+Y` de Windows y
 * `Ctrl+Mayús+Z` del resto— porque ninguna de las dos es "la" correcta y
 * quien viene de un editor u otro espera la suya. En macOS la tecla es `Cmd`,
 * que el navegador reporta como `metaKey`.
 *
 * Escribiendo en un campo las teclas son del campo: `Ctrl+Z` dentro del
 * `textarea` de importar un PGN tiene que deshacer lo tecleado, no retirar
 * una jugada del tablero (criterio C-1 de docs/07-coherencia-ui.md). Por eso
 * mira `isTextEntryTarget` y no `isTypingTarget`, que es la regla de los
 * atajos de navegación: un desplegable se queda con las flechas, pero no tiene
 * texto que deshacer, y quitarle `Ctrl+Z` al tablero con el foco en el
 * selector de motor sería perder el atajo sin dárselo a nadie.
 */
import { useEffect } from "react";
import { isTextEntryTarget } from "../../lib/keyboard";

export function useUndoRedoKeys({ onUndo, onRedo }: { onUndo: () => void; onRedo: () => void }) {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (!(event.ctrlKey || event.metaKey) || isTextEntryTarget(event.target)) return;
      const key = event.key.toLowerCase();
      if (key !== "z" && key !== "y") return;

      event.preventDefault();
      if (key === "y" || event.shiftKey) onRedo();
      else onUndo();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onUndo, onRedo]);
}
