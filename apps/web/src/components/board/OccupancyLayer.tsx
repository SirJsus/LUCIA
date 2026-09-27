/** La capa de ocupación dibujada **encima** del tablero (RF-7.1 a RF-7.7).
 *
 * La dibuja `Chessboard` cuando se le pasa un controlador por su propiedad
 * `occupancyController`, así que ocupa exactamente el cuadrado del tablero en
 * las cinco pantallas que la tienen y no le quita el ratón a chessground: todo
 * lo que pinta va con `pointer-events-none` y la casilla bajo el puntero la
 * resuelve el propio `Chessboard` por geometría.
 *
 * Son dos capas apiladas, cada una con un trabajo:
 *
 * 1. **Los tintes**, una casilla por celda. En mapa de calor (RF-7.1) el color
 *    dice quién domina y la intensidad, por cuánto; en cobertura (RF-7.2),
 *    hasta dónde llega el bando que se está mirando.
 * 2. **Las líneas**, en SVG. Los conectores pieza → casilla van continuos y los
 *    rayos X discontinuos, que es justamente lo que pide RF-7.5 para que no se
 *    confundan con un ataque directo.
 *
 * La rejilla enfocable con la que se inspecciona una casilla sin ratón (RF-7.3
 * con el criterio C-1) **no está aquí**: la dibuja `Chessboard`, que es quien
 * puede darle a Intro los dos trabajos que tiene una casilla —elegirla para
 * inspeccionarla y elegirla como origen o destino de una jugada— sin que salgan
 * dos rejillas superpuestas con dos juegos de paradas de foco (fila 91 del
 * inventario). De aquí sale solo `describeSquareOccupancy`, que es lo que esa
 * rejilla lee en voz alta cuando la capa está encendida.
 *
 * **Ningún significado va solo en el color** (criterio C-7): cada casilla con
 * atacantes lleva su número encima, las clavadas se marcan con borde a rayas y
 * las colgadas con borde continuo, y el panel de al lado repite todo en
 * palabras.
 */
import { coverageFrom, type OccupancyMap } from "./occupancy";
import { type PieceColor } from "./pieces";
import { squareScreenCell, squaresInReadingOrder, type BoardOrientation } from "./squares";
import type { OccupancyController } from "./useOccupancy";

/** Los colores de la capa, en componentes RGB sueltos para poder graduarles la
 * opacidad. Azul para las blancas y naranja para las negras —y no blanco y
 * negro, que se perderían sobre las casillas del propio tablero—; gris para lo
 * disputado, que no es de nadie. Se configurarán por separado del tema general
 * cuando llegue RF-8.3. */
const TINT_RGB_BY_COLOR: Record<PieceColor, string> = {
  w: "14 165 233",
  b: "234 88 12",
};
const CONTESTED_TINT_RGB = "100 116 139";

/** Cuánto tiñe una casilla según cuántas piezas la alcanzan. La capa se dibuja
 * **encima** de las piezas, así que la escala arranca baja y se corta pronto:
 * el primer atacante ya se tiene que ver y el cuarto no puede llegar a tapar
 * la pieza que hay debajo. */
function tintOpacity(attackerCount: number): number {
  return Math.min(0.15 + 0.1 * (attackerCount - 1), 0.45);
}

export function OccupancyLayer({
  controller,
  orientation,
}: {
  controller: OccupancyController;
  orientation: BoardOrientation;
}) {
  const { occupancy } = controller;
  if (!occupancy) return null;

  return (
    <>
      <div className="pointer-events-none absolute inset-0 grid grid-cols-8 grid-rows-8">
        {squaresInReadingOrder(orientation).map((square) => (
          <OccupancySquare
            key={square}
            square={square}
            occupancy={occupancy}
            controller={controller}
          />
        ))}
      </div>

      <svg
        viewBox="0 0 8 8"
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 size-full"
      >
        {buildOccupancyLines(controller, occupancy).map((line) => {
          const [fromX, fromY] = squareCenter(line.from, orientation);
          const [toX, toY] = squareCenter(line.to, orientation);
          return (
            <line
              key={`${line.from}${line.to}${line.isXray ? "x" : "d"}`}
              x1={fromX}
              y1={fromY}
              x2={toX}
              y2={toY}
              stroke={`rgb(${TINT_RGB_BY_COLOR[line.color]} / ${line.isFocused ? 0.85 : 0.2})`}
              strokeWidth={line.isFocused ? 0.05 : 0.03}
              strokeLinecap="round"
              // La línea discontinua es lo que distingue un rayo X de un
              // ataque directo sin recurrir al color (RF-7.5 y criterio C-7).
              strokeDasharray={line.isXray ? "0.12 0.12" : undefined}
            />
          );
        })}
      </svg>
    </>
  );
}

/** El tinte y las marcas de una casilla. */
function OccupancySquare({
  square,
  occupancy,
  controller,
}: {
  square: string;
  occupancy: OccupancyMap;
  controller: OccupancyController;
}) {
  const { mode, coverageColor, focusedPieceSquare, selectedSquare, marks } = controller;
  const { directAttacks, balance } = occupancy.squares[square];
  const coveringAttacks =
    mode === "coverage"
      ? directAttacks[coverageColor].filter(
          (attack) => !focusedPieceSquare || attack.from === focusedPieceSquare,
        )
      : [];
  const tint =
    mode === "heatmap"
      ? heatmapTint(balance, directAttacks.w.length + directAttacks.b.length)
      : coveringAttacks.length > 0
        ? { color: TINT_RGB_BY_COLOR[coverageColor], opacity: tintOpacity(coveringAttacks.length) }
        : null;

  // Qué número se lee encima: en mapa de calor, el balance con su signo —"+2"
  // es "dos atacantes blancos de más"—; en cobertura, cuántas piezas del bando
  // llegan. El signo y el número son lo que sostiene el significado cuando el
  // color no se distingue (criterio C-7).
  const countLabel =
    mode === "heatmap"
      ? balance !== 0
        ? `${balance > 0 ? "+" : "−"}${Math.abs(balance)}`
        : directAttacks.w.length > 0
          ? "="
          : ""
      : coveringAttacks.length > 0
        ? String(coveringAttacks.length)
        : "";

  const markClasses = [
    marks.pinned &&
      occupancy.pinnedSquares.includes(square) &&
      "outline-dashed outline-2 outline-amber-500",
    marks.hanging &&
      occupancy.hangingSquares.includes(square) &&
      "outline outline-2 outline-red-600",
    square === selectedSquare && "ring-2 ring-inset ring-indigo-500",
  ].filter(Boolean);

  return (
    <div className={`relative -outline-offset-2 ${markClasses.join(" ")}`}>
      {tint && (
        <div
          className="absolute inset-0"
          style={{ backgroundColor: `rgb(${tint.color} / ${tint.opacity})` }}
        />
      )}
      {/* El número va arriba a la derecha y en blanco con sombra: es la esquina
          que chessground deja libre —las coordenadas van a la izquierda y
          abajo—, y la sombra es lo que lo hace legible tanto sobre la casilla
          clara como sobre la oscura.

          El tamaño es el único valor fuera de la escala de la aplicación: una
          casilla mide un octavo del tablero —unos 40 px— y `text-xs`, el
          escalón más pequeño, taparía la pieza que hay debajo. */}
      {countLabel && (
        <span className="absolute top-0 right-0.5 text-[0.55rem] leading-tight font-semibold text-white [text-shadow:0_1px_2px_rgb(0_0_0/0.9)]">
          {countLabel}
        </span>
      )}
    </div>
  );
}

/** El color de una casilla en el mapa de calor (RF-7.1): de quien tenga más
 * atacantes directos, gris si empatan con al menos uno, y nada si no la alcanza
 * nadie. */
function heatmapTint(
  balance: number,
  attackerCount: number,
): { color: string; opacity: number } | null {
  if (balance !== 0) {
    return {
      color: TINT_RGB_BY_COLOR[balance > 0 ? "w" : "b"],
      opacity: tintOpacity(Math.abs(balance)),
    };
  }
  return attackerCount > 0 ? { color: CONTESTED_TINT_RGB, opacity: 0.18 } : null;
}

interface OccupancyLine {
  from: string;
  to: string;
  color: PieceColor;
  isXray: boolean;
  /** Resaltada: es la cobertura de la pieza que se está mirando, no el fondo. */
  isFocused: boolean;
}

/** Qué conectores se dibujan (RF-7.2 y RF-7.5).
 *
 * Con una pieza señalada o fijada, solo los suyos y bien visibles: es la
 * respuesta a "¿hasta dónde llega esta pieza?". Sin ninguna, el sub-modo de
 * cobertura dibuja los de todo el bando muy atenuados —la trama que deja ver la
 * forma del control sin taparlo— y el mapa de calor no dibuja ninguno, porque
 * ahí el color ya lo cuenta y sesenta líneas lo harían ilegible.
 */
function buildOccupancyLines(
  controller: OccupancyController,
  occupancy: OccupancyMap,
): OccupancyLine[] {
  const { mode, coverageColor, focusedPieceSquare, marks } = controller;
  const originSquares = focusedPieceSquare
    ? [focusedPieceSquare]
    : mode === "coverage"
      ? Object.keys(occupancy.pieces).filter(
          (square) => occupancy.pieces[square].color === coverageColor,
        )
      : [];

  return originSquares.flatMap((from) => {
    const coverage = coverageFrom(occupancy, from);
    const color = occupancy.pieces[from].color;
    const isFocused = from === focusedPieceSquare;
    return [
      ...coverage.directSquares.map((to) => ({ from, to, color, isXray: false, isFocused })),
      ...(marks.xray
        ? coverage.xraySquares.map((to) => ({ from, to, color, isXray: true, isFocused }))
        : []),
    ];
  });
}

/** El centro de una casilla en el sistema de coordenadas del SVG, que es el
 * tablero medido en casillas (0 a 8). */
function squareCenter(square: string, orientation: BoardOrientation): [x: number, y: number] {
  const { column, row } = squareScreenCell(square, orientation);
  return [column + 0.5, row + 0.5];
}
