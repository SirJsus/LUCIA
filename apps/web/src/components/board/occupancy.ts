/** Ocupación del tablero (RF-7.1 a RF-7.7): quién ataca y quién defiende cada
 * una de las 64 casillas de una posición.
 *
 * Es lógica pura y se calcula **en el cliente, sin motor**: no hace falta
 * evaluar nada, solo mirar de dónde alcanza cada pieza. Por eso vive aparte de
 * los componentes y se prueba sola (`__tests__/occupancy.test.ts`); quien la
 * enseña es `OccupancyLayer` y quien la explica en palabras, `OccupancyPanel`.
 *
 * **De dónde sale la posición y a dónde va el resultado**: entra un FEN —el de
 * la jugada que se está viendo en el visor (RF-5), el del nodo actual del
 * tablero de análisis (RF-6) o el de la posición que hay en juego en las tres
 * pantallas de entrenamiento con tablero (RF-4)— y sale un `OccupancyMap` que
 * las cinco pintan igual. No se guarda nada: se recalcula al cambiar de
 * posición.
 *
 * **Los alcances se generan a mano y no con `attackers()` de chess.js**, que
 * devuelve solo las casillas de origen. Aquí hacen falta tres cosas más que
 * ese atajo no da: qué pieza ataca desde cada una (para ordenar por valor,
 * RF-7.3), los rayos X aparte del conteo directo (RF-7.5), y si la pieza que
 * ataca está clavada (RF-7.6). Recorrer las líneas una vez las saca las tres.
 *
 * Las reglas de conteo de RF-7.7 caen solas de generarlo así: el rey alcanza
 * sus ocho casillas como cualquier otra pieza, el peón alcanza sus dos
 * diagonales y no la casilla de delante, y la casilla de captura al paso —que
 * está vacía— la alcanza el peón que podría capturar ahí, sin tener que
 * tratarla como un caso especial.
 */
import { Chess } from "chess.js";
import {
  colorName,
  otherColor,
  pieceName,
  pieceValue,
  type PieceColor,
  type PieceRole,
} from "./pieces";
import { ALL_SQUARES, FILES } from "./squares";

/** Un alcance sobre una casilla: una pieza que la ataca o la defiende. */
export interface Attack {
  /** Desde dónde se ataca; la casilla donde está la pieza. */
  from: string;
  role: PieceRole;
  color: PieceColor;
  /** Valor convencional de la pieza, para ordenar (RF-7.3) y para decidir qué
   * está colgado (RF-7.4). */
  value: number;
  /** La pieza está clavada contra su rey: sigue contando como atacante
   * —capturar daría jaque—, pero no puede moverse legalmente (RF-7.6). */
  isPinned: boolean;
  /** Si es un rayo X, la casilla de la pieza que se interpone; `null` si el
   * ataque es directo (RF-7.5). */
  throughSquare: string | null;
}

/** Lo que pasa en una casilla: quién llega directamente, quién a través de
 * otra pieza, y cómo queda el balance. */
export interface SquareOccupancy {
  /** Ataques directos de cada bando. Son los únicos que cuentan (RF-7.5). */
  directAttacks: Record<PieceColor, Attack[]>;
  /** Rayos X: baterías propias (torre tras torre) y líneas a través de una
   * pieza rival. Se enseñan aparte y **nunca** se suman al balance (RF-7.5). */
  xrayAttacks: Record<PieceColor, Attack[]>;
  /** Atacantes directos blancos menos negros. Es lo que colorea el mapa de
   * calor (RF-7.1): positivo dominio blanco, negativo dominio negro, cero con
   * atacantes es una casilla disputada y cero sin ellos, tierra de nadie. */
  balance: number;
}

/** Una casilla a la que llega una pieza, y a través de qué. `throughSquare` en
 * `null` es un alcance directo; con valor, un rayo X (RF-7.5). */
interface Reach {
  square: string;
  throughSquare: string | null;
}

export interface OccupancyPiece {
  role: PieceRole;
  color: PieceColor;
}

export interface OccupancyMap {
  /** Las 64 casillas, por nombre ("e4"). Están todas, también las vacías. */
  squares: Record<string, SquareOccupancy>;
  /** Qué pieza hay en cada casilla ocupada. */
  pieces: Record<string, OccupancyPiece>;
  /** Casillas con una pieza clavada contra su propio rey (RF-7.6). */
  pinnedSquares: string[];
  /** Casillas con una pieza colgada: atacada y sin defensa, o atacada por una
   * pieza de menor valor (RF-7.4). */
  hangingSquares: string[];
  /** A quién le toca mover. Es el bando que enseña por defecto el sub-modo de
   * cobertura directa (RF-7.2). */
  turn: PieceColor;
}

/** Los cuatro pasos rectos y los cuatro diagonales, que combinados dan los
 * movimientos de torre, alfil, dama y rey. */
const STRAIGHT_STEPS: [file: number, rank: number][] = [
  [1, 0],
  [-1, 0],
  [0, 1],
  [0, -1],
];
const DIAGONAL_STEPS: [file: number, rank: number][] = [
  [1, 1],
  [1, -1],
  [-1, 1],
  [-1, -1],
];
const KNIGHT_STEPS: [file: number, rank: number][] = [
  [1, 2],
  [2, 1],
  [2, -1],
  [1, -2],
  [-1, -2],
  [-2, -1],
  [-2, 1],
  [-1, 2],
];

/** Las ocho direcciones de la dama, que son también las del rey: este da uno
 * solo de esos pasos y aquella recorre la línea entera. */
const QUEEN_STEPS: [file: number, rank: number][] = [...STRAIGHT_STEPS, ...DIAGONAL_STEPS];

/** Por dónde se desliza cada pieza de largo alcance. Quien no está aquí no
 * desliza, y eso es justo lo que decide si una clavada es tal (RF-7.6). */
const SLIDING_STEPS: Partial<Record<PieceRole, [file: number, rank: number][]>> = {
  r: STRAIGHT_STEPS,
  b: DIAGONAL_STEPS,
  q: QUEEN_STEPS,
};

/** Calcula la ocupación de una posición, o `null` si el FEN no se puede leer
 * —el tablero de análisis pasa por una posición vacía mientras carga—. */
export function computeOccupancy(fen: string): OccupancyMap | null {
  const pieces = readPiecesFromFen(fen);
  if (!pieces) return null;

  const turn: PieceColor = fen.split(" ")[1] === "b" ? "b" : "w";
  const pinnedSquares = Object.entries(pieces)
    .filter(([square, piece]) => isPinnedToOwnKing(pieces, square, piece))
    .map(([square]) => square);

  const squares: Record<string, SquareOccupancy> = {};
  for (const square of ALL_SQUARES) {
    squares[square] = {
      directAttacks: { w: [], b: [] },
      xrayAttacks: { w: [], b: [] },
      balance: 0,
    };
  }

  for (const [from, piece] of Object.entries(pieces)) {
    const isPinned = pinnedSquares.includes(from);
    for (const reach of reachesOf(pieces, from, piece)) {
      const attack: Attack = {
        from,
        role: piece.role,
        color: piece.color,
        value: pieceValue(piece.role),
        isPinned,
        throughSquare: reach.throughSquare,
      };
      const reachedOccupancy = squares[reach.square];
      const attacksByColor =
        reach.throughSquare === null
          ? reachedOccupancy.directAttacks
          : reachedOccupancy.xrayAttacks;
      attacksByColor[piece.color].push(attack);
    }
  }

  for (const square of ALL_SQUARES) {
    const { directAttacks } = squares[square];
    squares[square].balance = directAttacks.w.length - directAttacks.b.length;
  }

  const hangingSquares = findHangingSquares(squares, pieces);
  return { squares, pieces, pinnedSquares, hangingSquares, turn };
}

/** Las casillas que alcanza una pieza desde donde está, directas y por rayo X.
 *
 * Una pieza de largo alcance recorre su línea hasta topar: todo lo anterior y
 * la casilla del tope son ataque directo (la del tope también, porque ahí es
 * donde captura o defiende). Pasado ese tope sigue el rayo X, hasta la
 * siguiente pieza incluida, y ahí se corta: RF-7.5 habla de líneas a través de
 * **una** pieza, y encadenar más sería dibujar líneas que no significan nada.
 */
function reachesOf(
  pieces: Record<string, OccupancyPiece>,
  from: string,
  piece: OccupancyPiece,
): Reach[] {
  if (piece.role === "p") {
    // Solo las capturas en diagonal: el peón avanza a la casilla de delante,
    // pero no la ataca ni la defiende (RF-7.7).
    const forward = piece.color === "w" ? 1 : -1;
    return [-1, 1]
      .map((sideStep) => stepFrom(from, sideStep, forward))
      .filter((square): square is string => square !== null)
      .map((square) => ({ square, throughSquare: null }));
  }

  // El caballo salta y el rey da un paso: en los dos casos, lo que alcanzan es
  // la lista de pasos sin recorrer ninguna línea (RF-7.7, el rey cuenta).
  const singleSteps = piece.role === "n" ? KNIGHT_STEPS : piece.role === "k" ? QUEEN_STEPS : null;
  if (singleSteps) {
    return singleSteps
      .map(([file, rank]) => stepFrom(from, file, rank))
      .filter((square): square is string => square !== null)
      .map((square) => ({ square, throughSquare: null }));
  }

  const reaches: Reach[] = [];
  for (const [fileStep, rankStep] of SLIDING_STEPS[piece.role] ?? []) {
    let square = stepFrom(from, fileStep, rankStep);
    let throughSquare: string | null = null;
    while (square) {
      reaches.push({ square, throughSquare });
      if (pieces[square]) {
        if (throughSquare !== null) break; // segunda pieza: el rayo X acaba aquí
        throughSquare = square;
      }
      square = stepFrom(square, fileStep, rankStep);
    }
  }
  return reaches;
}

/** Piezas colgadas (RF-7.4): las atacadas que nadie defiende, y las atacadas
 * por una pieza que vale menos que ellas —cambiarse por ella ya es perder
 * material aunque haya defensa—.
 *
 * El rey queda fuera: un rey atacado está en jaque, que es otra cosa y la
 * pantalla ya la cuenta de otra manera.
 */
function findHangingSquares(
  squares: Record<string, SquareOccupancy>,
  pieces: Record<string, OccupancyPiece>,
): string[] {
  return Object.entries(pieces)
    .filter(([square, piece]) => {
      if (piece.role === "k") return false;
      const attackers = squares[square].directAttacks[otherColor(piece.color)];
      if (attackers.length === 0) return false;
      const defenders = squares[square].directAttacks[piece.color];
      const cheapestAttackerValue = Math.min(...attackers.map((attack) => attack.value));
      return defenders.length === 0 || cheapestAttackerValue < pieceValue(piece.role);
    })
    .map(([square]) => square);
}

/** ¿Esta pieza está clavada contra su propio rey? (RF-7.6)
 *
 * Lo está si el rey, ella y una pieza rival de largo alcance están en la misma
 * línea, en ese orden, sin nada más entre medias. Se comprueba con geometría y
 * no pidiéndole las jugadas legales a chess.js, porque la respuesta hace falta
 * para las piezas de **los dos** bandos y chess.js solo calcula las del que
 * tiene el turno.
 */
function isPinnedToOwnKing(
  pieces: Record<string, OccupancyPiece>,
  square: string,
  piece: OccupancyPiece,
): boolean {
  if (piece.role === "k") return false;
  const kingSquare = Object.keys(pieces).find(
    (each) => pieces[each].role === "k" && pieces[each].color === piece.color,
  );
  if (!kingSquare) return false;

  const step = directionBetween(kingSquare, square);
  if (!step) return false;

  // Del rey hasta la pieza no puede haber nada: si hay algo, el clavado sería
  // eso y no esta pieza.
  for (let betweenSquare = stepFrom(kingSquare, ...step); betweenSquare !== square;) {
    if (betweenSquare === null || pieces[betweenSquare]) return false;
    betweenSquare = stepFrom(betweenSquare, ...step);
  }

  // Pasada la pieza, la primera que aparezca tiene que ser rival y deslizarse
  // justo por esta línea.
  for (
    let beyondSquare = stepFrom(square, ...step);
    beyondSquare !== null;
    beyondSquare = stepFrom(beyondSquare, ...step)
  ) {
    const candidatePinner = pieces[beyondSquare];
    if (!candidatePinner) continue;
    return (
      candidatePinner.color !== piece.color &&
      (SLIDING_STEPS[candidatePinner.role] ?? []).some(
        ([file, rank]) => file === step[0] && rank === step[1],
      )
    );
  }
  return false;
}

/** El paso unitario que lleva de una casilla a otra, o `null` si no están en
 * la misma fila, columna ni diagonal. */
function directionBetween(from: string, to: string): [file: number, rank: number] | null {
  const fileDistance = FILES.indexOf(to[0]) - FILES.indexOf(from[0]);
  const rankDistance = Number(to[1]) - Number(from[1]);
  const aligned =
    fileDistance === 0 || rankDistance === 0 || Math.abs(fileDistance) === Math.abs(rankDistance);
  if (!aligned || (fileDistance === 0 && rankDistance === 0)) return null;
  return [Math.sign(fileDistance), Math.sign(rankDistance)];
}

/** La casilla que queda al dar un paso desde otra, o `null` si cae fuera. */
function stepFrom(square: string, fileStep: number, rankStep: number): string | null {
  const file = FILES.indexOf(square[0]) + fileStep;
  const rank = Number(square[1]) + rankStep;
  if (file < 0 || file > 7 || rank < 1 || rank > 8) return null;
  return `${FILES[file]}${rank}`;
}

/** Lee las piezas del FEN con chess.js, que es quien sabe si el FEN es válido.
 * Solo se le pide eso: el resto del cálculo es de aquí.
 *
 * Se exporta porque la rejilla enfocable de `Chessboard` necesita decir qué hay
 * en cada casilla también con la capa de ocupación apagada (fila 91 del
 * inventario de docs/07-coherencia-ui.md). */
export function readPiecesFromFen(fen: string): Record<string, OccupancyPiece> | null {
  let board;
  try {
    board = new Chess(fen).board();
  } catch {
    return null;
  }
  const pieces: Record<string, OccupancyPiece> = {};
  for (const cell of board.flat()) {
    if (cell) pieces[cell.square] = { role: cell.type as PieceRole, color: cell.color };
  }
  return pieces;
}

/** Las casillas que cubre la pieza de una casilla, para el sub-modo de
 * cobertura (RF-7.2) y para dibujar sus conectores. */
export function coverageFrom(
  occupancy: OccupancyMap,
  from: string,
): { directSquares: string[]; xraySquares: string[] } {
  const directSquares: string[] = [];
  const xraySquares: string[] = [];
  for (const square of ALL_SQUARES) {
    const { directAttacks, xrayAttacks } = occupancy.squares[square];
    if ([...directAttacks.w, ...directAttacks.b].some((attack) => attack.from === from)) {
      directSquares.push(square);
    }
    if ([...xrayAttacks.w, ...xrayAttacks.b].some((attack) => attack.from === from)) {
      xraySquares.push(square);
    }
  }
  return { directSquares, xraySquares };
}

/** Los alcances de una casilla ordenados de la pieza más valiosa a la menos,
 * que es como se leen en la inspección (RF-7.3). */
export function sortAttacksByValue(attacks: Attack[]): Attack[] {
  return [...attacks].sort((a, b) => b.value - a.value);
}

/** Lo que se lee de una casilla con un lector de pantalla: qué hay en ella y
 * quién la alcanza. Es la versión en palabras de todo lo que la capa dice con
 * color (criterio C-7).
 *
 * **Las marcas mandan también aquí**, igual que en la inspección del panel: con
 * «Piezas colgadas» o «Piezas clavadas» desmarcada, la casilla no lo dice
 * tampoco en voz alta. Decirlo igual dejaría sin efecto apagarlas justo por la
 * vía del teclado —que es la única de la que se ocupa este texto— en las tres
 * pantallas de entrenamiento, donde arrancan apagadas para no adelantar la
 * solución (fila 108 del inventario de docs/07-coherencia-ui.md, criterio
 * C-3). El conteo de atacantes no depende de ninguna marca: es RF-7.3. */
export function describeSquareOccupancy(
  occupancy: OccupancyMap,
  square: string,
  marks: { hanging: boolean; pinned: boolean },
): string {
  const piece = occupancy.pieces[square];
  const { directAttacks } = occupancy.squares[square];
  const parts = [
    `${square}: ${piece ? pieceName(piece.role, piece.color) : "vacía"}`,
    ...(["w", "b"] as PieceColor[])
      .filter((color) => directAttacks[color].length > 0)
      .map((color) => `${directAttacks[color].length} de las ${colorName(color)}`),
  ];
  if (marks.pinned && piece && occupancy.pinnedSquares.includes(square)) parts.push("clavada");
  if (marks.hanging && piece && occupancy.hangingSquares.includes(square)) parts.push("colgada");
  if (directAttacks.w.length === 0 && directAttacks.b.length === 0) parts.push("sin control");
  return parts.join(", ");
}
