/** Las flechas que se dibujan sobre un puzzle ya cerrado (RF-4.1).
 *
 * Vive aparte del componente porque es lógica pura y conviene poder probarla:
 * las respuestas llegan en notación algebraica —que es como se leen— y hay
 * que traducirlas a casillas, que es lo que la flecha necesita. Quien sabe de
 * jugadas en el front es chess.js, aquí igual que en el resto de pantallas.
 */
import { Chess } from "chess.js";
import type { EngineArrow } from "../../components/board/boardConfig";

/** La solución en verde, las que valían lo mismo atenuadas (RF-10.3) y en
 * rojo la que se jugó en la partida. Una jugada que no encaje en la posición
 * no se dibuja: media respuesta mal puesta confunde más que faltar. */
export function arrowsFromPuzzleAnswer(
  fen: string,
  solutionsSan: string[],
  playedSan: string | null,
): EngineArrow[] {
  const arrows: EngineArrow[] = solutionsSan.flatMap((san, index) => {
    const uci = toUci(fen, san);
    return uci ? [{ uci, brush: index === 0 ? "green" : "paleGreen", label: san }] : [];
  });
  if (!playedSan) return arrows;
  const playedUci = toUci(fen, playedSan);
  return playedUci ? [...arrows, { uci: playedUci, brush: "red", label: playedSan }] : arrows;
}

function toUci(fen: string, san: string): string | null {
  try {
    return new Chess(fen).move(san).lan;
  } catch {
    return null;
  }
}
