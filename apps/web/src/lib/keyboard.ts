/** Reglas comunes de los atajos de teclado que escuchan en `window`.
 *
 * Escuchando en la ventana, la tecla llega aunque el foco esté en un control
 * de formulario, y ahí casi siempre es del control y no del tablero: la "o" de
 * un nombre de jugador encendía la capa de ocupación y las flechas del
 * selector de motor movían la partida. La regla vive en un solo sitio en vez
 * de copiada en cada atajo (criterio C-1 de docs/07-coherencia-ui.md).
 *
 * **Son dos preguntas distintas y por eso hay dos funciones.** Un desplegable
 * se queda con las flechas, porque le sirven para elegir opción, pero no tiene
 * texto que deshacer: `Ctrl+Z` sobre él no hace nada, así que retirarle esa
 * tecla al tablero sería perder el atajo a cambio de nada. Un campo de texto sí
 * tiene las dos cosas.
 */

/** ¿El foco está en algo que escribe texto? Lo que se teclea es suyo, y
 * deshacer también. */
export function isTextEntryTarget(target: EventTarget | null): boolean {
  return target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement;
}

/** ¿El foco está en un control de formulario que se maneja con el teclado?
 * Incluye los desplegables, que usan las flechas para elegir opción. */
export function isTypingTarget(target: EventTarget | null): boolean {
  return isTextEntryTarget(target) || target instanceof HTMLSelectElement;
}
