/** De dónde salió una partida, cuando no es de chess.com.
 *
 * Existe porque el listado no lo decía y los huecos no se explicaban solos: una
 * partida importada de un PGN (RF-1.5) enseña "—" en los dos ratings, en el
 * control de tiempo y en el ritmo, porque un archivo de torneo no trae esos
 * datos y la aplicación prefiere el hueco al número inventado. Cuatro columnas
 * vacías al lado de sus vecinas llenas, sin una palabra, se leen como un fallo
 * (fila 67 del inventario de docs/07-coherencia-ui.md, criterio C-6).
 *
 * **Las de chess.com no llevan insignia**: son la inmensa mayoría y marcarlas
 * todas convertiría la columna en ruido. Se señala lo que se sale de la norma,
 * que es justo lo que hay que explicar.
 *
 * Mismo componente en el listado y en el visor, como `CustomPositionBadge`, y
 * por la misma razón: mismo dato, mismo nombre y mismo aspecto en los dos
 * sitios (criterio C-2). Las dos insignias conviven en una misma partida —un
 * PGN importado puede además empezar en una posición dada—, así que ninguna da
 * por supuesta a la otra.
 */
import { Badge } from "./Badge";

/** Qué se dice de cada origen. `chesscom` no está: es el caso normal. */
const SOURCES: Record<string, { label: string; title: string }> = {
  manual: {
    label: "PGN importado",
    title:
      "Viene de un archivo PGN (OTB, lichess). Un PGN no trae ratings, ritmo ni si la partida " +
      "era puntuada, así que esos datos salen vacíos.",
  },
  board: {
    label: "tablero propio",
    title:
      "Es un tablero de análisis publicado como partida propia. Rating y ritmo no se piden al " +
      "marcarlo, así que salen vacíos.",
  },
};

export function GameSourceBadge({ platform }: { platform: string }) {
  const source = SOURCES[platform];
  if (!source) return null;
  return (
    <Badge tone="info" title={source.title}>
      {source.label}
    </Badge>
  );
}
