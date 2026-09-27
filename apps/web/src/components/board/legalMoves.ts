/** Las jugadas legales de una posición, en el formato que chessground espera
 * para dejar arrastrar piezas.
 *
 * Vive aquí, y no dentro de una pantalla, desde que la usan tres: el tablero
 * de análisis (RF-6.2), el de los puzzles (RF-4.1) y el del sparring
 * (RF-4.3). Es la regla de `components/`: en cuanto algo lo usa la segunda
 * pantalla, sube en vez de copiarse.
 *
 * Quien sabe de reglas de ajedrez en el front es chess.js. En el tablero de
 * análisis eso es además toda la autoridad que hay, porque la API guarda el
 * árbol sin interpretarlo; en el sparring no, porque allí el servidor es el
 * rival y valida lo que se le manda (ADR-0018), y esto queda en comodidad de
 * la interfaz: qué arrastres se permiten antes de preguntar.
 */
import { Chess } from "chess.js";

export function legalMovesByOrigin(fen: string): Map<string, string[]> {
  const destsByOrigin = new Map<string, string[]>();
  if (!fen) return destsByOrigin;
  try {
    const chess = new Chess(fen);
    for (const move of chess.moves({ verbose: true })) {
      destsByOrigin.set(move.from, [...(destsByOrigin.get(move.from) ?? []), move.to]);
    }
  } catch {
    // FEN inválido: sin jugadas, el tablero queda en modo lectura
  }
  return destsByOrigin;
}
