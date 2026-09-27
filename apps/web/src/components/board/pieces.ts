/** Lo que hace falta saber de una clase de pieza: cómo la dibuja chessground,
 * cómo se llama en español y cuánto vale.
 *
 * Vive aparte porque lo necesitan tres sitios que no se conocen entre sí: la
 * paleta del editor de posición (RF-6.1), que dibuja piezas fuera del tablero;
 * la capa de ocupación (RF-7), que las nombra al listar atacantes y las pesa
 * para decidir qué está colgado; y cualquier pantalla que tenga que decir en
 * palabras lo que hay en una casilla. Tenerlo repetido habría dado dos tablas
 * de nombres que se separarían en el primer retoque.
 *
 * Los nombres van con su color ya concordado —"Torre negra", no "Torre
 * negro"— porque componerlos sobre la marcha delata que la frase la armó una
 * máquina, y estos nombres se leen en voz alta (criterio C-7 de
 * docs/07-coherencia-ui.md).
 */
import type { Color, Role } from "chessground/types";

/** La letra con la que el FEN y chess.js nombran la clase de pieza. */
export type PieceRole = "p" | "n" | "b" | "r" | "q" | "k";

/** El bando, como lo escriben el FEN y chess.js. */
export type PieceColor = "w" | "b";

/** El valor convencional de cada pieza, el de toda la vida (peón 1, caballo y
 * alfil 3, torre 5, dama 9). Ordena las listas de atacantes (RF-7.3) y decide
 * qué pieza está colgada (RF-7.4).
 *
 * El rey vale 100 y no infinito: hace falta un número para ordenar, y con 100
 * ya queda por encima de cualquier suma de piezas, así que un rey que ataca
 * nunca cuenta como "atacante de menor valor" —capturar con el rey jamás es
 * el cambio favorable que RF-7.4 busca—.
 */
const PIECE_KINDS: Record<PieceRole, { role: Role; white: string; black: string; value: number }> =
  {
    p: { role: "pawn", white: "Peón blanco", black: "Peón negro", value: 1 },
    n: { role: "knight", white: "Caballo blanco", black: "Caballo negro", value: 3 },
    b: { role: "bishop", white: "Alfil blanco", black: "Alfil negro", value: 3 },
    r: { role: "rook", white: "Torre blanca", black: "Torre negra", value: 5 },
    q: { role: "queen", white: "Dama blanca", black: "Dama negra", value: 9 },
    k: { role: "king", white: "Rey blanco", black: "Rey negro", value: 100 },
  };

/** Cómo se llama la pieza, con su color: "Alfil blanco", "Dama negra". */
export function pieceName(role: PieceRole, color: PieceColor): string {
  return PIECE_KINDS[role][color === "w" ? "white" : "black"];
}

/** El nombre que chessground le da a la clase de pieza, para pintarla. */
export function chessgroundRole(role: PieceRole): Role {
  return PIECE_KINDS[role].role;
}

/** El bando como lo nombra chessground, que escribe la palabra entera. */
export function chessgroundColor(color: PieceColor): Color {
  return color === "w" ? "white" : "black";
}

export function pieceValue(role: PieceRole): number {
  return PIECE_KINDS[role].value;
}

/** El bando contrario. */
export function otherColor(color: PieceColor): PieceColor {
  return color === "w" ? "b" : "w";
}

/** Cómo se nombra un bando en una frase: "las blancas cubren…". */
export function colorName(color: PieceColor): string {
  return color === "w" ? "blancas" : "negras";
}
