/** Aviso de que una partida o un tablero no empieza en la posición estándar.
 *
 * Odds chess, Chess960 y partidas empezadas desde una posición dada existen en
 * chess.com y LUCIA las importa; un tablero de análisis se crea desde un FEN
 * casi siempre. Sin este aviso, un tablero al que le faltan piezas o las tiene
 * descolocadas se lee como un fallo de la aplicación (criterio C-6 de
 * docs/07-coherencia-ui.md).
 *
 * Es un componente y no una insignia suelta en cada pantalla porque aparece en
 * el listado de partidas, en el visor y en el listado de tableros: mismo dato,
 * mismo nombre y mismo aspecto en los tres (C-2). El texto largo va en el
 * `title`, que es donde cabe.
 */
import { Badge } from "./Badge";

export function CustomPositionBadge() {
  return (
    <Badge
      tone="warning"
      title="No empieza en la posición estándar: partida con ventaja, Chess960 o posición dada"
    >
      posición dada
    </Badge>
  );
}
