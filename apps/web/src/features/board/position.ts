/** La posición que se está montando en el editor, y su traducción a FEN
 * (lo que faltaba de RF-6.1).
 *
 * Vive aparte del componente porque es lógica pura y conviene poder probarla:
 * componer un FEN a mano tiene dos trampas —contar casillas vacías seguidas y
 * recorrer los rangos del 8 al 1— y equivocarse en cualquiera de las dos da
 * una cadena que parece un FEN y describe otra posición.
 *
 * **El modelo no es un `Chess` de chess.js** a propósito: mientras se edita,
 * la posición es ilegal casi todo el rato (sin reyes, con tres damas a medio
 * poner), y chess.js rechaza cargar eso. Aquí se guarda lo que hay puesto sin
 * juzgarlo, y solo al terminar se le pide a chess.js que diga si sirve
 * (`positionError`).
 */
import { Chess, validateFen } from "chess.js";

/** Una pieza en la notación FEN: mayúscula las blancas, minúscula las
 * negras. Es la misma letra que se escribe en el FEN, así que no hay que
 * traducir nada al componerlo. */
export type PieceCode = "P" | "N" | "B" | "R" | "Q" | "K" | "p" | "n" | "b" | "r" | "q" | "k";

/** Qué pieza hay en cada casilla ocupada ("e4" → "P"). Las vacías no están. */
export type PiecePlacement = Record<string, PieceCode>;

export interface EditablePosition {
  pieces: PiecePlacement;
  turn: "w" | "b";
  /** Enroques disponibles, en la forma del FEN: "KQkq", "Kq", o "" si
   * ninguno. */
  castling: string;
  /** Casilla de captura al paso ("e3"), o `null`. */
  enPassant: string | null;
}

/** La posición de partida, en el mismo FEN que escribe chess.js: así una
 * posición montada en el editor se compara sin más con la estándar. */
export const STANDARD_STARTING_FEN = new Chess().fen();

/** Las columnas, y las filas en el orden en que las escribe un FEN: de la
 * octava a la primera. Solo se usan aquí, al componer y leer la cadena; las
 * casillas que se pintan en pantalla se recorren con `components/board/squares`. */
const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"] as const;
const RANKS = ["8", "7", "6", "5", "4", "3", "2", "1"] as const;

/** Los enroques en el orden en que se escriben en un FEN. El orden importa:
 * "kqKQ" describe lo mismo que "KQkq" y no es un FEN válido. */
export const CASTLING_FLAGS = ["K", "Q", "k", "q"] as const;

export type CastlingFlag = (typeof CASTLING_FLAGS)[number];

export const EMPTY_POSITION: EditablePosition = {
  pieces: {},
  turn: "w",
  castling: "",
  enPassant: null,
};

/** Compone el FEN de la posición montada.
 *
 * El reloj de medias jugadas y el número de jugada van siempre a "0 1": una
 * posición montada a mano no viene de ninguna partida, así que no hay historia
 * que contar. Quien la abra en el tablero empezará a contar desde ahí.
 */
export function toFen(position: EditablePosition): string {
  const placement = RANKS.map((rank) => rankToFen(position.pieces, rank)).join("/");
  return [
    placement,
    position.turn,
    position.castling || "-",
    position.enPassant ?? "-",
    "0",
    "1",
  ].join(" ");
}

function rankToFen(pieces: PiecePlacement, rank: string): string {
  let rankText = "";
  let emptySquares = 0;
  for (const file of FILES) {
    const piece = pieces[`${file}${rank}`];
    if (piece) {
      // Las vacías acumuladas se escriben como número antes de la pieza.
      rankText += (emptySquares || "") + piece;
      emptySquares = 0;
    } else {
      emptySquares++;
    }
  }
  return rankText + (emptySquares || "");
}

/** Lee un FEN a la forma que edita la pantalla, o `null` si no lo es.
 *
 * Solo mira la estructura, no la legalidad: se usa para arrancar el editor
 * desde lo que hubiera escrito en el campo, y ahí una posición a medias es un
 * punto de partida perfectamente razonable.
 */
export function fromFen(fen: string): EditablePosition | null {
  const [placement, turn, castling, enPassant] = fen.trim().split(/\s+/);
  if (!placement || !turn) return null;

  const rows = placement.split("/");
  if (rows.length !== RANKS.length) return null;

  const pieces: PiecePlacement = {};
  for (const [rowIndex, row] of rows.entries()) {
    let fileIndex = 0;
    for (const character of row) {
      if (/\d/.test(character)) fileIndex += Number(character);
      else if (/[pnbrqk]/i.test(character)) {
        if (fileIndex >= FILES.length) return null;
        pieces[`${FILES[fileIndex]}${RANKS[rowIndex]}`] = character as PieceCode;
        fileIndex++;
      } else return null;
    }
    if (fileIndex !== FILES.length) return null;
  }

  return {
    pieces,
    turn: turn === "b" ? "b" : "w",
    castling: castling && castling !== "-" ? castling : "",
    enPassant: enPassant && enPassant !== "-" ? enPassant : null,
  };
}

/** Las casillas donde puede estar la marca de captura al paso: la tercera
 * fila si acaban de mover las blancas, la sexta si las negras. */
export function enPassantSquares(turn: "w" | "b"): string[] {
  const rank = turn === "w" ? "6" : "3";
  return FILES.map((file) => `${file}${rank}`);
}

/** Qué le pasa a esta posición, en una frase, o `null` si sirve para empezar
 * una partida.
 *
 * Los motivos los da `validateFen` de chess.js en inglés y aquí se traducen:
 * el usuario tiene que leer qué arreglar, no descifrarlo. El único que chess.js
 * no comprueba se añade después —que el bando que **no** mueve esté dando
 * jaque, que es imposible en una partida real y el motor rechazaría—.
 */
export function positionError(fen: string): string | null {
  const validation = validateFen(fen);
  if (!validation.ok) return translateFenError(validation.error ?? "");

  const board = new Chess(fen);
  const waitingColor = board.turn() === "w" ? "b" : "w";
  const waitingKing = board
    .board()
    .flat()
    .find((square) => square?.type === "k" && square.color === waitingColor);
  if (waitingKing && board.isAttacked(waitingKing.square, board.turn())) {
    return "El rey del bando que no mueve está en jaque: esa posición no puede darse en una partida.";
  }
  return null;
}

/** Los motivos de `validateFen` que se pueden encontrar montando una posición
 * a mano. Se emparejan por subcadena porque chess.js los da como frases
 * ("Invalid FEN: missing white king") y su redacción exacta es cosa suya. */
const FEN_ERROR_MESSAGES: [needle: string, message: string][] = [
  ["missing white king", "Falta el rey blanco."],
  ["missing black king", "Falta el rey negro."],
  ["too many white kings", "Hay más de un rey blanco."],
  ["too many black kings", "Hay más de un rey negro."],
  ["edge rows", "Hay peones en la primera o en la última fila, donde no pueden estar."],
  ["en-passant", "La casilla de captura al paso no encaja con el turno."],
  ["castling", "Los enroques marcados no son posibles con estas piezas."],
];

function translateFenError(error: string): string {
  const known = FEN_ERROR_MESSAGES.find(([needle]) => error.toLowerCase().includes(needle));
  return known ? known[1] : "La posición no es válida todavía.";
}
