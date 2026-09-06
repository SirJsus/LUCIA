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
 */
import type { Config } from "chessground/config";
import type { Key } from "chessground/types";

export interface BoardConfigInput {
  fen: string;
  orientation: "white" | "black";
  bestMoveUci?: string | null;
  lastMoveUci?: string | null;
  legalMoves?: Map<string, string[]>;
  turnColor?: "white" | "black";
}

export function buildBoardConfig({
  fen,
  orientation,
  bestMoveUci,
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
    drawable: {
      autoShapes: bestMoveUci
        ? [{ orig: uciOrig(bestMoveUci), dest: uciDest(bestMoveUci), brush: "green" }]
        : [],
    },
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

export function uciOrig(uci: string): Key {
  return uci.slice(0, 2) as Key;
}

export function uciDest(uci: string): Key {
  return uci.slice(2, 4) as Key;
}

export function toSquares(uci: string | null | undefined): Key[] | undefined {
  return uci ? [uciOrig(uci), uciDest(uci)] : undefined;
}
