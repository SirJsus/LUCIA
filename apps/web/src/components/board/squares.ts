/** La geometría del tablero: cómo se llaman las 64 casillas y dónde cae cada
 * una en pantalla según desde qué lado se mire.
 *
 * Vive aparte porque la necesitan cuatro capas que se dibujan sobre el mismo
 * cuadrado y tienen que coincidir casilla a casilla: el propio `Chessboard`
 * (qué casilla hay bajo el puntero), la capa de ocupación (los tintes y los
 * conectores, RF-7), la rejilla enfocable (`SquareKeyboardGrid`) y el cálculo
 * de alcances (`occupancy.ts`). Con una copia de la conversión en cada una,
 * bastaba con equivocarse en un `7 -` para que el tinte y la línea señalaran
 * casillas distintas.
 */
export const FILES = "abcdefgh";

/** Todas las casillas, de a1 a h8. */
export const ALL_SQUARES: string[] = [...FILES].flatMap((file) =>
  [1, 2, 3, 4, 5, 6, 7, 8].map((rank) => `${file}${rank}`),
);

export type BoardOrientation = "white" | "black";

/** Dónde se ve una casilla, contando columnas y filas desde la esquina
 * superior izquierda: así las coloca la rejilla CSS y así las mide el ratón.
 * Mirando desde las blancas arriba está la octava fila; desde las negras, la
 * primera, y las columnas van al revés. */
export function squareScreenCell(
  square: string,
  orientation: BoardOrientation,
): { column: number; row: number } {
  const fileIndex = FILES.indexOf(square[0]);
  const rankIndex = Number(square[1]) - 1;
  return orientation === "white"
    ? { column: fileIndex, row: 7 - rankIndex }
    : { column: 7 - fileIndex, row: rankIndex };
}

/** Las 64 casillas en el orden en que se ven: de izquierda a derecha y de
 * arriba abajo. Es el orden en que las coloca una rejilla de ocho por ocho, y
 * el índice dentro de la lista es `fila * 8 + columna`. */
export function squaresInReadingOrder(orientation: BoardOrientation): string[] {
  return READING_ORDER[orientation];
}

/** Las dos listas se arman una sola vez: `squaresInReadingOrder` se llama en
 * cada render de cada capa y con cada movimiento del ratón. */
const READING_ORDER: Record<BoardOrientation, string[]> = {
  white: buildReadingOrder("white"),
  black: buildReadingOrder("black"),
};

function buildReadingOrder(orientation: BoardOrientation): string[] {
  const squares: string[] = [];
  for (const square of ALL_SQUARES) {
    const { column, row } = squareScreenCell(square, orientation);
    squares[row * 8 + column] = square;
  }
  return squares;
}
