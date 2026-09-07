/** Construcción de la configuración que se le pasa a chessground.
 *
 * Vive aparte del componente porque tiene una trampa que conviene poder
 * probar: chessground fusiona la configuración con `deepMerge`, que hace
 * `base[clave] = nuevo[clave]` sin comprobar nada. Pasarle una clave con
 * valor `undefined` **borra** ese trozo de su estado interno. Es decir,
 * mandar `movable: undefined` deja el tablero sin `state.movable`, y la
 * siguiente actualización revienta con "Cannot set properties of undefined
 * (setting 'dests')".
 *
 * Por eso aquí las claves que no aplican se omiten en vez de mandarse en
 * `undefined`.
 *
 * Aquí también se decide cómo se ven las flechas del motor (RF-5.2 / RF-6.2):
 * qué pincel le toca a cada línea y qué texto lleva encima.
 *
 * Quién usa qué: `Chessboard` llama a `buildBoardConfig` y nadie más;
 * `BoardPage` arma sus flechas con `arrowsFromEngineLines` (MultiPV en vivo) y
 * `arrowsFromPreviewLine` (la continuación que se está señalando en el panel
 * del motor). `GameViewerPage` no usa ninguna de las dos: el análisis guardado
 * solo persiste la mejor jugada de cada posición, así que construye su única
 * flecha a mano. Cuando RF-10 guarde las N mejores líneas, pasará a usar
 * `arrowsFromEngineLines` como el tablero de análisis.
 */
import type { EngineLine } from "@lucia/shared-types";
import type { Config } from "chessground/config";
import type { DrawShape } from "chessground/draw";
import type { Key } from "chessground/types";
import { formatScore } from "../../lib/score";

/** Una flecha sobre el tablero. `brush` es el nombre de un pincel de
 * chessground: los `pale*` son los mismos colores con menos opacidad y trazo
 * más ancho, que es justo lo que se quiere para "esta línea también, pero es
 * la segunda opción". */
export interface EngineArrow {
  uci: string;
  brush: "green" | "paleGreen" | "paleGrey" | "blue" | "paleBlue";
  /** Texto sobre la flecha; la evaluación de esa línea, normalmente. */
  label?: string;
}

/** Cuántas líneas del motor se dibujan a la vez. Más de tres flechas sobre
 * un tablero de 64 casillas dejan de informar y empiezan a estorbar. */
const MAX_ENGINE_ARROWS = 3;

/** Pincel por posición en el ranking del motor: la mejor jugada destacada, la
 * segunda visible pero atenuada, la tercera casi un susurro. */
const ENGINE_LINE_BRUSHES: EngineArrow["brush"][] = ["green", "paleGreen", "paleGrey"];

/** Flechas para las mejores líneas de una posición, etiquetadas con su
 * evaluación. Cada flecha es la **primera** jugada de su línea: es la única
 * que se puede jugar desde la posición actual. */
export function arrowsFromEngineLines(lines: EngineLine[] | undefined): EngineArrow[] {
  return (lines ?? [])
    .slice(0, MAX_ENGINE_ARROWS)
    .filter((line) => line.pv_uci.length > 0)
    .map((line, index) => ({
      uci: line.pv_uci[0],
      brush: ENGINE_LINE_BRUSHES[index] ?? "paleGrey",
      label: formatScore(line),
    }));
}

/** Flechas para previsualizar una continuación completa: la última jugada de
 * la secuencia va destacada y las anteriores atenuadas, para que se lea el
 * recorrido y se vea dónde termina. En azul, no en verde, porque no es lo que
 * el motor recomienda ahora sino a dónde lleva la línea que se está mirando. */
export function arrowsFromPreviewLine(pvUci: string[]): EngineArrow[] {
  return pvUci.map((uci, index) => ({
    uci,
    brush: index === pvUci.length - 1 ? "blue" : "paleBlue",
    label: String(index + 1),
  }));
}

export interface BoardConfigInput {
  fen: string;
  orientation: "white" | "black";
  engineArrows?: EngineArrow[];
  lastMoveUci?: string | null;
  legalMoves?: Map<string, string[]>;
  turnColor?: "white" | "black";
}

export function buildBoardConfig({
  fen,
  orientation,
  engineArrows,
  lastMoveUci,
  legalMoves,
  turnColor,
}: BoardConfigInput): Config {
  const config: Config = {
    fen,
    orientation,
    // `lastMove` sí se manda siempre, incluso vacío: chessground lo trata
    // aparte (`'lastMove' in config && !config.lastMove`) y es lo que limpia
    // el resaltado al volver a la posición inicial.
    lastMove: toSquares(lastMoveUci),
    drawable: { autoShapes: (engineArrows ?? []).map(toDrawShape) },
  };

  if (turnColor) config.turnColor = turnColor;
  if (legalMoves) {
    config.movable = {
      free: false,
      color: turnColor,
      dests: legalMoves as Map<Key, Key[]>,
    };
  }

  return config;
}

function toDrawShape(arrow: EngineArrow): DrawShape {
  return {
    orig: uciOrig(arrow.uci),
    dest: uciDest(arrow.uci),
    brush: arrow.brush,
    ...(arrow.label ? { label: { text: arrow.label } } : {}),
  };
}

function uciOrig(uci: string): Key {
  return uci.slice(0, 2) as Key;
}

function uciDest(uci: string): Key {
  return uci.slice(2, 4) as Key;
}

function toSquares(uci: string | null | undefined): Key[] | undefined {
  return uci ? [uciOrig(uci), uciDest(uci)] : undefined;
}
