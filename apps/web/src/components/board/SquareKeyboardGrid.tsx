/** Una rejilla de casillas enfocables **encima** del tablero, para poder
 * usarlo sin ratón (criterio C-1 de docs/07-coherencia-ui.md).
 *
 * Hace falta porque chessground no es accesible por teclado: no pone
 * `tabindex` en ninguna casilla ni escucha teclas. Esta capa no lo sustituye,
 * se le superpone, y se le pasa a `Chessboard` por su hueco `overlay`.
 *
 * **No le quita el ratón a chessground**: la capa entera va con
 * `pointer-events-none`, así que los clics y los arrastres la atraviesan y
 * llegan al tablero de siempre. Lo único que aporta son paradas de foco y la
 * tecla Intro, que no dependen de los eventos de puntero.
 *
 * Una sola parada de tabulador y las flechas para moverse dentro, que es el
 * patrón de cualquier rejilla accesible: 64 paradas de tabulador harían
 * inservible el resto de la pantalla.
 *
 * La usan las dos capas que se dibujan sobre un tablero: el editor de posición
 * (RF-6.1), donde Intro coloca la pieza elegida, y la de ocupación (RF-7.3),
 * donde Intro inspecciona la casilla. Cada una dice con `describeSquare` qué se
 * lee en voz alta, que es lo único que cambia entre las dos.
 */
import { useState } from "react";
import { squaresInReadingOrder, type BoardOrientation } from "./squares";

export function SquareKeyboardGrid({
  orientation,
  describeSquare,
  onActivate,
}: {
  /** Desde qué lado se mira el tablero: la rejilla tiene que recorrerse en el
   * mismo orden en que se ven las casillas, o las flechas irían al revés. */
  orientation: BoardOrientation;
  /** Qué se lee de una casilla: su contenido, su ocupación, lo que aporte la
   * capa que la usa. */
  describeSquare: (square: string) => string;
  onActivate: (square: string) => void;
}) {
  const [focusedSquare, setFocusedSquare] = useState("e4");
  const squares = squaresInReadingOrder(orientation);

  /** Las flechas se mueven por lo que se ve, no por el nombre de la casilla:
   * en la lista en orden de lectura, los lados están a un paso y las filas a
   * ocho, mire quien mire el tablero. */
  function moveFocus(event: React.KeyboardEvent, square: string) {
    const steps: Record<string, [column: number, row: number]> = {
      ArrowLeft: [-1, 0],
      ArrowRight: [1, 0],
      ArrowUp: [0, -1],
      ArrowDown: [0, 1],
    };
    const step = steps[event.key];
    if (!step) return;
    event.preventDefault();
    // Y no llega a `window`: ahí escucha `useMoveNavigationKeys`, y sin esto
    // una flecha movería el foco dentro de la rejilla **y** la partida a la
    // jugada siguiente (criterio C-1). Es el mismo choque que ya se corrigió
    // con el desplegable de motor.
    event.stopPropagation();
    const index = squares.indexOf(square);
    const nextSquare =
      squares[clamp((index % 8) + step[0]) + clamp(Math.floor(index / 8) + step[1]) * 8];
    setFocusedSquare(nextSquare);
    event.currentTarget.parentElement
      ?.querySelector<HTMLButtonElement>(`[data-square="${nextSquare}"]`)
      ?.focus();
  }

  return (
    <div
      role="grid"
      aria-label="Casillas del tablero"
      className="pointer-events-none absolute inset-0 grid grid-cols-8 grid-rows-8"
    >
      {squares.map((square) => (
        <button
          key={square}
          type="button"
          role="gridcell"
          data-square={square}
          tabIndex={square === focusedSquare ? 0 : -1}
          onFocus={() => setFocusedSquare(square)}
          onKeyDown={(event) => moveFocus(event, square)}
          onClick={() => onActivate(square)}
          aria-label={describeSquare(square)}
          className="focus-visible:ring-opacity-90 rounded-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:outline-none"
        />
      ))}
    </div>
  );
}

/** Mantiene una columna o una fila dentro del tablero: en el borde, se queda. */
function clamp(index: number): number {
  return Math.min(Math.max(index, 0), 7);
}
