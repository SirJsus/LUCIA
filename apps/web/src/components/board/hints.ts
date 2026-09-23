/** Las frases que un tablero pone debajo: qué se puede hacer sin ratón y qué
 * está esperando de quien mira.
 *
 * Van juntas y en un solo sitio porque son las piezas con las que las cinco
 * pantallas con tablero arman su párrafo de pie (`BOARD_HINT_CLASSES`): cada
 * una añade lo suyo —"Arrastra una pieza para responder…", "La línea
 * terminó…"— y encadena estas. Escritas a mano en cada pantalla, el día que
 * cambie una tecla la ayuda mentiría en cuatro sitios (criterio C-1 de
 * docs/07-coherencia-ui.md).
 */

/** Cómo se mueve una pieza sin ratón, en los tableros que aceptan jugadas.
 *
 * Lo hace posible la rejilla enfocable de `Chessboard`
 * (`SquareKeyboardGrid`), que le devuelve la pulsación al `selectSquare` de
 * chessground: el primer Intro toma el origen y el segundo, el destino. Se
 * anuncia aquí porque un atajo que solo vive en el `aria-label` de una casilla
 * no lo descubre quien mira la pantalla (fila 91 del inventario). */
export const KEYBOARD_MOVE_HINT =
  "Con el teclado: Tab lleva al tablero, las flechas recorren las casillas, " +
  "Intro elige origen y destino, y Esc suelta la pieza elegida.";

/** Cómo se enciende la capa de ocupación (RF-7). Nombra la tecla que
 * `OCCUPANCY_TOGGLE_KEY` define en `useOccupancy.ts`: si cambia allí, esta
 * frase es el otro sitio que hay que tocar. */
export const OCCUPANCY_TOGGLE_KEY_HINT = "Con O se enciende y se apaga la capa de ocupación.";

/** Qué es lo que se está viendo cuando la jugada equivocada se queda encima
 * del tablero, en el puzzle (RF-4.1) y en el drill (RF-4.2): los dos la dejan
 * ahí hasta que se pulse el mismo botón, así que la frase que lo nombra tiene
 * que ser la misma (fila 97 del inventario, criterio C-2). */
export const RETRY_AFTER_WRONG_MOVE_HINT =
  "Ahí está tu jugada. Pulsa «Volver a intentarlo» para recuperar la posición.";
