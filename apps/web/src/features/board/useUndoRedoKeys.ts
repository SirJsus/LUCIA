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
 * una jugada del tablero (criterio C-1 de docs/07-coherencia-ui.md).
 */
import { useEffect } from "react";

export function useUndoRedoKeys({ onUndo, onRedo }: { onUndo: () => void; onRedo: () => void }) {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (
        !(event.ctrlKey || event.metaKey) ||
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement
      ) {
        return;
      }
      const key = event.key.toLowerCase();
      const isRedo = key === "y" || (key === "z" && event.shiftKey);
      if (key !== "z" && key !== "y") return;

      event.preventDefault();
      if (isRedo) onRedo();
      else onUndo();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onUndo, onRedo]);
}
