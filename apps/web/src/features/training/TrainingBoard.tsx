/** El tablero de una pantalla de entrenamiento: el tablero en sí, la capa de
 * ocupación que se enciende sobre él (RF-7) y la frase que dice qué se puede
 * hacer con él.
 *
 * Las tres pantallas de entrenamiento con tablero —el puzzle (RF-4.1), el
 * drill (RF-4.2) y el sparring (RF-4.3)— montan exactamente esto, así que está
 * escrito una vez: la columna entera con su marco, su párrafo de pie y su
 * panel de ocupación. Cada una pone lo suyo, que es la posición, quién puede
 * mover y la frase propia del ejercicio.
 *
 * **Sin barra de evaluación**, al contrario que el visor y el tablero de
 * análisis: en las tres, saber lo que opina el motor de la posición es media
 * respuesta. Y las marcas de la capa de ocupación arrancan **apagadas** por lo
 * mismo: las piezas colgadas de RF-7.4 delatan el puzzle y avisan del blunder
 * que un rival calibrado no debe avisar. Que las tres se comporten igual es lo
 * que evita explicarlo en cada una (criterio C-2 de docs/07-coherencia-ui.md).
 *
 * Por qué la capa entra donde la barra no —y qué se descartó— está en
 * docs/adr/0023-la-ocupacion-entra-en-el-entrenamiento-y-la-barra-no.md.
 */
import { useMemo } from "react";
import { BoardFrame } from "../../components/board/BoardFrame";
import type { EngineArrow } from "../../components/board/boardConfig";
import { Chessboard } from "../../components/board/Chessboard";
import { KEYBOARD_MOVE_HINT, OCCUPANCY_TOGGLE_KEY_HINT } from "../../components/board/hints";
import { legalMovesByOrigin } from "../../components/board/legalMoves";
import { OccupancyPanel } from "../../components/board/OccupancyPanel";
import { useOccupancy } from "../../components/board/useOccupancy";
import { BOARD_HINT_CLASSES } from "../../components/styles";

interface TrainingBoardProps {
  /** La posición que se ve, que no siempre es la del ejercicio: tras fallar,
   * el puzzle y el drill dejan encima la jugada intentada. La capa de
   * ocupación lee esta misma, porque lo que se lee es lo que hay en pantalla. */
  fen: string;
  /** El bando de quien entrena: orienta el tablero y es el único que mueve. */
  color: "white" | "black";
  /** Si se puede arrastrar **ahora mismo**. Falso también mientras el servidor
   * contesta: mover dos veces seguidas sería mover sobre una posición que ya
   * no es la de la pantalla (criterio C-3). */
  canMove: boolean;
  onMove: (from: string, to: string) => void;
  lastMoveUci: string | null;
  arrows?: EngineArrow[];
  /** Qué está pasando con el tablero, en la voz de cada pantalla ("Arrastra
   * una pieza para responder…", "La línea terminó…"). Los atajos se le
   * encadenan aquí, que es lo que hace que las tres los anuncien igual
   * (criterio C-1). */
  hint: string;
  /** Si la pantalla admite jugadas, aunque el servidor esté pensando. Decide
   * si se anuncia el teclado: con el ejercicio cerrado —o con la jugada
   * errónea encima— el tablero no las acepta por ninguna de las dos vías, y
   * prometer «Intro elige origen y destino» ahí es anunciar una tecla que no
   * hace nada. Esperar, en cambio, no es un estado de la pantalla. */
  acceptsMoves: boolean;
}

export function TrainingBoard({
  fen,
  color,
  canMove,
  onMove,
  lastMoveUci,
  arrows,
  hint,
  acceptsMoves,
}: TrainingBoardProps) {
  const legalMoves = useMemo(() => (canMove ? legalMovesByOrigin(fen) : undefined), [canMove, fen]);
  const occupancyController = useOccupancy(fen, { marksOnByDefault: false });

  return (
    <div className="space-y-3">
      <BoardFrame>
        <Chessboard
          fen={fen}
          orientation={color}
          turnColor={color}
          legalMoves={legalMoves}
          onMove={onMove}
          lastMoveUci={lastMoveUci}
          engineArrows={arrows}
          occupancyController={occupancyController}
        />
      </BoardFrame>
      <p className={BOARD_HINT_CLASSES}>
        {hint} {OCCUPANCY_TOGGLE_KEY_HINT}
        {acceptsMoves ? ` ${KEYBOARD_MOVE_HINT}` : ""}
      </p>

      <OccupancyPanel controller={occupancyController} />
    </div>
  );
}
