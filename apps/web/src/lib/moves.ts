/** Numeración de jugadas: del ply interno al número que se lee en un tablero.
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
 */

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
