/** Jugadas: del ply interno al número que se lee en un tablero, y el intento
 * de jugada sobre una posición.
 *
 * Existe porque el mismo dato se numeraba de tres formas: la lista de jugadas
 * y la comparación de motores contaban jugadas enteras desde 1, el gráfico de
 * evaluación contaba medias jugadas ("Jugada 41" para la 21 de las negras), y
 * el árbol de variantes numeraba desde la raíz real del tablero. Solo la
 * última era correcta para una partida que no empieza en la posición estándar
 * (criterio C-5 de docs/07-coherencia-ui.md).
 *
 * El `ply` que manejan el front y la API es siempre relativo al inicio de la
 * partida: el 0 es la primera jugada que se jugó, sea la del turno 1 o la del
 * 12. `plyFromFen` da el desplazamiento que hay que sumarle para llegar al
 * número real, y sale de la posición de partida.
 *
 * `tryMove` está aquí por lo mismo: era el otro trozo de chess.js que cada
 * tablero copiaba, y una promoción que en una pantalla corona dama y en otra
 * no sería la misma clase de incoherencia.
 */
import { Chess } from "chess.js";

/** Ply absoluto de una posición, deducido de su FEN: número de jugada y turno.
 * En la posición estándar da 0, así que sumarlo nunca estorba. */
export function plyFromFen(fen: string): number {
  const fenFields = fen.split(" ");
  const fullmove = Number(fenFields[5] ?? 1);
  const sideToMove = fenFields[1] ?? "w";
  return (fullmove - 1) * 2 + (sideToMove === "b" ? 1 : 0);
}

/** Número de jugada (el "12" de "12. Cf3") de un ply absoluto. */
export function moveNumberOf(absolutePly: number): number {
  return Math.floor(absolutePly / 2) + 1;
}

/** Cómo se nombra una jugada suelta: "12." si la jugaron las blancas, "12..."
 * si las negras. Es la convención del PGN, y así una jugada de negras no se
 * confunde con la de blancas del mismo turno. */
export function moveNumberLabel(absolutePly: number): string {
  return `${moveNumberOf(absolutePly)}${absolutePly % 2 === 0 ? "." : "..."}`;
}

/** Una secuencia de jugadas escrita como se lee en un tablero: "1. e4 e5 2.
 * Cf3 Cc6".
 *
 * Existe porque la línea del drill de aperturas era la única secuencia de
 * jugadas de la aplicación que se pintaba como prosa —"e4 e5 Nf3 Nc6", sin
 * número y sin monoespaciada—, mientras el visor, el sparring y el árbol de
 * variantes numeran y usan `font-mono` (fila 100 del inventario de
 * docs/07-coherencia-ui.md, criterio C-5).
 *
 * Se numera desde el turno 1 porque lo único que se escribe así es una línea
 * de apertura, que arranca siempre en la posición estándar: la lista de
 * jugadas de una partida que empieza a mitad es `turnsOf`, que sí recibe desde
 * dónde.
 */
export function formatMoveSequence(movesSan: string[]): string {
  return movesSan
    .map((san, ply) => (ply % 2 === 1 ? san : `${moveNumberLabel(ply)} ${san}`))
    .join(" ");
}

/** Un turno tal como se lee en un tablero: su número y la jugada de cada
 * bando, que puede faltar al principio —una partida retomada con negras— o al
 * final —la última jugada, todavía sin respuesta—. */
export interface Turn<MoveT> {
  number: number;
  white: MoveT | null;
  black: MoveT | null;
}

/** Las jugadas de una partida agrupadas por turno, que es como se leen.
 *
 * `absolutePlyOf` dice en qué ply real cae cada jugada: la lista analizada del
 * visor lo lleva encima (`move.ply` más el de la posición de partida) y la de
 * sparring lo cuenta por su sitio en la lista. De ahí salen el número del
 * turno y de qué bando es la jugada, así que una partida que empieza en la 23
 * —o que empieza con negras— se numera desde donde le toca y no desde 1.
 *
 * Quien pinta los turnos es `components/board/TurnList`; cada pantalla decide
 * qué hay dentro de cada celda.
 */
export function turnsOf<MoveT>(
  moves: MoveT[],
  absolutePlyOf: (move: MoveT, index: number) => number,
): Turn<MoveT>[] {
  const turns: Turn<MoveT>[] = [];
  moves.forEach((move, index) => {
    const ply = absolutePlyOf(move, index);
    const number = moveNumberOf(ply);
    let turn = turns.find((candidate) => candidate.number === number);
    if (!turn) {
      turn = { number, white: null, black: null };
      turns.push(turn);
    }
    if (ply % 2 === 0) turn.white = move;
    else turn.black = move;
  });
  return turns;
}

/** El resultado de intentar una jugada sobre una posición, en las tres
 * notaciones que la aplicación usa: UCI para hablar con la API y con
 * chessground, SAN para enseñarla y el FEN de después para pintar el tablero. */
export interface AttemptedMove {
  uci: string;
  san: string;
  fen: string;
}

/** Intenta mover de una casilla a otra, o `null` si la jugada no es legal
 * —chessground ya filtra casi todas, pero no arrastrar sobre una posición
 * vieja—.
 *
 * La promoción es **siempre a dama**: elegir pieza es un extra que no aporta
 * en ninguna de las cuatro pantallas que aceptan jugadas, y era la regla que
 * las cuatro repetían por su cuenta.
 */
export function tryMove(fen: string, from: string, to: string): AttemptedMove | null {
  try {
    const chess = new Chess(fen);
    const move = chess.move({ from, to, promotion: "q" });
    return { uci: move.lan, san: move.san, fen: chess.fen() };
  } catch {
    return null;
  }
}
